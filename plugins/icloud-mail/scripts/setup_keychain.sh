#!/bin/zsh
set -eu

ADDRESS_SERVICE="io.github.jacklandis29.codex-icloud-plugin.address"
PASSWORD_SERVICE="io.github.jacklandis29.codex-icloud-plugin.app-password"
ACCOUNT="local"

if [[ "${TERM_PROGRAM:-}" != "Apple_Terminal" ]] || [[ ! -t 0 ]]; then
  echo "For safety, run this setup only in Apple's Terminal app, not inside Codex or an embedded terminal."
  echo "Double-click setup_keychain.command from Finder or open Terminal and run this file there."
  exit 1
fi

echo "Private iCloud Mail setup"
echo ""
echo "Two secure /usr/bin/security terminal prompts will follow. Input is not echoed."
echo "1. At the first prompt, enter your full iCloud email address."
echo "2. At the second, enter the Apple app-specific password created for this plugin."
echo ""
echo "The setup script never receives the values: /usr/bin/security reads them directly"
echo "from this Apple Terminal session into Keychain. They are not command arguments,"
echo "shell history, plugin files, environment variables, or Codex tool input."
echo ""

/usr/bin/security add-generic-password \
  -U \
  -a "$ACCOUNT" \
  -s "$ADDRESS_SERVICE" \
  -l "Codex iCloud Mail address" \
  -j "Private local iCloud Mail MCP" \
  -T "" \
  -w

/usr/bin/security add-generic-password \
  -U \
  -a "$ACCOUNT" \
  -s "$PASSWORD_SERVICE" \
  -l "Codex iCloud Mail app-specific password" \
  -j "Private local iCloud Mail MCP; revoke at account.apple.com" \
  -T "" \
  -w

echo ""
echo "Keychain setup complete. macOS will ask you to approve Keychain access when"
echo "the local MCP starts. Choose Allow Once for the strictest access policy."
