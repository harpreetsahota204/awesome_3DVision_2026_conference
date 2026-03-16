"""
Parse the 3DVS 2026 conference papers into a FiftyOne grouped dataset.

Dataset structure
-----------------
Each group represents one paper (keyed by paper ID).  Every page image —
whether from the main PDF or the supplementary material — becomes its own
slice within that group:

    Group "44"
        page_01      → images/44_page_001.png
        page_02      → images/44_page_002.png
        ...
        supp_page_01 → images/44_supp_mat_page_001.png
        ...

Groups are unbalanced by design: papers with no supplementary material simply
have no supp_page_* slices, and papers with different page counts have
different numbers of page_* slices.  FiftyOne handles this natively.

Usage
-----
    python parse_fiftyone_dataset.py

The script creates (or overwrites) a persistent FiftyOne dataset named
"3dvs2026_papers" and launches the FiftyOne App for inspection.
"""

from __future__ import annotations

from pathlib import Path

import fiftyone as fo
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

WORKSPACE = Path(__file__).parent
IMAGES_DIR = WORKSPACE / "images"
SCHEDULE_CSV = WORKSPACE / "schedule_with_times.csv"

DATASET_NAME = "3dvs2026_papers"
DEFAULT_SLICE = "page_01"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nullable_str(value) -> str | None:
    """Return a string value, or None if the value is NaN / missing."""
    return str(value) if pd.notna(value) else None


def _paper_metadata(row: pd.Series) -> dict:
    """
    Extract the fields we want to store on every sample for a given paper row.

    Oral-specific fields (oral_date, oral_start_time) are None for
    poster-only papers.
    """
    return dict(
        paper_id=str(int(row["ID"])),
        title=row["Title"],
        authors=[a.strip() for a in row["Authors"].split(",")],
        abstract=row["Abstract"],
        poster_session=int(row["Poster Session"]),
        poster_id=int(row["Poster ID"]),
        oral_session=_nullable_str(int(row["Oral Session"]) if pd.notna(row["Oral Session"]) else None),
        pdf_link=row["PDF Link"],
        supplementary_link=_nullable_str(row["Supplementary Link"]),
        oral_date=_nullable_str(row["oral_date"]),
        oral_start_time=_nullable_str(row["oral_start_time"]),
        poster_date=str(row["poster_date"]),
        poster_start_time=str(row["poster_start_time"]),
    )


def _build_group_samples(
    row: pd.Series,
    images_dir: Path,
) -> list[fo.Sample]:
    """
    Build all FiftyOne samples for a single paper.

    Returns an empty list (with a warning) if no images are found for
    this paper ID, so the caller can safely skip it.
    """
    paper_id = str(int(row["ID"]))
    meta = _paper_metadata(row)

    main_pages = sorted(images_dir.glob(f"{paper_id}_page_*.png"))
    supp_pages = sorted(images_dir.glob(f"{paper_id}_supp_mat_page_*.png"))

    if not main_pages:
        print(f"  WARNING: no images found for paper {paper_id} — skipping")
        return []

    group = fo.Group()
    samples: list[fo.Sample] = []

    for i, path in enumerate(main_pages, start=1):
        samples.append(fo.Sample(
            filepath=str(path),
            group=group.element(f"page_{i:02d}"),
            **meta,
        ))

    for i, path in enumerate(supp_pages, start=1):
        samples.append(fo.Sample(
            filepath=str(path),
            group=group.element(f"supp_page_{i:02d}"),
            **meta,
        ))

    return samples


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_dataset() -> fo.Dataset:
    """
    Create the "3dvs2026_papers" grouped FiftyOne dataset from scratch.

    Reads the schedule CSV, globs the images directory for each paper, and
    adds every page as its own named slice within the paper's group.
    """
    df = pd.read_csv(SCHEDULE_CSV)
    print(f"Loaded {len(df)} papers from {SCHEDULE_CSV.name}")

    dataset = fo.Dataset(DATASET_NAME, overwrite=True, persistent=True)
    dataset.add_group_field("group", default=DEFAULT_SLICE)

    all_samples: list[fo.Sample] = []

    for _, row in df.iterrows():
        samples = _build_group_samples(row, IMAGES_DIR)
        all_samples.extend(samples)

    print(f"Adding {len(all_samples)} samples across {len(df)} papers …")
    dataset.add_samples(all_samples, progress=True)
    dataset.compute_metadata()
    dataset.add_dynamic_sample_fields()
    dataset.save()

    return dataset


def print_summary(dataset: fo.Dataset) -> None:
    """Print a brief summary of the finished dataset."""
    group_ids = dataset.values("group.id")
    num_groups = len(set(group_ids))
    slice_names = sorted(dataset.group_slices)
    main_slices = [s for s in slice_names if not s.startswith("supp_")]
    supp_slices = [s for s in slice_names if s.startswith("supp_")]

    print("\n--- Dataset summary ---")
    print(f"  Name    : {dataset.name}")
    print(f"  Samples : {len(dataset)}")
    print(f"  Groups  : {num_groups}")
    print(f"  Main page slices : {len(main_slices)}  ({main_slices[0]} … {main_slices[-1]})")
    print(f"  Supp page slices : {len(supp_slices)}  ({supp_slices[0]} … {supp_slices[-1]})")
    print("-----------------------\n")


if __name__ == "__main__":
    dataset = build_dataset()
    print_summary(dataset)
