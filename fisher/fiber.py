import _G
import utils
from _G import wait, uwait, rwait
from fisher import Input, stage, position, graphics, audio
import win32con, win32gui

def do_clicks(x, y):
  oh = win32gui.GetForegroundWindow()
  ox, oy = Input.get_cursor_pos()
  for _ in range(2):
    Input.rclick(x, y)
    yield
  Input.set_cursor_pos(ox, oy)
  win32gui.SetForegroundWindow(oh)

def start_fishing_fiber():
  utils.find_app_window()
  utils.resize_app_window()
  _G.ARGV['threshold'] = []
  thresholds = []
  config = _G.load_config()
  for i in range(5):
    thresholds.append(range(int(config.get(f"fish_threshold_{i+1}l")), int(config.get(f"fish_threshold_{i+1}h"))))
  while True:
    while not stage.is_stage('FishingMind'):
      yield from do_clicks(1169, 379)
      yield from rwait(3)
    yield from do_clicks(616, 342)
    yield from rwait(3)
    _G.ARGV['fish_up'] = None
    _G.ARGV['threshold'] = thresholds
    while not _G.ARGV.get('fish_up'):
      yield
    _G.ARGV['threshold'] = []
    yield from do_clicks(616, 342)
    if not stage.is_stage('FishingMind'):
      _G.log_info("Failed, recent sound waves logged to `logs/failed.log`")
      audio.export_wave('logs/failed.log')
      yield from rwait(5)
      yield from do_clicks(616, 342)
      continue
    _G.log_info("Success")
    yield from rwait(10)
    yield from do_clicks(616, 342)
    uwait(1)

def update_input():
  if not utils.is_focused():
    return
  Input.update()
  if Input.is_trigger(win32con.VK_F5):
    print("Redetecting app window")
    utils.detect_app_window()
  elif Input.is_trigger(win32con.VK_F6):
    audio.export_wave('logs/audiowave.log')
    _G.log_info("Audio wave exported to `logs/audiowave.log`")
  elif Input.is_trigger(win32con.VK_F7):
    _G.log_info("Worker unpaused" if _G.FlagPaused else "Worker paused")
    _G.FlagPaused ^= True

def main_loop():
  while _G.FlagRunning:
    wait(_G.FPS)
    update_input()
    if not _G.FlagWorking:
      continue
    try:
      _G.FrameCount += 1
      if not _G.FlagPaused and _G.Fiber and not _G.resume(_G.Fiber):
        _G.log_info(f"Worker ended, return value: {_G.pop_fiber_ret()}")
        _G.Fiber = None
        _G.FlagWorking = False
    except Exception as err:
      utils.handle_exception(err)