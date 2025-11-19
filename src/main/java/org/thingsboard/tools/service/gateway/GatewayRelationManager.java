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

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.thingsboard.rest.client.RestClient;
import org.thingsboard.server.common.data.Device;
import org.thingsboard.server.common.data.id.DeviceId;
import org.thingsboard.server.common.data.relation.EntityRelation;
import org.thingsboard.server.common.data.relation.RelationTypeGroup;
import org.thingsboard.tools.service.shared.RestClientService;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Manager for creating "Created" relations between gateways and devices.
 * Required for gateway dashboards to display device information.
 */
@Slf4j
@Service
public class GatewayRelationManager {

    private static final String CREATED_RELATION_TYPE = "Created";

    private final RestClientService restClientService;

    @Value("${gateway.createRelations:true}")
    private boolean createRelations;

    public GatewayRelationManager(RestClientService restClientService) {
        this.restClientService = restClientService;
    }

    /**
     * Creates bidirectional "Created" relations between gateway and its devices.
     * This is required for gateway dashboards to properly display device information.
     *
     * @param gateway The gateway device
     * @param devices List of devices that belong to this gateway
     * @return Number of relations successfully created
     */
    public int createGatewayDeviceRelations(Device gateway, List<Device> devices) {
        if (!createRelations) {
            log.info("Gateway relation creation is disabled (gateway.createRelations=false)");
            return 0;
        }

        log.info("Creating '{}' relations between gateway {} and {} devices...",
                CREATED_RELATION_TYPE, gateway.getName(), devices.size());

        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger failCount = new AtomicInteger(0);
        RestClient restClient = restClientService.getRestClient();

        for (Device device : devices) {
            try {
                // Create bidirectional "Created" relations
                // 1. Gateway -> Device (From gateway perspective)
                EntityRelation gatewayToDevice = new EntityRelation();
                gatewayToDevice.setFrom(gateway.getId());
                gatewayToDevice.setTo(device.getId());
                gatewayToDevice.setType(CREATED_RELATION_TYPE);
                gatewayToDevice.setTypeGroup(RelationTypeGroup.COMMON);

                restClient.saveRelation(gatewayToDevice);
                successCount.incrementAndGet();

                // 2. Device -> Gateway (From device perspective, shows as "To" gateway)
                EntityRelation deviceToGateway = new EntityRelation();
                deviceToGateway.setFrom(device.getId());
                deviceToGateway.setTo(gateway.getId());
                deviceToGateway.setType(CREATED_RELATION_TYPE);
                deviceToGateway.setTypeGroup(RelationTypeGroup.COMMON);

                restClient.saveRelation(deviceToGateway);
                successCount.incrementAndGet();

                log.debug("Created '{}' relations: {} <-> {}",
                        CREATED_RELATION_TYPE, gateway.getName(), device.getName());

            } catch (Exception e) {
                failCount.incrementAndGet();
                log.error("Failed to create relation between gateway {} and device {}: {}",
                        gateway.getName(), device.getName(), e.getMessage());
            }
        }

        int totalRelations = successCount.get();
        log.info("✓ Created {} '{}' relations for gateway {} ({} devices, {} relations each direction)",
                totalRelations, CREATED_RELATION_TYPE, gateway.getName(), devices.size(), totalRelations / 2);

        if (failCount.get() > 0) {
            log.warn("Failed to create {} relations", failCount.get());
        }

        return totalRelations;
    }

    /**
     * Creates bidirectional "Created" relations for multiple gateways.
     *
     * @param gatewayDeviceMap Map of gateways to their respective devices
     * @return Total number of relations successfully created
     */
    public int createAllGatewayDeviceRelations(java.util.Map<Device, List<Device>> gatewayDeviceMap) {
        if (!createRelations) {
            log.info("Gateway relation creation is disabled (gateway.createRelations=false)");
            return 0;
        }

        log.info("================================================================================");
        log.info("Creating '{}' relations for {} gateways", CREATED_RELATION_TYPE, gatewayDeviceMap.size());
        log.info("================================================================================");

        AtomicInteger totalRelations = new AtomicInteger(0);

        gatewayDeviceMap.forEach((gateway, devices) -> {
            int relationsCreated = createGatewayDeviceRelations(gateway, devices);
            totalRelations.addAndGet(relationsCreated);
        });

        log.info("================================================================================");
        log.info("SUMMARY: Created {} total '{}' relations across {} gateways",
                totalRelations.get(), CREATED_RELATION_TYPE, gatewayDeviceMap.size());
        log.info("================================================================================");

        return totalRelations.get();
    }

    /**
     * Creates relations asynchronously for better performance with large device counts.
     *
     * @param gatewayDeviceMap Map of gateways to their respective devices
     * @return CompletableFuture with total number of relations created
     */
    public CompletableFuture<Integer> createAllGatewayDeviceRelationsAsync(
            java.util.Map<Device, List<Device>> gatewayDeviceMap) {

        return CompletableFuture.supplyAsync(() -> {
            return createAllGatewayDeviceRelations(gatewayDeviceMap);
        }, restClientService.getHttpExecutor());
    }

    /**
     * Deletes "Created" relations between gateway and device.
     * Useful for cleanup operations.
     *
     * @param gatewayId Gateway device ID
     * @param deviceId Device ID
     */
    public void deleteGatewayDeviceRelation(DeviceId gatewayId, DeviceId deviceId) {
        try {
            RestClient restClient = restClientService.getRestClient();

            // Delete both directions
            restClient.deleteRelation(gatewayId, CREATED_RELATION_TYPE, RelationTypeGroup.COMMON, deviceId);
            restClient.deleteRelation(deviceId, CREATED_RELATION_TYPE, RelationTypeGroup.COMMON, gatewayId);

            log.debug("Deleted '{}' relations between gateway {} and device {}",
                    CREATED_RELATION_TYPE, gatewayId, deviceId);
        } catch (Exception e) {
            log.error("Failed to delete relation: {}", e.getMessage());
        }
    }

    /**
     * Verifies if "Created" relation exists between gateway and device.
     *
     * @param gatewayId Gateway device ID
     * @param deviceId Device ID
     * @return true if relation exists
     */
    public boolean verifyGatewayDeviceRelation(DeviceId gatewayId, DeviceId deviceId) {
        try {
            RestClient restClient = restClientService.getRestClient();
            EntityRelation relation = restClient.getRelation(gatewayId, CREATED_RELATION_TYPE,
                    RelationTypeGroup.COMMON, deviceId).orElse(null);
            return relation != null;
        } catch (Exception e) {
            log.debug("Relation check failed: {}", e.getMessage());
            return false;
        }
    }
}
