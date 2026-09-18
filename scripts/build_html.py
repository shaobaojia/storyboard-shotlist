"""
Feishu Bitable → HTML Storyboard Builder (multi-scene)
========================================================
Reads storyboard data from a Feishu bitable, generates multi-scene HTML.

Usage:
    python3 build_html.py

Output:
    /volume1/主目录/Hermes/read/done/{title}_feishu_backed.html

Dependencies: Python stdlib only (json, subprocess for token fetch)
"""

import json
import re
import os
from collections import OrderedDict

# ── Config (override via env vars) ──
APP_ID = os.environ.get("FEISHU_APP_ID", "cli_aa9045b4afb85be9")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
APP_TOKEN = os.environ.get("FEISHU_APP_TOKEN", "OwBSbEQS5aY9HksVVBYcYUnVnlg")
TABLE_ID = os.environ.get("FEISHU_TABLE_ID", "tbl2gBoybDUPpPz2")
ANALYSIS_TABLE_ID = os.environ.get("FEISHU_ANALYSIS_TABLE_ID", "tbl9L7UG4kJ2nuSr")
TITLE = os.environ.get("FEISHU_TITLE", "测试列表")

JIWEI_SHORT = {
    "🔴 正打": "🔴正",
    "🟡 反打": "🟡反",
    "🟢 第三人称": "🟢三",
    "🔵 空间环境": "🔵环",
    "🟣 插入/切出": "🟣插",
}

# Scene naming: map scene_id to display name
SCENE_NAMES = {
    "s010": "第一场",
    "s020": "第二场",
    "s030": "第三场",
    "s040": "第四场",
    "s050": "第五场",
    "s060": "第六场",
    "s070": "第七场",
    "s080": "第八场",
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
    """Convert Feishu record list to clean shot dicts, grouped by 场次."""
    shots = []
    for r in records:
        f = r.get("fields", {})
        s = {
            "record_id": r.get("record_id", ""),
            "场次": normalize(f.get("场次", "")),
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

def group_by_scene(shots):
    """Group shots by 场次 field, return OrderedDict {scene_id: [shots]}."""
    scenes = OrderedDict()
    for s in shots:
        sid = s.get("场次", "")
        if sid not in scenes:
            scenes[sid] = []
        scenes[sid].append(s)
    return scenes

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
    sheyingji = format_sheyingji(shot.get("景别", ""))
    kongjian = shot.get("空间关系", "").replace("\n", "<br>").replace("[", "<wbr>[")
    
    yinpin = shot.get("音频", "")
    if yinpin and yinpin.strip() and yinpin.strip() != "—":
        audio_html = '<span class="audio-sfx">' + yinpin.replace('\n', '<br>') + '</span>'
    else:
        audio_html = '<span class="audio-music">—</span>'
    
    dur = float(shot.get("时长_秒", 0)) if shot.get("时长_秒") else 0
    dur_disp = "{}s".format(int(dur)) if dur else ""
    
    taici = shot.get("台词", "")
    taici_html = '<td class="c-dialogue">{}</td>'.format(taici) if taici else "<td></td>"
    
    tishici = shot.get("提示词", "")
    has_prompt = ' class="has-prompt"' if tishici and tishici.strip() else ''
    return '<tr{} data-record-id="{}">\n<td class="c-num">{镜号}</td>\n<td>{运镜}</td>\n<td>{空间关系}</td>\n<td>{摄影机}</td>\n<td>{机位}</td>\n<td>{动作调度}</td>\n{台词}\n<td class="c-dur">{时长}</td>\n<td>{音频}</td>\n<td class="c-notes">{导演备注}</td>\n<td class="c-prompt">{提示词}</td>\n</tr>'.format(
        has_prompt, shot.get("record_id",""),
        镜号=shot["镜号"], 运镜=shot.get("运镜",""), 空间关系=kongjian,
        摄影机=sheyingji, 机位=JIWEI_SHORT.get(shot.get("机位",""), shot.get("机位","")), 动作调度=shot.get("动作调度",""),
        台词=taici_html, 时长=dur_disp, 音频=audio_html, 导演备注=shot.get("导演备注",""), 提示词=tishici)

def fetch_analysis_records(token, app_token, table_id):
    """Fetch analysis records from the analysis bitable."""
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

def build_beat_analysis_html(records, scene_id):
    """Build beat analysis table HTML for one scene."""
    if not records:
        return '<div class="placeholder-scene">分析数据待导入</div>'
    
    # Sort by beat number
    records.sort(key=lambda r: int(float(normalize(r.get("fields", {}).get("节拍序号", "0")))) if normalize(r.get("fields", {}).get("节拍序号", "")) else 0)
    
    # Extract scene value declaration
    first = records[0].get("fields", {})
    scene_value = normalize(first.get("场景价值", ""))
    viewpoint = normalize(first.get("视点角色", ""))
    
    rows = []
    for r in records:
        f = r.get("fields", {})
        btype = normalize(f.get("类型", ""))
        beat_num = str(int(float(normalize(f.get("节拍序号", "0"))))) if normalize(f.get("节拍序号", "")) else ""
        rid = r.get('record_id', '')
        row = '<tr data-record-id="' + rid + '">'
        row += '<td class="c-num">' + beat_num + '</td>'
        row += '<td>' + normalize(f.get("节拍名称", "")) + '</td>'
        row += '<td class="c-notes">' + normalize(f.get("外界动作", "")) + '</td>'
        row += '<td>' + normalize(f.get("人物反应", "")) + '</td>'
        row += '<td>' + btype + '</td>'
        row += '<td class="c-notes">' + normalize(f.get("说明", "")) + '</td>'
        row += '<td>' + normalize(f.get("闭环", "")) + '</td>'
        row += '</tr>'
        rows.append(row)
    
    # Rhythm curve
    rhythm_parts = []
    for r in records:
        f = r.get("fields", {})
        sec = normalize(f.get("节奏段落", ""))
        desc = normalize(f.get("节奏描述", ""))
        temp = normalize(f.get("情绪温度", ""))
        density = normalize(f.get("节奏密度", ""))
        if sec and desc:
            rhythm_parts.append("段落" + sec + "：" + desc + "（情绪" + temp + "/10，节奏" + density + "）")
    
    # Estimate
    estimate = ""
    for r in records:
        est = normalize(r.get("fields", {}).get("预估总镜头数", ""))
        if est:
            estimate = est
            break
    
    decl = '<div class="beat-decl">场景价值：' + scene_value + ' &nbsp;|&nbsp; 视点角色：' + viewpoint + '</div>' if scene_value else ''
    estimate_html = '<div class="beat-estimate">预估总镜头数：' + estimate + ' 镜</div>' if estimate else ''
    rhythm_html = '<div class="beat-rhythm">' + " | ".join(rhythm_parts) + '</div>' if rhythm_parts else ''
    
    html = decl
    html += '<div class="table-wrap"><table class="beat-analysis-table">'
    html += '<colgroup><col class="c1-b"><col class="c2-b"><col class="c3-b"><col class="c4-b"><col class="c5-b"><col class="c6-b"><col class="c7-b"></colgroup>'
    html += '<thead><tr><th>#</th><th>节拍</th><th>外界动作</th><th>人物反应</th><th>类型</th><th>说明</th><th>闭环</th></tr></thead>'
    html += '<tbody>' + "".join(rows) + '</tbody>'
    html += '</table></div>'
    html += rhythm_html + estimate_html
    return html

def build_beat_table(shots):
    """Build beat-grouped table HTML for one scene's shots."""
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
            block = '<div class="beat-section">\n<div class="space-label">▸ 空间建立镜 ({n} 镜)</div>\n<div class="table-wrap">\n<table>\n<colgroup>\n<col class="c1"><col class="c2"><col class="c3"><col class="c4"><col class="c5"><col class="c6"><col class="c7"><col class="c8"><col class="c9"><col class="c10"><col class="c11">\n</colgroup>\n<thead><tr><th>#</th><th>运镜</th><th>空间关系</th><th>摄影机</th><th>机位</th><th>动作调度</th><th>台词</th><th>时长</th><th>音频</th><th>导演备注</th><th>提示词</th></tr></thead>\n<tbody>\n{rows}\n</tbody>\n</table>\n</div>\n</div>'.format(n=len(bshots), rows="\n".join(build_shot_row(s) for s in bshots))
        else:
            label_class = "beat-red" if "戏点" in btype else "beat-dot"
            title_text = "beat {n}：{t} ({c} 镜)".format(n=bk, t=btitle, c=len(bshots))
            block = '<div class="beat-section">\n<span class="beat-label {lc}">{bt}</span>\n<span class="beat-title">{title}</span>\n'.format(lc=label_class, bt=btype, title=title_text)
            if baction:
                parts = baction.split('→', 1)
                action_html = parts[0].strip()
                if len(parts) > 1:
                    action_html += '<br>' + parts[1].strip()
                block += '<div class="beat-action">{action}</div>\n'.format(action=action_html)
            block += '<div class="table-wrap">\n<table>\n<colgroup>\n<col class="c1"><col class="c2"><col class="c3"><col class="c4"><col class="c5"><col class="c6"><col class="c7"><col class="c8"><col class="c9"><col class="c10"><col class="c11">\n</colgroup>\n<thead><tr><th>#</th><th>运镜</th><th>空间关系</th><th>摄影机</th><th>机位</th><th>动作调度</th><th>台词</th><th>时长</th><th>音频</th><th>导演备注</th><th>提示词</th></tr></thead>\n<tbody>\n{rows}\n</tbody>\n</table>\n</div>\n</div>'.format(rows="\n".join(build_shot_row(s) for s in bshots))
        beat_blocks.append(block)
    
    return "\n".join(beat_blocks)

def build_one_scene_section(shots, scene_id, analysis_data=None):
    """Build one scene's section HTML (info bar + beat table)."""
    sname = SCENE_NAMES.get(scene_id, scene_id)
    total_shots = len(shots)
    total_dur = sum(float(s.get("时长_秒", 0)) for s in shots if s.get("时长_秒"))
    
    info_bar = '<span>{sid} {sname}</span>\n<span>总镜数 <b>{shots}</b></span>\n<span>总时长 <b>{min}′{sec}″</b></span>\n<span class="sep">|</span>\n<span>机位：🔴正打 🟡反打 🟢第三人称 🔵空间环境 🟣插入/切出</span>\n<span class="sep">|</span>\n<button class="btn-refresh" onclick="refreshFromFeishu()">🔄 从飞书刷新</button>\n<span id="refresh-status" class="refresh-status"></span>\n<span class="sep">|</span>\n<button class="btn-refresh" onclick="openSettings()">⚙</button>'.format(
        sid=scene_id, sname=sname, shots=total_shots, min=int(total_dur//60), sec=int(total_dur%60))
    
    v2_table = build_beat_table(shots)
    beat_records = analysis_data.get(scene_id, []) if analysis_data else []
    beat_analysis = build_beat_analysis_html(beat_records, scene_id)
    
    return '''<section id="{sid}-section" class="scene-section">

<input type="radio" name="sub-{sid}" id="sub-v2-{sid}" checked>
<input type="radio" name="sub-{sid}" id="sub-beat-{sid}">
<nav class="sub-tabs">
<label for="sub-beat-{sid}">节拍分析</label>
<label for="sub-v2-{sid}">v2 分镜</label>
</nav>

<div id="beat-{sid}" class="sub-content">{beat_analysis}</div>

<div class="info-bar">{info}</div>

<div id="v2-{sid}" class="sub-content">{table}</div>

</section>'''.format(sid=scene_id, beat_analysis=beat_analysis, info=info_bar, table=v2_table)

# ── Step 3: Assemble HTML ──
def build_html(scenes, title=TITLE, analysis_data=None):
    """Build complete multi-scene HTML.
    
    Args:
        scenes: OrderedDict {scene_id: [shots]}
        title: HTML title
    """
    # Build scene tabs
    scene_ids = list(scenes.keys())
    # Radio inputs
    radios = '<input type="radio" name="scene" id="scene-arc" checked>\n'
    for sid in scene_ids:
        radios += '<input type="radio" name="scene" id="scene-{sid}">\n'.format(sid=sid)
    # Tab labels
    labels = '<nav class="scene-tabs">\n<label for="scene-arc">价值弧线</label>\n'
    for sid in scene_ids:
        sname = SCENE_NAMES.get(sid, sid)
        labels += '<label for="scene-{sid}">{sid} {sname}</label>\n'.format(sid=sid, sname=sname)
    labels += '</nav>'
    scene_tabs = radios + labels
    
    # Arc section (placeholder)
    arc_section = '<section id="arc-section" class="scene-section">\n<div class="placeholder-scene">价值弧线 — 待从模块0导入</div>\n</section>'
    
    # Scene sections
    sections = [arc_section]
    for sid in scene_ids:
        sections.append(build_one_scene_section(scenes[sid], sid, analysis_data))
    scene_sections_html = "\n".join(sections)
    
    # Generate scene-specific CSS rules
    scene_css_lines = []
    tab_active_lines = ['#scene-arc:checked~.scene-tabs label[for=scene-arc],']
    sub_display_lines = []
    sub_label_lines = []
    for sid in scene_ids:
        scene_css_lines.append('#scene-{sid}:checked~#{sid}-section{{display:block}}'.format(sid=sid))
        tab_active_lines.append('#scene-{sid}:checked~.scene-tabs label[for=scene-{sid}],'.format(sid=sid))
        for sub in ['beat', 'v2']:
            sub_display_lines.append('#sub-{sub}-{sid}:checked~#{sub}-{sid}{{display:block}}'.format(sub=sub, sid=sid))
            sub_label_lines.append('#sub-{sub}-{sid}:checked~.sub-tabs label[for=sub-{sub}-{sid}],'.format(sub=sub, sid=sid))
    # scene tab active highlight
    tab_active_css = "\n".join(tab_active_lines).rstrip(',') + "\n{border-bottom-color:var(--accent);color:var(--head)}"
    # sub-tab: display rules first, then label highlight grouped
    sub_tab_css = "\n".join(sub_display_lines) + "\n" + "\n".join(sub_label_lines).rstrip(',') + "\n{border-bottom-color:var(--accent);color:var(--head)}"
    scene_css = "\n".join(scene_css_lines)
    
    # Load template
    tmpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "feishu-backed.html")
    with open(tmpl_path) as f:
        template = f.read()
    
    html = template.replace("{{TITLE}}", title)
    html = html.replace("{{SCENE_TABS}}", scene_tabs)
    html = html.replace("{{ARC_SECTION}}", arc_section)
    html = html.replace("{{SCENE_SECTIONS}}", scene_sections_html)
    html = html.replace("{{SCENE_CSS}}", scene_css)
    html = html.replace("{{SCENE_TAB_ACTIVE_CSS}}", tab_active_css)
    html = html.replace("{{SUB_TAB_CSS}}", sub_tab_css)
    
    return html

# ── Main ──
if __name__ == "__main__":
    token = get_token()
    records = fetch_all_records(token, APP_TOKEN, TABLE_ID)
    shots = records_to_shots(records)
    scenes = group_by_scene(shots)
    
    # Filter out entries with empty scene_id (shouldn't happen, but guard)
    scenes = OrderedDict((k, v) for k, v in scenes.items() if k)
    
    if not scenes:
        print("ERROR: No scene data found")
        exit(1)
    
    # Fetch analysis data
    analysis_records = fetch_analysis_records(token, APP_TOKEN, ANALYSIS_TABLE_ID)
    analysis_by_scene = OrderedDict()
    for r in analysis_records:
        sid = normalize(r.get("fields", {}).get("场次", ""))
        if sid not in analysis_by_scene:
            analysis_by_scene[sid] = []
        analysis_by_scene[sid].append(r)
    
    # Merge analysis-only scenes into scenes dict (for Tab generation)
    for sid in analysis_by_scene:
        if sid not in scenes:
            scenes[sid] = []
    
    html = build_html(scenes, analysis_data=analysis_by_scene)
    
    total_shots = sum(len(v) for v in scenes.values())
    out = "/volume1/主目录/Hermes/read/done/s010_feishu_backed.html"  # multi-scene, keep legacy filename
    with open(out, "w") as f:
        f.write(html)
    
    scene_info = ", ".join("{}:{}镜".format(k, len(v)) for k, v in scenes.items())
    print("OK: {} ({} shots total, {}KB) [{}]".format(out, total_shots, len(html)//1024, scene_info))
