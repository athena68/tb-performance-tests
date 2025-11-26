#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


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

echo "Checking device types for DW devices..."
echo ""

# Get all devices
ALL_DEVICES=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

# Check first 5 DW devices
echo "Sample of DW devices:"
echo "$ALL_DEVICES" | jq -r '.data[] | select(.name | startswith("DW")) | "\(.name) - Type: \(.type)"' | head -5

echo ""
echo "Checking device type filter..."

# Test deviceType filter
FILTERED=$(curl -s -X GET "$REST_URL/api/tenant/devices?deviceType=EBMPAPST_FFU&pageSize=10&page=0" \
    -H "X-Authorization: Bearer $TOKEN")

COUNT=$(echo "$FILTERED" | jq '.data | length')

echo "Devices matching type 'EBMPAPST_FFU': $COUNT"

if [ "$COUNT" -eq 0 ]; then
    echo ""
    echo "No devices found with type EBMPAPST_FFU!"
    echo ""
    echo "Let's check what types exist:"
    echo "$ALL_DEVICES" | jq -r '.data[].type' | sort -u
fi
