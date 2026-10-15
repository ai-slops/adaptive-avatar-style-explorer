import argparse
import webbrowser

import uvicorn

from .main import create_app


def main():
    parser = argparse.ArgumentParser(description="Run the local Avatar Style Explorer")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", default=".data")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--provider", choices=("codex", "siwc"), default="codex")
    args = parser.parse_args()
    origin = f"http://127.0.0.1:{args.port}"
    app = create_app(
        args.data_dir,
        origin,
        execution_mode="codex_local"
        if args.provider == "codex"
        else "community_prompt_only",
    )
    url = f"{origin}/#launch={app.state.bootstrap_secret}"
    print(f"Open the local launch link: {url}", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
