// Exports the deck: one PNG per slide (final state), a 10-page PDF, and frames for animated slide video if asked.
// node src/export_deck.js            -> slides/png/slide-01..10.png, slides/deck.pdf, build/deck-sheet (contact sheet)
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
const url='file://'+path.resolve('slides/deck.html')+'#export';await p.goto(url);await p.evaluate(()=>document.fonts.ready);
fs.mkdirSync('slides/png',{recursive:true});const n=await p.evaluate(()=>document.querySelectorAll('.slide').length);
for(let i=0;i<n;i++){await p.evaluate(([i])=>show(i,8),[i]);await p.screenshot({path:`slides/png/slide-${String(i+1).padStart(2,'0')}.png`});}
// PDF: every slide shown, animations at their end state
await p.evaluate(()=>{document.querySelectorAll('.slide').forEach(s=>{s.classList.add('on');s.getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=99999})});
  document.getElementById('count').textContent='10'});
await p.pdf({path:'slides/deck.pdf',width:'1920px',height:'1080px',printBackground:true,margin:{top:0,bottom:0,left:0,right:0}});
await b.close();console.log('exported',n)})();
