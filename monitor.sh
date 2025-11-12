#!/bin/bash
#
# Convenience wrapper for monitoring and verification operations
# Usage: ./monitor.sh [operation] [additional args]
#

OPERATION=${1:-help}

case "$OPERATION" in
  "verify")
    echo "✅ Verifying current setup..."
    exec scripts/monitoring/verify-current-setup.sh "$@"
    ;;
  "dashboard")
    echo "📊 Checking dashboard..."
    exec scripts/monitoring/check-dashboard.sh "$@"
    ;;
  "test-dashboard")
    echo "🧪 Testing dashboard..."
    exec scripts/monitoring/test-dashboard-v1.sh "$@"
    ;;
  "list-ffu")
    echo "📋 Listing FFU devices..."
    exec scripts/monitoring/list-ffu-devices.sh "$@"
    ;;
  "device-types")
    echo "🔧 Checking device types..."
    exec scripts/device-management/check-device-types.sh "$@"
    ;;
  "help"|"h"|"-h"|"--help")
    echo "Usage: ./monitor.sh [operation] [additional args]"
    echo ""
    echo "Available operations:"
    echo "  verify           - Verify current setup and configuration"
    echo "  dashboard        - Check dashboard status"
    echo "  test-dashboard   - Test dashboard functionality"
    echo "  list-ffu         - List all FFU devices"
    echo "  device-types     - Check device type configurations"
    echo "  help             - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./monitor.sh verify"
    echo "  ./monitor.sh dashboard"
    echo "  ./monitor.sh list-ffu"
    ;;
  *)
    echo "❌ Unknown operation: $OPERATION"
    echo "Run './monitor.sh help' for available options"
    exit 1
    ;;
esac