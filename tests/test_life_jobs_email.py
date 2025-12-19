"""Tests for life_jobs.email module.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

from unittest.mock import MagicMock, patch

from life_jobs import email


class TestSendViaProviderMsgraph:
    """Tests for _send_via_provider with msgraph provider."""

    @patch("life_jobs.email.GraphClient")
    def test_send_via_msgraph(self, mock_client_class):
        """Should send via MS Graph when provider is msgraph."""
        mock_client = MagicMock()
        mock_client_class.from_authctl.return_value = mock_client

        result = email._send_via_provider(
            provider="msgraph",
            account="test-account",
            to=["user@example.com"],
            subject="Test Subject",
            body="Test body",
            is_html=False,
        )

        mock_client_class.from_authctl.assert_called_once_with(
            "test-account", scopes=["Mail.Send"]
        )
        mock_client.post.assert_called_once()

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/me/sendMail"
        message = call_args[0][1]["message"]
        assert message["subject"] == "Test Subject"
        assert message["body"]["contentType"] == "Text"
        assert message["body"]["content"] == "Test body"

        assert result["sent"] is True
        assert result["to"] == ["user@example.com"]
        assert result["subject"] == "Test Subject"
        assert result["error"] is None

    @patch("life_jobs.email.GraphClient")
    def test_send_via_msgraph_html(self, mock_client_class):
        """Should send HTML email via MS Graph."""
        mock_client = MagicMock()
        mock_client_class.from_authctl.return_value = mock_client

        email._send_via_provider(
            provider="msgraph",
            account="test",
            to=["user@example.com"],
            subject="Test",
            body="<h1>HTML</h1>",
            is_html=True,
        )

        call_args = mock_client.post.call_args
        message = call_args[0][1]["message"]
        assert message["body"]["contentType"] == "HTML"

    @patch("life_jobs.email.GraphClient")
    def test_send_via_msgraph_multiple_recipients(self, mock_client_class):
        """Should support multiple recipients in single call for msgraph."""
        mock_client = MagicMock()
        mock_client_class.from_authctl.return_value = mock_client

        email._send_via_provider(
            provider="msgraph",
            account="test",
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            body="Test",
            is_html=False,
        )

        call_args = mock_client.post.call_args
        message = call_args[0][1]["message"]
        assert len(message["toRecipients"]) == 2

    @patch("life_jobs.email.GraphClient")
    def test_send_via_msgraph_error(self, mock_client_class):
        """Should return error dict on failure."""
        mock_client_class.from_authctl.side_effect = Exception("Auth failed")

        result = email._send_via_provider(
            provider="msgraph",
            account="test",
            to=["user@example.com"],
            subject="Test",
            body="Test",
            is_html=False,
        )

        assert result["sent"] is False
        assert result["error"] == "Auth failed"


class TestSendViaProviderGmail:
    """Tests for _send_via_provider with gmail provider."""

    @patch("gorch.gmail.GmailClient")
    def test_send_via_gmail(self, mock_client_class):
        """Should send via Gmail when provider is gmail."""
        mock_client = MagicMock()
        mock_client_class.from_authctl.return_value = mock_client

        result = email._send_via_provider(
            provider="gmail",
            account="gmail-account",
            to=["user@example.com"],
            subject="Test Subject",
            body="Test body",
            is_html=False,
        )

        mock_client_class.from_authctl.assert_called_once_with("gmail-account")
        mock_client.send_message.assert_called_once_with(
            "user@example.com", "Test Subject", "Test body", html=False
        )

        assert result["sent"] is True
        assert result["to"] == ["user@example.com"]
        assert result["subject"] == "Test Subject"
        assert result["error"] is None

    @patch("gorch.gmail.GmailClient")
    def test_send_via_gmail_multiple_recipients(self, mock_client_class):
        """Should loop and send one message per recipient for gmail."""
        mock_client = MagicMock()
        mock_client_class.from_authctl.return_value = mock_client

        email._send_via_provider(
            provider="gmail",
            account="gmail-account",
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            body="Test",
            is_html=False,
        )

        assert mock_client.send_message.call_count == 2
        calls = mock_client.send_message.call_args_list
        assert calls[0][0][0] == "user1@example.com"
        assert calls[1][0][0] == "user2@example.com"

    @patch("gorch.gmail.GmailClient")
    def test_send_via_gmail_html(self, mock_client_class):
        """Should send HTML email via Gmail."""
        mock_client = MagicMock()
        mock_client_class.from_authctl.return_value = mock_client

        email._send_via_provider(
            provider="gmail",
            account="test",
            to=["user@example.com"],
            subject="Test",
            body="<h1>HTML</h1>",
            is_html=True,
        )

        mock_client.send_message.assert_called_once_with(
            "user@example.com", "Test", "<h1>HTML</h1>", html=True
        )

    @patch("gorch.gmail.GmailClient")
    def test_send_via_gmail_error(self, mock_client_class):
        """Should return error dict on failure."""
        mock_client_class.from_authctl.side_effect = Exception("Gmail auth failed")

        result = email._send_via_provider(
            provider="gmail",
            account="test",
            to=["user@example.com"],
            subject="Test",
            body="Test",
            is_html=False,
        )

        assert result["sent"] is False
        assert result["error"] == "Gmail auth failed"


class TestSend:
    """Tests for send() function."""

    @patch("life_jobs.email._send_via_provider")
    def test_send_passes_provider(self, mock_send_via_provider):
        """Should pass provider to _send_via_provider."""
        mock_send_via_provider.return_value = {
            "sent": True,
            "to": ["user@example.com"],
            "subject": "Test",
            "error": None,
        }

        result = email.send(
            account="test",
            to=["user@example.com"],
            subject="Test Subject",
            body="Test body",
            is_html=False,
            provider="gmail",
        )

        mock_send_via_provider.assert_called_once_with(
            "gmail",
            "test",
            ["user@example.com"],
            "Test Subject",
            "Test body",
            False,
        )

        assert result["sent"] is True

    @patch("life_jobs.email._send_via_provider")
    def test_send_defaults_to_msgraph(self, mock_send_via_provider):
        """Should default to msgraph provider."""
        mock_send_via_provider.return_value = {
            "sent": True,
            "to": ["user@example.com"],
            "subject": "Test",
            "error": None,
        }

        email.send(
            account="test",
            to=["user@example.com"],
            subject="Test",
            body="Test",
        )

        call_args = mock_send_via_provider.call_args
        assert call_args[0][0] == "msgraph"


class TestSendTemplated:
    """Tests for send_templated() function."""

    @patch("life_jobs.email._send_via_provider")
    def test_send_templated_passes_provider(self, mock_send_via_provider, tmp_path):
        """Should pass provider to _send_via_provider."""
        mock_send_via_provider.return_value = {
            "sent": True,
            "to": ["user@example.com"],
            "subject": "Test Subject",
            "error": None,
        }

        template = tmp_path / "template.md"
        template.write_text("---\nsubject: Test Subject\n---\nBody content")

        result = email.send_templated(
            account="test",
            to="user@example.com",
            template=str(template),
            provider="gmail",
        )

        mock_send_via_provider.assert_called_once()
        call_args = mock_send_via_provider.call_args
        assert call_args[0][0] == "gmail"

        # Return shape should have to as string (not list)
        assert result["to"] == "user@example.com"
        assert result["sent"] is True

    @patch("life_jobs.email._send_via_provider")
    def test_send_templated_defaults_to_msgraph(self, mock_send_via_provider, tmp_path):
        """Should default to msgraph provider."""
        mock_send_via_provider.return_value = {
            "sent": True,
            "to": ["user@example.com"],
            "subject": "Test",
            "error": None,
        }

        template = tmp_path / "template.md"
        template.write_text("---\nsubject: Test\n---\nBody")

        email.send_templated(
            account="test",
            to="user@example.com",
            template=str(template),
        )

        call_args = mock_send_via_provider.call_args
        assert call_args[0][0] == "msgraph"


class TestBatchSend:
    """Tests for batch_send() function."""

    @patch("life_jobs.email.send_templated")
    def test_batch_send_passes_provider(self, mock_send_templated, tmp_path):
        """Should pass provider to send_templated for each recipient."""
        mock_send_templated.return_value = {
            "sent": True,
            "to": "user@example.com",
            "subject": "Test",
            "error": None,
        }

        template = tmp_path / "template.md"
        template.write_text("---\nsubject: Test\n---\nBody")

        recipients = tmp_path / "recipients.json"
        recipients.write_text('[{"email": "user1@example.com"}, {"email": "user2@example.com"}]')

        email.batch_send(
            account="test",
            template=str(template),
            recipients_file=str(recipients),
            provider="gmail",
        )

        assert mock_send_templated.call_count == 2
        for call in mock_send_templated.call_args_list:
            assert call[1]["provider"] == "gmail"

    @patch("life_jobs.email.send_templated")
    def test_batch_send_defaults_to_msgraph(self, mock_send_templated, tmp_path):
        """Should default to msgraph provider."""
        mock_send_templated.return_value = {
            "sent": True,
            "to": "user@example.com",
            "subject": "Test",
            "error": None,
        }

        template = tmp_path / "template.md"
        template.write_text("---\nsubject: Test\n---\nBody")

        recipients = tmp_path / "recipients.json"
        recipients.write_text('[{"email": "user@example.com"}]')

        email.batch_send(
            account="test",
            template=str(template),
            recipients_file=str(recipients),
        )

        call_args = mock_send_templated.call_args
        assert call_args[1]["provider"] == "msgraph"
