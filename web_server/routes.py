# ==================== web_server/routes.py ====================
from flask import Blueprint, render_template, jsonify, request, current_app
import traceback  # 引入追蹤工具，強制讓終端機印出詳細報錯行號
from engine_bridge import gs, engine, game_initialized

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

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
# API 區塊 —— 移除所有 Emoji，防止 Windows CP950 終端機編碼出錯
# =================================================================

@main_bp.route('/api/init', methods=['POST'])
def api_init_game():
    try:
        data = request.json or {}
        num_players = data.get('num_players', 3)
        engine.init_game(gs, num_players)
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
            
        drawn_tile = engine.draw_tile(gs)
        print(f"[Debug Draw] Type: {drawn_tile.type}, Value: {drawn_tile.value}")
        
        if not gs.auction_active:
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


@main_bp.route('/api/submit_bid', methods=['POST'])
def api_player_bid():
    """
    單步競標核心處理 API（移除所有 Emoji 確保安全）
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

        # 呼叫 C 核心的單次出價處理
        print("[Backend] Calling engine.player_bid()...")
        engine.player_bid(gs, player_id, bid_value)
        print("[Backend] engine.player_bid() completed successfully.")
        
        # 狀態打包
        print("[Backend] Serializing state (STATE_PACKER)...")
        packer = current_app.config['STATE_PACKER']
        updated_state = packer(gs)
        
        if 'auction_active' not in updated_state:
            print("[Backend Warning] 'auction_active' missing in packed state!")

        response_payload = {
            "status": "success",
            "game_state": updated_state,
            "auction_result": {
                "winner": int(gs.highest_bidder),   
                "winning_bid": int(gs.highest_bid)  
            }
        }
        print("[Backend] Packing success. Sending 200 OK back to frontend.")
        return jsonify(response_payload)

    except Exception as e:
        print("\n[CRITICAL ERROR] Exception occurred in api_player_bid!!")
        traceback.print_exc()  # 強制印出詳細錯誤行號
        return jsonify({
            "status": "error", 
            "message": f"Backend exception: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500


@main_bp.route('/api/state', methods=['GET'])
def get_current_state():
    try:
        if not game_initialized['status']:
            return jsonify({"success": False, "error": "Game not initialized"}), 400
        packer = current_app.config['STATE_PACKER']
        return jsonify(packer(gs))
    except Exception as e:
        print("\n[ERROR] /api/state failed!")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500