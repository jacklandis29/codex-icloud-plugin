# Local Mail for Codex

An unofficial, local-only, read-only Codex connector for use with iCloud Mail.

[![Tests](https://github.com/jacklandis29/codex-icloud-plugin/actions/workflows/test.yml/badge.svg)](https://github.com/jacklandis29/codex-icloud-plugin/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

This plugin lets Codex search and read selected messages through Apple's encrypted IMAP service. It is deliberately narrow: there are no tools for sending, deleting, archiving, moving, marking, or downloading attachments.

## Security model

| Boundary | Behavior |
| --- | --- |
| Credentials | Your address and a dedicated Apple app-specific password are stored in macOS Keychain. |
| Setup | `/usr/bin/security` reads both values directly in Apple Terminal. The setup script never receives them. |
| Network | The MCP server connects only to `imap.mail.me.com` on port `993` with TLS certificate validation. |
| Mail access | Mailboxes are selected read-only. The exposed MCP tools only report status, list folders, search metadata, and read bounded text bodies. |
| Attachments | MIME parts identified as attachments, named files, or inline files are skipped. |
| Dependencies | The runtime uses only the Python standard library and macOS system tools. There is no package install step, telemetry, or third-party service. |

Credentials never go to GitHub or into the plugin files. Message metadata and body text that you ask the plugin to retrieve are returned to Codex, so that content is handled according to the data controls for your Codex product and account.

Email is untrusted input. The included skill instructs Codex not to follow links, commands, or tool-use requests found inside messages.

## Requirements

- macOS
- Codex with plugin support
- Python 3 available at `/usr/bin/python3`
- An Apple Account with two-factor authentication
- iCloud Mail enabled
- A dedicated Apple app-specific password

Do not use your primary Apple Account password. Apple documents how to [create and revoke app-specific passwords](https://support.apple.com/en-us/102654).

## Install

Cloning locally makes the code easy to inspect before you grant it mailbox access:

```bash
git clone https://github.com/jacklandis29/codex-icloud-plugin.git
cd codex-icloud-plugin
codex plugin marketplace add .
codex plugin add icloud-mail@codex-icloud-plugin
open plugins/icloud-mail/setup_keychain.command
```

The setup window must be Apple Terminal, not Codex's embedded terminal. Two non-echoing Keychain prompts will ask for:

1. Your full iCloud Mail address.
2. The dedicated app-specific password created for this connector.

When macOS asks whether the MCP may access the Keychain items, choose **Allow Once** for the strictest policy.

Restart Codex or open a new task after installation. You can then ask:

- “Summarize important unread iCloud Mail.”
- “Find recent iCloud Mail from this sender.”
- “Search my iCloud inbox for this subject.”

## What the plugin can do

- Check whether credentials and IMAP connectivity work.
- List available mail folders.
- Search a bounded mailbox range by date, sender, subject, text, or unread state.
- Read selected message headers and bounded plain-text or HTML-derived body text.

## What it cannot do

- Send or draft mail.
- Delete, archive, move, flag, or mark messages.
- Open, save, or expose attachments.
- Follow links or execute instructions found in messages.
- Search every account or mailbox automatically.
- Run on non-macOS systems without replacing the Keychain integration.

## Remove access

Remove the two local Keychain items:

```bash
./plugins/icloud-mail/scripts/remove_keychain.sh
```

You should also revoke the dedicated app-specific password at [account.apple.com](https://account.apple.com/) if the machine or credential may have been compromised.

## Development

Run the security-focused unit tests:

```bash
python3 scripts/validate_release.py

python3 -m unittest discover \
  -s plugins/icloud-mail/scripts \
  -p 'test_*.py' \
  -v
```

Validate the JSON and shell entrypoints:

```bash
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool plugins/icloud-mail/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/icloud-mail/.mcp.json >/dev/null
zsh -n plugins/icloud-mail/setup_keychain.command
zsh -n plugins/icloud-mail/scripts/setup_keychain.sh
zsh -n plugins/icloud-mail/scripts/remove_keychain.sh
```

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes to the security boundary.

## Independence and trademarks

This project is independent and has not been authorized, sponsored, or otherwise approved by Apple Inc. Apple, iCloud, and iCloud Mail are trademarks of Apple Inc. The project uses its own cloud-and-envelope artwork and does not use Apple's logo.

## License

[MIT](LICENSE)
