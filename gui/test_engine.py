import ctypes, os, sys

# ── 載入引擎 ──────────────────────────────────────────────
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

engine.init_game.argtypes       = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype        = None
engine.draw_tile.argtypes       = [ctypes.POINTER(GameState)]
engine.draw_tile.restype        = Tile
engine.conduct_auction.argtypes = [ctypes.POINTER(GameState)]
engine.conduct_auction.restype  = None
engine.next_player.argtypes     = [ctypes.POINTER(GameState)]
engine.next_player.restype      = None

# ── 測試工具 ──────────────────────────────────────────────
passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}" + (f" ({detail})" if detail else ""))
        failed += 1

# ══════════════════════════════════════════════════════════
print("\n測試 1：struct 大小")
check("Tile = 8 bytes",      ctypes.sizeof(Tile) == 8,      f"實際={ctypes.sizeof(Tile)}")
check("Player = 464 bytes",  ctypes.sizeof(Player) == 464,  f"實際={ctypes.sizeof(Player)}")
check("GameState = 4012 bytes", ctypes.sizeof(GameState) == 4012, f"實際={ctypes.sizeof(GameState)}")

# ══════════════════════════════════════════════════════════
print("\n測試 2：init_game")
gs = GameState()
engine.init_game(ctypes.byref(gs), 4)
check("玩家人數 = 4",         gs.num_players == 4)
check("牌堆 = 163 張",        gs.deck_size == 163,       f"實際={gs.deck_size}")
check("從第 1 時代開始",       gs.current_epoch == 1)
check("從玩家 0 開始",         gs.current_player == 0)
check("遊戲未結束",            gs.game_over == 0)
check("拍賣區初始為空",        gs.auction_count == 0)
check("Ra 軌道初始為 0",      gs.sun_boat_position == 0)

# ══════════════════════════════════════════════════════════
print("\n測試 3：draw_tile 一般牌進拍賣區")
gs2 = GameState()
engine.init_game(ctypes.byref(gs2), 4)

# 強制把牌堆前幾張設成法老牌（確保不是Ra牌）
for i in range(5):
    gs2.deck[gs2.deck_size - 1 - i].type = 1  # TILE_PHARAOH

before_deck = gs2.deck_size
engine.draw_tile(ctypes.byref(gs2))
check("抽牌後牌堆減少 1 張",   gs2.deck_size == before_deck - 1,
      f"before={before_deck} after={gs2.deck_size}")
check("一般牌進入拍賣區",      gs2.auction_count == 1,
      f"auction_count={gs2.auction_count}")

# ══════════════════════════════════════════════════════════
print("\n測試 4：draw_tile Ra 牌進 Ra 軌道")
gs3 = GameState()
engine.init_game(ctypes.byref(gs3), 4)

# 強制把最後一張設成 Ra 牌
gs3.deck[gs3.deck_size - 1].type = 0  # TILE_RA
before_ra = gs3.sun_boat_position
before_auction = gs3.auction_count
engine.draw_tile(ctypes.byref(gs3))
check("Ra 牌不進拍賣區",       gs3.auction_count == before_auction,
      f"auction_count={gs3.auction_count}")
check("Ra 軌道計數 +1",        gs3.sun_boat_position == before_ra + 1,
      f"before={before_ra} after={gs3.sun_boat_position}")

# ══════════════════════════════════════════════════════════
print("\n測試 5：next_player 輪替")
gs4 = GameState()
engine.init_game(ctypes.byref(gs4), 4)
check("初始玩家 = 0",          gs4.current_player == 0)
engine.next_player(ctypes.byref(gs4))
check("換到玩家 1",            gs4.current_player == 1, f"實際={gs4.current_player}")
engine.next_player(ctypes.byref(gs4))
check("換到玩家 2",            gs4.current_player == 2, f"實際={gs4.current_player}")
engine.next_player(ctypes.byref(gs4))
engine.next_player(ctypes.byref(gs4))
check("玩家 4 後回到玩家 0",   gs4.current_player == 0, f"實際={gs4.current_player}")

# ══════════════════════════════════════════════════════════
print("\n測試 6：conduct_auction 清空拍賣區")
gs5 = GameState()
engine.init_game(ctypes.byref(gs5), 4)
# 手動放 3 張牌進拍賣區
for i in range(3):
    gs5.auction_track[i] = Tile(1, 0)
gs5.auction_count = 3
engine.conduct_auction(ctypes.byref(gs5))
check("競標後拍賣區清空",      gs5.auction_count == 0, f"實際={gs5.auction_count}")

# ══════════════════════════════════════════════════════════
print("\n測試 7：Ra 軌道滿了時代結束")
gs6 = GameState()
engine.init_game(ctypes.byref(gs6), 4)
# 4人局 Ra 軌道上限 = 9，先填到 8
gs6.sun_boat_position = 8
# 再抽一張 Ra 牌觸發時代結束
gs6.deck[gs6.deck_size - 1].type = 0  # TILE_RA
engine.draw_tile(ctypes.byref(gs6))
check("時代推進到第 2 時代",   gs6.current_epoch == 2, f"實際={gs6.current_epoch}")
check("Ra 軌道重置為 0",      gs6.sun_boat_position == 0, f"實際={gs6.sun_boat_position}")

# ══════════════════════════════════════════════════════════
print(f"\n結果：{passed} 通過　{failed} 失敗")
if failed == 0:
    print("全部通過！可以繼續做競標功能了！")
else:
    print("有測試失敗，先修好再繼續！")
    sys.exit(1)
