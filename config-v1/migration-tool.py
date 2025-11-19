#!/usr/bin/env python3
"""
Migration Tool for Converting Hardcoded Attributes to Configurable YAML
Extracts hardcoded attributes from Java source files and creates YAML configurations
"""

import os
import re
import sys
import json
import yaml
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

class AttributeExtractor:
    """Extracts hardcoded attributes from Java source files"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.java_files = list(self.project_root.rglob('*.java'))
        self.extracted_data = {}

    def extract_all(self) -> Dict[str, Any]:
        """Extract all hardcoded attributes from Java files"""
        print("🔍 Extracting Hardcoded Attributes from Java Source Files")
        print("=" * 60)

        results = {
            'device_types': {},
            'constants': {},
            'arrays': {},
            'methods': {}
        }

        for java_file in self.java_files:
            print(f"\n📄 Processing: {java_file.relative_to(self.project_root)}")
            file_results = self._extract_from_file(java_file)

            # Merge results
            for category, data in file_results.items():
                if data:
                    results[category].update(data)

        return results

    def _extract_from_file(self, java_file: Path) -> Dict[str, Any]:
        """Extract attributes from a single Java file"""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()

            results = {
                'device_types': {},
                'constants': {},
                'arrays': {},
                'methods': {}
            }

            # Extract static final constants
            constants = self._extract_constants(content, java_file.name)
            if constants:
                results['constants'][java_file.stem] = constants
                print(f"  ✓ Found {len(constants)} constants")

            # Extract array definitions
            arrays = self._extract_arrays(content, java_file.name)
            if arrays:
                results['arrays'][java_file.stem] = arrays
                print(f"  ✓ Found {len(arrays)} arrays")

            # Extract method-based attribute generation
            methods = self._extract_attribute_methods(content, java_file.name)
            if methods:
                results['methods'][java_file.stem] = methods
                print(f"  ✓ Found {len(methods)} attribute methods")

            return results

        except Exception as e:
            print(f"  ✗ Error processing {java_file}: {e}")
            return {}

    def _extract_constants(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract static final constants"""
        constants = {}

        # Pattern for static final constants
        constant_pattern = r'''
            (?:private|public|protected)\s+
            static\s+final\s+
            (?:[A-Za-z_$][A-Za-z0-9_$]*)\s+   # Type
            ([A-Z_][A-Z0-9_]*)\s*             # Name
            =\s*                               # Assignment
            (.*?);                            # Value (non-greedy)
        '''

        matches = re.findall(constant_pattern, content, re.VERBOSE | re.DOTALL | re.IGNORECASE)

        for match in matches:
            type_hint, name, value = match
            value = value.strip()

            # Parse different value types
            parsed_value = self._parse_constant_value(value)

            constants[name] = {
                'type': self._normalize_type(type_hint),
                'value': parsed_value,
                'raw_value': value.strip(),
                'file': filename
            }

        return constants

    def _extract_arrays(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract array definitions"""
        arrays = {}

        # Pattern for array definitions
        array_pattern = r'''
            (?:private|public|protected)\s+
            static\s+final\s+
            ([A-Za-z_$][A-Za-z0-9_$]*\[\])\s+    # Array type
            ([A-Z_][A-Z0-9_]*)\s*                 # Name
            =\s*                                 # Assignment
            \{\s*(.*?)\s*\};                    # Array content
        '''

        matches = re.findall(array_pattern, content, re.VERBOSE | re.DOTALL)

        for match in matches:
            array_type, name, content = match

            # Parse array elements
            elements = self._parse_array_elements(content)

            arrays[name] = {
                'type': array_type,
                'elements': elements,
                'count': len(elements),
                'file': filename
            }

        return arrays

    def _extract_attribute_methods(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract methods that generate attributes"""
        methods = {}

        # Find methods that look like they generate attributes
        method_pattern = r'''
            (?:public|private|protected)\s+
            ([A-Za-z_$][A-Za-z0-9_$]*)\s+          # Return type
            (generate|create|get).*Attributes?\s*   # Method name pattern
            \(.*?\)\s*\{                           # Parameters and opening brace
            (.*?)\}                                # Method content
        '''

        matches = re.findall(method_pattern, content, re.VERBOSE | re.DOTALL | re.IGNORECASE)

        for match in matches:
            return_type, method_content = match

            # Extract attribute assignments from method
            attributes = self._extract_attribute_assignments(method_content)

            if attributes:
                method_name = f"generate_attributes_{filename}"
                methods[method_name] = {
                    'return_type': return_type,
                    'attributes': attributes,
                    'file': filename
                }

        return methods

    def _parse_constant_value(self, value: str) -> Any:
        """Parse and normalize constant values"""
        value = value.strip()

        # Handle string literals
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]

        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Handle boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # Handle other cases - return as string
        return value

    def _parse_array_elements(self, content: str) -> List[Any]:
        """Parse array elements"""
        elements = []

        # Split by commas and clean up
        raw_elements = re.split(r',\s*', content.strip())

        for element in raw_elements:
            element = element.strip()

            # Handle string literals
            if element.startswith('"') and element.endswith('"'):
                elements.append(element[1:-1])
            # Handle numeric values
            elif element.replace('.', '').replace('-', '').isdigit():
                try:
                    if '.' in element:
                        elements.append(float(element))
                    else:
                        elements.append(int(element))
                except ValueError:
                    elements.append(element)
            # Handle other
            elif element:
                elements.append(element)

        return elements

    def _extract_attribute_assignments(self, method_content: str) -> Dict[str, Any]:
        """Extract attribute assignments from method content"""
        attributes = {}

        # Pattern for attribute assignments
        assignment_pattern = r'''
            (\w+)\s*=                     # Variable name
            (.*?)?;                       # Value (until semicolon)
        '''

        matches = re.findall(assignment_pattern, method_content, re.VERBOSE | re.DOTALL)

        for var_name, value in matches:
            # Skip if this looks like a local variable declaration
            if not re.match(r'(final|static|private|public|protected)', value, re.IGNORECASE):
                parsed_value = self._parse_constant_value(value.strip())
                attributes[var_name] = parsed_value

        return attributes

    def _normalize_type(self, type_hint: str) -> str:
        """Normalize Java type hints to YAML-friendly types"""
        type_mapping = {
            'String': 'string',
            'int': 'integer',
            'Integer': 'integer',
            'double': 'float',
            'Double': 'float',
            'float': 'float',
            'Float': 'float',
            'boolean': 'boolean',
            'Boolean': 'boolean',
            'long': 'integer',
            'Long': 'integer'
        }

        # Remove array brackets
        clean_type = type_hint.replace('[]', '')

        # Map to YAML type
        return type_mapping.get(clean_type, clean_type.lower())

class YamlGenerator:
    """Generates YAML configuration files from extracted data"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_device_configs(self, extracted_data: Dict[str, Any]) -> None:
        """Generate device configuration files"""
        print("\n🏭 Generating Device Configuration Files")
        print("=" * 50)

        # Analyze which device types we have
        device_types = self._identify_device_types(extracted_data)

        for device_type in device_types:
            config = self._generate_device_config(device_type, extracted_data)
            output_file = self.output_dir / f"{device_type}.yaml"

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(config)

            print(f"✓ Generated: {output_file}")

    def _identify_device_types(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Identify device types from extracted data"""
        device_types = []

        # Look for device type indicators in file names and constants
        for file_name, data in extracted_data['constants'].items():
            if any(indicator in file_name.lower() for indicator in ['ffu', 'tracker', 'meter', 'plc']):
                device_type = self._extract_device_type_from_file(file_name)
                if device_type and device_type not in device_types:
                    device_types.append(device_type)

        # Default to common device types
        if not device_types:
            device_types = ['ebmpapst_ffu', 'smart_tracker', 'smart_meter', 'industrial_plc']

        return device_types

    def _extract_device_type_from_file(self, file_name: str) -> Optional[str]:
        """Extract device type from file name"""
        if 'ffu' in file_name.lower():
            return 'ebmpapst_ffu'
        elif 'tracker' in file_name.lower():
            return 'smart_tracker'
        elif 'meter' in file_name.lower():
            return 'smart_meter'
        elif 'plc' in file_name.lower():
            return 'industrial_plc'

        return None

    def _generate_device_config(self, device_type: str, extracted_data: Dict[str, Any]) -> str:
        """Generate YAML configuration for a specific device type"""
        config_lines = []
        config_lines.append(f"# Auto-generated configuration for {device_type}")
        config_lines.append("# Generated from Java source code analysis")
        config_lines.append("")

        # Add device info section
        config_lines.append("device_info:")
        config_lines.append("  manufacturer: Auto-generated from code")

        # Add constants as device info
        constants = self._get_relevant_constants(device_type, extracted_data['constants'])
        for const_name, const_data in constants.items():
            if self._is_device_info_constant(const_name):
                yaml_name = self._to_yaml_name(const_name)
                value = self._format_yaml_value(const_data['value'])
                config_lines.append(f"  {yaml_name}: {value}")

        config_lines.append("")

        # Add array data
        arrays = self._get_relevant_arrays(device_type, extracted_data['arrays'])
        if arrays:
            config_lines.append("# Configuration arrays:")
            for array_name, array_data in arrays.items():
                yaml_name = self._to_yaml_name(array_name)
                config_lines.append(f"{yaml_name}:")
                for element in array_data['elements']:
                    config_lines.append(f"  - {self._format_yaml_value(element)}")
            config_lines.append("")

        # Add notes about methods
        methods = self._get_relevant_methods(device_type, extracted_data['methods'])
        if methods:
            config_lines.append("# Method-based attribute generation:")
            config_lines.append("# The following attributes are generated by methods:")
            for method_name, method_data in methods.items():
                config_lines.append(f"# - {method_name}: {len(method_data['attributes'])} attributes")
                for attr_name, attr_value in method_data['attributes'].items():
                    yaml_name = self._to_yaml_name(attr_name)
                    config_lines.append(f"#   {yaml_name}: {attr_value}")

        return '\n'.join(config_lines)

    def _get_relevant_constants(self, device_type: str, constants: Dict[str, Any]) -> Dict[str, Any]:
        """Get constants relevant to a specific device type"""
        relevant = {}

        for file_name, file_constants in constants.items():
            if self._is_relevant_file(device_type, file_name):
                relevant.update(file_constants)

        return relevant

    def _get_relevant_arrays(self, device_type: str, arrays: Dict[str, Any]) -> Dict[str, Any]:
        """Get arrays relevant to a specific device type"""
        relevant = {}

        for file_name, file_arrays in arrays.items():
            if self._is_relevant_file(device_type, file_name):
                relevant.update(file_arrays)

        return relevant

    def _get_relevant_methods(self, device_type: str, methods: Dict[str, Any]) -> Dict[str, Any]:
        """Get methods relevant to a specific device type"""
        relevant = {}

        for file_name, file_methods in methods.items():
            if self._is_relevant_file(device_type, file_name):
                relevant.update(file_methods)

        return relevant

    def _is_relevant_file(self, device_type: str, file_name: str) -> bool:
        """Check if a file is relevant to a device type"""
        device_indicators = {
            'ebmpapst_ffu': ['ffu', 'ebmpapst', 'fan'],
            'smart_tracker': ['tracker', 'gps', 'smarttracker'],
            'smart_meter': ['meter', 'smartmeter'],
            'industrial_plc': ['plc', 'industrial']
        }

        indicators = device_indicators.get(device_type, [])
        file_lower = file_name.lower()

        return any(indicator in file_lower for indicator in indicators)

    def _is_device_info_constant(self, const_name: str) -> bool:
        """Check if a constant is device information"""
        device_info_patterns = [
            'manufacturer', 'model', 'version', 'firmware', 'serial',
            'type', 'protocol', 'address', 'timeout', 'retry',
            'port', 'host', 'url', 'path', 'config'
        ]

        const_lower = const_name.lower()
        return any(pattern in const_lower for pattern in device_info_patterns)

    def _to_yaml_name(self, java_name: str) -> str:
        """Convert Java constant name to YAML-friendly name"""
        # Convert CONSTANT_NAME to camelCase
        parts = java_name.lower().split('_')
        if len(parts) == 1:
            return parts[0]
        else:
            return parts[0] + ''.join(word.capitalize() for word in parts[1:])

    def _format_yaml_value(self, value: Any) -> str:
        """Format a value for YAML output"""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        else:
            return str(value)

class MigrationTool:
    """Main migration tool coordinator"""

    def __init__(self, project_root: str, output_dir: str):
        self.project_root = project_root
        self.output_dir = output_dir
        self.extractor = AttributeExtractor(project_root)
        self.generator = YamlGenerator(output_dir)

    def run_migration(self) -> None:
        """Run the complete migration process"""
        print("🔄 Java-to-YAML Migration Tool")
        print("=" * 60)
        print(f"Project Root: {self.project_root}")
        print(f"Output Directory: {self.output_dir}")
        print()

        try:
            # Step 1: Extract data from Java files
            extracted_data = self.extractor.extract_all()

            # Step 2: Generate YAML files
            self.generator.generate_device_configs(extracted_data)

            # Step 3: Generate migration report
            self._generate_migration_report(extracted_data)

            print("\n" + "=" * 60)
            print("🎉 Migration Completed Successfully!")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            sys.exit(1)

    def _generate_migration_report(self, extracted_data: Dict[str, Any]) -> None:
        """Generate a migration report"""
        report = {
            'summary': {
                'java_files_processed': len(self.extractor.java_files),
                'constants_found': sum(len(file_data) for file_data in extracted_data['constants'].values()),
                'arrays_found': sum(len(file_data) for file_data in extracted_data['arrays'].values()),
                'methods_found': sum(len(file_data) for file_data in extracted_data['methods'].values())
            },
            'details': extracted_data
        }

        report_file = Path(self.output_dir) / 'migration_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📊 Migration report saved to: {report_file}")

        # Print summary
        summary = report['summary']
        print(f"\n📈 Migration Summary:")
        print(f"  Java files processed: {summary['java_files_processed']}")
        print(f"  Constants extracted: {summary['constants_found']}")
        print(f"  Arrays extracted: {summary['arrays_found']}")
        print(f"  Methods found: {summary['methods_found']}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 migration-tool.py <project_root> [output_dir]")
        print("Example: python3 migration-tool.py /path/to/project ./migrated-configs")
        sys.exit(1)

    project_root = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./migrated-configs"

    # Validate project root
    if not os.path.exists(project_root):
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)

    # Run migration
    migration_tool = MigrationTool(project_root, output_dir)
    migration_tool.run_migration()

if __name__ == '__main__':
    main()