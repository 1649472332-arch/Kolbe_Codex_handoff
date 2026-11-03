# Kolbe 电解池 CAD B1

交互检查：双击上级目录 `打开模块检查.cmd`，或在 FreeCAD 执行 `scripts/inspect_modules.FCMacro`。操作说明见上级目录 `README_START_HERE.md`。`modules/` 提供独立功能模块 FCStd/STEP；可编辑建模历史仍在 `parts/`。模块保留装配坐标，支持自由旋转、隔离和显隐。PNG 和二维图纸只有固定视角。

源装配更新后，用 FreeCAD 自带 Python 运行 `scripts/build_inspection_modules.py` 重建检查模块；模块文件不会自动随源零件变化。

这是按照片所示紧凑板框形式重做的 FreeCAD 实体设计：前端集中进出液、内部并联歧管、3/5/7 片单极并联电极、小面积金属电极和独立绝缘载片。旧 SCAD 不参与本版建模。

## 先打开什么

1. `assemblies/Kolbe_5.FCStd`：建议先看的五电极原生装配；文件自含零件定义，不需要外链恢复。
2. `assemblies/Kolbe_5.step`：通用 STEP 装配，可导入其他 CAD。保留实体，不保留 FreeCAD 特征历史。
3. `assemblies/Kolbe_5_exploded.FCStd`：分层及电极横向移出展示。主体紧固件为清晰起见省略；铜排及专用附件已从当前设计移除，不是安装姿态。
4. `drawings/`：仍保留的单件图纸；旧合订评审 PDF 已归档，不适用于当前无铜排版本。
5. `parts/`：每件独立的原生 FCStd 与 STEP；`drawings/native/`（如存在）及其他带 TechDraw 名称的 FCStd 是原生投影视图。

单件零件树保留 Body、Sketch、Pad、Pocket 等实际建模特征；密封件为扫掠/环面实体。装配使用文档内 App::Link 和明确的基准定位，未建立 Assembly 工作台的运动学约束。草图几何使用 Block 约束固定精确坐标，可在 Sketcher 中解除并修改；批量尺寸改动通过生成脚本重建，**不会仅修改 JSON 就自动关联更新全部图纸**。

## 当前结构

- 金属主体 56 × 56 × 0.35 mm、R2；干侧耳片单独引出，A 朝 +X、C 朝 −X。
- 工作窗 50 × 50 mm、R3。几何面积 2492.27 mm²，金属主体面积 3132.57 mm²，主体单面几何利用率约 79.56%，不含干侧耳片；计入当前 72 × 16 mm 干侧耳片后，金属总面积约 4284.57 mm²，窗口占比约 58.17%。该口径单独列出，避免把反应主体占比当作整片材料利用率。内部电极两面开放；外侧阴极主要使用内侧面。
- 主密封中心线 53.6 mm 圆角方形、R4.8，槽宽 1.4、深 0.75，密封圈截面直径 1.0；密封槽只占电极窄边。
- 0.35 mm 绝缘精密载片承担外围、定位与歧管孔，贵金属不延伸到整张框体。可用钛基材在工作区双面镀铂，具体材料和镀覆范围待实验确定。
- 框体 150 × 150 × 6 mm，两个 Ø8 轴向歧管在 (0,±62)。每个歧管两侧各有独立闭合密封槽；Ø2.2 埋入支路贯通反应窗。
- 框体侧面小螺塞封闭横向钻孔的加工入口；正常供回液只有前端两口。不能把加工孔堵头省略。
- 前/后绝缘板厚 14/6；压板各厚 12。主体厚度 3 片为 57.05、5 片 69.75、7 片 82.45 mm，不含外侧支架、螺母和管件。
- 当前版本已移除铜梳排、专用绝缘支架、极耳夹块及其 M4 紧固件；电极干侧耳片保留。电连接方式待另行设计。拉杆垫圈和螺母直接压在前后压板上，使用压板跨度拉杆。

## 文件使用范围

当前有效零件由 `drawings/BOM_3.csv`、`BOM_5.csv`、`BOM_7.csv` 指定。`KF-01..06` 是改为内部歧管前的旧分支；`KP-302/303/401` 是被梳排及定长销替换的零件，不属于当前装配。检查面板只列当前 BOM 中的零件，避免误用。旧交付压缩包已归档。

当前无铜排版本重新检查 FCStd 与 STEP 实体，结果见 `validation/no_busbars_chinese.json` 和 `validation/step_roundtrip.json`。模块与模型树显示中文名称，零件编号保留。旧版含铜排的装配、模块、图纸和评审包保存在 `archive/before_no_busbars/`，不作为当前文件使用。

## 尚未定稿的输入

用户指定净距依据实际电极和流量确定。当前 **6 mm 只是机械评审尺寸**，实际电极、流量、泵最大压力、电解液/溶剂、电流和温度没有提供，设计压力保持 TBD。密封圈供货、载片与金属厚度配对、材料牌号、加工公差、螺纹/接头标准、预紧力和端板受力尚需确定。本版不得作为已完成承压与化学验证的加工放行图。

原生 CAD、实体校核与几何利用率不能证明实际密封、流量均匀性、电化学有效面积或长期可靠性。后续应按真实输入完成尺寸定型、材料/密封选型、端板与预紧计算，以及冷态循环、漏液和热态验证。内部共用液体网络还需评估旁路电流与混合气体处理。

## 重新生成

使用本机 FreeCAD 自带 Python，而非系统 Python：

```powershell
$cadPython = 'C:\Users\16494\AppData\Local\Programs\FreeCAD 1.1\bin\python.exe'
& $cadPython CAD_v2/scripts/model_flow.py
& $cadPython CAD_v2/scripts/model_parts.py
& $cadPython CAD_v2/scripts/model_hardware.py
& $cadPython CAD_v2/scripts/build_assemblies.py
```

`render_native.FCMacro` 通过 FreeCAD GUI 更新颜色和原生视口图；`make_cad_drawings.py` 生成投影与评审图纸；`audit_geometry.py` 做独立几何审查。尺寸变化后全部相关图纸、BOM 和验证均需重新生成。本版常用尺寸有脚本内的明确数值，重建前需一并复核，不能假定所有尺寸都只由 `design_basis.json` 驱动。
