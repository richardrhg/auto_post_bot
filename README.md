# 🤖 自動化市場分析發文機器人

這是一個自動化的投資市場分析機器人，可以：
- 📊 自動抓取股票和加密貨幣價格 (CoinGecko + Yahoo Finance)
- 🤖 使用 Google Gemini AI 生成專業分析文案
- 🐦 自動發布到 X (Twitter)
- ⏰ 透過 GitHub Actions 定時執行

## 🏗️ 系統架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CoinGecko API │    │   Yahoo Finance  │    │  Google Gemini  │
│  (加密貨幣價格)   │    │    (美股價格)     │    │   AI (文案生成)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │      Python 程式         │
                    │   main.py (核心邏輯)      │
                    └─────────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │      X (Twitter)       │
                    │     API (自動發文)       │
                    └─────────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │    GitHub Actions      │
                    │   (定時執行: 9AM, 3PM)   │
                    └─────────────────────────┘
```

## 🚀 快速部署指南

### 第一步：克隆或下載程式碼

```bash
git clone https://github.com/你的用戶名/你的倉庫名.git
cd 你的倉庫名
```

### 第二步：設定 API 金鑰

1. **Google Gemini API**
   - 到 [Google AI Studio](https://makersuite.google.com/app/apikey) 申請免費 API Key
   
2. **X (Twitter) API**
   - 到 [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
   - 創建新應用程式
   - 生成以下 4 個金鑰：
     - API Key
     - API Secret  
     - Access Token
     - Access Token Secret
   - ⚠️ **重要**: 確保應用程式權限設為 "Read and Write"

### 第三步：配置 GitHub Secrets

到你的 GitHub Repository 設定 Secrets：

1. 進入 **Settings** → **Secrets and variables** → **Actions**
2. 點擊 **New repository secret** 
3. 添加以下 5 個 secrets：

| Secret 名稱 | 說明 |
|-------------|------|
| `GEMINI_API_KEY` | Google Gemini API 金鑰 |
| `X_API_KEY` | X API Key |
| `X_API_SECRET` | X API Secret |
| `X_ACCESS_TOKEN` | X Access Token |
| `X_ACCESS_TOKEN_SECRET` | X Access Token Secret |

### 第四步：啟用 GitHub Actions

1. 推送程式碼到 GitHub
2. 到 **Actions** 頁面
3. 啟用 workflows
4. 可以手動觸發測試，或等待定時執行

## ⏰ 執行排程

- **上午 9:00** (台北時間) - 市場開盤分析
- **下午 3:00** (台北時間) - 市場收盤總結

可以在 `.github/workflows/auto-market-post.yml` 修改時間。

## 🔧 本地開發

### 安裝依賴

```bash
# 創建虛擬環境
python -m venv .venv

# 啟用虛擬環境 (Windows)
.venv\Scripts\activate

# 啟用虛擬環境 (Mac/Linux)  
source .venv/bin/activate

# 安裝套件
pip install -r requirements.txt
```

### 設定環境變數

1. 複製環境變數範例：
```bash
cp .env.example .env
```

2. 編輯 `.env` 文件，填入你的 API 金鑰：
```bash
GEMINI_API_KEY=your_actual_api_key_here
X_API_KEY=your_actual_x_api_key_here
# ... 等等
```

### 執行程式

```bash
python main.py
```

## 📊 監控的投資標的

### 加密貨幣 (CoinGecko API)
- Bitcoin (BTC)
- Ethereum (ETH) 
- Binance Coin (BNB)
- Cardano (ADA)
- Solana (SOL)

### 美股 (Yahoo Finance API)
- NVIDIA (NVDA)
- Tesla (TSLA)
- Apple (AAPL)
- Coinbase (COIN)

可在 `main.py` 的 `TARGETS` 變數中自由添加其他標的。

## 🛠️ 自定義設定

### 修改發文時間

編輯 `.github/workflows/auto-market-post.yml`：

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 1:00 = 台北 9:00
  - cron: '0 7 * * *'  # UTC 7:00 = 台北 15:00
```

### 調整文案風格

修改 `main.py` 中的 `generate_post()` 函數的 prompt。

### 添加投資標的

在 `TARGETS` 變數中添加：

```python
'SYMBOL': {
    'name': '顯示名稱',
    'source': 'coingecko',  # 或 'yahoo'
    'coingecko_id': 'coingeeko_id'  # 僅加密貨幣需要
}
```

## ⚠️ 重要注意事項

### 安全性
- **永遠不要**將 API 金鑰提交到 Git
- 使用 GitHub Secrets 保護敏感信息
- 定期更換 API 金鑰

### API 限制
- **Google Gemini**: 免費版有每月請求限制
- **CoinGecko**: 免費版每分鐘 10-30 次請求
- **X API**: 免費版每月 1500 條推文限制

### 內容政策
- 確保生成內容符合各平台政策
- 添加風險警告，避免投資建議爭議
- 遵守當地金融法規

## 🐛 常見問題

### Q: 推文沒有自動發布？
A: 檢查：
1. GitHub Secrets 是否正確設定
2. X API 權限是否為 "Read and Write"
3. Actions 是否正常執行

### Q: AI 生成失敗？
A: 檢查：
1. Gemini API Key 是否有效
2. 是否達到 API 限制
3. 網路連接是否正常

### Q: 資料抓取失敗？
A: 檢查：
1. API 服務是否正常
2. 是否達到請求限制
3. 標的代碼是否正確

## 📄 授權

MIT License - 詳見 LICENSE 文件

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

**免責聲明**: 本工具僅供教育和技術展示用途。投資有風險，請謹慎決策並諮詢專業投資建議。