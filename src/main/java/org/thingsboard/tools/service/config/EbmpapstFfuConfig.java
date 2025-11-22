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

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class EbmpapstFfuConfig {

    @JsonProperty("data_points")
    private Map<String, DataPointConfig> dataPoints;

    @JsonProperty("generation_rules")
    private GenerationRulesConfig generationRules;

    @JsonProperty("special_devices")
    private SpecialDevicesConfig specialDevices;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class DataPointConfig {
        private String unit;
        private String description;
        private Double min;
        private Double max;
        private Object defaultValue;
        private Double alarmThreshold;
        private Double criticalThreshold;
        private String formula;
        private Boolean persistent;
        private Double variance;
        private List<String> values;
        private Map<Integer, String> mapping;
        private Map<String, Double> probabilities;
        private List<String> correlation;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class GenerationRulesConfig {
        @JsonProperty("publish_interval_ms")
        private Long publishIntervalMs;

        @JsonProperty("data_variation")
        private Map<String, Double> dataVariation;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class SpecialDevicesConfig {
        @JsonProperty("alarm_devices")
        private AlarmDevicesConfig alarmDevices;

        @JsonProperty("vibration_warning_devices")
        private VibrationWarningDevicesConfig vibrationWarningDevices;

        @JsonProperty("stopped_devices")
        private StoppedDevicesConfig stoppedDevices;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AlarmDevicesConfig {
        private List<String> devices;
        private Map<String, Object> config;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class VibrationWarningDevicesConfig {
        private List<String> devices;
        private Map<String, Object> config;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class StoppedDevicesConfig {
        private List<String> devices;
        private Map<String, Object> config;
    }
}