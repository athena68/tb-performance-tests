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
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.thingsboard.tools.service.config.ConfigurationLoader;
import org.thingsboard.tools.service.msg.BaseMessageGenerator;
import org.thingsboard.tools.service.msg.MessageGenerator;
import org.thingsboard.tools.service.msg.Msg;

import java.util.Map;

@Slf4j
@Service(value = "randomAttributesGenerator")
@ConditionalOnProperty(prefix = "test", value = "payloadType", havingValue = "EBMPAPST_FFU")
public class EbmpapstFfuAttributesGenerator extends BaseMessageGenerator implements MessageGenerator {

    @Autowired(required = false)
    private ConfigurationLoader configLoader;

    @Value("${config.useYaml:true}")
    private boolean useYamlConfig;

    // ebmpapst fan models (actual product lines) - FALLBACK ONLY
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

            // Try to load from YAML configuration first
            if (useYamlConfig && configLoader != null) {
                try {
                    int deviceIndex = extractDeviceIndex(deviceName);
                    Map<String, Object> attributes = configLoader.loadDeviceAttributes("ebmpapstffu", deviceIndex);

                    if (!attributes.isEmpty()) {
                        log.debug("Loaded {} attributes from YAML config for device {}", attributes.size(), deviceName);
                        populateValuesFromConfig(values, attributes);
                    } else {
                        log.warn("No attributes loaded from config for {}, using hardcoded fallback", deviceName);
                        populateValuesHardcoded(values);
                    }
                } catch (Exception e) {
                    log.warn("Failed to load YAML config for {}, using hardcoded fallback: {}", deviceName, e.getMessage());
                    populateValuesHardcoded(values);
                }
            } else {
                // Use hardcoded values if YAML is disabled
                log.debug("YAML config disabled, using hardcoded values for device {}", deviceName);
                populateValuesHardcoded(values);
            }

            payload = mapper.writeValueAsBytes(data);
        } catch (Exception e) {
            log.warn("Failed to generate ebmpapst FFU attributes", e);
            throw new RuntimeException(e);
        }
        return new Msg(payload);
    }

    /**
     * Extract device index from device name (e.g., DW00000042 -> 42)
     */
    private int extractDeviceIndex(String deviceName) {
        try {
            // Extract numeric part from device name
            String numericPart = deviceName.replaceAll("[^0-9]", "");
            return Integer.parseInt(numericPart);
        } catch (Exception e) {
            log.warn("Failed to extract device index from {}, using 0", deviceName);
            return 0;
        }
    }

    /**
     * Populate values from YAML configuration
     */
    private void populateValuesFromConfig(ObjectNode values, Map<String, Object> attributes) {
        for (Map.Entry<String, Object> entry : attributes.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();

            if (value instanceof String) {
                values.put(key, (String) value);
            } else if (value instanceof Integer) {
                values.put(key, (Integer) value);
            } else if (value instanceof Long) {
                values.put(key, (Long) value);
            } else if (value instanceof Double) {
                values.put(key, (Double) value);
            } else if (value instanceof Boolean) {
                values.put(key, (Boolean) value);
            } else if (value != null) {
                values.put(key, value.toString());
            }
        }
    }

    /**
     * Populate values using hardcoded logic (FALLBACK)
     */
    private void populateValuesHardcoded(ObjectNode values) {
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
        values.put("ratedPower", 1500);   // W (maximum rated power)
        values.put("nominalPower", 1050 + random.nextInt(150));  // W (typical operating power at 70-80% load, 1050-1200W)
        values.put("ratedVoltage", 400);  // V DC-Link
        values.put("ratedCurrent", 4.5);  // A

        // Efficiency
        values.put("efficiency", Math.round((0.52 + random.nextDouble() * 0.08) * 100.0) / 100.0);  // 52-60% typical for EC fans
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
    }
}
