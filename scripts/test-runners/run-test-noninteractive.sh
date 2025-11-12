#!/bin/bash
#
# Non-interactive gateway performance test runner
#

# Load environment variables
export $(cat .env.ebmpapst-gateway | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)

# Run Maven
mvn spring-boot:run
