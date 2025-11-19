# Configurable Attributes & Telemetry System

This directory contains the new **YAML-based configuration system** for ThingsBoard device and asset **attributes** and **telemetry data generation**, replacing hardcoded values in Java source code.

## 🔍 ThingsBoard Concepts

In ThingsBoard, **attributes** and **telemetry** are distinct concepts:

- **Attributes**: Static or semi-static device/asset properties (configuration, metadata, specifications)
  - Example: device serial number, manufacturer, model, firmware version
  - Stored in the **attributes** database table
  - Updated less frequently, used for device management and filtering

- **Telemetry**: Dynamic time-series data from devices (sensor readings, measurements)
  - Example: temperature, pressure, speed, power consumption
  - Stored in the **telemetry** database table (time-series)
  - Updated frequently, used for monitoring and analytics

## 🎯 Why This System?

### **Before (Hardcoded in Java):**
```java
// In Java source files - hard to modify
private static final String[] FAN_MODELS = {
    "R3G355-AS03-01", "R3G310-AP09-01", ...
};
private static final String[] FILTER_TYPES = {
    "HEPA H13", "HEPA H14", "ULPA U15", "ULPA U16"
};
```

### **After (Configurable in YAML):**
```yaml
# In config/attributes/devices/ebmpapst_ffu.yaml
device_info:
  fan_model: ["R3G355-AS03-01", "R3G310-AP09-01", ...]
  manufacturer: "ebm-papst"

filter_specs:
  filter_type: ["HEPA H13", "HEPA H14", "ULPA U15", "ULPA U16"]
```

## 📁 Directory Structure

```
config/
├── README.md                    # This file
├── attribute_loader.py          # Python utility to load configurations
├── attributes/                  # **Attributes** configurations (static/semi-static)
│   ├── assets/                  # Asset attribute configurations
│   │   ├── site.yaml           # Site-level attributes
│   │   ├── building.yaml       # Building-level attributes
│   │   ├── floor.yaml          # Floor-level attributes
│   │   └── room.yaml           # Room-level attributes
│   ├── devices/                 # Device attribute configurations
│   │   ├── ebmpapst_ffu.yaml   # FFU device static attributes
│   │   ├── smart_tracker.yaml  # GPS tracker device attributes
│   │   ├── smart_meter.yaml    # Utility meter device attributes
│   │   └── industrial_plc.yaml # Industrial PLC device attributes
│   └── environments/            # Environment-specific attribute overrides
│       ├── dev/                 # Development environment
│       ├── staging/             # Staging environment
│       └── prod/                # Production environment
└── telemetry/                   # **Telemetry** generation configurations (dynamic data)
    └── devices/                 # Device telemetry generation configs
        ├── ebmpapst_ffu.yaml   # FFU telemetry data points & ranges
        ├── smart_tracker.yaml  # GPS tracker telemetry generation
        └── smart_meter.yaml    # Utility meter telemetry generation
```

### Key Separation:
- **`attributes/`** - Static device/asset properties (stored in ThingsBoard **attributes** table)
- **`telemetry/`** - Dynamic data generation rules (generates data for ThingsBoard **telemetry** table)

## 🚀 Quick Start

### **1. Load Asset Attributes**
```python
from attribute_loader import load_asset_attributes

# Load site attributes with context
site_attrs = load_asset_attributes('site', {
    'address': '123 Industrial Park Dr',
    'latitude': 21.0285,
    'longitude': 105.8542,
    'site_type': 'manufacturing'  # Triggers manufacturing overrides
})

# Result: Dictionary with all site attributes
print(f"Operating Hours: {site_attrs['operating_hours']}")  # "24/7"
print(f"Certification: {site_attrs['certification']}")     # ["ISO 9001", "ISO 14001"]
```

### **2. Load Device Attributes**
```python
from attribute_loader import load_device_attributes

# Generate attributes for FFU device #5
ffu_attrs = load_device_attributes('ebmpapst_ffu', device_index=5)

# Result: Dictionary with device-specific attributes
print(f"Fan Model: {ffu_attrs['fan_model']}")              # Random selection
print(f"Serial Number: {ffu_attrs['serial_number']}")      # Generated
print(f"Filter Type: {ffu_attrs['filter_type']}")          # Random selection
```

### **3. Load Telemetry Configuration**
```python
from attribute_loader import load_telemetry_config

# Load telemetry data point configuration
telemetry_config = load_telemetry_config('ebmpapst_ffu')

# Access data point configurations
motor_temp = telemetry_config['data_points']['motor_temperature']
print(f"Motor temp range: {motor_temp['min']}-{motor_temp['max']}°C")
print(f"Alarm threshold: {motor_temp['alarm_threshold']}°C")
```

## 🎛️ Configuration Features

### **1. Default Values + Context Overrides**
```yaml
# site.yaml
default:
  operating_hours: "24/7"
  description: "Manufacturing facility"

overrides:
  laboratory:
    operating_hours: "08:00-18:00"
    description: "Research and development laboratory"
```

### **2. Dynamic Value Generation**
```yaml
# ebmpapst_ffu.yaml
device_info:
  serial_number:
    prefix: "EBM"
    format: "{{prefix}}-{{random:1000:9999}}-{{random:100000:999999}}"

modbus_config:
  address:
    min: 1
    max: 247
```

### **3. Type-Specific Overrides**
```yaml
# room.yaml
overrides:
  "ISO 5":
    air_changes_per_hour: 400
    garment_requirements: "Full bunny suit"

  "ISO 8":
    air_changes_per_hour: 20
    garment_requirements: "Lab coat"
```

### **4. Telemetry Data Point Configuration**
```yaml
# telemetry/devices/ebmpapst_ffu.yaml
data_points:
  motor_temperature:
    unit: "°C"
    min: 40
    max: 85
    alarm_threshold: 75
    formula: "ambient_temperature + (load_factor * 20) + random_variation(0, 5)"
```

## 🛠️ Adding New Device Types

### **Step 1: Create Device Configuration**
```yaml
# config/attributes/devices/your_device.yaml
device_info:
  manufacturer: "Your Company"
  model: ["Model-A", "Model-B", "Model-C"]

physical_specs:
  weight_kg: 5
  mounting_type: "Wall"

# ... add more sections as needed
```

### **Step 2: Create Telemetry Configuration**
```yaml
# config/telemetry/devices/your_device.yaml
data_points:
  temperature:
    unit: "°C"
    min: 0
    max: 50
    default: 25

  status:
    unit: ""
    values: ["ON", "OFF", "ERROR"]
    default: "ON"
```

### **Step 3: Use in Python**
```python
from attribute_loader import load_device_attributes, load_telemetry_config

device_attrs = load_device_attributes('your_device', device_index=0)
telemetry_config = load_telemetry_config('your_device')
```

## 🔄 Integration with Existing Code

### **Option 1: Gradual Migration**
Keep existing hardcoded values but add configuration support:
```python
# In provision-scenario.py
try:
    # Try to load from configuration
    device_attrs = load_device_attributes('ebmpapst_ffu', device_index)
except:
    # Fallback to hardcoded values
    device_attrs = get_hardcoded_attributes()
```

### **Option 2: Direct Replacement**
Replace hardcoded attribute generators:
```python
# Instead of: attributes = EbmpapstFfuAttributesGenerator().generate()
# Use:
from attribute_loader import load_device_attributes
attributes = load_device_attributes('ebmpapst_ffu', device_index)
```

## 🎨 Customization Examples

### **Different Environments**
Create environment-specific configuration files:
```bash
# Development
config/attributes/devices/ebmpapst_ffu_dev.yaml

# Production
config/attributes/devices/ebmpapst_ffu_prod.yaml

# Test
config/attributes/devices/ebmpapst_ffu_test.yaml
```

### **Customer-Specific Configurations**
```yaml
# For customer with specific requirements
customer_overrides:
  customer_a:
    warranty_years: 5
    maintenance_interval_hours: 4380  # 6 months

  customer_b:
    warranty_years: 2
    maintenance_interval_hours: 8760  # 1 year
```

### **Regional Configurations**
```yaml
# Europe-specific compliance
regional_overrides:
  EU:
    ce_certified: true
    rohs_compliant: true

  US:
    ul_listed: true
    fcc_compliant: true
```

## 🧪 Testing and Validation

### **Test Your Configuration**
```bash
# Run the built-in tests
python3 config/attribute-loader.py

# See all available attributes for a device type
python3 -c "
from attribute_loader import load_device_attributes
import json
print(json.dumps(load_device_attributes('ebmpapst_ffu', 0), indent=2))
"
```

### **Validate YAML Syntax**
```bash
# Install YAML linter
pip install pyyaml

# Test syntax
python3 -c "import yaml; yaml.safe_load(open('config/attributes/devices/ebmpapst_ffu.yaml'))"
```

## 📚 Benefits Summary

| **Aspect** | **Before (Java)** | **After (YAML)** |
|-----------|------------------|------------------|
| **Modification** | Code recompilation | Edit text file |
| **Documentation** | Java comments | Inline YAML comments |
| **Version Control** | Code changes only | Clear config diffs |
| **Non-developers** | Requires dev skills | Human-readable YAML |
| **Environment** | Same for all | Different configs |
| **Testing** | Full rebuild needed | Instant changes |
| **Deployment** | Code deployment | Config change |

## 🔗 Related Files

- **`attribute-loader.py`** - Core loading logic
- **`../test-scenarios/provision-scenario.py`** - Main provisioner (can be updated)
- **`../test-scenarios/demo-configurable-attributes.py`** - Demo and examples
- **`../SCRIPTS.md`** - Updated script documentation

## 🚀 Next Steps

1. **Integrate with provisioner**: Update `provision-scenario.py` to use configurations
2. **Add Java support**: Create Java equivalent of `attribute-loader.py`
3. **Expand device types**: Add configs for smart_tracker, smart_meter, industrial_plc
4. **Environment configs**: Create dev/staging/production variations
5. **GUI editor**: Build simple web interface for editing configs

---

**📝 Note**: This system is designed to be backward compatible. Existing hardcoded values will continue to work while you migrate to the configuration system.