#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Create Cleanroom Asset Hierarchy for Option B Dashboard
# Hierarchy: Building A → Floor 5 → Room R501/R502
#

echo "==========================================="
echo "Cleanroom Asset Provisioning (Option B)"
echo "==========================================="
echo ""

# Load configuration
if [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

REST_URL=${REST_URL:-http://167.99.64.71:8080}
REST_USERNAME=${REST_USERNAME:-tenant@thingsboard.org}
REST_PASSWORD=${REST_PASSWORD:-tenant}

echo "Configuration:"
echo "  Server: $REST_URL"
echo "  Username: $REST_USERNAME"
echo ""

# Check jq
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is not installed"
    exit 1
fi

# Login
echo "Step 1: Logging in..."
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
    | jq -r '.token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "✗ Login failed"
    exit 1
fi
echo "✓ Logged in"
echo ""

# Create Building A
echo "Step 2: Creating Building A..."
BUILDING_JSON=$(cat <<'EOF'
{
  "name": "Building A",
  "type": "Building",
  "label": "Hanoi Cleanroom Facility"
}
EOF
)

BUILDING_RESPONSE=$(curl -s -X POST "$REST_URL/api/asset" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$BUILDING_JSON")

BUILDING_ID=$(echo "$BUILDING_RESPONSE" | jq -r '.id.id')

if [ -z "$BUILDING_ID" ] || [ "$BUILDING_ID" = "null" ]; then
    echo "✗ Failed to create Building A"
    echo "Response: $BUILDING_RESPONSE"
    exit 1
fi
echo "✓ Building A created"
echo "  ID: $BUILDING_ID"
echo ""

# Create Floor 5
echo "Step 3: Creating Floor 5..."
FLOOR_JSON=$(cat <<EOF
{
  "name": "Floor 5",
  "type": "Floor",
  "label": "Floor 5 - Cleanroom Area"
}
EOF
)

FLOOR_RESPONSE=$(curl -s -X POST "$REST_URL/api/asset" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$FLOOR_JSON")

FLOOR_ID=$(echo "$FLOOR_RESPONSE" | jq -r '.id.id')

if [ -z "$FLOOR_ID" ] || [ "$FLOOR_ID" = "null" ]; then
    echo "✗ Failed to create Floor 5"
    echo "Response: $FLOOR_RESPONSE"
    exit 1
fi
echo "✓ Floor 5 created"
echo "  ID: $FLOOR_ID"
echo ""

# Create relation: Building A → Floor 5
echo "Step 4: Creating relation Building A → Floor 5..."
RELATION_JSON=$(cat <<EOF
{
  "from": {
    "entityType": "ASSET",
    "id": "$BUILDING_ID"

  "to": {
    "entityType": "ASSET",
    "id": "$FLOOR_ID"

  "type": "Contains",
  "typeGroup": "COMMON"
}
EOF
)

RELATION_RESPONSE=$(curl -s -X POST "$REST_URL/api/relation" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$RELATION_JSON")

echo "✓ Relation created: Building A → Floor 5"
echo ""

# Create Room R501
echo "Step 5: Creating Room R501 (ISO 5 Cleanroom)..."
ROOM501_JSON=$(cat <<'EOF'
{
  "name": "Room R501",
  "type": "Room",
  "label": "ISO 5 Cleanroom"
}
EOF
)

ROOM501_RESPONSE=$(curl -s -X POST "$REST_URL/api/asset" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$ROOM501_JSON")

ROOM501_ID=$(echo "$ROOM501_RESPONSE" | jq -r '.id.id')

if [ -z "$ROOM501_ID" ] || [ "$ROOM501_ID" = "null" ]; then
    echo "✗ Failed to create Room R501"
    echo "Response: $ROOM501_RESPONSE"
    exit 1
fi
echo "✓ Room R501 created"
echo "  ID: $ROOM501_ID"
echo ""

# Create relation: Floor 5 → Room R501
echo "Step 6: Creating relation Floor 5 → Room R501..."
RELATION501_JSON=$(cat <<EOF
{
  "from": {
    "entityType": "ASSET",
    "id": "$FLOOR_ID"

  "to": {
    "entityType": "ASSET",
    "id": "$ROOM501_ID"

  "type": "Contains",
  "typeGroup": "COMMON"
}
EOF
)

curl -s -X POST "$REST_URL/api/relation" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$RELATION501_JSON" > /dev/null

echo "✓ Relation created: Floor 5 → Room R501"
echo ""

# Create Room R502
echo "Step 7: Creating Room R502 (ISO 6 Cleanroom)..."
ROOM502_JSON=$(cat <<'EOF'
{
  "name": "Room R502",
  "type": "Room",
  "label": "ISO 6 Cleanroom"
}
EOF
)

ROOM502_RESPONSE=$(curl -s -X POST "$REST_URL/api/asset" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$ROOM502_JSON")

ROOM502_ID=$(echo "$ROOM502_RESPONSE" | jq -r '.id.id')

if [ -z "$ROOM502_ID" ] || [ "$ROOM502_ID" = "null" ]; then
    echo "✗ Failed to create Room R502"
    echo "Response: $ROOM502_RESPONSE"
    exit 1
fi
echo "✓ Room R502 created"
echo "  ID: $ROOM502_ID"
echo ""

# Create relation: Floor 5 → Room R502
echo "Step 8: Creating relation Floor 5 → Room R502..."
RELATION502_JSON=$(cat <<EOF
{
  "from": {
    "entityType": "ASSET",
    "id": "$FLOOR_ID"

  "to": {
    "entityType": "ASSET",
    "id": "$ROOM502_ID"

  "type": "Contains",
  "typeGroup": "COMMON"
}
EOF
)

curl -s -X POST "$REST_URL/api/relation" \
    -H "Content-Type: application/json" \
    -H "X-Authorization: Bearer $TOKEN" \
    -d "$RELATION502_JSON" > /dev/null

echo "✓ Relation created: Floor 5 → Room R502"
echo ""

# Save IDs for device relation script
cat > /tmp/cleanroom_assets.env << EOF
BUILDING_ID=$BUILDING_ID
FLOOR_ID=$FLOOR_ID
ROOM501_ID=$ROOM501_ID
ROOM502_ID=$ROOM502_ID
EOF

echo "==========================================="
echo "Asset Hierarchy Created Successfully!"
echo "==========================================="
echo ""
echo "Hierarchy:"
echo "  Building A ($BUILDING_ID)"
echo "  └─ Floor 5 ($FLOOR_ID)"
echo "      ├─ Room R501 ($ROOM501_ID) - ISO 5"
echo "      └─ Room R502 ($ROOM502_ID) - ISO 6"
echo ""
echo "Asset IDs saved to: /tmp/cleanroom_assets.env"
echo ""
echo "Next step: Run ./create-device-relations.sh to link FFU devices"
echo "==========================================="
