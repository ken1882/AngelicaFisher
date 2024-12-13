import _G
import utils
from _G import wait, uwait, rwait
from fisher import Input, stage, position, graphics, audio

def start_fishing_fiber():
  utils.find_app_window()
  utils.resize_app_window()
  thresholds = []
  config = _G.load_config()
  for i in range(5):
      thresholds.append(range(int(config.get(f"fish_threshold_#{i+1}l")), int(config.get(f"fish_threshold_#{i+1}h"))))
  while True:
    while not stage.is_stage('FishingMind'):
      Input.rclick(1169, 379)
      yield from rwait(2)
    Input.rclick(616, 342)
    yield from rwait(3)
    audio.listen_fishing(thresholds, config.get('audio_input'), config.get('audio_output'), config.get('audio_playback'))
    Input.rclick(616, 342)
    if not stage.is_stage('FishingMind'):
      _G.log_info("Failed")
      with open('.tmp/fish.log', 'a') as fp:
        fp.write('\n'.join([str([int(n) for n in ar]) for ar in audio.DebugQueue]))
        fp.write('-'*30+'\n')
      yield from rwait(5)
      Input.rclick(616, 342)
      continue
    _G.log_info("Success")
    yield from rwait(10)
    Input.rclick(616, 342)
    uwait(1)

def main_loop():
  while _G.FlagRunning:
    wait(_G.FPS)
    if not _G.FlagWorking:
      continue
    try:
      if not _G.FlagPaused and _G.Fiber and not _G.resume(_G.Fiber):
        _G.log_info(f"Worker ended, return value: {_G.pop_fiber_ret()}")
        _G.Fiber = None 
        _G.FlagWorking = False
    except Exception as err:
      utils.handle_exception(err)