import yfinance as yf
import google.generativeai as genai
import datetime
import requests
import time
import tweepy
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import mplfinance as mpf
import pandas as pd
import numpy as np

# 載入環境變數文件
load_dotenv()

# =================設定區=================
# 把你的 API KEY 貼在這裡
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# X (Twitter) API 金鑰
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET')

# 自動發文設定 (雲端部署時建議設為 True)
AUTO_POST_TO_X = os.getenv('AUTO_POST_TO_X', 'False').lower() == 'true' 

# 設定你想追蹤的標的 (可以自己增加)
# 格式: {'symbol': '顯示名稱', 'source': '數據源', 'coingecko_id': 'CoinGecko ID (僅加密貨幣)'}
TARGETS = {
    # 加密貨幣 (使用 CoinGecko)
    'BTC': {
        'name': '比特幣 (Bitcoin)',
        'source': 'coingecko',
        'coingecko_id': 'bitcoin'
    },
    'ETH': {
        'name': '以太幣 (Ethereum)', 
        'source': 'coingecko',
        'coingecko_id': 'ethereum'
    },
    'BNB': {
        'name': '幣安幣 (Binance Coin)',
        'source': 'coingecko',
        'coingecko_id': 'binancecoin'
    },
    'ADA': {
        'name': '艾達幣 (Cardano)',
        'source': 'coingecko',
        'coingecko_id': 'cardano'
    },
    'SOL': {
        'name': '索拉納 (Solana)',
        'source': 'coingecko',
        'coingecko_id': 'solana'
    },
    'XRP': {
        'name': '瑞波幣 (XRP)',
        'source': 'coingecko',
        'coingecko_id': 'ripple'
    },
    'DOGE': {
        'name': '狗狗幣 (Dogecoin)',
        'source': 'coingecko',
        'coingecko_id': 'dogecoin'
    },
    'AVAX': {
        'name': '雪崩幣 (Avalanche)',
        'source': 'coingecko',
        'coingecko_id': 'avalanche-2'
    },
    'MATIC': {
        'name': '多邊形 (Polygon)',
        'source': 'coingecko',
        'coingecko_id': 'matic-network'
    },
    'DOT': {
        'name': '波卡幣 (Polkadot)',
        'source': 'coingecko',
        'coingecko_id': 'polkadot'
    },
    
    # 美股 (使用 Yahoo Finance)
    'NVDA': {
        'name': '輝達 (NVIDIA)',
        'source': 'yahoo'
    },
    'TSLA': {
        'name': '特斯拉 (Tesla)',
        'source': 'yahoo'
    },
    'AAPL': {
        'name': '蘋果 (Apple)',
        'source': 'yahoo'
    },
    'COIN': {
        'name': 'Coinbase',
        'source': 'yahoo'
    }
}
# =======================================

def get_coingecko_price(coingecko_id):
    """從 CoinGecko 獲取加密貨幣價格"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coingecko_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if coingecko_id in data:
            price = data[coingecko_id]['usd']
            change_24h = data[coingecko_id].get('usd_24h_change', 0)
            return price, change_24h
        else:
            return None, None
            
    except Exception as e:
        print(f"CoinGecko API 錯誤: {e}")
        return None, None

def get_yahoo_price(symbol):
    """從 Yahoo Finance 獲取股票價格"""
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.fast_info['last_price']
        prev_close = ticker.fast_info['previous_close']
        change_percent = ((price - prev_close) / prev_close) * 100
        return price, change_percent
    except Exception as e:
        print(f"Yahoo Finance 錯誤 ({symbol}): {e}")
        return None, None

def get_prices():
    """抓取最新的市場價格與漲跌幅"""
    print("正在從多個數據源抓取數據...")
    market_info = ""
    
    for symbol, config in TARGETS.items():
        try:
            name = config['name']
            source = config['source']
            
            print(f"正在抓取 {name} (來源: {source})")
            
            if source == 'coingecko':
                price, change_percent = get_coingecko_price(config['coingecko_id'])
            elif source == 'yahoo':
                price, change_percent = get_yahoo_price(symbol)
            else:
                print(f"未知的數據源: {source}")
                continue
            
            if price is not None and change_percent is not None:
                # 加上表情符號方便 AI 判讀情緒
                emoji = "🚀" if change_percent > 0 else "🔻"
                
                # 根據數據源調整顯示格式
                if source == 'coingecko':
                    market_info += f"{name}: ${price:.4f} (24h: {emoji} {change_percent:.2f}%) [CoinGecko]\n"
                else:
                    market_info += f"{name}: ${price:.2f} (漲跌: {emoji} {change_percent:.2f}%) [Yahoo]\n"
            else:
                market_info += f"{name}: 數據獲取失敗\n"
                
            # 避免 API 限制，稍微延遲
            time.sleep(0.2)
            
        except Exception as e:
            print(f"抓取 {config['name']} 失敗: {e}")
            
    return market_info

def create_price_chart(symbol, symbol_name, period='5d'):
    """生成英文版價格走勢圖並加上技術分析"""
    try:
        print(f"正在生成 {symbol_name} 價格圖表...")
        
        # 獲取歷史數據
        if symbol in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'AVAX', 'MATIC', 'DOT']:
            # 對於加密貨幣，使用 yfinance 的加密貨幣代碼
            crypto_symbols = {
                'BTC': 'BTC-USD',
                'ETH': 'ETH-USD', 
                'BNB': 'BNB-USD',
                'ADA': 'ADA-USD',
                'SOL': 'SOL-USD',
                'XRP': 'XRP-USD',
                'DOGE': 'DOGE-USD',
                'AVAX': 'AVAX-USD',
                'MATIC': 'MATIC-USD',
                'DOT': 'DOT-USD'
            }
            ticker = yf.Ticker(crypto_symbols[symbol])
        else:
            # 美股直接使用原代碼
            ticker = yf.Ticker(symbol)
            
        # 獲取歷史數據
        hist = ticker.history(period=period, interval='1h')
        
        if hist.empty:
            return None
            
        # 移除中文字體設定，使用默認英文字體
        plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 創建圖表
        fig, ax = plt.subplots(figsize=(12, 8), facecolor='black')
        ax.set_facecolor('black')
        
        # 繪製價格線
        prices = hist['Close']
        times = hist.index
        
        # 價格線 (綠色上漲，紅色下跌)
        color = '#26a69a' if prices.iloc[-1] > prices.iloc[0] else '#ef5350'
        ax.plot(times, prices, color=color, linewidth=3, alpha=0.8)
        
        # 計算支撐和阻力線
        recent_prices = prices.tail(24)  # 最近24小時
        support_level = recent_prices.min()
        resistance_level = recent_prices.max()
        
        # 畫支撐線（英文標籤）
        ax.axhline(y=support_level, color='cyan', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(times[-1], support_level, f'Support ${support_level:.2f}', 
                color='cyan', fontsize=12, ha='right')
        
        # 畫阻力線（英文標籤）
        ax.axhline(y=resistance_level, color='orange', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(times[-1], resistance_level, f'Resistance ${resistance_level:.2f}', 
                color='orange', fontsize=12, ha='right')
        
        # 英文幣種名稱對應
        symbol_names_en = {
            'BTC': 'Bitcoin (BTC)',
            'ETH': 'Ethereum (ETH)', 
            'BNB': 'Binance Coin (BNB)',
            'ADA': 'Cardano (ADA)',
            'SOL': 'Solana (SOL)',
            'NVDA': 'NVIDIA Corporation',
            'TSLA': 'Tesla Inc.',
            'AAPL': 'Apple Inc.',
            'COIN': 'Coinbase Global Inc.'
        }
        
        display_name = symbol_names_en.get(symbol, symbol)
        
        # 設定圖表樣式（英文標題）
        ax.set_title(f'{display_name} Price Chart', color='white', fontsize=20, pad=20, weight='bold')
        ax.set_xlabel('Time', color='white', fontsize=12)
        ax.set_ylabel('Price (USD)', color='white', fontsize=12)
        
        # 設定軸線顏色
        ax.tick_params(colors='white', labelsize=10)
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
        
        # 添加網格
        ax.grid(True, alpha=0.3, color='gray')
        
        # 加入當前價格標註（英文）
        current_price = prices.iloc[-1]
        change_pct = ((current_price - prices.iloc[0]) / prices.iloc[0]) * 100
        
        price_text = f'${current_price:.2f} ({change_pct:+.1f}%)'
        ax.text(0.02, 0.95, price_text, transform=ax.transAxes,
                fontsize=16, color='white', bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
        
        # 格式化 X 軸時間標籤
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存為圖片
        chart_path = f'{symbol}_chart.png'
        plt.savefig(chart_path, facecolor='black', dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path, current_price, change_pct
        
    except Exception as e:
        print(f"圖表生成失敗 ({symbol}): {e}")
        return None

def generate_engaging_question(symbol, price, change_pct, symbol_name):
    """生成吸引人的問句"""
    if change_pct > 5:
        return f"{symbol_name}突破${price:.0f}！下一個目標是多少？"
    elif change_pct < -5:
        return f"{symbol_name}跌破${price:.0f}後，何時反彈？"
    elif abs(change_pct) < 2:
        return f"{symbol_name}在${price:.0f}附近震盪，突破方向是？"
    else:
        return f"{symbol_name}現報${price:.0f}，接下來會如何？"

def generate_post(data_text, chart_info=None):
    """傳送數據給 AI 寫文案"""
    print("正在呼叫 AI 生成文案...")
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 嘗試不同的模型名稱（按優先順序）
        model_names = [
            'models/gemini-2.5-flash',
            'models/gemini-2.5-pro',
            'models/gemini-2.0-flash',
            'models/gemini-flash-latest',
            'models/gemini-pro-latest'
        ]
        
        model = None
        for model_name in model_names:
            try:
                print(f"嘗試模型: {model_name}")
                model = genai.GenerativeModel(model_name)
                break  # 成功創建模型就跳出
            except Exception as e:
                print(f"模型 {model_name} 失敗: {e}")
                continue
        
        if model is None:
            raise Exception("無法找到可用的模型")
        
        # 判斷是否為圖表版本
        if chart_info:
            symbol = chart_info['symbol']
            symbol_name = chart_info['symbol_name']
            price = chart_info['price']
            change_pct = chart_info['change_pct']
            question = generate_engaging_question(symbol, price, change_pct, symbol_name)
            
            prompt = f"""請根據市場數據寫一則繁體中文推文（配圖版本）：

{data_text}

重點標的：{symbol_name} 現價 ${price:.2f} ({change_pct:+.1f}%)
結尾問句：{question}

要求：
- 不超過 150 字元（因為有配圖）
- 重點分析當前市場趨勢
- 語氣專業但吸引人
- 結尾必須使用提供的問句
- 加 2-3 個 hashtag
- 直接輸出推文內容
- 不要提及這是AI生成的內容
- 最後要加上一句推廣語句，例如「關注我獲取更多市場分析！」或「持續關注，掌握最新市場動態！」等。
- 這是我的交易所連結：https://partner.bybit.com/b/COMEFROMX，請搭配推廣語句使用。

直接開始推文內容："""
        else:
            # 原版純文字推文
            prompt = f"""請根據市場數據寫一則繁體中文推文：

{data_text}

要求：
- 不超過 200 字元
- 分析 1-2 個波動最大標的
- 包含市場情緒
- 結尾加 2-3 個 hashtag
- 呼籲理性投資
- 直接輸出推文內容，不要任何開場白或說明
- 不要提及這是AI生成的內容
- 最後要加上一句推廣語句，例如「關注我獲取更多市場分析！」或「持續關注，掌握最新市場動態！」等。
- 這是我的交易所連結：https://partner.bybit.com/b/COMEFROMX，請搭配推廣語句使用。

範例格式：
今日市場[情緒]，BTC[$價格] ([漲跌%])... [簡短分析] 理性投資，控制風險。#BTC #投資

直接開始推文內容："""
        
        response = model.generate_content(prompt)
        
        # 清理 AI 回覆，移除不必要的開場白
        content = response.text.strip()
        
        # 移除常見的 AI 開場白
        prefixes_to_remove = [
            "好的，這是一篇為您量身打造的 X 推文：",
            "好的，老闆！這是為您準備的 X 推文草稿與圖片：",
            "好的，這是為您準備的推文：",
            "以下是推文內容：",
            "推文內容：",
            "---",
            "好的，",
            "當然，",
            "這是",
            "為您生成的推文："
        ]
        
        for prefix in prefixes_to_remove:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
        
        # 移除開頭的破折號或其他分隔符
        while content.startswith(("---", "—", "-", "＊", "*")):
            content = content[3:].strip() if content.startswith("---") else content[1:].strip()
            
        return content
    
    except Exception as e:
        print(f"AI 生成失敗: {e}")
        return f"無法生成 AI 文案，請檢查 API Key 是否正確。錯誤: {str(e)}"

def verify_x_credentials():

    """驗證 X API 認證資訊"""
    try:
        print("🔍 正在驗證 X API 認證...")
        
        # 設置 X API v2 認證
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET
        )
        
        # 測試 API 連接 - 獲取自己的用戶資訊
        try:
            user = client.get_me()
            if user.data:
                print(f"✅ API 認證成功！用戶: @{user.data.username}")
                return True, client
            else:
                print("❌ 無法獲取用戶資訊")
                return False, None
        except Exception as api_error:
            print(f"❌ API 測試失敗: {api_error}")
            return False, None
            
    except Exception as e:
        print(f"❌ 認證設置錯誤: {e}")
        return False, None

def post_to_x(content, image_path=None):
    """發布內容到 X (Twitter)，支援圖片上傳"""
    try:
        # 先驗證認證
        is_valid, client = verify_x_credentials()
        if not is_valid:
            print("\n🛠️ 可能的解決方案:")
            print("1. 檢查 API Key 和 Secret 是否正確")
            print("2. 檢查 Access Token 和 Secret 是否正確") 
            print("3. 確認應用程式權限為 'Read and Write'")
            print("4. 檢查 Token 是否過期")
            print("5. 確認應用程式已啟用並獲得批准")
            return False
        
        # 檢查推文長度
        print(f"📏 推文長度: {len(content)} 字元")
        if len(content) > 280:
            print(f"⚠️ 推文過長！Twitter 限制 280 字元")
            print("正在智能截短...")
            
            # 智能截短：優先保留 hashtag
            if '#' in content:
                # 找到最後一個 hashtag 的位置
                hashtag_start = content.rfind('#')
                hashtags = content[hashtag_start:]
                main_content = content[:hashtag_start].strip()
                
                # 計算可用長度 (保留 hashtags + 一些空間)
                available_length = 275 - len(hashtags) 
                if len(main_content) > available_length:
                    content = main_content[:available_length].rstrip() + "... " + hashtags
                else:
                    content = main_content + " " + hashtags
            else:
                # 沒有 hashtag 就直接截短
                content = content[:277] + "..."
                
            print(f"✂️ 截短後長度: {len(content)} 字元")
        else:
            print("✅ 長度符合 Twitter 限制")
        
        # 上傳圖片 (如果有)
        media_id = None
        if image_path and os.path.exists(image_path):
            try:
                print("📸 正在上傳圖片...")
                # 使用 API v1.1 上傳媒體
                auth = tweepy.OAuth1UserHandler(
                    X_API_KEY, X_API_SECRET,
                    X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
                )
                api_v1 = tweepy.API(auth)
                
                media = api_v1.media_upload(image_path)
                media_id = media.media_id
                print(f"✅ 圖片上傳成功！Media ID: {media_id}")
            except Exception as e:
                print(f"❌ 圖片上傳失敗: {e}")
                print("將改為純文字發文...")
        
        # 發布推文
        print("正在發布推文...")
        if media_id:
            response = client.create_tweet(text=content, media_ids=[media_id])
            print("📸 帶圖片推文")
        else:
            response = client.create_tweet(text=content)
            print("📝 純文字推文")
        
        if response.data:
            tweet_id = response.data['id']
            print(f"✅ 推文發布成功！")
            print(f"推文 ID: {tweet_id}")
            print(f"推文連結: https://twitter.com/i/web/status/{tweet_id}")
            return True
        else:
            print("❌ 推文發布失敗：沒有回應數據")
            return False
            
    except tweepy.Unauthorized as e:
        print(f"❌ 401 未授權錯誤: {e}")
        print("\n🛠️ 解決 401 錯誤的步驟:")
        print("1. 到 https://developer.twitter.com/en/portal/dashboard")
        print("2. 選擇你的應用程式 > 'Settings'")
        print("3. 確認 'App permissions' 設為 'Read and Write'") 
        print("4. 如果改過權限，需要重新生成 Access Token")
        print("5. 確認所有 4 個金鑰都是最新的")
        return False
    except tweepy.Forbidden as e:
        print(f"❌ 403 禁止訪問錯誤: {e}")
        print("可能原因：應用程式沒有寫入權限或內容違反政策")
        return False
    except tweepy.TooManyRequests as e:
        print(f"❌ 429 請求過多錯誤: {e}")
        print("請稍後再試，已達到 API 限制")
        return False
    except Exception as e:
        print(f"❌ 其他 X API 錯誤: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        return False

# --- 主程式執行入口 ---
if __name__ == "__main__":
    # 檢查 API 金鑰環境變數
    missing_keys = []
    
    if not GEMINI_API_KEY:
        missing_keys.append('GEMINI_API_KEY')
    if not X_API_KEY:
        missing_keys.append('X_API_KEY')
    if not X_API_SECRET:
        missing_keys.append('X_API_SECRET')
    if not X_ACCESS_TOKEN:
        missing_keys.append('X_ACCESS_TOKEN')
    if not X_ACCESS_TOKEN_SECRET:
        missing_keys.append('X_ACCESS_TOKEN_SECRET')
    
    if missing_keys:
        print("❌ 缺少以下環境變數:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\n📝 請設定環境變數或創建 .env 文件")
        print("🔗 參考 .env.example 文件設定格式")
        exit(1)
    
    # 檢查 X API 金鑰是否已設定（非空值）
    x_keys_set = all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET])
    
    # 1. 抓數據
    data = get_prices()
    
    if data:
        print(f"----------------\n抓取到的數據:\n{data}----------------")
        
        # 2. 生成技術分析圖表
        print("📈 正在生成技術分析圖表...")
        chart_path = None
        chart_info = None
        try:
            # 生成比特幣圖表作為主要分析
            chart_result = create_price_chart('BTC', '比特幣', '5d')
            if chart_result and len(chart_result) == 3:
                chart_path, current_price, change_pct = chart_result
                chart_info = {
                    'price': current_price,
                    'change_pct': change_pct,
                    'symbol': 'BTC',
                    'symbol_name': '比特幣'
                }
                print(f"✅ 圖表已生成: {chart_path}")
            else:
                print("❌ 圖表生成返回值不正確")
        except Exception as e:
            print(f"❌ 圖表生成失敗: {e}")
            print("將使用純文字模式...")
        
        # 3. 寫文案
        post_content = generate_post(data, chart_info)
        
        print("\n======= AI 生成的貼文預覽 =======")
        print(post_content)
        print("================================")
        
        # 4. 詢問是否要發布到 X
        if x_keys_set:
            if AUTO_POST_TO_X:
                # 自動發文模式
                print("\n🤖 自動發文模式啟用，正在發布到 X...")
                success = post_to_x(post_content, chart_path)
                if success:
                    print("🎉 貼文已自動發布到 X!")
                else:
                    print("😞 自動發布失敗，請檢查 X API 設定")
            else:
                # 手動確認模式
                while True:
                    user_input = input("\n要發布到 X (Twitter) 嗎? (y/n): ").lower().strip()
                    if user_input in ['y', 'yes', '是']:
                        success = post_to_x(post_content, chart_path)
                        if success:
                            print("🎉 貼文已成功發布到 X!")
                        else:
                            print("😞 發布失敗，請檢查 X API 設定")
                        break
                    elif user_input in ['n', 'no', '否']:
                        print("📝 貼文已生成，未發布到 X")
                        break
                    else:
                        print("請輸入 y (是) 或 n (否)")
        else:
            print("\n💡 提示: 設定 X API 金鑰後可直接發布到 X!")
            print("請到 https://developer.twitter.com/en/portal/dashboard 申請 API 金鑰")
        
        # 5. 清理臨時圖片檔案
        if chart_path:
            try:
                os.remove(chart_path)
                print("🗑️ 臨時圖表檔案已清理")
            except:
                pass
    else:
        print("抓取數據失敗，請檢查網路或代號。")