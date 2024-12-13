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
    return _G.set_config(key, value)

@api_expose
def get_config():
    return _G.load_config()

@api_expose
def start_fishing():
    _G.FlagWorking = True
    _G.Fiber = fiber.start_fishing_fiber()

@api_expose
def stop_fishing():
    _G.FlagWorking = False
    _G.Fiber = None

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

def init():
    _G.Config = _G.load_config()
    if not os.path.exists(_G.logfile_name()):
        with open(_G.logfile_name(), 'a'):
            pass
        _G.set_config('last_log_pos', 0)

if __name__ == '__main__':
    try:
        init()
        th = Thread(target=fiber.main_loop)
        th.start()
        webview.start(debug=_G.Config['debug'])
    finally:
        _G.FlagRunning = False
