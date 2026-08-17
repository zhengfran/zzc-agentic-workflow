#!/usr/bin/env node

"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

function failUsage() {
  console.error(
    "Usage: node scripts/validate_task_drawing.js /absolute/path/to/drawing.excalidraw.md",
  );
  process.exit(2);
}

function section(markdown, heading) {
  const headingPattern = new RegExp(`^## ${heading}\\r?$`, "m");
  const headingMatch = headingPattern.exec(markdown);
  if (!headingMatch) return null;

  const bodyStart = headingMatch.index + headingMatch[0].length;
  const tail = markdown.slice(bodyStart).replace(/^\r?\n/, "");
  const nextHeading = /^## |\n%%(?:\r?\n|$)/m.exec(tail);
  return nextHeading ? tail.slice(0, nextHeading.index) : tail;
}

function findPluginMain(startPath) {
  let cursor = path.dirname(path.resolve(startPath));
  while (true) {
    const candidate = path.join(
      cursor,
      ".obsidian",
      "plugins",
      "obsidian-excalidraw-plugin",
      "main.js",
    );
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(cursor);
    if (parent === cursor) return null;
    cursor = parent;
  }
}

function loadLzString(pluginMainPath) {
  const source = fs.readFileSync(pluginMainPath, "utf8");
  const start = source.indexOf("var hasRequiredLzString");
  const end = source.indexOf("var TextMode", start);
  if (start < 0 || end < 0) {
    throw new Error(
      `Cannot locate bundled LZString implementation in ${pluginMainPath}`,
    );
  }

  const sandbox = { module: { exports: {} }, exports: {} };
  const program =
    source.slice(start, end) + "\nmodule.exports = requireLzString();";
  vm.runInNewContext(program, sandbox, {
    filename: `${pluginMainPath}:lz-string`,
    timeout: 1000,
  });
  return sandbox.module.exports;
}

function parseScene(markdown, drawingPath) {
  const raw = /## Drawing\r?\n```json\r?\n([\s\S]*?)\r?\n```/.exec(markdown);
  if (raw) return JSON.parse(raw[1]);

  const compressed =
    /## Drawing\r?\n```compressed-json\r?\n([\s\S]*?)\r?\n```/.exec(markdown);
  if (!compressed) {
    throw new Error("Missing JSON or compressed-json Drawing block");
  }

  const pluginMain = findPluginMain(drawingPath);
  if (!pluginMain) {
    throw new Error(
      "Compressed drawing found, but no installed Excalidraw plugin was found above the drawing path",
    );
  }

  const lzString = loadLzString(pluginMain);
  const json = lzString.decompressFromBase64(
    compressed[1].replace(/\s+/g, ""),
  );
  if (!json) throw new Error("The compressed drawing could not be decompressed");
  return JSON.parse(json);
}

function parseTextElements(markdown, errors) {
  const body = section(markdown, "Text Elements");
  if (body === null) {
    errors.push("Missing ## Text Elements section");
    return new Map();
  }

  for (const match of body.matchAll(/\s\^([^\s\r\n]+)\r?$/gm)) {
    if (match[1].length !== 8) {
      errors.push(
        `Text Elements marker "${match[1]}" has ${match[1].length} characters; expected 8`,
      );
    }
  }

  const entries = new Map();
  const marker = / \^(.{8})\r?\n(?:\r?\n|$)/g;
  let cursor = 0;
  for (const match of body.matchAll(marker)) {
    const id = match[1];
    const rawText = body.slice(cursor, match.index);
    if (entries.has(id)) {
      errors.push(`Duplicate Text Elements marker for "${id}"`);
    }
    entries.set(id, rawText);
    cursor = match.index + match[0].length;
  }

  const residue = body.slice(cursor).trim();
  if (residue) {
    errors.push(
      `Unparsed content remains in Text Elements: ${JSON.stringify(residue.slice(0, 80))}`,
    );
  }
  return entries;
}

function parseElementLinks(markdown, errors) {
  const body = section(markdown, "Element Links");
  if (body === null) return new Map();

  const links = new Map();
  for (const match of body.matchAll(/^([^:\r\n]+):\s*(.*)$/gm)) {
    const id = match[1].trim();
    if (id.length !== 8) {
      errors.push(
        `Element Links key "${id}" has ${id.length} characters; expected 8`,
      );
    }
    if (links.has(id)) errors.push(`Duplicate Element Links key "${id}"`);
    links.set(id, match[2]);
  }
  return links;
}

function nonEmpty(value) {
  return typeof value === "string" && value.length > 0;
}

function canonicalRawText(element) {
  if (nonEmpty(element.rawText)) return element.rawText;
  if (nonEmpty(element.originalText)) return element.originalText;
  return typeof element.text === "string" ? element.text : "";
}

function normalizeNewlines(value) {
  return value.replace(/\r\n/g, "\n");
}

function validate(markdown, scene) {
  const errors = [];
  const mirroredText = parseTextElements(markdown, errors);
  const elementLinks = parseElementLinks(markdown, errors);
  const elements = Array.isArray(scene.elements) ? scene.elements : [];
  const liveElements = elements.filter((element) => !element.isDeleted);
  const byId = new Map();

  for (const element of elements) {
    if (!element || typeof element.id !== "string") {
      errors.push("Scene contains an element without a string ID");
      continue;
    }
    if (byId.has(element.id)) {
      errors.push(`Duplicate scene element ID "${element.id}"`);
    }
    byId.set(element.id, element);
  }

  const liveText = liveElements.filter((element) => element.type === "text");
  const liveTextIds = new Set(liveText.map((element) => element.id));
  for (const element of liveText) {
    if (element.id.length !== 8) {
      errors.push(
        `Text scene element "${element.id}" has ${element.id.length} characters; expected 8`,
      );
    }

    if (!mirroredText.has(element.id)) {
      errors.push(`Text scene element "${element.id}" has no mirrored entry`);
      continue;
    }

    const mirrored = mirroredText.get(element.id);
    const canonical = canonicalRawText(element);
    if (!nonEmpty(mirrored)) {
      errors.push(`Mirrored text for "${element.id}" is empty`);
    }
    if (normalizeNewlines(mirrored) !== normalizeNewlines(canonical)) {
      errors.push(
        `Mirrored text for "${element.id}" differs from the scene's canonical raw text`,
      );
    }
  }

  for (const [id, rawText] of mirroredText) {
    if (!liveTextIds.has(id)) {
      errors.push(`Mirrored text "${id}" does not map to a live text element`);
    }
    if (!nonEmpty(rawText)) errors.push(`Mirrored text for "${id}" is empty`);
  }

  for (const id of elementLinks.keys()) {
    if (!byId.has(id)) {
      errors.push(`Element Links key "${id}" does not exist in the scene`);
    }
  }

  return {
    errors,
    sceneElements: elements.length,
    liveTextElements: liveText.length,
    mirroredTextElements: mirroredText.size,
    elementLinks: elementLinks.size,
  };
}

function main() {
  if (process.argv.length !== 3) failUsage();

  const drawingPath = path.resolve(process.argv[2]);
  let markdown;
  let scene;
  try {
    markdown = fs.readFileSync(drawingPath, "utf8");
    scene = parseScene(markdown, drawingPath);
  } catch (error) {
    console.error(`FAIL ${drawingPath}`);
    console.error(`- ${error.message}`);
    process.exit(1);
  }

  const result = validate(markdown, scene);
  if (result.errors.length > 0) {
    console.error(`FAIL ${drawingPath}`);
    for (const error of result.errors) console.error(`- ${error}`);
    process.exit(1);
  }

  console.log(`PASS ${drawingPath}`);
  console.log(
    `scene=${result.sceneElements} text=${result.liveTextElements} mirrored=${result.mirroredTextElements} links=${result.elementLinks}`,
  );
}

main();
