"""
MindmapRenderer v3 — Premium mind-map cheatsheet PNG generator.
Features: gradient bg, glassmorphism cards, curved connectors with glow,
double-ring hub, section icons, micro-details, consistent color system.
"""
import math, random, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from config.settings import config

# Section icon mapping
SECTION_ICONS = {
    "variable": "🔤", "type": "🔤", "data type": "🔤",
    "function": "⚙️", "method": "⚙️", "def": "⚙️",
    "oop": "🧱", "class": "🧱", "object": "🧱", "inherit": "🧱",
    "error": "⚠️", "exception": "⚠️", "handling": "⚠️", "debug": "⚠️",
    "data structure": "📊", "list": "📊", "dict": "📊", "array": "📊",
    "module": "📦", "package": "📦", "import": "📦", "library": "📦",
    "security": "🛡️", "auth": "🛡️", "encrypt": "🛡️",
    "network": "🌐", "api": "🌐", "http": "🌐", "web": "🌐",
    "database": "🗄️", "sql": "🗄️", "query": "🗄️",
    "test": "🧪", "deploy": "🚀", "cloud": "☁️", "async": "⚡",
    "loop": "🔄", "control": "🔄", "flow": "🔄", "condition": "🔄",
}
FALLBACK_ICONS = ["🧠", "⚡", "🔧", "📊", "🚀", "🛡️", "💡", "🎯"]


def _pick_icon(title, idx):
    t = title.lower()
    for key, icon in SECTION_ICONS.items():
        if key in t:
            return icon
    return FALLBACK_ICONS[idx % len(FALLBACK_ICONS)]


class MindmapRenderer:
    W, H = 3200, 2000

    COLORS = [
        (59,130,246), (16,185,129), (245,158,11), (139,92,246),
        (244,63,94), (6,182,212), (234,179,8), (99,102,241),
    ]

    def __init__(self):
        self.output_dir = config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._f = {}
        for s in [10,12,14,16,18,22,28,38,50]:
            self._f[s] = self._load(s)

    def f(self, s):
        return self._f.get(s, self._f[16])

    def _load(self, size):
        for p in ["C:/Windows/Fonts/segoeuib.ttf","C:/Windows/Fonts/segoeui.ttf",
                   "C:/Windows/Fonts/arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
            try: return ImageFont.truetype(p, size)
            except: continue
        return ImageFont.load_default()

    def render(self, title, user_analysis, trend_data, content_data, timestamp=""):
        ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        topic = user_analysis.get("topic", title)
        diff = user_analysis.get("difficulty", "intermediate")
        secs = content_data.get("sections", [])
        tags = content_data.get("tags", [])
        trends = trend_data.get("latest_trends", [])
        summary = content_data.get("summary", "")

        random.seed(hash(topic) % 9999)
        img = Image.new("RGB", (self.W, self.H), (4,6,14))
        d = ImageDraw.Draw(img)

        self._bg_gradient(d)
        self._bg_particles(d)
        self._bg_grid(d)
        self._bg_mesh(d)

        hdr_h = 130
        ctr = (self.W//2, hdr_h + (self.H - hdr_h - 90)//2)
        pos = self._positions(ctr, len(secs))

        self._curved_connectors(d, ctr, pos)
        self._cross_links(d, pos)
        self._hub(d, ctr, title, topic, diff, len(secs))
        self._cards(d, pos, secs)
        self._header(d, title, topic, diff, len(secs))
        self._tag_bar(d, tags, hdr_h + 8)
        self._trend_bar(d, trends)
        if summary:
            self._summary_box(d, summary)
        self._footer(d, ts)
        self._frame(d)

        # Bloom effect
        bloom = img.filter(ImageFilter.GaussianBlur(4))
        img = Image.blend(img, bloom, 0.07)

        safe = "".join(c if c.isalnum() or c in " -" else "" for c in title[:50]).replace(" ","_")
        path = self.output_dir / f"mindmap_{safe}_{ts}.png"
        img.save(str(path), "PNG", quality=95)
        print(f"   🎨 Mind-map saved: {path} ({path.stat().st_size//1024}KB)")
        return str(path)

    # ═══════════ BACKGROUND ═══════════
    def _bg_gradient(self, d):
        """Blue→purple→black diagonal gradient."""
        for y in range(self.H):
            t = y / self.H
            r = int(8*(1-t) + 12*t)
            g = int(12*(1-t) + 8*t)
            b = int(35*(1-t) + 18*t)
            # Add slight purple in middle
            mid = 1 - abs(t - 0.5)*2
            r += int(15 * mid)
            b += int(20 * mid)
            d.line([(0,y),(self.W,y)], fill=(r,g,b))

    def _bg_particles(self, d):
        """Stars and glowing particles."""
        for _ in range(300):
            x, y = random.randint(0,self.W), random.randint(0,self.H)
            br = random.randint(25, 70)
            sz = random.choice([1,1,1,2,2,3])
            if sz >= 3:
                # Bright star with cross
                d.ellipse([x-2,y-2,x+2,y+2], fill=(br+30,br+30,br+50))
                d.line([(x-4,y),(x+4,y)], fill=(br,br,br+20), width=1)
                d.line([(x,y-4),(x,y+4)], fill=(br,br,br+20), width=1)
            else:
                d.ellipse([x,y,x+sz,y+sz], fill=(br,br,br+15))

    def _bg_grid(self, d):
        """Subtle dot grid."""
        for x in range(0, self.W, 50):
            for y in range(0, self.H, 50):
                d.ellipse([x,y,x+1,y+1], fill=(22,28,42))

    def _bg_mesh(self, d):
        """Network mesh connections."""
        pts = [(random.randint(50,self.W-50), random.randint(50,self.H-50)) for _ in range(35)]
        for i,p1 in enumerate(pts):
            for p2 in pts[i+1:]:
                dist = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
                if dist < 350:
                    a = max(8, int(18*(1-dist/350)))
                    d.line([p1,p2], fill=(15+a, 20+a, 35+a), width=1)
            d.ellipse([p1[0]-2,p1[1]-2,p1[0]+2,p1[1]+2], fill=(30,40,60))

    # ═══════════ HEADER BANNER ═══════════
    def _header(self, d, title, topic, diff, n):
        # Dark glass bar
        d.rectangle([0,0,self.W,115], fill=(6,10,18))
        # Gradient accent line (blue→purple)
        for x in range(self.W):
            t = x/self.W
            d.line([(x,113),(x,115)], fill=(
                int(59*(1-t)+139*t), int(130*(1-t)+92*t), 246))
        # Micro dots along top
        for x in range(0, self.W, 8):
            d.ellipse([x,0,x+1,1], fill=(25,35,55))

        # Title
        d.text((50, 18), title, fill=(241,245,249), font=self.f(38))
        # Subtitle
        d.text((50, 65), "📋 Quick Revision Cheatsheet  •  Mind Map",
               fill=(100,116,139), font=self.f(16))

        # Right-side badges
        badges = [f"📚 {topic}", f"📊 {diff.title()}", f"📄 {n} Sections",
                  f"⏰ {datetime.now().strftime('%b %Y')}"]
        bx = self.W - 50
        for b in reversed(badges):
            bb = d.textbbox((0,0), b, font=self.f(14))
            bw = bb[2]-bb[0]+24
            bx -= bw
            d.rounded_rectangle([bx,72,bx+bw,96], radius=12,
                                fill=(15,22,38), outline=(35,50,75))
            d.text((bx+12,75), b, fill=(148,163,184), font=self.f(14))
            bx -= 10

    # ═══════════ FRAME BORDER ═══════════
    def _frame(self, d):
        d.rounded_rectangle([3,3,self.W-3,self.H-3], radius=24,
                            outline=(25,40,65), width=2)
        # Corner gems
        for cx,cy in [(18,18),(self.W-18,18),(18,self.H-18),(self.W-18,self.H-18)]:
            d.ellipse([cx-6,cy-6,cx+6,cy+6], fill=(59,130,246))
            d.ellipse([cx-3,cy-3,cx+3,cy+3], fill=(120,180,255))

    # ═══════════ NODE LAYOUT ═══════════
    def _positions(self, ctr, n):
        if n == 0: return []
        cx, cy = ctr
        rx, ry = 950, 580
        out = []
        for i in range(n):
            a = math.radians(-90 + 360/n * i)
            nx = cx + int(rx*math.cos(a))
            ny = cy + int(ry*math.sin(a))
            w, h = 420, 320
            out.append((nx-w//2, ny-h//2, w, h))
        return out

    # ═══════════ CURVED CONNECTORS ═══════════
    def _curved_connectors(self, d, ctr, positions):
        cx, cy = ctr
        R = 150
        for i, (nx,ny,nw,nh) in enumerate(positions):
            col = self.COLORS[i % len(self.COLORS)]
            ncx, ncy = nx+nw//2, ny+nh//2
            ang = math.atan2(ncy-cy, ncx-cx)

            # Start: edge of hub circle
            sx = cx + int(R*math.cos(ang))
            sy = cy + int(R*math.sin(ang))

            # End: edge of the card (find intersection with card border)
            # Use half-width/height to find edge point toward center
            rev_ang = math.atan2(cy-ncy, cx-ncx)  # angle from node TO center
            # Clamp to card edge
            hw, hh = nw//2, nh//2
            cos_a, sin_a = math.cos(rev_ang), math.sin(rev_ang)
            if abs(cos_a) * hh > abs(sin_a) * hw:
                scale = abs(hw / cos_a) if cos_a != 0 else hh
            else:
                scale = abs(hh / sin_a) if sin_a != 0 else hw
            ex = ncx + int(scale * cos_a)
            ey = ncy + int(scale * sin_a)

            # Bezier curve control point (perpendicular offset)
            perp = ang + math.pi/2
            offset = 50 * (1 if i % 2 == 0 else -1)
            cpx = (sx+ex)//2 + int(offset*math.cos(perp))
            cpy = (sy+ey)//2 + int(offset*math.sin(perp))

            # Draw curved line as segments
            pts = []
            for t in [s/40 for s in range(41)]:
                px = (1-t)**2*sx + 2*(1-t)*t*cpx + t**2*ex
                py = (1-t)**2*sy + 2*(1-t)*t*cpy + t**2*ey
                pts.append((int(px), int(py)))

            # Glow layers
            for w in [12, 8, 5]:
                gc = tuple(int(c*0.12) for c in col)
                for j in range(len(pts)-1):
                    d.line([pts[j], pts[j+1]], fill=gc, width=w)
            # Main line
            lc = tuple(int(c*0.75) for c in col)
            for j in range(len(pts)-1):
                d.line([pts[j], pts[j+1]], fill=lc, width=3)

            # Arrowhead pointing AT the card (use last 2 curve points for direction)
            tip_x, tip_y = pts[-1]
            prev_x, prev_y = pts[-3]
            arr_ang = math.atan2(tip_y-prev_y, tip_x-prev_x)
            ax1 = tip_x - int(18*math.cos(arr_ang-0.4))
            ay1 = tip_y - int(18*math.sin(arr_ang-0.4))
            ax2 = tip_x - int(18*math.cos(arr_ang+0.4))
            ay2 = tip_y - int(18*math.sin(arr_ang+0.4))
            d.polygon([(tip_x,tip_y),(ax1,ay1),(ax2,ay2)], fill=col)

            # Traveling dots
            for t in [0.2, 0.4, 0.6, 0.8]:
                mx = (1-t)**2*sx + 2*(1-t)*t*cpx + t**2*ex
                my = (1-t)**2*sy + 2*(1-t)*t*cpy + t**2*ey
                r = 5 if t in [0.4, 0.6] else 3
                d.ellipse([int(mx)-r, int(my)-r, int(mx)+r, int(my)+r], fill=col)

    def _cross_links(self, d, positions):
        n = len(positions)
        for i in range(n):
            j = (i+1)%n
            x1,y1 = positions[i][0]+positions[i][2]//2, positions[i][1]+positions[i][3]//2
            x2,y2 = positions[j][0]+positions[j][2]//2, positions[j][1]+positions[j][3]//2
            dist = math.hypot(x2-x1, y2-y1)
            steps = max(1, int(dist/14))
            for s in range(0, steps, 2):
                t1,t2 = s/steps, min((s+1)/steps, 1)
                d.line([(int(x1+t1*(x2-x1)),int(y1+t1*(y2-y1))),
                        (int(x1+t2*(x2-x1)),int(y1+t2*(y2-y1)))],
                       fill=(20,28,42), width=1)

    # ═══════════ CENTER HUB ═══════════
    def _hub(self, d, ctr, title, topic, diff, n):
        cx, cy = ctr
        R = 140

        # Outer pulse glow (3 rings)
        for ring in [R+60, R+40, R+20]:
            for r in range(ring, ring-15, -1):
                a = int(8*(1-(r-ring+15)/15))
                d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(15+a,25+a,55+a*2))

        # Double ring
        d.ellipse([cx-R-6,cy-R-6,cx+R+6,cy+R+6], outline=(59,130,246), width=3)
        d.ellipse([cx-R-1,cy-R-1,cx+R+1,cy+R+1], outline=(100,160,255), width=1)

        # Inner gradient fill
        for r in range(R, 0, -1):
            t = r/R
            d.ellipse([cx-r,cy-r,cx+r,cy+r],
                      fill=(int(8+12*t), int(14+20*t), int(28+35*t)))

        # Inner accent ring
        d.ellipse([cx-R+8,cy-R+8,cx+R-8,cy+R-8], outline=(40,65,120), width=1)

        # Title
        short = title if len(title)<=22 else title[:20]+"…"
        lines = textwrap.wrap(short, width=12)
        th = len(lines)*44
        sy = cy - th//2 - 18
        for j, line in enumerate(lines):
            bb = d.textbbox((0,0), line, font=self.f(38))
            tw = bb[2]-bb[0]
            d.text((cx-tw//2, sy+j*44), line, fill=(241,245,249), font=self.f(38))

        # Subtitle
        sub = "Quick Revision Guide"
        bb = d.textbbox((0,0), sub, font=self.f(14))
        d.text((cx-(bb[2]-bb[0])//2, sy+len(lines)*44+8),
               sub, fill=(80,100,140), font=self.f(14))

        # Meta ring text
        meta = f"📚 {topic}  •  📊 {diff}  •  📄 {n}"
        bb = d.textbbox((0,0), meta, font=self.f(12))
        d.text((cx-(bb[2]-bb[0])//2, sy+len(lines)*44+28),
               meta, fill=(60,75,100), font=self.f(12))

    # ═══════════ GLASSMORPHISM CARDS ═══════════
    def _cards(self, d, positions, sections):
        for i, (sec, (x,y,w,h)) in enumerate(zip(sections, positions)):
            col = self.COLORS[i % len(self.COLORS)]
            t = sec.get("title", f"Section {i+1}")
            pts = sec.get("key_points", [])
            tip = sec.get("pro_tip", "")
            code = sec.get("code_example", "")
            icon = _pick_icon(t, i)

            # ── Glass card ──
            # Shadow
            d.rounded_rectangle([x+5,y+5,x+w+5,y+h+5], radius=20, fill=(0,0,0))
            # Glass bg (semi-transparent feel)
            d.rounded_rectangle([x,y,x+w,y+h], radius=20,
                                fill=(10,16,28))
            # Inner lighter panel
            d.rounded_rectangle([x+2,y+2,x+w-2,y+h-2], radius=19,
                                fill=(12,20,35))
            # Border with section color
            d.rounded_rectangle([x,y,x+w,y+h], radius=20,
                                outline=tuple(int(c*0.45) for c in col), width=2)
            # Top glow bar
            for bx in range(x+24, x+w-24):
                t_val = (bx-x-24)/(w-48)
                alpha = 1.0 - abs(t_val-0.5)*2
                bc = tuple(int(c*alpha*0.8) for c in col)
                d.line([(bx,y+2),(bx,y+5)], fill=bc)

            # ── Section number (01, 02...) ──
            num = f"{i+1:02d}"
            d.text((x+w-50, y+14), num, fill=tuple(int(c*0.2) for c in col), font=self.f(28))

            # ── Icon circle ──
            icx, icy = x+30, y+34
            d.ellipse([icx-18,icy-18,icx+18,icy+18],
                      fill=tuple(int(c*0.15) for c in col),
                      outline=tuple(int(c*0.4) for c in col), width=2)
            # Icon text (emoji)
            d.text((icx-8, icy-10), icon, font=self.f(16))

            # ── Title ──
            st = t if len(t)<=32 else t[:30]+"…"
            d.text((x+58, y+20), st, fill=col, font=self.f(22))
            # Highlight line under title
            d.line([(x+58, y+50), (x+58+min(len(st)*10, w-80), y+50)],
                   fill=tuple(int(c*0.3) for c in col), width=2)

            # ── Key points ──
            py = y+62
            for j, pt in enumerate(pts[:5]):
                sp = pt if len(pt)<=55 else pt[:53]+"…"
                bc = tuple(int(c*0.6) for c in col)
                d.text((x+24, py), "▸", fill=bc, font=self.f(16))
                d.text((x+42, py), sp, fill=(148,163,184), font=self.f(16))
                py += 28

            # ── Separator ──
            if tip or code:
                d.line([(x+20,py+4),(x+w-20,py+4)],
                       fill=tuple(int(c*0.12) for c in col), width=1)
                # Micro dots on separator
                for dx in range(x+20, x+w-20, 30):
                    d.ellipse([dx,py+3,dx+2,py+5],
                              fill=tuple(int(c*0.25) for c in col))
                py += 12

            # ── Pro tip ──
            if tip and py < y+h-45:
                st2 = tip if len(tip)<=55 else tip[:53]+"…"
                d.rounded_rectangle([x+16,py,x+w-16,py+30], radius=8,
                                    fill=tuple(int(c*0.08) for c in col),
                                    outline=tuple(int(c*0.15) for c in col))
                d.text((x+24,py+5), f"💡 {st2}",
                       fill=tuple(min(255,int(c*1.2)) for c in col), font=self.f(14))
                py += 36

            # ── Code snippet ──
            if code and py < y+h-35:
                snippet = code.replace('\n',' ')
                snippet = snippet if len(snippet)<=60 else snippet[:58]+"…"
                d.rounded_rectangle([x+16,py,x+w-16,py+28], radius=6,
                                    fill=(8,14,25), outline=(25,35,50))
                d.text((x+24,py+5), f"</> {snippet}",
                       fill=(80,200,140), font=self.f(12))

            # ── Corner tech icon ──
            self._tech_icon(d, x+w-38, y+h-38, i, col)

    def _tech_icon(self, d, x, y, idx, col):
        c = tuple(int(v*0.3) for v in col)
        t = idx % 4
        if t==0:
            pts=[(x+int(14*math.cos(math.radians(60*k-30))),
                  y+int(14*math.sin(math.radians(60*k-30)))) for k in range(6)]
            d.polygon(pts, outline=c)
        elif t==1:
            d.ellipse([x-12,y-12,x+12,y+12], outline=c, width=2)
            d.ellipse([x-4,y-4,x+4,y+4], fill=c)
        elif t==2:
            d.polygon([(x,y-14),(x+14,y),(x,y+14),(x-14,y)], outline=c)
        else:
            d.rectangle([x-12,y-12,x+12,y+12], outline=c, width=2)

    # ═══════════ TAGS / TRENDS / SUMMARY / FOOTER ═══════════
    def _tag_bar(self, d, tags, y):
        if not tags: return
        x = 50
        for i, tag in enumerate(tags[:12]):
            bb = d.textbbox((0,0), tag, font=self.f(14))
            tw = bb[2]-bb[0]+22
            d.rounded_rectangle([x,y,x+tw,y+28], radius=14,
                                fill=(15,22,38), outline=(30,45,65))
            d.text((x+11,y+5), tag, fill=(100,116,139), font=self.f(14))
            x += tw+8
            if x > self.W-120: break

    def _trend_bar(self, d, trends):
        if not trends: return
        y = self.H-80
        d.text((50,y), "🔥 TRENDING", fill=(100,116,139), font=self.f(14))
        x = 190
        for i, tr in enumerate(trends[:6]):
            s = tr if len(tr)<=30 else tr[:28]+"…"
            bb = d.textbbox((0,0), s, font=self.f(14))
            tw = bb[2]-bb[0]+24
            c = self.COLORS[i%len(self.COLORS)]
            d.rounded_rectangle([x,y-2,x+tw,y+24], radius=12,
                                fill=tuple(int(v*0.1) for v in c),
                                outline=tuple(int(v*0.3) for v in c))
            d.text((x+12,y), s, fill=c, font=self.f(14))
            x += tw+10
            if x > self.W-300: break

    def _summary_box(self, d, summary):
        bw = 750
        bx = self.W-bw-50
        by = self.H-80
        short = summary if len(summary)<=100 else summary[:98]+"…"
        d.rounded_rectangle([bx,by-4,bx+bw,by+26], radius=12,
                            fill=(10,16,30), outline=(25,38,58))
        d.text((bx+14,by), f"📝 {short}", fill=(80,95,120), font=self.f(14))

    def _footer(self, d, ts):
        y = self.H-35
        txt = f"Generated by AI Cheatsheet Generator  •  {ts}  •  Powered by Gemini AI"
        bb = d.textbbox((0,0), txt, font=self.f(12))
        d.text((self.W//2-(bb[2]-bb[0])//2, y), txt, fill=(30,40,55), font=self.f(12))
