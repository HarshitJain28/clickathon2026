/**
 * Turns a raw stdout/stderr line from one of the Python agents into a
 * friendly, human-readable step description, and a small StepFeed component
 * that renders those as a live, checklist-style progress list (with the
 * full raw log still available for debugging, never discarded).
 */

function toolIcon(name) {
  if (name === "Read" || name === "Glob" || name === "Grep") return "📖";
  if (name === "Write" || name === "Edit") return "✍️";
  if (name.startsWith("mcp__clickhouse-cloud__")) return "🗄️";
  return "🔧";
}

function toolLabel(name, args) {
  const known = {
    Read: "Reading a file",
    Write: "Writing output",
    Edit: "Updating a file",
    Glob: "Searching files",
    Grep: "Searching file contents",
  };
  if (known[name]) {
    // The agents log tool args as Python dict reprs, so keys/values come
    // through single-quoted ('file_path': '...'), not JSON double-quoted.
    // Accept either, so this keeps working if that ever changes.
    const fileMatch =
      args && args.match(/['"]file_path['"]\s*:\s*['"]([^'"]+)['"]/);
    if (fileMatch) {
      const short = fileMatch[1].split("/").slice(-2).join("/");
      return `${known[name]} (${short})`;
    }
    return known[name];
  }
  if (name.startsWith("mcp__clickhouse-cloud__")) {
    const tool = name.replace("mcp__clickhouse-cloud__", "");
    const chKnown = {
      run_select_query: "Querying ClickHouse",
      list_tables: "Listing ClickHouse tables",
      list_databases: "Listing ClickHouse databases",
      get_services_list: "Looking up the ClickHouse service",
      authenticate: "Authenticating with ClickHouse Cloud",
      complete_authentication: "Completing ClickHouse Cloud authentication",
    };
    return chKnown[tool] || `ClickHouse: ${tool.replace(/_/g, " ")}`;
  }
  return `Using ${name}`;
}

/** Ordered pipeline stages, mirroring orchestrator.py's own STAGES list.
 * The ids must match the ::stage-start:: / ::stage-end:: markers it emits. */
const PIPELINE_STAGES = [
  { id: "instrumentation", icon: "🧬", label: "Designing the schema" },
  { id: "loader", icon: "📥", label: "Creating tables & loading events" },
  { id: "context_1", icon: "📚", label: "Documenting the schema" },
  { id: "analysis", icon: "🔍", label: "Answering PM questions" },
  { id: "context_2", icon: "✨", label: "Consolidating findings" },
];

/** Parse an orchestrator stage marker, or null if the line isn't one. */
function parseStageMarker(rawLine) {
  const line = rawLine.trim();
  const start = line.match(/^::stage-start::(\S+)$/);
  if (start) return { type: "start", id: start[1] };
  const end = line.match(/^::stage-end::(\S+)::(-?\d+)$/);
  if (end) return { type: "end", id: end[1], code: Number(end[2]) };
  return null;
}

/** Parse one raw log line into { icon, label, kind } for display, or null
 * if the line isn't worth surfacing as its own step. */
function describeLine(rawLine) {
  const line = rawLine.trim();
  if (!line) return null;

  // Stage markers drive the pipeline tracker, not the step feed.
  if (parseStageMarker(line)) return null;

  const toolMatch = line.match(/^\[tool\]\s+(\S+)\s*(.*)$/);
  if (toolMatch) {
    return { icon: toolIcon(toolMatch[1]), label: toolLabel(toolMatch[1], toolMatch[2]), kind: "tool" };
  }
  if (/^skills discovered:/i.test(line)) {
    return { icon: "🧩", label: line.replace(/^skills discovered:\s*/i, "Skills loaded: "), kind: "info" };
  }
  if (/^no skills found/i.test(line)) {
    return { icon: "🧩", label: "No skills configured", kind: "info" };
  }
  if (/^langfuse trace:/i.test(line)) {
    return null; // internal telemetry link, not user-relevant
  }
  if (/^error:/i.test(line) || /^Traceback/i.test(line)) {
    return { icon: "⚠️", label: line.length > 100 ? line.slice(0, 97) + "…" : line, kind: "error" };
  }
  if (/^report (created|not created)/i.test(line)) {
    return { icon: "📄", label: line, kind: "info" };
  }
  // Fallback: still surface it (better to over-show than silently hide
  // progress), just truncated so one long line can't blow out the layout.
  return { icon: "⏳", label: line.length > 100 ? line.slice(0, 97) + "…" : line, kind: "info" };
}

class StepFeed {
  constructor({ listEl, rawEl, maxVisible = 8 }) {
    this.listEl = listEl;
    this.rawEl = rawEl;
    this.maxVisible = maxVisible;
    this.steps = [];
  }

  push(rawLine) {
    if (this.rawEl) {
      this.rawEl.textContent += (this.rawEl.textContent ? "\n" : "") + rawLine;
      this.rawEl.scrollTop = this.rawEl.scrollHeight;
    }

    const described = describeLine(rawLine);
    if (!described) return;

    const last = this.steps[this.steps.length - 1];
    if (last && last.label === described.label && last.kind === described.kind) {
      last.count = (last.count || 1) + 1;
    } else {
      this.steps.push(described);
    }
    this.render();
  }

  render() {
    if (!this.listEl) return;
    this.listEl.innerHTML = "";
    const visible = this.steps.slice(-this.maxVisible);
    visible.forEach((step, i) => {
      const isLast = i === visible.length - 1;
      const row = document.createElement("div");
      row.className = "step-row" + (isLast ? " step-active" : " step-done");

      const icon = document.createElement("span");
      icon.className = "step-icon";
      icon.textContent = isLast ? step.icon : "✓";

      const label = document.createElement("span");
      label.className = "step-label" + (step.kind === "error" ? " step-error" : "");
      label.textContent = step.label + (step.count ? ` (×${step.count})` : "");

      row.appendChild(icon);
      row.appendChild(label);
      this.listEl.appendChild(row);
    });
  }

  /** Freeze the last row into a final ✓ / ✕ state once the job is done. */
  finish(success) {
    if (!this.listEl) return;
    const rows = this.listEl.querySelectorAll(".step-row");
    const lastRow = rows[rows.length - 1];
    if (!lastRow) return;
    lastRow.classList.remove("step-active");
    lastRow.classList.add(success ? "step-done" : "step-failed");
    const icon = lastRow.querySelector(".step-icon");
    if (icon) icon.textContent = success ? "✓" : "✕";
  }
}

/**
 * Renders the orchestrator's five pipeline stages as a persistent checklist
 * that fills in as each stage starts and completes — so a long run always
 * shows where it is overall, not just the most recent tool call.
 */
class PipelineTracker {
  constructor(containerEl) {
    this.containerEl = containerEl;
    this.status = {}; // stageId -> "pending" | "active" | "done" | "failed"
    for (const s of PIPELINE_STAGES) this.status[s.id] = "pending";
    this.render();
  }

  /** Feed a raw log line; returns true if it was a stage marker. */
  push(rawLine) {
    const marker = parseStageMarker(rawLine);
    if (!marker) return false;

    if (marker.type === "start") {
      this.status[marker.id] = "active";
    } else {
      this.status[marker.id] = marker.code === 0 ? "done" : "failed";
    }
    this.render();
    return true;
  }

  /** Any stage still "active" when the job ends never reported an end
   * marker (killed, timed out, crashed) — mark it failed rather than
   * leaving a spinner running forever. */
  finish(success) {
    for (const s of PIPELINE_STAGES) {
      if (this.status[s.id] === "active") {
        this.status[s.id] = success ? "done" : "failed";
      }
    }
    this.render();
  }

  render() {
    if (!this.containerEl) return;
    this.containerEl.innerHTML = "";

    for (const stage of PIPELINE_STAGES) {
      const status = this.status[stage.id];
      const row = document.createElement("div");
      row.className = `pipeline-stage pipeline-${status}`;

      const marker = document.createElement("span");
      marker.className = "pipeline-marker";
      if (status === "done") marker.textContent = "✓";
      else if (status === "failed") marker.textContent = "✕";
      else if (status === "active") marker.textContent = stage.icon;
      else marker.textContent = "○";

      const label = document.createElement("span");
      label.className = "pipeline-label";
      label.textContent = stage.label;

      row.appendChild(marker);
      row.appendChild(label);
      this.containerEl.appendChild(row);
    }
  }
}
