#!/usr/bin/env bun

import { basename } from "node:path";
import { readFileSync } from "node:fs";

type Result = {
  ok: boolean;
  file: string;
  errors: string[];
  warnings: string[];
  checks: Record<string, number | string | boolean>;
};

function displayWidth(line: string): number {
  return [...line].reduce((width, char) => width + (char.codePointAt(0)! > 127 ? 2 : 1), 0);
}

function validate(content: string, file: string, coverage?: string): Result {
  const errors: string[] = [];
  const warnings: string[] = [];
  const markdownMode = file.toLowerCase().endsWith(".md");
  const requiredHeaders = markdownMode
    ? ["title", "subtitle", "date", "tags", "identifier"]
    : ["TITLE", "SUBTITLE", "DATE", "FILETAGS", "IDENTIFIER"];

  for (const header of requiredHeaders) {
    const pattern = markdownMode
      ? new RegExp(`^${header}:\\s*\\S`, "mi")
      : new RegExp(`^#\\+${header}:\\s*\\S`, "mi");
    if (!pattern.test(content)) {
      errors.push(`缺少或为空的 ${markdownMode ? header : `#+${header}`}`);
    }
  }

  const identifier = markdownMode
    ? content.match(/^identifier:\s*(\S+)/mi)?.[1] ?? ""
    : content.match(/^#\+IDENTIFIER:\s*(\S+)/mi)?.[1] ?? "";
  const filenameIdentifier = basename(file).match(/^(\d{8}T\d{6})--/)?.[1] ?? "";
  if (!filenameIdentifier) {
    errors.push("文件名不是 Denote 时间戳格式");
  } else if (identifier !== filenameIdentifier) {
    errors.push(`IDENTIFIER ${identifier || "为空"} 与文件名 ${filenameIdentifier} 不一致`);
  }

  const firstHeadingIndex = markdownMode
    ? content.search(/^# [^#]/m)
    : content.search(/^\* [^*]/m);
  const opening = firstHeadingIndex >= 0 ? content.slice(0, firstHeadingIndex) : content;
  const triadPattern = markdownMode
    ? /^- \*\*(x|f|f\(x\))\*\*：.+$/gm
    : /^- \*(x|f|f\(x\))\*：.+$/gm;
  const triad = [...opening.matchAll(triadPattern)].map((match) => match[1]);
  const expectedTriad = ["x", "f", "f(x)"];
  if (JSON.stringify(triad) !== JSON.stringify(expectedTriad)) {
    errors.push("开头必须按 x、f、f(x) 恰好各有一行");
  }

  const headingPattern = markdownMode ? /^# ([^#].*)$/gm : /^\* ([^*].*)$/gm;
  const headings = [...content.matchAll(headingPattern)].map((match) => match[1].trim());
  const expectedHeadings = [
    "x：作者在讨论什么问题",
    "f：作者怎样回答",
    "f(x)：怎样回应这个世界",
    "资料校准",
  ];
  if (JSON.stringify(headings) !== JSON.stringify(expectedHeadings)) {
    errors.push(`一级标题必须且只能依次为：${expectedHeadings.join(" / ")}`);
  }

  const calibrationPattern = markdownMode ? /^# 资料校准\s*$/m : /^\* 资料校准\s*$/m;
  const calibration = content.split(calibrationPattern)[1] ?? "";
  if (!/材料等级[：:]/.test(calibration)) {
    errors.push("资料校准中缺少「材料等级」");
  }

  const completeBook = /材料等级[：:][^\n]*完整拆书/.test(calibration);
  if (completeBook && !coverage) {
    errors.push("完整拆书必须提供 --coverage 覆盖记录");
  }
  if (coverage) {
    const authorFields = ["问题", "对象", "方法"].filter((field) =>
      new RegExp(`^- ${field}[：:]\\s*\\S`, "m").test(coverage),
    ).length;
    const zones = ["front", "early", "middle", "late"].filter((zone) =>
      new RegExp(`^- \\[${zone}\\][^\\n]*位置[：:]\\s*\\S`, "m").test(coverage),
    ).length;
    const candidates = [...coverage.matchAll(/^- \[candidate\]\s+.+$/gm)];
    const methodFields = ["输入", "操作", "中间变化", "结果"].filter((field) =>
      new RegExp(`^- ${field}[：:]\\s*\\S`, "m").test(coverage),
    ).length;
    const challengeFields = ["当前 f", "反证", "处理"].filter((field) =>
      new RegExp(`^- ${field}[：:]\\s*\\S`, "m").test(coverage),
    ).length;

    if (authorFields !== 3) errors.push("覆盖记录没有填完作者自述的问题、对象与方法");
    if (zones !== 4) errors.push("覆盖记录没有填完前言、前部、中部、后部四个区域");
    if (candidates.length < 5 || candidates.length > 12) {
      errors.push(`覆盖记录必须有 5–12 个候选部件，当前为 ${candidates.length}`);
    }
    if (methodFields !== 4) errors.push("覆盖记录没有用书内例子跑通输入、操作、中间变化与结果");
    if (challengeFields !== 3) errors.push("覆盖记录没有完成当前 f、反证与处理");
  }

  const examplePattern = markdownMode
    ? /^```(?:text)?\s*$([\s\S]*?)^```\s*$/gmi
    : /^#\+begin_example\s*$([\s\S]*?)^#\+end_example\s*$/gmi;
  const exampleBlocks = [...content.matchAll(examplePattern)];
  if (exampleBlocks.length > 1) {
    errors.push("最多保留一个 example 图块");
  }
  const maxDiagramWidth = exampleBlocks.length
    ? Math.max(...exampleBlocks[0][1].split(/\r?\n/).map(displayWidth))
    : 0;
  if (maxDiagramWidth > 80) {
    errors.push(`ASCII 图宽度 ${maxDiagramWidth}，超过 80`);
  }

  const bodyStart = content.search(
    markdownMode ? /^# x：作者在讨论什么问题\s*$/m : /^\* x：作者在讨论什么问题\s*$/m,
  );
  const bodyEnd = content.search(calibrationPattern);
  const body = bodyStart >= 0 ? content.slice(bodyStart, bodyEnd >= 0 ? bodyEnd : undefined) : "";
  const bodyChars = [...body.replace(/\s/g, "")].length;
  if (bodyChars < 900 || bodyChars > 1600) {
    warnings.push(`正文约 ${bodyChars} 字，超出通常的 900–1600 字范围；复杂书可保留必要超长`);
  }

  return {
    ok: errors.length === 0,
    file,
    errors,
    warnings,
    checks: {
      identifier,
      opening_lines: triad.length,
      top_headings: headings.length,
      example_blocks: exampleBlocks.length,
      max_diagram_width: maxDiagramWidth,
      body_chars: bodyChars,
      coverage_supplied: Boolean(coverage),
      format: markdownMode ? "markdown" : "org",
    },
  };
}

const args = process.argv.slice(2);
const stdinMode = args[0] === "--stdin";
const file = stdinMode ? args[1] ?? "19700101T000000--stdin__book.org" : args[0];
const coverageFlag = args.indexOf("--coverage");
const coveragePath = coverageFlag >= 0 ? args[coverageFlag + 1] : undefined;

if (!file) {
  console.error("用法：bun scripts/validate_note.ts <note.org|note.md>");
  console.error("或：  bun scripts/validate_note.ts --stdin <denote-filename>");
  process.exit(2);
}

if (coverageFlag >= 0 && !coveragePath) {
  console.error("--coverage 后必须提供覆盖记录路径");
  process.exit(2);
}

const content = stdinMode ? readFileSync(0, "utf8") : readFileSync(file, "utf8");
const coverage = coveragePath ? readFileSync(coveragePath, "utf8") : undefined;
const result = validate(content, file, coverage);
console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
