#!/usr/bin/env python3
"""
Enhanced ThingsBoard Provisioner with Configurable Attributes
Hierarchy: Site → Building → Floor → Room → Gateway → Devices
Uses YAML-based attribute configuration system
"""

import os
import sys
import json
import requests
import argparse
import time
from typing import Dict, List, Optional

# Add config directory to path for attribute loading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

# Load default credentials from credentials.json
DEFAULT_CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
DEFAULT_TB_URL = None
DEFAULT_TB_USERNAME = None
DEFAULT_TB_PASSWORD = None

def load_default_credentials():
    """Load default ThingsBoard credentials from credentials.json"""
    global DEFAULT_TB_URL, DEFAULT_TB_USERNAME, DEFAULT_TB_PASSWORD

    if os.path.exists(DEFAULT_CREDENTIALS_FILE):
        try:
            with open(DEFAULT_CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                tb_creds = creds.get('thingsboard', {})
                DEFAULT_TB_URL = tb_creds.get('url', 'https://demo.thingsboard.io/').rstrip('/')
                DEFAULT_TB_USERNAME = tb_creds.get('username')
                DEFAULT_TB_PASSWORD = tb_creds.get('password')

                if not DEFAULT_TB_USERNAME or not DEFAULT_TB_PASSWORD:
                    raise ValueError(f"Missing username or password in {DEFAULT_CREDENTIALS_FILE}")
        except Exception as e:
            print(f"❌ Error: Could not load credentials file: {e}")
            print(f"  Please fix {DEFAULT_CREDENTIALS_FILE} or use --credentials parameter")
            DEFAULT_TB_URL = None
            DEFAULT_TB_USERNAME = None
            DEFAULT_TB_PASSWORD = None
    else:
        print(f"❌ Error: Credentials file not found at {DEFAULT_CREDENTIALS_FILE}")
        print(f"  Please create {DEFAULT_CREDENTIALS_FILE} or use --credentials parameter")
        DEFAULT_TB_URL = None
        DEFAULT_TB_USERNAME = None
        DEFAULT_TB_PASSWORD = None

# Load credentials at module import
load_default_credentials()

class ThingsBoardProvisioner:
    def __init__(self, url: str, username: str, password: str, use_configurable_attrs: bool = True):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.use_configurable_attrs = use_configurable_attrs
        self.created_entities = {
            'sites': [],
            'buildings': [],
            'floors': [],
            'rooms': [],
            'gateways': [],
            'devices': []
        }

        # Initialize attribute loader if enabled
        if use_configurable_attrs:
            try:
                from attribute_loader import load_asset_attributes, load_device_attributes
                self.load_asset_attributes = load_asset_attributes
                self.load_device_attributes = load_device_attributes
                print("✓ Configurable attributes enabled")
            except Exception as e:
                print(f"⚠ Configurable attributes failed, using fallback: {e}")
                self.use_configurable_attrs = False
                self.load_asset_attributes = None
                self.load_device_attributes = None
        else:
            self.load_asset_attributes = None
            self.load_device_attributes = None

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

    def create_asset(self, name: str, asset_type: str, label: str, attributes: Dict[str, any]) -> Optional[str]:
        """Create asset with configurable attributes"""
        try:
            # Try configurable attributes first
            if self.use_configurable_attrs and self.load_asset_attributes:
                try:
                    config_attrs = self.load_asset_attributes(asset_type.lower(), {
                        **attributes,  # Pass existing attributes as context
                        'address': attributes.get('address'),
                        'latitude': attributes.get('latitude'),
                        'longitude': attributes.get('longitude'),
                        'classification': attributes.get('classification'),
                        'area_sqm': attributes.get('area_sqm'),
                        'building_type': attributes.get('building_type'),
                        'site_type': attributes.get('site_type')
                    })
                    # Merge configurable attrs with passed attributes (config takes precedence)
                    attributes = {**attributes, **config_attrs}
                    print(f"  ✓ Loaded {len(config_attrs)} configurable attributes for {asset_type}")
                except Exception as e:
                    print(f"  ⚠ Configurable attributes failed for {asset_type}, using fallback: {e}")

            asset_payload = {
                "name": name,
                "type": asset_type,
                "label": label,
                "assetProfileId": {
                    "entityType": "ASSET_PROFILE",
                    "id": "3d60ab70-bf80-11f0-9dac-f14aa7f7559f"
                }
            }

            # Add attributes if any
            if attributes:
                asset_payload["attributes"] = attributes

            response = requests.post(
                f"{self.url}/api/asset",
                headers=self._get_headers(),
                json=asset_payload
            )

            # Handle response
            if response.status_code == 400:
                # Asset already exists - delete and recreate like original script
                response_data = response.json()
                if response_data.get('message', '').startswith('Asset with such name already exists'):
                    print(f"  ⚠ Asset {name} already exists, deleting and recreating...")
                    # Find and delete existing asset
                    try:
                        search_response = requests.get(
                            f"{self.url}/api/tenant/assets?pageSize=100&page=0&assetName={name}",
                            headers=self._get_headers()
                        )
                        if search_response.status_code == 200:
                            assets = search_response.json().get('data', [])
                            for asset in assets:
                                if asset.get('name') == name:
                                    delete_response = requests.delete(
                                        f"{self.url}/api/asset/{asset['id']['id']}",
                                        headers=self._get_headers()
                                    )
                                    if delete_response.status_code in [200, 204]:
                                        print(f"  ✓ Deleted existing asset {name}")
                                        break
                    except Exception as delete_e:
                        print(f"  ⚠ Failed to delete existing asset: {delete_e}")
                        return None

                    # Retry creating the asset after deletion
                    response = requests.post(
                        f"{self.url}/api/asset",
                        headers=self._get_headers(),
                        json=asset_payload
                    )
                    if response.status_code not in [200, 201]:
                        print(f"  Debug - Retry failed: {response.text}")
                        return None
                else:
                    print(f"  Debug - Request payload: {json.dumps(asset_payload, indent=2)}")
                    print(f"  Debug - Response: {response.text}")
                    return None
            elif response.status_code not in [200, 201]:
                print(f"  Debug - HTTP {response.status_code} - Request payload: {json.dumps(asset_payload, indent=2)}")
                print(f"  Debug - HTTP {response.status_code} - Response: {response.text}")
                return None
            asset_id = response.json()['id']['id']
            print(f"✓ Created asset: {name} (Type: {asset_type})")

            # Log some key attributes
            if attributes:
                key_attrs = list(attributes.keys())[:3]  # Show first 3 attributes
                print(f"  Attributes: {', '.join(key_attrs)}{'...' if len(attributes) > 3 else ''}")

            return asset_id
        except Exception as e:
            print(f"✗ Failed to create asset {name}: {e}")
            return None

    def create_device(self, name: str, device_type: str, label: str, device_index: int = 0, context: Dict = None) -> Optional[str]:
        """Create device with configurable attributes"""
        try:
            attributes = {}

            # Try configurable attributes first
            if self.use_configurable_attrs and self.load_device_attributes:
                try:
                    attributes = self.load_device_attributes(device_type.lower().replace('_', ''), device_index, context or {})
                    print(f"  ✓ Loaded {len(attributes)} configurable attributes for {device_type}")
                except Exception as e:
                    print(f"  ⚠ Configurable attributes failed for {device_type}, using fallback: {e}")
                    attributes = {}

            device_payload = {
                "name": name,
                "type": device_type,
                "label": label
            }

            # Add attributes if any
            if attributes:
                device_payload["attributes"] = attributes

            response = requests.post(
                f"{self.url}/api/device",
                headers=self._get_headers(),
                json=device_payload
            )

            # Handle response
            if response.status_code == 400:
                # Device already exists - this is normal during re-runs
                response_data = response.json()
                if response_data.get('message', '').startswith('Device with such name already exists'):
                    print(f"  ⚠ Device {name} already exists, skipping creation")
                    return None
                elif response_data.get('message', '').startswith('Devices limit reached'):
                    print(f"  ⚠ Device {name} skipped - ThingsBoard device limit reached")
                    print(f"    (Consider using a different TB server or cleaning up existing devices)")
                    return None
                else:
                    print(f"  Debug - 400 Error - Request payload: {json.dumps(device_payload, indent=2)}")
                    print(f"  Debug - 400 Error - Response: {response.text}")
                    print(f"  Debug - Response JSON: {json.dumps(response_data, indent=2)}")
                    return None
            elif response.status_code not in [200, 201]:
                print(f"  Debug - HTTP {response.status_code} - Request payload: {json.dumps(device_payload, indent=2)}")
                print(f"  Debug - HTTP {response.status_code} - Response: {response.text}")
                return None
            device_id = response.json()['id']['id']
            print(f"✓ Created device: {name} (Type: {device_type})")

            # Log some key attributes
            if attributes:
                key_attrs = [k for k in attributes.keys() if k in ['fan_model', 'manufacturer', 'serial_number', 'filter_type']][:3]
                if key_attrs:
                    print(f"  Key attrs: {', '.join(f'{k}={attributes[k]}' for k in key_attrs)}")

            return device_id
        except Exception as e:
            print(f"✗ Failed to create device {name}: {e}")
            return None

    def create_relation(self, from_id: str, from_type: str, to_id: str, to_type: str, relation_type: str = "Contains") -> bool:
        """Create relation between entities"""
        try:
            relation_payload = {
                "from": {
                    "id": from_id,
                    "entityType": from_type
                },
                "to": {
                    "id": to_id,
                    "entityType": to_type
                },
                "type": relation_type
            }
            response = requests.post(
                f"{self.url}/api/relation",
                headers=self._get_headers(),
                json=relation_payload
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"✗ Failed to create relation: {e}")
            return False

    def add_attributes(self, entity_id: str, entity_type: str, attributes: Dict) -> bool:
        """Add server attributes to an entity (matches original script exactly)"""
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

    def validate_scenario(self, scenario: Dict) -> bool:
        """Validate scenario configuration"""
        print("============================================================")
        print("Validating Scenario Configuration")
        print("============================================================")

        # Count entities in scenario
        counts = {
            'sites': 1 if scenario.get('site') else 0,
            'buildings': len(scenario.get('buildings', [])),
            'floors': sum(len(building.get('floors', [])) for building in scenario.get('buildings', [])),
            'rooms': sum(len(floor.get('rooms', [])) for building in scenario.get('buildings', []) for floor in building.get('floors', [])),
            'gateways': sum(len(room.get('gateways', [])) for building in scenario.get('buildings', []) for floor in building.get('floors', []) for room in floor.get('rooms', [])),
            'devices': sum(gateway.get('devices', {}).get('count', 0) for building in scenario.get('buildings', []) for floor in building.get('floors', []) for room in floor.get('rooms', []) for gateway in room.get('gateways', []))
        }

        # Compare with declared totals
        declared = scenario.get('totals', {})
        print("\nEntity Type     Declared     Actual       Status")
        print("------------------------------------------------------------")

        all_valid = True
        for entity_type in ['sites', 'buildings', 'floors', 'rooms', 'gateways', 'devices']:
            actual = counts[entity_type]
            declared_val = declared.get(entity_type, 0)
            status = "✓ OK" if actual == declared_val or declared_val == 0 else "⚠ MISMATCH"
            if status != "✓ OK":
                all_valid = False
            print(f"{entity_type.ljust(15)} {str(declared_val).ljust(11)} {str(actual).ljust(11)} {status}")

        # Validate one gateway per room rule
        print("\nGateway-per-Room Validation:")
        for building in scenario.get('buildings', []):
            for floor in building.get('floors', []):
                for room in floor.get('rooms', []):
                    gateway_count = len(room.get('gateways', []))
                    room_name = room.get('name', 'Unnamed Room')
                    if gateway_count != 1:
                        print(f"  ✗ {room_name}: {gateway_count} gateways (must have exactly 1)")
                        all_valid = False
                    else:
                        print(f"  ✓ {room_name}: {gateway_count} gateway")

        if all_valid:
            print("\n✓ Validation passed - all checks OK")
        else:
            print("\n❌ VALIDATION FAILED - Please fix issues before provisioning")
            return False

        return True

    def provision_scenario(self, scenario_file: str) -> bool:
        """Provision complete scenario from JSON file"""
        try:
            with open(scenario_file, 'r') as f:
                scenario = json.load(f)
        except Exception as e:
            print(f"✗ Failed to load scenario file: {e}")
            return False

        print(f"============================================================")
        print(f"Provisioning Scenario: {scenario_file}")
        print("============================================================")

        print(f"Scenario: {scenario.get('scenarioName')}")
        print(f"Description: {scenario.get('description')}")
        print(f"Attributes: {'Configurable' if self.use_configurable_attrs else 'Hardcoded'}\n")

        # Store scenario for later use
        self.scenario = scenario

        # Validate scenario before provisioning
        if not self.validate_scenario(scenario):
            return False

        # Create Site with configurable attributes
        site_config = scenario.get('site', {})
        site_attrs = {
            'address': site_config.get('address'),
            'latitude': site_config.get('latitude'),
            'longitude': site_config.get('longitude'),
            'site_type': site_config.get('type', 'Site').lower()
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

        self.created_entities['sites'].append(site)

        # Create Buildings with configurable attributes
        building_count = 0
        for building_config in scenario.get('buildings', []):
            building_count += 1
            print(f"\n--- Building {building_count}: {building_config['name']} ---")

            building_attrs = {
                'address': building_config.get('address'),
                'latitude': building_config.get('latitude'),
                'longitude': building_config.get('longitude'),
                'building_type': building_config.get('type', 'Building').lower()
            }
            building_attrs = {k: v for k, v in building_attrs.items() if v is not None}

            building = self.create_asset(
                building_config['name'],
                building_config.get('type', 'Building'),
                building_config.get('label', building_config['name']),
                building_attrs
            )
            if not building:
                continue

            self.created_entities['buildings'].append(building)

            # Create Site -> Building relation
            if not self.create_relation(site, 'ASSET', building, 'ASSET'):
                return False

            # Create Floors
            floor_count = 0
            for floor_config in building_config.get('floors', []):
                floor_count += 1

                floor = self.create_asset(
                    floor_config['name'],
                    floor_config.get('type', 'Floor'),
                    floor_config.get('label', floor_config['name']),
                    {}  # Floors typically have minimal attributes
                )
                if not floor:
                    continue

                self.created_entities['floors'].append(floor)

                # Create Building -> Floor relation
                if not self.create_relation(building, 'ASSET', floor, 'ASSET'):
                    return False

                # Create Rooms with configurable attributes
                room_count = 0
                for room_config in floor_config.get('rooms', []):
                    room_count += 1
                    print(f"  Room {room_count}: {room_config['name']}")

                    room_attrs = {
                        'classification': room_config.get('classification'),
                        'area_sqm': room_config.get('area_sqm'),
                        'floorPlan': room_config.get('floorPlan')
                    }
                    room_attrs = {k: v for k, v in room_attrs.items() if v is not None}

                    room = self.create_asset(
                        room_config['name'],
                        room_config.get('type', 'Room'),
                        room_config.get('label', room_config['name']),
                        room_attrs
                    )
                    if not room:
                        continue

                    self.created_entities['rooms'].append(room)

                    # Create Floor -> Room relation
                    if not self.create_relation(floor, 'ASSET', room, 'ASSET'):
                        return False

                    # Create Gateways
                    gateway_count = 0
                    for gateway_config in room_config.get('gateways', []):
                        gateway_count += 1
                        print(f"    Gateway {gateway_count}: {gateway_config['name']}")

                        # Create Gateway as Device (not Asset)
                        # Gateway devices should keep original names for consistency
                        gateway = self.create_device(
                            gateway_config['name'],
                            gateway_config.get('type', 'Gateway'),
                            gateway_config.get('label', gateway_config['name'])
                        )
                        if not gateway:
                            print(f"    ⚠ Gateway {gateway_config['name']} already exists, skipping creation")
                            continue

                        self.created_entities['gateways'].append(gateway)

                        # Create Room -> Gateway relation (matches original script exactly)
                        if not self.create_relation(room, 'ASSET', gateway, 'DEVICE'):
                            return False

                        # Add protocol as server attribute to gateway device (matches original script)
                        try:
                            protocol_attrs = {
                                'protocol': gateway_config.get('protocol', 'MQTT')
                            }
                            self.add_attributes(gateway, 'DEVICE', protocol_attrs)
                            print(f"  ✓ Added protocol attribute to gateway {gateway_config['name']}")
                        except Exception as e:
                            print(f"  ⚠ Failed to add protocol attribute: {e}")

                        # Create Devices for this gateway
                        device_config = gateway_config.get('devices', {})
                        device_count = device_config.get('count', 0)
                        device_prefix = device_config.get('prefix', 'DW')
                        device_start = device_config.get('start', 0)
                        device_end = device_config.get('end', device_start + device_count - 1)

                        # Calculate device positioning
                        layout_config = device_config.get('layout', 'grid')
                        grid_columns = device_config.get('gridColumns', 6)
                        grid_rows = device_config.get('gridRows', (device_count + grid_columns - 1) // grid_columns)
                        start_x = device_config.get('startX', 0.1)
                        start_y = device_config.get('startY', 0.1)
                        spacing_x = device_config.get('spacingX', 0.15)
                        spacing_y = device_config.get('spacingY', 0.15)

                        created_device_count = 0
                        for device_index in range(device_start, device_end + 1):
                            # Calculate position
                            if layout_config == 'grid':
                                row = (device_index - device_start) // grid_columns
                                col = (device_index - device_start) % grid_columns
                                x_pos = start_x + (col * spacing_x)
                                y_pos = start_y + (row * spacing_y)
                            else:
                                # Random positioning
                                import random
                                x_pos = random.uniform(0.1, 0.8)
                                y_pos = random.uniform(0.1, 0.8)

                            device_name = f"{device_prefix}{device_index:08d}"
                            print(f"      Device {device_index - device_start + 1}/{device_count}: {device_name}")

                            # Context for device attributes
                            device_context = {
                                'room_name': room_config['name'],
                                'gateway_name': gateway_config['name'],
                                'building_name': building_config['name'],
                                'site_name': site_config['name']
                            }

                            # Add position attributes
                            if self.use_configurable_attrs:
                                device_context.update({
                                    'xPos': x_pos,
                                    'yPos': y_pos,
                                    'position_relative': True
                                })

                            device = self.create_device(
                                device_name,
                                'EBMPAPST_FFU',
                                f"FFU {device_index:08d}",
                                device_index,
                                device_context
                            )
                            if device:
                                self.created_entities['devices'].append(device)

                                # Create Gateway -> Device relation
                                if not self.create_relation(gateway, 'DEVICE', device, 'DEVICE'):
                                    return False

                                created_device_count += 1

                        if created_device_count > 0:
                          print(f"    ✓ Created {created_device_count} devices for {gateway_config['name']}")
                        else:
                          print(f"    ⚠ No devices created for {gateway_config['name']} (possible device limit reached)")

        # Save entities to file for later use
        entities_file = '/tmp/provisioned_entities.json'
        with open(entities_file, 'w') as f:
            json.dump(self.created_entities, f, indent=2)
        print(f"\n✓ All entities saved to {entities_file}")

        print("\n" + "=" * 60)
        print("🎉 PROVISIONING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Created entities:")
        for entity_type, entities in self.created_entities.items():
            print(f"  {entity_type.title()}: {len(entities)}")

        return True

    def generate_env_file(self) -> str:
        """Generate .env file for gateway configuration"""
        if not hasattr(self, 'scenario'):
            return ""

        env_content = []
        env_content.append("# Generated by provision-scenario-v2.py")
        env_content.append("# Gateway configuration for ebmpapst FFU test")
        env_content.append("")

        # ThingsBoard connection
        env_content.append("TB_HOST=your-thingsboard-host")
        env_content.append("TB_PORT=1883")
        env_content.append("TB_USERNAME=gateway")
        env_content.append("")

        # Gateway device tokens (would need to be fetched from ThingsBoard)
        for gateway_id in self.created_entities['gateways'][:3]:  # Limit to first 3
            env_content.append(f"GATEWAY_{len(env_content)-5}_TOKEN=your_token_here")

        env_content.append("")
        env_content.append("# Device configuration")
        env_content.append("DEVICE_START_INDEX=0")
        env_content.append(f"DEVICE_END_INDEX={len(self.created_entities['devices']) - 1}")
        env_content.append("MESSAGES_PER_SECOND=10")

        return "\n".join(env_content)


def main():
    parser = argparse.ArgumentParser(description='Enhanced ThingsBoard Scenario Provisioner')
    parser.add_argument('scenario_file', help='JSON scenario file')
    parser.add_argument('--url', default=DEFAULT_TB_URL, help='ThingsBoard URL')
    parser.add_argument('--username', default=DEFAULT_TB_USERNAME, help='ThingsBoard username')
    parser.add_argument('--password', default=DEFAULT_TB_PASSWORD, help='ThingsBoard password')
    parser.add_argument('--no-config-attrs', action='store_true', help='Disable configurable attributes (use hardcoded fallbacks)')
    parser.add_argument('--env-file', help='Save .env file for gateway configuration')

    args = parser.parse_args()

    # Check if scenario file exists
    if not os.path.exists(args.scenario_file):
        print(f"✗ Scenario file not found: {args.scenario_file}")
        return 1

    # Create provisioner
    provisioner = ThingsBoardProvisioner(
        args.url,
        args.username,
        args.password,
        use_configurable_attrs=not args.no_config_attrs
    )

    # Login
    if not provisioner.login():
        return 1

    # Provision scenario
    success = provisioner.provision_scenario(args.scenario_file)

    if success and args.env_file:
        env_content = provisioner.generate_env_file()
        with open(args.env_file, 'w') as f:
            f.write(env_content)
        print(f"\n✓ Environment file saved to {args.env_file}")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())