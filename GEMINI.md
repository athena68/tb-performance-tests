# ThingsBoard Performance Tests

## Project Overview

This project is a performance testing suite for the ThingsBoard IoT platform. It is a Java application built with Spring Boot, designed to stress-test a ThingsBoard server by simulating a large number of devices and gateways publishing data simultaneously.

**Key Technologies:**

*   **Backend:** Java 17, Spring Boot
*   **Build:** Maven for dependency management and core build, Gradle for packaging (.deb/.rpm)
*   **Protocols:** MQTT, HTTP, LwM2M
*   **Containerization:** Docker

The application simulates various device types and scenarios, allowing for comprehensive performance evaluation of a ThingsBoard instance. Configuration is primarily managed through environment variables or a `.env` file.

## Building and Running

### Building the Project

The project is built using Maven. To compile the code and package it into an executable JAR, run:

```bash
mvn clean package
```

This will produce the application JAR in the `target/` directory. The build process also creates `.deb` and `.rpm` packages for Linux distributions.

### Running the Tests

There are two primary ways to run the performance tests:

**1. Running from Source (for development):**

You can run the application directly from the source code using the Maven Spring Boot plugin. First, configure the test parameters using environment variables, then run:

```bash
# Example configuration (see README.md for all options)
export REST_URL=http://localhost:8080
export MQTT_HOST=localhost
export DEVICE_END_IDX=10
export MESSAGES_PER_SECOND=100

mvn spring-boot:run
```

**2. Running with Docker (recommended):**

The recommended way to run the tests is by using the official Docker image. This ensures a consistent and self-contained environment.

1.  Create a `.env` file with your test configuration (see `README.md` for a full template).
2.  Run the Docker container, mounting the `.env` file:

    ```bash
    docker run -it --env-file .env --name tb-perf-test thingsboard/tb-ce-performance-test:latest
    ```

## Development Conventions

*   **Java Version:** The project requires Java 17.
*   **Configuration:** Application configuration is handled through environment variables, which are documented in the `README.md` file. A default configuration file (`src/main/resources/tb-ce-performance-tests.yml`) is also present.
*   **Code Style:** The code follows standard Java conventions. The `license-maven-plugin` is used to ensure all source files have the correct license header.
*   **Main Entrypoint:** The main application class is `org.thingsboard.tools.PerformanceTestApplication`.
