---
name: fronti-progetto
description: "Divide ogni progetto in fronti di lavoro (app, sito, server, marketing, release…) e fa lavorare ogni sessione su un fronte solo. Mappa i fronti nella sezione ## Fronti di overview.md, crea per ogni fronte un CLAUDE.md con le sue regole e uno STATO.md da cui ripartire, e fissa il protocollo di sessione: dichiarare il fronte, restare nei suoi percorsi, fare commit solo dei suoi percorsi, aggiornare lo stato prima di chiudere, usare un worktree per il lavoro parallelo sullo stesso codice. Usala SEMPRE quando l'hook fronti-guard segnala la mappa mancante o cartelle fuori mappa, quando nasce un fronte nuovo (si inizia il sito o il marketing di un'app, un server, una release), quando l'utente chiede di suddividere, organizzare o riprendere un progetto, o di aprire una sessione per una parte del progetto. Splits any project into work fronts, one session per front."
---

# Fronti di progetto

Un progetto cresce per fronti: prima l'app, poi il sito, poi marketing, server, release. Se tutto
passa da una sessione sola, la conversazione si riempie, viene riassunta e perde dettagli; se due
sessioni lavorano alla cieca sugli stessi file, si pestano i piedi nei commit. La regola:
**un fronte = una cartella (o un gruppo di percorsi) = una sessione**, e la memoria del lavoro sta
nei file del fronte, non nelle chat.

Pezzi del sistema:
- questa skill (le regole e i passi);
- il subagent `mappa-fronti` (analizza il progetto e propone la mappa, solo lettura);
- il subagent `controllo-confini` (prima di un commit verifica che il lavoro resti nel fronte);
- l'hook `fronti-guard` (a inizio sessione ricorda la mappa o la chiede; blocca `git add -A`,
  `git add .`, `git add -u` e `git commit -a` nei progetti con più fronti).

Rispondi sempre nella lingua dell'utente, anche se queste istruzioni sono in italiano.

## Il formato della mappa (lo legge l'hook: rispettalo alla lettera)

In `overview.md`, una sezione di secondo livello che si chiama esattamente `## Fronti`:

```markdown
## Fronti

| Fronte | Percorsi | Casa | Avvio | Sessione |
|---|---|---|---|---|
| App | `app/`, `packages/`, `Cometa.xcodeproj/` | `app/` | — | Cometa · App |
| Sito | `sito/` | `sito/` | — | Cometa · Sito |
| Marketing | `marketing/` | `marketing/` | — | Cometa · Marketing |

Condivisi (una sessione alla volta): `overview.md`, `CLAUDE.md`, `docs/`, `design/`
```

- **Percorsi**: tutto ciò che appartiene al fronte, ognuno tra backtick. Ogni cartella di primo
  livello (tranne quelle che iniziano con un punto) deve stare in un fronte o tra i Condivisi,
  altrimenti l'hook la segnala come fuori mappa.
- **Casa**: la cartella dove stanno il `CLAUDE.md` e lo `STATO.md` del fronte. Di solito è la
  cartella del fronte; se il fronte è sparso in più cartelle, scegli la principale.
- **Avvio**: la skill o il comando con cui conviene aprire una sessione di quel fronte, se ce n'è
  uno nel progetto o tra le skill installate (`—` se nessuno).
- **Sessione**: il nome da dare alla sessione (`Progetto · Fronte`).
- **Condivisi**: file e cartelle che servono a più fronti. Si toccano da una sessione alla volta.
- **Progetto semplice** (un tema WordPress, un sito singolo): una riga sola con percorso `.` e
  casa `.`. Non inventare fronti che non esistono.

## A. Mappare un progetto (prima volta, o cartelle fuori mappa)

1. Se manca `overview.md`, crealo prima: è la mappa della codebase (struttura, cosa fa ogni
   file importante, come si avvia, compila, testa e pubblica).
2. Lancia il subagent `mappa-fronti` passandogli la radice del progetto. Ti restituisce la
   sezione pronta, i dettagli di ogni fronte e le segnalazioni.
3. Rivedi la proposta. Un fronte è un prodotto o un canale con ciclo di vita, strumenti o
   pubblico propri (app, sito, server/API, marketing, store/release). Cartelle di supporto
   (`docs/`, `design/`, `tools/`, `config/`) vanno nel fronte che le usa o tra i Condivisi: non
   spezzettare.
4. Scrivi la sezione `## Fronti` in `overview.md`, subito dopo l'introduzione. Se esiste già,
   aggiornala con una modifica mirata. Se `git status` mostra `overview.md` modificato da
   un'altra sessione, tocca solo la sezione Fronti.
5. Per ogni fronte crea, se mancano, i due file nella sua casa, dai modelli in `modelli/`:
   - `<casa>/CLAUDE.md`: confini, regole, skill, comandi del fronte. Claude lo legge da solo
     quando lavora in quella cartella. Se un `CLAUDE.md` c'è già, aggiungi solo la sezione
     `## Fronte` che manca, senza riscrivere il resto. Se la casa è la radice (fronte unico),
     non serve un secondo `CLAUDE.md`: basta quello del progetto.
   - `<casa>/STATO.md`: dove siamo, cosa resta, decisioni. Riempilo con quello che sai davvero
     (`git log -- <percorsi>`, documenti del fronte); se non sai, lascia "da compilare".
6. **Non spostare né rinominare codice** per pulire la suddivisione: rompe build, import,
   percorsi dei progetti Xcode e deploy. Se la struttura mescola due fronti nella stessa
   cartella, proponi lo spostamento all'utente e aspetta il sì.
7. Aggiorna l'elenco file di `overview.md` con i nuovi `CLAUDE.md`/`STATO.md`.
8. Riassumi all'utente in poche righe: i fronti, i nomi di sessione, cosa hai creato. Poi torna
   alla richiesta per cui era stata aperta la sessione.

## B. Il protocollo di ogni sessione

1. **Dichiara il fronte** nella prima risposta, in una riga: `Fronte: Sito (sito/)`. Deducilo
   dalla richiesta, dalla cartella in cui è aperta la sessione o dal suo nome. Se non è chiaro e
   stai per modificare file, chiedilo offrendo i fronti come opzioni.
2. Se hai uno strumento per rinominare la sessione, dalle il nome della colonna Sessione.
3. **Leggi** `<casa>/CLAUDE.md` e `<casa>/STATO.md` prima di lavorare.
4. **Resta nei percorsi del fronte.** Prima di toccare un altro fronte o un file condiviso,
   dillo in una riga. Se il lavoro sull'altro fronte è più di un ritocco, proponi una sessione
   dedicata invece di farlo qui.
5. **Lavoro parallelo sullo stesso codice** (due funzioni dell'app insieme): la seconda sessione
   lavora in un worktree, su un ramo suo, e lo unisce a fine lavoro.
6. **Commit solo dei percorsi del fronte**: `git add -- 'sito/'`, messaggio con il prefisso del
   fronte (`[sito] …`). Mai `git add -A`, `git add .` dalla radice, `git add -u`, `git commit -a`:
   l'hook li blocca. Prima del commit lancia il subagent `controllo-confini` con il nome del
   fronte: ti dà il comando `git add` esatto e segnala file di altri fronti.
7. **Aggiorna `STATO.md`** a fine blocco di lavoro (consegna, pausa, prima di chiudere): cosa è
   fatto, cosa è in corso, prossimi passi, decisioni prese. Breve, al presente.
8. **Cambio fronte o sessione troppo lunga** (riassunta più di una volta): proponi una sessione
   nuova e dai all'utente il primo messaggio pronto, per esempio:
   `Riprendi il fronte Sito: leggi sito/STATO.md e continua da "prossimi passi".`

## C. Nasce un fronte nuovo

Succede quando si inizia una parte nuova (il sito dopo l'app, il marketing, un server):

1. Crea la cartella del fronte (nome chiaro, nello stile delle altre: `sito/`, `marketing/`).
2. Aggiungi la riga alla tabella, con Avvio e Sessione.
3. Crea `CLAUDE.md` e `STATO.md` dai modelli e aggiorna `overview.md`.
4. Proponi all'utente di aprire una sessione dedicata, con il nome e il primo messaggio pronti.

## D. Riprendere un fronte in una sessione nuova

Leggi la mappa, poi `<casa>/CLAUDE.md`, `<casa>/STATO.md` e
`git log --oneline -15 -- <percorsi>`. Riassumi in due righe dove eravamo e continua dai
prossimi passi.
