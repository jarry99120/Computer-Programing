#include "game.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// 初始化完整牌堆（一個時代的牌，之後可擴充成 3 個時代）
static void init_deck(Tile* deck, int* size) {
    int idx = 0;

    // Ra 牌（每個時代有 1~2 張）
    deck[idx++] = (Tile){TILE_RA, 0};
    deck[idx++] = (Tile){TILE_RA, 0};

    // 法老牌
    for (int i = 0; i < 8; i++) deck[idx++] = (Tile){TILE_PHARAOH, 1};
    // 災難牌
    for (int i = 0; i < 6; i++) deck[idx++] = (Tile){TILE_DISASTER, 0};
    // 尼羅河牌
    for (int i = 0; i < 8; i++) deck[idx++] = (Tile){TILE_NILE, 0};
    // 文明牌
    for (int i = 0; i < 10; i++) deck[idx++] = (Tile){TILE_CIVILIZATION, 1};
    // 金字塔牌
    for (int i = 0; i < 6; i++) deck[idx++] = (Tile){TILE_PYRAMID, 1};

    *size = idx;
    printf("✅ 牌堆初始化完成！總共有 %d 張牌\n", *size);
}

// Fisher-Yates 洗牌演算法（真正隨機）
void shuffle_deck(Tile* deck, int size) {
    srand(time(NULL));
    for (int i = size - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        Tile temp = deck[i];
        deck[i] = deck[j];
        deck[j] = temp;
    }
    printf("✅ 牌堆已洗好！\n");
}

void init_game(GameState* gs, int num_players) {
    gs->num_players = num_players;
    gs->current_epoch = 1;
    gs->sun_boat_position = 0;
    gs->auction_count = 0;
    gs->game_over = 0;
    gs->current_player = 0;

    for (int i = 0; i < num_players; i++) {
        gs->players[i].player_id = i;
        gs->players[i].hand_count = 0;
        gs->players[i].score = 0;
        for (int j = 0; j < 13; j++) gs->players[i].suns[j] = 1; // 初始太陽神籌碼
    }

    init_deck(gs->deck, &gs->deck_size);
    shuffle_deck(gs->deck, gs->deck_size);

    printf("✅ 遊戲初始化完成！玩家人數：%d\n", num_players);
}

// 從牌堆抽牌，並放入拍賣區
Tile draw_tile(GameState* gs) {
    if (gs->deck_size <= 0) {
        Tile empty = {TILE_RA, 0};
        return empty;
    }
    gs->deck_size--;
    Tile drawn = gs->deck[gs->deck_size];
    
    // 加入拍賣區
    if (gs->auction_count < AUCTION_TRACK_SIZE) {
        gs->auction_track[gs->auction_count++] = drawn;
    }
    return drawn;
}

// 簡易競標（目前只是示範，之後會擴充成真正玩家出價）
void conduct_auction(GameState* gs) {
    printf("🔥 競標觸發！目前拍賣區有 %d 張牌\n", gs->auction_count);
    // TODO: 之後實作玩家出太陽神籌碼、最高者得牌的邏輯
    gs->auction_count = 0;  // 暫時清空拍賣區
}

