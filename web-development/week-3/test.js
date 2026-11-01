// Run with: node test.js   (needs internet access for the live Open-Meteo call; Node 18+)
const { getWeather } = require('./weather');
(async () => {
  const w = await getWeather('Bengaluru');
  console.log('live lookup:', w);
  if (!(typeof w.temperature === 'number' && w.humidity >= 0 && w.humidity <= 100 && w.condition)) throw new Error('unexpected shape');
  for (const bad of ['', 'zzzzqqqxxnotacity']) {
    try { await getWeather(bad); throw new Error('should have failed for "' + bad + '"'); }
    catch (e) { console.log('rejected', JSON.stringify(bad), '->', e.message); }
  }
  console.log('ok');
})().catch(e => { console.error('FAILED', e.message); process.exit(1); });
