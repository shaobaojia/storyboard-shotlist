#!/usr/bin/env python3
"""Shotlist server: serves static HTML + proxies Feishu API calls + generates prompts."""
import http.server
import json
import urllib.request
import os
import socketserver
import re

PORT = 8089
DOCROOT = "/volume1/主目录/Hermes/read/done"
SKILL_DIR = "/opt/data/skills/scriptwriting/storyboard-shotlist"
CONFIG_PATH = os.path.join(SKILL_DIR, "feishu_config.json")
TEMPLATE_PATH = os.path.join(SKILL_DIR, "references", "m4-prompt-template.md")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def feishu_token(cfg):
    data = json.dumps({"app_id": cfg["app_id"], "app_secret": cfg["app_secret"]}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())["tenant_access_token"]

def feishu_fetch(token, cfg):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{cfg['app_token']}/tables/{cfg['table_id']}/records?page_size=50"
    all_records = []
    page_token = None
    while True:
        u = url + (f"&page_token={page_token}" if page_token else "")
        req = urllib.request.Request(u, headers={"Authorization": f"Bearer {token}"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if data.get("code") != 0:
            raise Exception(f"Fetch error: {data.get('msg')}")
        all_records.extend(data["data"]["items"])
        if not data["data"].get("has_more"):
            break
        page_token = data["data"]["page_token"]
    return all_records

def feishu_put(token, cfg, record_id, fields):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{cfg['app_token']}/tables/{cfg['table_id']}/records/{record_id}"
    data = json.dumps({"fields": fields}).encode()
    req = urllib.request.Request(url, data=data, method="PUT",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

def norm(v):
    if isinstance(v, list) and v and isinstance(v[0], dict) and "text" in v[0]:
        return "".join(x.get("text", "") for x in v)
    return str(v) if v is not None else ""

def generate_prompts(cfg, shot_nums):
    token = feishu_token(cfg)
    records = feishu_fetch(token, cfg)
    
    # Build shot lookup
    shots = {}
    for r in records:
        jh = norm(r["fields"].get("镜号", ""))
        if jh in shot_nums:
            shots[jh] = {
                "record_id": r["record_id"],
                "运镜": norm(r["fields"].get("运镜", "")),
                "空间关系": norm(r["fields"].get("空间关系", "")),
                "摄影机": norm(r["fields"].get("景别", "")),
                "机位": norm(r["fields"].get("机位", "")),
                "动作调度": norm(r["fields"].get("动作调度", "")),
                "台词": norm(r["fields"].get("台词", "")),
                "提示词": norm(r["fields"].get("提示词", "")),
            }
    
    # Find upstream shared declarations
    shared = ""
    sorted_nums = sorted(shot_nums, key=lambda x: int(x) if x.isdigit() else x)
    first_num = sorted_nums[0]
    # Look for nearest upstream with full prompt
    for r in sorted(records, key=lambda r: norm(r["fields"].get("镜号","")), reverse=True):
        jh = norm(r["fields"].get("镜号", ""))
        if jh.isdigit() and int(jh) < int(first_num):
            ts = norm(r["fields"].get("提示词", ""))
            if ts and not ts.startswith("↑"):
                # Extract shared declarations (before 镜头一)
                idx = ts.find("镜头一")
                if idx > 0:
                    shared = ts[:idx].strip()
                break
    
    # Build shot data string
    shot_lines = []
    for sn in sorted_nums:
        s = shots.get(sn)
        if not s: continue
        shot_lines.append(
            f"镜{sn}: 运镜={s['运镜']} 摄影机={s['摄影机']} 机位={s['机位']}\n"
            f"空间关系={s['空间关系']}\n"
            f"动作调度={s['动作调度']}\n"
            f"台词={s['台词'] or '(无)'}"
        )
    
    # Read template
    with open(TEMPLATE_PATH) as f:
        template_rules = f.read()
    
    # Call DeepSeek
    system_prompt = f"""你是分镜提示词生成器。严格按以下规则生成提示词。

{template_rules}

生成提示词时：
- 共享声明（人物/场景/空间锚）从上游继承，不改动
- 每个镜头四行：动作表演/拍摄方式/画面呈现/主光方位
- 动作表演主语必须明确，台词用「」包裹
- 拍摄方式机位绑定主体
- 运镜镜头画面呈现拆起幅/运镜/落幅三段
- 末尾拼接风格块
- 纯文本输出，禁用 Markdown 格式（# ## ** --- 等）。只输出提示词正文，不要任何解释"""
    
    user_prompt = f"【上游共享声明】\n{shared or '(本组为场次首组，请根据镜头数据生成共享声明)'}\n\n【目标镜头】\n{chr(10).join(shot_lines)}\n\n生成镜{'/'.join(sorted_nums)}合并提示词。"
    
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg['deepseek_api_key']}"}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    prompt_text = resp["choices"][0]["message"]["content"]
    usage = resp.get("usage", {})
    
    # Write back to Feishu
    results = []
    first_shot = sorted_nums[0]
    for sn in sorted_nums:
        s = shots.get(sn)
        if not s: continue
        if sn == first_shot:
            fields = {"提示词": prompt_text}
        else:
            fields = {"提示词": f"↑s010-{first_shot}"}
        put_resp = feishu_put(token, cfg, s["record_id"], fields)
        results.append({"shot": sn, "ok": put_resp.get("code") == 0})
    
    return {"results": results, "usage": usage, "prompt_preview": prompt_text[:200]}


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOCROOT, **kwargs)

    def do_POST(self):
        if self.path == "/api/generate-prompts":
            self._handle_generate()
        else:
            self._proxy_request("POST")

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.path.startswith("/api/feishu"):
            self._proxy_request("GET")
        else:
            super().do_GET()

    def _handle_generate(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            shot_nums = body.get("shots", [])
            if not shot_nums:
                self._send_json(400, {"error": "missing shots"})
                return
            
            cfg = load_config()
            if "deepseek_api_key" not in cfg:
                self._send_json(400, {"error": "deepseek_api_key not in feishu_config.json"})
                return
            
            result = generate_prompts(cfg, shot_nums)
            self._send_json(200, result)
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _proxy_request(self, method):
        length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(length) if length > 0 else b"{}"
        params = json.loads(body_raw)
        feishu_url = params.get("url", "")
        feishu_headers = params.get("headers", {})
        feishu_body = params.get("body", None)
        if not feishu_url:
            self._send_json(400, {"error": "missing url"})
            return
        data_bytes = json.dumps(feishu_body).encode() if feishu_body else None
        req = urllib.request.Request(
            feishu_url, data=data_bytes,
            headers={**feishu_headers, "Content-Type": "application/json; charset=utf-8"} if data_bytes else feishu_headers,
            method=params.get("_method", method) if data_bytes else "GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                self._send_json(200, json.loads(data))
        except Exception as e:
            self._send_json(502, {"error": str(e)})

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"Shotlist server on :{PORT} (threaded)")
    server.serve_forever()
