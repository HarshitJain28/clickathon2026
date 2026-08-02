"use strict";

/**
 * Atlys Analytics — lightweight Node/Express web UI.
 *
 * Serves a ChatGPT-style chat page (public/) and exposes a small API that
 * shells out to the existing Python agents — no logic is reimplemented,
 * this only spawns the same scripts the CLI version did. Both the chat and
 * onboarding flows follow the same start/stream/results job pattern, so the
 * frontend can show real-time progress (each agent's own `[tool] ...` lines)
 * instead of a single static "please wait":
 *
 *   POST /api/analysis/start          -> analysis_agent.py (one question)
 *   GET  /api/analysis/stream/:jobId  -> SSE log stream for that run
 *   GET  /api/analysis/results/:jobId -> qNN.md (+ qNN_report.html) once done
 *
 *   POST /api/onboard/start             -> saves an uploaded spec.md +
 *                                          events.ndjson, then runs ONLY the
 *                                          Instrumentation Agent
 *   GET  /api/onboard/stream/:jobId      -> SSE log stream for the run;
 *                                          fires an `awaiting-approval` event
 *                                          (with the proposed ddl.sql +
 *                                          justification.md) once that
 *                                          agent finishes, and PAUSES there —
 *                                          this is the human-in-the-loop gate
 *   POST /api/onboard/approve/:jobId     -> continues the same job: runs
 *                                          orchestrator.py --skip-instrumentation
 *                                          (Loader -> Context -> Question
 *                                          Extractor -> Context) against the
 *                                          already-approved schema
 *   POST /api/onboard/reject/:jobId      -> ends the job right there; nothing
 *                                          past the schema design ever runs
 *   GET  /api/onboard/results/:jobId     -> analysis/qNN.md (+ qNN_report.html)
 *                                          once the run finishes
 *
 *   GET  /api/chats  -> the full persisted chat history (all chats, their
 *                        messages, which one was active), read from disk
 *   PUT  /api/chats  -> overwrite that same file with the client's current
 *                        state. Chat history intentionally lives on disk,
 *                        not in browser localStorage — avoids per-origin
 *                        buckets, private-mode wipes, and quota limits, and
 *                        means a fresh browser/profile still sees history.
 *
 * Usage:
 *   cd webui && npm install && npm start
 *   then open http://localhost:3000
 *
 * PYTHON_BIN env var overrides the interpreter used to spawn the agents;
 * otherwise this prefers the repo's own .venv if one exists, falling back
 * to `python3`/`python` on PATH.
 */

const path = require("path");
const fs = require("fs");
const fsp = fs.promises;
const crypto = require("crypto");
const { spawn } = require("child_process");
const express = require("express");
const multer = require("multer");

const REPO_ROOT = path.resolve(__dirname, "..");
const ANALYSIS_AGENT = path.join(REPO_ROOT, "analysis_agent.py");
const INSTRUMENTATION_AGENT = path.join(REPO_ROOT, "instrumentation_agent.py");
const ORCHESTRATOR = path.join(REPO_ROOT, "orchestrator.py");
const OUT_ROOT = path.join(REPO_ROOT, "out", "webui_chats");
const UPLOAD_ROOT = path.join(REPO_ROOT, "uploads");
const CHAT_HISTORY_FILE = path.join(OUT_ROOT, "chat_history.json");
const LAST_ONBOARD_FILE = path.join(OUT_ROOT, "last_onboard_run.json");

const ANALYSIS_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes
const ORCHESTRATOR_TIMEOUT_MS = 60 * 60 * 1000; // 1 hour
const JOB_TTL_MS = 2 * 60 * 60 * 1000; // clean up finished jobs after 2h

const PORT = process.env.PORT || 3000;

function resolvePython() {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  const venvPython =
    process.platform === "win32"
      ? path.join(REPO_ROOT, ".venv", "Scripts", "python.exe")
      : path.join(REPO_ROOT, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) return venvPython;
  return process.platform === "win32" ? "python" : "python3";
}
const PYTHON_BIN = resolvePython();

function slugify(name) {
  const slug = String(name)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return slug || "spec";
}

async function uniqueDir(root, slug) {
  let candidate = path.join(root, slug);
  let n = 2;
  while (fs.existsSync(candidate)) {
    candidate = path.join(root, `${slug}_${n}`);
    n += 1;
  }
  return candidate;
}

/** Spawn `cmd args`, line-buffering combined stdout+stderr into onLine.
 * Resolves with the exit code, or rejects on spawn error / timeout. */
function runProcess(cmd, args, { timeoutMs, onLine } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { cwd: REPO_ROOT });
    let buffer = "";
    let killedForTimeout = false;

    const timer = timeoutMs
      ? setTimeout(() => {
          killedForTimeout = true;
          child.kill("SIGKILL");
        }, timeoutMs)
      : null;

    const handleChunk = (chunk) => {
      buffer += chunk.toString("utf8");
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (onLine) onLine(line);
      }
    };

    child.stdout.on("data", handleChunk);
    child.stderr.on("data", handleChunk);

    child.on("error", (err) => {
      if (timer) clearTimeout(timer);
      reject(err);
    });

    child.on("close", (code) => {
      if (timer) clearTimeout(timer);
      if (buffer && onLine) onLine(buffer);
      if (killedForTimeout) {
        reject(new Error(`process timed out after ${timeoutMs}ms`));
        return;
      }
      resolve(code);
    });
  });
}

const app = express();
// Chat history can include full self-contained HTML reports, so the
// default 100kb express.json() body limit is too small for the /api/chats
// PUT — raise it well past what a realistic session should ever hit.
app.use(express.json({ limit: "50mb" }));
app.use(express.static(path.join(__dirname, "public")));

// ---------------------------------------------------------------------
// Chat history: persisted to disk, not browser localStorage
// ---------------------------------------------------------------------

/** Atomic write (temp file + rename) so a crash mid-write can never leave
 * the file half-written/corrupt. Shared by every small JSON state file this
 * server persists (chat history, last onboarding run). */
async function writeJsonFile(file, data) {
  await fsp.mkdir(path.dirname(file), { recursive: true });
  const tmpFile = `${file}.tmp`;
  await fsp.writeFile(tmpFile, JSON.stringify(data), "utf8");
  await fsp.rename(tmpFile, file);
}

async function readJsonFile(file, fallback) {
  try {
    return JSON.parse(await fsp.readFile(file, "utf8"));
  } catch (err) {
    if (err.code !== "ENOENT") {
      console.warn(`Could not read ${path.basename(file)}, using default:`, err.message);
    }
    return fallback;
  }
}

async function readChatHistory() {
  const parsed = await readJsonFile(CHAT_HISTORY_FILE, null);
  if (parsed && typeof parsed.chats === "object" && Array.isArray(parsed.chatOrder)) {
    return parsed;
  }
  return { chats: {}, chatOrder: [], activeChatId: null };
}

app.get("/api/chats", async (req, res) => {
  res.json(await readChatHistory());
});

app.put("/api/chats", async (req, res) => {
  const { chats, chatOrder, activeChatId } = req.body || {};
  if (typeof chats !== "object" || chats === null || !Array.isArray(chatOrder)) {
    res.status(400).json({ error: "chats (object) and chatOrder (array) are required" });
    return;
  }
  try {
    await writeJsonFile(CHAT_HISTORY_FILE, { chats, chatOrder, activeChatId: activeChatId || null });
    res.json({ ok: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------
// Last onboarding run: so a completed pipeline's outcome survives a page
// refresh too, not just an in-flight one (see the "active" job endpoint
// further down for the in-flight case).
// ---------------------------------------------------------------------

app.get("/api/onboard/last-run", async (req, res) => {
  res.json(await readJsonFile(LAST_ONBOARD_FILE, { specSlug: null }));
});

app.delete("/api/onboard/last-run", async (req, res) => {
  try {
    await fsp.unlink(LAST_ONBOARD_FILE);
  } catch (err) {
    if (err.code !== "ENOENT") {
      res.status(500).json({ error: err.message });
      return;
    }
  }
  res.json({ ok: true });
});

const upload = multer({ storage: multer.memoryStorage() });

// ---------------------------------------------------------------------
// Shared job infrastructure: both /api/analysis and /api/onboard run a
// Python script in the background and let the client watch its combined
// stdout/stderr live via SSE, so the UI can show real progress instead of
// a single static "please wait".
// ---------------------------------------------------------------------

/** jobId -> { lines, subscribers, done, code, status, ...extra per job type }
 * status is "running" | "awaiting_approval" | "rejected" | "done" — only
 * onboarding jobs ever enter "awaiting_approval"/"rejected"; analysis jobs
 * go straight from "running" to "done". */
const jobs = new Map();

function createJob(extra) {
  const jobId = crypto.randomUUID();
  const job = {
    lines: [],
    subscribers: new Set(),
    done: false,
    code: null,
    status: "running",
    ...extra,
  };
  jobs.set(jobId, job);
  return { jobId, job };
}

function broadcastLine(job, line) {
  job.lines.push(line);
  for (const sub of job.subscribers) sub.write(`data: ${JSON.stringify(line)}\n\n`);
}

function broadcastEvent(job, eventName, payload) {
  for (const sub of job.subscribers) {
    sub.write(`event: ${eventName}\ndata: ${JSON.stringify(payload)}\n\n`);
  }
}

/** Marks a job permanently finished (success, failure, or rejection) and
 * releases every subscriber. Never called for a job that's merely paused
 * awaiting approval — that's a distinct, resumable state. */
function finishJob(jobId, job, code) {
  job.done = true;
  job.code = code;
  if (job.status !== "rejected") job.status = code === 0 ? "done" : "failed";
  broadcastEvent(job, "done", { code, status: job.status });
  for (const sub of job.subscribers) sub.end();
  job.subscribers.clear();
  setTimeout(() => jobs.delete(jobId), JOB_TTL_MS);

  // So a completed onboarding run's outcome survives a page refresh: jobs
  // only live in memory (and only for JOB_TTL_MS), but a specSlug on disk
  // is enough to re-read its ddl.sql/justification.md/analysis output any
  // time after, independent of this job object still existing.
  if (job.kind === "onboard") {
    writeJsonFile(LAST_ONBOARD_FILE, {
      specSlug: job.specSlug,
      status: job.status,
      code,
      finishedAt: new Date().toISOString(),
    }).catch((err) => console.warn("Could not persist last_onboard_run.json:", err.message));
  }
}

/** Runs `cmd args` for `job`, streaming lines live, then calls `onExit(code)`
 * — the caller decides what "done" means (finish the job outright, or, for
 * the Instrumentation Agent phase, pause for approval instead). */
function runJobProcess(job, cmd, args, timeoutMs, onExit) {
  runProcess(cmd, args, { timeoutMs, onLine: (line) => broadcastLine(job, line) })
    .then(onExit)
    .catch((err) => {
      broadcastLine(job, `error: ${err.message}`);
      onExit(-1);
    });
}

/**
 * Pull the human-meaningful failure out of an agent's output.
 *
 * The useful message (a quota/auth failure, say) is usually printed FIRST,
 * then followed by a long Python traceback — so naively showing the tail
 * hides the one line that explains what went wrong. Prefer explicit
 * `error:` lines and the final `Exception:`/`Error:` line, and fall back to
 * the tail only when nothing matches.
 */
function summarizeFailure(lines) {
  const clean = lines.map((l) => l.trim()).filter(Boolean);
  const highlights = [];

  for (const line of clean) {
    if (/^error:\s*/i.test(line) && !/^error:\s*\w+\.py failed$/i.test(line)) {
      highlights.push(line.replace(/^error:\s*/i, ""));
    }
  }

  // The last exception line of a traceback is the proximate cause.
  const lastException = [...clean]
    .reverse()
    .find((l) => /^(\w*(Exception|Error)):\s+/.test(l));
  if (lastException && !highlights.includes(lastException)) {
    highlights.push(lastException);
  }

  if (highlights.length) return [...new Set(highlights)].join("\n");
  return clean.slice(-40).join("\n") || "The agent failed with no output.";
}

function streamJob(req, res) {
  const job = jobs.get(req.params.jobId);
  if (!job) {
    res.status(404).end();
    return;
  }

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });

  for (const line of job.lines) {
    res.write(`data: ${JSON.stringify(line)}\n\n`);
  }
  if (job.done) {
    res.write(`event: done\ndata: ${JSON.stringify({ code: job.code, status: job.status })}\n\n`);
    res.end();
    return;
  }
  // A page refresh while paused for review must still see the review panel
  // (and be able to approve/reject) rather than an empty, silent stream.
  if (job.status === "awaiting_approval" && job.approvalPayload) {
    res.write(`event: awaiting-approval\ndata: ${JSON.stringify(job.approvalPayload)}\n\n`);
  }

  job.subscribers.add(res);
  req.on("close", () => job.subscribers.delete(res));
}

// ---------------------------------------------------------------------
// Chat: one question -> analysis_agent.py
// ---------------------------------------------------------------------

app.post("/api/analysis/start", async (req, res) => {
  const { question, chatId, index } = req.body || {};
  if (!question || !chatId || !index) {
    res.status(400).json({ error: "question, chatId, and index are required" });
    return;
  }

  const safeChatId = String(chatId).replace(/[^a-zA-Z0-9_-]/g, "");
  const outDir = path.join(OUT_ROOT, safeChatId, "analysis");
  await fsp.mkdir(outDir, { recursive: true });

  const args = [ANALYSIS_AGENT, question, "--out-dir", outDir, "--index", String(index)];
  const { jobId, job } = createJob({ kind: "analysis", outDir, index });
  runJobProcess(job, PYTHON_BIN, args, ANALYSIS_TIMEOUT_MS, (code) => finishJob(jobId, job, code));

  res.json({ jobId });
});

app.get("/api/analysis/stream/:jobId", streamJob);

/** Whether a job is still tracked in memory, and if so its state. The client
 * uses this after a page refresh to tell "still running, reattach to the
 * stream" apart from "gone — fall back to reading results off disk". */
app.get("/api/analysis/job/:jobId", (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job) {
    res.json({ exists: false });
    return;
  }
  res.json({ exists: true, done: job.done, status: job.status, code: job.code });
});

async function readAnalysisOutput(outDir, index) {
  const base = `q${String(index).padStart(2, "0")}`;
  const mdPath = path.join(outDir, `${base}.md`);
  const htmlPath = path.join(outDir, `${base}_report.html`);
  if (!fs.existsSync(mdPath)) return null;

  const markdown = await fsp.readFile(mdPath, "utf8");
  let html = null;
  if (fs.existsSync(htmlPath)) {
    html = await fsp.readFile(htmlPath, "utf8");
  }
  return { markdown, html };
}

app.get("/api/analysis/results/:jobId", async (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job) {
    res.status(404).json({ error: "unknown or expired job" });
    return;
  }

  const output = await readAnalysisOutput(job.outDir, job.index);
  if (job.code !== 0 || !output) {
    res.json({ error: summarizeFailure(job.lines), rawLog: job.lines.join("\n") });
    return;
  }
  res.json(output);
});

/** Disk-only result lookup, keyed by chat + question index rather than a
 * jobId. Jobs live in memory, so a server restart (or the job TTL expiring)
 * loses them — but the agent's qNN.md output is on disk and still valid, so
 * a refreshed client can recover a completed answer either way. */
app.get("/api/analysis/result-file/:chatId/:index", async (req, res) => {
  const safeChatId = String(req.params.chatId).replace(/[^a-zA-Z0-9_-]/g, "");
  const index = Number(req.params.index);
  if (!safeChatId || !Number.isInteger(index) || index < 1) {
    res.status(400).json({ error: "valid chatId and index are required" });
    return;
  }
  const outDir = path.join(OUT_ROOT, safeChatId, "analysis");
  const output = await readAnalysisOutput(outDir, index);
  if (!output) {
    res.status(404).json({ error: "no result on disk for that chat/index" });
    return;
  }
  res.json(output);
});

// ---------------------------------------------------------------------
// Onboard: upload spec.md + events.ndjson -> Instrumentation Agent (alone)
// -> pause for human approval -> orchestrator.py --skip-instrumentation
// ---------------------------------------------------------------------

/** Phase 1: run the Instrumentation Agent alone. On success, don't finish
 * the job — pause it awaiting a human decision. On failure, finish it as
 * any other failed job (there's nothing to review yet). */
function runInstrumentationPhase(jobId, job) {
  const args = [INSTRUMENTATION_AGENT, job.specDir, "--out-dir", job.outDir];
  runJobProcess(job, PYTHON_BIN, args, ANALYSIS_TIMEOUT_MS, async (code) => {
    if (code !== 0) {
      finishJob(jobId, job, code);
      return;
    }
    const readIfExists = async (p) => {
      try {
        return await fsp.readFile(p, "utf8");
      } catch (_err) {
        return "";
      }
    };
    const ddl = await readIfExists(path.join(job.outDir, "ddl.sql"));
    const justification = await readIfExists(path.join(job.outDir, "justification.md"));

    job.status = "awaiting_approval";
    job.approvalPayload = { ddl, justification };
    broadcastEvent(job, "awaiting-approval", job.approvalPayload);
    // Deliberately no finishJob() call here — the SSE connection stays open,
    // subscribers attached, until POST /approve or /reject decides what
    // happens next.
  });
}

/** Phase 2 (only reachable via approval): the rest of the pipeline, reusing
 * the schema already designed and reviewed — never re-runs instrumentation. */
function runRestOfPipeline(jobId, job) {
  const args = [ORCHESTRATOR, job.specDir, "--out-dir", job.outDir, "--skip-instrumentation"];
  runJobProcess(job, PYTHON_BIN, args, ORCHESTRATOR_TIMEOUT_MS, (code) => finishJob(jobId, job, code));
}

app.post(
  "/api/onboard/start",
  upload.fields([
    { name: "specMd", maxCount: 1 },
    { name: "eventsNdjson", maxCount: 1 },
  ]),
  async (req, res) => {
    const specName = (req.body && req.body.specName) || "";
    const specMdFile = req.files && req.files.specMd && req.files.specMd[0];
    const eventsFile =
      req.files && req.files.eventsNdjson && req.files.eventsNdjson[0];

    if (!specName || !specMdFile || !eventsFile) {
      res
        .status(400)
        .json({ error: "specName, specMd, and eventsNdjson are all required" });
      return;
    }

    const slug = slugify(specName);
    const specDir = await uniqueDir(UPLOAD_ROOT, slug);
    await fsp.mkdir(specDir, { recursive: true });
    await fsp.writeFile(path.join(specDir, "spec.md"), specMdFile.buffer);
    await fsp.writeFile(path.join(specDir, "events.ndjson"), eventsFile.buffer);

    const outDir = path.join(REPO_ROOT, "out", path.basename(specDir));
    const { jobId, job } = createJob({
      kind: "onboard",
      specSlug: path.basename(specDir),
      specDir: String(specDir),
      outDir,
    });
    runInstrumentationPhase(jobId, job);

    res.json({ jobId, specSlug: job.specSlug });
  }
);

app.get("/api/onboard/stream/:jobId", streamJob);

/**
 * The most recent onboarding job that hasn't finished — how a freshly
 * loaded page discovers "there's a pipeline still running (or paused for
 * approval), reattach to it" instead of losing it on refresh. Jobs live in
 * this process, so if the server is up, so is the orchestrator child it
 * spawned; if the server died, the job is genuinely gone and this correctly
 * reports nothing.
 */
app.get("/api/onboard/active", (req, res) => {
  for (const [jobId, job] of [...jobs.entries()].reverse()) {
    if (job.kind === "onboard" && !job.done) {
      res.json({
        jobId,
        specSlug: job.specSlug,
        status: job.status,
        approvalPayload: job.status === "awaiting_approval" ? job.approvalPayload : null,
      });
      return;
    }
  }
  res.json({ jobId: null });
});

app.post("/api/onboard/approve/:jobId", (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job || job.status !== "awaiting_approval") {
    res.status(400).json({ error: "this job is not awaiting approval" });
    return;
  }
  job.status = "running";
  res.json({ ok: true });
  runRestOfPipeline(req.params.jobId, job);
});

app.post("/api/onboard/reject/:jobId", (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job || job.status !== "awaiting_approval") {
    res.status(400).json({ error: "this job is not awaiting approval" });
    return;
  }
  job.status = "rejected";
  broadcastLine(job, "Pipeline stopped: the proposed schema was rejected.");
  finishJob(req.params.jobId, job, null);
  res.json({ ok: true });
});

/** Disk-only: reads every qNN.md (+ qNN_report.html) for a spec, keyed by
 * its slug rather than a jobId — works long after the job object itself
 * has been garbage-collected from memory. */
async function readOnboardResultsBySlug(specSlug) {
  const analysisDir = path.join(REPO_ROOT, "out", specSlug, "analysis");
  if (!fs.existsSync(analysisDir)) return [];

  const files = (await fsp.readdir(analysisDir))
    .filter((f) => /^q\d+\.md$/.test(f))
    .sort();

  const results = [];
  for (const file of files) {
    const markdown = await fsp.readFile(path.join(analysisDir, file), "utf8");
    const base = file.replace(/\.md$/, "");
    const htmlPath = path.join(analysisDir, `${base}_report.html`);
    let html = null;
    if (fs.existsSync(htmlPath)) {
      html = await fsp.readFile(htmlPath, "utf8");
    }
    results.push({ markdown, html });
  }
  return results;
}

app.get("/api/onboard/results/:jobId", async (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job) {
    res.status(404).json({ error: "unknown or expired job" });
    return;
  }
  res.json({ results: await readOnboardResultsBySlug(job.specSlug) });
});

app.get("/api/onboard/results-by-slug/:specSlug", async (req, res) => {
  res.json({ results: await readOnboardResultsBySlug(req.params.specSlug) });
});

app.listen(PORT, () => {
  console.log(`Atlys Analytics web UI running at http://localhost:${PORT}`);
  console.log(`Using Python: ${PYTHON_BIN}`);
});
