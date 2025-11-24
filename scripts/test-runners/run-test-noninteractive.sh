#!/bin/bash
#
# Non-interactive gateway performance test runner
#

# Load environment variables
export $(cat .env | grep -v '^#' | sed 's/#.*$//' | sed 's/[[:space:]]*$//' | grep -v '^$' | xargs)

#mvn clean compile && mvn spring-boot:run

# Run Maven
mvn spring-boot:run
