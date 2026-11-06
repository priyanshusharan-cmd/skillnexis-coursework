const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1680,height:1188}});
for(const f of process.argv.slice(2)){await p.goto('file://'+require('path').resolve(f));await p.screenshot({path:f.replace('.svg','.png').replace('drawings/','build/')})}await b.close()})();
