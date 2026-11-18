# Building the prototype ISO

The ISO configuration targets Ubuntu 24.04 LTS amd64 and XFCE. It is a reproducible starting point, not a release pipeline. Package availability and licensing must be checked against the exact archive snapshot before distribution.

Requirements: Docker Desktop with at least 8 GB RAM, 30 GB free disk, and network access. Review the script before running it. From the repository root run `./scripts/build-iso.sh`. The script builds in a disposable Ubuntu container and writes the ISO under `output/`. On Apple Silicon, amd64 emulation is required. Do not boot this image on real hardware as an installation image; it has no supported installer workflow.

If build dependencies or live-build hooks fail, preserve the logs and fix the configuration before retrying. Never add credentials or personal data to the build context.
