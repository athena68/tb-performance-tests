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
package org.thingsboard.tools.service.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Configuration Loader for YAML-based device and telemetry configurations
 * Provides centralized configuration management for performance tests
 */
@Slf4j
@Service
public class ConfigurationLoader {

    @Value("${config.path:config}")
    private String configPath;

    private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory());
    private final Map<String, Map<String, Object>> configCache = new ConcurrentHashMap<>();
    private final Random random = new Random();

    @PostConstruct
    public void init() {
        log.info("ConfigurationLoader initialized with config path: {}", configPath);
    }

    /**
     * Load device attributes from YAML configuration
     * @param deviceType The device type (e.g., "ebmpapstffu")
     * @param deviceIndex Device index for randomization seed
     * @return Map of attribute key-value pairs
     */
    public Map<String, Object> loadDeviceAttributes(String deviceType, int deviceIndex) {
        String cacheKey = deviceType + "_" + deviceIndex;

        return configCache.computeIfAbsent(cacheKey, k -> {
            try {
                String filePath = configPath + "/attributes/devices/" + deviceType + ".yaml";
                File configFile = new File(filePath);

                if (!configFile.exists()) {
                    log.warn("Configuration file not found: {}. Using hardcoded fallback.", filePath);
                    return new HashMap<>();
                }

                Map<String, Object> config = yamlMapper.readValue(configFile, Map.class);
                return processDeviceConfig(config, deviceIndex);
            } catch (Exception e) {
                log.error("Failed to load config for {}: {}", deviceType, e.getMessage(), e);
                return new HashMap<>();
            }
        });
    }

    /**
     * Load telemetry configuration from YAML
     * @param deviceType The device type
     * @return Telemetry configuration map
     */
    public Map<String, Object> loadTelemetryConfig(String deviceType) {
        try {
            String filePath = configPath + "/telemetry/devices/" + deviceType + ".yaml";
            File configFile = new File(filePath);

            if (!configFile.exists()) {
                log.warn("Telemetry config file not found: {}", filePath);
                return new HashMap<>();
            }

            return yamlMapper.readValue(configFile, Map.class);
        } catch (Exception e) {
            log.error("Failed to load telemetry config for {}: {}", deviceType, e.getMessage(), e);
            return new HashMap<>();
        }
    }

    /**
     * Process device configuration, flattening nested structures
     * @param config Raw configuration map
     * @param deviceIndex Device index for seeded randomization
     * @return Flat map of attributes
     */
    private Map<String, Object> processDeviceConfig(Map<String, Object> config, int deviceIndex) {
        Map<String, Object> result = new HashMap<>();
        Random deviceRandom = new Random(deviceIndex); // Seed-based random for consistent device attributes

        for (Map.Entry<String, Object> entry : config.entrySet()) {
            String sectionName = entry.getKey();
            Object sectionValue = entry.getValue();

            if (sectionValue instanceof Map) {
                Map<String, Object> section = (Map<String, Object>) sectionValue;
                processSection(sectionName, section, result, deviceIndex, deviceRandom);
            }
        }

        return result;
    }

    /**
     * Process a configuration section recursively
     */
    private void processSection(String sectionName, Map<String, Object> section,
                                Map<String, Object> result, int deviceIndex, Random deviceRandom) {

        // Special handling for position section (calculate xPos, yPos from grid layout)
        if ("position".equals(sectionName)) {
            processPositionSection(section, result, deviceIndex);
            return;
        }

        for (Map.Entry<String, Object> entry : section.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();

            Object processedValue = processValue(key, value, deviceIndex, deviceRandom, result);

            // Use camelCase attribute names (e.g., device_info.fan_model -> fanModel)
            String attributeKey = toCamelCase(key);

            if (processedValue != null) {
                result.put(attributeKey, processedValue);
            }
        }
    }

    /**
     * Process position section to calculate xPos and yPos from grid layout
     */
    private void processPositionSection(Map<String, Object> section, Map<String, Object> result, int deviceIndex) {
        try {
            String layout = (String) section.get("layout");

            if ("grid".equals(layout)) {
                int gridColumns = ((Number) section.get("grid_columns")).intValue();
                int gridRows = ((Number) section.get("grid_rows")).intValue();
                double startX = ((Number) section.get("start_x")).doubleValue();
                double startY = ((Number) section.get("start_y")).doubleValue();
                double spacingX = ((Number) section.get("spacing_x")).doubleValue();
                double spacingY = ((Number) section.get("spacing_y")).doubleValue();

                // Calculate grid position
                int col = deviceIndex % gridColumns;
                int row = deviceIndex / gridColumns;

                double xPos = startX + col * spacingX;
                double yPos = startY + row * spacingY;

                // Round to 2 decimal places
                result.put("xPos", Math.round(xPos * 100.0) / 100.0);
                result.put("yPos", Math.round(yPos * 100.0) / 100.0);

                log.debug("Device {} positioned at ({}, {}) [col={}, row={}]",
                         deviceIndex, xPos, yPos, col, row);
            }
        } catch (Exception e) {
            log.warn("Failed to process position section: {}", e.getMessage());
        }
    }

    /**
     * Process individual configuration values
     */
    private Object processValue(String key, Object value, int deviceIndex, Random deviceRandom,
                               Map<String, Object> context) {
        if (value == null) {
            return null;
        }

        // Handle lists - select random or by index
        if (value instanceof List) {
            List<?> list = (List<?>) value;
            if (list.isEmpty()) {
                return null;
            }
            // Use device index to consistently select from list
            Object selected = list.get(deviceIndex % list.size());

            // Special handling for fan_model to extract diameter
            if ("fan_model".equals(key) && selected instanceof String) {
                String model = (String) selected;
                context.put("fanModel", model);
                // Extract diameter (e.g., R3G355 -> 355)
                try {
                    String diameterStr = model.substring(3, 6);
                    context.put("fanDiameter", Integer.parseInt(diameterStr));
                } catch (Exception e) {
                    log.warn("Failed to extract diameter from model: {}", model);
                }
            }

            return selected;
        }

        // Handle maps with special keys
        if (value instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) value;

            // Handle range specification
            if (map.containsKey("min") && map.containsKey("max")) {
                Object min = map.get("min");
                Object max = map.get("max");

                if (min instanceof Number && max instanceof Number) {
                    if (min instanceof Double || max instanceof Double) {
                        double minVal = ((Number) min).doubleValue();
                        double maxVal = ((Number) max).doubleValue();
                        double randomValue = minVal + deviceRandom.nextDouble() * (maxVal - minVal);
                        return Math.round(randomValue * 100.0) / 100.0;
                    } else {
                        int minVal = ((Number) min).intValue();
                        int maxVal = ((Number) max).intValue();
                        return minVal + deviceRandom.nextInt(maxVal - minVal + 1);
                    }
                }
            }

            // Handle format templates
            if (map.containsKey("format")) {
                String format = (String) map.get("format");
                return processTemplate(format, deviceIndex, deviceRandom, map);
            }

            // Handle special date/time types
            if (map.containsKey("type")) {
                String type = (String) map.get("type");
                return processDateType(type, map, deviceRandom, context);
            }

            // Handle values array (for random selection)
            if (map.containsKey("values")) {
                List<?> values = (List<?>) map.get("values");
                return values.get(deviceIndex % values.size());
            }
        }

        // Return as-is for simple values
        return value;
    }

    /**
     * Process template strings with placeholders
     * @param template The template string with placeholders
     * @param deviceIndex The device index
     * @param deviceRandom Random generator for this device
     * @param context Context map containing values like version, patch, macPrefix
     */
    private String processTemplate(String template, int deviceIndex, Random deviceRandom, Map<String, Object> context) {
        String result = template;

        // Replace {{random:min:max}} patterns (supports both decimal and hex)
        while (result.contains("{{random:")) {
            int startIdx = result.indexOf("{{random:");
            int endIdx = result.indexOf("}}", startIdx);
            if (endIdx == -1) break;

            String rangeSpec = result.substring(startIdx + 9, endIdx);
            String[] parts = rangeSpec.split(":");

            if (parts.length == 2) {
                try {
                    String minStr = parts[0].trim();
                    String maxStr = parts[1].trim();

                    // Check if hex format (contains A-F)
                    boolean isHex = minStr.matches(".*[A-Fa-f].*") || maxStr.matches(".*[A-Fa-f].*");

                    if (isHex) {
                        // Parse as hex
                        int min = Integer.parseInt(minStr, 16);
                        int max = Integer.parseInt(maxStr, 16);
                        int randomValue = min + deviceRandom.nextInt(max - min + 1);
                        // Format as hex with uppercase, 2 digits
                        String hexValue = String.format("%02X", randomValue);
                        result = result.substring(0, startIdx) + hexValue + result.substring(endIdx + 2);
                    } else {
                        // Parse as decimal
                        int min = Integer.parseInt(minStr);
                        int max = Integer.parseInt(maxStr);
                        int randomValue = min + deviceRandom.nextInt(max - min + 1);
                        result = result.substring(0, startIdx) + randomValue + result.substring(endIdx + 2);
                    }
                } catch (NumberFormatException e) {
                    log.warn("Invalid random range: {}", rangeSpec);
                    break;
                }
            } else {
                break;
            }
        }

        // Replace context values (version, patch, macPrefix, etc.)
        for (Map.Entry<String, Object> entry : context.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();

            // Skip format key itself
            if ("format".equals(key)) {
                continue;
            }

            String placeholder = "{{" + key + "}}";
            if (result.contains(placeholder)) {
                // Process the value if it's a range
                String replacementValue;
                if (value instanceof Map) {
                    Map<String, Object> valueMap = (Map<String, Object>) value;
                    if (valueMap.containsKey("min") && valueMap.containsKey("max")) {
                        int min = ((Number) valueMap.get("min")).intValue();
                        int max = ((Number) valueMap.get("max")).intValue();
                        replacementValue = String.valueOf(min + deviceRandom.nextInt(max - min + 1));
                    } else {
                        replacementValue = value.toString();
                    }
                } else {
                    replacementValue = value.toString();
                }
                result = result.replace(placeholder, replacementValue);
            }
        }

        // Replace standard placeholders
        result = result.replace("{{deviceIndex}}", String.valueOf(deviceIndex));

        return result;
    }

    /**
     * Process date/time type specifications
     */
    private Object processDateType(String type, Map<String, Object> config, Random deviceRandom,
                                   Map<String, Object> context) {
        long currentTime = System.currentTimeMillis();

        switch (type) {
            case "random_within_last_n_days":
                int days = (Integer) config.getOrDefault("days", 365);
                long randomOffset = (long) deviceRandom.nextInt(days) * 24 * 60 * 60 * 1000L;
                return currentTime - randomOffset;

            case "random_within_last_year":
                long yearOffset = (long) deviceRandom.nextInt(365) * 24 * 60 * 60 * 1000L;
                return currentTime - yearOffset;

            case "relative_to_installation":
                Long installDate = (Long) context.get("installationDate");
                if (installDate != null) {
                    if (config.containsKey("offset_days")) {
                        int offsetDays = (Integer) config.get("offset_days");
                        return installDate + (long) offsetDays * 24 * 60 * 60 * 1000L;
                    } else if (config.containsKey("years")) {
                        int years = (Integer) config.get("years");
                        return installDate + (long) years * 365 * 24 * 60 * 60 * 1000L;
                    }
                }
                return currentTime;

            case "future_relative":
                int futureDays = (Integer) config.getOrDefault("days", 180);
                return currentTime + (long) futureDays * 24 * 60 * 60 * 1000L;

            default:
                return currentTime;
        }
    }

    /**
     * Convert snake_case to camelCase
     */
    private String toCamelCase(String snakeCase) {
        if (snakeCase == null || snakeCase.isEmpty()) {
            return snakeCase;
        }

        String[] parts = snakeCase.split("_");
        if (parts.length == 1) {
            return snakeCase;
        }

        StringBuilder camelCase = new StringBuilder(parts[0]);
        for (int i = 1; i < parts.length; i++) {
            if (!parts[i].isEmpty()) {
                camelCase.append(Character.toUpperCase(parts[i].charAt(0)));
                if (parts[i].length() > 1) {
                    camelCase.append(parts[i].substring(1));
                }
            }
        }

        return camelCase.toString();
    }

    /**
     * Clear configuration cache (useful for testing)
     */
    public void clearCache() {
        configCache.clear();
        log.info("Configuration cache cleared");
    }
}
