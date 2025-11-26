#!/usr/bin/env python3
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


import requests
import json

# Configuration
BASE_URL = "http://167.172.75.1:8080"
USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"

def login():
    """Login to ThingsBoard and get JWT token"""
    login_url = f"{BASE_URL}/api/auth/login"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }

    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        token = response.json()['token']
        print(f"✓ Logged in successfully")
        return token
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def get_gateway_devices(token):
    """Get all gateway devices"""
    headers = {
        "X-Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{BASE_URL}/api/tenant/devices?pageSize=1000&page=0", headers=headers)
    if response.status_code == 200:
        devices = response.json()['data']
        gateways = [d for d in devices if d.get('type') == 'Gateway' and d['name'].startswith('GW')]
        return gateways
    else:
        print(f"✗ Failed to get devices: {response.status_code} - {response.text}")
        return []

def delete_device(token, device_id, device_name):
    """Delete a device"""
    headers = {
        "X-Authorization": f"Bearer {token}"
    }

    response = requests.delete(f"{BASE_URL}/api/device/{device_id}", headers=headers)
    if response.status_code == 200:
        print(f"✓ Deleted gateway: {device_name}")
        return True
    else:
        print(f"✗ Failed to delete {device_name}: {response.status_code} - {response.text}")
        return False

def main():
    print("Getting ThingsBoard authentication token...")
    token = login()
    if not token:
        return

    print("\nFinding existing gateway devices...")
    gateways = get_gateway_devices(token)

    if not gateways:
        print("No gateway devices found to delete.")
        return

    print(f"Found {len(gateways)} gateway devices:")
    for gateway in gateways:
        print(f"  - {gateway['name']} (ID: {gateway['id']['id']})")

    print("\nDeleting existing gateway devices...")
    for gateway in gateways:
        delete_device(token, gateway['id']['id'], gateway['name'])

    print("\n✅ Gateway cleanup completed!")

if __name__ == "__main__":
    main()