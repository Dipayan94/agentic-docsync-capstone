"""
CLI entrypoint for DocsSync.
"""
import argparse
import sys
from pathlib import Path

from docsync.exceptions import DocSyncError, ValidationError
from docsync.openapi_parser import load_openapi_schema, parse_endpoints
from docsync.markdown_generator import generate_markdown
from docsync.markers import read_existing_docs, merge_with_markers
from docsync.reporting import create_report, format_report_markdown, format_report_json


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="docsync",
        description="Generate/update markdown API docs from OpenAPI JSON files"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # sync subcommand
    sync_parser = subparsers.add_parser("sync", help="Sync documentation from OpenAPI schema")
    sync_parser.add_argument("--schema", required=True, help="Path to OpenAPI JSON schema file")
    sync_parser.add_argument("--docs", required=True, help="Path to existing documentation file")
    sync_parser.add_argument("--output", required=True, help="Path to output documentation file")
    sync_parser.add_argument("--dry-run", action="store_true", help="Don't write output file")
    sync_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    sync_parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                           help="Report output format (default: markdown)")
    
    args = parser.parse_args()
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "sync":
        return handle_sync(args)
    
    return 1


def handle_sync(args):
    """
    Handle the sync command.
    
    Returns:
        Exit code (0=success, 1=operational error, 2=validation failure)
    """
    try:
        # Validate format argument
        if args.format not in ["markdown", "json"]:
            raise ValidationError(f"Invalid format '{args.format}'. Must be 'markdown' or 'json'.")
        
        # Load and parse OpenAPI schema
        if args.verbose:
            print(f"Loading OpenAPI schema from {args.schema}...", file=sys.stderr)
        
        schema = load_openapi_schema(args.schema)
        endpoints = parse_endpoints(schema)
        
        if args.verbose:
            print(f"Found {len(endpoints)} endpoints", file=sys.stderr)
        
        # Generate markdown
        if args.verbose:
            print("Generating markdown documentation...", file=sys.stderr)
        
        generated_md = generate_markdown(endpoints)
        
        # Read existing docs
        existing_content = read_existing_docs(args.docs)
        
        # Merge with markers
        if args.verbose:
            print("Merging with existing documentation...", file=sys.stderr)
        
        final_content = merge_with_markers(existing_content, generated_md)
        
        # Write output (unless dry-run)
        if not args.dry_run:
            if args.verbose:
                print(f"Writing output to {args.output}...", file=sys.stderr)
            
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
        else:
            if args.verbose:
                print("Dry-run mode: skipping output write", file=sys.stderr)
        
        # Generate and print report
        report = create_report(endpoints)
        
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
    
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
