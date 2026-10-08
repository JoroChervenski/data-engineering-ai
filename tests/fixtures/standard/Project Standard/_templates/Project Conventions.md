---
project: {{project}}
type: conventions
status: active
authority: working
standard_version: {{standard_version}}
standard_commit: {{standard_commit}}
tags: [{{ptag}}, conventions]
---

# Conventions: {{project}} vault folder

This folder follows the [[Project Standard]] (version {{standard_version}}). The rules and their reasons are
there; this note shows the layout so the folder reads well on its own.

## Layout

| Folder | What goes there | Who writes it |
|---|---|---|
| `{{project}}.md` | Hub: summary, key facts, auto-generated lists, log | you (the block between the sync markers is automatic) |
| `_Conventions.md` | This note | the sync (only if missing) |
| `01 Overview/` | Project-level notes: overview, open questions, stakeholders | you |
| `02 Repos/<repo>/` | Read-only mirrors of the repo's `.ai/` files, one subfolder per repo | the sync |
| `03 Tickets/` | One note per ticket, named by ticket ID | the sync (mirror of `.ai/tickets/`) |
| `04 Decisions/` | Project-level ADRs; `<repo>/` subfolders mirror the repo's `.ai/adr/` | you (top level), the sync (`<repo>/`) |
| `05 Runbooks/` | Project-level runbooks; `<repo>/` subfolders mirror the repo's `.ai/runbooks/` | you (top level), the sync (`<repo>/`) |
| `06 Analysis/` | Comparisons, mappings, investigations | you |
| `07 Reference/` | API collections, vendor notes, external docs | you |
| `99 Inbox/` | Unsorted notes, filed weekly | you |

## Names
- Project-level note: `{{project}} - <Topic>`.
- Repo-level note: `{{project}} - <repo> - <Topic>`.
- Ticket note: the ticket ID.

## Authority
- The repo's `.ai/` is the source of truth. A note with `authority: mirror` is a copy: edit the repo file and
  re-run the sync, because edits made in the vault are overwritten.
- A note with `authority: working` is yours. Put a fact there only after it is recorded in the repo overlay.

## Isolation
This folder is mounted on its own into this project's container. Never mount the whole vault, and never
link from here to another project's folder.
