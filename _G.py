from datetime import datetime
from time import sleep
from random import random
from copy import copy
import sys
import json

ARGV = {}
Config = {}

if sys.platform == 'win32':
  IS_WIN32 = True
elif sys.platform == 'linux':
  IS_LINUX = True

AppWindowName = "ANGELICA ASTER R"
AppChildWindowName = ""
AppHwnd = 0
AppRect = [0,0,0,0]
AppPid  = 0
AppTid  = 0
AppChildHwnd = 0

AppInputHwnd   = 0
AppInputUseMsg = False

SelfHwnd = 0
SelfPid  = 0

DCTmpFolder = ".tmp"
DCSnapshotFile = "snapshot.png"

WindowWidth  = 1296
WindowHeight = 759
WinTitleBarSize = (0, 31)
WinDesktopBorderOffset = (8,0)

FPS   = (1.0 / 120)
Fiber = None
FiberRet = None
DesktopDC = None
SelectedFiber = None

ColorBiasRange = 10
CurrentStage   = None
FrameCount     = 0
LastFrameCount = -1
PosRandomRange = (8,8)

SnapshotCache = {}  # OCR snapshot cache for current frame

# 0:NONE 1:ERROR 2:WARNING 3:INFO 4:DEBUG
VerboseLevel = 3

FlagRunning = True
FlagPaused  = False
FlagWorking = False

MsgPipeContinue = '\x00\x50\x00CONTINUE\x00'
MsgPipeStop  = "\x00\x50\x00STOP\x00"
MsgPipeError = "\x00\x50\x00ERROR\x00"
MsgPipeTerminated = "\x00\x50\x00TERMINATED\x00"
MsgPipeRet = "\x00\x50\x00RET\x00"
MsgPipeInfo = "\x00\x50\x00INFO\x00"

CVMatchHardRate  = 0.7    # Hard-written threshold in order to match
CVMatchStdRate   = 1.22   # Similarity standard deviation ratio above average in consider digit matched
CVMatchMinCount  = 1      # How many matched point need to pass
CVLocalDistance  = 10     # Template local maximum picking range


DiskTypes = ['Accele', 'Blast', 'Charge']

def logfile_name():
  return 'logs/'+datetime.now().strftime("%Y%m%d.log")

def format_curtime():
  return datetime.strftime(datetime.now(), '%H:%M:%S')

def log_error(*args, **kwargs):
  if VerboseLevel >= 1:
    print(f"[{format_curtime()}] [ERROR]:", *args, **kwargs)
    with open(logfile_name(), 'a') as fp:
      kwargs['file'] = fp
      print(f"[{format_curtime()}] [ERROR]:", *args, **kwargs)
    

def log_warning(*args, **kwargs):
  if VerboseLevel >= 2:
    print(f"[{format_curtime()}] [WARNING]:", *args, **kwargs)
    with open(logfile_name(), 'a') as fp:
      kwargs['file'] = fp
      print(f"[{format_curtime()}] [WARNING]:", *args, **kwargs)

def log_info(*args, **kwargs):
  if VerboseLevel >= 3:
    print(f"[{format_curtime()}] [INFO]:", *args, **kwargs)
    with open(logfile_name(), 'a') as fp:
      kwargs['file'] = fp
      print(f"[{format_curtime()}] [INFO]:", *args, **kwargs)

def log_debug(*args, **kwargs):
  if VerboseLevel >= 4:
    print(f"[{format_curtime()}] [DEBUG]:", *args, **kwargs)
    with open(logfile_name(), 'a') as fp:
      kwargs['file'] = fp
      print(f"[{format_curtime()}] [DEBUG]:", *args, **kwargs)

def resume(fiber):
  global Fiber,FiberRet
  ret = None
  try:
    ret = next(fiber)
    if ret and ret[0] == MsgPipeRet:
      log_info("Fiber signaled return")
      FiberRet = ret[1]
      return False
  except StopIteration:
    log_info("Fiber has stopped")
    return False
  return True

def resume_from(fiber):
  global FiberRet
  while resume(fiber):
    yield
  return FiberRet

def pop_fiber_ret():
  global FiberRet
  ret = copy(FiberRet)
  FiberRet = None
  return ret

def flush():
  global LastFrameCount,CurrentStage,SnapshotCache
  LastFrameCount = -1
  CurrentStage   = None
  SnapshotCache  = {}

WaitInterval = 0.5
def wait(sec):
  sleep(sec)

def uwait(sec):
  sleep(sec + max(random() / 2, sec * random() / 5))

def rwait(sec):
  global WaitInterval,FPS
  times = int(sec // (WaitInterval + FPS))
  for _ in range(times):
    wait(WaitInterval)
    yield
  wait(sec - times * (WaitInterval+FPS))

def make_lparam(x, y):
  return (y << 16) | x

def get_lparam(val):
  return (val & 0xffff, val >> 16)

def load_config():
  with open('config.json', 'r') as fp:
    return json.load(fp)

def save_config(config):
  with open('config.json', 'w') as fp:
    return json.dump(config, fp)

def set_config(key, value):
  global Config
  Config[key] = value
  print(f"Config changed: {key} => {value}")
  save_config(Config)


### Loading process