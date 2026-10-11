"""Test di fronti-guard: python3 -m unittest discover -s tests -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "fronti-guard.py"

MAPPA = """# Cometa

## Fronti

| Fronte | Percorsi | Casa | Avvio | Sessione |
|---|---|---|---|---|
| **App** | `app/`, `App Watch/` | `app/` | — | Cometa · App |
| Sito | `sito/` | `sito/` | — | Cometa · Sito |

Condivisi (una sessione alla volta): `overview.md`, `docs/`

## Struttura
"""


def esegui(evento, cwd, comando=None, lingua="it"):
    dati = {"hook_event_name": evento, "cwd": str(cwd)}
    if comando is not None:
        dati.update({"tool_name": "Bash", "tool_input": {"command": comando}})
    env = {**os.environ, "FRONTI_LANG": lingua}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(dati), capture_output=True,
                       text=True, env=env, timeout=20)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


def repo(base, nome, file=(), overview=None):
    radice = Path(base) / nome
    radice.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=radice, check=True)
    for f in file:
        (radice / f).parent.mkdir(parents=True, exist_ok=True)
        (radice / f).write_text("x")
    if overview is not None:
        (radice / "overview.md").write_text(overview)
    return radice


class InizioSessione(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = cls.tmp.name
        cls.senza_overview = repo(base, "a", ["package.json"])
        cls.senza_mappa = repo(base, "b", ["src/x.js"], "# Overview\n")
        cls.multi = repo(base, "c", ["app/a.swift", "App Watch/w.swift", "sito/i.html", "docs/d.md",
                                     "nuovo/n.txt", ".github/w.yml"], MAPPA)
        cls.unico = repo(base, "d", ["src/a.js"], "# D\n\n## Fronti\n\n| Fronte | Percorsi | Casa | Avvio | "
                         "Sessione |\n|---|---|---|---|---|\n| Sito | `.` | `.` | — | D |\n")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def contesto(self, cwd, lingua="it"):
        return esegui("SessionStart", cwd, lingua=lingua)["hookSpecificOutput"]["additionalContext"]

    def test_senza_overview(self):
        self.assertIn("dopo aver creato overview.md", self.contesto(self.senza_overview))

    def test_senza_mappa_chiede_la_skill(self):
        t = self.contesto(self.senza_mappa)
        self.assertIn("MAPPA DEI FRONTI MANCANTE", t)
        self.assertIn("fronti-progetto", t)

    def test_multi_elenca_e_segnala_fuori_mappa(self):
        t = self.contesto(self.multi)
        self.assertIn("App (`app/`, `App Watch/`)", t)
        self.assertIn("Sito (`sito/`)", t)
        self.assertIn("`nuovo/`", t)
        self.assertNotIn(".github", t)
        self.assertNotIn("`docs/`", t.split("ATTENZIONE")[-1])

    def test_sessione_dentro_un_fronte(self):
        self.assertIn("il suo fronte e' Sito", self.contesto(self.multi / "sito"))

    def test_fronte_unico(self):
        self.assertIn("Progetto a fronte unico: Sito", self.contesto(self.unico))

    def test_inglese(self):
        self.assertIn("FRONTS of this project", self.contesto(self.multi, lingua="en"))

    def test_fuori_da_un_progetto_tace(self):
        vuota = Path(self.tmp.name) / "vuota"
        vuota.mkdir(exist_ok=True)
        self.assertIsNone(esegui("SessionStart", vuota))


class CommitDiTutto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.multi = repo(cls.tmp.name, "c", ["app/a.swift", "sito/i.html"], MAPPA)
        cls.unico = repo(cls.tmp.name, "d", ["src/a.js"], "# D\n\n## Fronti\n\n| Fronte | Percorsi | Casa | "
                         "Avvio | Sessione |\n|---|---|---|---|---|\n| Sito | `.` | `.` | — | D |\n")
        cls.senza = repo(cls.tmp.name, "e", ["src/a.js"], "# E\n")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def bloccato(self, comando, cwd=None):
        out = esegui("PreToolUse", cwd or self.multi, comando)
        return bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocca(self):
        for comando in ["git add -A", "git add --all && git commit -m 'x'", "git add .", "git add -u",
                        "git commit -am 'fix veloce'", "git commit -a -m 'x'", "git add -Av"]:
            with self.subTest(comando=comando):
                self.assertTrue(self.bloccato(comando))

    def test_blocca_con_cd_e_C(self):
        base = self.multi.parent
        self.assertTrue(self.bloccato("cd c && git add -A", cwd=base))
        self.assertTrue(self.bloccato("git -C c add --all", cwd=base))

    def test_lascia_passare(self):
        for comando in ["git add sito/ && git commit -m '[sito] - aggiunta pagina'",
                        "git add -- 'App Watch/' app/", "cd sito && git add .", "git commit -m 'a -a b'",
                        "git commit --amend --no-edit", "git status && git diff", "ls -la"]:
            with self.subTest(comando=comando):
                self.assertFalse(self.bloccato(comando))

    def test_non_blocca_senza_piu_fronti(self):
        self.assertFalse(self.bloccato("git add -A", cwd=self.unico))
        self.assertFalse(self.bloccato("git add -A", cwd=self.senza))

    def test_messaggio_inglese(self):
        out = esegui("PreToolUse", self.multi, "git add -A", lingua="en")
        self.assertIn("would also commit other fronts' work", out["hookSpecificOutput"]["permissionDecisionReason"])


class Plugin(unittest.TestCase):
    def test_hooks_json_punta_allo_script(self):
        radice = HOOK.parents[1]
        hooks = json.loads((radice / "hooks" / "hooks.json").read_text())["hooks"]
        comandi = [h["command"] for gruppo in hooks.values() for voce in gruppo for h in voce["hooks"]]
        self.assertTrue(all("${CLAUDE_PLUGIN_ROOT}/hooks/fronti-guard.py" in c for c in comandi))
        self.assertEqual(set(hooks), {"SessionStart", "PreToolUse"})


if __name__ == "__main__":
    unittest.main()
