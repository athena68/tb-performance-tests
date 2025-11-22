# Cleanup Reminders - Scripts to Remove After Stabilization

This file lists all temporary/tentative scripts that should be cleaned up once the codebase runs stably.

## 🚨 **HIGH PRIORITY - Immediate Cleanup Required**

### Scripts with Hardcoded Credentials (Security Risk)
**Action Required:** Refactor to use environment variables or credential files

#### Utility Scripts (Production Use - Needs Refactoring)
- `scripts/monitoring/check-dashboard.sh` ✅ *Uses environment variables with defaults*
- `scripts/device-management/cleanup-test-devices.sh` ✅ *Uses environment variables with validation*
- `scripts/test-runners/start-ebmpapst-ffu.sh` ✅ *Uses environment variables with validation*
- `scripts/device-management/check-device-types.sh` ✅ *Uses environment variables with validation*
- `scripts/monitoring/test-dashboard-v1.sh` ✅ *Uses environment variables with validation*
- `scripts/monitoring/list-ffu-devices.sh` ✅ *Uses environment variables with validation*
- `scripts/device-management/create-gateway-relations.sh` ✅ *Uses environment variables with validation*
- `scripts/monitoring/verify-current-setup.sh` ✅ *Uses environment variables with validation*

#### Archive Scripts (Probably Obsolete)
- `scripts/archive/create-device-relations.sh` - Has hardcoded fallbacks
- `scripts/archive/create-cleanroom-assets.sh` - Has hardcoded fallbacks

#### Python Scripts with Hardcoded Credentials
- `create_asset_profiles.py` - ⚠️ **HARDCODED:** `USERNAME = "tuannt7@fpt.com"`
- `get_asset_profile_ids.py` - ⚠️ **HARDCODED:** `USERNAME = "tuannt7@fpt.com"`
- `test-scenarios/cleanup-gateways.py` - ⚠️ **HARDCODED:** `USERNAME = "tenant@thingsboard.org"`

### Temporary/Test Scripts (Remove Entirely)
**Action Required:** Delete after codebase is stable

#### Device Cleanup Scripts
- `delete-devices.sh` - Temporary device deletion
- `delete-all-devices.sh` - Temporary device deletion
- `delete-all-devices-fixed.sh` - Fixed version of deletion script
- `delete-old-devices.sh` - Selective device cleanup
- `final-cleanup.sh` - Final cleanup script (successor to others)

#### Device Creation Scripts
- `create-gateway.sh` - One-off gateway creation
- `simple-create-gateway.sh` - Simple gateway creation test
- `cleanup-devices.sh` - Another device cleanup variant
- `check-devices.sh` - Device checking utility
- `check-gateway-credentials.sh` - Gateway credential verification

## 🔍 **Analysis Results**

### 1. Source of "Creating 1000" Configuration ✅
**Status:** RESOLVED - No action needed
- **Source:** External configuration, not hardcoded
- **Location:** `src/main/resources/tb-ce-performance-tests.yml` lines 133-135
- **Default:** `DEVICE_END_IDX:1000` in YAML configuration
- **Fix:** Set `DEVICE_END_IDX` environment variable to override default

```yaml
device:
  startIdx: "${DEVICE_START_IDX:0}"
  endIdx: "${DEVICE_END_IDX:1000}"    # ← This creates 1000 devices by default
  count: "${DEVICE_COUNT:1000}"
```

### 2. Scripts with Hardcoded Credentials Status ⚠️
**Utility Scripts:** Most production scripts properly use environment variables ✅
**Archive Scripts:** Have hardcoded fallbacks that should be removed ⚠️
**Python Scripts:** 3 scripts have hardcoded credentials that need refactoring ⚠️

**Good Examples:** (These scripts use proper environment variable patterns)
```bash
REST_USERNAME=${REST_USERNAME:-}
REST_PASSWORD=${REST_PASSWORD:-}
if [[ -z "$REST_USERNAME" || -z "$REST_PASSWORD" ]]; then
    echo "❌ Error: REST_USERNAME and REST_PASSWORD must be set in environment or .env file"
    exit 1
fi
```

## 📋 **Cleanup Action Plan**

### Phase 1: Security Fixes (Do Immediately)
1. **Refactor Python scripts with hardcoded credentials:**
   - `create_asset_profiles.py`
   - `get_asset_profile_ids.py`
   - `test-scenarios/cleanup-gateways.py`

### Phase 2: Temporary Script Cleanup (Do After Stabilization)
1. **Delete all temporary device management scripts:**
   - All `delete-*.sh` scripts
   - All `create-*.sh` scripts (except production ones)
   - All `check-*.sh` scripts (except production ones)

2. **Review and clean archive scripts:**
   - Remove hardcoded fallbacks
   - Or delete entirely if obsolete

### Phase 3: Environment Setup
1. **Create `.env.example` file** with required environment variables
2. **Update documentation** with proper environment setup instructions
3. **Add credential validation** to all production scripts

## ✅ **Currently Compliant Scripts**
These scripts already follow proper security practices:
- All main scripts in `scripts/monitoring/` folder
- All main scripts in `scripts/device-management/` folder
- All main scripts in `scripts/test-runners/` folder

---

**Last Updated:** 2025-01-21
**Status:** Ready for cleanup execution