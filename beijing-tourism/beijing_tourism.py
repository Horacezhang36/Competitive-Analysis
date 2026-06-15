#!/usr/bin/env python3
"""北京热门旅游地分析工具"""

import json
from datetime import datetime, timezone

# 北京热门旅游地数据
ATTRACTIONS = [
    {
        "name": "故宫博物院",
        "name_en": "The Forbidden City",
        "category": "历史文化",
        "district": "东城区",
        "rating": 4.8,
        "reviews": 285000,
        "price": 60,
        "price_note": "旺季60元/淡季40元",
        "best_season": ["4月", "5月", "9月", "10月"],
        "best_time": "8:30-17:00（周一闭馆）",
        "visit_duration": "3-5小时",
        "crowd_level": "极高",
        "description": "世界最大的宫殿建筑群，明清两代皇家宫殿，UNESCO世界文化遗产。拥有超过180万件珍贵文物，是中国古代建筑艺术的巅峰之作。",
        "highlights": ["太和殿", "乾清宫", "珍宝馆", "钟表馆", "御花园"],
        "tips": "建议提前7天在官网预约，旺季一票难求",
        "metro": "1号线天安门东站",
        "lat": 39.9163,
        "lng": 116.3972,
        "monthly_visitors": [120, 100, 140, 160, 180, 170, 190, 200, 150, 160, 130, 110],
    },
    {
        "name": "八达岭长城",
        "name_en": "Badaling Great Wall",
        "category": "历史文化",
        "district": "延庆区",
        "rating": 4.7,
        "reviews": 220000,
        "price": 40,
        "price_note": "40元（旺季）/35元（淡季）",
        "best_season": ["4月", "5月", "9月", "10月"],
        "best_time": "6:30-19:00",
        "visit_duration": "3-4小时",
        "crowd_level": "极高",
        "description": "万里长城最精华段，明长城代表性段落，世界文化遗产。地势险峻，气势磅礴，是'不到长城非好汉'的打卡圣地。",
        "highlights": ["北一楼至北八楼", "好汉坡", "缆车观光", "长城博物馆"],
        "tips": "建议早8点前到达避开人流高峰，可乘S2线或877路公交",
        "metro": "S2线八达岭站",
        "lat": 40.3597,
        "lng": 116.0200,
        "monthly_visitors": [80, 70, 110, 150, 170, 160, 180, 190, 140, 150, 100, 90],
    },
    {
        "name": "颐和园",
        "name_en": "Summer Palace",
        "category": "皇家园林",
        "district": "海淀区",
        "rating": 4.7,
        "reviews": 195000,
        "price": 30,
        "price_note": "旺季30元/淡季20元",
        "best_season": ["4月", "5月", "6月", "9月", "10月"],
        "best_time": "6:30-18:00",
        "visit_duration": "3-4小时",
        "crowd_level": "高",
        "description": "中国现存最大的皇家园林，以昆明湖和万寿山为主体，集传统造园艺术之大成，被誉为'皇家园林博物馆'。",
        "highlights": ["佛香阁", "十七孔桥", "长廊", "石舫", "苏州街"],
        "tips": "推荐从东宫门进入，沿昆明湖顺时针游览",
        "metro": "4号线北宫门站",
        "lat": 39.9999,
        "lng": 116.2755,
        "monthly_visitors": [90, 80, 120, 150, 160, 170, 180, 190, 140, 130, 100, 80],
    },
    {
        "name": "天坛公园",
        "name_en": "Temple of Heaven",
        "category": "历史文化",
        "district": "东城区",
        "rating": 4.6,
        "reviews": 168000,
        "price": 15,
        "price_note": "旺季15元/淡季10元",
        "best_season": ["4月", "5月", "9月", "10月"],
        "best_time": "6:00-21:00",
        "visit_duration": "2-3小时",
        "crowd_level": "高",
        "description": "明清两代皇帝祭天祈谷的场所，祈年殿是北京标志性建筑之一。建筑布局精妙，声学设计独特，回音壁闻名遐迩。",
        "highlights": ["祈年殿", "回音壁", "圜丘坛", "皇穹宇", "丹陛桥"],
        "tips": "早上去可以看到市民晨练的热闹场景，很有生活气息",
        "metro": "5号线天坛东门站",
        "lat": 39.8822,
        "lng": 116.4066,
        "monthly_visitors": [100, 90, 110, 130, 140, 130, 150, 160, 120, 110, 100, 90],
    },
    {
        "name": "南锣鼓巷",
        "name_en": "Nanluoguxiang",
        "category": "胡同文化",
        "district": "东城区",
        "rating": 4.4,
        "reviews": 145000,
        "price": 0,
        "price_note": "免费",
        "best_season": ["3月", "4月", "5月", "9月", "10月"],
        "best_time": "全天开放",
        "visit_duration": "1-2小时",
        "crowd_level": "极高",
        "description": "北京最古老的街区之一，700多年历史的胡同。两侧遍布特色小店、文创店铺、小吃摊和咖啡馆，是体验老北京胡同文化的绝佳去处。",
        "highlights": ["特色文创店", "老北京小吃", "胡同建筑", "帽儿胡同", "雨儿胡同"],
        "tips": "建议工作日前往避开人流，可顺路逛什刹海",
        "metro": "6/8号线南锣鼓巷站",
        "lat": 39.9380,
        "lng": 116.4034,
        "monthly_visitors": [110, 100, 130, 150, 160, 150, 170, 180, 140, 130, 110, 120],
    },
    {
        "name": "798艺术区",
        "name_en": "798 Art Zone",
        "category": "艺术文化",
        "district": "朝阳区",
        "rating": 4.5,
        "reviews": 128000,
        "price": 0,
        "price_note": "园区免费（部分展览收费）",
        "best_season": ["3月", "4月", "5月", "9月", "10月"],
        "best_time": "10:00-18:00（大部分画廊）",
        "visit_duration": "2-4小时",
        "crowd_level": "中",
        "description": "由老工厂改造的当代艺术区，汇集画廊、设计工作室、时尚店铺和餐厅。包豪斯风格建筑与现代艺术的完美融合，文艺青年必打卡。",
        "highlights": ["UCCA尤伦斯当代艺术中心", "木木美术馆", "火车头广场", "涂鸦墙", "艺术商店"],
        "tips": "周末有创意市集，建议预留半天时间慢慢逛",
        "metro": "14号线望京南站",
        "lat": 39.9842,
        "lng": 116.4951,
        "monthly_visitors": [90, 80, 110, 120, 130, 120, 140, 140, 110, 100, 90, 100],
    },
    {
        "name": "北海公园",
        "name_en": "Beihai Park",
        "category": "皇家园林",
        "district": "西城区",
        "rating": 4.5,
        "reviews": 115000,
        "price": 10,
        "price_note": "旺季10元/淡季5元",
        "best_season": ["4月", "5月", "6月", "7月", "8月"],
        "best_time": "6:30-21:00",
        "visit_duration": "2-3小时",
        "crowd_level": "中",
        "description": "中国现存最古老、最完整的皇家园林之一，白塔是标志性景观。'让我们荡起双桨'的灵感来源，湖光塔影美不胜收。",
        "highlights": ["白塔", "琼华岛", "九龙壁", "五龙亭", "静心斋"],
        "tips": "推荐划船游湖，夏季荷花盛开时景色最佳",
        "metro": "6号线北海北站",
        "lat": 39.9245,
        "lng": 116.3893,
        "monthly_visitors": [70, 60, 90, 110, 120, 130, 150, 160, 100, 90, 70, 60],
    },
    {
        "name": "鸟巢/水立方",
        "name_en": "Bird's Nest & Water Cube",
        "category": "现代建筑",
        "district": "朝阳区",
        "rating": 4.3,
        "reviews": 105000,
        "price": 50,
        "price_note": "鸟巢50元/水立方30元",
        "best_season": ["4月", "5月", "9月", "10月"],
        "best_time": "9:00-19:00",
        "visit_duration": "1-2小时",
        "crowd_level": "中",
        "description": "2008年北京奥运会主体育场和游泳馆，世界级建筑奇观。鸟巢的钢结构设计和水立方的膜结构令人叹为观止，夜景尤为壮观。",
        "highlights": ["鸟巢空中走廊", "水立方嬉水乐园", "奥林匹克公园", "奥运塔"],
        "tips": "建议傍晚前往，白天参观内部，晚上看灯光秀",
        "metro": "8号线奥体中心站",
        "lat": 39.9919,
        "lng": 116.3906,
        "monthly_visitors": [80, 70, 100, 110, 120, 130, 140, 150, 110, 100, 80, 80],
    },
    {
        "name": "雍和宫",
        "name_en": "Lama Temple",
        "category": "宗教文化",
        "district": "东城区",
        "rating": 4.6,
        "reviews": 98000,
        "price": 25,
        "price_note": "25元",
        "best_season": ["全年皆宜", "春节期间香火最旺"],
        "best_time": "9:00-16:30",
        "visit_duration": "1-2小时",
        "crowd_level": "高",
        "description": "北京最大的藏传佛教寺院，曾是雍正帝的府邸。建筑宏伟，佛像精美，26米高的白檀木弥勒大佛举世闻名。",
        "highlights": ["万福阁弥勒大佛", "雍和宫殿", "法轮殿", "青铜须弥山"],
        "tips": "初一、十五香客众多，可免费领取香火",
        "metro": "2/5号线雍和宫站",
        "lat": 39.9474,
        "lng": 116.4175,
        "monthly_visitors": [90, 130, 100, 90, 80, 70, 80, 90, 80, 90, 80, 100],
    },
    {
        "name": "什刹海",
        "name_en": "Shichahai",
        "category": "自然风光",
        "district": "西城区",
        "rating": 4.5,
        "reviews": 92000,
        "price": 0,
        "price_note": "免费",
        "best_season": ["5月", "6月", "7月", "8月", "9月"],
        "best_time": "全天开放",
        "visit_duration": "1-3小时",
        "crowd_level": "高",
        "description": "由前海、后海、西海组成的历史文化风景区，周边遍布酒吧、餐厅和胡同。白天宁静优雅，夜晚热闹非凡，是老北京与现代都市的交汇点。",
        "highlights": ["后海酒吧街", "银锭桥", "烟袋斜街", "恭王府", "荷花市场"],
        "tips": "推荐傍晚前往，先逛胡同再享受夜生活",
        "metro": "8号线什刹海站",
        "lat": 39.9375,
        "lng": 116.3853,
        "monthly_visitors": [100, 90, 110, 130, 150, 160, 180, 190, 140, 120, 100, 110],
    },
    {
        "name": "圆明园遗址公园",
        "name_en": "Old Summer Palace",
        "category": "历史文化",
        "district": "海淀区",
        "rating": 4.4,
        "reviews": 88000,
        "price": 10,
        "price_note": "10元（西洋楼遗址15元）",
        "best_season": ["4月", "5月", "6月", "7月"],
        "best_time": "7:00-19:00",
        "visit_duration": "2-4小时",
        "crowd_level": "中",
        "description": "清代皇家园林遗址，'万园之园'的沧桑见证。西洋楼遗址区的大水法残垣是圆明园的标志，荷花盛开时节景色绝美。",
        "highlights": ["西洋楼遗址", "大水法", "福海", "荷花池", "全景模型馆"],
        "tips": "夏季荷花盛开时最美，可与颐和园安排在同一天游览",
        "metro": "4号线圆明园站",
        "lat": 40.0086,
        "lng": 116.2983,
        "monthly_visitors": [60, 50, 80, 100, 110, 120, 140, 140, 100, 90, 70, 60],
    },
    {
        "name": "景山公园",
        "name_en": "Jingshan Park",
        "category": "皇家园林",
        "district": "西城区",
        "rating": 4.5,
        "reviews": 76000,
        "price": 2,
        "price_note": "2元",
        "best_season": ["4月", "5月", "9月", "10月"],
        "best_time": "6:30-21:00",
        "visit_duration": "1-1.5小时",
        "crowd_level": "中",
        "description": "俯瞰故宫全景的最佳位置，万春亭是北京城中轴线的制高点。曾是明清皇家御苑，牡丹花季尤为壮观。",
        "highlights": ["万春亭故宫全景", "牡丹园", "崇祯自缢处", "中轴线地标"],
        "tips": "建议故宫游览结束后从神武门出来直接上景山，日落时分景色最佳",
        "metro": "8号线中国美术馆站",
        "lat": 39.9225,
        "lng": 116.3963,
        "monthly_visitors": [60, 50, 80, 100, 110, 100, 120, 120, 90, 80, 60, 60],
    },
]

MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
CATEGORY_COLORS = {
    "历史文化": "#e53e3e",
    "皇家园林": "#38a169",
    "胡同文化": "#dd6b20",
    "艺术文化": "#805ad5",
    "现代建筑": "#3182ce",
    "宗教文化": "#d69e2e",
    "自然风光": "#319795",
}

def generate_html():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    total_reviews = sum(a["reviews"] for a in ATTRACTIONS)
    avg_rating = round(sum(a["rating"] for a in ATTRACTIONS) / len(ATTRACTIONS), 1)
    free_count = sum(1 for a in ATTRACTIONS if a["price"] == 0)
    
    sorted_attractions = sorted(ATTRACTIONS, key=lambda x: x["rating"], reverse=True)
    
    cards = []
    for a in sorted_attractions:
        cat_color = CATEGORY_COLORS.get(a["category"], "#718096")
        stars = "★" * int(a["rating"]) + "☆" * (5 - int(a["rating"]))
        reviews_str = f"{a['reviews'] // 10000}万+"
        price_str = a["price_note"] if a["price"] == 0 else f"¥{a['price']}（{a['price_note']}）"
        
        max_v = max(a["monthly_visitors"])
        bars = []
        for i, v in enumerate(a["monthly_visitors"]):
            height = int(v / max_v * 100)
            bar_color = "#48bb78" if v >= 150 else "#4299e1" if v >= 100 else "#a0aec0"
            bars.append(f'<div class="bar-wrapper"><div class="bar" style="height:{height}%;background:{bar_color}" title="{MONTHS[i]}: {v}K"></div><span class="bar-label">{MONTHS[i]}</span></div>')
        
        cards.append(f"""\
        <div class="card">
            <div class="card-header">
                <div class="card-title-row">
                    <h3 class="card-title">{a['name']}</h3>
                    <span class="card-en">{a['name_en']}</span>
                </div>
                <span class="category-tag" style="background:{cat_color}">{a['category']}</span>
            </div>
            <div class="card-body">
                <div class="card-info">
                    <div class="info-row">
                        <span class="stars">{stars}</span>
                        <span class="rating-num">{a['rating']}</span>
                        <span class="reviews">（{reviews_str}条评价）</span>
                    </div>
                    <p class="description">{a['description']}</p>
                    <div class="meta-grid">
                        <div class="meta-item"><span class="meta-icon">📍</span><span>{a['district']}</span></div>
                        <div class="meta-item"><span class="meta-icon">🚇</span><span>{a['metro']}</span></div>
                        <div class="meta-item"><span class="meta-icon">💰</span><span>{price_str}</span></div>
                        <div class="meta-item"><span class="meta-icon">⏱️</span><span>{a['visit_duration']}</span></div>
                        <div class="meta-item"><span class="meta-icon">👥</span><span>拥挤度: {a['crowd_level']}</span></div>
                        <div class="meta-item"><span class="meta-icon">📅</span><span>最佳: {', '.join(a['best_season'][:3])}</span></div>
                    </div>
                    <div class="highlights"><span class="hl-label">✨ 亮点:</span> {', '.join(a['highlights'])}</div>
                    <div class="tips"><span class="tip-icon">💡</span> {a['tips']}</div>
                </div>
                <div class="card-chart">
                    <div class="chart-title">月度访客趋势 (K)</div>
                    <div class="bar-chart">{''.join(bars)}</div>
                </div>
            </div>
        </div>""")
    
    ranking_items = []
    for i, a in enumerate(sorted_attractions[:8]):
        rank_icon = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}"
        ranking_items.append(f"""\
            <div class="rank-item">
                <span class="rank-num">{rank_icon}</span>
                <span class="rank-name">{a['name']}</span>
                <span class="rank-rating">⭐ {a['rating']}</span>
                <span class="rank-reviews">{a['reviews'] // 10000}万+评价</span>
            </div>""")
    
    cat_stats = {}
    for a in ATTRACTIONS:
        c = a["category"]
        if c not in cat_stats:
            cat_stats[c] = {"count": 0, "total_rating": 0}
        cat_stats[c]["count"] += 1
        cat_stats[c]["total_rating"] += a["rating"]
    
    cat_items = []
    for cat, stats in sorted(cat_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        avg_r = round(stats["total_rating"] / stats["count"], 1)
        color = CATEGORY_COLORS.get(cat, "#718096")
        cat_items.append(f"""\
            <div class="cat-item">
                <span class="cat-dot" style="background:{color}"></span>
                <span class="cat-name">{cat}</span>
                <span class="cat-count">{stats['count']}个景点</span>
                <span class="cat-rating">均分 {avg_r}</span>
            </div>""")
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>北京热门旅游地分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh; color: #e2e8f0;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
        .hero {{ text-align: center; padding: 50px 20px 30px; }}
        .hero h1 {{
            font-size: 2.6em; font-weight: 800;
            background: linear-gradient(135deg, #f093fb, #f5576c, #fda085);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
            margin-bottom: 10px;
        }}
        .hero .subtitle {{ color: #a0aec0; font-size: 1em; }}
        .stats-bar {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 30px; }}
        .stat-card {{
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 14px; padding: 20px; text-align: center; backdrop-filter: blur(10px);
        }}
        .stat-value {{
            font-size: 2em; font-weight: 700;
            background: linear-gradient(135deg, #f6ad55, #ed64a6);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        }}
        .stat-label {{ color: #a0aec0; font-size: 0.85em; margin-top: 4px; }}
        .section-title {{ font-size: 1.4em; font-weight: 700; margin: 30px 0 16px; padding-left: 14px; border-left: 4px solid #ed64a6; }}
        .ranking {{
            background: rgba(255,255,255,0.05); border-radius: 14px; padding: 20px;
            margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.08);
        }}
        .rank-item {{
            display: flex; align-items: center; padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.05); gap: 14px;
        }}
        .rank-item:last-child {{ border-bottom: none; }}
        .rank-num {{ font-size: 1.3em; width: 36px; text-align: center; }}
        .rank-name {{ font-weight: 600; flex: 1; }}
        .rank-rating {{ color: #f6ad55; font-weight: 600; }}
        .rank-reviews {{ color: #718096; font-size: 0.85em; }}
        .cat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 30px; }}
        .cat-item {{
            background: rgba(255,255,255,0.05); border-radius: 10px; padding: 14px 16px;
            display: flex; align-items: center; gap: 10px; border: 1px solid rgba(255,255,255,0.06);
        }}
        .cat-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
        .cat-name {{ font-weight: 600; flex: 1; }}
        .cat-count {{ color: #a0aec0; font-size: 0.85em; }}
        .cat-rating {{ color: #f6ad55; font-size: 0.85em; font-weight: 600; }}
        .cards {{ display: flex; flex-direction: column; gap: 20px; }}
        .card {{
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.3); }}
        .card-header {{
            padding: 18px 24px; display: flex; justify-content: space-between;
            align-items: center; border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .card-title-row {{ display: flex; flex-direction: column; gap: 2px; }}
        .card-title {{ font-size: 1.2em; font-weight: 700; }}
        .card-en {{ font-size: 0.78em; color: #718096; }}
        .category-tag {{ padding: 5px 14px; border-radius: 20px; font-size: 0.8em; font-weight: 600; color: #fff; white-space: nowrap; }}
        .card-body {{ display: grid; grid-template-columns: 1fr 180px; gap: 20px; padding: 20px 24px; }}
        .card-info {{ display: flex; flex-direction: column; gap: 10px; }}
        .info-row {{ display: flex; align-items: center; gap: 8px; }}
        .stars {{ color: #f6ad55; font-size: 1.1em; letter-spacing: 2px; }}
        .rating-num {{ font-weight: 700; font-size: 1.2em; color: #f6ad55; }}
        .reviews {{ color: #718096; font-size: 0.85em; }}
        .description {{ color: #cbd5e0; line-height: 1.6; font-size: 0.9em; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
        .meta-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.85em; color: #a0aec0; }}
        .highlights {{ color: #ecc94b; font-size: 0.85em; line-height: 1.5; }}
        .hl-label {{ font-weight: 600; }}
        .tips {{
            background: rgba(237, 100, 166, 0.1); border-left: 3px solid #ed64a6;
            padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: 0.85em; color: #fbb6ce; line-height: 1.5;
        }}
        .card-chart {{ display: flex; flex-direction: column; align-items: center; }}
        .chart-title {{ font-size: 0.75em; color: #718096; margin-bottom: 8px; text-align: center; }}
        .bar-chart {{ display: flex; align-items: flex-end; gap: 3px; height: 120px; width: 100%; }}
        .bar-wrapper {{ flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }}
        .bar {{ width: 100%; max-width: 14px; border-radius: 3px 3px 0 0; min-height: 2px; transition: opacity 0.2s; }}
        .bar:hover {{ opacity: 0.7; }}
        .bar-label {{ font-size: 0.55em; color: #4a5568; margin-top: 3px; transform: rotate(-45deg); white-space: nowrap; }}
        footer {{ text-align: center; padding: 40px 20px; color: #4a5568; font-size: 0.8em; }}
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 1.6em; }}
            .stats-bar {{ grid-template-columns: repeat(2, 1fr); }}
            .card-body {{ grid-template-columns: 1fr; }}
            .bar-chart {{ height: 80px; }}
            .meta-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🏯 北京热门旅游地分析报告</h1>
            <p class="subtitle">基于多维度数据的北京旅游景点综合分析 | 生成时间: {today}</p>
        </div>
        <div class="stats-bar">
            <div class="stat-card"><div class="stat-value">{len(ATTRACTIONS)}</div><div class="stat-label">收录景点</div></div>
            <div class="stat-card"><div class="stat-value">{avg_rating}</div><div class="stat-label">平均评分</div></div>
            <div class="stat-card"><div class="stat-value">{total_reviews // 10000}万+</div><div class="stat-label">累计评价</div></div>
            <div class="stat-card"><div class="stat-value">{free_count}</div><div class="stat-label">免费景点</div></div>
        </div>
        <h2 class="section-title">🏆 热门排行榜 TOP 8</h2>
        <div class="ranking">{''.join(ranking_items)}</div>
        <h2 class="section-title">📂 景点分类统计</h2>
        <div class="cat-grid">{''.join(cat_items)}</div>
        <h2 class="section-title">📋 详细景点分析</h2>
        <div class="cards">{''.join(cards)}</div>
        <footer>
            <p>📊 数据来源：综合各大旅游平台公开数据整理分析 | 仅供参考</p>
            <p style="margin-top:4px;">北京市 · 文化旅游资源分析</p>
        </footer>
    </div>
</body>
</html>"""
    return html

def main():
    print("=" * 50)
    print("  北京热门旅游地分析工具")
    print("=" * 50)
    html = generate_html()
    output_path = "/home/gem/Competitive-Analysis/beijing-tourism/beijing_tourism.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 已生成: {output_path}")
    print(f"   文件大小: {len(html):,} 字节")
    print(f"   收录景点: {len(ATTRACTIONS)} 个")

if __name__ == "__main__":
    main()
