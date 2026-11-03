"""Generate the dimensioned A3 concept drawing book for the Kolbe stack.

Concept review only. Dimensions are taken from kolbe_stack.scad as reviewed
2026-10-30; this document is not a fabrication release or pressure rating.
Optional OpenSCAD renders found in ../renders are appended as separate pages.
"""
from pathlib import Path
from math import cos, sin, radians
from datetime import date

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "Kolbe_design_review.pdf"
RENDERS = ROOT / "renders"
W, H = landscape(A3)
MM = 72 / 25.4

BLUE = colors.HexColor("#24536B")
INK = colors.HexColor("#17232D")
MID = colors.HexColor("#52636F")
LIGHT = colors.HexColor("#DCE6EA")
PALE = colors.HexColor("#F2F6F7")
ORANGE = colors.HexColor("#D17A27")
RED = colors.HexColor("#A53E38")
TEAL = colors.HexColor("#31827E")
GRAY = colors.HexColor("#7F8B91")

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
FONT = "STSong-Light"


def pt(v):
    return v * MM


def setup(c, page_no, title, subtitle=""):
    c.saveState()
    c.scale(MM, MM)
    c.setStrokeColor(INK)
    c.setLineWidth(0.35)
    c.rect(7, 7, 406, 283)
    c.setFillColor(BLUE)
    c.rect(7, 278, 406, 12, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT, 4.0)
    c.drawString(11, 282.2, "KOLBE FILTER-PRESS CELL  |  CONCEPT DRAWING BOOK")
    c.setFillColor(INK)
    c.setFont(FONT, 5.2)
    c.drawString(12, 268.8, title)
    if subtitle:
        c.setFillColor(MID)
        c.setFont(FONT, 2.9)
        c.drawString(12, 264.2, subtitle)
    # Title block
    c.setStrokeColor(INK)
    c.setLineWidth(0.25)
    c.line(7, 22, 413, 22)
    c.line(266, 7, 266, 22)
    c.line(334, 7, 334, 22)
    c.line(376, 7, 376, 22)
    c.setFillColor(MID)
    c.setFont(FONT, 2.35)
    c.drawString(10, 17.2, "图纸状态 / STATUS")
    c.drawString(10, 10.7, "2026-10-30  |  Rev A  |  概念评审 - 禁止直接加工 / CONCEPT REVIEW - DO NOT FABRICATE")
    c.drawString(269, 17.2, "图名 / TITLE")
    c.setFillColor(INK)
    c.setFont(FONT, 3.0)
    c.drawString(269, 10.6, title[:22])
    c.setFillColor(MID)
    c.setFont(FONT, 2.35)
    c.drawString(337, 17.2, "单位 / UNITS")
    c.setFillColor(INK)
    c.setFont(FONT, 3.0)
    c.drawString(337, 10.6, "mm")
    c.setFillColor(MID)
    c.setFont(FONT, 2.35)
    c.drawString(379, 17.2, "版次 / 页")
    c.setFillColor(INK)
    c.setFont(FONT, 3.0)
    c.drawString(379, 10.6, f"A  |  {page_no:02d}")
    c.restoreState()
    c.saveState()
    c.scale(MM, MM)


def end_page(c):
    c.restoreState()
    c.showPage()


def txt(c, x, y, s, size=3.0, color=INK, font=FONT):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, str(s))


def center_txt(c, x, y, s, size=3.0, color=INK):
    c.setFillColor(color)
    c.setFont(FONT, size)
    c.drawCentredString(x, y, str(s))


def line(c, x1, y1, x2, y2, color=INK, width=0.25, dash=None):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setDash(dash or [])
    c.line(x1, y1, x2, y2)
    c.setDash([])


def arrow(c, x, y, angle, size=1.6, color=INK):
    a1, a2 = radians(angle + 150), radians(angle - 150)
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(x, y)
    p.lineTo(x + size*cos(a1), y + size*sin(a1))
    p.lineTo(x + size*cos(a2), y + size*sin(a2))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def hdim(c, x1, x2, y, obj_y1, obj_y2, label, color=BLUE):
    line(c, x1, obj_y1, x1, y-1, color, 0.2)
    line(c, x2, obj_y2, x2, y-1, color, 0.2)
    line(c, x1, y, x2, y, color, 0.25)
    arrow(c, x1, y, 0, color=color)
    arrow(c, x2, y, 180, color=color)
    center_txt(c, (x1+x2)/2, y+1.1, label, 2.8, color)


def vdim(c, y1, y2, x, obj_x1, obj_x2, label, color=BLUE):
    line(c, obj_x1, y1, x+1, y1, color, 0.2)
    line(c, obj_x2, y2, x+1, y2, color, 0.2)
    line(c, x, y1, x, y2, color, 0.25)
    arrow(c, x, y1, 90, color=color)
    arrow(c, x, y2, -90, color=color)
    c.saveState()
    c.translate(x-1.3, (y1+y2)/2)
    c.rotate(90)
    center_txt(c, 0, 0, label, 2.8, color)
    c.restoreState()


def rounded_sq(c, x, y, size, r, stroke=INK, fill=None, width=0.35):
    c.setStrokeColor(stroke)
    c.setLineWidth(width)
    c.setFillColor(fill or colors.white)
    c.roundRect(x-size/2, y-size/2, size, size, r, fill=1 if fill else 0, stroke=1)


def callout(c, x, y, tx, ty, label, color=INK, size=2.7, anchor=None):
    if anchor is None:
        anchor = (x, y)
    mx = (anchor[0] + tx) / 2
    line(c, anchor[0], anchor[1], mx, ty+1.2, color, 0.22)
    line(c, mx, ty+1.2, tx, ty+1.2, color, 0.22)
    arrow(c, anchor[0], anchor[1], 0 if mx >= anchor[0] else 180, 1.2, color)
    txt(c, tx, ty, label, size, color)


def note_box(c, x, y, w, h, title, lines, accent=BLUE):
    c.setFillColor(PALE)
    c.setStrokeColor(LIGHT)
    c.setLineWidth(0.3)
    c.roundRect(x, y, w, h, 1.2, fill=1, stroke=1)
    c.setFillColor(accent)
    c.rect(x, y+h-5, w, 5, fill=1, stroke=0)
    txt(c, x+2, y+h-3.7, title, 2.9, colors.white)
    yy = y+h-8
    for s in lines:
        txt(c, x+2, yy, s, 2.5, INK)
        yy -= 4.2


def page_general(c):
    setup(c, 1, "总体布置与轴向堆叠", "XY 板面示意与 Z 向层序；外形参考主模型参数。标注尺寸均为概念名义值。")
    # Front plan view
    cx, cy, sc = 99, 157, 1.35
    c.saveState(); c.translate(cx, cy); c.scale(sc, sc)
    # electrode tails
    c.setFillColor(colors.HexColor("#E8D6B7")); c.setStrokeColor(ORANGE); c.setLineWidth(.35)
    c.rect(39, -5, 40, 10, fill=1, stroke=1)
    c.rect(-79, -5, 40, 10, fill=1, stroke=1)
    rounded_sq(c, 0, 0, 120, 4, INK, colors.HexColor("#E9EEF0"), .5)
    rounded_sq(c, 0, 0, 50, 3, BLUE, colors.white, .45)
    # seal groove centerline and outer edge hints
    rounded_sq(c, 0, 0, 61.4, 6.7, TEAL, None, .5)
    rounded_sq(c, 0, 0, 58.6, 5.3, TEAL, None, .5)
    # bolt hole locations
    for x in [-50,50]:
        for y in [-45,-15,15,45]:
            c.setFillColor(colors.white); c.setStrokeColor(INK); c.setLineWidth(.3)
            c.circle(x,y,3.5,fill=1,stroke=1)
    # electrodes/ports center marks
    c.setStrokeColor(RED); c.setLineWidth(.35)
    for y in [-60,60]:
        c.circle(0,y,1,fill=0,stroke=1)
    c.restoreState()
    hdim(c, cx-60*sc, cx+60*sc, 229, cy+60*sc, cy+60*sc, "120 外框")
    vdim(c, cy-60*sc, cy+60*sc, 12, cx-60*sc, cx-60*sc, "120 外框")
    hdim(c, cx-25*sc, cx+25*sc, 119, cy-25*sc, cy-25*sc, "50 × 50 工作窗")
    callout(c, 142, 192, 190, 207, "密封槽中心线 60 × 60", TEAL)
    callout(c, 99, 238, 157, 244, "8 × Ø7 框体通孔；M6 拉杆概念", INK)
    callout(c, 99, 76, 159, 84, "入口 / 出口：两侧 Y 向贯通钻孔", BLUE)
    txt(c, 15, 58, "计划视图 / PLAN", 3.0, BLUE)
    txt(c, 15, 53, "注：图中密封边线为槽宽示意，密封闭环不得被端面流道切断。", 2.55, MID)
    # Stack sequence schematic
    x0, y0, zscale = 218, 220, 1.85
    txt(c, 218, 249, "轴向层序 / AXIAL STACK (not to scale)", 3.0, BLUE)
    # vertical stacked bars, with labels to right
    parts = [(10,"端板 / endplate",GRAY),(4,"绝缘板 / insulator",ORANGE)]
    for p in parts:
        y0 -= p[0]*zscale
        c.setFillColor(p[2]); c.setStrokeColor(INK); c.rect(x0,y0,22,p[0]*zscale,fill=1,stroke=1)
    for i in range(3):
        y0 -= .35*zscale
        c.setFillColor(ORANGE if i%2 else BLUE); c.rect(x0,y0,22,.35*zscale,fill=1,stroke=1)
        if i < 2:
            y0 -= 4*zscale
            c.setFillColor(colors.HexColor("#CFE3E8")); c.rect(x0,y0,22,4*zscale,fill=1,stroke=1)
            c.setFillColor(TEAL); c.rect(x0,y0,22,.25,fill=1,stroke=0)
    y0 -= 4*zscale
    c.setFillColor(ORANGE); c.rect(x0,y0,22,4*zscale,fill=1,stroke=1)
    y0 -= 10*zscale
    c.setFillColor(GRAY); c.rect(x0,y0,22,10*zscale,fill=1,stroke=1)
    c.setStrokeColor(INK); c.setLineWidth(.3); c.line(x0+11, y0, x0+11, 76)
    txt(c, 245, 240, "上端板 10", 2.7)
    txt(c, 245, 233, "绝缘板 4", 2.7)
    txt(c, 245, 218, "C 0.35 / 流道框 4 / A 0.35", 2.7)
    txt(c, 245, 211, "重复：C-A-C (3片) 示例", 2.7)
    txt(c, 245, 177, "绝缘板 4", 2.7)
    txt(c, 245, 160, "下端板 10", 2.7)
    # stack table
    txt(c, 288, 243, "总堆叠名义尺寸链", 3.0, BLUE)
    rows = [("电极数", "活性段厚度", "总厚度"), ("3", "9.05", "37.05"), ("5", "17.75", "45.75"), ("7", "26.45", "54.45")]
    widths=[21,33,25]; xx=288; yy=232
    for ri,row in enumerate(rows):
        x=xx
        for j,item in enumerate(row):
            c.setFillColor(BLUE if ri==0 else (PALE if ri%2 else colors.white)); c.setStrokeColor(LIGHT); c.rect(x,yy-5,widths[j],5,fill=1,stroke=1)
            center_txt(c,x+widths[j]/2,yy-3.5,item,2.4,colors.white if ri==0 else INK)
            x+=widths[j]
        yy-=5
    txt(c, 288, 208, "总厚度 = n×0.35 + (n-1)×4 + 2×(10+4)", 2.45)
    txt(c, 288, 202, "不含螺母、垫圈、软管、线缆及接头。", 2.45, MID)
    note_box(c, 286, 110, 108, 78, "总览限制", [
        "单极并联概念；膜 / 隔膜：无。",
        "两侧外阴极主要利用朝流道面；",
        "内电极两面朝向相邻独立流道。",
        "干侧母排、极耳及拉杆绝缘避让",
        "需按实物复核；图中不代表认证。",
        "标注未含加工公差，禁止直接下料。",
    ], RED)
    end_page(c)


def page_frame(c):
    setup(c, 2, "流道框 / 密封槽 / 螺栓布局", "单个框体端面；双面槽剖面深度及流体孔另见第 4 页。")
    cx,cy,sc=134,154,1.55
    c.saveState(); c.translate(cx,cy); c.scale(sc,sc)
    rounded_sq(c,0,0,120,4,INK,colors.HexColor("#F2F5F6"),.45)
    rounded_sq(c,0,0,50,3,BLUE,colors.white,.45)
    # groove band with CL 60 and width 1.4
    rounded_sq(c,0,0,61.4,6.7,TEAL,None,.45)
    rounded_sq(c,0,0,58.6,5.3,TEAL,None,.45)
    # ports on top/bottom (port axes y +/-60)
    c.setFillColor(colors.white); c.setStrokeColor(BLUE); c.setLineWidth(.4)
    c.circle(0,60,.5,fill=1,stroke=1); c.circle(0,-60,.5,fill=1,stroke=1)
    for x in [-50,50]:
        for y in [-45,-15,15,45]:
            c.setFillColor(colors.white); c.setStrokeColor(INK); c.setLineWidth(.35); c.circle(x,y,3.5,fill=1,stroke=1)
    # centerlines
    line(c,-68,0,68,0,GRAY,.18,[1,1]); line(c,0,-68,0,68,GRAY,.18,[1,1])
    c.restoreState()
    hdim(c,cx-60*sc,cx+60*sc,245,cy+60*sc,cy+60*sc,"120")
    vdim(c,cy-60*sc,cy+60*sc,24,cx-60*sc,cx-60*sc,"120")
    hdim(c,cx-25*sc,cx+25*sc,110,cy-25*sc,cy-25*sc,"50 工作窗")
    callout(c,134,154+30*sc,213,221,"密封槽中心线：60 × 60，R6",TEAL)
    callout(c,134+30*sc,154+30*sc,214,210,"双侧槽：宽 1.4 / 深 0.75",TEAL)
    callout(c,134+50*sc,154+45*sc,214,195,"8 × Ø7 通孔；位置 X=±50, Y=±45/±15",INK,size=2.5)
    callout(c,134,154+60*sc,214,180,"流体孔中心 X=0、Y=±60；Ø1（gap=4时）",BLUE,size=2.5)
    txt(c, 17, 62, "框体端面 / FRAME FACE", 3, BLUE)
    # Right dimensions, section and details
    txt(c, 250, 246, "A-A 密封槽剖面（示意）", 3, BLUE)
    # frame cross section: 4 thick, 1.4 wide groove depth .75 both faces
    x,y=261,206; sx=15; sy=10
    c.setFillColor(colors.HexColor("#DDE5E9")); c.setStrokeColor(INK)
    c.rect(x,y,sx,sy,fill=1,stroke=1)
    groove_x, groove_w, groove_d = x+5.75, 3.5, 1.875  # diagram scale 2.5x
    seal_w_draw, seal_h_draw = 3.333, 1.875  # compressed section: 1.333 x 0.75 mm
    c.setFillColor(colors.white); c.rect(groove_x,y-0.1,groove_w,groove_d+.1,fill=1,stroke=1)
    c.rect(groove_x,y+sy-groove_d,groove_w,groove_d+.1,fill=1,stroke=1)
    c.setFillColor(TEAL); c.roundRect(groove_x+(groove_w-seal_w_draw)/2,y,seal_w_draw,seal_h_draw,seal_h_draw/2,fill=1,stroke=0)
    c.roundRect(groove_x+(groove_w-seal_w_draw)/2,y+sy-seal_h_draw,seal_w_draw,seal_h_draw,seal_h_draw/2,fill=1,stroke=0)
    # electrode plates adjacent to faces
    c.setFillColor(ORANGE); c.rect(x,y-1, sx,.45,fill=1,stroke=0); c.rect(x,y+sy+.55,sx,.45,fill=1,stroke=0)
    hdim(c,groove_x,groove_x+groove_w,y-5,y,y,"1.4 groove width")
    vdim(c,y,y+groove_d,x+17,x+15,x+15,"0.75 depth")
    vdim(c,y,y+sy,x+20,x+15,x+15,"4 frame thickness")
    txt(c,249,184,"每个端面闭合连续槽；框两侧各一条。",2.65)
    txt(c,249,178,"压缩截面椭圆约 1.333 × 0.75 mm（宽 × 高）。",2.65)
    txt(c,249,172,"槽尺寸 / 压缩率须按供应商规格与公差复核。",2.65,RED)
    note_box(c, 248, 104, 147, 57, "孔位与密封区关系", [
        "螺栓孔位于湿侧闭环之外，中心坐标：",
        "X=±50；Y=±45、±15；孔径 Ø7。",
        "框 / 端板 / 绝缘板孔均为 Ø7（模型值）。",
        "模型需用剖视 / 实物检查确认流道孔未切穿槽壁。",
    ], BLUE)
    note_box(c, 248, 48, 147, 48, "方案尺寸状态", [
        "框材料概念 PEEK；工作压差、流量、最高压差 TBD。",
        "本图不声明承压等级、密封保证或加工公差。",
        "对称压紧力及端板挠度需独立计算、试验验证。",
    ], RED)
    end_page(c)


def page_electrodes(c):
    setup(c, 3, "电极片与端板 / 绝缘板轮廓", "电极为薄片概念；两类极耳方向相反，螺钉孔仅作干侧连接占位。")
    def electrode(cx,cy,polarity):
        sc=1.15
        c.saveState(); c.translate(cx,cy); c.scale(sc,sc)
        # 80x80 body R2 and 40x10 ear to ±80
        c.setFillColor(colors.HexColor("#F2E3CB") if polarity=="A" else colors.HexColor("#D7E0E4"))
        c.setStrokeColor(ORANGE if polarity=="A" else BLUE); c.setLineWidth(.5)
        c.roundRect(-40,-40,80,80,2,fill=1,stroke=1)
        if polarity=="A": c.rect(40,-5,40,10,fill=1,stroke=1); hx=75
        else: c.rect(-80,-5,40,10,fill=1,stroke=1); hx=-75
        c.setFillColor(colors.white); c.setStrokeColor(INK); c.circle(hx,0,2.1,fill=1,stroke=1)
        line(c,-43,0,43,0,GRAY,.18,[1,1]); line(c,0,-43,0,43,GRAY,.18,[1,1])
        c.restoreState()
        hdim(c,cx-40*sc,cx+40*sc,cy-51,cy-40*sc,cy-40*sc,"80 本体")
        vdim(c,cy-40*sc,cy+40*sc,cx-53,cx-40*sc,cx-40*sc,"80 本体")
        ex1,ex2=(-40,80) if polarity=="A" else (-80,40)
        hdim(c,cx+ex1*sc,cx+ex2*sc,cy+54,cy+5*sc,cy+5*sc,"120 总长含极耳")
        callout(c,cx+(75 if polarity=="A" else -75)*sc,cy, cx+52,cy+37,"Ø4.2 干侧夹持孔",ORANGE,size=2.5)
        center_txt(c,cx,cy+64,f"{polarity} 极片 / {('阳极 ANODE' if polarity=='A' else '阴极 CATHODE')}",3,ORANGE if polarity=="A" else BLUE)
    electrode(103,169,"A")
    electrode(298,169,"C")
    # small endplate profile
    txt(c, 18, 90, "端板 / 绝缘板平面轮廓", 3, BLUE)
    cx,cy,sc=67,53,.47
    c.saveState(); c.translate(cx,cy); c.scale(sc,sc)
    rounded_sq(c,0,0,120,4,INK,colors.HexColor("#D7DEE2"),.8)
    for x in [-50,50]:
        for y in [-45,-15,15,45]: c.setFillColor(colors.white); c.setStrokeColor(INK); c.circle(x,y,3.5,fill=1,stroke=1)
    c.restoreState()
    hdim(c,cx-60*sc,cx+60*sc,18,cy-60*sc,cy-60*sc,"120")
    vdim(c,cy-60*sc,cy+60*sc,33,cx-60*sc,cx-60*sc,"120")
    callout(c,95,53,133,83,"端板厚 10；绝缘板厚 4",BLUE,size=2.55)
    note_box(c, 177, 32, 216, 54, "关键电连接说明", [
        "电极片厚 0.35；极耳宽 10；尖端 X=±80。",
        "中间电极两面朝向相邻流道；无膜 / 隔膜。",
        "C-A-C-A-C... 为单极并联阵列：同极支路分别汇流。",
        "双面阳极工作面需保持连续平整；双面镀铂钛仅为候选，",
        "实际基材 / 涂层与电流密度、接触、电化学窗口待确定。",
        "铜母排只能布置在干侧；不允许铜接触电解液。",
        "耳片应位于密封区外；母排和拉杆须电气隔离并留避让。",
    ], ORANGE)
    end_page(c)


def page_flow(c):
    setup(c, 4, "流体孔 / 单通道密封剖面", "流向仅表示概念。外部分配各通道；产气气液处理与泄压为系统设计任务。")
    # Plan and side flow schematic
    txt(c, 18, 244, "框体端面示意 / PORT ROUTING", 3, BLUE)
    cx,cy,sc=92,163,1.28
    c.saveState(); c.translate(cx,cy); c.scale(sc,sc)
    rounded_sq(c,0,0,120,4,INK,colors.HexColor("#F1F5F6"),.5)
    rounded_sq(c,0,0,50,3,BLUE,colors.white,.5)
    rounded_sq(c,0,0,61.4,6.7,TEAL,None,.45); rounded_sq(c,0,0,58.6,5.3,TEAL,None,.45)
    # ports follow Y axis, side drills at mid-plane, across X? OpenSCAD rotate y-cylinder corresponds axis Y; shown as ends at +/-Y.
    line(c,0,-61,0,-25,BLUE,1.0); line(c,0,25,0,61,BLUE,1.0)
    c.setFillColor(BLUE); c.circle(0,-60,.8,fill=1,stroke=0); c.circle(0,60,.8,fill=1,stroke=0)
    c.restoreState()
    callout(c,cx,cy-60*sc,171,90,"底部入口概念：Y=-60，Ø1",BLUE)
    callout(c,cx,cy+60*sc,171,218,"顶部出口 / 排气：Y=+60，Ø1",BLUE)
    txt(c,171,206,"流体孔沿框体实体内 Y 向钻通，孔轴 Z=gap/2。",2.6)
    txt(c,171,200,"gap=4 时孔径 gap/4=Ø1；换 gap 后随模型参数变化。",2.6)
    txt(c,171,194,"Ø1 与 CS/4 等径为模型概念，流阻 / 接头 / 堵塞风险待验证。",2.6,RED)
    # section cross section (not fabricated mesh projection; schematic axial view)
    txt(c, 18, 74, "流道横截面 / SECTION AT CHANNEL", 3, BLUE)
    x0,y0,w,h=35,48,118,6
    # electrodes and frame sandwich
    c.setFillColor(ORANGE); c.setStrokeColor(INK); c.rect(x0,y0-2,w,.7,fill=1,stroke=1)
    c.setFillColor(colors.HexColor("#DCE7EA")); c.rect(x0,y0-1.3,w,h+2.6,fill=1,stroke=1)
    c.setFillColor(TEAL); c.rect(x0+44,y0-1.3,30,.75,fill=1,stroke=0); c.rect(x0+44,y0+h+1.3,30,.75,fill=1,stroke=0)
    c.setFillColor(ORANGE); c.rect(x0,y0+h+2,w,.7,fill=1,stroke=1)
    # wet opening
    c.setFillColor(colors.HexColor("#B9DCE6")); c.rect(x0+38,y0+1.2,42,h-2.4,fill=1,stroke=0)
    txt(c,38,66,"阳极 A 面",2.55,ORANGE); txt(c,115,66,"阴极 C 面",2.55,BLUE)
    callout(c,91,52,169,69,"槽内 O 形圈概念线 (两面各一条)",TEAL)
    callout(c,70,51,169,60,"框体 gap=4",BLUE)
    note_box(c, 242, 141, 150, 99, "运行 / 安全待确认", [
        "工作压差、流量、最高允许压力与泄压路径：TBD。",
        "外部分配歧管必须逐通道供液 / 回液并便于隔离排障。",
        "顶端气液分离、受控排放、压力监测和防回流由系统提供。",
        "电解产气可形成可燃混合气；禁止把出口封死。",
        "接头形式、螺纹、软管、温度和密封材料兼容性待定。",
        "短接管仅为占位示意；密封微管接头未完成，也未验证。",
        "此图不证明孔道完全贯通、无死区或密封可靠。",
    ], RED)
    note_box(c, 242, 79, 150, 51, "端面密封禁止事项", [
        "侧向孔必须为框体内部钻孔；不得在端面开槽切断闭环。",
        "框体两侧各有完整闭合密封槽，电极平整面作压合面。",
        "压缩限位与均匀预紧须工程验证，不能仅由渲染确认。",
    ], TEAL)
    end_page(c)


def page_bom(c):
    setup(c, 5, "BOM / 未定工程参数与评审边界", "方案尺寸基于当前参数化模型；材料、载荷、加工、公差及系统安全仍需工程闭环。")
    headers=["项", "数量 / 几何", "概念材料 / 说明", "需要核查 / 决策"]
    rows=[
        ("流道框", "每相邻电极间 1 件；120×120×4；窗 50×50", "PEEK 占位；两面闭环槽", "化学兼容、刚度、蠕变、孔道与槽壁厚"),
        ("密封圈", "每框两条；CS 1；槽 1.4×0.75；压缩椭圆约 1.333×0.75", "EPDM/FKM/FFKM 候选待选型", "药液 / 羧酸盐 / 60-85°C 兼容性；压缩率 / 公差"),
        ("电极", "80×80×0.35；耳宽 10；尖端 X=±80", "阳极涂层与阴极基材 TBD", "腐蚀、平整度、载流、连接电阻、温升"),
        ("端板", "120×120×10；8 个拉杆孔位", "材料 / 刚度未指定", "板弯曲、预紧均匀性、应力、长期松弛"),
        ("绝缘板", "120×120×4；按端板开孔 / 缺口", "绝缘材料 TBD", "耐温、吸液、表面爬电与机械压溃"),
        ("拉杆 / 紧固件", "8×M6 概念；框 / 端板 / 绝缘板通孔 Ø7", "材质 / 绝缘套 TBD", "腐蚀、载荷分配、螺纹啮合、绝缘；不得预设扭矩"),
        ("流体接头", "每框两口；概念 Ø1 孔，Z=2", "螺纹标准 / 接头形式 TBD", "压降、堵塞、拔脱、密封、歧管分流"),
    ]
    x0=15; y=238; col=[37,92,116,143]
    x=x0
    for j,hdr in enumerate(headers):
        c.setFillColor(BLUE); c.setStrokeColor(colors.white); c.rect(x,y,col[j],11,fill=1,stroke=1)
        center_txt(c,x+col[j]/2,y+4,hdr,2.6,colors.white)
        x+=col[j]
    y-=11
    for ri,row in enumerate(rows):
        x=x0; heights=[21,17,17,17,17,17,17][ri]
        for j,item in enumerate(row):
            c.setFillColor(PALE if ri%2==0 else colors.white); c.setStrokeColor(LIGHT); c.rect(x,y-heights,col[j],heights,fill=1,stroke=1)
            # wrap by estimated width in font units
            max_chars=max(1,int(col[j]/1.7))
            parts=[item[k:k+max_chars] for k in range(0,len(item),max_chars)]
            for k,p in enumerate(parts[:4]): txt(c,x+2,y-5-k*4,p,2.35,INK)
            x+=col[j]
        y-=heights
    note_box(c, 15, 50, 195, 59, "关键待定项（不得隐去）", [
        "设计压力 / 泵关断压差 / 泄压设定值：TBD；不得自行给出承压额定值。",
        "电解液 / 溶剂组成、浓度、产物与最高温度 / 流量：由实验条件确认。",
        "压力边界的材料认证、供应商密封尺寸和加工公差：待获取并复核。",
        "端板受力、拉杆预紧、密封压缩均匀性：需计算 + 台架试验。",
    ], RED)
    note_box(c, 218, 50, 186, 59, "评审边界", [
        "OpenSCAD 几何和本图册只描述概念布局；不构成承压、寿命、腐蚀、",
        "电气安全或“保证不漏液”的证明。完成材料 / 强度 / 流体校核后，",
        "仍需逐级冷态与热态压力、循环和泄漏试验，并设置监测与安全排气。",
        "未完成上述闭环前：仅用于概念讨论，不可直接加工或运行。",
    ], BLUE)
    end_page(c)


def page_system_schematic(c):
    setup(c, 6, "外部分配与单极并联电气示意", "系统级功能框图，不代表接头规格、实际歧管尺寸或电化学参数。")
    # Fluid loop
    txt(c, 15, 246, "A  外部并联供液 / 排气路径", 3.4, BLUE)
    y=202
    boxes=[(15,42,"储液瓶", "RESERVOIR"),(69,36,"循环泵", "PUMP"),(116,43,"入口分配器", "DISTRIBUTOR"),(278,43,"出口集流器", "COLLECTOR"),(333,68,"气液分离器", "VENTED SEPARATOR")]
    for x,w,zh,en in boxes:
        c.setFillColor(PALE); c.setStrokeColor(BLUE); c.setLineWidth(.45); c.roundRect(x,y,w,21,2,fill=1,stroke=1)
        center_txt(c,x+w/2,y+12,zh,2.9,INK)
        center_txt(c,x+w/2,y+5,en,2.1,MID)
    def flow_arrow(x1,y1,x2,y2):
        line(c,x1,y1,x2,y2,BLUE,.8)
        from math import atan2, degrees
        arrow(c,x2,y2,degrees(atan2(y2-y1,x2-x1)),2.2,BLUE)
    flow_arrow(57,212.5,69,212.5)
    flow_arrow(105,212.5,116,212.5)
    # distributor and collector riser manifolds with 3 illustrative parallel channels
    line(c,159,212.5,169,212.5,BLUE,.7)
    line(c,169,179,169,232,BLUE,.65)
    line(c,268,179,268,232,BLUE,.65)
    line(c,268,212.5,278,212.5,BLUE,.7)
    for i,yy in enumerate([181,206,231],1):
        line(c,169,yy,183,yy,BLUE,.65)
        c.setFillColor(colors.HexColor("#DCE7EA")); c.setStrokeColor(INK); c.roundRect(183,yy-6,75,12,1.5,fill=1,stroke=1)
        center_txt(c,220.5,yy+1.4,f"流道 {i} / CHANNEL",2.4,INK)
        center_txt(c,220.5,yy-3.1,"两相邻电极间；单腔无膜",2.0,MID)
        flow_arrow(186,yy,253,yy)
        line(c,258,yy,268,yy,BLUE,.65)
    flow_arrow(321,212.5,333,212.5)
    # return line to reservoir from separator
    line(c,367,202,367,164,TEAL,.75)
    line(c,367,164,35,164,TEAL,.75)
    flow_arrow(35,164,35,200)
    txt(c,164,153,"液相回流 / LIQUID RETURN",2.4,TEAL)
    # pressure monitor at inlet and relief branch; vent remains open to managed exhaust
    line(c,169,212.5,177,212.5,RED,.55)
    line(c,177,212.5,177,236,RED,.55)
    c.setFillColor(colors.white); c.setStrokeColor(RED); c.circle(177,239,4,fill=1,stroke=1)
    center_txt(c,177,238,"P",2.8,RED)
    txt(c,183,238,"入口压力监测 / pressure monitor",2.3,RED)
    line(c,169,212.5,169,178,RED,.55)
    line(c,169,178,157,178,RED,.55)
    c.setFillColor(colors.white); c.setStrokeColor(RED); c.roundRect(125,173,31,10,1,fill=1,stroke=1)
    center_txt(c,140.5,176.5,"泄压 / RELIEF",2.2,RED)
    txt(c,160,176,"TBD → 安全收集",2.25,RED)
    # Vented gas path, no cap symbol
    line(c,367,223,367,241,ORANGE,.8)
    arrow(c,367,241,90,2.1,ORANGE)
    txt(c,283,239,"气相出口持续连通至安全排放系统",2.4,ORANGE)
    txt(c,283,233,"不得加封闭堵头 / 不得封死出口",2.4,RED)
    txt(c,15,141,"N 个电极对应 N-1 个并联流道；分配均匀性、排气、压降和泄漏监测需实测。",2.65,MID)

    # Electrical schematic
    txt(c, 15, 119, "B  单极并联干侧接线（示意）", 3.4, BLUE)
    # Supply box and separate buses
    c.setFillColor(PALE); c.setStrokeColor(INK); c.roundRect(17,58,42,28,2,fill=1,stroke=1)
    center_txt(c,38,75,"直流电源",3,INK); center_txt(c,38,67,"CURRENT-LIMITED",2.0,MID)
    line(c,59,78,83,78,RED,.9); line(c,59,66,83,66,BLUE,.9)
    txt(c,62,81,"+",3,RED); txt(c,62,61,"-",3,BLUE)
    # A+ and C- buses. A+ leads cross C- through a visible no-connect jumper.
    # Connection dots appear only where an electrode joins its own polarity bus.
    a_x=[184,266]
    line(c,83,78,381,78,RED,1.0)
    cursor=83
    for px in a_x:
        line(c,cursor,66,px-2.5,66,BLUE,1.0)
        p=c.beginPath(); p.moveTo(px-2.5,66); p.lineTo(px-1.0,68.5); p.lineTo(px+1.0,68.5); p.lineTo(px+2.5,66)
        c.setStrokeColor(BLUE); c.setLineWidth(1.0); c.drawPath(p,stroke=1,fill=0)
        cursor=px+2.5
    line(c,cursor,66,381,66,BLUE,1.0)
    txt(c,85,81,"A+ 干侧阳极母排",2.6,RED)
    txt(c,85,59,"C- 干侧阴极母排",2.6,BLUE)
    # Five electrode symbols with separate same-polarity connections.
    plate_x=[143,184,225,266,307]
    labels=["C0","A1","C2","A3","C4"]
    for i,(px,lab) in enumerate(zip(plate_x,labels)):
        col=BLUE if lab.startswith("C") else ORANGE
        line(c,px,39,px,53,col,1.5)
        center_txt(c,px,105,lab,2.7,col)
        if lab.startswith("A"):
            line(c,px,53,px,78,RED,.7)
            c.setFillColor(RED); c.circle(px,78,1.15,fill=1,stroke=0)
        else:
            line(c,px,53,px,66,BLUE,.7)
            c.setFillColor(BLUE); c.circle(px,66,1.15,fill=1,stroke=0)
    # show connection branch to bus with distinct paths
    txt(c,18,43,"电极片仅以干侧极耳接入母排；湿区内无铜连接件。",2.45,MID)
    txt(c,18,35,"A 极片全部并联至正极，C 极片全部并联至负极；不得跨接异极。",2.45,MID)
    txt(c,18,29,"母排在板外干侧 X=±82（极耳端 ±80）；拱线为不连接跨线，圆点为同极接点。",2.25,RED)
    end_page(c)


def append_render_pages(c, start_no=6):
    candidates = [
        ("assembly_3.png", "OpenSCAD 装配渲染 - 3 片", "assembly"),
        ("assembly_5.png", "OpenSCAD 装配渲染 - 5 片", "assembly"),
        ("assembly_7.png", "OpenSCAD 装配渲染 - 7 片", "assembly"),
        ("exploded.png", "OpenSCAD 爆炸图渲染", "exploded"),
        ("flow_section.png", "OpenSCAD 流道 / 密封剖面渲染", "flow_section"),
    ]
    found=[]
    for fn, title, kind in candidates:
        p=RENDERS/fn
        if p.is_file() and p.stat().st_size>0:
            found.append((p,title,kind))
    for idx,(img,title,kind) in enumerate(found,start_no):
        setup(c,idx,title,"OpenSCAD 概念渲染；仅用于识别空间关系，不替代尺寸图与验证。")
        maxw,maxh=382,233
        ir=ImageReader(str(img)); iw,ih=ir.getSize()
        scale=min(maxw/iw,maxh/ih)
        dw,dh=iw*scale,ih*scale
        x=(420-dw)/2; y=30+(maxh-dh)/2
        c.setStrokeColor(LIGHT); c.setLineWidth(.4); c.rect(x-1,y-1,dw+2,dh+2,fill=0,stroke=1)
        c.drawImage(ir,x,y,width=dw,height=dh,mask='auto',preserveAspectRatio=True,anchor='c')
        txt(c,12,26,f"来源文件：renders/{img.name}  |  图像比例保留：{iw} × {ih} px",2.5,MID)
        end_page(c)
    return [x[0].name for x in found]


def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(OUT),pagesize=landscape(A3),pageCompression=1)
    c.setTitle("Kolbe design review - dimensioned concept plates")
    c.setAuthor("Concept engineering review")
    page_general(c)
    page_frame(c)
    page_electrodes(c)
    page_flow(c)
    page_bom(c)
    page_system_schematic(c)
    renders=append_render_pages(c, start_no=7)
    c.save()
    print(f"Wrote {OUT}")
    print(f"Pages: {6+len(renders)}; appended renders: {', '.join(renders) if renders else 'none available'}")


if __name__ == "__main__":
    main()
