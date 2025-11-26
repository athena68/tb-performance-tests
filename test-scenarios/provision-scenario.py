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
# Fixed: Use abspath to prevent hanging issue with relative paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')))

# Default credentials file location (matching cleanup script)
DEFAULT_CREDENTIALS_FILE = 'test-scenarios/credentials.json'

# HTTP request timeout (seconds) - prevents hanging on network issues
HTTP_TIMEOUT = 30
HTTP_RETRY_ATTEMPTS = 3
HTTP_RETRY_DELAY = 2  # seconds between retries

def load_credentials(creds_file: str = None) -> Dict[str, str]:
    """Load credentials from JSON file with user-friendly fallbacks (reused from cleanup script)"""
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

    def _http_request_with_retry(self, method, *args, **kwargs):
        """Execute HTTP request with retry logic for connection issues"""
        for attempt in range(HTTP_RETRY_ATTEMPTS):
            try:
                return method(*args, **kwargs)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < HTTP_RETRY_ATTEMPTS - 1:
                    print(f"  ⚠ Connection issue (attempt {attempt + 1}/{HTTP_RETRY_ATTEMPTS}): {str(e)[:100]}")
                    print(f"  ↻ Retrying in {HTTP_RETRY_DELAY} seconds...")
                    time.sleep(HTTP_RETRY_DELAY)
                else:
                    raise

    def login(self) -> bool:
        """Login to ThingsBoard and get JWT token"""
        try:
            response = self._http_request_with_retry(
                requests.post,
                f"{self.url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=HTTP_TIMEOUT
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
                "label": label
            }

            # Create asset first (without attributes)
            response = self._http_request_with_retry(
                requests.post,
                f"{self.url}/api/asset",
                headers=self._get_headers(),
                json=asset_payload,
                timeout=HTTP_TIMEOUT
            )

            # Handle response
            if response.status_code == 400:
                # Asset already exists - delete and recreate like original script
                response_data = response.json()
                if response_data.get('message', '').startswith('Asset with such name already exists'):
                    print(f"  ⚠ Asset {name} already exists, deleting and recreating...")
                    # Find and delete existing asset
                    try:
                        search_response = self._http_request_with_retry(

                            requests.get,
                            f"{self.url}/api/tenant/assets?pageSize=100&page=0&assetName={name}",
                            headers=self._get_headers()
,
                            timeout=HTTP_TIMEOUT
                        )
                        if search_response.status_code == 200:
                            assets = search_response.json().get('data', [])
                            for asset in assets:
                                if asset.get('name') == name:
                                    delete_response = self._http_request_with_retry(

                                        requests.delete,
                                        f"{self.url}/api/asset/{asset['id']['id']}",
                                        headers=self._get_headers()
,
                                        timeout=HTTP_TIMEOUT
                                    )
                                    if delete_response.status_code in [200, 204]:
                                        print(f"  ✓ Deleted existing asset {name}")
                                        break
                    except Exception as delete_e:
                        print(f"  ⚠ Failed to delete existing asset: {delete_e}")
                        return None

                    # Retry creating the asset after deletion
                    response = self._http_request_with_retry(

                        requests.post,
                        f"{self.url}/api/asset",
                        headers=self._get_headers(),
                        json=asset_payload
,
                        timeout=HTTP_TIMEOUT
                    )
                    if response.status_code not in [200, 201]:
                        print(f"  Debug - Retry failed: {response.text}")
                        return None

                    retry_asset_id = response.json()['id']['id']
                    # Set attributes for recreated asset
                    if attributes and self.use_configurable_attrs:
                        self._set_asset_attributes(retry_asset_id, attributes)
                    return retry_asset_id
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

            # Set attributes using separate API call if we have any
            if attributes and self.use_configurable_attrs:
                self._set_asset_attributes(asset_id, attributes)

            # Log some key attributes
            if attributes:
                key_attrs = list(attributes.keys())[:3]  # Show first 3 attributes
                print(f"  Attributes: {', '.join(key_attrs)}{'...' if len(attributes) > 3 else ''}")

            return asset_id
        except Exception as e:
            print(f"✗ Failed to create asset {name}: {e}")
            return None

    def _set_asset_attributes(self, asset_id: str, attributes: Dict[str, any]) -> bool:
        """Set server attributes for an asset using ThingsBoard v4 API (original working method)"""
        try:
            # Filter out null values which ThingsBoard doesn't accept
            filtered_attributes = {k: v for k, v in attributes.items() if v is not None}

            if not filtered_attributes:
                print(f"  ⚠ No non-null attributes to set")
                return True

            # Use the original working endpoint format from the legacy script
            endpoint = f"{self.url}/api/plugins/telemetry/ASSET/{asset_id}/attributes/SERVER_SCOPE"

            response = self._http_request_with_retry(


                requests.post,
                endpoint,
                headers=self._get_headers(),
                json=filtered_attributes
,
                timeout=HTTP_TIMEOUT
            )
            if response.status_code == 200:
                print(f"  ✓ Set {len(filtered_attributes)} server attributes for asset using legacy API")
                return True
            else:
                print(f"  ⚠ Failed to set attributes: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"  ⚠ Error setting asset attributes: {e}")
            return False

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

            # Add additionalInfo for gateway devices to make them appear in Gateway tab
            if device_type.lower() == 'gateway':
                device_payload["additionalInfo"] = {"gateway": True}

            # Add attributes if any
            if attributes:
                device_payload["attributes"] = attributes

            response = self._http_request_with_retry(


                requests.post,
                f"{self.url}/api/device",
                headers=self._get_headers(),
                json=device_payload
,
                timeout=HTTP_TIMEOUT
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

    def set_device_credentials(self, device_id: str, access_token: str) -> bool:
        """Set device access token credentials"""
        try:
            # First, get current credentials to preserve deviceId field
            get_response = self._http_request_with_retry(
                requests.get,
                f"{self.url}/api/device/{device_id}/credentials",
                headers=self._get_headers(),
                timeout=HTTP_TIMEOUT
            )

            if get_response.status_code != 200:
                print(f"  ⚠ Could not retrieve current credentials: {get_response.text}")
                return False

            # Update credentials with new token
            credentials_payload = get_response.json()
            credentials_payload["credentialsType"] = "ACCESS_TOKEN"
            credentials_payload["credentialsId"] = access_token

            response = self._http_request_with_retry(
                requests.post,
                f"{self.url}/api/device/credentials",
                headers=self._get_headers(),
                json=credentials_payload,
                timeout=HTTP_TIMEOUT
            )

            if response.status_code not in [200, 201]:
                print(f"  ⚠ Failed to set credentials for device {device_id}: {response.text}")
                return False

            return True
        except Exception as e:
            print(f"  ⚠ Error setting credentials for device {device_id}: {e}")
            return False

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
            response = self._http_request_with_retry(

                requests.post,
                f"{self.url}/api/relation",
                headers=self._get_headers(),
                json=relation_payload
,
                timeout=HTTP_TIMEOUT
            )

            # Handle response - relation might already exist
            if response.status_code == 400:
                response_data = response.json()
                if 'already exists' in response_data.get('message', '').lower():
                    # Relation already exists - this is fine
                    return True
                else:
                    print(f"  ⚠ Relation creation failed: {response_data.get('message', 'Unknown error')}")
                    return False

            response.raise_for_status()
            return True
        except Exception as e:
            print(f"✗ Failed to create relation: {e}")
            return False

    def add_attributes(self, entity_id: str, entity_type: str, attributes: Dict) -> bool:
        """Add server attributes to an entity (matches original script exactly)"""
        try:
            response = self._http_request_with_retry(

                requests.post,
                f"{self.url}/api/plugins/telemetry/{entity_type}/{entity_id}/attributes/SERVER_SCOPE",
                headers=self._get_headers(),
                json=attributes
,
                timeout=HTTP_TIMEOUT
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  ✗ Failed to add attributes: {e}")
            return False

    def create_device_profile(self, profile_file_path: str) -> Optional[str]:
        """Create device profile from JSON file"""
        try:
            # Load profile JSON
            with open(profile_file_path, 'r') as f:
                profile_data = json.load(f)

            profile_name = profile_data.get('name')
            if not profile_name:
                print(f"  ⚠ No 'name' field in device profile JSON")
                return None

            # Check if profile already exists
            response = self._http_request_with_retry(
                requests.get,
                f"{self.url}/api/deviceProfiles?pageSize=1000&page=0",
                headers=self._get_headers(),
                timeout=HTTP_TIMEOUT
            )

            if response.status_code == 200:
                existing_profiles = response.json().get('data', [])
                for profile in existing_profiles:
                    if profile.get('name') == profile_name:
                        # Profile exists - check if it needs updating (has alarm rules)
                        profile_data_obj = profile.get('profileData', {})
                        existing_alarms = profile_data_obj.get('alarms') if profile_data_obj else None
                        existing_alarm_count = len(existing_alarms) if existing_alarms is not None else 0
                        new_alarm_count = len(profile_data.get('profileData', {}).get('alarms', []))

                        if existing_alarm_count == 0 and new_alarm_count > 0:
                            # Update existing profile with alarm rules
                            print(f"  ⚠ Device profile '{profile_name}' exists but has no alarm rules, updating...")
                            profile_data['id'] = profile.get('id')
                            profile_data['createdTime'] = profile.get('createdTime')

                            update_response = self._http_request_with_retry(
                                requests.post,
                                f"{self.url}/api/deviceProfile",
                                headers=self._get_headers(),
                                json=profile_data,
                                timeout=HTTP_TIMEOUT
                            )

                            if update_response.status_code in [200, 201]:
                                print(f"  ✓ Updated device profile: {profile_name} with {new_alarm_count} alarm rules")
                                profile_id = profile.get('id')
                                return profile_id.get('id') if isinstance(profile_id, dict) else profile_id
                            else:
                                print(f"  ⚠ Failed to update device profile: {update_response.text}")
                                profile_id = profile.get('id')
                                return profile_id.get('id') if isinstance(profile_id, dict) else profile_id
                        else:
                            print(f"  ℹ Device profile '{profile_name}' already exists with {existing_alarm_count} alarm rules")
                            profile_id = profile.get('id')
                            return profile_id.get('id') if isinstance(profile_id, dict) else profile_id

            # Create new profile
            response = self._http_request_with_retry(
                requests.post,
                f"{self.url}/api/deviceProfile",
                headers=self._get_headers(),
                json=profile_data,
                timeout=HTTP_TIMEOUT
            )

            if response.status_code in [200, 201]:
                alarm_count = len(profile_data.get('profileData', {}).get('alarms', []))
                print(f"  ✓ Created device profile: {profile_name} with {alarm_count} alarm rules")
                result = response.json()
                profile_id = result.get('id')
                return profile_id.get('id') if isinstance(profile_id, dict) else profile_id
            else:
                print(f"  ✗ Failed to create device profile: {response.text}")
                return None

        except Exception as e:
            print(f"  ✗ Error creating device profile: {e}")
            return None

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

        # Create device profiles BEFORE creating devices
        # This ensures devices get the correct profile with alarm rules
        print("\n============================================================")
        print("Creating Device Profiles")
        print("============================================================\n")

        # Path to device profile JSON (relative to project root)
        profile_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'device-profiles', 'ebmpapst_ffu.json')
        if os.path.exists(profile_path):
            self.create_device_profile(profile_path)
        else:
            print(f"  ⚠ Device profile not found at: {profile_path}")
            print(f"  ℹ Will use auto-created profile (without alarm rules)")

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
                            # Gateway already exists - retrieve its ID to create devices
                            print(f"    ⚠ Gateway {gateway_config['name']} already exists, retrieving ID...")
                            try:
                                response = self._http_request_with_retry(
                                    requests.get,
                                    f"{self.url}/api/tenant/devices?pageSize=100&page=0",
                                    headers=self._get_headers(),
                                    timeout=HTTP_TIMEOUT
                                )
                                if response.status_code == 200:
                                    devices = response.json().get('data', [])
                                    for device in devices:
                                        if device['name'] == gateway_config['name']:
                                            gateway = device['id']['id']
                                            print(f"    ✓ Retrieved existing gateway ID: {gateway[:8]}...")
                                            break

                                if not gateway:
                                    print(f"    ✗ Could not find existing gateway {gateway_config['name']}")
                                    continue
                            except Exception as e:
                                print(f"    ✗ Failed to retrieve gateway {gateway_config['name']}: {e}")
                                continue
                        else:
                            self.created_entities['gateways'].append(gateway)

                        # Create Room -> Gateway relation (matches original script exactly)
                        if not self.create_relation(room, 'ASSET', gateway, 'DEVICE'):
                            return False

                        # Set gateway credentials (token = gateway name)
                        # This allows Java app to connect using gateway name as token
                        if not self.set_device_credentials(gateway, gateway_config['name']):
                            print(f"  ⚠ Could not set credentials for gateway {gateway_config['name']}")
                        else:
                            print(f"  ✓ Set access token for gateway {gateway_config['name']}")

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

                                # Set device credentials (token = device name)
                                if not self.set_device_credentials(device, device_name):
                                    print(f"      ⚠ Could not set credentials for device {device_name}")

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
        """Generate .env file for gateway configuration using actual connection details"""
        if not hasattr(self, 'scenario'):
            return ""

        # Extract connection details from current ThingsBoard connection
        url = self.url.replace('https://', '').replace('http://', '').rstrip('/')
        mqtt_host = url
        if ':' in url:
            # Split hostname and port if present
            parts = url.split(':')
            mqtt_host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 443
        else:
            port = 443 if self.url.startswith('https://') else 80

        env_content = []
        env_content.append(f"# ebmpapst FFU Performance Test - Gateway Mode Configuration")
        env_content.append(f"# Auto-generated from scenario: {self.scenario.get('scenarioName', self.scenario.get('name', 'Unknown'))}")
        env_content.append(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        env_content.append("")

        env_content.append("# ThingsBoard Server Configuration")
        env_content.append(f"REST_URL={self.url}")
        env_content.append(f"REST_USERNAME={self.username}")
        env_content.append(f"REST_PASSWORD={self.password}")
        env_content.append("REST_POOL_SIZE=4")
        env_content.append("")

        env_content.append("# MQTT Broker Configuration")
        env_content.append(f"MQTT_HOST={mqtt_host}")
        env_content.append("MQTT_PORT=1883")
        env_content.append("")

        env_content.append("# SSL Configuration")
        env_content.append("MQTT_SSL_ENABLED=false")
        env_content.append("MQTT_SSL_KEY_STORE=")
        env_content.append("MQTT_SSL_KEY_STORE_PASSWORD=")
        env_content.append("")

        env_content.append("# *** CRITICAL: Use GATEWAY mode ***")
        env_content.append("TEST_API=gateway")
        env_content.append("")

        env_content.append("# Device API Protocol (MQTT for gateway)")
        env_content.append("DEVICE_API=MQTT")
        env_content.append("")

        # Read test configuration from scenario
        test_config = self.scenario.get('testConfig', {})
        payload_type = test_config.get('payloadType', 'EBMPAPST_FFU')
        messages_per_second = test_config.get('messagesPerSecond', 60)
        duration_in_seconds = test_config.get('durationInSeconds', 86400)

        # Calculate device and gateway counts from scenario configuration
        # This works even if entities already existed and weren't newly created
        num_gateways = 0
        num_devices = 0

        for building in self.scenario.get('buildings', []):
            for floor in building.get('floors', []):
                for room in floor.get('rooms', []):
                    gateways = room.get('gateways', [])
                    num_gateways += len(gateways)
                    for gateway in gateways:
                        device_config = gateway.get('devices', {})
                        num_devices += device_config.get('count', 0)

        env_content.append("# Gateway Configuration")
        env_content.append(f"GATEWAY_START_IDX=0")
        env_content.append(f"GATEWAY_END_IDX={num_gateways - 1 if num_gateways > 0 else 0}")
        env_content.append(f"GATEWAY_COUNT={num_gateways}")
        env_content.append("GATEWAY_CREATE_ON_START=false  # Already created by provisioner")
        env_content.append("GATEWAY_DELETE_ON_COMPLETE=false")
        env_content.append("")

        env_content.append("# Device Configuration")
        env_content.append("DEVICE_START_IDX=0")
        env_content.append(f"DEVICE_END_IDX={num_devices - 1 if num_devices > 0 else 0}")
        env_content.append(f"DEVICE_COUNT={num_devices}")
        env_content.append("DEVICE_CREATE_ON_START=false   # Already created by provisioner")
        env_content.append("DEVICE_DELETE_ON_COMPLETE=false")
        env_content.append("")

        env_content.append("# Test Payload Type")
        env_content.append(f"TEST_PAYLOAD_TYPE={payload_type}")
        env_content.append("")

        env_content.append("# Test Execution Configuration")
        env_content.append("WARMUP_ENABLED=true")
        env_content.append("TEST_ENABLED=true")
        env_content.append("")

        env_content.append("# Message Rate Configuration")
        env_content.append(f"MESSAGES_PER_SECOND={messages_per_second}")
        env_content.append(f"DURATION_IN_SECONDS={duration_in_seconds}")
        env_content.append("")

        env_content.append("# Alarm Configuration")
        env_content.append("ALARMS_PER_SECOND=2")
        env_content.append("ALARM_STORM_START_SECOND=60")
        env_content.append("ALARM_STORM_END_SECOND=240")
        env_content.append("")

        env_content.append("# Rule Chain Configuration")
        env_content.append("UPDATE_ROOT_RULE_CHAIN=false")
        env_content.append("REVERT_ROOT_RULE_CHAIN=false")
        env_content.append("RULE_CHAIN_NAME=root_rule_chain_ce.json")
        env_content.append("")

        env_content.append("# Test Execution Mode")
        env_content.append("TEST_SEQUENTIAL=false")
        env_content.append("")

        env_content.append("# Exit Configuration")
        env_content.append("EXIT_AFTER_COMPLETE=true")

        return "\n".join(env_content)


def main():
    parser = argparse.ArgumentParser(description='Enhanced ThingsBoard Scenario Provisioner')
    parser.add_argument('scenario_file', help='JSON scenario file')
    parser.add_argument('--url', help='ThingsBoard URL (required if not using --credentials)')
    parser.add_argument('--username', help='ThingsBoard username (required if not using --credentials)')
    parser.add_argument('--password', help='ThingsBoard password (required if not using --credentials)')
    parser.add_argument('--credentials', help='Credentials JSON file path')
    parser.add_argument('--no-config-attrs', action='store_true', help='Disable configurable attributes (use hardcoded fallbacks)')
    parser.add_argument('--env-file', default='.env', help='Save .env file for gateway configuration (default: .env)')
    parser.add_argument('--no-env-file', action='store_true', help='Skip .env file generation')

    args = parser.parse_args()

    # Handle credentials (matching cleanup script approach)
    url = username = password = None  # Initialize variables

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


    # Ensure credentials were loaded successfully
    if not all([url, username, password]):
        print("❌ Failed to load credentials properly")
        return 1

    # Check if scenario file exists
    if not os.path.exists(args.scenario_file):
        print(f"✗ Scenario file not found: {args.scenario_file}")
        return 1

    # Create provisioner
    provisioner = ThingsBoardProvisioner(
        url,
        username,
        password,
        use_configurable_attrs=not args.no_config_attrs
    )

    # Login
    if not provisioner.login():
        return 1

    # Provision scenario
    success = provisioner.provision_scenario(args.scenario_file)

    # Auto-generate .env file unless --no-env-file is specified
    if success and not args.no_env_file:
        env_content = provisioner.generate_env_file()
        with open(args.env_file, 'w') as f:
            f.write(env_content)
        print(f"\n✓ Environment file saved to {args.env_file}")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())