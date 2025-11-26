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
Create required asset profiles for EBMPAPST scenario provisioning
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

def create_asset_profile(token, name, description):
    """Create an asset profile"""
    profile_data = {
        "name": name,
        "description": description,
        "type": "DEFAULT",
        "image": None,
        "defaultRuleChainId": None,
        "defaultDashboardId": None,
        "defaultQueueName": ""
    }

    response = requests.post(
        f"{TB_URL}/api/assetProfile",
        headers={
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {token}"
        },
        json=profile_data
    )

    if response.status_code == 200:
        profile_id = response.json()['id']['id']
        print(f"✓ Created asset profile: {name} (ID: {profile_id})")
        return profile_id
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print(f"⚠ Asset profile {name} already exists")
        return None
    else:
        print(f"✗ Failed to create {name}: {response.status_code} - {response.text}")
        return None

def main():
    print("Creating required asset profiles for EBMPAPST scenario...")

    # Login
    try:
        token = login()
        print(f"✓ Logged in to {TB_URL}")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return 1

    # Required asset profiles
    asset_profiles = [
        ("Site", "Site location - top level hierarchy"),
        ("Building", "Building structure - contains floors"),
        ("Floor", "Floor level - contains rooms"),
        ("Room", "Room space - contains gateways and devices")
    ]

    created_profiles = {}

    for name, description in asset_profiles:
        profile_id = create_asset_profile(token, name, description)
        if profile_id:
            created_profiles[name] = profile_id

    if created_profiles:
        print(f"\n✓ Successfully created {len(created_profiles)} asset profiles")
        print("Asset Profile IDs:")
        for name, profile_id in created_profiles.items():
            print(f"  {name}: {profile_id}")

        # Save to file for script update
        with open('/tmp/asset_profile_ids.json', 'w') as f:
            json.dump(created_profiles, f, indent=2)
        print(f"\n✓ Saved profile IDs to /tmp/asset_profile_ids.json")
    else:
        print("⚠ No new profiles created (they may already exist)")

    return 0

if __name__ == '__main__':
    exit(main())