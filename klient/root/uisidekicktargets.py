# MT2009_PLUS_SIDEKICK_TARGETS_V1 [Autor: Vekirion] - "Zaawansowane": what the
# companion fights. The Orders page's "Zaawansowane" button (where "Dystans"
# was) opens it beside the companion's window.
#
#   Atakuje     Potwory / Metiny / Bossy - a button each, held down while the
#               companion fights that kind. A kind let up is never fought: not
#               the owner's target, not what strikes the owner or it, not looked
#               for (order: cele <sum of 1 monsters, 2 Metins, 4 bosses>).
#   Dystans     "Najpierw dystans": the archers and casters that hit the owner,
#               the companion or the party first (order: dystans N).
#   Najpierw    a part of a monster's name; the nearest monster of that name
#               goes before everything else (order: celnazwa <hex>, "-" none).
#
# What is set comes with the window's own answer (uisidekick.ParseInfo: kinds,
# target_name, ranged), which the companion's window asks for while it is open;
# this panel reads it from there and sends its orders through the same queue.
#
# Python 2.7 as the client has it; the Polish letters are CP1250 escapes.

import clientclock
import ui

import uisidekick

WIDTH = 236
HEIGHT = 238
NAME_MAX = 24
REFRESH_INTERVAL = 0.5
POLL_INTERVAL = 1.5

KIND_MOB = 1
KIND_STONE = 2
KIND_BOSS = 4
KIND_ALL = 7

COLOR_NORMAL = 0xffc2c2c2
COLOR_HINT = 0xffd8c9a0
COLOR_BAD = 0xffe57975

BUTTON_IMAGE = 'd:/ymir work/ui/public/%s_button_%02d.sub'
COLUMNS = (23, 94, 165)

TEXT_TITLE = 'Zaawansowane'
TEXT_KINDS = 'Atakuje (kliknij, \xbfeby w\xb3\xb9czy\xe6 / wy\xb3\xb9czy\xe6):'
TEXT_KIND_NAMES = ('Potwory', 'Metiny', 'Bossy')
TEXT_KIND_HINTS = ('zwyk\xb3e potwory', 'kamienie Metin', 'bossy')
TEXT_RANGED_STATES = ('Dystans: nie', 'Dystans: tak')
TEXT_RANGED = 'Najpierw \xb3ucznicy i magowie, kt\xf3rzy bij\xb9 ciebie, jego lub grup\xea:'
TEXT_NAME = 'Najpierw ten potw\xf3r (cz\xea\x9c\xe6 nazwy):'
TEXT_NAME_NOW = 'Teraz: %s'
TEXT_NAME_NONE = 'brak'
TEXT_SET = 'Ustaw'
TEXT_CLEAR = 'Wyczy\x9c\xe6'
TEXT_WAITING = 'Czekam na odpowied\x9f serwera...'
TEXT_OLD_SERVER = 'Zaktualizuj serwer, \xbfeby u\xbfywa\xe6 tego okna.'
TEXT_NO_COMPANION = 'Nie masz teraz towarzysza.'
TEXT_NONE_KIND = 'Nie atakuje niczego - w\xb3\xb9cz co\x9c powy\xbfej.'
TEXT_EMPTY_NAME = 'Wpisz nazw\xea potwora (albo jej cz\xea\x9c\xe6).'
TEXT_SENT = 'Wys\xb3ano - odpowied\x9f towarzysza na czacie.'


def _Hex(text):
	return ''.join('%02x' % ord(c) for c in text)


def _Info():
	window = uisidekick._window.get('window')
	if window is None:
		return None
	return getattr(window, 'info', None)


class TargetsWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.placed = False
		self.nextRefresh = 0.0
		self.nextPoll = 0.0
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetSize(WIDTH, HEIGHT)
		self._Build()

	# ------------------------------------------------------------ the widgets

	def _Label(self, x, y, text, color=COLOR_NORMAL, center=False):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetPackedFontColor(color)
		line.SetText(text)
		line.Show()
		self.widgets.append(line)
		return line

	def _Btn(self, size, x, y, text, event, *args):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual(BUTTON_IMAGE % (size, 1))
		button.SetOverVisual(BUTTON_IMAGE % (size, 2))
		button.SetDownVisual(BUTTON_IMAGE % (size, 3))
		button.SetText(text)
		button.SAFE_SetEvent(event, *args)
		button.Show()
		self.widgets.append(button)
		return button

	def _Build(self):
		self._Label(14, 36, TEXT_KINDS, COLOR_HINT)
		self.kindButtons = []
		for i, text in enumerate(TEXT_KIND_NAMES):
			self.kindButtons.append(self._Btn('middle', COLUMNS[i], 54, text, self.OnKind, 1 << i))
		self._Label(14, 84, TEXT_RANGED, COLOR_HINT)
		self.rangedButton = self._Btn('large', (WIDTH - 88) // 2, 102, TEXT_RANGED_STATES[1], self.OnRanged)
		self._Label(14, 132, TEXT_NAME, COLOR_HINT)
		bar = ui.Bar()
		bar.SetParent(self)
		bar.SetPosition(14, 150)
		bar.SetSize(WIDTH - 28, 18)
		bar.SetColor(0xC0000000)
		bar.Show()
		self.widgets.append(bar)
		self.nameEdit = ui.EditLine()
		self.nameEdit.SetParent(bar)
		self.nameEdit.SetPosition(4, 2)
		self.nameEdit.SetSize(WIDTH - 36, 14)
		self.nameEdit.SetMax(NAME_MAX)
		self.nameEdit.SetReturnEvent(ui.__mem_func__(self.OnSetName))
		self.nameEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.nameEdit.Show()
		self.widgets.append(self.nameEdit)
		self.setButton = self._Btn('middle', 47, 174, TEXT_SET, self.OnSetName)
		self.clearButton = self._Btn('middle', 128, 174, TEXT_CLEAR, self.OnClearName)
		self.nameNow = self._Label(WIDTH // 2, 198, '', COLOR_NORMAL, True)
		self.status = self._Label(WIDTH // 2, 214, TEXT_WAITING, COLOR_HINT, True)

	# ------------------------------------------------------------ the state

	def Refresh(self):
		info = _Info()
		if not info:
			self.status.SetPackedFontColor(COLOR_HINT)
			self.status.SetText(TEXT_WAITING)
			return
		if not info.get('has'):
			self.status.SetPackedFontColor(COLOR_HINT)
			self.status.SetText(TEXT_NO_COMPANION)
			return
		if 'kinds' not in info:
			self.status.SetPackedFontColor(COLOR_BAD)
			self.status.SetText(TEXT_OLD_SERVER)
			return
		kinds = info['kinds']
		for i, button in enumerate(self.kindButtons):
			if kinds & (1 << i):
				button.Down()
			else:
				button.SetUp()
		self.rangedButton.SetText(TEXT_RANGED_STATES[1 if info.get('ranged', 1) else 0])
		name = info.get('target_name', '')
		self.nameNow.SetText(TEXT_NAME_NOW % (name or TEXT_NAME_NONE))
		if kinds == 0:
			self.status.SetPackedFontColor(COLOR_BAD)
			self.status.SetText(TEXT_NONE_KIND)
		elif self.status.GetText() in (TEXT_WAITING, TEXT_NO_COMPANION, TEXT_OLD_SERVER, TEXT_NONE_KIND):
			self.status.SetText('')

	def _Send(self, text):
		uisidekick.SendCommand(text)
		window = uisidekick._window.get('window')
		if window is not None:
			# the companion's window asks again at once, so the buttons follow
			window.nextPoll = 0.0
		self.status.SetPackedFontColor(COLOR_HINT)
		self.status.SetText(TEXT_SENT)

	def OnKind(self, bit):
		info = _Info() or {}
		kinds = info.get('kinds', KIND_ALL)
		self._Send('cele %d' % ((kinds ^ bit) & KIND_ALL))

	def OnRanged(self):
		info = _Info() or {}
		on = info.get('ranged', 1)
		self._Send('dystans %d' % (0 if on else 1))

	def OnSetName(self):
		text = self.nameEdit.GetText().strip()
		if not text:
			self.status.SetPackedFontColor(COLOR_BAD)
			self.status.SetText(TEXT_EMPTY_NAME)
			return
		self._Send('celnazwa ' + _Hex(text[:NAME_MAX]))
		self.nameEdit.SetText('')
		self.nameEdit.KillFocus()

	def OnClearName(self):
		self._Send('celnazwa -')
		self.nameEdit.SetText('')
		self.nameEdit.KillFocus()

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
		self.nextRefresh = 0.0
		self.Refresh()

	def Close(self):
		try:
			self.nameEdit.KillFocus()
		except Exception:
			pass
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		uisidekick.PumpCommands()
		now = clientclock.Now()
		# With the companion's window closed nobody asks for its answer: this panel does.
		window = uisidekick._window.get('window')
		if (window is None or not window.IsShow()) and now >= self.nextPoll and uisidekick.TryPoll('okno'):
			self.nextPoll = now + POLL_INTERVAL
		if now >= self.nextRefresh:
			self.nextRefresh = now + REFRESH_INTERVAL
			self.Refresh()

	def Destroy(self):
		try:
			self.nameEdit.KillFocus()
		except Exception:
			pass
		self.Hide()
		self.widgets = []


_state = {'window': None}


def GetWindow():
	if _state['window'] is None:
		_state['window'] = TargetsWindow()
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


def Destroy():
	window = _state['window']
	if window is not None:
		window.Destroy()
	_state['window'] = None
