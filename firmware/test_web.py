def render_test_page(status):
    st = status or {}
    ir_on = "1" if st.get("ir_present") else "0"
    crush_on = "1" if st.get("crush") else "0"
    servo = st.get("servo", 0)
    ia = st.get("i_a", 0)
    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>工程师测试</title>
<style>
body{margin:0;font-family:sans-serif;background:#0f172a;color:#e2e8f0}
.wrap{max-width:480px;margin:0 auto;padding:12px}
h1{font-size:18px;margin:8px 0 4px}
.sub{color:#94a3b8;font-size:12px;margin:0 0 12px}
.card{background:#1e293b;border-radius:12px;padding:12px;margin:0 0 10px}
.row{display:flex;flex-wrap:wrap;gap:8px}
button{flex:1;min-width:90px;padding:10px;border:0;border-radius:10px;background:#0ea5e9;color:#fff;font-size:14px}
button.off{background:#334155}
.val{font-size:15px;line-height:1.5}
.warn{color:#fbbf24;font-size:12px}
</style>
</head>
<body>
<div class="wrap">
<h1>工程师测试</h1>
<p class="sub">http://192.168.99.1/test · 本模式热点保持开启 · 断电后回到客户模式</p>
<div class="card">
<div class="val" id="st">红外 __IR__ · 舵机 __SERVO__° · 粉碎 __CRUSH__ · 电流 __IA__ A</div>
<p class="warn" id="trip"></p>
</div>
<div class="card">
<p class="sub">冲水舵机（回位 / 按下，保存后断电仍有效）</p>
<div class="row" style="margin-bottom:8px">
<label class="sub" style="flex:1">回位 °<br><input id="home" type="number" min="0" max="180" step="1" value="0" style="width:100%;padding:8px;border-radius:8px;border:0"></label>
<label class="sub" style="flex:1">按下 °<br><input id="press" type="number" min="0" max="180" step="1" value="70" style="width:100%;padding:8px;border-radius:8px;border:0"></label>
</div>
<div class="row">
<button onclick="saveServo()">保存角度</button>
<button onclick="cmd('PRESS')">冲水 PRESS</button>
<button onclick="cmd('RELEASE')">回位 RELEASE</button>
</div>
</div>
<div class="card">
<p class="sub">粉碎电机（先试转，再保存选用方向；开 = 按保存方向转）</p>
<div class="row" style="margin-bottom:8px">
<label class="sub"><input type="radio" name="cdir" id="dirFwd" value="fwd" checked> 正转</label>
<label class="sub"><input type="radio" name="cdir" id="dirRev" value="rev"> 反转</label>
<button onclick="saveCrushDir()">保存方向</button>
</div>
<div class="row" style="margin-bottom:8px">
<button onclick="cmd('CRUSH 1')">开</button>
<button class="off" onclick="cmd('STOP')">停</button>
</div>
<div class="row">
<button onclick="cmd('FWD')">试转正转</button>
<button onclick="cmd('REV')">试转反转</button>
</div>
</div>
<div class="card">
<p class="sub">模式</p>
<div class="row">
<button class="off" onclick="cmd('CUST')">返回客户模式</button>
</div>
</div>
</div>
<script>
var filled=false;
function paint(j){
 var ir=j.ir_present?"触发":"未触发";
 var crush=j.crush?"开":"关";
 var dir=j.crush_dir==="rev"?"反转":"正转";
 document.getElementById("st").textContent="红外 "+ir+" (raw="+j.ir_raw+") · 舵机 "+(j.servo||0).toFixed(1)+"° · 粉碎 "+crush+"("+dir+") · 电流 "+(j.i_a||0).toFixed(2)+" A";
 document.getElementById("trip").textContent=j.trip?"过流保护，已停粉碎":"";
 if(!filled && j.release_deg!=null){
  document.getElementById("home").value=j.release_deg;
  document.getElementById("press").value=j.press_deg;
  if(j.crush_dir==="rev") document.getElementById("dirRev").checked=true;
  else document.getElementById("dirFwd").checked=true;
  filled=true;
 }
}
function saveServo(){
 var a=document.getElementById("home").value;
 var b=document.getElementById("press").value;
 cmd("SERVOCFG "+a+" "+b);
 filled=false;
}
function saveCrushDir(){
 var d=document.getElementById("dirRev").checked?"rev":"fwd";
 cmd("CRUSHDIR "+d);
 filled=false;
}
function cmd(c){
 if(c==="CUST"){
  fetch("/test/cmd",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"cmd="+encodeURIComponent(c)})
   .then(function(){ location.replace("/"); }).catch(function(){ location.replace("/"); });
  return;
 }
 fetch("/test/cmd",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"cmd="+encodeURIComponent(c)})
  .then(function(r){return r.json()}).then(paint).catch(function(){});
}
function tick(){
 fetch("/test/status").then(function(r){return r.json()}).then(paint).catch(function(){});
}
tick();
setInterval(tick,400);
</script>
</body></html>
"""
    for key, value in (
        ("__IR__", "触发" if ir_on == "1" else "未触发"),
        ("__SERVO__", "{:.1f}".format(float(servo))),
        ("__CRUSH__", "开" if crush_on == "1" else "关"),
        ("__IA__", "{:.2f}".format(float(ia))),
    ):
        page = page.replace(key, str(value))
    return page
