import ctypes, os, sys

lib_path = os.path.join(os.path.dirname(__file__), '..', 'c_engine', 'libra_engine.so')
engine = ctypes.CDLL(lib_path)

class Tile(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("value", ctypes.c_int)]

class Player(ctypes.Structure):
    _fields_ = [
        ("player_id",  ctypes.c_int),
        ("hand",       Tile * 50),
        ("hand_count", ctypes.c_int),
        ("suns",       ctypes.c_int * 13),
        ("score",      ctypes.c_int),
    ]

class GameState(ctypes.Structure):
    _fields_ = [
        ("players",           Player * 5),
        ("num_players",       ctypes.c_int),
        ("deck",              Tile * 200),
        ("deck_size",         ctypes.c_int),
        ("auction_track",     Tile * 8),
        ("auction_count",     ctypes.c_int),
        ("sun_boat_position", ctypes.c_int),
        ("current_epoch",     ctypes.c_int),
        ("current_player",    ctypes.c_int),
        ("game_over",         ctypes.c_int),
    ]

engine.init_game.argtypes   = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype    = None
engine.score_epoch.argtypes = [ctypes.POINTER(GameState)]
engine.score_epoch.restype  = None
engine.score_final.argtypes = [ctypes.POINTER(GameState)]
engine.score_final.restype  = None

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}" + (f"  ({detail})" if detail else ""))
        failed += 1

def new_gs():
    gs = GameState()
    engine.init_game(ctypes.byref(gs), 4)
    for i in range(4):
        gs.players[i].score = 0
        gs.players[i].hand_count = 0
        # 太陽籌碼清零（避免干擾計分測試）
        for j in range(13):
            gs.players[i].suns[j] = 0
        # 每人給 1 張文明牌（1種=0分），避免文明0種扣-5干擾其他測試
        gs.players[i].hand[0] = Tile(4, 0)
        gs.players[i].hand_count = 1
    return gs

def add_tile(gs, player, tile_type, value=0, count=1):
    p = gs.players[player]
    for _ in range(count):
        p.hand[p.hand_count] = Tile(tile_type, value)
        p.hand_count += 1

PHARAOH=1; NILE=3; CIV=4; PYRAMID=5; GOD=6; GOLD=7; FLOOD=8

print("\n=== 測試 A：法老牌 ===")
gs = new_gs()
add_tile(gs, 0, PHARAOH, count=5)   # 最多
add_tile(gs, 1, PHARAOH, count=3)
add_tile(gs, 2, PHARAOH, count=3)
add_tile(gs, 3, PHARAOH, count=1)   # 最少
engine.score_epoch(ctypes.byref(gs))
check("法老最多 +5",  gs.players[0].score == 5,  f"實際={gs.players[0].score}")
check("法老最少 -2",  gs.players[3].score == -2, f"實際={gs.players[3].score}")
check("法老中間 0",   gs.players[1].score == 0,  f"實際={gs.players[1].score}")

print("\n=== 測試 B：法老牌全部相同（不計分）===")
gs = new_gs()
for i in range(4): add_tile(gs, i, PHARAOH, count=3)
engine.score_epoch(ctypes.byref(gs))
check("全部相同不計分", all(gs.players[i].score == 0 for i in range(4)))

print("\n=== 測試 C：神牌 +2 且計分後丟棄 ===")
gs = new_gs()
add_tile(gs, 0, GOD, count=3)
engine.score_epoch(ctypes.byref(gs))
check("神牌3張 +6",    gs.players[0].score == 6, f"實際={gs.players[0].score}")
check("神牌計分後丟棄", gs.players[0].hand_count == 0)

print("\n=== 測試 D：金牌 +3 且計分後丟棄 ===")
gs = new_gs()
add_tile(gs, 1, GOLD, count=2)
engine.score_epoch(ctypes.byref(gs))
check("金牌2張 +6",    gs.players[1].score == 6, f"實際={gs.players[1].score}")
check("金牌計分後丟棄", gs.players[1].hand_count == 0)

print("\n=== 測試 E：尼羅河+洪水 ===")
gs = new_gs()
add_tile(gs, 0, NILE, count=4)
add_tile(gs, 0, FLOOD, count=2)   # 有洪水 → 計分
add_tile(gs, 1, NILE, count=3)    # 無洪水 → 不計分
engine.score_epoch(ctypes.byref(gs))
check("尼羅4+洪水2=+6",    gs.players[0].score == 6, f"實際={gs.players[0].score}")
check("無洪水不計分",       gs.players[1].score == 0, f"實際={gs.players[1].score}")
# 玩家0：1(civ) + 4(nile) + 2(flood) = 7張。計分後：civ丟、flood丟 → 剩4張nile
check("洪水丟棄尼羅保留",   gs.players[0].hand_count == 4,
      f"實際={gs.players[0].hand_count}")

print("\n=== 測試 F：文明牌 ===")
gs = new_gs()
# 把 new_gs 給的預設 civ 清掉，重新給
for i in range(4): gs.players[i].hand_count = 0
add_tile(gs, 0, CIV, value=0)
add_tile(gs, 0, CIV, value=1)
add_tile(gs, 0, CIV, value=2)          # 3種 → +5
add_tile(gs, 1, CIV, value=0)
add_tile(gs, 1, CIV, value=1)
add_tile(gs, 1, CIV, value=2)
add_tile(gs, 1, CIV, value=3)          # 4種 → +10
add_tile(gs, 2, CIV, value=0, count=3) # 1種 → 0分
                                        # 玩家4 沒有 → -5
engine.score_epoch(ctypes.byref(gs))
check("文明3種 +5",  gs.players[0].score == 5,  f"實際={gs.players[0].score}")
check("文明4種 +10", gs.players[1].score == 10, f"實際={gs.players[1].score}")
check("文明1種 0",   gs.players[2].score == 0,  f"實際={gs.players[2].score}")
check("文明0種 -5",  gs.players[3].score == -5, f"實際={gs.players[3].score}")
check("文明牌計分後丟棄", gs.players[0].hand_count == 0)

print("\n=== 測試 G：紀念碑（第3時代）===")
gs = new_gs()
for i in range(4): gs.players[i].hand_count = 0
# 太陽籌碼全部設相同 → 最高=最低=相同，+5-5=0，互相抵銷
for i in range(4): gs.players[i].suns[0] = 10
for k in range(8): add_tile(gs, 0, PYRAMID, value=k)  # 8種 → +15
add_tile(gs, 1, PYRAMID, value=0, count=3)             # 同種3張 → 多樣+1、重複+5 = +6
engine.score_final(ctypes.byref(gs))
check("8種紀念碑 +15",  gs.players[0].score == 15, f"實際={gs.players[0].score}")
check("同種3張 +1+5=+6", gs.players[1].score == 6,  f"實際={gs.players[1].score}")

print("\n=== 測試 H：太陽籌碼（第3時代）===")
gs = new_gs()
for i in range(4): gs.players[i].hand_count = 0
# 太陽籌碼已在 new_gs 清零，直接設單一數值
gs.players[0].suns[0] = 13  # 最高
gs.players[1].suns[0] = 5
gs.players[2].suns[0] = 5
gs.players[3].suns[0] = 1   # 最低
engine.score_final(ctypes.byref(gs))
check("籌碼最高 +5", gs.players[0].score == 5,  f"實際={gs.players[0].score}")
check("籌碼最低 -5", gs.players[3].score == -5, f"實際={gs.players[3].score}")
check("籌碼中間 0",  gs.players[1].score == 0,  f"實際={gs.players[1].score}")

print(f"\n結果：{passed} 通過　{failed} 失敗")
if failed == 0:
    print("計分系統全部通過！可以做遊戲結束畫面了！")
else:
    sys.exit(1)
