# FFU Device Test Implementation Guide

This guide provides step-by-step instructions for adding FFU (Fan Filter Unit) device performance tests to the ThingsBoard Performance Tests project.

## What is an FFU Device?

Fan Filter Units (FFUs) are industrial air filtration devices commonly used in cleanrooms, manufacturing facilities, and controlled environments. They monitor and control air quality through filtration and circulation.

### Typical FFU Telemetry Data:
- **fanSpeed** - Current fan RPM (0-2000)
- **filterPressure** - Pressure differential across filter in Pascals (0-500)
- **airFlowRate** - Air flow in cubic meters per hour (0-3000)
- **motorTemperature** - Motor temperature in Celsius (20-80)
- **filterLifetime** - Remaining filter life percentage (0-100)
- **powerConsumption** - Power usage in Watts (0-2000)
- **operatingHours** - Total operating hours

### Typical FFU Attributes:
- **firmwareVersion** - Device firmware version
- **serialNumber** - Unique device serial number
- **model** - FFU model identifier
- **manufacturer** - Device manufacturer
- **installationDate** - Installation timestamp

## Implementation Steps

### Step 1: Create Package Structure

Create the following directory:
```bash
mkdir -p src/main/java/org/thingsboard/tools/service/msg/ffu
```

### Step 2: Create FFU Telemetry Generator

Create file: `src/main/java/org/thingsboard/tools/service/msg/ffu/FfuTelemetryGenerator.java`

```java
/**
 * Copyright © 2016-2025 The Thingsboard Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.thingsboard.tools.service.msg.ffu;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.thingsboard.tools.service.msg.BaseMessageGenerator;
import org.thingsboard.tools.service.msg.MessageGenerator;
import org.thingsboard.tools.service.msg.Msg;

@Slf4j
@Service(value = "randomTelemetryGenerator")
@ConditionalOnProperty(prefix = "test", value = "payloadType", havingValue = "FFU")
public class FfuTelemetryGenerator extends BaseMessageGenerator implements MessageGenerator {

    // Alarm thresholds
    static final int FILTER_PRESSURE_ALARM = 450;     // High pressure indicates clogged filter
    static final int MOTOR_TEMP_ALARM = 75;           // High temperature alarm
    static final int FILTER_LIFETIME_ALARM = 10;      // Low filter lifetime alarm

    @Override
    public Msg getNextMessage(String deviceName, boolean shouldTriggerAlarm) {
        byte[] payload;
        try {
            ObjectNode data = mapper.createObjectNode();
            ObjectNode tsNode;

            // Handle gateway vs device mode
            if (isGateway()) {
                ArrayNode array = data.putArray(deviceName);
                tsNode = array.addObject();
            } else {
                tsNode = data;
            }

            tsNode.put("ts", System.currentTimeMillis());
            ObjectNode values = tsNode.putObject("values");

            // Generate FFU telemetry data
            int fanSpeed = random.nextInt(1000) + 1000;  // 1000-2000 RPM
            values.put("fanSpeed", fanSpeed);

            // Filter pressure - trigger alarm if shouldTriggerAlarm is true
            int filterPressure = shouldTriggerAlarm ?
                FILTER_PRESSURE_ALARM + random.nextInt(50) :
                random.nextInt(300) + 100;  // Normal: 100-400 Pa
            values.put("filterPressure", filterPressure);

            // Air flow rate correlates with fan speed
            double airFlowRate = (fanSpeed / 2000.0) * 2500 + random.nextDouble() * 500;
            values.put("airFlowRate", Math.round(airFlowRate * 100.0) / 100.0);

            // Motor temperature - normal 40-60°C, alarm at 75°C+
            int motorTemperature = shouldTriggerAlarm ?
                MOTOR_TEMP_ALARM + random.nextInt(10) :
                random.nextInt(20) + 40;
            values.put("motorTemperature", motorTemperature);

            // Filter lifetime - alarm when < 10%
            int filterLifetime = shouldTriggerAlarm ?
                random.nextInt(FILTER_LIFETIME_ALARM) :
                random.nextInt(90) + 10;
            values.put("filterLifetime", filterLifetime);

            // Power consumption correlates with fan speed
            int powerConsumption = (int)(fanSpeed / 2000.0 * 1500) + random.nextInt(200);
            values.put("powerConsumption", powerConsumption);

            // Operating hours - cumulative counter
            values.put("operatingHours", random.nextInt(50000));

            // Operating status
            values.put("status", shouldTriggerAlarm ? "ALARM" : "RUNNING");

            payload = mapper.writeValueAsBytes(data);
        } catch (Exception e) {
            log.warn("Failed to generate FFU message", e);
            throw new RuntimeException(e);
        }
        return new Msg(payload, shouldTriggerAlarm);
    }
}
```

### Step 3: Create FFU Attributes Generator

Create file: `src/main/java/org/thingsboard/tools/service/msg/ffu/FfuAttributesGenerator.java`

```java
/**
 * Copyright © 2016-2025 The Thingsboard Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.thingsboard.tools.service.msg.ffu;

import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.thingsboard.tools.service.msg.BaseMessageGenerator;
import org.thingsboard.tools.service.msg.MessageGenerator;
import org.thingsboard.tools.service.msg.Msg;

@Slf4j
@Service(value = "randomAttributesGenerator")
@ConditionalOnProperty(prefix = "test", value = "payloadType", havingValue = "FFU")
public class FfuAttributesGenerator extends BaseMessageGenerator implements MessageGenerator {

    private static final String[] MODELS = {"FFU-1200H", "FFU-1500H", "FFU-2000H", "FFU-2500H"};
    private static final String[] MANUFACTURERS = {"CleanAir Systems", "FilterTech", "AirFlow Industries"};

    @Override
    public Msg getNextMessage(String deviceName, boolean shouldTriggerAlarm) {
        byte[] payload;
        try {
            ObjectNode data = mapper.createObjectNode();
            ObjectNode values;

            if (isGateway()) {
                values = data.putObject(deviceName);
            } else {
                values = data;
            }

            // Static device attributes
            values.put("firmwareVersion", "v" + random.nextInt(3) + "." + random.nextInt(10) + "." + random.nextInt(100));
            values.put("serialNumber", "FFU-SN-" + String.format("%08d", random.nextInt(100000000)));
            values.put("model", MODELS[random.nextInt(MODELS.length)]);
            values.put("manufacturer", MANUFACTURERS[random.nextInt(MANUFACTURERS.length)]);
            values.put("installationDate", System.currentTimeMillis() - (long)random.nextInt(365*2) * 24 * 60 * 60 * 1000); // Within last 2 years
            values.put("filterType", "HEPA-H14");
            values.put("filterChangeInterval", 8760); // Hours (1 year)
            values.put("maxAirFlowRate", 3000);
            values.put("ratedPower", 1800);

            payload = mapper.writeValueAsBytes(data);
        } catch (Exception e) {
            log.warn("Failed to generate FFU attributes", e);
            throw new RuntimeException(e);
        }
        return new Msg(payload);
    }
}
```

### Step 4: Create Device Profile JSON

Create file: `src/main/resources/device/profile/ffu.json`

```json
{
  "name": "FFU",
  "description": "Fan Filter Unit profile created by performance test",
  "image": null,
  "type": "DEFAULT",
  "transportType": "DEFAULT",
  "provisionType": "DISABLED",
  "defaultRuleChainId": null,
  "defaultDashboardId": null,
  "defaultQueueName": "",
  "profileData": {
    "configuration": {
      "type": "DEFAULT"
  
    "transportConfiguration": {
      "type": "DEFAULT"
  
    "provisionConfiguration": {
      "type": "DISABLED",
      "provisionDeviceSecret": null
  
    "alarms": [
      {
        "id": "ffu-filter-pressure-alarm",
        "alarmType": "High Filter Pressure",
        "createRules": {
          "CRITICAL": {
            "condition": {
              "condition": [
                {
                  "key": {
                    "type": "TIME_SERIES",
                    "key": "filterPressure"
                
                  "valueType": "NUMERIC",
                  "value": null,
                  "predicate": {
                    "type": "NUMERIC",
                    "operation": "GREATER_OR_EQUAL",
                    "value": {
                      "defaultValue": 450,
                      "userValue": null,
                      "dynamicValue": null
                    }
                  }
                }
              ],
              "spec": {
                "type": "SIMPLE"
              }
          
            "schedule": null,
            "alarmDetails": "Filter pressure too high - filter may be clogged",
            "dashboardId": null
          }
      
        "clearRule": {
          "condition": {
            "condition": [
              {
                "key": {
                  "type": "TIME_SERIES",
                  "key": "filterPressure"
              
                "valueType": "NUMERIC",
                "value": null,
                "predicate": {
                  "type": "NUMERIC",
                  "operation": "LESS",
                  "value": {
                    "defaultValue": 400,
                    "userValue": null,
                    "dynamicValue": null
                  }
                }
              }
            ],
            "spec": {
              "type": "SIMPLE"
            }
        
          "schedule": null,
          "alarmDetails": null,
          "dashboardId": null
      
        "propagate": false,
        "propagateRelationTypes": null
    
      {
        "id": "ffu-motor-temp-alarm",
        "alarmType": "High Motor Temperature",
        "createRules": {
          "CRITICAL": {
            "condition": {
              "condition": [
                {
                  "key": {
                    "type": "TIME_SERIES",
                    "key": "motorTemperature"
                
                  "valueType": "NUMERIC",
                  "value": null,
                  "predicate": {
                    "type": "NUMERIC",
                    "operation": "GREATER_OR_EQUAL",
                    "value": {
                      "defaultValue": 75,
                      "userValue": null,
                      "dynamicValue": null
                    }
                  }
                }
              ],
              "spec": {
                "type": "SIMPLE"
              }
          
            "schedule": null,
            "alarmDetails": "Motor temperature critical - check cooling system",
            "dashboardId": null
          }
      
        "clearRule": {
          "condition": {
            "condition": [
              {
                "key": {
                  "type": "TIME_SERIES",
                  "key": "motorTemperature"
              
                "valueType": "NUMERIC",
                "value": null,
                "predicate": {
                  "type": "NUMERIC",
                  "operation": "LESS",
                  "value": {
                    "defaultValue": 65,
                    "userValue": null,
                    "dynamicValue": null
                  }
                }
              }
            ],
            "spec": {
              "type": "SIMPLE"
            }
        
          "schedule": null,
          "alarmDetails": null,
          "dashboardId": null
      
        "propagate": false,
        "propagateRelationTypes": null
    
      {
        "id": "ffu-filter-lifetime-alarm",
        "alarmType": "Low Filter Lifetime",
        "createRules": {
          "WARNING": {
            "condition": {
              "condition": [
                {
                  "key": {
                    "type": "TIME_SERIES",
                    "key": "filterLifetime"
                
                  "valueType": "NUMERIC",
                  "value": null,
                  "predicate": {
                    "type": "NUMERIC",
                    "operation": "LESS_OR_EQUAL",
                    "value": {
                      "defaultValue": 10,
                      "userValue": null,
                      "dynamicValue": null
                    }
                  }
                }
              ],
              "spec": {
                "type": "SIMPLE"
              }
          
            "schedule": null,
            "alarmDetails": "Filter lifetime low - schedule replacement",
            "dashboardId": null
          }
      
        "clearRule": {
          "condition": {
            "condition": [
              {
                "key": {
                  "type": "TIME_SERIES",
                  "key": "filterLifetime"
              
                "valueType": "NUMERIC",
                "value": null,
                "predicate": {
                  "type": "NUMERIC",
                  "operation": "GREATER",
                  "value": {
                    "defaultValue": 20,
                    "userValue": null,
                    "dynamicValue": null
                  }
                }
              }
            ],
            "spec": {
              "type": "SIMPLE"
            }
        
          "schedule": null,
          "alarmDetails": null,
          "dashboardId": null
      
        "propagate": false,
        "propagateRelationTypes": null
      }
    ]

  "provisionDeviceKey": null,
  "firmwareId": null,
  "softwareId": null,
  "default": false
}
```

### Step 5: Update README.md

Add FFU to the payload types list in `README.md`:

```bash
# Type of the payload to send: DEFAULT, SMART_TRACKER, SMART_METER, INDUSTRIAL_PLC, FFU
# RANDOM - TODO: add description
# SMART_TRACKER - sample payload: {"latitude": 42.222222, "longitude": 73.333333, "speed": 55.5, "fuel": 92, "batteryLevel": 81}
# SMART_METER - sample payload: {"pulseCounter": 1234567, "leakage": false, "batteryLevel": 81}
# INDUSTRIAL_PLC - sample payload (60 lines by default) {"line001": 1.0023, "line002": 95.440321}
# FFU - sample payload: {"fanSpeed": 1500, "filterPressure": 250, "airFlowRate": 2100.5, "motorTemperature": 50, "filterLifetime": 65, "powerConsumption": 1200, "operatingHours": 15000, "status": "RUNNING"}
TEST_PAYLOAD_TYPE=FFU
```

## Testing the FFU Implementation

### Test 1: Basic Local Test

```bash
# Edit start.sh or create a new test script
export REST_URL=http://127.0.0.1:8080
export MQTT_HOST=127.0.0.1
export REST_USERNAME=tenant@thingsboard.org
export REST_PASSWORD=tenant
export TEST_PAYLOAD_TYPE=FFU
export DEVICE_START_IDX=0
export DEVICE_END_IDX=10
export MESSAGES_PER_SECOND=10
export DURATION_IN_SECONDS=60
export DEVICE_CREATE_ON_START=true
export DEVICE_DELETE_ON_COMPLETE=false

mvn spring-boot:run
```

### Test 2: Docker Test

```bash
# Create .env file
cat > .env.ffu << EOF
REST_URL=http://192.168.1.100:8080
MQTT_HOST=192.168.1.100
REST_USERNAME=tenant@thingsboard.org
REST_PASSWORD=tenant
TEST_PAYLOAD_TYPE=FFU
DEVICE_START_IDX=0
DEVICE_END_IDX=100
MESSAGES_PER_SECOND=100
DURATION_IN_SECONDS=300
DEVICE_CREATE_ON_START=true
ALARMS_PER_SECOND=5
EOF

# Build and run
./build.sh
docker run -it --env-file .env.ffu --name tb-perf-test-ffu thingsboard/tb-ce-performance-test:latest
```

### Test 3: High Load Test

```bash
# Test with 1000 FFU devices sending 1000 messages/second
export TEST_PAYLOAD_TYPE=FFU
export DEVICE_END_IDX=1000
export MESSAGES_PER_SECOND=1000
export DURATION_IN_SECONDS=600
export ALARMS_PER_SECOND=10
export DEVICE_CREATE_ON_START=true

mvn spring-boot:run
```

### Test 4: Alarm Storm Test

Test alarm generation under load:

```bash
export TEST_PAYLOAD_TYPE=FFU
export DEVICE_END_IDX=500
export MESSAGES_PER_SECOND=500
export DURATION_IN_SECONDS=300
export ALARMS_PER_SECOND=50  # High alarm rate to test alarm processing
export ALARM_STORM_START_SECOND=60
export ALARM_STORM_END_SECOND=180

mvn spring-boot:run
```

## Verification Steps

After running the test:

1. **Check Device Creation**
   - Log into ThingsBoard UI
   - Navigate to Devices → All
   - Verify FFU devices were created with correct profile

2. **Verify Telemetry Data**
   - Click on an FFU device
   - Check "Latest telemetry" tab
   - Verify all fields are present: fanSpeed, filterPressure, airFlowRate, motorTemperature, filterLifetime, powerConsumption, operatingHours, status

3. **Check Attributes**
   - Go to "Attributes" tab
   - Verify server/shared attributes: firmwareVersion, serialNumber, model, manufacturer, installationDate, filterType

4. **Verify Alarms**
   - Navigate to Alarms
   - Check that alarms were generated for:
     - High Filter Pressure (when filterPressure ≥ 450)
     - High Motor Temperature (when motorTemperature ≥ 75)
     - Low Filter Lifetime (when filterLifetime ≤ 10)

5. **Monitor Performance**
   - Check ThingsBoard system stats
   - Verify message processing rate matches configured MESSAGES_PER_SECOND
   - Monitor CPU/Memory usage
   - Check for any error logs

## Sample Expected Output

```json
{
  "fanSpeed": 1523,
  "filterPressure": 287,
  "airFlowRate": 2105.73,
  "motorTemperature": 52,
  "filterLifetime": 68,
  "powerConsumption": 1347,
  "operatingHours": 23456,
  "status": "RUNNING"
}
```

## Troubleshooting

### Issue: Devices not created
**Solution:** Ensure `DEVICE_CREATE_ON_START=true` and check REST API credentials

### Issue: No telemetry data
**Solution:** Verify MQTT_HOST is reachable and MQTT broker is running on ThingsBoard

### Issue: Alarms not triggering
**Solution:** Check device profile alarm rules match the thresholds in FfuTelemetryGenerator.java

### Issue: Build fails
**Solution:** Run `mvn clean install` and check for compilation errors in the Java files

## Performance Expectations

| Devices | Messages/sec | Expected CPU | Expected RAM | Duration |
|---------|--------------|--------------|--------------|----------|
| 100     | 100          | 10-20%       | 2 GB         | 5 min    |
| 500     | 500          | 30-40%       | 4 GB         | 10 min   |
| 1000    | 1000         | 50-70%       | 8 GB         | 15 min   |
| 5000    | 5000         | 80-100%      | 16 GB        | 30 min   |

*Note: Performance depends on ThingsBoard server specs and configuration*

## Next Steps

1. **Customize FFU Data Model** - Adjust telemetry fields based on your actual FFU devices
2. **Add Custom Alarms** - Create additional alarm rules in the device profile JSON
3. **Create Dashboard** - Build a ThingsBoard dashboard for FFU visualization
4. **Implement Gateway Mode** - Test using `TEST_API=gateway` for multi-device gateways
5. **Add HTTP/LWM2M Support** - Extend tests to support other protocols

## References

- [ThingsBoard Device Profiles](https://thingsboard.io/docs/user-guide/device-profiles/)
- [ThingsBoard Alarms](https://thingsboard.io/docs/user-guide/alarms/)
- [MQTT API Reference](https://thingsboard.io/docs/reference/mqtt-api/)
- Main project README.md
- CLAUDE.md - Project architecture guide
