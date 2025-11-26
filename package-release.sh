#!/bin/bash
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


################################################################################
# Performance Tests Release Packager
#
# Creates a complete plug-and-play distribution package including:
# - Executable JAR with all dependencies
# - Configuration template
# - Quick-start documentation
# - Helper scripts
#
# Usage: ./package-release.sh
# Note: Version is auto-detected from pom.xml
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
# Auto-detect version from pom.xml
if [ -f "pom.xml" ]; then
    PROJECT_VERSION=$(grep "^    <version>" pom.xml | head -1 | sed 's/.*<version>\(.*\)<\/version>.*/\1/')
    echo -e "${GREEN}✓${NC} Detected version from pom.xml: ${YELLOW}${PROJECT_VERSION}${NC}"
else
    PROJECT_VERSION="${1:-4.0.1}"
    echo -e "${YELLOW}⚠${NC} pom.xml not found, using version: ${YELLOW}${PROJECT_VERSION}${NC}"
fi

PACKAGE_NAME="tb-ce-performance-tests"
DIST_DIR="performance-tests-dist-${PROJECT_VERSION}"
ZIP_FILE="${DIST_DIR}.zip"
BUILD_DIR="target"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Performance Tests Release Packager${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Package: ${YELLOW}${PACKAGE_NAME}-${PROJECT_VERSION}${NC}"
echo ""

# Step 1: Clean and build
echo -e "${BLUE}[1/6]${NC} Cleaning previous build..."
mvn clean -q
echo -e "${GREEN}✓${NC} Clean complete"

echo -e "${BLUE}[2/6]${NC} Building JAR with dependencies..."
mvn package -DskipTests -q
echo -e "${GREEN}✓${NC} Build complete"

# Verify JAR exists (boot JAR with all dependencies)
BOOT_JAR="${BUILD_DIR}/${PACKAGE_NAME}-${PROJECT_VERSION}-boot.jar"
if [ ! -f "${BOOT_JAR}" ]; then
    # Fallback to regular JAR if boot JAR doesn't exist
    BOOT_JAR="${BUILD_DIR}/${PACKAGE_NAME}-${PROJECT_VERSION}.jar"
    if [ ! -f "${BOOT_JAR}" ]; then
        echo -e "${RED}✗${NC} JAR not found in ${BUILD_DIR}/"
        exit 1
    fi
fi

JAR_SIZE=$(du -h "${BOOT_JAR}" | cut -f1)
echo -e "  JAR Size: ${YELLOW}${JAR_SIZE}${NC}"

# Step 2: Create distribution directory structure
echo -e "${BLUE}[3/6]${NC} Creating distribution package..."
rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}"/{bin,provisioning/scenarios,config,docs}

# Copy JAR to bin/
cp "${BOOT_JAR}" "${DIST_DIR}/bin/${PACKAGE_NAME}-${PROJECT_VERSION}.jar"
echo -e "${GREEN}✓${NC} JAR copied to bin/"

# Copy provisioning scripts
if [ -d "test-scenarios" ]; then
    cp test-scenarios/provision-scenario.py "${DIST_DIR}/provisioning/"
    cp test-scenarios/cleanup-scenario.py "${DIST_DIR}/provisioning/" 2>/dev/null || true

    # Copy scenario files
    cp test-scenarios/scenario-*.json "${DIST_DIR}/provisioning/scenarios/" 2>/dev/null || true

    # Copy attribute_loader.py if exists
    if [ -f "config/attribute_loader.py" ]; then
        cp config/attribute_loader.py "${DIST_DIR}/provisioning/"
        echo -e "${GREEN}✓${NC} attribute_loader.py copied"
    fi

    # Copy attributes directory to provisioning (needed by attribute_loader.py)
    if [ -d "config/attributes" ]; then
        cp -r config/attributes "${DIST_DIR}/provisioning/" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Attributes copied to provisioning/ (for attribute_loader.py)"
    fi

    # Copy telemetry directory to provisioning (for telemetry config access)
    if [ -d "config/telemetry" ]; then
        cp -r config/telemetry "${DIST_DIR}/provisioning/" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Telemetry configs copied to provisioning/"
    fi

    # Use the correct credentials template from test-scenarios
    if [ -f "test-scenarios/credentials.json.template" ]; then
        cp test-scenarios/credentials.json.template "${DIST_DIR}/provisioning/credentials.json.example"
    else
        # Fallback: create correct template structure
        cat > "${DIST_DIR}/provisioning/credentials.json.example" << 'CREDFILE'
{
  "thingsboard": {
    "url": "http://localhost:8080",
    "username": "tenant@thingsboard.org",
    "password": "tenant",
    "mqtt_host": "localhost",
    "mqtt_port": 1883
  }
}
CREDFILE
    fi

    echo -e "${GREEN}✓${NC} Provisioning scripts copied"
else
    echo -e "${YELLOW}⚠${NC} test-scenarios/ not found, skipping provisioning scripts"
fi

# Copy config directory if exists
if [ -d "config/attributes" ]; then
    cp -r config/attributes "${DIST_DIR}/config/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Attribute config files copied"
fi

# Copy telemetry configuration (CRITICAL for runtime device state configuration)
if [ -d "config/telemetry" ]; then
    cp -r config/telemetry "${DIST_DIR}/config/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Telemetry config files copied (includes device state configuration)"
fi

# Copy device profiles with alarm rules
if [ -d "src/main/resources/device/profile" ]; then
    mkdir -p "${DIST_DIR}/config/device-profiles"
    cp src/main/resources/device/profile/*.json "${DIST_DIR}/config/device-profiles/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Device profiles with alarm rules copied"
fi

# Step 3: Create .env template in config/
cat > "${DIST_DIR}/config/.env.example" << 'ENVFILE'
################################################################################
# ThingsBoard Performance Tests Configuration
#
# SETUP OPTIONS:
#   Option 1: Use provisioning script (recommended)
#     - Run: python3 provision-scenario.py scenario.json
#     - This auto-generates .env with all settings
#     - Skip manual .env creation
#
#   Option 2: Manual setup (without provisioning scripts)
#     - Copy this file: cp .env.example .env
#     - Edit .env with your settings below
#     - Run: ./run.sh
#
# NOTE: If you have provisioning scripts, use Option 1.
#       This .env.example is for Option 2 (manual setup).
################################################################################

# ThingsBoard Connection
REST_URL=http://localhost:8080
REST_USERNAME=tenant@thingsboard.org
REST_PASSWORD=tenant

# MQTT Connection
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_SSL_ENABLED=false

# Test Parameters
TEST_API=device
DEVICE_API=MQTT
TEST_PAYLOAD_TYPE=EBMPAPST_FFU

# Device Configuration
DEVICE_START_IDX=0
DEVICE_END_IDX=100
DEVICE_CREATE_ON_START=true
DEVICE_DELETE_ON_COMPLETE=false

# Performance Parameters
MESSAGES_PER_SECOND=50
DURATION_IN_SECONDS=300
WARMUP_ENABLED=true

# Alarm Configuration
ALARMS_PER_SECOND=0
UPDATE_ROOT_RULE_CHAIN=false
REVERT_ROOT_RULE_CHAIN=false

# Logging
LOGGING_LEVEL=INFO
ENVFILE

echo -e "${GREEN}✓${NC} .env template created"

# Step 4: Create run script
cat > "${DIST_DIR}/run.sh" << 'RUNFILE'
#!/bin/bash

################################################################################
# Quick Run Script
#
# Usage:
#   1. Edit .env with your configuration
#   2. Run: ./run.sh
#
# Or with inline variables:
#   REST_URL=http://your-server:8080 ./run.sh
################################################################################

set -e

# Check Java
if ! command -v java &> /dev/null; then
    echo "ERROR: Java is not installed or not in PATH"
    echo "Please install Java 17 or higher"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 17 ]; then
    echo "ERROR: Java 17+ required, found Java $JAVA_VERSION"
    exit 1
fi

# Find JAR file (script is already in bin/ directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR_FILE=$(ls -1 "$SCRIPT_DIR"/*.jar 2>/dev/null | head -1)
if [ -z "$JAR_FILE" ]; then
    echo "ERROR: No JAR file found in $SCRIPT_DIR directory"
    exit 1
fi

echo "=========================================="
echo "ThingsBoard Performance Tests"
echo "=========================================="
echo "Java Version: $JAVA_VERSION"
echo "JAR File: $(basename $JAR_FILE)"
echo ""

# Load .env if it exists (check multiple locations)
ENV_LOADED=0

# Check 1: Current directory (basedir)
if [ -f ".env" ]; then
    echo "Loading configuration from .env (basedir)..."
    set -a
    source .env
    set +a
    ENV_LOADED=1
# Check 2: provisioning/ directory (generated by provision script)
elif [ -f "$SCRIPT_DIR/provisioning/.env" ]; then
    echo "Loading configuration from provisioning/.env (auto-generated)..."
    set -a
    source "$SCRIPT_DIR/provisioning/.env"
    set +a
    ENV_LOADED=1
# Check 3: config/.env as fallback
elif [ -f "$SCRIPT_DIR/config/.env" ]; then
    echo "Loading configuration from config/.env..."
    set -a
    source "$SCRIPT_DIR/config/.env"
    set +a
    ENV_LOADED=1
fi

if [ $ENV_LOADED -eq 1 ]; then
    echo "✓ Configuration loaded"
else
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please choose one of these options:"
    echo ""
    echo "Option 1 (Recommended): Use provisioning script"
    echo "  cd provisioning"
    echo "  cp credentials.json.example credentials.json"
    echo "  # Edit credentials.json with your ThingsBoard server details"
    echo "  python3 provision-scenario.py scenarios/scenario-hanoi-cleanroom.json"
    echo "  # This auto-generates provisioning/.env"
    echo "  cd .. && ./run.sh"
    echo ""
    echo "Option 2 (Manual): Create .env manually"
    echo "  cp config/.env.example .env"
    echo "  # Edit .env with your settings"
    echo "  ./run.sh"
    echo ""
    exit 1
fi

echo ""
echo "Configuration:"
echo "  REST_URL: $REST_URL"
echo "  MQTT_HOST: $MQTT_HOST"
echo "  TEST_PAYLOAD_TYPE: $TEST_PAYLOAD_TYPE"
echo "  DEVICE_END_IDX: $DEVICE_END_IDX"
echo "  MESSAGES_PER_SECOND: $MESSAGES_PER_SECOND"
echo ""
echo "Starting performance tests..."
echo "=========================================="
echo ""

java -jar "$JAR_FILE"
RUNFILE

chmod +x "${DIST_DIR}/run.sh"
echo -e "${GREEN}✓${NC} Run script created"

# Step 5: Create documentation
cat > "${DIST_DIR}/README.md" << 'READMEFILE'
# ThingsBoard Performance Tests

Complete performance testing solution for ThingsBoard with automated provisioning.

## Package Structure

```
performance-tests-dist-4.0.1/
├── bin/
│   ├── tb-ce-performance-tests-4.0.1.jar    # Executable JAR
│   ├── run.sh                                # Linux/macOS launcher
│   └── run.bat                               # Windows launcher
├── provisioning/
│   ├── provision-scenario.py                 # Auto-provision devices
│   ├── cleanup-scenario.py                   # Cleanup script
│   ├── credentials.json.example              # Credentials template
│   └── scenarios/                            # Pre-defined scenarios
│       ├── scenario-hanoi-cleanroom.json
│       └── scenario-simple-devices.json
├── config/
│   ├── .env.example                          # Manual config template
│   └── attributes/                           # FFU config files
├── docs/                                     # Additional documentation
├── README.md                                 # This file
├── CHANGELOG.md
└── LICENSE
```

## Requirements

- **Java 17** or higher (check with `java -version`)
- **Python 3.8+** (for provisioning, optional)
- **ThingsBoard server** (local or remote)
- **Network access** to ThingsBoard

## Quick Start

You have two options for setup:

### Option 1: Automated Provisioning (Recommended)

Full automated setup with complex device hierarchies:

```bash
# 1. Configure credentials
cp provisioning/credentials.json.example provisioning/credentials.json
nano provisioning/credentials.json

# 2. Run provisioning (auto-creates devices + generates .env)
python3 provisioning/provision-scenario.py \
  provisioning/scenarios/scenario-hanoi-cleanroom.json

# 3. Run tests (uses auto-generated .env)
./run.sh
```

**What provisioning does**:
- ✅ Creates ThingsBoard entities (sites, buildings, gateways, devices)
- ✅ Sets up device relationships and hierarchies
- ✅ Generates `.env` with correct device tokens
- ✅ Configures MQTT settings automatically
- ✅ No manual configuration needed

**Available scenarios**:
- `scenario-hanoi-cleanroom.json` - Hanoi cleanroom with 2 sites, 4 gateways, 20 devices
- `scenario-simple-devices.json` - Simple device-only setup

### Option 2: Manual Setup (Quick Tests)

For simple testing without provisioning:

```bash
# 1. Copy configuration template
cp config/.env.example .env

# 2. Edit with your settings
nano .env

# Required settings:
#   REST_URL=http://your-server:8080
#   REST_USERNAME=your_user
#   REST_PASSWORD=your_password
#   MQTT_HOST=your-server
#   DEVICE_END_IDX=100

# 3. Run tests
./run.sh
```

**What happens**:
- Application creates devices automatically (`DEVICE_CREATE_ON_START=true`)
- Devices connect via MQTT
- Telemetry published at configured rate
- Optional cleanup on completion

## Configuration Guide

### Connection Settings
- `REST_URL` - ThingsBoard REST API endpoint
- `REST_USERNAME` / `REST_PASSWORD` - Login credentials
- `MQTT_HOST` / `MQTT_PORT` - MQTT broker address

### Test Parameters
- `TEST_PAYLOAD_TYPE` - Telemetry type: EBMPAPST_FFU, SMART_TRACKER, SMART_METER, INDUSTRIAL_PLC, DEFAULT
- `DEVICE_API` - Protocol: MQTT, HTTP, LWM2M
- `TEST_API` - Mode: device (direct) or gateway
- `DEVICE_START_IDX` / `DEVICE_END_IDX` - Range of device IDs
- `MESSAGES_PER_SECOND` - Publishing rate
- `DURATION_IN_SECONDS` - Test duration

### Lifecycle Options
- `DEVICE_CREATE_ON_START` - Create devices before test (true/false)
- `DEVICE_DELETE_ON_COMPLETE` - Delete devices after test (true/false)
- `WARMUP_ENABLED` - Send warmup messages (true/false)
- `UPDATE_ROOT_RULE_CHAIN` - Replace root rule chain (true/false)

## Troubleshooting

### Java not found
```bash
# Install Java 17
# Ubuntu/Debian:
sudo apt-get install openjdk-17-jre-headless

# macOS:
brew install openjdk@17
```

### Connection refused
- Verify `REST_URL` is reachable: `curl -I http://your-server:8080`
- Check `MQTT_HOST` connectivity: `nc -zv $MQTT_HOST $MQTT_PORT`
- Verify credentials are correct

### Devices not created
- Check `DEVICE_CREATE_ON_START=true` in .env
- Verify REST credentials have admin privileges
- Check server logs for errors

### No telemetry appearing
- Verify `TEST_PAYLOAD_TYPE` matches your device profile
- Check device connectivity in ThingsBoard UI
- Review application logs for errors

## Output

The application will display:
- Test initialization progress
- Device creation/provisioning
- Warmup phase status
- Real-time message rate and success count
- Performance statistics on completion
- Cleanup operations

## Example Scenarios

### Scenario 1: Light Load (100 devices)
```bash
DEVICE_END_IDX=100
MESSAGES_PER_SECOND=10
DURATION_IN_SECONDS=600
```

### Scenario 2: Medium Load (1000 devices)
```bash
DEVICE_END_IDX=1000
MESSAGES_PER_SECOND=50
DURATION_IN_SECONDS=300
```

### Scenario 3: Heavy Load (5000 devices)
```bash
DEVICE_END_IDX=5000
MESSAGES_PER_SECOND=100
DURATION_IN_SECONDS=180
```

## Support

For detailed documentation, visit the project repository or check the docs/ directory.

For issues or questions, review:
- Application logs (printed to console)
- ThingsBoard server logs
- Network connectivity
READMEFILE

echo -e "${GREEN}✓${NC} README created"

# Step 6: Create Windows batch file
cat > "${DIST_DIR}/run.bat" << 'BATFILE'
@echo off
REM ============================================================================
REM Performance Tests Run Script for Windows
REM
REM Usage:
REM   1. Edit .env with your configuration
REM   2. Run: run.bat
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo ThingsBoard Performance Tests
echo ==========================================
echo.

REM Check Java
java -version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Java is not installed or not in PATH
    echo Please install Java 17 or higher
    exit /b 1
)

REM Find JAR file in bin directory
for %%f in (bin\*.jar) do (
    set JAR_FILE=%%f
    goto :found_jar
)

:found_jar
if "%JAR_FILE%"=="" (
    echo ERROR: No JAR file found in bin\ directory
    exit /b 1
)

echo Java Version: 
java -version

echo JAR File: %JAR_FILE%
echo.

REM Load .env if it exists
if exist ".env" (
    echo Loading configuration from .env...
    for /f "delims=" %%i in (.env) do (
        if not "%%i"=="" (
            if not "%%i:~0,1%%"=="#" (
                set "%%i"
            )
        )
    )
    echo Configuration loaded
) else (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and update with your settings
    exit /b 1
)

echo.
echo Configuration:
echo   REST_URL: %REST_URL%
echo   MQTT_HOST: %MQTT_HOST%
echo.
echo Starting performance tests...
echo ==========================================
echo.

java -jar "%JAR_FILE%"
pause
BATFILE

echo -e "${GREEN}✓${NC} Windows batch script created"

# Move run scripts to bin/
mv "${DIST_DIR}/run.sh" "${DIST_DIR}/bin/"
mv "${DIST_DIR}/run.bat" "${DIST_DIR}/bin/"

# Create convenience run scripts in root
cat > "${DIST_DIR}/run.sh" << 'ROOTRUN'
#!/bin/bash
cd "$(dirname "$0")" && bin/run.sh "$@"
ROOTRUN
chmod +x "${DIST_DIR}/run.sh"

cat > "${DIST_DIR}/run.bat" << 'ROOTBAT'
@echo off
cd /d "%~dp0" && bin\run.bat %*
ROOTBAT

echo -e "${GREEN}✓${NC} Run scripts organized"

# Step 7: Create provisioning README
if [ -f "${DIST_DIR}/provisioning/provision-scenario.py" ]; then
cat > "${DIST_DIR}/provisioning/README.md" << 'PROVREADME'
# Provisioning Scripts

Automated device provisioning for ThingsBoard Performance Tests.

## Quick Start

```bash
# 1. Configure credentials
cp credentials.json.example credentials.json
nano credentials.json

# 2. Run provisioning
python3 provision-scenario.py scenarios/scenario-hanoi-cleanroom.json

# 3. Run tests (from parent directory)
cd .. && ./run.sh
```

## What It Does

The provisioning script:
- ✅ Creates sites (assets)
- ✅ Creates buildings (assets)
- ✅ Creates gateways (devices)
- ✅ Creates end devices (devices)
- ✅ Establishes relationships
- ✅ Generates `.env` file automatically

## Available Scenarios

### scenario-hanoi-cleanroom.json
Full Hanoi cleanroom setup with:
- 2 sites (Hanoi Site 1 & 2)
- 4 buildings per site
- 1 gateway per building
- 5 devices per gateway
- Total: ~40 devices

### scenario-simple-devices.json
Simple device-only setup:
- 10-100 devices (configurable)
- No complex hierarchy
- Quick testing

## Credentials Format

`credentials.json`:
```json
{
  "url": "http://your-thingsboard:8080",
  "username": "tenant@thingsboard.org",
  "password": "tenant"
}
```

## Generated Files

After provisioning:
- `../.env` - Auto-generated test configuration
- Device tokens, gateway tokens, and settings pre-configured

## Cleanup

Remove all provisioned entities:
```bash
python3 cleanup-scenario.py scenarios/scenario-hanoi-cleanroom.json
```

## Troubleshooting

**Connection refused**:
- Check `url` in credentials.json
- Verify ThingsBoard is running

**Authentication failed**:
- Check username/password in credentials.json
- Verify user has admin privileges

**Devices not created**:
- Check ThingsBoard logs
- Verify sufficient resources on server
PROVREADME
echo -e "${GREEN}✓${NC} Provisioning README created"
fi

# Step 8: Create LICENSE symlink or copy
if [ -f "LICENSE" ]; then
    cp LICENSE "${DIST_DIR}/"
    echo -e "${GREEN}✓${NC} License included"
fi

# Step 8: Create CHANGELOG reference
cat > "${DIST_DIR}/CHANGELOG.md" << 'CHANGELOGFILE'
# Changelog

## Version 4.0.1

### Features
- ✅ EBMPAPST FFU device profile with realistic telemetry
- ✅ 11 alarm rules for FFU monitoring
- ✅ YAML-based attribute configuration
- ✅ Configurable telemetry payloads
- ✅ Support for MQTT, HTTP, and LWM2M protocols
- ✅ Gateway API testing
- ✅ Performance metrics collection

### Improvements
- Optimized message generation
- Better error handling
- Comprehensive logging

For full changelog, see the main project repository.
CHANGELOGFILE

echo -e "${GREEN}✓${NC} Changelog included"

# Step 9: Create package info
cat > "${DIST_DIR}/PACKAGE.md" << 'PACKAGEFILE'
# Distribution Package Contents

## Files

```
tb-ce-performance-tests-4.0.1/
├── tb-ce-performance-tests-4.0.1.jar    # Main executable (all deps included)
├── run.sh                               # Linux/macOS run script
├── run.bat                              # Windows run script
├── .env.example                         # Configuration template
├── README.md                            # Quick start guide
├── CHANGELOG.md                         # Version history
├── LICENSE                              # Apache 2.0 License
└── PACKAGE.md                           # This file
```

## JAR Contents

The JAR file contains:
- Compiled Java application (Spring Boot)
- All library dependencies (Maven dependencies)
- Configuration resources (device profiles, rule chains)
- Embedded Tomcat web server

Total size: ~120-150 MB (includes all dependencies)

## Usage

1. Extract the ZIP file
2. Copy `.env.example` to `.env`
3. Edit `.env` with your settings
4. Run `./run.sh` (Linux/macOS) or `run.bat` (Windows)

Or directly:
```bash
source .env
java -jar tb-ce-performance-tests-4.0.1.jar
```

## System Requirements

- Java 17 or higher
- 2+ GB RAM recommended
- Network access to ThingsBoard server
- 50+ MB disk space (for temporary files during test)

## Troubleshooting

**Java not found:**
```bash
# Linux/macOS
brew install openjdk@17

# Ubuntu/Debian
sudo apt install openjdk-17-jre-headless

# Windows
Download from https://adoptium.net/
```

**Still having issues?**
Check the README.md for detailed troubleshooting guide.
PACKAGEFILE

echo -e "${GREEN}✓${NC} Package documentation created"

# Step 10: Create ZIP file
echo -e "${BLUE}[4/6]${NC} Creating ZIP archive..."
rm -f "${ZIP_FILE}"
zip -r -q "${ZIP_FILE}" "${DIST_DIR}"
ZIP_SIZE=$(du -h "${ZIP_FILE}" | cut -f1)
echo -e "${GREEN}✓${NC} ZIP file created (${ZIP_SIZE})"

# Step 11: Create SHA256 checksum
echo -e "${BLUE}[5/6]${NC} Generating checksums..."
sha256sum "${ZIP_FILE}" > "${ZIP_FILE}.sha256"
echo -e "${GREEN}✓${NC} Checksums generated"

# Step 12: Create installation guide
cat > "INSTALLATION.md" << 'INSTALLFILE'
# Installation Guide

## Package Contents

Download `tb-ce-performance-tests-4.0.1.zip` from the releases page.

## Installation Steps

### 1. Extract the Package

**Linux/macOS:**
```bash
unzip tb-ce-performance-tests-4.0.1.zip
cd tb-ce-performance-tests-4.0.1
```

**Windows:**
- Right-click ZIP file → Extract All
- Open the extracted folder

### 2. Verify Java Installation

```bash
java -version
```

You should see Java 17 or higher. If not, install Java first:
- [OpenJDK 17 Downloads](https://adoptium.net/)

### 3. Configure Environment

```bash
# Copy configuration template
cp .env.example .env

# Edit with your ThingsBoard settings
# Linux/macOS:
nano .env

# Windows (open in any text editor):
run.bat  # Edit the file before running
```

### 4. Run the Tests

**Linux/macOS:**
```bash
./run.sh
```

**Windows:**
```
Double-click run.bat
```

**Or directly with Java:**
```bash
source .env  # Linux/macOS
java -jar tb-ce-performance-tests-4.0.1.jar
```

## Configuration Quick Reference

Key settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| REST_URL | http://localhost:8080 | ThingsBoard API endpoint |
| REST_USERNAME | tenant@thingsboard.org | Login username |
| REST_PASSWORD | tenant | Login password |
| MQTT_HOST | localhost | MQTT broker address |
| TEST_PAYLOAD_TYPE | EBMPAPST_FFU | Device telemetry type |
| DEVICE_END_IDX | 100 | Number of devices to simulate |
| MESSAGES_PER_SECOND | 50 | Publishing rate |
| DURATION_IN_SECONDS | 300 | Test duration |

## First Test Run

1. Start with small scale:
   ```
   DEVICE_END_IDX=10
   MESSAGES_PER_SECOND=5
   DURATION_IN_SECONDS=60
   ```

2. Monitor ThingsBoard to see devices and telemetry appearing

3. Gradually increase load for production testing

## Troubleshooting

**Connection refused error:**
- Verify REST_URL is reachable
- Check credentials are correct
- Ensure ThingsBoard is running

**No devices created:**
- Set `DEVICE_CREATE_ON_START=true`
- Check REST credentials have admin access
- Review console output for error messages

**Low throughput:**
- Check network bandwidth to ThingsBoard
- Increase MESSAGES_PER_SECOND gradually
- Monitor server CPU/Memory

For more help, see README.md included in the package.
INSTALLFILE

echo -e "${GREEN}✓${NC} Installation guide created"

# Final summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Package Created Successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "📦 ${YELLOW}${ZIP_FILE}${NC}"
echo -e "   Size: ${ZIP_SIZE}"
echo ""
echo "Contents:"
echo "  ✓ tb-ce-performance-tests-${PROJECT_VERSION}.jar"
echo "  ✓ run.sh (Linux/macOS)"
echo "  ✓ run.bat (Windows)"
echo "  ✓ .env.example (Configuration template)"
echo "  ✓ README.md (Quick start guide)"
echo "  ✓ CHANGELOG.md"
echo "  ✓ LICENSE"
echo "  ✓ PACKAGE.md"
echo ""
echo "Next steps:"
echo "  1. Distribute ${ZIP_FILE}"
echo "  2. User extracts ZIP"
echo "  3. User copies .env.example → .env"
echo "  4. User edits .env with their settings"
echo "  5. User runs: ./run.sh (or run.bat on Windows)"
echo ""
echo -e "SHA256 checksum saved in:"
echo -e "  • ${ZIP_FILE}.sha256"
echo ""

# Cleanup
echo -e "${BLUE}[6/6]${NC} Cleaning up..."
rm -rf "${DIST_DIR}"
echo -e "${GREEN}✓${NC} Done"
echo ""
echo -e "${GREEN}Ready to deploy! ${NC}🚀"

