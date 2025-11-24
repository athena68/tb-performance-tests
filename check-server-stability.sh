#!/bin/bash
# ThingsBoard Server Stability Check Script

SERVER_IP="167.172.75.1"
SERVER_PORT="8080"
SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"

echo "============================================"
echo "ThingsBoard Server Stability Check"
echo "Server: ${SERVER_URL}"
echo "============================================"
echo ""

# 1. Check basic network connectivity
echo "[1/6] Testing basic network connectivity (ping)..."
if ping -c 5 -W 2 ${SERVER_IP} > /dev/null 2>&1; then
    echo "✓ Server is reachable via ping"
    ping -c 5 ${SERVER_IP} | grep -E "packets transmitted|rtt"
else
    echo "✗ Server is NOT reachable via ping"
    echo "  This indicates a fundamental network connectivity issue"
fi
echo ""

# 2. Check if port is open
echo "[2/6] Testing if port ${SERVER_PORT} is open..."
if timeout 5 bash -c "echo > /dev/tcp/${SERVER_IP}/${SERVER_PORT}" 2>/dev/null; then
    echo "✓ Port ${SERVER_PORT} is OPEN"
else
    echo "✗ Port ${SERVER_PORT} is CLOSED or FILTERED"
    echo "  The server might be down or firewall is blocking the connection"
fi
echo ""

# 3. Test HTTP endpoint response time (10 attempts)
echo "[3/6] Testing HTTP endpoint response time (10 attempts)..."
SUCCESS=0
FAIL=0
TOTAL_TIME=0

for i in {1..10}; do
    START=$(date +%s%N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 ${SERVER_URL}/api/auth/login 2>/dev/null)
    EXIT_CODE=$?
    END=$(date +%s%N)

    DURATION=$(( (END - START) / 1000000 )) # Convert to milliseconds

    if [ $EXIT_CODE -eq 0 ] && [ "$HTTP_CODE" != "000" ]; then
        echo "  Attempt $i: ✓ Response ${HTTP_CODE} in ${DURATION}ms"
        SUCCESS=$((SUCCESS + 1))
        TOTAL_TIME=$((TOTAL_TIME + DURATION))
    else
        echo "  Attempt $i: ✗ FAILED (timeout or connection refused)"
        FAIL=$((FAIL + 1))
    fi
    sleep 1
done

echo ""
echo "Results:"
echo "  Success: ${SUCCESS}/10 ($(( SUCCESS * 10 ))%)"
echo "  Failed:  ${FAIL}/10 ($(( FAIL * 10 ))%)"
if [ $SUCCESS -gt 0 ]; then
    AVG_TIME=$((TOTAL_TIME / SUCCESS))
    echo "  Average response time: ${AVG_TIME}ms"
fi
echo ""

# 4. Check network route and latency
echo "[4/6] Checking network route to server..."
echo "  (showing first 10 hops)"
traceroute -m 10 -w 2 ${SERVER_IP} 2>/dev/null | head -15 || echo "  traceroute not available"
echo ""

# 5. Test continuous connection stability (30 seconds)
echo "[5/6] Testing continuous connection stability (30 seconds)..."
echo "  Making rapid requests to detect intermittent failures..."
STABLE_SUCCESS=0
STABLE_FAIL=0

for i in {1..15}; do
    if timeout 3 curl -s -o /dev/null ${SERVER_URL}/api/auth/login 2>/dev/null; then
        echo -n "✓"
        STABLE_SUCCESS=$((STABLE_SUCCESS + 1))
    else
        echo -n "✗"
        STABLE_FAIL=$((STABLE_FAIL + 1))
    fi
    sleep 2
done

echo ""
echo "  Stability: ${STABLE_SUCCESS}/15 successful ($(( STABLE_SUCCESS * 100 / 15 ))%)"
echo ""

# 6. Test actual login to ThingsBoard
echo "[6/6] Testing actual ThingsBoard login..."
LOGIN_RESPONSE=$(curl -s -m 10 -w "\n%{http_code}" \
    -H "Content-Type: application/json" \
    -d '{"username":"tenant@thingsboard.org","password":"tenant"}' \
    ${SERVER_URL}/api/auth/login 2>/dev/null)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Login successful"
    echo "  Token received: $(echo $RESPONSE_BODY | jq -r '.token' 2>/dev/null | cut -c1-50)..."
else
    echo "✗ Login failed with HTTP code: $HTTP_CODE"
    echo "  Response: $RESPONSE_BODY"
fi
echo ""

# Summary and recommendations
echo "============================================"
echo "Summary and Recommendations"
echo "============================================"
echo ""

if [ $FAIL -gt 5 ]; then
    echo "⚠️  SEVERE CONNECTIVITY ISSUES DETECTED"
    echo ""
    echo "Your ThingsBoard server has significant stability problems:"
    echo "  - More than 50% of requests are failing"
    echo "  - This will cause the provision script to be very slow"
    echo ""
    echo "Recommended actions:"
    echo "  1. Check if the server ${SERVER_IP} is under heavy load"
    echo "  2. Check your network connection quality"
    echo "  3. Consider using a local ThingsBoard instance for testing"
    echo "  4. Check firewall/security group rules"
    echo ""
elif [ $FAIL -gt 2 ]; then
    echo "⚠️  MODERATE CONNECTIVITY ISSUES DETECTED"
    echo ""
    echo "Your connection has some instability:"
    echo "  - $(( FAIL * 10 ))% of requests are failing"
    echo "  - The provision script will work but may be slow with retries"
    echo ""
    echo "Recommended actions:"
    echo "  1. Run provision script with increased timeout (300+ seconds)"
    echo "  2. Monitor your network connection during provisioning"
    echo ""
else
    echo "✓ CONNECTION IS STABLE"
    echo ""
    echo "Your ThingsBoard server connection is working well."
    echo "The provision script should complete without major issues."
    echo ""
fi
