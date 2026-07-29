"use strict";

// This application deliberately has no network calls.  Selected File objects
// are read with File.text() and indexed only in this page's JavaScript memory.
const STOPWORDS = new Set([
  "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
  "for", "from", "has", "have", "he", "her", "hers", "him", "his", "i", "if",
  "in", "into", "is", "it", "its", "me", "my", "not", "of", "on", "or", "our",
  "she", "so", "that", "the", "their", "them", "there", "they", "this", "to",
  "was", "we", "were", "what", "when", "where", "which", "who", "will", "with",
  "you", "your"
]);

const state = { documents: new Map(), masterIndex: new Map() };
const elements = {
  fileInput: document.querySelector("#file-input"),
  fileList: document.querySelector("#file-list"),
  fileStatus: document.querySelector("#file-status"),
  form: document.querySelector("#search-form"),
  queryInput: document.querySelector("#query-input"),
  message: document.querySelector("#message"),
  summary: document.querySelector("#summary"),
  results: document.querySelector("#results")
};

function normalizeText(text) {
  return text.toLowerCase().replace(/[^0-9a-zA-Z가-힣\s]+/g, " ");
}

function tokensWithPositions(text) {
  return normalizeText(text).split(/\s+/).filter(Boolean)
    .map((word, position) => ({ word, position }))
    .filter(({ word }) => !STOPWORDS.has(word));
}

function searchableLineNumbers(lines) {
  const start = lines.findIndex(line => line.toLowerCase().includes("*** start of the project gutenberg ebook"));
  const end = lines.findIndex(line => line.toLowerCase().includes("*** end of the project gutenberg ebook"));
  if (start >= 0 && end > start) {
    return Array.from({ length: end - start - 1 }, (_, index) => start + index + 2);
  }
  return Array.from({ length: lines.length }, (_, index) => index + 1);
}

function makeLineKey(fileName, lineNumber) {
  return `${fileName}\u0000${lineNumber}`;
}

function makeSpanKey(fileName, lineNumber, start, end) {
  return `${fileName}\u0000${lineNumber}\u0000${start}\u0000${end}`;
}

function buildDocumentIndex(name, text) {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/);
  const lineNumbers = searchableLineNumbers(lines);
  const index = new Map();
  for (const lineNumber of lineNumbers) {
    for (const { word, position } of tokensWithPositions(lines[lineNumber - 1])) {
      if (!index.has(word)) index.set(word, []);
      index.get(word).push({ lineNumber, position });
    }
  }
  return { name, lines, lineNumbers, index };
}

function rebuildMasterIndex() {
  state.masterIndex = new Map();
  for (const documentData of state.documents.values()) {
    for (const [word, positions] of documentData.index) {
      if (!state.masterIndex.has(word)) state.masterIndex.set(word, []);
      const destination = state.masterIndex.get(word);
      positions.forEach(({ lineNumber, position }) => destination.push({
        fileName: documentData.name, lineNumber, position
      }));
    }
  }
}

function tokenizeQuery(query) {
  if (!query.trim()) throw new Error("Please enter a Boolean query.");
  const invalid = query.replace(/[0-9a-zA-Z가-힣\s&|!()]+/g, "");
  if (invalid) throw new Error("Query contains unsupported characters.");
  const tokens = query.toLowerCase().match(/[0-9a-zA-Z가-힣]+|&&|\|\||!|\(|\)/g) || [];
  if (!tokens.length) throw new Error("Please enter a Boolean query.");
  return tokens;
}

class QueryParser {
  constructor(tokens) { this.tokens = tokens; this.position = 0; }
  current() { return this.tokens[this.position] || null; }
  consume() {
    const token = this.current();
    if (token === null) throw new Error("Unexpected end of query.");
    this.position += 1;
    return token;
  }
  parse() {
    const expression = this.parseOr();
    if (this.current() !== null) throw new Error(`Unexpected token: ${this.current()}`);
    return expression;
  }
  parseOr() {
    let left = this.parseAnd();
    while (this.current() === "||") { this.consume(); left = { type: "OR", left, right: this.parseAnd() }; }
    return left;
  }
  parseAnd() {
    let left = this.parseUnary();
    while (this.current() === "&&") { this.consume(); left = { type: "AND", left, right: this.parseUnary() }; }
    return left;
  }
  parseUnary() {
    if (this.current() === "!") { this.consume(); return { type: "NOT", expression: this.parseUnary() }; }
    return this.parsePrimary();
  }
  parsePrimary() {
    const token = this.current();
    if (token === null) throw new Error("Unexpected end of query.");
    if (token === "(") {
      this.consume();
      const expression = this.parseOr();
      if (this.current() !== ")") throw new Error("Missing closing parenthesis.");
      this.consume();
      return expression;
    }
    if (["&&", "||", "!", ")"].includes(token)) throw new Error(`Expected a word or '(', got: ${token}`);
    return { type: "WORD", word: this.consume() };
  }
}

function allLines() {
  const lines = new Set();
  for (const documentData of state.documents.values()) {
    documentData.lineNumbers.forEach(lineNumber => lines.add(makeLineKey(documentData.name, lineNumber)));
  }
  return lines;
}

function union(left, right) { return new Set([...left, ...right]); }
function intersection(left, right) { return new Set([...left].filter(value => right.has(value))); }
function containsNot(node) {
  return node.type === "NOT" || ((node.type === "AND" || node.type === "OR") && (containsNot(node.left) || containsNot(node.right)));
}

function evaluate(node) {
  if (node.type === "WORD") {
    const spans = new Map();
    for (const entry of state.masterIndex.get(node.word) || []) {
      const span = { fileName: entry.fileName, lineNumber: entry.lineNumber, start: entry.position, end: entry.position };
      spans.set(makeSpanKey(span.fileName, span.lineNumber, span.start, span.end), span);
    }
    return { lines: new Set([...spans.values()].map(span => makeLineKey(span.fileName, span.lineNumber))), spans };
  }
  if (node.type === "NOT") {
    const child = evaluate(node.expression);
    return { lines: new Set([...allLines()].filter(line => !child.lines.has(line))), spans: new Map() };
  }
  const left = evaluate(node.left);
  const right = evaluate(node.right);
  if (node.type === "OR") return { lines: union(left.lines, right.lines), spans: new Map([...left.spans, ...right.spans]) };

  if (containsNot(node.left) || containsNot(node.right)) {
    const lines = intersection(left.lines, right.lines);
    const spans = new Map([...left.spans, ...right.spans].filter(([, span]) => lines.has(makeLineKey(span.fileName, span.lineNumber))));
    return { lines, spans };
  }
  const rightStarts = new Map([...right.spans.values()].map(span => [`${span.fileName}\u0000${span.lineNumber}\u0000${span.start}`, span]));
  const spans = new Map();
  for (const span of left.spans.values()) {
    const next = rightStarts.get(`${span.fileName}\u0000${span.lineNumber}\u0000${span.end + 1}`);
    if (next) {
      const combined = { fileName: span.fileName, lineNumber: span.lineNumber, start: span.start, end: next.end };
      spans.set(makeSpanKey(combined.fileName, combined.lineNumber, combined.start, combined.end), combined);
    }
  }
  return { lines: new Set([...spans.values()].map(span => makeLineKey(span.fileName, span.lineNumber))), spans };
}

function collectWords(node, words = []) {
  if (node.type === "WORD" && !words.includes(node.word)) words.push(node.word);
  else if (node.type === "NOT") collectWords(node.expression, words);
  else if (node.type === "AND" || node.type === "OR") { collectWords(node.left, words); collectWords(node.right, words); }
  return words;
}

function setMessage(text, kind = "neutral") {
  elements.message.textContent = text;
  elements.message.className = `message ${kind}`;
}

function appendHighlightedText(container, text, words) {
  const expression = /[0-9a-zA-Z가-힣]+/g;
  let offset = 0;
  for (const match of text.matchAll(expression)) {
    container.append(document.createTextNode(text.slice(offset, match.index)));
    const token = match[0];
    if (words.has(token.toLowerCase())) {
      const mark = document.createElement("mark");
      mark.textContent = token;
      container.append(mark);
    } else container.append(document.createTextNode(token));
    offset = match.index + token.length;
  }
  container.append(document.createTextNode(text.slice(offset)));
}

function renderResults(result, words) {
  elements.results.replaceChildren();
  const grouped = new Map();
  for (const lineKey of result.lines) {
    const [fileName, number] = lineKey.split("\u0000");
    if (!grouped.has(fileName)) grouped.set(fileName, []);
    grouped.get(fileName).push(Number(number));
  }
  for (const fileName of [...grouped.keys()].sort((a, b) => a.localeCompare(b))) {
    const section = document.createElement("section");
    section.className = "result-file";
    const title = document.createElement("h3");
    title.textContent = fileName;
    section.append(title);
    const documentData = state.documents.get(fileName);
    for (const lineNumber of grouped.get(fileName).sort((a, b) => a - b)) {
      const row = document.createElement("div");
      row.className = "result-line";
      const number = document.createElement("span");
      number.className = "line-number";
      number.textContent = String(lineNumber);
      const source = document.createElement("span");
      appendHighlightedText(source, documentData.lines[lineNumber - 1], words);
      row.append(number, source);
      section.append(row);
    }
    elements.results.append(section);
  }
}

async function handleFiles(files) {
  state.documents.clear();
  elements.fileList.replaceChildren();
  const errors = [];
  for (const file of files) {
    try {
      const name = state.documents.has(file.name) ? `${file.name} (${state.documents.size + 1})` : file.name;
      state.documents.set(name, buildDocumentIndex(name, await file.text()));
      const item = document.createElement("li");
      item.textContent = name;
      elements.fileList.append(item);
    } catch (error) { errors.push(`${file.name}: ${error.message}`); }
  }
  rebuildMasterIndex();
  elements.fileStatus.textContent = state.documents.size ? `${state.documents.size} file(s) ready to search.` : "No readable files selected.";
  elements.results.replaceChildren();
  elements.summary.hidden = true;
  setMessage(errors.length ? `Some files could not be read: ${errors.join("; ")}` : state.documents.size ? "Ready to search." : "No files selected.", errors.length ? "error" : "success");
}

function handleSearch(event) {
  event.preventDefault();
  elements.results.replaceChildren();
  elements.summary.hidden = true;
  if (!state.documents.size) { setMessage("Please upload at least one TXT file.", "error"); return; }
  try {
    const ast = new QueryParser(tokenizeQuery(elements.queryInput.value)).parse();
    const result = evaluate(ast);
    const words = new Set(collectWords(ast));
    const occurrenceCount = result.spans.size;
    elements.summary.replaceChildren();
    for (const [label, value] of [["Occurrences", occurrenceCount], ["Matching lines", result.lines.size]]) {
      const metric = document.createElement("span");
      metric.className = "metric";
      const strong = document.createElement("strong");
      strong.textContent = `${label}:`;
      metric.append(strong, document.createTextNode(` ${value}`));
      elements.summary.append(metric);
    }
    elements.summary.hidden = false;
    if (!result.lines.size) { setMessage("No matching lines found.", "neutral"); return; }
    setMessage(`Found ${result.lines.size} matching line(s).`, "success");
    renderResults(result, words);
  } catch (error) { setMessage(error.message || "Unable to process this query.", "error"); }
}

elements.fileInput.addEventListener("change", event => handleFiles([...event.target.files]));
elements.form.addEventListener("submit", handleSearch);
document.querySelectorAll("[data-query]").forEach(button => button.addEventListener("click", () => {
  elements.queryInput.value = button.dataset.query;
  elements.queryInput.focus();
}));
