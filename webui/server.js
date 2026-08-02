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
 *   POST /api/onboard/start           -> saves an uploaded spec.md +
 *                                         events.ndjson, then runs
 *                                         orchestrator.py in the background
 *   GET  /api/onboard/stream/:jobId    -> SSE log stream for that run
 *   GET  /api/onboard/results/:jobId   -> analysis/qNN.md (+ qNN_report.html)
 *                                         once the run finishes
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
const ORCHESTRATOR = path.join(REPO_ROOT, "orchestrator.py");
const OUT_ROOT = path.join(REPO_ROOT, "out", "webui_chats");
const UPLOAD_ROOT = path.join(REPO_ROOT, "uploads");

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
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const upload = multer({ storage: multer.memoryStorage() });

// ---------------------------------------------------------------------
// Shared job infrastructure: both /api/analysis and /api/onboard run a
// Python script in the background and let the client watch its combined
// stdout/stderr live via SSE, so the UI can show real progress instead of
// a single static "please wait".
// ---------------------------------------------------------------------

/** jobId -> { lines, subscribers, done, code, ...extra fields per job type } */
const jobs = new Map();

function createJob(extra) {
  const jobId = crypto.randomUUID();
  const job = { lines: [], subscribers: new Set(), done: false, code: null, ...extra };
  jobs.set(jobId, job);
  return { jobId, job };
}

/** Spawn `cmd args` for `job`, broadcasting each line to subscribers as it
 * happens and firing a `done` event (with the exit code) on completion. */
function startJob(jobId, job, cmd, args, timeoutMs) {
  const broadcastLine = (line) => {
    job.lines.push(line);
    for (const sub of job.subscribers) sub.write(`data: ${JSON.stringify(line)}\n\n`);
  };
  const finish = (code) => {
    job.done = true;
    job.code = code;
    for (const sub of job.subscribers) {
      sub.write(`event: done\ndata: ${JSON.stringify({ code })}\n\n`);
      sub.end();
    }
    job.subscribers.clear();
    setTimeout(() => jobs.delete(jobId), JOB_TTL_MS);
  };

  runProcess(cmd, args, { timeoutMs, onLine: broadcastLine })
    .then(finish)
    .catch((err) => {
      broadcastLine(`error: ${err.message}`);
      finish(-1);
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
    res.write(`event: done\ndata: ${JSON.stringify({ code: job.code })}\n\n`);
    res.end();
    return;
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
  const { jobId, job } = createJob({ outDir, index });
  startJob(jobId, job, PYTHON_BIN, args, ANALYSIS_TIMEOUT_MS);

  res.json({ jobId });
});

app.get("/api/analysis/stream/:jobId", streamJob);

app.get("/api/analysis/results/:jobId", async (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job) {
    res.status(404).json({ error: "unknown or expired job" });
    return;
  }

  const base = `q${String(job.index).padStart(2, "0")}`;
  const mdPath = path.join(job.outDir, `${base}.md`);
  const htmlPath = path.join(job.outDir, `${base}_report.html`);

  if (job.code !== 0 || !fs.existsSync(mdPath)) {
    res.json({ error: summarizeFailure(job.lines), rawLog: job.lines.join("\n") });
    return;
  }

  const markdown = await fsp.readFile(mdPath, "utf8");
  let html = null;
  if (fs.existsSync(htmlPath)) {
    html = await fsp.readFile(htmlPath, "utf8");
  }
  res.json({ markdown, html });
});

// ---------------------------------------------------------------------
// Onboard: upload spec.md + events.ndjson -> orchestrator.py (streamed)
// ---------------------------------------------------------------------

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

    const { jobId, job } = createJob({ specSlug: path.basename(specDir) });
    startJob(jobId, job, PYTHON_BIN, [ORCHESTRATOR, specDir], ORCHESTRATOR_TIMEOUT_MS);

    res.json({ jobId, specSlug: job.specSlug });
  }
);

app.get("/api/onboard/stream/:jobId", streamJob);

app.get("/api/onboard/results/:jobId", async (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job) {
    res.status(404).json({ error: "unknown or expired job" });
    return;
  }

  const analysisDir = path.join(REPO_ROOT, "out", job.specSlug, "analysis");
  if (!fs.existsSync(analysisDir)) {
    res.json({ results: [] });
    return;
  }

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
  res.json({ results });
});

app.listen(PORT, () => {
  console.log(`Atlys Analytics web UI running at http://localhost:${PORT}`);
  console.log(`Using Python: ${PYTHON_BIN}`);
});
