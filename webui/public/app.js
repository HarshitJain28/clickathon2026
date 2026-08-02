"use strict";

/**
 * Atlys Analytics — client-side app logic.
 *
 * Two views, toggled via state.view:
 *   "chat"     — ChatGPT-style thread. Each question starts a job via
 *                /api/analysis/start (-> analysis_agent.py), streams that
 *                agent's live progress over SSE into a step feed, then
 *                swaps in the finished markdown/HTML answer.
 *   "onboard"  — upload spec.md + events.ndjson, POST to
 *                /api/onboard/start (-> orchestrator.py), track its five
 *                pipeline stages live via SSE, then render the resulting
 *                analysis outputs.
 *
 * Chat state (chats, their messages, which one is active) is persisted on
 * the server (out/webui_chats/chat_history.json — see server.js's
 * GET/PUT /api/chats), not browser localStorage: it survives a refresh,
 * a different browser, or a cleared profile, all identically, since the
 * server is the single source of truth rather than something per-origin
 * living inside one browser.
 */

const DEFAULT_CHAT_TITLE = "Test";

const state = {
  chats: {}, // id -> { id, title, messages: [{role, content, html, error}] }
  chatOrder: [], // insertion order, oldest first
  activeChatId: null,
  view: "chat",
};

function uid() {
  return Math.random().toString(16).slice(2, 10);
}

/** Persists chats/chatOrder/activeChatId to disk via the server. Fire-and-
 * forget from callers' point of view — errors are logged, not thrown, so a
 * transient network hiccup never breaks the UI (it just risks that one
 * save not surviving a refresh). */
function saveChatState() {
  fetch("/api/chats", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chats: state.chats,
      chatOrder: state.chatOrder,
      activeChatId: state.activeChatId,
    }),
  }).catch((err) => console.warn("Could not persist chat history:", err.message));
}

/** Returns true if a valid saved session was restored into `state`. */
async function loadChatState() {
  try {
    const res = await fetch("/api/chats");
    const data = await res.json();
    if (!data || typeof data.chats !== "object" || !Array.isArray(data.chatOrder)) {
      return false;
    }
    const chatOrder = data.chatOrder.filter((id) => data.chats[id]);
    if (!chatOrder.length) return false;

    state.chats = data.chats;
    state.chatOrder = chatOrder;
    state.activeChatId =
      data.activeChatId && state.chats[data.activeChatId]
        ? data.activeChatId
        : chatOrder[chatOrder.length - 1];
    return true;
  } catch (err) {
    console.warn("Could not load persisted chat history:", err.message);
    return false;
  }
}

function createChat() {
  const id = uid();
  state.chats[id] = { id, title: DEFAULT_CHAT_TITLE, messages: [] };
  state.chatOrder.push(id);
  state.activeChatId = id;
  saveChatState();
  return id;
}

function activeChat() {
  return state.chats[state.activeChatId];
}

function chatTitleFromQuestion(question) {
  const q = question.trim().replace(/\s+/g, " ");
  return q.length <= 48 ? q : q.slice(0, 45).trimEnd() + "…";
}

// ----------------------------------------------------------------------
// Rendering
// ----------------------------------------------------------------------

function renderAll() {
  renderChatList();
  document.getElementById("chatView").style.display =
    state.view === "chat" ? "" : "none";
  document.getElementById("onboardView").style.display =
    state.view === "onboard" ? "" : "none";
  document.getElementById("chatInputBar").style.display =
    state.view === "chat" ? "" : "none";
  if (state.view === "chat") renderMessages();
  saveChatState();
}

function renderChatList() {
  const list = document.getElementById("chatList");
  list.innerHTML = "";
  for (let i = state.chatOrder.length - 1; i >= 0; i -= 1) {
    const chat = state.chats[state.chatOrder[i]];
    if (!chat) continue;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chat-row" + (chat.id === state.activeChatId ? " active" : "");
    btn.textContent = chat.title;
    btn.title = chat.title;
    btn.addEventListener("click", () => {
      state.activeChatId = chat.id;
      state.view = "chat";
      renderAll();
    });
    list.appendChild(btn);
  }
}

function reportBlock(html) {
  const details = document.createElement("details");
  details.open = true;
  const summary = document.createElement("summary");
  summary.textContent = "📊 Full report";
  const iframe = document.createElement("iframe");
  iframe.className = "report-frame";
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.srcdoc = html;
  details.appendChild(summary);
  details.appendChild(iframe);
  return details;
}

function renderMessageEl(msg) {
  const row = document.createElement("div");
  row.className = "message " + msg.role;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = msg.role === "user" ? "🧑" : "🤖";

  const content = document.createElement("div");
  content.className = "content" + (msg.error ? " error-content" : "");
  content.innerHTML = renderMarkdown(msg.content);

  if (msg.html) {
    content.appendChild(reportBlock(msg.html));
  }

  // Full traceback stays available for debugging, but collapsed by default
  // so it never buries the readable summary above it.
  if (msg.rawLog) {
    const details = document.createElement("details");
    details.className = "raw-log-details";
    const summary = document.createElement("summary");
    summary.textContent = "Show full log";
    const pre = document.createElement("pre");
    pre.className = "log-box";
    pre.textContent = msg.rawLog;
    details.appendChild(summary);
    details.appendChild(pre);
    content.appendChild(details);
  }

  row.appendChild(avatar);
  row.appendChild(content);
  return row;
}

function renderMessages() {
  const chat = activeChat();
  const hero = document.getElementById("hero");
  const container = document.getElementById("messages");
  container.innerHTML = "";

  hero.style.display = chat.messages.length === 0 ? "" : "none";

  for (const msg of chat.messages) {
    container.appendChild(renderMessageEl(msg));
  }
  window.scrollTo(0, document.body.scrollHeight);
}

// ----------------------------------------------------------------------
// Chat: sending a question
// ----------------------------------------------------------------------

/** The markdown analysis_agent.py writes is "## Question\n...\n\n##
 * Answer\n...", meant to stand alone as a file. In a chat thread the
 * question is already visible as its own bubble, so only the Answer
 * section is shown here — otherwise every reply would redundantly repeat
 * the question back as a big heading. */
function extractAnswerSection(markdown) {
  const match = markdown.match(/##\s*Answer\s*\n([\s\S]*)/i);
  return match ? match[1].trim() : markdown.trim();
}

function buildPendingAssistantRow() {
  const row = document.createElement("div");
  row.className = "message assistant";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "🤖";

  const content = document.createElement("div");
  content.className = "content";

  const header = document.createElement("div");
  header.className = "pending-header";
  header.innerHTML = '<span class="pending-dot"></span> Analyzing your question…';

  const stepList = document.createElement("div");
  stepList.className = "step-list";

  const rawDetails = document.createElement("details");
  rawDetails.className = "raw-log-details";
  const rawSummary = document.createElement("summary");
  rawSummary.textContent = "Show raw log";
  const rawPre = document.createElement("pre");
  rawPre.className = "log-box";
  rawDetails.appendChild(rawSummary);
  rawDetails.appendChild(rawPre);

  content.appendChild(header);
  content.appendChild(stepList);
  content.appendChild(rawDetails);
  row.appendChild(avatar);
  row.appendChild(content);

  return { row, feed: new StepFeed({ listEl: stepList, rawEl: rawPre }) };
}

/** Records the finished message in chat state, and swaps the imperative
 * "live" bubble for the standard rendered one so later full re-renders
 * (switching chats and back, etc.) reproduce it identically. */
function finalizeAssistantMessage(chat, pendingRow, message) {
  chat.messages.push(message);
  saveChatState();

  // If the user switched chats mid-request, the live bubble was already
  // discarded by a re-render — replaceWith on a detached node would
  // silently drop the answer, so fall back to a full re-render instead.
  if (pendingRow.isConnected) {
    pendingRow.replaceWith(renderMessageEl(message));
  } else if (chat.id === state.activeChatId) {
    renderMessages();
  }

  if (chat.id === state.activeChatId) {
    window.scrollTo(0, document.body.scrollHeight);
  }
}

/** Set while the page is being torn down (refresh/navigation). EventSource
 * fires onerror as the page unloads, which is NOT a real failure — without
 * this guard a refresh would write a bogus "Lost connection" message into
 * the persisted history, which is exactly what it did before. */
let pageUnloading = false;
window.addEventListener("beforeunload", () => {
  pageUnloading = true;
});

function setInputEnabled(enabled) {
  const promptInput = document.getElementById("promptInput");
  const sendBtn = document.getElementById("sendBtn");
  promptInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
  if (enabled) promptInput.focus();
}

/**
 * Attach to a running analysis job and drive the live bubble until it
 * settles. Used both for a freshly-started question and for reattaching to
 * a job that was still in flight when the page was refreshed.
 */
function watchAnalysisJob(chat, jobId, index, row, feed) {
  let settled = false;
  const es = new EventSource(`/api/analysis/stream/${jobId}`);

  // Idempotency guard: EventSource can legitimately fire onerror for a
  // transient blip and then still deliver "done" once it auto-reconnects
  // (or vice versa, in some race), so settle() itself must refuse a second
  // call rather than trusting every caller to check `settled` first.
  const settle = (finalMsg, ok) => {
    if (settled) return;
    settled = true;
    es.close();
    feed.finish(ok);
    delete chat.pendingJob;
    finalizeAssistantMessage(chat, row, finalMsg);
    setInputEnabled(true);
  };

  es.onmessage = (e) => {
    feed.push(JSON.parse(e.data));
    if (chat.id === state.activeChatId) {
      window.scrollTo(0, document.body.scrollHeight);
    }
  };

  es.addEventListener("done", async () => {
    try {
      const resultsRes = await fetch(`/api/analysis/results/${jobId}`);
      const data = await resultsRes.json();
      if (data.error) {
        settle(
          {
            role: "assistant",
            content:
              "⚠️ **The Analysis Agent couldn't answer this question.**\n\n```\n" +
              data.error +
              "\n```",
            error: true,
            rawLog: data.rawLog || null,
          },
          false
        );
      } else {
        settle(
          {
            role: "assistant",
            content: extractAnswerSection(data.markdown),
            html: data.html || null,
          },
          true
        );
      }
    } catch (err) {
      settle(
        { role: "assistant", content: "⚠️ Request failed: " + err.message, error: true },
        false
      );
    }
  });

  es.onerror = () => {
    if (settled) return; // server closes the stream normally on completion
    if (pageUnloading) {
      // The page is going away, not the job — leave chat.pendingJob intact
      // so the next load reattaches instead of recording a false failure.
      es.close();
      return;
    }
    // EventSource fires onerror on ANY hiccup — including ones it recovers
    // from on its own by auto-reconnecting (readyState goes to CONNECTING,
    // not CLOSED). Only readyState === CLOSED means the browser has well
    // and truly given up; anything else, just wait for it to reconnect
    // rather than declaring the job dead while it's still actually running.
    if (es.readyState !== EventSource.CLOSED) return;
    settle(
      { role: "assistant", content: "⚠️ Lost connection to the Analysis Agent.", error: true },
      false
    );
  };
}

async function sendPrompt(question) {
  const chat = activeChat();
  chat.messages.push({ role: "user", content: question });
  if (chat.title === DEFAULT_CHAT_TITLE) {
    chat.title = chatTitleFromQuestion(question);
  }
  renderAll();
  setInputEnabled(false);

  const index = chat.messages.filter((m) => m.role === "user").length;

  const container = document.getElementById("messages");
  const { row, feed } = buildPendingAssistantRow();
  container.appendChild(row);
  window.scrollTo(0, document.body.scrollHeight);

  let jobId;
  try {
    const startRes = await fetch("/api/analysis/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, chatId: chat.id, index }),
    });
    const startData = await startRes.json();
    if (startData.error) throw new Error(startData.error);
    jobId = startData.jobId;
  } catch (err) {
    finalizeAssistantMessage(chat, row, {
      role: "assistant",
      content: "⚠️ Request failed: " + err.message,
      error: true,
    });
    setInputEnabled(true);
    return;
  }

  // Persisted so a refresh mid-run can reattach to this same job rather
  // than losing it (see resumePendingJob).
  chat.pendingJob = { jobId, index };
  saveChatState();

  watchAnalysisJob(chat, jobId, index, row, feed);
}

/**
 * After a page load, pick up a question that was still running when the
 * page went away. Three cases:
 *   - job still alive in memory  -> reattach to its SSE stream
 *   - job gone but qNN.md exists -> it finished while we were away; show it
 *   - job gone and no output     -> it was genuinely interrupted; say so
 */
async function resumePendingJob(chat) {
  const pending = chat.pendingJob;
  if (!pending) return;

  const container = document.getElementById("messages");
  const { row, feed } = buildPendingAssistantRow();
  container.appendChild(row);

  let alive = false;
  try {
    const statusRes = await fetch(`/api/analysis/job/${pending.jobId}`);
    const status = await statusRes.json();
    alive = status.exists && !status.done;
  } catch (_err) {
    alive = false;
  }

  if (alive) {
    setInputEnabled(false);
    watchAnalysisJob(chat, pending.jobId, pending.index, row, feed);
    return;
  }

  // Not running anymore — recover the answer from disk if the agent got
  // far enough to write one.
  try {
    const res = await fetch(`/api/analysis/result-file/${chat.id}/${pending.index}`);
    if (res.ok) {
      const data = await res.json();
      feed.finish(true);
      delete chat.pendingJob;
      finalizeAssistantMessage(chat, row, {
        role: "assistant",
        content: extractAnswerSection(data.markdown),
        html: data.html || null,
      });
      return;
    }
  } catch (_err) {
    /* fall through to the interrupted message below */
  }

  feed.finish(false);
  delete chat.pendingJob;
  finalizeAssistantMessage(chat, row, {
    role: "assistant",
    content:
      "⚠️ This question was interrupted (the server restarted or the run " +
      "expired before it finished). Ask it again to retry.",
    error: true,
  });
}

// ----------------------------------------------------------------------
// Onboard spec
// ----------------------------------------------------------------------

function renderOnboardResults(results, resultsEl = document.getElementById("onboardResults")) {
  resultsEl.innerHTML = "";

  if (!results.length) {
    resultsEl.textContent =
      "The pipeline ran, but no PM questions were found to answer.";
    return;
  }

  const heading = document.createElement("h4");
  heading.textContent = "Results";
  resultsEl.appendChild(heading);

  for (const r of results) {
    const box = document.createElement("div");
    box.className = "result-box";
    box.innerHTML = renderMarkdown(r.markdown);
    if (r.html) {
      box.appendChild(reportBlock(r.html));
    }
    resultsEl.appendChild(box);
    resultsEl.appendChild(document.createElement("hr"));
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Wires a styled drag-and-drop zone around a hidden native <input
 * type="file">, keeping the input as the single source of truth (so
 * existing `input.files` reads elsewhere keep working unchanged). */
function initDropzone(dropzoneId, onChange) {
  const dropzone = document.getElementById(dropzoneId);
  const input = dropzone.querySelector(".dropzone-input");
  const emptyEl = dropzone.querySelector(".dropzone-empty");
  const fileEl = dropzone.querySelector(".dropzone-file");
  const fileNameEl = dropzone.querySelector(".dropzone-file-name");
  const removeBtn = dropzone.querySelector(".dropzone-remove");

  const update = () => {
    const file = input.files[0];
    if (file) {
      emptyEl.style.display = "none";
      fileEl.style.display = "flex";
      fileNameEl.textContent = `${file.name} — ${formatBytes(file.size)}`;
    } else {
      emptyEl.style.display = "flex";
      fileEl.style.display = "none";
    }
    onChange();
  };

  input.addEventListener("change", update);

  removeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    input.value = "";
    update();
  });

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      update();
    }
  });
}

const ONBOARD_STATUS_LABELS = {
  running: "Running",
  awaiting_approval: "Awaiting approval",
  done: "Done",
  failed: "Failed",
  rejected: "Rejected",
};

function formatTimestamp(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch (_err) {
    return iso;
  }
}

/** Every onboarding run this server has ever started, read straight from
 * disk — independent of whether anything is currently in flight. This is
 * what lets a finished run (or one from days ago, or before a server
 * restart) still be opened and reviewed. */
async function renderOnboardHistory() {
  // Whenever the history is (re)rendered, it should actually be visible —
  // the one place that hides it is watchOnboardJob, while a run is active.
  document.getElementById("onboardHistorySection").style.display = "";

  const listEl = document.getElementById("onboardHistoryList");
  let data;
  try {
    const res = await fetch("/api/onboard/history");
    data = await res.json();
  } catch (err) {
    listEl.innerHTML = "";
    listEl.textContent = "Could not load onboarding history: " + err.message;
    return;
  }

  listEl.innerHTML = "";
  const order = data.order || [];
  if (!order.length) {
    const empty = document.createElement("div");
    empty.className = "onboard-history-empty";
    empty.textContent = "No specs onboarded yet.";
    listEl.appendChild(empty);
    return;
  }

  for (let i = order.length - 1; i >= 0; i -= 1) {
    const run = data.runs[order[i]];
    if (!run) continue;

    const item = document.createElement("button");
    item.type = "button";
    item.className = "onboard-history-item";

    const name = document.createElement("span");
    name.className = "onboard-history-item-name";
    const when = formatTimestamp(run.finishedAt || run.startedAt);
    name.textContent = run.specSlug + (when ? " — " + when : "");

    const status = document.createElement("span");
    status.className = "onboard-history-status status-" + run.status;
    status.textContent = ONBOARD_STATUS_LABELS[run.status] || run.status;

    item.appendChild(name);
    item.appendChild(status);
    item.addEventListener("click", () => openOnboardHistoryDetail(run.specSlug));
    listEl.appendChild(item);
  }
}

async function openOnboardHistoryDetail(specSlug) {
  const detail = document.getElementById("onboardHistoryDetail");
  const titleEl = document.getElementById("onboardHistoryDetailTitle");
  const statusEl = document.getElementById("onboardHistoryDetailStatus");
  const ddlEl = document.getElementById("onboardHistoryDdl");
  const justificationEl = document.getElementById("onboardHistoryJustification");
  const resultsEl = document.getElementById("onboardHistoryResults");

  titleEl.textContent = "📤 " + specSlug;
  statusEl.textContent = "Loading…";
  ddlEl.textContent = "";
  justificationEl.innerHTML = "";
  resultsEl.innerHTML = "";
  detail.style.display = "";
  detail.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const res = await fetch(`/api/onboard/run/${specSlug}`);
    const run = await res.json();
    if (run.error) {
      statusEl.textContent = "⚠️ " + run.error;
      return;
    }

    const statusLabel = ONBOARD_STATUS_LABELS[run.status] || run.status;
    const when = formatTimestamp(run.finishedAt || run.startedAt);
    statusEl.textContent = `${statusLabel}${when ? " — " + when : ""}`;

    ddlEl.textContent = run.ddl || "(no ddl.sql on disk)";
    justificationEl.innerHTML = renderMarkdown(run.justification || "_No justification.md on disk._");
    renderOnboardResults(run.results || [], resultsEl);
  } catch (err) {
    statusEl.textContent = "⚠️ Request failed: " + err.message;
  }
}

document.getElementById("closeHistoryDetailBtn").addEventListener("click", () => {
  document.getElementById("onboardHistoryDetail").style.display = "none";
});

function initOnboardForm() {
  const formSection = document.getElementById("onboardFormSection");
  const collapsedBar = document.getElementById("onboardCollapsedBar");
  const collapsedLabel = document.getElementById("onboardCollapsedLabel");
  const onboardAnotherBtn = document.getElementById("onboardAnotherBtn");

  const specNameInput = document.getElementById("specNameInput");
  const specMdInput = document.getElementById("specMdInput");
  const eventsInput = document.getElementById("eventsInput");
  const runBtn = document.getElementById("runOrchestratorBtn");
  const statusEl = document.getElementById("onboardStatus");
  const pipelineEl = document.getElementById("onboardPipeline");
  const stepListEl = document.getElementById("onboardStepList");
  const rawDetailsEl = document.getElementById("onboardRawDetails");
  const rawLogEl = document.getElementById("onboardRawLog");
  const resultsEl = document.getElementById("onboardResults");

  const approvalPanel = document.getElementById("approvalPanel");
  const approvalDdlEl = document.getElementById("approvalDdl");
  const approvalJustificationEl = document.getElementById("approvalJustification");
  const approveBtn = document.getElementById("approveBtn");
  const rejectBtn = document.getElementById("rejectBtn");

  let currentJobId = null;

  const hideApprovalPanel = () => {
    approvalPanel.style.display = "none";
    approvalDdlEl.textContent = "";
    approvalJustificationEl.innerHTML = "";
    approveBtn.disabled = false;
    rejectBtn.disabled = false;
  };

  approveBtn.addEventListener("click", async () => {
    approveBtn.disabled = true;
    rejectBtn.disabled = true;
    statusEl.textContent = "Approved — continuing the pipeline…";
    hideApprovalPanel();
    try {
      const res = await fetch(`/api/onboard/approve/${currentJobId}`, { method: "POST" });
      const data = await res.json();
      if (data.error) statusEl.textContent = "⚠️ " + data.error;
    } catch (err) {
      statusEl.textContent = "⚠️ Request failed: " + err.message;
    }
  });

  rejectBtn.addEventListener("click", async () => {
    approveBtn.disabled = true;
    rejectBtn.disabled = true;
    try {
      const res = await fetch(`/api/onboard/reject/${currentJobId}`, { method: "POST" });
      const data = await res.json();
      if (data.error) statusEl.textContent = "⚠️ " + data.error;
    } catch (err) {
      statusEl.textContent = "⚠️ Request failed: " + err.message;
    }
    hideApprovalPanel();
  });

  const updateRunButtonState = () => {
    runBtn.disabled = !(
      specNameInput.value.trim() &&
      specMdInput.files.length &&
      eventsInput.files.length
    );
  };
  specNameInput.addEventListener("input", updateRunButtonState);
  initDropzone("specMdDropzone", updateRunButtonState);
  initDropzone("eventsDropzone", updateRunButtonState);

  /** Clears everything and shows the upload form again, ready for a fresh
   * spec. Only reachable once a prior run has fully settled (see the
   * "done" handler below), so it can never race a still-running job. */
  onboardAnotherBtn.addEventListener("click", () => {
    formSection.style.display = "";
    collapsedBar.style.display = "none";
    onboardAnotherBtn.style.display = "none";

    specNameInput.value = "";
    specMdInput.value = "";
    eventsInput.value = "";
    document.querySelectorAll(".dropzone").forEach((dz) => {
      dz.querySelector(".dropzone-empty").style.display = "flex";
      dz.querySelector(".dropzone-file").style.display = "none";
    });

    statusEl.textContent = "";
    pipelineEl.style.display = "none";
    pipelineEl.innerHTML = "";
    stepListEl.style.display = "none";
    stepListEl.innerHTML = "";
    rawDetailsEl.style.display = "none";
    rawLogEl.textContent = "";
    resultsEl.innerHTML = "";
    hideApprovalPanel();
    currentJobId = null;
    updateRunButtonState();
  });

  /** Puts the view into "a run is in flight" shape and attaches to its SSE
   * stream. Shared by a freshly-started run and by reattaching to one that
   * was already running when the page loaded (see resumeOnboardJob), so a
   * refresh mid-pipeline recovers instead of losing everything. */
  function watchOnboardJob(jobId, specSlug) {
    currentJobId = jobId;

    // Collapse the upload form now that a run is actually in flight, so the
    // pipeline/results below have the room instead of sitting under a form
    // that's no longer actionable.
    formSection.style.display = "none";
    collapsedBar.style.display = "flex";
    collapsedLabel.textContent = `📤 ${specSlug}`;
    onboardAnotherBtn.style.display = "none";
    pipelineEl.style.display = "";
    stepListEl.style.display = "";
    rawDetailsEl.style.display = "";

    // Old runs are just clutter under an active one — tuck them away while
    // this run is in flight; they come back once it settles (see the
    // "done" handler's renderOnboardHistory() call, which re-shows them).
    document.getElementById("onboardHistorySection").style.display = "none";
    document.getElementById("onboardHistoryDetail").style.display = "none";

    statusEl.textContent = `Onboarding ${specSlug} — this can take several minutes.`;
    const pipeline = new PipelineTracker(pipelineEl);
    const feed = new StepFeed({ listEl: stepListEl, rawEl: rawLogEl });

    let settled = false;
    const es = new EventSource(`/api/onboard/stream/${jobId}`);

    es.onmessage = (e) => {
      const line = JSON.parse(e.data);
      // A stage marker advances the pipeline tracker; anything else is a
      // detail line for the step feed. Both still land in the raw log.
      if (pipeline.push(line)) {
        if (rawLogEl) {
          rawLogEl.textContent += (rawLogEl.textContent ? "\n" : "") + line;
        }
        // A new stage starting resets the detail feed, so the visible steps
        // always belong to the stage currently running.
        stepListEl.innerHTML = "";
        feed.steps = [];
        return;
      }
      feed.push(line);
    };

    // The human-in-the-loop gate: the Instrumentation Agent finished and the
    // job is now paused, waiting on the Approve/Reject click below — the
    // server won't run anything further until one of those POSTs arrives.
    es.addEventListener("awaiting-approval", (e) => {
      const { ddl, justification } = JSON.parse(e.data);
      approvalDdlEl.textContent = ddl || "(no ddl.sql was produced)";
      approvalJustificationEl.innerHTML = renderMarkdown(
        justification || "_No justification.md was produced._"
      );
      approvalPanel.style.display = "";
      statusEl.textContent = "Schema designed — review it below before continuing.";
      window.scrollTo(0, document.body.scrollHeight);
      // History stays hidden through the approval pause too — it's still
      // "a run in flight" needing the user's attention, same as while it's
      // actively streaming. It reappears once the run truly settles (see
      // the "done" handler).
    });

    es.addEventListener("done", async (e) => {
      if (settled) return; // guards against a stray duplicate event
      settled = true;
      const { code, status } = JSON.parse(e.data);
      es.close();
      const succeeded = status !== "rejected" && code === 0;
      pipeline.finish(succeeded);
      feed.finish(succeeded);

      if (status === "rejected") {
        statusEl.textContent =
          `🚫 Schema rejected — pipeline stopped for ${specSlug}. ` +
          "Nothing was created in ClickHouse or the wiki.";
      } else if (code === 0) {
        statusEl.textContent = `✅ Spec ${specSlug} onboarded successfully.`;
        try {
          const resultsRes = await fetch(`/api/onboard/results/${jobId}`);
          const resultsData = await resultsRes.json();
          renderOnboardResults(resultsData.results || []);
        } catch (err) {
          statusEl.textContent += ` (couldn't load results: ${err.message})`;
        }
      } else {
        statusEl.textContent = `⚠️ The pipeline failed (exit code ${code}). See the log below.`;
      }
      onboardAnotherBtn.style.display = "";
      updateRunButtonState();
      renderOnboardHistory();
    });

    es.onerror = () => {
      if (settled) return; // server closes the stream normally on completion
      if (pageUnloading) {
        // Refresh/navigation, not a dead pipeline — the orchestrator keeps
        // running server-side and the next load reattaches to it.
        es.close();
        return;
      }
      // EventSource fires onerror on ANY hiccup, including ones it recovers
      // from on its own via auto-reconnect (readyState -> CONNECTING, not
      // CLOSED). Only a truly closed connection means the run is actually
      // unreachable — otherwise wait for it to reconnect rather than
      // declaring a multi-minute pipeline dead over a transient blip.
      if (es.readyState !== EventSource.CLOSED) return;
      settled = true;
      es.close();
      pipeline.finish(false);
      feed.finish(false);
      statusEl.textContent = "⚠️ Lost connection to the orchestrator.";
      onboardAnotherBtn.style.display = "";
      updateRunButtonState();
    };
  }

  runBtn.addEventListener("click", async () => {
    runBtn.disabled = true;
    statusEl.textContent = "";
    pipelineEl.innerHTML = "";
    stepListEl.innerHTML = "";
    rawLogEl.textContent = "";
    resultsEl.innerHTML = "";
    hideApprovalPanel();

    const form = new FormData();
    form.append("specName", specNameInput.value.trim());
    form.append("specMd", specMdInput.files[0]);
    form.append("eventsNdjson", eventsInput.files[0]);

    try {
      const res = await fetch("/api/onboard/start", { method: "POST", body: form });
      const data = await res.json();
      if (data.error) {
        statusEl.textContent = "⚠️ " + data.error;
        updateRunButtonState();
        return;
      }
      watchOnboardJob(data.jobId, data.specSlug);
    } catch (err) {
      statusEl.textContent = "⚠️ Request failed: " + err.message;
      updateRunButtonState();
    }
  });

  /** On page load, reattach to an onboarding run that's still going (or is
   * paused awaiting approval). Returns true if one was found, so boot can
   * switch straight to the onboard view. */
  async function resumeOnboardJob() {
    let active;
    try {
      const res = await fetch("/api/onboard/active");
      active = await res.json();
    } catch (_err) {
      return false;
    }
    if (!active || !active.jobId) return false;

    // Reattaching replays every line the job has emitted so far, which
    // rebuilds the pipeline tracker and step feed from scratch — and the
    // server re-sends `awaiting-approval` if it's paused, so the review
    // panel comes back too.
    watchOnboardJob(active.jobId, active.specSlug);
    return true;
  }

  return { resumeOnboardJob };
}

// ----------------------------------------------------------------------
// Boot
// ----------------------------------------------------------------------

function initChatInput() {
  const promptInput = document.getElementById("promptInput");
  const sendBtn = document.getElementById("sendBtn");

  const autosize = () => {
    promptInput.style.height = "auto";
    promptInput.style.height = Math.min(promptInput.scrollHeight, 160) + "px";
  };

  const submit = () => {
    const text = promptInput.value.trim();
    if (!text) return;
    promptInput.value = "";
    autosize();
    sendPrompt(text);
  };

  sendBtn.addEventListener("click", submit);
  promptInput.addEventListener("input", autosize);
  promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  });
}

document.getElementById("newChatBtn").addEventListener("click", () => {
  createChat();
  state.view = "chat";
  renderAll();
});
document.getElementById("onboardBtn").addEventListener("click", () => {
  state.view = "onboard";
  renderAll();
  renderOnboardHistory();
});
document.getElementById("backToChatBtn").addEventListener("click", () => {
  state.view = "chat";
  renderAll();
});

initChatInput();
const onboardApi = initOnboardForm();
(async () => {
  if (!(await loadChatState())) {
    createChat();
  }
  renderAll();

  // Anything that was still running when the page was refreshed gets picked
  // back up rather than silently lost. An in-flight onboarding pipeline wins
  // the view, since that's the longer, more disruptive thing to lose.
  const resumedOnboard = await onboardApi.resumeOnboardJob();
  if (resumedOnboard) {
    state.view = "onboard";
    renderAll();
  }
  await resumePendingJob(activeChat());
  renderOnboardHistory();
})();
