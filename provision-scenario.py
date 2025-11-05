#!/usr/bin/env python3
"""
Provision ThingsBoard hierarchy from scenario configuration
Hierarchy: Site → Building → Floor → Room → Gateway → Devices
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List, Optional

DEFAULT_TB_URL = 'http://167.99.64.71:8080'
DEFAULT_TB_USERNAME = 'tenant@thingsboard.org'
DEFAULT_TB_PASSWORD = 'tenant'

class ThingsBoardProvisioner:
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.created_entities = {
            'sites': [],
            'buildings': [],
            'floors': [],
            'rooms': [],
            'gateways': [],
            'devices': []
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

    def get_asset_by_name(self, name: str) -> Optional[Dict]:
        """Get an asset by name"""
        try:
            response = requests.get(
                f"{self.url}/api/tenant/assetInfos?pageSize=1000&page=0",
                headers=self._get_headers()
            )
            response.raise_for_status()
            assets = response.json().get('data', [])
            for asset in assets:
                if asset['name'] == name:
                    return asset
            return None
        except Exception as e:
            print(f"  ✗ Failed to get asset by name: {e}")
            return None

    def get_device_by_name(self, name: str) -> Optional[Dict]:
        """Get a device by name"""
        try:
            response = requests.get(
                f"{self.url}/api/tenant/deviceInfos?pageSize=1000&page=0",
                headers=self._get_headers()
            )
            response.raise_for_status()
            devices = response.json().get('data', [])
            for device in devices:
                if device['name'] == name:
                    return device
            return None
        except Exception as e:
            return None

    def delete_entity(self, entity_id: str, entity_type: str) -> bool:
        """Delete an entity (asset or device)"""
        try:
            endpoint = "asset" if entity_type == "ASSET" else "device"
            response = requests.delete(
                f"{self.url}/api/{endpoint}/{entity_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return True
        except Exception as e:
            return False

    def create_asset(self, name: str, asset_type: str, label: str = None,
                     attributes: Dict = None) -> Optional[Dict]:
        """Create an asset (Site, Building, Floor, Room)"""
        # Check if asset with same name already exists
        existing = self.get_asset_by_name(name)
        if existing:
            print(f"  ⚠ Asset {name} already exists, deleting...")
            self.delete_entity(existing['id']['id'], 'ASSET')

        payload = {
            "name": name,
            "type": asset_type,
            "label": label or name
        }

        try:
            response = requests.post(
                f"{self.url}/api/asset",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            asset = response.json()
            asset_id = asset['id']['id']

            # Add attributes if provided
            if attributes:
                self.add_attributes(asset_id, 'ASSET', attributes)

            print(f"  ✓ Created {asset_type}: {name} (ID: {asset_id})")
            return asset
        except requests.exceptions.HTTPError as e:
            print(f"  ✗ Failed to create {asset_type} {name}: {e}")
            try:
                error_detail = e.response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"  ✗ Failed to create {asset_type} {name}: {e}")
            return None

    def set_device_credentials(self, device_id: str, device_name: str, access_token: str) -> bool:
        """Set device credentials (access token)"""
        try:
            # Get current credentials
            response = requests.get(
                f"{self.url}/api/device/{device_id}/credentials",
                headers=self._get_headers()
            )
            response.raise_for_status()
            credentials = response.json()

            # Update access token
            credentials['credentialsId'] = access_token

            # Save updated credentials
            response = requests.post(
                f"{self.url}/api/device/credentials",
                headers=self._get_headers(),
                json=credentials
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  ⚠ Failed to set credentials for {device_name}: {e}")
            return False

    def create_device(self, name: str, device_type: str = "EBMPAPST_FFU",
                      label: str = None, is_gateway: bool = False) -> Optional[Dict]:
        """Create a device (regular device or gateway)"""
        # Check if device with same name already exists
        existing = self.get_device_by_name(name)
        if existing:
            self.delete_entity(existing['id']['id'], 'DEVICE')

        payload = {
            "name": name,
            "type": device_type,
            "label": label or name
        }

        # Add gateway flag if this is a gateway device
        if is_gateway:
            payload["additionalInfo"] = {"gateway": True}

        try:
            response = requests.post(
                f"{self.url}/api/device",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            device = response.json()

            # For gateways, set access token to match device name
            # This is required for gateway performance tests to work
            if is_gateway:
                device_id = device['id']['id']
                if self.set_device_credentials(device_id, name, name):
                    print(f"  ✓ Gateway credentials: {name} → token: {name}")

            return device
        except Exception as e:
            print(f"  ✗ Failed to create device {name}: {e}")
            return None

    def create_relation(self, from_id: str, from_type: str, to_id: str,
                        to_type: str, relation_type: str = "Contains") -> bool:
        """Create a relation between two entities"""
        payload = {
            "from": {
                "entityType": from_type,
                "id": from_id
            },
            "to": {
                "entityType": to_type,
                "id": to_id
            },
            "type": relation_type,
            "typeGroup": "COMMON"
        }

        try:
            response = requests.post(
                f"{self.url}/api/relation",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  ✗ Failed to create relation: {e}")
            return False

    def add_attributes(self, entity_id: str, entity_type: str,
                       attributes: Dict) -> bool:
        """Add server attributes to an entity"""
        try:
            response = requests.post(
                f"{self.url}/api/plugins/telemetry/{entity_type}/{entity_id}/attributes/SERVER_SCOPE",
                headers=self._get_headers(),
                json=attributes
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  ✗ Failed to add attributes: {e}")
            return False

    def calculate_device_position(self, index: int, layout_config: Dict) -> tuple:
        """Calculate device xPos, yPos based on layout configuration

        Returns relative coordinates (0.0 to 1.0 range) for ThingsBoard floor plan positioning.
        Example: xPos=0.35 means 35% from left edge, yPos=0.6 means 60% from top edge.
        """
        layout = layout_config.get('layout', 'grid')

        if layout == 'grid':
            cols = layout_config.get('gridColumns', 6)
            # Use relative coordinates (0.0 to 1.0) for resolution independence
            start_x = layout_config.get('startX', 0.1)  # 10% from left edge
            start_y = layout_config.get('startY', 0.1)  # 10% from top edge
            spacing_x = layout_config.get('spacingX', 0.15)  # 15% horizontal spacing
            spacing_y = layout_config.get('spacingY', 0.15)  # 15% vertical spacing

            row = index // cols
            col = index % cols

            x_pos = start_x + (col * spacing_x)
            y_pos = start_y + (row * spacing_y)

            return (x_pos, y_pos)

        # Default: random or custom layout can be added here
        return (0.5, 0.5)  # Center of floor plan

    def validate_scenario(self, scenario: Dict) -> bool:
        """Validate scenario configuration before provisioning"""
        print(f"\n{'='*60}")
        print(f"Validating Scenario Configuration")
        print(f"{'='*60}\n")

        errors = []
        warnings = []

        # Count actual entities in the scenario
        actual_counts = {
            'sites': 1 if scenario.get('site') else 0,
            'buildings': len(scenario.get('buildings', [])),
            'floors': 0,
            'rooms': 0,
            'gateways': 0,
            'devices': 0
        }

        # Count floors, rooms, gateways, and devices
        for building in scenario.get('buildings', []):
            for floor in building.get('floors', []):
                actual_counts['floors'] += 1
                for room in floor.get('rooms', []):
                    actual_counts['rooms'] += 1

                    # Check one gateway per room rule (STRICT)
                    gateway_count = len(room.get('gateways', []))
                    if gateway_count == 0:
                        errors.append(f"Room '{room.get('name')}' has NO gateways (must have exactly 1)")
                    elif gateway_count > 1:
                        errors.append(f"Room '{room.get('name')}' has {gateway_count} gateways (must have exactly 1)")

                    for gateway in room.get('gateways', []):
                        actual_counts['gateways'] += 1

                        # Count devices for this gateway
                        device_config = gateway.get('devices', {})
                        start = device_config.get('start', 0)
                        end = device_config.get('end', 0)
                        count = device_config.get('count', 0)

                        # Validate device count matches range
                        expected_count = end - start + 1
                        if count != expected_count:
                            warnings.append(
                                f"Gateway '{gateway.get('name')}': "
                                f"count={count} but range {start}-{end} implies {expected_count} devices"
                            )

                        actual_counts['devices'] += count

        # Compare with declared totals
        declared_totals = scenario.get('totals', {})

        print("Validation Results:")
        print(f"\n{'Entity Type':<15} {'Declared':<12} {'Actual':<12} {'Status'}")
        print("-" * 60)

        for entity_type in ['sites', 'buildings', 'floors', 'rooms', 'gateways', 'devices']:
            declared = declared_totals.get(entity_type, 0)
            actual = actual_counts[entity_type]

            if declared != actual:
                status = "⚠ MISMATCH"
                warnings.append(
                    f"Total {entity_type}: declared={declared}, actual={actual}"
                )
            else:
                status = "✓ OK"

            print(f"{entity_type.capitalize():<15} {declared:<12} {actual:<12} {status}")

        # Print warnings
        if warnings:
            print(f"\n⚠ Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  - {warning}")

        # Print errors
        if errors:
            print(f"\n✗ Errors ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
            print(f"\n{'='*60}")
            print("❌ VALIDATION FAILED - Cannot proceed with provisioning")
            print(f"{'='*60}\n")
            return False

        # If only warnings, ask user to confirm
        if warnings:
            print(f"\n{'='*60}")
            print("⚠ Validation completed with warnings")
            print("You can update the 'totals' field or proceed anyway")
            print(f"{'='*60}\n")
            response = input("Proceed with provisioning? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Provisioning cancelled by user.")
                return False
        else:
            print(f"\n{'='*60}")
            print("✓ Validation passed - all checks OK")
            print(f"{'='*60}\n")

        return True

    def provision_scenario(self, scenario_file: str, scenario_data: Optional[Dict] = None) -> bool:
        """Provision entire scenario from JSON file or pre-loaded data"""
        print(f"\n{'='*60}")
        print(f"Provisioning Scenario: {scenario_file}")
        print(f"{'='*60}\n")

        # Load scenario
        scenario = scenario_data
        if scenario is None:
            try:
                with open(scenario_file, 'r') as f:
                    scenario = json.load(f)
            except Exception as e:
                print(f"✗ Failed to load scenario file: {e}")
                return False

        print(f"Scenario: {scenario.get('scenarioName')}")
        print(f"Description: {scenario.get('description')}\n")

        # Store scenario for later use (e.g., generating .env file)
        self.scenario = scenario

        # Validate scenario before provisioning
        if not self.validate_scenario(scenario):
            return False

        # Create Site
        site_config = scenario.get('site', {})
        site_attrs = {
            'address': site_config.get('address'),
            'latitude': site_config.get('latitude'),
            'longitude': site_config.get('longitude')
        }
        # Remove None values
        site_attrs = {k: v for k, v in site_attrs.items() if v is not None}

        site = self.create_asset(
            site_config['name'],
            site_config.get('type', 'Site'),
            site_config.get('name'),
            site_attrs
        )
        if not site:
            return False

        site_id = site['id']['id']
        self.created_entities['sites'].append(site)

        # Create Buildings
        for building_config in scenario.get('buildings', []):
            building_attrs = {
                'address': building_config.get('address'),
                'email': building_config.get('email'),
                'phone': building_config.get('phone'),
                'latitude': building_config.get('latitude'),
                'longitude': building_config.get('longitude')
            }
            # Remove None values
            building_attrs = {k: v for k, v in building_attrs.items() if v is not None}

            building = self.create_asset(
                building_config['name'],
                building_config.get('type', 'Building'),
                building_config.get('label'),
                building_attrs
            )
            if not building:
                continue

            building_id = building['id']['id']
            self.created_entities['buildings'].append(building)

            # Link Site → Building
            self.create_relation(site_id, 'ASSET', building_id, 'ASSET')

            # Create Floors
            for floor_config in building_config.get('floors', []):
                floor = self.create_asset(
                    floor_config['name'],
                    floor_config.get('type', 'Floor'),
                    floor_config.get('label')
                )
                if not floor:
                    continue

                floor_id = floor['id']['id']
                self.created_entities['floors'].append(floor)

                # Link Building → Floor
                self.create_relation(building_id, 'ASSET', floor_id, 'ASSET')

                # Create Rooms
                for room_config in floor_config.get('rooms', []):
                    room_attrs = {
                        'classification': room_config.get('classification'),
                        'area_sqm': room_config.get('area_sqm'),
                        'floorPlan': room_config.get('floorPlan')
                    }
                    room = self.create_asset(
                        room_config['name'],
                        room_config.get('type', 'Room'),
                        room_config.get('label'),
                        room_attrs
                    )
                    if not room:
                        continue

                    room_id = room['id']['id']
                    self.created_entities['rooms'].append(room)

                    # Link Floor → Room
                    self.create_relation(floor_id, 'ASSET', room_id, 'ASSET')

                    # Create Gateways (as devices with gateway flag)
                    for gateway_config in room_config.get('gateways', []):
                        # Gateway is a DEVICE with is_gateway=True, not an asset
                        gateway = self.create_device(
                            gateway_config['name'],
                            gateway_config.get('type', 'default'),
                            gateway_config.get('label'),
                            is_gateway=True
                        )
                        if not gateway:
                            continue

                        gateway_id = gateway['id']['id']
                        self.created_entities['gateways'].append(gateway)

                        # Add protocol as server attribute
                        protocol_attrs = {
                            'protocol': gateway_config.get('protocol', 'MQTT')
                        }
                        self.add_attributes(gateway_id, 'DEVICE', protocol_attrs)

                        # Link Room (ASSET) → Gateway (DEVICE)
                        self.create_relation(room_id, 'ASSET', gateway_id, 'DEVICE')

                        # Create Devices
                        device_config = gateway_config.get('devices', {})
                        prefix = device_config.get('prefix', 'DW')
                        start = device_config.get('start', 0)
                        end = device_config.get('end', 9)

                        print(f"    Creating {end - start + 1} devices for gateway {gateway_config['name']}...")
                        for i in range(start, end + 1):
                            device_name = f"{prefix}{i:08d}"
                            device = self.create_device(
                                device_name,
                                "EBMPAPST_FFU",
                                f"FFU Device {device_name}"
                            )
                            if device:
                                device_id = device['id']['id']
                                self.created_entities['devices'].append(device)

                                # Calculate and add device position attributes
                                device_index = i - start
                                x_pos, y_pos = self.calculate_device_position(device_index, device_config)
                                position_attrs = {
                                    'xPos': x_pos,
                                    'yPos': y_pos
                                }
                                self.add_attributes(device_id, 'DEVICE', position_attrs)

                                # Link Gateway (DEVICE) → Device (DEVICE)
                                self.create_relation(gateway_id, 'DEVICE', device_id, 'DEVICE')

        print(f"\n{'='*60}")
        print(f"Provisioning Complete!")
        print(f"{'='*60}\n")
        self.print_summary()
        self.generate_env_file()
        return True

    def generate_env_file(self):
        """Generate .env.ebmpapst-gateway configuration file from scenario"""
        print(f"\n{'='*60}")
        print(f"Generating Test Configuration")
        print(f"{'='*60}\n")

        scenario = self.scenario
        tb_config = scenario.get('thingsboard', {})
        test_config = scenario.get('testConfig', {})

        # Count total devices and gateways
        total_devices = len(self.created_entities['devices'])
        total_gateways = len(self.created_entities['gateways'])

        # Get gateway range for the test
        # Note: END_IDX is exclusive (like Python range), so END_IDX = total_gateways
        # For 2 gateways (indices 0, 1), START_IDX=0, END_IDX=2
        gateway_start_idx = 0
        gateway_end_idx = total_gateways

        env_content = f"""# ebmpapst FFU Performance Test - Gateway Mode Configuration
# Auto-generated from scenario: {scenario.get('scenarioName')}
# Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# ThingsBoard Server Configuration
REST_URL={tb_config.get('url', 'http://167.99.64.71:8080')}
REST_USERNAME={tb_config.get('username', 'tenant@thingsboard.org')}
REST_PASSWORD={tb_config.get('password', 'tenant')}
REST_POOL_SIZE=4

# MQTT Broker Configuration
MQTT_HOST={tb_config.get('mqtt_host', '167.99.64.71')}
MQTT_PORT={tb_config.get('mqtt_port', 1883)}

# SSL Configuration
MQTT_SSL_ENABLED=false
MQTT_SSL_KEY_STORE=
MQTT_SSL_KEY_STORE_PASSWORD=

# *** CRITICAL: Use GATEWAY mode ***
TEST_API=gateway

# Device API Protocol (MQTT for gateway)
DEVICE_API=MQTT

# Gateway Configuration
# IMPORTANT: Gateways created by provisioner have default credentials
GATEWAY_START_IDX={gateway_start_idx}
GATEWAY_END_IDX={gateway_end_idx}
GATEWAY_CREATE_ON_START=false  # Already created by provisioner
GATEWAY_DELETE_ON_COMPLETE=false

# Device Configuration
# These are child devices that communicate THROUGH the gateway
# Note: END_IDX is exclusive (like Python range), so END_IDX = total_devices
# For 60 devices (indices 0-59), START_IDX=0, END_IDX=60
DEVICE_START_IDX=0
DEVICE_END_IDX={total_devices}
DEVICE_CREATE_ON_START=false   # IMPORTANT: Let gateway auto-provision devices!
DEVICE_DELETE_ON_COMPLETE=false

# CRITICAL: In gateway mode, devices MUST be created by gateway connect API
# Setting DEVICE_CREATE_ON_START=false allows gateway to auto-provision

# Dashboard Configuration
DASHBOARD_CREATE_ON_START=false  # Create dashboards manually via ThingsBoard UI
DASHBOARD_DELETE_IF_EXISTS=false
DASHBOARD_TENANT=

# Test Payload Type
TEST_PAYLOAD_TYPE={test_config.get('payloadType', 'EBMPAPST_FFU')}

# Test Execution Configuration
WARMUP_ENABLED={str(test_config.get('warmupEnabled', True)).lower()}
TEST_ENABLED=true

# Message Rate Configuration
# Gateway mode: all devices send through gateway connections
MESSAGES_PER_SECOND={test_config.get('messagesPerSecond', total_devices)}
DURATION_IN_SECONDS={test_config.get('durationInSeconds', 86400)}

# Alarm Configuration
ALARMS_PER_SECOND=2
ALARM_STORM_START_SECOND=60
ALARM_STORM_END_SECOND=240

# Rule Chain Configuration
UPDATE_ROOT_RULE_CHAIN=false
REVERT_ROOT_RULE_CHAIN=false
RULE_CHAIN_NAME=root_rule_chain_ce.json

# Test Execution Mode
TEST_SEQUENTIAL=false

# Exit Configuration
EXIT_AFTER_COMPLETE=true
"""

        env_file = '.env.ebmpapst-gateway'
        with open(env_file, 'w') as f:
            f.write(env_content)

        print(f"✓ Test configuration generated: {env_file}")
        print(f"  - Gateways: {total_gateways}")
        print(f"  - Devices: {total_devices}")
        print(f"  - Message rate: {test_config.get('messagesPerSecond', total_devices)} msg/sec")
        print(f"  - Duration: {test_config.get('durationInSeconds', 86400)} seconds")
        print()

    def print_summary(self):
        """Print summary of created entities"""
        print(f"Summary:")
        print(f"  Sites:     {len(self.created_entities['sites'])}")
        print(f"  Buildings: {len(self.created_entities['buildings'])}")
        print(f"  Floors:    {len(self.created_entities['floors'])}")
        print(f"  Rooms:     {len(self.created_entities['rooms'])}")
        print(f"  Gateways:  {len(self.created_entities['gateways'])}")
        print(f"  Devices:   {len(self.created_entities['devices'])}")
        print()

        # Save entity IDs
        output_file = '/tmp/provisioned_entities.json'
        with open(output_file, 'w') as f:
            json.dump(self.created_entities, f, indent=2)
        print(f"Entity IDs saved to: {output_file}")
        print()

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
    parser = argparse.ArgumentParser(description='Provision ThingsBoard hierarchy from scenario')
    parser.add_argument('scenario', help='Path to scenario JSON file')
    parser.add_argument('--credentials', default='test-scenarios/credentials.json',
                        help='Path to credentials.json file (default: test-scenarios/credentials.json)')
    parser.add_argument('--url', default=None,
                        help='ThingsBoard server URL (overrides credentials.json and env)')
    parser.add_argument('--username', default=None,
                        help='ThingsBoard username (overrides credentials.json and env)')
    parser.add_argument('--password', default=None,
                        help='ThingsBoard password (overrides credentials.json and env)')

    args = parser.parse_args()

    try:
        with open(args.scenario, 'r') as scenario_file:
            scenario_data = json.load(scenario_file)
    except Exception as e:
        print(f"✗ Failed to load scenario file '{args.scenario}': {e}")
        sys.exit(1)

    # Load credentials from credentials.json
    creds_config = load_credentials(args.credentials) or {}

    # Credential priority: CLI args > credentials.json > environment variables > defaults
    resolved_url = args.url or creds_config.get('url') or os.getenv('REST_URL') or DEFAULT_TB_URL
    resolved_username = args.username or creds_config.get('username') or os.getenv('REST_USERNAME') or DEFAULT_TB_USERNAME
    resolved_password = args.password or creds_config.get('password') or os.getenv('REST_PASSWORD') or DEFAULT_TB_PASSWORD

    # Validate that credentials are provided
    if not resolved_username or not resolved_password:
        print("✗ Error: ThingsBoard credentials not provided!")
        print("  Please provide credentials via one of:")
        print(f"    1. Credentials file: {args.credentials}")
        print("    2. Command-line: --username, --password")
        print("    3. Environment: REST_USERNAME, REST_PASSWORD")
        sys.exit(1)

    print(f"Using ThingsBoard endpoint {resolved_url} (user: {resolved_username})")

    provisioner = ThingsBoardProvisioner(resolved_url, resolved_username, resolved_password)

    if not provisioner.login():
        sys.exit(1)

    if not provisioner.provision_scenario(args.scenario, scenario_data):
        sys.exit(1)

    print("✓ All done!")

if __name__ == '__main__':
    main()
