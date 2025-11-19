#!/usr/bin/env python3
"""
Configuration Validator for Attribute System
Validates YAML configuration files for syntax, schema, and data integrity
"""

import os
import yaml
import sys
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

class ConfigurationValidator:
    """Validates configuration files for the attribute system"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), 'attributes')

        self.config_dir = Path(config_dir)
        self.errors = []
        self.warnings = []

    def validate_all(self) -> bool:
        """Validate all configuration files"""
        print("🔍 Configuration Validator - Comprehensive Check")
        print("=" * 60)

        success = True

        # Validate YAML syntax for all files
        print("\n📄 YAML Syntax Validation:")
        success &= self._validate_yaml_syntax()

        # Validate schema structure
        print("\n🏗️  Schema Validation:")
        success &= self._validate_schema_structure()

        # Validate data integrity
        print("\n✅ Data Integrity Validation:")
        success &= self._validate_data_integrity()

        # Validate cross-references
        print("\n🔗 Cross-Reference Validation:")
        success &= self._validate_cross_references()

        # Print summary
        self._print_summary()

        return success

    def _validate_yaml_syntax(self) -> bool:
        """Check YAML syntax for all files"""
        yaml_files = list(self.config_dir.rglob('*.yaml')) + list(self.config_dir.rglob('*.yml'))

        success = True
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                print(f"  ✓ {yaml_file.relative_to(self.config_dir.parent)}")
            except yaml.YAMLError as e:
                print(f"  ✗ {yaml_file.relative_to(self.config_dir.parent)}: {e}")
                self.errors.append(f"YAML syntax error in {yaml_file}: {e}")
                success = False
            except Exception as e:
                print(f"  ✗ {yaml_file.relative_to(self.config_dir.parent)}: {e}")
                self.errors.append(f"Error reading {yaml_file}: {e}")
                success = False

        return success

    def _validate_schema_structure(self) -> bool:
        """Validate expected schema structure"""
        success = True

        # Define expected schemas
        schemas = {
            'assets/site.yaml': {
                'required': ['default'],
                'optional': ['overrides'],
                'sections': ['address', 'latitude', 'longitude', 'site_type']
            },
            'assets/building.yaml': {
                'required': ['default'],
                'optional': ['overrides'],
                'sections': ['building_type', 'floors_count', 'latitude', 'longitude']
            },
            'assets/room.yaml': {
                'required': ['default'],
                'optional': ['overrides'],
                'sections': ['classification', 'area_sqm', 'air_changes_per_hour']
            },
            'devices/ebmpapst_ffu.yaml': {
                'required_sections': ['device_info', 'physical_specs', 'motor_specs'],
                'recommended_sections': ['filter_specs', 'sensors', 'control_features']
            },
            'telemetry/ebmpapst_ffu.yaml': {
                'required': ['data_points'],
                'optional': ['special_devices', 'generation_rules']
            }
        }

        for file_path, schema in schemas.items():
            full_path = self.config_dir / file_path
            if not full_path.exists():
                print(f"  ⚠ Missing file: {file_path}")
                self.warnings.append(f"Missing expected file: {file_path}")
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Validate required sections
                if 'required' in schema:
                    for required_key in schema['required']:
                        if required_key not in config:
                            print(f"  ✗ {file_path}: Missing required key '{required_key}'")
                            self.errors.append(f"{file_path}: Missing required key '{required_key}'")
                            success = False

                # Validate recommended sections
                if 'required_sections' in schema:
                    for section in schema['required_sections']:
                        if section not in config:
                            print(f"  ⚠ {file_path}: Missing recommended section '{section}'")
                            self.warnings.append(f"{file_path}: Missing recommended section '{section}'")

                if 'recommended_sections' in schema:
                    for section in schema['recommended_sections']:
                        if section not in config:
                            print(f"  ⚠ {file_path}: Missing recommended section '{section}'")
                            self.warnings.append(f"{file_path}: Missing recommended section '{section}'")

                print(f"  ✓ {file_path}")

            except Exception as e:
                print(f"  ✗ {file_path}: {e}")
                self.errors.append(f"Schema validation error in {file_path}: {e}")
                success = False

        return success

    def _validate_data_integrity(self) -> bool:
        """Validate data types, ranges, and logical consistency"""
        success = True

        # Validate device configurations
        device_configs = list(self.config_dir.glob('devices/*.yaml'))
        for device_file in device_configs:
            try:
                with open(device_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                file_path = device_file.relative_to(self.config_dir.parent)
                print(f"  Checking {file_path}:")

                # Validate numeric ranges
                for section_name, section_config in config.items():
                    if isinstance(section_config, dict):
                        for key, value in section_config.items():
                            if isinstance(value, dict):
                                if 'min' in value and 'max' in value:
                                    if value['min'] > value['max']:
                                        print(f"    ✗ Invalid range: {key} ({value['min']} > {value['max']})")
                                        self.errors.append(f"{file_path}: Invalid range for {key}")
                                        success = False

                                # Validate percentage values
                                if 'percent' in key.lower() or 'percentage' in key.lower():
                                    if isinstance(value, (int, float)) and not (0 <= value <= 100):
                                        print(f"    ✗ Invalid percentage: {key} = {value}")
                                        self.errors.append(f"{file_path}: Invalid percentage for {key}")
                                        success = False

                print(f"    ✓ Data validation passed")

            except Exception as e:
                print(f"    ✗ Error: {e}")
                self.errors.append(f"Data validation error in {file_path}: {e}")
                success = False

        # Validate telemetry configurations
        telemetry_configs = list(self.config_dir.glob('telemetry/*.yaml'))
        for telemetry_file in telemetry_configs:
            try:
                with open(telemetry_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                file_path = telemetry_file.relative_to(self.config_dir.parent)

                if 'data_points' in config:
                    data_points = config['data_points']

                    # Check for required fields in each data point
                    required_fields = ['unit']
                    for dp_name, dp_config in data_points.items():
                        for field in required_fields:
                            if field not in dp_config:
                                print(f"    ⚠ {file_path}: {dp_name} missing '{field}'")
                                self.warnings.append(f"{file_path}: {dp_name} missing '{field}'")

                        # Validate min/max relationships
                        if 'min' in dp_config and 'max' in dp_config:
                            if dp_config['min'] > dp_config['max']:
                                print(f"    ✗ {file_path}: {dp_name} has invalid range")
                                self.errors.append(f"{file_path}: {dp_name} invalid range")
                                success = False

                print(f"  ✓ {file_path}")

            except Exception as e:
                print(f"  ✗ {file_path}: {e}")
                self.errors.append(f"Telemetry validation error in {file_path}: {e}")
                success = False

        return success

    def _validate_cross_references(self) -> bool:
        """Validate cross-references between configuration files"""
        success = True

        # Check that device types referenced in scenarios have corresponding configs
        try:
            scenarios_dir = self.config_dir.parent.parent / 'test-scenarios'
            scenario_files = list(scenarios_dir.glob('scenario-*.json'))

            device_types_found = set()
            for scenario_file in scenario_files:
                try:
                    with open(scenario_file, 'r', encoding='utf-8') as f:
                        scenario = json.loads(f.read())

                    # Extract device types from scenario (simplified)
                    for building in scenario.get('buildings', []):
                        for floor in building.get('floors', []):
                            for room in floor.get('rooms', []):
                                for gateway in room.get('gateways', []):
                                    # Assume FFU devices for now
                                    device_types_found.add('ebmpapst_ffu')

                except Exception as e:
                    print(f"  ⚠ Could not parse {scenario_file}: {e}")
                    self.warnings.append(f"Could not parse scenario file {scenario_file}: {e}")

            # Check that all device types have corresponding config files
            for device_type in device_types_found:
                config_file = self.config_dir / 'devices' / f'{device_type}.yaml'
                if not config_file.exists():
                    print(f"  ⚠ Device type '{device_type}' referenced but no config file found")
                    self.warnings.append(f"Device type '{device_type}' missing config file")

            if device_types_found:
                print(f"  ✓ Found device types: {', '.join(device_types_found)}")
            else:
                print(f"  ⚠ No device types found in scenarios")

        except Exception as e:
            print(f"  ⚠ Cross-reference validation error: {e}")
            self.warnings.append(f"Cross-reference validation error: {e}")

        return success

    def _print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        if not self.errors and not self.warnings:
            print("🎉 All validations passed! Configuration is perfect.")
        else:
            if self.errors:
                print(f"❌ {len(self.errors)} Error(s) found:")
                for error in self.errors:
                    print(f"   • {error}")

            if self.warnings:
                print(f"⚠️  {len(self.warnings)} Warning(s) found:")
                for warning in self.warnings:
                    print(f"   • {warning}")

        print(f"\n📈 Results:")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")
        print(f"   Status: {'✅ VALID' if not self.errors else '❌ INVALID'}")

    def validate_file(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """Validate a specific configuration file"""
        full_path = Path(file_path)
        if not full_path.exists():
            return False, [], [f"File not found: {file_path}"]

        errors = []
        warnings = []

        try:
            # YAML syntax
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Basic structure validation
            if not isinstance(config, dict):
                errors.append("Configuration must be a dictionary")
                return False, errors, warnings

            # Validate based on file type
            if 'assets' in str(full_path):
                self._validate_asset_structure(config, errors, warnings)
            elif 'devices' in str(full_path):
                self._validate_device_structure(config, errors, warnings)
            elif 'telemetry' in str(full_path):
                self._validate_telemetry_structure(config, errors, warnings)

        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return len(errors) == 0, errors, warnings

    def _validate_asset_structure(self, config: Dict, errors: List[str], warnings: List[str]):
        """Validate asset configuration structure"""
        if 'default' not in config:
            errors.append("Asset config must have 'default' section")

    def _validate_device_structure(self, config: Dict, errors: List[str], warnings: List[str]):
        """Validate device configuration structure"""
        # Check for required sections
        required_sections = ['device_info']
        for section in required_sections:
            if section not in config:
                warnings.append(f"Missing recommended section: {section}")

    def _validate_telemetry_structure(self, config: Dict, errors: List[str], warnings: List[str]):
        """Validate telemetry configuration structure"""
        if 'data_points' not in config:
            errors.append("Telemetry config must have 'data_points' section")
        elif not isinstance(config['data_points'], dict):
            errors.append("'data_points' must be a dictionary")


def main():
    """Main validation function"""
    validator = ConfigurationValidator()

    if len(sys.argv) > 1:
        # Validate specific file
        file_path = sys.argv[1]
        success, errors, warnings = validator.validate_file(file_path)

        print(f"🔍 Validating {file_path}")
        print("=" * 40)

        if errors:
            print("❌ Errors:")
            for error in errors:
                print(f"   • {error}")

        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   • {warning}")

        if not errors and not warnings:
            print("✅ Validation passed!")

        return 0 if success else 1
    else:
        # Validate all configurations
        success = validator.validate_all()
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())