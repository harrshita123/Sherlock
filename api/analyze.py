from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import traceback

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sherlock.analysis.runner import run_analysis
from sherlock.report.generator import generate_markdown_report

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

            # Get base directory
            base_dir = os.path.join(os.path.dirname(__file__), '..')
            
            # Strict ID matching validation
            blk_id = "".join(filter(str.isdigit, os.path.basename(blk_file)))
            if rev_file:
                rev_id = "".join(filter(str.isdigit, os.path.basename(rev_file)))
                if blk_id != rev_id:
                    self.send_json({"ok": False, "error": {"code": "FILE_MISMATCH", "message": f"Block ID ({blk_id}) does not match Undo ID ({rev_id})."}}, status=400)
                    return
            else:
                rev_file = blk_file.replace("blk", "rev")

            # Map to fixtures (check public/fixtures first, then root fixtures)
            blk_basename = os.path.basename(blk_file)
            rev_basename = os.path.basename(rev_file)
            xor_basename = os.path.basename(xor_file)
            
            # Try public/fixtures first (for Vercel deployment), then root fixtures
            public_fixtures = os.path.join(base_dir, "public", "fixtures")
            root_fixtures = os.path.join(base_dir, "fixtures")
            
            if os.path.exists(os.path.join(public_fixtures, blk_basename)) or os.path.exists(os.path.join(public_fixtures, blk_basename + ".gz")):
                fixtures_dir = public_fixtures
            else:
                fixtures_dir = root_fixtures
            
            blk_path = os.path.join(fixtures_dir, blk_basename)
            rev_path = os.path.join(fixtures_dir, rev_basename)
            xor_path = os.path.join(fixtures_dir, xor_basename)

            # Verify fixtures exist
            if not os.path.exists(blk_path):
                self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"Block file {blk_file} not found."}}, status=404)
                return
            if rev_file and not os.path.exists(rev_path):
                self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"Undo file {rev_file} not found."}}, status=404)
                return
            if not os.path.exists(xor_path):
                self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"XOR key {xor_file} not found."}}, status=404)
                return

            stem = os.path.basename(blk_file).replace(".gz", "").replace(".dat", "")
            json_path = os.path.join(base_dir, "out", f"{stem}.json")

            # Check cache
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    report = json.load(f)
                self.send_json(report)
                return

            # Run analysis
            report, stem = run_analysis(blk_path, rev_path, xor_path)
            generate_markdown_report(report, stem)
            
            self.send_json(report)
        except Exception as e:
            print(f"Error: {traceback.format_exc()}")
            self.send_json({"ok": False, "error": str(e)}, status=500)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
