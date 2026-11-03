# 打开三维模型与独立模块

当前有效版本在 CAD_v2，顶层 OpenSCAD 资料为历史版本。

双击本目录“打开模块检查.cmd”，或在 FreeCAD 的“宏 → 宏…”中添加并执行 CAD_v2/scripts/inspect_modules.FCMacro。默认打开五片完整装配。

1. 面板顶部选择 assemblies（完整装配）、modules（功能模块）或 parts（单件），点击“打开选中文件”。
2. 在列表中选中零件，点击“只看选中零件”；Ctrl 支持多选。“显示全部”恢复当前文档的全部检查对象。“隐藏选中零件”方便逐层检查内部。
3. 点击绕 X/Y/Z 的按钮，每次旋转 15°，可组合连续使用获得中间角度。“适合窗口”居中缩放，不重置方向。
4. 鼠标操作取决于 FreeCAD 右下角的导航模式。CAD 模式：按住中键，再按住左键拖动旋转；中键拖动平移，滚轮缩放。可在导航模式菜单查看或切换适合触控板的模式。
5. “打开选中零件的可编辑源文件”进入 parts 中保留草图与特征历史的原件。更改原件不会自动重建已交付装配和检查模块。

列表选中零件会显示包围尺寸、体积和实体有效性；包围尺寸不是制造公差或工程图标注。源文件的完整建模树在 FreeCAD 的模型树中。

无需面板也可在 FreeCAD 中直接打开 CAD_v2/assemblies/Kolbe_5.FCStd。展开模型树的 Stack，选中零件后按空格切换显隐；Definitions 为隐藏的嵌入原生定义，不要全部显示，以免原点堆叠重复实体。

## 文件位置

- CAD_v2/assemblies：3/5/7 片完整装配和五片展示爆炸图。
- CAD_v2/modules：每个功能模块独立 FCStd 与 STEP。electrode 为电极与绝缘载片，flow 为流道与对应密封、堵头，另有前端、后端、管路与拉杆定位模块。模块保留装配坐标。
- CAD_v2/parts：可编辑原生单件及 STEP。保留了部分历史分支，当前装配采用哪些零件请查 BOM。
- CAD_v2/renders 的 PNG 和 drawings 的二维图纸为固定视角；自由旋转请打开三维文件。

modules 是独立检查实体，保留零件号及源文件信息，不包含完整建模历史；完整历史在 parts 中，原装配也有嵌入定义。压缩态密封与自由态源密封不同。功能拆分用于检查，没有新增机械约束或改变物理设计。

检查模块源脚本：CAD_v2/scripts/build_inspection_modules.py。源装配更新后需用 FreeCAD 自带 Python 重建。

验证记录：CAD_v2/validation/inspection_modules.json、inspection_gui.json。技术说明与尚未定稿的设计输入见 CAD_v2/README.md。

当前修订：中文模块/零件名称；铜排及其专用支架、夹块和 M4 紧固件已移除。保留电极极耳，电连接方案待定。旧含铜排文件保存在 CAD_v2/archive/before_no_busbars，不在检查面板列出。若 FreeCAD 已打开旧文件，请关闭后重新打开，以读取磁盘上的新版本。
