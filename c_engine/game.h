#ifndef GAME_H
#define GAME_H

#define MAX_PLAYERS 5
#define MAX_TILES 200
#define AUCTION_TRACK_SIZE 8
#define MAX_HAND 50

typedef enum {
    TILE_RA,
    TILE_PHARAOH,      // 法老牌
    TILE_DISASTER,     // 災難牌
    TILE_NILE,         // 尼羅河牌
    TILE_CIVILIZATION, // 文明牌
    TILE_PYRAMID       // 金字塔牌
} TileType;

typedef struct {
    TileType type;
    int value;         // 未來可用來存特殊分數或類型
} Tile;

typedef struct {
    int player_id;
    Tile hand[MAX_HAND];
    int hand_count;
    int suns[13];      // 太陽神籌碼
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
    int current_epoch;     // 1~3
    int current_player;
    int game_over;
} GameState;

// 核心函數宣告
void init_game(GameState* gs, int num_players);
void shuffle_deck(Tile* deck, int size);
Tile draw_tile(GameState* gs);                    // 從牌堆抽一張牌
int add_to_auction(GameState* gs, Tile tile);     // 把牌加入拍賣區
void conduct_auction(GameState* gs);              // 簡易競標（之後會擴充）

#endif
