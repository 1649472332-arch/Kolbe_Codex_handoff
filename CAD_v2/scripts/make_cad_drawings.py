"""Create BREP-derived drawing sheets, TechDraw source documents and DXFs.

Run with the bundled system Python 3.12. This script invokes the bundled
FreeCAD Python for native projection/TechDraw work, then creates SVG/PDF sheets
from those exact OCC/TechDraw projections. Part documents are read only.
"""
from __future__ import annotations
import json, math, os, re, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAW = ROOT / "drawings"
RENDER = ROOT / "renders" / "drawing QA"
PARTS = ROOT / "parts"
FREECAD_PY = Path(r"C:\Users\16494\AppData\Local\Programs\FreeCAD 1.1\bin\python.exe")
SYSTEM_PY = Path(r"C:\Users\16494\AppData\Local\Programs\Python\Python312\python.exe")
MAJOR = ["KF-101", "KP-101", "KP-102", "KP-201", "KP-202", "KP-203", "KP-204", "KP-601", "KP-602"]
HARDWARE = ["KB-A3", "KB-C3", "KB-A5", "KB-C5", "KB-A7", "KB-C7", "KB-801", "KB-802", "KH-901", "KH-902", "KS-101", "KS-102"]
ACTIVE_SUPPORT = ["KP-301", "KP-501", "KP-502", "KP-503"]
ALL_PARTS = MAJOR + ACTIVE_SUPPORT + HARDWARE  # KP-302/303/401 are superseded/unused.
NATIVE_CODES = MAJOR + HARDWARE
DXF_CODES = MAJOR + HARDWARE
ASSEMBLIES = [3, 5, 7]
SHEET = (420.0, 297.0)  # A3 landscape, millimetres

def ensure_dirs():
    DRAW.mkdir(parents=True, exist_ok=True)
    RENDER.mkdir(parents=True, exist_ok=True)

def xml(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))

def freecad_stage():
    import FreeCAD as App
    import Part, TechDraw
    V = App.Vector
    def projected_bounds(shape, direction):
        projected=TechDraw.projectEx(shape,direction)
        boxes=[obj.BoundBox for obj in projected if not obj.isNull()]
        if not boxes: raise RuntimeError("TechDraw returned no projected geometry")
        return [min(b.XMin for b in boxes),min(b.YMin for b in boxes),max(b.XMax for b in boxes),max(b.YMax for b in boxes)]
    basis = json.loads((ROOT / "design_basis.json").read_text(encoding="utf-8"))
    mech = json.loads((ROOT / "validation" / "mechanical_parts.json").read_text(encoding="utf-8"))
    mech_parts = {p["code"]: p for p in mech["parts"]}
    hardware = json.loads((ROOT / "validation" / "hardware_parts.json").read_text(encoding="utf-8"))
    hardware_parts = {p["code"]: p for p in hardware["parts"]}
    flow = json.loads((ROOT / "validation" / "flow_parts.json").read_text(encoding="utf-8"))
    meta = {p["code"]: p for p in mech["parts"]}
    meta.update(hardware_parts)
    meta["KF-101"] = {"material": flow["active_part"]["material"], "dimensions": flow["active_part"]}
    codes = [c for c in ALL_PARTS if (PARTS / (c + ".FCStd")).exists()]
    svg_views = {}
    for code in codes:
        src = App.openDocument(str(PARTS / (code + ".FCStd")))
        source = next((o for o in src.Objects if o.TypeId == "PartDesign::Body" and hasattr(o, "Shape") and not o.Shape.isNull()), None)
        if source is None:
            source = next((o for o in src.Objects if hasattr(o, "Shape") and not o.Shape.isNull() and len(o.Shape.Solids) == 1), None)
        if source is None:
            raise RuntimeError(f"No solid body found in {code}")
        shape = source.Shape.copy()
        if not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError(f"Invalid source BREP for {code}: valid={shape.isValid()} solids={len(shape.Solids)}")
        # Tight axis-aligned extents are used for dimension values; ordinary OCC BoundBox
        # can be loose on swept/torus surfaces (notably KS-101/KS-102).
        bb = shape.optimalBoundingBox()
        views = {"front": V(0, 0, 1), "side": V(1, 0, 0), "iso": V(1, -1, 1)}
        section = shape.section(Part.Plane(V(0, 0, (bb.ZMin + bb.ZMax) / 2.0), V(0, 1, 0)))
        if section.isNull() or not section.Edges:
            raise RuntimeError(f"No BREP section generated for {code}")
        svg_views[code] = {"bbox": [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax],
                          "volume_mm3": shape.Volume,
                          "material": meta.get(code, {}).get("material", "TBD"),
                          "views": {key: TechDraw.projectToSVG(shape, direction) for key, direction in views.items()},
                          "view_bounds": {key: projected_bounds(shape,direction) for key,direction in views.items()},
                          "section": TechDraw.projectToSVG(section, V(0, -1, 0)),
                          "section_bounds": projected_bounds(section,V(0,-1,0)),
                          "top_dxf": TechDraw.projectToDXF(shape, V(0, 0, 1))}
        # Native TechDraw document: source BREP is retained in the copied document;
        # orthographic and isometric views are live DrawViewPart objects.
        if code in NATIVE_CODES:
            page = src.addObject("TechDraw::DrawPage", "DrawingPage")
            page.Label = f"{code} BREP Drawing - Rev B1"
            template_path = DRAW / "A3_landscape_template.svg"
            template = src.addObject("TechDraw::DrawSVGTemplate", "DrawingTemplate")
            template.Template = str(template_path)
            page.Template = template
            page.Scale = 1.0
            native_front=min(4.0,126.0/max(bb.XLength,bb.YLength,1))
            native_side=min(3.0,55.0/max(bb.YLength,bb.ZLength,1))
            native_iso=min(3.0,70.0/max(bb.XLength,bb.YLength,bb.ZLength,1))
            native_section=min(.7 if code in HARDWARE else 3.0,55.0/max(bb.XLength,bb.ZLength,1))
            view_specs = [("Front", V(0,0,1), 110, 150, native_front),
                          ("Side", V(1,0,0), 265, 170, native_side),
                          ("Isometric", V(1,-1,1), 350, 165, native_iso)]
            for name, direction, x, y, scale in view_specs:
                view = src.addObject("TechDraw::DrawViewPart", "View" + name)
                view.Source = [source]
                view.Direction = direction
                view.ScaleType = 0
                view.Scale = scale
                key={"Front":"front","Side":"side","Isometric":"iso"}[name]
                pb=svg_views[code]["view_bounds"][key]
                view.X, view.Y = x - (pb[0]+pb[2])*.5*scale, y + (pb[1]+pb[3])*.5*scale
                view.Label = name
                page.addView(view)
            secfeat=src.addObject("Part::Feature", "SectionCutBREP")
            secfeat.Label=f"{code} BREP section, Y=0, Z={(bb.ZMin+bb.ZMax)/2:g}"
            secfeat.Shape=section
            secview=src.addObject("TechDraw::DrawViewPart", "SectionView")
            secview.Source=[secfeat]
            secview.Direction=V(0,-1,0)
            sb=svg_views[code]["section_bounds"]
            secview.ScaleType=0; secview.Scale=native_section
            secview.X=(220 if code in HARDWARE else 265) - (sb[1]+sb[3])*.5*native_section
            secview.Y=118 + (sb[0]+sb[2])*.5*native_section
            secview.Label="SECTION A-A (BREP cut at Y=0)"
            page.addView(secview)
            src.recompute()
            native_path = DRAW / f"{code}_drawing.FCStd"
            src.saveAs(str(native_path))
            # FreeCAD writes a sibling backup when regenerating; drawings/ contains deliverables only.
            backup = native_path.with_suffix(".FCBak")
            if backup.exists(): backup.unlink()
            for backup in DRAW.glob(native_path.stem + ".*.FCBak"):
                backup.unlink()
        App.closeDocument(src.Name)
    # Current 3/5/7-layer assemblies: projection views come from the assembled BREP compound.
    for count in ASSEMBLIES:
        asm_path = ROOT / "assemblies" / f"Kolbe_{count}.FCStd"
        val_path = ROOT / "validation" / f"assembly_{count}.json"
        if not asm_path.exists() or not val_path.exists():
            continue
        asm = App.openDocument(str(asm_path))
        stack = asm.getObject("Stack")
        if stack is None or not hasattr(stack, "Shape") or stack.Shape.isNull():
            raise RuntimeError(f"No assembled BREP Stack in {asm_path.name}")
        shape = stack.Shape.copy()
        bb = shape.optimalBoundingBox()
        section = shape.section(Part.Plane(V(0, 0, (bb.ZMin + bb.ZMax) / 2.0), V(0, 1, 0)))
        if section.isNull() or not section.Edges:
            raise RuntimeError(f"No assembly section generated for {count}-layer stack")
        asm_val = json.loads(val_path.read_text(encoding="utf-8"))
        key = f"ASSEMBLY-{count}"
        svg_views[key] = {"bbox": [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax],
                          "volume_mm3": shape.Volume,
                          "instances": asm_val.get("instances"),
                          "body_stack_height_mm": asm_val.get("body_stack_height_mm"),
                          "active_stack_height_mm": asm_val.get("active_stack_height_mm"),
                          "parts": asm_val.get("parts", []),
                          "views": {"front": TechDraw.projectToSVG(shape, V(0,0,1)),
                                    "side": TechDraw.projectToSVG(shape, V(1,0,0)),
                                    "iso": TechDraw.projectToSVG(shape, V(1,-1,1))},
                          "view_bounds": {"front":projected_bounds(shape,V(0,0,1)),"side":projected_bounds(shape,V(1,0,0)),"iso":projected_bounds(shape,V(1,-1,1))},
                          "section": TechDraw.projectToSVG(section,V(0,-1,0)),
                          "section_bounds":projected_bounds(section,V(0,-1,0))}
        App.closeDocument(asm.Name)
    (RENDER / "brep_projection_data.json").write_text(json.dumps(svg_views, ensure_ascii=False), encoding="utf-8")

def svg_text(x, y, txt, size=3.1, color="#162331", weight="normal", anchor="start", family="Microsoft YaHei, Arial, sans-serif"):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" font-size="{size:.2f}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{xml(txt)}</text>'

def centered_projection(svg, bounds, cx, cy, scale, rotate=False):
    xmid=(bounds[0]+bounds[2])*.5; ymid=(bounds[1]+bounds[3])*.5
    # Keep CAD pen weight visually constant when a small part is enlarged on sheet.
    svg=svg.replace('stroke-width="1.0"',f'stroke-width="{.35/max(scale,1e-6):.6f}"')
    if rotate:
        tx=cx-scale*ymid; ty=cy-scale*xmid
        transform=f"translate({tx:.4f},{ty:.4f}) scale({scale:.7f}) rotate(90)"
    else:
        tx=cx-scale*xmid; ty=cy+scale*ymid
        transform=f"translate({tx:.4f},{ty:.4f}) scale({scale:.7f})"
    return f'<g transform="{transform}">{svg}</g>'

def scale_note(scale):
    return f"{scale:.1f}:1" if scale>=1.0 else f"1:{1.0/scale:.1f}"

def line(x1,y1,x2,y2,stroke="#526171",sw=.25,dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{stroke}" stroke-width="{sw}"{d}/>'

def dim_h(x1,x2,y, label, ext_y1=None, ext_y2=None):
    a=[]
    if ext_y1 is not None: a.append(line(x1,ext_y1,x1,y+1.4))
    if ext_y2 is not None: a.append(line(x2,ext_y2,x2,y+1.4))
    a.append(line(x1,y,x2,y,"#246B8E",.35))
    a += [f'<path d="M{x1:.2f},{y:.2f} l2,-1 l0,2 z M{x2:.2f},{y:.2f} l-2,-1 l0,2 z" fill="#246B8E"/>', svg_text((x1+x2)/2,y-1.2,label,2.8,"#14526F","bold","middle")]
    return "".join(a)

def dim_v(x,y1,y2,label,ext_x1=None,ext_x2=None):
    a=[]
    if ext_x1 is not None: a.append(line(ext_x1,y1,x+1.4,y1))
    if ext_x2 is not None: a.append(line(ext_x2,y2,x+1.4,y2))
    a.append(line(x,y1,x,y2,"#246B8E",.35))
    a += [f'<path d="M{x:.2f},{y1:.2f} l-1,2 l2,0 z M{x:.2f},{y2:.2f} l-1,-2 l2,0 z" fill="#246B8E"/>', svg_text(x-1,(y1+y2)/2,label,2.8,"#14526F","bold","middle")]
    return "".join(a)

def part_info(code, basis, flow, mech, hardware):
    if code == "KF-101":
        f=flow["active_part"]
        return f["material"], ["150 x 150 x 6; R5 frame", "50 x 50 wet window, R3; no headers", "Main seal groove: 1.4 wide x 0.75 deep each face", "2 x D8 manifolds at (0, +/-62); mean D14 seal groove", "Buried branches D2.2 at Z3; plugged M4 access at Y +/-75", "Bolt clearance: 8 x D9 at +/-65, Y +/-20/55; locator round + slot"], "PVDF provisional; chemistry/pressure and sealing qualification pending"
    if code in {p["code"] for p in hardware["parts"]}:
        hitem=next(p for p in hardware["parts"] if p["code"]==code)
        hd=hardware.get("dimensions",{}).get(code,{})
        material=hitem.get("material","TBD")
        if code.startswith("KB-A") or code.startswith("KB-C"):
            fingers=hd.get("finger_indices",[])
            side="A positive-X" if code.startswith("KB-A") else "C negative-X"
            zline=f"2 x M4x0.7 tapped cross-holes, core Ø3.3, through the 6 mm spine along X at Z=1 and H-3"
            features=[f"{code[-1]}-layer {side} copper comb; 6 x 8 spine section",
                      f"Finger indices i={','.join(map(str,fingers))}; active height {hd.get('active_height','TBD')} mm; layer pitch 6.35",
                      f"Finger blank 34 x 8 x 2; through-hole Ø4.5 along Z at X={'90' if code.startswith('KB-A') else '-90'}",
                      zline]
            status="Copper grade TBD; allowable current rating not established; beam cross-section preliminary"
        elif code in ("KB-801","KB-802"):
            rear=code.endswith("802")
            post_top=31.5 if not rear else 25
            hole_z=27 if not rear else 21
            features=["Foot 70 x 60 x 5; 2 x Ø9 tie-rod clearance through at (65, +/-20)",
                      f"Post section 7 x 12; Z=-0.5..{post_top:g}; transverse comb hole Ø4.5 at Y=0, Z={hole_z:g}",
                      "Fixing holes align with existing M8 tie-rod stack; no separate clamp/strap fastener",
                      "Rear bracket assembly transform: flip 180 deg about X, then translate to stack height" if rear else "Front bracket in native coordinates; align A/C comb support cross-hole"]
            status="PEEK grade TBD; preliminary cantilever; structural qualification pending"
        elif code=="KH-901":
            features=["Axis global +Y; M4x0.7 nominal smooth Ø3.3 envelope x 6 long",
                      "Low-profile head Ø5.5 x 2; driver slot 1.0 wide x 0.8 deep",
                      "Thread is a smooth nominal envelope; helical thread is not modeled",
                      "Fit/seal compatibility with plugged manufacturing access requires qualification"]
            status="316L exact grade and thread fit TBD; no vendor certification implied"
        elif code=="KH-902":
            features=["Washer OD5.5 / ID4.2 x 0.5 thick", "Used beneath KH-901 plug head", "Stock/material and sealing fit TBD"]
            status="Washer stock and sealing fit TBD"
        elif code=="KS-101":
            features=["Closed rounded-square seal centerline 53.6 x 53.6; centerline R4.8",
                      "Free cross-section diameter Ø1.0 (diameter, not radius)",
                      "Centerline path corresponds to the KF-101 main groove; installed squeeze not assigned"]
            status="Elastomer compound, hardness, compression and chemical compatibility TBD"
        else:  # KS-102
            features=["Circular seal mean/centerline diameter Ø14.0", "Free cross-section diameter Ø1.5 (diameter, not radius)",
                      "For paired axial manifold seal grooves; installed squeeze not assigned"]
            status="Elastomer compound, hardness, compression and chemical compatibility TBD"
        return material,features,status
    item=next((p for p in mech["parts"] if p["code"]==code),{})
    d=mech.get("dimensions",{}).get(code,{})
    material=item.get("material","TBD")
    # Keep concise, high-value nominal feature data from the frozen design basis.
    summaries={
      "KP-101":["56 x 56 x 0.35 coupon; R2 corners", "A-side dry tab to +X; width 16; tip X=100", "D4.5 tab hole at X=90; no manifold or locator holes", "Wet-window / coupon footprint ratio: 79.56%; tab excluded"],
      "KP-102":["56 x 56 x 0.35 coupon; R2 corners", "C-side dry tab to -X; width 16; tip X=-100", "D4.5 tab hole at X=-90; no manifold or locator holes", "Wet-window / coupon footprint ratio: 79.56%; tab excluded"],
      "KP-201":["150 x 150 x 12 endplate; R5", "8 x D9 through bolt clearance", "2 x D12 tool-access through holes at (0, +/-62)", "2 x D3.2 x 3 deep inner locator blind holes"],
      "KP-202":["150 x 150 x 14 front insulator; R5", "8 x D9 bolts + 2 x D3.2 through locators", "6 front ports at X=+/-32.5, +/-19.5, +/-6.5; M6x1 nominal envelope", "Port stack: D6 x 8; D3.4 seat x 2; D2.2 pilot x 1; inner grooves mean D14 x 2.2W x 1.1 deep"],
      "KP-203":["150 x 150 x 6 rear insulator; R5", "8 x D9 bolt holes + 2 x D3.2 through locator holes", "Inner face (Z0): 2 x D8 x 2 blind manifolds", "2 x annular grooves mean D14, 2.2 wide x 1.1 deep"],
      "KP-204":["150 x 150 x 12 rear endplate; R5", "8 x D9 through bolt clearance", "No fluid-access holes", "2 x D3.2 x 3 deep inner locator blind holes"],
      "KP-601":["150 x 150 x 0.35 PEEK carrier film", "56.10 aperture, R2.05; terminal slot W16.10 to +X", "2 x D8 manifold holes at (0, +/-62)", "8 x D9 bolts; 2 x D3.2 locator holes; thickness tolerance provisional +/-0.01"],
      "KP-602":["150 x 150 x 0.35 PEEK carrier film", "56.10 aperture, R2.05; terminal slot W16.10 to -X", "2 x D8 manifold holes at (0, +/-62)", "8 x D9 bolts; 2 x D3.2 locator holes; thickness tolerance provisional +/-0.01"],
      "KP-301":["16 x 16 x 3 clamp jaw; R1", "D4.5 through hole", "Material: PEEK unfilled (provisional)"],
      "KP-302":["Contact terminal: 6 x 20 section x 60 long", "2 x D4.5 through fixings, 52 center spacing", "Copper, grade TBD"],
      "KP-303":["28 x 8 x 1 copper strap", "2 x D4.5 holes at X=+/-9", "End margin 2.75 nominal; temper TBD"],
      "KP-401":["D3 x 60 locating pin", "Material: PEEK unfilled, grade TBD"],
      "KP-501":["M6x1 nominal smooth envelope, D6 x 8 long", "Head D9 x 7; bore D3.1 through", "Thread is not modeled helically; 316L stainless"],
      "KP-502":["Compression seal: OD3.4 x 2 long", "Modeled bore D3.0; free-state bore D2.95", "PTFE supplier/fit TBD"],
      "KP-503":["Tube OD3 / ID1.6 x 35 long", "PTFE; chemistry and pressure suitability TBD"]}
    return material, summaries.get(code,[d.get("outer",d.get("size",d.get("coupon","See model"))),"See source BREP geometry","Nominal dimensions in mm; tolerance not assigned"]), item.get("material", "Material specification TBD")

def make_sheet(code, dataset, basis, flow, mech, hardware, chinese=False):
    data=dataset[code]; bb=data["bbox"]
    xmin,ymin,zmin,xmax,ymax,zmax=bb
    sx,sy,sz=xmax-xmin,ymax-ymin,zmax-zmin
    front_bounds=data["view_bounds"]["front"]  # projection extents are for layout only
    front_w=sx; front_h=sy  # dimensions use BREP optimalBoundingBox, not projected curve extents
    span=max(front_w,front_h)
    scale=min(4.0, 126.0/max(span,1))
    cx,cy=108.0,151.0
    # Three OCC hidden-line projections, with model coordinates preserved in SVG transforms.
    front=centered_projection(data["views"]["front"],data["view_bounds"]["front"],cx,cy,scale)
    # Side & isometric receive independent scale/position to suit their extents.
    side_bounds=data["view_bounds"]["side"]
    side_scale=min(3.0,48.0/max(side_bounds[2]-side_bounds[0],side_bounds[3]-side_bounds[1],1))
    side=centered_projection(data["views"]["side"],data["view_bounds"]["side"],265,170,side_scale)
    iso_bounds=data["view_bounds"]["iso"]
    iso_scale=min(3.0,60.0/max(iso_bounds[2]-iso_bounds[0],iso_bounds[3]-iso_bounds[1],1))
    iso=centered_projection(data["views"]["iso"],data["view_bounds"]["iso"],350,165,iso_scale)
    sec_bounds=data["section_bounds"]
    section_cap=.7 if code in HARDWARE else 3.0
    sec_scale=min(section_cap,48.0/max(sec_bounds[2]-sec_bounds[0],sec_bounds[3]-sec_bounds[1],1))
    section_cx=220 if code in HARDWARE else 265
    section=centered_projection(data["section"],data["section_bounds"],section_cx,118,sec_scale,True)
    material,features,status=part_info(code,basis,flow,mech,hardware)
    code_name=translate_chinese(code)
    c=[]
    c.append('<rect x="0" y="0" width="420" height="297" fill="white"/>')
    c.append('<rect x="8" y="8" width="404" height="281" rx="1" fill="none" stroke="#243647" stroke-width=".55"/>')
    c.append(svg_text(12,17,"KOLBE ELECTROCHEMICAL CELL  /  PROVISIONAL DESIGN REVIEW",3.2,"#607283","bold"))
    c.append(svg_text(408,17,"REV B1   |   DIMENSIONS mm",2.8,"#607283","bold","end"))
    c.append(line(12,21,408,21,"#243647",.45))
    c.append(svg_text(12,30, f"{code}  |  {code_name}",7,"#162331","bold"))
    c.append(svg_text(12,36,"BREP-derived orthographic projections   |   First-angle orientation   |   Not for manufacture",2.8,"#435464"))
    # model views
    c.append(front)
    c.append(side)
    c.append(iso)
    c.append(section)
    c.append(svg_text(108,231,f"PLAN / FRONT  ({scale_note(scale)})",2.6,"#435464","bold","middle"))
    c.append(svg_text(265,202,f"SIDE / 侧视  ({scale_note(side_scale)})",2.6,"#435464","bold","middle"))
    c.append(svg_text(350,203,f"ISOMETRIC / 轴测  ({scale_note(iso_scale)})",2.6,"#435464","bold","middle"))
    c.append(svg_text(section_cx,138,f"SECTION A-A / 剖视  (Y=0, Z={(zmin+zmax)/2:g})",2.6,"#435464","bold","middle"))
    # Overall dimensions in the plan projection. Include overall metal tabs where applicable.
    # Dimensions follow the centered BREP projection even when source geometry is offset from global origin.
    left=cx-front_w*scale/2; right=cx+front_w*scale/2
    top=cy-front_h*scale/2; bottom=cy+front_h*scale/2
    c.append(line(left,cy,right,cy,"#B14B27",.25,"1.4 1.0"))
    c.append(svg_text(left,cy-1.2,"A",2.4,"#9B4B2A","bold","middle"))
    c.append(svg_text(right,cy-1.2,"A",2.4,"#9B4B2A","bold","middle"))
    if right-left > 12:
        c.append(dim_h(left,right,max(bottom+4,218),f"{front_w:g} O/A",bottom,bottom))
    if bottom-top > 12:
        c.append(dim_v(max(20,left-9),top,bottom,f"{front_h:g} O/A",left,left))
    # feature schedule
    c.append(line(12,55,408,55,"#243647",.4))
    c.append(svg_text(12,62,"FEATURE / DIMENSION SCHEDULE  |  特征尺寸表",3.4,"#162331","bold"))
    rowy=69
    for i,text in enumerate(features[:5]):
        c.append(svg_text(14,rowy+5.0*i, f"{i+1:02d}  {text}",2.75,"#243647"))
    # materials, tolerance/status block
    c.append(line(256,58,256,92,"#B4C0CA",.3))
    c.append(svg_text(262,62,"MATERIAL / 材料",2.8,"#607283","bold"))
    c.append(svg_text(262,68,material,2.7,"#243647"))
    c.append(svg_text(262,76,"TOLERANCES / 公差",2.8,"#607283","bold"))
    c.append(svg_text(262,82,"Unspecified unless individually stated; confirm before release.",2.45,"#243647"))
    c.append(svg_text(262,90,status,2.2,"#9B4B2A"))
    # A3 title block
    c.append('<rect x="12" y="260" width="396" height="22" fill="#F5F7F8" stroke="#526171" stroke-width=".35"/>')
    c.append(line(250,260,250,282,"#526171",.3)); c.append(line(322,260,322,282,"#526171",.3)); c.append(line(366,260,366,282,"#526171",.3))
    c += [svg_text(15,267,"ASSEMBLY",2.3,"#607283","bold"), svg_text(15,276,"Compact plate-press cell",3.0,"#162331"),
          svg_text(253,267,"PART / DRAWING",2.3,"#607283","bold"),svg_text(253,277,f"{code} / DWG-{code}",3.0,"#162331","bold"),
          svg_text(325,267,"SCALE / 比例",2.3,"#607283","bold"),svg_text(325,277,"See each view; dimensions govern",2.2,"#162331"),
          svg_text(369,267,"STATUS",2.3,"#607283","bold"),svg_text(369,277,"REVIEW",3.0,"#9B4B2A","bold")]
    if code.startswith("KB-A") or code.startswith("KB-C"):
        footer="Copper grade/current rating unconfirmed; finger beam section is preliminary. No current capacity assigned."
    elif code in ("KB-801","KB-802"):
        footer="PEEK support is a preliminary cantilever; structural qualification pending."
    elif code.startswith("KH-"):
        footer="Thread/washer fit and plug sealing require qualification; thread is not modeled helically."
    elif code.startswith("KS-"):
        footer="Elastomer compound, hardness, compression and chemical compatibility remain TBD."
    else:
        footer="GAP 6 mm IS A REVIEW ENVELOPE ONLY; FINAL ELECTRODE/GAP/FLOW ARE TBD. No pressure rating or final torque assigned."
    c.append(svg_text(12,253,footer,2.55,"#9B4B2A","bold"))
    return '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="420mm" height="297mm" viewBox="0 0 420 297">' + "".join(c) + "</svg>"

def make_assembly_sheet(key, dataset, validation, basis):
    data=dataset[key]; n=int(key.split("-")[1]); bb=data["bbox"]
    xmin,ymin,zmin,xmax,ymax,zmax=bb; sx,sy,sz=xmax-xmin,ymax-ymin,zmax-zmin
    front_scale=min(.48,135/max(sx,sy,1))
    side_scale=min(.32,55/max(sy,sz,1))
    iso_scale=min(.24,70/max(sx,sy,sz,1))
    sec_scale=min(.20,55/max(sx,sz,1))
    front=centered_projection(data["views"]["front"],data["view_bounds"]["front"],112,151,front_scale)
    side=centered_projection(data["views"]["side"],data["view_bounds"]["side"],265,177,side_scale)
    iso=centered_projection(data["views"]["iso"],data["view_bounds"]["iso"],350,162,iso_scale)
    section=centered_projection(data["section"],data["section_bounds"],265,112,sec_scale,True)
    c=['<rect width="420" height="297" fill="white"/>','<rect x="8" y="8" width="404" height="281" fill="none" stroke="#243647" stroke-width=".55"/>']
    c += [svg_text(12,17,"KOLBE ELECTROCHEMICAL CELL  /  ASSEMBLY REVIEW",3.2,"#607283","bold"),
          svg_text(408,17,"REV B1   |   DIMENSIONS mm",2.8,"#607283","bold","end"),line(12,21,408,21,"#243647",.45),
          svg_text(12,31,f"KOLBE-{n}  |  {n}-LAYER PLATE-PRESS STACK",7,"#162331","bold"),
          svg_text(12,38,"Actual assembled BREP projection  |  See component sheets for manufacturing dimensions",2.8,"#435464")]
    c += [front,side,iso,section]
    c += [svg_text(112,233,f"PLAN / FRONT  ({scale_note(front_scale)})",2.7,"#435464","bold","middle"),
          svg_text(265,218,f"SIDE  ({scale_note(side_scale)})",2.7,"#435464","bold","middle"),
          svg_text(350,207,f"ISOMETRIC  ({scale_note(iso_scale)})",2.7,"#435464","bold","middle"),
          svg_text(265,125,f"SECTION A-A  (Y=0; Z MID-STACK)",2.6,"#435464","bold","middle")]
    c.append(line(12,55,408,55,"#243647",.4)); c.append(svg_text(12,62,"ASSEMBLY ENVELOPE / 总成参数",3.4,"#162331","bold"))
    c += [svg_text(14,70,f"01  BREP envelope: {sx:g} x {sy:g} x {sz:g} mm (X x Y x Z)",2.9,"#243647"),
          svg_text(14,76,f"02  Validated body stack height: {data['body_stack_height_mm']} mm; active layer-stack height: {data['active_stack_height_mm']} mm",2.9,"#243647"),
          svg_text(14,82,f"03  Assembly BREP contains {data['instances']} component instances; view shows actual model placements",2.9,"#243647"),
          svg_text(14,88,f"04  Geometry/model volume reported by assembly Stack: {data['volume_mm3']:.1f} mm³; not a pressure or strength rating",2.9,"#243647"),
          svg_text(14,94,"05  6 mm inter-electrode gap is a provisional envelope; pump flow, materials and sealing remain unresolved",2.9,"#9B4B2A")]
    c.append('<rect x="12" y="260" width="396" height="22" fill="#F5F7F8" stroke="#526171" stroke-width=".35"/>')
    c += [svg_text(15,267,"ASSEMBLY",2.3,"#607283","bold"),svg_text(15,276,f"{n}-layer compact plate-press",3,"#162331"),
          svg_text(253,267,"DRAWING",2.3,"#607283","bold"),svg_text(253,277,f"KOLBE-{n} / ASM-{n}",3,"#162331","bold"),
          svg_text(325,267,"SOURCE",2.3,"#607283","bold"),svg_text(325,277,f"Kolbe_{n}.FCStd Stack.Shape",2.2,"#162331"),
          svg_text(369,267,"STATUS",2.3,"#607283","bold"),svg_text(369,277,"REVIEW",3,"#9B4B2A","bold"),
          svg_text(12,253,"REVIEW GEOMETRY ONLY; do not infer pressure, torque, current capacity or final gap from this assembly view.",2.55,"#9B4B2A","bold")]
    return '<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">'+"".join(c)+"</svg>"

def translate_chinese(code, features=None):
    # Review-book sheet headings/notes in Chinese; exact nominal dimensions retained verbatim.
    trans = {"KP-101":"A向正极箔片", "KP-102":"C向负极箔片", "KP-201":"前端板", "KP-202":"前绝缘板", "KP-203":"后绝缘板", "KP-204":"后端板", "KP-601":"A侧电极载体膜", "KP-602":"C侧电极载体膜", "KF-101":"流道框架", "KP-301":"夹紧爪", "KP-501":"流体接头", "KP-502":"压缩密封圈", "KP-503":"PTFE管", "KB-A3":"A向三层铜梳排", "KB-C3":"C向三层铜梳排", "KB-A5":"A向五层铜梳排", "KB-C5":"C向五层铜梳排", "KB-A7":"A向七层铜梳排", "KB-C7":"C向七层铜梳排", "KB-801":"前PEEK支架", "KB-802":"后PEEK支架", "KH-901":"M4交叉孔堵头", "KH-902":"堵头垫圈", "KS-101":"主圆角方形密封圈", "KS-102":"歧管圆形密封圈"}
    return trans.get(code,code)

def pdf_stage():
    import fitz, cairosvg
    basis=json.loads((ROOT/"design_basis.json").read_text(encoding="utf-8"))
    flow=json.loads((ROOT/"validation"/"flow_parts.json").read_text(encoding="utf-8"))
    mech=json.loads((ROOT/"validation"/"mechanical_parts.json").read_text(encoding="utf-8"))
    hardware=json.loads((ROOT/"validation"/"hardware_parts.json").read_text(encoding="utf-8"))
    data=json.loads((RENDER/"brep_projection_data.json").read_text(encoding="utf-8"))
    part_paths=[]; assembly_paths=[]
    part_codes=[code for code in data if not code.startswith("ASSEMBLY-")]
    for code in part_codes:
        svg=make_sheet(code,data,basis,flow,mech,hardware)
        svgfile=DRAW/f"{code}_drawing.svg"
        pdffile=DRAW/f"{code}_drawing.pdf"
        svgfile.write_text(svg,encoding="utf-8")
        cairosvg.svg2pdf(bytestring=svg.encode("utf-8"),write_to=str(pdffile),output_width=420*72/25.4,output_height=297*72/25.4)
        part_paths.append(pdffile)
        # Native HLR plan projection DXFs for the major plates and all newly active hardware.
        if code in DXF_CODES:
            (DRAW/f"{code}_plan.dxf").write_text(data[code]["top_dxf"],encoding="ascii",errors="replace")
    for n in ASSEMBLIES:
        key=f"ASSEMBLY-{n}"
        if key not in data: continue
        val=json.loads((ROOT/"validation"/f"assembly_{n}.json").read_text(encoding="utf-8"))
        svg=make_assembly_sheet(key,data,val,basis)
        svgfile=DRAW/f"Kolbe_{n}_assembly.svg"; pdffile=DRAW/f"Kolbe_{n}_assembly.pdf"
        svgfile.write_text(svg,encoding="utf-8")
        cairosvg.svg2pdf(bytestring=svg.encode("utf-8"),write_to=str(pdffile),output_width=420*72/25.4,output_height=297*72/25.4)
        assembly_paths.append(pdffile)
    # Chinese-language review book cover followed by all part drawings. Keep imported projection geometry 1:1.
    cover_svg='''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><rect width="420" height="297" fill="#f5f7f8"/><rect x="15" y="15" width="390" height="267" fill="none" stroke="#243647" stroke-width=".8"/><text x="28" y="45" font-family="SimSun, sans-serif" font-size="5" fill="#607283">KOLBE ELECTROCHEMICAL CELL / REV B1</text><text x="28" y="78" font-family="SimSun, sans-serif" font-size="14" font-weight="bold" fill="#162331">板式压紧电化学电池</text><text x="28" y="98" font-family="SimSun, sans-serif" font-size="8" fill="#162331">CAD尺寸评审图册</text><line x1="28" y1="110" x2="392" y2="110" stroke="#246B8E" stroke-width="1"/><text x="28" y="130" font-family="SimSun, sans-serif" font-size="4" fill="#243647">依据最终零件BREP生成正视、侧视、轴测投影；尺寸单位为mm。</text><text x="28" y="146" font-family="SimSun, sans-serif" font-size="4" fill="#243647">电极活性区几何利用率：79.56%（56 x 56 mm箔片有效区，排除干端子区域）。</text><text x="28" y="162" font-family="SimSun, sans-serif" font-size="4" fill="#9B4B2A">审查状态：压力、化学兼容性、材料牌号、制造公差及密封验证未完成。</text><text x="28" y="178" font-family="SimSun, sans-serif" font-size="4" fill="#9B4B2A">6 mm间隙仅为机械评审包络；实际电极厚度、装配间隙和泵流量待确认。</text><text x="28" y="194" font-family="SimSun, sans-serif" font-size="4" fill="#9B4B2A">不赋予额定压力或最终紧固扭矩。螺纹标注为名义光滑包络，不代表螺旋牙型。</text><text x="28" y="226" font-family="SimSun, sans-serif" font-size="3.5" fill="#435464">图册包含零件功能、材料现状、主要尺寸、端口/密封/紧固特征和模型投影。</text><text x="28" y="256" font-family="SimSun, sans-serif" font-size="3.5" fill="#435464">图纸编号：B1-CAD-REVIEW  |  禁止用于制造放行</text></svg>'''
    cover_svg=cover_svg.replace("电极活性区几何利用率：79.56%（56 x 56 mm箔片有效区，排除干端子区域）。",
        "湿窗投影占箔片实体：79.56% = 2492.274 / 3132.566 mm²（50 x 50 R3窗口 / 56 x 56 R2箔片本体；干端子排除）。")
    cover_svg=cover_svg.replace("</svg>",'<text x="28" y="240" font-family="SimSun, sans-serif" font-size="3.5" fill="#435464">包含3/5/7层当前总成投影及全部在用自定义零件；已剔除未使用的旧端子、铜带和固定长度定位销。</text></svg>')
    cover=RENDER/"review_cover.pdf"
    cairosvg.svg2pdf(bytestring=cover_svg.encode("utf-8"),write_to=str(cover),output_width=420*72/25.4,output_height=297*72/25.4)
    writer=fitz.open(); writer.insert_pdf(fitz.open(str(cover)))
    for p in assembly_paths: writer.insert_pdf(fitz.open(str(p)))
    for p in part_paths: writer.insert_pdf(fitz.open(str(p)))
    cnbook=DRAW/"Kolbe_CAD_B1_Chinese_dimensioned_review_book.pdf"
    writer.save(str(cnbook)); writer.close()
    # Create PNG QA contact sheet at 110 dpi from the actual combined PDF.
    doc=fitz.open(str(cnbook)); qa=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False)
        out=RENDER/f"review_page_{i+1:02d}.png"; pix.save(str(out)); qa.append(str(out))
    # Detailed per-major PDFs also have individual PNGs; each should be visually reviewed.
    qa_codes=MAJOR+ ["KB-A7","KB-801","KB-802","KH-901","KH-902","KS-101","KS-102"]
    for code in qa_codes:
        if code not in data: continue
        partdoc=fitz.open(str(DRAW/f"{code}_drawing.pdf"))
        partdoc[0].get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(str(RENDER/f"{code}_drawing.png"))
    for n in ASSEMBLIES:
        pth=DRAW/f"Kolbe_{n}_assembly.pdf"
        if pth.exists():
            adoc=fitz.open(str(pth)); adoc[0].get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(str(RENDER/f"Kolbe_{n}_assembly.png"))
    print(json.dumps({"parts":part_codes,"assemblies":[str(p.name) for p in assembly_paths],"major_parts":NATIVE_CODES,"review_book":str(cnbook),"pdf_pages":len(doc),"qa_pages":len(qa)}))

def write_template():
    p=DRAW/"A3_landscape_template.svg"
    if p.exists(): return
    p.write_text('''<svg xmlns="http://www.w3.org/2000/svg" xmlns:freecad="http://www.freecadweb.org/wiki/index.php?title=Svg_Namespace" width="420mm" height="297mm" viewBox="0 0 420 297"><rect x="8" y="8" width="404" height="281" fill="none" stroke="#243647" stroke-width="0.5"/><path d="M12 260 H408 M250 260 V282 M322 260 V282 M366 260 V282" fill="none" stroke="#526171" stroke-width="0.3"/><text x="12" y="17" font-family="Arial" font-size="3.2" fill="#607283">KOLBE CELL - BREP DERIVED DRAWING</text><text x="12" y="276" font-family="Arial" font-size="3" fill="#243647">REVIEW ONLY - DIMENSIONS mm - TOLERANCES UNSPECIFIED UNLESS NOTED</text></svg>''',encoding="utf-8")

def main():
    ensure_dirs(); write_template()
    if "--freecad-stage" in sys.argv:
        freecad_stage(); return
    if not FREECAD_PY.exists(): raise FileNotFoundError(FREECAD_PY)
    subprocess.run([str(FREECAD_PY), str(Path(__file__).resolve()), "--freecad-stage"], cwd=str(ROOT), check=True)
    pdf_stage()

if __name__ == "__main__": main()
