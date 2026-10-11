<!-- Fronti — incolla UNA delle due versioni nel tuo CLAUDE.md globale (~/.claude/CLAUDE.md).
     Paste ONE of the two versions into your global CLAUDE.md (~/.claude/CLAUDE.md). -->

<!-- Italiano -->
- **Fronti — una sessione per fronte.** Ogni progetto è diviso in fronti (app, sito, server,
  marketing, release…) mappati nella sezione `## Fronti` di `overview.md`; un progetto semplice
  ha un fronte unico. Mappa mancante o cartelle fuori mappa → skill `fronti-progetto`, subito e
  senza chiedere. In ogni sessione: dichiara il fronte nella prima risposta, leggi `CLAUDE.md` e
  `STATO.md` della sua cartella, resta nei suoi percorsi, commit solo dei suoi percorsi (prima
  del commit subagent `controllo-confini`; mai `git add -A`), aggiorna `STATO.md` prima di
  chiudere. Due sessioni sullo stesso codice → worktree. Cambio fronte → sessione nuova.

<!-- English -->
- **Fronti — one session per front.** Every project is split into fronts (app, site, server,
  marketing, release…) mapped in the `## Fronti` section of `overview.md`; a simple project has a
  single front. Missing map or unmapped folders → run the `fronti-progetto` skill right away,
  without asking. In every session: state the front in your first reply, read the `CLAUDE.md` and
  `STATO.md` in its folder, stay inside its paths, commit only its paths (run the
  `controllo-confini` subagent before committing; never `git add -A`), update `STATO.md` before
  closing. Two sessions on the same code → worktree. Switching front → new session.
