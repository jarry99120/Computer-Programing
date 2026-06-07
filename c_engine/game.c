#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "game.h"
#include "scoring.h"

// =================================================================
// 📦 區塊一：核心基礎與輔助函式
// =================================================================

// 內部輔助函式：檢查玩家是否有可用（未翻面鎖定）的籌碼
int has_available_suns(Player* p) {
    for (int i = 0; i < 13; i++) {
        if (p->suns[i] > 0 && p->sun_used[i] == 0) {
            return 1; 
        }
    }
    return 0;
}

// 輔助洗牌函式：Fisher-Yates Shuffle
void shuffle_deck(Tile *deck, int size) {
    for (int i = size - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        
        // 分開交換 type
        TileType temp_type = deck[i].type;
        deck[i].type = deck[j].type;
        deck[j].type = temp_type;

        // 分開交換 value
        int temp_val = deck[i].value;
        deck[i].value = deck[j].value;
        deck[j].value = temp_val;
    }
}

// 取得不同人數下的太陽船軌道上限
static int ra_track_max(int num_players) {
    int maxes[] = {0, 0, 6, 8, 9, 10};
    return maxes[num_players];
}

// 遊戲初始化
void init_game(GameState* gs, int num_players) {
    memset(gs, 0, sizeof(GameState));
    srand((unsigned int)time(NULL));
    if (num_players < 2 || num_players > 5) {
        num_players = 3; 
    }
    gs->num_players = num_players;
    
    gs->current_epoch = 1;         
    gs->sun_boat_position = 0;     
    gs->auction_count = 0;         
    gs->game_over = 0;             
    gs->auction_active = 0;        

    int deck_idx = 0;

    // A. 文明板塊 (Civilization) : 25個
    for (int v = 1; v <= 5; v++) {
        for (int i = 0; i < 5; i++) {
            gs->deck[deck_idx].type = TILE_CIVILIZATION; 
            gs->deck[deck_idx].value = v;
            deck_idx++;
        }
    }

    // B. 建築/金字塔板塊 (Pyramid) : 40個
    for (int v = 1; v <= 8; v++) {
        for (int i = 0; i < 5; i++) {
            gs->deck[deck_idx].type = TILE_PYRAMID; 
            gs->deck[deck_idx].value = v;
            deck_idx++;
        }
    }

    // C. 河流板塊 : 總計 37個
    for (int i = 0; i < 25; i++) {
        gs->deck[deck_idx].type = TILE_NILE; 
            gs->deck[deck_idx].value = 1;
        deck_idx++;
    }
    for (int i = 0; i < 12; i++) {
        gs->deck[deck_idx].type = TILE_FLOOD; 
        gs->deck[deck_idx].value = 1;
        deck_idx++;
    }

    // E. 法老板塊 (Pharaoh) : 25個
    for (int i = 0; i < 25; i++) {
        gs->deck[deck_idx].type = TILE_PHARAOH; 
        gs->deck[deck_idx].value = 1;
        deck_idx++;
    }

    // F. 太陽神拉板塊 (Ra) : 30個
    for (int i = 0; i < 30; i++) {
        gs->deck[deck_idx].type = TILE_RA; 
        gs->deck[deck_idx].value = 1;
        deck_idx++;
    }

    // G. 神明板塊 (God) : 8個
    for (int i = 0; i < 8; i++) {
        gs->deck[deck_idx].type = TILE_GOD; 
        gs->deck[deck_idx].value = 1;
        deck_idx++;
    }

    // H. 黃金板塊 (Gold) : 5個
    for (int i = 0; i < 5; i++) {
        gs->deck[deck_idx].type = TILE_GOLD; 
        gs->deck[deck_idx].value = 1;
        deck_idx++;
    }

    // I. 災難板塊 (Disaster) : 10個
    int disaster_values[10] = {1, 1, 2, 2, 2, 3, 3, 4, 4, 4};
    for (int i = 0; i < 10; i++) {
        gs->deck[deck_idx].type = TILE_DISASTER; 
        gs->deck[deck_idx].value = disaster_values[i];
        deck_idx++;
    }

    gs->deck_size = deck_idx;

    int starter_suns[6][5][13] = {
        { {0} }, { {0} }, 
        { {9, 11, 13, 15}, {8, 10, 12, 14} },
        { {2, 5, 8, 11},   {3, 6, 9, 12},   {4, 7, 10, 13} },
        { {4, 7, 12},      {5, 6, 11},      {2, 9, 10},      {3, 8, 13} },
        { {2, 11},         {3, 10},         {4, 9},          {5, 8},          {6, 7} }
    };

    gs->center_sun = 1; 

    for (int p = 0; p < gs->num_players; p++) {
        gs->players[p].player_id = p; 
        gs->players[p].hand_count = 0;
        gs->players[p].score = 10;    

        for (int h = 0; h < 50; h++) {
            gs->players[p].hand[h].type = -1;
            gs->players[p].hand[h].value = 1;
        }

        int sun_count = 0;
        for (int s = 0; s < 13; s++) {
            int val = starter_suns[gs->num_players][p][s];
            if (val > 0) {
                gs->players[p].suns[sun_count] = val;
                gs->players[p].sun_used[sun_count] = 0; 
                sun_count++;
            } else {
                gs->players[p].suns[s] = 0;
                gs->players[p].sun_used[s] = 0;
            }
        }
    }
    
    shuffle_deck(gs->deck, gs->deck_size);
}

// 抽牌核心邏輯
Tile draw_tile(GameState* gs) {
    Tile empty = {-1, 1};
    
    if (gs->deck_size <= 0 || gs->auction_active || gs->game_over) return empty;

    gs->deck_size--;
    Tile drawn = gs->deck[gs->deck_size];
    
    if (drawn.type == TILE_RA) {
        gs->sun_boat_position++;
        int max_track = ra_track_max(gs->num_players);
        if (max_track <= 0) max_track = 8; 

        if (gs->sun_boat_position >= max_track) {
            printf("[C Core] 太陽船達到上限，觸發時代結束！\n");
            end_epoch(gs);
        } else {
            conduct_auction(gs, gs->current_player, 1); 
        }
    } else {
        if (gs->auction_count < AUCTION_TRACK_SIZE) {
            gs->auction_track[gs->auction_count++] = drawn;
        }
        
        if (gs->auction_count >= AUCTION_TRACK_SIZE) {
            printf("[C Core] 拍賣軌滿 8 格，觸發強制競標！\n");
            conduct_auction(gs, gs->current_player, 2); 
        }
    }
    return drawn;
}

int add_to_auction(GameState* gs, Tile tile) {
    if (gs->auction_count >= AUCTION_TRACK_SIZE) return 0;
    gs->auction_track[gs->auction_count++] = tile;
    return 1;
}

// 輪替到下一位有可用籌碼的玩家
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
        end_epoch(gs);
        return;
    }

    int tries = 0;
    do {
        gs->current_player = (gs->current_player + 1) % gs->num_players;
        tries++;
        if (tries > gs->num_players) return; 
    } while (!has_available_suns(&gs->players[gs->current_player]));
}


// =================================================================
// 🔨 區塊二：德式競標狀態機核心（流標全面清空版）
// =================================================================

void conduct_auction(GameState* gs, int trigger_player, int is_forced) {
    if (is_forced == 0) {
        gs->auction_active = 1; 
    } else if (is_forced == 1) {
        gs->auction_active = 2; 
    } else {
        gs->auction_active = 3; 
    }

    gs->highest_bid = 0;
    gs->highest_bidder = -1;
    gs->auction_trigger_player = trigger_player;

    if (gs->auction_active == 3) {
        gs->current_bidder = trigger_player;
    } else {
        gs->current_bidder = (trigger_player + 1) % gs->num_players;
    }
    
    int loop_count = 0;
    while (!has_available_suns(&gs->players[gs->current_bidder]) && loop_count < gs->num_players) {
        gs->current_bidder = (gs->current_bidder + 1) % gs->num_players;
        loop_count++;
    }
}

int player_bid(GameState* gs, int player_idx, int sun_value) {
    if (gs->auction_active == 0 || player_idx != gs->current_bidder) return 0; 

    // 主動喊拉發起人保底吞牌機制 (gs->auction_active == 1)
    if (gs->auction_active == 1 && gs->highest_bidder == -1 && player_idx == gs->auction_trigger_player) {
        if (sun_value <= 0) {
            int min_sun = 999;
            for (int i = 0; i < 13; i++) {
                if (gs->players[player_idx].suns[i] > 0 && gs->players[player_idx].sun_used[i] == 0) {
                    if (gs->players[player_idx].suns[i] < min_sun) {
                        min_sun = gs->players[player_idx].suns[i];
                    }
                }
            }
            sun_value = min_sun; 
        }
    }

    // 記錄有效出價
    if (sun_value > 0 && sun_value > gs->highest_bid) {
        gs->highest_bid = sun_value;
        gs->highest_bidder = player_idx;
    }

    // 尋找下一位「有可用籌碼」的玩家
    int next_bidder = gs->current_bidder;
    int search_count = 0;
    do {
        next_bidder = (next_bidder + 1) % gs->num_players;
        search_count++;
    } while (!has_available_suns(&gs->players[next_bidder]) && search_count <= gs->num_players);

    // 計算出價起點並進行無籌碼跳過校正
    int first_bidder = (gs->auction_active == 3) ? gs->auction_trigger_player : (gs->auction_trigger_player + 1) % gs->num_players;
    int fix_loop = 0;
    while (!has_available_suns(&gs->players[first_bidder]) && fix_loop <= gs->num_players) {
        first_bidder = (first_bidder + 1) % gs->num_players;
        fix_loop++;
    }

    // 當出價繞完一圈表態完畢
    if (next_bidder == first_bidder || search_count >= gs->num_players) {
        
        // 狀況 A：有人得標
        if (gs->highest_bidder != -1) {
            resolve_auction_win(gs, gs->highest_bidder, gs->highest_bid);
            return 1; 
        } 
        // 狀況 B：全員 PASS 流標！
        else {
            // 🎯【規則大對齊】：只要沒人出價，不管有沒有滿 8 格，場上板塊一律清空！
            printf("[C Core] 競標全員 PASS 流標！清空拍賣軌所有板塊（原數量: %d）。\n", gs->auction_count);
            gs->auction_count = 0; 
            
            gs->auction_active = 0; 
            
            if (!has_available_suns(&gs->players[gs->current_player])) {
                next_player(gs);
            }
            return -1; 
        }
    }

    gs->current_bidder = next_bidder;
    return 0; 
}

int run_auction(GameState* gs, int *bids, int bids_count) {
    int highest_bid = 0, winner_idx = -1;
    for (int i = 0; i < bids_count; i++) {
        if (bids[i] > highest_bid) {
            highest_bid = bids[i];
            winner_idx = i;
        }
    }
    if (winner_idx >= 0) {
        resolve_auction_win(gs, winner_idx, highest_bid);
    } else {
        gs->auction_count = 0; // 同步防禦清空
        gs->auction_active = 0;
        next_player(gs);
    }
    return winner_idx;
}


// =================================================================
// ⏳ 區塊三：時代推進判斷
// =================================================================

int is_epoch_over(GameState* gs) {
    int maxes[] = {0, 0, 6, 8, 9, 10};
    return gs->sun_boat_position >= maxes[gs->num_players];
}

void end_epoch(GameState* gs) {
    if (gs->current_epoch < 1) gs->current_epoch = 1;
    
    printf("====== 第 %d 時代結束結算 ======\n", gs->current_epoch);
    score_epoch(gs); 

    gs->auction_count     = 0;
    gs->sun_boat_position = 0;
    gs->auction_active    = 0;

    for (int p = 0; p < gs->num_players; p++) {
        for (int s = 0; s < 13; s++) {
            gs->players[p].sun_used[s] = 0; 
        }
    }

    if (gs->current_epoch >= 3) {
        printf("====== 三個時代已全部結束，進入終局總計分 ======\n");
        gs->game_over = 1;
        score_final(gs); 
    } else {
        gs->current_epoch++;
        printf("[C Core] 時代推進成功，目前進入第 %d 時代。\n", gs->current_epoch);
    }
}


// =================================================================
// 🌋 區塊四：拍賣池拾取與災難處理
// =================================================================

void resolve_auction_win(GameState* gs, int winner_idx, int win_bid) {
    Player* winner = &gs->players[winner_idx];

    for (int i = 0; i < gs->auction_count; i++) {
        Tile tile = gs->auction_track[i];
        if (tile.type == TILE_DISASTER) {
            resolve_disaster_immediate(winner, tile.value);
        } else {
            if (winner->hand_count < 50) {
                winner->hand[winner->hand_count++] = tile;
            } else {
                printf("[C Warning] 玩家 %d 手牌空間已滿(50)，板塊遭強制遺棄！\n", winner_idx + 1);
            }
        }
    }

    for (int s = 0; s < 13; s++) {
        if (winner->suns[s] == win_bid && winner->sun_used[s] == 0) {
            int temp = winner->suns[s];
            winner->suns[s] = gs->center_sun; 
            winner->sun_used[s] = 1;          
            gs->center_sun = temp;            
            break;
        }
    }
    
    gs->current_player = winner_idx;
    gs->auction_count = 0;
    gs->auction_active = 0; 

    if (!has_available_suns(&gs->players[gs->current_player])) {
        next_player(gs);
    }
}

// =================================================================
// 👑 新增區塊五：神明板塊特殊行動（精準一換一對齊版）
// =================================================================

/**
 * 玩家執行「使用神明板塊」進行一對一精準換卡行動
 * @param track_index 玩家指定的拍賣軌格子索引 (0 ~ gs->auction_count-1)
 * 返回值: 1 : 執行成功 | 0 : 執行失敗
 */
int player_use_god_tile(GameState* gs, int player_idx, int track_index) {
    // 防禦 A：基本狀態與競標程序校驗
    if (gs->game_over || gs->auction_active) {
        printf("[C Core] 錯誤：目前遊戲狀態不允許執行神明行動。\n");
        return 0;
    }

    // 防禦 B：回合校驗
    if (player_idx != gs->current_player) {
        printf("[C Core] 錯誤：非玩家 %d 的回合，無法執行行動。\n", player_idx + 1);
        return 0;
    }

    // 防禦 C：指定索引範圍校驗
    if (track_index < 0 || track_index >= gs->auction_count) {
        printf("[C Core] 錯誤：無效的拍賣軌索引 %d。\n", track_index);
        return 0;
    }

    Player* p = &gs->players[player_idx];

    // 防禦 D：檢查玩家手牌中是否真的持有神明板塊 (TILE_GOD)
    int god_tile_idx = -1;
    for (int i = 0; i < p->hand_count; i++) {
        if (p->hand[i].type == TILE_GOD) {
            god_tile_idx = i;
            break;
        }
    }

    if (god_tile_idx == -1) {
        printf("[C Core] 錯誤：玩家 %d 手中沒有神明板塊，拒絕行動。\n", player_idx + 1);
        return 0;
    }

    // 🎯 核心邏輯 1：取得目標板塊
    Tile target_tile = gs->auction_track[track_index];
    printf("[C Core] 玩家 %d 使用神明挑選了板塊: %d (Value: %d)\n", player_idx + 1, target_tile.type, target_tile.value);

    // 🎯 核心邏輯 2：扣除並「永久捨棄」玩家手牌中的該張神明板塊
    for (int i = god_tile_idx; i < p->hand_count - 1; i++) {
        p->hand[i] = p->hand[i + 1];
    }
    p->hand_count--;

    // 🎯 核心邏輯 3：將目標板塊移入玩家手牌 (若是災難則立刻結算)
    if (target_tile.type == TILE_DISASTER) {
        resolve_disaster_immediate(p, target_tile.value);
    } else {
        if (p->hand_count < 50) {
            p->hand[p->hand_count++] = target_tile;
        } else {
            printf("[C Warning] 玩家 %d 手牌已滿，換回的板塊遭強制遺棄！\n", player_idx + 1);
        }
    }

    // 🎯 核心邏輯 4：維護拍賣軌連續性，移出被拿走的卡片，後方卡片依序往前遞補
    for (int i = track_index; i < gs->auction_count - 1; i++) {
        gs->auction_track[i] = gs->auction_track[i + 1];
    }
    gs->auction_count--;

    // 將移出後的最後一格清空防呆
    gs->auction_track[gs->auction_count].type = -1;
    gs->auction_track[gs->auction_count].value = 0;

    printf("[C Core] 神明交換成功，拍賣軌目前剩餘數量: %d。\n", gs->auction_count);

    // 🎯 核心邏輯 5：行動結束，將回合移交給下一位有效玩家
    next_player(gs);

    return 1;
}