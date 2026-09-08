"""CLI interface for docsync."""

import sys
import argparse
from pathlib import Path
from docsync import ValidationError
from docsync.openapi import load_openapi_schema, extract_endpoints
from docsync.markdown import render_markdown
from docsync.merge import merge_docs, split_by_markers
from docsync.report import extract_endpoint_ids_from_markdown, compute_report, render_report


def main(argv=None):
    """Main entry point for the docsync CLI."""
    parser = argparse.ArgumentParser(
        prog="docsync",
        description="Generate and sync API documentation from OpenAPI schemas"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # sync subcommand
    sync_parser = subparsers.add_parser("sync", help="Sync API documentation")
    sync_parser.add_argument("--schema", required=True, help="Path to OpenAPI JSON schema file")
    sync_parser.add_argument("--docs", required=True, help="Path to existing documentation file (may not exist)")
    sync_parser.add_argument("--output", required=True, help="Path to output documentation file")
    sync_parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing output")
    sync_parser.add_argument("--format", choices=["json", "markdown"], default="markdown", 
                           help="Report output format (default: markdown)")
    sync_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "sync":
        return sync_command(args)
    
    return 1


def sync_command(args):
    """Execute the sync command."""
    try:
        # Load and validate OpenAPI schema
        if args.verbose:
            print(f"Loading schema from: {args.schema}", file=sys.stderr)
        
        schema = load_openapi_schema(args.schema)
        
        # Extract endpoints
        endpoints = extract_endpoints(schema)
        if args.verbose:
            print(f"Extracted {len(endpoints)} endpoints", file=sys.stderr)
        
        # Generate new markdown
        generated_block = render_markdown(endpoints)
        
        # Load existing docs if they exist
        existing_text = None
        old_ids = set()
        docs_path = Path(args.docs)
        
        if docs_path.exists():
            with open(docs_path, 'r', encoding='utf-8') as f:
                existing_text = f.read()
            
            # Try to extract old endpoint IDs for diff
            try:
                _, old_generated, _ = split_by_markers(existing_text)
                old_ids = extract_endpoint_ids_from_markdown(old_generated)
            except ValidationError:
                # No markers or malformed - that's ok for report purposes
                old_ids = set()
        
        # Compute report
        new_ids = extract_endpoint_ids_from_markdown(generated_block)
        report = compute_report(old_ids, new_ids)
        
        # Print report
        report_output = render_report(report, args.format)
        print(report_output)
        
        # Merge with existing content
        merged_content = merge_docs(existing_text, generated_block)
        
        # Write output (unless dry-run)
        if not args.dry_run:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            if args.verbose:
                print(f"Documentation written to: {args.output}", file=sys.stderr)
        else:
            if args.verbose:
                print("Dry-run mode: no files were modified", file=sys.stderr)
        
        return 0
        
    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
