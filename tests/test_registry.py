# Copyright 2025 Ben Mensi
# SPDX-License-Identifier: Apache-2.0

"""Tests for registry.py module."""


from life.registry import (
    TOOL_REGISTRY,
    ToolInfo,
    get_tool_info,
    is_tool_installed,
    list_tools,
    register_tool,
)


class TestToolInfo:
    """Test ToolInfo dataclass."""

    def test_tool_info_creation(self):
        """Test creating ToolInfo instance."""
        tool = ToolInfo(
            name="test-tool",
            binary="test",
            description="A test tool",
            install_hint="pip install test-tool",
        )

        assert tool.name == "test-tool"
        assert tool.binary == "test"
        assert tool.description == "A test tool"
        assert tool.install_hint == "pip install test-tool"


class TestIsToolInstalled:
    """Test tool installation checking."""

    def test_known_tool_installed(self):
        """Test checking if a known tool is installed."""
        # Use a common tool that should exist
        result = is_tool_installed("msg")
        # Result depends on whether msg is actually installed
        assert isinstance(result, bool)

    def test_unknown_tool_installed(self):
        """Test checking if an unknown tool is installed."""
        # Python should be available on PATH
        result = is_tool_installed("python")
        assert isinstance(result, bool)

    def test_nonexistent_tool(self):
        """Test checking a tool that doesn't exist."""
        result = is_tool_installed("definitely-not-a-real-tool-xyz123")
        assert result is False


class TestGetToolInfo:
    """Test getting tool metadata."""

    def test_get_registered_tool(self):
        """Test getting info for a registered tool."""
        info = get_tool_info("msg")
        assert info is not None
        assert info.name == "msg"
        assert info.binary == "msg"
        assert "Microsoft Graph" in info.description

    def test_get_unregistered_tool(self):
        """Test getting info for an unregistered tool."""
        info = get_tool_info("unknown-tool")
        assert info is None

    def test_all_builtin_tools(self):
        """Test all built-in tools have proper metadata."""
        for tool_name in ["msg", "gws", "cal", "dataverse"]:
            info = get_tool_info(tool_name)
            assert info is not None
            assert info.name == tool_name
            assert info.binary
            assert info.description
            assert info.install_hint


class TestListTools:
    """Test listing all tools."""

    def test_list_tools_returns_list(self):
        """Test that list_tools returns a list."""
        tools = list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_list_tools_contains_builtins(self):
        """Test that list_tools includes built-in tools."""
        tools = list_tools()
        tool_names = [t.name for t in tools]

        assert "msg" in tool_names
        assert "gws" in tool_names
        assert "cal" in tool_names
        assert "dataverse" in tool_names

    def test_list_tools_returns_tool_info(self):
        """Test that list_tools returns ToolInfo objects."""
        tools = list_tools()
        for tool in tools:
            assert isinstance(tool, ToolInfo)
            assert tool.name
            assert tool.binary
            assert tool.description
            assert tool.install_hint


class TestRegisterTool:
    """Test tool registration."""

    def test_register_new_tool(self):
        """Test registering a new tool."""
        original_count = len(TOOL_REGISTRY)

        new_tool = ToolInfo(
            name="custom-tool",
            binary="custom",
            description="A custom tool",
            install_hint="Install custom-tool",
        )

        register_tool(new_tool)

        assert len(TOOL_REGISTRY) == original_count + 1
        assert "custom-tool" in TOOL_REGISTRY
        assert TOOL_REGISTRY["custom-tool"] == new_tool

        # Cleanup
        del TOOL_REGISTRY["custom-tool"]

    def test_register_overrides_existing(self):
        """Test that registering overwrites existing tool."""
        # Get original msg tool info
        original = get_tool_info("msg")

        # Register a modified version
        modified = ToolInfo(
            name="msg",
            binary="msg-v2",
            description="Modified msg tool",
            install_hint="Install modified msg",
        )

        register_tool(modified)

        # Check it was updated
        current = get_tool_info("msg")
        assert current.binary == "msg-v2"
        assert current.description == "Modified msg tool"

        # Restore original
        register_tool(original)
