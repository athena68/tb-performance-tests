# ThingsBoard Performance Tests

[![ThingsBoard Builds Server Status](https://img.shields.io/teamcity/build/e/ThingsBoard_Build?label=TB%20builds%20server&server=https%3A%2F%2Fbuilds.thingsboard.io&logo=data:image/png;base64,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&labelColor=305680)](https://builds.thingsboard.io/viewType.html?buildTypeId=PerformanceTests_Build&guest=1)

Performance testing tool for ThingsBoard IoT platform. Simulates high-volume MQTT/HTTP/LWM2M message traffic from thousands of concurrent devices to stress test ThingsBoard deployments.

## 📚 Documentation

Complete documentation available in the [docs/](docs/) directory:

| Document | Description |
|----------|-------------|
| **[docs/INDEX.md](docs/INDEX.md)** | 📖 Documentation navigation and quick reference |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | 🏗️ Architecture decisions and design patterns |
| **[docs/CHANGELOG.md](docs/CHANGELOG.md)** | 📝 Version history and migration notes |
| **[docs/MAINTENANCE.md](docs/MAINTENANCE.md)** | 🔧 Operations, troubleshooting, and cleanup |
| **[docs/TOOLS.md](docs/TOOLS.md)** | 🛠️ Development tools and utilities |
| **[CLAUDE.md](CLAUDE.md)** | 🤖 Claude Code AI-assisted development |

### Specific Guides

- **[Gateway Provisioning](docs/GATEWAY_PROVISIONING.md)** - Setup gateways and devices
- **[FFU Testing](docs/FFU_TEST_EBMPAPST.md)** - ebmpapst Fan Filter Unit testing
- **[Gateway Relations](docs/GATEWAY_DEVICE_RELATION_GUIDE.md)** - Managing device relations

## 🚀 Quick Start

### Prerequisites

- **Java 17** or higher
- **Maven 3.6+**
- **Python 3.8+** (for provisioning scripts)
- **ThingsBoard** server (local or remote)
- **Docker** (optional, for containerized deployment)

### 1. Setup Credentials

```bash
# Copy credentials template
cp test-scenarios/credentials.json.example test-scenarios/credentials.json

# Edit with your ThingsBoard server details
nano test-scenarios/credentials.json
```

### 2. Provision Entities

```bash
# Create gateways, devices, and generate .env configuration
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json
```

This automatically:
- Creates ThingsBoard entities (sites, buildings, gateways, devices)
- Sets device credentials
- Generates `.env` file with test configuration

### 3. Run Performance Test

```bash
# Load configuration and run test
source .env && mvn spring-boot:run
```

Or using Docker:

```bash
docker run -it --rm --network host \
  --env-file .env \
  thingsboard/tb-ce-performance-test:latest
```

## 📊 What It Does

- **Simulates IoT Devices**: Create thousands of virtual devices publishing telemetry
- **Protocol Testing**: MQTT, HTTP, and LWM2M protocol support
- **Gateway Mode**: Test gateway API with devices behind gateways
- **Realistic Payloads**: Industry-specific telemetry (FFU, smart meters, GPS trackers, PLCs)
- **Performance Metrics**: Measure throughput, latency, and system capacity
- **Configurable Load**: Adjust message rate, test duration, and device count

## 🏗️ Project Structure

```
performance-tests/
├── docs/                               # Documentation
├── src/main/java/                      # Java source code
│   └── org/thingsboard/tools/
│       ├── PerformanceTestApplication.java
│       └── service/                    # Test implementations
├── test-scenarios/                     # Python provisioning scripts
│   ├── provision-scenario.py           # Main provisioning script
│   ├── cleanup-scenario.py             # Cleanup utility
│   └── scenario-*.json                 # Test scenario configurations
├── config/attributes/                  # Configurable attribute templates
├── scripts/test-runners/               # Shell test runners
└── .env                                # Auto-generated test configuration
```

## 🔧 Common Tasks

| Task | Command |
|------|---------|
| **Build project** | `mvn clean install` |
| **Run tests** | `mvn spring-boot:run` |
| **Clean up entities** | `python3 test-scenarios/cleanup-scenario.py --credentials test-scenarios/credentials.json --assets --devices --confirm` |
| **Build Docker image** | `mvn clean install -Ddockerfile.skip=false` |
| **View documentation** | See [docs/INDEX.md](docs/INDEX.md) |

## ⚙️ Configuration

Configuration is managed through:
1. **Scenario JSON files** (`test-scenarios/scenario-*.json`) - Define entity hierarchy and test parameters
2. **Credentials file** (`test-scenarios/credentials.json`) - ThingsBoard connection details
3. **Auto-generated .env** - Created by provision script from scenario configuration

See [.env.README](.env.README) for details on environment configuration.

## 📦 Supported Payload Types

- **EBMPAPST_FFU** - Fan Filter Unit industrial telemetry
- **SMART_TRACKER** - GPS tracker data (lat/lon, speed, fuel)
- **SMART_METER** - Utility meter readings
- **INDUSTRIAL_PLC** - Industrial sensor arrays (configurable channels)
- **DEFAULT** - Basic telemetry
- **RANDOM** - Random values for testing

## 🤝 Contributing

See [docs/TOOLS.md](docs/TOOLS.md) for development setup and available utilities.

## 📄 License

Apache License 2.0

## 🔗 Links

- [ThingsBoard Documentation](https://thingsboard.io/docs/)
- [ThingsBoard GitHub](https://github.com/thingsboard/thingsboard)
- [Performance Tests Builds](https://builds.thingsboard.io/viewType.html?buildTypeId=PerformanceTests_Build&guest=1)

---

**Version:** 4.0.1 | **ThingsBoard Compatibility:** 4.0.1 | **Java:** 17 | **Spring Boot:** 3.2.12
