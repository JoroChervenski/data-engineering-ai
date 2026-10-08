#!/bin/sh
# Runs on the host, from the repo folder, before the container is created or started.
# It only checks. It never creates anything in the vault (the vault folder is created by new-client.sh).
project="$1"

if [ -z "${AI_VAULT:-}" ]; then
    echo "AI_VAULT is not set. Export the path of your Obsidian vault in your WSL shell, then start VS Code from it." >&2
    exit 1
fi
for dir in "$AI_VAULT/Knowledge" "$AI_VAULT/Projects/$project"; do
    if [ ! -d "$dir" ]; then
        echo "Missing vault folder: $dir" >&2
        echo "Create the project with scripts/new-client.sh, or check AI_VAULT." >&2
        exit 1
    fi
done

# The container reads this file for client-specific values. It is git-ignored.
[ -f .env ] || : > .env
