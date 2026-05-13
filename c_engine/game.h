#ifndef GAME_H
#define GAME_H

#define MAX_PLAYERS 5
#define MAX_TILES 200
#define AUCTION_TRACK_SIZE 8

typedef enum {
    TILE_RA,
    TILE_PHARAOH,
    TILE_DISASTER,
    TILE_NILE,
    TILE_CIVILIZATION,
    TILE_PYRAMID
} TileType;

typedef struct {
    TileType type;
    int value;        // 未來可以用來存分數或特殊屬性
} Tile;

typedef struct {
    int player_id;
    Tile hand[50];          // 玩家持有的牌
    int hand_count;
    int suns[13];           // 太陽神籌碼 (1~13)
    int score;
} Player;

typedef struct {
    Player players[MAX_PLAYERS];
    int num_players;
    Tile deck[MAX_TILES];
    int deck_size;
    Tile auction_track[AUCTION_TRACK_SIZE];
    int auction_count;
    int sun_boat_position;  // 太陽船位置
    int current_epoch;      // 1~3
    int current_player;
    int game_over;
} GameState;

// 函數宣告
void init_game(GameState* gs, int num_players);
void shuffle_deck(Tile* deck, int size);

#endif
