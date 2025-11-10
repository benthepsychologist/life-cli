---
version: "0.1"
tier: C
title: Life-CLI - Lightweight CLI Orchestrator for Personal Data Pipelines
owner: benthepsychologist
goal: Open-source a stateful, YAML-driven CLI orchestrator that wraps specialized data tools
labels: [cli, orchestration, data-pipeline, python, typer]
orchestrator_contract: "standard"
repo:
  working_branch: "main"
---

# Life-CLI - Lightweight CLI Orchestrator for Personal Data Pipelines

## Objective

> Create a lightweight, stateful, CLI-first orchestrator for personal data pipelines that wraps specialized CLI tools (dv, msg, cal, gws, xl, etc.) with YAML configuration, incremental sync state tracking, and workflow management.

## Acceptance Criteria

- [ ] Core CLI structure implemented with typer (sync, merge, process, status commands)
- [ ] YAML config loader supporting command templates with variable injection
- [ ] Incremental state tracking with `{extra_args}` pattern for cursor-based syncing
- [ ] Multi-command execution support (commands array)
- [ ] Apache 2.0 LICENSE file in repository
- [ ] README.md with project overview, installation, and basic usage examples
- [ ] Example life.yml configuration demonstrating key features
- [ ] Basic error handling and logging for command execution

## Context

### Background

Life-CLI emerged from orchestrating multiple specialized data tools (Dataverse queries, email syncing, calendar syncing, Google Sheets operations, payment processing, assessment scoring) for a clinical practice management workflow. Initially considered using Airflow, Meltano, or Taskfile, but discovered a gap in the tooling landscape:

- **Bash scripts**: No structure, no state tracking, grows unmaintainable
- **Make/Taskfile**: No incremental state, not designed for data pipelines
- **Airflow/Prefect**: Scheduler-first, web UI overhead, too heavyweight for on-demand CLI workflows
- **Meltano**: Singer-protocol only, data warehouse focused, not generalized for any CLI tool

Life-CLI fills the gap: a lightweight orchestrator that provides stateful syncing and workflow management for ANY CLI tool, triggered on-demand (e.g., from Neovim), without scheduler or web UI overhead.

### Constraints

- Must remain lightweight (minimal dependencies: typer, pyyaml, standard library)
- No protected paths (this is a greenfield project)
- Keep orchestration separate from business logic (life-cli calls tools, doesn't implement them)
- Support both single commands and multi-step workflows
- YAML config must be human-readable and easy to modify

## Plan

### Step 1: Project Scaffolding [G0: Structure Approval]

**Prompt:**

Create the basic project structure for life-cli:
1. Set up Python package structure with `src/life/` directory
2. Create `pyproject.toml` with dependencies (typer, pyyaml)
3. Add Apache 2.0 LICENSE file
4. Create initial `.gitignore` for Python projects
5. Set up basic project metadata (version 0.1.0)

**Outputs:**

- `pyproject.toml`
- `LICENSE` (Apache 2.0)
- `.gitignore`
- `src/life/__init__.py`
- `src/life/cli.py` (entry point skeleton)

---

### Step 2: Core CLI Framework [G1: CLI Foundation]

**Prompt:**

Implement the base CLI structure using typer:
1. Create main CLI app with subcommands: sync, merge, process, status
2. Implement config loader that reads YAML from `~/life.yml` or specified path
3. Add `--config` global option for custom config file paths
4. Add `--dry-run` global option for preview mode
5. Implement basic logging setup (console output with timestamps)

**Commands:**

```bash
# Install in development mode
pip install -e .

# Test CLI loads
life --help
life sync --help
```

**Outputs:**

- `src/life/cli.py` (main CLI with typer app)
- `src/life/config.py` (YAML config loader)
- `src/life/commands/sync.py`
- `src/life/commands/merge.py`
- `src/life/commands/process.py`
- `src/life/commands/status.py`

---

### Step 3: State Management & Incremental Sync [G2: Core Feature]

**Prompt:**

Implement stateful incremental syncing:
1. Create state manager that reads/writes JSON state files
2. Implement `{extra_args}` variable injection for incremental syncs
3. Build cursor-based pagination support using `incremental_field` and `state_file`
4. Add state tracking per sync task (last sync timestamp, high-water marks)
5. Support `--full-refresh` flag to bypass state and run full sync

**Commands:**

```bash
# Test state tracking
life sync contacts --dry-run
cat ~/.life-state.json
```

**Outputs:**

- `src/life/state.py` (state manager)
- `src/life/runner.py` (command execution with variable injection)
- Updated `src/life/commands/sync.py` (with state integration)

---

### Step 4: Multi-Command & Workflow Support [G3: Workflow Features]

**Prompt:**

Add support for complex workflows:
1. Support `commands` array (multiple commands in sequence)
2. Implement variable substitution for config fields (`{clients_file}`, `{from_date}`, etc.)
3. Add date range helpers (`{from_date}`, `{to_date}` based on `date_range` config)
4. Support append-mode outputs with `append_template` and timestamp injection
5. Implement output path expansion (tilde and environment variables)

**Commands:**

```bash
# Test multi-command execution
life process assessments --dry-run

# Test merge with variable substitution
life merge clients sessions --dry-run
```

**Outputs:**

- Updated `src/life/runner.py` (variable substitution, multi-command)
- `src/life/utils.py` (date helpers, path expansion)
- Updated `src/life/commands/merge.py`
- Updated `src/life/commands/process.py`

---

### Step 5: Documentation & Example Config [G4: Release Readiness]

**Prompt:**

Create comprehensive documentation:
1. Write README.md with project overview, installation, usage examples
2. Create example `life.yml` demonstrating sync, merge, process, status commands
3. Add inline code comments for key functions
4. Create CONTRIBUTING.md with development setup instructions
5. Add example workflows section showing common patterns

**Outputs:**

- `README.md`
- `examples/life.yml` (sanitized example configuration)
- `CONTRIBUTING.md`
- `docs/ARCHITECTURE.md` (explaining the design philosophy)

---

## Models & Tools

**Tools:** python, pip, typer, pyyaml, git

**Models:** (Sonnet 4.5 for implementation)

## Repository

**Branch:** `main`

**Merge Strategy:** direct commits (single maintainer, initial development)