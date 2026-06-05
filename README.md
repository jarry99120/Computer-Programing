# 太陽神 Ra (Ra Board Game) — C 語言核心 × Flask 網頁版專題

本專案將經典桌遊《太陽神 Ra》的核心邏輯以高效的 **C 語言** 實作，並透過 **Python Ctypes** 橋樑，將其包裝成現代化的 **Flask 網頁伺服器（Blueprint 藍圖架構）**。前端採用 **Tailwind CSS** 打造美觀、響應式的暗色系遊戲介面。

---

## 📂 專案目錄與檔案用途說明

```text
Computer-Programing/
│
├── c_engine/                  # 💡 C 語言遊戲核心引擎 (純運算)
│   ├── game.c                 # 遊戲主流程、抽牌、玩家輪替與競標核心邏輯
│   ├── game.h                 # 定義遊戲核心資料結構 (Tile, Player, GameState)
│   ├── scoring.c              # 每個時代結束與終局的計分演算法
│   └── scoring.h              # 計分模組的函式宣告
│
└── web_server/                # 💡 Flask 網頁伺服器與前端介面
    ├── app.py                 # 專案啟動點，負責初始化 Flask 並註冊藍圖路由
    ├── engine_bridge.py       # Python 與 C 的橋樑，定義 Ctypes 結構體並載入 DLL
    ├── libra_engine.dll       # 由 c_engine 編譯而成的動態連結庫 (背景光速運算)
    │
    ├── routes/                # 💡 路由模組化目錄 (負責不同類型的請求)
    │   ├── __init__.py        # 將 routes 包裝成 Python 套件
    │   ├── view_routes.py     # 畫面路由：負責渲染並回傳 index.html 主網頁
    │   └── api_routes.py      # API 路由：負責前後端資料交換 (抽牌、召喚Ra、結算競標)
    │
    └── templates/             # 💡 網頁樣板目錄
        └── index.html         # 遊戲前端 UI 介面 (包含 HTML5、Tailwind CSS 與 Fetch API 邏輯)
