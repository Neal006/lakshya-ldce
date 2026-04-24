import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Classifier Inference Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8002, help="Bind port (default: 8002)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    args = parser.parse_args()

    print(f"  Classifier — Inference Server")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    
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
