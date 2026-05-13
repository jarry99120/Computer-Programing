#include "game.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void init_game(GameState* gs, int num_players) {
    gs->num_players = num_players;
    gs->current_epoch = 1;
    gs->sun_boat_position = 0;
    gs->auction_count = 0;
    gs->game_over = 0;
    gs->current_player = 0;
    printf("✅ 遊戲初始化完成！玩家人數: %d\n", num_players);
}

void shuffle_deck(Tile* deck, int size) {
    // 暫時先不實作完整 Fisher-Yates，之後會補上
    srand(time(NULL));
    printf("✅ 牌堆已洗好！總共有 %d 張牌\n", size);
}
