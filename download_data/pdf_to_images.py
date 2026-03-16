#!/usr/bin/env python3
import os
from pathlib import Path

from pdf2image import convert_from_path

PAPERS_DIR = "papers"
IMAGES_DIR = "images"


def pdf_to_images(pdf_path, output_dir):
    pdf_name = Path(pdf_path).stem
    pages = convert_from_path(pdf_path, dpi=200)

    for idx, page in enumerate(pages, start=1):
        image_path = os.path.join(output_dir, f"{pdf_name}_page_{idx:03d}.png")
        page.save(image_path, "PNG")

    return len(pages)


Path(IMAGES_DIR).mkdir(exist_ok=True)

pdf_files = sorted(f for f in os.listdir(PAPERS_DIR) if f.endswith(".pdf"))

for i, pdf_file in enumerate(pdf_files, 1):
    pdf_path = os.path.join(PAPERS_DIR, pdf_file)
    print(f"[{i}/{len(pdf_files)}] Converting: {pdf_file}...")
    try:
        num_pages = pdf_to_images(pdf_path, IMAGES_DIR)
        print(f"  Converted {num_pages} pages")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nDone! Images saved to {IMAGES_DIR}/")
