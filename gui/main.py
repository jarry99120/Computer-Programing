import tkinter as tk
from tkinter import messagebox, font
import ctypes
import os

# ====================== 載入 C 引擎 ======================
lib_path = os.path.join(os.path.dirname(__file__), '..', 'c_engine', 'libra_engine.so')
engine = ctypes.CDLL(lib_path)

# ====================== 定義 C 語言的結構體 ======================
class Tile(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("value", ctypes.c_int)
    ]

class Player(ctypes.Structure):
    _fields_ = [
        ("player_id", ctypes.c_int),
        ("hand", Tile * 50),
        ("hand_count", ctypes.c_int),
        ("suns", ctypes.c_int * 13),
        ("score", ctypes.c_int)
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
    ]

# 設定 C 函數參數型別
engine.init_game.argtypes = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype = None

# ====================== GUI 主程式 ======================
class RaGameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("太陽神 Ra - 單機版")
        self.root.geometry("1024x680")
        self.root.configure(bg="#2c2f33")

        # 中文字型
        self.title_font = font.Font(family="Noto Sans CJK TC", size=48, weight="bold")
        self.subtitle_font = font.Font(family="Noto Sans CJK TC", size=24)
        self.button_font = font.Font(family="Noto Sans CJK TC", size=18, weight="bold")

        self.game_state = GameState()

        # 標題
        title = tk.Label(self.root, text="太陽神 Ra", font=self.title_font, 
                        fg="#f1c40f", bg="#2c2f33")
        title.pack(pady=40)

        subtitle = tk.Label(self.root, text="經典桌遊單機電腦版", font=self.subtitle_font,
                           fg="#ffffff", bg="#2c2f33")
        subtitle.pack(pady=10)

        # 開始按鈕
        start_btn = tk.Button(self.root, text="開始新遊戲 (4人)", font=self.button_font,
                             bg="#f1c40f", fg="#2c2f33", width=20, height=2,
                             command=self.start_new_game)
        start_btn.pack(pady=50)

        # 退出按鈕
        quit_btn = tk.Button(self.root, text="退出遊戲", font=("Noto Sans CJK TC", 14),
                            bg="#e74c3c", fg="white", width=15, command=self.root.quit)
        quit_btn.pack(pady=20)

        self.root.mainloop()

    def start_new_game(self):
        try:
            engine.init_game(ctypes.byref(self.game_state), 4)
            actual_players = self.game_state.num_players
            messagebox.showinfo("遊戲開始！", 
                              f"C 引擎初始化成功！\n\n系統讀取到的玩家人數：{actual_players} 人")
            print(f"✅ 遊戲初始化完成！玩家人數：{actual_players}")
        except Exception as e:
            messagebox.showerror("錯誤", f"C 引擎呼叫失敗：{e}")

if __name__ == "__main__":
    RaGameGUI()
