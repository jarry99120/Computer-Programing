// ==================== scoring.h ====================
#ifndef SCORING_H
#define SCORING_H

// 引入 game.h，直接讓全域都知道 GameState 與 Player 是什麼
#include "game.h" 

void resolve_disaster_immediate(Player* p, int disaster_value);
void score_epoch(GameState* gs);
void score_final(GameState* gs);

#endif // SCORING_H