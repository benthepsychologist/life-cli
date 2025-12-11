"""Tests for email command template resolution.

Tests the _resolve_template_path() function which resolves template names
to full paths in the command layer (before passing to processors).
"""

from pathlib import Path

from life.commands.email import _resolve_template_path


class TestResolveTemplatePath:
    """Tests for _resolve_template_path()."""

    def test_absolute_path_unchanged(self):
        """Absolute paths should pass through unchanged."""
        result = _resolve_template_path("/abs/path/template.md", {})
        assert result == "/abs/path/template.md"

    def test_home_path_expanded(self):
        """Paths with ~ should be expanded."""
        result = _resolve_template_path("~/foo/bar.md", {})
        expected = str(Path.home() / "foo" / "bar.md")
        assert result == expected

    def test_tilde_prefix_treated_as_path(self):
        """Tilde at start (like ~/path) should be treated as path, not template name."""
        # ~/ is a common pattern for home directory paths
        result = _resolve_template_path("~/templates/custom.md", {})
        expected = str(Path.home() / "templates" / "custom.md")
        assert result == expected
        # Should NOT look up in default templates dir
        assert ".life/templates/email" not in result

    def test_relative_path_with_slash_unchanged(self):
        """Paths containing / should pass through (with ~ expansion if needed)."""
        result = _resolve_template_path("subdir/template.md", {})
        assert result == "subdir/template.md"

    def test_template_name_resolves_to_default_dir(self):
        """Template name without path should resolve to default templates directory."""
        result = _resolve_template_path("reminder", {})
        expected = str(Path.home() / ".life" / "templates" / "email" / "reminder.md")
        assert result == expected

    def test_template_name_with_md_extension(self):
        """Template name with .md extension should use it directly."""
        result = _resolve_template_path("reminder.md", {})
        expected = str(Path.home() / ".life" / "templates" / "email" / "reminder.md")
        assert result == expected

    def test_template_name_with_html_extension(self):
        """Template name with .html extension should use it directly."""
        result = _resolve_template_path("reminder.html", {})
        expected = str(Path.home() / ".life" / "templates" / "email" / "reminder.html")
        assert result == expected

    def test_custom_templates_dir_from_config(self):
        """Config email.templates_dir should override default location."""
        config = {"email": {"templates_dir": "/custom/templates"}}
        result = _resolve_template_path("reminder", config)
        assert result == "/custom/templates/reminder.md"

    def test_custom_templates_dir_with_tilde(self):
        """Config templates_dir with ~ should be expanded."""
        config = {"email": {"templates_dir": "~/my-templates"}}
        result = _resolve_template_path("reminder", config)
        expected = str(Path.home() / "my-templates" / "reminder.md")
        assert result == expected

    def test_md_takes_precedence_over_html(self, tmp_path):
        """When both .md and .html exist, .md should win."""
        # Create both files
        (tmp_path / "reminder.md").write_text("md content")
        (tmp_path / "reminder.html").write_text("html content")

        config = {"email": {"templates_dir": str(tmp_path)}}
        result = _resolve_template_path("reminder", config)

        assert result == str(tmp_path / "reminder.md")

    def test_html_used_when_md_missing(self, tmp_path):
        """When only .html exists, it should be used."""
        (tmp_path / "reminder.html").write_text("html content")

        config = {"email": {"templates_dir": str(tmp_path)}}
        result = _resolve_template_path("reminder", config)

        assert result == str(tmp_path / "reminder.html")

    def test_defaults_to_md_when_neither_exists(self, tmp_path):
        """When neither .md nor .html exists, default to .md path."""
        config = {"email": {"templates_dir": str(tmp_path)}}
        result = _resolve_template_path("nonexistent", config)

        # Should return .md path (processor will give clear error)
        assert result == str(tmp_path / "nonexistent.md")

    def test_empty_config_uses_defaults(self):
        """Empty config should use default templates directory."""
        result = _resolve_template_path("reminder", {})
        expected = str(Path.home() / ".life" / "templates" / "email" / "reminder.md")
        assert result == expected

    def test_backslash_path_treated_as_path(self):
        """Paths with backslash (Windows-style) should be treated as paths."""
        result = _resolve_template_path("subdir\\template.md", {})
        # Should not look up in templates directory
        assert "templates/email" not in result
