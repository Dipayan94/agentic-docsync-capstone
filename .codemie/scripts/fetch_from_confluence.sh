#!/bin/bash

# fetch_from_confluence.sh
# Helper script to fetch approved_packet.md content from Confluence Cloud
# (dipayan4das.atlassian.net) — page body is the source of truth, there is
# no separate attachment to download.

set -e

# Check if required environment variables are set
# These match the MCP server config in ~/.codemie/mcp.json
if [ -z "$CONFLUENCE_USER_EMAIL" ] || [ -z "$CONFLUENCE_API_TOKEN" ]; then
    echo "❌ Error: CONFLUENCE_USER_EMAIL and/or CONFLUENCE_API_TOKEN environment variables are not set"
    echo "Please set them with:"
    echo "  export CONFLUENCE_USER_EMAIL='your-email@example.com'"
    echo "  export CONFLUENCE_API_TOKEN='your-atlassian-api-token'"
    echo "(Same credentials as ~/.codemie/mcp.json mcpServers.confluence.env)"
    exit 1
fi

if [ -z "$1" ]; then
    echo "❌ Error: Confluence page URL is required"
    echo "Usage: $0 <confluence-page-url>"
    echo "Example: $0 'https://dipayan4das.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title'"
    exit 1
fi

CONFLUENCE_URL="$1"
OUTPUT_DIR=".codemie/approved_docs"
OUTPUT_FILE="${OUTPUT_DIR}/approved_packet.md"

# Extract domain and page ID from URL
# Example URL: https://dipayan4das.atlassian.net/wiki/spaces/SPACE/pages/196709/Page+Title
if [[ $CONFLUENCE_URL =~ https://([^/]+)/wiki/.*/pages/([0-9]+) ]]; then
    CONFLUENCE_DOMAIN="${BASH_REMATCH[1]}"
    PAGE_ID="${BASH_REMATCH[2]}"
else
    echo "❌ Error: Invalid Confluence Cloud URL format"
    echo "Expected format: https://dipayan4das.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title"
    exit 1
fi

echo "📄 Fetching approved_packet.md content from Confluence..."
echo "   Domain: $CONFLUENCE_DOMAIN"
echo "   Page ID: $PAGE_ID"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Confluence Cloud REST API v2 (Basic auth: email + API token)
API_URL="https://${CONFLUENCE_DOMAIN}/wiki/api/v2/pages/${PAGE_ID}?body-format=storage"
echo "🔍 Fetching page content..."
echo "   API URL: $API_URL"

HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/confluence_page_response.json \
                 -u "${CONFLUENCE_USER_EMAIL}:${CONFLUENCE_API_TOKEN}" \
                 -H "Accept: application/json" \
                 "$API_URL")

if [ "$HTTP_CODE" -ne 200 ]; then
    echo "❌ Error: Failed to fetch page (HTTP $HTTP_CODE). Please check your URL, email, and API token."
    cat /tmp/confluence_page_response.json | jq '.' 2>/dev/null || cat /tmp/confluence_page_response.json
    exit 1
fi

# The page body (storage/XHTML format) IS the approved packet content —
# there is no separate attachment to look for.
jq -r '.body.storage.value' /tmp/confluence_page_response.json > /tmp/confluence_content.html

# Simple conversion: strip HTML/storage-format tags (basic approach)
# For production, consider using pandoc or html2text
sed 's/<[^>]*>//g' /tmp/confluence_content.html > "$OUTPUT_FILE"

echo "✅ Extracted markdown content to $OUTPUT_FILE"
echo ""
echo "📊 File info:"
ls -lh "$OUTPUT_FILE"
echo ""
echo "📝 Preview (first 10 lines):"
head -n 10 "$OUTPUT_FILE"
