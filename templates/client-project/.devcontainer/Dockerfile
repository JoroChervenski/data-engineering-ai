# Conservative base: Debian 12 with Python 3.12 and a non-root "vscode" user. It already has git, curl
# and the usual shell tools. Nothing client-specific and no credentials are baked in; everything else is
# injected at run time (see README.md, "Credentials").
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Add client-specific tools below, as root, then switch back to "vscode". If `apt-get update` fails with a
# Yarn "NO_PUBKEY" error, the base image's Yarn apt source has an expired key: delete
# /etc/apt/sources.list.d/yarn.list first.

USER vscode
