import app
import net
import player
import ime

FIXED_TIMESTEP_UPDATE = 167
ONE_SECOND = 10000


# FPS_CAP_RAISE_V1: the frame cap, chosen in the options (System tab,
# uisystemoption.py) and kept in fps.cfg. The exe runs one OnUpdate per frame;
# with the exe patched by Ustaw_FPS.bat, app.SetFPS(n) makes every frame
# exactly 1000/n ms. FIXED_TIMESTEP_UPDATE (the step the timers below add per
# frame) and Ticks() follow it. With the original exe nothing changes.
FPS_CHOICES = (60, 120, 144, 240)
FPS_FILE = "fps.cfg"

# Where Ustaw_FPS.bat patches each client's exe: (CPythonApplication::SetFPS,
# its jump to the frame timer, the camera byte - see __IsCameraSpeedPatched).
EXE_PATCHES = (
	(0x2674c0, "\xe9\xeb\xdd\x6e\x00", 0x27fcbe),  # client 2.0.56
	(0x26b880, "\xe9\x3b\xe7\x6e\x00", 0x28409e),  # client 2.0.57
	(0x26c660, "\xe9\x6b\xe9\x6e\x00", 0x284e6e),  # client 2.0.60 / 2.0.62
	(0x26c6e0, "\xe9\x7b\xdd\x60\x00", 0x284eee),  # client 2.0.63
)

def __ReadExe(offset, size):
	try:
		f = old_open("metin2client.exe", "rb")
		f.seek(offset)
		code = f.read(size)
		f.close()
	except:
		return ""
	return code

def __PatchedExe():
	for fps, code, camera in EXE_PATCHES:
		if __ReadExe(fps, len(code)) == code:
			return fps, camera
	return None

def __IsExePatched():
	return __PatchedExe() is not None

def __LoadFps():
	try:
		fps = int(old_open(FPS_FILE, "r").read().strip())
	except:
		return 60
	if fps in FPS_CHOICES:
		return fps
	return 60

FPS_PATCHED = __IsExePatched()
FPS = 0  # 0 = original exe

# FPS_CAP_RAISE_V1: the camera keys (Q/E, R/F, T/G and the Scroll Lock movie
# camera) move the camera a fixed step per frame, so at 144 FPS they turned
# 2.4x faster. app.SetCameraSpeed scales those steps; Ustaw_FPS.bat makes it
# leave the mouse-drag sensitivity alone (one byte in the exe), so it is only
# used when that byte is patched.
def __IsCameraSpeedPatched():
	patched = __PatchedExe()
	if not patched:
		return False
	return __ReadExe(patched[1], 2) == "\xeb\x1d"  # app.SetCameraSpeed: the jump past the mouse sensitivity

CAMERA_SPEED_PATCHED = __IsCameraSpeedPatched()

def __ApplyCameraSpeed(fps):
	if not CAMERA_SPEED_PATCHED:
		return
	try:
		app.SetCameraSpeed(int(6000.0 / fps + 0.5))  # percent: the 60 FPS speed per second
	except:
		pass

def SetFps(fps, save = True):
	global FPS, FIXED_TIMESTEP_UPDATE
	if not FPS_PATCHED or fps not in FPS_CHOICES:
		return False
	app.SetFPS(fps)
	__ApplyCameraSpeed(fps)
	FPS = fps
	FIXED_TIMESTEP_UPDATE = int(10000.0 / fps + 0.5)
	if save:
		try:
			f = old_open(FPS_FILE, "w")
			f.write(str(fps))
			f.close()
		except:
			pass
	return True

def GetFps():
	return FPS or 60

def Ticks(frames60):
	"""Frames at 60 FPS -> the same time in frames at the current FPS."""
	if not FPS or frames60 <= 0:
		return frames60
	return max(1, int(frames60 * FPS / 60.0 + 0.5))

if FPS_PATCHED:
	SetFps(__LoadFps(), False)


class UpdatableAbstract:
	def __init__(self):
		pass

	def OnUpdate(self):
		pass

	def Destroy(self):
		pass

	def CanUpdate(self):
		return False


class PickUpOnDownKey(UpdatableAbstract):
	def __init__(self):
		UpdatableAbstract.__init__(self)
		self.timer = 0
		self.delay = 1500  # 0.15s

	def OnUpdate(self):
		self.timer += FIXED_TIMESTEP_UPDATE
		# With the pick-up filter on (uipickupfilter.py) the server picks up,
		# as it may once in half a second; PickCloseItem would take whatever
		# lies nearest, filtered or not.
		import uipickupfilter
		if uipickupfilter.IsActive():
			if self.timer >= 5000:
				net.SendChatPacket("/pickup_nearby")
				self.timer = 0
			return
		if self.timer >= self.delay:
			player.PickCloseItem()
			self.timer = 0

	def CanUpdate(self):
		# MT2009_PLUS_VEKIRION_V1 (Autor: Vekirion): the pick-up's own keys
		# (keybind.py: Z and ~ unless rebound; Ctrl+Z is the filter's window,
		# no pick-up).
		if ime.IsCaptureInput():
			return False
		import keybind
		return keybind.IsHeld("pickup") or keybind.IsHeld("pickup_near")
