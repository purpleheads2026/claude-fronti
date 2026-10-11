#!/usr/bin/env python3
# fronti-guard — un progetto, piu' fronti, una sessione per fronte.
# One project, many fronts, one session per front.
#
# Parte del plugin Fronti per Claude Code (https://github.com/purpleheads2026/claude-fronti),
# insieme alla skill fronti-progetto e ai subagent mappa-fronti e controllo-confini.
# MIT · purpleheads — Samuel
#
# La mappa dei fronti e' la sezione "## Fronti" di overview.md (la scrive la skill):
#   | Fronte | Percorsi | Casa | Avvio | Sessione |
#   | App    | `app/`, `packages/` | `app/` | — | Cometa · App |
#   Condivisi: `overview.md`, `docs/`
#
# Due momenti (stesso script, l'evento arriva nel JSON su stdin):
#  - SessionStart: senza mappa chiede di crearla con la skill fronti-progetto prima di ogni altro
#    lavoro; con la mappa elenca i fronti, chiede di dichiarare quello della sessione e segnala le
#    cartelle di primo livello che non stanno in nessun fronte.
#  - PreToolUse (Bash): nei progetti con almeno due fronti blocca i commit "di tutto"
#    (git add -A/--all/-u/., git commit -a), che mescolano il lavoro di sessioni parallele.
#
# Lingua dei messaggi: FRONTI_LANG=it|en; altrimenti segue LANG (it_* -> italiano, il resto inglese).
# Progetto = radice del repository git, oppure una cartella con i segni di un progetto.
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

SEGNI = ("package.json", "composer.json", "Package.swift", "pyproject.toml", "requirements.txt",
         "Cargo.toml", "go.mod", "Gemfile", "index.html", "functions.php", "style.css",
         "astro.config.mjs", "astro.config.ts", "next.config.js", "next.config.mjs", "vite.config.ts",
         "vite.config.js")
TITOLO = re.compile(r"^##\s+(Fronti|Fronts)\b", re.IGNORECASE)


def lingua():
    scelta = os.environ.get("FRONTI_LANG", "").lower()
    if scelta in ("it", "en"):
        return scelta
    locale = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
    return "it" if locale.lower().startswith("it") else "en"


TESTI = {
    "it": {
        "senza_overview": ("FRONTI: dopo aver creato overview.md, aggiungi la sezione '## Fronti' con la skill "
                           "fronti-progetto (regola del sistema Fronti: ogni progetto diviso in fronti, una "
                           "sessione per fronte)."),
        "senza_mappa": ("MAPPA DEI FRONTI MANCANTE. overview.md di {radice} non ha la sezione '## Fronti'. "
                        "PRIMA di qualsiasi altro lavoro esegui la skill fronti-progetto, senza chiedere "
                        "conferma: mappa i fronti del progetto (app, sito, server, marketing, release…; un "
                        "progetto semplice ha un fronte unico), crea CLAUDE.md e STATO.md di ogni fronte, non "
                        "spostare codice. Poi dichiara il fronte di questa sessione e prosegui con la richiesta."),
        "unico": ("Progetto a fronte unico: {nome}. Leggi {casa}/STATO.md se esiste e aggiornalo prima di "
                  "chiudere un blocco di lavoro."),
        "multi": ("FRONTI di questo progetto: {elenco}. Una sessione = un fronte. Nella prima risposta dichiara "
                  "in una riga il fronte di questa sessione (deducilo dalla richiesta; se non e' chiaro e devi "
                  "modificare file, chiedilo), leggi CLAUDE.md e STATO.md della sua casa e resta nei suoi "
                  "percorsi. Commit solo dei suoi percorsi (subagent controllo-confini prima del commit), "
                  "STATO.md aggiornato prima di chiudere, worktree se un'altra sessione lavora sullo stesso "
                  "codice, sessione nuova se cambi fronte. Dettagli: skill fronti-progetto."),
        "qui": " Questa sessione e' aperta dentro {relativo}/: il suo fronte e' {nome}.",
        "worktree": " Sei in un worktree: lavora qui e unisci il ramo a fine lavoro.",
        "fuori": (" ATTENZIONE: queste cartelle non stanno in nessun fronte ne' tra i condivisi: {cartelle}. "
                  "Aggiorna la mappa con la skill fronti-progetto."),
        "blocco": ("fronti-guard: '{cosa}' aggiunge al commit anche il lavoro degli altri fronti, e in questo "
                   "progetto possono lavorare piu' sessioni in parallelo. Aggiungi solo i percorsi del fronte di "
                   "questa sessione (fronti: {elenco}), per esempio git add -- 'sito/' && git commit -m "
                   "'[sito] …'. Il subagent controllo-confini ti da' il comando esatto. Se l'utente ha chiesto di "
                   "includere piu' fronti, elenca i percorsi uno per uno."),
    },
    "en": {
        "senza_overview": ("FRONTS: once overview.md exists, add its '## Fronti' section with the fronti-progetto "
                           "skill (Fronti rule: every project split into fronts, one session per front)."),
        "senza_mappa": ("FRONT MAP MISSING. overview.md in {radice} has no '## Fronti' section. BEFORE any other "
                        "work run the fronti-progetto skill without asking: map the project's fronts (app, site, "
                        "server, marketing, release…; a simple project has a single front), create each front's "
                        "CLAUDE.md and STATO.md, do not move code. Then state this session's front and go on with "
                        "the request."),
        "unico": ("Single-front project: {nome}. Read {casa}/STATO.md if it exists and update it before closing a "
                  "block of work."),
        "multi": ("FRONTS of this project: {elenco}. One session = one front. In your first reply state this "
                  "session's front in one line (infer it from the request; if unclear and you are about to edit "
                  "files, ask), read the CLAUDE.md and STATO.md in its home folder and stay inside its paths. "
                  "Commit only its paths (controllo-confini subagent before committing), update STATO.md before "
                  "closing, use a worktree if another session works on the same code, open a new session to "
                  "switch front. Details: fronti-progetto skill."),
        "qui": " This session was opened inside {relativo}/: its front is {nome}.",
        "worktree": " You are in a worktree: work here and merge the branch when done.",
        "fuori": (" WARNING: these folders belong to no front and are not shared: {cartelle}. Update the map with "
                  "the fronti-progetto skill."),
        "blocco": ("fronti-guard: '{cosa}' would also commit other fronts' work, and several sessions may be "
                   "working on this project in parallel. Add only this session's front paths (fronts: {elenco}), "
                   "e.g. git add -- 'site/' && git commit -m '[site] …'. The controllo-confini subagent gives you "
                   "the exact command. If the user asked to include several fronts, list the paths one by one."),
    },
}


def testo(chiave, **valori):
    return TESTI[lingua()][chiave].format(**valori)


def git(radice, *argomenti):
    try:
        r = subprocess.run(["git", "-C", str(radice), *argomenti], capture_output=True, text=True, timeout=8)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def trova_radice(cwd):
    top = git(cwd, "rev-parse", "--show-toplevel")
    radice = Path(top.strip()) if top else None
    if radice is None:
        p = Path(cwd)
        if any((p / s).exists() for s in SEGNI) or any(p.glob("*.xcodeproj")):
            radice = p
    if radice is None or radice in (Path.home(), Path("/")):
        return None
    return radice


def esci(dati=None):
    if dati:
        print(json.dumps(dati, ensure_ascii=False))
    sys.exit(0)


def pulisci(percorso):
    p = percorso.strip()
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/") or "."


def leggi_mappa(radice):
    """None se overview.md manca; {} se manca la sezione; altrimenti fronti e condivisi."""
    overview = radice / "overview.md"
    if not overview.exists():
        return None
    righe = overview.read_text(encoding="utf-8", errors="ignore").splitlines()
    nella_sezione, fronti, condivisi = False, [], []
    for riga in righe:
        if TITOLO.match(riga):
            nella_sezione = True
            continue
        if nella_sezione and riga.startswith("## "):
            break
        if not nella_sezione:
            continue
        s = riga.strip()
        if s.startswith("|"):
            celle = [c.strip() for c in s.strip("|").split("|")]
            intestazione = celle[0].strip("* ").lower() in ("fronte", "front")
            if len(celle) < 2 or set("".join(celle)) <= set("-: ") or intestazione:
                continue
            casa = re.findall(r"`([^`]+)`", celle[2]) if len(celle) > 2 else []
            fronti.append({
                "nome": celle[0].strip("* "),
                "percorsi": [pulisci(p) for p in re.findall(r"`([^`]+)`", celle[1])],
                "casa": pulisci(casa[0]) if casa else ".",
            })
        elif re.match(r"^\**(condivis|shared)", s, re.IGNORECASE):
            condivisi += [pulisci(p) for p in re.findall(r"`([^`]+)`", s)]
    if not fronti:
        return {}
    return {"fronti": fronti, "condivisi": condivisi}


def mostra(percorsi):
    return ", ".join("`.`" if p == "." else f"`{p}/`" for p in percorsi)


def dentro(relativo, percorso):
    return percorso == "." or relativo == percorso or relativo.startswith(percorso + "/")


def cartelle_fuori_mappa(radice, mappa):
    elenco = git(radice, "ls-files", "--cached", "--others", "--exclude-standard")
    if elenco is None:
        return []
    cartelle = sorted({f.split("/", 1)[0] for f in elenco.splitlines() if "/" in f})
    coperti = [p for f in mappa["fronti"] for p in f["percorsi"]] + mappa["condivisi"]
    return [c for c in cartelle
            if not c.startswith(".") and not any(dentro(c, p) or p.startswith(c + "/") for p in coperti)]


def inizio(dati, radice):
    mappa = leggi_mappa(radice)
    if mappa is None:
        contesto = testo("senza_overview")
    elif not mappa:
        contesto = testo("senza_mappa", radice=radice)
    else:
        fronti = mappa["fronti"]
        if len(fronti) == 1:
            contesto = testo("unico", nome=fronti[0]["nome"], casa=fronti[0]["casa"])
        else:
            elenco = "; ".join(f"{f['nome']} ({mostra(f['percorsi'])})" for f in fronti)
            contesto = testo("multi", elenco=elenco)
            cwd = Path(dati.get("cwd") or os.getcwd()).resolve()
            try:
                relativo = str(cwd.relative_to(radice.resolve())) or "."
            except ValueError:
                relativo = "."
            qui = [f for f in fronti if relativo != "." and any(dentro(relativo, p) for p in f["percorsi"])]
            if qui:
                contesto += testo("qui", relativo=relativo, nome=qui[0]["nome"])
        if git(radice, "rev-parse", "--git-dir") != git(radice, "rev-parse", "--git-common-dir"):
            contesto += testo("worktree")
        fuori = cartelle_fuori_mappa(radice, mappa)
        if fuori:
            contesto += testo("fuori", cartelle=mostra(fuori[:10]))
    esci({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": contesto}})


def commit_di_tutto(comando, cwd):
    """(cosa, cartella) se il comando aggiunge o committa tutto il repository, altrimenti None."""
    if "git" not in comando:
        return None
    cartella = Path(cwd)
    for pezzo in re.split(r"&&|\|\||;|\||\n", comando):
        try:
            parole = shlex.split(pezzo)
        except ValueError:
            parole = pezzo.split()
        if not parole:
            continue
        if parole[0] == "cd" and len(parole) > 1:
            cartella = (cartella / os.path.expanduser(parole[1])).resolve()
            continue
        if parole[0] != "git":
            continue
        resto, dir_git = parole[1:], cartella
        while resto and resto[0].startswith("-"):
            if resto[0] in ("-C", "-c") and len(resto) > 1:
                if resto[0] == "-C":
                    dir_git = (dir_git / os.path.expanduser(resto[1])).resolve()
                resto = resto[2:]
            else:
                resto = resto[1:]
        if not resto:
            continue
        sotto, argomenti = resto[0], resto[1:]
        if sotto == "add":
            for a in argomenti:
                if a in ("-A", "--all", "-u", "--update", ":/", ":(top)") or re.fullmatch(r"-[a-zA-Z]*[Au][a-zA-Z]*", a):
                    return f"git add {a}", dir_git
                if a in (".", "./", "*"):
                    radice = trova_radice(dir_git)
                    if radice and dir_git.resolve() == radice.resolve():
                        return f"git add {a}", dir_git
        elif sotto == "commit":
            salta = False
            for a in argomenti:
                if salta:
                    salta = False
                    continue
                if a in ("--all", "-a"):
                    return f"git commit {a}", dir_git
                if re.fullmatch(r"-[a-zA-Z]+", a):
                    if "a" in a[1:]:
                        return f"git commit {a}", dir_git
                    salta = a[-1] in "mFCct"
                elif a in ("--message", "--file", "--author", "--date", "--template", "--reuse-message"):
                    salta = True
    return None


def prima_del_comando(dati):
    comando = (dati.get("tool_input") or {}).get("command") or ""
    trovato = commit_di_tutto(comando, dati.get("cwd") or os.getcwd())
    if not trovato:
        esci()
    cosa, cartella = trovato
    radice = trova_radice(cartella)
    mappa = leggi_mappa(radice) if radice else None
    if not mappa or len(mappa["fronti"]) < 2:
        esci()
    elenco = "; ".join(f"{f['nome']}: {mostra(f['percorsi'])}" for f in mappa["fronti"])
    esci({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": testo("blocco", cosa=cosa, elenco=elenco),
    }})


def main():
    try:
        dati = json.load(sys.stdin)
    except Exception:
        esci()
    evento = dati.get("hook_event_name")
    if evento == "PreToolUse":
        prima_del_comando(dati)
    elif evento == "SessionStart":
        radice = trova_radice(dati.get("cwd") or os.getcwd())
        if radice is not None:
            inizio(dati, radice)
    esci()


if __name__ == "__main__":
    main()
