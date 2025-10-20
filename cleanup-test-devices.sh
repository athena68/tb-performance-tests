#!/bin/bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Cleanup script for performance test devices
#
# NOTE: This script only cleans DEVICES (gateways and FFU devices).
#       For full scenario cleanup including ASSETS (Site, Building, Floor, Room),
#       use cleanup-scenario.py instead!
#

echo "=========================================="
echo "ThingsBoard Test Device Cleanup"
echo "=========================================="
echo ""
echo "⚠️  NOTE: This script only deletes DEVICES"
echo "   To delete full scenario (assets + devices):"
echo "   Use: ./cleanup-scenario.py"
echo ""

# Load configuration
if [ -f .env.ebmpapst ]; then
    export $(cat .env.ebmpapst | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
elif [ -f .env.ebmpapst-gateway ]; then
    export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
fi

# Default values if not set
REST_URL=${REST_URL:-http://167.99.64.71:8080}
REST_USERNAME=${REST_USERNAME:-tenant@thingsboard.org}
REST_PASSWORD=${REST_PASSWORD:-tenant}

echo "Configuration:"
echo "  ThingsBoard Server: $REST_URL"
echo "  Username: $REST_USERNAME"
echo ""

# Menu for cleanup options
echo "Cleanup Options:"
echo "  1) Delete devices by device profile (EBMPAPST_FFU)"
echo "  2) Delete devices by name range (DW00000000 to DW00000049)"
echo "  3) Delete gateways by name range (GW00000000 to GW00000002)"
echo "  4) Delete ALL test devices and gateways"
echo "  5) Cancel"
echo ""

read -p "Select option (1-5): " option

case $option in
    1)
        echo ""
        echo "Deleting all devices with profile: EBMPAPST_FFU..."
        CLEANUP_TYPE="profile"
        PROFILE_NAME="EBMPAPST_FFU"
        ;;
    2)
        echo ""
        read -p "Enter start index (default: 0): " START_IDX
        START_IDX=${START_IDX:-0}
        read -p "Enter end index (default: 50): " END_IDX
        END_IDX=${END_IDX:-50}
        echo "Deleting devices: DW$(printf '%08d' $START_IDX) to DW$(printf '%08d' $((END_IDX-1)))..."
        CLEANUP_TYPE="device_range"
        ;;
    3)
        echo ""
        read -p "Enter start index (default: 0): " START_IDX
        START_IDX=${START_IDX:-0}
        read -p "Enter end index (default: 3): " END_IDX
        END_IDX=${END_IDX:-3}
        echo "Deleting gateways: GW$(printf '%08d' $START_IDX) to GW$(printf '%08d' $((END_IDX-1)))..."
        CLEANUP_TYPE="gateway_range"
        ;;
    4)
        echo ""
        echo "⚠️  WARNING: This will delete ALL test devices and gateways!"
        read -p "Are you sure? Type 'DELETE ALL' to confirm: " CONFIRM
        if [ "$CONFIRM" != "DELETE ALL" ]; then
            echo "Cancelled."
            exit 0
        fi
        CLEANUP_TYPE="all"
        ;;
    5)
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo "Invalid option."
        exit 1
        ;;
esac

echo ""
read -p "Proceed with cleanup? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Create temporary Java cleanup program
cat > /tmp/TbCleanup.java << 'EOF'
import org.thingsboard.rest.client.RestClient;
import org.thingsboard.server.common.data.Device;
import org.thingsboard.server.common.data.DeviceProfile;
import org.thingsboard.server.common.data.page.PageData;
import org.thingsboard.server.common.data.page.PageLink;

import java.util.Optional;

public class TbCleanup {
    public static void main(String[] args) throws Exception {
        String url = System.getenv("REST_URL");
        String username = System.getenv("REST_USERNAME");
        String password = System.getenv("REST_PASSWORD");
        String cleanupType = System.getenv("CLEANUP_TYPE");

        RestClient client = new RestClient(url);
        client.login(username, password);

        int deletedCount = 0;

        if ("profile".equals(cleanupType)) {
            String profileName = System.getenv("PROFILE_NAME");
            Optional<DeviceProfile> profile = client.getDeviceProfileByName(profileName);
            if (profile.isPresent()) {
                PageLink pageLink = new PageLink(100);
                PageData<Device> devices;
                do {
                    devices = client.getTenantDevices(profile.get().getId(), pageLink);
                    for (Device device : devices.getData()) {
                        System.out.println("Deleting device: " + device.getName());
                        client.deleteDevice(device.getId());
                        deletedCount++;
                    }
                    pageLink = pageLink.nextPageLink();
                } while (devices.hasNext());
            }
        } else if ("device_range".equals(cleanupType)) {
            int startIdx = Integer.parseInt(System.getenv("START_IDX"));
            int endIdx = Integer.parseInt(System.getenv("END_IDX"));
            for (int i = startIdx; i < endIdx; i++) {
                String deviceName = "DW" + String.format("%08d", i);
                Optional<Device> device = client.findDevice(deviceName);
                if (device.isPresent()) {
                    System.out.println("Deleting device: " + deviceName);
                    client.deleteDevice(device.get().getId());
                    deletedCount++;
                }
            }
        } else if ("gateway_range".equals(cleanupType)) {
            int startIdx = Integer.parseInt(System.getenv("START_IDX"));
            int endIdx = Integer.parseInt(System.getenv("END_IDX"));
            for (int i = startIdx; i < endIdx; i++) {
                String gatewayName = "GW" + String.format("%08d", i);
                Optional<Device> gateway = client.findDevice(gatewayName);
                if (gateway.isPresent()) {
                    System.out.println("Deleting gateway: " + gatewayName);
                    client.deleteDevice(gateway.get().getId());
                    deletedCount++;
                }
            }
        } else if ("all".equals(cleanupType)) {
            // Delete all DW* devices
            for (int i = 0; i < 10000; i++) {
                String deviceName = "DW" + String.format("%08d", i);
                Optional<Device> device = client.findDevice(deviceName);
                if (device.isPresent()) {
                    System.out.println("Deleting device: " + deviceName);
                    client.deleteDevice(device.get().getId());
                    deletedCount++;
                }
            }
            // Delete all GW* gateways
            for (int i = 0; i < 100; i++) {
                String gatewayName = "GW" + String.format("%08d", i);
                Optional<Device> gateway = client.findDevice(gatewayName);
                if (gateway.isPresent()) {
                    System.out.println("Deleting gateway: " + gatewayName);
                    client.deleteDevice(gateway.get().getId());
                    deletedCount++;
                }
            }
        }

        System.out.println("\n✓ Cleanup completed! " + deletedCount + " devices/gateways deleted.");
        client.logout();
    }
}
EOF

# Compile and run cleanup
export CLEANUP_TYPE START_IDX END_IDX PROFILE_NAME
mvn exec:java -Dexec.mainClass="org.thingsboard.tools.service.shared.DefaultRestClientService" \
    -Dexec.classpathScope=test \
    -Dexec.args="cleanup" 2>/dev/null || {

    # Fallback: Use REST API directly with curl
    echo "Using REST API cleanup method..."

    # Login
    TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" \
        | grep -o '"token":"[^"]*' | cut -d'"' -f4)

    if [ -z "$TOKEN" ]; then
        echo "ERROR: Failed to login to ThingsBoard"
        exit 1
    fi

    DELETED=0

    if [ "$CLEANUP_TYPE" = "profile" ]; then
        # Get device profile ID
        PROFILE_ID=$(curl -s -X GET "$REST_URL/api/deviceProfiles?pageSize=100&page=0" \
            -H "X-Authorization: Bearer $TOKEN" \
            | grep -B5 "\"name\":\"$PROFILE_NAME\"" | grep -o '"id":{"id":"[^"]*' | head -1 | cut -d'"' -f6)

        if [ -z "$PROFILE_ID" ]; then
            echo "ERROR: Device profile '$PROFILE_NAME' not found"
        else
            echo "Found device profile: $PROFILE_NAME (ID: $PROFILE_ID)"

            # Get all devices with this profile
            PAGE=0
            while true; do
                RESPONSE=$(curl -s -X GET "$REST_URL/api/tenant/deviceInfos?pageSize=100&page=$PAGE&sortProperty=createdTime&sortOrder=DESC" \
                    -H "X-Authorization: Bearer $TOKEN")

                # Extract device IDs that match the profile
                DEVICE_IDS=$(echo "$RESPONSE" | grep -o '"id":{"id":"[^"]*' | cut -d'"' -f6)

                if [ -z "$DEVICE_IDS" ]; then
                    break
                fi

                # Check each device's profile
                for DEVICE_ID in $DEVICE_IDS; do
                    DEVICE_INFO=$(curl -s -X GET "$REST_URL/api/device/$DEVICE_ID" \
                        -H "X-Authorization: Bearer $TOKEN")

                    DEVICE_PROFILE_ID=$(echo "$DEVICE_INFO" | grep -o '"deviceProfileId":{"id":"[^"]*' | cut -d'"' -f6)
                    DEVICE_NAME=$(echo "$DEVICE_INFO" | grep -o '"name":"[^"]*' | head -1 | cut -d'"' -f4)

                    if [ "$DEVICE_PROFILE_ID" = "$PROFILE_ID" ]; then
                        echo "Deleting device: $DEVICE_NAME"
                        curl -s -X DELETE "$REST_URL/api/device/$DEVICE_ID" \
                            -H "X-Authorization: Bearer $TOKEN" > /dev/null
                        DELETED=$((DELETED+1))
                    fi
                done

                # Check if there are more pages
                HAS_NEXT=$(echo "$RESPONSE" | grep -o '"hasNext":[^,}]*' | cut -d':' -f2)
                if [ "$HAS_NEXT" != "true" ]; then
                    break
                fi
                PAGE=$((PAGE+1))
            done
        fi
    fi

    if [ "$CLEANUP_TYPE" = "device_range" ] || [ "$CLEANUP_TYPE" = "all" ]; then
        START=${START_IDX:-0}
        END=${END_IDX:-50}

        # Get all devices first (use large pageSize to get all at once)
        echo "Fetching all devices from server..."
        ALL_DEVICES=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
            -H "X-Authorization: Bearer $TOKEN")

        for i in $(seq $START $((END-1))); do
            DEVICE_NAME="DW$(printf '%08d' $i)"

            # Extract device ID using jq if available, otherwise use grep
            if command -v jq &> /dev/null; then
                DEVICE_ID=$(echo "$ALL_DEVICES" | jq -r ".data[] | select(.name==\"$DEVICE_NAME\") | .id.id" 2>/dev/null)
            else
                # Fallback: extract using grep pattern matching
                DEVICE_ID=$(echo "$ALL_DEVICES" | grep -o "\"name\":\"$DEVICE_NAME\"" -A 50 | grep -o '"id":{"id":"[^"]*' | head -1 | cut -d'"' -f6)
            fi

            if [ ! -z "$DEVICE_ID" ]; then
                echo "Deleting device: $DEVICE_NAME (ID: $DEVICE_ID)"
                curl -s -X DELETE "$REST_URL/api/device/$DEVICE_ID" \
                    -H "X-Authorization: Bearer $TOKEN" > /dev/null
                DELETED=$((DELETED+1))
            fi
        done
    fi

    if [ "$CLEANUP_TYPE" = "gateway_range" ] || [ "$CLEANUP_TYPE" = "all" ]; then
        START=${START_IDX:-0}
        END=${END_IDX:-3}

        # Get all devices first if not already fetched
        if [ -z "$ALL_DEVICES" ]; then
            echo "Fetching all devices from server..."
            ALL_DEVICES=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000&page=0" \
                -H "X-Authorization: Bearer $TOKEN")
        fi

        for i in $(seq $START $((END-1))); do
            GATEWAY_NAME="GW$(printf '%08d' $i)"

            # Extract device ID using jq if available, otherwise use grep
            if command -v jq &> /dev/null; then
                GATEWAY_ID=$(echo "$ALL_DEVICES" | jq -r ".data[] | select(.name==\"$GATEWAY_NAME\") | .id.id" 2>/dev/null)
            else
                # Fallback: extract using grep pattern matching
                GATEWAY_ID=$(echo "$ALL_DEVICES" | grep -o "\"name\":\"$GATEWAY_NAME\"" -A 50 | grep -o '"id":{"id":"[^"]*' | head -1 | cut -d'"' -f6)
            fi

            if [ ! -z "$GATEWAY_ID" ]; then
                echo "Deleting gateway: $GATEWAY_NAME (ID: $GATEWAY_ID)"
                curl -s -X DELETE "$REST_URL/api/device/$GATEWAY_ID" \
                    -H "X-Authorization: Bearer $TOKEN" > /dev/null
                DELETED=$((DELETED+1))
            fi
        done
    fi

    echo ""
    echo "✓ Cleanup completed! $DELETED devices/gateways deleted."
}

echo ""
echo "=========================================="
echo "Verify on ThingsBoard UI:"
echo "  Devices → All"
echo "  Check that test devices have been removed"
echo "=========================================="
