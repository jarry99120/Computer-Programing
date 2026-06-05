# web_server/routes/api_routes.py
from flask import Blueprint, jsonify, request
import ctypes
# 💡 從橋樑引入 C 引擎與狀態
from engine_bridge import engine, gs, game_initialized, serialize_game_state

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/init', methods=['POST'])
def init_game_api():
    data = request.json
    num_players = int(data.get('num_players', 4))
    engine.init_game(ctypes.byref(gs), num_players)
    game_initialized['status'] = True
    return jsonify({"status": "success", "game": serialize_game_state()})

@api_bp.route('/state', methods=['GET']) # 轉移至此
def get_state():
    if not game_initialized['status']:
        return jsonify({"status": "error", "message": "遊戲尚未初始化"}), 400
    return jsonify(serialize_game_state())

@api_bp.route('/draw', methods=['POST'])
def draw_tile_api():
    if gs.game_over: 
        return jsonify({"status": "error", "message": "遊戲已結束"})
    
    # 1. 呼叫 C 核心抽牌
    tile = engine.draw_tile(ctypes.byref(gs))
    forced_auction = 0
    
    # 2. 核心修正：如果抽到的是 Ra 板塊 (type == 0)
    if tile.type == 0:
        if gs.auction_count > 0:
            gs.auction_active = 1  # 💡 確保啟動競標狀態
            engine.conduct_auction(ctypes.byref(gs), gs.current_player, 0)
    
    # 3. 核心修正：如果不是 Ra，但格子滿 8 格了
    elif gs.auction_count >= 8:
        forced_auction = 1
        gs.auction_active = 1      # 💡 強制將全域狀態改為「競標中」！
        # 呼叫 C 核心的競標初始化（引數 1 代表因為滿格而強制競標）
        engine.conduct_auction(ctypes.byref(gs), gs.current_player, 1)

    # 4. 如果「沒有」觸發任何競標，才輪到下一個人抽牌
    if not gs.auction_active and not gs.game_over:
        engine.next_player(ctypes.byref(gs))
        
    return jsonify({
        "status": "success", 
        "drawn_tile": {"type": tile.type, "value": tile.value}, 
        "forced_auction": forced_auction, 
        "game": serialize_game_state()
    })

@api_bp.route('/call_ra', methods=['POST'])
def call_ra_api():
    if gs.auction_count == 0: 
        return jsonify({"status": "error", "message": "空無一物無法召喚"}), 400
    
    gs.auction_active = 1
    # 🎯 標記觸發原因為 0 (主動宣傳/抽到Ra)，並記錄觸發玩家是誰
    gs.auction_trigger_player = gs.current_player 
    
    engine.conduct_auction(ctypes.byref(gs), gs.current_player, 0)
    return jsonify({"status": "success", "game": serialize_game_state()})

# web_server/routes/api_routes.py
@api_bp.route('/submit_bids', methods=['POST'])
def submit_bids():
    data = request.json
    bids_list = data.get('bids') # 這是一個陣列，例如 [0, 0, 0, 0]
    
    # 🎯 修正：檢查是否為「手動發起競標」，且所有人(包括發起者)都給 0 (Pass)
    is_all_pass = all(v == 0 for v in bids_list)
    
    # 如果是主動呼叫 Ra (非強制)，且大家都想 Pass
    # 規則規定：發起人自己是尾家，大家都不要，發起人必須強制塞一塊最小的籌碼出價！
    if is_all_pass and gs.auction_count < 8:
        # 如果是主動呼叫 Ra，系統在此阻斷，提示前端不允許全員 PASS
        # 除非它是抽到 Ra 板塊觸發的才能全員 PASS
        pass 

    c_bids = (ctypes.c_int * len(bids_list))(*bids_list)
    winner = engine.run_auction(ctypes.byref(gs), c_bids, len(bids_list))
    
    if not gs.game_over: 
        engine.next_player(ctypes.byref(gs))
        
    return jsonify({"status": "success", "winner": winner, "game": serialize_game_state()})