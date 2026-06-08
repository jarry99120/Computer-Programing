# ==================== web_server/app.py ====================
from flask import Flask, jsonify, current_app
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
    names = {
        0: "太陽神 Ra", 1: "法老 Pharaoh", 2: "災難 Disaster", 
        3: "尼羅河 Nile", 4: "文明 Civilization", 5: "建築 Pyramid", 
        6: "神明 God", 7: "金幣 Gold", 8: "洪水 Flood"
    }
    base_name = names.get(tile_type, f"未知板塊(ID:{tile_type})")
    if tile_type == 4: 
        civ_names = {1: "天文 🔭", 2: "農業 🌾", 3: "寫作 📜", 4: "建築 📐", 5: "醫學 🧪"}
        return f"{base_name} - {civ_names.get(tile_value, '通用')}"
    if tile_type == 5: return f"{base_name} (型號 {tile_value})"
    if tile_type == 2: 
        dis_names = {1: "乾旱 ", 2: "地震 ", 3: "駕崩 ", 4: "戰亂 "}
        return f"🔥 {base_name} ({dis_names.get(tile_value, '未知型')})"
    return base_name

def get_display_name(tile_type, tile_value):
    ui_map = {
        0: "太陽神 Ra", 1: "法老", 2: "災難", 3: "尼羅河", 
        4: "文明", 5: "建築", 6: "神明", 7: "金幣", 8: "洪水"
    }
    base = ui_map.get(tile_type, "未知")
    if tile_type == 2:
        dis = {1: "乾旱 ", 2: "地震 ", 3: "駕崩 ", 4: "戰亂 "}
        return f"{dis.get(tile_value, '未知')} ({base})"
    if tile_type == 5: return f"建築 {tile_value}"
    if tile_type == 4:
        civ = {1: "火", 2: "農業", 3: "文字", 4: "天文", 5: "藝術"}
        return f"{civ.get(tile_value, '通用')} ({base})"
    return base

def get_game_state_json(gs):
    """將 C 核心的 GameState 序列化為 JSON，並注入 ra_limit。"""
    try:
        # 1. 取得人數 (防呆：若無屬性則預設 2)
        num_p = int(getattr(gs, 'num_players', 2))
        
        # 2. 計算 ra_limit
        ra_limit = 6 if num_p == 2 else 8
        
        # 3. 打包玩家資訊
        players_data = []
        for i in range(num_p): 
            p = gs.players[i]
            active_suns = sorted([p.suns[s_idx] for s_idx in range(13) if p.suns[s_idx] > 0 and p.sun_used[s_idx] == 0])
            used_suns = sorted([p.suns[s_idx] for s_idx in range(13) if p.suns[s_idx] > 0 and p.sun_used[s_idx] != 0])

            detailed_hand = []
            for h_idx in range(min(max(0, p.hand_count), 50)):
                tile = p.hand[h_idx]
                if tile.type != -1 and tile.type >= 0:
                    detailed_hand.append({
                        "type_id": tile.type, "type": tile.type,
                        "value_id": tile.value, "value": tile.value,
                        "name": get_tile_name(tile.type, tile.value)
                    })

            players_data.append({
                "player_id": int(p.player_id), "score": int(p.score),
                "hand_count": int(p.hand_count), "hand_tiles": detailed_hand,
                "active_suns": active_suns, "used_suns": used_suns
            })

        # 4. 打包拍賣軌道
        auction_track = []
        for m in range(min(max(0, gs.auction_count), 8)):
            t = gs.auction_track[m]
            auction_track.append({
                "type_id": t.type, "type": t.type,
                "value_id": t.value, "value": t.value,
                "name": get_tile_name(t.type, t.value),
                "display_name": get_display_name(t.type, t.value) 
            })

        # 5. 組合最終字典
        packed_dict = {
            "num_players": num_p,
            "ra_limit": ra_limit, 
            "current_player": int(gs.current_player),
            "current_epoch": int(gs.current_epoch),
            "sun_boat_position": int(gs.sun_boat_position),
            "deck_size": int(gs.deck_size),
            "center_sun": int(gs.center_sun),
            "auction_count": int(gs.auction_count), 
            "auction_track": auction_track,
            "auction_active": int(gs.auction_active),
            "highest_bid": int(gs.highest_bid),
            "highest_bidder": int(gs.highest_bidder),
            "current_bidder": int(gs.current_bidder),
            "game_over": bool(gs.game_over),
            "players": players_data,
            "forced_auction": True if int(gs.auction_active) in [2, 3] else False
        }
        
        packed_dict["auction_trigger_player"] = int(getattr(gs, 'auction_trigger_player', gs.current_player))

        return packed_dict

    except Exception as e:
        print("\n🔥 [💥 打包錯誤]")
        traceback.print_exc()
        raise e

# 將狀態打包工具函數掛載到 app.config 中
app.config['STATE_PACKER'] = get_game_state_json

# ==================== 啟動伺服器 ====================
if __name__ == '__main__':
    app.run(debug=True, port=8080)