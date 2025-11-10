---
version: "0.1"
tier: C
title: Config Management Spec
owner: benthepsychologist
goal: Implement Config Management Spec
labels: []
orchestrator_contract: "standard"
repo:
  working_branch: "feat/config-management-spec"
---

# Config Management Spec

## Objective

Implement a config management system that validates YAML configuration, checks for tool availability, and provides semantic feedback to users about their task definitions.

## Acceptance Criteria

- [ ] CI green (lint + unit)
- [ ] No protected paths modified
- [ ] 70% test coverage achieved
- [ ] Tool registry supports msg, gws, cal, dataverse, and extensibility for custom tools
- [ ] `life config validate` performs full semantic validation
- [ ] `life config check` verifies all referenced tools are installed
- [ ] `life config list` displays tasks with tool availability status

## Context

### Background

Life-CLI currently validates YAML structure but doesn't verify that referenced CLI tools actually exist on the system. Users discover tool availability issues at runtime, which is a poor developer experience. Additionally, the config system could benefit from:

1. **Tool Registry**: A central registry of known CLI tools (msg, gws, cal, dataverse) with validation patterns
2. **Semantic Validation**: Beyond YAML structure, validate that commands reference installed tools
3. **Config Management CLI**: Interactive commands to inspect, validate, and troubleshoot configurations
4. **Extensibility**: Support for user-defined tools beyond the built-in registry

This work creates the foundation for a self-documenting, validated config system while maintaining Life-CLI's lightweight orchestration philosophy.

### Constraints

- Must remain lightweight (no heavy validation dependencies)
- Tool registry should be simple data structures (no external registry service)
- Validation should be helpful, not prescriptive (warnings, not hard failures)
- Maintain backward compatibility with existing life.yml files

## Plan

### Phase 1: Core Config Management (IMPLEMENT NOW)

**Goal**: Provide tool validation and config inspection capabilities

**Files to Create:**
- `src/life/registry.py` - Tool registry with known CLI tools
- `src/life/config_manager.py` - Semantic validation utilities
- `src/life/commands/config.py` - Config management subcommands
- `tests/test_registry.py` - Registry tests
- `tests/test_config_manager.py` - Config manager tests
- `tests/test_config_command.py` - Config command tests

**Implementation Steps:**

#### Step 1.1: Tool Registry [G0: Plan Approval]

**Prompt:** Create `src/life/registry.py` with a tool registry supporting:
- Known tools: msg, gws, cal, dataverse
- Tool metadata: binary name, description, install hints
- `is_tool_installed(tool_name)` - Check if tool binary exists on PATH
- `get_tool_info(tool_name)` - Get tool metadata
- `list_tools()` - List all registered tools

**Outputs:**
- `src/life/registry.py`
- `tests/test_registry.py`

#### Step 1.2: Config Manager [G0: Plan Approval]

**Prompt:** Create `src/life/config_manager.py` with semantic validation:
- `extract_tools_from_config(config)` - Parse commands to identify tools used
- `validate_tools(config)` - Check if all referenced tools are installed
- `get_task_summary(config)` - Generate task inventory with tool info
- Integration with existing `validation.py` for structure validation

**Outputs:**
- `src/life/config_manager.py`
- `tests/test_config_manager.py`

#### Step 1.3: Config Command [G1: Code Readiness]

**Prompt:** Create `src/life/commands/config.py` with subcommands:
- `life config validate` - Full validation (structure + tools)
- `life config check` - Tool availability check only
- `life config list` - List tasks with tool status
- Wire up config command in main CLI app

**Commands:**
```bash
ruff check .
pytest tests/test_config*.py -v
```

**Outputs:**
- `src/life/commands/config.py`
- `tests/test_config_command.py`

#### Step 1.4: Integration & Testing [G2: Pre-Release]

**Prompt:** Run full test suite and verify Phase 1 implementation

**Commands:**
```bash
pytest -v
ruff check .
```

**Outputs:**
- All tests passing
- Linting clean

### Phase 2: Interactive Config (DOCUMENT ONLY - Future Work)

**Goal**: Enable interactive task creation and management

**Future Capabilities:**
- `life config add <command>` - Interactive task creation wizard
  - Prompt for task name, description, command
  - Detect tool from command string
  - Optionally configure incremental sync, date ranges, variables
  - Write back to life.yml with proper YAML formatting

- `life config init [--template <name>]` - Bootstrap new config file
  - Generate life.yml from templates (basic, dataverse, calendar, etc.)
  - Include example tasks for common workflows

- `life config edit <task>` - Interactive task editor
  - Load existing task config
  - Prompt for field updates
  - Preserve comments and formatting where possible

**Design Notes:**
- Use typer prompts for interactive input
- Preserve YAML comments using `ruamel.yaml` instead of `pyyaml`
- Validate inputs before writing back to config
- Support dry-run mode to preview changes

### Phase 3: Registry Expansion (DOCUMENT ONLY - Future Work)

**Goal**: Support custom tools and registry extensibility

**Future Capabilities:**
- External registry files (`~/.life/tools.yml`)
  - User-defined tool entries
  - Override built-in tool metadata
  - Share tool registries across teams

- Tool version requirements
  - Specify minimum versions: `gws >= 2.1.0`
  - Version detection strategies (--version, version subcommand)
  - Warning when tool version is outdated

- Registry sources
  - Built-in registry (shipped with life-cli)
  - User registry (~/.life/tools.yml)
  - Project registry (.life-tools.yml in repo)
  - Priority order: project > user > built-in

**Design Notes:**
- Keep registry format simple (YAML or JSON)
- Version checking is best-effort (warn, don't block)
- Registry merging should be predictable and documented

## Models & Tools

**Tools:** bash, pytest, ruff

**Models:** (to be filled by defaults)

## Repository

**Branch:** `feat/config-management-spec`

**Merge Strategy:** squash