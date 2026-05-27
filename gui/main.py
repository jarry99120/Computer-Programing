import tkinter as tk
from tkinter import messagebox, font
import ctypes
import os

print("程式開始執行...")

# 載入 C 引擎
lib_path = os.path.join(os.path.dirname(__file__), '..', 'c_engine', 'libra_engine.so')
engine = ctypes.CDLL(lib_path)

# 對應 C 的結構體
class Tile(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("value", ctypes.c_int),
    ]

class Player(ctypes.Structure):
    _fields_ = [
        ("player_id", ctypes.c_int),
        ("hand", Tile * 50),
        ("hand_count", ctypes.c_int),
        ("suns", ctypes.c_int * 13),
        ("score", ctypes.c_int),
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

engine.init_game.argtypes = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype = None

print("C 引擎載入完成")

class RaGameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("太陽神 Ra - 單機版")
        self.root.geometry("1100x700")
        self.root.configure(bg="#2c2f33")

        self.font = font.Font(family="Noto Sans CJK TC", size=16)
        self.game_state = GameState()

        self.create_start_screen()
        self.root.mainloop()

    def create_start_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="太陽神 Ra",
                 font=("Noto Sans CJK TC", 48, "bold"),
                 fg="#f1c40f", bg="#2c2f33").pack(pady=80)

        tk.Label(self.root, text="經典桌遊單機電腦版",
                 font=self.font, fg="#ffffff", bg="#2c2f33").pack(pady=20)

        tk.Button(self.root, text="開始新遊戲 (4人)", font=self.font,
                  bg="#f1c40f", fg="#2c2f33", width=25, height=3,
                  command=self.start_new_game).pack(pady=60)

        tk.Button(self.root, text="退出遊戲", font=self.font,
                  bg="#e74c3c", fg="white",
                  command=self.root.quit).pack(pady=10)

    def start_new_game(self):
        try:
            engine.init_game(ctypes.byref(self.game_state), 4)
            actual_players = self.game_state.num_players
            print(f"遊戲初始化完成！玩家人數：{actual_players}")
            messagebox.showinfo("遊戲開始！",
                                f"C 引擎初始化成功！\n\n玩家人數：{actual_players} 人")
            self.create_game_screen()
        except Exception as e:
            messagebox.showerror("錯誤", f"發生錯誤：{e}")

    def create_game_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="遊戲主畫面開發中...",
                 font=("Noto Sans CJK TC", 28),
                 fg="#f1c40f", bg="#2c2f33").pack(pady=100)
        tk.Label(self.root, text="拍賣區、太陽船、玩家面板 即將加入",
                 font=self.font, fg="#ffffff", bg="#2c2f33").pack(pady=20)
        tk.Button(self.root, text="返回開始畫面", font=self.font,
                  command=self.create_start_screen).pack(pady=40)

if __name__ == "__main__":
    RaGameGUI()
