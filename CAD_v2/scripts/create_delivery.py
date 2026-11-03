"""Build the CAD review cover/assembly/area pages and a current-only delivery ZIP.
Uses the bundled document Python (reportlab, pypdf), after native CAD exports.
"""
import json,math,zipfile,hashlib
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader,PdfWriter
ROOT=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
M=72/25.4;W=420;H=297
blue='#234958';orange='#AE6234';muted='#5C6970'

def main():
    out=ROOT/'drawings'/'Kolbe_B1_Assembly_and_Area.pdf'
    c=canvas.Canvas(str(out),pagesize=(W*M,H*M));c.setTitle('Kolbe CAD B1 assembly and electrode area review')
    def text(x,y,t,size=10,color='#233139'):
        c.setFillColor(color);c.setFont('STSong-Light',size);c.drawString(x*M,y*M,t)
    def begin(title,index):
        c.setFillColor(blue);c.rect(8*M,269*M,404*M,20*M,fill=1,stroke=0)
        text(14,277,title,18,'#FFFFFF')
        text(12,11,f'Kolbe CAD B1 | 2026-10-30 | mm | 结构评审，工况与加工放行待定 | {index}',8,muted)
        c.setStrokeColor('#D4DCE0');c.line(12*M,20*M,408*M,20*M)
    def picture(name,x,y,w,h):
        img=ImageReader(str(ROOT/'renders'/name));iw,ih=img.getSize();scale=min(w/iw,h/ih)
        ww=iw*scale;hh=ih*scale
        c.drawImage(img,(x+(w-ww)/2)*M,(y+(h-hh)/2)*M,ww*M,hh*M,mask='auto')
    def lines(x,y,items,size=11,dy=8):
        for i,t in enumerate(items):text(x,y-i*dy,t,size)
    begin('01 / 紧凑板框电堆 - 前端集中进出液',1)
    picture('Kolbe_5_upright.png',8,25,285,240)
    lines(296,249,['建议先打开五电极原生装配', 'assemblies/Kolbe_5.FCStd', '', '可导入其他 CAD 的实体文件', 'assemblies/Kolbe_5.step'],10,8)
    lines(296,195,['150 × 150 mm 主体板面', '5 电极 / 4 并联流道', '主体轴向厚度 69.75 mm', '照片式板框夹紧，内部共用歧管', '', '金属电极主体 56 × 56 mm', '绝缘载片承担歧管与外围定位', '所有 A 并联，所有 C 并联', '铜梳排有独立绝缘支架'],10.5,8)
    lines(296,99,['净距 6 mm 是评审尺寸。', '实际电极、泵流量与压力待提供。', '密封材料、预紧与端板受力待核定。', '图中外侧支架用于支撑干侧梳排。', '本版未做压力、漏液或热态试验。'],10,8)
    c.showPage()
    begin('02 / 分层拆装 - 电极与绝缘载片分离',2)
    picture('Kolbe_5_exploded_upright.png',7,25,287,239)
    lines(296,248,['从前至后：', '前压板 / 前绝缘液路板', 'C / 流道框 / A / 流道框 / C', '流道框 / A / 流道框 / C', '后绝缘封液板 / 后压板'],10.5,9)
    lines(296,188,['每张金属片配同厚绝缘载片。', '主密封圈仅压金属片窄边。', '歧管密封圈压在绝缘载片上。', '内部电极两面均面向流道。', '最外侧阴极主要使用朝内一面。', '', '爆炸图横向移出金属电极，', '用于检查反应窗、耳片与载片。', '铜连接与紧固件在本图中省略。'],10.5,8.5)
    lines(296,88,['单件 FCStd 保留原生特征树。', '装配零件定义嵌入同一文件，', '无外部零件引用。', '定位采用明确基准放置；', '未添加运动学装配约束。'],10,8)
    c.showPage()
    begin('03 / 电极面积 - 窄边密封，外围由绝缘载片承担',3)
    # Exact nominal coupon and window outlines, to a declared scale.
    cx,cy,sc=90,154,2.5
    c.setFillColor('#DCE3E6');c.setStrokeColor(blue);c.setLineWidth(.8)
    c.roundRect((cx-28*sc)*M,(cy-28*sc)*M,56*sc*M,56*sc*M,2*sc*M,fill=1,stroke=1)
    c.setFillColor('#E2F1E9');c.setStrokeColor('#4B826C')
    c.roundRect((cx-25*sc)*M,(cy-25*sc)*M,50*sc*M,50*sc*M,3*sc*M,fill=1,stroke=1)
    c.setStrokeColor(orange);c.setLineWidth(.65)
    c.roundRect((cx-27.5*sc)*M,(cy-27.5*sc)*M,55*sc*M,55*sc*M,5.5*sc*M,fill=0,stroke=1)
    c.roundRect((cx-26.1*sc)*M,(cy-26.1*sc)*M,52.2*sc*M,52.2*sc*M,4.1*sc*M,fill=0,stroke=1)
    text(23,236,'金属主体 56 × 56 / R2；窗口 50 × 50 / R3',12)
    text(45,151,'双面开放反应窗口',14,'#326A52')
    text(23,70,'橙线：密封槽边界（中心线 53.6 / R4.8；宽 1.4）',10,orange)
    text(23,61,'外槽边至金属边名义余量 0.5 mm；需结合公差与薄片变形核查。',10,muted)
    a=50**2-(4-math.pi)*3**2;b=56**2-(4-math.pi)*2**2
    total=b+72*16
    lines(190,239,['按圆角轮廓计算：',f'单面窗口面积：{a:.2f} mm²',f'金属主体面积：{b:.2f} mm²',f'主体几何面积占比：{100*a/b:.2f}%',f'计入当前干侧耳片后，金属总面积 {total:.2f} mm²，',f'窗口占金属总面积 {100*a/total:.2f}%。', '这是几何开窗面积，不是实测电化学有效面积。', '载片不覆盖金属反应面。', '', '实际电极尺寸未提供，主体和窗口均可重做。', '如采用镀铂钛，可将铂镀层限制在工作区，', '耳片与密封边的镀覆范围另行明确。'],11,9)
    picture('KP-601.png',230,24,170,100)
    text(204,31,'150 mm 绝缘载片承担歧管孔、定位与外围。',10,muted)
    c.showPage()
    begin('04 / 实际 CAD 核验与待定工程输入',4)
    ys=[235,212,189,166]
    headers=['电极数','内部流道','主体厚度 / mm','STEP 实体数','未解释实体干涉']
    xs=[22,80,143,229,306]
    for x,h in zip(xs,headers):text(x,252,h,12,'#FFFFFF')
    c.setFillColor(blue);c.rect(15*M,245*M,387*M,14*M,fill=1,stroke=0)
    for x,h in zip(xs,headers):text(x,250,h,12,'#FFFFFF')
    for n,y in zip([3,5,7],ys):
        d=json.loads((ROOT/'validation'/f'assembly_{n}.json').read_text())
        vals=[str(n),str(n-1),f"{d['body_stack_height_mm']:.2f}",str(d['instances']),str(len(d['unresolved_intersections']))]
        for x,t in zip(xs,vals):text(x,y,t,14)
        c.setStrokeColor('#D4DCE0');c.line(16*M,(y-8)*M,400*M,(y-8)*M)
    lines(20,154,['已核验：原生装配可打开；全部实例为有效实体；STEP 重新导入实体数量一致。', '螺纹采用名义包络。M4 螺钉与攻丝底孔的设计啮合已单列，不属于遗漏的碰撞。', '密封件装配形状为保面积椭圆截面示意，供货尺寸以独立自由态零件为准。'],12,10)
    lines(20,107,['仍需：实际电极长宽厚及材料、泵工作流量与最大压力、电解液/溶剂、温度和电流。', '据此确定净距、支路孔径、材料、密封圈、公差、预紧以及端板挠度要求。', '内部共用歧管仍需检查旁路电流、并联流量分配和气体排放路径。', '未执行实际加工、压力/漏液、介质相容性、热循环和电气温升试验。'],12,11)
    text(20,42,'后附原生实体投影与剖视图。每个定制件的 FCStd 与 STEP 见 parts/。',12,orange)
    c.showPage();c.save()
    writer=PdfWriter()
    for p in [out,ROOT/'drawings'/'Kolbe_CAD_B1_Chinese_dimensioned_review_book.pdf']:
        for page in PdfReader(str(p)).pages:writer.add_page(page)
    with (ROOT/'Kolbe_CAD_B1_review.pdf').open('wb') as f:writer.write(f)
    print('Review pages',len(writer.pages))
    # Manifest: only active assembly parts and their drawings, with current artifacts.
    codes=set()
    for n in [3,5,7]:
        for row in json.loads((ROOT/'validation'/f'assembly_{n}.json').read_text())['parts']:codes.add(row['code'].replace('-COMP',''))
    files=[]
    for p in ROOT.rglob('*'):
        if not p.is_file() or p.suffix.lower() in ['.fcbak','.zip','.pyc'] or '__pycache__' in p.parts:continue
        rel=p.relative_to(ROOT)
        if 'archive' in rel.parts:continue
        if any('qa' in part.lower() for part in rel.parts[:-1]) or 'tmp' in rel.parts:continue
        if rel.parts[0]=='parts' and p.stem not in codes:continue
        if p.name in ['import_test.step','delivery_manifest.json'] or p.suffix=='.log':continue
        if rel.parts[0]=='drawings' and any(t in p.stem for t in ['KP-302','KP-303','KP-401']):continue
        files.append(p)
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ROOT/'validation'/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    files.append(ROOT/'validation'/'delivery_manifest.json')
    package=ROOT/'Kolbe_CAD_B1_package.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,str(p.relative_to(ROOT)))
    print('Package files',len(files),'bytes',package.stat().st_size,'active part types',len(codes))

if __name__=='__main__':main()
