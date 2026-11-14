import sys,math,random,json
sys.path.insert(0,sys.argv[1]); from common import *
OUT=sys.argv[2]; PROC=sys.argv[3]
BG='#05070B'; W_='#EEF3FA'; MU='#8A95A5'; DIMC='#2A3240'
CYN='#5EC8FF'; BLU='#4C7DFF'; TEAL='#3FE0C0'; VIO='#9B7BFF'; GRY='#8A93A0'; GOLD='#FFD27A'; ROSE='#D98CA8'; MINT='#5EE0B5'
def new():
    g=SVG(bg=BG)
    g.a('<defs><filter id="gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<filter id="gl2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter></defs>')
    return g
def T(g,x,y,t,size=14,c=W_,**k): g.text(x,y,t,size,c,fam=k.pop('fam','Inter'),**k)
def M(g,x,y,t,size=12,c=MU,**k): g.text(x,y,t,size,c,fam='JetBrains Mono',**k)
def header(g,title,sub,n):
    T(g,80,92,title,46,W_,fam='Inter Display',weight=700,ls=-1); T(g,82,124,sub,17,MU)
    T(g,1840,92,f'ATTENTION GARDEN · {n}',12,MU,anchor='end',ls=3)
def rosette(g,cx,cy,r,n,c,w=1.8,sq=1,op=1,inner=True):
    g.a(f'<g transform="translate({cx:.1f},{cy:.1f}) scale(1,{sq})" filter="url(#gl)" opacity="{op}">')
    for k in range(n):
        an=360*k/n; g.a(f'<ellipse cx="{r*.55:.1f}" cy="0" rx="{r*.47:.1f}" ry="{r*.2:.1f}" transform="rotate({an:.1f})" fill="none" stroke="{c}" stroke-width="{w}"/>')
        if inner: g.a(f'<ellipse cx="{r*.3:.1f}" cy="0" rx="{r*.2:.1f}" ry="{r*.08:.1f}" transform="rotate({an+180/n:.1f})" fill="none" stroke="{W_}" stroke-width="{w*.55}" opacity=".7"/>')
    g.a(f'<circle r="{r*.17:.1f}" fill="{c}"/></g>')

# ================= 08 · ANATOMY =================
g=new()
header(g,'Anatomy of a flower','One grammar, fourteen parameter sets, and a little chance for every plant','08')
CX=900; c=PALS[9]
parts=[('IMAGE DISC',270),('INNER PETALS',340),('OUTER PETALS',420),('BRANCHES',520),('LEAVES',620),('STEM',720),('ROOT',860)]
g.line(CX,230,CX,930,DIMC,1.2,dash='3 6')
# image disc
g.a(f'<g transform="translate({CX},270) scale(1,.38)" filter="url(#gl)"><circle r="44" fill="none" stroke="{c}" stroke-width="2"/></g>')
g.rect(CX-24,270-24,48,48,fill=PALS[1]); g.rect(CX-24,246,48,48,W_,sw=1.2)
# inner / outer petals (perspective)
rosette(g,CX,340,70,6,c,sq=.36,inner=False)
rosette(g,CX,420,120,10,c,sq=.36,inner=False)
# branches
for s_ in (-1,1):
    g.a('<g filter="url(#gl)">'); g.path(f'M{CX},{540} Q{CX+s_*60},{520} {CX+s_*120},{490}',MINT,2); g.a('</g>')
    g.rect(CX+s_*120-14,476,28,28,fill=PALS[6] if s_<0 else PALS[4]); g.rect(CX+s_*120-14,476,28,28,W_,sw=1)
# leaves
for s_ in (-1,1): g.a('<g filter="url(#gl)">'); g.ell(CX+s_*56,612,52,14,-20*s_,MINT,2); g.line(CX,620,CX+s_*100,600,MINT,.8,op=.6); g.a('</g>')
# stem
g.a('<g filter="url(#gl)">'); g.path(f'M{CX},{820} Q{CX+18},{740} {CX},{660}',MINT,3); g.a('</g>')
# root to port
g.a('<g filter="url(#gl)">'); g.path(f'M{CX},{840} Q{CX-30},{880} {CX-10},{910}',VIO,2); g.a('</g>'); g.circ(CX-10,916,8,VIO,2,fill=BG)
# left labels / right params
L=[('IMAGE DISC',270,'one real generated image per plant'),
   ('INNER RING',340,'colour · palette of the species'),
   ('OUTER RING',420,'petals 2–10 by species'),
   ('BRANCHES',492,'from the bud stage · 2–4 more images'),
   ('LEAVES',612,'two pairs, along the stem'),
   ('STEM',740,'height × species × plant'),
   ('ROOT',900,'ends at a capture port, screen 3')]
for n,y,d in L:
    g.line(CX-170,y,CX-140,y,DIMC,1); T(g,CX-180,y+5,n,15,W_,anchor='end',weight=700,ls=1.4); T(g,CX-180,y+25,d,12,MU,anchor='end')
R=[(340,'hue ± 16° · lightness ± 5 %','per plant'),(420,'petals ± 2 · head × 0.84–1.20','per plant'),(420+28,'head × 0.72–1.34','from platform likes'),
   (740,'species × 0.88–1.16 · plant × 0.82–1.24','height'),(740+28,'species × 0.88–1.10','growth rate')]
T(g,CX+180,250,'WHAT VARIES',12,MU,weight=700,ls=2)
for y,d,who in R:
    g.line(CX+140,y,CX+170,y,DIMC,1); T(g,CX+180,y+5,d,14,GOLD if 'likes' in who else W_,weight=600); T(g,CX+180+len(d)*7.6+12,y+5,who,12,MU)
T(g,CX+180,860,'SPECIES',12,MU,weight=700,ls=2)
T(g,CX+180,884,'sets form, palette, petals, height and growth',14,W_)
T(g,CX+180,904,'PLANT',12,MU,weight=700,ls=2)
T(g,CX+180,928,'adds small random differences, and its image',14,W_)
# bottom strip: 14 forms
forms=['blade','bell','spike','umbel','tulip','wing','fringe','dot','stack','star','layer','tube','pod','grid']
for k,(zh,en,pal,pet) in enumerate(SPECIES):
    x=110+k*128; y=1010
    rosette(g,x,y-22,20,max(pet,3),PALS[pal],w=1.4,inner=False)
    T(g,x,y+12,en,11,W_,anchor='middle',weight=600); M(g,x,y+28,forms[k],10,MU,anchor='middle')
g.save(OUT+'/F8_anatomy.svg')

# ================= 09 · STREAMS =================
g=new()
header(g,'Which species win','Plants of each species over 20 simulated minutes. Width = number of living plants','09')
def stream(file,y0,h,label,note):
    s=json.load(open(f'{PROC}/{file}')); s=[{'t':0,'sp':[0]*14,'dorm':[0]*14,'tr':[0]*14}]+s
    X0,XW=260,1500; sc=h/30
    T(g,80,y0+h/2-6,label,22,W_,fam='Inter Display',weight=700); T(g,80,y0+h/2+18,note,13,MU)
    n=len(s); xs=[X0+XW*r['t']/1200 for r in s]
    tot=[sum(r['sp'])+sum(r['dorm']) for r in s]
    base=[y0+h/2-t*sc/2 for t in tot]
    cur=base[:]
    order=list(range(14))
    for si in order+['d']:
        vals=[(sum(r['dorm']) if si=='d' else r['sp'][si])*sc for r in s]
        if max(vals)==0: continue
        top=cur; bot=[cur[i]+vals[i] for i in range(n)]
        c=GRY if si=='d' else PALS[SPECIES[si][2]]
        d='M'+' L'.join(f'{xs[i]:.1f},{top[i]:.1f}' for i in range(n))+' L'+' L'.join(f'{xs[i]:.1f},{bot[i]:.1f}' for i in reversed(range(n)))+' Z'
        g.a(f'<path d="{d}" fill="{c}" opacity="{.35 if si=="d" else .78}" stroke="{BG}" stroke-width=".6"/>')
        # label at widest point
        cand=[i for i in range(n) if xs[i]>X0+XW*.55]
        wi=max(cand,key=lambda i:vals[i]) if cand and max(vals[i] for i in cand)>0 else max(range(n),key=lambda i:vals[i])
        if vals[wi]>=1.6*sc and si!='d':
            T(g,xs[wi],(top[wi]+bot[wi])/2+5,SPECIES[si][1],13,BG,anchor='middle',weight=800,ls=1)
        if si=='d' and vals[wi]>=2*sc: T(g,xs[wi],(top[wi]+bot[wi])/2+4,'dormant',11,'#05070B',anchor='middle',weight=700)
        cur=bot
    last=s[-1]
    M(g,X0+XW+16,y0+h/2-6,f'{sum(last["sp"])+sum(last["dorm"])} plants',12,W_)
    M(g,X0+XW+16,y0+h/2+12,f'{sum(1 for v in last["sp"] if v)} species',12,MU)
    M(g,X0+XW+16,y0+h/2+30,f'{sum(last["tr"])} trends',12,MU)
stream('sp_auto.json',180,330,'No visitor','the algorithm looks')
stream('sp_vis.json',560,330,'One visitor','who prefers two species')
for m in (0,5,10,15,20):
    x=260+1500*m/20; g.line(x,930,x,940,MU,1); M(g,x,960,f'{m} min',11,MU,anchor='middle')
M(g,80,1010,'Simulation with the piece’s own update code, one run per case. Built-in patterns stand in for the corpus.',11,MU)
g.save(OUT+'/F9_streams.svg')

# ================= 10 · AGENCY =================
g=new()
header(g,'Agency is a setting','Who holds which dial — and what the garden becomes when the dials move','10')
CX,CY_,R=560,560,280
g.circ(CX,CY_,90,TEAL,2,fill=BG); g.a(f'<circle cx="{CX}" cy="{CY_}" r="90" fill="{TEAL}" opacity=".12" filter="url(#gl2)"/>')
rosette(g,CX,CY_-10,40,10,TEAL,w=1.6); T(g,CX,CY_+58,'THE GARDEN',13,TEAL,anchor='middle',weight=700,ls=2)
actors=[('VISITOR',GOLD,['gaze strength 36','feed strength 26']),
        ('RANKING',CYN,['algorithmic gaze ×0.12','baseline exposure 0.24','takes over after 60 s']),
        ('DATASET',MINT,['734 real images','likes → body size','video share']),
        ('MODEL',BLU,['what the images look like','→ which species they join']),
        ('POWER',VIO,['the cost of every image','Wh · CO₂ · water']),
        ('ARTIST',ROSE,['decay 0.34 · growth ×1','26 plants · 4 per species','240 s dormant → debris'])]
for k,(n,c,ps) in enumerate(actors):
    an=-math.pi/2+2*math.pi*k/len(actors); x=CX+math.cos(an)*R; y=CY_+math.sin(an)*R
    g.line(CX+math.cos(an)*95,CY_+math.sin(an)*95,x-math.cos(an)*36,y-math.sin(an)*36,c,1.6,op=.8)
    g.circ(x,y,32,c,2,fill=BG); g.a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="32" fill="{c}" opacity=".15" filter="url(#gl2)"/>')
    T(g,x,y+5,n[0],18,c,anchor='middle',weight=800)
    side=1 if math.cos(an)>=0 else -1; tx=x+side*48; anc='start' if side>0 else 'end'
    if abs(math.cos(an))<.2: tx=x+52; anc='start'
    T(g,tx,y-8,n,15,c,anchor=anc,weight=700,ls=1.4)
    for j,p in enumerate(ps): T(g,tx,y+12+j*17,p,12,MU,anchor=anc)
# presets
def mini(file,x,y,c,title,sub):
    s=json.load(open(f'{PROC}/{file}')); s=[{'t':0,'sp':[0]*14,'dorm':[0]*14,'tr':[0]*14}]+s
    w,h=560,120
    g.rect(x,y,w+40,h+90,c,sw=1.4,rx=16,fill='#080B11')
    T(g,x+20,y+30,title,15,c,weight=700,ls=1.4); T(g,x+20,y+50,sub,12,MU)
    pa=[(x+20+w*r['t']/1200, y+60+h-h*sum(r['sp'])/26) for r in s]
    pd=[(x+20+w*r['t']/1200, y+60+h-h*(sum(r['sp'])+sum(r['dorm']))/26) for r in s]
    g.a(f'<path d="M{x+20},{y+60+h} L'+' L'.join(f'{a:.1f},{b:.1f}' for a,b in pa)+f' L{x+20+w},{y+60+h} Z" fill="{c}" opacity=".35"/>')
    g.a(f'<path d="M'+' L'.join(f'{a:.1f},{b:.1f}' for a,b in pa)+f'" fill="none" stroke="{c}" stroke-width="2" filter="url(#gl)"/>')
    l=s[-1]; T(g,x+w+20,y+30,f'{sum(l["sp"])+sum(l["dorm"])}',30,c,anchor='end',fam='Inter Display',weight=700); T(g,x+w+20,y+50,f'plants · {sum(1 for v in l["sp"] if v)} species · {sum(l["tr"])} trends',12,MU,anchor='end')
px=1180
T(g,px,190,'THE SAME GARDEN, THREE SETTINGS · 20 min, nobody watching',12,MU,weight=700,ls=1.6)
mini('sp_harsh.json',px,215,ROSE,'HARSH','decay 0.8 · no baseline · no algorithm')
mini('sp_auto.json',px,450,TEAL,'AS SHOWN','decay 0.34 · baseline 0.24 · algorithm ×0.12')
mini('sp_gentle.json',px,685,GOLD,'GENTLE','decay 0.15 · baseline 0.5 · algorithm ×0.3')
T(g,80,1010,'Nobody holds agency alone; the dials are set by someone.',15,W_,weight=600)
g.save(OUT+'/F10_agency.svg')

# ================= 11 · SITE PLAN =================
g=new()
header(g,'Sydney, the setup','One screen, one laptop, one camera — proposed layout, plan view','11')
# room plan
ox,oy=260,240
g.rect(ox,oy,900,640,DIMC,sw=1.4,rx=6)
for x in range(ox+40,ox+900,40):
    for y in range(oy+40,oy+640,40): g.circ(x,y,1.2,DIMC,0,fill=DIMC)
# wall + screen
g.line(ox,oy,ox+900,oy,W_,3)
g.rect(ox+250,oy+4,400,22,TEAL,sw=2,fill='#0E2A27'); T(g,ox+450,oy-14,'DISPLAY · garden + roots',14,TEAL,anchor='middle',weight=700,ls=1.4)
# camera + FOV
camx,camy=ox+450,oy+26
g.circ(camx,camy+6,7,GOLD,0,fill=GOLD)
fov=math.radians(39); L_=520
p1=(camx-math.sin(fov)*L_,camy+math.cos(fov)*L_); p2=(camx+math.sin(fov)*L_,camy+math.cos(fov)*L_)
g.a(f'<path d="M{camx},{camy} L{p1[0]:.1f},{p1[1]:.1f} A{L_},{L_} 0 0 0 {p2[0]:.1f},{p2[1]:.1f} Z" fill="{GOLD}" opacity=".08"/>')
g.path(f'M{p1[0]:.1f},{p1[1]:.1f} L{camx},{camy} L{p2[0]:.1f},{p2[1]:.1f}',GOLD,1.2,dash='5 5')
# interaction zone 1–2.5 m (1 m = 120 px)
for r_,lab in ((120,'1 m'),(300,'2.5 m')):
    a0,a1=-math.pi/2-fov,-math.pi/2+fov
    g.a(f'<path d="M{camx+math.cos(math.pi/2-fov)*r_:.1f},{camy+math.sin(math.pi/2-fov)*r_:.1f} A{r_},{r_} 0 0 1 {camx+math.cos(math.pi/2+fov)*r_:.1f},{camy+math.sin(math.pi/2+fov)*r_:.1f}" fill="none" stroke="{GOLD}" stroke-width="1.4" opacity=".7"/>')
    M(g,camx+r_*.66+8,camy+r_*.78,lab,11,GOLD)
T(g,camx,camy+230,'interaction zone',15,GOLD,anchor='middle',weight=700)
# visitors
for (vx,vy,hand) in ((camx-60,camy+200,True),(camx+70,camy+240,False),(camx-180,camy+420,False)):
    g.circ(vx,vy,14,W_,1.6,fill=BG); g.circ(vx,vy,4,W_,0,fill=W_)
    if hand: g.line(vx,vy,vx+20,vy-30,GOLD,2); g.circ(vx+20,vy-30,5,GOLD,0,fill=GOLD)
# table + laptop
g.rect(ox+700,oy+330,170,90,W_,sw=1.4,rx=6,fill='#0B0F15'); g.rect(ox+730,oy+350,110,50,CYN,sw=1.6,rx=4)
T(g,ox+785,oy+440,'LAPTOP · feed',13,CYN,anchor='middle',weight=700,ls=1.2)
# poster board
g.rect(ox+30,oy+120,26,280,ROSE,sw=1.6,fill='#1A0F14'); T(g,ox+70,oy+150,'POSTER',13,ROSE,weight=700,ls=1.2); T(g,ox+70,oy+170,'+ camera notice',12,MU)
# cables
g.path(f'M{ox+785},{oy+330} L{ox+785},{oy+60} L{ox+650},{oy+60}',DIMC,1.6,dash='4 4'); g.path(f'M{ox+760},{oy+330} L{ox+760},{oy+80} L{camx+10},{oy+80} L{camx+10},{camy+12}',DIMC,1.6,dash='4 4')
# right: what runs where
px=1240
T(g,px,250,'ON THE LAPTOP',12,MU,weight=700,ls=2)
rows=[(CYN,'Feed','on the laptop’s own screen'),(TEAL,'Garden + roots','on the display'),(GOLD,'Hand tracking','local, in the browser'),(ROSE,'Silhouette','abstract, never stored'),(VIO,'Behaviour log','JSON on disk · no images')]
for k,(c,n,d) in enumerate(rows):
    y=290+k*78; g.circ(px+12,y,10,c,2,fill=BG); g.circ(px+12,y,3.5,c,0,fill=c)
    T(g,px+36,y+2,n,17,c,weight=700); T(g,px+36,y+24,d,13,MU)
T(g,px,720,'Offline. A second laptop holds',14,W_); T(g,px,740,'an identical backup.',14,W_)
M(g,80,1010,'Proposed layout; distances approximate (1 m ≈ 120 px). Gesture input and logging are being built for Sydney.',11,MU)
g.save(OUT+'/F11_site.svg')
