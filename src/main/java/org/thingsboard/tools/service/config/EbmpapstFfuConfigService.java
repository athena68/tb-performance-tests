/**
 * Copyright © 2016-2025 The ThingsBoard Authors
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
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.Optional;

@Slf4j
@Service
public class EbmpapstFfuConfigService {

    private EbmpapstFfuConfig config;
    private final ObjectMapper yamlMapper;

    public EbmpapstFfuConfigService() {
        this.yamlMapper = new ObjectMapper(new YAMLFactory());
    }

    @PostConstruct
    public void init() {
        try {
            loadConfig();
            log.info("✅ FFU Configuration loaded successfully from config/telemetry/devices/ebmpapstffu.yaml");
        } catch (Exception e) {
            log.error("❌ Failed to load FFU configuration", e);
            // Fallback to empty config
            config = new EbmpapstFfuConfig();
        }
    }

    private void loadConfig() throws IOException {
        // Try multiple possible locations
        String[] possiblePaths = {
            "config/telemetry/devices/ebmpapstffu.yaml",
            "../config/telemetry/devices/ebmpapstffu.yaml",
            "src/main/resources/config/telemetry/devices/ebmpapstffu.yaml"
        };

        for (String path : possiblePaths) {
            File configFile = new File(path);
            if (configFile.exists() && configFile.canRead()) {
                log.info("Loading FFU config from: {}", configFile.getAbsolutePath());
                config = yamlMapper.readValue(configFile, EbmpapstFfuConfig.class);
                return;
            }
        }

        // Try loading from classpath
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("config/telemetry/devices/ebmpapstffu.yaml")) {
            if (is != null) {
                log.info("Loading FFU config from classpath");
                config = yamlMapper.readValue(is, EbmpapstFfuConfig.class);
                return;
            }
        } catch (IOException e) {
            log.warn("Failed to load from classpath", e);
        }

        throw new IOException("Could not find FFU configuration file in any location");
    }

    public Optional<EbmpapstFfuConfig> getConfig() {
        return Optional.ofNullable(config);
    }

    public Optional<EbmpapstFfuConfig.DataPointConfig> getDataPointConfig(String dataPointName) {
        if (config != null && config.getDataPoints() != null) {
            return Optional.ofNullable(config.getDataPoints().get(dataPointName));
        }
        return Optional.empty();
    }

    public boolean isAlarmDevice(String deviceName) {
        if (config != null && config.getSpecialDevices() != null &&
            config.getSpecialDevices().getAlarmDevices() != null) {
            return config.getSpecialDevices().getAlarmDevices().getDevices().contains(deviceName);
        }
        return false;
    }

    public boolean isVibrationWarningDevice(String deviceName) {
        if (config != null && config.getSpecialDevices() != null &&
            config.getSpecialDevices().getVibrationWarningDevices() != null) {
            return config.getSpecialDevices().getVibrationWarningDevices().getDevices().contains(deviceName);
        }
        return false;
    }

    public boolean isStoppedDevice(String deviceName) {
        if (config != null && config.getSpecialDevices() != null &&
            config.getSpecialDevices().getStoppedDevices() != null) {
            return config.getSpecialDevices().getStoppedDevices().getDevices().contains(deviceName);
        }
        return false;
    }
}