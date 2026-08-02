/**
 * Minimal, dependency-free Markdown -> HTML renderer.
 *
 * Covers what analysis_agent.py's answers actually use: # headers, prose
 * paragraphs, `code`, **bold**, *italic*, fenced code blocks, "- " / "1. "
 * lists, "> " blockquotes, "---" rules, pipe tables, and [text](url) links —
 * not a full CommonMark implementation. Input is HTML-escaped before any
 * markdown transform is applied, so raw "<"/"&" in an agent's answer can
 * never be interpreted as markup.
 */

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function inlineMarkdown(str) {
  return str
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>'
    );
}

function parseTableRow(line) {
  let cells = line.trim();
  if (cells.startsWith("|")) cells = cells.slice(1);
  if (cells.endsWith("|")) cells = cells.slice(0, -1);
  return cells.split("|").map((c) => c.trim());
}

function isTableSeparatorRow(line) {
  const trimmed = line.trim();
  return trimmed.includes("-") && /^[\s|:-]+$/.test(trimmed);
}

function renderTable(rows) {
  if (!rows.length) return "";
  const [headerCells, ...bodyRows] = rows.map(parseTableRow);
  const thead = `<thead><tr>${headerCells
    .map((c) => `<th>${inlineMarkdown(c)}</th>`)
    .join("")}</tr></thead>`;
  const tbody = `<tbody>${bodyRows
    .map((r) => `<tr>${r.map((c) => `<td>${inlineMarkdown(c)}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;
  return `<table>${thead}${tbody}</table>`;
}

function renderMarkdown(raw) {
  if (!raw) return "";
  const escaped = escapeHtml(raw);

  // Pull fenced code blocks out first so their contents are never touched
  // by heading/list/inline transforms below.
  const codeBlocks = [];
  const withoutCode = escaped.replace(
    /```[a-zA-Z0-9]*\n([\s\S]*?)```/g,
    (_match, code) => {
      codeBlocks.push(code);
      return ` CODEBLOCK${codeBlocks.length - 1} `;
    }
  );

  const lines = withoutCode.split("\n");
  const htmlLines = [];
  let blockType = null; // null | "ul" | "ol" | "blockquote" | "table"
  let tableRows = [];

  const closeBlock = () => {
    if (blockType === "ul") htmlLines.push("</ul>");
    else if (blockType === "ol") htmlLines.push("</ol>");
    else if (blockType === "blockquote") htmlLines.push("</blockquote>");
    else if (blockType === "table") {
      htmlLines.push(renderTable(tableRows));
      tableRows = [];
    }
    blockType = null;
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const trimmed = line.trim();

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      closeBlock();
      htmlLines.push("<hr>");
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      closeBlock();
      const level = headingMatch[1].length;
      htmlLines.push(`<h${level}>${inlineMarkdown(headingMatch[2])}</h${level}>`);
      continue;
    }

    // A pipe row immediately followed by a "---|---" separator starts a
    // table; while inside one, keep consuming pipe rows as its body.
    if (blockType !== "table" && trimmed.includes("|") && lines[i + 1] && isTableSeparatorRow(lines[i + 1])) {
      closeBlock();
      blockType = "table";
      tableRows = [trimmed];
      i += 1; // skip the separator row itself
      continue;
    }
    if (blockType === "table") {
      if (trimmed.includes("|")) {
        tableRows.push(trimmed);
        continue;
      }
      closeBlock(); // fall through: this line starts something else
    }

    // ">" was already HTML-escaped to "&gt;" above (escapeHtml runs on the
    // whole string before this loop), so match its escaped form here.
    const quoteMatch = line.match(/^&gt;\s?(.*)$/);
    if (quoteMatch) {
      if (blockType !== "blockquote") {
        closeBlock();
        htmlLines.push("<blockquote>");
        blockType = "blockquote";
      }
      htmlLines.push(`<p>${inlineMarkdown(quoteMatch[1])}</p>`);
      continue;
    }

    const ulMatch = line.match(/^[-*]\s+(.*)$/);
    if (ulMatch) {
      if (blockType !== "ul") {
        closeBlock();
        htmlLines.push("<ul>");
        blockType = "ul";
      }
      htmlLines.push(`<li>${inlineMarkdown(ulMatch[1])}</li>`);
      continue;
    }

    const olMatch = line.match(/^\d+[.)]\s+(.*)$/);
    if (olMatch) {
      if (blockType !== "ol") {
        closeBlock();
        htmlLines.push("<ol>");
        blockType = "ol";
      }
      htmlLines.push(`<li>${inlineMarkdown(olMatch[1])}</li>`);
      continue;
    }

    closeBlock();
    if (trimmed === "") {
      htmlLines.push("");
    } else {
      htmlLines.push(`<p>${inlineMarkdown(line)}</p>`);
    }
  }
  closeBlock();

  let html = htmlLines.join("\n");
  html = html.replace(/ CODEBLOCK(\d+) /g, (_match, i) => {
    return `<pre><code>${codeBlocks[Number(i)]}</code></pre>`;
  });
  return html;
}
