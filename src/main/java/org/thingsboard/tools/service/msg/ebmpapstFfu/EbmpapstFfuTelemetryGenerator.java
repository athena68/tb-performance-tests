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
