"""
run_server.py — Launch the inference server.

Usage:
    python run_server.py                  # default: 0.0.0.0:8000
    python run_server.py --port 5000      # custom port
    python run_server.py --host 127.0.0.1 # localhost only
"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Complaint Classifier Inference Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  Complaint Classifier — Inference Server")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"{'='*50}\n")

    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1,  # single worker — GPU models can't be forked
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
