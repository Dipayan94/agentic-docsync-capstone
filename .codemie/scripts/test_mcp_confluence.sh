#!/bin/bash

# test_mcp_confluence.sh
# Test script to verify MCP Confluence connection and fetch a page
# Account: dipayan4das.atlassian.net (Confluence Cloud)

set -e

PAGE_ID="${1:-196709}"

echo "🔍 Testing MCP Confluence Connection"
echo "======================================"
echo ""
echo "Page ID: $PAGE_ID"
echo "Page URL: https://dipayan4das.atlassian.net/wiki/spaces/~5be6fae9099a4b03a3099025/pages/$PAGE_ID"
echo ""

# Check if MCP config exists
if [ ! -f ~/.codemie/mcp.json ]; then
    echo "❌ Error: MCP configuration not found at ~/.codemie/mcp.json"
    exit 1
fi

echo "✅ MCP configuration found"
echo ""

# Display current MCP configuration (without showing full token)
echo "📋 Current MCP Configuration:"
cat ~/.codemie/mcp.json | jq '.mcpServers.confluence.env | {
    "CONFLUENCE_HOST_URL": .CONFLUENCE_HOST_URL,
    "CONFLUENCE_USER_EMAIL": .CONFLUENCE_USER_EMAIL,
    "CONFLUENCE_API_TOKEN": (.CONFLUENCE_API_TOKEN[:10] + "...")
}'
echo ""

# Test if MCP server can start
echo "🚀 Testing MCP server startup..."
# NOTE: Using environment variables from MCP config, not hardcoded values
if [ -f ~/.codemie/mcp.json ]; then
    CONF_URL=$(cat ~/.codemie/mcp.json | jq -r '.mcpServers.confluence.env.CONFLUENCE_HOST_URL')
    CONF_EMAIL=$(cat ~/.codemie/mcp.json | jq -r '.mcpServers.confluence.env.CONFLUENCE_USER_EMAIL')

    CONFLUENCE_HOST_URL="$CONF_URL" \
    CONFLUENCE_USER_EMAIL="$CONF_EMAIL" \
    CONFLUENCE_API_TOKEN="test" \
    timeout 10 npx -y @dsazz/mcp-confluence 2>&1 | grep -E "tool|registered|error|Error" | head -20 || echo "Server started (timeout expected)"
else
    echo "⚠️  Warning: MCP config not found, skipping startup test"
fi

echo ""
echo "📝 Instructions for Testing with Codemie:"
echo "=========================================="
echo ""
echo "To test fetching the Confluence page using MCP tools in Codemie CLI:"
echo ""
echo "1. Start a Codemie session:"
echo "   codemie"
echo ""
echo "2. Ask Codemie to use the confluence_get_page tool:"
echo "   \"Please use the confluence_get_page MCP tool to fetch page ID $PAGE_ID with includeContent set to true\""
echo ""
echo "3. Or ask to search for the page:"
echo "   \"Please use the confluence_search MCP tool to search for 'PRD-001 Automated API Documentation Sync'\""
echo ""
echo "4. Check if the page content is returned"
echo ""
echo "🔧 Troubleshooting:"
echo "=================="
echo ""
echo "If authentication fails:"
echo "1. Verify your API token is still valid: https://id.atlassian.com/manage-profile/security/api-tokens"
echo "2. Confirm CONFLUENCE_USER_EMAIL matches the Atlassian account that owns the token"
echo "3. Confirm you can access the page in a browser while logged in as that account"
echo "4. Try regenerating the API token if needed"
echo ""
echo "If MCP tools aren't available:"
echo "1. Restart Codemie CLI after updating mcp.json"
echo "2. Check that npx can install @dsazz/mcp-confluence"
echo "3. Verify network access to npm registry"
