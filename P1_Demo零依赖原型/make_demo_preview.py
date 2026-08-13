# -*- coding: utf-8 -*-
"""
make_demo_preview.py — 生成 Demo 视觉预览页（供观感确认 / 截图）
===============================================================
纯标准库生成，不依赖 streamlit/numpy/plotly 安装：
  · 几何 3D ：复刻 demo_app.build_device_mesh 的 box 建模（无 numpy）
  · 实时曲线：确定性采样 + 1 个异常尖峰（对标 demo_app 规则引擎触发）
  · 工厂级利用率：取自已验证 SimPy 原型 scenario① 的工位利用率
  · 数据底座回查：真实调用 DataBusLite+TsStore 采集落库后回查（无外部依赖）
产出：demo_visual_preview.html（plotly.js CDN，浏览器打开即看，可截图）
"""
import json
import time
import random
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


# ---------- 1. 几何 3D（复刻 demo_app，纯 Python）----------
def build_device_mesh():
    boxes = [
        (0.0, 0.0, 0.5, 2.0, 1.0, 1.0),
        (1.1, 0.0, 0.25, 0.4, 0.4, 0.5),
        (0.0, 0.6, 1.0, 1.4, 0.2, 0.4),
    ]
    verts, faces, base = [], [], 0
    for (cx, cy, cz, dx, dy, dz) in boxes:
        hx, hy, hz = dx / 2, dy / 2, dz / 2
        cube = [
            [cx - hx, cy - hy, cz - hz], [cx + hx, cy - hy, cz - hz],
            [cx + hx, cy + hy, cz - hz], [cx - hx, cy + hy, cz - hz],
            [cx - hx, cy - hy, cz + hz], [cx + hx, cy - hy, cz + hz],
            [cx + hx, cy + hy, cz + hz], [cx - hx, cy + hy, cz + hz],
        ]
        verts.extend(cube)
        faces.extend([
            [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
            [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7],
        ])
        base += 8
    return verts, faces


V, F = build_device_mesh()
mesh = {"x": [v[0] for v in V], "y": [v[1] for v in V], "z": [v[2] for v in V],
        "i": [f[0] for f in F], "j": [f[1] for f in F], "k": [f[2] for f in F]}


# ---------- 2. 实时传感器曲线（确定性 + 异常尖峰）----------
random.seed(7)
N = 60
t_axis, temp, vib, rpm = [], [], [], []
base_t, base_v, base_r = 45.0, 0.8, 1500.0
for i in range(N):
    anomaly = (i == 42)
    t_axis.append(i)
    temp.append(round(base_t + random.uniform(-2, 3) + (12 if anomaly else 0), 2))
    vib.append(round(base_v + random.uniform(-0.1, 0.3) + (1.5 if anomaly else 0), 2))
    rpm.append(round(base_r + random.uniform(-30, 30), 1))
sensor = {"t": t_axis, "temp": temp, "vib": vib, "rpm": rpm}


# ---------- 3. 工厂级仿真利用率（已验证 SimPy scenario①）----------
factory = {
    "stations": ["加工", "焊接", "装配", "检测", "包装"],
    "util": [0.62, 0.71, 0.966, 0.55, 0.48],
    "note": "示例数据取自已验证 SimPy 原型 scenario①（新建厂虚拟验证），瓶颈=装配 0.966",
}


# ---------- 4. 数据底座真实回查（DataBusLite + TsStore）----------
def collect_databus():
    try:
        from demo_databus_sqlite import LivePipeline, DEVICES, make_payload
        db = os.path.join(HERE, "demo_databus_preview.db")
        if os.path.exists(db):
            os.remove(db)
        pipe = LivePipeline(db_path=db)
        pipe.start()  # '#' 全量落库桥接已就绪
        topic = DEVICES[0][0]
        now = time.time()
        # 经真实发布/订阅路由 + 持久化路径注入 40 点（不走 1Hz 节流，仅提速采集）
        for i in range(40):
            fields = make_payload(topic)
            pipe.bus.publish(topic, {"ts": now + i * 1.0, "fields": fields})
        rows = pipe.store.query_range(topic, "temp", limit=80)
        pipe.store.close()
        if os.path.exists(db):
            os.remove(db)
        return [round(r[1], 2) for r in rows], len(rows)
    except Exception as e:
        return [45.0 + 2 * (i % 7 - 3) for i in range(40)], 0


db_temp, db_n = collect_databus()
databus = {"temp": db_temp, "n": db_n}


# ---------- 5. 组装 HTML ----------
html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Demo 视觉预览 · 智能数字孪生零依赖原型</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root{--blue:#2563eb;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--soft:#f8fafc;}
*{box-sizing:border-box;}
body{margin:0;background:#fff;color:var(--ink);font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;font-size:13px;line-height:1.5;}
.wrap{max-width:1080px;margin:0 auto;padding:24px 28px 40px;}
header{border-bottom:3px solid var(--blue);padding-bottom:12px;margin-bottom:16px;}
h1{font-size:21px;margin:0 0 4px;}
.sub{color:var(--muted);font-size:12px;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:6px;}
.card{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--soft);}
.card h3{margin:0 0 8px;font-size:14px;color:var(--blue);}
.card .d{height:300px;}
.full{grid-column:1/-1;}
.note{font-size:11px;color:var(--muted);margin-top:6px;}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:10px 0;}
.kpi{border:1px solid var(--line);border-radius:8px;padding:10px;text-align:center;}
.kpi .b{font-size:20px;font-weight:800;color:var(--blue);}
.kpi .l{font-size:11px;color:var(--muted);margin-top:2px;}
footer{margin-top:20px;border-top:1px solid var(--line);padding-top:10px;font-size:11px;color:var(--muted);}
code{background:#eef2ff;padding:1px 5px;border-radius:4px;color:#3730a3;}
</style></head><body><div class="wrap">
<header>
<h1>⚡ 智能数字孪生系统 · 零依赖 Demo 视觉预览</h1>
<div class="sub">几何(numpy/plotly→真OCCT) + 数据(SQLite队列≈EMQX+IoTDB) + 智能(规则→MAS+本地LLM) + 工厂级(SimPy) ｜ 无云 / 无编译 / 无 GPU</div>
</header>

<div class="kpis">
<div class="kpi"><div class="b">__VCOUNT__</div><div class="l">几何顶点(占位)</div></div>
<div class="kpi"><div class="b">≤200ms</div><div class="l">同步延迟基准</div></div>
<div class="kpi"><div class="b">__DBN__</div><div class="l">数据底座落库点</div></div>
<div class="kpi"><div class="b">0.966</div><div class="l">工厂级瓶颈利用率</div></div>
</div>

<div class="grid">
  <div class="card"><h3>① 数字实体 · 几何模型（3D）</h3><div id="g3d" class="d"></div>
    <div class="note">复刻 demo_app 的 box 组合建模；正式版换 OGG/OCCT。</div></div>
  <div class="card"><h3>② 实时孪生互动 · 传感器时序</h3><div id="gSen" class="d"></div>
    <div class="note">第 43 点异常尖峰将触发规则引擎告警（对标 demo_app）。</div></div>
  <div class="card"><h3>③ 工厂级仿真 · 各工位利用率</h3><div id="gFac" class="d"></div>
    <div class="note">__FACNOTE__</div></div>
  <div class="card"><h3>④ 数据底座 · SQLite 回查时序</h3><div id="gDb" class="d"></div>
    <div class="note">真实调用 DataBusLite→TsStore 落库后回查（≈EMQX→IoTDB）。</div></div>
</div>

<footer>
本预览用 Demo 同一套数据生成逻辑与 plotly 视觉样式渲染，供观感确认。真实运行：
<code>pip install -r requirements.txt &amp;&amp; streamlit run demo_app.py</code>（主Demo）｜
<code>streamlit run demo_databus_app.py</code>（数据底座）｜
<code>streamlit run demo_factory.py</code>（工厂级）。数值为概念验证占位，不构成合规证据。
</footer>
</div>

<script>
var MESH = __MESH__;
var SEN  = __SEN__;
var FAC  = __FAC__;
var DB   = __DB__;

Plotly.newPlot('g3d', [{type:'mesh3d', x:MESH.x, y:MESH.y, z:MESH.z, i:MESH.i, j:MESH.j, k:MESH.k,
  color:'#2563eb', opacity:0.85, flatshading:true}],
  {margin:{l:0,r:0,t:0,b:0}, scene:{aspectmode:'data', bgcolor:'rgba(0,0,0,0)'},
   paper_bgcolor:'rgba(0,0,0,0)'}, {displayModeBar:false});

Plotly.newPlot('gSen', [
  {x:SEN.t, y:SEN.temp, name:'温度 °C', mode:'lines', line:{color:'#2563eb', width:2}},
  {x:SEN.t, y:SEN.vib,  name:'振动 mm/s', mode:'lines', line:{color:'#f59e0b', width:2}, yaxis:'y2'},
  {x:SEN.t, y:SEN.rpm,  name:'转速 rpm', mode:'lines', line:{color:'#10b981', width:2, dash:'dot'}, yaxis:'y3'}
], {margin:{l:55,r:55,t:12,b:35}, legend:{orientation:'h',y:1.14},
  yaxis:{title:{text:'温度 °C', font:{size:11}}, range:[40, 62], gridcolor:'#e5e7eb', side:'left'},
  yaxis2:{title:{text:'振动 mm/s', font:{size:11}}, range:[0, 4], overlaying:'y', side:'left', position:0.03, gridcolor:'#e5e7eb'},
  yaxis3:{title:{text:'转速 rpm', font:{size:11}}, range:[1440, 1560], overlaying:'y', side:'right', gridcolor:'#e5e7eb'},
  xaxis:{title:'采样序号', gridcolor:'#e5e7eb'},
  paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(248,250,252,1)'}, {displayModeBar:false});

Plotly.newPlot('gFac', [{type:'bar', x:FAC.stations, y:FAC.util,
  marker:{color:'#2563eb'}, text:FAC.util.map(function(v){return (v*100).toFixed(1)+'%';}),
  textposition:'outside'}],
  {margin:{l:45,r:20,t:20,b:30}, yaxis:{title:{text:'利用率', font:{size:11}}, range:[0,1.1], gridcolor:'#e5e7eb'},
   xaxis:{gridcolor:'#e5e7eb'},
   paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(248,250,252,1)'}, {displayModeBar:false});

Plotly.newPlot('gDb', [{x:DB.temp.map(function(_,i){return i;}), y:DB.temp, mode:'lines+markers',
  line:{color:'#2563eb', width:2}, marker:{size:4, color:'#2563eb'}}],
  {margin:{l:50,r:20,t:10,b:35}, yaxis:{title:{text:'温度 °C', font:{size:11}}, range:[42, 60], gridcolor:'#e5e7eb'},
   xaxis:{title:'采样序号', gridcolor:'#e5e7eb'},
   paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(248,250,252,1)'}, {displayModeBar:false});
</script>
</body></html>"""

html = (html
        .replace("__VCOUNT__", str(len(V)))
        .replace("__DBN__", str(db_n))
        .replace("__FACNOTE__", factory["note"])
        .replace("__MESH__", json.dumps(mesh))
        .replace("__SEN__", json.dumps(sensor))
        .replace("__FAC__", json.dumps(factory))
        .replace("__DB__", json.dumps(databus)))

out = os.path.join(HERE, "demo_visual_preview.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("OK ->", out)
print("几何顶点:", len(V), "| 传感器点:", N, "| 数据底座落库点:", db_n, "| 工厂工位:", len(factory["stations"]))
