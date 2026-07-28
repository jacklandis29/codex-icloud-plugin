# Contributing

Contributions are welcome when they preserve the connector's narrow security model.

## Before opening a pull request

1. Keep the MCP read-only.
2. Do not add SMTP, message mutations, attachment access, arbitrary filesystem access, telemetry, or configurable network destinations.
3. Avoid runtime dependencies unless the security and maintenance benefit clearly outweighs the added supply-chain surface.
4. Add or update tests for behavior that touches IMAP commands, MIME parsing, credentials, search bounds, or tool schemas.
5. Do not include real addresses, message content, credentials, logs, Keychain output, compiled bytecode, or machine-specific paths.

Run:

```bash
python3 scripts/validate_release.py

python3 -m unittest discover \
  -s plugins/icloud-mail/scripts \
  -p 'test_*.py' \
  -v

python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool plugins/icloud-mail/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/icloud-mail/.mcp.json >/dev/null

zsh -n plugins/icloud-mail/setup_keychain.command
zsh -n plugins/icloud-mail/scripts/setup_keychain.sh
zsh -n plugins/icloud-mail/scripts/remove_keychain.sh
```

Pull requests should explain what changed, why it is necessary, and how the security boundary remains intact.
