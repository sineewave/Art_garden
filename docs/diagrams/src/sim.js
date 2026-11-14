const {chromium}=require('/opt/node-tools/node_modules/playwright');
const fs=require('fs');
const [,,OUT,MODE]=process.argv;   // MODE: auto | visitor
(async()=>{
 const b=await chromium.launch(); const pg=await b.newPage({viewport:{width:1600,height:900}});
 pg.on('pageerror',e=>console.log('ERR',e.message));
 await pg.goto('file:///home/user/Art_garden/index.html?skip=1&page=garden&vt=1&cam=0');
 await pg.waitForTimeout(800);
 const shots=[0.5,2,5,10,20];   // minutes
 const series=[]; let si=0;
 for(const m of shots){
  const r=await pg.evaluate(({m,MODE})=>{
   const dt=.05; const out=[];
   window.__t=window.__t||0; window.__v=window.__v||0;
   while(window.__t<m*60){
     window.__t+=dt;
     G.camT=0; G.tour=-9999;
     if(MODE==='visitor'){
       window.__v-=dt;
       if(window.__v<=0){ window.__v=5;
         // 一位有偏好的观众：偏爱物种 5（蝶尾菊）与 0（十字菀），其次随便看看
         const fav=G.plants.filter(p=>p.state!=='dying'&&(p.si===5||p.si===0));
         const pool=(fav.length&&Math.random()<.75)?fav:G.plants;
         if(pool.length){ const p=pool[Math.floor(Math.random()*pool.length)];
           window.__vp=[p.fx*cG._w, gy(ROWS[p.row].wy-p.h*p.rs*.6)]; } }
       if(window.__vp) gazeInput(window.__vp[0],window.__vp[1]);
     }
     updateGaze(dt);
     let drain=updateBloom(dt)+updateGarden(dt);
     drain=Math.min(drain,20*dt); S.att=clamp(S.att+dt*5.2-drain,0,100);
     if(Math.abs(window.__t/10-Math.round(window.__t/10))<dt/20){
       const st=[0,0,0,0,0,0,0,0,0]; let dorm=0, att=0, sp=new Set();
       G.plants.forEach(p=>{ if(p.state==='dormant')dorm++; else st[p.stage]++; att+=p.att; sp.add(p.si); });
       out.push({t:Math.round(window.__t), plants:G.plants.length, st, dorm, trends:trendCount(),
         att:Math.round(att), meter:Math.round(S.att), debris:S.debris, migrated:S.migrated,
         feed:B.items.length, species:sp.size, flies:G.flies.length});
     }
   }
   renderGarden();
   return out;
  },{m,MODE});
  series.push(...r);
  const cv=await pg.$('#cGarden'); await cv.screenshot({path:`${OUT}_${String(m).replace('.','_')}m.png`});
 }
 fs.writeFileSync(`${OUT}.json`,JSON.stringify(series));
 console.log(MODE, series.length, JSON.stringify(series[series.length-1]));
 await b.close();
})();
