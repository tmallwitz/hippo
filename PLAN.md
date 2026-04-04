# Hippo — Planungsdokument

Ein experimenteller Claude-Agent basierend auf dem Claude Agent SDK (Python),
mit Telegram-Frontend und Obsidian-Vault als mehrschichtigem Gedächtnis.
Portierung und Weiterentwicklung der Idee von `obsidian-memory-mcp` (YuNaga224).

---

## Zum Namen

**Hippo** — Kurzform für *Hippocampus*, die Hirnregion die beim Menschen
genau das tut was dieser Agent tun soll: Kurzzeit-Eindrücke in strukturiertes
Langzeitgedächtnis überführen, vorzugsweise im Schlaf. Die biologische
Metapher ist nicht nur Deko, sie trägt die Architektur: Kurzzeit-Buffer,
Dream-Cycle, mehrschichtiges Langzeitgedächtnis. Auf der CLI liest sich das
natürlich (`hippo dream`, `hippo remember`, `hippo recall`). Der sekundäre
Charme des Flusspferds als Wappentier ist ein erlaubter Bonus.

---

## Designentscheidungen (fixiert)

| Entscheidung | Wert |
| --- | --- |
| Sprache | Python 3.12+, Package-Manager `uv` |
| Framework | `claude-agent-sdk` (Python), In-Process MCP-Server via `@tool` + `create_sdk_mcp_server` |
| Model-Backend | Claude Pro OAuth (`claude setup-token`), kein API-Key |
| Frontend | Telegram (aiogram v3), ab Phase 1 |
| Host | Headless Linux (local), via `uv run`, no containerization |
| Skills | Filesystem-Skills im Vault unter `.claude/skills/` |
| Prozedurales Wissen | Wird als Skills abgebildet, NICHT als eigener Memory-Store |
| Vault-Strategie | Ein Vault pro Bot, Trennung intern per Ordner |
| Multi-User | Ein menschlicher User pro Bot (Telegram-ID Whitelist in Config) |
| Inter-Bot-Kommunikation | Filesystem-Mailbox im Vault (`inbox/`), ab Phase 3 |
| Dream-Trigger | Cron (systemd-timer) + manuelles `/dream` (überschreibt Cron-Fenster) |
| Kurzzeit-Buffer nach Dream | Archivieren in `short_term/processed/YYYY-MM-DD.jsonl`, Git-commit optional später |

---

## Projekt-Struktur (finale Zielform)

```
hippo/
├── pyproject.toml             # uv-verwaltet
├── .env.example               # Telegram-Token, User-Whitelist, Vault-Pfad
├── PLAN.md                    # dieses Dokument
├── README.md
├── hippo/
│   ├── __init__.py
│   ├── config.py              # Pydantic-Settings, lädt .env
│   ├── agent.py               # ClaudeSDKClient Setup, System-Prompt, Tool-Wiring
│   ├── telegram_bridge.py     # aiogram v3 Bot, User-Whitelist, Session-pro-User
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── types.py           # Entity, Relation, Observation, Episode, ShortTermEntry
│   │   ├── store.py           # MemoryStore Protocol + Implementierungen
│   │   ├── semantic.py        # Knowledge-Graph als Markdown-Files
│   │   ├── episodic.py        # Daily-Note Journal
│   │   ├── short_term.py      # JSONL Append-only Buffer
│   │   ├── mailbox.py         # Inter-Bot Mailbox (Phase 3)
│   │   └── server.py          # Alle Tools als SDK-MCP-Server
│   └── dream/
│       ├── __init__.py
│       ├── runner.py          # Sub-Agent-Orchestrierung
│       ├── prompts.py         # System-Prompts für Dream-Agent
│       └── cron.py            # Entry-Point für systemd-timer
└── tests/
    ├── test_memory_roundtrip.py
    ├── test_short_term.py
    └── test_dream_consolidation.py
```

Im Vault liegt parallel:

```
<bot-vault>/
├── .claude/
│   └── skills/                # Prozedurales Wissen als SKILL.md
│       ├── antworte_kurz_auf_deutsch/
│       └── ...
├── semantic/                  # Knowledge-Graph (Phase 1)
│   ├── People/
│   ├── Projects/
│   └── Topics/
├── episodic/                  # Daily Journal (Phase 2)
│   └── 2026-04-04.md
├── short_term/                # Kurzzeitgedächtnis (Phase 3)
│   ├── buffer.jsonl
│   └── processed/
├── inbox/                     # Inter-Bot Mailbox (Phase 3)
└── dream_reports/             # Dream-Protokolle (Phase 3)
```

---

## Phase 1 — Port nach Python + Telegram-Bridge

**Ziel:** Funktionsäquivalenter Port von `obsidian-memory-mcp` nach Python als
In-Process SDK-Server, plus minimale Telegram-Bridge mit User-Whitelist.
Kein Dream, kein Kurzzeitgedächtnis, kein Episodisches. Nur semantisches
Memory und ein lauffähiger Bot.

### Scope

- Neun Tools aus dem Original portiert:
  `create_entities`, `create_relations`, `add_observations`,
  `delete_entities`, `delete_observations`, `delete_relations`,
  `read_graph`, `search_nodes`, `open_nodes`
- Markdown-Storage mit YAML-Frontmatter, Relations als `[[Typed::Target]]`
- `MemoryStore` Protocol von Anfang an (macht Phase 3 einfacher)
- Telegram-Bridge mit aiogram v3
- User-Whitelist via `ALLOWED_TELEGRAM_IDS` in `.env`
- Ein Bot = ein Vault = ein User
- System-Prompt der den Agent anweist, die Memory-Tools aktiv zu nutzen

### Tech-Stack Phase 1

```toml
# pyproject.toml Auszug
dependencies = [
    "claude-agent-sdk>=0.1.0",
    "aiogram>=3.0",
    "python-frontmatter>=1.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0",
]
```

### Snippet-Orientierung (nicht vollständig)

Tool-Definition im SDK-Stil:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(
    "create_entities",
    "Create multiple new entities in the knowledge graph",
    {"entities": list},
)
async def create_entities(args):
    store = get_semantic_store()
    created = [store.put(e) for e in args["entities"] if not store.exists(e["name"])]
    return {"content": [{"type": "text", "text": f"Created: {created}"}]}

memory_server = create_sdk_mcp_server(
    name="hippo-memory",
    version="0.1.0",
    tools=[create_entities, create_relations, add_observations, ...],
)
```

Telegram-Session pro User (in Phase 1 reicht ein einziger Client, da
ein User pro Bot):

```python
# Pseudo
client = ClaudeSDKClient(options=ClaudeAgentOptions(
    system_prompt=SYSTEM_PROMPT,
    mcp_servers={"memory": memory_server},
    allowed_tools=[...],
    setting_sources=["project"],  # lädt .claude/skills/ aus dem Vault
))
await client.connect()

@dp.message()
async def handle(msg: Message):
    if msg.from_user.id not in ALLOWED_IDS:
        return
    await client.query(msg.text)
    async for response in client.receive_response():
        # Text-Blöcke extrahieren und zurück an Telegram
        ...
```

### Akzeptanzkriterien Phase 1

1. `uv run hippo` startet den Bot, Telegram ist erreichbar.
2. Nicht-whitelistete User bekommen keine Antwort (still gedroppt).
3. Du sagst dem Bot "merk dir dass mein Lieblingsbuch The Dispossessed von Le Guin ist".
4. Im Vault erscheint `semantic/Topics/The_Dispossessed.md` mit korrektem
   Frontmatter und einer Observation dazu.
5. Obsidian Graph View öffnet den Vault und zeigt das Entity als Knoten.
6. Du sagst "was weißt du über mein Lieblingsbuch?", der Bot findet die Information
   via `search_nodes`.
7. Du editierst die Datei manuell in Obsidian, fügst eine Observation hinzu,
   fragst erneut, der Bot sieht die Änderung.
8. Roundtrip-Test in `tests/test_memory_roundtrip.py` läuft grün.
9. Ein handgepflegter Skill unter `.claude/skills/` wird vom Agent im richtigen
   Kontext geladen (Verifikation: teste mit einer simplen Präferenzregel).

### Offene Mini-Entscheidungen für Phase 1

- **Relation-Syntax:** `[[Typed::Target]]` beibehalten (original) oder
  Obsidian-Alias `[[Target|Typed]]`? Empfehlung: Original-Syntax für
  Kompatibilität mit dem TS-Referenz-Projekt, Pfadwechsel später möglich.
- **Graph-in-Memory oder Per-Request-Parse:** Für den Start Per-Request-Parse
  (immer frisch aus Files lesen). Caching erst wenn messbar langsam.

---

## Phase 2 — Episodisches Gedächtnis

**Ziel:** Eine zweite Memory-Schicht neben dem Knowledge-Graph: episodisches
Wissen als zeitlich geordnete Einträge in Daily Notes. Prozedurales Wissen
wird über Skills abgebildet und bekommt keine eigene Schicht.

### Warum keine prozedurale Schicht?

Skills (`SKILL.md` mit Frontmatter-Beschreibung + Body) sind bereits die
richtige Abstraktion für "wenn Situation X, tue Y". Das SDK lädt sie
automatisch aus dem Vault, und der Dream-Cycle in Phase 3 kann neue Skills
generieren. Eine parallele prozedurale Memory-Schicht wäre redundant.

### Scope

- `episodic.py` mit zwei Tools: `log_episode` und `recall_episodes`
- Daily Notes im Format `episodic/YYYY-MM-DD.md`
- Jeder Episode-Eintrag hat Timestamp, Content, Tags
- `recall_episodes` unterstützt Zeitraum-Filter und Volltextsuche
- System-Prompt-Update: Agent darf/soll episodische Einträge proaktiv loggen,
  wenn etwas Erlebnishaftes passiert (Entscheidungen, Meilensteine, Learnings)

### Format einer Daily Note

```markdown
---
date: 2026-04-04
episodes: 3
---

# 2026-04-04

## 14:32 — Projekt Hippo gestartet
tags: projekt, hippo, meta
Heute den Plan für Hippo finalisiert. Drei Phasen,
Dream-Command als Kern-Idee.

## 16:10 — Entscheidung Pro-Auth
tags: technik, hippo
Anstatt Bedrock oder API-Key nutzen wir OAuth via `claude setup-token`.
```

### Retrieval-Strategie

- **Automatisch im Kontext:** Nichts aus episodic. Der Agent muss aktiv
  `recall_episodes` aufrufen wenn relevant.
- **Skills automatisch:** Ja, wie vom SDK vorgesehen.
- **Semantisches:** Auf Anfrage via `search_nodes`.

Das hält den Kontext schlank und gibt dem Agent echte Agency über sein Erinnern.

### Akzeptanzkriterien Phase 2

1. Du chattest mehrere Tage mit dem Bot über verschiedene Themen.
2. Der Bot legt Daily Notes an und schreibt selbstständig Episoden rein.
3. Du fragst "was haben wir letzten Dienstag besprochen?" und der Bot findet
   via `recall_episodes` die passende Daily Note.
4. Du editierst manuell eine Episode in Obsidian, der Bot sieht die Änderung.
5. Ein Skill der eine feste Präferenz encodiert ("antworte immer knapp auf
   Deutsch") wird vom Agent gelernt und konsistent angewandt.

---

## Phase 3 — Kurzzeitgedächtnis + Dream-Cycle + Inter-Bot-Mailbox

**Ziel:** Das Zwei-Stufen-Modell einführen. Tagsüber landet alles schnell und
unstrukturiert im Kurzzeit-Buffer. Der Dream-Cycle (nachts via Cron oder
manuell via `/dream`) konsolidiert den Buffer in semantisch, episodisch und
Skills. Außerdem: Bots können über Filesystem-Mailboxen miteinander reden.

### Teil A: Kurzzeitgedächtnis

- Neues Tool `remember(content, tags?)` das sehr billig ist: einfach eine
  Zeile in `short_term/buffer.jsonl` anhängen, fertig.
- Der Agent nutzt dieses Tool liberal. Keine Struktur, keine Deduplizierung,
  keine Entscheidung in welchen Store. Nur "das ist interessant, merk's dir".
- Entry-Format:
  ```json
  {
    "ts": "2026-04-04T14:32:11Z",
    "session": "tg-12345",
    "content": "User prefers concise German responses and uses uv instead of pip",
    "tags": ["preference", "tooling"]
  }
  ```

### Teil B: Der Dream-Cycle

**Wichtig:** Implementiert als **Sub-Agent**, nicht als Tool. Eigener
`ClaudeSDKClient` mit eigenem System-Prompt, eigenen Tools, eigenem Kontext.
Das SDK unterstützt verschachtelte Clients problemlos.

**Ablauf eines Dream-Cycles:**

1. Dream-Agent startet mit fokussiertem System-Prompt (siehe unten).
2. Liest den aktuellen Buffer (alles seit letztem Dream).
3. Liest relevante Teile des Langzeit-Speichers (nicht alles, nur via
   `search_nodes` kontextabhängig).
4. Entscheidet für jeden Buffer-Eintrag:
   - **Fakt über Entity** → `create_entities` oder `add_observations`
   - **Ereignis mit Zeitbezug** → `log_episode`
   - **Wiederkehrende Präferenz/Regel** → neuer Skill in `.claude/skills/`
   - **Irrelevant** → verwerfen
5. Schreibt einen Dream-Report nach `dream_reports/YYYY-MM-DD.md`.
6. Archiviert den Buffer nach `short_term/processed/YYYY-MM-DD.jsonl`.
7. Buffer wird geleert.

**System-Prompt-Skelett für den Dream-Agent:**

```
Du bist der Dream-Konsolidator von Hippo. Dein Job ist Schlaf-Konsolidierung:
rohe Eindrücke aus dem Kurzzeit-Buffer in strukturiertes Langzeitgedächtnis
überführen.

Für jeden Eintrag im Buffer entscheide:
1. Semantisch (Fakt über Person/Projekt/Topic)
   → create_entities / add_observations
2. Episodisch (Erlebnis mit Zeitbezug)
   → log_episode
3. Skill-würdig (wiederkehrende Präferenz oder Handlungsregel)
   → schreibe SKILL.md in .claude/skills/<name>/
4. Irrelevant (Smalltalk, Rauschen)
   → verwerfen

Priorisiere Präzision vor Vollständigkeit. Dedupliziere aggressiv:
bevor du eine neue Entity erstellst, suche mit search_nodes ob sie
schon existiert. Im Zweifel verwerfen, nicht speichern.

Am Ende schreibe einen Report mit:
- Anzahl verarbeiteter Einträge
- Neue Entities, Observations, Episoden, Skills
- Was wurde verworfen und warum
```

**Trigger:**

- `systemd-timer` nachts um 3 Uhr auf dem Host.
- `/dream` Command im Telegram überschreibt das Fenster und startet sofort.
- Während ein Dream läuft: `/dream` wird ignoriert oder queued.

**Autonome Skill-Erstellung:**

Der Dream-Agent darf selbstständig `SKILL.md` Dateien schreiben, aber jeder
neue Skill wird im Dream-Report erwähnt. Du kannst nachträglich in Obsidian
reviewen, editieren oder löschen. Git-Commit nach jedem Dream macht das zu
einer perfekten Audit-Spur.

### Teil C: Inter-Bot-Mailbox

**Mechanismus:** Jeder Bot hat einen `inbox/` Ordner in seinem Vault. Bots
schreiben Nachrichten an andere Bots als Markdown-Dateien mit Frontmatter:

```markdown
---
from: alice
to: bob
ts: 2026-04-04T22:15:00Z
subject: Heads-up about tomorrow's review
---

Just confirmed the code review is scheduled for 10am tomorrow.
If the user asks about it, here are the details...
```

**Tools für den Agent:**

- `send_message(bot_name, subject, content)` → legt Datei in der Inbox
  des Ziel-Bots ab (Pfad kommt aus Config).
- Die eigene Inbox wird beim Dream-Cycle mitverarbeitet: Nachrichten werden
  wie Buffer-Einträge behandelt und ins Langzeitgedächtnis konsolidiert.

**Warum Filesystem und nicht Netzwerk:** Debuggbar (du siehst die Nachrichten
in Obsidian), atomar (mv ist atomar), kein Netzwerk-Stack, kein Auth-Hassle,
und die Metapher passt: Bots schreiben sich Briefe, die erst beim nächsten
Schlaf-Zyklus wirklich "gelesen" und verinnerlicht werden.

**Bot-Registry:** Einfache YAML-Datei im Projekt-Root `bots.yaml`:

```yaml
bots:
  alice:
    vault: ~/hippo-vaults/alice
    role: "personal daily driver"
  bob:
    vault: ~/hippo-vaults/bob
    role: "work assistant"
  carol:
    vault: ~/hippo-vaults/carol
    role: "research companion"
```

### Akzeptanzkriterien Phase 3

1. Der Agent ruft während einer normalen Konversation mehrfach `remember`
   auf, `buffer.jsonl` füllt sich.
2. `/dream` im Telegram startet den Dream-Agent, du siehst im Chat eine
   Status-Meldung und bekommst am Ende den Report.
3. Der Dream-Report zeigt plausible Einträge: X Entities neu, Y Observations
   hinzugefügt, Z Episoden geloggt, W Skills erstellt.
4. Nach dem Dream ist `buffer.jsonl` leer, `processed/YYYY-MM-DD.jsonl`
   existiert.
5. Ein autonom vom Dream-Agent erstellter Skill funktioniert in der nächsten
   Session (wird geladen und wirkt).
6. Systemd-Timer triggert den Dream um 3 Uhr, Report liegt am Morgen vor.
7. Inter-Bot: Bot A sendet Nachricht an Bot B, bei B's nächstem Dream-Cycle
   wird die Nachricht konsolidiert und B "weiß" danach was A ihm gesagt hat.
8. Git-Log im Vault zeigt nach mehreren Dreams eine saubere Historie der
   Gedächtnis-Evolution.

---

## Risiken und Unsicherheiten

- **Pro-Rate-Limits:** Bei mehreren parallelen Bots + Dream-Cycles kann es knapp
  werden. Monitoring einbauen und ggf. Dream-Zeitpunkte versetzen
  (z.B. Bot A 3 Uhr, Bot B 3:30, Bot C 4 Uhr).
- **Skill-Inflation:** Der Dream-Agent könnte zu eifrig neue Skills
  generieren. Gegenmaßnahme: im Dream-Prompt eine Hürde ("nur wenn mindestens
  dreimal in verschiedenen Kontexten beobachtet"). Nachjustieren.
- **Konflikte Obsidian vs. Agent:** Wenn du eine Datei in Obsidian offen hast
  während der Agent sie schreibt, kann Obsidian fragen ob neu laden. Fürs
  Erste akzeptieren, später eventuell Datei-Locks.
- **Episodic-Blowup:** Daily Notes können groß werden. In Phase 2 akzeptabel,
  in Phase 3 kann der Dream-Cycle alte Daily Notes zusammenfassen.
- **Dream-Determinismus:** Zwei Dreams auf demselben Buffer könnten
  unterschiedliche Entscheidungen treffen. Das ist okay solange der Agent
  nicht dieselbe Info doppelt speichert (Deduplizierung via search_nodes
  ist Pflicht).

---

## Reihenfolge für Claude Code

1. Phase 1 komplett fertigstellen inklusive Tests und Akzeptanzkriterien.
   Nicht in Phase 2 reingrätschen, auch wenn es verlockend ist.
2. Zwischendurch: ein, zwei Tage mit dem Bot chatten, Gefühl für die
   Memory-Struktur bekommen. Eventuell Relation-Syntax nachjustieren.
3. Phase 2: Episodic dazubauen, sicherstellen dass Skills sauber geladen
   werden.
4. Phase 3: Erst Kurzzeit, dann Dream als Sub-Agent, dann Mailbox. In dieser
   Reihenfolge, weil jedes auf dem vorigen aufbaut.
5. Nach jeder Phase: Git-Tag setzen (`v0.1-phase1`, `v0.2-phase2`, `v0.3-phase3`).
