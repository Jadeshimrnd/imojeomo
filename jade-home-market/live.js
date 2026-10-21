'use strict';
const $ = s => document.querySelector(s);
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = amount => (amount / 10000).toFixed(2);
const median = values => { const v = [...values].sort((a,b)=>a-b), n=v.length; return n ? (v[Math.floor((n-1)/2)]+v[Math.floor(n/2)])/2 : null; };
const signed = n => n === null ? '표본 부족' : `${n>0?'+':''}${n.toFixed(1)}%`;
let groups=[], selected=null, months=[], page=0, descending=true, scope='';
let favoriteKeys;
try {favoriteKeys=new Set(JSON.parse(localStorage.getItem('jade-live-favorites')||'[]'));} catch {favoriteKeys=new Set();}

$('.header-right').textContent='국토교통부 실거래';
$('.sample').innerHTML='<span>실거래 조회</span><p>신고·정정에 따라 변경될 수 있습니다</p>';
$('.notice').setAttribute('role','status');
$('.notice').textContent='시·구별 실제 신고 거래를 조회합니다. 같은 단지·주소·전용면적을 묶고, 해제 신고 거래는 제외합니다.';
$('.small-tag').textContent='시·구별 조회';
$('.filters').insertAdjacentHTML('beforebegin', `<form id="live-query" class="live-query"><label>조회월 <input id="live-month" type="month" required></label><label>조회 범위 <select id="live-months"><option value="3">3개월</option><option value="6">6개월</option><option value="12">12개월</option></select></label><button type="submit">실거래 조회</button><span id="live-status" role="status" aria-live="polite"></span></form>`);
$('#leaders').disabled=true;
$('#leaders').closest('label').title='공식 단지 식별 매핑 후 제공 예정입니다.';
$('#leaders').closest('label').querySelector('span').textContent='대장 필터 준비 중';
$('#watchlist').innerHTML='<p class="insight-caption">실거래 조회와 별도로 KRES 분석은 아직 연결되지 않았습니다.</p>';
$('.watch-card .connection-tag').textContent='KRES 미연동';
$('.watch-card .insight-caption:last-child').textContent='검증된 선정 기준과 분석 데이터가 연결되면 표시합니다.';
$('.chart-label').textContent='월별 중위가격 · 거래 점';
$('.chart-foot span:last-child').textContent='단위: 억원 · 실거래';
$('.stats article:last-child > span').textContent='유효 거래';
$('.stats article:last-child p').textContent='조회 기간 · 해제 거래 제외';
$('.stats article:first-child p').textContent='조회 지역의 단지·면적 조합';
$('.stats article:nth-child(2) p').textContent='마지막 두 달 · 각 3건 이상';
$('.stats article:nth-child(3) p').textContent='마지막 두 달 · 각 3건 이상';
$('footer span:last-child').textContent='출처: 국토교통부 · 전월세 매물/시장 심리 미연동';
$('.periods').querySelectorAll('button').forEach(button=>{
 button.classList.toggle('active',button.dataset.period==='월간');
 button.disabled=button.dataset.period!=='월간';
 button.title='실거래 모드에서는 현재 월별 집계를 제공합니다. 상단에서 조회 범위를 선택하세요.';
});
$('.detail').hidden=true;

async function getJSON(url) {
 const r=await fetch(url); let body;
 try {body=await r.json();} catch {throw Error('API 서버 응답을 확인할 수 없습니다. python3 server.py로 실행해 주세요.');}
 if(!r.ok) throw Error(body.error || '실거래 조회에 실패했습니다.');
 return body;
}
function groupTrades(data) {
 const map=new Map();
 for(const t of data.trades) {
  const key=JSON.stringify([t.district,t.dong,t.jibun,t.name,t.area]);
  if(!map.has(key)) map.set(key,{key,name:t.name,area:t.area,dong:t.dong,jibun:t.jibun,trades:[]});
  map.get(key).trades.push(t);
 }
 return [...map.values()].map(g=>{
  g.series=data.months.map(m=>({month:m,values:g.trades.filter(t=>t.date.replaceAll('-','').startsWith(m)).map(t=>t.amount)}));
  g.series.forEach(s=>s.price=median(s.values));
  const prev=g.series.at(-2),last=g.series.at(-1);
  g.change=prev.values.length>=3 && last.values.length>=3 ? (last.price/prev.price-1)*100 : null;
  g.trades.sort((a,b)=>b.date.localeCompare(a.date));g.price=g.trades[0].amount;
  return g;
 });
}
function render() {
 const q=$('#search').value.trim();
 const visible=groups.filter(g=>(g.name+g.dong).includes(q)).sort((a,b)=>{
  if(a.change===null && b.change===null)return a.name.localeCompare(b.name,'ko');
  if(a.change===null)return 1;if(b.change===null)return -1;
  return descending?b.change-a.change:a.change-b.change;
 });
 if(!visible.some(g=>g.key===selected)) selected=visible[0]?.key;
 page=Math.min(page,Math.max(0,Math.ceil(visible.length/20)-1));
 const paged=visible.slice(page*20,page*20+20);
 $('#total').innerHTML=visible.length+'<small>개</small>';
 $('#rise').textContent=visible.filter(g=>g.change!==null&&g.change>0).length;
 $('#fall').textContent=visible.filter(g=>g.change!==null&&g.change<0).length;
 $('#leaderCount').innerHTML=visible.reduce((n,g)=>n+g.trades.length,0)+'<small>건</small>';
 $('#list-count').textContent=visible.length;
 $('#list').innerHTML=paged.length?paged.map(g=>`<button class="apt-row ${g.key===selected?'selected':''}" data-key="${escapeHTML(g.key)}" aria-pressed="${g.key===selected}"><span><b>${escapeHTML(g.dong)}</b><small>${escapeHTML(g.name)} · 전용 ${escapeHTML(g.area)}㎡</small></span><span class="row-price">${money(g.price)}</span><span class="row-change ${g.change===null?'':g.change>=0?'up':'down'}">${signed(g.change)}</span></button>`).join(''):'<div class="empty">조회된 거래가 없습니다.</div>';
 $('#page-info').textContent=visible.length?`${page*20+1}–${Math.min((page+1)*20,visible.length)} / ${visible.length}개`:'0개';
 $('#prev-page').disabled=page===0;$('#next-page').disabled=(page+1)*20>=visible.length;
 $('.detail').hidden=!visible.length;
 if(visible.length)detail();
}
function detail() {
 const g=groups.find(g=>g.key===selected);if(!g)return;
 $('#location').textContent=`${scope} / ${g.dong} ${g.jibun}`;
 $('#apt-name').textContent=g.name;$('#area').textContent=`전용 ${g.area}㎡ · ${(Number(g.area)/3.305785).toFixed(1)}평`;
 $('#leader-badge').hidden=true;$('#price').textContent=money(g.price)+'억';
 $('#change').textContent=signed(g.change);$('#change').className=g.change===null?'':g.change>=0?'up':'down';
 $('#comparison').textContent=`최근 계약 ${g.trades[0].date} · 등락률은 ${months.at(-2)}→${months.at(-1)} 월 중위가격`;
 $('#favorite').textContent=favoriteKeys.has(g.key)?'★':'☆';$('#favorite').setAttribute('aria-pressed',favoriteKeys.has(g.key));
 $('#favorite').setAttribute('aria-label',favoriteKeys.has(g.key)?'관심 단지 해제':'관심 단지 추가');
 $('.recent-head span').textContent=`조회 ${g.trades.length}건 · 최근 20건 표시`;
 $('#trades').innerHTML=g.trades.slice(0,20).map(t=>`<tr><td>${escapeHTML(t.date)}</td><td>${escapeHTML(t.area)}㎡</td><td>${escapeHTML(t.floor)}층</td><td>${money(t.amount)}억</td></tr>`).join('');
 $('#method').textContent='동일 법정동·지번·단지명·정확한 전용면적별 집계입니다. 단지 공식 식별자 매핑은 미완료입니다. 등락률은 마지막 두 달 각각 3건 이상일 때만 표시합니다. 중위가격·최근 거래가격은 호가가 아니며 층·동·향 구성에 따라 달라집니다. 중복된 것처럼 보이는 거래도 서로 다른 계약일 수 있어 임의로 삭제하지 않습니다. 신고 지연·해제·정정으로 결과가 바뀔 수 있습니다.';
 $('#chart-note').textContent='거래 없는 월은 공백 · 원: 개별 계약 · 숫자: 월 거래 건수';
 drawChart(g);
}
function drawChart(g) {
 const width=Math.max(280,$('#chart').clientWidth),height=280,left=12,right=60,top=20,bottom=220;
 const amounts=g.trades.map(t=>t.amount/10000),pad=Math.max(.1,(Math.max(...amounts)-Math.min(...amounts))*.15);
 const low=Math.min(...amounts)-pad,high=Math.max(...amounts)+pad;
 const x=i=>left+i/(months.length-1)*(width-left-right),y=v=>top+(high-v)/(high-low)*(bottom-top);
 let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="월별 실제 거래 가격">`;
 for(let i=0;i<5;i++){const v=low+(high-low)*i/4;svg+=`<line x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}" stroke="#ded5c7"/><text x="${width-right+5}" y="${y(v)+4}" fill="#8d8273" font-size="10">${v.toFixed(2)}</text>`;}
 g.series.forEach((s,i)=>{
  if(i && s.price!==null && g.series[i-1].price!==null)svg+=`<line x1="${x(i-1)}" y1="${y(g.series[i-1].price/10000)}" x2="${x(i)}" y2="${y(s.price/10000)}" stroke="#88704e" stroke-width="2"/>`;
  for(const amount of s.values)svg+=`<circle cx="${x(i)}" cy="${y(amount/10000)}" r="3" fill="#bbaa8d" opacity=".65"><title>${s.month} 실거래 ${money(amount)}억</title></circle>`;
  if(s.price!==null)svg+=`<circle cx="${x(i)}" cy="${y(s.price/10000)}" r="4" fill="#88704e"><title>중위가격 ${money(s.price)}억 · ${s.values.length}건</title></circle>`;
  svg+=`<text x="${x(i)}" y="244" text-anchor="middle" font-size="9" fill="#8d8273">${s.values.length}건</text>`;
  if(months.length<=6||i%2===0||i===months.length-1)svg+=`<text x="${x(i)}" y="267" text-anchor="${i===0?'start':i===months.length-1?'end':'middle'}" font-size="9" fill="#8d8273">${s.month.slice(2,4)}.${s.month.slice(4)}</text>`;
 });
 $('#chart').innerHTML=svg+'</svg>';$('#chart').setAttribute('aria-label',`${g.name} 월별 실거래 추이`);
}
async function load() {
 const button=$('#live-query button');button.disabled=true;
 $('#live-status').textContent='국토부 거래 조회 중…';groups=[];selected=null;render();
 try {
  const data=await getJSON(`/api/trades?${new URLSearchParams({district:$('#district').value,month:$('#live-month').value.replace('-',''),months:$('#live-months').value})}`);
  months=data.months;scope=data.district;groups=groupTrades(data);page=0;
  document.querySelectorAll('.scope-label').forEach(el=>el.textContent=scope);
  $('#live-status').textContent=`${scope} · ${months[0]}–${months.at(-1)} · ${data.trades.length}건 (신고 지연·정정 가능)`;
  render();
 } catch(e){$('#live-status').textContent=e.message;$('#list').innerHTML='<div class="empty">조회 실패 · 예시 가격으로 대체하지 않습니다.</div>';}
 finally{button.disabled=false;}
}
$('#live-query').onsubmit=e=>{e.preventDefault();load();};
$('#district').onchange=load;
$('#search').oninput=()=>{page=0;render();};
$('#sort').onclick=()=>{descending=!descending;$('#sort').textContent='등락률 '+(descending?'↓':'↑');render();};
$('#prev-page').onclick=()=>{page--;render();};$('#next-page').onclick=()=>{page++;render();};
$('#list').onclick=e=>{const row=e.target.closest('[data-key]');if(!row)return;selected=row.dataset.key;render();if(matchMedia('(max-width:760px)').matches)$('.detail').scrollIntoView({behavior:'smooth'});};
$('#favorite').onclick=()=>{if(!selected)return;favoriteKeys.has(selected)?favoriteKeys.delete(selected):favoriteKeys.add(selected);try{localStorage.setItem('jade-live-favorites',JSON.stringify([...favoriteKeys]));}catch{}detail();};
window.addEventListener('resize',()=>{if(!$('.detail').hidden)detail();});
let config;
function regionOptions(region='전체'){
 $('#district').innerHTML=Object.entries(config.districts).filter(([,name])=>region==='전체'||(region==='서울'?name.startsWith('서울'):!name.startsWith('서울'))).map(([code,name])=>`<option value="${code}">${escapeHTML(name)}</option>`).join('');
 if(region!=='경기/인천')$('#district').value='11710';
}
(async()=>{try{
 config=await getJSON('/api/config');$('#live-month').value=config.defaultMonth.slice(0,4)+'-'+config.defaultMonth.slice(4);
 regionOptions();document.querySelectorAll('.region').forEach(button=>button.onclick=()=>{document.querySelectorAll('.region').forEach(b=>b.classList.toggle('active',b===button));regionOptions(button.dataset.region);load();});
 await load();
}catch(e){$('#live-status').textContent=e.message;$('#list').innerHTML='<div class="empty">API 서버를 실행해 주세요.</div>';}})();
