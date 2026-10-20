# MT2009_PLUS_SIDEKICK_ROSTER_V1 - "Druzyna towarzyszy": the player's
# companions, the ones in the game and the ones resting on the bench (the
# owner, 19 October: "oddelegowac towarzysza na przerwe ... i zastapic ja
# inna", "uzywania paru towarzyszy na raz"). Alt+P (keybind.py
# "companion_roster"), the letter's "Druzyna i lawka" and "Druzyna" on the
# Orders page of the companion's window open it.
#
# A row a companion: its face, name, class and level, where it is, and
#   Wybierz   - the companion the window (P), the bag (Shift+P), the effects
#               (Ctrl+P) and every order without a name go to,
#   Na lawke  - out of the game, its gear, level and settings kept,
#   Do gry    - back into the game while there is room,
#   Zamien    - back into the game in place of the chosen one in it.
#
# The server (playerbot_sidekick.h, SendPlayerBotSidekickRoster) answers
# "/towarzysz lista" and every change of the roster with
#
#   SidekickRosterBegin <protocol> <max active> <max roster> <chosen pid> <count>
#   SidekickRoster <pid> <name hex> <race> <group> <level> <active> <where> <mode>
#   SidekickRosterEnd <count>
#
# where: 0 out of the game, 1 beside the owner's map, 2 in the game elsewhere.
#
# Python 2.7 as the client has it; the Polish letters are CP1250 escapes.

import clientclock
import ui

import uisidekick

PROTOCOL = 1
POLL_INTERVAL = 3.0

WIDTH = 320
ROW_TOP = 56
ROW_HEIGHT = 46
ROW_X = 12
ROW_WIDTH = WIDTH - 24
FACE_SCALE = 0.75
BOTTOM = 52

COLOR_NORMAL = 0xffc2c2c2
COLOR_HINT = 0xffd8c9a0
COLOR_ACTIVE = 0xff8ad07a
COLOR_BENCH = 0xff9a9a9a
COLOR_BAD = 0xffe57975
ROW_COLORS = (0x18ffffff, 0x30000000)
ROW_CHOSEN = 0x40c8a050

BUTTON_IMAGE = 'd:/ymir work/ui/public/%s_button_%02d.sub'

TEXT_TITLE = 'Dru\xbfyna towarzyszy'
TEXT_COUNTS = 'W grze: %d/%d     Dru\xbfyna: %d/%d'
TEXT_WAITING = 'Czekam na odpowied\x9f serwera...'
TEXT_EMPTY = 'Nie masz jeszcze towarzysza.'
TEXT_HINT_NEW = 'Nowego stworzysz w li\x9ccie "Towarzysz".'
TEXT_OLD_SERVER = 'Zaktualizuj serwer, \xbfeby mie\xe6 dru\xbfyn\xea.'
TEXT_LEVEL = 'Poz. %d  %s'
TEXT_CHOOSE = 'Wybierz'
TEXT_CHOSEN = 'Wybrany'
TEXT_BENCH = 'Na \xb3awk\xea'
TEXT_ACTIVATE = 'Do gry'
TEXT_SWAP = 'Zamie\xf1'
TEXT_WHERE = {
	0: 'w grze, \xb3aduje si\xea',
	1: 'w grze, przy tobie',
	2: 'w grze, gdzie indziej',
}
TEXT_MODE = {
	1: 'w grze, wolna r\xeaka',
	2: 'w grze, czeka w miejscu',
	3: 'w grze, na zakupach',
}
TEXT_ON_BENCH = 'odpoczywa na \xb3awce'
TEXT_SWAP_HINT = 'Wchodzi do gry za: %s'
TEXT_SWAP_NONE = 'Najpierw wybierz towarzysza w grze, kt\xf3rego ma zast\xb9pi\xe6.'


def ParseInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


class RosterWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.rowWidgets = []
		self.placed = False
		self.nextPoll = 0.0
		self.pending = None
		self.answer = None
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.countsLine = self._Label(self, WIDTH // 2, 34, TEXT_WAITING)
		self.countsLine.SetHorizontalAlignCenter()
		self.countsLine.SetPackedFontColor(COLOR_HINT)
		self.hintLine = self._Label(self, WIDTH // 2, 0, TEXT_HINT_NEW)
		self.hintLine.SetHorizontalAlignCenter()
		self.statusLine = self._Label(self, WIDTH // 2, 0, '')
		self.statusLine.SetHorizontalAlignCenter()
		self._Resize(1)

	# ------------------------------------------------------------ widgets

	def _Label(self, parent, x, y, text, store=None):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		line.SetText(text)
		line.Show()
		(self.widgets if store is None else store).append(line)
		return line

	def _Btn(self, parent, size, x, y, text, event, *args):
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetUpVisual(BUTTON_IMAGE % (size, 1))
		button.SetOverVisual(BUTTON_IMAGE % (size, 2))
		button.SetDownVisual(BUTTON_IMAGE % (size, 3))
		button.SetText(text)
		button.SAFE_SetEvent(event, *args)
		button.Show()
		self.rowWidgets.append(button)
		return button

	def _Resize(self, rows):
		rows = max(1, rows)
		height = ROW_TOP + rows * ROW_HEIGHT + BOTTOM
		self.SetSize(WIDTH, height)
		self.hintLine.SetPosition(WIDTH // 2, height - BOTTOM + 8)
		self.statusLine.SetPosition(WIDTH // 2, height - BOTTOM + 24)

	def SetStatus(self, text, color=COLOR_NORMAL):
		self.statusLine.SetPackedFontColor(color)
		self.statusLine.SetText(text)

	def _ClearRows(self):
		for widget in self.rowWidgets:
			try:
				widget.Hide()
			except Exception:
				pass
		self.rowWidgets = []

	# ------------------------------------------------------------ the server

	def OnOldServer(self):
		self.countsLine.SetText(TEXT_OLD_SERVER)

	def SetAnswer(self, answer):
		# The same roster again (the poll): the rows stay as they are, so a
		# click on them is not lost to their rebuilding.
		if self.answer is not None and self.answer == answer:
			return
		self.answer = answer
		self.Refresh()

	# ------------------------------------------------------------ the rows

	def _ChosenActive(self):
		answer = self.answer
		if answer is None:
			return None
		for row in answer['rows']:
			if row['pid'] == answer['chosen'] and row['active']:
				return row
		return None

	def Refresh(self):
		self._ClearRows()
		answer = self.answer
		if answer is None:
			return
		rows = answer['rows']
		active = len([row for row in rows if row['active']])
		self.countsLine.SetText(TEXT_COUNTS % (active, answer['maxActive'], len(rows), answer['maxRoster']))
		if not rows:
			self._Resize(1)
			self.SetStatus(TEXT_EMPTY, COLOR_HINT)
			return
		roomInGame = active < answer['maxActive']
		chosenActive = self._ChosenActive()
		for index, row in enumerate(rows):
			y = ROW_TOP + index * ROW_HEIGHT
			bar = ui.Bar()
			bar.SetParent(self)
			bar.SetPosition(ROW_X, y)
			bar.SetSize(ROW_WIDTH, ROW_HEIGHT - 2)
			bar.SetColor(ROW_CHOSEN if row['pid'] == answer['chosen'] else ROW_COLORS[index % 2])
			bar.AddFlag('not_pick')
			bar.Show()
			self.rowWidgets.append(bar)
			face = uisidekick.FaceImage(row['race'])
			if face:
				image = ui.ExpandedImageBox()
				image.SetParent(self)
				image.SetPosition(ROW_X + 4, y + 3)
				try:
					image.LoadImage(face)
					image.SetScale(FACE_SCALE, FACE_SCALE)
				except Exception:
					pass
				image.AddFlag('not_pick')
				image.Show()
				self.rowWidgets.append(image)
			name = self._Label(self, ROW_X + 46, y + 4, row['name'] or '-', self.rowWidgets)
			name.SetPackedFontColor(COLOR_HINT)
			self._Label(self, ROW_X + 46, y + 17,
				TEXT_LEVEL % (row['level'], uisidekick.ClassText(row['race'], row['group'])), self.rowWidgets)
			if row['active']:
				state = TEXT_MODE.get(row['mode'], TEXT_WHERE.get(row['where'], TEXT_WHERE[0]))
				if row['mode'] == 0:
					state = TEXT_WHERE.get(row['where'], TEXT_WHERE[0])
				color = COLOR_ACTIVE
			else:
				state = TEXT_ON_BENCH
				color = COLOR_BENCH
			stateLine = self._Label(self, ROW_X + 46, y + 30, state, self.rowWidgets)
			stateLine.SetPackedFontColor(color)
			# The buttons: "Wybierz" at the right, the bench's one before it.
			right = ROW_X + ROW_WIDTH - 4
			chooseButton = self._Btn(self, 'small', right - 43, y + 4,
				TEXT_CHOSEN if row['pid'] == answer['chosen'] else TEXT_CHOOSE, self.OnChoose, row['pid'])
			if row['pid'] == answer['chosen']:
				chooseButton.Disable()
			if row['active']:
				self._Btn(self, 'middle', right - 43 - 4 - 61, y + 4, TEXT_BENCH, self.OnBench, row['pid'])
			elif roomInGame:
				self._Btn(self, 'middle', right - 43 - 4 - 61, y + 4, TEXT_ACTIVATE, self.OnActivate, row['pid'])
			else:
				swap = self._Btn(self, 'middle', right - 43 - 4 - 61, y + 4, TEXT_SWAP, self.OnSwap, row['pid'])
				hint = (TEXT_SWAP_HINT % chosenActive['name']) if chosenActive else TEXT_SWAP_NONE
				swap.ShowToolTip = _Call(self.SetStatus, hint, COLOR_HINT)
				swap.HideToolTip = _Call(self.SetStatus, '')
		self._Resize(len(rows))

	# ------------------------------------------------------------ orders

	def OnChoose(self, pid):
		uisidekick.SendCommand('wybierz %d' % pid)

	def OnBench(self, pid):
		uisidekick.SendCommand('lawka %d' % pid)

	def OnActivate(self, pid):
		uisidekick.SendCommand('aktywuj %d' % pid)

	def OnSwap(self, pid):
		chosen = self._ChosenActive()
		if chosen is None:
			self.SetStatus(TEXT_SWAP_NONE, COLOR_BAD)
			return
		uisidekick.SendCommand('zamien %d %d' % (pid, chosen['pid']))

	# ------------------------------------------------------------ the frame

	def Open(self, anchor=None):
		# MT2009_PLUS_SIDEKICK_TABS_V1: what the roster last said, at once.
		if _state['answer'] is not None:
			self.SetAnswer(_state['answer'])
		if not self.placed:
			self.placed = True
			placedBeside = False
			if anchor is not None:
				try:
					import wndMgr
					(x, y) = anchor.GetGlobalPosition()
					left = x - WIDTH - 4
					if left >= 0:
						self.SetPosition(left, y)
						placedBeside = True
				except Exception:
					pass
			if not placedBeside:
				self.SetCenterPosition()
		self.Show()
		self.SetTop()
		self.nextPoll = 0.0

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		uisidekick.PumpCommands()
		now = clientclock.Now()
		if now >= self.nextPoll and uisidekick.TryPoll('lista'):
			self.nextPoll = now + POLL_INTERVAL

	def Destroy(self):
		self._ClearRows()
		self.Hide()
		# A board, not a script window: it has no dictionary of children to
		# clear (ClearDictionary is ScriptWindow's) - its widgets go with the
		# lists below.
		self.widgets = []


class _Call(object):
	def __init__(self, func, *args):
		self.func = func
		self.args = args

	def __call__(self, *ignored):
		self.func(*self.args)


# MT2009_PLUS_SIDEKICK_TABS_V1: the roster is the module's, not the window's:
# the companion's window (uisidekick.py) shows its tabs from it too.
_state = {'window': None, 'pending': None, 'answer': None}


def GetAnswer():
	return _state['answer']


def GetWindow():
	if _state['window'] is None:
		_state['window'] = RosterWindow()
	return _state['window']


def ToggleWindow(anchor=None):
	window = GetWindow()
	if window.IsShow():
		window.Close()
	else:
		window.Open(anchor)


def OpenWindow(anchor=None):
	window = GetWindow()
	if not window.IsShow():
		window.Open(anchor)


def SelectNext():
	"""The next companion in the game becomes the chosen one (keybind.py
	"companion_next"); the server says so in the windows."""
	uisidekick.SendCommand('wybierz nastepny')


def OnBegin(*args):
	if len(args) < 5 or ParseInt(args[0], -1) != PROTOCOL:
		_state['pending'] = None
		window = _state['window']
		if window is not None:
			window.OnOldServer()
		return
	_state['pending'] = {
		'maxActive': ParseInt(args[1], 1),
		'maxRoster': ParseInt(args[2], 1),
		'chosen': ParseInt(args[3]),
		'rows': [],
	}


def OnRow(*args):
	pending = _state['pending']
	if pending is None or len(args) < 8:
		return
	pending['rows'].append({
		'pid': ParseInt(args[0]),
		'name': uisidekick.DecodeText(args[1]),
		'race': ParseInt(args[2], -1),
		'group': ParseInt(args[3]),
		'level': ParseInt(args[4], 1),
		'active': ParseInt(args[5]) != 0,
		'where': ParseInt(args[6]),
		'mode': ParseInt(args[7]),
	})


def OnEnd(*args):
	answer = _state['pending']
	_state['pending'] = None
	if answer is None:
		return
	_state['answer'] = answer
	window = _state['window']
	if window is not None:
		window.SetAnswer(answer)
	uisidekick.OnRoster(answer)	# MT2009_PLUS_SIDEKICK_TABS_V1: the tabs


def Destroy():
	window = _state['window']
	if window is not None:
		window.Destroy()
	_state['window'] = None
	_state['pending'] = None
	_state['answer'] = None


class Keeper(object):
	"""One of the game's updateables: the window goes with the game window."""

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
