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

echo "=========================================="
echo "ebmpapst FFU Performance Test"
echo "=========================================="
echo ""

# Load environment variables from .env.ebmpapst if it exists
if [ -f .env.ebmpapst ]; then
    echo "Loading configuration from .env.ebmpapst..."
    export $(cat .env.ebmpapst | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)
    echo "Configuration loaded successfully!"
else
    echo "Warning: .env.ebmpapst not found. Using default values."
    echo ""
    echo "Default Configuration:"
    # Set ThingsBoard connection details from environment or use defaults
    export REST_URL=${REST_URL:-"http://localhost:8080"}
    export MQTT_HOST=${MQTT_HOST:-"localhost"}
    # Set authentication details from environment
    export REST_USERNAME=${REST_USERNAME:-""}
    export REST_PASSWORD=${REST_PASSWORD:-""}

    if [[ -z "$REST_USERNAME" || -z "$REST_PASSWORD" ]]; then
        echo "❌ Error: REST_USERNAME and REST_PASSWORD must be set in environment or .env file"
        exit 1
    fi
    export TEST_PAYLOAD_TYPE=EBMPAPST_FFU
    export DEVICE_START_IDX=0
    export DEVICE_END_IDX=50
    export MESSAGES_PER_SECOND=50
    export ALARMS_PER_SECOND=2
    export DURATION_IN_SECONDS=300
    export DEVICE_CREATE_ON_START=true
    export DEVICE_DELETE_ON_COMPLETE=false
fi

echo ""
echo "Test Configuration:"
echo "  ThingsBoard Server: $REST_URL"
echo "  MQTT Broker: $MQTT_HOST:${MQTT_PORT:-1883}"
echo "  Payload Type: $TEST_PAYLOAD_TYPE"
echo "  Number of Devices: $((DEVICE_END_IDX - DEVICE_START_IDX))"
echo "  Messages per Second: $MESSAGES_PER_SECOND"
echo "  Test Duration: $DURATION_IN_SECONDS seconds"
echo "  Create Devices: $DEVICE_CREATE_ON_START"
echo "  Delete devices on Complete: $DEVICE_DELETE_ON_COMPLETE"
echo "  Create Gateways: $GATEWAY_CREATE_ON_START"
echo "  Delete GW on Complete: $DEVICE_DELETE_ON_COMPLETE"
echo ""

# Confirm before starting
read -p "Start test with above configuration? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Test cancelled."
    exit 1
fi

echo ""
echo "Starting ThingsBoard ebmpapst FFU Performance Test..."
echo ""

mvn spring-boot:run
