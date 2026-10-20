# MT2009_PLUS_DPS_METER_V1 (the owner, 18 October: "a DPS counter in the client - the
# character's DPS / the damage dealt in a time"). The damage numbers over the monsters
# are the exe's own and Python never sees them, so the server sums up what the
# character and its companion dealt and sends it once a second while anything hits:
# "DpsTick <character> <companion>" (char_battle.cpp, MT2009_PLUS_DPS_METER_V1;
# game.py registers the command). This window shows, while "Licznik DPS" is ticked
# in Opcje Gry -> Dodatkowe (uiopcjedodatkowe.py, key "dpsmeter"):
#   DPS (5 s)     - the damage of the last five seconds / 5
#   DPS walki     - the fight's damage / its length
#   Obrazenia     - the fight's damage, and below: character | companion
#   Czas walki    - from its first hit to its last
# A fight ends FIGHT_GAP seconds after its last hit; the window keeps showing it
# ("zakonczona") until the next hit starts a new one, or "Reset".
# The window moves with the mouse; its place is kept in dpsmeter.cfg.
#
# Python 2.7 as the client has it.

import ui
import wndMgr
import grp

CONFIG_FILE = "dpsmeter.cfg"
FIGHT_GAP = 6.0
RECENT = 5.0
REFRESH = 0.25

WIDTH = 196
HEIGHT = 104

COLOR_TITLE = grp.GenerateColor(1.0, 0.85, 0.45, 1.0)
COLOR_TEXT = grp.GenerateColor(0.9, 0.9, 0.9, 1.0)
COLOR_DIM = grp.GenerateColor(0.6, 0.6, 0.6, 1.0)

_state = {"window": None, "enabled": None}


def _Now():
	import clientclock
	return clientclock.Now()


def _Open(name, mode):
	try:
		return old_open(name, mode)  # the real file open (system.py); open() reads packs
	except NameError:
		return open(name, mode)


def _Number(n):
	n = int(n)
	if n <= 0:
		return "0"
	s = str(n)
	parts = []
	while len(s) > 3:
		parts.insert(0, s[-3:])
		s = s[:-3]
	parts.insert(0, s)
	return " ".join(parts)


def _LoadPosition():
	try:
		f = _Open(CONFIG_FILE, "r")
		try:
			x, y = [int(v) for v in f.read().split()[:2]]
		finally:
			f.close()
		x = max(0, min(x, wndMgr.GetScreenWidth() - WIDTH))
		y = max(0, min(y, wndMgr.GetScreenHeight() - HEIGHT))
		return x, y
	except Exception:
		return 10, wndMgr.GetScreenHeight() / 2 - HEIGHT / 2


def _SavePosition(window):
	try:
		x, y = window.GetGlobalPosition()
		f = _Open(CONFIG_FILE, "w")
		try:
			f.write("%d %d" % (x, y))
		finally:
			f.close()
	except Exception:
		pass


def Enabled():
	if _state["enabled"] is None:
		try:
			import uiopcjedodatkowe
			_state["enabled"] = bool(uiopcjedodatkowe.Settings().get("dpsmeter", False))
		except Exception:
			_state["enabled"] = False
	return _state["enabled"]


class DpsMeterWindow(ui.ThinBoard):
	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(WIDTH, HEIGHT)
		self.lines = []
		for i in xrange(5):
			line = ui.TextLine()
			line.SetParent(self)
			line.SetPosition(10, 8 + i * 17)
			line.SetPackedFontColor(COLOR_TITLE if i == 0 else COLOR_TEXT)
			line.Show()
			self.lines.append(line)
		self.resetButton = ui.Button()
		self.resetButton.SetParent(self)
		self.resetButton.SetPosition(WIDTH - 54, 6)
		self.resetButton.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
		self.resetButton.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
		self.resetButton.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
		self.resetButton.SetText("Reset")
		self.resetButton.SetEvent(ui.__mem_func__(self.Reset))
		self.resetButton.Show()
		self.nextRefresh = 0.0
		self.Reset()
		(x, y) = _LoadPosition()
		self.SetPosition(x, y)

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def Destroy(self):
		_SavePosition(self)
		self.resetButton = None
		self.lines = []
		self.Hide()

	def Reset(self):
		self.samples = []	# (time, character, companion) - one a second while hits come
		self.fightStart = 0.0
		self.lastHit = 0.0
		self.totalSelf = 0
		self.totalSidekick = 0
		self.Refresh()

	def OnTick(self, dmgSelf, dmgSidekick):
		now = _Now()
		if not self.lastHit or now - self.lastHit > FIGHT_GAP:
			self.Reset()
			self.fightStart = now - 1.0	# the tick sums up the second before it
		self.lastHit = now
		self.totalSelf += dmgSelf
		self.totalSidekick += dmgSidekick
		self.samples.append((now, dmgSelf, dmgSidekick))
		self.samples = [s for s in self.samples if now - s[0] <= RECENT + 1.0]
		self.Refresh()

	def Refresh(self):
		now = _Now()
		fighting = self.lastHit and now - self.lastHit <= FIGHT_GAP
		total = self.totalSelf + self.totalSidekick
		length = max(1.0, (self.lastHit - self.fightStart)) if self.lastHit else 0.0
		recentWindow = RECENT
		if self.lastHit and length < RECENT:
			recentWindow = length
		recent = 0
		if fighting:
			recent = sum([s[1] + s[2] for s in self.samples if now - s[0] <= RECENT])
		self.lines[0].SetText("Licznik DPS")
		if self.lastHit and not fighting:
			self.lines[1].SetText("Walka zako\xf1czona")
		else:
			self.lines[1].SetText("DPS (5 s): %s" % _Number(recent / max(1.0, recentWindow)))
		self.lines[2].SetText("DPS walki: %s" % _Number(total / length if length else 0))
		self.lines[3].SetText("Obra\xbfenia: %s   Czas: %d s" % (_Number(total), int(length)))
		self.lines[4].SetText("Posta\xe6: %s | Towarzysz: %s" % (_Number(self.totalSelf), _Number(self.totalSidekick)))
		self.lines[4].SetPackedFontColor(COLOR_DIM)

	def OnUpdate(self):
		now = _Now()
		if now >= self.nextRefresh:
			self.nextRefresh = now + REFRESH
			self.Refresh()


def _Window():
	window = _state["window"]
	if window is None:
		window = DpsMeterWindow()
		_state["window"] = window
	return window


def Start():
	"""The game window opened (game.py): the window shows when the option is on."""
	if Enabled():
		_Window().Show()


def SetEnabled(on):
	"""Opcje Gry -> Dodatkowe -> Licznik DPS (uiopcjedodatkowe.Set)."""
	_state["enabled"] = bool(on)
	if on:
		window = _Window()
		window.Reset()
		window.Show()
	elif _state["window"] is not None:
		_SavePosition(_state["window"])
		_state["window"].Hide()


def OnTick(dmgSelf="0", dmgSidekick="0", *rest):
	"""The server's "DpsTick <character> <companion>" (game.py)."""
	if not Enabled():
		return
	try:
		dmgSelf = max(0, int(dmgSelf))
		dmgSidekick = max(0, int(dmgSidekick))
	except ValueError:
		return
	window = _Window()
	if not window.IsShow():
		window.Show()
	window.OnTick(dmgSelf, dmgSidekick)


def Destroy():
	"""The game window closes (a warp, a channel change, the logout)."""
	window = _state["window"]
	_state["window"] = None
	if window is not None:
		window.Destroy()
