from flask import Blueprint, render_template, jsonify, request, current_app
import traceback  # 引入追蹤工具，強制讓終端機印出詳細報報錯行號
import ctypes
from engine_bridge import gs, engine, game_initialized

main_bp = Blueprint('main', __name__)

# =================================================================
# 🎯 時代結束 - 板塊大掃除工具函式 (方案 B 實作)
# =================================================================
def cleanup_epoch_tiles(game_state):
    """
    當時代切換時，強制清洗 C 核心結構體內部的玩家手牌。
    只保留：法老 (1)、尼羅河 (3)、所有種類的建築 (5)
    """
    num_players = int(getattr(game_state, 'num_players', 2))
    
    for i in range(num_players):
        p = game_state.players[i]
        old_count = p.hand_count  # 💡 先記下清洗前的手牌總數（這是髒資料的邊界）
        kept_tiles = []
        
        # 1. 遍歷當前所有手牌，收集符合保留條件的板塊
        for h_idx in range(old_count):
            tile = p.hand[h_idx]
            if tile.type in [1, 3, 5]:
                kept_tiles.append((tile.type, tile.value))
        
        # 2. 將保留的板塊重新覆蓋回 C 結構體的陣列前段
        for idx, (t_type, t_val) in enumerate(kept_tiles):
            p.hand[idx].type = t_type
            p.hand[idx].value = t_val
            
        # 🎯【關鍵修改點】：把後面原本殘留文明板塊的「死角」全部強力超渡掉
        # 必須設為 -1，這樣前端 switch 才會走到 default 變成 generic.png
        for idx in range(len(kept_tiles), old_count):
            p.hand[idx].type = -1
            p.hand[idx].value = 0
            
        # 3. 精準更新手牌計數
        p.hand_count = len(kept_tiles)


# =================================================================
# 頁面路由區塊
# =================================================================

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/rule')
def rule():
    return render_template('rule.html')

@main_bp.route('/board')
def board():
    try:
        packer = current_app.config['STATE_PACKER']
        return render_template('board.html', state=packer(gs))
    except Exception as e:
        print("\n[ERROR] /board render failed!")
        traceback.print_exc()
        return f"Internal Server Error: {str(e)}", 500

# =================================================================
# API 區塊 ------ 移除所有 Emoji，防止 Windows CP950 終端機編碼出錯
# =================================================================

@main_bp.route('/api/init', methods=['POST'])
def api_init_game():
    try:
        data = request.json or {}
        num_players = data.get('num_players', 3)
        
        # 1. 呼叫 C 核心初始化
        engine.init_game(gs, num_players)
        
        # 🎯【關鍵修正】：強制把前端傳來的人數，綁定到 Python 的 gs 物件上
        gs.num_players = num_players
        
        game_initialized['status'] = True
        packer = current_app.config['STATE_PACKER']
        return jsonify({"success": True, "game_state": packer(gs)})
    except Exception as e:
        print("\n[ERROR] /api/init failed!")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route('/api/draw', methods=['POST'])
def api_draw_tile():
    try:
        if not game_initialized['status']:
            return jsonify({"success": False, "error": "Game not initialized"}), 400
            
        # 🎯 攔截點 1：記錄抽牌前的時代
        old_epoch = int(gs.current_epoch)
            
        # 呼叫 C 核心抽牌
        drawn_tile = engine.draw_tile(gs)
        print(f"[Debug Draw] Type: {drawn_tile.type}, Value: {drawn_tile.value}, Current Active State: {gs.auction_active}")
        
        # 🎯 檢查時代是否因為抽牌（如抽滿 Ra 船）而推進
        if int(gs.current_epoch) > old_epoch:
            print(f"[Epoch Advanced] Epoch changed from {old_epoch} to {gs.current_epoch}. Cleaning tiles...")
            cleanup_epoch_tiles(gs)
        
        # 1. 如果 auction_active == 0 (沒抽到 Ra 且沒滿 8 格)，正常推進到下一位玩家的主回合。
        if int(gs.auction_active) == 0:
            engine.next_player(gs)
            
        packer = current_app.config['STATE_PACKER']
        return jsonify({
            "success": True, 
            "drawn_tile": {"type": drawn_tile.type, "value": drawn_tile.value},
            "game_state": packer(gs)
        })
    except Exception as e:
        print("\n[ERROR] /api/draw failed!")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route('/api/invoke_auction', methods=['POST'])
def api_invoke_auction():
    """
    🎯 玩家在前端主動點擊 [呼喚太陽神 / 發起競標] 按鈕
    """
    print("\n[Backend] Received /api/invoke_auction request...")
    try:
        if not game_initialized['status']:
            return jsonify({"success": False, "error": "Game not initialized"}), 400

        if int(gs.auction_active) != 0 or bool(gs.game_over):
            return jsonify({"success": False, "error": "Current state does not allow initiating auction"}), 400

        current_player = gs.current_player
        
        # 🛑【核心安全防禦】：利用真實的 C 結構體欄位檢查該玩家是否還有未使用的可用籌碼
        player_struct = gs.players[current_player]
        has_usable_sun = False
        for s_idx in range(13):
            if player_struct.suns[s_idx] > 0 and player_struct.sun_used[s_idx] == 0:
                has_usable_sun = True
                break
                
        if not has_usable_sun:
            return jsonify({"success": False, "error": "You have no active suns left to initiate an auction!"}), 400

        print(f"[Backend] Player {current_player + 1} voluntarily initiated an auction.")

        # 第三個參數 is_forced 傳入 0，精準定位這是「玩家主動喊拉」
        engine.conduct_auction(gs, current_player, 0)

        packer = current_app.config['STATE_PACKER']
        return jsonify({
            "success": True,
            "game_state": packer(gs),
            "message": f"Player {current_player + 1} called Ra! Auction started."
        })
    except Exception as e:
        print("\n[ERROR] /api/invoke_auction failed!")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route('/api/submit_bid', methods=['POST'])
def api_player_bid():
    """
    單步競標核心處理 API（精準對齊 C 核心回傳狀態版）
    """
    print("\n[Backend] Received /api/submit_bid request...")
    try:
        if not game_initialized['status']:
            print("[Bid Error] Game not initialized.")
            return jsonify({"success": False, "error": "Game not initialized"}), 400

        data = request.json or {}
        player_id = data.get('player_id')
        bid_value = data.get('bid_value', 0) 
        
        print(f"[Backend Params] Player ID: {player_id} ({type(player_id)}), Bid Value: {bid_value} ({type(bid_value)})")
        
        if player_id is None:
            print("[Bid Error] player_id is None.")
            return jsonify({"success": False, "error": "Missing player_id"}), 400

        # 🛑 【第一道防禦：Python 層驗證】
        if int(player_id) != int(gs.current_bidder):
            print(f"[Bid Warning] Python Layer Blocked! Expected bidder: {gs.current_bidder}, received: {player_id}")
            return jsonify({"success": False, "error": "It is not your turn to bid!"}), 400

        # 🎯 攔截點 2：記錄出價結算前的時代
        old_epoch = int(gs.current_epoch)

        # 呼叫 C 核心的單次出價處理，並 🎯 捕捉核心回傳值
        print("[Backend] Calling engine.player_bid()...")
        result = engine.player_bid(gs, player_id, bid_value)
        print(f"[Backend] engine.player_bid() completed. Return code: {result}")
        
        # 🎯 檢查時代是否因為這次競標結算（例如大家都用完籌碼、或結算完剛好踩到時代結束）而推進
        if int(gs.current_epoch) > old_epoch:
            print(f"[Epoch Advanced] Epoch changed from {old_epoch} to {gs.current_epoch} via Auction. Cleaning tiles...")
            cleanup_epoch_tiles(gs)

        # 🛑 【第二道防禦：根據 C 核心回傳值進行嚴格分流】
        if result == -2:
            print("[Bid Error] C Core rejected: Not in auction phase.")
            return jsonify({"success": False, "error": "目前非競標階段，拒絕出價"}), 400
        elif result == -3:
            print("[Bid Error] C Core rejected: Wrong bidder turn.")
            return jsonify({"success": False, "error": "不輪到你出價"}), 400

        # 狀態解讀
        auction_status = "continue"
        if result == 1:
            auction_status = "resolved"
        elif result == -1:
            auction_status = "passed"

        # 狀態打包
        print("[Backend] Serializing state (STATE_PACKER)...")
        packer = current_app.config['STATE_PACKER']
        updated_state = packer(gs)
        
        response_payload = {
            "status": "success",
            "auction_status": auction_status,
            "game_state": updated_state,
            "auction_result": {
                "winner": int(gs.highest_bidder),   
                "winning_bid": int(gs.highest_bid)  
            }
        }
        print(f"[Backend] Packing success. Auction Status: {auction_status}. Sending 200 OK.")
        return jsonify(response_payload)

    except Exception as e:
        print("\n[CRITICAL ERROR] Exception occurred in api_player_bid!!")
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": f"Backend exception: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500


@main_bp.route('/api/state', methods=['GET'])
def get_current_state():
    try:
        print(f"DEBUG: 在 routes.py 準備呼叫 packer 前，gs.num_players = {gs.num_players}")
        packer = current_app.config['STATE_PACKER']
        return jsonify(packer(gs))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/use_god_tile', methods=['POST'])
def api_use_god_tile():
    """
    🎯 玩家執行「使用神明板塊交換指定競標格」行動 API
    """
    print("\n[Backend] Received /api/use_god_tile request...")
    try:
        if not game_initialized['status']:
            return jsonify({"success": False, "error": "Game not initialized"}), 400

        data = request.json or {}
        player_id = data.get('player_id')
        track_index = data.get('track_index')

        if player_id is None or track_index is None:
            print("[God Action Error] player_id or track_index is None.")
            return jsonify({"success": False, "error": "Missing player_id or track_index"}), 400

        if int(player_id) != int(gs.current_player):
            return jsonify({"success": False, "error": "It is not your turn to take action!"}), 400

        if int(gs.auction_active) != 0 or bool(gs.game_over):
            return jsonify({"success": False, "error": "Cannot use God tile right now."}), 400

        if int(track_index) < 0 or int(track_index) >= int(gs.auction_count):
            return jsonify({"success": False, "error": "Invalid board tile slot selection."}), 400

        # 🎯 攔截點 3：記錄神明牌使用前的時代 (安全防禦用)
        old_epoch = int(gs.current_epoch)

        print(f"[Backend] Calling engine.player_use_god_tile(player_id={player_id}, track_index={track_index})...")
        success_code = engine.player_use_god_tile(gs, int(player_id), int(track_index))
        
        if success_code == 1:
            # 🎯 檢查時代是否因為此行動意外推進
            if int(gs.current_epoch) > old_epoch:
                cleanup_epoch_tiles(gs)

            packer = current_app.config['STATE_PACKER']
            updated_state = packer(gs)

            return jsonify({
                "success": True,
                "game_state": updated_state,
                "message": "God tile exchange successfully executed."
            })
        else:
            return jsonify({
                "success": False, 
                "error": "Action rejected by core engine rules (Verify your hand or chosen tile)."
            }), 400

    except Exception as e:
        print("\n[CRITICAL ERROR] Exception occurred in api_use_god_tile!!")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Backend exception: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500