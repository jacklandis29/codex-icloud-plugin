#!/bin/zsh
set -eu
PLUGIN_DIR="${0:A:h}"
exec "$PLUGIN_DIR/scripts/setup_keychain.sh"
