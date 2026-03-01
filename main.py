import argparse
import os
import json
from sherlock.analysis.runner import run_analysis
from sherlock.report.generator import generate_markdown_report

def main():
    parser = argparse.ArgumentParser(description="Sherlock: Bitcoin Chain Analysis (Python)")
    parser.add_argument("--block", nargs=3, metavar=("blk.dat", "rev.dat", "xor.dat"), help="Run CLI analysis mode")
    parser.add_argument("--web", action="store_true", help="Run web server mode")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 3000)), help="Web server port")
    
    args = parser.parse_args()
    
    if args.block:
        blk, rev, xor = args.block
        report, stem = run_analysis(blk, rev, xor)
        
        os.makedirs("out", exist_ok=True)
        with open(f"out/{stem}.json", "w") as f:
            json.dump(report, f, indent=2)
        generate_markdown_report(report, stem)
        print(f"Reports saved to out/{stem}.json and out/{stem}.md")
        
    elif args.web:
        print(f"Starting web server on port {args.port}...")
        # (Web server implementation would go here)
        from sherlock.web.server import start_server
        start_server(args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
