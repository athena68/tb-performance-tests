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

#
# Populate ebmpapst FFU device attributes on ThingsBoard
#

echo "=========================================="
echo "Populating ebmpapst FFU Device Attributes"
echo "=========================================="

# Load from .env.ebmpapst but override telemetry setting
if [ -f .env.ebmpapst ]; then
    export $(cat .env.ebmpapst | grep -v '^#' | grep -v 'TEST_TELEMETRY' | xargs)
fi

# Override settings for attribute population
export TEST_TELEMETRY=false      # Send attributes
export DEVICE_CREATE_ON_START=false  # Devices should already exist
export DURATION_IN_SECONDS=10    # Quick run to populate attributes
export DEVICE_DELETE_ON_COMPLETE=false

echo ""
echo "Configuration:"
echo "  ThingsBoard Server: $REST_URL"
echo "  Payload Type: $TEST_PAYLOAD_TYPE"
echo "  Mode: ATTRIBUTES (not telemetry)"
echo "  Devices: $DEVICE_START_IDX to $DEVICE_END_IDX"
echo "  Duration: $DURATION_IN_SECONDS seconds"
echo ""

echo "Starting attribute population..."
mvn spring-boot:run

echo ""
echo "Attributes populated! Check ThingsBoard UI:"
echo "  Devices → Select device → Attributes tab"
