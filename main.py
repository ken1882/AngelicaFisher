import _G
import utils
import os
import webview
import functools
from threading import Thread

from fisher import fiber, audio

Window = webview.create_window('Angel Fish', 'ui/index.html')

def api_expose(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            utils.handle_exception(err)
    return Window.expose(wrapper)

@api_expose
def set_config(key, value):
    old_in  = str(_G.Config.get('audio_input'))
    old_out = str(_G.Config.get('audio_output'))
    ret = _G.set_config(key, value)
    try:
        if key == 'audio_input' and value != old_in:
            audio.close_audio()
            init_audio()
        elif key == 'audio_output' and value != old_out:
            audio.close_audio()
            init_audio()
        start_listening()
    except Exception as err:
        utils.handle_exception(err)
        _G.log_warning("Perhaps you selected wrong device, try others")
    return ret

@api_expose
def get_config():
    return _G.load_config()

@api_expose
def start_fishing():
    _G.FlagWorking = True
    _G.Fiber = fiber.start_fishing_fiber()
    _G.log_info('Worker started')

@api_expose
def stop_fishing():
    _G.FlagWorking = False
    _G.Fiber = None
    _G.log_info('Worker terminated')

@api_expose
def get_logs(log_pos=0):
    fname = _G.logfile_name()
    if os.path.exists(fname):
        with open(fname, 'r') as fp:
            fp.seek(int(log_pos) or 0)
            return {'logs': fp.read(), 'pos': fp.tell()}
    else:
        pass

@api_expose
def get_devices():
    return audio.list_devices()

@api_expose
def play_sound_test():
    audio.play_file('test.wav', int(_G.load_config().get('audio_output') or 0))

@api_expose
def export_audio_wave():
    audio.export_wave('logs/audiowave.log')
    _G.log_info("Audio wave exported to `logs/audiowave.log`")

@api_expose
def pause():
    _G.FlagPaused ^= True
    _G.log_info('Worker paused' if _G.FlagPaused else 'Worker unpaused')

def start_listening():
    if not audio.Listening:
        th = Thread(target=audio.start_listening)
        th.start()

def init():
    if not os.path.exists('config.json'):
        with open('config.default.json', 'r') as fp:
            with open('config.json', 'w') as fp2:
                fp2.write(fp.read())
    _G.Config = _G.load_config()
    if not os.path.exists(_G.logfile_name()):
        with open(_G.logfile_name(), 'a'):
            pass
        _G.set_config('last_log_pos', 0)
    init_audio()

def init_audio():
    iv = int(_G.Config.get('audio_input'))
    ov = int(_G.Config.get('audio_output'))
    audio.init(iv, ov)

if __name__ == '__main__':
    try:
        init()
        th = Thread(target=fiber.main_loop)
        th.start()
        start_listening()
        try:
            utils.find_app_window()
            utils.resize_app_window()
        except Exception:
            _G.log_warning("Game not found, make sure starts it before running!")
        webview.start(debug=_G.Config['debug'])
    finally:
        _G.FlagRunning = False
