import sys,math,random,json
sys.path.insert(0,sys.argv[1]); from common import *
OUT=sys.argv[2]
BG='#05070B'; W_='#EEF3FA'; MU='#7C8796'; DIMC='#4A5462'
EARLY='#5EE0B5'; CYN='#5EC8FF'; BLU='#4C7DFF'; TEAL='#3FE0C0'; VIO='#9B7BFF'; GRY='#9AA3AF'; MAG='#FF4FA3'; AMB='#FFB547'
def defs(g):
    g.a('<defs><filter id="gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<filter id="gl2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7"/></filter></defs>')
def T(g,x,y,t,size=13,c=W_,**k): g.text(x,y,t,size,c,fam=k.pop('fam','Inter'),**k)
def M(g,x,y,t,size=11,c=MU,**k): g.text(x,y,t,size,c,fam='JetBrains Mono',**k)
def header(g,title,sub,n):
    T(g,80,92,title,46,W_,fam='Inter Display',weight=700,ls=-1); T(g,82,122,sub,16,MU)
    T(g,1840,92,f'ATTENTION GARDEN · {n}',12,MU,anchor='end',ls=3)
def rosette(g,cx,cy,r,n,c,sq=1.0,w=1.8,inner=True,op=1,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ''
    g.a(f'<g transform="translate({cx:.1f},{cy:.1f}) scale(1,{sq})" filter="url(#gl)" opacity="{op}">')
    for k in range(n):
        an=360*k/n
        g.a(f'<ellipse cx="{r*.55:.1f}" cy="0" rx="{r*.47:.1f}" ry="{r*.2:.1f}" transform="rotate({an:.1f})" fill="none" stroke="{c}" stroke-width="{w}"{d}/>')
        if inner: g.a(f'<ellipse cx="{r*.3:.1f}" cy="0" rx="{r*.2:.1f}" ry="{r*.08:.1f}" transform="rotate({an+180/n:.1f})" fill="none" stroke="{W_}" stroke-width="{w*.55}" opacity=".75"/>')
    g.a(f'<circle r="{r*.17:.1f}" fill="{c}"/></g>')
def capsule(g,x,y,w,h,c,title,lines,tc=None):
    g.rect(x,y,w,h,c,sw=1.4,rx=min(h/2,22),fill=BG,op=1)
    T(g,x+20,y+26,title,12,tc or c,weight=700,ls=1.6)
    for k,s in enumerate(lines): T(g,x+20,y+46+k*18,s,12,MU)
def tile(g,cx,cy,s,c=W_):
    g.rect(cx-s/2,cy-s/2,s,s,c,sw=1.2); g.line(cx-s/2,cy-s/2,cx+s/2,cy+s/2,c,.8,op=.7); g.line(cx+s/2,cy-s/2,cx-s/2,cy+s/2,c,.8,op=.7)

STG=[('SEED',16,6,0),('SPROUT',20,22,0),('SEEDLING',26,48,0),('STEMMING',30,78,0),('BUD',34,104,18),('BLOOM',46,126,42),('FLOURISH',62,150,58),('COLONY',None,164,70),('SENESCE',60,156,60),('DORMANT',None,140,40)]
COL=[EARLY,EARLY,EARLY,EARLY,CYN,CYN,BLU,TEAL,VIO,GRY]

# ================= 1 · GROWTH =================
g=SVG(bg=BG); defs(g)
header(g,'Growth logic','One plant, ten states: how long each lasts, how big it gets, how it ends','01')
G=720; S=2.0; x0=170; dx=122
def plant(i,x,c):
    name,dur,h,hd=STG[i]; Hh=h*S; R=hd*S*.62
    dorm=name=='DORMANT'; sen=name=='SENESCE'; dash='5 4' if dorm else None
    bend=.42 if dorm else (.2 if sen else 0)
    tx=x+Hh*bend*.55; ty=G-Hh*(1-bend*.35)
    g.a('<g filter="url(#gl)">')
    if i==0:
        g.ell(x,G-4,10,4.5,0,c,1.8); tile(g,x,G-28,18,c); g.line(x,G-9,x,G-19,c,1,dash='2 2'); g.a('</g>'); return tx,G-28
    cx=x+Hh*.06+Hh*bend*.25; cy=G-Hh*.5
    g.path(f'M{x:.1f},{G} Q{cx:.1f},{cy:.1f} {tx:.1f},{ty:.1f}',c,2.2,dash=dash)
    for f,sg in ((.28,-1),(.36,1),(.55,-1),(.62,1)):
        if Hh*f<12: continue
        t=f; px=(1-t)**2*x+2*(1-t)*t*cx+t*t*tx; py=(1-t)**2*G+2*(1-t)*t*cy+t*t*ty
        L=10+Hh*.07
        g.ell(px+sg*L*.5,py-L*.3,L*.55,L*.17,-35*sg+(30 if dorm else 0),c,1.5,dash=dash)
    if hd==0: g.a('</g>'); return tx,ty
    if name=='BUD':
        g.ell(tx,ty-R*.9,R*.42,R*.95,0,c,2)
        for k in (-.5,0,.5): g.path(f'M{tx+k*R*.42:.1f},{ty-R*.05:.1f} Q{tx+k*R*.62:.1f},{ty-R*.9:.1f} {tx:.1f},{ty-R*1.85:.1f}',W_,.8,op=.7)
        g.a('</g>'); return tx,ty-R*1.85
    hy=ty-R*.85
    if dorm:
        g.ell(tx,hy,R*.55,R*.75,40,c,1.6,dash='5 4'); tile(g,tx,hy,R*.5,c); g.a('</g>'); return tx,hy
    rings=[(8,1.0,0)] if name=='BLOOM' else ([(6,.95,10)] if sen else [(10,1.0,0),(6,.66,18)])
    for n,sc,ph in rings:
        for k in range(n):
            an=math.radians(ph+360*k/n); rr=R*sc
            g.ell(tx+math.cos(an)*rr*.55,hy+math.sin(an)*rr*.55,rr*.48,rr*.17,math.degrees(an),c,1.6)
    g.circ(tx,hy,R*.3,c,1.6,fill=BG); tile(g,tx,hy,R*.36,W_)
    if sen:
        for k,(ddx,ddy) in enumerate(((-18,60),(14,110),(-6,170))):
            g.ell(tx+ddx,hy+ddy,R*.38,R*.13,30+k*40,c,1.2,op=.7)
    g.a('</g>'); return tx,hy-R
g.line(100,G,1390,G,'#3A4350',2)
for gx in range(104,1390,10): g.line(gx,G+1,gx-7,G+8,'#3A4350',1)
tops=[]
for i in range(10):
    x=x0+i*dx; c=COL[i]; name,dur,h,hd=STG[i]
    if name=='COLONY':
        for ox in (-36,36):
            hh=h*S*.42; g.a('<g filter="url(#gl)">'); g.path(f'M{x+ox},{G} Q{x+ox+4},{G-hh*.5} {x+ox+2},{G-hh}',c,1.5,op=.8)
            for k in range(7):
                an=math.radians(360*k/7); r2=hd*S*.62*.42
                g.ell(x+ox+2+math.cos(an)*r2*.5,G-hh-r2*.8+math.sin(an)*r2*.5,r2*.42,r2*.15,math.degrees(an),c,1.1,op=.8)
            g.a('</g>')
        for k in range(9): g.circ(x-66+k*16,G-3,2,c,0,fill=c)
    tops.append(plant(i,x,c))
    top=G-h*S-(hd*S*.62*1.85 if hd else 0); dl=x-(64 if name=='COLONY' else 48)
    g.line(dl,G,dl,top,DIMC,1); g.line(dl-4,top,dl+4,top,DIMC,1)
    M(g,dl-7,(G+top)/2,f'h {h} · head {hd}',10,MU,anchor='middle',rot=-90)
    T(g,x,G+34,name,13,c,anchor='middle',weight=700,ls=1.4)
    M(g,x,G+52,(f'{dur} s' if dur else ('while trend' if name=='COLONY' else '240 s → debris')),11,MU,anchor='middle')
# timeline
ty_=G+104; tx0=100; tw=1290
segs=[('seed',16,EARLY),('sprout',20,EARLY),('seedling',26,EARLY),('stemming',30,EARLY),('bud',34,CYN),('bloom',46,CYN),('flourish',62,BLU),('colony',80,TEAL),('senesce',60,VIO)]
tot=sum(d for _,d,_ in segs); cx_=tx0
M(g,tx0,ty_-16,'BASE DURATION AT VIGOR 1.0 · colony shown at 80 s; it lasts as long as its trend',11,MU)
for n,d,c in segs:
    w=tw*d/tot-4
    g.a(f'<rect x="{cx_:.1f}" y="{ty_:.1f}" width="{w:.1f}" height="8" rx="4" fill="{c}" filter="url(#gl)" opacity=".9"/>')
    M(g,cx_+w/2,ty_+26,n,10,MU,anchor='middle'); cx_+=w+4
# callouts
def call(px,py,x,y,c,title,lines,w=250):
    g.line(px,py,x+(0 if x>px else w),y+22,c,1,op=.8); g.circ(px,py,3.5,c,0,fill=c)
    capsule(g,x,y,w,46+18*len(lines),c,title,lines)
call(tops[0][0],tops[0][1]-12,110,330,EARLY,'ONE REAL IMAGE PER PLANT',['the generated image rides the seed','and becomes the flower head'],270)
call(tops[4][0],tops[4][1],420,250,CYN,'HEAD APPEARS',['bud · 18 px'],170)
call(tops[7][0]-10,tops[7][1]+10,660,160,TEAL,'COLONY · ONLY INSIDE A TREND',['≥ 3 of a species in bloom','summed attention > 14'],270)
call(tops[9][0]+10,tops[9][1],1140,160,GRY,'DORMANT',['attention ran out','one look revives it','240 s unattended → debris'],210)
# right: head from above, stacked
px=1490; g.line(px-30,170,px-30,960,'#1E2530',1.2)
T(g,px,190,'THE HEAD, FROM ABOVE',12,MU,weight=700,ls=2)
stack=[('SENESCE',60,6,VIO),('COLONY',70,12,TEAL),('FLOURISH',58,10,BLU),('BLOOM',42,8,CYN),('BUD',18,3,CYN)]
cxs=1640
g.line(cxs,230,cxs,720,CYN,1,op=.35)
for k,(n,hd,pet,c) in enumerate(stack):
    y=255+k*108; r=hd*1.3
    rosette(g,cxs,y,r,pet,c,sq=.36,w=1.6)
    T(g,cxs+110,y-2,n,12,c,weight=700,ls=1.4); M(g,cxs+110,y+15,f'Ø {hd*2} px · {pet} petals',10,MU)
g.rect(px,800,350,150,'#2A3340',sw=1.2,rx=20,fill=BG)
T(g,px+22,828,'GROWTH RATE',12,W_,weight=700,ls=1.6)
M(g,px+22,858,'vigor = clamp(0.28 + 0.042·a,',13,W_); M(g,px+22,878,'                0.28, 1.6)',13,W_)
T(g,px+22,906,'a = attention on this plant',12,MU); T(g,px+22,926,'neglected 0.28 · well fed 1.6: it sets the pace',12,MU)
g.save(OUT+'/F1_growth.svg')

# ================= 2 · ATTENTION FLOW =================
g=SVG(bg=BG); defs(g)
header(g,'Where attention comes from','Sources feed one plant’s attention; attention sets the pace of growth; the stage it reaches decides how it ends','02')
RID=[0]
def ribbon(x1,y1a,y1b,x2,y2a,y2b,c,op=.32,c2=None):
    m=(x1+x2)/2; RID[0]+=1; gid=f'rg{RID[0]}'
    g.a(f'<defs><linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0"><stop offset="0" stop-color="{c}" stop-opacity="{op}"/><stop offset="1" stop-color="{c2 or c}" stop-opacity="{op*.55}"/></linearGradient></defs>')
    d=f'M{x1:.1f},{y1a:.1f} C{m:.1f},{y1a:.1f} {m:.1f},{y2a:.1f} {x2:.1f},{y2a:.1f} L{x2:.1f},{y2b:.1f} C{m:.1f},{y2b:.1f} {m:.1f},{y1b:.1f} {x1:.1f},{y1b:.1f} Z'
    g.a(f'<path d="{d}" fill="url(#{gid})"/>')
    g.a(f'<path d="M{x1:.1f},{y1a:.1f} C{m:.1f},{y1a:.1f} {m:.1f},{y2a:.1f} {x2:.1f},{y2a:.1f}" fill="none" stroke="{c}" stroke-width="1" opacity=".75" filter="url(#gl)"/>')
    g.a(f'<path d="M{x1:.1f},{y1b:.1f} C{m:.1f},{y1b:.1f} {m:.1f},{y2b:.1f} {x2:.1f},{y2b:.1f}" fill="none" stroke="{c}" stroke-width="1" opacity=".75" filter="url(#gl)"/>')
src=[('VISITOR GAZE','drains the visitor’s meter','#FFD27A'),('ALGORITHMIC GAZE','after 60 s alone · ×0.12',CYN),('BASELINE EXPOSURE','recommendation traffic · 0.24','#8593AA'),('TREND FEEDING','≥ 3 of a species in bloom',VIO),('PLATFORM LIKES','set body size at birth',EARLY)]
sy0,sh,sg=200,90,22; sx=400
T(g,80,180,'SOURCES',12,MU,weight=700,ls=2)
blk=[]
for i,(n,d,c) in enumerate(src):
    y=sy0+i*(sh+sg); g.a(f'<rect x="{sx}" y="{y}" width="10" height="{sh}" rx="5" fill="{c}" filter="url(#gl)"/>')
    T(g,80,y+40,n,15,c,weight=700,ls=1.2); T(g,80,y+62,d,13,MU); blk.append((y,y+sh,c))
ax,ay0,ay1=820,250,640
for i in range(4):
    y0,y1,c=blk[i]; seg=(ay1-ay0)/4; ribbon(sx+10,y0+10,y1-10,ax,ay0+seg*i+6,ay0+seg*(i+1)-6,c,.34,W_)
g.a(f'<rect x="{ax}" y="{ay0}" width="14" height="{ay1-ay0}" rx="7" fill="{W_}" filter="url(#gl)"/>')
T(g,ax+7,ay0-36,'ATTENTION',12,W_,anchor='middle',weight=700,ls=2); M(g,ax+7,ay0-16,'decay 0.34 · faster when crowded',11,MU,anchor='middle')
st=[('Seed',16,EARLY),('Sprout',20,EARLY),('Seedling',26,EARLY),('Stemming',30,EARLY),('Bud',34,CYN),('Bloom',46,CYN),('Flourish',62,BLU),('Colony',80,TEAL),('Senesce',60,VIO)]
tot=sum(d for _,d,_ in st); kx,kw,ky0,ky1=1150,170,180,830; sc=(ky1-ky0-8*5)/tot; y=ky0; pos={}
T(g,kx,ky0-16,'STAGES · height = base duration',12,MU,weight=700,ls=1.6)
ribbon(ax+14,ay0+10,ay1-10,kx,ky0,ky1,W_,.09,CYN)
T(g,(ax+kx)/2+10,ay0+20,'sets the pace',14,W_,anchor='middle',weight=600)
M(g,(ax+kx)/2+10,ay0+40,'vigor 0.28 – 1.6',11,MU,anchor='middle')
for n,d,c in st:
    h=d*sc; g.rect(kx,y,kw,h,c,sw=1.6,rx=6,fill=BG)
    g.a(f'<rect x="{kx}" y="{y:.1f}" width="{kw}" height="{h:.1f}" rx="6" fill="{c}" opacity=".16"/>')
    T(g,kx+14,y+h/2+5,n,14,c,weight=700); M(g,kx+kw-10,y+h/2+4,('trend' if n=='Colony' else f'{d} s'),11,MU,anchor='end')
    pos[n]=(y,y+h); y+=h+5
y0,y1,c=blk[4]; ribbon(sx+10,y0+12,y1-12,kx,pos['Bloom'][0]+4,pos['Flourish'][1]-4,c,.22,BLU)
T(g,610,y0+20,'body size',12,c,anchor='middle',weight=700)
ox=1640
outs=[('BLOOM','grows, branches, drops seeds',CYN,8,(pos['Bloom'][0],pos['Flourish'][1]),240,None),
      ('COLONY','only while its species trends',TEAL,12,pos['Colony'],430,None),
      ('DORMANT','attention ran out · a look revives it',GRY,6,(pos['Bud'][0],pos['Flourish'][1]),620,'5 4'),
      ('DEBRIS','240 s dormant, or after senescence','#D98CA8',0,pos['Senesce'],800,None)]
T(g,ox-90,180,'OUTCOMES',12,MU,weight=700,ls=2)
for n,d,c,pet,frm,cy,dash in outs:
    ribbon(kx+kw,frm[0]+3,frm[1]-3,ox-56,cy-14,cy+14,c,.14 if n=='DORMANT' else .28)
    if pet: rosette(g,ox,cy,44,pet,c,w=1.8,dash=dash)
    else:
        r=random.Random(4)
        for k in range(26):
            an=r.uniform(0,6.28); dd=r.uniform(4,44); s_=r.uniform(3,8)
            g.rect(ox+math.cos(an)*dd-s_/2,cy+math.sin(an)*dd-s_/2,s_,s_,fill=c,op=r.uniform(.35,.95))
    T(g,ox+64,cy-4,n,16,c,weight=700,ls=1.4); T(g,ox+64,cy+18,d,12,MU)
g.arrowdef('am','#D98CA8'); g.arrowdef('ag',GRY)
g.path(f'M{ox},{620+52} L{ox},{800-54}','#D98CA8',1.6,marker='am')
g.path(f'M{ox-48},{606} C{ox-140},{560} {ox-140},{300} {ox-54},{256}',GRY,1.4,dash='4 5',marker='ag')
T(g,ox-150,430,'revived',12,GRY,anchor='end',weight=600)
M(g,80,1010,'Ribbon widths are schematic. Stage heights, rates and thresholds are taken from the code.',11,MU)
g.save(OUT+'/F2_flow.svg')

# ================= 3 · TAXONOMY =================
random.seed(7)
g=SVG(bg=BG); defs(g)
header(g,'Species are found, not designed','Generated images are measured by how they look, clustered with their look-alikes, and grown as one of 14 species','03')
# matrix of images
T(g,80,180,'734 IMAGES',12,MU,weight=700,ls=2)
for i in range(10):
    for j in range(8):
        c=random.choice(PALS); g.rect(80+j*30,200+i*30,26,26,fill=c,op=random.uniform(.45,1))
M(g,80,510,'each image → a 128 px tile',11,MU)
# features
fx=80; fy=560
T(g,fx,fy,'WHAT IS MEASURED',12,MU,weight=700,ls=2)
for i in range(4):
    for j in range(4): g.rect(fx+j*22,fy+20+i*22,20,20,fill=random.choice(PALS))
T(g,fx+108,fy+42,'Colour layout',14,W_,weight=600); M(g,fx+108,fy+60,'4×4 RGB · 48',11,MU)
hues=['#FF5A4F','#FF9A3D','#F2D23C','#7FD35B','#3FB8E8','#6A6CFF']
for k in range(18):
    h=random.uniform(8,56); g.a(f'<rect x="{fx+k*6}" y="{fy+180-h:.1f}" width="4" height="{h:.1f}" fill="{hues[k//3]}" opacity="{[1,.7,.45][k%3]}" filter="url(#gl)"/>')
T(g,fx+120,fy+150,'Hue histogram',14,W_,weight=600); M(g,fx+120,fy+168,'6×3×3 · 54',11,MU)
for i in range(8):
    for j in range(8):
        v=random.uniform(.15,.95); g.circ(fx+5+j*11,fy+210+i*11,4,'none',0,fill=f'rgb({int(v*230)},{int(v*235)},{int(v*245)})')
T(g,fx+108,fy+240,'Grey fingerprint',14,W_,weight=600); M(g,fx+108,fy+258,'16×16 · 256 · weight 0.4',11,MU)
# ring with distribution inside
CX,CY_,R=800,560,300
g.a(f'<circle cx="{CX}" cy="{CY_}" r="{R}" fill="none" stroke="{CYN}" stroke-width="1.2" opacity=".4" filter="url(#gl)"/>')
cents=[]
for c in range(8):
    an=-math.pi/2+2*math.pi*c/8
    cents.append((CX+math.cos(an)*R*.5,CY_+math.sin(an)*R*.5,an))
for c,(x,y,an) in enumerate(cents):
    g.a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="56" fill="{PALS[c]}" opacity=".18" filter="url(#gl2)"/>')
    for k in range(40): g.circ(x+random.gauss(0,20),y+random.gauss(0,17),2.2,'none',0,fill=PALS[c],op=.85)
    g.line(x-6,y,x+6,y,W_,1.4); g.line(x,y-6,x,y+6,W_,1.4)
    nx,ny=CX+math.cos(an)*R,CY_+math.sin(an)*R
    g.line(x+math.cos(an)*30,y+math.sin(an)*30,nx-math.cos(an)*40,ny-math.sin(an)*40,PALS[c],1,op=.6,dash='2 4')
    sp=[s for s in SPECIES if bucket(s[2])==c]
    rosette(g,nx,ny,34,max(sp[0][3],3),PALS[c],w=1.8)
    T(g,nx+math.cos(an)*54,ny+math.sin(an)*54+5,f'C{c}',13,PALS[c],anchor='middle',weight=800)
M(g,CX,CY_+R+78,'k-means++ · k = 8 · fixed seed · positions schematic',11,MU,anchor='middle')
M(g,CX,CY_+R+96,'80 % purity on a labelled test set (grey fingerprint alone: 54 %)',11,MU,anchor='middle')
# species table
tx=1210; T(g,tx,180,'14 SPECIES · grouped by cluster',12,MU,weight=700,ls=2)
for c in range(8):
    y=212+c*62; sp=[s for s in SPECIES if bucket(s[2])==c]
    T(g,tx,y+22,f'C{c}',13,PALS[c],weight=800)
    for k,(zh,en,pal,pet) in enumerate(sp):
        x=tx+52+k*300; rosette(g,x+20,y+16,20,max(pet,3),PALS[pal],w=1.4,inner=False)
        T(g,x+52,y+16,en,15,W_,weight=600,ls=.6)
        g.text(x+52,y+33,zh,10,MU,fam='IPAGothic')
        M(g,x+52+len(en)*10.5,y+16,f'{pet} petals',10,DIMC)
    g.line(tx,y+46,tx+620,y+46,'#1E2530',1)
M(g,tx,720,'cluster = palette index mod 8 · two species can share one pool of images',11,MU)
# born unequal
px,py,pw,ph=1210,800,420,150
T(g,px,py-22,'BORN UNEQUAL · platform likes set body size',12,MU,weight=700,ls=1.6)
pts=[]
for i in range(0,101):
    lk=10**(i/100*5)-1; v=0.72+0.62*min(1,math.log10(1+lk)/4.2); pts.append(f'{px+pw*i/100:.1f},{py+ph-(v-0.6)/0.8*ph:.1f}')
g.a(f'<path d="M{" L".join(pts)}" fill="none" stroke="{AMB}" stroke-width="2.4" filter="url(#gl)"/>')
g.line(px,py+ph,px+pw,py+ph,DIMC,1)
for e,lab in enumerate(['0','10','100','1k','10k','100k']): M(g,px+pw*e/5,py+ph+18,lab,10,MU,anchor='middle')
T(g,px+450,py+50,'0.72',28,W_,fam='Inter Display',weight=600); T(g,px+530,py+50,'nobody liked it',12,MU)
T(g,px+450,py+100,'1.34',28,AMB,fam='Inter Display',weight=600); T(g,px+530,py+100,'~16k likes or more',12,MU)
g.save(OUT+'/F3_taxonomy.svg')

# ================= 4 · INTERACTION =================
GOLD='#FFD27A'
g=SVG(bg=BG); defs(g); g.arrowdef('ag2',GOLD); g.arrowdef('ac2',CYN)
header(g,'Looking is the only input','A gaze that feeds what it rests on, a supply that runs out, and an algorithm that looks when nobody does','04')
# --- the gaze
T(g,80,190,'THE GAZE',12,MU,weight=700,ls=2)
bx,by,R0=300,420,150
harm=[(2,.06,.3),(3,.045,1.2),(5,.03,2.1),(7,.02,.7)]
pts=[]
for i in range(0,361,2):
    t=math.radians(i); r=R0*(1+sum(a*math.sin(k*t+p) for k,a,p in harm)); pts.append(f'{bx+r*math.cos(t):.1f},{by+r*math.sin(t):.1f}')
g.a(f'<path d="M{" L".join(pts)} Z" fill="none" stroke="{GOLD}" stroke-width="2.6" filter="url(#gl)"/>')
g.circ(bx,by,R0,DIMC,1,dash='3 5')
g.line(bx,by,bx+R0,by,DIMC,1); M(g,bx+R0/2,by-8,'r 96',11,MU,anchor='middle')
for k,c in enumerate([PALS[1],PALS[5],PALS[3]]): g.rect(bx-50+k*36,by-56,30,30,fill=c,op=.9)
for k,(n,a,p) in enumerate(harm):
    sx=120+k*100; sy=650; pp=[]
    for i in range(0,361,4):
        t=math.radians(i); r=30*(1+a*4*math.sin(n*t+p)); pp.append(f'{sx+r*math.cos(t):.1f},{sy+r*math.sin(t):.1f}')
    g.a(f'<path d="M{" L".join(pp)} Z" fill="none" stroke="{GOLD}" stroke-width="1.4" opacity=".8" filter="url(#gl)"/>')
    M(g,sx,sy+52,f'sin {n}θ',11,MU,anchor='middle')
T(g,80,740,'One membrane, four harmonics summed:',13,W_); T(g,80,760,'it keeps bending and never settles.',13,MU)
# --- who is looking
cx0=640
T(g,cx0,190,'WHO IS LOOKING',12,MU,weight=700,ls=2)
capsule(g,cx0,215,420,112,GOLD,'VISITOR',['your pointer is the gaze point','feeds +26 / s in the feed, +36 / s in the garden','spends the visitor’s own attention'])
capsule(g,cx0,505,420,112,CYN,'ALGORITHM',['takes over after 60 s with no input','the same gains × 0.12','never runs out'])
g.path(f'M{cx0+110},{329} L{cx0+110},{500}',CYN,1.8,marker='ac2'); T(g,cx0+124,440,'60 s alone',13,CYN,weight=700)
g.path(f'M{cx0+310},{503} L{cx0+310},{332}',GOLD,1.8,marker='ag2'); T(g,cx0+324,440,'any input',13,GOLD,weight=700)
T(g,cx0,705,'WHERE THE ALGORITHM LOOKS FIRST',12,MU,weight=700,ls=2)
pri=[('dormant plants',2.2),('wilting plants',1.5),('one short of a trend',1.1),('about to bloom',.8),('already trending',.5)]
for k,(n,w) in enumerate(pri):
    y=730+k*34
    T(g,cx0,y+14,n,13,W_)
    g.a(f'<rect x="{cx0+190}" y="{y+3}" width="{w*90:.1f}" height="12" rx="6" fill="{CYN}" opacity="{.35+.25*w/2.2:.2f}" filter="url(#gl)"/>')
    M(g,cx0+200+w*90,y+14,f'+{w}',11,MU)
M(g,cx0,912,'score added when picking the next plant to look at',11,MU)
# --- meter
mx=1180
T(g,mx,190,'THE VISITOR’S ATTENTION',12,MU,weight=700,ls=2)
gx,gy,gw,gh=mx,220,70,420
g.rect(gx,gy,gw,gh,GOLD,sw=1.6,rx=35,fill=BG)
g.a(f'<defs><linearGradient id="mg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GOLD}" stop-opacity=".9"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".15"/></linearGradient></defs>')
g.a(f'<rect x="{gx+8}" y="{gy+gh*.45:.1f}" width="{gw-16}" height="{gh*.55-8:.1f}" rx="27" fill="url(#mg)"/>')
g.a(f'<line x1="{gx+14}" y1="{gy+gh*.45+2:.1f}" x2="{gx+gw-14}" y2="{gy+gh*.45+2:.1f}" stroke="{GOLD}" stroke-width="3" filter="url(#gl)"/>')
for v in (0,50,100): M(g,gx+gw+12,gy+gh-gh*v/100+4,str(v),11,MU)
g.arrowdef('am2',EARLY); g.arrowdef('ar2',GOLD)
g.path(f'M{gx+150},{gy+gh-30} L{gx+150},{gy+gh-140}',EARLY,2,marker='am2'); T(g,gx+170,gy+gh-90,'refills 5.2 / s',15,EARLY,weight=700); T(g,gx+170,gy+gh-70,'when you rest',12,MU)
g.path(f'M{gx+150},{gy+40} L{gx+150},{gy+150}',GOLD,2,marker='ar2'); T(g,gx+170,gy+90,'spent up to 20 / s',15,GOLD,weight=700); T(g,gx+170,gy+110,'while you feed',12,MU)
T(g,mx,700,'You cannot feed everything.',22,W_,fam='Inter Display',weight=600)
T(g,mx,730,'Choosing what to feed is choosing what to let go.',15,MU)
# --- what one look does
T(g,1180,800,'WHAT ONE LOOK DOES',12,MU,weight=700,ls=2)
eff=[('FEED','gains attention; may breed or migrate',GOLD),('GARDEN','grows; a dormant plant wakes up',TEAL),('ROOTS','its path lights up to the power layer',VIO),('SOUND','the looked-at video speaks; ambience to 45 %',CYN)]
for k,(n,d,c) in enumerate(eff):
    x=1180+(k%2)*330; y=830+(k//2)*90
    g.circ(x+16,y+18,14,c,1.8,fill=BG); g.circ(x+16,y+18,4,c,0,fill=c)
    T(g,x+42,y+16,n,14,c,weight=700,ls=1.4); T(g,x+42,y+36,d,12,MU)
g.save(OUT+'/F4_interaction.svg')
