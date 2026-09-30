"""argparse-based CLI for DocSync, returning the locked exit-code contract."""
import argparse
import sys

from docsync.doc_writer import atomic_write, merge_with_markers, read_existing_docs
from docsync.exceptions import DocSyncError, ValidationError
from docsync.markdown_generator import generate_markdown
from docsync.openapi_parser import load_openapi_schema, parse_endpoints
from docsync.report import build_report, format_report_json, format_report_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docsync", description="Sync markdown API docs from an OpenAPI schema")
    subparsers = parser.add_subparsers(dest="command")

    sync_parser = subparsers.add_parser("sync", help="Generate/update docs from an OpenAPI schema")
    sync_parser.add_argument("--schema", required=True, help="Path to OpenAPI 3.x JSON schema file")
    sync_parser.add_argument("--docs", required=True, help="Path to existing docs to merge into")
    sync_parser.add_argument("--output", required=True, help="Path to write the resulting docs to")
    sync_parser.add_argument("--dry-run", action="store_true", help="Do not write the output file")
    sync_parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="Report output format")
    sync_parser.add_argument("--verbose", action="store_true", help="Print extra progress logging")

    return parser


def handle_sync(args: argparse.Namespace) -> int:
    try:
        if args.verbose:
            print(f"Loading schema: {args.schema}", file=sys.stderr)
        schema = load_openapi_schema(args.schema)
        endpoints = parse_endpoints(schema)

        if args.verbose:
            print(f"Found {len(endpoints)} endpoint(s)", file=sys.stderr)

        generated_block = generate_markdown(endpoints)
        existing_content = read_existing_docs(args.docs)
        final_content = merge_with_markers(existing_content, generated_block)

        if args.dry_run:
            if args.verbose:
                print("Dry-run: skipping write", file=sys.stderr)
        else:
            if args.verbose:
                print(f"Writing output: {args.output}", file=sys.stderr)
            atomic_write(args.output, final_content)

        report = build_report(endpoints)
        if args.format == "json":
            print(format_report_json(report))
        else:
            print(format_report_markdown(report))

        return 0

    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 2
    except DocSyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sync":
        return handle_sync(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
