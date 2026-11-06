const {chromium}=require('playwright');const path=require('path');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:2});
await p.goto('file://'+path.resolve('infographics/infographics.html'));await p.evaluate(()=>document.fonts.ready);
const names={ig1:'read-a-python-error',ig2:'variables-labelled-boxes',ig3:'for-vs-while'};
for(const [id,n] of Object.entries(names)){const el=await p.$('#'+id);await el.screenshot({path:`infographics/${n}.png`});
 const over=await p.evaluate(id=>{const s=document.getElementById(id);return [...s.querySelectorAll('*')].filter(e=>{const r=e.getBoundingClientRect(),q=s.getBoundingClientRect();return r.bottom>q.bottom-40||r.right>q.right+1||e.scrollWidth>e.clientWidth+1&&getComputedStyle(e).whiteSpace!=='pre'}).map(e=>e.className||e.tagName).slice(0,5)},id);console.log(n,'overflow:',JSON.stringify(over))}
await b.close()})();
