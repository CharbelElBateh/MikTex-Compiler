import argparse
import sys

from src.app import Application


def main() -> int:
    parser = argparse.ArgumentParser(description="MIKTEX-Compiler - A LaTeX IDE for MiKTeX")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("file", nargs="?", help="File or project to open")
    args = parser.parse_args()

    app = Application(verbose=args.verbose)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
