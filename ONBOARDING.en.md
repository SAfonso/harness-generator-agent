# ONBOARDING — harness-generator-agent

> 🇪🇸 Versión en español: [`ONBOARDING.md`](ONBOARDING.md)

> This is a guided tour of the project, written for someone joining today who
> has never seen the code. It doesn't replace the specs (`SPEC.md`,
> `specs/*.md`) — when you're about to touch code, those are the real
> contract and take priority over this document. This file is the map; the
> specs are the territory.
>
> **A note on names:** every "mode" name in this project (DIRECTOR, FISCAL,
> PROFESOR...) is Spanish, on purpose, and stays Spanish everywhere —
> including in the harness this generator produces for an English-speaking
> project. They aren't translated because they're identifiers baked into
> `src/config.py` and the Jinja templates, not prose. Treat them like proper
> nouns.

---

## TL;DR (30 seconds)

This project is **not an app** you use directly day to day. It's a
**config factory for Claude Code**: you describe a project (or point it at
one that already exists) and it hands back a folder (`harness/`) with rules,
agents with their own personas, and a task backlog — all designed to make
working with Claude Code on that project disciplined, verifiable, and hard
to derail.

There are **two completely separate systems** in this repo, and it's easy to
mix them up:

```
SYSTEM A — "The Generator"                 SYSTEM B — "The Generated Harness"
(this repo, runs ONCE)                     (lives INSIDE your project,
                                             runs CONTINUOUSLY)

  your description / your project            DIRECTOR (leader)
         │                                        │
         ▼                                   ARQUITECTO (planner)
  intake_agent (PROFESOR)                         │
         │                                   BISTURÍ (implementer)
         ▼                                        │
  analysis_agent (JUEZ)                      FISCAL (reviewer) ──► QA (tester)
         │                                        │
         ▼                                   NOTARIO (integrator)
  generator_agent (ESCRIBANO)                     │
         │                                   CENTINELA (watchman)
         ▼
  validator_agent (FISCAL)
         │
         ▼
     harness/  ────────────────────────►  this is what you install in your
                                            project, and it becomes System B
```

If you ever read "FISCAL" and aren't sure whether it means System A or B:
there's a section below (§5) dedicated exactly to that trap.

---

## 1. The problem this solves

When someone uses Claude Code (or any agentic LLM) to build a project
without structure, the same failures show up every time:

- The agent tries to swallow huge goals ("build the whole backend") instead
  of small, verifiable tasks.
- No test discipline: it implements and moves on, without verifying
  before/after.
- Approved work gets lost because nobody committed it (this actually
  happened: an external `git reset` reverted already-approved tasks on one
  of the projects this harness was applied to, before NOTARIO existed —
  the real reason NOTARIO commits when it closes each task, see
  `specs/generator_agent.md#v2`).
- Every session reinvents the project's rules because there's no fixed
  place they're written down.
- If the project already exists (it isn't a blank page), there's no way for
  the agent to quickly understand what's there and what's missing.

This generator attacks that by producing a **harness**: a folder with
explicit rules, an atomic task backlog with assigned complexity, and several
"agents" (behavior profiles, not separate processes) that hand off work to
each other with very specific responsibilities.

---

## 2. Quick glossary (before you go further)

| Term | What it means here |
|---|---|
| **Harness** | The folder (`harness/`) this repo generates: `CLAUDE.md`, `AGENTS.md`, `CHECKPOINTS.md`, `feature_list.json`, `.claude/agents/*.md`, etc. It's what gets installed in your project. |
| **Agent** | Not a process or a microservice — it's a **Markdown file** (`.claude/agents/name.md`) with behavior instructions that Claude Code reads and adopts as a persona while working in that role. |
| **Mode** | An agent's "code name" (DIRECTOR, FISCAL, PROFESOR...). It's a mnemonic label, but each mode has very concrete behavior rules behind it — it's not just a fun name. |
| **`HarnessSpec`** | The Pydantic data structure that travels through System A. Every generator agent reads and/or fills it in. Defined in `specs/models.md` / `src/models/harness_spec.py`. |
| **Atomic backlog** | `feature_list.json`: a list of short tasks, each with **a single verifiable deliverable** — never "build the entire front end." |
| **SDD** | Spec-Driven Development: nothing gets coded without first being described in a `spec`. The spec is the contract. |
| **TDD** | Test-Driven Development: the test is written before the implementation, and you watch it fail (red) before making it pass (green). |
| **Brownfield / Greenfield** | Greenfield = a project from scratch. Brownfield = a project that already exists and has code/history that must be respected. This generator supports both (see §3.4). |

---

## 3. System A in detail — the generator (this repo)

This is the pipeline that runs **exactly once** to produce your `harness/`.
It's written in plain Python (Pydantic + Jinja2), with no real LLM inside the
code — this system's "agents" are deterministic functions (keyword
heuristics) that **simulate** what an LLM would do, so the whole pipeline can
be tested with `pytest` without spending tokens or depending on the network.

```
run_pipeline(text, mode, output_dir)          ←  src/main.py
   │
   ├─► inspect_project(output_dir)             ←  brownfield, see §3.4
   │
   ├─► run_intake(text, mode, inspection)       ←  intake_agent.py  (PROFESOR)
   │        │
   │        ├─ status="needs_input" → stops here, nothing gets generated
   │        └─ status="complete" → partial HarnessSpec
   │
   ├─► run_analysis(spec)                       ←  analysis_agent.py (JUEZ)
   │        → complete HarnessSpec (agents, complexity, rules)
   │
   ├─► run_generator(spec, harness/)            ←  generator_agent.py (ESCRIBANO)
   │        → writes every file of the harness
   │
   └─► run_validator(harness/, spec)            ←  validator_agent.py (FISCAL)
            → verdict: approved / rejected (8 checks)
```

### 3.1 What is "intake"?

**Intake literally means "information gathering"** — it's the first and
only agent in this system that has "contact" with the user (or with the
existing project, in brownfield). Its job is to fill in 7 dimensions about
what's being built:

1. `project_type` — kind of project (`data_pipeline`, `api`, `web`, `agent`, `cli`, `other`)
2. `stack` — main technologies
3. `data_sources` — where the data/inputs come from
4. `constraints` — known limitations (no network, rate limits...)
5. `acceptance_criteria` — what "done" means
6. `deliverable` — what gets delivered at the end
7. `time_available` — how much time there is

If the text describing the project already covers all 7 (a "rich" input),
intake extracts all of them at once. If information is missing (a "sparse"
input), it returns `status="needs_input"` with the list of what's missing —
and **nothing gets generated** until it's complete. That's the key
difference from just "coding a form": intake never moves forward with gaps.

Its mode is **PROFESOR** (Spanish for "teacher/professor"): it doesn't
accept vague answers, and if something doesn't make sense (an odd stack for
the project type, an unrealistic deadline, a subjective acceptance
criterion) it says so with a concrete argument instead of validating it by
default.

📄 Spec: `specs/intake_agent.md` · Code: `src/agents/intake_agent.py`

### 3.2 System A's 4 agents, one by one

| Agent | Mode | What it does | Input → Output |
|---|---|---|---|
| **`intake_agent`** | PROFESOR | Interviews (or confirms, in brownfield) until all 7 dimensions are covered | free text → partial `HarnessSpec` |
| **`analysis_agent`** | JUEZ ("judge") | Decides the structure: confirms the project type, computes the harness's complexity based on time available, builds the list of agents (`AgentRole`) the generated harness will have, and its specific rules | partial `HarnessSpec` → complete `HarnessSpec` |
| **`generator_agent`** | ESCRIBANO ("scribe") | Renders every harness file from Jinja2 templates, in a fixed order (so each file can reference the previous ones without contradictions) | complete `HarnessSpec` → files in `harness/` |
| **`validator_agent`** | FISCAL ("prosecutor/auditor") | Runs 8 automated checks on the output (do the agents in `AGENTS.md` match the real files? is there a pending task? any unresolved `{{`?...) and issues a verdict | `harness/` + `HarnessSpec` → approved/rejected + report |

Each one has its own spec (`specs/<agent>.md`) and its own known-errors file
(`errors/<agent>.md`) — you don't need to read the ones for an agent you
aren't touching.

### 3.3 `HarnessSpec` — the shared state

It's the single structure that travels through the whole pipeline. Think of
it as a form that gets filled in gradually: `intake_agent` writes half the
fields, `analysis_agent` fills in the rest (`agent_roles`,
`harness_complexity`, `rules`), and `generator_agent`/`validator_agent` only
read it. Defined in `src/models/harness_spec.py` (contract in
`specs/models.md`).

### 3.4 Brownfield: when the project already exists

If `output_dir` (where the harness is about to be generated) already shows
signs of being a real project — dependency manifests (`requirements.txt`,
`package.json`...), git history, a `README.md`/`CLAUDE.md` with content —
before asking anything, `run_pipeline` calls `inspect_project()`:

- **Infers** what it can (project type and stack) with concrete evidence and
  a confidence level (`high`/`low`). If it's `high`, PROFESOR doesn't ask
  again — it confirms it in the opening message. If it's `low`, it does ask
  for a quick confirmation (it never silently assumes).
- **Audits** mechanical problems that would break the generated harness: no
  git repo or remote (NOTARIO couldn't commit/open a PR), no CI (CENTINELA
  would have nothing to check), no tests, empty documentation, or an
  existing `CLAUDE.md` that will need to be merged by hand. Every finding
  turns into an **initial task in the generated backlog** — it's never left
  as a mere comment.
- Never touches or generates the project's `README.md` — that's the user's
  product documentation, outside the harness's scope.

📄 Spec: `specs/tools.md#inspect_project` · Code: `src/tools/inspect_project.py`

---

## 4. System B in detail — the harness installed in your project

This is what you'll actually use day to day once it's generated. It lives
inside **your** project (not this repo) and Claude Code runs it directly —
there's no Python engine orchestrating it; the `.claude/agents/*.md` files
are instructions Claude Code follows to the letter.

```
harness/
├── CLAUDE.md              # the first thing Claude Code reads: mode, rules, model policy
├── AGENTS.md              # map of every role and its mode
├── CHECKPOINTS.md         # acceptance criteria (what FISCAL reviews against)
├── feature_list.json      # backlog: atomic tasks + complexity (alta|media|baja)
├── init.sh                # checks that the environment (git, gh, etc.) is ready
├── progress/
│   └── ledger.json        # DIRECTOR's persistent memory across tasks (decisions + summaries)
└── .claude/agents/
    ├── leader.md          # DIRECTOR
    ├── planner.md         # ARQUITECTO
    ├── implementer.md     # BISTURÍ
    ├── reviewer.md        # FISCAL
    ├── integrator.md      # NOTARIO
    ├── watchman.md        # CENTINELA
    └── tester.md          # QA (only if the project is type "agent")
```

### 4.1 The fixed agent core, one by one

This set **doesn't change based on project type** — it's always the same
(except `tester`, which only shows up for `agent`-type projects). No new
agents get invented on a whim.

| Agent | Mode | Its job, in one sentence |
|---|---|---|
| **`leader`** | **DIRECTOR** | Orchestrates execution task by task. Doesn't weigh in on design, just coordinates. Escalates to the user if something gets rejected 3 times. Its memory across tasks is `progress/ledger.json`, not a long conversation — so each task starts with a clean sub-session and a minimal context package, not the full history. |
| **`planner`** | **ARQUITECTO** ("architect") | Breaks broad goals into atomic tasks and assigns each one a complexity (`alta`\|`media`\|`baja`, i.e. high/medium/low) — that complexity decides which LLM tier runs that task. |
| **`implementer`** | **BISTURÍ** ("scalpel") | Implements **one** task, without straying from the given scope. Doesn't decide architecture, doesn't touch what it wasn't asked to. |
| **`reviewer`** | **FISCAL** | Approves or rejects BISTURÍ's work by checking it against `CHECKPOINTS.md`. Doesn't hunt for bugs on its own initiative — it checks against what was agreed. *(Heads up: there's ANOTHER "FISCAL" in System A — see §5.)* |
| **`integrator`** | **NOTARIO** ("notary") | Formalizes approved work in git: creates the `task/{id}-slug` branch when the task starts, and commits + pushes + opens a PR when it closes, only after FISCAL (or QA) approves. |
| **`watchman`** | **CENTINELA** ("sentinel") | Checks the PR's CI and conflicts. If everything's green, it **merges automatically** — it doesn't wait for human approval (runs unattended). If it fails, it reopens the cycle with FISCAL instead of blindly relaunching BISTURÍ. |
| **`tester`** | **QA** | Only for `agent`-type projects. Designs and runs behavior tests before FISCAL approves. |

### 4.2 A task's life cycle

For every `pending` task in `feature_list.json`, here's the actual path it
takes:

```
NOTARIO (creates branch task/{id}-slug)
   │
   ▼
BISTURÍ (implements, strict scope)
   │
   ▼
FISCAL (reviews) ──rejection──► back to BISTURÍ (max 3 rejections, then escalates to DIRECTOR)
   │
   approved (+ QA if it applies)
   ▼
NOTARIO (commit + push + PR)
   │
   ▼
CENTINELA (CI + merge)
   │
   ├─ green → automatic merge, task closed
   └─ fails → reopens the cycle with FISCAL, with the failure context attached
```

When the task closes (integrated or escalated), a distilled summary gets
added to `progress/ledger.json` — never the raw conversation log.

**If CENTINELA's failure is a merge conflict** (not red CI), it's handled
differently from a generic CI failure: CENTINELA flags it explicitly as
such, FISCAL requires that the fix trace the intent on each side (commit,
PR, or originating task) instead of accepting a brute-force
`--ours`/`--theirs`, and BISTURÍ — who actually touches the file once the
task reopens — applies that standard (or uses the `/resolving-merge-conflicts`
skill if it's installed). Integration by reference, same pattern as the
`/code-review` recommendation in `inspect_project` (§3.4): delegate to a
dedicated skill, don't reinvent it.

**FISCAL deliberately covers only the "Spec axis"** (does it satisfy
`CHECKPOINTS.md`?) — never code conventions or code smells, that's the
"Standards axis," out of its scope by design. Before NOTARIO closes the PR,
it recommends running `/code-review` for that axis. And **if a task reopens
after a rejection**, BISTURÍ doesn't guess blindly: it reproduces the exact
reason for the rejection before touching anything, and from the 2nd retry
on it writes concrete hypotheses before fixing anything — it uses
`/diagnosing-bugs` if installed, or the same discipline by hand if not. Two
more integrations by reference, same pattern.

### 4.3 The key files you'll look at as a junior

- **`CLAUDE.md`** — always read this first when you join a project that has
  this harness installed. It states the active mode and the non-negotiable
  rules.
- **`feature_list.json`** — the backlog. This is where you see what's
  pending, in progress, or done, and at what complexity.
- **`CHECKPOINTS.md`** — if you want to know "is this considered done?",
  the answer lives here, not in your personal judgment.
- **`progress/ledger.json`** — the history of important decisions, so you
  don't have to reread the whole conversation.

---

## 5. The repeated-name trap: FISCAL ≠ FISCAL

You'll see "FISCAL" in two different places, and **it isn't the same
agent**:

| | System A (this repo) | System B (generated harness) |
|---|---|---|
| Agent | `validator_agent` | `reviewer` |
| When it runs | Once, at the end of generating the harness | Continuously, on every backlog task |
| What it validates against | The generated harness's 8 coherence checks | Your project's `CHECKPOINTS.md` |
| File | `src/agents/validator_agent.py` | `.claude/agents/reviewer.md` (generated) |

Both share a philosophy ("doesn't hunt for bugs, checks against what was
agreed"), which is presumably why someone gave them the same code name — but
they're different agents, in different systems, that never run in the same
phase. If you read "FISCAL" in a conversation, ask (or check the context)
which of the two is meant.

---

## 6. How it's installed and used (summary)

Full detail in `README.md`; here's just the mental map:

1. **Install the generator** (once): `pip install -e .` makes the
   `harness-agents` command available. There's also a Claude Code skill
   (`skill/harness-agents/`) that installs this for you the first time you
   invoke it with `/harness-agents`.
2. **Run it inside your project** (greenfield or brownfield, doesn't
   matter): `cd your-project && harness-agents`. The `cwd` matters a lot —
   the harness always gets generated in the directory you launched it from,
   never in this generator's own repo (there was a real bug about this,
   documented in `errors/packaging.md` — worth reading, it's a good example
   of how the repo's error protocol works).
3. You choose a mode (`EJECUTOR` — "executor" — or `PROFESOR`), describe the
   project (or let the brownfield inspection fill in what it can), and the
   approved harness ends up in `harness/` inside your project.
4. Moving `harness/*` to your project's root and merging `CLAUDE.md` with an
   existing one (if there was one) is still manual — not automated.

**If you invoke it from inside Claude Code** (via `/harness-agents`, not by
typing it yourself in a terminal), bare `harness-agents` **doesn't work**:
it uses `input()`, and an agent's Bash tool doesn't sustain a turn-by-turn
stdin conversation — it blows up with `EOFError` on the first prompt
(another real bug, this one found in production against a real project,
see `errors/main.md`). That's why `main()` accepts `--text`: the skill has
Claude ask in the chat itself, build
`harness-agents --text "..." --mode ... --output-dir "$(pwd)"`, and re-invoke
with expanded text if the output asks for more information — Claude is the
conversational layer, never the subprocess.

---

## 7. How this repo is organized (if you're going to touch code)

The golden rule, no exceptions, lives in `CLAUDE.md` and `SPEC.md`:

> **Strict SDD + TDD:** update the module's spec → write the test (watch it
> fail) → implement → watch it pass → commit.

Nothing gets coded that isn't first described in `specs/<module>.md`. If
you're asked for a new function and it's not in the spec, the first step is
**editing the spec**, not writing code.

| If you're touching… | Read its spec | And its known errors |
|---|---|---|
| `src/models/` | `specs/models.md` | `errors/models.md` |
| `src/tools/` | `specs/tools.md` | `errors/tools.md` |
| `src/agents/intake_agent.py` | `specs/intake_agent.md` | `errors/intake_agent.md` |
| `src/agents/analysis_agent.py` | `specs/analysis_agent.md` | `errors/analysis_agent.md` |
| `src/agents/generator_agent.py` | `specs/generator_agent.md` | `errors/generator_agent.md` |
| `src/agents/validator_agent.py` | `specs/validator_agent.md` | `errors/validator_agent.md` |
| `src/templates/` | `specs/templates.md` | `errors/templates.md` |
| `src/main.py` | `specs/main.md` | `errors/main.md` |
| `pyproject.toml`, `skill/` | `specs/packaging.md` | `errors/packaging.md` |

**Error protocol** (in `errors/ERRORS.md`): if you hit an error, first check
whether it's already documented in `errors/<module>.md` — if it is, apply
the solution that's already written, don't re-investigate from scratch. If
it's new, fix it and log it before closing the task. The goal: no error ever
gets investigated twice.

**Tests:** `python3 -m pytest tests/ -q` before every commit. Use pytest's
`tmp_path` fixture for anything touching the filesystem — never create test
files by hand in the repo. Two explicit quality rules in `SPEC.md`:
`monkeypatch`/mocks only at real external boundaries (filesystem,
path/config variables), never to simulate the logic of another function of
your own; and no tautological tests (the expected value has to be a literal
traceable to the spec, not the result of recomputing it with the same
formula the code under test uses).

---

## 8. Weird things you'll run into (honesty, not embarrassment)

A real project has documented technical debt, not hidden debt:

- **`src/templates/agents/intake.md.j2`, `analysis.md.j2`, `generator.md.j2`
  exist but are never used.** The real core of generated agents
  (`_CORE_AGENTS` in `src/config.py`) is `leader, planner, implementer,
  reviewer, integrator, watchman` (+`tester`) — it never includes `intake`,
  `analysis`, or `generator` as agents of the generated harness. Those three
  templates are leftovers from an earlier design iteration. They're
  harmless (never rendered), but if you edit them thinking they do
  something, they don't.
- **`PROJECT.md` is out of date** in its "agent modes" table and in the
  `harness/` tree it describes — it mixes System A's agents with System B's
  as if they were the same set. `README.md` and `SPEC.md` reflect the real
  state; when in doubt, trust those two.
- **In brownfield, only 2 of the 7 dimensions get inferred** (`project_type`
  and `stack`). The other 5 (`data_sources`, `constraints`,
  `acceptance_criteria`, `deliverable`, `time_available`) would only get
  filled in if there were explicit evidence of a previous harness run
  (`CHECKPOINTS.md`/`feature_list.json` already existing) — and that isn't
  implemented yet.
- **`progress/current.md`, `history.md`, `errors.md`** show up mentioned in
  older rules/specs as part of what should get generated, but today only
  `progress/ledger.json` actually gets generated.

If you're looking for a first task to learn this repo's SDD+TDD flow with
low risk, cleaning up any of these (spec → test → implementation → commit)
is a good candidate.

---

## 9. Where to go next

1. Read `SPEC.md` in full, once — it's short and it's the cross-cutting
   contract.
2. Run the suite: `python3 -m pytest tests/ -q` (should be all green).
3. Generate a test harness on an empty directory to see the full greenfield
   flow, then on one with a `requirements.txt` to see the brownfield flow +
   the audit in action.
4. When you're about to touch a specific module, go straight to its row in
   the §7 table — you don't need to read the specs of the modules you're
   not touching.
5. If anything in this document doesn't match what you see in the code, the
   code (and its spec) always wins — update this `ONBOARDING.en.md` (and
   `ONBOARDING.md`) while you're at it.
