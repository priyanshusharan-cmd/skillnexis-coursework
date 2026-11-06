"""Technical drawings (A3, first-angle projection, mm) generated from the CAD solids.
Views come from OpenCASCADE's hidden-line removal (HLR): visible edges as thick lines, hidden edges dashed.
Dimensions, centre lines, the gear data table, the BOM with balloons and the title block are added on top.
    python src/drawing.py  -> drawings/*.svg and drawings/*.pdf"""
import json, math, os, subprocess, sys, datetime
sys.path.insert(0, "src")
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.GeomAbs import GeomAbs_Line
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from parts import P, centres, gear, side_plate
from assembly import build, shapes, MATERIAL
os.makedirs("drawings", exist_ok=True)
def conventional_gear(z, p=P):
    """ISO 2203 conventional representation for side/assembly views: a plain cylinder at the tip diameter (teeth not
    drawn; the pitch line is added as a chain line), with hub, bore and keyway."""
    m = p["module"]; g = cq.Workplane("XY").circle(m * (z + 2) / 2).extrude(p["face"])
    g = g.union(cq.Workplane("XY").workplane(offset=p["face"]).circle(p["hub_d"] / 2).extrude(p["hub_len"]))
    b = p["shaft_d"] / 2 + p["bore_clear"]; return g.cut(cq.Workplane("XY").circle(b).extrude(p["face"] + p["hub_len"])).val()
VIEWS = {"front": ((0, -1, 0), (1, 0, 0)), "top": ((0, 0, 1), (1, 0, 0)), "left": ((-1, 0, 0), (0, -1, 0)), "iso": ((-1, -1, 1), (1, -1, 0)),
         "gear_face": ((0, -1, 0), (1, 0, 0)), "gear_side": ((-1, 0, 0), (0, -1, 0))}
def norm(v): l = math.sqrt(sum(c * c for c in v)); return tuple(c / l for c in v)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def to2d(view, p):
    n, vx = map(norm, VIEWS[view]); vy = cross(n, vx); return (sum(a * b for a, b in zip(p, vx)), sum(a * b for a, b in zip(p, vy)))
def polylines(compound):
    out = []
    if compound is None or compound.IsNull(): return out
    ex = TopExp_Explorer(compound, TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge_s(ex.Current()); c = BRepAdaptor_Curve(e)
        if c.GetType() == GeomAbs_Line: pts = [c.Value(c.FirstParameter()), c.Value(c.LastParameter())]
        else:
            d = GCPnts_QuasiUniformDeflection(c, 0.02); pts = [d.Value(i) for i in range(1, d.NbPoints() + 1)]
        out.append([(p.X(), p.Y()) for p in pts]); ex.Next()
    return out
def hlr(shape, view):
    n, vx = map(norm, VIEWS[view]); algo = HLRBRep_Algo(); algo.Add(shape.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*n), gp_Dir(*vx)))); algo.Update(); algo.Hide(); h = HLRBRep_HLRToShape(algo)
    vis = polylines(h.VCompound()) + polylines(h.OutLineVCompound()); hid = polylines(h.HCompound()) + polylines(h.OutLineHCompound())
    return vis, hid

class Sheet:
    """A3 landscape sheet in mm; views placed by (origin, scale); y up in model, down in SVG."""
    def __init__(self, title, number, of, scale_label, material="", part_no=""):
        self.el, self.title, self.no, self.of, self.scale_label, self.material, self.part_no = [], title, number, of, scale_label, material, part_no
    def view(self, shape, view, ox, oy, s, hidden=True, label=None, label_dy=9):
        vis, hid = hlr(shape, view); f = lambda x, y: (ox + s * x, oy - s * y)
        if hidden:
            for pl in hid: self.el.append(f'<polyline class="hid" points="{" ".join(f"{a:.2f},{b:.2f}" for a, b in (f(*p) for p in pl))}"/>')
        for pl in vis: self.el.append(f'<polyline class="vis" points="{" ".join(f"{a:.2f},{b:.2f}" for a, b in (f(*p) for p in pl))}"/>')
        if label:
            xs_ = [f(*p)[0] for pl in vis for p in pl]; ys_ = [f(*p)[1] for pl in vis for p in pl]
            self.text((min(xs_) + max(xs_)) / 2, max(ys_) + label_dy, label, 3.5, anchor="middle", cls="lbl")
        return f
    def line(self, a, b, cls="thin"): self.el.append(f'<line class="{cls}" x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}"/>')
    def text(self, x, y, t, size=3.5, anchor="start", cls="txt", rot=0):
        tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
        self.el.append(f'<text class="{cls}" x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}"{tr}>{t}</text>')
    def arrow(self, tip, frm):
        dx, dy = tip[0] - frm[0], tip[1] - frm[1]; l = math.hypot(dx, dy) or 1; ux, uy = dx / l, dy / l; L, W = 3.0, 0.9
        p1 = (tip[0] - ux * L - uy * W, tip[1] - uy * L + ux * W); p2 = (tip[0] - ux * L + uy * W, tip[1] - uy * L - ux * W)
        self.el.append(f'<polygon class="arr" points="{tip[0]:.2f},{tip[1]:.2f} {p1[0]:.2f},{p1[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}"/>')
    def dim(self, a, b, off, value=None, orient="h", txt=None):
        """Linear dimension between paper points a and b, dimension line offset by `off` mm (h: horizontal, v: vertical)."""
        if orient == "h":
            y = min(a[1], b[1]) - off if off > 0 else max(a[1], b[1]) - off
            self.line(a, (a[0], y + (1.5 if off > 0 else -1.5)), "ext"); self.line(b, (b[0], y + (1.5 if off > 0 else -1.5)), "ext")
            pa, pb = (a[0], y), (b[0], y); self.line((pa[0] - 0, y), (pb[0], y)); self.arrow(pa, pb); self.arrow(pb, pa)
            self.text((pa[0] + pb[0]) / 2, y - 1.2, txt or f"{value:g}", 3.5, "middle")
        else:
            x = max(a[0], b[0]) + off if off > 0 else min(a[0], b[0]) + off
            self.line(a, (x + (1.5 if off > 0 else -1.5), a[1]), "ext"); self.line(b, (x + (1.5 if off > 0 else -1.5), b[1]), "ext")
            pa, pb = (x, a[1]), (x, b[1]); self.line(pa, pb); self.arrow(pa, pb); self.arrow(pb, pa)
            self.text(x - 1.2, (pa[1] + pb[1]) / 2, txt or f"{value:g}", 3.5, "middle", rot=-90)
    def leader(self, tip, to, t):
        self.line(tip, to); self.arrow(tip, to); self.line(to, (to[0] + (len(t) * 2.0 + 2) * (1 if to[0] >= tip[0] else -1), to[1]))
        self.text(to[0] + (1 if to[0] >= tip[0] else -1) * 1.5, to[1] - 1.2, t, 3.5, "start" if to[0] >= tip[0] else "end")
    def centre(self, a, b): self.line(a, b, "ctr")
    def cross_mark(self, c, r): self.centre((c[0] - r, c[1]), (c[0] + r, c[1])); self.centre((c[0], c[1] - r), (c[0], c[1] + r))
    def table(self, x, y, rows, widths, h=6.5, head=True):
        for i, row in enumerate(rows):
            cx = x
            for j, (cell, w) in enumerate(zip(row, widths)):
                self.el.append(f'<rect class="{"th" if head and i == 0 else "td"}" x="{cx:.2f}" y="{y + i * h:.2f}" width="{w}" height="{h}"/>')
                self.text(cx + 1.8, y + i * h + h - 2, str(cell), 3.0, cls="txtb" if head and i == 0 else "txt"); cx += w
    def svg(self, path):
        x0, y0 = 240, 241                                                       # title block 170 x 46 at bottom right
        tb = [f'<rect class="frame" x="10" y="10" width="400" height="277"/>', f'<rect class="tb" x="{x0}" y="{y0}" width="170" height="46"/>']
        for yy in (y0 + 12, y0 + 24, y0 + 35): tb.append(f'<line class="thin" x1="{x0}" y1="{yy}" x2="{x0 + 170}" y2="{yy}"/>')
        tb.append(f'<line class="thin" x1="{x0 + 100}" y1="{y0 + 12}" x2="{x0 + 100}" y2="{y0 + 46}"/>')
        T = lambda x, y, t, s=3, c="txt": tb.append(f'<text class="{c}" x="{x}" y="{y}" font-size="{s}">{t}</text>')
        T(x0 + 3, y0 + 8.5, self.title, 5.2, "txtb"); T(x0 + 3, y0 + 19, f"Part no. {self.part_no}" if self.part_no else "Hand-cranked spur gear train", 3.2)
        T(x0 + 3, y0 + 30, f"Material: {self.material}" if self.material else "Materials: see BOM", 3.2); T(x0 + 3, y0 + 42, "General tolerances ISO 2768-m · dimensions in mm", 2.8)
        T(x0 + 103, y0 + 19, f"Scale {self.scale_label}", 3.2); T(x0 + 103, y0 + 30, f"Sheet {self.no} of {self.of} · A3", 3.2)
        T(x0 + 103, y0 + 42, f"Drawn: Priyanshu Sharan · {datetime.date(2026, 11, 6).isoformat()}", 2.6)
        # first-angle projection symbol
        sx, sy = 372, 236; tb += [f'<circle class="thin" cx="{sx + 22}" cy="{sy}" r="3.2"/>', f'<circle class="thin" cx="{sx + 22}" cy="{sy}" r="1.6"/>',
                                  f'<polygon class="thin" fill="none" points="{sx},{sy - 3.2} {sx + 12},{sy - 5.5} {sx + 12},{sy + 5.5} {sx},{sy + 3.2}"/>']
        tb.append(f'<text class="txt" x="{sx - 2}" y="{sy - 7.5}" font-size="2.6">First-angle projection</text>')
        style = ("<style>.vis{fill:none;stroke:#000;stroke-width:.5;stroke-linejoin:round}.hid{fill:none;stroke:#000;stroke-width:.25;stroke-dasharray:1.6 .9}"
                 ".thin{stroke:#000;stroke-width:.18;fill:none}.ext{stroke:#000;stroke-width:.18}.ctr{stroke:#000;stroke-width:.18;stroke-dasharray:6 1.2 1 1.2;fill:none}"
                 ".arr{fill:#000}.frame{fill:none;stroke:#000;stroke-width:.7}.tb{fill:none;stroke:#000;stroke-width:.5}.th{fill:#eee;stroke:#000;stroke-width:.25}.td{fill:none;stroke:#000;stroke-width:.25}"
                 "text{font-family:'DejaVu Sans',sans-serif;fill:#000}.txtb{font-weight:bold}.lbl{font-weight:bold;letter-spacing:.2px}</style>")
        open(path, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">{style}<rect width="420" height="297" fill="#fff"/>{"".join(tb)}{"".join(self.el)}</svg>')

def to_pdf(svgs, out):
    html = "".join(f'<div style="page-break-after:always;width:420mm;height:297mm"><img src="{os.path.abspath(s)}" style="width:420mm;height:297mm"></div>' for s in svgs)
    open("build/dw.html", "w").write(f"<html><body style='margin:0'>{html}</body></html>")
    js = "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://'+process.argv[2]);await p.waitForTimeout(400);" \
         "await p.pdf({path:process.argv[3],width:'420mm',height:'297mm',printBackground:true,margin:{top:0,bottom:0,left:0,right:0}});await b.close()})()"
    open("build/pdf.js", "w").write(js); subprocess.run(["node", "build/pdf.js", os.path.abspath("build/dw.html"), out], check=True)

if __name__ == "__main__":
    xs, (a1, a2) = centres(); S = shapes()
    # ---------------- sheet 1: side plate (the parametric sketch part)
    plate = S["plate"]; L = xs[-1] - xs[0] + 2 * P["plate_margin"] + 30; h, t, sh = P["plate_h"], P["plate_t"], P["shaft_height"]
    s1 = Sheet("SIDE PLATE", 1, 3, "1:1", "Aluminium 6061-T6, 6 mm plate", "GT-002"); sc = 1.0
    F = s1.view(plate, "front", 60 + L / 2, 125, sc, label="FRONT VIEW", label_dy=40)
    Tv = s1.view(plate, "top", 60 + L / 2, 175, sc, label="TOP VIEW")
    Lv = s1.view(plate, "left", 335, 125, sc, label="LEFT VIEW")
    for x in xs: s1.cross_mark(F(x, sh), 8)
    s1.centre(F(xs[0] - 12, sh), F(xs[-1] + 12, sh))
    s1.dim(F(-L / 2, 0), F(L / 2, 0), -14, L, "h"); s1.dim(F(-L / 2, 0), F(-L / 2, h), 14, txt=f"{h:g}", orient="v") if False else s1.dim(F(L / 2, 0), F(L / 2, h), 10, h, "v")
    s1.dim(F(xs[0], sh), F(xs[1], sh), h - sh + 8, a1, "h"); s1.dim(F(xs[1], sh), F(xs[2], sh), h - sh + 8, a2, "h")
    s1.dim(F(-L / 2, 0), F(xs[0], sh), -(xs[0] + L / 2) + 4, txt=f"{sh:g}", orient="v") if False else s1.dim(F(-L / 2, 0), F(-L / 2, sh), -8, sh, "v")
    s1.dim(F(-L / 2, 0), F(xs[0], 0), -24, xs[0] + L / 2, "h")
    s1.leader(F(xs[2] + P["shaft_d"] / 2 * .7, sh + P["shaft_d"] / 2 * .7), F(xs[2] + 22, sh + 22), f"3× Ø{P['shaft_d'] + .2:g} THRU")
    s1.leader(F(-L / 2 + 14 - 14 * .29, h - 14 + 14 * .96), F(-L / 2 - 4, h + 12), "R14 (2×)")
    sx1, sx2 = (xs[0] + xs[1]) / 2, (xs[1] + xs[2]) / 2
    s1.leader(F(sx2 + 8, 20), F(L / 2 + 16, 8), "2× slot 16 × 7 (R3.5 ends)")
    s1.dim(F(sx2, 20), F(sx2, 0), 4 + 20, 20, "v")
    s1.centre(F(sx1, 8), F(sx1, 32)); s1.centre(F(sx2, 8), F(sx2, 32))
    s1.text(F(sx1, 0)[0], F(sx1, 0)[1] - 30, f"slot centres midway between bores ({(xs[0] + xs[1]) / 2 - xs[0]:g} / {(xs[1] + xs[2]) / 2 - xs[1]:g} from bores 1, 2)", 2.6, "middle") if False else None
    s1.dim(Tv(-L / 2, 0), Tv(-L / 2, t), -8, t, "v")
    s1.text(30, 262, "Bore centres follow the gear centre distances a = m(z₁ + z₂)/2 = 40 and 65 mm (module 2; z = 15, 25, 40).", 3.0)
    s1.text(30, 268, "Bores Ø8.2 give 0.1 mm radial running clearance on the Ø8 shafts. Slot centres midway between bores. Break sharp edges 0.3 × 45°.", 3.0)
    s1.svg("drawings/01-side-plate.svg")
    # ---------------- sheet 2: output gear
    z = P["z_out"]; m = P["module"]; g = S["gear_out"]
    s2 = Sheet("SPUR GEAR z = 40", 2, 3, "1.4:1", "Brass CW614N", "GT-005")
    gF = s2.view(g.rotate(cq.Vector(), cq.Vector(1, 0, 0), 90), "gear_face", 120, 130, 1.4, hidden=False, label="FACE VIEW (1.4 : 1)", label_dy=28)
    gc = conventional_gear(z).rotate(cq.Vector(), cq.Vector(1, 0, 0), 90)
    gS = s2.view(gc, "gear_side", 250, 130, 1.4, label="SIDE VIEW (1.4 : 1, conventional)", label_dy=28)
    s2.centre(gS(4, m * z / 2), gS(-P["face"] - 4, m * z / 2)); s2.centre(gS(4, -m * z / 2), gS(-P["face"] - 4, -m * z / 2)); s2.centre(gS(6, 0), gS(-P["face"] - P["hub_len"] - 6, 0))
    s2.dim(gS(0, -(m * z / 2 + m)), gS(-P["face"], -(m * z / 2 + m)), -8, P["face"], "h")
    s2.dim(gS(0, -(m * z / 2 + m)), gS(-P["face"] - P["hub_len"], -(m * z / 2 + m)), -18, P["face"] + P["hub_len"], "h")
    s2.dim(gS(-P["face"] - P["hub_len"], P["hub_d"] / 2), gS(-P["face"] - P["hub_len"], -P["hub_d"] / 2), 10, txt=f"Ø{P['hub_d']:g}", orient="v")
    c = gF(0, 0); s2.cross_mark(c, 64)
    s2.el.append(f'<circle class="ctr" cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{1.4 * m * z / 2:.2f}"/>')
    s2.leader(gF(m * z / 2 * .707, m * z / 2 * .707), gF(58, 58), f"PCD Ø{m * z:g}")
    s2.dim(gF(-(m * z / 2 + m), 0), gF(m * z / 2 + m, 0), -(1.4 * (m * z / 2 + m)) - 8, txt=f"Ø{m * (z + 2):g}", orient="h")
    s2.leader(gF(0, -(P["shaft_d"] / 2 + .05)), gF(-30, -50), f"Ø{P['shaft_d'] + .05:g} bore, keyway {P['key_w']:g} × {P['key_h']:g}")
    yz = lambda y_, zz: gS(-y_, zz)
    s2.dim(gS(0, -(m * z / 2 + m)), gS(-P["face"], -(m * z / 2 + m)), -10, P["face"], "h") if False else None
    rim_in, hub_out = m * z / 2 - 1.25 * m - 4, P["hub_d"] / 2 + 3; rc = (rim_in + hub_out) / 2; dh = min(rim_in - hub_out - 4, 16)
    s2.leader(gF(rc * math.cos(math.radians(-72)) + dh / 2 * .7, rc * math.sin(math.radians(-72)) - dh / 2 * .7), gF(40, -58), f"5× Ø{dh:g} equally spaced on Ø{2 * rc:g}")
    s2.text(30, 268, f"Web 3 mm thick between hub and rim (recess Ø{2 * rim_in:g} × {P['face'] - 3:g} deep from the hub side). Teeth: tip and root edges unbroken.", 3.0)
    s2.table(300, 40, [["GEAR DATA", ""], ["Module m", f"{m:g}"], ["Number of teeth z", f"{z}"], ["Pressure angle", f"{P['pressure_angle']:g}°"], ["Pitch circle Ø", f"{m * z:g}"],
                       ["Tip circle Ø", f"{m * (z + 2):g}"], ["Root circle Ø", f"{m * z - 2.5 * m:g}"], ["Face width", f"{P['face']:g}"], ["Backlash (tooth thickness)", f"{P['backlash']:g}"],
                       ["Mates with", f"idler z = {P['z_idler']} at a = {a2:g}"]], [62, 44])
    s2.text(30, 262, "Involute profile generated from first principles (src/parts.py); verified with zero overlap through a full mesh cycle (results/mesh-check.json).", 3.0)
    s2.svg("drawings/02-output-gear.svg")
    # ---------------- sheet 3: assembly with exploded view, BOM and balloons
    Sc = dict(S); Sc.update({"gear_in": conventional_gear(P["z_in"]), "gear_idler": conventional_gear(P["z_idler"]), "gear_out": conventional_gear(P["z_out"])})
    A = build(0, 0, Sc); comp = cq.Compound.makeCompound([shp for _, shp in A.values()])
    s3 = Sheet("GEAR TRAIN ASSEMBLY", 3, 3, "1:2", part_no="GT-000"); k = 0.5
    aF = s3.view(comp, "front", 85, 105, k, hidden=False, label="FRONT VIEW", label_dy=22); aT = s3.view(comp, "top", 85, 172, k, hidden=False, label="TOP VIEW")
    s3.dim(aF(-P["base_l"] / 2, 0), aF(P["base_l"] / 2, 0), -10, P["base_l"], "h")
    s3.dim(aF(P["base_l"] / 2, 0), aF(P["base_l"] / 2, P["base_t"] + sh), 6, P["base_t"] + sh, "v")
    top_z = P["base_t"] + sh + P["module"] * (P["z_out"] + 2) / 2
    s3.dim(aF(-P["base_l"] / 2, 0), aF(-P["base_l"] / 2, top_z), -6, round(top_z, 1), "v")
    s3.dim(aF(xs[0], top_z), aF(xs[1], top_z), 6, a1, "h"); s3.dim(aF(xs[1], top_z), aF(xs[2], top_z), 6, a2, "h")
    E = build(0, 1.0, S); compE = cq.Compound.makeCompound([shp for _, shp in E.values()]); kE = 0.42
    iso = s3.view(compE, "iso", 262, 112, kE, hidden=False, label="EXPLODED ISOMETRIC VIEW", label_dy=42)
    bom = json.load(open("results/assembly.json"))["bom"]; item = {b["part"]: i + 1 for i, b in enumerate(bom)}
    pts = {}
    for n, (part, shp) in E.items():
        if part not in pts: pts[part] = iso(*to2d("iso", shp.Center().toTuple()))
    cx = sum(p[0] for p in pts.values()) / len(pts); cy = sum(p[1] for p in pts.values()) / len(pts)
    order = sorted(pts, key=lambda q: math.atan2(pts[q][1] - cy, pts[q][0] - cx)); angs = [math.atan2(pts[q][1] - cy, pts[q][0] - cx) for q in order]
    for _ in range(50):                                                          # spread balloons to at least 24 deg apart
        for i in range(len(angs)):
            j = (i + 1) % len(angs); d = (angs[j] - angs[i]) % (2 * math.pi)
            if d < math.radians(24): angs[i] -= math.radians(1); angs[j] += math.radians(1)
    for q, a in zip(order, angs):
        px, py = pts[q]; bx, by = cx + 92 * math.cos(a), cy + 70 * math.sin(a)
        s3.line((px, py), (bx, by)); s3.el.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r=".7" fill="#000"/><circle class="thin" cx="{bx:.2f}" cy="{by:.2f}" r="4" fill="#fff"/>')
        s3.text(bx, by + 1.3, str(item[q]), 3.6, "middle", "txtb")
    names = {"base": "Base plate", "plate": "Side plate", "shaft": "Shaft Ø8 × 74", "shaft_in": "Input shaft Ø8 × 86", "gear_in": "Spur gear z15", "gear_idler": "Idler gear z25",
             "gear_out": "Spur gear z40", "collar": "Shaft collar", "crank": "Hand crank"}
    rows = [["ITEM", "PART", "QTY", "MATERIAL", "MASS g"]] + [[item[b["part"]], names[b["part"]], b["qty"], b["material"].replace("_", " "), b["mass_g_each"]] for b in bom]
    s3.table(30, 236, rows, [12, 40, 11, 42, 16], h=5.0)
    s3.svg("drawings/03-assembly.svg")
    to_pdf(["drawings/01-side-plate.svg", "drawings/02-output-gear.svg", "drawings/03-assembly.svg"], "drawings/gear-train-drawings.pdf"); print("drawings done")
