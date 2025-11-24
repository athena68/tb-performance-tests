# Documentation Index

Welcome to the ThingsBoard Performance Tests documentation!

## Quick Start

New to the project? Start here:

1. **[GATEWAY_PROVISIONING.md](GATEWAY_PROVISIONING.md)** - Quickstart guide for gateway provisioning
2. **[TOOLS.md](TOOLS.md)** - Overview of available tools and utilities
3. **[MAINTENANCE.md](MAINTENANCE.md)** - Common maintenance tasks

## Core Documentation

### Architecture & Design
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture decisions, design patterns, and project structure
- **[CHANGELOG.md](CHANGELOG.md)** - Implementation history, version changes, and migration notes

### Operational Guides
- **[MAINTENANCE.md](MAINTENANCE.md)** - Maintenance procedures, troubleshooting, and cleanup guides
- **[TOOLS.md](TOOLS.md)** - Development tools, utilities, scripts, and testing aids

## Testing Guides

### FFU Testing
- **[FFU_TEST_EBMPAPST.md](FFU_TEST_EBMPAPST.md)** - Comprehensive ebmpapst FFU testing guide
- **[FFU_TEST.md](FFU_TEST.md)** - General FFU testing procedures

### Gateway & Device Management
- **[GATEWAY_PROVISIONING.md](GATEWAY_PROVISIONING.md)** - Gateway provisioning procedures
- **[GATEWAY_DEVICE_RELATION_GUIDE.md](GATEWAY_DEVICE_RELATION_GUIDE.md)** - Managing gateway-device relations

## Project Files

### Root Documentation
- **[../README.md](../README.md)** - Main project README
- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code instructions for AI-assisted development

### Archive
- **[archive/](archive/)** - Archived documentation and historical references

## Documentation Structure

```
docs/
├── INDEX.md (this file)                    # Documentation navigation
├── ARCHITECTURE.md                          # Architecture & design
├── CHANGELOG.md                             # Version history
├── MAINTENANCE.md                           # Operations & troubleshooting
├── TOOLS.md                                 # Development tools
├── GATEWAY_PROVISIONING.md                  # Gateway setup guide
├── GATEWAY_DEVICE_RELATION_GUIDE.md         # Relation management
├── FFU_TEST_EBMPAPST.md                     # FFU testing (ebmpapst)
├── FFU_TEST.md                              # FFU testing (general)
└── archive/                                 # Historical documentation
```

## Getting Help

### Common Tasks

| Task | Documentation |
|------|---------------|
| Set up a new test environment | [GATEWAY_PROVISIONING.md](GATEWAY_PROVISIONING.md) |
| Run FFU performance tests | [FFU_TEST_EBMPAPST.md](FFU_TEST_EBMPAPST.md) |
| Clean up test devices | [MAINTENANCE.md](MAINTENANCE.md#cleanup-devices-and-assets) |
| Troubleshoot MQTT connection | [MAINTENANCE.md](MAINTENANCE.md#issue-java-app-mqtt-connection-failure) |
| Understand payload types | [ARCHITECTURE.md](ARCHITECTURE.md#payload-types) |
| Use provisioning scripts | [TOOLS.md](TOOLS.md#provisioning-scripts) |
| Configure test scenarios | [TOOLS.md](TOOLS.md#scenario-files) |

### Troubleshooting

If you encounter issues, check:
1. [MAINTENANCE.md - Troubleshooting](MAINTENANCE.md#troubleshooting) - Common issues and solutions
2. [CHANGELOG.md - Known Issues](CHANGELOG.md#known-issues) - Known limitations and workarounds

### Contributing

When adding new documentation:
- Place architectural decisions in [ARCHITECTURE.md](ARCHITECTURE.md)
- Record changes in [CHANGELOG.md](CHANGELOG.md)
- Add operational procedures to [MAINTENANCE.md](MAINTENANCE.md)
- Document tools and utilities in [TOOLS.md](TOOLS.md)
- Create specific guides for complex procedures (like FFU_TEST.md)

## Version Information

- **Project Version**: 4.0.1
- **ThingsBoard Compatibility**: 4.0.1
- **Java Version**: 17
- **Spring Boot Version**: 3.2.12

## External Resources

- [ThingsBoard Documentation](https://thingsboard.io/docs/)
- [ThingsBoard GitHub](https://github.com/thingsboard/thingsboard)
- [Claude Code](https://claude.ai/code)
- [Maven Central](https://search.maven.org/)
