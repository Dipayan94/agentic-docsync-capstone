"""Command-line orchestration for the offline documentation sync workflow."""

import argparse
import logging
import sys
import traceback
from pathlib import Path
from typing import List, Optional, Sequence

from .diff_engine import detect_changes
from .generator import format_report, render_document
from .markdown_parser import parse_document
from .models import ValidationError
from .parser import parse_openapi
from .utils import safe_write_file


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def build_parser() -> argparse.ArgumentParser:
    """Build the supported CLI argument parser."""
    parser = _ArgumentParser(prog="docsync", description="Synchronize local API Markdown from OpenAPI JSON")
    commands = parser.add_subparsers(dest="command", required=True)
    sync = commands.add_parser("sync", help="Synchronize an existing Markdown document")
    sync.add_argument("--schema", required=True, help="OpenAPI 3.0/3.1 JSON input")
    sync.add_argument("--docs", required=True, help="Existing Markdown source document")
    sync.add_argument("--output", required=True, help="Synchronized Markdown destination")
    sync.add_argument("--dry-run", action="store_true", help="Report changes without writing output")
    sync.add_argument("--format", choices=("json", "markdown"), default="markdown",
                      help="Report format written to stdout (default: markdown)")
    sync.add_argument("--verbose", action="store_true", help="Enable detailed diagnostics on stderr")
    return parser


def sync_command(args: argparse.Namespace) -> int:
    """Run the sync workflow, writing only a fully rendered document atomically."""
    schema_path = Path(args.schema)
    output_path = Path(args.output)
    if schema_path.resolve() == output_path.resolve():
        raise ValidationError("Output path must not overwrite the read-only OpenAPI schema")

    schema = parse_openapi(args.schema)
    document = parse_document(args.docs)
    changes = detect_changes(document, schema.endpoints)
    markdown = render_document(document, schema.endpoints, changes)
    report = format_report(changes, args.format, {
        "schema_title": schema.title,
        "schema_version": schema.version,
        "openapi_version": schema.openapi_version,
    })

    for warning in document.parse_warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not args.dry_run:
        safe_write_file(args.output, markdown)
    if args.verbose:
        logging.getLogger(__name__).info(
            "Sync completed: %d added, %d modified, %d removed%s",
            len(changes.added), len(changes.modified), len(changes.removed),
            " (dry run)" if args.dry_run else "",
        )
    sys.stdout.write(report)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and return the documented success/operational/validation code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except ValueError as error:
        parser.print_usage(sys.stderr)
        print(f"docsync: error: {error}", file=sys.stderr)
        return 2
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
    try:
        return sync_command(args)
    except ValidationError as error:
        print(f"docsync: validation error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"docsync: I/O error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"docsync: error: {error}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
