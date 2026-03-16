# 3DV 2026 Papers Pipeline

Downloads all 3DV 2026 papers, converts PDFs to images, and loads everything into a FiftyOne grouped dataset.

## Setup

Install Python dependencies:
```bash
pip install requests pdf2image Pillow pandas fiftyone
```

`pdf2image` requires `poppler`:
```bash
# Ubuntu / Debian
sudo apt install poppler-utils

# macOS
brew install poppler
```

## Run everything from this directory

```bash
cd download_data

python scrape_papers.py           # Step 1 — download PDFs
python pdf_to_images.py           # Step 2 — convert PDFs to page images
python add_times_to_schedule.py   # Step 3 — enrich schedule with session times
python parse_fiftyone_dataset.py  # Step 4 — build the FiftyOne dataset
```

That's it. All output lands in this directory.

---

## What each script does

### Step 1 — `scrape_papers.py`
- Fetches `schedule.csv` from `https://3dvconf.github.io/2026/schedule.csv`
- Downloads each paper's main PDF to `papers/{ID}.pdf`
- Downloads supplementary material (PDF or ZIP → PDF) to `papers/{ID}_supp_mat.pdf`
- Skips files that already exist, so it's safe to re-run after an interruption

### Step 2 — `pdf_to_images.py`
- Converts every PDF in `papers/` to per-page PNGs at 200 DPI
- Saves images to `images/` named `{pdf_stem}_page_{N:03d}.png`
  - e.g. `44_page_001.png`, `44_supp_mat_page_003.png`

### Step 3 — `add_times_to_schedule.py`
- Reads `schedule.csv` and `conf_schedule.txt`
- Adds concrete dates and times for each paper's oral and poster sessions
- Writes `schedule_with_times.csv`

### Step 4 — `parse_fiftyone_dataset.py`
- Reads `schedule_with_times.csv` and the `images/` directory
- Creates a persistent FiftyOne dataset named **`3dvs2026_papers`**
- Each paper becomes a **group**; each PDF page becomes a named **slice**:
  - `page_01`, `page_02`, … — main paper pages
  - `supp_page_01`, `supp_page_02`, … — supplementary pages
- Stores metadata on every sample: `title`, `authors`, `abstract`, `poster_session`, `poster_id`, `oral_session`, `pdf_link`, `oral_date`, `oral_start_time`, `poster_date`, `poster_start_time`

---

## Directory layout after running

```
download_data/
├── papers/                    # PDFs (created by Step 1)
│   ├── 44.pdf
│   ├── 44_supp_mat.pdf
│   └── ...
├── images/                    # PNGs (created by Step 2)
│   ├── 44_page_001.png
│   ├── 44_supp_mat_page_001.png
│   └── ...
├── schedule.csv               # downloaded in Step 1
├── schedule_with_times.csv    # created in Step 3
└── conf_schedule.txt          # session → date/time mapping (hand-curated)
```

---

## Exploring the dataset

```python
import fiftyone as fo

dataset = fo.load_dataset("3dvs2026_papers")
fo.launch_app(dataset)
```

Filter by session:
```python
view = dataset.match(fo.ViewField("poster_session") == 2)
fo.launch_app(view)
```
