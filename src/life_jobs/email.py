"""Email operations via MS Graph and Gmail.

Implementation rules enforced here (Rule 8):
- Never print
- Never read global config or environment (except Path.expanduser)
- Always return simple dicts
- Side effects: file IO, morch/gorch API calls only

Transport: Microsoft Graph API via morch.GraphClient or Gmail API via gorch.GmailClient
Auth: authctl account name passed as `account` parameter
Provider selection: "msgraph" (default) or "gmail" parameter
Scope: Mail.Send (msgraph) or Gmail send (gorch)
Attachments: Not supported in v1

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jinja2
import yaml
from morch import GraphClient


def _to_bool(value: Union[bool, str]) -> bool:
    """Convert string/bool to bool (for job runner string passing)."""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes")

# I/O declaration for static analysis and auditing
__io__ = {
    "reads": ["template", "recipients_file"],
    "writes": [],
    "external": ["msgraph.send_mail", "gmail.send_message"],
}


def _send_via_provider(
    provider: str,
    account: str,
    to: List[str],
    subject: str,
    body: str,
    is_html: bool,
) -> Dict[str, Any]:
    """Send email via specified provider.

    Args:
        provider: "gmail" or "msgraph" (default)
        account: authctl account name for authentication
        to: List of recipient email addresses
        subject: Email subject
        body: Email body text
        is_html: Whether body is HTML

    Returns:
        {sent: bool, to: list, subject: str, error: str|None}
    """
    try:
        if provider == "gmail":
            from gorch.gmail import GmailClient

            client = GmailClient.from_authctl(account)
            # GmailClient only accepts single recipient; loop for multiple
            for recipient in to:
                client.send_message(recipient, subject, body, html=is_html)
        else:  # msgraph (default)
            client = GraphClient.from_authctl(account, scopes=["Mail.Send"])
            message = {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",
                    "content": body,
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            }
            client.post("/me/sendMail", {"message": message})
        return {"sent": True, "to": to, "subject": subject, "error": None}
    except Exception as e:
        return {"sent": False, "to": to, "subject": subject, "error": str(e)}


def send(
    account: str,
    to: List[str],
    subject: str,
    body: str,
    is_html: bool = False,
    provider: str = "msgraph",
) -> Dict[str, Any]:
    """Send single email via MS Graph or Gmail.

    Reads: None
    External: msgraph.send_mail or gmail.send_message

    Args:
        account: authctl account name for authentication
        to: List of recipient email addresses
        subject: Email subject
        body: Email body text
        is_html: Whether body is HTML (default: False)
        provider: "msgraph" (default) or "gmail"

    Returns:
        {sent: bool, to: list, subject: str, error: str|None}
    """
    return _send_via_provider(provider, account, to, subject, body, is_html)


def send_templated(
    account: str,
    to: str,
    template: str,
    context: Optional[Dict[str, Any]] = None,
    provider: str = "msgraph",
) -> Dict[str, Any]:
    """Render Jinja template and send to one recipient.

    Reads: template file
    External: msgraph.send_mail or gmail.send_message
    Template format: YAML frontmatter (subject) + Jinja body

    Template file format:
    ```
    ---
    subject: "Your subject with {{ variables }}"
    ---
    Body content with {{ jinja }} {{ variables }}
    ```

    Args:
        account: authctl account name for authentication
        to: Single recipient email address
        template: Path to template file
        context: Dict of variables for Jinja rendering
        provider: "msgraph" (default) or "gmail"

    Returns:
        {sent: bool, to: str, subject: str, error: str|None}
    """
    template_path = Path(template).expanduser()

    if not template_path.exists():
        return {
            "sent": False,
            "to": to,
            "subject": None,
            "error": f"Template not found: {template}",
        }

    # Parse template with YAML frontmatter
    content = template_path.read_text()
    ctx = context or {}

    # Split frontmatter and body
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            body_template = parts[2].strip()
        else:
            return {
                "sent": False,
                "to": to,
                "subject": None,
                "error": "Invalid template format: missing closing ---",
            }
    else:
        return {
            "sent": False,
            "to": to,
            "subject": None,
            "error": "Template must have YAML frontmatter with subject",
        }

    # Render subject and body with Jinja
    try:
        env = jinja2.Environment(autoescape=False)
        subject_template = env.from_string(frontmatter.get("subject", ""))
        body_jinja = env.from_string(body_template)

        subject = subject_template.render(**ctx)
        body = body_jinja.render(**ctx)
    except jinja2.TemplateError as e:
        return {
            "sent": False,
            "to": to,
            "subject": None,
            "error": f"Template rendering error: {e}",
        }

    # Determine if HTML based on frontmatter or file extension
    is_html = frontmatter.get("html", template_path.suffix == ".html")

    # Send via provider
    result = _send_via_provider(provider, account, [to], subject, body, is_html)
    # Preserve return shape: to is a string, not a list
    return {
        "sent": result["sent"],
        "to": to,
        "subject": result["subject"],
        "error": result["error"],
    }


def batch_send(
    account: str,
    template: str,
    recipients_file: str,
    email_field: str = "email",
    dry_run: Union[bool, str] = False,
    provider: str = "msgraph",
) -> Dict[str, Any]:
    """Send templated emails to multiple recipients.

    Reads: template file, recipients_file (JSON)
    External: msgraph.send_mail or gmail.send_message (per recipient)
    Behavior: Continues on individual failures, reports all errors

    Args:
        account: authctl account name for authentication
        template: Path to template file
        recipients_file: Path to JSON file with recipient list
        email_field: Field name containing email address (default: "email")
        dry_run: If True, render but don't send (default: False)
        provider: "msgraph" (default) or "gmail"

    Returns:
        {sent: int, failed: int, errors: list, dry_run: bool, recipients: list}
    """
    dry_run = _to_bool(dry_run)
    template_path = Path(template).expanduser()
    recipients_path = Path(recipients_file).expanduser()

    if not template_path.exists():
        return {
            "sent": 0,
            "failed": 0,
            "errors": [f"Template not found: {template}"],
            "dry_run": dry_run,
            "recipients": [],
        }

    if not recipients_path.exists():
        return {
            "sent": 0,
            "failed": 0,
            "errors": [f"Recipients file not found: {recipients_file}"],
            "dry_run": dry_run,
            "recipients": [],
        }

    # Load recipients
    try:
        recipients = json.loads(recipients_path.read_text())
        if not isinstance(recipients, list):
            return {
                "sent": 0,
                "failed": 0,
                "errors": ["Recipients file must contain a JSON array"],
                "dry_run": dry_run,
                "recipients": [],
            }
    except json.JSONDecodeError as e:
        return {
            "sent": 0,
            "failed": 0,
            "errors": [f"Invalid JSON in recipients file: {e}"],
            "dry_run": dry_run,
            "recipients": [],
        }

    sent_count = 0
    failed_count = 0
    errors: List[str] = []
    processed: List[Dict[str, Any]] = []

    for recipient in recipients:
        email = recipient.get(email_field)
        if not email:
            errors.append(f"Missing {email_field} field in recipient: {recipient}")
            failed_count += 1
            continue

        if dry_run:
            # Just record what would be sent
            processed.append({"email": email, "status": "would_send"})
            sent_count += 1
            continue

        # Send using send_templated
        result = send_templated(
            account=account,
            to=email,
            template=template,
            context=recipient,
            provider=provider,
        )

        if result["sent"]:
            sent_count += 1
            processed.append({"email": email, "status": "sent", "subject": result["subject"]})
        else:
            failed_count += 1
            errors.append(f"{email}: {result['error']}")
            processed.append({"email": email, "status": "failed", "error": result["error"]})

    return {
        "sent": sent_count,
        "failed": failed_count,
        "errors": errors,
        "dry_run": dry_run,
        "recipients": processed,
    }
