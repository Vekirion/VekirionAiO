# Walking through one's own companion (26 September:
# "towarzysz jest dla naszej postaci nieblokujacym, zeby dalo sie przez niego
# przenikac, bo jak expi sie z nim to on strasznie przeszkadza").
#
# The collision between two characters is the client's alone:
# CInstanceBase::CheckAdvancing tests the main instance against every other
# one, and CActorInstance::TestActorCollision skips a victim whose actor type
# is NPC (ENABLE_NPC_WITHOUT_COLLISIONS in this client's GameLib). The server
# tells the owner's client which character its companion is
# (playerbot_sidekick.h, SendPlayerBotSidekickBody):
#
#   SidekickVid <vid>     - 0 once it has gone
#
# and the companion is an NPC for as long as the world is updated and not a
# moment longer. CheckAdvancing runs in one place,
# CPythonCharacterManager::UpdateTransform, inside app.UpdateGame, which
# game.py's OnUpdate calls first of all; so app.UpdateGame is wrapped once
# (Install), and the wrapper types the companion as an NPC before the stock
# update and as the player it is after it.
#
# It used to stay an NPC from the moment the client had made it, and to this
# client an NPC is a body and nothing else ("Napraw fryzury npc, bo szamanka
# nie ma wlosow", 28 September: a Shaman companion, bald). Armour of
# another shape - its gear pass, its owner's hand, a stone or the anvil taking
# the piece off and back - comes as a character update, and
# CInstanceBase::ChangeArmor builds the model again: SetRace, where
# CActorInstance::SetRace reserves one model part for anything but a PC, then
# SetHair, which returns for a non-PC, SetWeapon, whose part is not there, and
# SetAcce, which returns too. The companion stood bald and empty-handed until
# it next came into view, and a hair dye or a sash never showed at all
# (ChangeHair, ChangeAcce). The client reads the packets before the windows'
# update in a frame (CPythonApplication::Process: the network stream, then
# OnUIUpdate) and handles a click between two frames (Loop), so now every
# model is built for a player, a click opens the player's menu
# (CPythonPlayer::OpenCharacterMenu takes a player only), and nothing but the
# collision ever sees an NPC.
#
# Under the cursor (SetPicked, from game.py's picking, every frame) it stays a
# player through the update as well, as it has been since a click on it
# opened no menu ("Na towarzysza nie dziala prawe klikniecie", Piciu713, 28
# September). The click itself falls between two frames now, but what it sets
# going inside the update - the walk to a character out of reach,
# CPythonPlayer::__ReserveProcess_ClickActor - meets what it met then. Walking
# into it with the cursor on it collides.
#
# Python 2.7 as the client has it; any exe of this line has the chr calls, and
# one without them only loses the collision, never the game or its update.

import chr
import player

# MT2009_PLUS_SIDEKICK_ROSTER_V1: an owner may have several companions in the
# game at once - "SidekickVids <count> <vid>..." names them all (the server
# sends "SidekickVid <first>" before it, for a root that knows only one).
# 'hover' is the VID of the one under the cursor, 0 for none.
_state = {'vid': 0, 'vids': [], 'hover': 0}

# Marks the wrapper on app.UpdateGame, so it is put there once.
WRAPPER_MARK = 'sidekickCollision'


def ParseVid(value):
	try:
		vid = int(value)
	except (TypeError, ValueError):
		return 0
	return vid if vid > 0 else 0


def SetVid(value, *rest):
	# Numbers after the VID (an older server's hair and sash, the keeper that
	# put them back before the model was built as a player's) are not read.
	vid = ParseVid(value)
	_state['vid'] = vid
	_state['vids'] = [vid] if vid else []
	_state['hover'] = 0
	if vid:
		Install()


def SetVids(count='0', *values):
	"""MT2009_PLUS_SIDEKICK_ROSTER_V1: every companion of the owner's in view
	of the server."""
	try:
		count = max(0, int(count))
	except (TypeError, ValueError):
		count = 0
	vids = []
	for value in values[:count]:
		vid = ParseVid(value)
		if vid and vid not in vids:
			vids.append(vid)
	_state['vids'] = vids
	_state['vid'] = vids[0] if vids else 0
	if _state['hover'] not in vids:
		_state['hover'] = 0
	if vids:
		Install()


def GetVid():
	return _state['vid']


def GetVids():
	return list(_state['vids'])


def _SetType(vid, kind):
	chr.SelectInstance(vid)
	try:
		chr.SetInstanceType(kind)
	finally:
		# The selection is what every other chr.Set* call acts on; the main
		# character is where the stock scripts expect to find it, whatever
		# the call did.
		chr.SelectInstance(player.GetMainCharacterIndex())


def BeginWorldUpdate():
	"""The companions' VIDs that were typed as NPCs for the update just now,
	an empty list when none was. Only while both instances are there: a
	selection that fails keeps the previous one, and the type would go to
	that. The one under the cursor stays a player."""
	typed = []
	vids = _state['vids']
	if not vids:
		return typed
	main = player.GetMainCharacterIndex()
	if not chr.HasInstance(main):
		return typed
	for vid in vids:
		if vid == _state['hover'] or vid == main or not chr.HasInstance(vid):
			continue
		_SetType(vid, chr.INSTANCE_TYPE_NPC)
		typed.append(vid)
	return typed


def EndWorldUpdate(vids):
	"""The companions players again. The update itself lets an instance that
	walked out of view go (CPythonCharacterManager::Update), and one no longer
	there is left alone."""
	if not vids or not chr.HasInstance(player.GetMainCharacterIndex()):
		return
	for vid in vids:
		if chr.HasInstance(vid):
			_SetType(vid, chr.INSTANCE_TYPE_PLAYER)


def _Guarded(call, *args):
	try:
		return call(*args)
	except Exception:
		# An exe without the call: the owner collides with its companion again,
		# and the world goes on being updated.
		_state['vid'] = 0
		_state['vids'] = []
		return 0


def Install():
	"""Wraps app.UpdateGame, once; True when the wrapper is on it. game.py
	looks the function up on the module at every frame, so the next update
	is the wrapper's."""
	# Imported here, as clientclock does it, so a test's stub is the one read.
	import app
	stock = getattr(app, 'UpdateGame', None)
	if stock is None:
		return False
	if getattr(stock, WRAPPER_MARK, False):
		return True

	def UpdateGame(*args):
		typed = _Guarded(BeginWorldUpdate)
		try:
			return stock(*args)
		finally:
			if typed:
				_Guarded(EndWorldUpdate, typed)

	setattr(UpdateGame, WRAPPER_MARK, True)
	try:
		app.UpdateGame = UpdateGame
	except Exception:
		return False
	return True


def SetPicked(picked):
	"""The character under the cursor, from game.py every frame (-1 for none).
	True when the companion came under the cursor or left it: under it, it
	stays a player through the next update too."""
	hover = picked if picked in _state['vids'] else 0
	if hover == _state['hover']:
		return False
	_state['hover'] = hover
	return True


class Keeper(object):
	"""Registered among game.py's updateables for its Destroy: the game
	window's end forgets the companion, and the next window hears the VID
	again (a warp is a new login on the server). The typing is the wrapped
	app.UpdateGame's, so there is nothing to do on a frame."""

	def CanUpdate(self):
		return False

	def OnUpdate(self):
		pass

	def Destroy(self):
		_state['vid'] = 0
		_state['vids'] = []
		_state['hover'] = 0


_keeper = []


def GetKeeper():
	if not _keeper:
		_keeper.append(Keeper())
	return _keeper[0]
