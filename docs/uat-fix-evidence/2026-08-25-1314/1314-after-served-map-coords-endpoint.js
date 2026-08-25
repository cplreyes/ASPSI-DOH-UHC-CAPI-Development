# #1314 after-fix evidence — served map page excerpt
# Source: https://capi.asiansocial.org/projects/uhc-y2/monitoring/map/ (pulled from /opt/app/capi-www/... on the box)
# Page stamp: "generated": "2026-08-25 03:32 UTC"   generator: /opt/csweb-map-gen.py md5 dffb2a0001b3efdd8533118a3cfe179c
# Before: const COORDS_EP='coords.php'  (relative -> /projects/uhc-y2/monitoring/map/coords.php -> static 404 -> 'Network error')

// ---- coordinate intake: enter lat/lon inline, or download/import the CSV, -> coords.php ----
// ABSOLUTE on purpose: the map is served from /projects/uhc-y2/monitoring/map/ (capi nginx, static)
// since the 2026-08-09 console unification, but coords.php lives on the lamp Apache at /docs/.
// A relative 'coords.php' resolved to a static 404 and surfaced as 'Network error' (#1314).
const COORDS_EP='/docs/coords.php';
function asJson(r){ const ct=r.headers.get('content-type')||'';
  if(ct.indexOf('json')>=0) return r.json();   // coords.php always answers JSON, even on 400/500 (keeps its error text)
  throw new Error(r.ok?'Unexpected reply — sign in again (reload the page)'
    :'HTTP '+r.status+(r.status===401||r.status===403?' — sign in again (reload the page)':'')); }
function netErr(e){ return (e&&/^HTTP /.test(e.message))?e.message:'Network error — is the site reachable?'; }
function awStatus(msg,ok){ const s=document.getElementById('awStatus'); if(!s) return;
  s.textContent=msg||''; s.className='awstatus'+(ok===true?' ok':ok===false?' err':''); }
function downloadTemplate(){
  const cols=['code9','facility_name','municipality','province','region','lat','lon','note'];
  const q=v=>{ v=(v==null?'':''+v); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v; };
  const lines=[cols.join(',')];
  (P.awaiting||[]).forEach(a=>lines.push([a.code9,a.name,a.muni,a.prov,a.region,'','',''].map(q).join(',')));
  const blob=new Blob(['﻿'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob), a=document.createElement('a');
  a.href=url; a.download='facility_coords_manual.csv'; document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(url);
}
function optimisticPin(u){                 // show a violet pin now; the 2-min cron makes it permanent
  const aw=(P.awaiting||[]).find(a=>a.code9===u.code9)||{};
  (P.facilities||[]).push({code9:u.code9, name:u.name||aw.name||u.code9,
    region:aw.region||'(unknown)', prov:aw.prov||'(unknown)', insts:aw.insts||[], target:0,
    lat:+u.lat, lon:+u.lon, placed:'manual', done:false, nCases:0, nCompleted:0});
  P.awaiting=(P.awaiting||[]).filter(a=>a.code9!==u.code9);
  if(P.facMeta){ P.facMeta.manual=(P.facMeta.manual||0)+1; P.facMeta.noloc=Math.max(0,(P.facMeta.noloc||0)-1); }
}
function afterSave(res){
  (res.updated||[]).forEach(optimisticPin);
  render(); renderAwaiting();
  const n=res.updatedCount||0, sk=(res.skipped||[]);
  let msg=n+' coordinate'+(n===1?'':'s')+' saved';
  if(sk.length) msg+=', '+sk.length+' skipped ('+esc(sk[0].reason||'invalid')+')';
  if(n) msg+=' · pins appear within ~2 min';
  awStatus(msg, n>0);
}
function saveRow(code,lat,lon,btn){
  awStatus('Saving…'); if(btn) btn.disabled=true;
  fetch(COORDS_EP,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({code9:code,lat:lat,lon:lon})})
    .then(asJson).then(res=>{ if(btn) btn.disabled=false;
      if(res.ok) afterSave(res); else awStatus(res.error||'Save failed',false); })
    .catch(function(e){ if(btn) btn.disabled=false; awStatus(netErr(e),false); });
}
function importCsv(file){
  awStatus('Importing '+file.name+'…');
  const fd=new FormData(); fd.append('csv',file,file.name);
  fetch(COORDS_EP,{method:'POST',body:fd}).then(asJson)
    .then(res=>{ if(res.ok) afterSave(res); else awStatus(res.error||'Import failed',false); })
    .catch(function(e){ awStatus(netErr(e),false); });
}
