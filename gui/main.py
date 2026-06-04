import tkinter as tk
from tkinter import messagebox, font
import ctypes, os

lib_path = r"C:\Users\Wei-han\Desktop\Computer-Programing\c_engine\libra_engine.dll"
engine = ctypes.CDLL(lib_path)

class Tile(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("value", ctypes.c_int)]

class Player(ctypes.Structure):
    _fields_ = [
        ("player_id",  ctypes.c_int),
        ("hand",       Tile * 50),
        ("hand_count", ctypes.c_int),
        ("suns",       ctypes.c_int * 13),
        ("sun_used",   ctypes.c_int * 13),  # 同步補上「籌碼是否已使用」旗標
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
        ("current_bidder", ctypes.c_int),     # 💡 確保與 game.h 順序完全一致
        ("auction_trigger_player", ctypes.c_int) 
    ]

print(f"Tile={ctypes.sizeof(Tile)}B  Player={ctypes.sizeof(Player)}B  GameState={ctypes.sizeof(GameState)}B")

# 設定 C 函式參數型態
engine.init_game.argtypes       = [ctypes.POINTER(GameState), ctypes.c_int]
engine.init_game.restype        = None
engine.draw_tile.argtypes       = [ctypes.POINTER(GameState)]
engine.draw_tile.restype        = Tile
engine.conduct_auction.argtypes = [ctypes.POINTER(GameState), ctypes.c_int, ctypes.c_int] # 💡 修正對齊 game.h 參數
engine.conduct_auction.restype  = None
engine.next_player.argtypes     = [ctypes.POINTER(GameState)]
engine.next_player.restype      = None
engine.run_auction.argtypes     = [ctypes.POINTER(GameState), ctypes.POINTER(ctypes.c_int), ctypes.c_int]
engine.run_auction.restype      = ctypes.c_int

TILE_NAMES  = {0:"Ra", 1:"法老", 2:"災難", 3:"尼羅",
               4:"文明", 5:"金字塔", 6:"神", 7:"金", 8:"洪水"}
TILE_COLORS = {0:"#e74c3c", 1:"#9b59b6", 2:"#7f8c8d", 3:"#3498db",
               4:"#27ae60", 5:"#e67e22", 6:"#f1c40f", 7:"#f39c12", 8:"#2980b9"}

class AuctionDialog(tk.Toplevel):
    def __init__(self, parent, gs):
        super().__init__(parent)
        self.title("神聖競標場")
        self.configure(bg="#2c2f33")
        self.resizable(False, False)
        self.gs = gs
        
        # 預設所有人都是 Pass (0)
        self.result = [0] * gs.num_players
        # 💡 自動與 C 引擎的競標出價順序同步，由觸發者的下一位開始
        self.current_voter = gs.current_bidder 
        self.votes_cast = 0  # 紀錄已經投了幾個人
        
        self.fn = font.Font(family="Noto Sans CJK TC", size=13)
        self.fb = font.Font(family="Noto Sans CJK TC", size=15, weight="bold")
        
        # 頂部狀態列
        tk.Label(self, text="🔥 太陽神招標大會 🔥", font=self.fb, fg="#f1c40f", bg="#2c2f33").pack(pady=10)
        tk.Label(self, text=f"拍賣區共 {gs.auction_count} 張牌  |  中央公共籌碼：[{gs.center_sun}]", 
                 font=self.fn, fg="#bdc3c7", bg="#2c2f33").pack(pady=2)
        
        # 當前出價狀況面板 (💡 修正拼字錯誤 pading -> padx, pady)
        self.status_frame = tk.Frame(self, bg="#23272a", relief="sunken", borderwidth=1)
        self.status_frame.pack(padx=20, pady=10, fill="x")
        
        self.status_labels = []
        for i in range(gs.num_players):
            lbl = tk.Label(self.status_frame, text=f"玩家 {i+1}：考慮中...", font=self.fn, fg="#99aab5", bg="#23272a")
            lbl.pack(anchor="w", padx=10, pady=4)
            self.status_labels.append(lbl)
            
        # 互動出價控制區
        self.control_frame = tk.Frame(self, bg="#2c2f33")
        self.control_frame.pack(pady=15, padx=20)
        self.turn_label = tk.Label(self.control_frame, text="", font=self.fb, fg="white", bg="#2c2f33")
        self.turn_label.grid(row=0, column=0, columnspan=5, pady=5)
        
        self.buttons_frame = tk.Frame(self.control_frame, bg="#2c2f33")
        self.buttons_frame.grid(row=1, column=0, columnspan=5, pady=5)
        
        self.grab_set()
        self.ask_next_player()
        self.wait_window()

    def ask_next_player(self):
        # 如果已經投滿人數，關閉視窗
        if self.votes_cast >= self.gs.num_players:
            self.destroy()
            return

        p_idx = self.current_voter
        
        # 重新整理出價看板
        for i in range(self.gs.num_players):
            if i == p_idx:
                self.status_labels[i].config(text=f"玩家 {i+1} 👤 正在挑選籌碼...", fg="#f1c40f")
            elif self.result[i] > 0:
                self.status_labels[i].config(text=f"玩家 {i+1}：出價 [{self.result[i]}]", fg="#2ec4b6")
            elif self.result[i] == 0 and self.status_labels[i]["text"] != "考慮中...":
                # 如果已經歷過且值為0，代表選擇了 Pass
                self.status_labels[i].config(text=f"玩家 {i+1}：Pass", fg="#e74c3c")

        p = self.gs.players[p_idx]
        self.turn_label.config(text=f"請玩家 {p_idx+1} 選擇出價籌碼：")
        
        # 清空舊按鈕
        for w in self.buttons_frame.winfo_children():
            w.destroy()
            
        # 撈取未使用的太陽籌碼做成按鈕
        available_suns = [p.suns[j] for j in range(13) if p.suns[j] > 0 and p.sun_used[j] == 0]
        
        col = 0
        for sun_val in available_suns:
            btn = tk.Button(self.buttons_frame, text=f"☀️ {sun_val}", font=self.fn, bg="#f1c40f", fg="#2c2f33",
                            width=6, command=lambda v=sun_val: self.cast_bid(v))
            btn.grid(row=0, column=col, padx=4, pady=4)
            col += 1
            
        # Pass 按鈕
        pass_btn = tk.Button(self.buttons_frame, text="Pass (不出價)", font=self.fn, bg="#e74c3c", fg="white",
                             width=12, command=lambda: self.cast_bid(0))
        pass_btn.grid(row=0, column=col, padx=10, pady=4)

    def cast_bid(self, val):
        # 最高出價限制（除了 Pass，出的價格必須大於場上目前的最高出價）
        max_current_bid = max(self.result)
        if val > 0 and val <= max_current_bid:
            messagebox.showwarning("出價無效", f"出價數字必須大於目前場上最高出價 ({max_current_bid})！")
            return
            
        self.result[self.current_voter] = val
        
        # 移動到下一位玩家（環狀循環）
        self.current_voter = (self.current_voter + 1) % self.gs.num_players
        self.votes_cast += 1
        self.ask_next_player()


class RaGameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("太陽神 Ra — 埃及榮耀重現版")
        self.root.geometry("1200x760")
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
                 fg="#f1c40f", bg="#2c2f33").pack(pady=60)
        tk.Label(self.root, text="經典桌遊單機電腦版 (完整機制支援)",
                 font=self.fb, fg="#fff", bg="#2c2f33").pack(pady=10)
        tk.Label(self.root, text="選擇人數",
                 font=self.fb, fg="#bdc3c7", bg="#2c2f33").pack(pady=20)
        btn_frame = tk.Frame(self.root, bg="#2c2f33")
        btn_frame.pack(pady=10)
        for n in [2, 3, 4, 5]:
            tk.Button(btn_frame,
                      text=f"{n} 人遊戲",
                      font=self.fb,
                      bg="#f1c40f", fg="#2c2f33",
                      width=10, height=2,
                      command=lambda num=n: self.start_new_game(num)
                      ).grid(row=0, column=n-2, padx=10)
        tk.Button(self.root, text="退出遊戲", font=self.fn,
                 bg="#e74c3c", fg="white",
                 command=self.root.quit).pack(pady=20)

    def start_new_game(self, num_players=4):
        engine.init_game(ctypes.byref(self.gs), num_players)
        messagebox.showinfo("遊戲開始！",
                            f"初始化成功！\n玩家：{self.gs.num_players} 人\n牌堆：{self.gs.deck_size} 張\n中央初始太陽：[{self.gs.center_sun}]")
        self.create_game_screen()

    def create_game_screen(self):
        self._clear()
        top = tk.Frame(self.root, bg="#2c3e50", pady=8)
        top.pack(fill="x")
        self.epoch_lbl = tk.Label(top, text="", font=self.fb, fg="#f1c40f", bg="#2c3e50")
        self.epoch_lbl.pack(side="left", padx=20)
        self.ra_lbl = tk.Label(top, text="", font=self.fb, fg="#e74c3c", bg="#2c3e50")
        self.ra_lbl.pack(side="left", padx=20)
        
        self.center_sun_lbl = tk.Label(top, text="", font=self.fb, fg="#2ec4b6", bg="#2c3e50")
        self.center_sun_lbl.pack(side="left", padx=40)
        
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
        bf.pack(pady=15)
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
                           width=22, pady=6, relief="ridge", justify="left")
            lbl.grid(row=0, column=i, padx=5)
            self.score_lbls.append(lbl)

        tk.Button(self.root, text="返回開始畫面", font=self.fn,
                 command=self.create_start_screen).pack(pady=10)
        self._refresh()

    def _refresh(self):
        cp = self.gs.current_player
        self.epoch_lbl.config(text=f"第 {self.gs.current_epoch} 時代")
        self.ra_lbl.config(text=f"Ra軌道：{self.gs.sun_boat_position}/9")
        
        self.center_sun_lbl.config(text=f"☯️ 中央公共太陽：[{self.gs.center_sun}]")
        
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
            
            active_suns = [p.suns[j] for j in range(13) if p.suns[j] > 0 and p.sun_used[j] == 0]
            used_suns   = [p.suns[j] for j in range(13) if p.suns[j] > 0 and p.sun_used[j] == 1]
            
            active_str = "、".join(str(s) for s in sorted(active_suns)) or "無"
            used_str   = "、".join(str(s) for s in sorted(used_suns)) or "無"
            
            info_text = (
                f" 玩家 {i+1} 👤\n"
                f" ────────────────\n"
                f"  分數：{p.score} 分\n"
                f"  板塊：{p.hand_count} 張\n"
                f"  可用太陽：{active_str}\n"
                f"  翻面太陽：{used_str}"
            )
            
            self.score_lbls[i].config(
                text=info_text,
                bg="#f1c40f" if i == cp else "#2c3e50",
                fg="#2c2f33" if i == cp else "white"
            )

    def _do_auction(self, is_forced=0):
        if self.gs.auction_count == 0:
            messagebox.showinfo("競標", "拍賣區沒有任何板塊，競標取消。")
            return
            
        # 💡 先呼叫 C 核心的 conduct_auction 來計算並記錄誰是目前的 current_bidder
        engine.conduct_auction(ctypes.byref(self.gs), self.gs.current_player, is_forced)
            
        dlg = AuctionDialog(self.root, self.gs)
        if dlg.result is None:
            return
            
        bids = dlg.result
        BidsArray = ctypes.c_int * len(bids)
        c_bids = BidsArray(*bids)
        
        winner = engine.run_auction(ctypes.byref(self.gs), c_bids, len(bids))
        
        if winner >= 0:
            messagebox.showinfo("競標定案",
                f"🎉 恭喜玩家 {winner+1} 贏得本次競標！\n手牌板塊已更新，出價籌碼與中央完成對調。")
        else:
            messagebox.showinfo("競標定案", "全員選擇 Pass，此輪無人得標，拍賣區直接清空！")
        self._refresh()

    def action_draw(self):
        tile = engine.draw_tile(ctypes.byref(self.gs))
        name = TILE_NAMES.get(tile.type, "未知")
        if tile.type == 0: # TILE_RA
            messagebox.showinfo("☀️ Ra 牌現身！",
                f"玩家 {self.gs.current_player+1} 抽到了 Ra 牌！\n天神船前進一格！Ra軌道上升至：{self.gs.sun_boat_position}/9")
            if self.gs.auction_count > 0:
                self._do_auction(is_forced=0)
        else:
            messagebox.showinfo("抽牌結果",
                f"抽到板塊：【{name}】\n拍賣區目前：{self.gs.auction_count}/8 張\n牌堆剩餘：{self.gs.deck_size} 張")
            if self.gs.auction_active:
                messagebox.showinfo("強制競標", "🚨 拍賣區 8 張已滿！立刻強制進入招標程序！")
                self.gs.auction_active = 0
                self._do_auction(is_forced=1)
                
        if self.gs.game_over:
            self._show_result()
            return
            
        engine.next_player(ctypes.byref(self.gs))
        self._refresh()

    def action_ra(self):
        messagebox.showinfo("召喚天神", f"玩家 {self.gs.current_player+1} 大喊 'RA'！主動開啟競標！")
        self._do_auction(is_forced=0)
        if self.gs.game_over:
            self._show_result()
            return
        engine.next_player(ctypes.byref(self.gs))
        self._refresh()

    def _show_result(self):
        self._clear()
        tk.Label(self.root, text="🏁 遊戲全場結束！ 🏁",
                 font=("Noto Sans CJK TC", 42, "bold"),
                 fg="#f1c40f", bg="#2c2f33").pack(pady=40)
                 
        winner = max(range(self.gs.num_players),
                     key=lambda i: self.gs.players[i].score)
                     
        sf = tk.Frame(self.root, bg="#2c2f33")
        sf.pack(pady=20)
        for i in range(self.gs.num_players):
            score = self.gs.players[i].score
            is_winner = (i == winner)
            color  = "#f1c40f" if is_winner else "white"
            prefix = "👑 冠軍  " if is_winner else f"第 {i+1} 名  "
            tk.Label(sf,
                     text=f"{prefix} 玩家 {i+1} ： {score} 分",
                     font=("Noto Sans CJK TC", 24,
                           "bold" if is_winner else "normal"),
                     fg=color, bg="#2c2f33").pack(pady=10)
                     
        tk.Button(self.root, text="再戰一局",
                 font=("Noto Sans CJK TC", 16, "bold"),
                 bg="#27ae60", fg="white", width=16, height=2,
                 command=self.create_start_screen).pack(pady=30)
        tk.Button(self.root, text="離開遊戲",
                 font=("Noto Sans CJK TC", 14),
                 bg="#e74c3c", fg="white",
                 command=self.root.quit).pack(pady=5)

if __name__ == "__main__":
    RaGameGUI()