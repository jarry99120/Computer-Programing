// scoring.h
#ifndef SCORING_H
#define SCORING_H

// 1. 直接引入 game.h，讓這裏能讀到完整的 Player, GameState 和 TILE_FLOOD 等定義
#include "game.h" 

// 2. 移除原本的 typedef struct GameState GameState; (因為 game.h 裡面有了)
// 3. 移除原本的 typedef struct Player Player;

void resolve_disaster_immediate(Player* p, int disaster_value);
void score_epoch(GameState* gs);
void score_final(GameState* gs);

#endif // SCORING_H