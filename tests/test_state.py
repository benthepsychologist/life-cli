# Copyright 2024 Life-CLI Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for state.py module."""

import json
from datetime import datetime
from pathlib import Path

from life.state import StateManager


class TestStateManager:
    """Test state management functionality."""

    def test_init_creates_manager(self, state_file):
        """Test StateManager initialization."""
        manager = StateManager(str(state_file))
        # StateManager converts string to Path internally
        assert manager.state_file == Path(str(state_file))
        assert manager.state == {}

    def test_get_high_water_mark_missing(self, state_file):
        """Test getting high-water mark when none exists."""
        manager = StateManager(str(state_file))
        mark = manager.get_high_water_mark("task1", "modified_on")
        assert mark is None

    def test_set_and_get_high_water_mark(self, state_file):
        """Test setting and retrieving high-water mark."""
        manager = StateManager(str(state_file))
        manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")

        mark = manager.get_high_water_mark("task1", "modified_on")
        assert mark == "2024-11-10T12:00:00Z"

    def test_high_water_mark_persists(self, state_file):
        """Test high-water mark persists across instances."""
        # Set mark in first instance
        manager1 = StateManager(str(state_file))
        manager1.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")

        # Read mark in second instance
        manager2 = StateManager(str(state_file))
        mark = manager2.get_high_water_mark("task1", "modified_on")
        assert mark == "2024-11-10T12:00:00Z"

    def test_get_last_run_missing(self, state_file):
        """Test getting last run timestamp when none exists."""
        manager = StateManager(str(state_file))
        last_run = manager.get_last_run("task1")
        assert last_run is None

    def test_set_high_water_mark_updates_last_run(self, state_file):
        """Test that setting high-water mark also updates last_run."""
        manager = StateManager(str(state_file))
        if hasattr(datetime, 'UTC'):
            before = datetime.now(datetime.UTC)
        else:
            before = datetime.utcnow().replace(tzinfo=None)
        manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")
        if hasattr(datetime, 'UTC'):
            after = datetime.now(datetime.UTC)
        else:
            after = datetime.utcnow().replace(tzinfo=None)

        last_run_str = manager.get_last_run("task1")
        assert last_run_str is not None

        # Parse the timestamp and make it timezone naive for comparison
        last_run = datetime.fromisoformat(last_run_str.replace("Z", "+00:00")).replace(tzinfo=None)
        before_naive = before.replace(tzinfo=None) if hasattr(before, 'tzinfo') else before
        after_naive = after.replace(tzinfo=None) if hasattr(after, 'tzinfo') else after
        assert before_naive <= last_run <= after_naive

    def test_clear_task(self, state_file):
        """Test clearing task state."""
        manager = StateManager(str(state_file))
        manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")
        manager.set_high_water_mark("task1", "created_on", "2024-11-09T10:00:00Z")

        manager.clear_task("task1")

        assert manager.get_high_water_mark("task1", "modified_on") is None
        assert manager.get_high_water_mark("task1", "created_on") is None
        assert manager.get_last_run("task1") is None

    def test_clear_task_preserves_other_tasks(self, state_file):
        """Test clearing one task doesn't affect others."""
        manager = StateManager(str(state_file))
        manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")
        manager.set_high_water_mark("task2", "modified_on", "2024-11-09T10:00:00Z")

        manager.clear_task("task1")

        assert manager.get_high_water_mark("task1", "modified_on") is None
        assert manager.get_high_water_mark("task2", "modified_on") == "2024-11-09T10:00:00Z"

    def test_get_all_state(self, state_file):
        """Test retrieving all state."""
        manager = StateManager(str(state_file))
        manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")
        manager.set_high_water_mark("task2", "created_on", "2024-11-09T10:00:00Z")

        state = manager.get_all_state()
        assert "task1" in state
        assert "task2" in state
        assert state["task1"]["modified_on"] == "2024-11-10T12:00:00Z"
        assert state["task2"]["created_on"] == "2024-11-09T10:00:00Z"

    def test_handles_corrupt_state_file(self, state_file):
        """Test graceful handling of corrupt JSON."""
        # Write invalid JSON
        with open(state_file, "w") as f:
            f.write("{ invalid json content")

        # Should not crash, returns empty state
        manager = StateManager(str(state_file))
        assert manager.state == {}

    def test_creates_parent_directories(self, temp_dir):
        """Test state file creation creates parent directories."""
        nested_state = temp_dir / "nested" / "dir" / "state.json"
        manager = StateManager(str(nested_state))
        manager.set_high_water_mark("task1", "field1", "value1")

        assert nested_state.exists()
        assert nested_state.parent.exists()

    def test_multiple_fields_per_task(self, state_file):
        """Test tracking multiple high-water marks per task."""
        manager = StateManager(str(state_file))
        manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")
        manager.set_high_water_mark("task1", "created_on", "2024-11-09T10:00:00Z")
        manager.set_high_water_mark("task1", "id", "12345")

        assert manager.get_high_water_mark("task1", "modified_on") == "2024-11-10T12:00:00Z"
        assert manager.get_high_water_mark("task1", "created_on") == "2024-11-09T10:00:00Z"
        assert manager.get_high_water_mark("task1", "id") == "12345"

    def test_state_file_format(self, state_file):
        """Test state file is valid JSON with expected structure."""
        manager = StateManager(str(state_file))
        manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")

        # Read raw JSON
        with open(state_file) as f:
            data = json.load(f)

        assert "task1" in data
        assert "modified_on" in data["task1"]
        assert "last_run" in data["task1"]
        assert data["task1"]["modified_on"] == "2024-11-10T12:00:00Z"
