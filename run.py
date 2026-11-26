"""Application launcher for OrangeHRM RPA Automation Dashboard."""
import argparse
import sys
import uvicorn
from config.settings import settings


def main():
    parser = argparse.ArgumentParser(description="Start OrangeHRM RPA Automation Dashboard Server")
    parser.add_argument("--host", default=settings.app_host, help=f"Host address (default: {settings.app_host})")
    parser.add_argument("--port", type=int, default=settings.app_port, help=f"Port number (default: {settings.app_port})")
    parser.add_argument("--reload", action="store_true", default=settings.debug, help="Enable auto-reload on code change")

    args = parser.parse_args()

    print("=" * 60)
    print("  OrangeHRM RPA Automation Dashboard")
    print(f"  Web Interface : http://localhost:{args.port}")
    print(f"  Interactive API Docs: http://localhost:{args.port}/docs")
    print(f"  Target Portal : {settings.orangehrm_url}")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
