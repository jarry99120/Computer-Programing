#include "scoring.h"
#include <stdio.h>
#include <string.h>

/* ── 工具：計算某玩家手牌中特定 type 的數量 ── */
static int count_type(Player* p, TileType type) {
    int cnt = 0;
    for (int i = 0; i < p->hand_count; i++)
        if (p->hand[i].type == type) cnt++;
    return cnt;
}

/* ── 工具：計算文明牌種類數（value 0~4 各算一種）── */
static int count_civ_types(Player* p) {
    int seen[5] = {0};
    for (int i = 0; i < p->hand_count; i++)
        if (p->hand[i].type == TILE_CIVILIZATION)
            seen[p->hand[i].value % 5] = 1;
    int total = 0;
    for (int i = 0; i < 5; i++) total += seen[i];
    return total;
}

/* ── 工具：移除手牌中所有特定 type 的牌 ── */
static void discard_type(Player* p, TileType type) {
    int new_count = 0;
    for (int i = 0; i < p->hand_count; i++)
        if (p->hand[i].type != type)
            p->hand[new_count++] = p->hand[i];
    p->hand_count = new_count;
}

/* ── 每個時代結束計分 ─────────────────────────── */
void score_epoch(GameState* gs) {
    int n = gs->num_players;
    printf("\n====== 第 %d 時代計分 ======\n", gs->current_epoch);

    /* 1. 法老牌：最多 +5，最少 -2（全部一樣則不計分） */
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

    /* 2. 神牌：每張 +2，之後丟棄 */
    for (int i = 0; i < n; i++) {
        int gods = count_type(&gs->players[i], TILE_GOD);
        if (gods > 0) {
            gs->players[i].score += gods * 2;
            printf("  玩家%d 神牌 %d 張 +%d\n", i+1, gods, gods*2);
            discard_type(&gs->players[i], TILE_GOD);
        }
    }

    /* 3. 金牌：每張 +3，之後丟棄 */
    for (int i = 0; i < n; i++) {
        int gold = count_type(&gs->players[i], TILE_GOLD);
        if (gold > 0) {
            gs->players[i].score += gold * 3;
            printf("  玩家%d 金牌 %d 張 +%d\n", i+1, gold, gold*3);
            discard_type(&gs->players[i], TILE_GOLD);
        }
    }

    /* 4. 尼羅河 + 洪水（有洪水才計分）*/
    for (int i = 0; i < n; i++) {
        int nile  = count_type(&gs->players[i], TILE_NILE);
        int flood = count_type(&gs->players[i], TILE_FLOOD);
        if (flood > 0) {
            int pts = nile + flood;
            gs->players[i].score += pts;
            printf("  玩家%d 尼羅%d+洪水%d = +%d\n", i+1, nile, flood, pts);
        } else {
            printf("  玩家%d 無洪水牌，尼羅河不計分\n", i+1);
        }
        discard_type(&gs->players[i], TILE_FLOOD);  /* 洪水牌丟棄，尼羅河保留 */
    }

    /* 5. 文明牌：依種類數計分，之後丟棄 */
    for (int i = 0; i < n; i++) {
        int types = count_civ_types(&gs->players[i]);
        int pts = 0;
        if      (types == 0) pts = -5;
        else if (types == 3) pts =  5;
        else if (types == 4) pts = 10;
        else if (types == 5) pts = 15;
        gs->players[i].score += pts;
        printf("  玩家%d 文明 %d 種 %+d\n", i+1, types, pts);
        discard_type(&gs->players[i], TILE_CIVILIZATION);
    }

    /* 印出本時代結果 */
    printf("  ── 本時代結束後分數 ──\n");
    for (int i = 0; i < n; i++)
        printf("  玩家%d：%d 分\n", i+1, gs->players[i].score);
}

/* ── 第3時代額外計分 ─────────────────────────── */
void score_final(GameState* gs) {
    int n = gs->num_players;
    printf("\n====== 最終額外計分 ======\n");

    /* 1. 紀念碑（TILE_PYRAMID，value 0~7 代表 8 種）*/
    for (int i = 0; i < n; i++) {
        int counts[8] = {0};
        for (int j = 0; j < gs->players[i].hand_count; j++) {
            Tile t = gs->players[i].hand[j];
            if (t.type == TILE_PYRAMID)
                counts[t.value % 8]++;
        }

        /* 多樣性（有幾種不同紀念碑）*/
        int diversity = 0;
        for (int k = 0; k < 8; k++) if (counts[k] > 0) diversity++;
        int div_pts = 0;
        if      (diversity == 8) div_pts = 15;
        else if (diversity == 7) div_pts = 10;
        else                     div_pts = diversity;
        gs->players[i].score += div_pts;

        /* 重複性（同種 3/4/5 張）*/
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

    /* 2. 太陽籌碼：總和最高 +5，最低 -5 */
    int sun_totals[5] = {0};
    int max_sun = -1, min_sun = 999999;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < 13; j++)
            sun_totals[i] += gs->players[i].suns[j];
        if (sun_totals[i] > max_sun) max_sun = sun_totals[i];
        if (sun_totals[i] < min_sun) min_sun = sun_totals[i];
    }
    for (int i = 0; i < n; i++) {
        if (sun_totals[i] == max_sun) { gs->players[i].score += 5; printf("  玩家%d 太陽籌碼最高(%d) +5\n", i+1, max_sun); }
        if (sun_totals[i] == min_sun) { gs->players[i].score -= 5; printf("  玩家%d 太陽籌碼最低(%d) -5\n", i+1, min_sun); }
    }

    /* 最終排名 */
    printf("\n====== 最終結果 ======\n");
    int winner = 0;
    for (int i = 0; i < n; i++) {
        printf("  玩家%d：%d 分\n", i+1, gs->players[i].score);
        if (gs->players[i].score > gs->players[winner].score) winner = i;
    }
    printf("  獲勝者：玩家%d！\n", winner+1);
}
