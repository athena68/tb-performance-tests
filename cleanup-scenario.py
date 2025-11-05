#!/usr/bin/env python3
"""
Clean up ThingsBoard entities created by scenario provisioner
Uses /tmp/provisioned_entities.json if available, or cleans by pattern
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List, Optional

class ThingsBoardCleaner:
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None

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

    def delete_device(self, device_id: str, device_name: str) -> bool:
        """Delete a device"""
        try:
            response = requests.delete(
                f"{self.url}/api/device/{device_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            print(f"  ✓ Deleted device: {device_name}")
            return True
        except Exception as e:
            print(f"  ✗ Failed to delete device {device_name}: {e}")
            return False

    def delete_asset(self, asset_id: str, asset_name: str) -> bool:
        """Delete an asset"""
        try:
            response = requests.delete(
                f"{self.url}/api/asset/{asset_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            print(f"  ✓ Deleted asset: {asset_name}")
            return True
        except Exception as e:
            print(f"  ✗ Failed to delete asset {asset_name}: {e}")
            return False

    def cleanup_from_file(self, file_path: str) -> bool:
        """Clean up entities from provisioned_entities.json file"""
        print(f"\n{'='*60}")
        print(f"Cleaning up from: {file_path}")
        print(f"{'='*60}\n")

        try:
            with open(file_path, 'r') as f:
                entities = json.load(f)
        except Exception as e:
            print(f"✗ Failed to load file: {e}")
            return False

        deleted_counts = {
            'devices': 0,
            'gateways': 0,
            'rooms': 0,
            'floors': 0,
            'buildings': 0,
            'sites': 0
        }

        # Delete in reverse order (bottom-up)
        # Devices first
        print("Deleting FFU Devices...")
        for device in entities.get('devices', []):
            if self.delete_device(device['id']['id'], device['name']):
                deleted_counts['devices'] += 1

        # Gateways (these are devices too)
        print("\nDeleting Gateways...")
        for gateway in entities.get('gateways', []):
            if self.delete_device(gateway['id']['id'], gateway['name']):
                deleted_counts['gateways'] += 1

        # Rooms
        print("\nDeleting Rooms...")
        for room in entities.get('rooms', []):
            if self.delete_asset(room['id']['id'], room['name']):
                deleted_counts['rooms'] += 1

        # Floors
        print("\nDeleting Floors...")
        for floor in entities.get('floors', []):
            if self.delete_asset(floor['id']['id'], floor['name']):
                deleted_counts['floors'] += 1

        # Buildings
        print("\nDeleting Buildings...")
        for building in entities.get('buildings', []):
            if self.delete_asset(building['id']['id'], building['name']):
                deleted_counts['buildings'] += 1

        # Sites
        print("\nDeleting Sites...")
        for site in entities.get('sites', []):
            if self.delete_asset(site['id']['id'], site['name']):
                deleted_counts['sites'] += 1

        print(f"\n{'='*60}")
        print(f"Cleanup Summary:")
        print(f"{'='*60}")
        for entity_type, count in deleted_counts.items():
            print(f"  {entity_type.capitalize():12} : {count}")
        print(f"{'='*60}\n")

        return True

    def cleanup_by_pattern(self, device_prefix: str = "DW", gateway_prefix: str = "GW",
                          asset_patterns: List[str] = None) -> bool:
        """Clean up entities by name patterns"""
        print(f"\n{'='*60}")
        print(f"Cleaning up by pattern...")
        print(f"{'='*60}\n")

        deleted_counts = {
            'devices': 0,
            'gateways': 0,
            'assets': 0
        }

        # Get all devices
        print("Fetching devices...")
        response = requests.get(
            f"{self.url}/api/tenant/deviceInfos?pageSize=1000&page=0",
            headers=self._get_headers()
        )
        response.raise_for_status()
        devices = response.json().get('data', [])

        # Delete devices matching pattern
        print(f"\nDeleting devices with prefix '{device_prefix}'...")
        for device in devices:
            if device['name'].startswith(device_prefix):
                if self.delete_device(device['id']['id'], device['name']):
                    deleted_counts['devices'] += 1

        # Delete gateways matching pattern
        print(f"\nDeleting gateways with prefix '{gateway_prefix}'...")
        for device in devices:
            if device['name'].startswith(gateway_prefix):
                if self.delete_device(device['id']['id'], device['name']):
                    deleted_counts['gateways'] += 1

        # Get all assets
        if asset_patterns:
            print("\nFetching assets...")
            response = requests.get(
                f"{self.url}/api/tenant/assetInfos?pageSize=1000&page=0",
                headers=self._get_headers()
            )
            response.raise_for_status()
            assets = response.json().get('data', [])

            # Delete assets matching patterns
            print(f"\nDeleting assets matching patterns: {asset_patterns}...")
            for asset in assets:
                for pattern in asset_patterns:
                    if pattern in asset['name']:
                        if self.delete_asset(asset['id']['id'], asset['name']):
                            deleted_counts['assets'] += 1
                        break

        print(f"\n{'='*60}")
        print(f"Cleanup Summary:")
        print(f"{'='*60}")
        for entity_type, count in deleted_counts.items():
            print(f"  {entity_type.capitalize():12} : {count}")
        print(f"{'='*60}\n")

        return True

def load_credentials(credentials_path: str = 'test-scenarios/credentials.json') -> Optional[Dict]:
    """Load ThingsBoard credentials from credentials.json file"""
    try:
        if os.path.exists(credentials_path):
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return creds.get('thingsboard', {})
    except Exception as e:
        print(f"⚠ Warning: Failed to load credentials from {credentials_path}: {e}")
    return None

def main():
    parser = argparse.ArgumentParser(description='Clean up ThingsBoard scenario entities')
    parser.add_argument('--credentials', default='test-scenarios/credentials.json',
                        help='Path to credentials.json file (default: test-scenarios/credentials.json)')
    parser.add_argument('--url', default=None,
                        help='ThingsBoard server URL (overrides credentials.json and env)')
    parser.add_argument('--username', default=None,
                        help='ThingsBoard username (overrides credentials.json and env)')
    parser.add_argument('--password', default=None,
                        help='ThingsBoard password (overrides credentials.json and env)')
    parser.add_argument('--file', default='/tmp/provisioned_entities.json',
                        help='Path to provisioned_entities.json file')
    parser.add_argument('--pattern', action='store_true',
                        help='Use pattern matching instead of file')
    parser.add_argument('--device-prefix', default='DW',
                        help='Device name prefix (default: DW)')
    parser.add_argument('--gateway-prefix', default='GW',
                        help='Gateway name prefix (default: GW)')
    parser.add_argument('--assets', nargs='+',
                        help='Asset name patterns to delete')

    args = parser.parse_args()

    # Load credentials from credentials.json
    creds_config = load_credentials(args.credentials) or {}

    # Credential priority: CLI args > credentials.json > environment variables
    resolved_url = args.url or creds_config.get('url') or os.getenv('REST_URL')
    resolved_username = args.username or creds_config.get('username') or os.getenv('REST_USERNAME')
    resolved_password = args.password or creds_config.get('password') or os.getenv('REST_PASSWORD')

    # Validate that credentials are provided
    if not resolved_url or not resolved_username or not resolved_password:
        print("✗ Error: ThingsBoard credentials not provided!")
        print("  Please provide credentials via one of:")
        print(f"    1. Credentials file: {args.credentials}")
        print("    2. Command-line: --url, --username, --password")
        print("    3. Environment: REST_URL, REST_USERNAME, REST_PASSWORD")
        sys.exit(1)

    cleaner = ThingsBoardCleaner(resolved_url, resolved_username, resolved_password)

    if not cleaner.login():
        sys.exit(1)

    if args.pattern:
        # Cleanup by pattern
        success = cleaner.cleanup_by_pattern(
            device_prefix=args.device_prefix,
            gateway_prefix=args.gateway_prefix,
            asset_patterns=args.assets
        )
    else:
        # Cleanup from file
        if not os.path.exists(args.file):
            print(f"✗ File not found: {args.file}")
            print(f"  Use --pattern to clean up by name patterns instead")
            sys.exit(1)

        success = cleaner.cleanup_from_file(args.file)

    if success:
        print("✓ Cleanup completed successfully!")
    else:
        print("✗ Cleanup failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
