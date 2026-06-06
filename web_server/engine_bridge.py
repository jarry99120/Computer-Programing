# ==================== web_server/engine_bridge.py ====================
import os
import ctypes

# 1. 載入 DLL
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "libra_engine.dll")
engine = ctypes.CDLL(lib_path)

# 2. 定義 Ctypes 結構體
class Tile(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("value", ctypes.c_int)]

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

# 3. 設定參數型態 (加上嚴格防禦)
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

# 🎯 【修正核心】補齊 player_bid 的函式宣告，否則 C 核心收到的指標會直接變殘廢亂碼
engine.player_bid.argtypes      = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int]
engine.player_bid.restype       = ctypes.c_int # 假設回傳 1:有人得標, -1:流標, 0:下一位

# 初始化單一全域遊戲狀態
gs = GameState()
game_initialized = {'status': False} # 用 dict 方便在不同模組間共享狀態

def serialize_game_state():
    """
    🎯 修正列舉對照表：嚴格對齊 game.h 定義
    0:太陽神Ra, 1:法老, 2:災難, 3:尼羅, 4:文明, 5:金字塔, 6:神, 7:金, 8:洪水
    """
    TILE_NAMES = {
        0: "太陽神 Ra", 
        1: "法老 Pharaoh", 
        2: "災難 Disaster", 
        3: "尼羅河 Nile", 
        4: "文明 Civilization", 
        5: "金字塔 Pyramid", 
        6: "神明 God", 
        7: "金幣 Gold", 
        8: "洪水 Flood"
    }
    players_data = []
    for i in range(gs.num_players):
        p = gs.players[i]
        active_suns = [p.suns[j] for j in range(13) if p.suns[j] > 0 and p.sun_used[j] == 0]
        used_suns = [p.suns[j] for j in range(13) if p.suns[j] > 0 and p.sun_used[j] == 1]
        players_data.append({
            "player_id": p.player_id, # 保持 0-based
            "score": p.score, 
            "hand_count": p.hand_count,
            "active_suns": sorted(active_suns), 
            "used_suns": sorted(used_suns)
        })
        
    auction_track = [{"type_id": gs.auction_track[i].type, "name": TILE_NAMES.get(gs.auction_track[i].type, "未知")} for i in range(gs.auction_count)]
    
    return {
        "num_players": gs.num_players, 
        "current_player": gs.current_player, 
        "current_epoch": gs.current_epoch,
        "sun_boat_position": gs.sun_boat_position, 
        "deck_size": gs.deck_size, 
        "center_sun": gs.center_sun,
        "auction_count": gs.auction_count, 
        "auction_track": auction_track, 
        "auction_active": bool(gs.auction_active), # 強制轉布林
        "highest_bid": gs.highest_bid,
        "highest_bidder": gs.highest_bidder,
        "current_bidder": gs.current_bidder, 
        "game_over": bool(gs.game_over), 
        "players": players_data
    }