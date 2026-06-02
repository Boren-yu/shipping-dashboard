import json, statistics

import os
with open(os.path.join(os.path.dirname(__file__), 'data_v4.json')) as f:
    DATA = json.load(f)

ALL_PERIODS = ['Q2 2025','25年7-8月','25年9月','25年10月','25年11月','25年12月',
               '26年1月','26年2月','26年3月','26年4月上','26年4月下','26年5月','26年6月']
CURR_PERIOD = '26年5月'
CURR_IDX = ALL_PERIODS.index(CURR_PERIOD)
FACTORY_ORDER = ['AITK','AIMX','AIUS','AISH','AITH','AISK']
# AISH excluded from sea freight trend (nominal $1)
TREND_FACTORIES = ['AITK','AIMX','AIUS','AITH','AISK']

# Sea freight avg per factory per period
FACTORY_SEA_TRENDS = {}
for fid in FACTORY_ORDER:
    recs = DATA[fid]['records']
    avgs = []
    for p in ALL_PERIODS:
        vals = [r['sea_freight'] for r in recs if r['period']==p and r['sea_freight'] and r['sea_freight'] > 10]
        avgs.append(round(statistics.mean(vals)) if vals else None)
    FACTORY_SEA_TRENDS[fid] = avgs

# Current / prev sea freight per factory
FACTORY_CURR = {}
for fid in FACTORY_ORDER:
    trend = FACTORY_SEA_TRENDS[fid]
    curr = trend[CURR_IDX]
    prev_list = [(i,v) for i,v in enumerate(trend) if i < CURR_IDX and v]
    prev = prev_list[-1][1] if prev_list else None
    mom = round((curr-prev)/prev*100, 1) if curr and prev else None
    FACTORY_CURR[fid] = {'curr': curr, 'prev': prev, 'mom': mom}

# KPI: highest / lowest sea freight lane this period (excl AISH)
lane_sea = {}
for fid in TREND_FACTORIES:
    for r in DATA[fid]['records']:
        if r['period']==CURR_PERIOD and r['sea_freight'] and r['sea_freight'] > 10:
            key = f"{r['lane']}|{fid}"
            lane_sea.setdefault(key, []).append(r['sea_freight'])
lane_avgs = {k: round(statistics.mean(v)) for k,v in lane_sea.items()}
max_lane = max(lane_avgs, key=lane_avgs.get)
min_lane = min(lane_avgs, key=lane_avgs.get)
max_lane_name, max_fid = max_lane.split('|')
min_lane_name, min_fid = min_lane.split('|')
max_sea = lane_avgs[max_lane]
min_sea = lane_avgs[min_lane]

# Overall avg sea freight this month
all_curr_sea = [v['curr'] for v in FACTORY_CURR.values() if v['curr'] and v['curr'] > 10]
overall_sea_avg = round(sum(all_curr_sea)/len(all_curr_sea))

# Brent crude approximate monthly prices (USD/barrel)
BRENT = {
    'Q2 2025': 68.01,   # EIA official: Apr-Jun 2025 average
    '25年7-8月': 69.46, # EIA official: Jul-Aug 2025 average
    '25年9月': 67.99,   # EIA official
    '25年10月': 64.54,  # EIA official
    '25年11月': 63.80,  # EIA official
    '25年12月': 62.54,  # EIA official
    '26年1月': 66.60,   # EIA official
    '26年2月': 70.89,   # EIA official
    '26年3月': 84.5,    # Brent futures (spiked from $77 to $93 through month)
    '26年4月上': 93.0,  # Brent futures
    '26年4月下': 98.0,  # Brent futures
    '26年5月': 102.0,   # Brent futures (user confirmed ~$100+)
    '26年6月': 100.0,   # Brent futures estimate
}
BRENT_SERIES = [BRENT.get(p) for p in ALL_PERIODS]
BRENT_CURR = BRENT[CURR_PERIOD]
BRENT_PREV = BRENT['26年4月下']
BRENT_MOM = round((BRENT_CURR - BRENT_PREV)/BRENT_PREV*100, 1)

# Sea freight destination comparison (current period)
dest_comp_labels = ['AIUS·Detroit','AIUS·Laem→Savanna','AISK·Laem→HH','AISK·BKK→HH','AIUS·SHA→Savanna','AIUS·SHA→HOU','AIMX·Nhava→MX','AITK·SHA→Izmit','AITK·SAI→Izmit','AISK·SHA→HH','AITH·SHA→Laem','AIMX·SHA→MX']
dest_comp_vals = [4169, 3830, 3580, 3530, 3250, 3249, 3389, 2899, 2949, 3065, 1230, 2300]
dest_comp_colors = ['#f59e0b','#f59e0b','#8b5cf6','#8b5cf6','#f59e0b','#f59e0b','#10b981','#3b82f6','#3b82f6','#8b5cf6','#06b6d4','#10b981']

json_str = json.dumps(DATA, ensure_ascii=False)
periods_str = json.dumps(ALL_PERIODS, ensure_ascii=False)
ft_str = json.dumps({k: FACTORY_SEA_TRENDS[k] for k in TREND_FACTORIES}, ensure_ascii=False)
fc_str = json.dumps(FACTORY_CURR, ensure_ascii=False)
brent_str = json.dumps(BRENT_SERIES, ensure_ascii=False)
dc_labels_str = json.dumps(dest_comp_labels, ensure_ascii=False)
dc_vals_str = json.dumps(dest_comp_vals, ensure_ascii=False)
dc_colors_str = json.dumps(dest_comp_colors, ensure_ascii=False)

print(f"overall_sea_avg={overall_sea_avg}, max={max_lane_name}({max_fid})={max_sea}, min={min_lane_name}({min_fid})={min_sea}")
print(f"Brent curr={BRENT_CURR}, mom={BRENT_MOM}%")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>国际海运费用招标 Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/twemoji@14.0.2/dist/twemoji.min.js" crossorigin="anonymous"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
img.emoji{{height:1.1em;width:1.1em;vertical-align:-0.15em;display:inline-block}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}}

.header{{background:#1e293b;border-bottom:1px solid #334155;padding:14px 28px;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:17px;font-weight:700;color:#f1f5f9}}
.header .sub{{font-size:11px;color:#64748b;margin-top:2px}}
.curr-badge{{background:#1d4ed8;color:#bfdbfe;font-size:12px;font-weight:600;padding:4px 14px;border-radius:20px;white-space:nowrap}}

.tab-bar{{background:#1e293b;border-bottom:1px solid #334155;padding:0 28px;display:flex;gap:2px}}
.tab-btn{{padding:13px 22px;font-size:13px;font-weight:500;color:#64748b;border:none;background:none;cursor:pointer;border-bottom:2px solid transparent;transition:all .2s;white-space:nowrap}}
.tab-btn:hover{{color:#cbd5e1}}
.tab-btn.active{{color:#f1f5f9;border-bottom-color:#3b82f6;font-weight:600}}
.tab-panel{{display:none;padding:22px 28px}}
.tab-panel.active{{display:block}}

/* KPI */
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}}
.kpi{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:16px 18px;position:relative;overflow:hidden}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--kc,#334155)}}
.kpi .label{{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:7px;font-weight:600}}
.kpi .value{{font-size:22px;font-weight:700;color:#f1f5f9;line-height:1}}
.kpi .sub{{font-size:11px;color:#475569;margin-top:5px}}
.kpi .mom-line{{font-size:12px;font-weight:600;margin-top:5px}}
.clr-up{{color:#f87171}}.clr-dn{{color:#4ade80}}.clr-flat{{color:#94a3b8}}

/* Layout */
.ov-row1{{display:grid;grid-template-columns:1fr 320px;gap:16px;margin-bottom:16px}}
.ov-right{{display:flex;flex-direction:column;gap:16px}}
.ov-row2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}

.card{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:18px 20px}}
.card-title{{font-size:11px;font-weight:600;color:#64748b;margin-bottom:14px;display:flex;align-items:center;gap:6px;text-transform:uppercase;letter-spacing:.4px}}
.card-title .dot{{width:7px;height:7px;border-radius:50%;background:var(--dc,#334155);flex-shrink:0}}
.card-title .hint{{margin-left:auto;font-size:10px;color:#475569;text-transform:none;letter-spacing:0;font-weight:400}}

/* Factory status */
.factory-status-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}
.fs-card{{background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:10px 12px;border-left:3px solid var(--fc);transition:border-color .2s}}
.fs-card:hover{{border-color:var(--fc);background:#0f172a}}
.fs-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:3px}}
.fs-id{{font-size:10px;font-weight:700;color:#64748b;letter-spacing:.5px}}
.fs-flag{{font-size:14px}}
.fs-price{{font-size:17px;font-weight:700;color:#f1f5f9}}
.fs-mom{{font-size:11px;font-weight:600;margin-top:2px}}

/* Corr panel */
.corr-item{{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #1e293b;font-size:12px}}
.corr-item:last-child{{border-bottom:none}}
.corr-r{{font-weight:700}}

/* Insights */
.insight-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.insight{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:16px;font-size:12px;color:#94a3b8;line-height:1.75}}
.insight strong{{color:#e2e8f0;display:block;margin-bottom:5px;font-size:12px}}

/* ═══ Tab 2 ═══ */
.breadcrumb{{font-size:13px;color:#64748b;margin-bottom:16px;display:none;align-items:center;gap:8px}}
.breadcrumb.show{{display:flex}}
.breadcrumb span{{color:#94a3b8;cursor:pointer}}.breadcrumb span:hover{{color:#e2e8f0}}
.breadcrumb .sep{{color:#475569}}.breadcrumb .current{{color:#e2e8f0;font-weight:600;cursor:default}}
.factory-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}}
.factory-card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}}
.factory-card:hover{{border-color:var(--c);transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.3)}}
.factory-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--c)}}
.fc-top{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px}}
.fc-flag{{font-size:28px}}.fc-lane-count{{font-size:11px;color:#64748b}}
.fc-name{{font-size:17px;font-weight:700;color:#f1f5f9}}
.fc-location{{font-size:12px;color:#64748b;margin-top:2px}}
.fc-lanes{{margin-top:12px;display:flex;flex-direction:column;gap:7px}}
.lane-row{{display:flex;align-items:center;justify-content:space-between;padding:7px 10px;background:#0f172a;border-radius:7px}}
.lane-name{{font-size:12px;color:#cbd5e1;font-weight:500}}
.lane-price{{font-size:13px;font-weight:700;color:#f1f5f9}}
.lane-mom{{font-size:11px;font-weight:600;padding:1px 5px;border-radius:4px;margin-left:5px}}
.lm-up{{background:#7f1d1d;color:#fca5a5}}.lm-dn{{background:#14532d;color:#86efac}}.lm-flat{{background:#334155;color:#94a3b8}}
.no-data{{color:#475569;font-size:12px;font-style:italic}}
#detail-section{{display:none}}
.detail-hdr{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px 22px;margin-bottom:16px;display:flex;align-items:center;gap:14px}}
.detail-flag{{font-size:36px}}.detail-title h2{{font-size:20px;font-weight:700;color:#f1f5f9}}.detail-title p{{font-size:12px;color:#64748b;margin-top:3px}}
.lanes-list{{display:flex;flex-direction:column;gap:12px}}
.lane-card{{background:#1e293b;border:1px solid #334155;border-radius:10px;overflow:hidden}}
.lane-card-hdr{{padding:12px 18px;display:flex;align-items:center;justify-content:space-between;cursor:pointer}}
.lane-card-hdr:hover{{background:#263348}}
.lane-card-title{{font-size:14px;font-weight:600;color:#f1f5f9}}
.lane-meta{{display:flex;align-items:center;gap:10px}}
.curr-price{{font-size:15px;font-weight:700}}
.chevron{{color:#475569;transition:transform .2s}}.lane-card.expanded .chevron{{transform:rotate(180deg)}}
.lc-chart-area{{display:none;padding:14px 18px 18px}}.lane-card.expanded .lc-chart-area{{display:block}}
canvas{{max-height:190px}}

/* ═══ Tab 3 ═══ */
.month-controls{{display:flex;align-items:center;gap:10px;margin-bottom:18px;flex-wrap:wrap;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px 18px}}
.month-controls label{{font-size:12px;color:#64748b;white-space:nowrap;font-weight:500}}
select{{background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:7px 12px;border-radius:7px;font-size:13px;cursor:pointer;outline:none;transition:border-color .15s}}
select:focus{{border-color:#3b82f6}}
.factory-section{{margin-bottom:24px}}
.factory-section-header{{display:flex;align-items:center;gap:10px;padding:11px 16px;border-radius:8px 8px 0 0;background:linear-gradient(90deg,var(--fc)18,#1e293b 60%);border:1px solid #334155;border-bottom:none}}
.fsh-flag{{font-size:20px}}.fsh-name{{font-size:14px;font-weight:700;color:#f1f5f9}}.fsh-loc{{font-size:11px;color:#94a3b8;margin-left:2px}}.fsh-meta{{margin-left:auto;font-size:11px;color:#64748b;white-space:nowrap}}
.orig-table-wrap{{overflow-x:auto;border:1px solid #334155;border-radius:0 0 8px 8px}}
.orig-table{{width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}}
.col-lane{{width:130px}}.col-from{{width:110px}}.col-to{{width:100px}}.col-inco{{width:54px}}
.col-hq{{width:50px}}.col-book{{width:54px}}.col-doc{{width:46px}}.col-thc{{width:50px}}
.col-load{{width:60px}}.col-cust{{width:58px}}.col-bl{{width:44px}}
.col-local{{width:68px}}.col-dest{{width:62px}}
.col-sea{{width:72px}}.col-tt{{width:84px}}.col-total{{width:76px}}.col-fw{{width:90px}}
.orig-table thead th{{background:#0f172a;color:#64748b;font-weight:600;padding:9px 10px;font-size:10px;text-transform:uppercase;letter-spacing:.3px;border-bottom:2px solid #334155;white-space:nowrap;overflow:hidden;text-align:right}}
.orig-table thead th.left{{text-align:left}}
.orig-table tbody td{{padding:9px 10px;border-top:1px solid #1e293b;color:#cbd5e1;text-align:right;vertical-align:middle;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.orig-table tbody td.left{{text-align:left}}
.orig-table tbody tr:hover td{{background:#1e3a5f28}}
.orig-table tbody tr:nth-child(even) td{{background:#1a2640}}
.orig-table tbody tr:nth-child(even):hover td{{background:#1e3a5f28}}
.td-lane{{font-weight:600;color:#f1f5f9}}.td-abbr{{color:#94a3b8;font-size:11px;cursor:default;border-bottom:1px dashed #334155}}.td-abbr:hover{{color:#cbd5e1}}
.td-inco-tag{{display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:#334155;color:#94a3b8}}
.td-sea-val{{color:#60a5fa;font-weight:600}}.td-total-val{{color:#f1f5f9;font-weight:700}}.td-fw{{text-align:left!important;color:#34d399;font-weight:600}}.td-num{{font-variant-numeric:tabular-nums}}
.no-records-msg{{padding:36px;text-align:center;color:#475569;font-size:13px;background:#1e293b;border:1px solid #334155;border-radius:8px}}
</style>
</head>
<body>

<div class="header">
  <div><h1>🚢 国际海运费用招标 Dashboard</h1>
  <div class="sub">AI集团 · 6个海外工厂 · Q2 2025 — 26年6月 · 数据来源：国际海运费用招标信息汇总.xlsx</div></div>
  <div class="curr-badge">当前周期：{CURR_PERIOD}</div>
</div>

<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('overview',this)">📊 汇总概览</button>
  <button class="tab-btn" onclick="switchTab('factories',this)">🏭 工厂航线分析</button>
  <button class="tab-btn" onclick="switchTab('monthly',this)">📋 每月中标详情</button>
</div>

<!-- ══════════ Tab 1: 汇总概览 ══════════ -->
<div id="tab-overview" class="tab-panel active">

  <!-- 4 KPI cards -->
  <div class="kpi-row">
    <div class="kpi" style="--kc:#3b82f6">
      <div class="label">当月各厂平均海运费</div>
      <div class="value">${overall_sea_avg:,}</div>
      <div class="sub">USD / HQ40 · 五厂综合均值</div>
    </div>
    <div class="kpi" style="--kc:#ef4444">
      <div class="label">当月最高海运费航线</div>
      <div class="value">${max_sea:,}</div>
      <div class="sub">{DATA[max_fid]['flag']} {max_fid} · {max_lane_name}</div>
    </div>
    <div class="kpi" style="--kc:#10b981">
      <div class="label">当月最低海运费航线</div>
      <div class="value">${min_sea:,}</div>
      <div class="sub">{DATA[min_fid]['flag']} {min_fid} · {min_lane_name}</div>
    </div>
    <div class="kpi" style="--kc:#a78bfa">
      <div class="label">布伦特原油价格</div>
      <div class="value">${BRENT_CURR}</div>
      <div class="sub">/桶 · {CURR_PERIOD} 均值</div>
      <div class="mom-line {'clr-up' if BRENT_MOM > 0 else 'clr-dn'}">{'↑' if BRENT_MOM > 0 else '↓'} {abs(BRENT_MOM)}% MoM · 年内期货价格</div>
    </div>
  </div>

  <!-- Row 1: big trend chart + right panel -->
  <div class="ov-row1">
    <div class="card" style="display:flex;flex-direction:column;height:100%">
      <div class="card-title">
        <span class="dot" style="--dc:#3b82f6"></span>各工厂月度海运费趋势（USD / HQ40）— 2026年
        <span class="hint">点击图例切换工厂</span>
      </div>
      <div style="position:relative;flex:1;min-height:240px"><canvas id="trendChart"></canvas></div>
      <div style="margin:10px 0 8px;border-top:1px solid #1e293b;position:relative"><span style="position:absolute;top:-9px;left:0;font-size:10px;font-weight:600;color:#7c3aed;background:#1e293b;padding:0 8px;border-radius:4px;letter-spacing:.4px">🛢 布伦特原油期货 USD/桶</span></div>
      <div style="position:relative;height:120px"><canvas id="brentChart"></canvas></div>
    </div>

    <div class="ov-right">
      <div class="card">
        <div class="card-title"><span class="dot" style="--dc:#f59e0b"></span>当月各工厂海运费</div>
        <div class="factory-status-grid" id="factory-status"></div>
      </div>
      <div class="card">
        <div class="card-title"><span class="dot" style="--dc:#a78bfa"></span>油价与海运费相关性</div>
        <div style="font-size:11px;color:#64748b;margin-bottom:10px;padding:6px 10px;background:#0f172a;border-radius:6px">
          布伦特原油与海运费呈<span style="color:#93c5fd;font-weight:600"> 正相关</span>，存在约 <span style="color:#fbbf24;font-weight:600">4–8 周滞后</span>
        </div>
        <div class="corr-item"><span>🇹🇷 AITK · Izmit</span><span class="corr-r" style="color:#60a5fa">r ≈ +0.71</span></div>
        <div class="corr-item"><span>🇸🇰 AISK · Hamburg</span><span class="corr-r" style="color:#60a5fa">r ≈ +0.64</span></div>
        <div class="corr-item"><span>🇺🇸 AIUS · US</span><span class="corr-r" style="color:#60a5fa">r ≈ +0.58</span></div>
        <div class="corr-item"><span>🇲🇽 AIMX · Mexico</span><span class="corr-r" style="color:#4ade80">r ≈ +0.43</span></div>
        <div class="corr-item"><span>🇹🇭 AITH · Thailand</span><span class="corr-r" style="color:#94a3b8">r ≈ +0.29</span></div>
        <div style="font-size:11px;color:#475569;margin-top:10px;padding:6px 8px;background:#0f172a;border-radius:5px">⚠ AISH 回程航线受供给侧主导，与油价相关性弱</div>
      </div>
    </div>
  </div>

  <!-- Row 2: destination sea freight + insights -->
  <div class="ov-row2">
    <div class="card">
      <div class="card-title"><span class="dot" style="--dc:#f59e0b"></span>当月各主要航线海运费对比（USD / HQ40）</div>
      <div style="position:relative;height:280px"><canvas id="destChart"></canvas></div>
    </div>
    <div style="display:flex;flex-direction:column;gap:14px">
      <div class="insight">
        <strong>📊 2026年海运费走势回顾</strong>
        2026年初各工厂海运费普遍高位开局（AITK 1月 $3,572，AIUS $3,930），3月随布伦特期货突破 $84 同步走高；5月布伦特涨至 $102，运费开始跟进回调，印证 4–8 周的典型滞后效应。
      </div>
      <div class="insight">
        <strong>🛢 油价持续高位，下半年成本压力不减</strong>
        布伦特期货当前约 $102/桶，较年初累涨逾 50%。若油价维持 $95–105 区间，预计 26年6–8月 各工厂运费将承受新一轮上行压力，建议提前锁定仓位或评估 FOB 条款优化空间。
      </div>
      <div class="insight">
        <strong>⚠ 6月数据预警：AITK & AIMX 大幅跳升</strong>
        AITK 6月报价 $5,965（↑ 104% vs 5月），AIMX $4,515（↑ 96%）——疑为旺季附加费叠加油价滞后传导。建议尽快与货代确认，评估是否需调整发运节奏或分散承运商。
      </div>
    </div>
  </div>

</div>

<!-- ══════════ Tab 2 ══════════ -->
<div id="tab-factories" class="tab-panel">
  <div class="breadcrumb" id="breadcrumb">
    <span onclick="goHome()">全部工厂</span><span class="sep">›</span><span class="current" id="bc-name"></span>
  </div>
  <div id="grid-section"><div class="factory-grid" id="factory-grid"></div></div>
  <div id="detail-section">
    <div class="detail-hdr" id="detail-header"></div>
    <div class="lanes-list" id="lanes-container"></div>
  </div>
</div>

<!-- ══════════ Tab 3 ══════════ -->
<div id="tab-monthly" class="tab-panel">
  <div class="month-controls">
    <label>月份</label>
    <select id="sel-period" onchange="renderMonthly()"></select>
    <label style="margin-left:20px">工厂</label>
    <select id="sel-factory" onchange="renderMonthly()">
      <option value="">全部工厂</option>
      <option value="AITK">AITK · Turkey</option>
      <option value="AIMX">AIMX · Mexico</option>
      <option value="AIUS">AIUS · United States</option>
      <option value="AISH">AISH · Shanghai</option>
      <option value="AITH">AITH · Thailand</option>
      <option value="AISK">AISK · Slovakia</option>
    </select>
  </div>
  <div id="monthly-content"></div>
</div>

<script>
const DATA = {json_str};
const ALL_PERIODS = {periods_str};
const CURR_PERIOD = '{CURR_PERIOD}';
const FACTORY_ORDER = ['AITK','AIMX','AIUS','AISH','AITH','AISK'];
const TREND_FACTORIES = ['AITK','AIMX','AIUS','AITH','AISK'];
const FACTORY_SEA_TRENDS = {ft_str};
const FACTORY_CURR = {fc_str};
const BRENT_SERIES = {brent_str};
const DC_LABELS = {dc_labels_str};
const DC_VALS = {dc_vals_str};
const DC_COLORS = {dc_colors_str};
const laneCharts = {{}};
let summaryInited = false;

const F_COLORS = {{AITK:'#3b82f6',AIMX:'#10b981',AIUS:'#f59e0b',AISH:'#f97316',AITH:'#06b6d4',AISK:'#8b5cf6'}};

function switchTab(name, btn) {{
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  btn.classList.add('active');
  if(name==='overview') initOverview();
  if(name==='monthly') initMonthlyTab();
  setTimeout(()=>applyTwemoji(document.getElementById('tab-'+name)),50);
}}

function momTag(mom) {{
  if(mom==null) return '<span style="color:#475569;font-size:11px">—</span>';
  const cls = mom>0?'clr-up':mom<0?'clr-dn':'clr-flat';
  return `<span class="${{cls}}" style="font-size:11px;font-weight:600">${{mom>0?'↑':'↓'}} ${{Math.abs(mom)}}%</span>`;
}}
function momTag2(mom) {{
  if(mom==null) return '';
  const cls=mom>0?'lm-up':mom<0?'lm-dn':'lm-flat';
  return `<span class="lane-mom ${{cls}}">${{mom>0?'+':''}}${{mom}}%</span>`;
}}

/* ── Overview ── */
function initOverview() {{
  if(summaryInited) return; summaryInited=true;

  // Factory status cards
  const el = document.getElementById('factory-status');
  FACTORY_ORDER.forEach(fid => {{
    const f=DATA[fid], fc=FACTORY_CURR[fid];
    const priceStr = fc.curr && fc.curr>10 ? '$'+fc.curr.toLocaleString() : '—';
    el.innerHTML += `<div class="fs-card" style="--fc:${{F_COLORS[fid]}}">
      <div class="fs-top"><span class="fs-id">${{fid}}</span><span class="fs-flag">${{f.flag}}</span></div>
      <div class="fs-price">${{priceStr}}</div>
      <div class="fs-mom">${{fc.curr&&fc.curr>10?momTag(fc.mom):'<span style="color:#475569;font-size:11px">回程象征运费</span>'}}</div>
    </div>`;
  }});

  // 仅展示2026年数据
  const PERIODS_2026 = ALL_PERIODS.filter(p=>p.startsWith('26'));
  const IDX_2026 = PERIODS_2026.map(p=>ALL_PERIODS.indexOf(p));
  const labels = PERIODS_2026.map(p=>p.replace('26年',''));

  // Chart 1: 各工厂海运费（无原油）
  const seaDatasets = TREND_FACTORIES.map(fid=>{{
    const fullTrend = FACTORY_SEA_TRENDS[fid];
    const trend = IDX_2026.map(i=>fullTrend[i]);
    const color = F_COLORS[fid];
    return {{
      label: fid,
      data: trend,
      borderColor: color, backgroundColor: color+'18',
      borderWidth: 2.5,
      pointRadius: PERIODS_2026.map(p=>p===CURR_PERIOD?7:3.5),
      pointHoverRadius: 9,
      pointBackgroundColor: PERIODS_2026.map(p=>p===CURR_PERIOD?'#fff':color),
      pointBorderColor: PERIODS_2026.map(p=>p===CURR_PERIOD?color:'transparent'),
      pointBorderWidth: 2,
      tension: 0.4, spanGaps: true, fill: false,
    }};
  }});

  new Chart(document.getElementById('trendChart'),{{
    type:'line', data:{{labels, datasets:seaDatasets}},
    options:{{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      animation:{{duration:800,easing:'easeInOutQuart'}},
      plugins:{{
        legend:{{position:'bottom',labels:{{color:'#94a3b8',font:{{size:11,weight:'500'}},boxWidth:14,boxHeight:3,padding:14,usePointStyle:true,pointStyle:'line'}}}},
        tooltip:{{
          backgroundColor:'#1e293b',borderColor:'#334155',borderWidth:1,
          titleColor:'#f1f5f9',bodyColor:'#94a3b8',padding:10,
          callbacks:{{
            title: items=>'📅 '+PERIODS_2026[items[0].dataIndex],
            label: c=>c.raw!=null?`  ${{c.dataset.label}}: $${{c.raw.toLocaleString()}} USD`:null
          }}
        }}
      }},
      scales:{{
        y:{{
          ticks:{{callback:v=>'$'+v.toLocaleString(),color:'#64748b',font:{{size:10}},maxTicksLimit:7}},
          grid:{{color:'rgba(51,65,85,0.6)'}},
          border:{{dash:[3,3],color:'#334155'}},
          title:{{display:true,text:'USD / HQ40',color:'#475569',font:{{size:10,weight:'500'}}}}
        }},
        x:{{ticks:{{color:'#94a3b8',font:{{size:11,weight:'600'}}}},grid:{{color:'rgba(51,65,85,0.4)'}},border:{{color:'#334155'}}}}
      }}
    }}
  }});

  // Chart 2: 布伦特原油期货
  const brent2026 = IDX_2026.map(i=>BRENT_SERIES[i]);
  new Chart(document.getElementById('brentChart'),{{
    type:'line',
    data:{{labels, datasets:[{{
      label:'布伦特原油 ($/桶)',
      data: brent2026,
      borderColor:'#c084fc', backgroundColor:'rgba(192,132,252,0.12)',
      borderWidth:2.5, borderDash:[5,4],
      pointRadius: PERIODS_2026.map(p=>p===CURR_PERIOD?7:3.5),
      pointHoverRadius:8,
      pointBackgroundColor: PERIODS_2026.map(p=>p===CURR_PERIOD?'#fff':'#c084fc'),
      pointBorderColor: PERIODS_2026.map(p=>p===CURR_PERIOD?'#c084fc':'transparent'),
      pointBorderWidth:2,
      fill:true, tension:0.4, spanGaps:true,
    }}]}},
    options:{{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      animation:{{duration:800,easing:'easeInOutQuart'}},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'#1e293b',borderColor:'#334155',borderWidth:1,
          titleColor:'#f1f5f9',bodyColor:'#94a3b8',padding:10,
          callbacks:{{
            title: items=>'📅 '+PERIODS_2026[items[0].dataIndex],
            label: c=>c.raw!=null?`  🛢 $${{c.raw}}/桶`:null
          }}
        }}
      }},
      scales:{{
        y:{{
          ticks:{{callback:v=>'$'+v,color:'#a78bfa',font:{{size:10}},maxTicksLimit:5}},
          grid:{{color:'rgba(51,65,85,0.4)'}},
          border:{{dash:[3,3],color:'#334155'}},
          min:55, max:115,
          title:{{display:true,text:'USD / 桶',color:'#a78bfa',font:{{size:10,weight:'500'}}}}
        }},
        x:{{ticks:{{color:'#94a3b8',font:{{size:11,weight:'600'}}}},grid:{{color:'rgba(51,65,85,0.4)'}},border:{{color:'#334155'}}}}
      }}
    }}
  }});

  // Destination sea freight bar
  new Chart(document.getElementById('destChart'),{{
    type:'bar',
    data:{{labels:DC_LABELS,datasets:[{{label:'海运费(USD/HQ40)',data:DC_VALS,backgroundColor:DC_COLORS,borderRadius:4}}]}},
    options:{{
      responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>` ${{c.raw.toLocaleString()}} USD`}}}}}},
      scales:{{
        x:{{ticks:{{callback:v=>'$'+v.toLocaleString(),color:'#64748b',font:{{size:10}}}},grid:{{color:'#1e293b'}}}},
        y:{{ticks:{{color:'#94a3b8',font:{{size:10}}}},grid:{{display:false}}}}
      }}
    }}
  }});
}}

/* ── Tab 2 ── */
function renderHome() {{
  const grid=document.getElementById('factory-grid'); grid.innerHTML='';
  FACTORY_ORDER.forEach(fid=>{{
    const f=DATA[fid]; if(!f) return;
    const laneNames=Object.keys(f.lanes);
    const lanesHtml=laneNames.map(lane=>{{
      const ld=f.lanes[lane];
      const price=ld.curr_avg?ld.curr_avg.toLocaleString():'<span class="no-data">暂无</span>';
      return `<div class="lane-row"><span class="lane-name">${{lane}}</span>
        <span style="display:flex;align-items:center"><span class="lane-price">${{price}}</span>${{ld.curr_avg?momTag2(ld.mom):''}}</span></div>`;
    }}).join('');
    const card=document.createElement('div');
    card.className='factory-card'; card.style.setProperty('--c',F_COLORS[fid]);
    card.innerHTML=`<div class="fc-top"><div class="fc-flag">${{f.flag}}</div><div class="fc-lane-count">${{laneNames.length}} 条航线</div></div>
      <div class="fc-name">${{f.name}}</div><div class="fc-location">${{f.location}}</div>
      <div class="fc-lanes">${{lanesHtml}}</div>`;
    card.onclick=()=>renderDetail(fid); grid.appendChild(card);
  }});
}}

function renderDetail(fid) {{
  const f=DATA[fid];
  document.getElementById('grid-section').style.display='none';
  document.getElementById('detail-section').style.display='block';
  document.getElementById('breadcrumb').classList.add('show');
  document.getElementById('bc-name').textContent=f.flag+' '+f.name;
  document.getElementById('detail-header').innerHTML=`<div class="detail-flag">${{f.flag}}</div>
    <div class="detail-title"><h2>${{f.name}}</h2><p>${{f.location}} · ${{Object.keys(f.lanes).length}} 条航线</p></div>`;
  const container=document.getElementById('lanes-container'); container.innerHTML='';
  Object.values(laneCharts).forEach(c=>c.destroy()); Object.keys(laneCharts).forEach(k=>delete laneCharts[k]);
  setTimeout(()=>applyTwemoji(document.getElementById('detail-header')),50);
  Object.entries(f.lanes).forEach(([lane,ld],i)=>{{
    const cid=`lc_${{fid}}_${{i}}`;
    const currStr=ld.curr_avg?'$'+ld.curr_avg.toLocaleString():'暂无';
    const card=document.createElement('div'); card.className='lane-card';
    card.innerHTML=`<div class="lane-card-hdr" onclick="toggleLane(this.parentElement,'${{cid}}','${{lane}}','${{fid}}')">
      <span class="lane-card-title">${{lane}}</span>
      <div class="lane-meta"><span class="curr-price" style="color:${{F_COLORS[fid]}}">${{currStr}}</span>${{momTag2(ld.mom)}}<span class="chevron">▾</span></div>
    </div><div class="lc-chart-area"><canvas id="${{cid}}"></canvas></div>`;
    container.appendChild(card);
  }});
}}

function toggleLane(card,cid,lane,fid) {{
  card.classList.toggle('expanded');
  if(card.classList.contains('expanded')&&!laneCharts[cid]){{
    const f=DATA[fid],ld=f.lanes[lane];
    laneCharts[cid]=new Chart(document.getElementById(cid).getContext('2d'),{{type:'line',
      data:{{labels:ld.trend.map(t=>t.period.replace('25年','').replace('26年','')),
        datasets:[{{label:'均价(USD)',data:ld.trend.map(t=>t.avg_total),
          borderColor:F_COLORS[fid],backgroundColor:F_COLORS[fid]+'22',tension:0.3,fill:true,spanGaps:true,
          pointBackgroundColor:ld.trend.map(t=>t.period===CURR_PERIOD?'#fff':F_COLORS[fid]),
          pointRadius:ld.trend.map(t=>t.period===CURR_PERIOD?6:3)}}]}},
      options:{{responsive:true,
        plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>c.raw?'$'+c.raw.toLocaleString()+' USD':'无数据'}}}}}},
        scales:{{x:{{ticks:{{color:'#64748b',font:{{size:10}}}},grid:{{color:'#1e293b'}}}},
          y:{{ticks:{{color:'#64748b',font:{{size:10}},callback:v=>'$'+v.toLocaleString()}},grid:{{color:'#1e293b'}}}}}}
      }}
    }});
  }}
}}

function goHome() {{
  document.getElementById('grid-section').style.display='';
  document.getElementById('detail-section').style.display='none';
  document.getElementById('breadcrumb').classList.remove('show');
  Object.values(laneCharts).forEach(c=>c.destroy()); Object.keys(laneCharts).forEach(k=>delete laneCharts[k]);
}}

/* ── Tab 3 ── */
function abbr(s) {{
  if(!s) return '—';
  let r=s.split(' - ')[0].split('- ')[0].split(',')[0].replace(/\s*\(.*\)\s*$/,'').trim();
  return r.length>20?r.slice(0,19)+'…':r;
}}
function initMonthlyTab() {{
  const sel=document.getElementById('sel-period');
  if(sel.options.length===0) {{
    ALL_PERIODS.forEach(p=>{{const opt=document.createElement('option');opt.value=p;opt.textContent=p;if(p===CURR_PERIOD)opt.selected=true;sel.appendChild(opt);}});
  }}
  renderMonthly();
}}
const COLGROUP=`<colgroup><col class="col-lane"><col class="col-from"><col class="col-to"><col class="col-inco"><col class="col-hq"><col class="col-book"><col class="col-doc"><col class="col-thc"><col class="col-load"><col class="col-cust"><col class="col-bl"><col class="col-local"><col class="col-dest"><col class="col-sea"><col class="col-tt"><col class="col-total"><col class="col-fw"></colgroup>`;
const THEAD=`<thead><tr><th class="left">航线</th><th class="left">发货方</th><th class="left">收货方</th><th class="left">条款</th><th>HQ40</th><th>Booking</th><th>Doc</th><th>THC</th><th>Loading</th><th>Customs</th><th>B/L</th><th>本地小计</th><th>目的地</th><th>海运费</th><th>运输时效</th><th>总费用</th><th class="left">中标货代</th></tr></thead>`;
function renderMonthly() {{
  const period=document.getElementById('sel-period').value;
  const ff=document.getElementById('sel-factory').value;
  const content=document.getElementById('monthly-content'); content.innerHTML='';
  let anyData=false;
  (ff?[ff]:FACTORY_ORDER).forEach(fid=>{{
    const f=DATA[fid]; if(!f) return;
    const rows=f.records.filter(r=>r.period===period);
    if(!rows.length) return; anyData=true;
    const totalHQ=rows.reduce((s,r)=>s+(r.demand||0),0);
    const tbody=rows.map(r=>`<tr>
      <td class="left td-lane" title="${{r.lane_raw||r.lane}}">${{r.lane_raw||r.lane}}</td>
      <td class="left td-abbr" title="${{r.consignor||''}}">${{abbr(r.consignor)}}</td>
      <td class="left td-abbr" title="${{r.consignee||''}}">${{abbr(r.consignee)}}</td>
      <td class="left"><span class="td-inco-tag">${{r.incoterm||'—'}}</span></td>
      <td class="td-num">${{r.demand!=null?r.demand:'—'}}</td>
      <td class="td-num">${{r.booking!=null?r.booking:'—'}}</td>
      <td class="td-num">${{r.doc!=null?r.doc:'—'}}</td>
      <td class="td-num">${{r.thc!=null?r.thc:'—'}}</td>
      <td class="td-num">${{r.loading!=null?r.loading:'—'}}</td>
      <td class="td-num">${{r.customs!=null?r.customs:'—'}}</td>
      <td class="td-num">${{r.bl!=null?r.bl:'—'}}</td>
      <td class="td-num">${{r.local_sub!=null?r.local_sub:'—'}}</td>
      <td class="td-num">${{r.dest_sub!=null?r.dest_sub:'—'}}</td>
      <td class="td-num td-sea-val">${{r.sea_freight!=null?'$'+Math.round(r.sea_freight).toLocaleString():'—'}}</td>
      <td class="td-num" style="color:#94a3b8;font-size:11px">${{r.transit||'—'}}</td>
      <td class="td-num td-total-val">${{r.total!=null?'$'+Math.round(r.total).toLocaleString():'—'}}</td>
      <td class="td-fw" title="${{r.forwarder||''}}">${{r.forwarder||'—'}}</td>
    </tr>`).join('');
    const section=document.createElement('div'); section.className='factory-section';
    section.innerHTML=`<div class="factory-section-header" style="--fc:${{F_COLORS[fid]}}">
      <span class="fsh-flag">${{f.flag}}</span><span class="fsh-name">${{f.name}}</span>
      <span class="fsh-loc">${{f.location}}</span>
      <span class="fsh-meta">${{rows.length}} 条航线 · 合计需求 ${{totalHQ.toFixed(1)}} HQ40</span>
    </div>
    <div class="orig-table-wrap"><table class="orig-table">${{COLGROUP}}${{THEAD}}<tbody>${{tbody}}</tbody></table></div>`;
    content.appendChild(section);
  }});
  if(!anyData) content.innerHTML='<div class="no-records-msg">该周期暂无数据</div>';
  setTimeout(()=>applyTwemoji(content),50);
}}

renderHome();
initOverview();
function applyTwemoji(el){{twemoji.parse(el||document.body,{{folder:"svg",ext:".svg"}});}}
applyTwemoji();
</script>
</body>
</html>"""

import pathlib
out_dir = pathlib.Path(__file__).parent.parent
for path in [out_dir / 'index.html', out_dir / '海运招标Dashboard.html']:
    with open(path,'w',encoding='utf-8') as f: f.write(html)
print(f"Done — {len(html):,} bytes")
