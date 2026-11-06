const {chromium}=require('playwright');const path=require('path');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:2600,height:1500}});
await p.goto('file://'+path.resolve('channel/art.html'));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
const out={logo:'channel/logo.png',watermark:'channel/watermark.png',banner:'channel/banner.png',endscreen:'build/endscreen.png','cover-52':'thumbnails/cover-52.png','cover-bottom-up':'thumbnails/cover-bottom-up.png'};
for(const [id,f] of Object.entries(out)){await (await p.$('#'+id)).screenshot({path:f,omitBackground:id==='watermark'})}
await b.close()})();
