#!/bin/zsh
set -eu

/usr/bin/security delete-generic-password -a "local" -s "io.github.jacklandis29.codex-icloud-plugin.address" >/dev/null 2>&1 || true
/usr/bin/security delete-generic-password -a "local" -s "io.github.jacklandis29.codex-icloud-plugin.app-password" >/dev/null 2>&1 || true
echo "Removed the private iCloud Mail credentials from macOS Keychain."
