# ThingsBoard Cleanup Guide

## 🧹 Enhanced Cleanup Tools

I've created two improved cleanup scripts that handle missing entities gracefully and provide more options for cleaning up your ThingsBoard test data.

---

## 🛠️ Available Cleanup Scripts

### 1. **cleanup-scenario.py** (Fixed Original)
```bash
python3 test-scenarios/cleanup-scenario.py
```

**Features:**
- ✅ **Fixed 404 error handling** - Gracefully handles missing entities
- ✅ **Simple to use** - Works with existing `/tmp/provisioned_entities.json`
- ✅ **Backward compatible** - Drop-in replacement for original script
- ✅ **Clean output** - Clear success/warning messages

**When to use:**
- Quick cleanup from known entities file
- Existing workflows that expect the original script behavior

### 2. **cleanup-scenario-v2.py** (Enhanced)
```bash
python3 test-scenarios/cleanup-scenario-v2.py [options]
```

**Features:**
- ✅ **Dry run mode** - Preview what would be deleted
- ✅ **Pattern-based cleanup** - Delete entities by name patterns
- ✅ **Comprehensive statistics** - Detailed cleanup summary
- ✅ **Confirmation prompts** - Safety confirmation before deletion
- ✅ **Entity existence checking** - Checks before attempting deletion
- ✅ **Multiple cleanup methods** - File, pattern, or all test data

**When to use:**
- Complex cleanup scenarios
- When you need to preview before deletion
- Pattern-based cleanup operations
- Detailed cleanup reporting

---

## 🚀 Usage Examples

### **Basic Cleanup (Both Scripts)**
```bash
# Original fixed script
python3 test-scenarios/cleanup-scenario.py

# Enhanced script - same behavior as original
python3 test-scenarios/cleanup-scenario-v2.py --file /tmp/provisioned_entities.json
```

### **Dry Run Preview**
```bash
# See what would be deleted without actually deleting
python3 test-scenarios/cleanup-scenario-v2.py --dry-run --file /tmp/provisioned_entities.json
```

### **Pattern-Based Cleanup**
```bash
# Delete all devices starting with DW
python3 test-scenarios/cleanup-scenario-v2.py --pattern "DW*" --type device

# Delete all assets with "Test" in the name
python3 test-scenarios/cleanup-scenario-v2.py --pattern "*Test*" --type asset

# Delete all entities (devices + assets) matching pattern
python3 test-scenarios/cleanup-scenario-v2.py --pattern "Demo*"
```

### **Comprehensive Test Data Cleanup**
```bash
# Clean up all common test patterns (DW*, GW*, Test*, Demo*, etc.)
python3 test-scenarios/cleanup-scenario-v2.py --all-test-data

# Use dry run to preview what would be cleaned up
python3 test-scenarios/cleanup-scenario-v2.py --dry-run --all-test-data
```

### **Custom Server and Credentials**
```bash
# Use custom server
python3 test-scenarios/cleanup-scenario-v2.py --url http://localhost:8080 --username admin@local.org --password admin --pattern "Test*"
```

---

## 📊 Enhanced Script Output

The enhanced script provides detailed statistics:

```
============================================================
📊 CLEANUP SUMMARY
============================================================

Devices:
  Found: 60
  Deleted: 45
  Missing: 15
  Failed: 0

Assets:
  Found: 8
  Deleted: 6
  Missing: 2
  Failed: 0

🎯 Overall Results:
  Total Found: 68
  Total Deleted: 51
  Already Missing: 17
  Failed: 0
  Success Rate: 100.0%
```

**Status Indicators:**
- ⚠ **"not found"** means entity was already deleted (normal)
- ✅ **"Deleted successfully"** means entity was removed
- 🔍 **"DRY RUN"** shows what would be deleted (no actual deletion)

---

## 🎯 Common Cleanup Scenarios

### **Scenario 1: After Running Provisioner**
```bash
# Clean up the entities you just created
python3 test-scenarios/cleanup-scenario.py
# OR
python3 test-scenarios/cleanup-scenario-v2.py --file /tmp/provisioned_entities.json
```

### **Scenario 2: Clean Up All Test Data**
```bash
# Preview what will be cleaned up
python3 test-scenarios/cleanup-scenario-v2.py --dry-run --all-test-data

# Actually clean up
python3 test-scenarios/cleanup-scenario-v2.py --all-test-data
```

### **Scenario 3: Selective Cleanup**
```bash
# Only clean up FFU devices (DW*)
python3 test-scenarios/cleanup-scenario-v2.py --pattern "DW*" --type device

# Only clean up test entities
python3 test-scenarios/cleanup-scenario-v2.py --pattern "*Test*" --type all
```

### **Scenario 4: Safe Cleanup with Preview**
```bash
# Always use dry run first
python3 test-scenarios/cleanup-scenario-v2.py --dry-run --pattern "*"

# Then execute without dry run if satisfied
python3 test-scenarios/cleanup-scenario-v2.py --pattern "*"
```

---

## 🔍 Troubleshooting

### **404 Errors (Entity Not Found)**
- ✅ **Normal** - Entity already deleted or never existed
- ✅ **Fixed** - Both scripts now handle this gracefully
- ⚠ **Not an error** - Considered as successful cleanup

### **405 Method Not Allowed**
- ⚠ **API limitation** - Some ThingsBoard instances don't support textSearch
- ✅ **Fallback** - Use file-based cleanup or all-test-data cleanup

### **Permission Denied**
- ❌ **Authentication issue** - Check username/password
- ❌ **Authorization issue** - Ensure user has delete permissions

### **Connection Refused**
- ❌ **Server offline** - Check ThingsBoard server status
- ❌ **Wrong URL** - Verify ThingsBoard URL

---

## 🛡️ Safety Features

### **Built-in Protections:**
1. **Existence checking** - Verifies entities exist before deletion
2. **Dry run mode** - Preview before actual deletion
3. **Confirmation prompts** - User confirmation required for pattern deletion
4. **Graceful 404 handling** - Already deleted entities not considered errors
5. **Detailed logging** - Clear status messages for each operation

### **Best Practices:**
1. **Always use dry run first** for pattern-based cleanup
2. **Keep entities file** for reliable cleanup reference
3. **Test with smaller patterns** before using wildcards
4. **Check output** for any unexpected "Failed" messages

---

## 📝 Notes

- Both scripts handle **missing entities gracefully** (404 errors are normal)
- The enhanced script provides **better visibility** and **more options**
- **All-test-data cleanup** uses common test patterns: `DW*`, `GW*`, `Test*`, `Demo*`, `ST*`, `SM*`, `*-Asset`, `Site*`, `Building*`, `Floor*`, `Room*`
- **Statistics** help you understand exactly what was cleaned up

---

## 🎉 Ready to Use

Both cleanup scripts are ready for immediate use. The original script has been fixed to handle the 404 errors you encountered, and the enhanced script provides powerful additional capabilities for more complex cleanup scenarios.

**Start with:** `python3 test-scenarios/cleanup-scenario.py` for immediate results, or try `python3 test-scenarios/cleanup-scenario-v2.py --dry-run` to preview what would be cleaned up.