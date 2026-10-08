#!/bin/sh
# Create a new client repo from the framework's client template. See new_client.py for details.
#
#   ./scripts/new-client.sh <project> <target-path> [--repo NAME] [--vault DIR] [--with-azure-cli] [--no-sync]
#
# Run it yourself in a host terminal, not inside a container.
exec python3 "$(dirname "$0")/new_client.py" "$@"
