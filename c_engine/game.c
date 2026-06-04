// game.c 最頂端
#include "game.h"     // 💡 先引入核心結構
#include "scoring.h"  // 💡 再引入計分模組
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 內部輔助函式：檢查玩家是否有可用（未翻面）的籌碼
static int has_available_suns(Player* p) {
    for (int i = 0; i < 13; i++) {
        if (p->suns[i] > 0 && p->sun_used[i] == 0) {
            return 1; 
        }
    }
    return 0;
}

// 初始化牌堆
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

// 洗牌
void shuffle_deck(Tile* deck, int size) {
    srand((unsigned)time(NULL));
    for (int i = size-1; i > 0; i--) {
        int j = rand() % (i+1);
        Tile tmp = deck[i]; deck[i] = deck[j]; deck[j] = tmp;
    }
    printf("✅ 牌堆已洗好！\n");
}

// 取得不同人數下的太陽船軌道上限
static int ra_track_max(int num_players) {
    int maxes[] = {0, 0, 6, 8, 9, 10};
    return maxes[num_players];
}

// 初始化遊戲
void init_game(GameState* gs, int num_players) {
    memset(gs, 0, sizeof(GameState));
    gs->num_players       = num_players;
    gs->current_epoch     = 1;
    gs->current_player    = 0;
    gs->game_over         = 0;
    gs->auction_count     = 0;
    gs->sun_boat_position = 0;

    gs->center_sun = 1;

    // 隨機分發 2~13 號籌碼
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
        gs->players[p].player_id = p;
        gs->players[p].score = 0;
        gs->players[p].hand_count = 0;

        for (int s = 0; s < 13; s++) {
            gs->players[p].suns[s] = 0;
            gs->players[p].sun_used[s] = 0;
        }

        printf("  玩家 %d 籌碼：", p+1);
        for (int s = 0; s < per_player; s++) {
            gs->players[p].suns[s] = all_suns[idx++];
            printf("%d ", gs->players[p].suns[s]);
        }
        printf("\n");
    }

    init_deck(gs->deck, &gs->deck_size);
    shuffle_deck(gs->deck, gs->deck_size);
    
    // 初始化競標相關狀態
    gs->auction_active = 0;
    gs->highest_bid = 0;
    gs->highest_bidder = -1;

    printf("✅ 遊戲初始化完成！玩家人數：%d，中央初始籌碼：[%d]\n", num_players, gs->center_sun);
}

// 抽牌邏輯
Tile draw_tile(GameState* gs) {
    Tile empty = {-1, 0};
    if (gs->deck_size <= 0) return empty;
    
    // 競標中不允許抽牌
    if (gs->auction_active) return empty;

    gs->deck_size--;
    Tile drawn = gs->deck[gs->deck_size];
    
    if (drawn.type == TILE_RA) {
        gs->sun_boat_position++;
        printf("☀️  Ra 牌！Ra軌道：%d/%d\n",
               gs->sun_boat_position, ra_track_max(gs->num_players));
        
        if (gs->sun_boat_position >= ra_track_max(gs->num_players)) {
            end_epoch(gs);
        } else {
            // 抽到 Ra 牌，強制引發競標 (發起人是當前抽牌玩家)
            conduct_auction(gs, gs->current_player, 0); 
        }
    } else {
        if (gs->auction_count < AUCTION_TRACK_SIZE) {
            gs->auction_track[gs->auction_count++] = drawn;
            printf("✅ 抽到牌 type=%d，拍賣區：%d/8\n", drawn.type, gs->auction_count);
        }

        // 拍賣區滿 8 張，強制觸發競標
        if (gs->auction_count >= AUCTION_TRACK_SIZE) {
            printf("📦 拍賣區已滿！強制競標！\n");
            conduct_auction(gs, gs->current_player, 1); // 1 代表因滿了而強制觸發
        }
    }
    return drawn;
}

int add_to_auction(GameState* gs, Tile tile) {
    if (gs->auction_count >= AUCTION_TRACK_SIZE) return 0;
    gs->auction_track[gs->auction_count++] = tile;
    return 1;
}

// 觸發與初始化競標狀態機
// is_forced: 0 代表抽到Ra或主動喊Ra；1 代表因格子滿了被動強制觸發
void conduct_auction(GameState* gs, int trigger_player, int is_forced) {
    printf("🔥 競標狀態機啟動！拍賣區：%d 張牌\n", gs->auction_count);
    
    gs->auction_active = 1;
    gs->highest_bid = 0;
    gs->highest_bidder = -1;
    gs->auction_trigger_player = trigger_player;
    
    // 由發起人的下一位玩家開始出價
    gs->current_bidder = (trigger_player + 1) % gs->num_players;
    
    // 尋找第一個有籌碼的合法出價者
    int loop_count = 0;
    while (!has_available_suns(&gs->players[gs->current_bidder]) && loop_count < gs->num_players) {
        gs->current_bidder = (gs->current_bidder + 1) % gs->num_players;
        loop_count++;
    }
}

int is_epoch_over(GameState* gs) {
    return gs->sun_boat_position >= ra_track_max(gs->num_players);
}

// 結束時代與結算
void end_epoch(GameState* gs) {
    printf("====== 第 %d 時代結束 ======\n", gs->current_epoch);
    
    score_epoch(gs);

    gs->auction_count     = 0;
    gs->sun_boat_position = 0;
    gs->auction_active    = 0;

    // 將所有存活玩家的籌碼恢復為「未翻面（可用）」
    for (int p = 0; p < gs->num_players; p++) {
        for (int s = 0; s < 13; s++) {
            gs->players[p].sun_used[s] = 0;
        }
    }

    if (gs->current_epoch >= 3) {
        gs->game_over = 1;
        score_final(gs);
        printf("🏁 遊戲結束！\n");
    } else {
        gs->current_epoch++;
        printf("進入第 %d 時代！\n", gs->current_epoch);
    }
}

// 輪到下一位有籌碼的玩家抽牌/喊Ra
void next_player(GameState* gs) {
    if (gs->auction_active) return; // 競標中不透過此函式切換玩家

    int all_out = 1;
    for (int p = 0; p < gs->num_players; p++) {
        if (has_available_suns(&gs->players[p])) {
            all_out = 0;
            break;
        }
    }

    if (all_out) {
        printf("⚠️ 所有玩家均無可用籌碼！提前結束此時代。\n");
        end_epoch(gs);
        return;
    }

    int tries = 0;
    do {
        gs->current_player = (gs->current_player + 1) % gs->num_players;
        tries++;
        if (tries > gs->num_players) return; 
    } while (!has_available_suns(&gs->players[gs->current_player]));

    printf("輪到玩家 %d (擁有可用籌碼)\n", gs->current_player + 1);
}

// 獨立結算得標與籌碼交換（原 run_auction 內核優化版）
static void resolve_auction_win(GameState* gs, int winner_idx, int win_bid) {
    Player* winner = &gs->players[winner_idx];

    // 1. 發放拍賣區板塊，如果是災難立刻結算
    for (int i = 0; i < gs->auction_count; i++) {
        Tile tile = gs->auction_track[i];
        if (tile.type == TILE_DISASTER) {
            resolve_disaster_immediate(winner, tile.value);
        } else {
            winner->hand[winner->hand_count++] = tile;
        }
    }

    // 2. 進行中央與玩家的太陽籌碼交換，並翻面 (sun_used = 1)
    for (int s = 0; s < 13; s++) {
        if (winner->suns[s] == win_bid && winner->sun_used[s] == 0) {
            int temp = winner->suns[s];
            winner->suns[s] = gs->center_sun;
            winner->sun_used[s] = 1;
            gs->center_sun = temp;

            printf("🔄 籌碼交換：玩家 %d 用數字 [%d] 標走拍賣區，換回中央的 [%d] 籌碼並翻面。\n", 
                   winner_idx + 1, temp, winner->suns[s]);
            break;
        }
    }
    printf("🎉 競標勝者：玩家 %d，共得到 %d 張牌。\n", winner_idx + 1, gs->auction_count);
    
    gs->auction_count = 0;
    gs->auction_active = 0;
}

// 🎮 核心狀態機連動：供 Python GUI 逐次呼叫的出價函式
// sun_value: 玩家選擇出的籌碼數字，0 代表 Pass
// 返回值：1 = 整個競標結束有人得標, -1 = 整個競標結束且流標, 0 = 繼續輪到下一位玩家出價
int player_bid(GameState* gs, int player_idx, int sun_value) {
    if (!gs->auction_active) return -1;
    if (player_idx != gs->current_bidder) return 0; // 預防非當前回合玩家搶填

    // 1. 處理出價
    if (sun_value > 0) {
        if (sun_value > gs->highest_bid) {
            gs->highest_bid = sun_value;
            gs->highest_bidder = player_idx;
        }
    }

    // 2. 尋找下一位有資格出價的玩家
    int next_bidder = gs->current_bidder;
    int loop_count = 0;
    do {
        next_bidder = (next_bidder + 1) % gs->num_players;
        loop_count++;
    } while (!has_available_suns(&gs->players[next_bidder]) && loop_count < gs->num_players);

    gs->current_bidder = next_bidder;

    // 3. 判斷是否所有人都輪過一遍了（回到發起人的下一位，或者繞完一圈）
    // 當前競標手等於發起者，代表他是最後一個做決定的人，做完就該結算
    if (player_idx == gs->auction_trigger_player) {
        if (gs->highest_bidder != -1) {
            // 有人得標，執行結算
            resolve_auction_win(gs, gs->highest_bidder, gs->highest_bid);
            return 1;
        } else {
            // 全員 Pass 流標
            printf("❌ 沒有人出價，拍賣區清空（流標）。\n");
            gs->auction_count = 0; // 依原作流標時拍賣區清空
            gs->auction_active = 0;
            return -1;
        }
    }

    return 0; // 競標尚未結束，繼續等下一個玩家輸入
}

// 保留你原本的一次性測試函式，避免你其他測試檔報錯
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
        resolve_auction_win(gs, best_player, best_bid);
    } else {
        printf("沒有人出價，拍賣區清空（流標）。\n");
        gs->auction_count = 0;
        gs->auction_active = 0;
    }
    return best_player;
}