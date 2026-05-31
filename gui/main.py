import tkinter as tk
from tkinter import messagebox, font
import ctypes, os

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

print(f"Tile={ctypes.sizeof(Tile)}B  Player={ctypes.sizeof(Player)}B  GameState={ctypes.sizeof(GameState)}B")

engine.init_game.argtypes       = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype        = None
engine.draw_tile.argtypes       = [ctypes.POINTER(GameState)]
engine.draw_tile.restype        = Tile
engine.conduct_auction.argtypes = [ctypes.POINTER(GameState)]
engine.conduct_auction.restype  = None
engine.next_player.argtypes     = [ctypes.POINTER(GameState)]
engine.next_player.restype      = None
engine.run_auction.argtypes     = [ctypes.POINTER(GameState),
                                   ctypes.POINTER(ctypes.c_int), ctypes.c_int]
engine.run_auction.restype      = ctypes.c_int

TILE_NAMES  = {0:"Ra", 1:"法老", 2:"災難", 3:"尼羅",
               4:"文明", 5:"金字塔", 6:"神", 7:"金", 8:"洪水"}
TILE_COLORS = {0:"#e74c3c", 1:"#9b59b6", 2:"#7f8c8d", 3:"#3498db",
               4:"#27ae60", 5:"#e67e22", 6:"#f1c40f", 7:"#f39c12", 8:"#2980b9"}

class AuctionDialog(tk.Toplevel):
    """競標出價視窗：每位玩家輸入出價或 0 表示 Pass"""
    def __init__(self, parent, gs):
        super().__init__(parent)
        self.title("競標！")
        self.configure(bg="#2c2f33")
        self.resizable(False, False)
        self.gs = gs
        self.result = None   # 存放各玩家出價的 list

        fn = font.Font(family="Noto Sans CJK TC", size=13)
        fb = font.Font(family="Noto Sans CJK TC", size=15, weight="bold")

        tk.Label(self, text="競標開始！",
                 font=fb, fg="#f1c40f", bg="#2c2f33").pack(pady=12)
        tk.Label(self, text=f"拍賣區共 {gs.auction_count} 張牌\n出價 0 = Pass",
                 font=fn, fg="#bdc3c7", bg="#2c2f33").pack(pady=4)

        # 每位玩家一排輸入框
        self.entries = []
        form = tk.Frame(self, bg="#2c2f33")
        form.pack(padx=20, pady=10)
        for i in range(gs.num_players):
            suns = [gs.players[i].suns[j]
                    for j in range(13) if gs.players[i].suns[j] > 0]
            suns_str = "、".join(str(s) for s in suns) or "無"
            tk.Label(form, text=f"玩家 {i+1}（籌碼：{suns_str}）",
                     font=fn, fg="white", bg="#2c2f33",
                     width=22, anchor="w").grid(row=i, column=0, pady=4)
            entry = tk.Entry(form, font=fn, width=6)
            entry.insert(0, "0")
            entry.grid(row=i, column=1, padx=10)
            self.entries.append(entry)

        tk.Button(self, text="確認出價", font=fb,
                  bg="#27ae60", fg="white",
                  command=self._confirm).pack(pady=16)

        # 讓視窗置中並等待
        self.grab_set()
        self.wait_window()

    def _confirm(self):
        bids = []
        for i, e in enumerate(self.entries):
            try:
                val = int(e.get())
            except ValueError:
                val = 0
            bids.append(max(0, val))
        self.result = bids
        self.destroy()


class RaGameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("太陽神 Ra")
        self.root.geometry("1200x720")
        self.root.configure(bg="#2c2f33")
        self.fn = font.Font(family="Noto Sans CJK TC", size=14)
        self.fb = font.Font(family="Noto Sans CJK TC", size=18, weight="bold")
        self.gs = GameState()
        self.create_start_screen()
        self.root.mainloop()

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def create_start_screen(self):
        self._clear()
        tk.Label(self.root, text="太陽神 Ra",
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
        messagebox.showinfo("遊戲開始！",
                            f"初始化成功！\n玩家：{self.gs.num_players} 人\n牌堆：{self.gs.deck_size} 張")
        self.create_game_screen()

    def create_game_screen(self):
        self._clear()

        top = tk.Frame(self.root, bg="#2c3e50", pady=8)
        top.pack(fill="x")
        self.epoch_lbl = tk.Label(top, text="", font=self.fb, fg="#f1c40f", bg="#2c3e50")
        self.epoch_lbl.pack(side="left", padx=20)
        self.ra_lbl = tk.Label(top, text="", font=self.fb, fg="#e74c3c", bg="#2c3e50")
        self.ra_lbl.pack(side="left", padx=20)
        self.player_lbl = tk.Label(top, text="", font=self.fb, fg="#fff", bg="#2c3e50")
        self.player_lbl.pack(side="right", padx=20)

        af = tk.Frame(self.root, bg="#34495e", pady=10)
        af.pack(fill="x", padx=20, pady=10)
        tk.Label(af, text="拍賣區 (Auction Track)",
                 font=self.fb, fg="white", bg="#34495e").pack()
        self.auction_lbls = []
        row = tk.Frame(af, bg="#34495e")
        row.pack()
        for i in range(8):
            lbl = tk.Label(row, text="", font=("Noto Sans CJK TC", 16),
                           width=7, height=2, bg="#ecf0f1", relief="ridge")
            lbl.grid(row=0, column=i, padx=4, pady=4)
            self.auction_lbls.append(lbl)

        bf = tk.Frame(self.root, bg="#2c2f33")
        bf.pack(pady=25)
        tk.Button(bf, text="抽牌", font=self.fb, width=12, height=2,
                  bg="#27ae60", fg="white",
                  command=self.action_draw).grid(row=0, column=0, padx=12)
        tk.Button(bf, text="召喚 Ra (競標)", font=self.fb, width=14, height=2,
                  bg="#e67e22", fg="white",
                  command=self.action_ra).grid(row=0, column=1, padx=12)

        sf = tk.Frame(self.root, bg="#2c2f33")
        sf.pack(pady=10)
        self.score_lbls = []
        for i in range(self.gs.num_players):
            lbl = tk.Label(sf, text="",
                           font=self.fn, fg="white", bg="#2c3e50",
                           width=16, pady=6, relief="ridge")
            lbl.grid(row=0, column=i, padx=5)
            self.score_lbls.append(lbl)

        tk.Button(self.root, text="返回開始畫面", font=self.fn,
                  command=self.create_start_screen).pack(pady=15)
        self._refresh()

    def _refresh(self):
        cp = self.gs.current_player
        self.epoch_lbl.config(text=f"第 {self.gs.current_epoch} 時代")
        self.ra_lbl.config(text=f"Ra軌道：{self.gs.sun_boat_position}/9")
        self.player_lbl.config(text=f"玩家 {cp+1} 的回合")
        for i, lbl in enumerate(self.auction_lbls):
            if i < self.gs.auction_count:
                t = self.gs.auction_track[i]
                lbl.config(text=TILE_NAMES.get(t.type, "?"),
                           bg=TILE_COLORS.get(t.type, "#95a5a6"), fg="white")
            else:
                lbl.config(text="", bg="#ecf0f1", fg="#2c2f33")
        for i in range(self.gs.num_players):
            p = self.gs.players[i]
            suns = [p.suns[j] for j in range(13) if p.suns[j] > 0]
            self.score_lbls[i].config(
                text=f"玩家{i+1}: {p.score}分\n手牌:{p.hand_count}張",
                bg="#f39c12" if i == cp else "#2c3e50",
                fg="#2c2f33" if i == cp else "white")

    def _do_auction(self):
        """跳出競標視窗，呼叫 C 引擎結算"""
        if self.gs.auction_count == 0:
            messagebox.showinfo("競標", "拍賣區沒有牌，競標取消")
            return
        dlg = AuctionDialog(self.root, self.gs)
        if dlg.result is None:
            return
        bids = dlg.result
        BidsArray = ctypes.c_int * len(bids)
        c_bids = BidsArray(*bids)
        winner = engine.run_auction(ctypes.byref(self.gs), c_bids, len(bids))
        if winner >= 0:
            messagebox.showinfo("競標結果",
                f"玩家 {winner+1} 以出價 {bids[winner]} 贏得競標！\n獲得拍賣區所有牌！")
        else:
            messagebox.showinfo("競標結果", "沒有人出價，拍賣區清空")

    def action_draw(self):
        tile = engine.draw_tile(ctypes.byref(self.gs))
        name = TILE_NAMES.get(tile.type, "未知")
        if tile.type == 0:
            messagebox.showinfo("抽到 Ra 牌！",
                f"Ra 牌出現！\nRa軌道：{self.gs.sun_boat_position}/9")
            if self.gs.auction_count > 0:
                self._do_auction()
        else:
            messagebox.showinfo("抽牌",
                f"抽到：{name}\n拍賣區：{self.gs.auction_count}/8 張\n牌堆剩：{self.gs.deck_size} 張")
        if self.gs.game_over:
            self._show_result()
            return
        engine.next_player(ctypes.byref(self.gs))
        self._refresh()

    def action_ra(self):
        self._do_auction()
        if self.gs.game_over:
            self._show_result()
            return
        engine.next_player(ctypes.byref(self.gs))
        self._refresh()

    def _show_result(self):
        self._clear()
        tk.Label(self.root, text="遊戲結束！",
                 font=("Noto Sans CJK TC", 42, "bold"),
                 fg="#f1c40f", bg="#2c2f33").pack(pady=40)

        # 找出勝者（分數最高）
        winner = max(range(self.gs.num_players),
                     key=lambda i: self.gs.players[i].score)

        # 各玩家分數
        sf = tk.Frame(self.root, bg="#2c2f33")
        sf.pack(pady=20)
        for i in range(self.gs.num_players):
            score = self.gs.players[i].score
            is_winner = (i == winner)
            color  = "#f1c40f" if is_winner else "white"
            prefix = "冠軍  " if is_winner else f"第{i+1}名  "
            tk.Label(sf,
                     text=f"{prefix}玩家 {i+1}：{score} 分",
                     font=("Noto Sans CJK TC", 22, "bold" if is_winner else "normal"),
                     fg=color, bg="#2c2f33").pack(pady=8)

        tk.Button(self.root, text="再玩一局",
                  font=("Noto Sans CJK TC", 16),
                  bg="#27ae60", fg="white", width=16, height=2,
                  command=self.create_start_screen).pack(pady=30)
        tk.Button(self.root, text="退出遊戲",
                  font=("Noto Sans CJK TC", 14),
                  bg="#e74c3c", fg="white",
                  command=self.root.quit).pack(pady=5)

if __name__ == "__main__":
    RaGameGUI()

# 注意：這段要手動貼進 RaGameGUI class 裡替換 action_draw
# 先用 nano 開檔案確認位置
