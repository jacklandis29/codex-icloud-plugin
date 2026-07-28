#!/usr/bin/env python3
"""Validate the public repository without installing third-party packages."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "icloud-mail"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
MCP_PATH = PLUGIN_ROOT / ".mcp.json"

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require_string(mapping: dict[str, Any], field: str, context: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f"{context}.{field} must be a non-empty string")
    return value


def validate_asset_path(value: str, field: str) -> None:
    if not value.startswith("./"):
        fail(f"interface.{field} must begin with ./")
    resolved = (PLUGIN_ROOT / value[2:]).resolve()
    try:
        resolved.relative_to(PLUGIN_ROOT.resolve())
    except ValueError:
        fail(f"interface.{field} escapes the plugin root")
    if not resolved.is_file():
        fail(f"interface.{field} does not exist: {value}")


def validate_manifest() -> None:
    manifest = load_json(MANIFEST_PATH)
    if require_string(manifest, "name", "plugin") != "icloud-mail":
        fail("plugin.name must be icloud-mail")
    version = require_string(manifest, "version", "plugin")
    if not SEMVER.fullmatch(version):
        fail(f"plugin.version is not strict semver: {version}")
    require_string(manifest, "description", "plugin")

    author = manifest.get("author")
    if not isinstance(author, dict):
        fail("plugin.author must be an object")
    require_string(author, "name", "plugin.author")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        fail("plugin.interface must be an object")
    for field in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
    ):
        require_string(interface, field, "plugin.interface")
    for field in ("composerIcon", "logo", "logoDark"):
        validate_asset_path(require_string(interface, field, "plugin.interface"), field)

    if manifest.get("mcpServers") != "./.mcp.json":
        fail("plugin.mcpServers must point to ./.mcp.json")
    if manifest.get("skills") != "./skills/":
        fail("plugin.skills must point to ./skills/")
    if not MCP_PATH.is_file():
        fail("plugin .mcp.json is missing")


def validate_marketplace() -> None:
    marketplace = load_json(MARKETPLACE_PATH)
    if marketplace.get("name") != "codex-icloud-plugin":
        fail("marketplace.name must be codex-icloud-plugin")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail("marketplace.plugins must contain exactly one plugin")
    entry = plugins[0]
    if not isinstance(entry, dict) or entry.get("name") != "icloud-mail":
        fail("marketplace plugin entry must be icloud-mail")
    if entry.get("source") != {
        "source": "local",
        "path": "./plugins/icloud-mail",
    }:
        fail("marketplace source must point to ./plugins/icloud-mail")
    if entry.get("policy") != {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }:
        fail("marketplace policy is incomplete or unexpected")
    if entry.get("category") != "Productivity":
        fail("marketplace category must be Productivity")


def validate_public_files() -> None:
    forbidden_names = {
        ".DS_Store",
        ".env",
    }
    forbidden_suffixes = {
        ".key",
        ".log",
        ".p12",
        ".pem",
        ".pyc",
        ".sqlite",
        ".sqlite3",
    }
    sensitive_patterns = {
        "iCloud email literal": re.compile(
            r"[A-Z0-9._%+-]+@(icloud|me|mac)\.com", re.IGNORECASE
        ),
        "Apple app-password-shaped literal": re.compile(
            r"\b[a-z]{4}(?:-[a-z]{4}){3}\b"
        ),
        "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
        "local user path": re.compile(r"/Users/[^/\s]+/"),
        "unfinished placeholder": re.compile(r"\[TODO:"),
    }

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        if "__pycache__" in relative.parts:
            fail(f"generated cache directory is present: {relative}")
        if path.name in forbidden_names or path.suffix.lower() in forbidden_suffixes:
            fail(f"generated or private artifact is present: {relative}")
        if relative == Path("scripts/validate_release.py"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in sensitive_patterns.items():
            if pattern.search(text):
                fail(f"{label} found in {relative}")


def validate_keychain_namespace() -> None:
    address_service = "io.github.jacklandis29.codex-icloud-plugin.address"
    password_service = "io.github.jacklandis29.codex-icloud-plugin.app-password"
    paths = (
        PLUGIN_ROOT / "scripts" / "icloud_mail_mcp.py",
        PLUGIN_ROOT / "scripts" / "setup_keychain.sh",
        PLUGIN_ROOT / "scripts" / "remove_keychain.sh",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if address_service not in text or password_service not in text:
            fail(f"Keychain service names are inconsistent in {path.relative_to(ROOT)}")


def main() -> int:
    try:
        validate_manifest()
        validate_marketplace()
        validate_public_files()
        validate_keychain_namespace()
    except ValueError as exc:
        print(f"release validation failed: {exc}", file=sys.stderr)
        return 1
    print("release validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
