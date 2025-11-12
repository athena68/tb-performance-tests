#!/bin/bash

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

REST_URL=${REST_URL:-"http://localhost:8080"}
REST_USERNAME=${REST_USERNAME:-""}
REST_PASSWORD=${REST_PASSWORD:-""}

if [[ -z "$REST_USERNAME" || -z "$REST_PASSWORD" ]]; then
    echo "❌ Error: REST_USERNAME and REST_PASSWORD must be set in environment or .env file"
    exit 1
fi

# Login
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | jq -r '.token')

# Get dashboard
DASHBOARD_ID="0dd5a410-ab25-11f0-af4d-97d7c19de825"
echo "Fetching dashboard $DASHBOARD_ID..."
echo ""

DASHBOARD=$(curl -s -X GET "$REST_URL/api/dashboard/$DASHBOARD_ID" \
    -H "X-Authorization: Bearer $TOKEN")

# Save to file for inspection
echo "$DASHBOARD" | jq '.' > /tmp/dashboard_check.json

echo "Dashboard retrieved and saved to /tmp/dashboard_check.json"
echo ""
echo "Dashboard title: $(echo "$DASHBOARD" | jq -r '.title')"
echo "Widget count: $(echo "$DASHBOARD" | jq '.configuration.widgets | length')"
echo "State count: $(echo "$DASHBOARD" | jq '.configuration.states | length')"
echo ""

# Check for errors
ERROR=$(echo "$DASHBOARD" | jq -r '.message // empty')
if [ -n "$ERROR" ]; then
    echo "ERROR: $ERROR"
    echo "$DASHBOARD" | jq '.'
fi
