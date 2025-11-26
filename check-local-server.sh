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

echo "=== Quick Local ThingsBoard Server Check ==="
echo ""

echo "1. Testing if port 8080 is open..."
if timeout 3 bash -c "echo > /dev/tcp/localhost/8080" 2>/dev/null; then
  echo "✓ Port 8080 is OPEN"
else
  echo "✗ Port 8080 is CLOSED"
  exit 1
fi
echo ""

echo "2. Testing HTTP endpoint (5 attempts)..."
SUCCESS=0
for i in {1..5}; do
  echo -n "  Attempt $i: "
  RESPONSE=$(curl -s -m 3 -w "%{http_code}|%{time_total}" -o /dev/null http://localhost:8080/api/auth/login 2>/dev/null)
  HTTP_CODE=$(echo $RESPONSE | cut -d'|' -f1)
  TIME=$(echo $RESPONSE | cut -d'|' -f2)
  if [ "$HTTP_CODE" != "000" ]; then
    echo "✓ HTTP $HTTP_CODE in ${TIME}s"
    SUCCESS=$((SUCCESS + 1))
  else
    echo "✗ FAILED"
  fi
  sleep 0.5
done
echo "  Success rate: $SUCCESS/5"
echo ""

echo "3. Testing actual login..."
LOGIN_RESPONSE=$(curl -s -m 10 -w "\n%{http_code}" \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}' \
  http://localhost:8080/api/auth/login 2>/dev/null)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Login successful - Local ThingsBoard server is ready!"
  echo ""
  echo "✅ All checks passed - ready to run provision script"
else
  echo "✗ Login failed with HTTP code: $HTTP_CODE"
  echo "Response: $RESPONSE_BODY"
  exit 1
fi
