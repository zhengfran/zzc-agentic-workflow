# Output and scrollback

Read this reference when inspecting pane output, logs, transcripts, styling, or
missing history.

Choose the source that matches the evidence:

- `visible`: current rendered viewport.
- `recent`: recent rendered output including soft wraps.
- `recent-unwrapped`: recent output with soft wraps joined; prefer for logs and
  transcripts.
- `detection`: plain-text bottom-buffer snapshot used for agent detection.

Use `--format ansi` only when colors or terminal styling are evidence; otherwise
use text. Increase `--lines` to request more rows from the pane's available screen
and host scrollback.

If a larger line count still cannot reveal a completed response, the process is
probably using the terminal alternate screen. Rows leaving that screen do not
enter Herdr's host scrollback and cannot be recovered by requesting more lines.

Only after that failed read, ask the agent to write its complete response as
Markdown in a temporary directory and reply with the file path, then read the file
directly. Keep inline output as the default; do not request file transport in the
initial prompt.
