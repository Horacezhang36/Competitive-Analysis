#!/usr/bin/env python3
"""北京未来60天天气预测工具 - 使用 Open-Meteo 免费 API"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

# 北京坐标
LAT = 39.9042
LON = 116.4074
TZ = "Asia/Shanghai"

# 天气代码映射 (WMO Weather interpretation codes)
WMO_CODES = {
    0:  ("☀️", "晴天"),
    1:  ("🌤️", "大部晴朗"),
    2:  ("⛅", "多云"),
    3:  ("☁️", "阴天"),
    45: ("🌫️", "雾"),
    48: ("🌫️", "雾凇"),
    51: ("🌦️", "小毛毛雨"),
    53: ("🌦️", "中毛毛雨"),
    55: ("🌧️", "大毛毛雨"),
    56: ("🌧️", "冻毛毛雨"),
    57: ("🌧️", "冻毛毛雨"),
    61: ("🌦️", "小雨"),
    63: ("🌧️", "中雨"),
    65: ("🌧️", "大雨"),
    66: ("🌧️", "冻雨"),
    67: ("🌧️", "冻雨"),
    71: ("🌨️", "小雪"),
    73: ("🌨️", "中雪"),
    75: ("❄️", "大雪"),
    77: ("🌨️", "雪粒"),
    80: ("🌦️", "阵雨"),
    81: ("🌧️", "中阵雨"),
    82: ("🌧️", "大阵雨"),
    85: ("🌨️", "小阵雪"),
    86: ("🌨️", "大阵雪"),
    95: ("⛈️", "雷暴"),
    96: ("⛈️", "雷暴+小冰雹"),
    99: ("⛈️", "雷暴+大冰雹"),
}

def fetch_weather():
    """从 Open-Meteo API 获取北京天气数据"""
    params = urllib.parse.urlencode({
        "latitude": LAT,
        "longitude": LON,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,relative_humidity_2m_mean",
        "timezone": TZ,
        "forecast_days": 16,  # Open-Meteo 免费版最多16天
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    
    print(f"正在请求 Open-Meteo API...")
    req = urllib.request.Request(url, headers={"User-Agent": "BeijingWeather/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    
    daily = data["daily"]
    days = []
    for i in range(len(daily["time"])):
        days.append({
            "date": daily["time"][i],
            "weather_code": daily["weather_code"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "precip": daily["precipitation_sum"][i],
            "wind_max": daily["wind_speed_10m_max"][i],
            "humidity": daily["relative_humidity_2m_mean"][i],
        })
    return days

def generate_simulated_days(real_days, total=60):
    """基于真实16天数据，模拟扩展到60天（加入合理波动）"""
    import random
    random.seed(42)
    
    all_days = list(real_days)
    last_date = datetime.strptime(real_days[-1]["date"], "%Y-%m-%d")
    
    # 使用最后几天的平均值作为基准
    base = real_days[-7:]
    avg_max = sum(d["temp_max"] for d in base) / len(base)
    avg_min = sum(d["temp_min"] for d in base) / len(base)
    avg_precip = sum(d["precip"] for d in base) / len(base)
    avg_wind = sum(d["wind_max"] for d in base) / len(base)
    avg_humidity = sum(d["humidity"] for d in base) / len(base)
    common_codes = [d["weather_code"] for d in base]
    
    for i in range(total - len(real_days)):
        new_date = last_date + timedelta(days=i + 1)
        # 加入季节性趋势（北京夏季温度波动）
        trend = (i / 60) * 3  # 轻微升温趋势
        noise_max = random.uniform(-3, 3)
        noise_min = random.uniform(-2, 2)
        
        all_days.append({
            "date": new_date.strftime("%Y-%m-%d"),
            "weather_code": random.choice(common_codes),
            "temp_max": round(avg_max + trend + noise_max, 1),
            "temp_min": round(avg_min + trend + noise_min, 1),
            "precip": round(max(0, avg_precip + random.uniform(-2, 5)), 1),
            "wind_max": round(max(0, avg_wind + random.uniform(-5, 8)), 1),
            "humidity": round(min(100, max(10, avg_humidity + random.uniform(-10, 10)))),
        })
    return all_days

def temp_color(temp):
    """根据温度返回颜色"""
    if temp >= 35:
        return "#e53e3e"
    elif temp >= 30:
        return "#ed8936"
    elif temp >= 25:
        return "#ecc94b"
    elif temp >= 20:
        return "#48bb78"
    elif temp >= 10:
        return "#4299e1"
    elif temp >= 0:
        return "#63b3ed"
    else:
        return "#b794f4"

def generate_html(days):
    """生成 HTML 页面"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    # 构建表格行
    rows = []
    for i, d in enumerate(days):
        emoji, desc = WMO_CODES.get(d["weather_code"], ("❓", "未知"))
        date_obj = datetime.strptime(d["date"], "%Y-%m-%d")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
        month_day = f"{date_obj.month}/{date_obj.day}"
        
        # 标记前16天为真实预报
        badge = '<span class="badge real">真实预报</span>' if i < 16 else '<span class="badge sim">趋势推测</span>'
        
        tmax_color = temp_color(d["temp_max"])
        tmin_color = temp_color(d["temp_min"])
        
        rows.append(f"""\
            <tr class="{'real-row' if i < 16 else 'sim-row'}">
                <td class="date-cell">
                    <span class="month-day">{month_day}</span>
                    <span class="weekday">{weekday}</span>
                </td>
                <td class="weather-cell">
                    <span class="emoji">{emoji}</span>
                    <span class="desc">{desc}</span>
                </td>
                <td class="temp-cell">
                    <span class="temp-high" style="color:{tmax_color}">{d["temp_max"]}°</span>
                    <span class="temp-sep">/</span>
                    <span class="temp-low" style="color:{tmin_color}">{d["temp_min"]}°</span>
                </td>
                <td class="data-cell">{d["precip"]} mm</td>
                <td class="data-cell">{d["wind_max"]} km/h</td>
                <td class="data-cell">{d["humidity"]}%</td>
                <td class="badge-cell">{badge}</td>
            </tr>""")
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>北京未来60天天气预测</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e2e8f0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 40px 20px 30px;
        }}
        
        header h1 {{
            font-size: 2.2em;
            font-weight: 700;
            background: linear-gradient(135deg, #f6ad55, #ed64a6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }}
        
        header .subtitle {{
            color: #a0aec0;
            font-size: 0.95em;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85em;
            color: #a0aec0;
        }}
        
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
        
        .legend-dot.real {{ background: #48bb78; }}
        .legend-dot.sim {{ background: #ed8936; }}
        
        .table-wrapper {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead th {{
            background: rgba(255,255,255,0.08);
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85em;
            color: #a0aec0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
        }}
        
        tbody td {{
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.95em;
        }}
        
        tbody tr:hover {{
            background: rgba(255,255,255,0.06);
        }}
        
        .real-row {{ }}
        .sim-row {{ opacity: 0.7; }}
        .sim-row:hover {{ opacity: 1; }}
        
        .date-cell {{
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        
        .month-day {{
            font-weight: 600;
            font-size: 1em;
        }}
        
        .weekday {{
            font-size: 0.75em;
            color: #718096;
        }}
        
        .weather-cell {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .emoji {{ font-size: 1.5em; }}
        .desc {{ color: #cbd5e0; }}
        
        .temp-cell {{
            font-weight: 600;
            font-size: 1.05em;
        }}
        
        .temp-sep {{ color: #4a5568; margin: 0 2px; }}
        
        .data-cell {{
            color: #a0aec0;
        }}
        
        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
        }}
        
        .badge.real {{
            background: rgba(72, 187, 120, 0.2);
            color: #48bb78;
        }}
        
        .badge.sim {{
            background: rgba(237, 137, 54, 0.2);
            color: #ed8936;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: #4a5568;
            font-size: 0.8em;
        }}
        
        footer a {{
            color: #718096;
            text-decoration: none;
        }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            header h1 {{ font-size: 1.5em; }}
            thead th, tbody td {{ padding: 10px 8px; font-size: 0.8em; }}
            .data-cell {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏙️ 北京未来60天天气预测</h1>
            <p class="subtitle">数据来源: Open-Meteo API | 前16天为气象模型预报，后44天为趋势推测 | 生成时间: {today}</p>
        </header>
        
        <div class="legend">
            <div class="legend-item"><div class="legend-dot real"></div> 真实预报（前16天）</div>
            <div class="legend-item"><div class="legend-dot sim"></div> 趋势推测（后44天）</div>
        </div>
        
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>天气</th>
                        <th>温度</th>
                        <th>降水</th>
                        <th>风速</th>
                        <th>湿度</th>
                        <th>来源</th>
                    </tr>
                </thead>
                <tbody>
                    {chr(10).join(rows)}
                </tbody>
            </table>
        </div>
        
        <footer>
            <p>⚠️ 前16天数据来自 Open-Meteo 气象模型，后44天为基于近期趋势的统计推测，仅供参考</p>
            <p style="margin-top:6px;">Powered by <a href="https://open-meteo.com/" target="_blank">Open-Meteo</a> | 北京 (39.90°N, 116.41°E)</p>
        </footer>
    </div>
</body>
</html>"""
    return html

def main():
    print("=" * 50)
    print("  北京未来60天天气预测工具")
    print("=" * 50)
    
    # 获取真实预报
    real_days = fetch_weather()
    print(f"✅ 获取到 {len(real_days)} 天真实预报数据")
    
    # 扩展到60天
    all_days = generate_simulated_days(real_days, total=60)
    print(f"✅ 已扩展到 {len(all_days)} 天（含趋势推测）")
    
    # 生成 HTML
    html = generate_html(all_days)
    output_path = "/home/gem/beijing_weather_60days.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ HTML 已生成: {output_path}")
    print(f"   文件大小: {len(html):,} 字节")
    print("\n📊 数据概览（前5天）:")
    for d in all_days[:5]:
        emoji, desc = WMO_CODES.get(d["weather_code"], ("?", "?"))
        print(f"   {d['date']} | {emoji} {desc} | {d['temp_min']}°C ~ {d['temp_max']}°C | 降水:{d['precip']}mm")

if __name__ == "__main__":
    main()
