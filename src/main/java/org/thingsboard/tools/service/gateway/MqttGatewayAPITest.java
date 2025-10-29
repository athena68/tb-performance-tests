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

import io.netty.util.concurrent.Future;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.thingsboard.server.common.data.Device;
import org.thingsboard.server.common.data.id.IdBased;
import org.thingsboard.tools.service.gateway.GatewayRelationManager;
import org.thingsboard.tools.service.mqtt.DeviceClient;
import org.thingsboard.tools.service.shared.BaseMqttAPITest;

import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

@Slf4j
@Service
@ConditionalOnProperty(prefix = "device", value = "api", havingValue = "MQTT")
public class MqttGatewayAPITest extends BaseMqttAPITest implements GatewayAPITest {

    @Value("${gateway.startIdx}")
    int gatewayStartIdxConfig;
    @Value("${gateway.endIdx}")
    int gatewayEndIdxConfig;
    @Value("${gateway.count}")
    int gatewayCount;
    @Value("${gateway.createRelations:true}")
    boolean createGatewayRelations;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private GatewayRelationManager gatewayRelationManager;

    private List<Device> gateways = Collections.synchronizedList(new ArrayList<>(1024));

    private int gatewayStartIdx;
    private int gatewayEndIdx;


    @PostConstruct
    protected void init() {
        super.init();
        if (this.useInstanceIdx) {
            this.gatewayStartIdx = this.gatewayCount * this.instanceIdx;
            this.gatewayEndIdx = this.gatewayStartIdx + this.gatewayCount;
        } else {
            this.gatewayStartIdx = this.gatewayStartIdxConfig;
            this.gatewayEndIdx = this.gatewayEndIdxConfig;
        }
        log.info("Initialized with gatewayStartIdx [{}], gatewayEndIdx [{}]", this.gatewayStartIdx, this.gatewayEndIdx);
    }

    @Override
    public void createDevices() throws Exception {
        createDevices(false);
    }

    @Override
    public void createGateways() throws Exception {
        List<Device> entities = createEntities(gatewayStartIdx, gatewayEndIdx, true,true);
        gateways = Collections.synchronizedList(entities);
    }

    @Override
    public void connectGateways() throws InterruptedException {
        AtomicInteger totalConnectedCount = new AtomicInteger();
        List<String> pack = null;
        List<String> gatewayNames;
        if (!gateways.isEmpty()) {
            gatewayNames = gateways.stream().map(Device::getName).collect(Collectors.toList());
        } else {
            gatewayNames = new ArrayList<>();
            for (int i = gatewayStartIdx; i < gatewayEndIdx; i++) {
                gatewayNames.add(getToken(true, i));
            }
        }
        for (String gateway : gatewayNames) {
            if (pack == null) {
                pack = new ArrayList<>(warmUpPackSize);
            }
            pack.add(gateway);
            if (pack.size() == warmUpPackSize) {
                connectDevices(pack, totalConnectedCount, true);
                Thread.sleep(100 + new Random().nextInt(100));
                pack = null;
            }
        }
        if (pack != null && !pack.isEmpty()) {
            connectDevices(pack, totalConnectedCount, true);
        }
        reportScheduledFuture = restClientService.getScheduler().scheduleAtFixedRate(this::reportMqttClientsStats, 300, 300, TimeUnit.SECONDS);
        mapDevicesToGatewayClientConnections();

        // Log device-gateway connection mapping grouped by gateway
        log.info("================================================================================");
        log.info("GATEWAY CONNECTOR CONFIGURATION");
        log.info("================================================================================");
        log.info("");

        // Group devices by gateway
        java.util.Map<String, java.util.List<DeviceClient>> devicesByGateway = new java.util.LinkedHashMap<>();
        for (DeviceClient deviceClient : deviceClients) {
            String gatewayName = deviceClient.getGatewayName();
            devicesByGateway.computeIfAbsent(gatewayName, k -> new java.util.ArrayList<>()).add(deviceClient);
        }

        // Display each gateway and its connected devices
        for (java.util.Map.Entry<String, java.util.List<DeviceClient>> entry : devicesByGateway.entrySet()) {
            String gatewayName = entry.getKey();
            java.util.List<DeviceClient> devices = entry.getValue();

            log.info("┌─────────────────────────────────────────────────────────────────────────────┐");
            log.info(String.format("│ Gateway: %-66s │", gatewayName));
            log.info("│ Connector Type: MQTT                                                        │");
            log.info(String.format("│ Devices Connected: %-58d │", devices.size()));
            log.info("├─────────────────────────────────────────────────────────────────────────────┤");
            log.info("│ Device Name          │ Device Type     │ Status       │ Connector Type    │");
            log.info("├──────────────────────┼─────────────────┼──────────────┼───────────────────┤");

            for (DeviceClient deviceClient : devices) {
                log.info(String.format("│ %-20s │ %-15s │ %-12s │ %-17s │",
                    deviceClient.getDeviceName(),
                    "EBMPAPST_FFU",
                    "Mapped",
                    "MQTT"));
            }

            log.info("└─────────────────────────────────────────────────────────────────────────────┘");
            log.info("");
        }

        log.info("================================================================================");
        log.info("SUMMARY: {} devices mapped to {} gateways", deviceClients.size(), mqttClients.size());
        log.info("================================================================================");
    }

    private void mapDevicesToGatewayClientConnections() {
        int gatewayCount = mqttClients.size();
        for (int i = deviceStartIdx; i < deviceEndIdx; i++) {
            int deviceIdx = i - deviceStartIdx;
            int gatewayIdx = deviceIdx % gatewayCount;
            DeviceClient client = new DeviceClient();
            client.setMqttClient(mqttClients.get(gatewayIdx));
            client.setDeviceName(getToken(false, i));
            client.setGatewayName(getToken(true, gatewayIdx));
            deviceClients.add(client);
        }
    }

    @Override
    public void warmUpDevices() throws InterruptedException {
        super.warmUpDevices();

        // Log device connection details AFTER warmup completes - grouped by gateway
        log.info("");
        log.info("================================================================================");
        log.info("DEVICE CONNECTION STATUS - All Devices Connected via Gateway");
        log.info("================================================================================");
        log.info("");

        // Group devices by gateway
        java.util.Map<String, java.util.List<DeviceClient>> devicesByGateway = new java.util.LinkedHashMap<>();
        for (DeviceClient deviceClient : deviceClients) {
            String gatewayName = deviceClient.getGatewayName();
            devicesByGateway.computeIfAbsent(gatewayName, k -> new java.util.ArrayList<>()).add(deviceClient);
        }

        // Display each gateway and its connected devices
        for (java.util.Map.Entry<String, java.util.List<DeviceClient>> entry : devicesByGateway.entrySet()) {
            String gatewayName = entry.getKey();
            java.util.List<DeviceClient> devices = entry.getValue();

            log.info("┌─────────────────────────────────────────────────────────────────────────────┐");
            log.info(String.format("│ Gateway: %-66s │", gatewayName));
            log.info("│ Connector Type: MQTT                                                        │");
            log.info(String.format("│ Devices Connected: %-58d │", devices.size()));
            log.info("├─────────────────────────────────────────────────────────────────────────────┤");
            log.info("│ Device Name          │ Device Type     │ Status       │ Connector Type    │");
            log.info("├──────────────────────┼─────────────────┼──────────────┼───────────────────┤");

            for (DeviceClient deviceClient : devices) {
                log.info(String.format("│ %-20s │ %-15s │ %-12s │ %-17s │",
                    deviceClient.getDeviceName(),
                    "EBMPAPST_FFU",
                    "Connected",
                    "MQTT"));
            }

            log.info("└─────────────────────────────────────────────────────────────────────────────┘");
            log.info("");
        }

        log.info("================================================================================");
        log.info("SUMMARY: {} devices successfully connected through {} gateways",
            deviceClients.size(), mqttClients.size());
        log.info("================================================================================");
        log.info("");
    }

    @Override
    public void sendInitialAttributes() throws InterruptedException {
        log.info("Sending initial attributes for {} devices...", deviceClients.size());
        AtomicInteger totalSent = new AtomicInteger();
        AtomicInteger totalFailed = new AtomicInteger();
        CountDownLatch latch = new CountDownLatch(deviceClients.size());

        for (DeviceClient deviceClient : deviceClients) {
            restClientService.getScheduler().submit(() -> {
                try {
                    // Get attribute message from attribute generator
                    byte[] payload = attrMsgGenerator.getNextMessage(deviceClient.getDeviceName(), false).getData();

                    deviceClient.getMqttClient().publish("v1/gateway/attributes",
                        io.netty.buffer.Unpooled.wrappedBuffer(payload),
                        io.netty.handler.codec.mqtt.MqttQoS.AT_MOST_ONCE)
                            .addListener(future -> {
                                if (future.isSuccess()) {
                                    totalSent.incrementAndGet();
                                    log.debug("Initial attributes sent for device: {}", deviceClient.getDeviceName());
                                } else {
                                    totalFailed.incrementAndGet();
                                    log.error("Failed to send initial attributes for device: {}", deviceClient.getDeviceName(), future.cause());
                                }
                                latch.countDown();
                            });
                } catch (Exception e) {
                    totalFailed.incrementAndGet();
                    log.error("Error preparing attributes for device: {}", deviceClient.getDeviceName(), e);
                    latch.countDown();
                }
            });
        }

        boolean completed = latch.await(60, TimeUnit.SECONDS);
        if (completed) {
            log.info("Initial attributes sent successfully for {} devices! Failed: {}", totalSent.get(), totalFailed.get());
        } else {
            log.error("Timeout while sending initial attributes! Sent: {}, Failed: {}, Remaining: {}",
                totalSent.get(), totalFailed.get(), latch.getCount());
        }
    }

    @Override
    public void runApiTests() throws InterruptedException {
        super.runApiTests(deviceClients.size());
    }


    @Override
    protected String getWarmUpTopic() {
        return "v1/gateway/connect";
    }

    @Override
    protected byte[] getData(String deviceName) {
        // Include device type in gateway connect to ensure proper device provisioning
        return ("{\"device\":\"" + deviceName + "\",\"type\":\"EBMPAPST_FFU\"}").getBytes(StandardCharsets.UTF_8);
    }

    @Override
    protected void runApiTestIteration(int iteration, AtomicInteger totalSuccessPublishedCount, AtomicInteger totalFailedPublishedCount, CountDownLatch testDurationLatch) {
        runApiTestIteration(iteration, totalSuccessPublishedCount, totalFailedPublishedCount, testDurationLatch, true);
    }

    @Override
    protected String getTestTopic() {
        // Gateway mode: attributes are sent once during initialization
        // Test phase always sends continuous telemetry
        return "v1/gateway/telemetry";
    }

    @Override
    protected org.thingsboard.tools.service.msg.Msg getNextMessage(String deviceName, boolean alarmRequired) {
        // Gateway mode: always use telemetry generator for test phase
        // Attributes are sent separately during initialization
        return tsMsgGenerator.getNextMessage(deviceName, alarmRequired);
    }

    @Override
    protected void logSuccessTestMessage(int iteration, DeviceClient client) {
        log.debug("[{}] Message was successfully published to device: {} and gateway: {}", iteration, client.getDeviceName(), client.getGatewayName());
    }

    @Override
    protected void logFailureTestMessage(int iteration, DeviceClient client, Future<?> future) {
        log.error("[{}] Error while publishing message to device: {} and gateway: {}", iteration, client.getDeviceName(), client.getGatewayName(),
                future.cause());
    }

    @Override
    public void createGatewayDeviceRelations() throws Exception {
        if (!createGatewayRelations) {
            log.info("Gateway relation creation is disabled (gateway.createRelations=false)");
            return;
        }

        if (gatewayRelationManager == null) {
            log.warn("GatewayRelationManager not available, skipping relation creation");
            return;
        }

        log.info("");
        log.info("================================================================================");
        log.info("CREATING GATEWAY-DEVICE 'Created' RELATIONS");
        log.info("================================================================================");
        log.info("");

        // Build gateway-to-devices map
        Map<Device, List<Device>> gatewayDeviceMap = new HashMap<>();

        // Fetch gateway objects from ThingsBoard if not already loaded
        List<Device> gatewayList = gateways;
        if (gatewayList.isEmpty()) {
            log.info("Gateway list is empty, fetching from ThingsBoard...");
            gatewayList = new ArrayList<>();
            for (int i = gatewayStartIdx; i < gatewayEndIdx; i++) {
                String gatewayName = getToken(true, i);
                try {
                    Device gateway = restClientService.getRestClient().getTenantDevice(gatewayName).orElse(null);
                    if (gateway != null) {
                        gatewayList.add(gateway);
                        log.info("  ✓ Found gateway: {}", gatewayName);
                    } else {
                        log.warn("  ✗ Gateway {} not found in ThingsBoard", gatewayName);
                    }
                } catch (Exception e) {
                    log.error("  ✗ Failed to fetch gateway {}: {}", gatewayName, e.getMessage());
                }
            }
            log.info("Fetched {} gateways from ThingsBoard", gatewayList.size());
        } else {
            log.info("Using {} gateways from existing list", gatewayList.size());
        }

        // First, fetch all device objects from ThingsBoard
        log.info("Fetching device objects from ThingsBoard...");
        Map<String, Device> deviceMap = new HashMap<>();
        for (int i = deviceStartIdx; i < deviceEndIdx; i++) {
            String deviceName = getToken(false, i);
            try {
                Device device = restClientService.getRestClient().getTenantDevice(deviceName).orElse(null);
                if (device != null) {
                    deviceMap.put(deviceName, device);
                } else {
                    log.warn("Device {} not found in ThingsBoard", deviceName);
                }
            } catch (Exception e) {
                log.error("Failed to fetch device {}: {}", deviceName, e.getMessage());
            }
        }

        log.info("Fetched {} devices from ThingsBoard", deviceMap.size());

        // Map devices to gateways based on deviceClients mapping
        log.info("Mapping devices to gateways...");
        for (Device gateway : gatewayList) {
            List<Device> gatewayDevices = new ArrayList<>();

            // Find all devices that belong to this gateway
            for (DeviceClient deviceClient : deviceClients) {
                if (deviceClient.getGatewayName().equals(gateway.getName())) {
                    Device device = deviceMap.get(deviceClient.getDeviceName());
                    if (device != null) {
                        gatewayDevices.add(device);
                    }
                }
            }

            if (!gatewayDevices.isEmpty()) {
                gatewayDeviceMap.put(gateway, gatewayDevices);
                log.info("Mapped {} devices to gateway {}", gatewayDevices.size(), gateway.getName());
            }
        }

        // Create relations
        int totalRelations = gatewayRelationManager.createAllGatewayDeviceRelations(gatewayDeviceMap);

        log.info("");
        log.info("================================================================================");
        log.info("'Created' RELATION SUMMARY");
        log.info("================================================================================");
        log.info("Total gateways: {}", gatewayList.size());
        log.info("Total devices: {}", deviceMap.size());
        log.info("Total 'Created' relations: {}", totalRelations);
        log.info("================================================================================");
        log.info("");
        log.info("Verification:");
        log.info("  1. Login to ThingsBoard UI");
        if (!gatewayList.isEmpty()) {
            log.info("  2. Navigate to: Devices → {} → Relations", gatewayList.get(0).getName());
        }
        log.info("  3. You should see 'Created' relations to all devices");
        log.info("  4. Gateway dashboards should now display device information");
        log.info("================================================================================");
        log.info("");
    }

    @Override
    public void removeGateways() throws Exception {
        removeEntities(gateways.stream().map(Device::getId).collect(Collectors.toList()), "gateways");
    }

    @Override
    public void removeDevices() throws Exception {
        removeEntities(devices.stream().map(IdBased::getId).collect(Collectors.toList()), "devices");
    }
}
