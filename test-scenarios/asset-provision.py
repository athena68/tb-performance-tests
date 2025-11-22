#!/usr/bin/env python3
"""
Asset Provisioning Script - Creates Hierarchy Only
Site → Building → Floor → Room (NO devices/gateways)
Generates .env file for Java device creation
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Add config directory to path for attribute loading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

# Default credentials file location (matching cleanup script)
DEFAULT_CREDENTIALS_FILE = 'test-scenarios/credentials.json'

def load_credentials(creds_file: str = None) -> Dict[str, str]:
    """Load credentials from JSON file"""
    if creds_file is None:
        creds_file = DEFAULT_CREDENTIALS_FILE

    if not os.path.exists(creds_file):
        print(f"❌ Credentials file not found: {creds_file}")
        print(f"\n📝 Please create a credentials file at: {creds_file}")
        print(f" with the following content:\n")
        example_content = f'''{{
  "thingsboard": {{
    "url": "http://localhost:8080",
    "username": "tenant@thingsboard.org",
    "password": "tenant"
  }}
}}'''
        print(example_content)
        print(f"\n⚠️  For security, make sure the file is NOT committed to version control")
        print(f"   Add '{creds_file.split('/')[-1]}' to your .gitignore file")
        raise FileNotFoundError(f"Credentials file not found: {creds_file}")

    try:
        with open(creds_file, 'r') as f:
            creds = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format in credentials file: {e}")
        raise

    return creds

class AssetProvisioner:
    def __init__(self, creds_file: str = None, conflict_resolution: str = 'ask'):
        creds = load_credentials(creds_file)
        self.base_url = creds["thingsboard"]["url"]
        self.username = creds["thingsboard"]["username"]
        self.password = creds["thingsboard"]["password"]
        self.token = None
        self.created_assets = {}  # Store created asset IDs
        self.room_configurations = {}  # Store room info for .env generation
        self.conflict_resolution = conflict_resolution  # 'ask', 'skip', 'recreate'

    def login(self) -> bool:
        """Login to ThingsBoard"""
        try:
            login_url = f"{self.base_url}/api/auth/login"
            response = requests.post(login_url, json={
                "username": self.username,
                "password": self.password
            })

            if response.status_code == 200:
                self.token = response.json()["token"]
                print(f"✅ Login successful as: {self.username}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def create_asset(self, name: str, asset_type: str, attributes: Dict = None) -> Optional[str]:
        """Create asset with intelligent conflict resolution"""
        try:
            # Check if asset already exists
            existing = self.find_asset_by_name(name)
            if existing:
                return self._handle_existing_asset(name, existing)

            # Create new asset
            return self._create_new_asset(name, asset_type, attributes)

        except Exception as e:
            print(f"❌ Error creating asset {name}: {e}")
            return None

    def _handle_existing_asset(self, name: str, existing: Dict) -> Optional[str]:
        """Handle conflicts with existing assets"""
        asset_id = existing["id"]["id"]

        if self.conflict_resolution == 'skip':
            print(f"⚠️  Asset '{name}' already exists, skipping (ID: {asset_id})")
            return asset_id

        elif self.conflict_resolution == 'recreate':
            print(f"🔄 Asset '{name}' already exists, deleting and recreating...")
            if self._delete_asset(asset_id):
                return self._create_new_asset(name, existing.get('type', 'Asset'), existing.get('attributes'))
            else:
                print(f"❌ Failed to delete existing asset '{name}'")
                return None

        else:  # 'ask' mode
            return self._ask_user_conflict_resolution(name, existing)

    def _ask_user_conflict_resolution(self, name: str, existing: Dict) -> Optional[str]:
        """Ask user how to resolve conflict"""
        asset_id = existing["id"]["id"]
        print(f"\n⚠️  CONFLICT DETECTED!")
        print(f"   Asset '{name}' already exists in ThingsBoard")
        print(f"   ID: {asset_id}")
        print(f"   Type: {existing.get('type', 'Unknown')}")
        print(f"   Created: {existing.get('createdTime', 'Unknown')}")

        while True:
            print(f"\nPlease choose how to resolve:")
            print(f"  1. Skip - Use existing asset as-is")
            print(f"  2. Recreate - Delete existing and create new")
            print(f"  3. Abort - Stop the script")

            try:
                choice = input(f"\nEnter your choice (1-3) [default: 1]: ").strip()
                if not choice:
                    choice = "1"

                if choice == "1":
                    print(f"✅ Using existing asset '{name}' (ID: {asset_id})")
                    return asset_id
                elif choice == "2":
                    print(f"🔄 Deleting and recreating asset '{name}'...")
                    if self._delete_asset(asset_id):
                        return self._create_new_asset(name, existing.get('type', 'Asset'), existing.get('attributes'))
                    else:
                        print(f"❌ Failed to delete existing asset '{name}'")
                        return None
                elif choice == "3":
                    print(f"❌ User chose to abort script")
                    sys.exit(1)
                else:
                    print(f"❌ Invalid choice. Please enter 1, 2, or 3.")
            except (KeyboardInterrupt, EOFError):
                print(f"\n❌ Script interrupted by user")
                sys.exit(1)

    def _delete_asset(self, asset_id: str) -> bool:
        """Delete an asset by ID"""
        try:
            headers = {"X-Authorization": f"Bearer {self.token}"}
            response = requests.delete(
                f"{self.base_url}/api/asset/{asset_id}",
                headers=headers
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error deleting asset: {e}")
            return False

    def _create_new_asset(self, name: str, asset_type: str, attributes: Dict = None) -> Optional[str]:
        """Create a new asset"""
        asset_data = {
            "name": name,
            "type": asset_type
        }

        if attributes:
            asset_data["attributes"] = attributes

        headers = {"X-Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/api/asset",
            json=asset_data,
            headers=headers
        )

        if response.status_code == 200:
            asset_id = response.json()["id"]["id"]
            print(f"✅ Created asset: {name} (ID: {asset_id})")
            return asset_id
        else:
            print(f"❌ Failed to create asset {name}: {response.status_code} - {response.text}")
            return None

    def find_asset_by_name(self, name: str) -> Optional[Dict]:
        """Find asset by name using robust pagination search"""
        try:
            headers = {"X-Authorization": f"Bearer {self.token}"}
            page_size = 100
            page = 0
            assets = []

            # Search through all pages using the proven approach from cleanup script
            while True:
                params = {
                    'pageSize': page_size,
                    'page': page
                }

                response = requests.get(
                    f"{self.base_url}/api/tenant/assets",  # Note: uses 'assets' not 'asset'
                    headers=headers,
                    params=params
                )

                if response.status_code != 200:
                    print(f"❌ Failed to fetch assets page {page}")
                    break

                data = response.json()
                page_assets = data.get("data", [])
                assets.extend(page_assets)

                if len(page_assets) < page_size:
                    break

                page += 1

            print(f"📋 Searched {page + 1} pages, found {len(assets)} total assets")

            # Search for exact name match
            for asset in assets:
                if asset.get("name") == name:
                    print(f"✅ Found existing asset: '{name}' (ID: {asset.get('id', {}).get('id', 'Unknown')})")
                    return asset

            print(f"❌ Asset '{name}' not found in {len(assets)} assets")
            return None

        except Exception as e:
            print(f"❌ Error finding asset {name}: {e}")
            return None

    def create_relation(self, from_id: str, to_id: str, relation_type: str = "Contains") -> bool:
        """Create relation between assets"""
        try:
            relation_data = {
                "from": {
                    "id": from_id,
                    "entityType": "ASSET"
                },
                "to": {
                    "id": to_id,
                    "entityType": "ASSET"
                },
                "type": relation_type,
                "typeGroup": "COMMON"
            }

            headers = {"X-Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.base_url}/api/relation",
                json=relation_data,
                headers=headers
            )

            if response.status_code == 200:
                return True
            else:
                print(f"❌ Failed to create relation: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error creating relation: {e}")
            return False

    def create_hierarchy(self, scenario: Dict) -> bool:
        """Create asset hierarchy from scenario"""
        print("🏗️  Creating asset hierarchy...")

        # Create Site
        site_config = scenario.get('site', {})
        site_name = site_config['name']
        site_attrs = {
            'address': site_config.get('address'),
            'latitude': site_config.get('latitude'),
            'longitude': site_config.get('longitude'),
            'site_type': site_config.get('type', 'Site').lower()
        }
        # Remove None values
        site_attrs = {k: v for k, v in site_attrs.items() if v is not None}

        site_id = self.create_asset(site_name, site_config.get('type', 'Site'), site_attrs)
        if not site_id:
            return False

        self.created_assets['site'] = site_id
        print(f"📍 Site: {site_name}")

        # Create Buildings, Floors, Rooms
        room_counter = 0
        device_counter = 0

        for building_config in scenario.get('buildings', []):
            building_name = building_config['name']
            building_id = self.create_asset(building_name, building_config.get('type', 'Building'))
            if not building_id:
                continue

            # Create Site -> Building relation
            if not self.create_relation(site_id, building_id):
                continue

            print(f"  🏢 Building: {building_name}")

            for floor_config in building_config.get('floors', []):
                floor_name = floor_config['name']
                floor_id = self.create_asset(floor_name, floor_config.get('type', 'Floor'))
                if not floor_id:
                    continue

                # Create Building -> Floor relation
                if not self.create_relation(building_id, floor_id):
                    continue

                for room_config in floor_config.get('rooms', []):
                    room_name = room_config['name']
                    room_attrs = {
                        'classification': room_config.get('classification'),
                        'area_sqm': room_config.get('area_sqm'),
                        'floor_plan': room_config.get('floorPlan')
                    }
                    room_attrs = {k: v for k, v in room_attrs.items() if v is not None}

                    room_id = self.create_asset(room_name, room_config.get('type', 'Room'), room_attrs)
                    if not room_id:
                        continue

                    # Create Floor -> Room relation
                    if not self.create_relation(floor_id, room_id):
                        continue

                    room_counter += 1
                    print(f"    🚪 Room {room_counter}: {room_name}")

                    # Store room configuration for .env generation
                    room_key = f"room_{room_counter}"
                    gateway_count = len(room_config.get('gateways', []))

                    # Calculate device counts for this room
                    room_device_count = 0
                    for gateway_config in room_config.get('gateways', []):
                        device_config = gateway_config.get('devices', {})
                        room_device_count += device_config.get('count', 0)

                    self.room_configurations[room_key] = {
                        'id': room_id,
                        'name': room_name,
                        'device_start': device_counter,
                        'device_end': device_counter + room_device_count - 1,
                        'device_count': room_device_count,
                        'gateway_count': gateway_count
                    }

                    device_counter += room_device_count

        return True

    def generate_env_file(self, scenario: Dict, env_output: str) -> bool:
        """Generate .env file for Java device creation"""
        print(f"\n📄 Generating environment file: {env_output}")

        env_content = [
            f"# Generated by Asset Provisioning Script",
            f"# Scenario: {scenario.get('scenarioName', 'Unknown')}",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Command: python {' '.join(sys.argv)}",
            "",
            f"# === Asset Hierarchy Information ===",
            f"HIERARCHY_CREATED=true",
            f"SITE_ID={self.created_assets.get('site', '')}",
            f"TOTAL_ROOMS={len(self.room_configurations)}",
            ""
        ]

        # Add room-specific configurations
        room_device_start = 0
        for room_key, room_info in self.room_configurations.items():
            if room_info['device_count'] > 0:
                env_content.extend([
                    f"# Room {room_key.replace('room_', '')}: {room_info['name']}",
                    f"ROOM_{room_key.replace('room_', '').upper()}_ID={room_info['id']}",
                    f"ROOM_{room_key.replace('room_', '').upper()}_NAME=\"{room_info['name']}\"",
                    f"ROOM_{room_key.replace('room_', '').upper()}_DEVICE_START={room_info['device_start']}",
                    f"ROOM_{room_key.replace('room_', '').upper()}_DEVICE_END={room_info['device_end']}",
                    f"ROOM_{room_key.replace('room_', '').upper()}_DEVICE_COUNT={room_info['device_count']}",
                    f"ROOM_{room_key.replace('room_', '').upper()}_GATEWAY_COUNT={room_info['gateway_count']}",
                    ""
                ])

        # Calculate totals
        total_devices = sum(room['device_count'] for room in self.room_configurations.values())
        total_gateways = sum(room['gateway_count'] for room in self.room_configurations.values())

        env_content.extend([
            f"# === Overall Device Configuration ===",
            f"TOTAL_DEVICES={total_devices}",
            f"TOTAL_GATEWAYS={total_gateways}",
            f"DEVICE_START_IDX=0",
            f"DEVICE_END_IDX={total_devices - 1 if total_devices > 0 else 0}",
            f"GATEWAY_START_IDX=0",
            f"GATEWAY_END_IDX={total_gateways - 1 if total_gateways > 0 else 0}",
            "",
            f"# === Performance Test Configuration ===",
            f"TEST_API=gateway",
            f"TEST_PAYLOAD_TYPE=EBMPAPST_FFU",
            f"DEVICE_CREATE_ON_START=true",
            f"GATEWAY_CREATE_ON_START=true",
            f"DEVICE_DELETE_ON_COMPLETE=false",
            f"GATEWAY_DELETE_ON_COMPLETE=false",
            ""
        ])

        try:
            with open(env_output, 'w') as f:
                f.write('\n'.join(env_content))

            print(f"✅ Environment file saved: {env_output}")
            return True

        except Exception as e:
            print(f"❌ Error saving environment file: {e}")
            return False

    def provision_scenario(self, scenario_file: str, env_output: str) -> bool:
        """Main provisioning method"""
        try:
            print(f"🚀 Starting asset provisioning...")
            print(f"📁 Scenario file: {scenario_file}")
            print(f"📄 Environment output: {env_output}")

            # Load scenario
            with open(scenario_file, 'r') as f:
                scenario = json.load(f)

            print(f"📋 Scenario: {scenario.get('scenarioName', 'Unknown')}")
            print(f"📝 Description: {scenario.get('description', 'No description')}")

            # Login
            if not self.login():
                return False

            # Create hierarchy
            if not self.create_hierarchy(scenario):
                return False

            # Generate .env file
            if not self.generate_env_file(scenario, env_output):
                return False

            # Summary
            total_devices = sum(room['device_count'] for room in self.room_configurations.values())
            total_gateways = sum(room['gateway_count'] for room in self.room_configurations.values())

            print(f"\n✅ Asset provisioning completed successfully!")
            print(f"📊 Summary:")
            print(f"   - Sites: 1")
            print(f"   - Buildings: {len([k for k in self.room_configurations.keys()])}")
            print(f"   - Rooms: {len(self.room_configurations)}")
            print(f"   - Total Devices (for Java): {total_devices}")
            print(f"   - Total Gateways (for Java): {total_gateways}")

            print(f"\n🎯 Next Steps:")
            print(f"   1. source {env_output}")
            print(f"   2. mvn spring-boot:run")

            return True

        except Exception as e:
            print(f"❌ Provisioning error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Asset Provisioning Script - Creates hierarchy and generates .env')
    parser.add_argument('scenario', help='Scenario JSON file path')
    parser.add_argument('--env-output', default='.env', help='Environment file output path (default: .env)')
    parser.add_argument('--creds', help='Credentials file path (default: test-scenarios/credentials.json)')
    parser.add_argument('--conflict', choices=['ask', 'skip', 'recreate'], default='ask',
                       help='How to handle conflicts with existing assets: ask (prompt), skip (use existing), recreate (delete + create new)')

    args = parser.parse_args()

    # Validate scenario file exists
    if not os.path.exists(args.scenario):
        print(f"❌ Scenario file not found: {args.scenario}")
        return 1

    # Provision assets
    provisioner = AssetProvisioner(args.creds, args.conflict)
    success = provisioner.provision_scenario(args.scenario, args.env_output)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())