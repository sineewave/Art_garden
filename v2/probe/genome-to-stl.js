/* 基因组 → 三维实体网格 → 二进制 STL
   纯数学，零依赖，不需要 GPU。证明 3D 打印那条路不必经 Blender / Unity。 */
const fs = require('fs');

const TAU = Math.PI * 2;
function rng(seed){ let s=seed>>>0; return ()=> (s=(s*1664525+1013904223)>>>0)/4294967296; }

/* 与 2D 版本完全相同的基因组 —— 这是架构的关键：一套基因，两个渲染器 */
function genome(seed){
  const r = rng(seed), pick=(a,b)=>a+r()*(b-a);
  return { sym:Math.round(pick(3,13)), whorls:Math.round(pick(1,4)),
    open:pick(0.30,1.0), len:pick(0.55,1.15), wid:pick(0.08,0.40),
    curl:pick(-0.5,0.75), serr:Math.round(pick(0,9)), tipN:pick(0.5,3.2),
    hue:pick(0,360), sat:pick(0.18,0.95), val:pick(0.45,1.0),
    spread:pick(0,70), twist:pick(0,1), disc:pick(0.05,0.3),
    weave:Math.round(pick(0,7)), pix:Math.round(pick(0,5)) };
}

const tris = [];
const push = (a,b,c) => tris.push(a,b,c);

/* 把一串横截面环缝成封闭管体（水密 = 可打印） */
function loft(rings){
  const K = rings[0].length;
  for (let i=0;i<rings.length-1;i++)
    for (let k=0;k<K;k++){
      const k2=(k+1)%K, A=rings[i][k],B=rings[i][k2],C=rings[i+1][k2],D=rings[i+1][k];
      push(A,B,C); push(A,C,D);
    }
  // 两端封盖
  for (const [ring,flip] of [[rings[0],true],[rings[rings.length-1],false]]){
    const c = ring.reduce((a,p)=>[a[0]+p[0]/ring.length,a[1]+p[1]/ring.length,a[2]+p[2]/ring.length],[0,0,0]);
    for (let k=0;k<ring.length;k++){
      const k2=(k+1)%ring.length;
      flip ? push(c,ring[k2],ring[k]) : push(c,ring[k],ring[k2]);
    }
  }
}

/* 一枚花瓣：沿瓣长扫掠一个扁椭圆截面 */
function petal(G, phi, tilt, R, S, thick){
  const STEPS=18, K=8, rings=[];
  for (let i=0;i<=STEPS;i++){
    const u = 0.03 + (0.97)*i/STEPS;
    const w = Math.max(0.012, G.wid*Math.pow(Math.sin(Math.PI*Math.pow(u,0.75)),G.tipN)
            * (1+0.14*Math.sin(G.serr*Math.PI*u))) * S;
    const th = thick*(1-0.45*u);                  // 尖端更薄
    const x0 = R + u*G.len*S, z0 = G.curl*G.len*S*u*u;
    const ring=[];
    for (let k=0;k<K;k++){
      const a=TAU*k/K, ly=Math.cos(a)*w, lz=Math.sin(a)*th;
      const x1=x0*Math.cos(tilt)-lz*Math.sin(tilt);
      const z1=x0*Math.sin(tilt)+lz*Math.cos(tilt)+z0;
      ring.push([x1*Math.cos(phi)-ly*Math.sin(phi), x1*Math.sin(phi)+ly*Math.cos(phi), z1]);
    }
    rings.push(ring);
  }
  loft(rings);
}

function sphere(cx,cy,cz,r,seg=14){
  const rings=[];
  for(let i=0;i<=seg;i++){
    const t=Math.PI*i/seg, ring=[];
    for(let k=0;k<seg;k++){
      const a=TAU*k/seg;
      ring.push([cx+r*Math.sin(t)*Math.cos(a), cy+r*Math.sin(t)*Math.sin(a), cz+r*Math.cos(t)*0.6]);
    }
    rings.push(ring);
  }
  loft(rings);
}

function stem(G,h,r){
  const rings=[];
  for(let i=0;i<=10;i++){
    const t=i/10, ring=[];
    for(let k=0;k<10;k++){
      const a=TAU*k/10;
      ring.push([G.curl*0.12*(1-t)+r*Math.cos(a), r*Math.sin(a), -h*t]);
    }
    rings.push(ring);
  }
  loft(rings);
}

function build(G, thick){
  tris.length = 0;
  for (let w=0; w<G.whorls; w++){
    const t = G.whorls>1 ? w/(G.whorls-1) : 0;
    const open = G.open*(0.45+0.55*t);
    const tilt = (1-open)*Math.PI*0.36;
    const S = 1-0.3*(1-t), R = G.disc*(0.6+0.4*t);
    const n = Math.max(3, G.sym-w);
    for (let k=0;k<n;k++) petal(G, TAU*k/n + G.twist*w*2.399, tilt, R, S, thick);
  }
  sphere(0,0,0, G.disc*1.15);
  stem(G, 1.5, 0.035+G.whorls*0.012);
}

/* 二进制 STL */
function writeSTL(path){
  const n = tris.length/3;
  const buf = Buffer.alloc(84 + n*50);
  buf.write('attention-garden genome mesh'.padEnd(80,' '), 0, 80, 'ascii');
  buf.writeUInt32LE(n, 80);
  let o = 84;
  for (let i=0;i<tris.length;i+=3){
    const [a,b,c]=[tris[i],tris[i+1],tris[i+2]];
    const u=[b[0]-a[0],b[1]-a[1],b[2]-a[2]], v=[c[0]-a[0],c[1]-a[1],c[2]-a[2]];
    let nx=u[1]*v[2]-u[2]*v[1], ny=u[2]*v[0]-u[0]*v[2], nz=u[0]*v[1]-u[1]*v[0];
    const L=Math.hypot(nx,ny,nz)||1; nx/=L; ny/=L; nz/=L;
    for (const f of [nx,ny,nz, ...a, ...b, ...c]){ buf.writeFloatLE(f,o); o+=4; }
    buf.writeUInt16LE(0,o); o+=2;
  }
  fs.writeFileSync(path, buf);
  return buf.length;
}

function stats(){
  let V=0, mn=[9,9,9], mx=[-9,-9,-9];
  for (let i=0;i<tris.length;i+=3){
    const [a,b,c]=[tris[i],tris[i+1],tris[i+2]];
    V += (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0]))/6;
    for (const p of [a,b,c]) for (let d=0;d<3;d++){ mn[d]=Math.min(mn[d],p[d]); mx[d]=Math.max(mx[d],p[d]); }
  }
  return { V:Math.abs(V), size:mx.map((v,i)=>v-mn[i]) };
}

/* ---- 跑三个样本 ---- */
const OUT = __dirname;
console.log('基因组 → 三维实体 → STL\n' + '='.repeat(62));
for (const seed of [41, 263, 301]) {
  const G = genome(seed);
  // 目标实物高 120mm；壁厚按 FDM 最小 0.9mm 反推到基因单位
  const TARGET_MM = 120;
  build(G, 0.03);
  const s0 = stats();
  const scale = TARGET_MM / (s0.size[2] || 1);
  const wallMM = 0.03 * 2 * scale;
  console.log(
    `\n#${seed}  瓣${G.sym} 层${G.whorls} 开${G.open.toFixed(2)}`,
    `\n   三角面      ${(tris.length/3).toLocaleString()}`,
    `\n   包围盒      ${s0.size.map(v=>(v*scale).toFixed(0)).join(' × ')} mm`,
    `\n   体积        ${(s0.V*scale**3/1000).toFixed(1)} cm³  (PLA 约 ${(s0.V*scale**3/1000*1.24).toFixed(0)} g)`,
    `\n   最薄壁      ${wallMM.toFixed(2)} mm  ${wallMM>=0.9?'✓ FDM 可打':'✗ 需加厚或改树脂'}`
  );
  const bytes = writeSTL(`${OUT}/flower_${seed}.stl`);
  console.log(`   STL         ${(bytes/1024).toFixed(0)} KB  → flower_${seed}.stl`);
}
console.log('\n' + '='.repeat(62));
