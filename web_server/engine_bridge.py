# ==================== web_server/engine_bridge.py ====================
import os
import ctypes

# 1. 載入 DLL / SO 共享核心庫
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "libra_engine.dll")

if not os.path.exists(lib_path):
    raise FileNotFoundError(f"找不到核心函式庫: {lib_path}")

engine = ctypes.CDLL(lib_path)

# ==================== 2. 定義 Ctypes 結構體 (1:1 對齊 game.h) ====================

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
    ]

# ==================== 3. 嚴格型別綁定 (防止記憶體錯位) ====================

# --- 基礎遊戲運作 ---
engine.init_game.argtypes = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype = None

engine.draw_tile.argtypes = [ctypes.POINTER(GameState)]
engine.draw_tile.restype = Tile

engine.next_player.argtypes = [ctypes.POINTER(GameState)]
engine.next_player.restype = None

# --- 拍賣系統 ---
engine.conduct_auction.argtypes = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int]
engine.conduct_auction.restype = None

engine.run_auction.argtypes = [ctypes.POINTER(GameState), ctypes.POINTER(ctypes.c_int), ctypes.c_int]
engine.run_auction.restype = ctypes.c_int

engine.player_bid.argtypes = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int]
engine.player_bid.restype = ctypes.c_int

# --- 災難與板塊管理 (關鍵修復區) ---
# resolve_disaster_immediate(Player* p, int disaster_value)
engine.resolve_disaster_immediate.argtypes = [ctypes.POINTER(Player), ctypes.c_int]
engine.resolve_disaster_immediate.restype = None

# remove_tiles_by_type(Player* p, TileType type, int count)
engine.remove_tiles_by_type.argtypes = [ctypes.POINTER(Player), ctypes.c_int, ctypes.c_int]
engine.remove_tiles_by_type.restype = ctypes.c_int

# --- 特殊動作 ---
engine.player_use_god_tile.argtypes = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int]
engine.player_use_god_tile.restype = ctypes.c_int

# ==================== 4. 初始化全域狀態機 ====================

gs = GameState()
game_initialized = {'status': False}

def get_gs_pointer():
    """提供給 Flask 路由使用的指標取得函式"""
    return ctypes.byref(gs)