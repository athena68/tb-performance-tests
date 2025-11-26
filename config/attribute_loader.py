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
Attribute Configuration Loader
Loads and manages attribute configurations from YAML files
"""

import os
import yaml
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class AttributeLoader:
    """Loads and processes attribute configurations"""

    def __init__(self, config_dir: str = None, telemetry_dir: str = None, environment: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), 'attributes')
        if telemetry_dir is None:
            telemetry_dir = os.path.join(os.path.dirname(__file__), 'telemetry')

        self.config_dir = config_dir
        self.telemetry_dir = telemetry_dir
        self.environment = environment
        self.cache = {}

    def load_asset_attributes(self, asset_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Load attributes for an asset type with context overrides"""
        config = self._load_yaml(f'assets/{asset_type}.yaml')
        if context is None:
            context = {}

        # Start with default attributes
        attributes = config.get('default', {}).copy()

        # Apply context values (from scenario or runtime)
        for key, value in context.items():
            if value is not None:
                attributes[key] = value

        # Apply overrides if applicable
        override_key = self._get_override_key(attributes, config)
        if override_key and override_key in config.get('overrides', {}):
            overrides = config['overrides'][override_key]
            attributes.update(overrides)

        # Process any dynamic values
        return self._process_dynamic_values(attributes)

    def load_device_attributes(self, device_type: str, device_index: int = 0,
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Load attributes for a device type"""
        config = self._load_yaml(f'devices/{device_type}.yaml')
        if context is None:
            context = {}

        attributes = {}

        # Process each configuration section
        for section_name, section_config in config.items():
            if isinstance(section_config, dict):
                section_attributes = self._process_section(section_name, section_config, device_index)
                attributes.update(section_attributes)

        return attributes

    def load_telemetry_config(self, device_type: str) -> Dict[str, Any]:
        """Load telemetry configuration for a device type"""
        return self._load_telemetry_yaml(f'devices/{device_type}.yaml')

    def _load_yaml(self, relative_path: str) -> Dict[str, Any]:
        """Load YAML file with caching and environment support"""
        # Try environment-specific file first
        if self.environment:
            env_file_path = os.path.join(self.config_dir, self.environment, relative_path)
            if os.path.exists(env_file_path):
                file_path = env_file_path
            else:
                file_path = os.path.join(self.config_dir, relative_path)
        else:
            file_path = os.path.join(self.config_dir, relative_path)

        if file_path not in self.cache:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # If environment-specific, merge with base config
            if self.environment and os.path.exists(file_path):
                base_config_path = os.path.join(self.config_dir, relative_path)
                if os.path.exists(base_config_path):
                    with open(base_config_path, 'r', encoding='utf-8') as f:
                        base_config = yaml.safe_load(f)
                    config = self._merge_configs(base_config, config)

            self.cache[file_path] = config

        return self.cache[file_path]

    def _load_telemetry_yaml(self, relative_path: str) -> Dict[str, Any]:
        """Load telemetry YAML file with caching and environment support"""
        # Try environment-specific file first
        if self.environment:
            env_file_path = os.path.join(self.telemetry_dir, self.environment, relative_path)
            if os.path.exists(env_file_path):
                file_path = env_file_path
            else:
                file_path = os.path.join(self.telemetry_dir, relative_path)
        else:
            file_path = os.path.join(self.telemetry_dir, relative_path)

        if file_path not in self.cache:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # If environment-specific, merge with base config
            if self.environment and os.path.exists(file_path):
                base_config_path = os.path.join(self.telemetry_dir, relative_path)
                if os.path.exists(base_config_path):
                    with open(base_config_path, 'r', encoding='utf-8') as f:
                        base_config = yaml.safe_load(f)
                    config = self._merge_configs(base_config, config)

            self.cache[file_path] = config

        return self.cache[file_path]

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base config with environment-specific overrides"""
        result = base.copy()

        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _process_section(self, section_name: str, section_config: Dict[str, Any],
                        device_index: int) -> Dict[str, Any]:
        """Process a configuration section and return flat attributes"""
        attributes = {}

        for key, value in section_config.items():
            processed_value = self._process_value(key, value, device_index)
            if isinstance(processed_value, dict):
                # Flatten nested objects with prefixes
                for sub_key, sub_value in processed_value.items():
                    attributes[f"{key}_{sub_key}"] = sub_value
            else:
                attributes[key] = processed_value

        return attributes

    def _process_value(self, key: str, value: Any, device_index: int) -> Any:
        """Process individual values, handling templates and randomization"""

        if isinstance(value, str) and '{{' in value and '}}' in value:
            # Process template strings
            return self._process_template(value, device_index)
        elif isinstance(value, list):
            # Select random from list
            return random.choice(value)
        elif isinstance(value, dict):
            if 'min' in value and 'max' in value:
                # Random range
                if isinstance(value['min'], float) or isinstance(value['max'], float):
                    return random.uniform(value['min'], value['max'])
                else:
                    return random.randint(value['min'], value['max'])
            elif 'prefix' in value and 'format' in value:
                # Serial number format
                return self._process_template(value['format'], device_index)
            else:
                # Recursively process nested objects
                return {k: self._process_value(k, v, device_index) for k, v in value.items()}
        else:
            return value

    def _process_template(self, template: str, device_index: int) -> str:
        """Process template strings with variables"""
        replacements = {
            'device_index': device_index,
            'random': self._random_replacement,
            'timestamp': lambda: datetime.now().isoformat(),
            'date': lambda: datetime.now().strftime('%Y-%m-%d')
        }

        result = template
        for key, replacement in replacements.items():
            if key in result:
                result = result.replace(f'{{{key}}}', str(replacement))

        return result

    def _random_replacement(self, match_str: str) -> str:
        """Handle random generation in templates"""
        # Simple random string generation
        if 'string' in match_str:
            length = 8
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        elif 'number' in match_str:
            return str(random.randint(1000, 9999))
        else:
            return str(random.randint(100000, 999999))

    def _process_dynamic_values(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Process any dynamic attribute values"""
        processed = attributes.copy()

        # Calculate auto-generated values
        if 'total_buildings' in processed and processed['total_buildings'] is None:
            processed['total_buildings'] = 1  # Default

        # Add timestamps for installation dates
        if 'installation_date' in processed and processed['installation_date'] == 'auto':
            days_ago = random.randint(1, 730)  # Random within 2 years
            installation_date = datetime.now() - timedelta(days=days_ago)
            processed['installation_date'] = installation_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        return processed

    def _get_override_key(self, attributes: Dict[str, Any], config: Dict[str, Any]) -> Optional[str]:
        """Determine which override key to use based on attributes"""
        # Check for classification-based overrides
        if 'classification' in attributes:
            classification = attributes['classification']
            if classification in config.get('overrides', {}):
                return classification

        # Check for building type overrides
        if 'building_type' in attributes:
            building_type = attributes['building_type']
            if building_type in config.get('overrides', {}):
                return building_type

        # Check for site type overrides
        if 'site_type' in attributes:
            site_type = attributes['site_type']
            if site_type in config.get('overrides', {}):
                return site_type

        return None

# Global instance for easy access
attribute_loader = AttributeLoader()

def load_asset_attributes(asset_type: str, context: Dict[str, Any] = None, environment: str = None) -> Dict[str, Any]:
    """Convenience function to load asset attributes"""
    if environment:
        loader = AttributeLoader(environment=environment)
        return loader.load_asset_attributes(asset_type, context)
    return attribute_loader.load_asset_attributes(asset_type, context)

def load_device_attributes(device_type: str, device_index: int = 0,
                         context: Dict[str, Any] = None, environment: str = None) -> Dict[str, Any]:
    """Convenience function to load device attributes"""
    if environment:
        loader = AttributeLoader(environment=environment)
        return loader.load_device_attributes(device_type, device_index, context)
    return attribute_loader.load_device_attributes(device_type, device_index, context)

def load_telemetry_config(device_type: str, environment: str = None) -> Dict[str, Any]:
    """Convenience function to load telemetry configuration"""
    if environment:
        loader = AttributeLoader(environment=environment)
        return loader.load_telemetry_config(device_type)
    return attribute_loader.load_telemetry_config(device_type)

if __name__ == "__main__":
    # Example usage
    print("=== Site Attributes ===")
    site_attrs = load_asset_attributes('site', {
        'address': '123 Main St',
        'latitude': 21.0285,
        'longitude': 105.8542
    })
    print(yaml.dump(site_attrs, default_flow_style=False))

    print("=== Building Attributes ===")
    building_attrs = load_asset_attributes('building', {
        'building_type': 'manufacturing',
        'latitude': 21.0285,
        'longitude': 105.8542
    })
    print(yaml.dump(building_attrs, default_flow_style=False))

    print("=== FFU Device Attributes ===")
    ffu_attrs = load_device_attributes('ebmpapst_ffu', device_index=1)
    print(yaml.dump(ffu_attrs, default_flow_style=False))

    print("=== Telemetry Config ===")
    telemetry_config = load_telemetry_config('ebmpapst_ffu')
    print(f"Data points: {list(telemetry_config['data_points'].keys())}")