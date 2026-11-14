const {chromium}=require('/opt/node-tools/node_modules/playwright');
const fs=require('fs');
const [,,OUT,MODE,TUNEJ]=process.argv;
(async()=>{
 const b=await chromium.launch(); const pg=await b.newPage({viewport:{width:1600,height:900}});
 pg.on('pageerror',e=>console.log('ERR',e.message));
 await pg.goto('file:///home/user/Art_garden/index.html?skip=1&page=garden&vt=1&cam=0');
 await pg.waitForTimeout(800);
 if(TUNEJ) await pg.evaluate(o=>Object.assign(TUNE,JSON.parse(o)),TUNEJ);
 const out=await pg.evaluate((MODE)=>{
   const dt=.05,res=[]; let t=0,v=0,vp=null;
   while(t<1200){ t+=dt; G.camT=0; G.tour=-9999;
     if(MODE==='visitor'){ v-=dt; if(v<=0){ v=5;
         const fav=G.plants.filter(p=>p.state!=='dying'&&(p.si===5||p.si===0));
         const pool=(fav.length&&Math.random()<.75)?fav:G.plants;
         if(pool.length){const p=pool[Math.floor(Math.random()*pool.length)]; vp=[p.fx*cG._w, gy(ROWS[p.row].wy-p.h*p.rs*.6)];} }
       if(vp) gazeInput(vp[0],vp[1]); }
     updateGaze(dt); let d=updateBloom(dt)+updateGarden(dt); d=Math.min(d,20*dt); S.att=clamp(S.att+dt*5.2-d,0,100);
     if(Math.abs(t/10-Math.round(t/10))<dt/20){
       const sp=new Array(14).fill(0), dorm=new Array(14).fill(0), tr=new Array(14).fill(0);
       G.plants.forEach(p=>{ if(p.state==='dormant')dorm[p.si]++; else sp[p.si]++; });
       Object.keys(G.trends).forEach(k=>{ if(G.trends[k].on)tr[+k]=1; });
       res.push({t:Math.round(t),sp,dorm,tr,plants:G.plants.length,debris:S.debris});
     } }
   return res;},MODE);
 fs.writeFileSync(OUT,JSON.stringify(out)); const l=out[out.length-1];
 console.log(OUT.split('/').pop(),'plants',l.plants,'species alive',l.sp.filter(x=>x).length,'trends',l.tr.reduce((a,b)=>a+b,0));
 await b.close();})();
