# Security

This connector handles private mail and a credential capable of reading it. Security changes receive priority over feature work.

## Reporting a vulnerability

Do not put credentials, private messages, Keychain output, or authentication logs in a public issue.

Use GitHub's private vulnerability reporting for this repository when it is available. If it is not available, open a minimal issue asking the maintainer for a private reporting channel without including sensitive details.

If you believe an app-specific password was exposed:

1. Revoke it immediately at [account.apple.com](https://account.apple.com/).
2. Remove the local Keychain items with `plugins/icloud-mail/scripts/remove_keychain.sh`.
3. Generate a replacement only after the cause is understood.

## Intended security boundary

The connector is expected to:

- retrieve credentials only from macOS Keychain;
- connect only to `imap.mail.me.com:993` using validated TLS;
- use read-only IMAP mailbox selection;
- expose no mutating, SMTP, attachment, arbitrary-file, or arbitrary-network tool;
- bound search results and returned body text;
- treat all email content as untrusted data;
- avoid telemetry and runtime package dependencies.

A change that weakens one of these properties should be called out explicitly and reviewed as a security-sensitive change.

## Supported version

Security fixes are applied to the latest release on the `main` branch.
