import http.server
import socketserver
import os
import json
import traceback
import threading
from ..analysis.runner import run_analysis
from ..report.generator import generate_markdown_report

class SherlockHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type, Accept')
        self.send_header('Connection', 'keep-alive')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0].rstrip('/')
        if not path: path = "/"
        
        if path == "/api/health":
            self.send_json({"ok": True})
        elif path == "/api/files":
            files = []
            if os.path.exists("out"):
                files = [f.replace(".json", "") for f in os.listdir("out") if f.endswith(".json")]
            self.send_json({"files": sorted(files)})
        elif path == "/" or path == "/index.html":
            self.serve_file(os.path.join("sherlock", "web", "static", "index.html"), "text/html")
        elif path.startswith("/out"):
            filename = path[4:].lstrip('/')
            ctype = "application/json" if filename.endswith(".json") else "text/markdown"
            self.serve_file(os.path.join("out", filename), ctype)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path.split('?')[0].rstrip('/') == "/api/analyze":
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
                    # Fallback to auto-match if not provided
                    rev_file = blk_file.replace("blk", "rev")

                # Map to fixtures
                blk_path = os.path.join("fixtures", os.path.basename(blk_file))
                rev_path = os.path.join("fixtures", os.path.basename(rev_file))
                xor_path = os.path.join("fixtures", os.path.basename(xor_file))

                # Verify fixtures exist
                if not os.path.exists(blk_path):
                    self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"Block file {blk_file} not found. Please ensure it is in the fixtures folder."}}, status=404)
                    return
                if rev_file and not os.path.exists(rev_path):
                    self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"Undo file {rev_file} not found. Please ensure it is in the fixtures folder."}}, status=404)
                    return
                if not os.path.exists(xor_path):
                    self.send_json({"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"XOR key {xor_file} not found. Please ensure it is in the fixtures folder."}}, status=404)
                    return

                stem = os.path.basename(blk_file).replace(".gz", "").replace(".dat", "")
                json_path = os.path.join("out", f"{stem}.json")

                if os.path.exists(json_path):
                    print(f"[POST] Serving cached report for {blk_file}...")
                    with open(json_path, 'r') as f:
                        report = json.load(f)
                    self.send_json(report)
                    return

                print(f"[POST] Analyzing {blk_file} (no cache found)...")

                print(f"[POST] Analyzing {blk_file}...")
                report, stem = run_analysis(blk_path, rev_path, xor_path)
                generate_markdown_report(report, stem)
                
                print(f"[POST] Success: {stem}")
                self.send_json(report)
            except Exception as e:
                print(f"!!! SERVER ERROR: {traceback.format_exc()}")
                self.send_json({"ok": False, "error": str(e)}, status=500)
        else:
            self.send_json({"ok": False, "error": "Not Found"}, status=404)

    def send_json(self, data, status=200):
        try:
            body = json.dumps(data).encode('utf-8')
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            print(f"Failed to send JSON: {e}")

    def serve_file(self, path, content_type):
        if os.path.exists(path):
            with open(path, "rb") as f:
                content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        else:
            self.send_error(404)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def start_server(port):
    with ThreadedHTTPServer(("0.0.0.0", port), SherlockHandler) as httpd:
        print(f"Python Sherlock Server running at http://127.0.0.1:{port}")
        httpd.serve_forever()
