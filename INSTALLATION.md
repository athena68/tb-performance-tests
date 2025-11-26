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
