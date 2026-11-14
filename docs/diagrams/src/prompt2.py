import sys,math,random,colorsys
sys.path.insert(0,sys.argv[1]); from common import *
OUT=sys.argv[2]; MIN=len(sys.argv)>3 and sys.argv[3]=='min'; SUF='_min' if MIN else ''
BG='#05070B'; W_='#EEF3FA'; MU='#8A95A5'; DIMC='#2A3240'
CYN='#5EC8FF'; TEAL='#3FE0C0'; VIO='#9B7BFF'; GOLD='#FFD27A'; ROSE='#D98CA8'; GRY='#8A93A0'
def new():
    g=SVG(bg=BG)
    g.a('<defs><filter id="gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<filter id="gl2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter></defs>')
    g.a(f'<defs><marker id="mg" markerWidth="10" markerHeight="10" refX="7" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{GOLD}"/></marker></defs>')
    return g
def hsl(h,s,l):
    r,g_,b=colorsys.hls_to_rgb((h%360)/360,l,s); return '#%02x%02x%02x'%(int(r*255),int(g_*255),int(b*255))

# ============ A · prompt reuse (simple) ============
g=new(); random.seed(4)
def T(x,y,t,size=14,c=W_,**k): g.text(x,y,t,size,c,fam=k.pop('fam','Inter'),**k)
if not MIN:
    T(80,92,'Prompt reuse',46,W_,fam='Inter Display',weight=700,ls=-1)
    T(82,128,'A feed copies the item. Generation copies the recipe.',22,GOLD,weight=600)
else: g.a('<g transform="translate(30,-20) scale(1.0)">')
prompts=[[('a',0),('cat',0),('dancing',0),('on',0),('a',0),('rooftop,',0),('neon',0),('lights,',0),('cinematic',0)],
         [('a',0),('cat',0),('dancing',0),('on',0),('a',0),('rooftop,',0),('neon',0),('lights,',0),('cinematic,',0),('pixar',1),('style',1)],
         [('a',0),('cat',0),('dancing',0),('in',1),('the',1),('rain,',1),('neon',0),('lights,',0),('pixar',0),('style,',0),('8k',1)]]
X0=110; CW=580; target=330; PY=270; IY=470; TS=112
for r,pr in enumerate(prompts):
    x=X0+r*CW
    T(x,PY-20,f'ROUND {r+1}',14,MU,weight=700,ls=2)
    g.rect(x,PY,500,112,'#5A6576',sw=1.4,rx=18,fill='#0A0E15')
    xx=x+24; li=0
    for word,ch in pr:
        w=len(word)*12.0
        if xx+w>x+480: xx=x+24; li+=1
        yy=PY+42+li*36
        if ch: g.a(f'<rect x="{xx-5}" y="{yy-24}" width="{w+10}" height="32" rx="7" fill="{GOLD}" opacity=".22"/>')
        g.text(xx,yy,word,20,GOLD if ch else W_,fam='JetBrains Mono',weight=600 if ch else 400)
        xx+=w+12
    mix=[0,.6,.9][r]
    for k in range(4):
        ix=x+k*(TS+17)
        l0=[.20,.34,.27,.40][k]; l=l0+(.30-l0)*mix
        g.rect(ix,IY,TS,TS,fill=hsl(215,.14,l),rx=8)
        ox_=[-22,14,-6,20][k]*(1-mix); oy_=[10,-14,18,-6][k]*(1-mix); rr=[16,30,22,36][k]*(1-mix)+26*mix
        g.circ(ix+TS/2+ox_,IY+TS/2+oy_,rr,'none',0,fill='#DCE3EC',op=.85)
        if k==1: g.a(f'<rect x="{ix-6}" y="{IY-6}" width="{TS+12}" height="{TS+12}" rx="11" fill="none" stroke="{GOLD}" stroke-width="2.6" filter="url(#gl)"/>')
    bx=x+(TS+17)+TS/2
    g.text(bx,IY-18,'♥ most liked',15,GOLD,anchor='middle',fam='JetBrains Mono')
    if r<2:
        nx=X0+(r+1)*CW; gx=x+530; ly=IY+TS+40
        d=(f'M{bx},{IY+TS+6} L{bx},{ly-12} Q{bx},{ly} {bx+12},{ly} L{gx-12},{ly} Q{gx},{ly} {gx},{ly-12} '
           f'L{gx},{PY+68} Q{gx},{PY+56} {gx+12},{PY+56} L{nx-12},{PY+56}')
        g.a(f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-width="2.6" stroke-dasharray="7 6" marker-end="url(#mg)"/>')
        g.text((bx+gx)/2,ly+30,'copy the liked prompt, tweak a few words',16,GOLD,anchor='middle',fam='Inter',weight=700)
if MIN:
    for lab,yy in (('PROMPT',PY+60),('IMAGES',IY+TS/2+5)):
        g.text(X0-24,yy,lab,13,MU,anchor='end',fam='Inter',weight=700,ls=2)
# family strip
FY=800
for k in range(42):
    mix=min(1,k/26); l=random.uniform(.18,.42)*(1-mix)+.30*mix
    g.rect(110+k*40,FY,32,32,fill=hsl(215,.14,l),rx=4)
    rr=random.uniform(4,13)*(1-mix)+8*mix; ox_=random.uniform(-7,7)*(1-mix); oy_=random.uniform(-7,7)*(1-mix)
    g.circ(126+k*40+ox_,FY+16+oy_,rr,'none',0,fill='#DCE3EC',op=.85)
T(110,FY+76,'every round shapes the next',20,W_,weight=600)
T(1790,FY+76,'a family of look-alikes',20,W_,anchor='end',weight=700)
g.ell(110+33*40+16,FY+16,300,40,0,'#8A95A5',1.4,dash='4 6')
if MIN: g.a('</g>')
else: g.text(80,1020,'Illustrative prompts in the style shared on open model hubs; to be replaced with real prompt chains.',13,MU,fam='JetBrains Mono')
g.save(OUT+f'/F12_prompt{SUF}.svg')

# ============ B · infinite content, finite attention ============
g=new(); random.seed(8)
def T(x,y,t,size=14,c=W_,**k): g.text(x,y,t,size,c,fam=k.pop('fam','Inter'),**k)
if not MIN:
    T(80,92,'Endless images, one day',46,W_,fam='Inter Display',weight=700,ls=-1)
    T(82,128,'Production can be scaled and automated. Our time cannot.',22,GOLD,weight=600)
else: g.a('<g transform="translate(0,-60)">')
# left: 24h dial
cx,cy,R=420,560,250
g.circ(cx,cy,R,DIMC,26)
def arc(a0,a1,c,w=26,op=1):
    p=lambda a:(cx+R*math.sin(math.radians(a)),cy-R*math.cos(math.radians(a)))
    (x0,y0),(x1,y1)=p(a0),p(a1); large=1 if a1-a0>180 else 0
    g.a(f'<path d="M{x0:.1f},{y0:.1f} A{R},{R} 0 {large} 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{c}" stroke-width="{w}" opacity="{op}"/>')
arc(0,120,'#3A4350')            # 8 h sleep
arc(122,360,GOLD,op=.9); g.a(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{GOLD}" stroke-width="2" opacity=".2" filter="url(#gl2)"/>')
for h in range(24):
    a=math.radians(h*15); g.line(cx+(R-40)*math.sin(a),cy-(R-40)*math.cos(a),cx+(R-30)*math.sin(a),cy-(R-30)*math.cos(a),MU,1.4)
T(cx,cy-20,'24',96,W_,anchor='middle',fam='Inter Display',weight=700)
T(cx,cy+24,'hours in a day',20,MU,anchor='middle')
T(cx+R*.92,cy-R*.62,'asleep 8 h',18,MU,weight=700); T(cx-R*1.02,cy-R*.62,'awake 16 h',18,GOLD,anchor='end',weight=700)
T(cx,cy+R+70,'19,200',56,GOLD,anchor='middle',fam='Inter Display',weight=700)
T(cx,cy+R+102,'images one person could see' if MIN else 'images, if you did nothing but look, 3 s each',18 if MIN else 16,MU,anchor='middle')
# right: flood of tiles
x0,y0,w,h=820,220,1020,640
cols,rows=68,40; s=w/cols
for i in range(rows):
    for j in range(cols):
        p=random.random()
        c=random.choice(PALS)
        g.rect(x0+j*s,y0+i*s*1.0,s-3,s-3,fill=c,op=.25+.65*random.random())
# the portion one person can see (19,200 / 254,000 ≈ 7.6 %)
frac=19200/254117; ncell=int(cols*rows*frac)
g.a(f'<rect x="{x0-4}" y="{y0-4}" width="{(ncell//rows+1)*s+4:.1f}" height="{rows*s+4:.1f}" fill="none" stroke="{GOLD}" stroke-width="3" filter="url(#gl)"/>')
T(x0,y0-18,'what one person can see',18,GOLD,weight=700)
g.a(f'<rect x="{x0}" y="{y0+rows*s-60}" width="{w}" height="60" fill="url(#fade)"/>')
T(x0+w,y0+rows*s+70,'254,000',56,W_,anchor='end',fam='Inter Display',weight=700)
T(x0+w,y0+rows*s+102,'images made by this installation' if MIN else 'images a day from this installation’s feed alone (one every 0.34 s)',18 if MIN else 16,MU,anchor='end')
if MIN:
    T(cx,cy+R+126,'16 waking hours · 3 s per image',14,MU,anchor='middle')
    T(x0+w,y0+rows*s+126,'in one day · one every 0.34 s',14,MU,anchor='end')
    g.a('</g>')
else: g.text(80,1020,'Each square = about 94 images. Assumptions: 16 waking hours, 3 seconds per image, nothing else done all day.',13,MU,fam='JetBrains Mono')
g.save(OUT+f'/F13_attention{SUF}.svg')
