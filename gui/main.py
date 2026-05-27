# gui/main.py
import tkinter as tk
from tkinter import messagebox, simpledialog, font
import ctypes, os

# ── C 引擎載入 ────────────────────────────────────────────
lib_path = os.path.join(os.path.dirname(__file__), '..', 'c_engine', 'libra_engine.so')
engine = ctypes.CDLL(lib_path)

# ── 完整 struct（對應 game.h，順序不能錯）─────────────────
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

# ── 啟動驗證（確認 struct 對齊）──────────────────────────
print(f"Tile={ctypes.sizeof(Tile)}B  Player={ctypes.sizeof(Player)}B  GameState={ctypes.sizeof(GameState)}B")

# ── C 函式簽名 ────────────────────────────────────────────
engine.init_game.argtypes = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype  = None
engine.draw_tile.argtypes = [ctypes.POINTER(GameState)]
engine.draw_tile.restype  = Tile          # ← 回傳 Tile struct，不是 c_int！
engine.conduct_auction.argtypes = [ctypes.POINTER(GameState)]
engine.conduct_auction.restype  = None

TILE_NAMES = {0:"Ra☀️", 1:"法老👑", 2:"災難💀", 3:"尼羅🌊", 4:"文明📜", 5:"金字塔🔺"}
TILE_COLORS = {0:"#e74c3c", 1:"#9b59b6", 2:"#7f8c8d", 3:"#3498db", 4:"#27ae60", 5:"#e67e22"}

# ── GUI ──────────────────────────────────────────────────
class RaGameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("☀️ 太陽神 Ra")
        self.root.geometry("1200x720")
        self.root.configure(bg="#2c2f33")
        self.fn = font.Font(family="Noto Sans CJK TC", size=14)
        self.fb = font.Font(family="Noto Sans CJK TC", size=18, weight="bold")
        self.gs = GameState()
        self.create_start_screen()
        self.root.mainloop()   # ← 這行之前漏掉了！

    def _clear(self):
        for w in self.root.winfo_children(): w.destroy()

    # ── 開始畫面 ─────────────────────────────────────────
    def create_start_screen(self):
        self._clear()
        tk.Label(self.root, text="☀️ 太陽神 Ra",
                 font=("Noto Sans CJK TC", 48, "bold"),
                 fg="#f1c40f", bg="#2c2f33").pack(pady=80)
        tk.Label(self.root, text="經典桌遊單機電腦版",
                 font=self.fb, fg="#fff", bg="#2c2f33").pack(pady=10)
        tk.Button(self.root, text="開始新遊戲 (4人)", font=self.fb,
                  bg="#f1c40f", fg="#2c2f33", width=25, height=3,
                  command=self.start_new_game).pack(pady=60)
        tk.Button(self.root, text="退出遊戲", font=self.fn,
                  bg="#e74c3c", fg="white",
                  command=self.root.quit).pack(pady=10)

    def start_new_game(self):
        engine.init_game(ctypes.byref(self.gs), 4)
        print(f"✅ init 成功，玩家人數={self.gs.num_players}，牌堆={self.gs.deck_size}張")
        messagebox.showinfo("遊戲開始！",
                            f"初始化成功！\n玩家：{self.gs.num_players} 人\n牌堆：{self.gs.deck_size} 張")
        self.create_game_screen()

    # ── 遊戲主畫面 ───────────────────────────────────────
    def create_game_screen(self):
        self._clear()

        # 頂部
        top = tk.Frame(self.root, bg="#2c3e50", pady=8)
        top.pack(fill="x")
        tk.Label(top, text=f"第 {self.gs.current_epoch} 時代",
                 font=self.fb, fg="#f1c40f", bg="#2c3e50").pack(side="left", padx=20)
        tk.Label(top, text=f"太陽船：{self.gs.sun_boat_position} / 9",
                 font=self.fb, fg="#e74c3c", bg="#2c3e50").pack(side="left", padx=20)
        self.player_lbl = tk.Label(top, text="", font=self.fb, fg="#fff", bg="#2c3e50")
        self.player_lbl.pack(side="right", padx=20)

        # 拍賣區
        af = tk.Frame(self.root, bg="#34495e", pady=10)
        af.pack(fill="x", padx=20, pady=10)
        tk.Label(af, text="拍賣區 (Auction Track)",
                 font=self.fb, fg="white", bg="#34495e").pack()
        self.auction_lbls = []
        row = tk.Frame(af, bg="#34495e"); row.pack()
        for i in range(8):
            lbl = tk.Label(row, text="□", font=("Noto Sans CJK TC", 20),
                           width=6, height=2, bg="#ecf0f1", relief="ridge")
            lbl.grid(row=0, column=i, padx=4, pady=4)
            self.auction_lbls.append(lbl)

        # 動作按鈕
        bf = tk.Frame(self.root, bg="#2c2f33"); bf.pack(pady=25)
        tk.Button(bf, text="抽牌", font=self.fb, width=12, height=2,
                  bg="#27ae60", fg="white",
                  command=self.action_draw).grid(row=0, column=0, padx=12)
        tk.Button(bf, text="召喚 Ra (競標)", font=self.fb, width=12, height=2,
                  bg="#e67e22", fg="white",
                  command=self.action_ra).grid(row=0, column=1, padx=12)

        # 玩家得分
        sf = tk.Frame(self.root, bg="#2c2f33"); sf.pack()
        self.score_lbls = []
        for i in range(self.gs.num_players):
            lbl = tk.Label(sf, text=f"玩家{i+1}: 0分",
                           font=self.fn, fg="white", bg="#2c3e50",
                           width=16, pady=6, relief="ridge")
            lbl.grid(row=0, column=i, padx=5)
            self.score_lbls.append(lbl)

        tk.Button(self.root, text="返回開始畫面", font=self.fn,
                  command=self.create_start_screen).pack(pady=15)
        self._refresh()

    def _refresh(self):
        cp = self.gs.current_player
        self.player_lbl.config(text=f"玩家 {cp+1} 的回合")
        for i, lbl in enumerate(self.auction_lbls):
            if i < self.gs.auction_count:
                t = self.gs.auction_track[i]
                lbl.config(text=TILE_NAMES.get(t.type,"?"),
                           bg=TILE_COLORS.get(t.type,"#95a5a6"), fg="white")
            else:
                lbl.config(text="□", bg="#ecf0f1", fg="#2c2f33")
        for i in range(self.gs.num_players):
            self.score_lbls[i].config(
                text=f"玩家{i+1}: {self.gs.players[i].score}分",
                bg="#f39c12" if i==cp else "#2c3e50",
                fg="#2c2f33" if i==cp else "white")

    def action_draw(self):
        tile = engine.draw_tile(ctypes.byref(self.gs))
        name = TILE_NAMES.get(tile.type, "未知")
        messagebox.showinfo("抽牌",
            f"抽到：{name}\n拍賣區：{self.gs.auction_count}/8 張\n牌堆剩：{self.gs.deck_size} 張")
        self._refresh()

    def action_ra(self):
        engine.conduct_auction(ctypes.byref(self.gs))
        messagebox.showinfo("競標", "競標結束，拍賣區已清空\n（完整競標功能開發中）")
        self._refresh()

if __name__ == "__main__":
    RaGameGUI()
