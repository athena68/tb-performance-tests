#!/usr/bin/env python3
"""
Demo script showing how to use configurable attributes
This demonstrates the new attribute configuration system
"""

import sys
import os
import json
import yaml

# Add the config directory to path for imports
config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
sys.path.insert(0, config_path)

# Import the attribute loader
import attribute_loader
from attribute_loader import load_asset_attributes, load_device_attributes, load_telemetry_config

def demo_asset_attributes():
    """Demonstrate loading asset attributes with different contexts"""
    print("=" * 60)
    print("🏢 DEMO: Asset Attribute Configuration")
    print("=" * 60)

    # Site attributes with override for manufacturing
    print("\n📍 Manufacturing Site Attributes:")
    site_context = {
        'address': '123 Industrial Park Dr',
        'latitude': 21.0285,
        'longitude': 105.8542,
        'site_type': 'manufacturing'
    }
    site_attrs = load_asset_attributes('site', site_context)
    print(f"  Address: {site_attrs['address']}")
    print(f"  Operating Hours: {site_attrs['operating_hours']}")
    print(f"  Certification: {site_attrs['certification']}")

    # Room attributes with ISO classification override
    print("\n🏠 ISO 5 Cleanroom Attributes:")
    room_context = {
        'classification': 'ISO 5',
        'area_sqm': 100
    }
    room_attrs = load_asset_attributes('room', room_context)
    print(f"  Classification: {room_attrs['classification']}")
    print(f"  Air Changes/Hour: {room_attrs['air_changes_per_hour']}")
    print(f"  Pressure Differential: {room_attrs['pressure_differential_pa']} Pa")
    print(f"  Entry Procedure: {room_attrs['entry_procedure']}")

    # Room attributes with ISO 8 classification override
    print("\n🏠 ISO 8 Standard Room Attributes:")
    room_context_8 = {
        'classification': 'ISO 8',
        'area_sqm': 200
    }
    room_attrs_8 = load_asset_attributes('room', room_context_8)
    print(f"  Classification: {room_attrs_8['classification']}")
    print(f"  Air Changes/Hour: {room_attrs_8['air_changes_per_hour']}")
    print(f"  Pressure Differential: {room_attrs_8['pressure_differential_pa']} Pa")
    print(f"  Entry Procedure: {room_attrs_8['entry_procedure']}")

def demo_device_attributes():
    """Demonstrate loading device attributes"""
    print("\n" + "=" * 60)
    print("🔧 DEMO: Device Attribute Configuration")
    print("=" * 60)

    # Generate attributes for multiple FFU devices
    print("\n💨 FFU Device Attributes (3 devices):")
    for i in range(3):
        ffu_attrs = load_device_attributes('ebmpapst_ffu', device_index=i)
        print(f"\n  Device {i+1} (DW0000000{i}):")
        print(f"    Fan Model: {ffu_attrs['fan_model']}")
        print(f"    Serial Number: {ffu_attrs['serial_number']}")
        print(f"    Firmware: {ffu_attrs['firmware_version']}")
        print(f"    Filter Type: {ffu_attrs['filter_type']}")

def demo_telemetry_config():
    """Demonstrate loading telemetry configuration"""
    print("\n" + "=" * 60)
    print("📊 DEMO: Telemetry Configuration")
    print("=" * 60)

    telemetry_config = load_telemetry_config('ebmpapst_ffu')

    print("\n🔢 Available Telemetry Data Points:")
    for data_point, config in telemetry_config['data_points'].items():
        unit = config.get('unit', '')
        default = config.get('default', 'N/A')
        print(f"  {data_point}: {unit} (default: {default})")

    print("\n⚠️  Special Device Configurations:")
    special_devices = telemetry_config['special_devices']
    for device_type, config in special_devices.items():
        devices = config.get('devices', [])
        print(f"  {device_type}: {len(devices)} devices")
        if devices:
            print(f"    Examples: {devices[:3]}")

def demo_json_output():
    """Show how this integrates with ThingsBoard API"""
    print("\n" + "=" * 60)
    print("🔗 DEMO: ThingsBoard Integration Example")
    print("=" * 60)

    print("\n📋 Example API Payload for Site Asset:")
    site_context = {
        'address': '123 Industrial Park Dr',
        'latitude': 21.0285,
        'longitude': 105.8542
    }
    site_attrs = load_asset_attributes('site', site_context)

    api_payload = {
        "name": "Demo Manufacturing Site",
        "type": "Site",
        "label": "Demo Site",
        "attributes": site_attrs
    }

    print(json.dumps(api_payload, indent=2))

    print("\n📋 Example API Payload for FFU Device:")
    ffu_attrs = load_device_attributes('ebmpapst_ffu', device_index=42)

    device_payload = {
        "name": "DW00000042",
        "type": "EBMPAPST_FFU",
        "label": "FFU Device 42",
        "attributes": ffu_attrs
    }

    print(json.dumps(device_payload, indent=2))

def demo_customization_examples():
    """Show how easy it is to customize attributes"""
    print("\n" + "=" * 60)
    print("🎨 DEMO: Easy Customization Examples")
    print("=" * 60)

    print("\n✅ Before: Hardcoded in Java")
    print("   private static final String[] FAN_MODELS = {")
    print("     \"R3G355-AS03-01\", \"R3G310-AP09-01\", ...")
    print("   };")

    print("\n✅ After: Configurable in YAML")
    print("   # In config/attributes/devices/ebmpapst_ffu.yaml")
    print("   fan_model: [\"R3G355-AS03-01\", \"R3G310-AP09-01\", ...]")

    print("\n🎯 Benefits:")
    print("   ✅ No code compilation required")
    print("   ✅ Comments explain each attribute")
    print("   ✅ Different configs per environment")
    print("   ✅ Easy version control")
    print("   ✅ Non-developers can modify")

if __name__ == "__main__":
    print("🚀 Configurable Attributes System Demo")
    print("This shows how the new YAML-based attribute system works")

    demo_asset_attributes()
    demo_device_attributes()
    demo_telemetry_config()
    demo_json_output()
    demo_customization_examples()

    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("📖 See config/attributes/ for full configuration files")
    print("🔧 Use attribute_loader.py in your Python scripts")
    print("=" * 60)