# Configurable Attributes System - Implementation Plan

## 🎯 Executive Summary

This plan outlines the refactoring of hardcoded device and asset attributes from Java source code into a **YAML-based configuration system**, providing developers with an intuitive way to modify data models without code recompilation.

## 📊 Current State Analysis

### **Problems Identified:**

1. **Hardcoded Attributes**: 100+ attributes scattered across 15+ Java files
2. **No Developer Documentation**: Attributes hidden in complex Java logic
3. **Compilation Required**: Any change needs full Maven rebuild
4. **No Environment Flexibility**: Same attributes for dev/staging/production
5. **Maintenance Overhead**: Complex attribute generation code

### **Current Attribute Distribution:**
```
Java Source Files:
├── EbmpapstFfuAttributesGenerator.java    (40+ attributes)
├── EbmpapstFfuTelemetryGenerator.java    (20+ telemetry points)
├── provision-scenario.py                  (30+ asset attributes)
└── 10+ other generator classes           (50+ attributes)
```

## 🏗️ Proposed Solution: YAML Configuration System

### **Key Design Principles:**
- ✅ **Developer-friendly**: Human-readable YAML with comments
- ✅ **Flexible**: Environment-specific configurations
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Backward Compatible**: Gradual migration path
- ✅ **Extensible**: Easy to add new device types

### **Architecture Overview:**
```
┌─────────────────────────────────────────────────────────────┐
│                    YAML Configuration System                │
├─────────────────────────────────────────────────────────────┤
│ config/attributes/                                          │
│ ├── assets/         (site, building, floor, room)          │
│ ├── devices/        (ebmpapst_ffu, smart_tracker, etc.)     │
│ └── telemetry/      (data point configurations)            │
│                                                             │
│ attribute-loader.py          ← Python Configuration Loader │
└─────────────────────────────────────────────────────────────┘
                            ↓ Integration
┌─────────────────────────────────────────────────────────────┐
│                 Application Integration                     │
├─────────────────────────────────────────────────────────────┤
│ provision-scenario.py         ← Uses configuration          │
│ Java Generators               ← Future Java integration     │
│ Performance Tests             ← Uses telemetry config       │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Detailed Implementation Plan

### **Phase 1: Foundation (✅ COMPLETED)**

**Status**: ✅ **DONE**

1. **Configuration Schema Design**
   - ✅ YAML structure for assets, devices, telemetry
   - ✅ Override system for different contexts
   - ✅ Dynamic value generation (ranges, templates)

2. **Core Configuration Files Created**
   - ✅ `config/attributes/assets/site.yaml`
   - ✅ `config/attributes/assets/building.yaml`
   - ✅ `config/attributes/assets/room.yaml`
   - ✅ `config/attributes/devices/ebmpapst_ffu.yaml`
   - ✅ `config/attributes/telemetry/ebmpapst_ffu.yaml`

3. **Python Attribute Loader**
   - ✅ `config/attribute-loader.py` with full loading logic
   - ✅ Dynamic value processing
   - ✅ Context-based overrides
   - ✅ Template string support

4. **Documentation**
   - ✅ `config/README.md` with usage examples
   - ✅ Integration guidelines
   - ✅ Customization examples

### **Phase 2: Integration (🔄 IN PROGRESS)**

**Status**: 🔄 **PARTIALLY DONE**

#### **2.1 Python Integration (Priority: HIGH)**
- [x] **Basic Loading**: Attribute loader working
- [x] **Demo System**: `test-scenarios/demo-configurable-attributes.py`
- [ ] **Provisioner Integration**: Update `provision-scenario.py`
- [ ] **Backward Compatibility**: Fallback to hardcoded values

#### **2.2 Java Integration (Priority: MEDIUM)**
- [ ] **Java YAML Loader**: Create equivalent of `attribute-loader.py`
- [ ] **Generator Refactoring**: Update `EbmpapstFfuAttributesGenerator`
- [ ] **Telemetry Generator**: Update `EbmpapstFfuTelemetryGenerator`
- [ ] **Maven Dependencies**: Add YAML processing libraries

#### **2.3 Configuration Validation**
- [ ] **Schema Validation**: YAML structure validation
- [ ] **Type Validation**: Data type verification
- [ ] **Range Validation**: Min/max value checking
- [ ] **Consistency Checks**: Cross-reference validation

### **Phase 3: Expansion (⏳ PENDING)**

**Status**: ⏳ **NOT STARTED**

#### **3.1 Additional Device Types**
- [ ] **Smart Tracker**: `smart_tracker.yaml`
- [ ] **Smart Meter**: `smart_meter.yaml`
- [ ] **Industrial PLC**: `industrial_plc.yaml`
- [ ] **Custom Devices**: Template for new types

#### **3.2 Environment Configurations**
- [ ] **Development**: `dev/` subdirectory
- [ ] **Staging**: `staging/` subdirectory
- [ ] **Production**: `prod/` subdirectory
- [ ] **Environment Switching**: Config selection logic

#### **3.3 Advanced Features**
- [ ] **Template System**: Advanced string templating
- [ ] **Dependency Resolution**: Inter-attribute dependencies
- [ ] **Version Management**: Configuration versioning
- [ ] **Hot Reload**: Runtime configuration updates

## 🛠️ Technical Implementation Details

### **Configuration File Structure**
```yaml
# config/attributes/devices/ebmpapst_ffu.yaml
device_info:                    # Logical grouping
  fan_model: ["R3G355-AS03-01", "R3G310-AP09-01"]  # Random selection
  manufacturer: "ebm-papst"                           # Static value
  serial_number:                                        # Dynamic generation
    prefix: "EBM"
    format: "{{prefix}}-{{random:1000:9999}}-{{random:100000:999999}}"

motor_specs:                   # Another logical section
  rated_speed_rpm: 1800                               # Static
  efficiency_percent: 55                               # Static
  efficiency_class: "IE4"                              # Static
```

### **Override System**
```yaml
# config/attributes/room.yaml
default:
  air_changes_per_hour: 20
  garment_requirements: "Standard"

overrides:
  "ISO 5":                      # Key-based override
    air_changes_per_hour: 400
    garment_requirements: "Full bunny suit"

  "ISO 8":
    air_changes_per_hour: 20
    garment_requirements: "Lab coat"
```

### **Dynamic Value Processing**
```python
# attribute-loader.py logic
def _process_value(self, key: str, value: Any, device_index: int) -> Any:
    if isinstance(value, list):
        return random.choice(value)                    # Random selection
    elif isinstance(value, dict) and 'min' in value:
        return random.uniform(value['min'], value['max'])  # Random range
    elif isinstance(value, dict) and 'format' in value:
        return self._process_template(value['format'], device_index)  # Template
    else:
        return value                                    # Static value
```

## 📈 Migration Strategy

### **Option 1: Gradual Migration (Recommended)**
```python
# provision-scenario.py
def get_device_attributes(device_type, device_index, context=None):
    try:
        # Try configuration first
        return load_device_attributes(device_type, device_index, context)
    except Exception as e:
        logger.warning(f"Config failed, using fallback: {e}")
        return get_hardcoded_attributes(device_type, device_index)
```

### **Option 2: Complete Replacement**
```python
# Replace hardcoded generators entirely
# Old: generator = EbmpapstFfuAttributesGenerator()
# New: attributes = load_device_attributes('ebmpapst_ffu', device_index)
```

### **Migration Timeline**
```
Month 1:  Foundation (✅ Complete)
Month 2:  Python Integration (🔄 50% Complete)
Month 3:  Java Integration (⏳ Not Started)
Month 4:  Testing & Validation
Month 5:  Full Deployment
```

## 🎯 Benefits and Impact

### **Developer Experience**
- ✅ **Immediate Feedback**: Edit config, see results instantly
- ✅ **Clear Documentation**: YAML with inline comments
- ✅ **No Compilation**: Changes without Maven build
- ✅ **Non-Technical Access**: Non-developers can modify

### **Maintenance Benefits**
- ✅ **Single Source**: One place for all attribute definitions
- ✅ **Version Control**: Clear diffs in configuration changes
- ✅ **Environment Management**: Different configs per environment
- ✅ **Testing**: Isolated configuration testing

### **Operational Benefits**
- ✅ **Rapid Prototyping**: Quick attribute changes for testing
- ✅ **Customer Customization**: Per-customer configurations
- ✅ **A/B Testing**: Different configurations for experiments
- ✅ **Compliance**: Easy to update certification attributes

## 🔧 Implementation Checklist

### **Phase 1: Foundation (✅ COMPLETE)**
- [x] Design YAML schema
- [x] Create core configuration files
- [x] Implement Python attribute loader
- [x] Create documentation
- [x] Test basic functionality

### **Phase 2: Integration (🔄 IN PROGRESS)**
- [ ] Update provision-scenario.py
- [ ] Add fallback mechanism
- [ ] Create Java configuration loader
- [ ] Update Java generators
- [ ] Add configuration validation

### **Phase 3: Expansion (⏳ PENDING)**
- [ ] Add remaining device types
- [ ] Implement environment configs
- [ ] Add advanced features
- [ ] Create GUI editor (optional)
- [ ] Performance testing

## 🚀 Getting Started

### **Try It Now**
```bash
# Test the current implementation
python3 config/attribute-loader.py

# See demo with various configurations
python3 test-scenarios/demo-configurable-attributes.py

# Edit configurations
vim config/attributes/devices/ebmpapst_ffu.yaml

# Test your changes
python3 config/attribute-loader.py
```

### **Next Steps for Integration**
1. **Test with Your Data**: Add your specific attribute requirements
2. **Integrate with Provisioner**: Update `provision-scenario.py`
3. **Create Environment Configs**: Dev/staging/production variations
4. **Add Validation**: Ensure data integrity
5. **Team Training**: Educate developers on new system

## 🔗 Resources

- **Configuration Files**: `config/attributes/`
- **Loader Code**: `config/attribute-loader.py`
- **Documentation**: `config/README.md`
- **Demo**: `test-scenarios/demo-configurable-attributes.py`
- **Examples**: See YAML files for attribute examples

---

**📝 Status**: Phase 1 Complete, Phase 2 In Progress
**🎯 Next Milestone**: Integration with provision-scenario.py
**👥 Stakeholders**: Developers, QA, DevOps, System Administrators