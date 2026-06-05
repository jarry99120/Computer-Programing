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

// 輔助洗牌函式：將袋子裡的板塊隨機打亂 (Fisher-Yates Shuffle)
void shuffle_deck(Tile *deck, int size) {
    for (int i = size - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        Tile temp = deck[i];
        deck[i] = deck[j];
        deck[j] = temp;
    }
}

// 取得不同人數下的太陽船軌道上限
static int ra_track_max(int num_players) {
    int maxes[] = {0, 0, 6, 8, 9, 10};
    return maxes[num_players];
}

// 完整的遊戲初始化函式 (嚴格對齊官方規則)
void init_game(GameState *gs, int num_players) {
    // 安全防呆：限制人數在 2 到 5 人之間
    if (num_players < 2 || num_players > 5) {
        num_players = 4; 
    }

    // 1. 初始化基礎全域遊戲狀態
    gs->num_players = num_players;
    gs->current_epoch = 1;          // 從第 1 時代開始
    gs->sun_boat_position = 0;      // 太陽船軌道歸零
    gs->auction_count = 0;          // 拍賣區初始空無一物
    gs->auction_active = 0;         // 初始非競標狀態
    gs->game_over = 0;              // 遊戲未結束
    
    // 官方規則：1 號太陽籌碼初始放在桌面中央作為公共籌碼
    gs->center_sun = 1;

    // 2. 初始化所有玩家的基礎數值
    for (int i = 0; i < 5; i++) {
        gs->players[i].player_id = i;
        gs->players[i].hand_count = 0;
        gs->players[i].score = 5;    // 💡 官方規則：每位玩家起手發予 5 分
        
        // 清空手牌與籌碼槽
        for (int j = 0; j < 50; j++) {
            gs->players[i].hand[j].type = -1;
            gs->players[i].hand[j].value = 0;
        }
        for (int j = 0; j < 13; j++) {
            gs->players[i].suns[j] = 0;
            gs->players[i].sun_used[j] = 0;
        }
    }

    // 3. 🎯 嚴格遵循官方設定，依人數指派太陽籌碼
    if (num_players == 3) {
        int suns_3p[3][4] = {
            {2, 5, 8, 13},   // 玩家 A (Index 0)
            {3, 6, 9, 12},   // 玩家 B (Index 1)
            {4, 7, 10, 11}   // 玩家 C (Index 2)
        };
        for (int p = 0; p < 3; p++) {
            for (int s = 0; s < 4; s++) {
                gs->players[p].suns[s] = suns_3p[p][s];
            }
        }
    } 
    else if (num_players == 4) {
        int suns_4p[4][3] = {
            {2, 6, 13},      // 玩家 A
            {3, 7, 12},      // 玩家 B
            {4, 8, 11},      // 玩家 C
            {5, 9, 10}       // 玩家 D
        };
        for (int p = 0; p < 4; p++) {
            for (int s = 0; s < 3; s++) {
                gs->players[p].suns[s] = suns_4p[p][s];
            }
        }
    } 
    else if (num_players == 5) {
        int suns_5p[5][3] = {
            {2, 7, 16},      // 玩家 A
            {3, 8, 15},      // 玩家 B
            {4, 9, 14},      // 玩家 C
            {5, 10, 13},     // 玩家 D
            {6, 11, 12}      // 玩家 E
        };
        for (int p = 0; p < 5; p++) {
            for (int s = 0; s < 3; s++) {
                gs->players[p].suns[s] = suns_5p[p][s];
            }
        }
    }
    else if (num_players == 2) {
        int suns_2p[2][4] = {{2, 4, 6, 8}, {3, 5, 7, 9}};
        for (int p = 0; p < 2; p++) {
            for (int s = 0; s < 4; s++) gs->players[p].suns[s] = suns_2p[p][s];
        }
    }

    // 4. 🎯 尋找全場擁有最大太陽籌碼的玩家，作為起手玩家
    int max_sun_val = -1;
    int starting_player = 0;

    for (int p = 0; p < num_players; p++) {
        for (int s = 0; s < 13; s++) {
            if (gs->players[p].suns[s] > max_sun_val) {
                max_sun_val = gs->players[p].suns[s];
                starting_player = p;
            }
        }
    }
    gs->current_player = starting_player; // 💡 鎖定由他開始第一回合

    // 5. 📦 建立牌組袋子 (Deck) 並放入所有官方常規板塊
    int idx = 0;

    // (A) 放入 30 張太陽神 Ra 板塊
    for (int i = 0; i < 30; i++) { gs->deck[idx].type = TILE_RA; gs->deck[idx].value = 0; idx++; }
    // (B) 放入 25 張法老板塊 (Pharaoh)
    for (int i = 0; i < 25; i++) { gs->deck[idx].type = TILE_PHARAOH; gs->deck[idx].value = 0; idx++; }
    // (C) 放入 16 張金字塔板塊 (Pyramid)
    for (int i = 0; i < 16; i++) { gs->deck[idx].type = TILE_PYRAMID; gs->deck[idx].value = i % 8; idx++; }
    // (D) 放入 12 張金幣板塊 (Gold)
    for (int i = 0; i < 12; i++) { gs->deck[idx].type = TILE_GOLD; gs->deck[idx].value = 0; idx++; }
    // (E) 放入 25 張尼羅河板塊 (Nile) 與 12 張洪水板塊 (Flood)
    for (int i = 0; i < 25; i++) { gs->deck[idx].type = TILE_NILE; gs->deck[idx].value = 0; idx++; }
    for (int i = 0; i < 12; i++) { gs->deck[idx].type = TILE_FLOOD; gs->deck[idx].value = 0; idx++; }
    // (F) 放入文明板塊 (Civilization) - 5 種不同類型各 5 張 = 25 張
    for (int type_val = 1; type_val <= 5; type_val++) {
        for (int i = 0; i < 5; i++) { gs->deck[idx].type = TILE_CIVILIZATION; gs->deck[idx].value = type_val; idx++; }
    }
    // (G) 放入 8 張阿努比斯神明板塊 (God)
    for (int i = 0; i < 8; i++) { gs->deck[idx].type = TILE_GOD; gs->deck[idx].value = 0; idx++; }
    // (H) 放入災難板塊 (Disaster) - 4 種災難各 2 張 = 8 張
    for (int dis_val = 1; dis_val <= 4; dis_val++) {
        for (int i = 0; i < 2; i++) { gs->deck[idx].type = TILE_DISASTER; gs->deck[idx].value = dis_val; idx++; }
    }

    gs->deck_size = idx; // 統計總板塊數

    // 6. 🎲 亂數洗牌
    shuffle_deck(gs->deck, gs->deck_size);
}

// 抽牌邏輯
Tile draw_tile(GameState* gs) {
    Tile empty = {-1, 0};
    if (gs->deck_size <= 0) return empty;
    if (gs->auction_active) return empty; // 競標中不允許抽牌

    gs->deck_size--;
    Tile drawn = gs->deck[gs->deck_size];
    
    if (drawn.type == TILE_RA) {
        gs->sun_boat_position++;
        printf("☀️  Ra 牌！Ra軌道：%d/%d\n",
               gs->sun_boat_position, ra_track_max(gs->num_players));
        
        if (gs->sun_boat_position >= ra_track_max(gs->num_players)) {
            end_epoch(gs);
        } else {
            // 抽到 Ra 牌，強制引發競標，類型標記為 0 (Ra 觸發)
            conduct_auction(gs, gs->current_player, 0); 
        }
    } else {
        if (gs->auction_count < AUCTION_TRACK_SIZE) {
            gs->auction_track[gs->auction_count++] = drawn;
            printf("✅ 抽到牌 type=%d，拍賣區：%d/8\n", drawn.type, gs->auction_count);
        }

        // 拍賣區滿 8 張，強制觸發競標，類型標記為 1 (8格滿強制)
        if (gs->auction_count >= AUCTION_TRACK_SIZE) {
            printf("📦 拍賣區已滿！強制競標！\n");
            conduct_auction(gs, gs->current_player, 1); 
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
// is_forced: 0 = 抽到Ra或主動喊Ra；1 = 8格滿被動強制觸發
void conduct_auction(GameState* gs, int trigger_player, int is_forced) {
    printf("🔥 競標狀態機啟動！原因代碼：%d | 拍賣區：%d 張牌\n", is_forced, gs->auction_count);
    
    gs->auction_active = 1;
    gs->highest_bid = 0;
    gs->highest_bidder = -1;
    gs->auction_trigger_player = trigger_player;
    gs->center_sun = is_forced; // 💡 巧妙利用原 center_sun 空間或保留此變數供 player_bid 區分流標類型

    // 由發起人的下一位玩家開始順時針出價
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

    // 將所有玩家的籌碼恢復為「未翻面（可用）」
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
    if (gs->auction_active) return; 

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

// 獨立結算得標與籌碼交換
static void resolve_auction_win(GameState* gs, int winner_idx, int win_bid) {
    Player* winner = &gs->players[winner_idx];

    // 1. 發放拍賣區板塊，如果是災難立刻扣除
    for (int i = 0; i < gs->auction_count; i++) {
        Tile tile = gs->auction_track[i];
        if (tile.type == TILE_DISASTER) {
            resolve_disaster_immediate(winner, tile.value);
        } else {
            winner->hand[winner->hand_count++] = tile;
        }
    }

    // 2. 🎯 核心修復：找到玩家出價的那枚籌碼，與中央交換並「翻面鎖定」
    for (int s = 0; s < 13; s++) {
        if (winner->suns[s] == win_bid && winner->sun_used[s] == 0) {
            int temp = winner->suns[s];
            winner->suns[s] = gs->center_sun;
            winner->sun_used[s] = 1; // 💡 標記為已使用，不再參與下一次競標！
            gs->center_sun = temp;

            printf("🔄 籌碼交換：玩家 %d 用數字 [%d] 標走，換回中央的舊籌碼 [%d] 並翻面朝下。\n", 
                   winner_idx + 1, temp, winner->suns[s]);
            break;
        }
    }
    printf("🎉 競標勝者：玩家 %d，共得到 %d 張牌。\n", winner_idx + 1, gs->auction_count);
    
    gs->auction_count = 0;
    gs->auction_active = 0;
}

// 🎮 核心狀態機連動：供 Web / Python GUI 逐次呼叫的出價函式
// sun_value: 玩家選擇出的籌碼數字，0 代表 Pass
// 返回值：1 = 有人得標, -1 = 全員流標結束, 0 = 繼續等待下一位玩家出價
int player_bid(GameState* gs, int player_idx, int sun_value) {
    if (!gs->auction_active) return -1;
    if (player_idx != gs->current_bidder) return 0; 

    // 1. 處理出價邏輯
    if (sun_value > 0) {
        if (sun_value > gs->highest_bid) {
            gs->highest_bid = sun_value;
            gs->highest_bidder = player_idx;
        }
    }

    // 2. 尋找下一位有資格（有剩餘籌碼）出價的玩家
    int next_bidder = gs->current_bidder;
    int loop_count = 0;
    do {
        next_bidder = (next_bidder + 1) % gs->num_players;
        loop_count++;
    } while (!has_available_suns(&gs->players[next_bidder]) && loop_count < gs->num_players);

    // 3. 🎯 判斷是否「整圈出價表態完畢」
    // 當 player_idx 等於觸發者的同一人時，代表順時針一圈回到尾家做完了終極決定
    if (player_idx == gs->auction_trigger_player) {
        if (gs->highest_bidder != -1) {
            // (A) 有人成功標到一池板塊
            resolve_auction_win(gs, gs->highest_bidder, gs->highest_bid);
            return 1;
        } else {
            // (B) 🎯 全員 PASS 流標：根據觸發原因執行分流
            // 這裡利用 conduct_auction 暫存的滿格標記做判斷
            if (gs->auction_count >= 8) {
                // 規則：如果是 8 格滿觸發流標 -> 拍賣區「全數移除」
                gs->auction_count = 0;
                printf("📦 規則生效：8 格滿強制競標流標，圖板板塊全數清空棄牌！\n");
            } else {
                // 規則：如果是抽到 Ra 牌觸發流標 -> 板塊「均原地保留」
                printf("☀️ 規則生效：Ra 板塊競標流標，圖板板塊原地留下。\n");
            }
            gs->auction_active = 0;
            return -1;
        }
    }

    // 回合尚未結束，指定下一位出價者
    gs->current_bidder = next_bidder;
    return 0; 
}

// 供一次性測試或舊版序列化維持相容的舊介面
int run_auction(GameState *gs, int *bids, int bids_count) {
    int highest_bid = 0;
    int winner_idx = -1;

    for (int i = 0; i < bids_count; i++) {
        if (bids[i] > highest_bid) {
            highest_bid = bids[i];
            winner_idx = i;
        }
    }

    if (winner_idx >= 0) {
        resolve_auction_win(gs, winner_idx, highest_bid);
    } else {
        if (gs->auction_count >= 8) {
            gs->auction_count = 0;
            printf("📦 8格滿流標：全數移除\n");
        } else {
            printf("☀️ Ra流標：全數保留\n");
        }
        gs->auction_active = 0;
    }
    return winner_idx;
}