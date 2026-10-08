#!/bin/sh
# Runs on the host, from the repo folder, before the container is created or started.
# It only checks; it creates nothing. The container gets Knowledge/ and Templates/ from the vault,
# read-only, and nothing else: no Projects/, no Home.md, no client repos.

if [ -z "${AI_VAULT:-}" ]; then
    echo "AI_VAULT is not set. Export the path of your Obsidian vault in your WSL shell, then start VS Code from it." >&2
    exit 1
fi
for dir in "$AI_VAULT/Knowledge" "$AI_VAULT/Templates"; do
    if [ ! -d "$dir" ]; then
        echo "Missing vault folder: $dir (check AI_VAULT)" >&2
        exit 1
    fi
done
