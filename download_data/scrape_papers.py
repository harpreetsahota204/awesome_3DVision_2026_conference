#!/usr/bin/env python3
import csv
import os
import requests
import time
import zipfile
import tempfile
from pathlib import Path
from requests.exceptions import ChunkedEncodingError, RequestException

CSV_URL = "https://3dvconf.github.io/2026/schedule.csv"
CSV_FILE = "schedule.csv"
OUTPUT_DIR = "papers"

def download_file(url, output_path):
    """Download a file with error handling. Returns True if successful, False otherwise."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        if response.status_code == 404:
            return False
        
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except (ChunkedEncodingError, RequestException) as e:
        # Delete partial file on error
        if os.path.exists(output_path):
            os.unlink(output_path)
        print(f"  Error downloading {url}: {e}")
        return False

Path(OUTPUT_DIR).mkdir(exist_ok=True)

response = requests.get(CSV_URL)
csv_content = response.text

with open(CSV_FILE, 'w') as f:
    f.write(csv_content)

reader = csv.DictReader(csv_content.splitlines())

papers = [(row.get('ID', '').strip(), row['Title'].strip(), row['PDF Link'].strip(), row.get('Supplementary Link', '').strip()) 
          for row in reader if row.get('Title', '').strip() and row.get('PDF Link', '').strip()]

for i, (paper_id, title, pdf_url, supp_url) in enumerate(papers, 1):
    filename = paper_id or f"{i:03d}"
    
    # Download PDF
    pdf_path = os.path.join(OUTPUT_DIR, f"{filename}.pdf")
    if not os.path.exists(pdf_path):
        print(f"[{i}/{len(papers)}] Downloading PDF: {title[:60]}...")
        if download_file(pdf_url, pdf_path):
            print(f"  Saved: {pdf_path}")
        time.sleep(1)
    
    # Download supplemental materials if available
    if supp_url:
        supp_path = os.path.join(OUTPUT_DIR, f"{filename}_supp_mat.pdf")
        if not os.path.exists(supp_path):
            print(f"[{i}/{len(papers)}] Downloading supplemental: {title[:60]}...")
            try:
                response = requests.get(supp_url, stream=True, timeout=60)
                
                if response.status_code == 404:
                    print(f"  Skipping (404): {supp_url}")
                else:
                    response.raise_for_status()
                    
                    content_type = response.headers.get('content-type', '').lower()
                    url_lower = supp_url.lower()
                    
                    # Check if it's a ZIP file
                    if 'zip' in content_type or url_lower.endswith('.zip'):
                        tmp_path = None
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                                for chunk in response.iter_content(chunk_size=8192):
                                    tmp.write(chunk)
                                tmp_path = tmp.name
                            
                            # Extract ZIP and find PDFs
                            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                                pdf_files = [f for f in zip_ref.namelist() if f.lower().endswith('.pdf')]
                                if pdf_files:
                                    # Extract first PDF found
                                    pdf_content = zip_ref.read(pdf_files[0])
                                    with open(supp_path, 'wb') as f:
                                        f.write(pdf_content)
                                    print(f"  Extracted PDF from ZIP: {supp_path}")
                                else:
                                    print(f"  No PDF found in ZIP")
                        except (ChunkedEncodingError, RequestException, zipfile.BadZipFile) as e:
                            if os.path.exists(supp_path):
                                os.unlink(supp_path)
                            print(f"  Error processing ZIP: {e}")
                        finally:
                            if tmp_path and os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                    # Check if it's a PDF
                    elif 'pdf' in content_type or url_lower.endswith('.pdf'):
                        if download_file(supp_url, supp_path):
                            print(f"  Saved: {supp_path}")
                    else:
                        print(f"  Unknown file type: {content_type}")
            except (ChunkedEncodingError, RequestException) as e:
                if os.path.exists(supp_path):
                    os.unlink(supp_path)
                print(f"  Error downloading supplemental: {e}")
            
            time.sleep(1)
