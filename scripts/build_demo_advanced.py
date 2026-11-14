"""Build a standalone, read-only demo from recorded advanced v2 results."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

reviews = {x["id"]: x for x in read("advanced_v2/results/test_reasoned/reviews.json")["reviews"]}
items = []
for gold in read("advanced_v2/benchmarks/test.gold.json"):
    trace = read(f"advanced_v2/results/test_reasoned/{gold['id']}.json")
    items.append({k: trace[k] for k in ("id", "question", "status", "claims", "elapsed_ms", "viewed_pages")} | {
        "group": gold["primary_group"], "expected": gold["expected"],
        "passed": reviews[gold["id"]]["passed"], "reason": reviews[gold["id"]]["reason"],
    })
template = '''<!doctype html>
<html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Day 7 · Retrieval & Context — Demo</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121e30;--line:#283950;--muted:#a4b5cc;--accent:#64e5bb}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#edf4ff;font:16px/1.6 system-ui,sans-serif}main{max-width:1240px;margin:auto;padding:32px}header{display:flex;justify-content:space-between;gap:20px;align-items:center}small,.muted{color:var(--muted)}h1{font-size:clamp(30px,4vw,50px);line-height:1.15;margin:22px 0}h2{font-size:23px}h3{font-size:17px}a{color:var(--accent)}.tag{border:1px solid var(--line);border-radius:30px;padding:6px 14px;font-size:13px}.hero{padding:24px 0}.hero p{max-width:820px;color:var(--muted)}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card,.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:22px}.card strong{display:block;font-size:32px;color:var(--accent)}.flow{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}.flow span{padding:10px 14px;background:var(--panel);border-radius:9px;border:1px solid var(--line)}.workspace{display:grid;grid-template-columns:340px 1fr;gap:20px}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:15px}input,select,button{font:inherit;background:#0d1727;color:#edf4ff;border:1px solid var(--line);border-radius:8px;padding:10px}input{width:100%}button{cursor:pointer}button:hover,button.active{border-color:var(--accent);background:#193b3a}#list{max-height:620px;overflow:auto;display:grid;gap:8px}#list button{text-align:left;font-size:13px}#list button span{display:block}.good{color:#64e5bb}.bad{color:#ffb692}.citation{border-left:3px solid var(--accent);padding:4px 14px;margin:16px 0;color:var(--muted);font-size:14px}blockquote{margin:8px 0;color:#e0ecfb}details{margin-top:20px;border-top:1px solid var(--line);padding-top:14px}summary{cursor:pointer}#detail{overflow-wrap:anywhere}footer{padding:30px 0;color:var(--muted);font-size:13px}.note{border-left:3px solid #ffd380;padding:12px 18px;background:#26271f;margin:24px 0}.bars{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:20px 0}.bar{height:6px;background:var(--line);border-radius:8px;overflow:hidden}.bar i{display:block;height:100%;background:var(--accent)}@media(max-width:850px){main{padding:18px}.cards{grid-template-columns:repeat(2,1fr)}.workspace{grid-template-columns:1fr}.bars{grid-template-columns:repeat(3,1fr)}#list{max-height:250px}header{align-items:start}}
</style>
<main>
<header><b>DAY 07 / AGENTIC RAG</b><span class="tag">Demo kết quả đã lưu · Không gọi API</span></header>
<section class="hero"><small>K5-L3A · 2A202603399 · Đồng Ngọc Phúc</small><h1>Đọc tài liệu.<br>Trả lời có bằng chứng.</h1><p>Pipeline truy xuất toàn bộ NASA Systems Engineering Handbook, đọc trang và phóng to vùng cần thiết, kiểm tra câu trả lời với nguồn trước khi trả kết quả.</p></section>
<div class="cards"><div class="card"><small>Test mới độc lập</small><strong>96,67%</strong>29 / 30 câu đạt</div><div class="card"><small>Tài liệu nguồn</small><strong>297</strong>trang PDF</div><div class="card"><small>Thiếu bằng chứng</small><strong>6 / 6</strong>xử lý đúng về nội dung</div><div class="card"><small>Lỗi hệ thống</small><strong>0</strong>trên 30 câu test mới</div></div>
<div class="flow"><span>① BM25 tìm trang</span><span>② Đọc ảnh gốc</span><span>③ Zoom vùng</span><span>④ Kiểm chứng nguồn</span><span>⑤ Citation / từ chối</span></div>
<div class="bars" id="groups"></div>
<div class="note">Vòng cũ: <b>23/30</b> — giữ nguyên. Lỗi cũ được dùng làm dev; bộ test mới được chốt trước khi đánh giá. Hai bộ khác nhau nên mức tăng không phải so sánh trên cùng bộ test. Pipeline: GPT-5.2, reasoning medium, top-k 7.</div>
<h2>Khám phá 30 câu test</h2><p class="muted">Chọn câu để xem đầu ra thực tế, citation và nhận xét chấm. Có thể lọc câu chưa đạt để trình bày giới hạn của hệ thống.</p>
<div class="toolbar"><select id="group" aria-label="Nhóm câu"><option value="all">Tất cả nhóm</option></select><select id="result" aria-label="Kết quả"><option value="all">Tất cả kết quả</option><option value="pass">Đạt</option><option value="fail">Chưa đạt</option></select><button id="prev">← Trước</button><button id="next">Tiếp →</button></div>
<div class="workspace"><aside class="panel"><input id="search" placeholder="Tìm câu hỏi hoặc mã câu…" aria-label="Tìm câu hỏi"><p id="count" class="muted"></p><div id="list"></div></aside><article id="detail" class="panel" aria-live="polite"></article></div>
<footer>Đây là bản phát lại bằng chứng, không phải chat trực tiếp. Chi phí test ước tính: $3,0354 · 162 lượt gọi model · Thời gian chạy toàn bộ khoảng 6 phút (2 workers). Chấm dựa trên đối chiếu nguồn; không phải điểm do giảng viên xác nhận.<br>Nguồn: <a href="https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf" target="_blank" rel="noopener">NASA Systems Engineering Handbook (Rev. 2)</a>. Citation dùng số trang PDF vật lý. File HTML không chứa API key và không gửi câu hỏi đi.</footer>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id),labels={table:'Bảng',diagram:'Sơ đồ',chart:'Biểu đồ',multi_hop:'Đa bước',text:'Văn bản',unanswerable:'Thiếu bằng chứng'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let selected=data[0].id,visible=data;
Object.entries(labels).forEach(([k,v])=>{let rows=data.filter(x=>x.group===k),n=rows.filter(x=>x.passed).length;$('group').add(new Option(v,k));$('groups').insertAdjacentHTML('beforeend',`<div><small>${v}</small><div>${n}/${rows.length}</div><div class="bar"><i style="width:${100*n/rows.length}%"></i></div></div>`)});
function render(){const q=$('search').value.toLowerCase();visible=data.filter(x=>($('group').value==='all'||x.group===$('group').value)&&($('result').value==='all'||x.passed===($('result').value==='pass'))&&(x.id+' '+x.question).toLowerCase().includes(q));if(!visible.some(x=>x.id===selected))selected=visible[0]?.id;$('count').textContent=visible.length+' câu phù hợp';$('list').replaceChildren();visible.forEach(x=>{let b=document.createElement('button');b.className=x.id===selected?'active':'';b.innerHTML=`<span class="${x.passed?'good':'bad'}">${esc(x.id)} · ${x.passed?'Đạt':'Chưa đạt'}</span>${esc(x.question)}`;b.onclick=()=>{selected=x.id;render()};$('list').append(b)});const x=data.find(x=>x.id===selected);if(!x){$('detail').textContent='Không có câu phù hợp.';return}$('detail').innerHTML=`<small>${esc(x.id)} / ${labels[x.group]} / ${(x.elapsed_ms/1000).toFixed(1)} giây</small><h2>${esc(x.question)}</h2><p class="${x.passed?'good':'bad'}">● ${x.passed?'Đạt':'Chưa đạt'} · Status thực tế: ${esc(x.status)}</p>${x.claims.map(c=>`<p>${esc(c.text)}</p>${(c.citations||[]).map(s=>{let p=Number(s.source_id.split('p').pop());return `<div class="citation"><a target="_blank" rel="noopener" href="https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf#page=${p}">${esc(s.source_id)} ↗</a><div>${esc(s.locator)}</div><blockquote>“${esc(s.evidence)}”</blockquote></div>`}).join('')}`).join('')}<details><summary>Xem đáp án chuẩn & nhận xét chấm</summary><h3>Đáp án chuẩn</h3><p>${esc(x.expected)}</p><h3>Nhận xét</h3><p>${esc(x.reason)}</p><small>Các trang đã đọc: ${x.viewed_pages.join(', ')}</small></details>${x.id==='ADV2-TEST-27'?'<p class="muted">Lưu ý: status là answered nhưng nội dung “None” được chấm là từ chối về mặt ngữ nghĩa.</p>':''}`}
['group','result','search'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));for(const [id,step] of [['prev',-1],['next',1]])$(id).onclick=()=>{if(visible.length){selected=visible[(visible.findIndex(x=>x.id===selected)+step+visible.length)%visible.length].id;render()}};render();
</script></html>'''
out = ROOT / "demo_advanced.html"
out.write_text(template.replace("__DATA__", json.dumps(items, ensure_ascii=False).replace("<", "\\u003c")), encoding="utf-8")
print(f"Built {out.name}: {len(items)} recorded cases, {out.stat().st_size} bytes")
