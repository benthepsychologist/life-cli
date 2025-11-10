# Copyright 2024 Life-CLI Contributors
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for sync command with state persistence."""

import json
from pathlib import Path

import yaml

from life.runner import CommandRunner
from life.state import StateManager


class TestSyncIntegration:
    """Integration tests for sync workflow."""

    def test_sync_incremental_workflow(self, temp_dir):
        """Test complete incremental sync workflow."""
        # Setup
        state_file = temp_dir / "state.json"
        output_file = temp_dir / "output.txt"

        state_manager = StateManager(str(state_file))
        runner = CommandRunner(dry_run=False)

        task_name = "test-task"
        incremental_field = "modified_on"

        # First run: No state, full sync
        last_value = state_manager.get_high_water_mark(task_name, incremental_field)
        assert last_value is None

        # Simulate sync command
        command = f"echo 'Full sync' > {output_file}"
        runner.run(command)

        # Save state after first run
        state_manager.set_high_water_mark(task_name, incremental_field, "2024-11-10T12:00:00Z")

        # Verify state persisted
        assert state_file.exists()
        with open(state_file) as f:
            state_data = json.load(f)
        assert task_name in state_data
        assert state_data[task_name][incremental_field] == "2024-11-10T12:00:00Z"

        # Second run: Use state for incremental sync
        last_value = state_manager.get_high_water_mark(task_name, incremental_field)
        assert last_value == "2024-11-10T12:00:00Z"

        # Simulate incremental sync with extra_args
        extra_args = f'--where "{incremental_field} gt {last_value}"'
        command = f"echo 'Incremental sync {extra_args}' >> {output_file}"
        runner.run(command)

        # Update state after second run
        state_manager.set_high_water_mark(task_name, incremental_field, "2024-11-10T15:00:00Z")

        # Verify updated state
        last_value = state_manager.get_high_water_mark(task_name, incremental_field)
        assert last_value == "2024-11-10T15:00:00Z"

    def test_sync_full_refresh_clears_state(self, temp_dir):
        """Test full refresh clears state and starts fresh."""
        state_file = temp_dir / "state.json"
        state_manager = StateManager(str(state_file))

        task_name = "test-task"
        incremental_field = "modified_on"

        # Set initial state
        state_manager.set_high_water_mark(task_name, incremental_field, "2024-11-10T12:00:00Z")
        assert state_manager.get_high_water_mark(task_name, incremental_field) is not None

        # Full refresh: clear state
        state_manager.clear_task(task_name)

        # Verify state cleared
        assert state_manager.get_high_water_mark(task_name, incremental_field) is None
        assert state_manager.get_last_run(task_name) is None

    def test_sync_with_variable_substitution(self, temp_dir):
        """Test sync command with variable substitution."""
        output_file = temp_dir / "output.txt"
        runner = CommandRunner(dry_run=False)

        # Variables for substitution
        variables = {
            "output": str(output_file),
            "extra_args": "--where 'modified_on gt 2024-11-10T00:00:00Z'",
            "workspace": str(temp_dir),
        }

        # Command with placeholders
        command = "echo 'Syncing to {output} with {extra_args}' > {output}"
        runner.run(command, variables)

        # Verify command executed with substituted values
        assert output_file.exists()
        content = output_file.read_text()
        assert "Syncing to" in content
        assert str(output_file) in content

    def test_multiple_tasks_independent_state(self, temp_dir):
        """Test multiple tasks maintain independent state."""
        state_file = temp_dir / "state.json"
        state_manager = StateManager(str(state_file))

        # Set state for multiple tasks
        state_manager.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")
        state_manager.set_high_water_mark("task2", "modified_on", "2024-11-09T10:00:00Z")
        state_manager.set_high_water_mark("task3", "created_on", "2024-11-08T08:00:00Z")

        # Verify each task has independent state
        assert state_manager.get_high_water_mark("task1", "modified_on") == "2024-11-10T12:00:00Z"
        assert state_manager.get_high_water_mark("task2", "modified_on") == "2024-11-09T10:00:00Z"
        assert state_manager.get_high_water_mark("task3", "created_on") == "2024-11-08T08:00:00Z"

        # Clear one task doesn't affect others
        state_manager.clear_task("task2")
        assert state_manager.get_high_water_mark("task1", "modified_on") == "2024-11-10T12:00:00Z"
        assert state_manager.get_high_water_mark("task2", "modified_on") is None
        assert state_manager.get_high_water_mark("task3", "created_on") == "2024-11-08T08:00:00Z"

    def test_state_survives_multiple_instances(self, temp_dir):
        """Test state persists across multiple StateManager instances."""
        state_file = temp_dir / "state.json"

        # Instance 1: Set state
        manager1 = StateManager(str(state_file))
        manager1.set_high_water_mark("task1", "modified_on", "2024-11-10T12:00:00Z")
        del manager1  # Explicitly delete

        # Instance 2: Read state
        manager2 = StateManager(str(state_file))
        mark = manager2.get_high_water_mark("task1", "modified_on")
        assert mark == "2024-11-10T12:00:00Z"

        # Instance 3: Update state
        manager3 = StateManager(str(state_file))
        manager3.set_high_water_mark("task1", "modified_on", "2024-11-10T15:00:00Z")
        del manager3

        # Instance 4: Verify update
        manager4 = StateManager(str(state_file))
        mark = manager4.get_high_water_mark("task1", "modified_on")
        assert mark == "2024-11-10T15:00:00Z"

    def test_sync_with_config_file(self, temp_dir):
        """Test sync using actual config file structure."""
        # Create config
        config_data = {
            "workspace": str(temp_dir),
            "sync": {
                "test-task": {
                    "command": "echo 'test {extra_args}' > {output}",
                    "description": "Test sync task",
                    "incremental_field": "modified_on",
                    "state_file": str(temp_dir / "state.json"),
                    "output": str(temp_dir / "output.txt"),
                }
            }
        }

        config_file = temp_dir / "life.yml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Load and verify config
        with open(config_file) as f:
            loaded_config = yaml.safe_load(f)

        assert "sync" in loaded_config
        assert "test-task" in loaded_config["sync"]

        task_config = loaded_config["sync"]["test-task"]

        # Simulate sync execution
        runner = CommandRunner(dry_run=False)
        state_manager = StateManager(task_config["state_file"])

        # Get state
        last_value = state_manager.get_high_water_mark(
            "test-task",
            task_config["incremental_field"]
        )

        # Build variables
        variables = {
            "output": task_config["output"],
            "extra_args": f'--where "{task_config["incremental_field"]} gt {last_value}"'
            if last_value else "",
        }

        # Run command
        runner.run(task_config["command"], variables)

        # Verify output
        assert Path(task_config["output"]).exists()
