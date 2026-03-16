"""Utility to enrich the conference schedule with concrete dates and times.

This script:
- Reads `conf_schedule.txt`, which encodes a mapping from session type/number
  (e.g. oral 3, poster 5) to a calendar date and start/end times.
- Reads `schedule.csv`, which contains paper metadata and the `Oral Session`
  and `Poster Session` indices.
- Produces `schedule_with_times.csv` that contains all original columns plus
  six new columns:
    * oral_date, oral_start_time, oral_end_time
    * poster_date, poster_start_time, poster_end_time

Run from the project root with:

    python add_times_to_schedule.py
"""

import csv
from pathlib import Path


# Base directory of this script (assumed to contain the CSV/TXT files as well).
BASE_DIR = Path(__file__).parent

# Input schedule exported from the conference system (no concrete times).
SCHEDULE_CSV = BASE_DIR / "schedule.csv"

# Machine-readable mapping derived from the human-facing program.
CONF_SCHEDULE = BASE_DIR / "conf_schedule.txt"

# Output schedule with concrete date/time columns added.
OUTPUT_CSV = BASE_DIR / "schedule_with_times.csv"


def load_session_mapping(path: Path):
    """Load the (session_type, session_num) -> date/time mapping.

    The file at `path` is expected to be a CSV with the following columns:
        session_type, session_num, date, start_time, end_time

    Where:
    - `session_type` is a lowercase string like 'oral' or 'poster'.
    - `session_num` is the numeric index used in `schedule.csv` (1–6).

    Returns
    -------
    dict
        Nested dict of the form:
        {
            ('oral', 'date'): {1: '2026-03-20', ...},
            ('oral', 'start_time'): {1: '09:15', ...},
            ('oral', 'end_time'): {...},
            ('poster', 'date'): {...},
            ('poster', 'start_time'): {...},
            ('poster', 'end_time'): {...},
        }
    """
    # Initialize a small, explicit structure rather than a deeply nested dict,
    # which keeps the access pattern in `main` very straightforward.
    mapping = {
        ("oral", "date"): {},
        ("oral", "start_time"): {},
        ("oral", "end_time"): {},
        ("poster", "date"): {},
        ("poster", "start_time"): {},
        ("poster", "end_time"): {},
    }

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize and parse keys so that we can look up by integer
            # session number without worrying about whitespace or casing.
            session_type = row["session_type"].strip().lower()
            num = row["session_num"].strip()
            key = int(num) if num.isdigit() else num

            # Store date and time information for this (type, number) pair.
            mapping[(session_type, "date")][key] = row["date"].strip()
            mapping[(session_type, "start_time")][key] = row["start_time"].strip()
            mapping[(session_type, "end_time")][key] = row["end_time"].strip()

    return mapping


def main():
    """Enrich `schedule.csv` with concrete date/time information.

    This function wires everything together:
    - loads the session mapping from `conf_schedule.txt`
    - streams through `schedule.csv`
    - for each row, looks up the appropriate oral/poster time window
    - writes out the augmented rows to `schedule_with_times.csv`
    """
    session_map = load_session_mapping(CONF_SCHEDULE)

    with SCHEDULE_CSV.open(newline="", encoding="utf-8") as f_in, OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8"
    ) as f_out:
        reader = csv.DictReader(f_in)

        # Extend the original header with our new date/time columns.
        fieldnames = (
            reader.fieldnames
            + [
                "oral_date",
                "oral_start_time",
                "oral_end_time",
                "poster_date",
                "poster_start_time",
                "poster_end_time",
            ]
        )
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # ---- Oral mapping -------------------------------------------------
            # `Oral Session` is either an integer-like string (e.g. "3") or empty.
            oral_session_raw = row.get("Oral Session", "").strip()
            oral_num = int(oral_session_raw) if oral_session_raw.isdigit() else None

            if oral_num is not None:
                row["oral_date"] = session_map[("oral", "date")].get(oral_num, "")
                row["oral_start_time"] = session_map[("oral", "start_time")].get(
                    oral_num, ""
                )
                row["oral_end_time"] = session_map[("oral", "end_time")].get(
                    oral_num, ""
                )
            else:
                # No oral session for this paper (e.g. posters-only).
                row["oral_date"] = ""
                row["oral_start_time"] = ""
                row["oral_end_time"] = ""

            # ---- Poster mapping -----------------------------------------------
            poster_session_raw = row.get("Poster Session", "").strip()
            poster_num = (
                int(poster_session_raw) if poster_session_raw.isdigit() else None
            )

            if poster_num is not None:
                row["poster_date"] = session_map[("poster", "date")].get(
                    poster_num, ""
                )
                row["poster_start_time"] = session_map[("poster", "start_time")].get(
                    poster_num, ""
                )
                row["poster_end_time"] = session_map[("poster", "end_time")].get(
                    poster_num, ""
                )
            else:
                # No poster session for this paper (e.g. orals-only).
                row["poster_date"] = ""
                row["poster_start_time"] = ""
                row["poster_end_time"] = ""

            writer.writerow(row)


if __name__ == "__main__":
    main()
