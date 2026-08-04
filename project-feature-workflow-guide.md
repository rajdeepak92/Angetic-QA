# Agentic-QA feature workflow guide

This human-facing guide explains how to prepare a feature before referencing `project-prompt.md`.
Keep both files at the repository root. Neither file replaces the six authoritative files in
`coding-agent-context/`.

## 0. One-time installation

Save these tracked operational files at:

```text
D:\Repos\Agentic-QA\project-prompt.md
D:\Repos\Agentic-QA\project-feature-workflow-guide.md
```

Add these exact lines to `.graphifyignore` so placeholder/example content can never become graph
provenance or planned architecture:

```gitignore
project-prompt.md
project-feature-workflow-guide.md
```

Do not add them to `.gitignore`; they should be version-controlled. Verify once:

```powershell
Set-Location "D:\Repos\Agentic-QA"

$OperationalDocs = @(
    "project-prompt.md",
    "project-feature-workflow-guide.md"
)

foreach ($Path in $OperationalDocs) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing operational document: $Path"
    }

    $Ignored = (& git check-ignore --no-index -- $Path 2>&1 | Out-String).Trim()

    if ($LASTEXITCODE -eq 0) {
        throw "Operational document is ignored by Git: $Path"
    }

    if ($LASTEXITCODE -ne 1) {
        throw "Unable to evaluate Git ignore policy for ${Path}: $Ignored"
    }
}

$GraphifyIgnore = @(Get-Content -LiteralPath ".\.graphifyignore")

foreach ($Path in $OperationalDocs) {
    if ($GraphifyIgnore -notcontains $Path) {
        throw "Operational document is not excluded from Graphify: $Path"
    }
}

Write-Host "OPERATIONAL DOCUMENT SETUP PASS" -ForegroundColor Green
```

## 1. Classify the request

| Situation | Prompt mode | Context preparation |
|---|---|---|
| Declared `READY`, not implemented | `IMPLEMENT_READY_FEATURE` | Validate all six contracts; normally no edits. |
| Implemented behavior violates its existing contract | `FIX_IMPLEMENTED_FEATURE` | Capture reproduction/evidence; verify the tracker has a fix-record convention. |
| `DONE` feature needs different/new behavior | `CHANGE_IMPLEMENTED_FEATURE` | Create a new approved change contract or use an explicit reopen policy. Never rewrite history silently. |
| Behavior is absent from the plan | `IMPLEMENT_NEW_FEATURE` | Complete the context-first workflow in section 3. |

## 2. Existing-feature validation workflow

### Step 1 mechanical preflight

Replace `*FEATURE_ID*`, then run from PowerShell:

```powershell
$ErrorActionPreference = "Stop"
Set-Location "D:\Repos\Agentic-QA"

$FeatureId = "*FEATURE_ID*"
$ContextFiles = @(
    ".\coding-agent-context\project-overview.md",
    ".\coding-agent-context\project-architecture-stack.md",
    ".\coding-agent-context\layout.md",
    ".\coding-agent-context\coding-standard.md",
    ".\coding-agent-context\ai-workflow-rules.md",
    ".\coding-agent-context\progress-tracker.md"
)

foreach ($Path in $ContextFiles) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing authoritative context: $Path"
    }
}

$Head = (& git rev-parse HEAD 2>&1 | Out-String).Trim()

if ($LASTEXITCODE -ne 0) {
    throw "Unable to resolve Git HEAD: $Head"
}

$Status = @(& git status --short 2>&1)

if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect Git status."
}

Write-Host "HEAD: $Head"
Write-Host "Worktree entries: $($Status.Count)"
$Status | ForEach-Object { Write-Host $_ }

$SearchPaths = @($ContextFiles)

if (Test-Path -LiteralPath ".\README.md" -PathType Leaf) {
    $SearchPaths += ".\README.md"
}

$Matches = @(
    Select-String `
        -LiteralPath $SearchPaths `
        -SimpleMatch `
        -Pattern $FeatureId
)

if ($Matches.Count -eq 0) {
    throw "Feature ID not found in authoritative context: $FeatureId"
}

$Matches |
    Select-Object Path, LineNumber, Line |
    Format-Table -AutoSize
```

This proves file/search availability only. It does not prove that the feature is semantically ready.

### Step 2 validate all six authorities

| Authority | Required existing-feature evidence |
|---|---|
| `project-overview.md` | One ID/name, user outcome, scope, exclusions, dependencies, testable acceptance criteria, stage, and status. |
| `project-architecture-stack.md` | Every required version, boundary, provider/store, schema/artifact, protocol/port, and infrastructure decision. |
| `layout.md` | Existing/planned owners, paths, layer direction, and create/modify intent. |
| `coding-standard.md` | Applicable typing, validation, errors, logging, security, and testing rules. |
| `ai-workflow-rules.md` | Required tools, approval boundaries, verification commands, and completion rules. |
| `progress-tracker.md` | Same current feature/status, dependencies `DONE`, accurate completed count/history, and no blocker. |

Also verify physically:

- dependencies exist and match their `DONE` records;
- expected files are correctly classified as existing or planned;
- affected callers, tests, config, scripts, lockfile, interfaces, services, UI, stores, and
  infrastructure were inspected;
- tools/services/ports required by the feature are available;
- acceptance criteria map to deterministic tests/evidence;
- existing user changes can be preserved;
- Graphify is used only for query navigation and not as implementation proof.

### Step 3 decide whether context must change

- Declared `READY` feature with complete consistent contracts: no pre-implementation context edit.
- Missing/contradictory fact: update only the owning context file before prompting.
- Defect restoring existing behavior: do not change product scope; add reproduction and follow the
  trackers fix-record convention.
- New behavior for a `DONE` feature: use the new-feature preparation workflow or an explicit reopen
  policy. Do not edit its historical `CHG-###` record.

### Step 4 invoke the agent

Start a clean Codex or Claude Code session. Copy the matching invocation block from
`project-prompt.md`, fill every placeholder, and use the correct feature mode.

## 3. New-feature implementation workflow

### Step 1 reserve an identity

Read the overview and tracker, then choose the next unused ID following the repositorys current
numbering convention. Identify dependencies. Keep the feature `PLANNED` until its full contract is
complete and every mandatory dependency is `DONE`.

### Step 2 update context by ownership

| Context file | Required before implementation | Leave unchanged when |
|---|---|---|
| `project-overview.md` | **Always:** ID, name, stage, user outcome, scope, exclusions, dependencies, acceptance criteria, and `PLANNED`/`READY`. | Never for a genuinely new feature. |
| `project-architecture-stack.md` | Exact new/changed runtime, package/image version, service/store ownership, protocol/port, schema/artifact format, trust boundary, or technical decision. | Existing architecture already covers every fact accurately. |
| `layout.md` | Planned files/directories, owner, layer direction, and create/modify intent. Clearly label nonexistent paths as planned. | All affected owners/paths already exist and remain accurate. |
| `coding-standard.md` | Only a reusable production rule that should govern multiple future features. | Behavior is feature-specific or an existing rule covers it. |
| `ai-workflow-rules.md` | Only a project-wide agent procedure, security boundary, required tool, approval rule, or completion gate. | Tests/behavior are feature-specific or existing rules cover them. |
| `progress-tracker.md` | **Always:** prospective current/planned state in its existing format. Mark `READY` only after contract readiness. | Never when activating a new feature. |

Before implementation, do not:

- append a completion `CHG-###` record;
- increment the `DONE` count;
- state that planned files or behavior already exist;
- refresh Graphify/Obsidian;
- document planned user behavior in `README.md` as available.

### Step 3 make the contract implementation-ready

The six files must answer:

1. Who receives what observable outcome?
2. What is included and explicitly excluded?
3. Which dependencies must be `DONE`?
4. What testable criteria cover success, validation, failure, and security?
5. Which layer owns each behavior/data item?
6. Which existing interface/pattern must be reused?
7. Which files will be created or modified?
8. What exact authorized versions are required, and why?
9. Are schema, migration, compatibility, reset, data-loss, or rollback rules required?
10. Are secrets, external services, paid calls, or destructive actions involved?
11. Which unit, contract, integration, UI, security, and end-to-end gates prove completion?
12. Which feature may become `READY` next, only after this one is `DONE`?

Keep the feature `PLANNED` while a required answer is unresolved.

### Step 4 illustrative context example

This example is not project scope. Replace the placeholders and adapt the headings to the physical
files rather than copying formatting blindly.

#### `project-overview.md`

```markdown
### *NEW_FEATURE_ID* Export a completed-run evidence bundle

- Status: `READY`
- Stage: `*FEATURE_STAGE*`
- Dependencies: `*DONE_DEPENDENCY_IDS*`
- User outcome: Export one completed run as a deterministic ZIP for offline review.
- In scope:
  - Select an existing completed run by deterministic project/run identity.
  - Export a canonical manifest, allowlisted artifacts, checksums, and provenance.
  - Reject missing, incomplete, or cross-project runs with a typed error.
- Out of scope:
  - Creating or rerunning workflows.
  - Network upload/sharing.
  - Credentials, prompts, raw provider responses, or non-allowlisted source bodies.
- Acceptance criteria:
  1. Identical canonical inputs produce identical manifest/checksum values.
  2. The bundle contains only artifact-contract allowlisted files.
  3. Invalid project/run identities fail without leaving partial output.
  4. Unit, contract, UI, and end-to-end tests require no provider API key.
```

#### `project-architecture-stack.md` only if the artifact contract is new

```markdown
#### Completed-run evidence bundle

- Ownership: immutable export projection derived from canonical PostgreSQL run records.
- Format: ZIP with a canonically ordered JSON manifest and allowlisted immutable artifacts.
- Integrity: SHA-256 over canonical bytes; archive entry ordering/timestamps are deterministic.
- Security: credentials, prompts, raw provider payloads, and non-allowlisted bodies are excluded.
- Implementation: Python standard library; no new dependency.
```

#### `layout.md` planned paths using the repositorys real conventions

```text
src/multi_agentic_graph_rag/ports/evidence_export.py          # planned typed port
src/multi_agentic_graph_rag/services/evidence_export.py       # planned service
src/multi_agentic_graph_rag/ui/components/evidence_export.py  # planned UI adapter
tests/unit/services/test_evidence_export.py                    # planned tests
tests/contract/test_evidence_export.py                         # planned contract tests
```

For this example, `coding-standard.md` and `ai-workflow-rules.md` need no change because deterministic
data, path safety, secret handling, layering, and completion gates already exist as reusable rules.

#### `progress-tracker.md` adapt to its existing format

```text
Current feature: *NEW_FEATURE_ID* READY
Dependencies: verified DONE
Blocker: none
```

Do not add the completion record or increment completed totals yet.

### Step 5 invoke the coding agent

Use the `IMPLEMENT_NEW_FEATURE` block from `project-prompt.md`. For example:

```text
FEATURE_MODE: IMPLEMENT_NEW_FEATURE
FEATURE_ID: *NEW_FEATURE_ID*
FEATURE_NAME: Export a completed-run evidence bundle
REQUEST: Implement the complete newly declared contract.
USER_OUTCOME: Export one completed run as a deterministic sanitized ZIP.
EXPECTED_HEAD: AUTO_DETECT
DEPENDENCIES: Verify the exact `DONE` dependencies in project-overview.md.
ACCEPTANCE_CRITERIA: Use the exact new-feature section in project-overview.md.
OUT_OF_SCOPE: Workflow execution, network sharing, secrets, raw prompts/responses, later features.
REPRODUCTION: NONE
EXPECTED_FILES: Discover from layout.md and verify every physical path.
SPECIAL_CONSTRAINTS: Deterministic output, project/run isolation, no partial write.
ADDITIONAL_GATES: Run all feature-specific contract and end-to-end tests declared in context.
HUMAN_APPROVALS_GRANTED: NONE
```

### Step 6 review and close

After implementation:

1. Review `git diff`, `git diff --check`, test evidence, and the exact tracker entry.
2. Confirm mandatory gates are truly `PASS`; skipped work remains `NOT_RUN`.
3. Confirm exactly one factual completion record and correct next `READY` feature.
4. Confirm no secret, database data, runtime artifact, Graphify output, or Obsidian vault file is tracked.
5. Human stages/commits only after approval.
6. Graphify synchronization remains a separate human-controlled operation.

## 4. Prompt hygiene

- Use one clean session per feature.
- Reference `project-prompt.md`; send only the short feature values.
- State each constraint once. Keep durable policy in its owning context file.
- Use observable acceptance criteria and executable verification.
- Point to existing physical patterns when known; otherwise require discovery.
- After repeated corrections, stop and restart with corrected contracts/task values.