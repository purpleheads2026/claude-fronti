# Overview — claude-fronti

Plugin per Claude Code «Fronti»: divide ogni progetto in fronti di lavoro e fa lavorare ogni
sessione su un fronte solo. Il repository è insieme plugin, marketplace (un solo plugin) e sito
della guida (GitHub Pages da `docs/`). MIT · purpleheads — Samuel.

## Fronti

| Fronte | Percorsi | Casa | Avvio | Sessione |
|---|---|---|---|---|
| Plugin | `skills/`, `agents/`, `hooks/`, `regola/`, `tests/` | `.` | — | claude-fronti · Plugin |
| Guida | `docs/`, `tools/` | `docs/` | — | claude-fronti · Guida |

Condivisi (una sessione alla volta): `overview.md`, `README.md`, `README.en.md`, `LICENSE`, `design-tokens.json`

Lo stato del lavoro di questo repository vive nelle issue e nelle release di GitHub, non in `STATO.md`.

## Struttura

```
.claude-plugin/
  plugin.json          manifest del plugin "fronti" (nome, versione, autore, licenza)
  marketplace.json     marketplace "claude-fronti" con il solo plugin "fronti" (source: ./)
skills/fronti-progetto/
  SKILL.md             le regole: formato della mappa, mappatura, protocollo di sessione, fronte nuovo, ripresa
  modelli/             CLAUDE-fronte.md e STATO.md, i modelli dei due file di ogni fronte
agents/
  mappa-fronti.md      subagent di sola lettura: analizza il repo e propone la sezione ## Fronti
  controllo-confini.md subagent di sola lettura: prima del commit classifica i file per fronte e dà il git add esatto
hooks/
  hooks.json           registra fronti-guard su SessionStart e PreToolUse(Bash, if git *) via ${CLAUDE_PLUGIN_ROOT}
  fronti-guard.py      l'hook: legge la mappa da overview.md, inietta il contesto, blocca i commit «di tutto»; messaggi it/en
regola/
  CLAUDE-snippet.md    le otto righe da incollare nel CLAUDE.md globale (italiano e inglese)
tests/
  test_fronti_guard.py unittest dell'hook su repository git temporanei (SessionStart, blocchi, lingua, hooks.json)
docs/
  index.html           la guida (GitHub Pages): pagina unica bilingue con le cinque tavole in HTML/CSS
  img/                 tav-0N-{it,en}.png, fotografie delle tavole usate nei README e come og:image
tools/
  render-tavole.mjs    rigenera docs/img/*.png da docs/index.html con Playwright
  package.json         dipendenza playwright (node_modules ignorato)
design-tokens.json     legge della guida: spacing, ruoli tipografici, palette (hex + OKLCH), easing
.github/workflows/test.yml  CI: unittest su ubuntu e macos a ogni push e pull request
README.md · README.en.md    documentazione in italiano e inglese
LICENSE                MIT
```

## Come si collegano i pezzi

- Il plugin si installa dal marketplace del repo stesso: `.claude-plugin/marketplace.json` punta a `./`,
  dove Claude Code trova `plugin.json`, `skills/`, `agents/` e `hooks/hooks.json`.
- `hooks.json` lancia `fronti-guard.py`, che legge la sezione `## Fronti` di `overview.md` del progetto
  dell'utente e rimanda alla skill `fronti-progetto` e ai subagent per nome.
- La skill usa `mappa-fronti` per proporre la mappa e i `modelli/` per creare `CLAUDE.md` e `STATO.md`.
- La guida (`docs/index.html`) prende i valori da `design-tokens.json`; `tools/render-tavole.mjs`
  fotografa le `figure.tavola` in italiano e in inglese e scrive `docs/img/`.

## Comandi

```bash
python3 -m unittest discover -s tests -v                     # test
claude plugin validate .                                     # validazione manifest
cd tools && npm install && npm run tavole                    # PNG delle tavole
python3 -m http.server 8765 --directory docs                 # anteprima della guida
```

Pubblicazione: push su `main` (commit firmati SSH), tag firmato `vX.Y.Z` e release su GitHub;
la guida è servita da GitHub Pages, ramo `main`, cartella `/docs`.
