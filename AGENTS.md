# Repository Guidelines

## Project Structure & Module Organization
- `src/main/java/org/thingsboard/tools/`: Core Java services for provisioning, gateway simulation, rule validation, and FFU payload generators (`service/...`).
- `src/main/resources/`: Device profiles and assembly descriptors; update `device-profiles/ebmpapst_ffu.json` when telemetry fields change.
- `docs/` & `STATUS.md`: Authoritative runbooks and environment notes—place new guides beside the existing markdown.
- `test-scenarios/`: Scenario JSON definitions (Site → Building → Floor → Room → Gateway → Devices); record updates in `test-scenarios/README.md`.
- `scripts/` and root shell utilities: Entry points such as `start-ebmpapst-gateway.sh`, `verify-current-setup.sh`, and `cleanup-scenario.py`; `scripts/archive/` retains deprecated examples.

## Build, Test, and Development Commands
- `mvn license:format clean install -Ddockerfile.skip=false` or `./build.sh`: Compile, enforce headers, and build Docker artifacts.
- `mvn test`: Execute unit/integration suites in `src/test/java`; mirror package layout for new tests.
- `./provision-scenario.py test-scenarios/<file>.json`: Build full hierarchies and produce `.env.ebmpapst-gateway`.
- `./start-ebmpapst-gateway.sh`: Run the MQTT gateway performance test using generated credentials.
- `./verify-current-setup.sh`, `./check-device-types.sh`, `./list-ffu-devices.sh`: Pre/post-test sanity checks.
- `./cleanup-scenario.py [--pattern ...]`: Remove provisioned assets; prefer the JSON-driven default to avoid strays.

## Coding Style & Naming Conventions
- Java: four-space indentation, PascalCase classes, camelCase members, SCREAMING_SNAKE_CASE constants; keep packages aligned with directory structure.
- Python: follow PEP 8 (snake_case, four spaces) and reuse existing argparse patterns for new CLI helpers.
- Scenario JSON: keep lowerCamelCase keys and ThingsBoard-friendly identifiers (`GW00000000`, `DW00000000`).
- Run `mvn license:format` before submitting to refresh headers and formatting.

## Testing Guidelines
- Place Java tests under `src/test/java/...` with `*Test` suffixes; focus on provisioning flows, gateway publishers, and payload builders.
- Demonstrate script changes by running the relevant provisioning command, `./start-ebmpapst-gateway.sh`, and `./verify-current-setup.sh`, attaching condensed output to reviews.
- After large test runs, execute `./cleanup-scenario.py` to return shared environments to baseline.

## Commit & Pull Request Guidelines
- Use imperative, descriptive commit messages (e.g., "Add multi-gateway test scenario"), matching current history.
- PRs should outline affected modules/scripts, list verification commands, and link related dashboards or issues.
- Highlight breaking changes to scenario schemas, device profiles, or Docker packaging so deployment teams can coordinate.

## Security & Configuration Tips
- Keep `.env*`, tokens, and certificates out of version control; store local copies only.
- For shared clusters, rotate generated credentials after demos and confirm cleanup scripts removed temporary assets.
- When adjusting Docker build settings, note required host packages (e.g., `qemu-user-static`, `binfmt-support`) in `STATUS.md` or docs.
