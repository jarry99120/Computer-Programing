// ==================== game.h ====================
#ifndef GAME_H
#define GAME_H

#define MAX_PLAYERS        5
#define MAX_TILES        200
#define AUCTION_TRACK_SIZE 8
#define MAX_HAND          50

// ==================== 列舉與結構體定義 ====================

typedef enum {
    TILE_RA = 0, 
    TILE_PHARAOH = 1, 
    TILE_DISASTER = 2,
    TILE_NILE = 3, 
    TILE_CIVILIZATION = 4, 
    TILE_PYRAMID = 5,
    TILE_GOD = 6, 
    TILE_GOLD = 7, 
    TILE_FLOOD = 8
} TileType;

typedef struct { 
    TileType type; 
    int value; 
} Tile;

typedef struct {
    int player_id;
    Tile hand[MAX_HAND];
    int hand_count;
    int suns[13];
    int sun_used[13];   // 💡 0 = 正面可用, 1 = 翻面鎖定（次世代解鎖）
    int score;
} Player;

typedef struct {
    Player players[MAX_PLAYERS];
    int num_players;
    Tile deck[MAX_TILES];
    int deck_size;
    Tile auction_track[AUCTION_TRACK_SIZE];
    int auction_count;
    int sun_boat_position;
    int current_epoch;
    int current_player;
    int game_over;
    
    int auction_active;         // 競標狀態機是否啟動中
    int center_sun;             // 桌面正中央的公共太陽籌碼數值
    int highest_bid;            // 當前競標的最高出價
    int highest_bidder;         // 當前最高出價者的玩家 Index
    int current_bidder;         // 當前輪到出價的玩家 Index
    int auction_trigger_player; // 發起競標（喊Ra或抽到Ra）的玩家 Index
} GameState;

// ==================== 跨檔案函式宣告 (通訊橋樑) ====================

// 1️⃣ 核心基礎與輔助功能
void init_game(GameState* gs, int num_players);
void shuffle_deck(Tile* deck, int size);
Tile draw_tile(GameState* gs);
int  add_to_auction(GameState* gs, Tile tile);
void next_player(GameState* gs);
int  has_available_suns(Player* p); // 💡 公開給狀態機檢查資格

// 2️⃣ 德式競標狀態機核心
void conduct_auction(GameState* gs, int trigger_player, int is_forced);
int  player_bid(GameState* gs, int player_idx, int sun_value);
int  run_auction(GameState* gs, int bids[], int num_bids);

// 3️⃣ 拍賣池拾取與災難處理
void resolve_auction_win(GameState* gs, int winner_idx, int win_bid); // 💡 公開給競標模組結算

// 4️⃣ 時代推進判斷
int  is_epoch_over(GameState* gs);
void end_epoch(GameState* gs);

// 🎯 5️⃣ 全新擴充：神明板塊特殊行動 (God Action)
// 💡 供後端 API 控制器呼叫，執行成功回傳 1，失敗回傳 0
// ✨ 已修正：傳入 track_index 以實作「精準一換一」規則對齊
int  player_use_god_tile(GameState* gs, int player_idx, int track_index);

#endif // GAME_H