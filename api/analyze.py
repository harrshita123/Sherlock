from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import traceback
import tempfile
import gzip
import urllib.request

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sherlock.analysis.runner import run_analysis
from sherlock.report.generator import generate_markdown_report

# Blob storage base URL
BLOB_BASE_URL = "https://bg4wqyfw9rdueaik.public.blob.vercel-storage.com/fixtures"

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            blk_file = data.get('blk')
            rev_file = data.get('rev')
            xor_file = data.get('xor')

            if not blk_file or not xor_file:
                self.send_json({"ok": False, "error": {"code": "MISSING_FILES", "message": "BLK and XOR files are required."}}, status=400)
                return

            # Strict ID matching validation
            blk_id = "".join(filter(str.isdigit, os.path.basename(blk_file)))
            if rev_file:
                rev_id = "".join(filter(str.isdigit, os.path.basename(rev_file)))
                if blk_id != rev_id:
                    self.send_json({"ok": False, "error": {"code": "FILE_MISMATCH", "message": f"Block ID ({blk_id}) does not match Undo ID ({rev_id})."}}, status=400)
                    return
            else:
                rev_file = blk_file.replace("blk", "rev")

            # Get base names
            blk_basename = os.path.basename(blk_file).replace('.dat', '')
            rev_basename = os.path.basename(rev_file).replace('.dat', '')
            xor_basename = os.path.basename(xor_file)

            stem = blk_basename.replace(".gz", "")

            # Check cache in public/out first
            base_dir = os.path.join(os.path.dirname(__file__), '..')
            json_path = os.path.join(base_dir, "public", "out", f"{stem}.json")
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    report = json.load(f)
                self.send_json(report)
                return

            # Download files from Blob storage to temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                blk_path = self.download_and_extract(f"{blk_basename}.dat.gz", tmpdir)
                rev_path = self.download_and_extract(f"{rev_basename}.dat.gz", tmpdir)
                xor_path = self.download_file(xor_basename, tmpdir)

                if not blk_path:
                    self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"Block file {blk_file} not found in storage."}}, status=404)
                    return
                if not rev_path:
                    self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"Undo file {rev_file} not found in storage."}}, status=404)
                    return
                if not xor_path:
                    self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"XOR key {xor_file} not found in storage."}}, status=404)
                    return

                # Run analysis
                report, stem = run_analysis(blk_path, rev_path, xor_path)
                generate_markdown_report(report, stem)
                
                self.send_json(report)
        except Exception as e:
            print(f"Error: {traceback.format_exc()}")
            self.send_json({"ok": False, "error": {"code": "ANALYSIS_ERROR", "message": str(e)}}, status=500)

    def download_and_extract(self, filename, tmpdir):
        """Download a gzipped file from Blob storage and extract it."""
        try:
            url = f"{BLOB_BASE_URL}/{filename}"
            gz_path = os.path.join(tmpdir, filename)
            dat_path = gz_path.replace('.gz', '')
            
            print(f"Downloading {url}...")
            urllib.request.urlretrieve(url, gz_path)
            
            # Extract gzip
            with gzip.open(gz_path, 'rb') as f_in:
                with open(dat_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            return dat_path
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return None

    def download_file(self, filename, tmpdir):
        """Download a file from Blob storage."""
        try:
            url = f"{BLOB_BASE_URL}/{filename}"
            file_path = os.path.join(tmpdir, filename)
            
            print(f"Downloading {url}...")
            urllib.request.urlretrieve(url, file_path)
            
            return file_path
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return None

    def send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
