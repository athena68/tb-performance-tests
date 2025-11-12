#!/bin/bash
#
# Convenience wrapper for commonly used test runners
# Usage: ./run-test.sh [type] [additional args]
#

TYPE=${1:-help}

case "$TYPE" in
  "performance"|"perf")
    echo "🚀 Starting performance test..."
    exec scripts/test-runners/start.sh "$@"
    ;;
  "gateway"|"gw")
    echo "🌐 Starting ebmpapst gateway test..."
    exec scripts/test-runners/start-ebmpapst-gateway.sh "$@"
    ;;
  "ffu")
    echo "💨 Starting ebmpapst FFU test..."
    exec scripts/test-runners/start-ebmpapst-ffu.sh "$@"
    ;;
  "non-interactive"|"auto")
    echo "🤖 Starting non-interactive test..."
    exec scripts/test-runners/run-test-noninteractive.sh "$@"
    ;;
  "stop")
    echo "🛑 Stopping all tests..."
    exec scripts/test-runners/stop-all-tests.sh "$@"
    ;;
  "help"|"h"|"-h"|"--help")
    echo "Usage: ./run-test.sh [type] [additional args]"
    echo ""
    echo "Available test types:"
    echo "  performance, perf     - Run standard performance test"
    echo "  gateway, gw           - Run ebmpapst gateway test"
    echo "  ffu                   - Run ebmpapst FFU test"
    echo "  non-interactive, auto - Run non-interactive test"
    echo "  stop                  - Stop all running tests"
    echo "  help                  - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run-test.sh performance"
    echo "  ./run-test.sh gateway"
    echo "  ./run-test.sh stop"
    ;;
  *)
    echo "❌ Unknown test type: $TYPE"
    echo "Run './run-test.sh help' for available options"
    exit 1
    ;;
esac