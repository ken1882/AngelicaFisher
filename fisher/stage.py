import _G
from fisher import graphics
from _G import log_debug, log_error, log_info, log_warning, resume, uwait, wait

Enum = {
  'NormalCombatVictory': {
    'pos': ((49, 619),(112, 620),(50, 60),(858, 630),(748, 653),),
    'color': ((18, 155, 254),(19, 155, 254),(254, 254, 254),(136, 135, 134),(30, 6, 1),)
  },
  'MinigameDropEnd': {
    'pos': ((124, 165),(332, 610),(951, 618),(213, 168),),
    'color': ((254, 251, 239),(35, 213, 186),(32, 221, 188),(254, 254, 254),)
  },
  'FishingMind': {
    'pos': ((133, 58),(281, 58),(519, 73),(751, 71),(967, 76),),
    'color': ((0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),)
  },
  'CafeMain': {
    'pos': ((21, 24),(348, 40),(117, 542),(94, 688),(1207, 542),(1179, 694),),
    'color': ((205, 45, 65),(221, 215, 220),(254, 254, 253),(230, 236, 248),(111, 141, 252),(230, 236, 246),)
  }
}

def get_current_stage():
  global Enum
  if _G.LastFrameCount != _G.FrameCount:
    _G.CurrentStage = None
    _G.LastFrameCount = _G.FrameCount
  else:
    return _G.CurrentStage
  for key in Enum:
    stg = Enum[key]
    if graphics.is_pixel_match(stg['pos'], stg['color']):
      _G.CurrentStage = key
      return key

  return None

def check_pixels(pixstruct):
  return graphics.is_pixel_match(pixstruct['pos'], pixstruct['color'])

StageDepth = 0
LastStage = '_'
def is_stage(stg):
  global LastStage,StageDepth
  s = get_current_stage()
  if s != LastStage:
    _G.log_info("Current stage:", s)
    LastStage = s
    StageDepth = 0
  else:
    StageDepth += 1
  return s and stg in s

def has_completed_errands():
  return graphics.is_pixel_match(
    ((869, 320),(872, 316),(869, 312),(865, 315),),
    ((223, 44, 44),(223, 44, 44),(223, 44, 44),(223, 44, 44),)
  )