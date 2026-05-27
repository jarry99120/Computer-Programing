import tkinter as tk
from tkinter import messagebox, font
import ctypes
import os

# ====================== 載入 C 引擎 ======================
lib_path = os.path.join(os.path.dirname(__file__), '..', 'c_engine', 'libra_engine.so')
engine = ctypes.CDLL(lib_path)

class GameState(ctypes.Structure):
    _fields_ = [
        ("num_players", ctypes.c_int),
        ("current_epoch", ctypes.c_int),
        ("sun_boat_position", ctypes.c_int),
        ("auction_count", ctypes.c_int),
        ("current_player", ctypes.c_int),
        ("game_over", ctypes.c_int),
    ]

engine.init_game.argtypes = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype = None
engine.draw_tile.argtypes = [ctypes.POINTER(GameState)]
engine.draw_tile.restype = ctypes.c_int   # 暫時簡化
engine.conduct_auction.argtypes = [ctypes.POINTER(GameState)]
engine.conduct_auction.restype = None

# ====================== GUI 主程式 ======================
class RaGameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("太陽神 Ra - 單機版")
        self.root.geometry("1200x720")
        self.root.configure(bg="#2c2f33")

        self.font = font.Font(family="Noto Sans CJK TC", size=14)
        self.big_font = font.Font(family="Noto Sans CJK TC", size=18, weight="bold")

        self.game_state = GameState()
        self.create_start_screen()

    def create_start_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="太陽神 Ra", 
                 font=("Noto Sans CJK TC", 48, "bold"), fg="#f1c40f", bg="#2c2f33").pack(pady=80)

        tk.Label(self.root, text="經典桌遊單機電腦版", 
                 font=self.big_font, fg="#ffffff", bg="#2c2f33").pack(pady=20)

        tk.Button(self.root, text="開始新遊戲 (4人)", font=self.big_font,
                  bg="#f1c40f", fg="#2c2f33", width=25, height=3,
                  command=self.start_new_game).pack(pady=80)

        tk.Button(self.root, text="退出遊戲", font=self.font,
                  bg="#e74c3c", fg="white", command=self.root.quit).pack(pady=10)

    def start_new_game(self):
        engine.init_game(ctypes.byref(self.game_state), 4)
        messagebox.showinfo("遊戲開始！", f"C 引擎初始化成功！\n玩家人數：{self.game_state.num_players} 人")
        self.create_game_screen()

    def create_game_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # 標題列
        header = tk.Frame(self.root, bg="#2c2f33")
        header.pack(fill="x", pady=10)
        tk.Label(header, text=f"第 {self.game_state.current_epoch} 時代", 
                 font=self.big_font, fg="#f1c40f", bg="#2c2f33").pack(side="left", padx=20)
        tk.Label(header, text=f"目前玩家：{self.game_state.current_player + 1}", 
                 font=self.big_font, fg="#ffffff", bg="#2c2f33").pack(side="right", padx=20)

        # 拍賣區
        auction_frame = tk.Frame(self.root, bg="#34495e", relief="sunken", bd=2)
        auction_frame.pack(pady=20, padx=30, fill="x")
        tk.Label(auction_frame, text="拍賣區 (Auction Track)", font=self.big_font, 
                 fg="white", bg="#34495e").pack(pady=8)
        self.auction_labels = []
        grid = tk.Frame(auction_frame, bg="#34495e")
        grid.pack()
        for i in range(8):
            lbl = tk.Label(grid, text="□", font=("Noto Sans CJK TC", 24), width=4, height=2,
                           bg="#ecf0f1", relief="ridge")
            lbl.grid(row=0, column=i, padx=4, pady=4)
            self.auction_labels.append(lbl)

        # 太陽船
        tk.Label(self.root, text=f"☀️ 太陽船位置：{self.game_state.sun_boat_position} / 9", 
                 font=self.big_font, fg="#f1c40f", bg="#2c2f33").pack(pady=15)

        # 動作按鈕
        btn_frame = tk.Frame(self.root, bg="#2c2f33")
        btn_frame.pack(pady=30)
        tk.Button(btn_frame, text="抽牌", font=self.big_font, width=12, height=2,
                  command=self.draw_card).grid(row=0, column=0, padx=15)
        tk.Button(btn_frame, text="召喚 Ra\n(開始競標)", font=self.big_font, width=15, height=2,
                  command=self.call_ra).grid(row=0, column=1, padx=15)

        # 返回按鈕
        tk.Button(self.root, text="返回開始畫面", font=self.font,
                  command=self.create_start_screen).pack(pady=20)

    def draw_card(self):
        # 呼叫 C 引擎抽牌
        engine.draw_tile(ctypes.byref(self.game_state))
        messagebox.showinfo("抽牌", f"已抽出一張牌！\n目前拍賣區有 {self.game_state.auction_count} 張牌")
        # TODO: 之後會在拍賣區顯示實際牌圖

    def call_ra(self):
        engine.conduct_auction(ctypes.byref(self.game_state))
        messagebox.showinfo("競標觸發", "Ra 牌出現！競標開始！\n（完整競標功能開發中）")

if __name__ == "__main__":
    RaGameGUI()
