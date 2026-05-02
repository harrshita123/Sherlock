from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        files = []
        out_dir = os.path.join(os.path.dirname(__file__), '..', 'public', 'out')
        if os.path.exists(out_dir):
            files = [f.replace(".json", "") for f in os.listdir(out_dir) if f.endswith(".json")]
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"files": sorted(files)}).encode())
        return
