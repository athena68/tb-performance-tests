#!/usr/bin/env python3

import json
import time
import requests
import random
from datetime import datetime

# ThingsBoard connection details
REST_URL = "http://167.172.75.1:8080"
USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"

def get_jwt_token():
    """Get JWT token from ThingsBoard"""
    url = f"{REST_URL}/api/auth/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()["token"]
    else:
        print(f"Failed to get token: {response.status_code}")
        return None

def create_device(device_name, token):
    """Create a device if it doesn't exist"""
    url = f"{REST_URL}/api/tenant/device?deviceName={device_name}"
    headers = {"X-Authorization": f"Bearer {token}"}

    # Check if device exists
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.json():
        print(f"✅ Device {device_name} already exists")
        return response.json()["id"]

    # Create new device
    url = f"{REST_URL}/api/tenant/device"
    device_data = {
        "name": device_name,
        "type": "EBMPAPST_FFU"
    }
    response = requests.post(url, json=device_data, headers=headers)
    if response.status_code == 200:
        device_id = response.json()["id"]["id"]
        print(f"✅ Created device {device_name} with ID: {device_id}")
        return device_id
    else:
        print(f"❌ Failed to create device {device_name}: {response.text}")
        return None

def get_device_credentials(device_id, token):
    """Get device credentials"""
    url = f"{REST_URL}/api/device/{device_id}/credentials"
    headers = {"X-Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["credentialsId"]
    else:
        print(f"❌ Failed to get credentials for device {device_id}")
        return None

def send_telemetry_via_rest(device_name, data, token):
    """Send telemetry via REST API"""
    url = f"{REST_URL}/api/v1/{device_name}/telemetry"
    headers = {"Content-Type": "application/json"}

    payload = [{
        "ts": int(time.time() * 1000),
        "values": data
    }]

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ Sent telemetry to {device_name}: {data}")
        return True
    else:
        print(f"❌ Failed to send telemetry to {device_name}: {response.status_code}")
        return False

def generate_ffu_telemetry(device_index):
    """Generate realistic FFU telemetry data"""
    base_seed = abs(hash(f"DW{device_index:08d}")) % 1000

    # Simulate realistic FFU values
    rpm = 1300 + (base_seed % 500) + random.randint(-10, 10)
    airflow = int(rpm / 1800.0 * 2330)  # m³/h
    power = int(400.0 * (rpm / 1800.0) * 4.5 * 0.9)  # Watts
    pressure = 100 + int(rpm / 1800.0 * 150) + (base_seed % 80) + random.randint(-5, 5)
    motor_temp = 25 + int((rpm / 1800.0) * 25) + random.randint(-2, 2)

    return {
        "actualSpeed": rpm,
        "speedSetpoint": 1300 + (base_seed % 500),
        "calculatedAirflow": airflow,
        "powerConsumption": power,
        "differentialPressure": pressure,
        "motorTemperature": motor_temp,
        "ambientTemperature": 22 + (base_seed % 8),
        "operatingHours": base_seed + 10000,
        "operatingStatus": "RUNNING",
        "alarmCode": 0,
        "warningCode": 0
    }

def main():
    print("🚀 Starting Hanoi Cleanroom FFU Test Data Generation")
    print(f"📊 Target Server: {REST_URL}")
    print(f"👤 User: {USERNAME}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # Get authentication token
    token = get_jwt_token()
    if not token:
        print("❌ Authentication failed!")
        return

    print(f"✅ Successfully authenticated")

    # Create sample devices (first 5 for quick test)
    devices_created = 0
    for i in range(5):  # Start with 5 devices for testing
        device_name = f"DW{i:08d}"

        device_id = create_device(device_name, token)
        if device_id:
            devices_created += 1

            # Get credentials
            credentials_id = get_device_credentials(device_id, token)
            if credentials_id:
                print(f"   📱 Device Credentials: {credentials_id}")

    print(f"\n✅ Successfully created/verified {devices_created} devices")

    # Send test telemetry data
    print("\n📡 Starting telemetry data transmission...")

    message_count = 0
    start_time = time.time()

    try:
        while message_count < 100:  # Send 100 messages for testing
            for i in range(5):  # Send to 5 devices
                device_name = f"DW{i:08d}"
                telemetry = generate_ffu_telemetry(i)

                if send_telemetry_via_rest(device_name, telemetry, token):
                    message_count += 1

            print(f"📊 Sent {message_count} telemetry messages...")
            time.sleep(2)  # Wait 2 seconds between batches

    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")

    elapsed = time.time() - start_time
    print(f"\n✅ Test completed!")
    print(f"📊 Total messages sent: {message_count}")
    print(f"⏱️  Elapsed time: {elapsed:.2f} seconds")
    print(f"📈 Rate: {message_count/elapsed:.2f} messages/second")
    print(f"🕐 Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()