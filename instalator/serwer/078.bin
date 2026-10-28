"""MT2009_PLUS_RARE_DROP_SWITCHES_V1: "Kupony SM, szarfy i Cor Draconis" - six
switches of the database editor (the owner, 5 October 2026): what a boss
and what a Metin stone hands out by itself, each kind on its own.

    Kupony SM z bossów / z metinów        m2_sm_boss_off   / m2_sm_metin_off
    Delikatne Sukno (szarfy) z bossów / z metinów   m2_sash_boss_off / m2_sash_metin_off
    Cor Draconis z bossów / z metinów     m2_cor_boss_off  / m2_cor_metin_off

Where they live: world event flags, rows of player.quest with dwPID 0
(lValue 1 = off; no row or 0 = on, the default and the old behaviour). The
db core loads every event flag at its boot and hands them to the game cores
(ClientManagerEventFlag.cpp), so a change is live after "Zastosuj" (the
restart restarts the db core too); a GM's "/e m2_cor_boss_off 1" switches
one live (and the db core writes it into the same row). The engine reads
them at drop time (server-patches/raremobrules, MT2009_PLUS_RARE_DROP_SWITCHES_V1,
item_manager.cpp / char_item.cpp; the drop wiki in server-patches/dropwiki).

What a switch holds back - only the game's own (built-in) sources:
  * Kupon SM (50), vnum 80017: the engine's roll per kill, CONFIG
    DRAGON_COIN_BOSS_PERMILLE (50 = 5%) / DRAGON_COIN_STONE_PERMILLE (3 = 0.3%);
  * sash: the +0 sash roll (boss 80%, Metin 15%, WuKong 15%, the per-mob rules
    of raremobrules) - since MT2009_PLUS_SASH_CLOTH_V1 (6 October) it gives
    Delikatne Sukno (80019, 2 / 5 / 10 by the killer's level 1-49 / 50-74 / 75+;
    ten make the plain sash at Uriel) instead of the sash - and, under "z bossów", the
    unique +3 sash (85004/85008/85014/85018/85024, 6-10%) of a boss chest
    opened with its key;
  * Cor Draconis (Rough), vnum 50255: the engine's roll (boss 80%, Metin 20%,
    a bot's kill 5%, WuKong 5 at 15%) and the rows of the drop tables that came
    with the game (Baronówna Pająków 9706: 3 at 5%, Król Skorpionów 9694: 10 at 5%).
A row the operator saved on the "Drop z potworów" page (Group MT2009_panel_*)
drops whatever these say. Bots: the same CreateDropItem, so the same switches.

Writes go through common_items (history with undo, pending until
"Zastosuj"): the table is registered as player.quest keyed by szName -
only these six names are ever written, and only the world's rows (dwPID 0)
carry such names. The current state for an export: SELECT szName, lValue
FROM player.quest WHERE dwPID=0 AND szName IN FLAGS.
"""
from flask import flash, redirect, render_template, request, url_for

from dbeditor import common_items as common
from dbeditor import tables_common

TABLE = "player.quest"
COL = "lValue"
MARKER = "MT2009_PLUS_RARE_DROP_SWITCHES_V1"

# (flag, kind, source, label) - the order of the page.
SWITCHES = (
    ("m2_sm_boss_off", "sm", "boss", "Kupony SM z bossów"),
    ("m2_sm_metin_off", "sm", "metin", "Kupony SM z metinów"),
    ("m2_sash_boss_off", "sash", "boss", "Delikatne Sukno (szarfy) z bossów"),
    ("m2_sash_metin_off", "sash", "metin", "Delikatne Sukno (szarfy) z metinów"),
    ("m2_cor_boss_off", "cor", "boss", "Cor Draconis z bossów"),
    ("m2_cor_metin_off", "cor", "metin", "Cor Draconis z metinów"),
)
FLAGS = tuple(s[0] for s in SWITCHES)
LABELS = {s[0]: s[3] for s in SWITCHES}

KINDS = {
    "sm": {"icon": "🎟️", "title": "Kupony SM", "items": "Kupon SM (50), vnum 80017 – wymienia się na Smocze Monety w ItemShopie"},
    "sash": {"icon": "🧣", "title": "Delikatne Sukno (szarfy)", "items": "Delikatne Sukno, vnum 80019 (×2 do 49 poz. zabójcy, ×5 od 50, ×10 od 75; 10 sztuk + 80 000 Yang = szarfa u Uriela) zamiast szarfy +0; przy bossach także szarfa unikatowa +3 ze skrzyń bossów"},
    "cor": {"icon": "🐉", "title": "Cor Draconis", "items": "Cor Draconis (surowy), vnum 50255 – kamień do alchemii"},
}

# What each switch turns off (the game's own sources; MT2009_PLUS_RARE_DROP_SWITCHES_V1).
SOURCES = {
    "m2_sm_boss_off": ["każdy boss: 5% na zabicie (ustawienie DRAGON_COIN_BOSS_PERMILLE = 50 ‰ w .env serwera)"],
    "m2_sm_metin_off": ["każdy metin: 0,3% na zabicie (ustawienie DRAGON_COIN_STONE_PERMILLE = 3 ‰ w .env serwera)"],
    "m2_sash_boss_off": ["każdy boss: Delikatne Sukno na 80% (WuKong 15%; Płomienny Feniks i Jajo Feniksa – nigdy)",
                         "skrzynia bossa otwierana kluczem: szarfa unikatowa +3 na 6–10% (nie Złota/Srebrna Szkatułka)"],
    "m2_sash_metin_off": ["każdy metin: Delikatne Sukno na 15% (Kamień Wzgórza i Metin Ciemności w Bibliotece – nigdy)"],
    "m2_cor_boss_off": ["każdy boss: 1 Cor na 80% (gdy zabija bot: 5%; WuKong: 5 Corów na 15%)",
                        "tabele dropu z gry: Baronówna Pająków – 3 Cory na 5%, Król Skorpionów – 10 Corów na 5%"],
    "m2_cor_metin_off": ["każdy metin: 1 Cor na 20% (gdy zabija bot: 5%; Metin Ciemności w Bibliotece – nigdy)"],
}

SPEC = {"kind": "int", "min": 0, "max": 1, "label": "Drop"}

# MT2009_PLUS_METIN_BOOK_SWITCH_V1 [Autor: Vekirion]: the one item the engine adds
# to every Metin's drop (item_manager.cpp CreateDropItem: topped up to one, for a
# killer at most 15 levels above the stone; also the previews and the drop wiki).
# Two world event flags in the same table, read by Mt2009PlusMetinBookVnum():
#   m2_metin_book_off   1 = the engine adds nothing (books only from the drop tables)
#   m2_metin_book_vnum  the item instead of the Skill Book (0 = 50300)
# No row = the old behaviour. The engine falls back to 50300 for a VNUM it does not know.
BOOK_OFF = "m2_metin_book_off"
BOOK_VNUM = "m2_metin_book_vnum"
BOOK_FLAGS = (BOOK_OFF, BOOK_VNUM)
BOOK_DEFAULT = 50300
LABELS.update({BOOK_OFF: "Księga z metinów (silnik)",
               BOOK_VNUM: "Księga z metinów – przedmiot (0 = Księga Umiejętności 50300)"})


def state_text(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return str(value)
    if number > 1:  # MT2009_PLUS_METIN_BOOK_SWITCH_V1: m2_metin_book_vnum holds a VNUM
        return f"przedmiot {number}"
    return "wyłączony" if number else "włączony"


def _formatter(col, value):
    return state_text(value) if col == COL else None


def register():
    common.register_table(TABLE, "szName", {COL: SPEC}, "Kupony SM, szarfy, Cor", "dbeditor.raredrop", _formatter)


def read_flags(rows):
    """{flag: 0/1} of the six switches plus the two global ones (raretoggle)."""
    names = FLAGS + ("m2_alchemy_off", "m2_sash_off")
    marks = ",".join(["%s"] * len(names))
    found = rows(f"SELECT szName, lValue FROM {TABLE} WHERE dwPID=0 AND szState='' AND szName IN ({marks})", names)
    values = {name: 0 for name in names}
    for row in found:
        name = row["szName"].decode() if isinstance(row["szName"], bytes) else row["szName"]
        try:
            values[name] = 1 if int(row["lValue"]) else 0
        except (TypeError, ValueError):
            pass
    return values


def save(rows, wanted, note):
    """wanted {flag: 0/1} -> the history's changed fields. A switch without a
    row gets one (0 = on, what the game already does) first, so the history
    and its undo cover the real change."""
    for flag in wanted:
        if flag not in FLAGS:
            raise ValueError(f"nieznany przełącznik {flag}")
        rows(f"INSERT IGNORE INTO {TABLE} (dwPID, szName, szState, lValue) VALUES (0, %s, '', 0)", (flag,))
    updates = [(flag, {COL: int(value)}) for flag, value in wanted.items()]
    _batch, changed = common.save_rows(TABLE, updates, note=note, label_of=lambda flag: LABELS.get(flag, flag))
    return changed


def read_book(rows):
    """MT2009_PLUS_METIN_BOOK_SWITCH_V1: {"off": bool, "vnum": int} (vnum 0 = 50300)."""
    marks = ",".join(["%s"] * len(BOOK_FLAGS))
    found = rows(f"SELECT szName, lValue FROM {TABLE} WHERE dwPID=0 AND szState='' AND szName IN ({marks})", BOOK_FLAGS)
    values = {name: 0 for name in BOOK_FLAGS}
    for row in found:
        name = row["szName"].decode() if isinstance(row["szName"], bytes) else row["szName"]
        try:
            values[name] = int(row["lValue"])
        except (TypeError, ValueError):
            pass
    return {"off": bool(values[BOOK_OFF]), "vnum": max(0, values[BOOK_VNUM])}


def save_book(rows, wanted, note):
    """MT2009_PLUS_METIN_BOOK_SWITCH_V1: wanted {flag: value} of BOOK_FLAGS, through
    the same history (undo, pending until "Zastosuj") as the six switches."""
    for flag in wanted:
        if flag not in BOOK_FLAGS:
            raise ValueError(f"nieznany przełącznik {flag}")
        rows(f"INSERT IGNORE INTO {TABLE} (dwPID, szName, szState, lValue) VALUES (0, %s, '', 0)", (flag,))
    updates = [(flag, {COL: int(value)}) for flag, value in wanted.items()]
    _batch, changed = common.save_rows(TABLE, updates, note=note, label_of=lambda flag: LABELS.get(flag, flag))
    return changed


def install(bp, ctx):
    import dbeditor
    common.init(ctx)
    register()
    common.install_history(bp, ctx)
    tables_common.register(bp)
    login_required = ctx["login_required"]

    def q(sql, params=()):
        return common.ctx()["rows"](sql, params)

    def pending_here():
        try:
            return [c for c in common.pending_changes() if c["tbl"] == TABLE and c["row_key"] in FLAGS + BOOK_FLAGS]
        except Exception:
            return []

    @bp.route("/rzadki-drop", methods=["GET", "POST"])
    @login_required
    def raredrop():
        if request.method == "POST":
            if not common.check_csrf():
                return redirect(url_for("dbeditor.raredrop"))
            try:
                current = read_flags(q)
            except Exception as exc:
                flash(f"Nie udało się odczytać przełączników: {exc}", "error")
                return redirect(url_for("dbeditor.raredrop"))
            # A checked box = the drop is on (flag 0); the form sends every switch.
            wanted = {}
            for flag in FLAGS:
                if request.form.get("present_" + flag) != "1":
                    continue
                value = 0 if request.form.get(flag) == "1" else 1
                if value != current.get(flag, 0):
                    wanted[flag] = value
            if not wanted:
                flash("Nic się nie zmieniło.", "info")
                return redirect(url_for("dbeditor.raredrop"))
            note = request.form.get("note", "").strip()[:200] or "Kupony SM, szarfy, Cor: " + ", ".join(
                f"{LABELS[f]} – {state_text(v)}" for f, v in wanted.items())
            try:
                changed = save(q, wanted, note)
            except Exception as exc:
                flash(f"Nie zapisano: {exc}", "error")
                return redirect(url_for("dbeditor.raredrop"))
            if changed:
                flash(f"Zapisano {len(changed)} przełącznik(i). Gra zastosuje je po restarcie rdzeni – kliknij Zastosuj.",
                      "success")
            else:
                flash("Nic się nie zmieniło.", "info")
            return redirect(url_for("dbeditor.raredrop"))

        error = None
        try:
            values = read_flags(q)
        except Exception as exc:
            values, error = {name: 0 for name in FLAGS + ("m2_alchemy_off", "m2_sash_off")}, str(exc)
        pending = pending_here()
        pending_flags = {c["row_key"] for c in pending}
        groups = []
        for kind in ("sm", "sash", "cor"):
            items = []
            for flag, k, source, label in SWITCHES:
                if k == kind:
                    items.append({"flag": flag, "source": source, "label": label, "on": not values.get(flag),
                                  "pending": flag in pending_flags, "sources": SOURCES[flag]})
            groups.append(dict(KINDS[kind], kind=kind, switches=items))
        try:
            history = common.history_batches(10, TABLE)
        except Exception:
            history = []
        book = book_view(pending_flags)
        return render_template("dbeditor/raredrop.html", groups=groups, error=error, pending=pending,
                               history=history, alchemy_off=bool(values.get("m2_alchemy_off")),
                               sash_off=bool(values.get("m2_sash_off")), dbe_csrf=common.csrf_token(),
                               book=book, **common.template_helpers())

    # ------------------------------------------- MT2009_PLUS_METIN_BOOK_SWITCH_V1 ---
    def item_name(vnum):
        found = q("SELECT vnum, locale_name FROM player.item_proto WHERE vnum=%s", (int(vnum),))
        if not found:
            return None
        return common.ctx()["game_text"](found[0]["locale_name"]) or f"przedmiot {vnum}"

    def book_view(pending_flags):
        try:
            state = read_book(q)
        except Exception as exc:
            return {"error": str(exc), "off": False, "vnum": 0, "item": BOOK_DEFAULT, "name": None, "mode": "default",
                    "pending": False}
        item = state["vnum"] or BOOK_DEFAULT
        try:
            name = item_name(item)
        except Exception:
            name = None
        mode = "off" if state["off"] else ("other" if state["vnum"] and state["vnum"] != BOOK_DEFAULT else "default")
        return dict(state, item=item, name=name, mode=mode, error=None,
                    pending=bool(set(BOOK_FLAGS) & set(pending_flags)))

    @bp.post("/rzadki-drop/ksiega")
    @login_required
    def raredrop_book():
        back = url_for("dbeditor.raredrop")
        if not common.check_csrf():
            return redirect(back)
        mode = request.form.get("book_mode", "")
        try:
            current = read_book(q)
            if mode == "off":
                wanted = {BOOK_OFF: 1}
            elif mode == "default":
                wanted = {BOOK_OFF: 0, BOOK_VNUM: 0}
            elif mode == "other":
                raw = (request.form.get("book_vnum") or "").strip().lower().lstrip("s")
                if not raw.isdigit() or not 1 <= int(raw) <= 4000000000:
                    raise ValueError(f"„{raw}” to nie VNUM przedmiotu.")
                vnum = int(raw)
                if item_name(vnum) is None:
                    raise ValueError(f"Przedmiotu {vnum} nie ma w item_proto – gra dałaby wtedy zwykłą Księgę Umiejętności.")
                wanted = {BOOK_OFF: 0, BOOK_VNUM: 0 if vnum == BOOK_DEFAULT else vnum}
            else:
                raise ValueError("Wybierz, co ma dawać metin.")
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(back)
        except Exception as exc:
            flash(f"Nie udało się odczytać ustawienia: {exc}", "error")
            return redirect(back)
        now = {BOOK_OFF: 1 if current["off"] else 0, BOOK_VNUM: current["vnum"]}
        wanted = {flag: value for flag, value in wanted.items() if now[flag] != value}
        if not wanted:
            flash("Nic się nie zmieniło.", "info")
            return redirect(back)
        note = request.form.get("note", "").strip()[:200] or "Księga z metinów: " + (
            "wyłączona" if mode == "off" else "Księga Umiejętności 50300" if mode == "default"
            else f"przedmiot {wanted.get(BOOK_VNUM, current['vnum'])}")
        try:
            changed = save_book(q, wanted, note)
        except Exception as exc:
            flash(f"Nie zapisano: {exc}", "error")
            return redirect(back)
        if changed:
            flash("Zapisano księgę z metinów. Gra zastosuje to po restarcie rdzeni – kliknij Zastosuj.", "success")
        else:
            flash("Nic się nie zmieniło.", "info")
        return redirect(back)

    # On the hub right after "Drop z potworów" (the parts install in __init__'s order).
    dbeditor.add_section("dbeditor.raredrop", "🔀", "Kupony SM, szarfy, Cor",
                         "wyłączniki dropu Kuponów SM, szarf i Cor Draconis – osobno z bossów i z metinów; "
                         "księga, którą silnik dokłada z każdego metina")
    entry = dbeditor.SECTIONS.pop()
    after = next((i + 1 for i, s in enumerate(dbeditor.SECTIONS) if s[0] == "dbeditor.drops_index"), len(dbeditor.SECTIONS))
    dbeditor.SECTIONS.insert(after, entry)
