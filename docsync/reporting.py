"""
Reporting module for sync operations.
"""
import json
from datetime import datetime
from typing import List

from docsync.models import Endpoint, SyncReport


def create_report(endpoints: List[Endpoint]) -> SyncReport:
    """
    Create a sync report from endpoints.
    
    Args:
        endpoints: List of processed endpoints
        
    Returns:
        SyncReport object
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    endpoints_list = [
        {"method": ep.method, "path": ep.path}
        for ep in endpoints
    ]
    
    return SyncReport(
        timestamp=timestamp,
        endpoints_total=len(endpoints),
        endpoints=endpoints_list
    )


def format_report_markdown(report: SyncReport) -> str:
    """
    Format sync report as human-readable markdown.
    
    Args:
        report: SyncReport object
        
    Returns:
        Markdown-formatted report string
    """
    lines = []
    lines.append("# DocSync Report")
    lines.append("")
    lines.append(f"**Timestamp:** {report.timestamp}")
    lines.append(f"**Total Endpoints:** {report.endpoints_total}")
    lines.append("")
    
    if report.endpoints:
        lines.append("**Endpoints:**")
        lines.append("")
        for ep in report.endpoints:
            lines.append(f"- {ep['method']} {ep['path']}")
        lines.append("")
    
    return "\n".join(lines)


def format_report_json(report: SyncReport) -> str:
    """
    Format sync report as JSON.
    
    Args:
        report: SyncReport object
        
    Returns:
        JSON-formatted report string
    """
    report_dict = {
        "timestamp": report.timestamp,
        "endpoints_total": report.endpoints_total,
        "endpoints": report.endpoints
    }
    return json.dumps(report_dict, indent=2)
