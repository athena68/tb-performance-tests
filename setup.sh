#!/bin/bash
#
# Convenience wrapper for setup and management operations
# Usage: ./setup.sh [operation] [additional args]
#

OPERATION=${1:-help}

case "$OPERATION" in
  "scenario")
    echo "🏗️  Provisioning scenario..."
    exec python3 test-scenarios/provision-scenario.py "$@"
    ;;
  "cleanup-scenario")
    echo "🧹 Cleaning up scenario..."
    exec python3 test-scenarios/cleanup-scenario.py "$@"
    ;;
  "gateway-credentials")
    echo "🔑 Setting up gateway credentials..."
    exec scripts/device-management/setup-gateway-credentials.sh "$@"
    ;;
  "gateway-relations")
    echo "🔗 Creating gateway relations..."
    exec scripts/device-management/create-gateway-relations.sh "$@"
    ;;
  "cleanup-devices")
    echo "🗑️  Cleaning up test devices..."
    exec scripts/device-management/cleanup-test-devices.sh "$@"
    ;;
  "verify")
    echo "✅ Verifying setup..."
    exec scripts/monitoring/verify-current-setup.sh "$@"
    ;;
  "build")
    echo "🏗️  Building project..."
    exec scripts/build/build.sh "$@"
    ;;
  "help"|"h"|"-h"|"--help")
    echo "Usage: ./setup.sh [operation] [additional args]"
    echo ""
    echo "Available operations:"
    echo "  scenario           - Provision scenario hierarchy"
    echo "  cleanup-scenario   - Clean up provisioned scenario"
    echo "  gateway-credentials - Setup gateway device tokens"
    echo "  gateway-relations  - Create gateway-device relations"
    echo "  cleanup-devices    - Remove test devices"
    echo "  verify             - Verify current setup"
    echo "  build              - Build the project"
    echo "  help               - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh scenario test-scenarios/scenario-hanoi-cleanroom.json"
    echo "  ./setup.sh verify"
    echo "  ./setup.sh build"
    ;;
  *)
    echo "❌ Unknown operation: $OPERATION"
    echo "Run './setup.sh help' for available options"
    exit 1
    ;;
esac