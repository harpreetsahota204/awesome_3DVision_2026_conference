# 3DV 2026 Papers Scraper

This script downloads all PDF papers from the 3DV 2026 accepted papers page.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python scrape_papers.py
```

The script will:
1. Fetch the CSV file containing paper metadata from `https://3dvconf.github.io/2026/schedule.csv`
2. Parse the CSV to extract PDF links
3. Download each PDF to the `papers/` directory
4. Name files based on the paper title (sanitized for filesystem compatibility)

## Features

- Automatically creates the `papers/` directory
- Skips already downloaded files
- Sanitizes filenames to be filesystem-safe
- Includes a delay between downloads to be respectful to the server
- Shows progress and handles errors gracefully

## Output

PDFs will be saved in the `papers/` directory with filenames like:
- `001_Paper_Title.pdf`
- `002_Another_Paper_Title.pdf`

If a paper has a Poster ID, it will be prefixed:
- `01_Paper_Title.pdf`
