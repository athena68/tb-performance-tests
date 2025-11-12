# Scripts Organization

This document describes the reorganized script structure designed to make the performance test tools easier to understand and use.

## 🗂️ Directory Structure

```
scripts/
├── build/                    # Build & deployment scripts
│   ├── build.sh              # Maven build with Docker support
│   └── start-docker.sh       # Start test via Docker
├── test-runners/             # Performance test execution
│   ├── start.sh              # Standard performance test runner
│   ├── run-test-noninteractive.sh  # Automated test runner
│   ├── start-ebmpapst-gateway.sh   # Gateway performance test
│   ├── start-ebmpapst-ffu.sh       # FFU device test
│   └── stop-all-tests.sh           # Stop all running tests
├── scenarios/                # Scenario management
│   ├── provision-scenario.py        # Provision hierarchy from JSON
│   └── cleanup-scenario.py          # Clean up provisioned entities
├── device-management/        # Device & gateway operations
│   ├── setup-gateway-credentials.sh  # Set gateway device tokens
│   ├── create-gateway-relations.sh   # Create bidirectional relations
│   ├── cleanup-test-devices.sh       # Remove test devices
│   └── check-device-types.sh         # Verify device type configs
├── monitoring/               # Verification & monitoring
│   ├── verify-current-setup.sh       # Verify complete setup
│   ├── check-dashboard.sh            # Check dashboard status
│   ├── test-dashboard-v1.sh          # Test dashboard functionality
│   └── list-ffu-devices.sh           # List all FFU devices
├── config/                   # Configuration utilities
│   └── populate-ebmpapst-attributes.sh  # Set device attributes
└── archive/                  # Legacy scripts (deprecated)
    ├── create-cleanroom-assets.sh
    └── create-device-relations.sh

test-scenarios/               # Scenario configurations
├── README.md                 # Scenario documentation
├── scenario-hanoi-cleanroom.json
├── scenario-multi-site.json
├── provision-scenario.py
├── cleanup-scenario.py
├── credentials.json
└── credentials.json.template

# Convenience wrappers (root level)
├── run-test.sh               # Quick access to test runners
├── setup.sh                  # Quick access to setup operations
└── monitor.sh                # Quick access to monitoring tools
```

## 🚀 Quick Start Guide

### 1. Build and Run Tests
```bash
# Standard performance test
./run-test.sh performance

# ebmpapst gateway test
./run-test.sh gateway

# FFU test
./run-test.sh ffu

# Stop all tests
./run-test.sh stop
```

### 2. Setup and Provisioning
```bash
# Provision a scenario
./setup.sh scenario test-scenarios/scenario-hanoi-cleanroom.json

# Setup gateway credentials
./setup.sh gateway-credentials

# Verify setup
./setup.sh verify
```

### 3. Monitoring and Verification
```bash
# Complete setup verification
./monitor.sh verify

# Check dashboard status
./monitor.sh dashboard

# List all FFU devices
./monitor.sh list-ffu
```

## 📋 Detailed Script Categories

### 🏗️ Build & Deployment (`scripts/build/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `build.sh` | Maven build with optional Docker | `./scripts/build/build.sh` |
| `start-docker.sh` | Run performance test via Docker | `./scripts/build/start-docker.sh` |

### 🏃 Test Runners (`scripts/test-runners/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `start.sh` | Standard ThingsBoard performance test | `./scripts/test-runners/start.sh` |
| `run-test-noninteractive.sh` | Automated test runner | `./scripts/test-runners/run-test-noninteractive.sh` |
| `start-ebmpapst-gateway.sh` | Gateway API performance test | `./scripts/test-runners/start-ebmpapst-gateway.sh` |
| `start-ebmpapst-ffu.sh` | FFU device performance test | `./scripts/test-runners/start-ebmpapst-ffu.sh` |
| `stop-all-tests.sh` | Stop all running tests | `./scripts/test-runners/stop-all-tests.sh` |

### 🏗️ Scenario Management (`test-scenarios/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `provision-scenario.py` | Provision IoT hierarchy from JSON | `python3 test-scenarios/provision-scenario.py scenario.json` |
| `cleanup-scenario.py` | Clean up provisioned entities | `python3 test-scenarios/cleanup-scenario.py` |

#### Available Scenarios
- `scenario-hanoi-cleanroom.json` - Single building basic setup
- `scenario-multi-site.json` - Multi-building advanced setup

### 🔧 Device Management (`scripts/device-management/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup-gateway-credentials.sh` | Set gateway device access tokens | `./scripts/device-management/setup-gateway-credentials.sh` |
| `create-gateway-relations.sh` | Create gateway-device relations | `./scripts/device-management/create-gateway-relations.sh` |
| `cleanup-test-devices.sh` | Remove test devices and entities | `./scripts/device-management/cleanup-test-devices.sh` |
| `check-device-types.sh` | Verify device type configurations | `./scripts/device-management/check-device-types.sh` |

### 📊 Monitoring (`scripts/monitoring/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `verify-current-setup.sh` | Complete setup verification | `./scripts/monitoring/verify-current-setup.sh` |
| `check-dashboard.sh` | Check dashboard status | `./scripts/monitoring/check-dashboard.sh` |
| `test-dashboard-v1.sh` | Test dashboard functionality | `./scripts/monitoring/test-dashboard-v1.sh` |
| `list-ffu-devices.sh` | List all FFU devices | `./scripts/monitoring/list-ffu-devices.sh` |

### ⚙️ Configuration (`scripts/config/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `populate-ebmpapst-attributes.sh` | Set device attributes | `./scripts/config/populate-ebmpapst-attributes.sh` |

## 🗃️ Archive (`scripts/archive/`)

Contains legacy scripts that have been replaced by the scenario system:
- `create-cleanroom-assets.sh` - Replaced by `provision-scenario.py`
- `create-device-relations.sh` - Replaced by scenario-based relations

## 💡 Usage Examples

### Complete Test Workflow
```bash
# 1. Build the project
./setup.sh build

# 2. Provision scenario
./setup.sh scenario test-scenarios/scenario-hanoi-cleanroom.json

# 3. Setup gateway credentials
./setup.sh gateway-credentials

# 4. Create gateway relations
./setup.sh gateway-relations

# 5. Verify setup
./monitor.sh verify

# 6. Run performance test
./run-test.sh gateway

# 7. Monitor dashboard
./monitor.sh dashboard

# 8. Stop test when done
./run-test.sh stop

# 9. Cleanup if needed
./setup.sh cleanup-scenario
```

### Quick Development Loop
```bash
# After code changes...
./setup.sh build
./run-test.sh performance
./run-test.sh stop
```

### Multi-Site Testing
```bash
# Provision multi-site scenario
./setup.sh scenario test-scenarios/scenario-multi-site.json

# Run gateway test
./run-test.sh gateway

# Verify all sites are working
./monitor.sh verify
```

## 🔗 Related Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Project overview and architecture
- **[test-scenarios/README.md](./test-scenarios/README.md)** - Scenario configuration details
- **ThingsBoard Documentation** - Platform-specific documentation

## 🛠️ Maintenance

### Adding New Scripts
1. Choose appropriate category directory
2. Add script with executable permissions
3. Update this README
4. Consider adding convenience wrapper support

### Updating Scripts
1. Maintain backward compatibility when possible
2. Update documentation and help text
3. Test with convenience wrappers

### Deprecation
- Move old scripts to `scripts/archive/`
- Add deprecation notice
- Document replacement in this README

---

**Last Updated:** 2025-11-11
**Refactored From:** 18 root-level scripts → 6 organized categories + 3 convenience wrappers