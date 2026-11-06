// Deterministic "screen recording": steps a page's render clock frame by frame and pipes JPEG screenshots to ffmpeg.
// node src/capture.js job.json   job = {page, kind: "editor"|"deck", tl?, slides?, dur, fps, out}
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');const {spawn}=require('child_process');
(async()=>{const job=JSON.parse(fs.readFileSync(process.argv[2]));const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1920,height:1080}});await p.goto('file://'+path.resolve(job.page)+'#export');await p.evaluate(()=>document.fonts.ready);
if(job.kind==='editor')await p.evaluate(tl=>{window.TL=tl},job.tl);
const tmp=job.out.replace(/\.mp4$/,'.tmp.mp4');
const ff=spawn('ffmpeg',['-loglevel','error','-y','-f','image2pipe','-c:v','mjpeg','-framerate',String(job.fps),'-i','-','-vf','fps=30,format=yuv420p','-c:v','libx264','-crf','18','-preset','veryfast','-pix_fmt','yuv420p',tmp]);
const n=Math.round(job.dur*job.fps);
for(let i=0;i<n;i++){const t=i/job.fps;
  if(job.kind==='editor')await p.evaluate(t=>render(t),t);
  else{let s=job.slides[0];for(const x of job.slides)if(x.start<=t)s=x;await p.evaluate(([i,tt,ta])=>show(i,tt,ta),[s.i,t-s.start,s.timer_at??2])}
  const buf=await p.screenshot({type:'jpeg',quality:92});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r))}
ff.stdin.end();await new Promise(r=>ff.on('close',r));fs.renameSync(tmp,job.out);await b.close();console.log('captured',job.out,n,'frames')})();
