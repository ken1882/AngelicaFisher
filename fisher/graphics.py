import numpy as np
import win32gui
from desktopmagic.screengrab_win32 import getRectAsImage
from PIL import Image

import _G
from _G import log_debug, log_error, log_info, log_warning, resume, uwait, wait, flush
from fisher import Input

_G.DesktopDC = win32gui.GetDC(0)

def is_color_ok(cur, target, bias=None):
  if bias == None:
    bias = _G.ColorBiasRange
  log_debug("=== Pixel Color Comparing ===")
  for c1,c2 in zip(cur,target):
    if _G.VerboseLevel >= 4:
      print('-'*10)
      print(c1, c2)
    if abs(c1 - c2) > bias:
      return False
  return True

def is_pixel_match(pix, col, sync=False):
  for i, j in zip(pix, col):
    tx, ty = i
    if not is_color_ok(get_pixel(tx, ty, sync), j):
      return False
  return True

def get_pixel(x,y,sync=False):
  # use win32api to get pixel in real time, slower
  if sync:
    rect = get_full_rect()
    x += rect[0]
    y += rect[1]
    rgb = win32gui.GetPixel(_G.DesktopDC, x, y)
    b = (rgb & 0xff0000) >> 16
    g = (rgb & 0x00ff00) >> 8
    r = (rgb & 0x0000ff)
    return (r,g,b)
  # take DC snapshot first, faster
  dc = take_snapshot()
  return dc.getpixel((x,y))

def get_mouse_pixel(mx=None, my=None):
  if not mx and not my:
    mx, my = Input.get_cursor_pos()
  r,g,b = get_pixel(mx, my, True)
  return ["({}, {}),".format(mx, my), "({}, {}, {}),".format(r,g,b)]

def get_full_rect():
  return (
    _G.AppRect[0] + _G.WinTitleBarSize[0] + _G.WinDesktopBorderOffset[0],
    _G.AppRect[1] + _G.WinTitleBarSize[1] + _G.WinDesktopBorderOffset[1],
    _G.AppRect[2],
    _G.AppRect[3]
  )

def get_content_rect():
  rect = list(win32gui.GetClientRect(_G.AppHwnd))
  rect[0] += _G.WinTitleBarSize[0] + _G.WinDesktopBorderOffset[0] + _G.AppRect[0]
  rect[1] += _G.WinTitleBarSize[1] + _G.WinDesktopBorderOffset[1] + _G.AppRect[1]
  rect[2] += _G.WinTitleBarSize[0] - _G.WinTitleBarSize[0]
  rect[3] += _G.WinTitleBarSize[1] - _G.WinTitleBarSize[1]
  return tuple(rect)

def take_snapshot(rect=None,filename=None):
  if not filename:
    filename = _G.DCSnapshotFile
  offset = list(get_content_rect())
  if not rect:
    rect = offset
    rect[2] += rect[0]
    rect[3] += rect[1]
  else:
    rect = list(rect)
    rect[0] += offset[0]
    rect[1] += offset[1]
    rect[2] += offset[0]
    rect[3] += offset[1]
  # note: cache will be flushed every frame during main_loop
  if _G.LastFrameCount == _G.FrameCount and filename in _G.SnapshotCache:
    return _G.SnapshotCache[filename]
  else:
    _G.LastFrameCount = _G.FrameCount
  depth = 0
  while True:
    try:
      return _take_snapshot(rect, filename)
    except Exception as err:
      if depth > 5:
        raise err
      log_error("Error while taking snapshot, waiting for 5 seconds")
      depth += 1
      wait(5)

def _take_snapshot(rect,filename):
  path = filename if filename.startswith(_G.DCTmpFolder) else f"{_G.DCTmpFolder}/{filename}"
  getRectAsImage(tuple(rect)).save(path, format='png')
  img = Image.open(path)
  _G.SnapshotCache[filename] = img 
  return img 
