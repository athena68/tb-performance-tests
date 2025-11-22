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
package org.thingsboard.tools.service.msg.ebmpapstFfu;

import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.thingsboard.tools.service.config.EbmpapstFfuConfig;
import org.thingsboard.tools.service.config.EbmpapstFfuConfigService;
import org.thingsboard.tools.service.msg.BaseMessageGenerator;
import org.thingsboard.tools.service.msg.MessageGenerator;
import org.thingsboard.tools.service.msg.Msg;

import java.util.Map;
import java.util.Optional;
import java.util.Random;

@Slf4j
@Service(value = "configuredTelemetryGenerator")
@ConditionalOnProperty(prefix = "test", value = "payloadType", havingValue = "EBMPAPST_FFU")
public class ConfiguredEbmpapstFfuTelemetryGenerator extends BaseMessageGenerator implements MessageGenerator {

    @Autowired
    private EbmpapstFfuConfigService configService;

    private final Random random = new Random();

    // Get persistent device seed for consistent per-device values
    private int getDeviceSeed(String deviceName) {
        return Math.abs(deviceName.hashCode());
    }

    private Object getRandomValue(EbmpapstFfuConfig.DataPointConfig config, int deviceSeed) {
        if (config == null) return null;

        Random deviceRandom = new Random(deviceSeed);

        if (config.getValues() != null && !config.getValues().isEmpty()) {
            // For discrete values with probabilities
            if (config.getProbabilities() != null) {
                double rand = deviceRandom.nextDouble();
                double cumulative = 0.0;
                for (Map.Entry<String, Double> entry : config.getProbabilities().entrySet()) {
                    cumulative += entry.getValue();
                    if (rand <= cumulative) {
                        return entry.getKey();
                    }
                }
            }
            // For discrete values without probabilities (equal chance)
            int index = deviceRandom.nextInt(config.getValues().size());
            return config.getValues().get(index);
        } else if (config.getMin() != null && config.getMax() != null) {
            // For numeric ranges
            double min = config.getMin();
            double max = config.getMax();
            double value;

            if (config.getVariance() != null && config.getDefaultValue() != null) {
                // For values with variance around default
                double defaultValue = ((Number) config.getDefaultValue()).doubleValue();
                double variance = config.getVariance() * defaultValue;
                value = defaultValue + (deviceRandom.nextGaussian() * variance);
                value = Math.max(min, Math.min(max, value));
            } else {
                // For random values in range
                value = min + (max - min) * deviceRandom.nextDouble();
            }

            // Handle different data types
            if (config.getUnit() != null && config.getUnit().contains("mm/s")) {
                return Math.round(value * 10.0) / 10.0; // One decimal place for vibration
            } else if (config.getUnit() != null && config.getUnit().contains("W")) {
                return (int) Math.round(value); // Integer for power
            } else if (config.getUnit() != null && config.getUnit().contains("m³/h")) {
                return (int) Math.round(value); // Integer for airflow
            } else if (config.getUnit() != null && config.getUnit().contains("RPM")) {
                return (int) Math.round(value); // Integer for RPM
            } else {
                return (int) Math.round(value); // Default to integer
            }
        } else if (config.getDefaultValue() != null) {
            return config.getDefaultValue();
        }

        return null;
    }

    private void applySpecialDeviceConfig(ObjectNode values, String deviceName) {
        Optional<EbmpapstFfuConfig> configOpt = configService.getConfig();
        if (!configOpt.isPresent()) return;

        EbmpapstFfuConfig config = configOpt.get();
        if (config.getSpecialDevices() == null) return;

        // Apply alarm device configuration
        if (configService.isAlarmDevice(deviceName) &&
            config.getSpecialDevices().getAlarmDevices() != null &&
            config.getSpecialDevices().getAlarmDevices().getConfig() != null) {

            Map<String, Object> alarmConfig = config.getSpecialDevices().getAlarmDevices().getConfig();
            for (Map.Entry<String, Object> entry : alarmConfig.entrySet()) {
                values.put(entry.getKey(), entry.getValue());
            }
        }

        // Apply vibration warning device configuration
        if (configService.isVibrationWarningDevice(deviceName) &&
            config.getSpecialDevices().getVibrationWarningDevices() != null &&
            config.getSpecialDevices().getVibrationWarningDevices().getConfig() != null) {

            Map<String, Object> warningConfig = config.getSpecialDevices().getVibrationWarningDevices().getConfig();
            for (Map.Entry<String, Object> entry : warningConfig.entrySet()) {
                values.put(entry.getKey(), entry.getValue());
            }
        }

        // Apply stopped device configuration
        if (configService.isStoppedDevice(deviceName) &&
            config.getSpecialDevices().getStoppedDevices() != null &&
            config.getSpecialDevices().getStoppedDevices().getConfig() != null) {

            Map<String, Object> stoppedConfig = config.getSpecialDevices().getStoppedDevices().getConfig();
            for (Map.Entry<String, Object> entry : stoppedConfig.entrySet()) {
                values.put(entry.getKey(), entry.getValue());
            }
        }
    }

    @Override
    public Msg getNextMessage(String deviceName, boolean shouldTriggerAlarm) {
        byte[] payload;
        try {
            ObjectNode data = mapper.createObjectNode();
            ObjectNode tsNode;

            // Handle gateway vs device mode
            if (isGateway()) {
                tsNode = data.putArray(deviceName).addObject();
            } else {
                tsNode = data;
            }

            tsNode.put("ts", System.currentTimeMillis());
            ObjectNode values = tsNode.putObject("values");

            Optional<EbmpapstFfuConfig> configOpt = configService.getConfig();
            if (!configOpt.isPresent() || configOpt.get().getDataPoints() == null) {
                log.warn("FFU config not available, skipping telemetry generation for device: {}", deviceName);
                return new Msg(data.toString().getBytes());
            }

            EbmpapstFfuConfig config = configOpt.get();
            Map<String, EbmpapstFfuConfig.DataPointConfig> dataPoints = config.getDataPoints();
            int deviceSeed = getDeviceSeed(deviceName);

            // Generate telemetry for all configured data points
            for (Map.Entry<String, EbmpapstFfuConfig.DataPointConfig> entry : dataPoints.entrySet()) {
                String dataPointName = entry.getKey();
                EbmpapstFfuConfig.DataPointConfig dataPointConfig = entry.getValue();

                // Skip if this device is offline (no telemetry at all)
                if ("DW00000012".equals(deviceName) || "DW00000029".equals(deviceName) || "DW00000056".equals(deviceName)) {
                    continue;
                }

                Object value = getRandomValue(dataPointConfig, deviceSeed);
                if (value != null) {
                    values.put(dataPointName, value);
                }
            }

            // Apply special device configurations (alarms, warnings, stopped states)
            applySpecialDeviceConfig(values, deviceName);

            payload = data.toString().getBytes();
        } catch (Exception e) {
            log.error("Failed to generate telemetry for device: {}", deviceName, e);
            payload = "{\"error\":\"Failed to generate telemetry\"}".getBytes();
        }

        return new Msg(payload);
    }
}