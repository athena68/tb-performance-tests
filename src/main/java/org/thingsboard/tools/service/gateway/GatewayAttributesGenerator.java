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
package org.thingsboard.tools.service.gateway;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.thingsboard.tools.service.config.ConfigurationLoader;

import java.util.Map;
import java.util.Random;

/**
 * Generates gateway client-scope attributes from gateway.yaml configuration
 */
@Slf4j
@Component
public class GatewayAttributesGenerator {

    @Autowired(required = false)
    private ConfigurationLoader configLoader;

    @Value("${config.useYaml:true}")
    private boolean useYamlConfig;

    private final ObjectMapper mapper = new ObjectMapper();
    private final Random random = new Random();

    // Fallback values if YAML config is not available
    private static final String[] GW_MODELS = {"TB-GW-100", "TB-GW-200", "TB-GW-300"};

    /**
     * Generate gateway attributes for a specific gateway
     * @param gatewayName The gateway name (e.g., "GW1", "GW2")
     * @return JSON byte array with gateway attributes
     */
    public byte[] generateAttributes(String gatewayName) {
        try {
            ObjectNode attributes = mapper.createObjectNode();

            // Try to load from YAML configuration first
            if (useYamlConfig && configLoader != null) {
                try {
                    int gatewayIndex = extractGatewayIndex(gatewayName);
                    Map<String, Object> config = configLoader.loadDeviceAttributes("gateway", gatewayIndex);

                    if (!config.isEmpty()) {
                        log.debug("Loaded {} attributes from YAML config for gateway {}", config.size(), gatewayName);
                        populateFromConfig(attributes, config);
                    } else {
                        log.warn("No attributes loaded from config for {}, using hardcoded fallback", gatewayName);
                        populateHardcoded(attributes, gatewayName);
                    }
                } catch (Exception e) {
                    log.warn("Failed to load YAML config for {}, using hardcoded fallback: {}", gatewayName, e.getMessage());
                    populateHardcoded(attributes, gatewayName);
                }
            } else {
                // Use hardcoded values if YAML is disabled
                log.debug("YAML config disabled, using hardcoded values for gateway {}", gatewayName);
                populateHardcoded(attributes, gatewayName);
            }

            return mapper.writeValueAsBytes(attributes);
        } catch (Exception e) {
            log.error("Failed to generate gateway attributes for {}", gatewayName, e);
            return new byte[0];
        }
    }

    /**
     * Extract gateway index from gateway name (e.g., GW1 -> 1, GW2 -> 2)
     */
    private int extractGatewayIndex(String gatewayName) {
        try {
            String numericPart = gatewayName.replaceAll("[^0-9]", "");
            return Integer.parseInt(numericPart);
        } catch (Exception e) {
            log.warn("Failed to extract gateway index from {}, using 0", gatewayName);
            return 0;
        }
    }

    /**
     * Populate attributes from YAML configuration
     */
    private void populateFromConfig(ObjectNode attributes, Map<String, Object> config) {
        for (Map.Entry<String, Object> entry : config.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();

            if (value instanceof String) {
                attributes.put(key, (String) value);
            } else if (value instanceof Integer) {
                attributes.put(key, (Integer) value);
            } else if (value instanceof Long) {
                attributes.put(key, (Long) value);
            } else if (value instanceof Double) {
                attributes.put(key, (Double) value);
            } else if (value instanceof Boolean) {
                attributes.put(key, (Boolean) value);
            } else if (value != null) {
                attributes.put(key, value.toString());
            }
        }
    }

    /**
     * Populate hardcoded fallback values
     */
    private void populateHardcoded(ObjectNode attributes, String gatewayName) {
        // Device Information
        attributes.put("manufacturer", "ThingsBoard");
        attributes.put("gw_model", GW_MODELS[random.nextInt(GW_MODELS.length)]);
        attributes.put("firmware_version", "GW-" + (2 + random.nextInt(2)) + "." + random.nextInt(10));
        attributes.put("serial_number", "GW-" + String.format("%04d", random.nextInt(10000)) +
                                       "-" + String.format("%06d", random.nextInt(1000000)));

        // Network Configuration
        attributes.put("mac_address", "DC:A6:32:" +
                                     String.format("%02X", random.nextInt(256)) + ":" +
                                     String.format("%02X", random.nextInt(256)) + ":" +
                                     String.format("%02X", random.nextInt(256)));
        attributes.put("ip_address", "192.168.1." + (100 + random.nextInt(101)));
        attributes.put("protocol", "MQTT");
        attributes.put("port", 1883);

        // Communication
        attributes.put("max_devices", 100);
        attributes.put("supported_device_types", "ebmpapst_ffu,smart_meter,smart_tracker");

        // Installation Data
        long currentTime = System.currentTimeMillis();
        long installDate = currentTime - (long)random.nextInt(365) * 24 * 60 * 60 * 1000;  // Within last year
        attributes.put("installation_date", installDate);
        attributes.put("commissioning_date", installDate + 24 * 60 * 60 * 1000L);  // 1 day after install
    }
}
