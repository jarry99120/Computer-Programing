#ifndef SCORING_H
#define SCORING_H

#include "game.h"

void score_epoch(GameState* gs);   /* 每個時代結束計分 */
void score_final(GameState* gs);   /* 第3時代額外計分 */

#endif
