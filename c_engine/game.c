#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "game.h"
#include "scoring.h" // 完美串接時代結束(score_epoch)與終局(score_final)的計分模組

// =================================================================
// 📦 區塊一：核心基礎與輔助函式 (原 game_core.c 基礎部分)
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

// 遊戲初始化
void init_game(GameState* gs, int num_players) {
    // 1. 核心防禦：先把整個結構體的記憶體全部清空為 0，防止隨機垃圾值干擾狀態機
    memset(gs, 0, sizeof(GameState));

    // 人數安全限制 (德式標準 2~5 人局，預設 3 人)
    if (num_players < 2 || num_players > 5) {
        num_players = 3; 
    }
    gs->num_players = num_players;
    
    // 初始化全域基本遊戲狀態
    gs->current_epoch = 1;         // 起始時代為第 1 時代
    gs->sun_boat_position = 0;     // 太陽船歸零
    gs->auction_count = 0;         // 拍賣軌清空
    gs->game_over = 0;             // 遊戲未結束
    gs->auction_active = 0;        // 競標狀態機關閉

    // ==================== 📦 牌堆板塊填充 (共 180 張) ====================
    int deck_idx = 0;

    // A. 文明板塊 (Civilization) : 25個 (5種型號，各5張)
    for (int v = 1; v <= 5; v++) {
        for (int i = 0; i < 5; i++) {
            gs->deck[deck_idx].type = TILE_CIVILIZATION; // ID: 4
            gs->deck[deck_idx].value = v;
            deck_idx++;
        }
    }

    // B. 建築/金字塔板塊 (Pyramid) : 40個 (8種型號，各5張)
    for (int v = 1; v <= 8; v++) {
        for (int i = 0; i < 5; i++) {
            gs->deck[deck_idx].type = TILE_PYRAMID; // ID: 5
            gs->deck[deck_idx].value = v;
            deck_idx++;
        }
    }

    // C. 河流板塊 : 總計 37個
    // 尼羅河 (Nile) : 25個
    for (int i = 0; i < 25; i++) {
        gs->deck[deck_idx].type = TILE_NILE; // ID: 3
        gs->deck[deck_idx].value = 0;
        deck_idx++;
    }
    // 洪水 (Flood) : 12個
    for (int i = 0; i < 12; i++) {
        gs->deck[deck_idx].type = TILE_FLOOD; // ID: 8
        gs->deck[deck_idx].value = 0;
        deck_idx++;
    }

    // D. 法老板塊 (Pharaoh) : 25個
    for (int i = 0; i < 25; i++) {
        gs->deck[deck_idx].type = TILE_PHARAOH; // ID: 1
        gs->deck[deck_idx].value = 0;
        deck_idx++;
    }

    // E. 太陽神拉板塊 (Ra) : 30個
    for (int i = 0; i < 30; i++) {
        gs->deck[deck_idx].type = TILE_RA; // ID: 0
        gs->deck[deck_idx].value = 0;
        deck_idx++;
    }

    // F. 神明板塊 (God) : 8個
    for (int i = 0; i < 8; i++) {
        gs->deck[deck_idx].type = TILE_GOD; // ID: 6
        gs->deck[deck_idx].value = 0;
        deck_idx++;
    }

    // G. 黃金板塊 (Gold) : 5個
    for (int i = 0; i < 5; i++) {
        gs->deck[deck_idx].type = TILE_GOLD; // ID: 7
        gs->deck[deck_idx].value = 0;
        deck_idx++;
    }

    // H. 災難板塊 (Disaster) : 10個 (4種型號配比)
    int disaster_values[10] = {1, 1, 2, 2, 2, 3, 3, 4, 4, 4};
    for (int i = 0; i < 10; i++) {
        gs->deck[deck_idx].type = TILE_DISASTER; // ID: 2
        gs->deck[deck_idx].value = disaster_values[i];
        deck_idx++;
    }

    // 牌堆數量防禦檢查
    if (deck_idx != 180) {
        printf("[C Error] 警告！初始化牌堆總數為 %d，與預期的 180 張不符！\n", deck_idx);
    } else {
        printf("[C Core] 成功初始化自訂牌堆，總計共 %d 張板塊。\n", deck_idx);
    }
    gs->deck_size = deck_idx;

    // ==================== 🪙 玩家起始太陽籌碼官方設定集 ====================
    // 陣列維度：[人數局][玩家Index][籌碼槽]
    int starter_suns[6][5][13] = {
        { {0} }, // 0人局 (未使用)
        { {0} }, // 1人局 (未使用)
        { // 2人局
            {9, 11, 13, 15}, {8, 10, 12, 14}
        },
        { // 3人局 🎯 
            {2, 5, 8, 11},   {3, 6, 9, 12},   {4, 7, 10, 13}
        },
        { // 4人局
            {4, 7, 12},      {5, 6, 11},      {2, 9, 10},      {3, 8, 13}
        },
        { // 5人局
            {2, 11},         {3, 10},         {4, 9},          {5, 8},          {6, 7}
        }
    };

    // 根據官方规则設定「中央公共太陽」的初始值（3人與4人局起手皆為 1）
    gs->center_sun = 1; 

    // ==================== 👤 玩家個人資產槽初始化 ====================
    for (int p = 0; p < gs->num_players; p++) {
        gs->players[p].player_id = p; // 保持 0-based，與 Python 橋樑完美接軌
        gs->players[p].hand_count = 0;
        gs->players[p].score = 10;    // 依據 Ra 規則，起手發 10 分糖果籌碼，避免開局扣到負數

        // 將手牌槽全部清空初始化為 -1
        for (int h = 0; h < 50; h++) {
            gs->players[p].hand[h].type = -1;
            gs->players[p].hand[h].value = 0;
        }

        // 從設定集精準發放太陽籌碼
        int sun_count = 0;
        for (int s = 0; s < 13; s++) {
            int val = starter_suns[gs->num_players][p][s];
            if (val > 0) {
                gs->players[p].suns[sun_count] = val;
                gs->players[p].sun_used[sun_count] = 0; // 0 = 正面可用（未翻面鎖定）
                sun_count++;
            } else {
                gs->players[p].suns[s] = 0;
                gs->players[p].sun_used[s] = 0;
            }
        }
        printf("[C Core] 玩家 %d 初始化完畢，成功發放 %d 枚可用太陽籌碼。\n", p + 1, sun_count);
    }

    // 3. 最後進行全面洗牌，打亂 180 張板塊
    shuffle_deck(gs->deck, gs->deck_size);
    printf("[C Core] 核心初始隨機洗牌完成，遊戲準備就緒。\n");
}

// 抽牌核心邏輯
Tile draw_tile(GameState* gs) {
    Tile empty = {-1, 0};
    
    // 安全防禦：如果牌堆空了、遊戲結束了、或是競標中，不允許抽牌
    if (gs->deck_size <= 0 || gs->auction_active || gs->game_over) return empty;

    gs->deck_size--;
    Tile drawn = gs->deck[gs->deck_size];
    
    if (drawn.type == TILE_RA) {
        gs->sun_boat_position++;
        // 3人局上限是 8 格
        int max_track = ra_track_max(gs->num_players);
        if (max_track <= 0) max_track = 8; // 萬一讀到垃圾值的防呆基準線

        if (gs->sun_boat_position >= max_track) {
            printf("[C Core] 太陽船達到上限 (%d/%d)，觸發時代結束！\n", gs->sun_boat_position, max_track);
            end_epoch(gs);
        } else {
            conduct_auction(gs, gs->current_player, 0); 
        }
    } else {
        if (gs->auction_count < AUCTION_TRACK_SIZE) {
            gs->auction_track[gs->auction_count++] = drawn;
        }
        
        // 滿 8 格觸發強制競標
        if (gs->auction_count >= AUCTION_TRACK_SIZE) {
            printf("[C Core] 拍賣軌滿 8 格，觸發強制競標！\n");
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
// 🔨 區塊二：德式競標狀態機核心 (原 game_auction.c 部分)
// =================================================================

// 啟動競標狀態機
void conduct_auction(GameState* gs, int trigger_player, int is_forced) {
    gs->auction_active = 1;
    gs->highest_bid = 0;
    gs->highest_bidder = -1;
    gs->auction_trigger_player = trigger_player;
    
    // 🎯 修正：在 game.h 中加一個變數（或借用現有未用欄位），這裡先將 8 格滿強制競標標記保存
    // 假設你在 game.h 的 GameState 有定義一個額外狀態，若無，我們可以使用一個獨立邏輯
    // 這裡我們暫時借用 trigger_player 的特殊標記，或者用全新安全計數器。
    
    // 拍賣順序：從觸發者的下一位玩家開始
    gs->current_bidder = (trigger_player + 1) % gs->num_players;
    
    // 🎯 修正 1 的輔助：如果下一位沒籌碼，自動跳到下一個，直到所有人找過一輪
    int loop_count = 0;
    while (!has_available_suns(&gs->players[gs->current_bidder]) && loop_count < gs->num_players) {
        gs->current_bidder = (gs->current_bidder + 1) % gs->num_players;
        loop_count++;
    }
}

// 逐次接收並處理各玩家在拍賣彈窗中的出價
int player_bid(GameState* gs, int player_idx, int sun_value) {
    if (!gs->auction_active || player_idx != gs->current_bidder) return 0; 

    // 有效出價紀錄
    if (sun_value > 0 && sun_value > gs->highest_bid) {
        gs->highest_bid = sun_value;
        gs->highest_bidder = player_idx;
    }

    // 尋找下一個有籌碼的出價者
    int next_bidder = gs->current_bidder;
    int loop_count = 0;
    do {
        next_bidder = (next_bidder + 1) % gs->num_players;
        loop_count++;
    } while (!has_available_suns(&gs->players[next_bidder]) && loop_count < gs->num_players);

    // 🎯 修正 1：改用完美的「剩餘表態人數計數」來判斷是否整圈出價結束
    // 當前出價者已經是最後一個有籌碼的人，或者次位輪替回到了起點，代表出價圈結束！
    if (next_bidder == (gs->auction_trigger_player + 1) % gs->num_players || loop_count >= gs->num_players) {
        if (gs->highest_bidder != -1) {
            resolve_auction_win(gs, gs->highest_bidder, gs->highest_bid);
            return 1; // 有人得標
        } else {
            // 🎯 修正 2：全體 PASS 流標處理 (完美區分強制滿格流標與主動流標)
            // 依據 Ra 桌遊官方規則：若因8格全滿強制拍賣且全員流標，拍賣區「必須全部清空移出遊戲」
            if (gs->auction_count >= AUCTION_TRACK_SIZE) {
                gs->auction_count = 0; 
            }
            gs->auction_active = 0;
            next_player(gs);
            return -1; // 全員流標
        }
    }

    gs->current_bidder = next_bidder;
    return 0; // 繼續等待下一位出價
}

// 舊版一次性打包出價之相容介面
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
        if (gs->auction_count >= AUCTION_TRACK_SIZE) gs->auction_count = 0;
        gs->auction_active = 0;
        next_player(gs);
    }
    return winner_idx;
}


// =================================================================
// ⏳ 區塊三：時代推進判斷 (原 game_epoch.c 部分)
// =================================================================

int is_epoch_over(GameState* gs) {
    int maxes[] = {0, 0, 6, 8, 9, 10};
    return gs->sun_boat_position >= maxes[gs->num_players];
}

// 結束當前時代並進行清算
void end_epoch(GameState* gs) {
    // 預防性防禦：如果時代數值已經不正常，強制修正
    if (gs->current_epoch < 1) gs->current_epoch = 1;
    
    printf("====== 第 %d 時代結束結算 ======\n", gs->current_epoch);
    
    score_epoch(gs); // 呼叫計分模組

    // 重置時代變數
    gs->auction_count     = 0;
    gs->sun_boat_position = 0;
    gs->auction_active    = 0;

    // 時代更換，所有人的籌碼解除鎖定
    for (int p = 0; p < gs->num_players; p++) {
        for (int s = 0; s < 13; s++) {
            gs->players[p].sun_used[s] = 0; 
        }
    }

    // 🎯 修正：Ra 的時代是第 1 時代、第 2 時代、第 3 時代。
    // 當第 3 時代結束時，遊戲正式終結。
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
// 🌋 區塊四：拍賣池拾取與災難處理 (原 game_resolution.c 部分)
// =================================================================

// 結算得標並執行中央籌碼互換
void resolve_auction_win(GameState* gs, int winner_idx, int win_bid) {
    Player* winner = &gs->players[winner_idx];

    // 1. 發放拍賣區板塊與災難立即扣除
    for (int i = 0; i < gs->auction_count; i++) {
        Tile tile = gs->auction_track[i];
        if (tile.type == TILE_DISASTER) {
            resolve_disaster_immediate(winner, tile.value);
        } else {
            winner->hand[winner->hand_count++] = tile;
        }
    }

    // 2. 🎯 核心互換規則：尋找對應籌碼，與中央 center_sun 交換並標記 sun_used = 1
    for (int s = 0; s < 13; s++) {
        if (winner->suns[s] == win_bid && winner->sun_used[s] == 0) {
            int temp = winner->suns[s];
            winner->suns[s] = gs->center_sun; // 拿回中央公共太陽舊籌碼
            winner->sun_used[s] = 1;          // 💡 翻面鎖定！當前時代不能再使用
            gs->center_sun = temp;            // 得標出的籌碼變成新中央公共太陽
            break;
        }
    }
    
    // 3. 得標者接續主回合動作
    gs->current_player = winner_idx;
    gs->auction_count = 0;
    gs->auction_active = 0;

    // 防呆：如果剛好把最後一枚籌碼用完了，主回合移交給下一位有籌碼的人
    if (!has_available_suns(&gs->players[gs->current_player])) {
        next_player(gs);
    }
}