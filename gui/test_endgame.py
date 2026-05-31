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

engine.init_game.argtypes    = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype     = None
engine.draw_tile.argtypes    = [ctypes.POINTER(GameState)]
engine.draw_tile.restype     = Tile
engine.score_epoch.argtypes  = [ctypes.POINTER(GameState)]
engine.score_epoch.restype   = None
engine.score_final.argtypes  = [ctypes.POINTER(GameState)]
engine.score_final.restype   = None
engine.end_epoch.argtypes    = [ctypes.POINTER(GameState)]
engine.end_epoch.restype     = None

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

print("\n=== 測試：3個時代完整流程 ===")
gs = GameState()
engine.init_game(ctypes.byref(gs), 4)

# 模擬第1時代結束
gs.sun_boat_position = 9
engine.end_epoch(ctypes.byref(gs))
check("進入第2時代",      gs.current_epoch == 2, f"實際={gs.current_epoch}")
check("Ra軌道重置",       gs.sun_boat_position == 0)
check("遊戲未結束",       gs.game_over == 0)

# 模擬第2時代結束
gs.sun_boat_position = 9
engine.end_epoch(ctypes.byref(gs))
check("進入第3時代",      gs.current_epoch == 3, f"實際={gs.current_epoch}")
check("遊戲未結束",       gs.game_over == 0)

# 模擬第3時代結束
gs.sun_boat_position = 9
# 手動給分讓結果明確
gs.players[0].score = 20
gs.players[1].score = 15
gs.players[2].score = 10
gs.players[3].score = 25
engine.end_epoch(ctypes.byref(gs))
check("遊戲結束",         gs.game_over == 1, f"實際={gs.game_over}")

print("\n=== 測試：勝者判定 ===")
winner = max(range(4), key=lambda i: gs.players[i].score)
check("玩家4分數最高(25分)", gs.players[3].score >= gs.players[0].score)
check("勝者是玩家4",         winner == 3, f"實際winner={winner}")

print(f"\n結果：{passed} 通過　{failed} 失敗")
if failed == 0:
    print("流程測試通過！可以開遊戲確認結束畫面了！")
    print("\n現在用 GUI 手動測試：")
    print("  cd gui && python3 main.py")
    print("  開始遊戲後一直按「召喚Ra」，讓拍賣區清空觸發時代切換")
    print("  直到第3時代結束，確認出現結束畫面")
else:
    sys.exit(1)
