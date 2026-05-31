#include "game.h"
#include "scoring.h"
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
    int total_suns = 12;
    for (int i = total_suns - 1; i > 0; i--) {
        int j = rand() % (i+1);
	int tmp = all_suns[i];
	all_suns[i] = all_suns[j];
	all_suns[j] = tmp;
    }
    int per_player = total_suns / num_players;
    int idx = 0;
    for (int p = 0; p < num_players; p++) {
	gs -> players[p].player_id = p;
	gs -> players[p].score = 0;
	gs -> players[p].hand_count = 0;
	for (int s = 0; s < per_player; s++) {
	    gs -> players[p].suns[s] = all_suns[idx++];
	printf("  玩家%d 籌碼：", p+1);
	for (int s = 0; s < per_player; s++)
	    printf("%d ", gs->players[p].suns[s]);
	printf("\n");
    }
    init_deck(gs->deck, &gs->deck_size);
    shuffle_deck(gs->deck, gs->deck_size);
    printf("✅ 遊戲初始化完成！玩家人數：%d\n", num_players);
}
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
        if (gs->auction_count < AUCTION_TRACK_SIZE) {
        	gs->auction_track[gs->auction_count++] = drawn;
        	printf("✅ 抽到牌 type=%d，拍賣區：%d/8\n", drawn.type, gs->auction_count);
    	}
    	/* 拍賣區滿了 → 設旗標讓 Python 觸發競標 */
    	if (gs->auction_count >= AUCTION_TRACK_SIZE) {
        	printf("📦 拍賣區已滿！強制競標！\n");
        	gs->auction_active = 1;
    	}
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
    score_final(gs);
        printf("🏁 遊戲結束！\n");
    } else {
        gs->current_epoch++;
        printf("進入第 %d 時代！\n", gs->current_epoch);
    }
}

void next_player(GameState* gs) {
    int tries = 0;
    do {
        gs->current_player = (gs->current_player + 1) % gs->num_players;
        tries++;
        if (tries > gs->num_players) return;  /* 所有人都沒籌碼，時代結束 */
    } while (0);  /* 之後加入「沒籌碼就跳過」的邏輯 */
    printf("輪到玩家 %d\n", gs->current_player);
}

/* 回傳出價成功的玩家index，沒人出價回傳 -1 */
int run_auction(GameState* gs, int bids[], int num_bids) {
    int best_player = -1;
    int best_bid    = 0;
    for (int i = 0; i < num_bids; i++) {
        if (bids[i] > best_bid) {
            best_bid    = bids[i];
            best_player = i;
        }
    }
    if (best_player >= 0) {
        /* 勝者得到拍賣區所有牌 */
        Player* winner = &gs->players[best_player];
        for (int i = 0; i < gs->auction_count; i++)
            winner->hand[winner->hand_count++] = gs->auction_track[i];
        printf("競標勝者：玩家%d，出價%d，得到%d張牌\n",
               best_player, best_bid, gs->auction_count);
    } else {
        printf("沒有人出價，拍賣區清空\n");
    }
    gs->auction_count = 0;
    return best_player;
}
