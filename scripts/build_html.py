"""
Feishu Bitable → HTML Storyboard Builder
==========================================
Reads storyboard data from a Feishu bitable, generates v2 HTML.

Usage:
    python3 build_html.py

Requires:
    - /tmp/s010_canonical.json (output from read_bridge)
    - templates/feishu-backed.html (template with {{TITLE}}, {{SCENE_TABS}}, {{ARC_SECTION}}, {{SCENE_SECTIONS}})

Output:
    - /volume1/主目录/Hermes/read/done/{场次}_feishu_backed.html

Dependencies: Python stdlib only (json, subprocess optional for token fetch)
"""

import json
import re

# ── Config (override via env vars) ──
import os
APP_ID = os.environ.get("FEISHU_APP_ID", "cli_aa9045b4afb85be9")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
APP_TOKEN = os.environ.get("FEISHU_APP_TOKEN", "OwBSbEQS5aY9HksVVBYcYUnVnlg")
TABLE_ID = os.environ.get("FEISHU_TABLE_ID", "tbl2gBoybDUPpPz2")

JINGBIE_STARS = {}  # deprecated — 景别 now carries its own stars from Feishu

JIWEI_SHORT = {
    "🔴 正打": "🔴正",
    "🟡 反打": "🟡反",
    "🟢 第三人称": "🟢三",
    "🔵 空间环境": "🔵环",
    "🟣 插入/切出": "🟣插",
}

# ── Step 1: Fetch from Feishu ──
def get_token():
    import subprocess
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET})
    ], capture_output=True, text=True)
    return json.loads(r.stdout)["tenant_access_token"]

def fetch_all_records(token, app_token, table_id):
    """Fetch all records from bitable with pagination."""
    import subprocess
    all_records = []
    page_token = None
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=50"
        if page_token:
            url += f"&page_token={page_token}"
        r = subprocess.run(["curl", "-s", url, "-H", f"Authorization: Bearer {token}"],
                           capture_output=True, text=True)
        data = json.loads(r.stdout)
        if data.get("code") != 0:
            break
        items = data.get("data", {}).get("items", [])
        all_records.extend(items)
        if not data.get("data", {}).get("has_more"):
            break
        page_token = data.get("data", {}).get("page_token")
    return all_records

def normalize(val):
    """Unwrap Feishu rich text [{text:'...',type:'text'}] → plain string."""
    if isinstance(val, list) and val and isinstance(val[0], dict) and 'text' in val[0]:
        return ''.join(v.get('text', '') for v in val)
    return str(val) if val is not None else ""

def records_to_shots(records):
    """Convert Feishu record list to clean shot dicts."""
    shots = []
    for r in records:
        f = r.get("fields", {})
        s = {
            "record_id": r.get("record_id", ""),
            "镜号": normalize(f.get("镜号", "")),
            "运镜": normalize(f.get("运镜", "")),
            "空间关系": normalize(f.get("空间关系", "")),
            "景别": normalize(f.get("景别", "")),
            "焦段": normalize(f.get("焦段", "")),
            "景深": normalize(f.get("景深", "")),
            "机位": normalize(f.get("机位", "")),
            "动作调度": normalize(f.get("动作调度", "")),
            "台词": normalize(f.get("台词", "")),
            "时长_秒": float(f.get("时长(秒)", 0)) if f.get("时长(秒)") else 0,
            "音频": normalize(f.get("音频", "")),
            "导演备注": normalize(f.get("导演备注", "")),
            "提示词": normalize(f.get("提示词", "")),
            "节拍属性": normalize(f.get("节拍属性", "")),
            "beat序号": normalize(f.get("beat序号", "")),
            "beat类型": normalize(f.get("beat类型", "")),
            "beat标题": normalize(f.get("beat标题", "")),
            "节拍动作": normalize(f.get("节拍动作", "")),
        }
        if s["镜号"]:
            shots.append(s)
    shots.sort(key=lambda x: x["镜号"])
    return shots

# ── Step 2: Build HTML rows ──
def format_sheyingji(raw):
    """Parse 景别 text into HTML: framing lines + ↓ separator + lens-tech span."""
    raw = raw.strip()
    lens_match = re.search(r'(\d+mm·(?:浅|中|深)(?:→(?:浅|中|深))?)', raw)
    lens_html = ''
    framing = raw
    if lens_match:
        lens_html = '<br><span class="lens-tech">{}</span>'.format(lens_match.group(1))
        framing = (raw[:lens_match.start()] + raw[lens_match.end():]).strip()
    if '↓' in framing:
        parts = framing.split('↓')
        return parts[0].strip() + '<br>↓<br>' + parts[1].strip() + lens_html
    return framing + lens_html

def build_shot_row(shot):
    # 摄影机 cell: 景别字段已包含 ★ + ↓ + 焦段·景深，格式化后搬运
    sheyingji = format_sheyingji(shot.get("景别", ""))
    
    yinpin = shot.get("音频", "")
    if yinpin and yinpin.strip() and yinpin.strip() != "—":
        audio_html = '<span class="audio-sfx">' + yinpin.replace('\n', '<br>') + '</span>'
    else:
        audio_html = '<span class="audio-music">—</span>'
    
    dur = float(shot.get("时长_秒", 0)) if shot.get("时长_秒") else 0
    dur_disp = "{}s".format(int(dur)) if dur else ""
    
    taici = shot.get("台词", "")
    taici_html = '<td class="c-dialogue">{}</td>'.format(taici) if taici else "<td></td>"
    
    return '<tr>\n<td class="c-num">{镜号}</td>\n<td>{运镜}</td>\n<td>{空间关系}</td>\n<td>{摄影机}</td>\n<td>{机位}</td>\n<td>{动作调度}</td>\n{台词}\n<td class="c-dur">{时长}</td>\n<td>{音频}</td>\n<td class="c-notes">{导演备注}</td>\n<td class="c-prompt">{提示词}</td>\n</tr>'.format(
        镜号=shot["镜号"], 运镜=shot.get("运镜",""), 空间关系=shot.get("空间关系",""),
        摄影机=sheyingji, 机位=JIWEI_SHORT.get(shot.get("机位",""), shot.get("机位","")), 动作调度=shot.get("动作调度",""),
        台词=taici_html, 时长=dur_disp, 音频=audio_html, 导演备注=shot.get("导演备注",""), 提示词=shot.get("提示词",""))

# ── Step 3: Assemble HTML ──
def build_html(shots, title="电玩城的大小孩", scene_id="s010", scene_name="第一场"):
    shot_rows = "\n".join(build_shot_row(s) for s in shots)
    total_shots = len(shots)
    total_dur = sum(float(s.get("时长_秒", 0)) for s in shots if s.get("时长_秒"))
    
    scene_tabs = '<input type="radio" name="scene" id="scene-arc" checked>\n<input type="radio" name="scene" id="scene-{sid}">\n<nav class="scene-tabs">\n<label for="scene-arc">价值弧线</label>\n<label for="scene-{sid}">{sid} {sname}</label>\n</nav>'.format(sid=scene_id, sname=scene_name)
    
    arc_section = '<section id="arc-section" class="scene-section">\n<div class="placeholder-scene">价值弧线 — 待从模块0导入</div>\n</section>'
    
    info_bar = '<span>{sid} {sname}</span>\n<span>总镜数 <b>{shots}</b></span>\n<span>总时长 <b>{min}′{sec}″</b></span>\n<span class="sep">|</span>\n<span>机位：🔴正打 🟡反打 🟢第三人称 🔵空间环境 🟣插入/切出</span>\n<span class="sep">|</span>\n<button class="btn-refresh" id="btn-refresh" onclick="refreshFromFeishu()">🔄 从飞书刷新</button>\n<span id="refresh-status" class="refresh-status"></span>\n<span class="sep">|</span>\n<button class="btn-refresh" onclick="openSettings()" style="background:var(--row-light);color:var(--text)">⚙</button>'.format(
        sid=scene_id, sname=scene_name, shots=total_shots, min=int(total_dur//60), sec=int(total_dur%60))
    
    # Build beat-grouped table
    from collections import OrderedDict
    beats = OrderedDict()
    for s in shots:
        bk = s.get("beat序号", "")
        if bk not in beats:
            beats[bk] = {"类型": s.get("beat类型",""), "标题": s.get("beat标题",""), "动作": s.get("节拍动作",""), "shots": []}
        beats[bk]["shots"].append(s)
    
    beat_blocks = []
    for bk, bd in beats.items():
        btype = bd["类型"]
        btitle = bd["标题"]
        baction = bd["动作"]
        bshots = bd["shots"]
        
        if bk == "空间":
            # Space label block
            block = '<div class="beat-section">\n<div class="space-label">▸ 空间建立镜 ({n} 镜)</div>\n<div class="table-wrap">\n<table>\n<colgroup>\n<col class="c1"><col class="c2"><col class="c3"><col class="c4"><col class="c5"><col class="c6"><col class="c7"><col class="c8"><col class="c9"><col class="c10"><col class="c11">\n</colgroup>\n<thead><tr><th>#</th><th>运镜</th><th>空间关系</th><th>摄影机</th><th>机位</th><th>动作调度</th><th>台词</th><th>时长</th><th>音频</th><th>导演备注</th><th>提示词</th></tr></thead>\n<tbody>\n{rows}\n</tbody>\n</table>\n</div>\n</div>'.format(n=len(bshots), rows="\n".join(build_shot_row(s) for s in bshots))
        else:
            label_class = "beat-red" if "戏点" in btype else "beat-dot"
            title_text = "beat {n}：{t} ({c} 镜)".format(n=bk, t=btitle, c=len(bshots))
            block = '<div class="beat-section">\n<span class="beat-label {lc}">{bt}</span>\n<span class="beat-title">{title}</span>\n'.format(lc=label_class, bt=btype, title=title_text)
            if baction:
                # Split 外界动作/人物反应 at → for line break
                parts = baction.split('→', 1)
                action_html = parts[0].strip()
                if len(parts) > 1:
                    action_html += '<br>' + parts[1].strip()
                block += '<div class="beat-action">{action}</div>\n'.format(action=action_html)
            block += '<div class="table-wrap">\n<table>\n<colgroup>\n<col class="c1"><col class="c2"><col class="c3"><col class="c4"><col class="c5"><col class="c6"><col class="c7"><col class="c8"><col class="c9"><col class="c10"><col class="c11">\n</colgroup>\n<thead><tr><th>#</th><th>运镜</th><th>空间关系</th><th>摄影机</th><th>机位</th><th>动作调度</th><th>台词</th><th>时长</th><th>音频</th><th>导演备注</th><th>提示词</th></tr></thead>\n<tbody>\n{rows}\n</tbody>\n</table>\n</div>\n</div>'.format(rows="\n".join(build_shot_row(s) for s in bshots))
        beat_blocks.append(block)
    
    v2_table = "\n".join(beat_blocks)
    
    s010_section = '''<section id="{sid}-section" class="scene-section">

<input type="radio" name="sub-{sid}" id="sub-v2-{sid}" checked>
<nav class="sub-tabs">
<label for="sub-v2-{sid}">v2 分镜</label>
</nav>

<div class="info-bar">{info}</div>

<div id="v2-{sid}" class="sub-content">{table}</div>

</section>'''.format(sid=scene_id, info=info_bar, table=v2_table)
    
    scene_sections = arc_section + "\n" + s010_section
    
    with open("/opt/data/skills/scriptwriting/storyboard-shotlist/templates/feishu-backed.html") as f:
        template = f.read()
    
    html = template.replace("{{TITLE}}", title)
    html = html.replace("{{SCENE_TABS}}", scene_tabs)
    html = html.replace("{{ARC_SECTION}}", arc_section)
    html = html.replace("{{SCENE_SECTIONS}}", scene_sections)
    
    return html

# ── Main ──
if __name__ == "__main__":
    token = get_token()
    records = fetch_all_records(token, APP_TOKEN, TABLE_ID)
    shots = records_to_shots(records)
    html = build_html(shots)
    
    out = "/volume1/主目录/Hermes/read/done/{}_feishu_backed.html".format("s010")
    with open(out, "w") as f:
        f.write(html)
    print("OK: {} ({} shots, {}KB)".format(out, len(shots), len(html)//1024))
