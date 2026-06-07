# ==================== web_server/app.py ====================
from flask import Flask, jsonify
import traceback
from routes import main_bp
import sys
import io

# 🎯 強制指定 Python 終端機輸出的編碼為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)

# 註冊藍圖 (Blueprint)
app.register_blueprint(main_bp)

# ==================== 🎯 德式桌遊核心資料打包工具 ====================

def get_tile_name(tile_type, tile_value):
    """
    將 C 語言核心定義的 TileType (0~8) 轉換為前端可讀的中文詳細名稱。
    🎯 完美對齊 game.h 的真實列舉順序：
    0:RA, 1:PHARAOH, 2:DISASTER, 3:NILE, 4:CIVILIZATION, 5:PYRAMID, 6:GOD, 7:GOLD, 8:FLOOD
    """
    names = {
        0: "太陽神 Ra",
        1: "法老 Pharaoh",
        2: "災難 Disaster",
        3: "尼羅河 Nile",
        4: "文明 Civilization",
        5: "建築 Pyramid",  # 🎯 將原本的金字塔名稱包裝為前端想要的「建築」
        6: "神明 God",
        7: "金幣 Gold",
        8: "洪水 Flood"
    }
    base_name = names.get(tile_type, f"未知板塊(ID:{tile_type})")
    
    # 針對具有子類別（value）的板塊進行外觀字詞強化
    if tile_type == 4:    # 文明板塊 (game.h 中文明是 4)
        civ_names = {1: "天文 🔭", 2: "農業 🌾", 3: "寫作 📜", 4: "建築 📐", 5: "醫學 🧪"}
        return f"{base_name} - {civ_names.get(tile_value, '通用')}"
        
    if tile_type == 5:    # 金字塔板塊 (game.h 中金字塔是 5)
        return f"{base_name} (型號 {tile_value})"
        
    if tile_type == 2:    # 災難板塊 (game.h 中災難是 2)
        dis_names = {1: "戰亂 ⚔️", 2: "乾旱 ☀️", 3: "地震 🌋", 4: "瘟疫 💀"}
        return f"🔥 {base_name} ({dis_names.get(tile_value, '未知型')})"
    
    return base_name


def get_game_state_json(gs):
    """
    將 C 核心的 GameState 結構體完整序列化為 Python 字典（JSON）。
    加上全面的 try-except 終端機除錯機制，防止無聲卡死。
    """
    print("[Backend Packer] 正在將 C 結構體序列化為 JSON 字典...")
    try:
        players_data = []
        
        # 巡訪所有當前加入遊戲的玩家槽位
        for i in range(gs.num_players):
            p = gs.players[i]
            
            # 1. 籌碼分流
            active_suns = []
            used_suns = []
            for s_idx in range(13):
                sun_val = p.suns[s_idx]
                if sun_val > 0:  # 過濾 C 語言陣列的 0 號填充值
                    if p.sun_used[s_idx] == 0:
                        active_suns.append(sun_val)
                    else:
                        used_suns.append(sun_val)
            
            active_suns.sort()
            used_suns.sort()

            # 2. 板塊穿透 (安全防禦：最高不超過 MAX_HAND=50)
            detailed_hand = []
            safe_hand_count = min(max(0, p.hand_count), 50)
            for h_idx in range(safe_hand_count):
                tile = p.hand[h_idx]
                # 只要不是未填入的空槽 (-1) 或是未初始化的 0 值垃圾資料就打包
                if tile.type != -1 and tile.type >= 0:
                    detailed_hand.append({
                        "type_id": tile.type,  # 🎯 統一前端變數命名格式
                        "type": tile.type,
                        "value_id": tile.value, # 🎯 發放手牌也要帶有子數值型號
                        "value": tile.value,
                        "name": get_tile_name(tile.type, tile.value)
                    })

            # 組裝單一玩家的 JSON 資料物件
            players_data.append({
                "player_id": int(p.player_id), 
                "score": int(p.score),
                "hand_count": int(p.hand_count),
                "hand_tiles": detailed_hand,
                "active_suns": active_suns,
                "used_suns": used_suns
            })

        # 3. 組裝全域遊戲狀態機回傳 (加上上限安全防呆)
        safe_auction_count = min(max(0, gs.auction_count), 8)
        auction_track = []
        for m in range(safe_auction_count):
            t = gs.auction_track[m]
            # 🎯 補上 value 和 value_id，儲存格資料防禦
            auction_track.append({
                "type_id": t.type, 
                "type": t.type,
                "value_id": t.value,
                "value": t.value,
                "name": get_tile_name(t.type, t.value)
            })

        # 🎯【關鍵修復一】：不要轉成 bool！直接保留 C 底層的狀態碼整數給前端（0, 1, 2, 3）
        raw_auction_active = int(gs.auction_active)

        # 🎯【關鍵修復二】：利用 C 核心新狀態，極簡且精準地指派強制競標旗標 (給相容舊版前端使用)
        # 2 (抽到Ra) 或 3 (8格滿) 皆屬於強制競標
        forced_auction_flag = True if raw_auction_active in [2, 3] else False
                
        packed_dict = {
            "num_players": int(gs.num_players),
            "current_player": int(gs.current_player),
            "current_epoch": int(gs.current_epoch),
            "sun_boat_position": int(gs.sun_boat_position),
            "deck_size": int(gs.deck_size),
            "center_sun": int(gs.center_sun),
            "auction_count": int(gs.auction_count), 
            "auction_track": auction_track,
            "auction_active": raw_auction_active,  # 🚀 現在傳回的是 0, 1, 2, 3 整數
            "highest_bid": int(gs.highest_bid),
            "highest_bidder": int(gs.highest_bidder),
            "current_bidder": int(gs.current_bidder),
            "game_over": bool(gs.game_over),
            "players": players_data,
            "forced_auction": forced_auction_flag   # 🚀 根據 C 核心狀態完美對齊的相容旗標
        }
        
        # 💡 新增追蹤欄位防止前端在老代碼中找不到發起人
        if hasattr(gs, 'auction_trigger_player'):
            packed_dict["auction_trigger_player"] = int(gs.auction_trigger_player)
        else:
            packed_dict["auction_trigger_player"] = int(gs.current_player)

        print(f"[Backend Packer Success] 打包完成。當前輪位資訊 -> 玩家: {packed_dict['current_player']}, 狀態碼: {packed_dict['auction_active']}, 強制競標: {packed_dict['forced_auction']}")
        return packed_dict

    except Exception as e:
        print("\n🔥 [💥 app.py 打包工具崩潰] get_game_state_json 發生重大錯誤！")
        traceback.print_exc()
        raise e

# 將狀態打包工具函數掛載到 app.config 中
app.config['STATE_PACKER'] = get_game_state_json


# ==================== 啟動伺服器 ====================
if __name__ == '__main__':
    app.run(debug=True, port=5000)