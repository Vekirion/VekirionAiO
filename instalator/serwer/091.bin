"""MT2009_PLUS_DROP_BULK_V1 [Autor: Vekirion]: python3 -m unittest test_dbeditor_drops_bulk

"Drop – zmiana masowa" (dbeditor/drops_bulk.py): the pure part (one group,
one change), and the page through the Flask test client on a temporary spool
with the samples of test_dbeditor_drops - filters, preview (nothing written),
save (one write, one backup, the rest of every table kept), the guard against
a file changed after the preview, and the game side (m2-drops) taking it."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from flask import Blueprint, Flask
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

import dbeditor
from dbeditor import chests, drops, drops_bulk
from dbeditor import dropfiles as df
from test_dbeditor_drops import CHEST_SAMPLE, COMMON_SAMPLE, ETC_SAMPLE, M2_DROPS, MOB_SAMPLE, FakeDb

HERE = Path(__file__).resolve().parent


def make_app(spool, mob_vnums):
    app = Flask(__name__, static_folder=str(HERE / "static"))
    app.secret_key = "test-only"
    app.config.update(TESTING=True, DBE_SPOOL=str(spool))
    app.jinja_loader = ChoiceLoader([
        DictLoader({"base.html": "<main>{% with m=get_flashed_messages(with_categories=true) %}{% for c, t in m %}"
                                 "<p class='flash {{ c }}'>{{ t }}</p>{% endfor %}{% endwith %}"
                                 "{% block content %}{% endblock %}</main>"}),
        FileSystemLoader(str(HERE / "templates"))])
    bp = Blueprint("dbeditor", "dbeditor", url_prefix="/db")
    bp.add_url_rule("/", "index", lambda: "hub")
    ctx = {"app": app, "db": None, "rows": FakeDb(mob_vnums), "one": None,
           "login_required": lambda view: view, "game_text": lambda value: value or ""}
    drops.install(bp, ctx)
    drops_bulk.install(bp, ctx)
    chests.install(bp, ctx)
    app.register_blueprint(bp)
    return app


def params(**form):
    class Form(dict):
        def getlist(self, key):
            value = self.get(key)
            return value if isinstance(value, list) else ([value] if value is not None else [])
    return drops_bulk.parse_params(Form(form))


class PureTests(unittest.TestCase):
    group = {"type": "drop", "kill_drop": "0", "items": [
        {"item": "27001", "count": "1", "prob": "4", "rare": "0", "comment": "a"},
        {"item": "s50011", "count": "1", "prob": "2", "rare": "0", "comment": ""}]}

    def test_add(self):
        p = params(op="add", item="50300", kind="drop", count="1", pct="0.5")
        p["comment"] = "Ksiega"
        items, status, _ = drops_bulk.apply_op("drop", self.group, "add", p)
        self.assertEqual(status, "change")
        self.assertEqual(items[-1], {"item": "50300", "count": "1", "prob": "2", "rare": "0", "comment": "Ksiega"})
        self.assertEqual(len(self.group["items"]), 2)                       # the input is not touched
        self.assertEqual(drops_bulk.apply_op("drop", None, "add", p)[1], "new")
        self.assertEqual(drops_bulk.apply_op("kill", self.group, "add", p)[1], "none")  # other kind
        again = drops_bulk.apply_op("drop", {"items": items}, "add", p)
        self.assertEqual(again[1], "skip")                                  # already there
        p["exists"] = "update"
        p["pct"] = 1.0
        updated = drops_bulk.apply_op("drop", {"items": items}, "add", p)
        self.assertEqual((updated[1], updated[0][-1]["prob"]), ("change", "4"))
        chest = params(op="add", item="s50011", kind="kill", count="1", weight="3")
        self.assertEqual(drops_bulk.apply_op("kill", None, "add", chest)[1], "skip")   # s... only in drop
        full = {"items": [{"item": str(i), "count": "1", "prob": "1"} for i in range(1, 256)]}
        self.assertEqual(drops_bulk.apply_op("drop", full, "add", p)[1], "skip")       # 255 lines max

    def test_edit_and_remove(self):
        swap = params(op="edit", item="27001", to_item="27002", prob_mode="keep")
        items, status, _ = drops_bulk.apply_op("drop", self.group, "edit", swap)
        self.assertEqual((status, items[0]["item"], items[0]["prob"]), ("change", "27002", "4"))
        both = drops_bulk.apply_op("drop", self.group, "edit", params(op="edit", item="27001", to_item="s50011"))
        self.assertIn("dwie osobne pozycje", both[2])
        scaled = params(op="edit", item="s50011", prob_mode="mul", factor="3")
        self.assertEqual(drops_bulk.apply_op("drop", self.group, "edit", scaled)[0][1]["prob"], "6")
        limit = {"type": "limit", "items": [{"item": "27005", "count": "1", "prob": "50"}]}
        self.assertEqual(drops_bulk.apply_op("limit", limit, "edit", params(op="edit", item="27005", prob_mode="mul",
                                                                            factor="3"))[0][0]["prob"], "100")  # capped
        kill = {"type": "kill", "kill_drop": "10", "items": [{"item": "27001", "count": "1", "prob": "3"}]}
        self.assertEqual(drops_bulk.apply_op("kill", kill, "edit", params(op="edit", item="27001", prob_mode="mul",
                                                                          factor="0.1"))[0][0]["prob"], "1")
        set_pct = params(op="edit", item="27001", prob_mode="set", pct="0.25", weight="7", new_count="3")
        self.assertEqual(drops_bulk.apply_op("drop", self.group, "edit", set_pct)[0][0], dict(
            self.group["items"][0], prob="1", count="3"))
        self.assertEqual(drops_bulk.apply_op("kill", kill, "edit", set_pct)[0][0]["prob"], "7")
        self.assertEqual(drops_bulk.apply_op("drop", self.group, "edit",
                                             params(op="edit", item="27001", prob_mode="set", pct="1"))[1], "same")
        self.assertEqual(drops_bulk.apply_op("drop", self.group, "edit", params(op="edit", item="99", new_count="2"))[1],
                         "none")
        items, status, _ = drops_bulk.apply_op("drop", self.group, "remove", params(op="remove", item="27001"))
        self.assertEqual((status, [e["item"] for e in items]), ("change", ["s50011"]))
        only = {"items": [self.group["items"][0]]}
        self.assertEqual(drops_bulk.apply_op("drop", only, "remove", params(op="remove", item="27001"))[1], "empty")
        self.assertEqual(drops_bulk.apply_op("drop", only, "remove",
                                             params(op="remove", item="27001", kinds=["kill"]))[1], "none")

    def test_params_refused(self):
        for form in ({"op": "x", "item": "1"}, {"op": "add", "item": ""}, {"op": "add", "item": "abc"},
                     {"op": "add", "item": "1", "pct": "150"}, {"op": "edit", "item": "1"},
                     {"op": "edit", "item": "1", "prob_mode": "mul", "factor": "0"}):
            with self.assertRaises(ValueError, msg=form):
                params(**form)


class PageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = Path(self.tmp.name)
        (self.spool / "drops").mkdir()
        (self.spool / "chests").mkdir()
        (self.spool / "drops" / "mob_drop_item.base.txt").write_text(MOB_SAMPLE, encoding="utf-8")
        (self.spool / "drops" / "common_drop_item.base.txt").write_bytes(COMMON_SAMPLE.encode("latin-1"))
        (self.spool / "drops" / "etc_drop_item.base.txt").write_text(ETC_SAMPLE, encoding="ascii")
        (self.spool / "drops" / "drop_item_group.base.txt").write_text("", encoding="ascii")
        (self.spool / "chests" / "special_item_group.base.txt").write_text(CHEST_SAMPLE, encoding="utf-8")
        self.sections = list(dbeditor.SECTIONS)
        self.app = make_app(self.spool, [101, 102, 103, 8001, 8002])
        self.client = self.app.test_client()
        self.client.get("/db/drops/masowo")
        with self.client.session_transaction() as session:
            self.csrf = session["dbe_drops_csrf"]

    def tearDown(self):
        dbeditor.SECTIONS[:] = self.sections
        self.tmp.cleanup()

    def post(self, step="preview", **form):
        data = dict({"dbe_csrf": self.csrf, "step": step}, **form)
        if step == "save" and "token" not in data:
            data["token"] = df.file_sha(df.custom_path(self.spool, "mob"))
        return self.client.post("/db/drops/masowo", data=data, follow_redirects=True).get_data(as_text=True)

    def custom(self):
        return df.read_mob_custom(self.spool)

    def test_filters(self):
        page = self.client.get("/db/drops/masowo").get_data(as_text=True)
        self.assertIn("Wybierz potwory", page)
        self.assertNotIn('name="mob"', page)                                # nothing listed without a filter
        metins = self.client.get("/db/drops/masowo?typ=metin").get_data(as_text=True)
        self.assertIn('value="8001"', metins)
        self.assertIn('value="8002"', metins)
        self.assertNotIn('value="101"', metins)
        who = self.client.get("/db/drops/masowo?dropi=27001").get_data(as_text=True)
        for vnum in ("101", "102", "8001"):
            self.assertIn(f'name="mob" value="{vnum}"', who)
        self.assertNotIn('name="mob" value="103"', who)
        self.assertIn("Przedmiot 27001 – 1%", who)
        self.assertIn('value="edit" checked', who)                         # from "who drops": swap/edit first
        kill = self.client.get("/db/drops/masowo?dropi=27002&dropi_kind=kill").get_data(as_text=True)
        self.assertIn('name="mob" value="101"', kill)
        self.assertNotIn('name="mob" value="102"', kill)
        listed = self.client.get("/db/drops/masowo?q=8001,103").get_data(as_text=True)
        self.assertIn('name="mob" value="103"', listed)
        self.assertNotIn('name="mob" value="101"', listed)
        self.assertIn("Poziom do", self.client.get("/db/drops/masowo?od=1&do=abc").get_data(as_text=True))
        # the links from the other pages
        self.assertIn("Zmień masowo u wszystkich", self.client.get("/db/drops?q=27001").get_data(as_text=True))
        self.assertIn("Zmiana masowa", self.client.get("/db/drops").get_data(as_text=True))

    def test_add_preview_then_save(self):
        form = {"mob": ["101", "103", "8001"], "op": "add", "item": "50300", "kind": "drop", "count": "1", "pct": "2",
                "exists": "skip", "filters": "typ=metin"}
        page = self.post(**form)
        self.assertIn("Podgląd", page)
        self.assertIn("Zmieni się 3 grup", page)
        self.assertIn("w tym 1 nowych grup", page)                         # 103 had no drop group
        self.assertIn("Przedmiot 50300 – 2%", page)
        self.assertIsNone(df.read_text(df.custom_path(self.spool, "mob")))  # a preview writes nothing
        page = self.post(step="save", **form)
        self.assertIn("Zmiana masowa zapisana: 3 grup", page)
        custom = self.custom()
        self.assertEqual(sorted(custom), [(101, "drop"), (103, "drop"), (8001, "drop")])
        self.assertEqual([(e["item"], e["prob"]) for e in custom[(8001, "drop")]["items"]],
                         [("27001", "8"), ("s50011", "2"), ("50300", "8")])     # both image groups kept
        self.assertEqual(custom[(8001, "drop")]["replaces"], ["Metin", "MetinMore"])
        self.assertEqual(custom[(103, "drop")]["replaces"], [])
        self.assertIn("-- Przedmiot 50300", df.read_text(df.custom_path(self.spool, "mob")))
        self.assertEqual(len(list((self.spool / "drops" / "backup").glob("mob_drop_item.custom.*.txt"))), 1)
        self.assertEqual([p["key"] for p in df.pending_changes(self.spool)], ["mob"])
        # the same again: every monster skipped, nothing written
        page = self.post(step="save", **form)
        self.assertIn("Nic do zapisania", page)
        self.assertEqual(len(list((self.spool / "drops" / "backup").glob("mob_drop_item.custom.*.txt"))), 1)

    def test_new_kill_and_limit_groups(self):
        self.post(step="save", mob=["102", "103"], op="add", item="27005", kind="kill", count="2", weight="5",
                  rare="10", kill_drop="40", exists="skip")
        custom = self.custom()
        self.assertEqual(custom[(103, "kill")]["kill_drop"], "40")
        self.assertEqual(custom[(103, "kill")]["items"][0]["rare"], "10")
        self.post(step="save", mob=["101"], op="add", item="27006", kind="kill", count="1", weight="1",
                  kill_drop="7", exists="skip")
        custom = self.custom()
        self.assertEqual(custom[(101, "kill")]["kill_drop"], "100")         # an existing group keeps its own
        self.assertEqual([e["item"] for e in custom[(101, "kill")]["items"]], ["27002", "27003", "27006"])
        self.post(step="save", mob=["8001", "103"], op="add", item="27007", kind="limit", count="1", pct="10",
                  level_limit="55", exists="skip")
        custom = self.custom()
        self.assertEqual((custom[(8001, "limit")]["level_limit"], custom[(103, "limit")]["level_limit"]), ("30", "55"))
        self.assertEqual(custom[(8001, "limit")]["items"][-1]["prob"], "10")

    def test_swap_everywhere(self):
        # the user's case: every Metin's skill book -> a chest of books
        form = {"mob": ["101", "102", "8001"], "op": "edit", "item": "27001", "to_item": "50011", "prob_mode": "mul",
                "factor": "0.5", "kinds": ["drop", "kill"]}
        page = self.post(**form)
        self.assertIn("Przedmiot 50011 – 0,5%", page)
        self.post(step="save", **form)
        custom = self.custom()
        self.assertEqual([(e["item"], e["prob"]) for e in custom[(101, "drop")]["items"]], [("50011", "2"), ("50011", "0.4")])
        self.assertEqual([e["item"] for e in custom[(8001, "drop")]["items"]], ["50011", "s50011"])
        self.assertNotIn((101, "kill"), custom)                              # no 27001 in that kill group

    def test_remove_and_empty(self):
        page = self.post(mob=["8001"], op="remove", item="27005", kinds=["limit"])
        self.assertIn("zostanie pustych", page)
        self.post(step="save", mob=["8001"], op="remove", item="27005", kinds=["limit"])
        custom = self.custom()
        self.assertEqual(custom[(8001, "limit")]["items"], [])               # "nothing of this kind"
        self.assertEqual(custom[(8001, "limit")]["replaces"], ["Limit"])
        effective = df.effective_mob_drops(df.parse_mob_drop(MOB_SAMPLE), custom)
        self.assertNotIn((8001, "limit"), effective)
        self.assertIn((8001, "drop"), effective)                              # the other kinds untouched

    def test_refused(self):
        self.assertIn("nie ma w item_proto", self.post(mob=["101"], op="add", item="999999", kind="drop", pct="1"))
        self.assertIn("nie ma szkatułki", self.post(mob=["101"], op="add", item="s777", kind="drop", pct="1"))
        self.assertIn("Zaznacz co najmniej", self.post(op="add", item="27001", kind="drop", pct="1"))
        self.client.post("/db/drops/masowo", data={"dbe_csrf": "zly", "step": "save", "mob": "101", "op": "remove",
                                                   "item": "27001", "token": ""})
        self.assertIsNone(df.read_text(df.custom_path(self.spool, "mob")))
        # a preview made before another save: refused
        old_token = df.file_sha(df.custom_path(self.spool, "mob"))
        self.post(step="save", mob=["102"], op="remove", item="50011")
        page = self.post(step="save", token=old_token, mob=["101"], op="remove", item="27001")
        self.assertIn("zmienił się od podglądu", page)
        self.assertNotIn((101, "drop"), self.custom())

    @unittest.skipUnless(shutil.which("sh") and M2_DROPS.is_file(), "game/bin/m2-drops not around")
    def test_game_takes_it(self):
        self.post(step="save", mob=["101", "8001"], op="add", item="50300", kind="drop", count="1", pct="1")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            locale = root / "share" / "locale" / "poland"
            locale.mkdir(parents=True)
            (locale / "mob_drop_item.txt").write_text(MOB_SAMPLE.replace("\n", "\r\n"), encoding="ascii")
            for name in ("common_drop_item.txt", "etc_drop_item.txt", "drop_item_group.txt"):
                (locale / name).write_text("", encoding="ascii")
            env = dict(os.environ, M2_SHARE_DIR=str(root / "share"), M2_VAR_DIR=str(root / "var"),
                       M2_RATES_SPOOL=str(self.spool), PATH="/usr/bin:/bin")
            for command in ("prepare", "apply"):
                subprocess.run(["sh", str(M2_DROPS), command], env=env, check=True, capture_output=True)
            live = df.parse_mob_drop((locale / "mob_drop_item.txt").read_text(encoding="ascii"))
            effective = df.effective_mob_drops(live, {})
            self.assertEqual([e["item"] for e in effective[(8001, "drop")]["items"]], ["27001", "s50011", "50300"])
            self.assertEqual([e["item"] for e in effective[(101, "drop")]["items"]], ["27001", "50011", "50300"])
            self.assertEqual(len(effective[(101, "kill")]["items"]), 2)        # untouched


if __name__ == "__main__":
    unittest.main()
