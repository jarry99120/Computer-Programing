// scoring.c 最頂端
#include "game.h"     // 💡 一樣先引入核心結構，確保看得見 GameState 的手牌與分數！
#include "scoring.h"  // 再引入計分模組
#include <stdio.h>
#include <string.h>

// 內部輔助函式：計算某種板塊的數量
static int count_type(Player* p, TileType type) {
    int cnt = 0;
    for (int i = 0; i < p->hand_count; i++)
        if (p->hand[i].type == type) cnt++;
    return cnt;
}

// 內部輔助函式：計算文明牌有幾種不重複的類型
static int count_civ_types(Player* p) {
    int seen[5] = {0};
    for (int i = 0; i < p->hand_count; i++)
        if (p->hand[i].type == TILE_CIVILIZATION)
            seen[p->hand[i].value % 5] = 1;
    int total = 0;
    for (int i = 0; i < 5; i++) total += seen[i];
    return total;
}

// 內部輔助函式：棄置某一種類型的板塊（清除過期板塊用）
static void discard_type(Player* p, TileType type) {
    int new_count = 0;
    for (int i = 0; i < p->hand_count; i++)
        if (p->hand[i].type != type)
            p->hand[new_count++] = p->hand[i];
    p->hand_count = new_count;
}

// 災難板塊立即結算：扣除 2 張對應牌
void resolve_disaster_immediate(Player* p, int disaster_value) {
    int target_type = -1;
    if (disaster_value == 0)      target_type = TILE_NILE;
    else if (disaster_value == 1) target_type = TILE_PHARAOH;
    else if (disaster_value == 2) target_type = TILE_GOD;
    else if (disaster_value == 3) target_type = TILE_CIVILIZATION;

    if (target_type == -1) return;

    int removed = 0;

    // 先扣除主要目標類型
    for (int i = p->hand_count - 1; i >= 0 && removed < 2; i--) {
        if (p->hand[i].type == target_type) {
            p->hand[i] = p->hand[p->hand_count - 1];
            p->hand_count--;
            removed++;
        }
    }

    // 如果是尼羅河災難（值為0）且主要牌不夠扣，則由「洪水牌」代扣
    if (target_type == TILE_NILE && removed < 2) {
        for (int i = p->hand_count - 1; i >= 0 && removed < 2; i--) {
            if (p->hand[i].type == TILE_FLOOD) {
                p->hand[i] = p->hand[p->hand_count - 1];
                p->hand_count--;
                removed++;
            }
        }
    }
    printf("💥 [災難結算] 玩家 %d 被迫棄置了 %d 張對應的發展板塊。\n", p->player_id + 1, removed);
}

// 時代結束計分（第 1, 2, 3 時代結束都會觸發）
void score_epoch(GameState* gs) {
    int n = gs->num_players;
    printf("\n====== 第 %d 時代計分 ======\n", gs->current_epoch);

    // 1. 法老王結算（多+5，少-2）
    int pharaoh[5] = {0};
    int max_p = -1, min_p = 999;
    for (int i = 0; i < n; i++) {
        pharaoh[i] = count_type(&gs->players[i], TILE_PHARAOH);
        if (pharaoh[i] > max_p) max_p = pharaoh[i];
        if (pharaoh[i] < min_p) min_p = pharaoh[i];
    }
    if (max_p != min_p) {
        for (int i = 0; i < n; i++) {
            if (pharaoh[i] == max_p) { gs->players[i].score += 5;  printf("  玩家%d 法老最多(%d張) +5\n", i+1, pharaoh[i]); }
            if (pharaoh[i] == min_p) { gs->players[i].score -= 2;  printf("  玩家%d 法老最少(%d張) -2\n", i+1, pharaoh[i]); }
        }
    } else {
        printf("  法老牌全部相同，不計分\n");
    }

    // 2. 天神牌結算（每張 2 分，算完就棄置）
    for (int i = 0; i < n; i++) {
        int gods = count_type(&gs->players[i], TILE_GOD);
        if (gods > 0) {
            gs->players[i].score += gods * 2;
            printf("  玩家%d 神牌 %d 張 +%d\n", i+1, gods, gods*2);
            discard_type(&gs->players[i], TILE_GOD); // 天神不留到下一時代
        }
    }

    // 3. 金幣牌結算（每張 3 分，算完就棄置）
    for (int i = 0; i < n; i++) {
        int gold = count_type(&gs->players[i], TILE_GOLD);
        if (gold > 0) {
            gs->players[i].score += gold * 3;
            printf("  玩家%d 金牌 %d 張 +%d\n", i+1, gold, gold*3);
            discard_type(&gs->players[i], TILE_GOLD); // 金幣不留到下一時代
        }
    }

    // 4. 尼羅河與洪水結算（有洪水時，尼羅河與洪水每張各 1 分）
    for (int i = 0; i < n; i++) {
        int nile  = count_type(&gs->players[i], TILE_NILE);
        int flood = count_type(&gs->players[i], TILE_FLOOD);
        if (flood > 0) {
            int pts = nile + flood;
            gs->players[i].score += pts;
            printf("  玩家%d 尼羅%d+洪水%d = +%d\n", i+1, nile, flood, pts);
        } else {
            printf("  玩家%d 無洪水牌，尼羅河本輪不計分\n", i+1);
        }
        discard_type(&gs->players[i], TILE_FLOOD); // 💡 洪水一定要棄置，尼羅河會保留下來
    }

    // 5. 文明牌結算（根據不重複種類給分：0種-5分, 3種5分, 4種10分, 5種15分）
    for (int i = 0; i < n; i++) {
        int types = count_civ_types(&gs->players[i]);
        int pts = 0;
        if      (types == 0) pts = -5;
        else if (types == 3) pts =  5;
        else if (types == 4) pts = 10;
        else if (types == 5) pts = 15;
        gs->players[i].score += pts;
        printf("  玩家%d 文明 %d 種 %+d\n", i+1, types, pts);
        // 💡 修正：文明牌在真實遊戲中「不會被棄置」，會留到下一時代累積！所以拿掉 discard_type 呼叫。
    }

    printf("  ── 本時代結束後總分 ──\n");
    for (int i = 0; i < n; i++)
        printf("  玩家%d：%d 分\n", i+1, gs->players[i].score);
}

// 終局結算（第 3 時代結束 score_epoch 跑完後接著觸發）
void score_final(GameState* gs) {
    int n = gs->num_players;
    printf("\n====== 最終額外計分 ======\n");

    // 1. 金字塔（紀念碑）結算
    for (int i = 0; i < n; i++) {
        int counts[8] = {0};
        for (int j = 0; j < gs->players[i].hand_count; j++) {
            Tile t = gs->players[i].hand[j];
            if (t.type == TILE_PYRAMID)
                counts[t.value % 8]++;
        }

        // 多樣性計分（有幾種不同的金字塔）
        int diversity = 0;
        for (int k = 0; k < 8; k++) if (counts[k] > 0) diversity++;
        int div_pts = 0;
        if      (diversity == 8) div_pts = 15;
        else if (diversity == 7) div_pts = 10;
        else                     div_pts = diversity; // 1~6 種就是 1~6 分
        gs->players[i].score += div_pts;

        // 重複性計分（同一種收集了多張）
        int rep_pts = 0;
        for (int k = 0; k < 8; k++) {
            if      (counts[k] >= 5) rep_pts += 15;
            else if (counts[k] == 4) rep_pts += 10;
            else if (counts[k] == 3) rep_pts +=  5;
        }
        gs->players[i].score += rep_pts;
        printf("  玩家%d 紀念碑：多樣%d種+%d，重複+%d\n",
               i+1, diversity, div_pts, rep_pts);
    }

    // 2. 太陽籌碼總值結算（加總所有人籌碼，最高+5，最低-5）
    int sun_totals[5] = {0};
    int max_sun = -1, min_sun = 999999;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < 13; j++) {
            if (gs->players[i].suns[j] > 0) {
                sun_totals[i] += gs->players[i].suns[j];
            }
        }
        if (sun_totals[i] > max_sun) max_sun = sun_totals[i];
        if (sun_totals[i] < min_sun) min_sun = sun_totals[i];
    }

    if (max_sun != min_sun) {
        for (int i = 0; i < n; i++) {
            if (sun_totals[i] == max_sun) { gs->players[i].score += 5; printf("  玩家%d 太陽籌碼最高總值(%d) +5\n", i+1, max_sun); }
            if (sun_totals[i] == min_sun) { gs->players[i].score -= 5; printf("  玩家%d 太陽籌碼最低總值(%d) -5\n", i+1, min_sun); }
        }
    }

    // 3. 宣布贏家
    printf("\n====== 最終結果 ======\n");
    int winner = 0;
    for (int i = 0; i < n; i++) {
        printf("  玩家%d：%d 分\n", i+1, gs->players[i].score);
        if (gs->players[i].score > gs->players[winner].score) winner = i;
    }
    printf("  🎉 恭喜獲勝者：玩家%d！ 🎉\n", winner+1);
}