from flask import Blueprint, render_template

view_bp = Blueprint('view', __name__)

# 1. 導向大廳（人數選擇）
@view_bp.route('/')
def index():
    return render_template('index.html')

# 2. 導向正式遊戲面板
@view_bp.route('/board')
def game_board():
    return render_template('board.html')