"""MT2009_PLUS_DROP_BULK_V1 [Autor: Vekirion]: "Drop – zmiana masowa" in the
database editor: one change of one item in the drop of many monsters at once.

The "Drop" page (drops.py) edits a "zestaw" - monsters whose drop of one kind is
EXACTLY the same. Metins and bosses mostly have tables of their own, so giving
every Metin one more item, or swapping one item for another in all of them,
meant opening every monster on its own. Here the operator:

  1. picks the monsters with filters: name or a list of VNUMs, Metin / boss /
     ordinary monster, rank, level from-to, the map (the respawn files, groups
     expanded - spawnfiles.SpawnIndex, the same as "Potwory i bossowie"), and
     "drops item X" (any kind or one kind of group);
  2. chooses one change of ONE item (the rest of each monster's table stays):
       add       - the item in a kind of group (a new group where a monster
                   has none of that kind); an item the group already has is
                   skipped or updated;
       edit      - the item's chance (set or ×), count, or swap it for another
                   item (keeping or setting the chance);
       remove    - the item out of the chosen kinds of group;
  3. sees every monster's table line before -> after (and what is skipped and
     why), and saves it all at once.

The save is the same as a save of a zestaw (dropfiles.py): every changed
(monster, kind) group goes whole into drops/mob_drop_item.custom.txt with its
MT2009_REPLACES line, one backup of the previous file (one "Przywróć" undoes
the whole change), pending until "Zastosuj". A preview carries the sha of the
custom file it was made on; a save over a file changed meanwhile is refused.

Not here: the item the ENGINE adds to every Metin (Skill Book 50300) - that is
"Kupony SM, szarfy, Cor" -> "Księga z metinów" (raredrop.py,
MT2009_PLUS_METIN_BOOK_SWITCH_V1); the common and etc tables have pages of
their own.
"""
import re

from flask import flash, g, redirect, render_template, request, url_for

from . import dropfiles as df

MARKER = "MT2009_PLUS_DROP_BULK_V1"
LIMIT = 600
OPS = ("add", "edit", "remove")
OP_NAMES = {"add": "Dodaj przedmiot", "edit": "Zmień albo zamień przedmiot", "remove": "Usuń przedmiot"}
MOB_KIND_FILTER = {"metin": "Metiny", "boss": "Bossowie", "mob": "Zwykłe potwory", "other": "Inne (NPC, ...)"}
EXISTS = {"skip": "pomiń tego potwora", "update": "ustaw ilość i szansę jak wyżej"}


# ------------------------------------------------------------------ pure ---
def item_token(raw, label):
    """"27001" / "s50011" (a chest's draw) from what the operator typed, or
    ValueError. "" -> None."""
    text = (raw or "").strip().lower()
    if not text:
        return None
    text = text.split()[0]
    if text.isdigit() and 0 < int(text) < 4000000000:
        return str(int(text))
    if text.startswith("s") and text[1:].isdigit() and int(text[1:]) > 0:
        return "s" + str(int(text[1:]))
    raise ValueError(f"{label}: „{raw}” to nie VNUM przedmiotu (ani s+numer szkatułki).")


def same_item(a, b):
    return df._item_key(a) == df._item_key(b)


def kind_prob(kind, pct, weight):
    """The value written to the file for a chance typed in % (drop, limit,
    thiefgloves) or a weight (kill)."""
    if kind == "kill":
        return str(int(weight))
    return df.mob_file_prob(kind, pct)


def scale_prob(kind, prob, factor):
    if kind == "kill":
        return str(max(1, int(round(df.num(prob) * factor))))
    cap = 100.0 if kind == "limit" else 400.0
    return df.fmt_num(min(cap, df.num(prob) * factor), 9)


def apply_op(kind, group, op, p):
    """One (monster, kind) group -> (new items or None = no change, status,
    message). group None = the monster has no group of this kind. p: the
    parsed form (parse_params)."""
    items = [dict(e) for e in group["items"]] if group else []
    item = p["item"]
    if op == "add":
        if kind != p["kind"]:
            return None, "none", ""
        if item.startswith("s") and kind != "drop":
            return None, "skip", "losowanie ze szkatułki działa tylko w zwykłym dropie"
        found = [e for e in items if same_item(e["item"], item)]
        line = {"item": item, "count": str(p["count"]), "prob": kind_prob(kind, p["pct"], p["weight"]),
                "rare": str(p["rare"]) if kind == "kill" else "0", "comment": p["comment"]}
        if found:
            if p["exists"] != "update":
                return None, "skip", "już ma ten przedmiot w tej grupie"
            changed = False
            for entry in found:
                for key in ("count", "prob", "rare"):
                    if df._norm_prob(entry.get(key) or 0) != df._norm_prob(line[key]):
                        entry[key] = line[key]
                        changed = True
            return (items, "change", "zmieniona istniejąca pozycja") if changed else (None, "same", "już ma dokładnie to")
        if len(items) >= df.MOB_MAX_LINES:
            return None, "skip", f"grupa ma już {df.MOB_MAX_LINES} pozycji (więcej silnik nie czyta)"
        items.append(line)
        return items, ("change" if group else "new"), ("" if group else "nowa grupa")
    if not group or kind not in p["kinds"]:
        return None, "none", ""
    found = [e for e in items if same_item(e["item"], item)]
    if not found:
        return None, "none", ""
    if op == "remove":
        items = [e for e in items if not same_item(e["item"], item)]
        return items, ("empty" if not items else "change"), ("grupa zostaje pusta – potwór straci drop tego rodzaju"
                                                              if not items else "")
    # edit
    target = p.get("to_item")
    if target and target.startswith("s") and kind != "drop":
        return None, "skip", "losowanie ze szkatułki działa tylko w zwykłym dropie"
    note = ""
    if target and not same_item(target, item) and any(same_item(e["item"], target) for e in items):
        note = "w grupie był już nowy przedmiot – teraz są dwie osobne pozycje"
    changed = False
    for entry in found:
        before = dict(entry)
        if target:
            entry["item"] = target
            entry["comment"] = p["to_comment"]
        if p["prob_mode"] == "set":
            entry["prob"] = kind_prob(kind, p["pct"], p["weight"])
        elif p["prob_mode"] == "mul":
            entry["prob"] = scale_prob(kind, entry["prob"], p["factor"])
        if p["count"] is not None:
            entry["count"] = str(p["count"])
        if (df._item_key(before["item"]), df._norm_prob(before["prob"]), str(int(df.num(before["count"])))) != \
                (df._item_key(entry["item"]), df._norm_prob(entry["prob"]), str(int(df.num(entry["count"])))):
            changed = True
    if not changed:
        return None, "same", "już jest tak, jak chcesz"
    return items, "change", note


def parse_params(form):
    """The action half of the form -> p (ValueError with a Polish message)."""
    op = form.get("op", "")
    if op not in OPS:
        raise ValueError("Wybierz, co zrobić (dodaj, zmień albo usuń).")
    p = {"op": op, "item": item_token(form.get("item"), "Przedmiot")}
    if not p["item"]:
        raise ValueError("Wpisz przedmiot (VNUM).")
    p["kinds"] = [k for k in df.MOB_KINDS if k in form.getlist("kinds")] or list(df.MOB_KINDS)
    p["kind"] = form.get("kind", "drop") if form.get("kind") in df.MOB_KINDS else "drop"
    p["pct"], p["weight"], p["rare"], p["factor"], p["count"] = 0.0, 1, 0, 1.0, None
    p["exists"] = form.get("exists") if form.get("exists") in EXISTS else "skip"
    p["comment"] = p["to_comment"] = ""
    p["to_item"] = None
    p["prob_mode"] = "keep"
    if op == "add":
        p["count"] = int(df.parse_number(form.get("count") or "1", "Ilość", 1, df.MOB_MAX_COUNT, True))
        if p["kind"] == "kill":
            p["weight"] = int(df.parse_number(form.get("weight") or "1", "Waga", 1, 1000000, True))
            p["rare"] = int(df.parse_number(form.get("rare") or "0", "Rare", 0, 100, True))
        else:
            p["pct"] = df.parse_number(form.get("pct"), "Szansa %", 0.000001, 100)
        p["kill_drop"] = str(int(df.parse_number(form.get("kill_drop") or "1", "Co ile zabójstw", 1, 1000000, True)))
        p["level_limit"] = str(int(df.parse_number(form.get("level_limit") or "0", "Od poziomu", 0, 250, True)))
        p["kinds"] = [p["kind"]]
    elif op == "edit":
        p["to_item"] = item_token(form.get("to_item"), "Zamień na")
        mode = form.get("prob_mode", "keep")
        p["prob_mode"] = mode if mode in ("keep", "set", "mul") else "keep"
        if p["prob_mode"] == "set":
            if not (form.get("pct") or "").strip() and not (form.get("weight") or "").strip():
                raise ValueError("Wpisz nową szansę % (albo wagę dla „Co N zabójstw”).")
            p["pct"] = df.parse_number(form.get("pct") or "0", "Szansa %", 0, 100)
            p["weight"] = int(df.parse_number(form.get("weight") or "1", "Waga", 1, 1000000, True))
        elif p["prob_mode"] == "mul":
            p["factor"] = df.parse_number(form.get("factor"), "Mnożnik", 0.01, 100)
        raw_count = (form.get("new_count") or "").strip()
        if raw_count:
            p["count"] = int(df.parse_number(raw_count, "Nowa ilość", 1, df.MOB_MAX_COUNT, True))
        if not p["to_item"] and p["prob_mode"] == "keep" and p["count"] is None:
            raise ValueError("Nic do zmiany – wpisz nowy przedmiot, nową szansę albo nową ilość.")
    return p


# --------------------------------------------------------------- the page ---
def install(bp, ctx):
    rows, game_text, login_required = ctx["rows"], ctx["game_text"], ctx["login_required"]

    def mobs():
        if "dbe_mobs" not in g:
            g.dbe_mobs = df.mob_table(rows, game_text)
        return g.dbe_mobs

    def state():
        spool = df.spool_dir()
        text = df.read_text(df.base_path(spool, "mob"))
        base = df.parse_mob_drop(text or "")
        custom = df.read_mob_custom(spool)
        return {"spool": spool, "base": base, "custom": custom, "effective": df.effective_mob_drops(base, custom),
                "has_base": text is not None, "token": df.file_sha(df.custom_path(spool, "mob"))}

    def chest_vnums():
        spool = df.spool_dir()
        base, _ = df.read_chest_base(spool)
        return set(base) | set(df.read_chest_custom(spool))

    def names_for(tokens):
        return df.item_names(rows, game_text, [t for t in tokens if t])

    def spawn_index():
        try:
            from . import spawnfiles
            return spawnfiles.SpawnIndex.load(spawnfiles.spool_dir())
        except Exception:  # an older image, no respawn files yet: no map filter
            return None

    def mob_label(vnum):
        info = mobs().get(vnum)
        return (info["name"] or f"Potwór {vnum}") if info else f"Nieznany potwór {vnum}"

    def line_text(kind, entry, group, names):
        item = str(entry["item"]).lower()
        if item.startswith("s"):
            label = "szkatułka " + item[1:]
        else:
            known = names.get(int(item)) if item.isdigit() else None
            label = known["name"] if known else f"NIEZNANY {item}"
        count = int(df.num(entry.get("count") or 1))
        chance = df.mob_chance(kind, entry, group) if group else 0
        extra = f" (waga {int(df.num(entry['prob']))})" if kind == "kill" else ""
        return f"{label}{' ×' + str(count) if count > 1 else ''} – {df.pct_text(chance)}{extra}"

    # ------------------------------------------------------------ filters ---
    def read_filters(args):
        f = {"q": (args.get("q") or "").strip(), "typ": args.get("typ", ""), "ranga": args.get("ranga", ""),
             "od": (args.get("od") or "").strip(), "do": (args.get("do") or "").strip(),
             "mapa": (args.get("mapa") or "").strip(), "dropi": (args.get("dropi") or "").strip(),
             "dropi_kind": args.get("dropi_kind", "")}
        f["typ"] = f["typ"] if f["typ"] in MOB_KIND_FILTER else ""
        f["dropi_kind"] = f["dropi_kind"] if f["dropi_kind"] in df.MOB_KINDS else ""
        return f

    def select_mobs(f, st):
        """(monsters, too_many, error, searched) for the filters."""
        searched = any(f[k] for k in ("q", "typ", "ranga", "od", "do", "mapa", "dropi"))
        if not searched:
            return [], False, None, False
        found = list(mobs().values())
        try:
            if f["q"]:
                if re.fullmatch(r"[\d\s,;]+", f["q"]):
                    wanted = {int(v) for v in re.split(r"[\s,;]+", f["q"]) if v}
                    found = [m for m in found if m["vnum"] in wanted]
                else:
                    needle = f["q"].casefold()
                    found = [m for m in found if needle in (m["name"] or "").casefold()]
            if f["typ"]:
                found = [m for m in found if m["kind"] == f["typ"]]
            if f["ranga"].isdigit():
                found = [m for m in found if m["rank"] == int(f["ranga"])]
            if f["od"]:
                low = int(df.parse_number(f["od"], "Poziom od", 0, 999, True))
                found = [m for m in found if m["level"] >= low]
            if f["do"]:
                high = int(df.parse_number(f["do"], "Poziom do", 0, 999, True))
                found = [m for m in found if m["level"] <= high]
            if f["mapa"]:
                index = spawn_index()
                if not f["mapa"].isdigit() or index is None:
                    raise ValueError("Filtr mapy nie działa – gra nie opublikowała jeszcze plików respawnu.")
                on_map = index.mobs_by_map().get(int(f["mapa"]), set())
                found = [m for m in found if m["vnum"] in on_map]
            if f["dropi"]:
                token = item_token(f["dropi"], "Dropi przedmiot")
                kinds = [f["dropi_kind"]] if f["dropi_kind"] else list(df.MOB_KINDS)
                found = [m for m in found if any(
                    any(same_item(e["item"], token) for e in st["effective"].get((m["vnum"], k), {}).get("items", []))
                    for k in kinds)]
        except ValueError as exc:
            return [], False, str(exc), True
        found.sort(key=lambda m: (m["level"], m["vnum"]))
        return found[:LIMIT], len(found) > LIMIT, None, True

    def map_choices():
        index = spawn_index()
        if not index:
            return [], None
        return [(idx, index.map_title(idx)) for idx, vnums in sorted(index.mobs_by_map().items()) if vnums], index

    def mob_rows(found, f, st, index):
        token = None
        if f["dropi"]:
            try:
                token = item_token(f["dropi"], "")
            except ValueError:
                token = None
        names = names_for([token] if token else [])
        result = []
        for m in found:
            kinds = []
            for k in df.MOB_KINDS:
                group = st["effective"].get((m["vnum"], k))
                if not group:
                    continue
                lines = [line_text(k, e, group, names) for e in group["items"] if token and same_item(e["item"], token)]
                kinds.append({"kind": k, "count": len(group["items"]), "lines": lines,
                              "custom": group.get("source") == "custom"})
            maps = index.maps_of_mob(m["vnum"])[:3] if index else []
            result.append(dict(m, kinds=kinds, maps=[index.map_title(i) for i in maps] if index else []))
        return result

    # --------------------------------------------------------------- plan ---
    def make_plan(st, selected, p):
        """[(mob, kind, status, message, before, after, new_items)] for every
        selected monster and the kinds the change can touch."""
        plan = []
        kinds = [p["kind"]] if p["op"] == "add" else p["kinds"]
        for mob in selected:
            for kind in kinds:
                group = st["effective"].get((mob, kind))
                items, status, message = apply_op(kind, group, p["op"], p)
                if status == "none":
                    continue
                if p["op"] in ("edit", "remove") and kind == "drop" and group and group.get("kept"):
                    if any(same_item(e["item"], p["item"]) for gr in group["kept"] for e in gr["items"]):
                        message = (message + "; " if message else "") + \
                            "ten przedmiot dropi też z nowej grupy z gry obok zapisu panelu (przejmij ją na stronie zestawu)"
                plan.append({"mob": mob, "kind": kind, "status": status, "message": message,
                             "group": group, "items": items})
        return plan

    def plan_view(plan, p):
        tokens = [p["item"], p.get("to_item")]
        for row in plan:
            for source in (row["group"]["items"] if row["group"] else []), (row["items"] or []):
                tokens += [e["item"] for e in source]
        names = names_for(sorted({t.lstrip("s") for t in tokens if t}))
        watched = {df._item_key(p["item"])} | ({df._item_key(p["to_item"])} if p.get("to_item") else set())
        view = []
        for row in plan:
            kind, group = row["kind"], row["group"]
            before = [line_text(kind, e, group, names) for e in (group["items"] if group else [])
                      if df._item_key(e["item"]) in watched]
            after = []
            if row["items"] is not None:
                new_group = {"type": kind, "items": row["items"],
                             "kill_drop": (group or {}).get("kill_drop") or p.get("kill_drop", "1")}
                after = [line_text(kind, e, new_group, names) for e in row["items"] if df._item_key(e["item"]) in watched]
            info = mobs().get(row["mob"])
            view.append(dict(row, name=mob_label(row["mob"]), info=info, before=before, after=after,
                             lines_before=len(group["items"]) if group else 0,
                             lines_after=len(row["items"]) if row["items"] is not None else None))
        return view

    def validate_items(p):
        names = names_for([p["item"], p.get("to_item")])
        chests = None
        for label, token in (("Przedmiot", p["item"]), ("Zamień na", p.get("to_item"))):
            if not token:
                continue
            if token.isdigit():
                if int(token) not in names:
                    if p["op"] == "remove" or (label == "Przedmiot" and p["op"] == "edit"):
                        continue  # a broken line may be taken out or swapped
                    raise ValueError(f"{label}: przedmiotu {token} nie ma w item_proto (rdzeń gry by nie wstał).")
            else:
                chests = chest_vnums() if chests is None else chests
                if int(token[1:]) not in chests and not (label == "Przedmiot" and p["op"] != "add"):
                    raise ValueError(f"{label}: nie ma szkatułki {token[1:]} w special_item_group (nic by nie wypadło).")
        for key, token in (("comment", p["item"]), ("to_comment", p.get("to_item"))):
            if token and token.isdigit() and int(token) in names:
                p[key] = names[int(token)]["name"]
            elif token:
                p[key] = token
        return names

    def save_plan(st, plan, p, reason):
        custom = dict(st["custom"])
        done = 0
        for row in plan:
            if row["items"] is None:
                continue
            mob, kind, group = row["mob"], row["kind"], row["group"]
            if not row["items"]:
                # as "Usuń ten drop" on a zestaw (drops.py): nothing of this kind
                if df.image_groups_of(st["base"], mob, kind):
                    custom[(mob, kind)] = {"mob": mob, "type": kind, "kill_drop": "1", "level_limit": "0", "items": [],
                                           "replaces": [gr["name"] for gr in df.image_groups_of(st["base"], mob, kind)]}
                else:
                    custom.pop((mob, kind), None)
            else:
                kill_drop = ((group or {}).get("kill_drop") or p.get("kill_drop") or "1") if kind == "kill" else "0"
                level_limit = ((group or {}).get("level_limit") or p.get("level_limit") or "0") if kind == "limit" else "0"
                new = {"type": kind, "items": row["items"], "kill_drop": kill_drop, "level_limit": level_limit}
                if kind == "kill" and int(df.num(new["kill_drop"])) < 1:
                    new["kill_drop"] = "1"
                custom[(mob, kind)] = dict(new, mob=mob,
                                           replaces=df.replaces_for_save(st["base"], st["custom"], st["effective"], mob, kind))
            done += 1
        if done:
            df.write_custom(st["spool"], "mob", df.render_mob_custom(custom, reason, st["base"]), reason)
        return done

    def reason_of(p, count):
        what = {"add": f"dodano {p['item']} ({p['kind']})", "remove": f"usunieto {p['item']}",
                "edit": f"zmieniono {p['item']}" + (f" na {p['to_item']}" if p.get("to_item") else "")}[p["op"]]
        return f"zmiana masowa: {what} - {count} grup"

    # -------------------------------------------------------------- views ---
    def render(st, f, preview=None, p=None, form_items=None, code=200):
        found, too_many, error, searched = select_mobs(f, st) if preview is None else ([], False, None, False)
        maps, index = map_choices() if preview is None else ([], None)
        counts = {}
        if preview is not None:
            for row in preview:
                counts[row["status"]] = counts.get(row["status"], 0) + 1
        return render_template(
            "dbeditor/drops_bulk.html", f=f, mobs=mob_rows(found, f, st, index) if found else [], too_many=too_many,
            error=error, searched=searched, limit=LIMIT, maps=maps, kinds_filter=MOB_KIND_FILTER,
            rank_names=df.MOB_RANK_NAMES, kind_names=df.MOB_KIND_SHORT, kind_help=df.MOB_KIND_NAMES, ops=OP_NAMES,
            exists=EXISTS, preview=preview, p=p, form_items=form_items or [], counts=counts, token=st["token"],
            status=df.live_state(st["spool"], "mob"), has_base=st["has_base"], csrf=df.csrf_token(),
            prefill=request.args, filters=request.query_string.decode("ascii", "replace")), code

    @bp.route("/drops/masowo")
    @login_required
    def drops_bulk():
        return render(state(), read_filters(request.args))

    @bp.post("/drops/masowo")
    @login_required
    def drops_bulk_post():
        back = url_for("dbeditor.drops_bulk") + ("?" + request.form["filters"] if request.form.get("filters") else "")
        if not df.csrf_ok(request.form):
            flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return redirect(back)
        st = state()
        if not st["has_base"]:
            flash("Gra nie opublikowała jeszcze mob_drop_item.txt – nie ma czego zmieniać.", "error")
            return redirect(back)
        selected = []
        for value in request.form.getlist("mob"):
            if value.isdigit() and int(value) in mobs() and int(value) not in selected:
                selected.append(int(value))
        try:
            if not selected:
                raise ValueError("Zaznacz co najmniej jednego potwora.")
            p = parse_params(request.form)
            validate_items(p)
        except ValueError as exc:
            flash(str(exc), "error")
            flash("Nic nie zostało zapisane.", "error")
            return redirect(back)
        plan = make_plan(st, selected, p)
        if request.form.get("step") == "save":
            if request.form.get("token", "") != st["token"]:
                flash("Drop zmienił się od podglądu (inny zapis w panelu). Nic nie zapisano – zrób podgląd jeszcze raz.", "error")
                return redirect(back)
            changes = [row for row in plan if row["items"] is not None]
            if not changes:
                flash("Nic do zapisania – żadna grupa się nie zmienia.", "info")
                return redirect(back)
            try:
                done = save_plan(st, plan, p, reason_of(p, len(changes)))
            except OSError as exc:
                flash(f"Nie udało się zapisać pliku w wolumenie spool: {exc}", "error")
                return redirect(back)
            skipped = sum(1 for row in plan if row["status"] == "skip")
            flash(f"Zmiana masowa zapisana: {done} grup dropu u {len({r['mob'] for r in changes})} potworów"
                  + (f", pominięto {skipped}" if skipped else "")
                  + ". Gra użyje tego po restarcie rdzeni (Zastosuj). Cofnięcie: Kopie zapasowe → najnowsza kopia.", "success")
            return redirect(back)
        form_items = [(k, v) for k, values in request.form.lists() if k not in ("dbe_csrf", "step", "token")
                      for v in values]
        return render(st, read_filters({}), preview=plan_view(plan, p), p=p, form_items=form_items)
