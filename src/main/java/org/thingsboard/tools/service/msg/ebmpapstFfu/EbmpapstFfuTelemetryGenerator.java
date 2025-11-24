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
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.thingsboard.tools.service.config.ConfigurationLoader;
import org.thingsboard.tools.service.msg.BaseMessageGenerator;
import org.thingsboard.tools.service.msg.MessageGenerator;
import org.thingsboard.tools.service.msg.Msg;

import jakarta.annotation.PostConstruct;
import java.util.*;

@Slf4j
@Service(value = "randomTelemetryGenerator")
@ConditionalOnProperty(prefix = "test", value = "payloadType", havingValue = "EBMPAPST_FFU")
public class EbmpapstFfuTelemetryGenerator extends BaseMessageGenerator implements MessageGenerator {

    @Autowired(required = false)
    private ConfigurationLoader configLoader;

    @Value("${config.useYaml:true}")
    private boolean useYamlConfig;

    // ebmpapst EC motor specifications - FALLBACK VALUES
    static int MIN_SPEED = 500;                    // Minimum RPM
    static int MAX_SPEED = 2000;                   // Maximum RPM for typical FFU
    static int RATED_SPEED = 1800;                 // Rated speed

    // Alarm thresholds based on ebmpapst specifications - FALLBACK VALUES
    static int DIFFERENTIAL_PRESSURE_ALARM = 450;  // High filter pressure (Pa)
    static int MOTOR_TEMP_DERATING = 75;           // Temperature derating starts (°C)
    static int MOTOR_TEMP_SHUTDOWN = 85;           // Critical shutdown temperature (°C)

    // Electrical specifications for 355mm fan - FALLBACK VALUES
    static double RATED_VOLTAGE = 400.0;           // DC-Link voltage (V)
    static double RATED_CURRENT = 4.5;             // DC-Link current at full load (A)
    static int RATED_POWER = 1500;                 // Rated power (W)

    // Airflow calculations (approximation for 355mm fan) - FALLBACK VALUES
    static int MAX_AIRFLOW = 2330;                 // m³/h at rated speed

    // Device status configuration - simulates real-world scenarios - FALLBACK VALUES
    private static String[] ALARM_DEVICES = {
        "DW00000015",  // High differential pressure (filter clogged)
        "DW00000032",  // Motor overheating
        "DW00000047"   // High differential pressure (filter clogged)
    };

    private static String[] STOPPED_DEVICES = {
        "DW00000008",  // Manually stopped for maintenance
        "DW00000023",  // Stopped - awaiting repair
        "DW00000041"   // Stopped - scheduled maintenance
    };

    // Vibration warning devices - show elevated vibration but not critical
    private static String[] VIBRATION_WARNING_DEVICES = {
        "DW00000022",
        "DW00000038",
        "DW00000051"
    };

    // OFFLINE DEVICES - These should NOT send telemetry at all!
    // ThingsBoard will automatically set their 'active' attribute to false
    // when no telemetry is received. Do NOT generate telemetry for these devices.
    public static String[] OFFLINE_DEVICES = {
        "DW00000012",  // Communication lost
        "DW00000029",  // Network timeout
        "DW00000056"   // Disconnected
    };

    @PostConstruct
    public void init() {
        if (useYamlConfig && configLoader != null) {
            try {
                loadConfigurationFromYaml();
            } catch (Exception e) {
                log.warn("Failed to load telemetry config from YAML, using hardcoded values: {}", e.getMessage());
            }
        } else {
            log.info("YAML config disabled, using hardcoded telemetry constants");
        }
    }

    /**
     * Load telemetry configuration constants from YAML
     */
    private void loadConfigurationFromYaml() {
        try {
            Map<String, Object> config = configLoader.loadTelemetryConfig("ebmpapstffu");

            if (config.isEmpty()) {
                log.warn("No telemetry config found, using hardcoded values");
                return;
            }

            // Load data points configuration
            Map<String, Object> dataPoints = (Map<String, Object>) config.get("data_points");
            if (dataPoints != null) {
                // Load RPM configuration
                Map<String, Object> rpmConfig = (Map<String, Object>) dataPoints.get("RPM");
                if (rpmConfig != null) {
                    if (rpmConfig.containsKey("min")) {
                        MIN_SPEED = ((Number) rpmConfig.get("min")).intValue();
                    }
                    if (rpmConfig.containsKey("max")) {
                        MAX_SPEED = ((Number) rpmConfig.get("max")).intValue();
                    }
                    if (rpmConfig.containsKey("default")) {
                        RATED_SPEED = ((Number) rpmConfig.get("default")).intValue();
                    }
                }

                // Load airflow configuration
                Map<String, Object> airflowConfig = (Map<String, Object>) dataPoints.get("airSpeed");
                if (airflowConfig != null && airflowConfig.containsKey("default")) {
                    MAX_AIRFLOW = ((Number) airflowConfig.get("default")).intValue();
                }
            }

            // Load special device configurations
            Map<String, Object> specialDevices = (Map<String, Object>) config.get("special_devices");
            if (specialDevices != null) {
                // Load alarm devices
                Map<String, Object> alarmDevicesConfig = (Map<String, Object>) specialDevices.get("alarm_devices");
                if (alarmDevicesConfig != null && alarmDevicesConfig.containsKey("devices")) {
                    List<String> alarmList = (List<String>) alarmDevicesConfig.get("devices");
                    ALARM_DEVICES = alarmList.toArray(new String[0]);
                }

                // Load stopped devices
                Map<String, Object> stoppedDevicesConfig = (Map<String, Object>) specialDevices.get("stopped_devices");
                if (stoppedDevicesConfig != null && stoppedDevicesConfig.containsKey("devices")) {
                    List<String> stoppedList = (List<String>) stoppedDevicesConfig.get("devices");
                    STOPPED_DEVICES = stoppedList.toArray(new String[0]);
                }
            }

            log.info("Successfully loaded telemetry configuration from YAML:");
            log.info("  Speed range: {} - {} RPM (rated: {})", MIN_SPEED, MAX_SPEED, RATED_SPEED);
            log.info("  Max airflow: {} m³/h", MAX_AIRFLOW);
            log.info("  Alarm devices: {}", Arrays.toString(ALARM_DEVICES));
            log.info("  Stopped devices: {}", Arrays.toString(STOPPED_DEVICES));

        } catch (Exception e) {
            log.error("Failed to load telemetry configuration from YAML", e);
            throw e;
        }
    }

    // Get persistent device seed for consistent per-device values
    private int getDeviceSeed(String deviceName) {
        return Math.abs(deviceName.hashCode());
    }

    // Check if device has alarm
    private boolean isAlarmDevice(String deviceName) {
        for (String device : ALARM_DEVICES) {
            if (deviceName.equals(device)) {
                return true;
            }
        }
        return false;
    }

    // Check if device is stopped
    private boolean isStoppedDevice(String deviceName) {
        for (String device : STOPPED_DEVICES) {
            if (deviceName.equals(device)) {
                return true;
            }
        }
        return false;
    }

    // Check if device has vibration warning
    private boolean isVibrationWarningDevice(String deviceName) {
        for (String device : VIBRATION_WARNING_DEVICES) {
            if (deviceName.equals(device)) {
                return true;
            }
        }
        return false;
    }

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

            // Get persistent seed for this device
            int deviceSeed = getDeviceSeed(deviceName);
            java.util.Random deviceRandom = new java.util.Random(deviceSeed);

            // Determine device status
            boolean isAlarm = isAlarmDevice(deviceName);
            boolean isStopped = isStoppedDevice(deviceName);
            boolean isVibrationWarning = isVibrationWarningDevice(deviceName);

            // Core Motor Parameters
            // Speed Setpoint - PERSISTENT per device (changes rarely, not every message)
            int speedSetpoint = 1300 + (deviceSeed % 500);  // Each device has its own setpoint (1300-1800 RPM)

            // Actual Speed - depends on device status
            int actualSpeed;
            if (isStopped) {
                actualSpeed = 0;  // No speed when stopped
            } else {
                actualSpeed = speedSetpoint + random.nextInt(20) - 10;  // ±10 RPM variation for running devices
            }

            // YAML-compliant key: RPM (not actualSpeed)
            values.put("RPM", actualSpeed);
            values.put("speedSetpoint", speedSetpoint);  // This stays constant for each device

            // Calculate airflow based on fan curve (simplified linear approximation)
            double speedRatio = (double) actualSpeed / RATED_SPEED;
            int calculatedAirflow = (int) (MAX_AIRFLOW * speedRatio);
            // YAML-compliant key: airSpeed (not calculatedAirflow)
            values.put("airSpeed", calculatedAirflow);

            // DC-Link Voltage - relatively stable around rated voltage
            double dcLinkVoltage = RATED_VOLTAGE + (random.nextDouble() * 20 - 10);  // ±10V variation
            values.put("dcLinkVoltage", Math.round(dcLinkVoltage * 10.0) / 10.0);

            // DC-Link Current - correlates with speed/load
            double loadFactor = speedRatio * (0.7 + random.nextDouble() * 0.3);  // 70-100% load
            double dcLinkCurrent = RATED_CURRENT * loadFactor;
            values.put("dcLinkCurrent", Math.round(dcLinkCurrent * 100.0) / 100.0);

            // Power Consumption - P = V * I * efficiency
            int powerConsumption = (int) (dcLinkVoltage * dcLinkCurrent * 0.9);  // 90% efficiency
            // YAML-compliant key: energy_consumption (not powerConsumption)
            values.put("energy_consumption", powerConsumption);

            // Ambient Temperature - PERSISTENT per device (room-specific)
            int ambientTemp = 22 + (deviceSeed % 8);  // Each device has persistent ambient (22-30°C)
            values.put("ambientTemperature", ambientTemp);

            // Differential Pressure across HEPA filter
            int differentialPressure;
            if (isStopped) {
                // Stopped devices: pressure drops to zero or ambient
                differentialPressure = random.nextInt(20);  // 0-20 Pa (no airflow)
            } else if (isAlarm && (deviceName.equals("DW00000015") || deviceName.equals("DW00000047"))) {
                // Fixed high pressure for clogged filter devices
                differentialPressure = DIFFERENTIAL_PRESSURE_ALARM + random.nextInt(50);  // 450-500 Pa
            } else {
                // Normal operation: pressure increases with airflow and gradual filter clogging
                int basePressure = (int) (100 + (speedRatio * 150));  // 100-250 Pa for clean filter
                int filterClogging = (deviceSeed % 80);  // Persistent filter clogging per device (0-80 Pa)
                differentialPressure = basePressure + filterClogging + random.nextInt(20);  // Small variation
            }
            values.put("differentialPressure", differentialPressure);
            values.put("pressureSetpoint", 250);  // Target differential pressure (constant)

            // Motor Temperature - correlates with load and ambient
            int motorTemperature;
            if (isStopped) {
                // Recently stopped devices: temperature cooling down
                motorTemperature = ambientTemp + random.nextInt(10);  // 0-10°C above ambient
            } else if (isAlarm && deviceName.equals("DW00000032")) {
                // Fixed overheating for motor temp fault device
                motorTemperature = MOTOR_TEMP_DERATING + random.nextInt(10);  // 75-85°C
            } else {
                // Normal operation: temperature rises with load
                int motorTempRise = (int) (loadFactor * 25);  // Temperature rise above ambient
                motorTemperature = ambientTemp + motorTempRise + random.nextInt(5);  // Small variation
            }
            values.put("motorTemperature", motorTemperature);
            values.put("motorTempDerating", MOTOR_TEMP_DERATING);
            values.put("motorTempShutdown", MOTOR_TEMP_SHUTDOWN);

            // Operating Hours - PERSISTENT cumulative counter (slowly incrementing)
            // Use device seed as base hours, increment by a few hours each time
            int baseHours = (deviceSeed % 30000);  // Each device has different base hours (0-30000)
            int operatingHours = baseHours + (int)((System.currentTimeMillis() / 3600000) % 20000);  // Slowly incrementing
            values.put("operatingHours", operatingHours);

            // Control Mode: 1=MODBUS (PERSISTENT - doesn't change)
            values.put("controlMode", 1);  // MODBUS control

            // Operating Status - based on device state
            // NOTE: OFFLINE status is NOT sent in telemetry!
            // Offline devices simply stop sending telemetry, and ThingsBoard
            // will automatically set their 'active' attribute to false.
            String operatingStatus;
            int alarmCode = 0;
            int warningCode = 0;

            if (isStopped) {
                // Stopped devices - manually stopped for maintenance
                operatingStatus = "STOPPED";
            } else if (isAlarm) {
                // Fixed alarm devices - always show alarms based on their specific issue
                if (deviceName.equals("DW00000032")) {
                    // Motor overheating device
                    operatingStatus = motorTemperature >= MOTOR_TEMP_SHUTDOWN ? "FAULT" : "ALARM";
                    alarmCode = 101;  // Motor overheat alarm
                } else if (deviceName.equals("DW00000015") || deviceName.equals("DW00000047")) {
                    // High differential pressure devices (clogged filters)
                    operatingStatus = "ALARM";
                    alarmCode = 201;  // High differential pressure
                } else {
                    operatingStatus = "RUNNING";
                }
            } else {
                // Normal devices - operating properly
                operatingStatus = "RUNNING";

                // Check for warnings even in normal operation
                if (differentialPressure > 350) {
                    warningCode = 302;  // Filter maintenance warning
                }
                if (motorTemperature > 65) {
                    warningCode = 301;  // High temperature warning
                }
            }

            // YAML-compliant keys: operating_status, error_code, warning_code
            values.put("operating_status", operatingStatus);
            values.put("error_code", alarmCode);
            values.put("warning_code", warningCode);

            // Vibration telemetry (ISO 10816 standard for industrial fans)
            double vibration5thHarmonic;
            double vibrationRMS;

            if (isStopped) {
                // Stopped devices: no vibration
                vibration5thHarmonic = 0.0;
                vibrationRMS = 0.0;
            } else if (isAlarm) {
                // Alarm devices: high vibration (critical levels)
                vibration5thHarmonic = 6.0 + random.nextDouble() * 1.5;  // 6.0-7.5 mm/s (near critical)
                vibrationRMS = 7.5 + random.nextDouble() * 3.0;          // 7.5-10.5 mm/s (above alarm threshold)
            } else if (isVibrationWarning) {
                // Vibration warning devices: elevated but not critical
                vibration5thHarmonic = 3.8 + random.nextDouble() * 0.8;  // 3.8-4.6 mm/s (near alarm threshold)
                vibrationRMS = 6.2 + random.nextDouble() * 1.2;          // 6.2-7.4 mm/s (near alarm threshold)
                if (warningCode == 0) {
                    warningCode = 402;  // High vibration warning
                }
            } else {
                // Normal devices: vibration correlates with RPM and load factor
                // Base vibration increases with speed
                double speedFactor = speedRatio;  // 0.0 to 1.0
                double vibrationLoadFactor = loadFactor;  // 0.7 to 1.0

                // 5th harmonic vibration: indicates blade/fan balance issues
                // Normal range: 0.1-3.0 mm/s, increases with speed
                double base5thHarmonic = 0.8 + (speedFactor * 1.5);  // 0.8-2.3 mm/s base
                vibration5thHarmonic = base5thHarmonic * vibrationLoadFactor + (random.nextDouble() * 0.3 - 0.15);
                vibration5thHarmonic = Math.max(0.1, Math.min(3.5, vibration5thHarmonic));  // Clamp 0.1-3.5 mm/s

                // RMS vibration: overall condition indicator
                // Normal range: 0.5-5.0 mm/s, increases with speed and load
                double baseRMS = 1.5 + (speedFactor * 2.0);  // 1.5-3.5 mm/s base
                vibrationRMS = baseRMS * vibrationLoadFactor + (random.nextDouble() * 0.5 - 0.25);
                vibrationRMS = Math.max(0.5, Math.min(5.5, vibrationRMS));  // Clamp 0.5-5.5 mm/s
            }

            // Round to 2 decimal places and add to telemetry
            values.put("Vibration_5th_harmonic_sum", Math.round(vibration5thHarmonic * 100.0) / 100.0);
            values.put("Vibration_RMS_sum", Math.round(vibrationRMS * 100.0) / 100.0);

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
