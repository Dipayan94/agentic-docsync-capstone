"""Build and render the sync report (human-readable and JSON)."""
import json
from typing import List

from docsync.models import Endpoint, SyncReport


def build_report(endpoints: List[Endpoint]) -> SyncReport:
    """MVP report: every endpoint found is reported as 'added'.

    Deep diffing against prior state (to populate 'modified'/'removed') is out of scope.
    """
    added = [{"method": ep.method, "path": ep.path} for ep in endpoints]
    return SyncReport(added=added, modified=[], removed=[])


def format_report_markdown(report: SyncReport) -> str:
    lines = [
        "# DocSync Report",
        "",
        f"- Added: {len(report.added)}",
        f"- Modified: {len(report.modified)}",
        f"- Removed: {len(report.removed)}",
        "",
    ]
    if report.added:
        lines.append("**Endpoints added:**")
        lines.append("")
        for ep in report.added:
            lines.append(f"- {ep['method']} {ep['path']}")
        lines.append("")
    return "\n".join(lines)


def format_report_json(report: SyncReport) -> str:
    return json.dumps(
        {"added": report.added, "modified": report.modified, "removed": report.removed},
        indent=2,
    )
