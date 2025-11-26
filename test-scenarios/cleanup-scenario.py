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
Enhanced ThingsBoard Cleanup Script
Handles missing entities gracefully and provides multiple cleanup options
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List, Optional, Tuple

# Default credentials file location
DEFAULT_CREDENTIALS_FILE = '../credentials.json'

def load_credentials(creds_file: str = None) -> Dict[str, str]:
    """Load credentials from JSON file with user-friendly fallbacks"""
    if creds_file is None:
        creds_file = DEFAULT_CREDENTIALS_FILE

    if not os.path.exists(creds_file):
        # Create helpful error message with example
        print(f"❌ Credentials file not found: {creds_file}")
        print(f"\n📝 Please create a credentials file at: {creds_file}")
        print(f" with the following content:\n")

        example_content = f'''{{
  "thingsboard": {{
    "url": "https://your-thingsboard-server.com",
    "username": "your-email@domain.com",
    "password": "your-password"
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
        raise ValueError(f"Invalid JSON format in {creds_file}: {e}")

    tb_creds = creds.get('thingsboard', {})
    if not tb_creds:
        print(f"❌ No 'thingsboard' section found in {creds_file}")
        print(f"\n📝 Your credentials file should have a 'thingsboard' section:")
        print(f'"thingsboard": {"url": "...", "username": "...", "password": "..."}')
        raise ValueError(f"No 'thingsboard' section found in {creds_file}")

    required_fields = ['url', 'username', 'password']
    missing = [field for field in required_fields if not tb_creds.get(field)]
    if missing:
        print(f"❌ Missing required fields in {creds_file}: {missing}")
        print(f"\n📝 Please add these fields to your 'thingsboard' section:")
        for field in missing:
            print(f'    "{field}": "your_{field}"')
        raise ValueError(f"Missing required fields in {creds_file}: {missing}")

    return tb_creds

class ThingsBoardCleaner:
    def __init__(self, url: str, username: str, password: str, dry_run: bool = False):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.dry_run = dry_run
        self.stats = {
            'devices': {'found': 0, 'deleted': 0, 'missing': 0, 'failed': 0},
            'assets': {'found': 0, 'deleted': 0, 'missing': 0, 'failed': 0}
        }

    def login(self) -> bool:
        """Login to ThingsBoard and get JWT token"""
        try:
            response = requests.post(
                f"{self.url}/api/auth/login",
                json={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
            self.token = response.json().get('token')
            print(f"✓ Logged in as {self.username}")
            if self.dry_run:
                print("🔍 DRY RUN MODE - No actual deletions will be performed")
            return True
        except Exception as e:
            print(f"✗ Login failed: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {self.token}"
        }

    def _check_entity_exists(self, entity_type: str, entity_id: str) -> bool:
        """Check if an entity exists before attempting deletion"""
        try:
            response = requests.get(
                f"{self.url}/api/{entity_type}/{entity_id}",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except:
            return False

    def delete_device(self, device_id: str, device_name: str) -> Tuple[bool, str]:
        """Delete a device with better error handling"""
        self.stats['devices']['found'] += 1

        # Check if device exists first
        if not self._check_entity_exists('device', device_id):
            self.stats['devices']['missing'] += 1
            return False, f"Device {device_name} does not exist"

        if self.dry_run:
            print(f"  🔍 DRY RUN: Would delete device: {device_name}")
            self.stats['devices']['deleted'] += 1
            return True, "Would be deleted (dry run)"

        try:
            response = requests.delete(
                f"{self.url}/api/device/{device_id}",
                headers=self._get_headers()
            )

            if response.status_code == 404:
                self.stats['devices']['missing'] += 1
                return False, f"Device {device_name} not found"
            elif response.status_code == 204:
                self.stats['devices']['deleted'] += 1
                print(f"  ✓ Deleted device: {device_name}")
                return True, "Deleted successfully"
            else:
                response.raise_for_status()
                self.stats['devices']['failed'] += 1
                return False, f"Unexpected response: {response.status_code}"

        except requests.exceptions.HTTPError as e:
            self.stats['devices']['failed'] += 1
            if "404" in str(e):
                return False, f"Device {device_name} not found"
            else:
                return False, f"HTTP error: {e}"
        except Exception as e:
            self.stats['devices']['failed'] += 1
            return False, f"Error: {e}"

    def delete_asset(self, asset_id: str, asset_name: str) -> Tuple[bool, str]:
        """Delete an asset with better error handling"""
        self.stats['assets']['found'] += 1

        # Check if asset exists first
        if not self._check_entity_exists('asset', asset_id):
            self.stats['assets']['missing'] += 1
            return False, f"Asset {asset_name} does not exist"

        if self.dry_run:
            print(f"  🔍 DRY RUN: Would delete asset: {asset_name}")
            self.stats['assets']['deleted'] += 1
            return True, "Would be deleted (dry run)"

        try:
            response = requests.delete(
                f"{self.url}/api/asset/{asset_id}",
                headers=self._get_headers()
            )

            if response.status_code == 404:
                self.stats['assets']['missing'] += 1
                return False, f"Asset {asset_name} not found"
            elif response.status_code == 204:
                self.stats['assets']['deleted'] += 1
                print(f"  ✓ Deleted asset: {asset_name}")
                return True, "Deleted successfully"
            else:
                response.raise_for_status()
                self.stats['assets']['failed'] += 1
                return False, f"Unexpected response: {response.status_code}"

        except requests.exceptions.HTTPError as e:
            self.stats['assets']['failed'] += 1
            if "404" in str(e):
                return False, f"Asset {asset_name} not found"
            else:
                return False, f"HTTP error: {e}"
        except Exception as e:
            self.stats['assets']['failed'] += 1
            return False, f"Error: {e}"

    def cleanup_from_file(self, entities_file: str) -> bool:
        """Clean up entities from a JSON file"""
        print(f"============================================================")
        print(f"Cleaning up from: {entities_file}")
        print("============================================================")

        if not os.path.exists(entities_file):
            print(f"✗ Entities file not found: {entities_file}")
            return False

        try:
            with open(entities_file, 'r') as f:
                entities = json.load(f)

            success = True

            # Delete devices first (to avoid relation conflicts)
            if 'devices' in entities and entities['devices']:
                print(f"\n📱 Deleting {len(entities['devices'])} Devices...")
                for device_id in entities['devices']:
                    device_name = device_id.split('/')[-1] if '/' in device_id else device_id
                    result, message = self.delete_device(device_id, device_name)
                    if not result and "not found" not in message:
                        success = False

            # Delete assets
            for asset_type in ['gateways', 'rooms', 'floors', 'buildings', 'sites']:
                if asset_type in entities and entities[asset_type]:
                    print(f"\n🏢 Deleting {len(entities[asset_type])} {asset_type.title()}...")
                    for asset_id in entities[asset_type]:
                        asset_name = asset_id.split('/')[-1] if '/' in asset_id else asset_id
                        result, message = self.delete_asset(asset_id, asset_name)
                        if not result and "not found" not in message:
                            success = False

            return success

        except Exception as e:
            print(f"✗ Error processing entities file: {e}")
            return False

    def cleanup_by_pattern(self, pattern: str = None, device_type: str = None) -> bool:
        """Clean up entities by name pattern or type"""
        print(f"============================================================")
        print(f"Cleaning up by pattern: {pattern or 'all'}")
        print("============================================================")

        try:
            # Search for entities matching the pattern
            entities_to_delete = []

            if not device_type or device_type in ['device', 'all']:
                print("\n📱 Searching for devices...")
                devices = self._search_entities('device', pattern)
                entities_to_delete.extend([('device', d['id']['id'], d['name']) for d in devices])

            if not device_type or device_type in ['asset', 'all']:
                print("\n🏢 Searching for assets...")
                assets = self._search_entities('asset', pattern)
                entities_to_delete.extend([('asset', a['id']['id'], a['name']) for a in assets])

            if not entities_to_delete:
                print("✓ No entities found matching the pattern")
                return True

            print(f"\n🎯 Found {len(entities_to_delete)} entities to delete:")

            # Confirm deletion
            for entity_type, entity_id, entity_name in entities_to_delete[:10]:  # Show first 10
                print(f"  {entity_type}: {entity_name}")

            if len(entities_to_delete) > 10:
                print(f"  ... and {len(entities_to_delete) - 10} more")

            if not self.dry_run:
                response = input(f"\n⚠️  Delete {len(entities_to_delete)} entities? (yes/no): ")
                if response.lower() != 'yes':
                    print("❌ Cleanup cancelled")
                    return False

            # Delete entities
            success = True
            for entity_type, entity_id, entity_name in entities_to_delete:
                if entity_type == 'device':
                    result, message = self.delete_device(entity_id, entity_name)
                else:
                    result, message = self.delete_asset(entity_id, entity_name)

                if not result and "not found" not in message:
                    success = False

            return success

        except Exception as e:
            print(f"✗ Error during pattern cleanup: {e}")
            return False

    def _search_entities(self, entity_type: str, pattern: str = None) -> List[Dict]:
        """Search for entities by name pattern"""
        try:
            page_size = 100
            page = 0
            entities = []

            # Fetch all entities first
            while True:
                params = {
                    'pageSize': page_size,
                    'page': page
                }

                # Use correct ThingsBoard v4 API endpoints
                endpoint = f"{self.url}/api/tenant/{entity_type}s"
                response = requests.get(
                    endpoint,
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()

                data = response.json()
                page_entities = data.get('data', [])
                entities.extend(page_entities)

                if len(page_entities) < page_size:
                    break

                page += 1

            # Filter entities locally if pattern provided
            if pattern:
                import fnmatch
                filtered_entities = []
                for entity in entities:
                    entity_name = entity.get('name', '')
                    if fnmatch.fnmatch(entity_name.lower(), pattern.lower()):
                        filtered_entities.append(entity)
                return filtered_entities

            return entities

        except Exception as e:
            print(f"✗ Error searching {entity_type}s: {e}")
            return []

    def cleanup_all_test_data(self) -> bool:
        """Clean up all test data (devices and assets with specific naming patterns)"""
        print(f"============================================================")
        print("Cleaning up ALL test data")
        print("============================================================")

        patterns = [
            "DW*",     # FFU devices
            "GW*",     # Gateway devices (note: only devices, no assets)
            "Test*",   # Test entities
            "Demo*",   # Demo entities
            "ST*",     # Smart tracker devices
            "SM*",     # Smart meter devices
            "Site*",   # Site assets
            "Building*", # Building assets
            "Floor*",  # Floor assets
            "Room*",   # Room assets
        ]

        success = True
        total_deleted = 0

        for pattern in patterns:
            print(f"\n🔍 Cleaning pattern: {pattern}")
            try:
                entities = self._search_entities('device', pattern)
                assets = self._search_entities('asset', pattern)

                for device in entities:
                    result, _ = self.delete_device(device['id']['id'], device['name'])
                    if result or "not found" in _:
                        total_deleted += 1

                for asset in assets:
                    result, _ = self.delete_asset(asset['id']['id'], asset['name'])
                    if result or "not found" in _:
                        total_deleted += 1

            except Exception as e:
                print(f"✗ Error with pattern {pattern}: {e}")
                success = False

        print(f"\n📊 Total entities processed: {total_deleted}")
        return success

    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "=" * 60)
        print("📊 CLEANUP SUMMARY")
        print("=" * 60)

        for entity_type in ['devices', 'assets']:
            stats = self.stats[entity_type]
            print(f"\n{entity_type.title()}:")
            print(f"  Found: {stats['found']}")
            print(f"  Deleted: {stats['deleted']}")
            print(f"  Missing: {stats['missing']}")
            print(f"  Failed: {stats['failed']}")

        total_found = self.stats['devices']['found'] + self.stats['assets']['found']
        total_deleted = self.stats['devices']['deleted'] + self.stats['assets']['deleted']
        total_missing = self.stats['devices']['missing'] + self.stats['assets']['missing']
        total_failed = self.stats['devices']['failed'] + self.stats['assets']['failed']

        print(f"\n🎯 Overall Results:")
        print(f"  Total Found: {total_found}")
        print(f"  Total Deleted: {total_deleted}")
        print(f"  Already Missing: {total_missing}")
        print(f"  Failed: {total_failed}")

        if total_found > 0:
            success_rate = (total_deleted + total_missing) / total_found * 100
            print(f"  Success Rate: {success_rate:.1f}%")

        if self.dry_run:
            print(f"\n🔍 DRY RUN COMPLETED - No actual deletions performed")

        status = "✅ SUCCESS" if total_failed == 0 else "⚠️  PARTIAL SUCCESS"
        print(f"\n{status}")


def main():
    parser = argparse.ArgumentParser(description='Enhanced ThingsBoard Cleanup Script')
    parser.add_argument('--url', help='ThingsBoard URL (required if not using --credentials)')
    parser.add_argument('--username', help='ThingsBoard username (required if not using --credentials)')
    parser.add_argument('--password', help='ThingsBoard password (required if not using --credentials)')
    parser.add_argument('--credentials', help='Credentials JSON file path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--file', help='Clean up from entities file')
    parser.add_argument('--pattern', help='Clean up entities matching name pattern')
    parser.add_argument('--type', choices=['device', 'asset', 'all'], default='all', help='Entity type to clean up')
    parser.add_argument('--all-test-data', action='store_true', help='Clean up all test data (DW*, GW*, Test*, Demo*, etc.)')

    args = parser.parse_args()

    # Handle credentials
    try:
        if args.credentials:
            creds = load_credentials(args.credentials)
            url = creds['url']
            username = creds['username']
            password = creds['password']
        elif args.url and args.username and args.password:
            # Use command line credentials
            url = args.url
            username = args.username
            password = args.password
        else:
            # Try to load from default credentials file
            creds = load_credentials()
            url = creds['url']
            username = creds['username']
            password = creds['password']
    except Exception as e:
        print(f"❌ Credentials error: {e}")
        print("Please provide credentials via:")
        print("  1. --credentials <file>")
        print("  2. --url <url> --username <user> --password <pass>")
        print(f"  3. Create {DEFAULT_CREDENTIALS_FILE}")
        return 1

    # Create cleaner
    cleaner = ThingsBoardCleaner(url, username, password, args.dry_run)

    # Login
    if not cleaner.login():
        return 1

    success = True

    # Execute cleanup based on arguments
    if args.file:
        success &= cleaner.cleanup_from_file(args.file)
    elif args.pattern:
        success &= cleaner.cleanup_by_pattern(args.pattern, args.type)
    elif args.all_test_data:
        success &= cleaner.cleanup_all_test_data()
    else:
        # Default: clean up from file if it exists, otherwise show help
        entities_file = '/tmp/provisioned_entities.json'
        if os.path.exists(entities_file):
            success &= cleaner.cleanup_from_file(entities_file)
        else:
            print("❌ No cleanup method specified and entities file not found.")
            print("Use --file, --pattern, or --all-test-data")
            print("Or create /tmp/provisioned_entities.json")
            return 1

    # Print summary
    cleaner.print_summary()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())