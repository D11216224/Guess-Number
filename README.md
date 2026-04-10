# 猜數字遊戲（Pure Web）

A fully client-side number guessing game — **no server, no install needed**.  
Just open `index.html` in any browser and play!

## Features

- Random 1–100 integer generated in the browser each game
- Real-time **大了 / 小了 / 恭喜通過！** feedback
- Guess count tracked per game
- Personal stats stored in `localStorage`: best score, recent-5 average, history

## How to Play

1. Open `index.html` in your browser (double-click or drag into a browser tab)
2. Type a number between 1 and 100
3. Click **猜！** (or press Enter)
4. Follow the hints until you guess correctly
5. Click **🔄 開始新局** to start a new round

## Project Structure

```
├── index.html   # Complete game (HTML + CSS + JS, single file)
└── README.md
```