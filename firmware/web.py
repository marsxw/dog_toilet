import asyncio
import network
import time
import ubinascii


AP_IP = "192.168.99.1"
ENGINEER_IP = "192.168.99.99"
AP_MASK = "255.255.255.0"


def make_ssid():
    wlan = network.WLAN(network.AP_IF)
    mac = wlan.config("mac")
    return "toilet_" + ubinascii.hexlify(mac[-3:]).decode()


def start_ap():
    ap = network.WLAN(network.AP_IF)
    try:
        ap.active(False)
    except OSError:
        pass
    time.sleep_ms(150)
    ap.active(True)
    time.sleep_ms(150)
    ssid = make_ssid()
    ap.config(essid=ssid, channel=6, authmode=network.AUTH_OPEN)
    try:
        ap.config(txpower=8)
    except (ValueError, OSError):
        pass
    time.sleep_ms(100)
    try:
        ap.ifconfig((AP_IP, AP_MASK, AP_IP, AP_IP))
    except OSError:
        pass
    return ap, ssid


def stop_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(False)


def _fmt1(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        n = 0.0
    if n < 0:
        n = 0.0
    tenths = int(n * 10 + 0.0001)
    return str(tenths // 10) + "." + str(tenths % 10)


def _html_escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_page(cfg, ssid, status):
    st = status or {}
    remain_s = int(st.get("wifi_remain_s") or 0)
    lang = cfg.get("lang") or "zh"
    page = """<!DOCTYPE html>
<html lang="__HTML_LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__TITLE__</title>
<style>
:root{--bg:#eef4f1;--card:#fff;--ink:#1c1917;--muted:#7a736c;--line:#e7e5e4;--acc:#0f766e}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Noto Sans SC",sans-serif;background:linear-gradient(180deg,#dceee8 0%,var(--bg) 22%);color:var(--ink)}
.wrap{max-width:440px;margin:0 auto;padding:10px 12px 20px}
.card{background:var(--card);border:1px solid rgba(28,25,23,.06);border-radius:16px;padding:12px;margin-bottom:8px;box-shadow:0 8px 18px rgba(28,25,23,.04)}
.cardhead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 8px}
.kicker{font-size:12px;color:var(--muted);margin:0}
.headleft{display:flex;align-items:center;gap:8px;min-width:0}
.ir-mark{display:inline-flex;align-items:center;gap:5px;padding:2px 7px;border-radius:999px;background:#f5f5f4;font-size:12px;color:var(--muted);font-weight:600}
.ir-mark .dot{width:7px;height:7px;border-radius:50%;background:#d6d3d1}
.ir-mark.on{color:#15803d;background:#ecfdf5}
.ir-mark.on .dot{background:#22c55e;box-shadow:0 0 0 3px rgba(34,197,94,.22)}
.stepbox{background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:10px 12px}
.stepbox b{display:block;font-size:17px;line-height:1.35;font-weight:700;color:#115e59}
.hint{margin:0;padding:8px 10px;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:10px;font-size:12px;line-height:1.45}
form{display:grid;gap:8px}
.group{font-size:11px;color:var(--muted);margin:0 0 8px;letter-spacing:.1em}
.split{height:1px;background:var(--line);margin:10px 0}
label{display:block;font-size:12px;margin:0 0 4px;color:#44403c}
input[type=number]{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:10px;background:#fafaf9;font-size:16px;color:var(--ink)}
input[type=number]:focus{outline:2px solid #99f6e4;border-color:#2dd4bf;background:#fff}
.choice{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:0 0 8px}
.choice .opt{position:relative;margin:0;padding:8px 6px;border:1px solid var(--line);border-radius:10px;background:#fafaf9;text-align:center;font-size:12px;font-weight:600;line-height:1.3;color:#44403c}
.choice .opt.on{background:#ecfdf5;border-color:#5eead4;color:#0f766e}
.choice input{position:absolute;opacity:0;width:0;height:0}
.hold{margin:0 0 8px}
.hold.dim{opacity:.4;pointer-events:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}
button{width:100%;border:0;border-radius:12px;padding:11px;background:linear-gradient(180deg,#0f766e,#0b5f58);color:#fff;font-size:15px;font-weight:600}
.btn-reset{background:#fff;color:#44403c;border:1px solid #d6d3d1;box-shadow:none}
.lang{display:flex;background:#f5f5f4;border:1px solid var(--line);border-radius:999px;padding:2px;flex:0 0 auto}
.lang button{width:auto;padding:4px 8px;margin:0;border-radius:999px;background:transparent;color:#57534e;font-size:11px;font-weight:600;box-shadow:none}
.lang button.on{background:#0f766e;color:#fff}
.lab{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 4px}
.lab label{margin:0;flex:1}
.q{flex:0 0 18px;width:18px;height:18px;padding:0;border-radius:50%;background:#f5f5f4;color:#0f766e;font-size:11px;font-weight:700;border:1px solid #d6d3d1;line-height:16px}
.mask{position:fixed;inset:0;background:rgba(28,25,23,.45);display:none;align-items:center;justify-content:center;padding:20px;z-index:20}
.mask.show{display:flex}
.pop{background:#fff;border-radius:16px;padding:16px;max-width:340px;width:100%;box-shadow:0 20px 50px rgba(0,0,0,.16)}
.pop h3{margin:0 0 8px;font-size:16px}
.pop p{margin:0 0 12px;color:#57534e;line-height:1.6;font-size:14px}
.pop button{margin-top:0}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<div class="cardhead">
<div class="headleft">
<p class="kicker" data-i18n="live">实时状态</p>
<span id="irMark" class="__IR_CLASS__"><span class="dot"></span><span data-i18n="ir">红外</span></span>
</div>
<div class="lang">
<button type="button" id="btnZh" onclick="setLang('zh')">中文</button>
<button type="button" id="btnEn" onclick="setLang('en')">EN</button>
</div>
</div>
<div class="stepbox"><b id="step">__STEP__</b></div>
</div>
<form method="POST" action="/save">
<input type="hidden" name="lang" id="langField" value="__LANG__">
<div class="card">
<p class="group" data-i18n="sense">感应</p>
<div class="lab"><label data-i18n="trigger">冲水触发</label><button type="button" class="q" onclick="help('trigger')">?</button></div>
<div class="choice">
<label class="opt"><input type="radio" name="trigger_mode" value="instant" onchange="syncHold()" __INSTANT_ON__><span data-i18n="triggerInstant">单次</span></label>
<label class="opt"><input type="radio" name="trigger_mode" value="hold" onchange="syncHold()" __HOLD_ON__><span data-i18n="triggerHold">持续</span></label>
</div>
<div id="holdWrap" class="hold">
<div class="lab"><label data-i18n="triggerHoldS">持续时长 (秒)</label></div>
<input name="trigger_hold_s" id="holdSec" type="number" step="0.1" min="0.1" value="__TRIGGER_HOLD__">
</div>
<div class="lab"><label data-i18n="leave">离开后延迟冲水 (秒)</label><button type="button" class="q" onclick="help('leave')">?</button></div>
<input name="leave_delay_s" type="number" step="0.1" min="0.1" value="__LEAVE_DELAY__">
<div class="split"></div>
<p class="group" data-i18n="flush">冲水</p>
<div class="grid">
<div>
<div class="lab"><label data-i18n="flushCount">冲水次数</label><button type="button" class="q" onclick="help('flushCount')">?</button></div>
<input name="flush_count" type="number" step="1" min="1" value="__FLUSH_COUNT__">
</div>
<div>
<div class="lab"><label data-i18n="flushInterval">蓄水时间 (秒)</label><button type="button" class="q" onclick="help('flushInterval')">?</button></div>
<input name="flush_interval_s" type="number" step="0.1" min="0.1" value="__FLUSH_INTERVAL__">
</div>
</div>
<div>
<div class="lab"><label data-i18n="crushTime">粉碎时间 (秒)</label><button type="button" class="q" onclick="help('crushTime')">?</button></div>
<input name="crush_s" type="number" step="0.1" min="0" value="__CRUSH_S__">
</div>
</div>
<div class="actions">
<button type="button" class="btn-reset" onclick="askReset()" data-i18n="reset">重置参数</button>
<button type="submit" data-i18n="save">保存设置</button>
</div>
<p class="hint" id="wifiHint">WiFi 将于 __REMAIN_MIN__ 分钟后关闭，关闭后需重新上电才能再次开启。</p>
</form>
</div>
<div class="mask" id="mask" onclick="hideHelp()">
<div class="pop" onclick="event.stopPropagation()">
<h3 id="helpTitle"></h3>
<p id="helpBody"></p>
<button type="button" id="helpOk" onclick="hideHelp()">知道了</button>
<div id="resetActions" class="actions" style="display:none">
<button type="button" class="btn-reset" onclick="hideHelp()" data-i18n="cancel">取消</button>
<button type="button" onclick="doReset()" data-i18n="resetOk">确认重置</button>
</div>
</div>
</div>
<script>
var LANG="__LANG__";
var lastRemain=0;
var lastState="__RAW_STATE__";
var lastFlushPhase="__FLUSH_PHASE__";
var lastWait=__WAIT_S__;
var lastHold=__HOLD_REMAIN__;
var T={
zh:{title:"自动冲水",live:"实时状态",ir:"红外",irOn:"触发",irOff:"未触发",sense:"感应",trigger:"冲水触发",triggerInstant:"单次",triggerHold:"持续",triggerHoldS:"持续时长 (秒)",leave:"离开后延迟冲水 (秒)",flush:"冲水",flushCount:"冲水次数",flushInterval:"蓄水时间 (秒)",crushTime:"粉碎时间 (秒)",reset:"重置参数",resetOk:"确认重置",cancel:"取消",save:"保存设置",ok:"知道了",idle:"空闲",waitLeave:"等待宠物离开",flushCountdown:"冲水倒计时",flushing:"冲水中",crushing:"粉碎中",waitRefill:"蓄水时间",confirmOccupy:"持续检测",h_reset:"将把感应和冲水参数恢复为默认值，当前语言保持不变。确定要重置吗？",h_trigger:"单次：红外被触发，就触发冲水流程。持续：红外被持续触发指定的时间，就触发冲水流程。",h_leave:"红外从触发变为未触发后，等待这么多秒再冲水。冲水流程一旦开始，必须完成离开倒计时和冲水后，才会重新检测红外。",h_flushCount:"一次离开后电机冲水的次数。",h_flushInterval:"冲水次数大于 1 时，两次冲水之间等待水箱蓄水的时间。",h_crushTime:"粉碎电机用于粉碎排泄物，方便排入下水道。每冲水一次，都按设定的时长进行粉碎。"},
en:{title:"Auto Flush",live:"Live status",ir:"IR",irOn:"Triggered",irOff:"Not triggered",sense:"Sensing",trigger:"Flush trigger",triggerInstant:"Once",triggerHold:"Hold",triggerHoldS:"Hold time (s)",leave:"Flush delay after leave (s)",flush:"Flush",flushCount:"Flush count",flushInterval:"Refill time (s)",crushTime:"Crush time (s)",reset:"Reset",resetOk:"Confirm reset",cancel:"Cancel",save:"Save",ok:"OK",idle:"Idle",waitLeave:"Waiting for the pet to leave",flushCountdown:"Flush countdown",flushing:"Flushing",crushing:"Crushing",waitRefill:"Refill time",confirmOccupy:"Holding",h_reset:"This restores sensing and flush settings to defaults. Language stays the same. Reset now?",h_trigger:"Once: when IR is triggered, the flush sequence starts. Hold: when IR stays triggered for the specified time, the flush sequence starts.",h_leave:"After IR goes from triggered to idle, wait this long before flushing. Once the flush sequence starts, it must finish before IR is checked again.",h_flushCount:"How many flush cycles after the pet leaves.",h_flushInterval:"When flush count is greater than 1, wait this long between cycles so the tank can refill.",h_crushTime:"The crush motor breaks down waste so it can go down the drain. After every flush, it runs for the time you set."}
};
function wifiText(s){
 s=parseInt(s,10); if(isNaN(s)||s<0)s=0; lastRemain=s;
 var m=Math.max(0,Math.ceil(s/60));
 if(LANG==="en") return "WiFi will turn off in "+m+" min. Power-cycle the device to turn it on again.";
 return "WiFi 将于 "+m+" 分钟后关闭，关闭后需重新上电才能再次开启。";
}
function applyLang(){
 var t=T[LANG]||T.zh;
 document.documentElement.lang=LANG==="en"?"en":"zh-CN";
 document.title=t.title;
 document.getElementById("langField").value=LANG;
 document.getElementById("btnZh").className=LANG==="zh"?"on":"";
 document.getElementById("btnEn").className=LANG==="en"?"on":"";
 var els=document.querySelectorAll("[data-i18n]");
 for(var i=0;i<els.length;i++){
  var k=els[i].getAttribute("data-i18n");
  if(t[k]) els[i].textContent=t[k];
 }
 document.getElementById("helpOk").textContent=t.ok;
 document.getElementById("wifiHint").textContent=wifiText(lastRemain);
 setIr(lastIr);
 document.getElementById("step").textContent=stepText();
 syncHold();
 if(document.getElementById("mask").className.indexOf("show")>=0 && window._helpKey) help(window._helpKey);
}
function help(key){
 window._helpKey=key;
 var t=T[LANG]||T.zh;
 document.getElementById("helpTitle").textContent=t[key]||"";
 document.getElementById("helpBody").textContent=t["h_"+key]||"";
 document.getElementById("helpOk").style.display="";
 document.getElementById("resetActions").style.display="none";
 document.getElementById("mask").className="mask show";
}
function askReset(){
 window._helpKey="";
 var t=T[LANG]||T.zh;
 document.getElementById("helpTitle").textContent=t.reset;
 document.getElementById("helpBody").textContent=t.h_reset;
 document.getElementById("helpOk").style.display="none";
 document.getElementById("resetActions").style.display="grid";
 document.getElementById("mask").className="mask show";
}
function doReset(){
 fetch("/reset",{method:"POST"}).then(function(){
  location.replace("/");
 });
}
function hideHelp(){
 window._helpKey="";
 document.getElementById("helpOk").style.display="";
 document.getElementById("resetActions").style.display="none";
 document.getElementById("mask").className="mask";
}
function setLang(next){
 LANG=next;
 applyLang();
 fetch("/lang",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"lang="+next});
}
function syncHold(){
 var hold=document.querySelector('input[name="trigger_mode"][value="hold"]');
 var on=!!(hold&&hold.checked);
 document.getElementById("holdWrap").className=on?"hold":"hold dim";
 var labs=document.querySelectorAll(".choice .opt");
 for(var i=0;i<labs.length;i++){
  var inp=labs[i].querySelector("input");
  labs[i].className=(inp&&inp.checked)?"opt on":"opt";
 }
}
function withWait(msg,s){
 s=parseFloat(s); if(isNaN(s)||s<0) s=0;
 return msg+" "+s.toFixed(1)+"s";
}
function stepText(){
 var t=T[LANG]||T.zh;
 if(lastHold>0 && (lastState==="idle" || lastState==="leaving")) return withWait(t.confirmOccupy,lastHold);
 if(lastState==="occupied") return t.waitLeave;
 if(lastState==="leaving") return withWait(t.flushCountdown,lastWait);
 if(lastState==="flushing"){
  if(lastFlushPhase==="crushing") return withWait(t.crushing,lastWait);
  if(lastFlushPhase==="refill") return withWait(t.waitRefill,lastWait);
  return withWait(t.flushing,lastWait);
 }
 return t.idle;
}
function setIr(present){
 lastIr=!!present;
 document.getElementById("irMark").className=lastIr?"ir-mark on":"ir-mark";
}
var pollBusy=false;
function refresh(){
 if(pollBusy) return;
 pollBusy=true;
 fetch("/status").then(function(r){return r.json()}).then(function(j){
  lastState=j.state||"";
  lastFlushPhase=j.flush_phase||"";
  lastWait=j.wait_s||0;
  lastHold=j.hold_remain_s||0;
  document.getElementById("step").textContent=stepText();
  setIr(j.ir_present);
  document.getElementById("wifiHint").textContent=wifiText(j.wifi_remain_s);
 }).catch(function(){}).then(function(){pollBusy=false;});
}
lastRemain=__REMAIN_S__;
var lastIr=__IR_BOOL__;
applyLang();
refresh();
setInterval(refresh,100);
</script>
</body></html>
"""
    titles = {"zh": "自动冲水", "en": "Auto Flush"}
    raw_state = str(st.get("state", "idle"))
    wait_s = float(st.get("wait_s") or 0)
    hold_remain = float(st.get("hold_remain_s") or 0)
    flush_phase = str(st.get("flush_phase") or "")
    ir_on = bool(st.get("ir_present"))
    mode = cfg.get("trigger_mode") or "hold"
    names = {
        "zh": {
            "idle": "空闲",
            "occupied": "等待宠物离开",
            "leaving": "冲水倒计时 " + _fmt1(wait_s) + "s",
            "flushing": "冲水中 " + _fmt1(wait_s) + "s",
            "crushing": "粉碎中 " + _fmt1(wait_s) + "s",
            "refill": "蓄水时间 " + _fmt1(wait_s) + "s",
            "confirm": "持续检测 " + _fmt1(hold_remain) + "s",
        },
        "en": {
            "idle": "Idle",
            "occupied": "Waiting for the pet to leave",
            "leaving": "Flush countdown " + _fmt1(wait_s) + "s",
            "flushing": "Flushing " + _fmt1(wait_s) + "s",
            "crushing": "Crushing " + _fmt1(wait_s) + "s",
            "refill": "Refill time " + _fmt1(wait_s) + "s",
            "confirm": "Holding " + _fmt1(hold_remain) + "s",
        },
    }
    pack = names.get(lang) or names["zh"]
    if hold_remain > 0 and raw_state in ("idle", "leaving"):
        step_text = pack["confirm"]
    elif raw_state == "flushing" and flush_phase == "crushing":
        step_text = pack["crushing"]
    elif raw_state == "flushing" and flush_phase == "refill":
        step_text = pack["refill"]
    elif raw_state == "leaving":
        step_text = pack["leaving"]
    else:
        step_text = pack.get(raw_state, pack["idle"])
    for key, value in (
        ("__HTML_LANG__", "en" if lang == "en" else "zh-CN"),
        ("__TITLE__", titles.get(lang) or titles["zh"]),
        ("__LANG__", lang),
        ("__SSID__", _html_escape(ssid)),
        ("__RAW_STATE__", _html_escape(raw_state)),
        ("__FLUSH_PHASE__", _html_escape(flush_phase)),
        ("__WAIT_S__", wait_s),
        ("__HOLD_REMAIN__", hold_remain),
        ("__STEP__", _html_escape(step_text)),
        ("__IR_BOOL__", "true" if ir_on else "false"),
        ("__IR_CLASS__", "ir-mark on" if ir_on else "ir-mark"),
        ("__REMAIN_S__", remain_s),
        ("__REMAIN_MIN__", (remain_s + 59) // 60),
        ("__LEAVE_DELAY__", cfg["leave_delay_s"]),
        ("__TRIGGER_HOLD__", cfg["trigger_hold_s"]),
        ("__INSTANT_ON__", "checked" if mode == "instant" else ""),
        ("__HOLD_ON__", "checked" if mode != "instant" else ""),
        ("__FLUSH_COUNT__", cfg["flush_count"]),
        ("__FLUSH_INTERVAL__", cfg["flush_interval_s"]),
        ("__CRUSH_S__", cfg.get("crush_s", 15)),
    ):
        page = page.replace(key, str(value))
    return page


def _parse_form(body):
    result = {}
    if not body:
        return result
    for pair in body.split("&"):
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        result[_urldecode(k)] = _urldecode(v)
    return result


def _urldecode(text):
    text = text.replace("+", " ")
    out = []
    i = 0
    while i < len(text):
        if text[i] == "%" and i + 2 < len(text):
            try:
                out.append(chr(int(text[i + 1 : i + 3], 16)))
                i += 3
                continue
            except ValueError:
                pass
        out.append(text[i])
        i += 1
    return "".join(out)


class WebServer:
    def __init__(self, app):
        self.app = app
        self._server = None

    async def start(self):
        self._server = await asyncio.start_server(self._handle, "0.0.0.0", 80)

    def close(self):
        if self._server:
            self._server.close()
            self._server = None

    async def _handle(self, reader, writer):
        try:
            header = await asyncio.wait_for(reader.read(4096), 3)
            if not header:
                writer.close()
                await writer.wait_closed()
                return
            text = header.decode()
            line = text.split("\r\n", 1)[0]
            parts = line.split(" ")
            method = parts[0] if parts else "GET"
            path = parts[1] if len(parts) > 1 else "/"
            host = ""
            for h in text.split("\r\n"):
                if h.lower().startswith("host:"):
                    host = h.split(":", 1)[1].strip().split(":")[0]
                    break
            body = ""
            if method == "POST":
                length = 0
                for h in text.split("\r\n"):
                    if h.lower().startswith("content-length:"):
                        length = int(h.split(":", 1)[1].strip())
                already = text.split("\r\n\r\n", 1)
                body = already[1] if len(already) > 1 else ""
                remain = length - len(body.encode())
                if remain > 0:
                    extra = await reader.read(remain)
                    body += extra.decode()
            await self._respond(writer, method, path, body, host)
        except Exception as exc:
            try:
                writer.write(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
                writer.write(str(exc).encode())
                await writer.drain()
            except Exception:
                pass
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    def _is_engineer_req(self, path, host, query=""):
        host = (host or "").split(":")[0]
        if host == ENGINEER_IP:
            return True
        if "m=test" in (query or ""):
            return True
        p = (path or "/").split("?")[0]
        if len(p) > 1 and p.endswith("/"):
            p = p[:-1]
        p = p.lower()
        return p in ("/test", "/eng", "/engineer") or p.startswith("/test/")

    async def _write_bytes(self, writer, status, content_type, data):
        writer.write(
            status
            + b"\r\nContent-Type: "
            + content_type
            + b"\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: "
            + str(len(data)).encode()
            + b"\r\n\r\n"
            + data
        )
        await writer.drain()

    async def _respond_engineer(self, writer, method, path, body):
        self.app.enter_engineer()
        p = (path or "/").split("?")[0]
        is_cmd = method == "POST" and (
            "/cmd" in p or p.endswith("/test") or "m=test" in path
        )
        is_status = "/status" in p
        if is_cmd:
            form = _parse_form(body)
            cmd = (form.get("cmd") or body or "").strip()
            if cmd:
                try:
                    self.app.bench_cmd(cmd)
                except Exception as exc:
                    self.app.error = str(exc)
        if is_cmd or is_status:
            try:
                payload = self.app.engineer_status_json().encode()
            except Exception as exc:
                payload = ('{"error":"%s"}' % str(exc).replace('"', "")).encode()
            await self._write_bytes(
                writer, b"HTTP/1.1 200 OK", b"application/json", payload
            )
            return
        try:
            from test_web import render_test_page

            page = render_test_page({})
            data = page.encode()
        except Exception as exc:
            data = (
                "<!DOCTYPE html><meta charset=utf-8><title>test</title>"
                "<p>engineer page error: %s</p>" % _html_escape(exc)
            ).encode()
        await self._write_bytes(
            writer, b"HTTP/1.1 200 OK", b"text/html; charset=utf-8", data
        )

    async def _respond(self, writer, method, path, body, host=""):
        raw = path or "/"
        query = raw.split("?", 1)[1] if "?" in raw else ""
        path = raw.split("?")[0]
        if self._is_engineer_req(path, host, query):
            await self._respond_engineer(writer, method, raw, body)
            return
        if self.app.engineer_mode:
            self.app.leave_engineer()
        if method == "POST" and path.startswith("/lang"):
            form = _parse_form(body)
            self.app.apply_form({"lang": form.get("lang", "zh")})
            data = b'{"ok":1}'
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: "
                + str(len(data)).encode()
                + b"\r\n\r\n"
                + data
            )
            await writer.drain()
            return
        if method == "POST" and path.startswith("/reset"):
            self.app.reset_params()
            writer.write(
                b"HTTP/1.1 303 See Other\r\nLocation: /\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
            )
            await writer.drain()
            return
        if method == "POST" and path.startswith("/save"):
            form = _parse_form(body)
            self.app.apply_form(form)
            writer.write(
                b"HTTP/1.1 303 See Other\r\nLocation: /\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
            )
            await writer.drain()
            return
        if path.startswith("/status"):
            payload = self.app.status_json()
            data = payload.encode()
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: "
                + str(len(data)).encode()
                + b"\r\n\r\n"
                + data
            )
            await writer.drain()
            return
        page = render_page(self.app.cfg, self.app.ssid, self.app.status())
        data = page.encode()
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: "
            + str(len(data)).encode()
            + b"\r\n\r\n"
            + data
        )
        await writer.drain()
