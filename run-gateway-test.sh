#!/bin/bash

# ThingsBoard Gateway Performance Test Runner
# This script properly sets environment variables and runs the test

echo "=== Starting ThingsBoard Gateway Performance Test ==="
echo "Configuration:"
echo "  REST_URL: http://167.172.75.1:8080"
echo "  MQTT_HOST: 167.172.75.1:1883"
echo "  TEST_API: gateway"
echo "  TEST_PAYLOAD_TYPE: EBMPAPST_FFU"
echo "  GATEWAY_START_IDX: 0"
echo "  GATEWAY_END_IDX: 1"
echo "  DEVICE_START_IDX: 0"
echo "  DEVICE_END_IDX: 5"
echo ""

# Set all environment variables explicitly
export REST_URL=http://167.172.75.1:8080
export REST_USERNAME=tenant@thingsboard.org
export REST_PASSWORD=tenant
export REST_POOL_SIZE=4
export REST_CONNECT_SERVER=true

export MQTT_HOST=167.172.75.1
export MQTT_PORT=1883
export MQTT_SSL_ENABLED=false
export MQTT_SSL_KEY_STORE=
export MQTT_SSL_KEY_STORE_PASSWORD=

export TEST_API=gateway
export DEVICE_API=MQTT

export GATEWAY_START_IDX=0
export GATEWAY_END_IDX=1
export GATEWAY_CREATE_ON_START=true
export GATEWAY_DELETE_ON_COMPLETE=false

export DEVICE_START_IDX=0
export DEVICE_END_IDX=5
export DEVICE_CREATE_ON_START=true
export DEVICE_DELETE_ON_COMPLETE=false

export TEST_PAYLOAD_TYPE=EBMPAPST_FFU

export WARMUP_ENABLED=true
export TEST_ENABLED=true

export MESSAGES_PER_SECOND=60
export DURATION_IN_SECONDS=86400

export ALARMS_PER_SECOND=2
export ALARM_STORM_START_SECOND=60
export ALARM_STORM_END_SECOND=240

export UPDATE_ROOT_RULE_CHAIN=false
export REVERT_ROOT_RULE_CHAIN=false
export RULE_CHAIN_NAME=root_rule_chain_ce.json

export TEST_SEQUENTIAL=false
export EXIT_AFTER_COMPLETE=true
export DASHBOARD_CREATE_ON_START=false

echo "Environment variables set. Starting application..."
echo ""

# Run the Spring Boot application
mvn spring-boot:run