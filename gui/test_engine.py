import ctypes
import os

# 載入 C 共享函式庫
lib_path = os.path.join(os.path.dirname(__file__), '..', 'c_engine', 'libra_engine.so')
engine = ctypes.CDLL(lib_path)

# 定義 GameState 結構（必須和 game.h 一樣）
class GameState(ctypes.Structure):
    _fields_ = [
        ("players", ctypes.c_void_p * 5),   # 暫時用 void* 簡化
        ("num_players", ctypes.c_int),
        ("deck", ctypes.c_void_p * 200),
        ("deck_size", ctypes.c_int),
        ("auction_track", ctypes.c_void_p * 8),
        ("auction_count", ctypes.c_int),
        ("sun_boat_position", ctypes.c_int),
        ("current_epoch", ctypes.c_int),
        ("current_player", ctypes.c_int),
        ("game_over", ctypes.c_int),
    ]

# 設定函數的參數型別
engine.init_game.argtypes = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype = None

engine.shuffle_deck.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]  # 暫時簡化
engine.shuffle_deck.restype = None

print("✅ C 引擎載入成功！")

# 測試呼叫 C 函數
gs = GameState()
engine.init_game(ctypes.byref(gs), 4)        # 4 人遊戲
print(f"✅ init_game 呼叫成功！玩家人數 = {gs.num_players}")

print("🎉 Python 已經成功呼叫 C 引擎了！")
