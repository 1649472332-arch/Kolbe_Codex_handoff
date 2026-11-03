#!/usr/bin/env python3
"""从交付FCStd的实际半框剖面生成中文PNG；箭头为设计意图，不是CFD结果。"""
from pathlib import Path
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.font_manager import FontProperties, fontManager

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_variants as G
App, Part, V = G.App, G.Part, G.V
HERE = Path(__file__).resolve().parent
font = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if font.exists():
    fontManager.addfont(str(font))
    plt.rcParams['font.family'] = FontProperties(fname=str(font)).get_name()
plt.rcParams['axes.unicode_minus'] = False
COLORS = {'inlet': '#067ac1', 'outlet': '#db7131', 'vent': '#995ab5'}


def arrow(ax, p, q, color, rad=0, lw=1.8):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=15,
                                color=color, lw=lw, connectionstyle=f'arc3,rad={rad}', zorder=8))


def actual_section(ax, shape, z):
    plane = Part.makePlane(160, 160, V(-80, -80, z))
    section = shape.section(plane)
    wires = Part.sortEdges(section.Edges)
    face = Part.makeFace([Part.Wire(edges) for edges in wires], 'Part::FaceMakerBullseye')
    vs, tris = face.tessellate(.12)
    xy = np.array([[v.x, v.y] for v in vs])
    ax.add_collection(PolyCollection([xy[list(t)] for t in tris], color='#dbe5eb', edgecolor='none', zorder=1))
    for edge in section.Edges:
        p = edge.discretize(Deflection=.08)
        ax.plot([v.x for v in p], [v.y for v in p], color='#485d6a', lw=.7, zorder=2)


def draw_frame(ax, doc, which, layout, stem):
    body = doc.getObject('HalfFrame'+which)
    actual_section(ax, body.Shape, G.ZC[which])
    # 密封槽在另一Z面，虚线只是投影提示，不意味着孔道横切密封槽。
    for size, r in ((68, 4), (72, 6)):
        for edge in G.rr_face(size, size, r).Edges:
            pts = edge.discretize(Deflection=.1)
            ax.plot([p.x for p in pts], [p.y for p in pts], '--', color='#8c75a2', lw=.7, zorder=3)
    x = 18 if which == 'A' else -16
    ax.plot([x, x], [-31.5, 28.5], color='#138c73', lw=2.2, zorder=4)
    ax.plot([x, x], [28.5, 60.6], color='#33383e', lw=2, zorder=4)
    # 夹具在local Z=-2：以投影轮廓表示，保持与模型一致的高度。
    ax.add_patch(Rectangle((x-5.1, 46.15), 10.2, 14.2, fill=False, ec='#30363a', lw=1))
    ax.add_patch(Rectangle((x-7, 60.35), 14, 5, color='#30363a', alpha=.85))
    for spec in layout['ports']:
        p, q = np.array(spec['p'][:2]), np.array(spec['q'][:2])
        u = (q-p)/np.linalg.norm(q-p)
        color = COLORS[spec['kind']]
        ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=2, alpha=.7, zorder=5)
        if spec['kind'] == 'inlet':
            arrow(ax, p-u*10, q+u*7, color)
        else:
            arrow(ax, q+u*5, p-u*10, color)
        if abs(p[1]) > 52:
            # 分散底部四点标注，避免孔径与孔号拥挤。
            label = ('进' if spec['kind'] == 'inlet' else '排气' if spec['kind'] == 'vent' else '出')
            label += f'Ø{spec["diameter_mm"]:g}'
            ypos = -66 if p[1] < 0 else 71
            ax.text(p[0], ypos, label, ha='center', va='center', fontsize=8, color=color)
        else:
            ax.text(-65, p[1]-8, ('进' if spec['kind'] == 'inlet' else '出')+f'Ø{spec["diameter_mm"]:g}',
                    ha='center', fontsize=8, color=color)
    if stem == 'inlet_tangential':
        for p, q, rad in [((-23,-27),(25,-22),.1), ((25,-20),(24,22),.2),
                          ((22,23),(-23,23),.15), ((-24,20),(-24,-18),.1)]:
            arrow(ax, p, q, '#2e9e97', rad=rad, lw=1.2)
        ax.text(0, 0, '偏置射流\n旋流待验证', ha='center', va='center', fontsize=10, color='#237e78')
    elif stem == 'inlet_top':
        arrow(ax, (22,25), (0,-15), '#2e9e97', rad=-.15, lw=1.2)
        arrow(ax, (-7,-15), (-26,-24), '#2e9e97', lw=1.2)
        arrow(ax, (-23,2), (-29,29), COLORS['vent'], lw=1.2)
        ax.text(4, 0, '下行液流\n上行排气', ha='center', fontsize=10, color='#237e78')
    else:
        for xx in (-23, 0, 23):
            arrow(ax, (xx,-22), (xx,23), '#2e9e97', lw=1.2)
        ax.text(0, 0, '上升扫流\n均匀性待验证', ha='center', va='center', fontsize=10,
                color='#237e78', bbox=dict(fc='white', ec='none', alpha=.85))
    ax.set(xlim=(-76,76), ylim=(-74,79), aspect='equal', xlabel='X / mm', ylabel='Y / mm（向上）')
    ax.set_title(f'半框{which}：Z = {G.ZC[which]:+.2f} mm剖面', fontsize=11, pad=9)
    ax.grid(alpha=.12)
    ax.set_xticks([-52.35, -34, 0, 34, 52.35])


def draw_stack(ax):
    # XZ示意单独说明薄片方向和无隔膜连通关系，比例与源码一致。
    for which, color in [('A', '#72a8ce'), ('B', '#e8b768')]:
        z0 = G.ZC[which]-10
        for x0 in (-52.35, 34):
            ax.add_patch(Rectangle((x0,z0), 18.35,20, color=color, alpha=.55))
        x = 18 if which == 'A' else -16
        ax.add_patch(Rectangle((x-.175,G.ZC[which]-9), .35,14, color='#138c73'))
        ax.text(43, G.ZC[which], which, ha='center', va='center', fontsize=14)
    ax.axhline(0, color='#aaa', lw=.7, ls=':')
    ax.text(0, 24, 'A/B保留原装配间距0.18 mm\n中部无膜实体，液腔连通', ha='center', fontsize=10)
    ax.text(0, -31, '电极片位于YZ面\n各为60(Y)×14(Z)×0.35(X) mm', ha='center', fontsize=10, color='#138c73')
    ax.set(xlim=(-62,62), ylim=(-42,42), xlabel='X / mm', ylabel='Z / mm（堆叠方向）', aspect='equal')
    ax.set_title('Y=0的XZ剖面关系示意', fontsize=11)
    ax.grid(alpha=.12)


def main():
    configs = json.loads((HERE/'port_layouts.json').read_text())
    for stem, layout in configs.items():
        doc = App.openDocument(str(HERE/(stem+'.FCStd')))
        fig = plt.figure(figsize=(17,8), facecolor='#fafbfd', layout='constrained')
        gs = fig.add_gridspec(1,3, width_ratios=[1,1,.8])
        for i, which in enumerate(('A','B')):
            draw_frame(fig.add_subplot(gs[0,i]), doc, which, layout, stem)
        draw_stack(fig.add_subplot(gs[0,2]))
        fig.suptitle(layout['title']+'  |  V37半框派生方案', fontsize=19, color='#233d50')
        handles = [Line2D([0],[0],color=c,lw=2,label=l) for c,l in [
            (COLORS['inlet'],'进口'),(COLORS['outlet'],'气液出口'),(COLORS['vent'],'顶部排气出口'),
            ('#138c73','薄电极／预期流向'),('#8c75a2','另一Z面的密封槽投影')]]
        fig.legend(handles=handles, loc='outside lower center', ncols=3, frameon=False, fontsize=10)
        fig.text(.5,.085,'剖面取自实际FCStd实体；夹具为投影占位。箭头仅表示设计意图，未经CFD或实测验证。',
                 ha='center', fontsize=10, color='#6b4950')
        fig.savefig(HERE/(stem+'.png'), dpi=165)
        plt.close(fig)
        App.closeDocument(doc.Name)
        print('已生成示意图', stem, flush=True)


if __name__ == '__main__':
    main()
