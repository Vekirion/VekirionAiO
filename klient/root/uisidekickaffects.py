# MT2009_PLUS_SIDEKICK_AFFECTS_V1 - "Efekty towarzysza": what is on the
# companion - its buffs, potions and debuffs - with the pictures, tooltips and
# time left of the player's own affect bar (uiaffectbar.py). Shift+P is the
# bag, Ctrl+P this panel (keybind.py "companion_effects"); the Orders page of
# the companion's window opens it too ("Efekty" on the "Co robi" bar).
#
# The server answers "/towarzysz efekty" (playerbot_sidekick.h,
# SendPlayerBotSidekickAffects), asked every POLL_INTERVAL while the panel is
# shown, through uisidekick's one queue:
#
#   SidekickAffBegin <protocol> <state> <name hex> <hp> <maxhp> <sp> <maxsp> <dead>
#   SidekickAff <type> <apply> <value> <seconds left> <flag> <item vnum>
#   SidekickAffEnd <lines>
#
# state: 0 no companion, 1 in the world, 2 companions switched off, 3 not in
# the world just now. An affect the player's bar has no picture for is not
# shown here either.
#
# Python 2.7 as the client has it; the Polish letters are CP1250 escapes.

import app
import chr
import clientclock
import skill
import ui

import uisidekick

PROTOCOL = 1
POLL_INTERVAL = 2.0

WIDTH = 236
ICON_STEP = 28
ICONS_PER_ROW = 8
ICONS_TOP = 78
MIN_ROWS = 1
MAX_ROWS = 4
GAUGE_X = 14
GAUGE_WIDTH = WIDTH - 28
GAUGE_HEIGHT = 9

STATE_NONE = 0
STATE_OK = 1
STATE_OFF = 2
STATE_AWAY = 3

COLOR_NORMAL = 0xffc2c2c2
COLOR_HINT = 0xffd8c9a0
COLOR_BAD = 0xffe57975
COLOR_GAUGE_BACK = 0xff2a2622
COLOR_HP = 0xffc23a2e
COLOR_SP = 0xff3a62c2

TEXT_TITLE = 'Efekty towarzysza'
TEXT_WAITING = 'Czekam na odpowied\x9f serwera...'
TEXT_STATE = {
	STATE_NONE: 'Nie masz jeszcze towarzysza.',
	STATE_OFF: 'Towarzysze s\xb9 wy\xb3\xb9czeni na tym serwerze.',
	STATE_AWAY: 'Towarzysza nie ma teraz przy tobie.',
}
TEXT_NO_AFFECTS = 'Brak aktywnych efekt\xf3w.'
TEXT_DEAD = ' (le\xbfy)'
TEXT_HP = 'P\xaf %d / %d'
TEXT_SP = 'PE %d / %d'
TEXT_OLD_SERVER = 'Zaktualizuj serwer, \xbfeby widzie\xe6 efekty.'


def ParseInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def ViewType(affectType, flag):
	"""uiaffectbar's own picture choice: a skill's affect with a debuff's flag
	is that debuff (AffectShower.__ConvertSkillAffectBasedOnFlag)."""
	if affectType > 111:
		return affectType
	pairs = (
		('AFF_SLOW', 'AFFECT_SLOW'),
		('AFF_STUN', 'AFFECT_STUN'),
		('AFF_ROOT', 'AFFECT_ROOT'),
		('AFF_FIRE', 'AFFECT_FIRE'),
		('AFF_POISON', 'AFFECT_POISON'),
	)
	for flagName, affectName in pairs:
		if hasattr(chr, flagName) and hasattr(chr, affectName) and flag == getattr(chr, flagName):
			return getattr(chr, affectName)
	if hasattr(chr, 'AFF_SKILL_DISPEL') and hasattr(skill, 'SKILL_DISPEL') and flag == chr.AFF_SKILL_DISPEL:
		return skill.SKILL_DISPEL
	return affectType


class _Gauge(object):
	"""A bar of the companion's HP or SP with its numbers on it."""

	def __init__(self, parent, y, color, widgets):
		self.back = ui.Bar()
		self.back.SetParent(parent)
		self.back.SetPosition(GAUGE_X, y)
		self.back.SetSize(GAUGE_WIDTH, GAUGE_HEIGHT)
		self.back.SetColor(COLOR_GAUGE_BACK)
		self.back.AddFlag('not_pick')
		self.back.Show()
		self.fill = ui.Bar()
		self.fill.SetParent(self.back)
		self.fill.SetPosition(0, 0)
		self.fill.SetSize(0, GAUGE_HEIGHT)
		self.fill.SetColor(color)
		self.fill.AddFlag('not_pick')
		self.fill.Show()
		self.text = ui.TextLine()
		self.text.SetParent(parent)
		self.text.SetPosition(WIDTH // 2, y - 2)
		self.text.SetHorizontalAlignCenter()
		self.text.SetOutline()
		self.text.Show()
		widgets.extend((self.back, self.fill, self.text))

	def Set(self, value, maximum, fmt):
		maximum = max(0, maximum)
		value = max(0, min(value, maximum))
		width = int(GAUGE_WIDTH * value / maximum) if maximum > 0 else 0
		self.fill.SetSize(width, GAUGE_HEIGHT)
		self.text.SetText(fmt % (value, maximum) if maximum > 0 else '')


class AffectsWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.images = {}
		self.signature = None
		self.placed = False
		self.nextPoll = 0.0
		self.state = None
		self.pending = None
		self.toolTip = None
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self._Build()
		self._Resize(MIN_ROWS)

	def _Build(self):
		self.nameLine = ui.TextLine()
		self.nameLine.SetParent(self)
		self.nameLine.SetPosition(WIDTH // 2, 34)
		self.nameLine.SetHorizontalAlignCenter()
		self.nameLine.SetPackedFontColor(COLOR_HINT)
		self.nameLine.Show()
		self.widgets.append(self.nameLine)
		self.hpGauge = _Gauge(self, 52, COLOR_HP, self.widgets)
		self.spGauge = _Gauge(self, 64, COLOR_SP, self.widgets)
		self.iconArea = ui.Window()
		self.iconArea.SetParent(self)
		self.iconArea.SetPosition(GAUGE_X, ICONS_TOP)
		self.iconArea.SetSize(ICON_STEP * ICONS_PER_ROW, ICON_STEP * MAX_ROWS)
		self.iconArea.Show()
		self.widgets.append(self.iconArea)
		self.statusLine = ui.TextLine()
		self.statusLine.SetParent(self)
		self.statusLine.SetPosition(WIDTH // 2, ICONS_TOP + 6)
		self.statusLine.SetHorizontalAlignCenter()
		self.statusLine.Show()
		self.widgets.append(self.statusLine)
		self.SetStatus(TEXT_WAITING)

	def _ToolTip(self):
		if self.toolTip is None:
			import uiToolTip
			self.toolTip = uiToolTip.ToolTip(130)
		return self.toolTip

	def _Resize(self, rows):
		rows = max(MIN_ROWS, min(MAX_ROWS, rows))
		self.SetSize(WIDTH, ICONS_TOP + rows * ICON_STEP + 14)

	def SetStatus(self, text, color=COLOR_NORMAL):
		self.statusLine.SetPackedFontColor(color)
		self.statusLine.SetText(text)
		if text:
			self.statusLine.Show()
		else:
			self.statusLine.Hide()

	# ------------------------------------------------------------ the server

	def OnBegin(self, args):
		if len(args) < 8 or ParseInt(args[0], -1) != PROTOCOL:
			self.pending = None
			self.state = None
			self._Clear()
			self.SetStatus(TEXT_OLD_SERVER, COLOR_BAD)
			return
		self.pending = {
			'state': ParseInt(args[1]),
			'name': uisidekick.DecodeText(args[2]),
			'hp': ParseInt(args[3]), 'maxhp': ParseInt(args[4]),
			'sp': ParseInt(args[5]), 'maxsp': ParseInt(args[6]),
			'dead': ParseInt(args[7]) != 0,
			'affects': [],
		}

	def OnAffect(self, args):
		if self.pending is None or len(args) < 6:
			return
		self.pending['affects'].append(tuple(ParseInt(value) for value in args[:6]))

	def OnEnd(self, args):
		answer = self.pending
		self.pending = None
		if answer is None:
			return
		self.state = answer['state']
		if self.state != STATE_OK:
			self._Clear()
			self.nameLine.SetText('')
			self.hpGauge.Set(0, 0, TEXT_HP)
			self.spGauge.Set(0, 0, TEXT_SP)
			self.SetStatus(TEXT_STATE.get(self.state, TEXT_STATE[STATE_AWAY]), COLOR_HINT)
			return
		self.nameLine.SetText(answer['name'] + (TEXT_DEAD if answer['dead'] else ''))
		self.hpGauge.Set(answer['hp'], answer['maxhp'], TEXT_HP)
		self.spGauge.Set(answer['sp'], answer['maxsp'], TEXT_SP)
		self._ShowAffects(answer['affects'])

	# ------------------------------------------------------------ the icons

	def _Clear(self):
		for image in self.images.values():
			try:
				image.HideToolTip()
			except Exception:
				pass
			image.Hide()
		self.images = {}
		self.signature = None

	def _ShowAffects(self, affects):
		import uiaffectbar
		groups = []	# [(key, affectType, viewType, [(point, value)], seconds, itemVnum)]
		byKey = {}
		for affectType, point, value, seconds, flag, itemVnum in affects:
			viewType = ViewType(affectType, flag)
			data = uiaffectbar.GetAffectData(viewType, point)
			if data is None or not data.has_key('icon'):
				continue
			# One picture for an affect of several points, as the player's bar
			# shows it, when its entry has a description of its own.
			merged = uiaffectbar.AFFECT_SHOW_DATA.get(viewType, {}).has_key('description')
			key = (affectType, viewType) if merged else (affectType, viewType, point)
			if byKey.has_key(key):
				group = byKey[key]
				group[3].append((point, value))
				group[4] = max(group[4], seconds)
				continue
			group = [key, affectType, viewType, [(point, value)], seconds, itemVnum]
			byKey[key] = group
			groups.append(group)
		signature = tuple((group[0], tuple(group[3])) for group in groups)
		if signature != self.signature:
			self._Clear()
			self.signature = signature
			for index, (key, affectType, viewType, points, seconds, itemVnum) in enumerate(groups):
				try:
					image = uiaffectbar.AffectImage(affectType, viewType, points[0][0], points[0][1], seconds)
				except Exception:
					continue
				for point, value in points[1:]:
					image.AddPoint(point, value)
				image.SetParent(self.iconArea)
				image.SetPosition((index % ICONS_PER_ROW) * ICON_STEP, (index // ICONS_PER_ROW) * ICON_STEP)
				image.tooltip = self._ToolTip()
				image.itemVnum = itemVnum
				image.Show()
				self.images[key] = image
			rows = (len(self.images) + ICONS_PER_ROW - 1) // ICONS_PER_ROW
			self._Resize(rows)
		else:
			# The same affects: their time again, from the server's clock.
			now = int(app.GetGlobalTimeStamp())
			for key, affectType, viewType, points, seconds, itemVnum in groups:
				image = self.images.get(key)
				if image is not None:
					image.createTime = now
					image.SetDuration(seconds)
		self.SetStatus('' if self.images else TEXT_NO_AFFECTS)

	# ------------------------------------------------------------ the frame

	def Open(self, anchor=None):
		if not self.placed:
			self.placed = True
			placedBeside = False
			if anchor is not None:
				try:
					import wndMgr
					(x, y) = anchor.GetGlobalPosition()
					right = x + anchor.GetWidth() + 4
					if right + WIDTH <= wndMgr.GetScreenWidth():
						self.SetPosition(right, y)
						placedBeside = True
				except Exception:
					pass
			if not placedBeside:
				self.SetCenterPosition()
		self.Show()
		self.SetTop()
		self.nextPoll = 0.0

	def Close(self):
		if self.toolTip is not None:
			self.toolTip.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		uisidekick.PumpCommands()
		now = clientclock.Now()
		if now >= self.nextPoll and uisidekick.TryPoll('efekty'):
			self.nextPoll = now + POLL_INTERVAL
		for image in self.images.values():
			try:
				image.OnFixedUpdate()
			except Exception:
				pass

	def Destroy(self):
		self._Clear()
		if self.toolTip is not None:
			self.toolTip.HideToolTip()
		self.toolTip = None
		self.Hide()
		# A board, not a script window: it has no dictionary of children to
		# clear (ClearDictionary is ScriptWindow's) - its widgets go with the
		# lists below.
		self.widgets = []


_state = {'window': None}


def GetWindow():
	if _state['window'] is None:
		_state['window'] = AffectsWindow()
	return _state['window']


def ToggleWindow(anchor=None):
	window = GetWindow()
	if window.IsShow():
		window.Close()
	else:
		window.Open(anchor)


def IsShown():
	window = _state['window']
	return window is not None and window.IsShow()


def OnBegin(*args):
	GetWindow().OnBegin(args)


def OnAffect(*args):
	window = _state['window']
	if window is not None:
		window.OnAffect(args)


def OnEnd(*args):
	window = _state['window']
	if window is not None:
		window.OnEnd(args)


def Destroy():
	window = _state['window']
	if window is not None:
		window.Destroy()
	_state['window'] = None


class Keeper(object):
	"""One of the game's updateables: the panel goes with the game window."""

	def CanUpdate(self):
		return False

	def OnUpdate(self):
		pass

	def Destroy(self):
		# The game window's DestroyUpdateables runs this at every warp and
		# channel change; an error here would stop its Close and close the
		# client, so it is written to syserr.txt and goes no further.
		try:
			Destroy()
		except Exception:
			try:
				import dbg
				import traceback
				dbg.TraceError('%s.Keeper.Destroy: %s' % (__name__, traceback.format_exc()))
			except Exception:
				pass


def GetKeeper():
	return Keeper()
