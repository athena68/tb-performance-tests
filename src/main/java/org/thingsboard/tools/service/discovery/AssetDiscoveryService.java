package org.thingsboard.tools.service.discovery;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.thingsboard.server.common.data.Device;
import org.thingsboard.tools.service.shared.RestClientService;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.*;

@Slf4j
@Service
public class AssetDiscoveryService {

    @Autowired
    private RestClientService restClientService;

    public static class HierarchyInfo {
        private boolean hasHierarchicalAssets = false;
        private boolean configuredFromEnv = false;
        private String envConfigurationFile;
        private Map<String, RoomConfig> roomConfigurations = new HashMap<>();

        // Getters and setters
        public boolean isHasHierarchicalAssets() { return hasHierarchicalAssets; }
        public void setHasHierarchicalAssets(boolean hasHierarchicalAssets) { this.hasHierarchicalAssets = hasHierarchicalAssets; }
        public boolean isConfiguredFromEnv() { return configuredFromEnv; }
        public void setConfiguredFromEnv(boolean configuredFromEnv) { this.configuredFromEnv = configuredFromEnv; }
        public String getEnvConfigurationFile() { return envConfigurationFile; }
        public void setEnvConfigurationFile(String envConfigurationFile) { this.envConfigurationFile = envConfigurationFile; }
        public Map<String, RoomConfig> getRoomConfigurations() { return roomConfigurations; }
        public void setRoomConfigurations(Map<String, RoomConfig> roomConfigurations) { this.roomConfigurations = roomConfigurations; }
    }

    public static class RoomConfig {
        private String id;
        private String name;
        private int deviceStart;
        private int deviceEnd;
        private int deviceCount;

        // Getters and setters
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public int getDeviceStart() { return deviceStart; }
        public void setDeviceStart(int deviceStart) { this.deviceStart = deviceStart; }
        public int getDeviceEnd() { return deviceEnd; }
        public void setDeviceEnd(int deviceEnd) { this.deviceEnd = deviceEnd; }
        public int getDeviceCount() { return deviceCount; }
        public void setDeviceCount(int deviceCount) { this.deviceCount = deviceCount; }
    }

    /**
     * Detect if hierarchical assets exist and load configuration
     */
    public HierarchyInfo detectHierarchy() {
        HierarchyInfo info = new HierarchyInfo();

        try {
            // Check for .env file first
            File envFile = new File(".env");
            if (envFile.exists()) {
                info.setEnvConfigurationFile(".env");
                info.setConfiguredFromEnv(true);
                loadEnvConfiguration(info, envFile);
                log.info("📄 Found .env configuration file");
            }

            // Since we don't have Asset classes in this codebase,
            // we rely on the .env file to determine if hierarchy exists
            if (info.isConfiguredFromEnv() && !info.getRoomConfigurations().isEmpty()) {
                info.setHasHierarchicalAssets(true);
                log.info("🏗️  Detected hierarchical configuration from .env with {} rooms",
                    info.getRoomConfigurations().size());
            }

        } catch (Exception e) {
            log.warn("Error detecting hierarchy: {}", e.getMessage());
        }

        return info;
    }

    /**
     * Load room configurations from .env file
     */
    private void loadEnvConfiguration(HierarchyInfo info, File envFile) throws IOException {
        Properties props = new Properties();
        try (FileInputStream fis = new FileInputStream(envFile)) {
            props.load(fis);
        }

        // Check if hierarchy was created
        String hierarchyCreated = props.getProperty("HIERARCHY_CREATED", "false");
        if (!"true".equals(hierarchyCreated)) {
            log.info("📄 .env file found but HIERARCHY_CREATED=false");
            return;
        }

        // Parse room configurations from .env
        Map<String, RoomConfig> roomConfigs = new HashMap<>();

        // Find all room configurations
        for (String key : props.stringPropertyNames()) {
            if (key.startsWith("ROOM_") && key.endsWith("_NAME")) {
                String roomNumber = key.substring(5, key.indexOf("_NAME"));
                RoomConfig roomConfig = new RoomConfig();

                roomConfig.setName(props.getProperty(key));
                roomConfig.setId(props.getProperty("ROOM_" + roomNumber + "_ID"));

                String deviceStart = props.getProperty("ROOM_" + roomNumber + "_DEVICE_START", "0");
                String deviceEnd = props.getProperty("ROOM_" + roomNumber + "_DEVICE_END", "0");
                String deviceCount = props.getProperty("ROOM_" + roomNumber + "_DEVICE_COUNT", "0");

                try {
                    roomConfig.setDeviceStart(Integer.parseInt(deviceStart));
                    roomConfig.setDeviceEnd(Integer.parseInt(deviceEnd));
                    roomConfig.setDeviceCount(Integer.parseInt(deviceCount));

                    roomConfigs.put("ROOM_" + roomNumber, roomConfig);
                } catch (NumberFormatException e) {
                    log.warn("Invalid device configuration for room {}: {}", roomNumber, e.getMessage());
                }
            }
        }

        info.setRoomConfigurations(roomConfigs);

        if (!roomConfigs.isEmpty()) {
            int totalDevices = roomConfigs.values().stream().mapToInt(RoomConfig::getDeviceCount).sum();
            log.info("📄 Loaded {} room configurations from .env ({} devices total)",
                roomConfigs.size(), totalDevices);
        }
    }

    /**
     * Find which room a device index belongs to
     */
    public Optional<RoomConfig> findRoomForDeviceIndex(int deviceIndex) {
        HierarchyInfo hierarchy = detectHierarchy();

        for (RoomConfig room : hierarchy.getRoomConfigurations().values()) {
            if (deviceIndex >= room.getDeviceStart() && deviceIndex <= room.getDeviceEnd()) {
                return Optional.of(room);
            }
        }

        return Optional.empty();
    }

    /**
     * Check if device exists
     */
    public boolean deviceExists(String deviceName) {
        try {
            Optional<Device> device = restClientService.getRestClient().findDevice(deviceName);
            return device.isPresent();
        } catch (Exception e) {
            log.debug("Error checking device existence: {}", e.getMessage());
            return false;
        }
    }

    /**
     * Count existing devices in range
     */
    public int countExistingDevices(String prefix, int startIdx, int endIdx) {
        int count = 0;
        for (int i = startIdx; i <= endIdx; i++) {
            String deviceName = prefix + String.format("%08d", i);
            if (deviceExists(deviceName)) {
                count++;
            }
        }
        return count;
    }

    /**
     * Get summary information
     */
    public String getHierarchySummary() {
        HierarchyInfo info = detectHierarchy();

        if (!info.isHasHierarchicalAssets()) {
            return "No hierarchical assets detected";
        }

        StringBuilder summary = new StringBuilder();
        summary.append("Hierarchical configuration detected:\n");
        summary.append(String.format("  - Rooms: %d\n", info.getRoomConfigurations().size()));

        if (info.isConfiguredFromEnv()) {
            summary.append(String.format("  - Configured from: %s\n", info.getEnvConfigurationFile()));
            int totalDevices = info.getRoomConfigurations().values().stream()
                .mapToInt(RoomConfig::getDeviceCount).sum();
            summary.append(String.format("  - Devices planned: %d\n", totalDevices));
        }

        return summary.toString();
    }
}