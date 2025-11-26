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

"""
Get existing asset profile IDs for Site, Building, Floor, Room
"""

import requests
import json

# ThingsBoard connection details
TB_URL = "https://demo.thingsboard.io"
USERNAME = "tuannt7@fpt.com"
PASSWORD = "Fpt2025"

def login():
    """Login and get JWT token"""
    response = requests.post(
        f"{TB_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()['token']

def get_asset_profile_ids(token):
    """Get all asset profiles and find IDs for our required profiles"""
    required_profiles = ["Site", "Building", "Floor", "Room"]
    found_profiles = {}

    # Get all asset profiles
    response = requests.get(
        f"{TB_URL}/api/tenant/assetProfile?pageSize=100&page=0",
        headers={
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {token}"
        }
    )

    if response.status_code == 200:
        profiles = response.json().get('data', [])
        print(f"Found {len(profiles)} asset profiles:")

        for profile in profiles:
            name = profile.get('name', 'Unknown')
            profile_id = profile.get('id', {}).get('id', 'No ID')
            print(f"  - {name}: {profile_id}")

            if name in required_profiles:
                found_profiles[name] = profile_id

        missing = set(required_profiles) - set(found_profiles.keys())
        if missing:
            print(f"\n⚠ Missing profiles: {missing}")
        else:
            print(f"\n✓ All required profiles found!")

    else:
        print(f"✗ Failed to get asset profiles: {response.status_code} - {response.text}")
        return {}

    return found_profiles

def main():
    print("Getting existing asset profile IDs for EBMPAPST scenario...")

    # Login
    try:
        token = login()
        print(f"✓ Logged in to {TB_URL}")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return 1

    # Get asset profile IDs
    profile_ids = get_asset_profile_ids(token)

    if profile_ids:
        print("\nRequired Asset Profile IDs:")
        for name, profile_id in profile_ids.items():
            print(f"  {name}: {profile_id}")

        # Save to file
        with open('/tmp/asset_profile_ids.json', 'w') as f:
            json.dump(profile_ids, f, indent=2)
        print(f"\n✓ Saved profile IDs to /tmp/asset_profile_ids.json")

        # Also create code snippet for script update
        print("\nCode snippet for provision-scenario.py:")
        print("ASSET_PROFILE_IDS = {")
        for name, profile_id in profile_ids.items():
            print(f"    '{name.upper()}': '{profile_id}',")
        print("}")

    return 0

if __name__ == '__main__':
    exit(main())