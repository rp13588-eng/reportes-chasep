// Extractor del PDF "MexicoSalesComparison" (HyCite). Ejecutar con javascript_tool de Claude in Chrome
// en la pestaña que muestra el PDF abierto (origen mail-attachment.googleusercontent.com, recién navegado).
// Devuelve un arreglo de líneas: H:, F:, D:, T:MES|m25|m26|%|y25|y26|%, id|m25|m26|y25|y26|R|NOMBRE
(async()=>{
const inflate=async b=>new Uint8Array(await new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('deflate'))).arrayBuffer());
const r=await fetch(location.href);const buf=new Uint8Array(await r.arrayBuffer());
if(new TextDecoder('latin1').decode(buf.slice(0,5))!=='%PDF-')return ['ERROR: no es PDF'];
const txt=new TextDecoder('latin1').decode(buf);
let re=/<<([^]*?)>>\s*stream\r?\n/g,m,items=[],pg=0;
while((m=re.exec(txt))){const st=m.index+m[0].length,en=txt.indexOf('endstream',st);if(!/FlateDecode/.test(m[1]))continue;let s;
 try{s=new TextDecoder('latin1').decode(await inflate(buf.slice(st,en)))}catch(e){try{s=new TextDecoder('latin1').decode(await inflate(buf.slice(st,en-2)))}catch(e2){continue}}
 if(!/BT/.test(s))continue;pg++;
 const tr=/BT\s+\/F\d+\s+[\d.]+\s+Tf\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+rg\s+[\d.]+\s+TL\s+([\d.]+)\s+([\d.]+)\s+Td\s+\(((?:\\.|[^\\)])*)\)\s*Tj/g;let t;
 while((t=tr.exec(s)))items.push({p:pg,x:+t[1],y:+t[2],t:t[3].replace(/\\(.)/g,'$1')});}
const out=['P:'+pg+' N:'+items.length];
out.push('H:'+items.filter(i=>i.p===1&&Math.abs(i.y-550)<3).sort((a,b)=>a.x-b.x).map(i=>i.t).join('|'));
out.push('F:'+items.filter(i=>i.p===1&&i.y<35).map(i=>i.t).join('|'));
const num=items.filter(i=>i.x>270&&/^[-$\d]/.test(i.t)&&i.y>40&&i.y<545);const g={};
num.forEach(i=>{const k=i.p+'_'+Math.round(i.y);(g[k]=g[k]||[]).push(i)});
const lab=items.filter(i=>i.x<260&&i.y>40&&i.y<545);
lab.filter(l=>/DETAILS/.test(l.t)).forEach(l=>out.push('D:'+l.t));
Object.keys(g).sort((a,b)=>{const [pa,ya]=a.split('_').map(Number),[pb,yb]=b.split('_').map(Number);return pa-pb||yb-ya}).forEach(k=>{
 const [p,y]=k.split('_').map(Number);const v=g[k].sort((a,b)=>a.x-b.x).map(i=>i.t.replace(/[$,]/g,''));
 const L=lab.filter(l=>l.p===p&&Math.abs(l.y-y)<=9).sort((a,b)=>b.y-a.y).map(l=>l.t.trim()).join(' ');
 const id=(L.match(/^(\d+)-/)||[])[1];
 if(/TOTALS/.test(L))out.push('T:'+L.replace(' TOTALS:','')+'|'+v.join('|'));
 else if(id)out.push(id+'|'+[v[0],v[1],v[3],v[4],v[6]].join('|')+'|'+L.replace(/^\d+-/,''));
 else out.push('?:'+L+'|'+v.join('|'));});
return out;
})()
