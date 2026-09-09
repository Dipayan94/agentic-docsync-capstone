"""
Entry point for running docsync as a module: python -m docsync
"""
import sys
from docsync.cli import main

if __name__ == "__main__":
    sys.exit(main())
