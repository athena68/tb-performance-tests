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
Demo script showing environment-specific attribute configurations
"""

import os
import sys
import yaml

# Add the config directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from attribute_loader import load_asset_attributes, load_device_attributes, load_telemetry_config

def demo_environment_configs():
    """Demonstrate environment-specific configurations"""
    print("🌍 Environment-Specific Configuration Demo")
    print("=" * 60)

    environments = ['dev', 'staging', 'prod', None]  # None = default

    for env in environments:
        env_name = env.upper() if env else "DEFAULT"
        print(f"\n📦 {env_name} Environment:")
        print("-" * 40)

        # Load site attributes for this environment
        site_context = {
            'address': '123 Industrial Park Dr',
            'latitude': 21.0285,
            'longitude': 105.8542
        }

        try:
            site_attrs = load_asset_attributes('site', site_context, environment=env)

            # Show key differences between environments
            key_attrs = ['description', 'contact_email', 'debug_mode', 'test_data', 'environment']
            print("  Site Attributes:")
            for attr in key_attrs:
                if attr in site_attrs:
                    print(f"    {attr}: {site_attrs[attr]}")

        except Exception as e:
            print(f"  Error loading site config: {e}")

    print("\n" + "=" * 60)

def demo_device_environment_configs():
    """Demonstrate device configurations across environments"""
    print("🔧 Device Environment Configuration Demo")
    print("=" * 60)

    # Compare FFU device attributes in dev vs prod
    environments = ['dev', 'prod']

    for env in environments:
        print(f"\n🏭 {env.upper()} Environment - FFU Device:")
        print("-" * 40)

        try:
            ffu_attrs = load_device_attributes('ebmpapst_ffu', device_index=1, environment=env)

            # Show environment-specific attributes
            env_specific_attrs = ['firmware_version', 'debug_mode', 'test_mode',
                               'maintenance_interval_hours']

            for attr in env_specific_attrs:
                if attr in ffu_attrs:
                    print(f"    {attr}: {ffu_attrs[attr]}")

        except Exception as e:
            print(f"  Error loading device config: {e}")

def demo_config_merging():
    """Demonstrate how environment configs merge with base configs"""
    print("\n🔗 Configuration Merging Demo")
    print("=" * 60)

    print("\n📄 Base + Environment Configuration Merging:")
    print("Base config provides the foundation...")
    print("Environment config overrides and extends...")
    print("Result = Merged configuration for specific environment")

    # Show a complete example
    print("\n🏗️  Complete Site Configuration (Development):")
    try:
        dev_site_attrs = load_asset_attributes('site', {
            'address': 'Dev Site Address',
            'latitude': 21.0285,
            'longitude': 105.8542
        }, environment='dev')

        print("  Merged Attributes:")
        for key, value in list(dev_site_attrs.items())[:8]:  # Show first 8
            print(f"    {key}: {value}")
        if len(dev_site_attrs) > 8:
            print(f"    ... and {len(dev_site_attrs) - 8} more attributes")

    except Exception as e:
        print(f"  Error: {e}")

def demo_environment_detection():
    """Demonstrate automatic environment detection"""
    print("\n🔍 Environment Detection Demo")
    print("=" * 60)

    # Show how to determine environment
    environment_sources = [
        "Environment variable: TB_ENV",
        "Command line argument: --environment",
        "Configuration file: .env",
        "Host-based detection"
    ]

    print("📋 Environment can be set via:")
    for source in environment_sources:
        print(f"  • {source}")

    print("\n💡 Usage Examples:")
    print("  python3 provision-scenario.py --environment dev")
    print("  export TB_ENV=prod && python3 script.py")
    print("  # In code: load_device_attributes('ffu', environment='staging')")

def demo_best_practices():
    """Show environment configuration best practices"""
    print("\n✅ Environment Configuration Best Practices")
    print("=" * 60)

    practices = [
        {
            "category": "Development Environment",
            "practices": [
                "Enable debug mode and verbose logging",
                "Use accelerated time for testing (1min = 1day)",
                "Short maintenance intervals for testing",
                "Mock external services when needed",
                "Auto-cleanup test data regularly"
            ]
        },
        {
            "category": "Staging Environment",
            "practices": [
                "Mirror production configuration",
                "Use real data (anonymized if needed)",
                "Enable comprehensive monitoring",
                "Test disaster recovery procedures",
                "Validate performance benchmarks"
            ]
        },
        {
            "category": "Production Environment",
            "practices": [
                "Disable all debug features",
                "Enable comprehensive security",
                "Use real-time processing",
                "Implement robust backup strategy",
                "Monitor and alert on all metrics"
            ]
        }
    ]

    for practice in practices:
        print(f"\n🏷️  {practice['category']}:")
        for p in practice['practices']:
            print(f"  ✓ {p}")

if __name__ == "__main__":
    demo_environment_configs()
    demo_device_environment_configs()
    demo_config_merging()
    demo_environment_detection()
    demo_best_practices()

    print("\n" + "=" * 60)
    print("🎉 Environment Configuration Demo Complete!")
    print("📖 See config/attributes/{dev,staging,prod}/ for environment configs")
    print("=" * 60)