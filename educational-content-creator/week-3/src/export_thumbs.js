const {chromium}=require('playwright');const path=require('path');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});
await p.goto('file://'+path.resolve('thumbnails/thumbs.html'));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
for(const id of ['yt-if-else','yt-variables','yt-errors','cover-equals','cover-elif','cover-indent']){await (await p.$('#'+id)).screenshot({path:`thumbnails/${id}.png`})}
await b.close()})();
