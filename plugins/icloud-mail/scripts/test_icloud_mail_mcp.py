#!/usr/bin/python3
import importlib.util
import ast
import pathlib
import unittest
from unittest import mock


MODULE_PATH = pathlib.Path(__file__).with_name("icloud_mail_mcp.py")
SPEC = importlib.util.spec_from_file_location("icloud_mail_mcp", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ICloudMailMCPTests(unittest.TestCase):
    def test_initialize_and_tools_are_read_only(self):
        response = MODULE._handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        self.assertEqual(response["result"]["protocolVersion"], MODULE.PROTOCOL_VERSION)
        tools = MODULE._handle(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )["result"]["tools"]
        names = {tool["name"] for tool in tools}
        self.assertEqual(
            names,
            {
                "icloud_mail_status",
                "icloud_mail_list_folders",
                "icloud_mail_search",
                "icloud_mail_read",
            },
        )
        self.assertTrue(all(tool["annotations"]["readOnlyHint"] for tool in tools))
        self.assertTrue(all(not tool["annotations"]["destructiveHint"] for tool in tools))

    def test_network_destination_is_pinned(self):
        self.assertEqual(MODULE.IMAP_HOST, "imap.mail.me.com")
        self.assertEqual(MODULE.IMAP_PORT, 993)
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("smtp", source.lower())
        self.assertNotIn("import requests", source.lower())
        self.assertNotIn("import urllib", source.lower())
        self.assertNotIn("BODY.PEEK[]", source)

    def test_imports_and_imap_commands_stay_narrow(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(
            imported,
            {
                "__future__",
                "datetime",
                "email",
                "html",
                "imaplib",
                "json",
                "re",
                "ssl",
                "subprocess",
                "sys",
                "typing",
            },
        )
        for mutating_command in (
            "client.store(",
            "client.copy(",
            "client.expunge(",
            "client.append(",
            "client.delete(",
            "client.rename(",
        ):
            self.assertNotIn(mutating_command, source.lower())

    def test_search_rejects_control_characters(self):
        with self.assertRaises(MODULE.SafeError):
            MODULE._search_criteria({"subject": "hello\r\nUID EXPUNGE"})

    def test_search_builds_bounded_criteria(self):
        criteria = MODULE._search_criteria(
            {
                "since": "2026-07-01",
                "unread_only": True,
                "from_address": "person@example.com",
            }
        )
        self.assertEqual(criteria[:3], ["SINCE", "01-Jul-2026", "UNSEEN"])
        self.assertEqual(criteria[3], "FROM")
        self.assertEqual(criteria[4], '"person@example.com"')

    def test_search_encodes_non_ascii_criteria_as_utf8(self):
        charset, criteria = MODULE._search_arguments({"subject": "café"})
        self.assertEqual(charset, "UTF-8")
        self.assertEqual(criteria, [b"SUBJECT", b'"caf\xc3\xa9"'])

    def test_select_quotes_mailbox_names(self):
        client = mock.Mock()
        client.select.return_value = ("OK", [b"0"])
        MODULE._select_readonly(client, 'Sent "Team" Messages')
        client.select.assert_called_once_with(
            '"Sent \\"Team\\" Messages"', readonly=True
        )

    def test_search_returns_empty_result_when_imap_returns_none(self):
        client = mock.Mock()
        client.select.return_value = ("OK", [b"0"])
        client.uid.return_value = ("OK", [None])
        with mock.patch.object(MODULE, "_connect", return_value=client):
            result = MODULE.tool_search({"mailbox": "INBOX", "subject": "missing"})
        self.assertEqual(result["matches"], 0)
        self.assertEqual(result["returned"], 0)
        self.assertEqual(result["messages"], [])
        client.select.assert_called_once_with('"INBOX"', readonly=True)

    def test_read_rejects_non_numeric_uids_before_network(self):
        with self.assertRaises(MODULE.SafeError):
            MODULE.tool_read({"uids": ["1:*"]})

    def test_bodystructure_selects_text_and_skips_attachment_parts(self):
        metadata = [
            b'1 (UID 7 RFC822.SIZE 123 BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 50 2)("APPLICATION" "PDF" ("NAME" "x.pdf") NIL NIL "BASE64" 70 NIL ("ATTACHMENT" ("FILENAME" "x.pdf"))) "MIXED"))'
        ]
        size, structure = MODULE._fetch_metadata(metadata)
        self.assertEqual(size, 123)
        self.assertEqual(MODULE._text_part_ids(structure), ["1"])

    def test_bodystructure_skips_named_and_inline_text_attachments(self):
        named = [
            "TEXT",
            "PLAIN",
            ["CHARSET", "UTF-8", "NAME", "notes.txt"],
            None,
            None,
            "7BIT",
            50,
            2,
        ]
        inline = [
            "TEXT",
            "PLAIN",
            ["CHARSET", "UTF-8"],
            None,
            None,
            "7BIT",
            50,
            2,
            None,
            ["INLINE", ["FILENAME", "notes.txt"]],
        ]
        continued_name = [
            "TEXT",
            "PLAIN",
            ["CHARSET", "UTF-8", "NAME*0*", "utf-8''notes", "NAME*1*", ".txt"],
            None,
            None,
            "7BIT",
            50,
            2,
        ]
        self.assertEqual(MODULE._text_part_ids(named), [])
        self.assertEqual(MODULE._text_part_ids(inline), [])
        self.assertEqual(MODULE._text_part_ids(continued_name), [])

    def test_bodystructure_rejects_missing_size(self):
        with self.assertRaises(MODULE.SafeError):
            MODULE._fetch_metadata([b'1 (BODYSTRUCTURE ("TEXT" "PLAIN" NIL NIL NIL "7BIT" 10 1))'])

    def test_invalid_params_do_not_raise(self):
        initialize = MODULE._handle(
            {"jsonrpc": "2.0", "id": 9, "method": "initialize", "params": ["bad"]}
        )
        self.assertEqual(initialize["error"]["code"], -32602)
        tool_call = MODULE._handle(
            {"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": ["bad"]}
        )
        self.assertEqual(tool_call["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
