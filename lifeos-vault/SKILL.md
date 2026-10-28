---
name: lifeos-vault
description: Create, move, rename, delete or edit notes in the LifeOS Obsidian vault (~/LifeOS), choosing the folder each note belongs in and bringing the files a note references (images, PDFs, audio) into the vault. Use when asked to save, file, write down, reorganize or clean up a note in LifeOS or Obsidian.
---

# LifeOS vault notes

The vault is `~/LifeOS` (`$LIFEOS_VAULT` overrides). Its `AGENTS.md` is the source of truth for Denote filenames, the `title` property, the Project template and link form: read it before the first write in a session.

Every file operation that touches names or links goes through `scripts/vault.py` (paths vault-relative): it allocates free Denote IDs and rewrites every link when something moves. Moving or renaming with plain `mv` leaves links broken.

## Placement

Choose the **home** for a note before writing it. Work down this list; the first match wins.

1. **Not a note.** A reminder or personal to-do goes to Google Tasks; a project work item goes to Plane (workspace `allinone`). Say so and stop.
2. **LifeOS record** (Area, Goal, Idea, Baseline, Project): its record folder (`Areas/`, `Goals/`, `Ideas/`, `Baselines/`, `Projects/<Title>/`). Copy the frontmatter of an existing record of that type; a Project follows the template rule in `AGENTS.md`.
3. **Periodic note**: `02-Perodic/00-Daily`, `01-Weekly`, `02-Monthly`, named like their neighbours (`<YYYYMMDD>T000000--<YYYY-MM-DD-ddd>__journal.md`).
4. **Belongs to a Project**: `Projects/<Project>/`, or the existing subfolder already holding its kind (`Resources/`, `Research/`, `Exposure-Control/`, …). Match by reading each project note's title and Purpose (`ls Projects/*/*__project.md`), not by folder name alone.
5. **Nothing fits** (loose thought, article clipping, roundtable): `00-Inbox/`.

Ask the owner, with numbered options, when two homes fit equally well; otherwise decide and name the choice in your reply.

Machine-owned, never hand-written: `01-Extras/LifeOS/` (Agent Reviews, Audio, time categories), `.lifeos/`, `.obsidian/`, `01-Extras/Templates/`.

**Keywords** follow the home's neighbours: `__project`, `__idea`, `__journal`, `__aqrp`, `__quant`, `__interview`. Reuse the keyword the sibling notes carry; add a second only when it distinguishes the note.

## Operations

**Create.** Place it, then `vault.py name "<Title>" <keyword>... --dir <home>` prints a free path. Write the file there with `title` frontmatter (plus the record fields when it is a record), then run the attachment pass.

**Modify.** Edit in place. A changed `title` means a rename: keep the ID and run `vault.py name "<New title>" <keywords> --dir <same dir> --id <ID>`, then move to that path. Run the attachment pass if the edit added references.

**Move / rename.** `vault.py move <src> <dst>` moves a note, attachment or whole folder and relinks every note pointing into it. Renames keep the Denote ID, and a record's `id` must still equal it. Moving a Project means moving its whole `Projects/<Title>/` folder.

**Delete.** Run `vault.py refs <path>` first and show the owner what links to it. Deleting a LifeOS record (anything with `lifeos_schema`) breaks reviews and time logging: offer a `status` change instead and delete only on an explicit yes. `vault.py trash <path>` moves it into `.trash/` (recoverable) and lists the links now broken; fix or unlink each one. Attachments referenced only by the deleted note go to `.trash/` with it.

## Attachment pass

After writing a note, `vault.py attachments <note>` lists each non-Markdown reference as:

- `ok`: already in the vault.
- `outside`: an absolute path on this machine. `vault.py attach <file> <dir>` copies it in, then replace the reference with the printed `![[name]]` (`[[name]]` for a PDF meant to open, not render).
- `missing`: nowhere to be found. Look for the filename under `~/Downloads`, `~/Pictures`, `~/Desktop`, `~/Documents` and any path the owner gave; attach it if found, otherwise list it in your reply.

Files the owner hands over with a note (a screenshot path, a PDF to file) take the same `attach` route.

Attachment homes, so files stay findable by kind:

- PDF: `01-Extras/PDF/` (datasheets and specs in `01-Extras/PDF/Specs_Datasheets/`).
- Image: `01-Extras/Images/`.
- Excalidraw and canvas: `01-Extras/Canvas/`.
- A project's evidence (logs, dumps, multi-file result sets): beside the project, in its `Evidence/` subfolder.
- Anything else: `01-Extras/Files/`.

`attach` keeps the original filename, reuses an identical file already in the vault, and suffixes the name when a different file has it, so `![[name]]` always resolves to one file.

## Done

The work is done when every changed note's `attachments` report shows only `ok` (or the owner knows which files are missing), `vault.py refs` on anything moved or trashed finds no stale link, and your reply names each path written, moved or trashed.
