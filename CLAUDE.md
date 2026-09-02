# J_AI — standing instructions for Claude

J_AI is Jaber's flagship AI project: a structured evaluation engine (templates in → validated JSON verdicts out), local-first via Ollama. If this folder is opened as its own chat, this file is the brain — read [SPEC.md](SPEC.md) (state + build order) and [README.md](README.md) first.

## On session start
1. Read `SPEC.md`'s "Recall triggers" section and the newest `G:\AI\PROGRESS.md` entries; brief Jaber on what exists and what's queued.
2. **Source of truth is WSL `/home/j/J_AI`** (venv, Ollama, `.env`, logs). This folder's `code/` is a Windows snapshot — work happens in WSL; re-sync the snapshot afterwards (rsync, excluding venv/logs/runs/.env).
3. Build history (Phases 1–8): `docs/Project Journal - J_AI.docx`.

## Rules
- **Jaber builds; Claude coaches** — prepare, review, unblock; don't write the implementation unless he asks.
- **Recall over memorization** — each session adds one line to SPEC.md's recall triggers (what exists now + the one decision made). Stop-condition for any explanation: one clear paragraph.
- **Never commit `.env`** (it configures JAI_PROVIDER / model / base URL and may hold keys).
- Known issue queued in week 1: `src/**/__int__.py` should be `__init__.py`.
- MUV scope is frozen (see SPEC.md) — resist feature creep; the journal's Decision 0072 says small-but-complete beats large-but-unfinished.
- **CV rule:** publishing the MUV to GitHub is a CV-ready moment — propose the bullet when it happens.
