"""
Command-line interface for docsync.

Commands:
  docsync parse <schema-file>                - Parse and display schema info
  docsync generate <schema-file> <output-dir> - Generate markdown docs
  docsync diff <old-schema> <new-schema>     - Detect schema changes
  docsync sync <schema-file> <docs-dir>      - Full workflow: parse → diff → generate → cache
  docsync validate <docs-dir>                - Validate documentation completeness
"""

import argparse
import sys
from pathlib import Path
from docsync.parser import parse_openapi
from docsync.generator import generate_markdown
from docsync.diff_engine import DiffEngine
from docsync.utils import get_logger


logger = get_logger(__name__)


class DocsyncCLI:
    """Command-line interface for docsync."""

    @staticmethod
    def parse_command(args) -> None:
        """Parse and display schema info."""
        try:
            schema = parse_openapi(args.schema_file)
            print(f"\n✓ Schema: {schema}")
            print(f"  Endpoints: {len(schema.endpoints)}")
            for ep in schema.endpoints[:5]:  # Show first 5
                print(f"    - {ep}")
            if len(schema.endpoints) > 5:
                print(f"    ... and {len(schema.endpoints) - 5} more")
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            sys.exit(1)

    @staticmethod
    def generate_command(args) -> None:
        """Generate markdown documentation."""
        try:
            schema = parse_openapi(args.schema_file)
            generate_markdown(schema, args.output_dir)
            print(f"\n✓ Generated {len(schema.endpoints)} endpoint docs in {args.output_dir}")
        except Exception as e:
            logger.error(f"Generate failed: {e}")
            sys.exit(1)

    @staticmethod
    def diff_command(args) -> None:
        """Detect schema changes."""
        try:
            old_schema = parse_openapi(args.old_schema)
            new_schema = parse_openapi(args.new_schema)
            changes = DiffEngine.compute_diff(old_schema, new_schema)
            
            print(f"\n✓ Detected {len(changes)} changes:")
            for change in changes:
                print(f"  - {change}")
        except Exception as e:
            logger.error(f"Diff failed: {e}")
            sys.exit(1)

    @staticmethod
    def sync_command(args) -> None:
        """Full sync workflow: parse → diff → generate → cache."""
        try:
            print(f"\n→ Parsing schema...")
            new_schema = parse_openapi(args.schema_file)
            
            print(f"→ Loading previous schema...")
            old_schema = DiffEngine.load_schema_cache("docs/schema_cache.json")
            
            print(f"→ Computing diff...")
            changes = DiffEngine.compute_diff(old_schema, new_schema)
            
            print(f"→ Generating markdown...")
            generate_markdown(new_schema, args.docs_dir)
            
            print(f"→ Saving cache...")
            DiffEngine.save_schema_cache(new_schema, "docs/schema_cache.json")
            
            print(f"\n✓ Sync complete!")
            print(f"  New schema: {new_schema}")
            print(f"  Changes detected: {len(changes)}")
            print(f"  Documentation: {args.docs_dir}")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            sys.exit(1)

    @staticmethod
    def validate_command(args) -> None:
        """Validate documentation completeness."""
        try:
            docs_path = Path(args.docs_dir)
            if not docs_path.exists():
                print(f"✗ Documentation directory not found: {args.docs_dir}")
                sys.exit(1)
            
            md_files = list(docs_path.glob("*.md"))
            if not md_files:
                print(f"✗ No markdown files found in {args.docs_dir}")
                sys.exit(1)
            
            print(f"\n✓ Documentation valid!")
            print(f"  Directory: {args.docs_dir}")
            print(f"  Files: {len(md_files)}")
            for md_file in sorted(md_files)[:5]:
                print(f"    - {md_file.name}")
            if len(md_files) > 5:
                print(f"    ... and {len(md_files) - 5} more")
        except Exception as e:
            logger.error(f"Validate failed: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="docsync",
        description="Automated OpenAPI documentation sync"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse and display schema info")
    parse_parser.add_argument("schema_file", help="Path to openapi.json")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate markdown docs")
    gen_parser.add_argument("schema_file", help="Path to openapi.json")
    gen_parser.add_argument("output_dir", help="Output directory for markdown")

    # diff command
    diff_parser = subparsers.add_parser("diff", help="Detect schema changes")
    diff_parser.add_argument("old_schema", help="Path to previous openapi.json")
    diff_parser.add_argument("new_schema", help="Path to current openapi.json")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Full sync workflow")
    sync_parser.add_argument("schema_file", help="Path to openapi.json")
    sync_parser.add_argument("docs_dir", help="Docs directory")

    # validate command
    val_parser = subparsers.add_parser("validate", help="Validate documentation")
    val_parser.add_argument("docs_dir", help="Documentation directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handler
    if args.command == "parse":
        DocsyncCLI.parse_command(args)
    elif args.command == "generate":
        DocsyncCLI.generate_command(args)
    elif args.command == "diff":
        DocsyncCLI.diff_command(args)
    elif args.command == "sync":
        DocsyncCLI.sync_command(args)
    elif args.command == "validate":
        DocsyncCLI.validate_command(args)


if __name__ == "__main__":
    main()
