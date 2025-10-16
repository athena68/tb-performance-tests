# ebmpapst FFU Device Test Implementation Guide

This guide provides step-by-step instructions for adding **ebmpapst Fan Filter Unit (FFU)** device performance tests to the ThingsBoard Performance Tests project.

> **Based on:** ebmpapst EC centrifugal fans with MODBUS-RTU communication protocol
> **References:** ebmpapst MODBUS parameter specifications V5.01, FanGrid documentation

## What is an ebmpapst FFU Device?

ebmpapst manufactures EC (Electronically Commutated) centrifugal fans for Fan Filter Units used in cleanrooms, chip manufacturing, pharmaceutical production, and controlled environments. These fans feature intelligent MODBUS-RTU communication for comprehensive monitoring and control.

### ebmpapst FFU Key Specifications:
- **Fan Diameters:** 310mm, 355mm, 400mm
- **Air Performance:** 1170-2330 m³/h per fan (at 250-300 Pa back pressure)
- **Communication:** MODBUS-RTU (RS485), 0-10V analog control
- **IoT Gateway Support:** MQTT, OPC-UA, BACnet IP
- **Auto-Addressing:** Automatic fan discovery and addressing
- **Efficiency:** >50% with EC technology

## ebmpapst FFU Telemetry Data (MODBUS Registers)

### Core Motor Parameters:
- **actualSpeed** - Current fan RPM (direct tachometer feedback)
- **speedSetpoint** - Target speed command in RPM
- **dcLinkVoltage** - DC bus voltage (V)
- **dcLinkCurrent** - Motor current draw (A)
- **powerConsumption** - Electrical power consumption (W)
- **motorTemperature** - Internal motor/electronics temperature (°C)
- **operatingHours** - Cumulative operating hours counter

### Filter & Airflow Parameters:
- **differentialPressure** - Pressure drop across HEPA filter (Pa) - via external 0-10V sensor
- **pressureSetpoint** - Target differential pressure (Pa)
- **calculatedAirflow** - Derived from speed and system curve (m³/h)

### Status & Control:
- **controlMode** - Current control mode (0=0-10V, 1=MODBUS)
- **operatingStatus** - Current state (RUNNING, STOPPED, ALARM, FAULT)
- **alarmCode** - Active alarm/fault code
- **warningCode** - Active warning code

### Temperature Monitoring:
- **motorTempDerating** - Temperature at which derating starts (°C)
- **motorTempShutdown** - Critical temperature for shutdown (°C)
- **ambientTemperature** - Optional external temperature sensor (°C)

## ebmpapst FFU Attributes

### Device Information:
- **firmwareVersion** - Motor controller firmware version
- **serialNumber** - Unique motor serial number
- **fanModel** - Fan model (e.g., "RadiPac-355", "R3G355-AS03-01")
- **manufacturer** - "ebm-papst"
- **modbusAddress** - MODBUS slave address (auto-assigned or manual)

### Installation Data:
- **installationDate** - Installation timestamp
- **commissioningDate** - System commissioning date
- **filterType** - HEPA filter specification (e.g., "H14")
- **filterInstallDate** - Last filter change date
- **filterChangeInterval** - Recommended change interval (hours)

### System Configuration:
- **ratedSpeed** - Maximum rated RPM
- **ratedAirflow** - Maximum rated airflow (m³/h)
- **ratedPower** - Rated electrical power (W)
- **fanDiameter** - Fan impeller diameter (mm)
- **numberOfFans** - Number of fans in FanGrid (if applicable)

## Implementation Steps

### Step 1: Create Package Structure

```bash
mkdir -p src/main/java/org/thingsboard/tools/service/msg/ebmpapstFfu
```

### Step 2: Create ebmpapst FFU Telemetry Generator

Create file: `src/main/java/org/thingsboard/tools/service/msg/ebmpapstFfu/EbmpapstFfuTelemetryGenerator.java`

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
package org.thingsboard.tools.service.msg.ebmpapstFfu;

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
@ConditionalOnProperty(prefix = "test", value = "payloadType", havingValue = "EBMPAPST_FFU")
public class EbmpapstFfuTelemetryGenerator extends BaseMessageGenerator implements MessageGenerator {

    // ebmpapst EC motor specifications
    static final int MIN_SPEED = 500;                    // Minimum RPM
    static final int MAX_SPEED = 2000;                   // Maximum RPM for typical FFU
    static final int RATED_SPEED = 1800;                 // Rated speed

    // Alarm thresholds based on ebmpapst specifications
    static final int DIFFERENTIAL_PRESSURE_ALARM = 450;  // High filter pressure (Pa)
    static final int MOTOR_TEMP_DERATING = 75;           // Temperature derating starts (°C)
    static final int MOTOR_TEMP_SHUTDOWN = 85;           // Critical shutdown temperature (°C)

    // Electrical specifications for 355mm fan
    static final double RATED_VOLTAGE = 400.0;           // DC-Link voltage (V)
    static final double RATED_CURRENT = 4.5;             // DC-Link current at full load (A)
    static final int RATED_POWER = 1500;                 // Rated power (W)

    // Airflow calculations (approximation for 355mm fan)
    static final int MAX_AIRFLOW = 2330;                 // m³/h at rated speed

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

            // Core Motor Parameters
            // Actual Speed - realistic variation around setpoint
            int speedSetpoint = random.nextInt(500) + 1300;  // 1300-1800 RPM typical operating range
            int actualSpeed = speedSetpoint + random.nextInt(20) - 10;  // ±10 RPM variation
            values.put("actualSpeed", actualSpeed);
            values.put("speedSetpoint", speedSetpoint);

            // Calculate airflow based on fan curve (simplified linear approximation)
            double speedRatio = (double) actualSpeed / RATED_SPEED;
            int calculatedAirflow = (int) (MAX_AIRFLOW * speedRatio);
            values.put("calculatedAirflow", calculatedAirflow);

            // DC-Link Voltage - relatively stable around rated voltage
            double dcLinkVoltage = RATED_VOLTAGE + (random.nextDouble() * 20 - 10);  // ±10V variation
            values.put("dcLinkVoltage", Math.round(dcLinkVoltage * 10.0) / 10.0);

            // DC-Link Current - correlates with speed/load
            double loadFactor = speedRatio * (0.7 + random.nextDouble() * 0.3);  // 70-100% load
            double dcLinkCurrent = RATED_CURRENT * loadFactor;
            values.put("dcLinkCurrent", Math.round(dcLinkCurrent * 100.0) / 100.0);

            // Power Consumption - P = V * I * efficiency
            int powerConsumption = (int) (dcLinkVoltage * dcLinkCurrent * 0.9);  // 90% efficiency
            values.put("powerConsumption", powerConsumption);

            // Differential Pressure across HEPA filter
            // Increases with airflow and filter clogging
            int basePressure = (int) (100 + (speedRatio * 150));  // 100-250 Pa for clean filter
            int filterClogging = random.nextInt(100);  // 0-100 Pa additional for clogging
            int differentialPressure = shouldTriggerAlarm ?
                DIFFERENTIAL_PRESSURE_ALARM + random.nextInt(50) :
                basePressure + filterClogging;
            values.put("differentialPressure", differentialPressure);
            values.put("pressureSetpoint", 250);  // Target differential pressure

            // Motor Temperature - correlates with load and ambient
            // ebmpapst has built-in temperature sensors
            int ambientTemp = 22 + random.nextInt(8);  // 22-30°C ambient
            int motorTempRise = (int) (loadFactor * 25);  // Temperature rise above ambient
            int motorTemperature = shouldTriggerAlarm ?
                MOTOR_TEMP_DERATING + random.nextInt(10) :
                ambientTemp + motorTempRise + random.nextInt(5);
            values.put("motorTemperature", motorTemperature);
            values.put("motorTempDerating", MOTOR_TEMP_DERATING);
            values.put("motorTempShutdown", MOTOR_TEMP_SHUTDOWN);
            values.put("ambientTemperature", ambientTemp);

            // Operating Hours - cumulative counter (MODBUS register D009)
            // In real system, this increments continuously
            values.put("operatingHours", random.nextInt(50000));

            // Control Mode: 0=0-10V analog, 1=MODBUS
            values.put("controlMode", 1);  // MODBUS control

            // Operating Status
            String operatingStatus;
            int alarmCode = 0;
            int warningCode = 0;

            if (shouldTriggerAlarm) {
                if (motorTemperature >= MOTOR_TEMP_SHUTDOWN) {
                    operatingStatus = "FAULT";
                    alarmCode = 101;  // Motor overheat alarm
                } else if (differentialPressure >= DIFFERENTIAL_PRESSURE_ALARM) {
                    operatingStatus = "ALARM";
                    alarmCode = 201;  // High differential pressure
                } else {
                    operatingStatus = "WARNING";
                    warningCode = 301;  // High temperature warning
                }
            } else {
                operatingStatus = actualSpeed < 100 ? "STOPPED" : "RUNNING";

                // Check for warnings even in normal operation
                if (differentialPressure > 350) {
                    warningCode = 302;  // Filter maintenance warning
                }
            }

            values.put("operatingStatus", operatingStatus);
            values.put("alarmCode", alarmCode);
            values.put("warningCode", warningCode);

            // Additional ebmpapst-specific parameters
            values.put("speedActualPercent", (int)((actualSpeed * 100.0) / RATED_SPEED));
            values.put("speedSetpointPercent", (int)((speedSetpoint * 100.0) / RATED_SPEED));

            // Modbus communication status
            values.put("modbusStatus", "OK");
            values.put("communicationErrors", random.nextInt(5));  // Communication error counter

            payload = mapper.writeValueAsBytes(data);
        } catch (Exception e) {
            log.warn("Failed to generate ebmpapst FFU message", e);
            throw new RuntimeException(e);
        }
        return new Msg(payload, shouldTriggerAlarm);
    }
}
```

### Step 3: Create ebmpapst FFU Attributes Generator

Create file: `src/main/java/org/thingsboard/tools/service/msg/ebmpapstFfu/EbmpapstFfuAttributesGenerator.java`

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
package org.thingsboard.tools.service.msg.ebmpapstFfu;

import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.thingsboard.tools.service.msg.BaseMessageGenerator;
import org.thingsboard.tools.service.msg.MessageGenerator;
import org.thingsboard.tools.service.msg.Msg;

@Slf4j
@Service(value = "randomAttributesGenerator")
@ConditionalOnProperty(prefix = "test", value = "payloadType", havingValue = "EBMPAPST_FFU")
public class EbmpapstFfuAttributesGenerator extends BaseMessageGenerator implements MessageGenerator {

    // ebmpapst fan models (actual product lines)
    private static final String[] FAN_MODELS = {
        "R3G355-AS03-01",  // RadiPac 355mm
        "R3G310-AP09-01",  // RadiPac 310mm
        "R3G400-AP30-01",  // RadiPac 400mm
        "R2E250-AE52-05",  // RadiCal 250mm
        "R2E220-AA06-17"   // RadiCal 220mm
    };

    private static final String[] FILTER_TYPES = {
        "HEPA H13",
        "HEPA H14",
        "ULPA U15",
        "ULPA U16"
    };

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

            // Device Information
            String selectedModel = FAN_MODELS[random.nextInt(FAN_MODELS.length)];
            values.put("fanModel", selectedModel);
            values.put("manufacturer", "ebm-papst");
            values.put("firmwareVersion", "ACE-" + (3 + random.nextInt(2)) + "." + random.nextInt(10));  // ACE-3.x or ACE-4.x

            // Extract diameter from model name (e.g., R3G355 -> 355mm)
            String diameterStr = selectedModel.substring(3, 6);
            values.put("fanDiameter", Integer.parseInt(diameterStr));

            // Serial number format: typical ebmpapst format
            values.put("serialNumber", "EBM-" + String.format("%04d", random.nextInt(10000)) +
                                      "-" + String.format("%06d", random.nextInt(1000000)));

            // MODBUS Configuration
            values.put("modbusAddress", 1 + random.nextInt(247));  // MODBUS address 1-247
            values.put("modbusBaudRate", 19200);  // Typical: 9600, 19200, 38400
            values.put("modbusProtocol", "RTU");

            // Communication interfaces
            values.put("communicationInterface", "RS485 MODBUS-RTU");
            values.put("analogControlSupport", true);  // 0-10V support
            values.put("iotGatewayProtocols", "MQTT, OPC-UA, BACnet IP");

            // Installation Data
            long currentTime = System.currentTimeMillis();
            long installDate = currentTime - (long)random.nextInt(730) * 24 * 60 * 60 * 1000;  // Within last 2 years
            values.put("installationDate", installDate);
            values.put("commissioningDate", installDate + 7 * 24 * 60 * 60 * 1000L);  // 1 week after install

            // Filter Information
            values.put("filterType", FILTER_TYPES[random.nextInt(FILTER_TYPES.length)]);
            long filterInstallDate = currentTime - (long)random.nextInt(365) * 24 * 60 * 60 * 1000;  // Within last year
            values.put("filterInstallDate", filterInstallDate);
            values.put("filterChangeInterval", 8760);  // Hours (1 year typical)

            // Motor Specifications (based on 355mm fan)
            values.put("ratedSpeed", 1800);  // RPM
            values.put("maxSpeed", 2000);    // RPM
            values.put("minSpeed", 500);     // RPM
            values.put("ratedAirflow", 2330); // m³/h
            values.put("ratedPower", 1500);   // W
            values.put("ratedVoltage", 400);  // V DC-Link
            values.put("ratedCurrent", 4.5);  // A

            // Efficiency
            values.put("efficiency", 0.52 + random.nextDouble() * 0.08);  // 52-60% typical for EC fans
            values.put("efficiencyClass", "IE4");  // ebmpapst EC motors typically IE4

            // System Configuration
            values.put("numberOfFans", 1);  // Single fan or part of FanGrid
            values.put("fanGridEnabled", false);
            values.put("autoAddressingEnabled", true);  // ebmpapst auto-addressing feature

            // Cleanroom Information
            values.put("cleanroomClass", "ISO " + (4 + random.nextInt(4)));  // ISO 4-7
            values.put("applicationArea", "Cleanroom FFU");
            values.put("mountingType", "Ceiling");

            // Sensor Configuration
            values.put("pressureSensorType", "0-10V Differential");
            values.put("pressureSensorRange", "0-500 Pa");
            values.put("temperatureSensorBuiltIn", true);
            values.put("temperatureSensorExternal", false);

            // Control Features
            values.put("pidControlEnabled", true);
            values.put("constantVolumeControl", true);
            values.put("constantPressureControl", false);

            // Maintenance
            values.put("maintenanceInterval", 8760);  // Hours
            values.put("nextMaintenanceDue", currentTime + 180L * 24 * 60 * 60 * 1000);  // 6 months from now

            // Warranty
            values.put("warrantyYears", 3);
            values.put("warrantyExpiry", installDate + 3L * 365 * 24 * 60 * 60 * 1000);

            payload = mapper.writeValueAsBytes(data);
        } catch (Exception e) {
            log.warn("Failed to generate ebmpapst FFU attributes", e);
            throw new RuntimeException(e);
        }
        return new Msg(payload);
    }
}
```

### Step 4: Create Device Profile JSON

Create file: `src/main/resources/device/profile/ebmpapst_ffu.json`

```json
{
  "name": "EBMPAPST_FFU",
  "description": "ebm-papst EC Fan Filter Unit profile with MODBUS-RTU monitoring",
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
    },
    "transportConfiguration": {
      "type": "DEFAULT"
    },
    "provisionConfiguration": {
      "type": "DISABLED",
      "provisionDeviceSecret": null
    },
    "alarms": [
      {
        "id": "ebmpapst-diff-pressure-alarm",
        "alarmType": "High Differential Pressure",
        "createRules": {
          "CRITICAL": {
            "condition": {
              "condition": [
                {
                  "key": {
                    "type": "TIME_SERIES",
                    "key": "differentialPressure"
                  },
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
            },
            "schedule": null,
            "alarmDetails": "HEPA filter differential pressure critical - filter replacement required",
            "dashboardId": null
          }
        },
        "clearRule": {
          "condition": {
            "condition": [
              {
                "key": {
                  "type": "TIME_SERIES",
                  "key": "differentialPressure"
                },
                "valueType": "NUMERIC",
                "value": null,
                "predicate": {
                  "type": "NUMERIC",
                  "operation": "LESS",
                  "value": {
                    "defaultValue": 350,
                    "userValue": null,
                    "dynamicValue": null
                  }
                }
              }
            ],
            "spec": {
              "type": "SIMPLE"
            }
          },
          "schedule": null,
          "alarmDetails": "Filter pressure returned to normal",
          "dashboardId": null
        },
        "propagate": true,
        "propagateRelationTypes": ["Contains"]
      },
      {
        "id": "ebmpapst-motor-temp-derating",
        "alarmType": "Motor Temperature Derating",
        "createRules": {
          "WARNING": {
            "condition": {
              "condition": [
                {
                  "key": {
                    "type": "TIME_SERIES",
                    "key": "motorTemperature"
                  },
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
            },
            "schedule": null,
            "alarmDetails": "Motor temperature in derating zone - performance reduced",
            "dashboardId": null
          }
        },
        "clearRule": {
          "condition": {
            "condition": [
              {
                "key": {
                  "type": "TIME_SERIES",
                  "key": "motorTemperature"
                },
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
          },
          "schedule": null,
          "alarmDetails": null,
          "dashboardId": null
        },
        "propagate": true,
        "propagateRelationTypes": ["Contains"]
      },
      {
        "id": "ebmpapst-motor-temp-critical",
        "alarmType": "Motor Temperature Critical",
        "createRules": {
          "CRITICAL": {
            "condition": {
              "condition": [
                {
                  "key": {
                    "type": "TIME_SERIES",
                    "key": "motorTemperature"
                  },
                  "valueType": "NUMERIC",
                  "value": null,
                  "predicate": {
                    "type": "NUMERIC",
                    "operation": "GREATER_OR_EQUAL",
                    "value": {
                      "defaultValue": 85,
                      "userValue": null,
                      "dynamicValue": null
                    }
                  }
                }
              ],
              "spec": {
                "type": "SIMPLE"
              }
            },
            "schedule": null,
            "alarmDetails": "Motor temperature critical - automatic shutdown imminent",
            "dashboardId": null
          }
        },
        "clearRule": {
          "condition": {
            "condition": [
              {
                "key": {
                  "type": "TIME_SERIES",
                  "key": "motorTemperature"
                },
                "valueType": "NUMERIC",
                "value": null,
                "predicate": {
                  "type": "NUMERIC",
                  "operation": "LESS",
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
          },
          "schedule": null,
          "alarmDetails": null,
          "dashboardId": null
        },
        "propagate": true,
        "propagateRelationTypes": ["Contains"]
      },
      {
        "id": "ebmpapst-modbus-error",
        "alarmType": "MODBUS Communication Error",
        "createRules": {
          "MAJOR": {
            "condition": {
              "condition": [
                {
                  "key": {
                    "type": "TIME_SERIES",
                    "key": "communicationErrors"
                  },
                  "valueType": "NUMERIC",
                  "value": null,
                  "predicate": {
                    "type": "NUMERIC",
                    "operation": "GREATER",
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
            },
            "schedule": null,
            "alarmDetails": "MODBUS-RTU communication errors detected - check RS485 connection",
            "dashboardId": null
          }
        },
        "clearRule": {
          "condition": {
            "condition": [
              {
                "key": {
                  "type": "TIME_SERIES",
                  "key": "communicationErrors"
                },
                "valueType": "NUMERIC",
                "value": null,
                "predicate": {
                  "type": "NUMERIC",
                  "operation": "LESS_OR_EQUAL",
                  "value": {
                    "defaultValue": 5,
                    "userValue": null,
                    "dynamicValue": null
                  }
                }
              }
            ],
            "spec": {
              "type": "SIMPLE"
            }
          },
          "schedule": null,
          "alarmDetails": null,
          "dashboardId": null
        },
        "propagate": false,
        "propagateRelationTypes": null
      }
    ]
  },
  "provisionDeviceKey": null,
  "firmwareId": null,
  "softwareId": null,
  "default": false
}
```

## Testing the ebmpapst FFU Implementation

### Test 1: Basic MODBUS Simulation Test

```bash
export REST_URL=http://127.0.0.1:8080
export MQTT_HOST=127.0.0.1
export REST_USERNAME=tenant@thingsboard.org
export REST_PASSWORD=tenant
export TEST_PAYLOAD_TYPE=EBMPAPST_FFU
export DEVICE_START_IDX=0
export DEVICE_END_IDX=10
export MESSAGES_PER_SECOND=10
export DURATION_IN_SECONDS=60
export DEVICE_CREATE_ON_START=true

mvn spring-boot:run
```

### Test 2: FanGrid Simulation (Multiple Fans)

```bash
# Simulate a cleanroom with 50 ebmpapst FFUs in a FanGrid configuration
export TEST_PAYLOAD_TYPE=EBMPAPST_FFU
export TEST_API=gateway  # Use gateway mode for centralized control
export GATEWAY_END_IDX=5
export DEVICE_END_IDX=50  # 50 fans across 5 gateways
export MESSAGES_PER_SECOND=50
export DURATION_IN_SECONDS=300
export DEVICE_CREATE_ON_START=true

mvn spring-boot:run
```

### Test 3: High Performance Test

```bash
# Test 500 FFUs with realistic MODBUS polling rate
export TEST_PAYLOAD_TYPE=EBMPAPST_FFU
export DEVICE_END_IDX=500
export MESSAGES_PER_SECOND=100  # 5 seconds poll interval per device
export DURATION_IN_SECONDS=3600  # 1 hour test
export ALARMS_PER_SECOND=2
export DEVICE_CREATE_ON_START=true

mvn spring-boot:run
```

## Sample Expected Telemetry Output

```json
{
  "ts": 1234567890000,
  "values": {
    "actualSpeed": 1547,
    "speedSetpoint": 1550,
    "calculatedAirflow": 1990,
    "dcLinkVoltage": 398.5,
    "dcLinkCurrent": 3.67,
    "powerConsumption": 1315,
    "differentialPressure": 287,
    "pressureSetpoint": 250,
    "motorTemperature": 52,
    "motorTempDerating": 75,
    "motorTempShutdown": 85,
    "ambientTemperature": 24,
    "operatingHours": 12456,
    "controlMode": 1,
    "operatingStatus": "RUNNING",
    "alarmCode": 0,
    "warningCode": 0,
    "speedActualPercent": 86,
    "speedSetpointPercent": 86,
    "modbusStatus": "OK",
    "communicationErrors": 0
  }
}
```

## Sample Expected Attributes Output

```json
{
  "fanModel": "R3G355-AS03-01",
  "manufacturer": "ebm-papst",
  "firmwareVersion": "ACE-4.3",
  "fanDiameter": 355,
  "serialNumber": "EBM-0547-234567",
  "modbusAddress": 15,
  "modbusBaudRate": 19200,
  "modbusProtocol": "RTU",
  "communicationInterface": "RS485 MODBUS-RTU",
  "analogControlSupport": true,
  "iotGatewayProtocols": "MQTT, OPC-UA, BACnet IP",
  "filterType": "HEPA H14",
  "ratedSpeed": 1800,
  "ratedAirflow": 2330,
  "ratedPower": 1500,
  "efficiency": 0.56,
  "efficiencyClass": "IE4",
  "autoAddressingEnabled": true,
  "cleanroomClass": "ISO 5",
  "pidControlEnabled": true
}
```

## Verification Checklist

- [ ] All telemetry fields match ebmpapst MODBUS register specifications
- [ ] DC-Link voltage and current values are realistic
- [ ] Speed setpoint and actual speed show realistic control behavior
- [ ] Differential pressure reflects filter loading correctly
- [ ] Motor temperature correlates with load
- [ ] Operating hours counter increments properly
- [ ] Alarm codes trigger at correct thresholds
- [ ] MODBUS communication status is monitored
- [ ] Device attributes match ebmpapst product specifications
- [ ] Fan model numbers are valid ebmpapst models

## Key Differences from Generic FFU

| Parameter | Generic FFU | ebmpapst FFU |
|-----------|------------|--------------|
| Speed Reporting | RPM only | RPM + Setpoint + % |
| Pressure | filterPressure | differentialPressure (external sensor) |
| Electrical | powerConsumption only | dcLinkVoltage, dcLinkCurrent, power |
| Airflow | Direct reading | Calculated from speed + curve |
| Control | Simple on/off | MODBUS-RTU + 0-10V analog |
| Temperature | Motor temp only | Motor + ambient + derating thresholds |
| Communication | Basic | MODBUS + IoT gateway protocols |
| Status | Running/Stopped | Multiple states + alarm/warning codes |

## Performance Benchmarks

| Devices | Messages/sec | Expected CPU | Expected RAM | Notes |
|---------|--------------|--------------|--------------|-------|
| 50      | 50           | 5-10%        | 2 GB         | Single cleanroom |
| 200     | 100          | 15-25%       | 4 GB         | Small facility |
| 500     | 100          | 30-40%       | 6 GB         | Medium facility |
| 1000    | 200          | 50-70%       | 12 GB        | Large facility |

*Based on typical MODBUS polling interval of 5-10 seconds per device*

## References

- [ebm-papst FFU/EFU Product Page](https://www.ebmpapst.com/de/en/industries/air-conditioning/ffu-efu.html)
- [ebm-papst MODBUS Parameter Specifications](https://www.ebmpapst.com/us/en/support/downloads/modbus-ebmbus.html)
- [ebm-papst FanGrid Solutions](https://mag.ebmpapst.com/en/industries/refrigeration-ventilation/fangrid-solutions-for-high-air-performance_14339/)
- [ebm-papst EC Centrifugal Fans for FFU](https://mag.ebmpapst.com/en/industries/refrigeration-ventilation/ec-centrifugal-fans-for-fan-filter-units_8371/)
