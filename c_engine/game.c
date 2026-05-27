#include "game.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static void init_deck(Tile* deck, int* size) {
    int i = 0;
    for (int n=0; n<30; n++) deck[i++] = (Tile){TILE_RA, 0};
    for (int n=0; n<25; n++) deck[i++] = (Tile){TILE_PHARAOH, 0};
    for (int n=0; n<8;  n++) deck[i++] = (Tile){TILE_GOD, 0};
    for (int n=0; n<5;  n++) deck[i++] = (Tile){TILE_GOLD, 0};
    for (int n=0; n<25; n++) deck[i++] = (Tile){TILE_NILE, 0};
    for (int n=0; n<12; n++) deck[i++] = (Tile){TILE_FLOOD, 0};
    for (int n=0; n<30; n++) deck[i++] = (Tile){TILE_CIVILIZATION, n%5};
    for (int n=0; n<4;  n++) deck[i++] = (Tile){TILE_DISASTER, n};
    for (int n=0; n<24; n++) deck[i++] = (Tile){TILE_PYRAMID, n%8};
    *size = i;
    printf("✅ 牌堆初始化完成！共 %d 張牌\n", *size);
}

void shuffle_deck(Tile* deck, int size) {
    srand((unsigned)time(NULL));
    for (int i = size-1; i > 0; i--) {
        int j = rand() % (i+1);
        Tile tmp = deck[i]; deck[i] = deck[j]; deck[j] = tmp;
    }
    printf("✅ 牌堆已洗好！\n");
}

static int ra_track_max(int num_players) {
    int maxes[] = {0, 0, 6, 8, 9, 10};
    return maxes[num_players];
}

void init_game(GameState* gs, int num_players) {
    memset(gs, 0, sizeof(GameState));
    gs->num_players    = num_players;
    gs->current_epoch  = 1;
    gs->current_player = 0;
    gs->game_over      = 0;
    gs->auction_count  = 0;
    gs->sun_boat_position = 0;
    int all_suns[] = {2,3,4,5,6,7,8,9,10,11,12,13};
    int per_player = 3;
    for (int p = 0; p < num_players; p++) {
        gs->players[p].player_id  = p;
        gs->players[p].score      = 0;
        gs->players[p].hand_count = 0;
        for (int s = 0; s < per_player; s++)
            gs->players[p].suns[s] = all_suns[p * per_player + s];
    }
    init_deck(gs->deck, &gs->deck_size);
    shuffle_deck(gs->deck, gs->deck_size);
    printf("✅ 遊戲初始化完成！玩家人數：%d\n", num_players);
}

Tile draw_tile(GameState* gs) {
    Tile empty = {-1, 0};
    if (gs->deck_size <= 0) return empty;
    gs->deck_size--;
    Tile drawn = gs->deck[gs->deck_size];
    if (drawn.type == TILE_RA) {
        gs->sun_boat_position++;
        printf("☀️  Ra 牌！Ra軌道：%d/%d\n",
               gs->sun_boat_position, ra_track_max(gs->num_players));
        if (gs->sun_boat_position >= ra_track_max(gs->num_players))
            end_epoch(gs);
    } else {
        if (gs->auction_count < AUCTION_TRACK_SIZE)
            gs->auction_track[gs->auction_count++] = drawn;
        printf("✅ 抽到牌 type=%d，拍賣區：%d/8\n", drawn.type, gs->auction_count);
    }
    return drawn;
}

int add_to_auction(GameState* gs, Tile tile) {
    if (gs->auction_count >= AUCTION_TRACK_SIZE) return 0;
    gs->auction_track[gs->auction_count++] = tile;
    return 1;
}

void conduct_auction(GameState* gs) {
    printf("🔥 競標觸發！拍賣區：%d 張牌\n", gs->auction_count);
    gs->auction_count = 0;
}

int is_epoch_over(GameState* gs) {
    return gs->sun_boat_position >= ra_track_max(gs->num_players);
}

void end_epoch(GameState* gs) {
    printf("====== 第 %d 時代結束 ======\n", gs->current_epoch);
    gs->auction_count     = 0;
    gs->sun_boat_position = 0;
    if (gs->current_epoch >= 3) {
        gs->game_over = 1;
        printf("🏁 遊戲結束！\n");
    } else {
        gs->current_epoch++;
        printf("進入第 %d 時代！\n", gs->current_epoch);
    }
}
