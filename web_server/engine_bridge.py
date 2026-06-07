# ==================== web_server/engine_bridge.py ====================
import os
import ctypes

# 1. 載入 DLL / SO 共享核心庫
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "libra_engine.dll")
engine = ctypes.CDLL(lib_path)

# ==================== 2. 定義 Ctypes 結構體對齊 ====================

class Tile(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int), 
        ("value", ctypes.c_int)
    ]

class Player(ctypes.Structure):
    _fields_ = [
        ("player_id",  ctypes.c_int),
        ("hand",       Tile * 50),
        ("hand_count", ctypes.c_int),
        ("suns",       ctypes.c_int * 13),
        ("sun_used",   ctypes.c_int * 13),
        ("score",      ctypes.c_int),
    ]

class GameState(ctypes.Structure):
    # 🎯 嚴格與 C 核心 game.h 記憶體規格 1:1 複製，絕不多塞欄位防止錯位
    _fields_ = [
        ("players", Player * 5),
        ("num_players", ctypes.c_int),
        ("deck", Tile * 200),
        ("deck_size", ctypes.c_int),
        ("auction_track", Tile * 8),
        ("auction_count", ctypes.c_int),
        ("sun_boat_position", ctypes.c_int),
        ("current_epoch", ctypes.c_int),
        ("current_player", ctypes.c_int),
        ("game_over", ctypes.c_int),
        
        ("auction_active", ctypes.c_int),
        ("center_sun", ctypes.c_int),
        ("highest_bid", ctypes.c_int),        
        ("highest_bidder", ctypes.c_int),     
        ("current_bidder", ctypes.c_int),     
        ("auction_trigger_player", ctypes.c_int)
        # ❌ 已移除 forced_auction 記憶體地雷，改由 app.py 在序列化時動態生成
    ]

# ==================== 3. 設定參數型態 (嚴格型別防禦) ====================

engine.init_game.argtypes       = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype        = None

engine.draw_tile.argtypes       = [ctypes.POINTER(GameState)]
engine.draw_tile.restype        = Tile

engine.conduct_auction.argtypes = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int]
engine.conduct_auction.restype  = None

engine.next_player.argtypes     = [ctypes.POINTER(GameState)]
engine.next_player.restype      = None

engine.run_auction.argtypes     = [ctypes.POINTER(GameState), ctypes.POINTER(ctypes.c_int), ctypes.c_int]
engine.run_auction.restype      = ctypes.c_int

engine.player_bid.argtypes      = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int]
engine.player_bid.restype       = ctypes.c_int # 1:有人得標, -1:流標, 0:下一位

# 🎯 全新擴充：神明板塊特殊行動 (God Action) 的型別防禦
# C 原型：int player_use_god_tile(GameState* gs, int player_idx, int track_index);
# ✨ 已修正：引數型別追加第三個參數 (ctypes.c_int)，對齊「精準一換一」後端規格
engine.player_use_god_tile.argtypes = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int]
engine.player_use_god_tile.restype  = ctypes.c_int # 1:執行成功, 0:執行失敗

# ==================== 4. 初始化全域狀態機指標 ====================

gs = GameState()
game_initialized = {'status': False} # 用於在跨模組間共享初始化狀態