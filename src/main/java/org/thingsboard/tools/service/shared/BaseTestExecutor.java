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
package org.thingsboard.tools.service.shared;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.thingsboard.tools.service.customer.CustomerManager;
import org.thingsboard.tools.service.dashboard.DefaultDashboardManager;
import org.thingsboard.tools.service.device.DeviceProfileManager;
import org.thingsboard.tools.service.discovery.AssetDiscoveryService;
import org.thingsboard.tools.service.rule.RuleChainManager;

import jakarta.annotation.PostConstruct;

@Slf4j
public abstract class BaseTestExecutor implements TestExecutor {
    @Value("${dashboard.createOnStart}")
    private boolean dashboardCreateOnStart;

    @Value("${dashboard.deleteOnComplete}")
    private boolean dashboardDeleteOnComplete;

    @Value("${customer.createOnStart}")
    private boolean customerCreateOnStart;

    @Value("${customer.deleteOnComplete}")
    private boolean customerDeleteOnComplete;

    @Value("${device.createOnStart}")
    protected boolean deviceCreateOnStart;

    @Value("${device.deleteOnComplete}")
    protected boolean deviceDeleteOnComplete;

    @Value("${warmup.enabled:true}")
    protected boolean warmupEnabled;

    @Value("${test.enabled:true}")
    protected boolean testEnabled;

    @Value("${test.updateRootRuleChain:true}")
    protected boolean updateRootRuleChain;

    @Value("${test.revertRootRuleChain:true}")
    protected boolean revertRootRuleChain;

    @Autowired
    private RuleChainManager ruleChainManager;

    @Autowired
    private DefaultDashboardManager dashboardManager;

    @Autowired
    private CustomerManager customerManager;

    @Autowired
    private DeviceProfileManager deviceProfileManager;

    @Autowired
    private AssetDiscoveryService assetDiscoveryService;

    @PostConstruct
    public void init() throws Exception {

    }

    @Override
    public void runTest() throws Exception {
        // Detect and log asset hierarchy
        detectAndLogHierarchy();

        deviceProfileManager.createDeviceProfiles();

        if (dashboardCreateOnStart) {
            dashboardManager.createDashboards();
        }
        if (customerCreateOnStart) {
            customerManager.createCustomers();
        }

        initEntities();

        if (updateRootRuleChain) {
            ruleChainManager.createRuleChainWithCountNodeAndSetAsRoot();
        }

        if (testEnabled) {
            runApiTests();
        }

        if (revertRootRuleChain) {
            Thread.sleep(3000); // wait for messages delivery before removing rule chain

            ruleChainManager.revertRootNodeAndCleanUp();
        }

        cleanUpEntities();

        if (customerDeleteOnComplete) {
            customerManager.removeCustomers();
        }
        if (dashboardDeleteOnComplete) {
            dashboardManager.removeDashboards();
        }
        waitOtherClients();
    }

    protected abstract void initEntities() throws Exception;

    protected abstract void runApiTests() throws InterruptedException;

    protected abstract void cleanUpEntities() throws Exception;

    protected abstract void waitOtherClients() throws Exception;

    /**
     * Detect and log asset hierarchy information
     */
    protected void detectAndLogHierarchy() {
        try {
            log.info("🔍 Analyzing ThingsBoard ecosystem for asset hierarchy...");

            AssetDiscoveryService.HierarchyInfo hierarchy = assetDiscoveryService.detectHierarchy();

            if (hierarchy.isHasHierarchicalAssets()) {
                log.info("🏗️  Hierarchical assets detected!");
                log.info("   📊 Summary: {}", assetDiscoveryService.getHierarchySummary());

                if (hierarchy.isConfiguredFromEnv()) {
                    log.info("   📄 Configuration loaded from: {}", hierarchy.getEnvConfigurationFile());

                    int totalDevices = hierarchy.getRoomConfigurations().values().stream()
                        .mapToInt(AssetDiscoveryService.RoomConfig::getDeviceCount).sum();

                    if (totalDevices > 0) {
                        log.info("   🎯 Ready to create {} devices across {} rooms",
                            totalDevices, hierarchy.getRoomConfigurations().size());
                        log.info("   💡 Devices will be automatically linked to their assigned rooms");
                    }
                } else {
                    log.info("   ⚠️  Hierarchical assets found but no .env configuration");
                    log.info("   💡 Consider running: python test-scenarios/asset-provision.py <scenario>.json");
                }
            } else {
                log.info("🏭 No hierarchical assets detected - running in standalone mode");
                log.info("   💡 Use Python asset provisioning script to create hierarchical scenarios");
            }

        } catch (Exception e) {
            log.warn("Error detecting hierarchy: {}", e.getMessage());
            log.info("🏭 Continuing with standalone device creation");
        }
    }
}
