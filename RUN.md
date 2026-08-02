# Running C-ATLYST

Setup, credentials, and the one command that runs the whole pipeline.
For what the system actually *is*, see [README.md](README.md).

---

## 1. Install

Python 3.11+ (developed on 3.13).

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Dependencies: `claude-agent-sdk`, `python-dotenv`, `langfuse`,
`clickhouse-connect`.

---

## 2. Environment variables

Create a `.env` in the repo root. Every script loads it automatically via
`python-dotenv`; the Node web UI parses the same file.

```bash
# --- Claude (required) ---------------------------------------------------
# Get one with:  claude setup-token
CLAUDE_OAUTH_TOKEN="sk-ant-oat01-..."

# --- ClickHouse Cloud (required for the Loader) --------------------------
CLICKHOUSE_HOST="jrb2cafd4r.ap-south-1.aws.clickhouse.cloud"
CLICKHOUSE_PORT="8443"
CLICKHOUSE_USER="default"
CLICKHOUSE_PASSWORD=".MwRKmUgG1nge"
CLICKHOUSE_DATABASE="clickathon"
CLICKHOUSE_SECURE="true"

# --- Langfuse tracing (optional but recommended) -------------------------
LANGFUSE_SECRET_KEY="sk-lf-274fc3ca-1d12-4c89-9101-83a65f7717ef"
LANGFUSE_PUBLIC_KEY="pk-lf-989642f5-3d21-4abd-b72c-cea3963cdc87"
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

| Variable | Required | Notes |
|---|---|---|
| `CLAUDE_OAUTH_TOKEN` | yes | Re-exported as `CLAUDE_CODE_OAUTH_TOKEN` at runtime, which is the name the Agent SDK's CLI subprocess actually reads. |
| `CLICKHOUSE_HOST` | yes | Hostname only — no scheme, no port. |
| `CLICKHOUSE_PORT` | no | Defaults to `8443` (HTTPS). |
| `CLICKHOUSE_USER` | no | Defaults to `default`. |
| `CLICKHOUSE_PASSWORD` | yes | |
| `CLICKHOUSE_DATABASE` | no | Defaults to `clickathon`. |
| `CLICKHOUSE_SECURE` | no | Defaults to `true`; set `false` only for a plaintext local instance. |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | no | Without them the pipeline still runs; you just get no traces. |
| `LANGFUSE_BASE_URL` | no | Defaults to Langfuse Cloud. Set this for self-hosted. |

---

## 3. ClickHouse Cloud connection — two paths

The system talks to ClickHouse **two different ways**, and they authenticate
differently. This trips people up, so it's worth being explicit:

| | Used by | Auth |
|---|---|---|
| **`clickhouse-connect`** (HTTPS, port 8443) | `loader.py` — runs DDL, inserts rows | The `CLICKHOUSE_*` credentials above |
| **Remote MCP server** (`https://mcp.clickhouse.cloud/mcp`) | `analysis_agent.py` — reads live data to answer questions | **OAuth**, interactive browser sign-in |

The MCP endpoint **does not accept API keys** — ClickHouse only supports
OAuth there, scoped to your signed-in user. That means:

- The first time the Analytics Agent connects, it needs an interactive OAuth
  handshake. Once completed, the token is cached and later runs reuse it.
- If you see the agent report the connector as unauthorized, re-authorize it
  from an interactive session (`claude mcp` / `/mcp`) rather than looking for
  a key to put in `.env`.
- The Loader is unaffected by this — it uses the credentials directly and
  works headlessly.

The Analytics Agent targets a specific Cloud service, overridable per run:

```bash
python analysis_agent.py "..." --service-id <uuid> --database clickathon
```

---

## 4. Run the pipeline end to end

**One command:**

```bash
python orchestrator.py ps/Atlys/specs/01_express_checkout
```

That runs, in order: Instrumentation Agent → Loader → Context Agent →
Analytics Agents (one per PM question, concurrently) → Context Agent.

`<spec_dir>` just needs to contain `spec.md` and `events.ndjson`.

Options:

```bash
python orchestrator.py <spec_dir> \
    --out-dir out/my_run \          # default: out/<spec_dir name>
    --context-dir context \         # default: context/
    --skip-instrumentation          # reuse an existing ddl.sql, start at the Loader
```

### Output

```
out/<spec>/
├── profile.md          deterministic event statistics
├── ddl.sql             the proposed schema (executable as-is)
├── justification.md    why every table/column/key is what it is
├── load_report.md      rows loaded per table + verification results
└── analysis/
    ├── q01.md          answer to PM question 1
    ├── q01_report.html visualization (only if the question asked for one)
    └── ...
```

The context wiki under `context/` is updated in place. Changes are **not**
committed automatically — review the diff yourself:

```bash
git diff context/
```

---

## 5. Running individual stages

Each agent is independently runnable, which is the fastest way to iterate:

```bash
# Schema design only
python instrumentation_agent.py <spec_dir> --out-dir out/<spec>

# Load an already-designed schema
python loader.py <spec_dir> --out-dir out/<spec>

# One ad-hoc question against live data
python analysis_agent.py "What is the funnel conversion rate?" \
       --out-dir out/adhoc --index 1

# All of a spec's PM questions, concurrently
python question_extractor.py <spec_dir> --out-dir out/<spec>/analysis

# Update the wiki from a completed run
python context_agent.py out/<spec>
```

Run standalone, each one traces to its own Langfuse trace. Run via
`orchestrator.py`, they all nest into a single trace for the run.

---

## 6. Web UI (optional)

```bash
cd webui
npm install
npm start           # http://localhost:3000
```

Gives you a chat interface for ad-hoc questions and a spec-upload flow with a
**human approval gate** — it shows the proposed `ddl.sql` next to
`justification.md` and runs nothing against ClickHouse until you approve.

The server shells out to the same Python entrypoints, so it needs the same
`.env` and the same activated environment. Override the interpreter if needed:

```bash
PYTHON_BIN=/path/to/python npm start
PORT=8080 npm start
```

---

## 7. Tracing

With the Langfuse keys set, each `orchestrator.py` run appears as **one
trace** named `onboard-spec:<spec>`, with `sessionId` set to the spec slug —
so every agent, tool call, and token/cost figure for that run is in one
place. Onboarding via the web UI produces the same single trace, spanning
both sides of the approval pause.

No keys set → the pipeline runs normally, just untraced.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'dotenv'`**
The venv isn't active, or deps aren't installed. Re-run step 1.

**"You've hit your session limit"**
Claude quota, not a bug. The message states when it resets.

**Analytics Agent says the ClickHouse MCP is unauthorized**
Expected on first use, or after the OAuth token expires — see §3. There is no
API-key alternative for the MCP endpoint.

**A run looks frozen on one step**
Between tool calls the model is generating, which emits no output, so the
last logged line just sits there. To check whether it's genuinely alive:

```bash
ps -eo pid,etime,command | grep -E "instrumentation_agent|analysis_agent"
```

**Loader reports `overlap_pct = 0%`**
A finding, not a crash: the spec's join key doesn't match the live table's.
It's recorded in `load_report.md` and documented by the Context Agent — the
pipeline deliberately continues.
