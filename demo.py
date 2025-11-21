#!/usr/bin/env python3
"""
演示版本：帶圖表的市場分析機器人
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def create_demo_chart():
    """創建演示圖表"""
    # 創建模擬比特幣價格數據
    dates = pd.date_range(start=datetime.now() - timedelta(days=5), 
                         end=datetime.now(), freq='h')
    np.random.seed(42)
    prices = 85000 + np.cumsum(np.random.randn(len(dates)) * 100)
    
    # 創建圖表
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    
    # 畫價格線
    ax.plot(dates, prices, color='#00ff41', linewidth=3, alpha=0.9)
    
    # 添加支撐和阻力線
    support = prices.min()
    resistance = prices.max()
    
    ax.axhline(y=support, color='cyan', linestyle='--', linewidth=2, alpha=0.7)
    ax.axhline(y=resistance, color='orange', linestyle='--', linewidth=2, alpha=0.7)
    
    # 標籤
    ax.text(dates[-1], support, f'支撐 ${support:.0f}', 
            color='cyan', fontsize=12, ha='right')
    ax.text(dates[-1], resistance, f'阻力 ${resistance:.0f}', 
            color='orange', fontsize=12, ha='right')
    
    # 設定圖表樣式
    ax.set_title('比特幣 價格走勢 (演示)', color='white', fontsize=20, pad=20)
    ax.set_xlabel('時間', color='white', fontsize=12)
    ax.set_ylabel('價格 (USD)', color='white', fontsize=12)
    
    # 設定軸線顏色
    ax.tick_params(colors='white', labelsize=10)
    for spine in ax.spines.values():
        spine.set_color('white')
    
    # 添加網格
    ax.grid(True, alpha=0.3, color='gray')
    
    # 添加當前價格
    current_price = prices.iloc[-1]
    change_pct = ((current_price - prices.iloc[0]) / prices.iloc[0]) * 100
    price_text = f'${current_price:.2f} ({change_pct:+.1f}%)'
    ax.text(0.02, 0.95, price_text, transform=ax.transAxes,
            fontsize=16, color='white', 
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
    
    plt.tight_layout()
    
    # 保存圖片
    chart_path = 'demo_chart.png'
    plt.savefig(chart_path, facecolor='black', dpi=150, bbox_inches='tight')
    plt.close()
    
    return chart_path, current_price, change_pct

if __name__ == "__main__":
    print("🎨 正在生成演示圖表...")
    chart_path, price, change = create_demo_chart()
    print(f"✅ 圖表已生成: {chart_path}")
    print(f"📊 比特幣價格: ${price:.2f} ({change:+.1f}%)")
    print("📱 圖表可用於社交媒體發文，增加 5-10 倍的互動率！")