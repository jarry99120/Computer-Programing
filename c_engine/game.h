#ifndef GAME_H
#define GAME_H

#define MAX_PLAYERS        5
#define MAX_TILES        200
#define AUCTION_TRACK_SIZE 8
#define MAX_HAND          50

typedef enum {
    TILE_RA=0, TILE_PHARAOH=1, TILE_DISASTER=2,
    TILE_NILE=3, TILE_CIVILIZATION=4, TILE_PYRAMID=5,
    TILE_GOD=6, TILE_GOLD=7, TILE_FLOOD=8
} TileType;

typedef struct { TileType type; int value; } Tile;

typedef struct {
    int player_id;
    Tile hand[MAX_HAND];
    int hand_count;
    int suns[13];
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
} GameState;

void init_game(GameState* gs, int num_players);
void shuffle_deck(Tile* deck, int size);
Tile draw_tile(GameState* gs);
int  add_to_auction(GameState* gs, Tile tile);
void conduct_auction(GameState* gs);
int  is_epoch_over(GameState* gs);
void end_epoch(GameState* gs);

#endif
