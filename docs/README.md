# Documentation Index

Complete documentation for ebmpapst FFU Performance Testing project.

---

## Quick Start

- **[../STATUS.md](../STATUS.md)** - Current project status and quick commands
- **[../README.md](../README.md)** - Main project README
- **[../CLAUDE.md](../CLAUDE.md)** - Project architecture for AI assistants

---

## Gateway Provisioning

### Main Guide
- **[GATEWAY_PROVISIONING.md](GATEWAY_PROVISIONING.md)** - Complete guide for gateway-based device provisioning
  - Gateway setup and configuration
  - Auto-provisioning flow
  - Real-world IoT device behavior
  - Troubleshooting common issues

### Archived (Old Versions)
- [archive/PROVISIONING_GUIDE.md](archive/PROVISIONING_GUIDE.md)
- [archive/REAL_WORLD_PROVISIONING.md](archive/REAL_WORLD_PROVISIONING.md)
- [archive/GATEWAY_SETUP.md](archive/GATEWAY_SETUP.md)

---

## FFU Device Testing

### Implementation Guides
- **[FFU_TEST.md](FFU_TEST.md)** - Generic FFU device implementation guide
  - Basic FFU telemetry and attributes
  - Step-by-step implementation
  - Generic device profile

- **[FFU_TEST_EBMPAPST.md](FFU_TEST_EBMPAPST.md)** - ebmpapst-specific FFU implementation
  - Accurate ebmpapst specifications
  - MODBUS-RTU parameters
  - Real product models (R3G355, R3G310, R3G400)
  - DC motor parameters (dcLinkVoltage, dcLinkCurrent)
  - Differential pressure monitoring

---

## Dashboard Development

### Implementation Plans
- [archive/CLEANROOM_DASHBOARD_IMPLEMENTATION_PLAN.md](archive/CLEANROOM_DASHBOARD_IMPLEMENTATION_PLAN.md) - Original complete plan
  - Option A: Flat view dashboard
  - Option B: Hierarchical dashboard with assets
  - Upgrade path between options

- [archive/PHASE1_OPTION_A_COMPLETED.md](archive/PHASE1_OPTION_A_COMPLETED.md) - Phase 1 completion report

---

## File Organization

```
/home/tuan/ThingsboardSetup/performance-tests/
├── README.md                    # Main project README
├── CLAUDE.md                    # Project architecture
├── STATUS.md                    # Current status & quick commands
│
├── docs/                        # 📁 All documentation
│   ├── README.md               # This file (documentation index)
│   ├── GATEWAY_PROVISIONING.md # ✨ Complete provisioning guide
│   ├── FFU_TEST.md             # Generic FFU testing
│   ├── FFU_TEST_EBMPAPST.md    # ebmpapst FFU testing
│   └── archive/                # Old documentation versions
│
├── dashboards/                  # Dashboard JSON files
│   ├── cleanroom_working.json  # Current working dashboard
│   └── ...
│
├── src/                        # Source code
│   ├── main/java/.../ebmpapstFfu/  # FFU generators
│   └── main/resources/device-profiles/  # Device profiles
│
└── scripts/                    # Helper scripts
    ├── verify-current-setup.sh
    ├── create-simple-dashboard.sh
    └── ...
```

---

## Topics Covered

### 1. Gateway Provisioning
**File:** [GATEWAY_PROVISIONING.md](GATEWAY_PROVISIONING.md)

Topics:
- Gateway setup and configuration
- Auto-provisioning vs REST API creation
- Real-world IoT device lifecycle
- MQTT gateway API (v1/gateway/connect, attributes, telemetry)
- Troubleshooting device relations
- Device type assignment

### 2. Generic FFU Testing
**File:** [FFU_TEST.md](FFU_TEST.md)

Topics:
- Basic FFU telemetry (fanSpeed, filterPressure, airFlowRate)
- Generic attributes (firmwareVersion, serialNumber, model)
- Device profile creation
- Simple alarm rules
- Testing procedures

### 3. ebmpapst FFU Testing
**File:** [FFU_TEST_EBMPAPST.md](FFU_TEST_EBMPAPST.md)

Topics:
- Accurate ebmpapst EC motor specifications
- MODBUS-RTU communication parameters
- Real product models and specifications
- DC motor parameters (voltage, current, power)
- Differential pressure monitoring (external 0-10V sensor)
- Temperature derating and shutdown thresholds
- Motor efficiency (IE4 class)
- Advanced alarm configuration

---

## Key Differences: Generic vs ebmpapst

| Aspect | Generic FFU | ebmpapst FFU |
|--------|-------------|--------------|
| **Specifications** | Approximate values | Real ebmpapst specs |
| **Pressure** | filterPressure (internal) | differentialPressure (external sensor) |
| **Electrical** | powerConsumption only | dcLinkVoltage, dcLinkCurrent, power |
| **Control** | Simple on/off | MODBUS-RTU + 0-10V analog |
| **Models** | Generic names | Real models (R3G355-AS03-01) |
| **Accuracy** | Test purposes | Production-ready |

---

## Common Tasks

### Start Performance Test
```bash
./start-ebmpapst-gateway.sh
```

### Verify Setup
```bash
./verify-current-setup.sh
```

### Create Dashboard
```bash
./create-simple-dashboard.sh
```

### View Status
```bash
cat STATUS.md
```

---

## Learning Path

**Recommended reading order:**

1. **[../STATUS.md](../STATUS.md)** - Understand current state
2. **[../README.md](../README.md)** - Project overview
3. **[GATEWAY_PROVISIONING.md](GATEWAY_PROVISIONING.md)** - Learn provisioning
4. **[FFU_TEST_EBMPAPST.md](FFU_TEST_EBMPAPST.md)** - Understand implementation
5. **[../CLAUDE.md](../CLAUDE.md)** - Deep dive into architecture

---

## Getting Help

### Documentation
- Check [STATUS.md](../STATUS.md) for current issues
- Review [GATEWAY_PROVISIONING.md](GATEWAY_PROVISIONING.md) troubleshooting section
- Check archived docs for historical context

### Testing
- All scripts have built-in help: `./script-name.sh --help`
- Verification script checks entire setup: `./verify-current-setup.sh`
- Dashboard test validates functionality: `./test-dashboard-v1.sh`

### ThingsBoard Resources
- [ThingsBoard Documentation](https://thingsboard.io/docs/)
- [Gateway MQTT API](https://thingsboard.io/docs/reference/gateway-mqtt-api/)
- [Device Profiles](https://thingsboard.io/docs/user-guide/device-profiles/)

---

**Last Updated:** 2025-10-17
