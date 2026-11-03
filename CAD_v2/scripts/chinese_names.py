"""Chinese display labels for the Kolbe FreeCAD documents.

This module only changes FreeCAD Label fields. Object names, properties,
placements and shapes are deliberately left intact.
"""
import os
import re


_PARTS = {
    'KP-101': '阳极电极片', 'KP-102': '阴极电极片',
    'KP-201': '前端压板', 'KP-202': '前端绝缘流道板',
    'KP-203': '后端绝缘封流板', 'KP-204': '后端压板',
    'KP-301': '电极极耳绝缘夹块', 'KP-302': '铜极性母排',
    'KP-303': '柔性极性连接带', 'KP-401': '电极堆定位销',
    'KP-501': 'M6×1隔板接头螺母', 'KP-502': '管路压紧卡套',
    'KP-503': '电解液导管', 'KP-601': '阳极精密绝缘载膜',
    'KP-602': '阴极精密绝缘载膜', 'KF-101': '内部并联流道框',
    'KB-801': '前端母排绝缘支架', 'KB-802': '后端母排绝缘支架',
    'KH-901': 'M4横钻孔堵头', 'KH-902': '堵头密封垫圈',
    'KS-101': '主流道周边密封圈', 'KS-102': '歧管端面密封圈',
    'STD-M8-WASHER': 'M8平垫圈', 'STD-M8-NUT': 'M8螺母',
    'STD-M4-NUT': 'M4螺母', 'STD-M4-S10': 'M4×10螺钉',
    'STD-M4-S12': 'M4×12螺钉', 'STD-M4-S20': 'M4×20螺钉',
}

_ROLE_WORDS = (
    (r'\bFront\b', '前端'), (r'\bRear\b', '后端'),
    (r'\bAnode\b', '阳极'), (r'\bCathode\b', '阴极'),
    (r'\bPositive\b', '正极'), (r'\bNegative\b', '负极'),
    (r'\bElectrode\b', '电极'), (r'\bPrecision insulating carrier\b', '精密绝缘载膜'),
    (r'\bParallel flow channel\b', '并联流道'), (r'\bChannel\b', '流道'),
    (r'\bperimeter seal\b', '周边密封圈'), (r'\bmanifold seal\b', '歧管密封圈'),
    (r'\bmanifold\b', '歧管'), (r'\bseal\b', '密封圈'),
    (r'\bpressure plate\b', '压板'), (r'\binsulating fluid adapter\b', '绝缘流道接板'),
    (r'\binsulating manifold closure\b', '绝缘歧管封板'),
    (r'\bfluid\b', '流体'), (r'\bElectrolyte tubing\b', '电解液导管'),
    (r'\btube\b', '导管'), (r'\btubing\b', '导管'),
    (r'\bcompression nut\b', '压紧螺母'), (r'\bferrule\b', '卡套'),
    (r'\bcrossdrill plug\b', '横钻孔堵头'), (r'\bplug face washer\b', '堵头端面垫圈'),
    (r'\bInsulating tab clamp\b', '绝缘极耳夹块'),
    (r'\bTab clamp screw\b', '极耳夹紧螺钉'), (r'\bTab clamp nut\b', '极耳夹紧螺母'),
    (r'\bBusbar support screw\b', '母排支架螺钉'),
    (r'\bFront busbar insulating support\b', '前端母排绝缘支架'),
    (r'\bRear busbar insulating support\b', '后端母排绝缘支架'),
    (r'\bcomb\b', '梳形母排'), (r'\bbusbar\b', '母排'),
    (r'\bStack tie rod\b', '电堆拉杆'), (r'\btie washer\b', '拉杆垫圈'),
    (r'\btie nut\b', '拉杆螺母'), (r'\bInsulating alignment pin\b', '绝缘对准销'),
    (r'\bElectrode tab clamp jaw\b', '电极极耳绝缘夹块'),
    (r'\bCopper polarity busbar\b', '铜极性母排'),
    (r'\bFlexible polarity bridge strap\b', '柔性极性连接带'),
    (r'\bElectrode stack locating dowel\b', '电极堆定位销'),
    (r'\bM6x1 bulkhead connector nut\b', 'M6×1隔板接头螺母'),
    (r'\bTube compression ferrule\b', '管路压紧卡套'),
    (r'\bElectrolyte tube stub\b', '电解液导管'),
    (r'\bFront dry endplate with manifold tool access\b', '前端带歧管工具孔压板'),
    (r'\bRear dry endplate\b', '后端压板'),
    (r'\bFront manifold insulator\b', '前端歧管绝缘板'),
    (r'\bRear manifold insulator\b', '后端歧管绝缘板'),
    (r'\bAnode precision-film carrier\b', '阳极精密绝缘载膜'),
    (r'\bCathode precision-film carrier\b', '阴极精密绝缘载膜'),
    (r'\bAnode electrode\b', '阳极电极片'), (r'\bCathode electrode\b', '阴极电极片'),
)

_FEATURE_WORDS = {
    'Body': '实体', 'FlowFrame': '流道框', 'Section': '截面', 'Outline': '轮廓',
    'Profile': '轮廓', 'Pad': '凸台', 'Pocket': '凹槽', 'Blank': '毛坯',
    'Foil': '箔片', 'Film': '薄膜', 'Hole': '孔', 'Holes': '孔',
    'Clearance': '间隙', 'Through': '贯穿', 'Blind': '盲孔', 'Manifold': '歧管',
    'Seal': '密封', 'Groove': '密封槽', 'Terminal': '端子', 'Tab': '极耳',
    'Electrode': '电极', 'Carrier': '载膜', 'Coupon': '极片', 'Window': '窗口',
    'Fastener': '紧固件', 'Locator': '定位', 'Bolt': '螺栓', 'Pattern': '阵列',
    'Port': '接口', 'Bore': '孔', 'Ferrule': '卡套', 'Thread': '螺纹',
    'Connector': '接头', 'Seat': '座孔', 'Pilot': '导向孔', 'Access': '检修',
    'Tool': '工具', 'Slot': '槽', 'Clamp': '夹紧', 'Jaw': '夹块',
    'Dowel': '定位销', 'Washer': '垫圈', 'Nut': '螺母', 'Screw': '螺钉',
    'Spine': '主脊', 'Finger': '指状触片', 'Support': '支撑', 'Cross': '横向',
    'Drill': '钻孔', 'Branch': '支路', 'Feed': '供液', 'Frame': '框架',
    'Wet': '湿区', 'Dry': '干区', 'Top': '上侧', 'Bottom': '下侧',
    'Front': '前端', 'Rear': '后端', 'Inner': '内侧', 'Outer': '外侧',
    'Main': '主', 'Axial': '轴向', 'Integral': '一体式', 'Pierced': '冲孔',
    'Recess': '沉孔', 'Face': '端面', 'Length': '长度', 'Thickness': '厚度',
    'Outline': '轮廓', 'Section': '截面', 'End': '端部', 'Fixing': '固定',
    'Low': '低矮', 'Head': '头部', 'Driver': '起子', 'Socket': '内六角',
    'Hex': '六角', 'Crossdrill': '横钻', 'Spotface': '沉台', 'Buried': '内置',
    'Alignment': '对准', 'CrossHole': '横孔', 'CrossDrill': '横钻孔',
}


def _code_for(path_or_code):
    value = str(path_or_code or '')
    name = os.path.basename(value)
    name = re.sub(r'\.(FCStd|step|stp|FCBak|FCMacro)$', '', name, flags=re.I)
    m = re.search(r'(STD-M8-ROD-(?:3|5|7)-(?:PLATE|SUPPORT)|STD-LOCATOR-(?:3|5|7)|STD-M[48]-(?:WASHER|NUT|S\d+)|KP-\d{3}|KF-\d{2,3}|KB-[AC](?:3|5|7)|KB-80[12]|KH-\d{3}|KS-\d{3})(?:-COMP)?', name.replace('_', '-'))
    return m.group(1) if m else None


def part_name(code):
    """Return Chinese part name, retaining the exact part number."""
    code = str(code or '').upper()
    base = _PARTS.get(code)
    if base is None:
        m = re.fullmatch(r'KB-([AC])([357])', code)
        if m:
            base = ('阳极正极' if m.group(1) == 'A' else '阴极负极') + m.group(2) + '层梳形母排'
        else:
            m = re.fullmatch(r'STD-M8-ROD-([357])-(PLATE|SUPPORT)', code)
            if m:
                base = 'M8×' + m.group(1) + '层' + ('压板用' if m.group(2) == 'PLATE' else '支架用') + '拉杆'
            else:
                m = re.fullmatch(r'STD-LOCATOR-([357])', code)
                if m:
                    base = m.group(1) + '层电堆绝缘对准销'
    if not base:
        if re.fullmatch(r'KF-0[1-6]', code):return code+'｜旧版流道框'
        return code
    return code + '｜' + base


def _translate_role(role):
    text = str(role or '').strip()
    for pattern, replacement in sorted(_ROLE_WORDS, key=lambda item: -len(item[0])):
        text = re.sub(pattern, replacement, text, flags=re.I)
    text = re.sub(r'\b(both faces exposed when internal)\b', '内部两面均暴露', text, flags=re.I)
    text = re.sub(r'\bM6x1\b', 'M6×1', text, flags=re.I)
    text = re.sub(r'\bM4\b', 'M4', text, flags=re.I)
    text = re.sub(r'\b(A|C)\b', lambda m: '阳极' if m.group(1).upper() == 'A' else '阴极', text)
    text = re.sub(r'\b(i)\b', '序号', text)
    text = re.sub(r'\s*,\s*', '，', text)
    return text


def instance_label(code, role):
    """Translate an assembly function and retain its part code and indices."""
    code_text = str(code or '').upper()
    clean_code = code_text.replace('-COMP', '')
    role_text = _translate_role(role)
    return '{}｜{}'.format(part_name(clean_code), role_text) if role_text else part_name(clean_code)


def file_label(path):
    """Return a Chinese file-picker label while retaining identifying codes."""
    value = str(path or '')
    stem = os.path.splitext(os.path.basename(value))[0]
    # Strip backup timestamps before interpreting the document stem.
    stem = re.sub(r'\.\d{8}-\d{6}$', '', stem)
    if stem.startswith('Kolbe_'):
        return document_label(stem)
    code = _code_for(stem)
    if code:
        return part_name(code) + os.path.splitext(value)[1].lower()
    return stem


def document_label(path):
    """Translate part, assembly and inspection-module document names."""
    value = os.path.basename(str(path or ''))
    stem = os.path.splitext(value)[0]
    stem = re.sub(r'\.\d{8}-\d{6}$', '', stem)
    if stem.startswith('Kolbe_'):
        m = re.fullmatch(r'Kolbe_([357])(_exploded)?', stem)
        if m:
            return 'Kolbe｜{}层装配{}'.format(m.group(1), '｜分解视图' if m.group(2) else '')
        m = re.fullmatch(r'Kolbe_([357])_(.+)', stem)
        if m:
            n, module = m.groups()
            labels = {'front_end':'前端组件', 'rear_end':'后端组件',
                      'fluid_ports':'流体接口组件', 'tie_rods_alignment':'拉杆与定位组件',
                      'electrical_busbars':'电气母排组件'}
            item = re.fullmatch(r'(electrode|flow)_(\d+)', module)
            if item:
                kind, index = item.groups()
                family = '电极组件' if kind == 'electrode' else '流道组件'
                return 'Kolbe｜{}层{}第{}号'.format(n, family, int(index))
            return 'Kolbe｜{}层{}'.format(n, labels.get(module, _translate_role(module.replace('_', ' '))))
    code = _code_for(stem)
    return part_name(code) if code else stem


def _feature_label(name):
    text = str(name or '')
    # Preserve ordinal and dimension tokens while translating CamelCase feature names.
    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', text).replace('_', ' ').split()
    result = []
    for word in words:
        key = re.sub(r'\d+$', '', word)
        suffix = word[len(key):]
        result.append(_FEATURE_WORDS.get(key, key) + suffix)
    return ''.join(result) or text


def localize_document(doc):
    """Localize document/object Label fields without touching names or geometry."""
    if doc is None:
        return doc
    doc.Label = document_label(getattr(doc, 'FileName', '') or getattr(doc, 'Name', ''))
    for obj in getattr(doc, 'Objects', []):
        code = getattr(obj, 'PartNumber', '') or _code_for(getattr(obj, 'Name', ''))
        role = getattr(obj, 'Function', '')
        type_id = str(getattr(obj, 'TypeId', ''))
        name = str(getattr(obj, 'Name', ''))
        if type_id == 'App::Link' or role:
            if code:
                obj.Label = instance_label(code, role or getattr(obj, 'Label', ''))
        elif code:
            if (hasattr(obj,'SourceObject') or type_id == 'PartDesign::Body' or name.lower() == 'body' or
                    name.replace('_', '-').upper().replace('-COMP', '') == code.upper()):
                obj.Label = part_name(code)
            else:
                obj.Label = _feature_label(name)
        elif type_id in ('App::DocumentObjectGroup', 'App::Part'):
            if name.lower() in ('definitions', 'definition'):
                obj.Label = '零件定义'
            elif name.lower() in ('stack', 'assembly'):
                obj.Label = '电堆总成'
        elif type_id.startswith(('PartDesign::', 'Sketcher::', 'Part::')):
            obj.Label = _feature_label(name)
            if re.search('[A-Za-z]',obj.Label):
                prefix={'Sketcher::SketchObject':'草图','PartDesign::Pad':'拉伸凸台','PartDesign::Pocket':'切除凹槽','PartDesign::Body':'实体'}.get(type_id,'建模特征')
                obj.Label=prefix+' '+str(getattr(obj,'ID',name))
    return doc
