/*
基于 v37 A(两个M12孔)/B(一个M12孔)原版新增【电极十字放置示意】。
孔编号：1=B原孔 X=-2.5；2=A原孔 X=-7.5（仅保留接口）；3=A新增孔 X=+6.0。
1、3孔下分别悬挂竖直片式电极，与电解池框架大面 XY 垂直。
为与 20mm 厚的单侧液腔兼容，本示意电极片采用 30(Y)×14(Z)×0.35(X) mm；
这只是可视化占位尺寸，并非直接把原先30x30实际电极削小后的加工图。
若坚持使用30x30mm整片垂直摆放，单侧20mm厚液腔无法完整容纳，须修改结构或电极尺寸。
可编辑项目：part="cross_electrode_assembly"、"cross_electrode_exploded"、"electrodes_only"。
半框真实几何、原有M12孔、膜密封槽和独立打印模式均不修改。
*/

// v37-A2 geometry notes (mm):
// A original electrode port center: X=-7.5, Z=+2.0
// A new M12 port center: X=+6.0, Z=-2.0
// B original electrode port center: X=-2.5, Z=-2.0 (unchanged)
// Center projection spacing of original A/B electrode ports: 5.0
// A two M12 port center distance in 3D: sqrt(13.5^2+4^2)=14.08.
// Top-right M7 keepout radius: 10.25 (including 6.5 wall from bolt radius).
// New port axis x separation from right bolt axis: 22.675-6.0=16.675.
// Nominal M12 envelope r=6.0; clearance to bolt keepout 16.675-(10.25+6.0)=0.425 mm.
// This clears geometrically but is NOT validated for machining tolerance, thread damage or pressure.
// Do not treat this small keepout clearance as a proven robust seal for permanent use.

/*
V37_AB_face_to_face - A/B 每块1孔，两孔投影中心距10mm，垫片槽面对面叠合（非左右平铺）

在 V19 基础上进一步修改，用于降低电解产气时漏液风险：
- 内部液腔保持 43 x 43 mm，并把内腔基础圆角增大，减少角部应力和膜/垫片折皱；
- 删除顶部 M12 电极夹口周围的端面 O 型圈环/浅座，顶部只保留电极夹孔本体；
- M12 电极夹孔沿 Z 方向向靠近膜的一侧平移，默认每片平移 2.0 mm；
- 模块与膜接触面增加浅垫片定位槽，用于让硅胶/FKM/EPDM 垫片更稳定地被压住；
- 删除 V20 中的四边中部辅助压紧孔，只保留四角 M7 通孔；
- 顶部 M12 电极夹孔不再以 10.6 mm 大孔直接连通液腔，而是在与内部液腔连接处收缩为 6.65 mm 小口；
- 继续保留 43x43 主体窗口 + 四角 M7 螺丝孔安全避让结构；
- 加大四角 M7 孔靠近内腔一侧的半圈实体宽度，方便打印、密封和垫片剪裁；
- A/B 两片打印导出时都让平整外侧面朝下，避免垫片浅槽面贴平台；
- 电极夹孔从靠近四角孔的位置向中间移动，远离四角 M7 螺丝孔；
- 在每个电极夹孔外侧局部增加 8 mm 加高/延长座，并让加高座向主体内部重叠 4 mm，保证与主体完全连接；
- 将顶部 10.6 mm M12 攻丝预孔的有效深度从 10 mm 加深到 15 mm；
- 15 mm 以下到液腔之间仍保留 6.65 mm 小孔连通；
- 删除模块间垫片定位浅槽，使膜接触面恢复为平面；
- 保留电极夹口 15 mm 深度、6.65 mm 液腔连接小孔和电极夹加高座；
- 四角 M7 螺丝孔周围进一步加大实体隔离区，使螺丝孔更远离液腔；
- 已取消四角 M7 螺丝孔外侧浅台阶垫圈座，四角外表面恢复为平面。
- 保留 flat_AB_print 模式，把 A 片和 B 片平铺在同一个平面中一次导出/打印；
- 取消内部电极定位轨，液腔保持空心；
- 每片 half_frame 总厚度保持 20 mm；
- 四角螺丝孔保持 M7 通孔；
- M12 电极插口保持顶部垂直贯通、无外凸耳座。

结构：
原侧模块 / half_frame_A 内的 30x30 电极 / half_frame_A 的 20mm 液腔 / 膜 /
half_frame_B 的 20mm 液腔 / half_frame_B 内的 30x30 电极 / 原侧模块

坐标定义：
XY 平面 = 原电解池侧模块平面；Z 方向 = 堆叠厚度方向。
电极片与膜均平行于 XY 平面。
顶部 M12 插口轴线沿 Y 方向，从 +Y 顶部向下进入液腔。

重要说明：
- 黑色 M12 件本身只是电极引出/固定件。若你的 30x30 电极片没有耳片，
  它不能凭空被 M12 件可靠夹住；最好给电极片加一个上方导电耳片，
  或者用导电杆/导电夹从 M12 贯通孔进入并压/接触电极上缘。
- M12 孔仍建议打印为 10.6 mm 预孔，然后用 M12 x 1.5 丝锥攻牙。
- V22 已去掉顶部 O 型圈环/浅座；若后续仍需要密封，建议在外部电极夹肩部另加平垫或重新开启 O 型圈座参数。
- 模块间垫片建议使用 FKM/EPDM/硅胶片，垫片厚度与槽深需要配合，避免过压或压缩不足。
- 每片 half_frame 总厚度为 20 mm；两片加膜后中间主体厚度约 40.18 mm。
*/

// V37 scalable version: scale the XY chamber opening while preserving interfaces.
// footprint_scale=1 reproduces original nominal dimensions; 2 doubles chamber
// length and width (4x planar area), without enlarging M12/M7 or Z thickness.
footprint_scale = 2.0;
assert(footprint_scale >= 1, "footprint_scale must be >= 1");

$fn = 96;

// =========================
// 输出选择
// =========================
// 可选：
// "AB_gasket_face_to_face"  A/B夹膜垫片面相对、XY投影重合，预留0.18mm膜厚间隙（默认）
// "AB_gasket_exploded"      仅用于观察密封槽的爆炸预览（间距另加5mm）
// "single_cell_assembly"  单电池装配预览
// "half_frame_A"          半框 A：装配姿态
// "half_frame_B"          半框 B：装配姿态
// "half_frame_A_print"    半框 A：平整外侧面朝下，适合打印
// "half_frame_B_print"    半框 B：平整外侧面朝下，适合打印
// "membrane_template"     膜裁剪参考片
// "electrode_reference"   30x30 电极片参考
// "scale_stack_demo"      多单元堆叠示意
// "flat_AB_print"       A/B 两片同平面平铺打印：四角填平外侧面朝上
// "flat_AB_inner_groove_up_print" A/B 两片同平面平铺打印：中间夹膜垫片槽朝上
// "gasket_cut_template" 垫片定位槽轮廓薄片，用于剪裁垫片
part = "cross_electrode_assembly";

// =========================
// 原电解池外形与螺丝参数
// =========================
outer_L = 61.7 + 43.0 * (footprint_scale - 1);
outer_W = 61.7 + 43.0 * (footprint_scale - 1);
outer_R = 3.0;

// 原孔位：孔中心距外边 = 4.45 + 7.45/2 = 8.175；中心坐标 = 22.675
bolt_x = outer_L/2 - 8.175;
bolt_y = outer_W/2 - 8.175;

// 四角螺丝孔：按 M7 通孔处理，预留 7.5 mm 便于螺丝穿过和打印公差
bolt_d = 7.5;

// V22：已删除四边中部辅助压紧孔，只保留四角 M7 通孔
include_side_compression_holes = false;
side_compression_hole_d = 5.5;    // 保留参数但默认关闭，不参与模型切除
side_compression_offset = 27.0;

// =========================
// 43x43 液腔与半框
// =========================
chamber_L = 43.0 * footprint_scale;
chamber_W = 43.0 * footprint_scale;
chamber_R = 4.0;      // V22：保持圆角，减少膜/垫片在内腔角部折皱

// 重要：43x43 内腔会接近/碰到四角 M7 孔。
// 为避免液腔与螺丝孔连通，这里在内腔四角给螺丝孔留安全避让区。
// chamber_bolt_keepout_d = bolt_d + 2*wall_between_chamber_and_bolt
// V23：把四角 M7 孔靠近内腔一侧的半圈实体宽度从 2.0 mm 加大到 3.8 mm，
// 这样更方便打印成型，也更方便垫片按轮廓剪裁，不容易剪到螺丝孔边缘。
wall_between_chamber_and_bolt = 6.5;   // V32：进一步加大螺丝孔与液腔之间的实体干区，降低水线爬到螺丝孔的风险
chamber_bolt_keepout_d = bolt_d + 2*wall_between_chamber_and_bolt;

// 四角螺丝孔外侧垫圈座已关闭。
// 当前版本按你的要求将四角垫圈座填平，外侧面保持平整。
// 如需恢复该结构，只需把 include_bolt_washer_seats 改回 true。
include_bolt_washer_seats = false;
bolt_washer_seat_d = 15.0;       // 垫圈座外径，建议配 12~14 mm 外径软垫圈
bolt_washer_seat_depth = 0.80;   // 垫圈座深度，适合 0.8~1.5 mm 厚软垫圈


// V34 修改：中间垫片槽宽度从 3.0 mm 缩窄至 2.0 mm，其余尺寸/布局保持不变。
// 模块间垫片/膜定位浅槽：开在每片 half_frame 的膜接触面一侧
// 这是“定位槽/浅密封槽”，用于让软垫片不易滑动；最终密封仍取决于垫片材料、厚度和压紧力。
include_interface_gasket_pocket = true;   // V32：重新开启中间液腔周围垫片槽，负责防止模块中间缝漏液
gasket_pocket_L = 54.0;                   // 保留旧参数，V32 主体采用 gasket_ring_width 控制密封环宽度
gasket_pocket_W = 54.0;
gasket_pocket_R = 3.0;
gasket_ring_width = 2.0;                  // V34：中间密封环宽度由 3.0 mm 缩窄到 2.0 mm；深度仍为 0.50 mm
gasket_pocket_depth = 0.50;               // 中间垫片槽深度，适合 0.5–1.0 mm 软垫片做定位
gasket_pocket_bolt_clearance = 2.25;      // V32：螺丝孔周围额外干区，避免中间垫片槽贴近螺丝孔
gasket_bolt_dry_zone_d = bolt_d + 2*gasket_pocket_bolt_clearance;

// V28：垫片剪裁模板薄片厚度。打印这个薄片后，可按其外形描线/裁剪垫片。
gasket_template_T = 0.80;

// 每片半框原始厚度 15 mm；按你的要求，以膜接触面为基准向外侧加厚 5 mm
// 最终每片总厚度 = 20 mm；两片 half_frame + 膜后，中间主体总厚度约为 40.18 mm
half_frame_base_T = 15.0;
outer_side_extra_T = 5.0;
half_frame_T = half_frame_base_T + outer_side_extra_T;

// =========================
// 膜与电极参数
// =========================
membrane_T = 0.18;
membrane_L = 55.0 + 43.0 * (footprint_scale - 1);
membrane_W = 55.0 + 43.0 * (footprint_scale - 1);
membrane_has_bolt_holes = true;

electrode_L = 30.0 * footprint_scale;
electrode_W = 30.0 * footprint_scale;
electrode_T = 0.35;

// 电极定位轨：承托 30x30 电极片的左右边缘
include_electrode_rails = false;
rail_w = 2.0;                  // 从 43x43 液腔侧壁向内伸出的宽度
rail_len = electrode_W + 0.8;  // 沿 Y 方向长度，略大于电极高度
rail_T = 0.65;                 // 沿 Z 方向厚度，略大于电极片厚度
rail_clearance_z = 0.08;

// =========================
// 顶部垂直贯通 M12 电极插口
// =========================
include_electrode_socket = true;

// 黑色件外螺纹实测约 11.81 mm，按 M12 处理
socket_thread_major_measured = 11.81;
socket_pitch_guess = 1.5;

// 打印预孔后攻丝；若要直接通孔可把 socket_mode 改成 "clearance"
socket_mode = "tap";
socket_tap_pilot_d = 10.60;
socket_clearance_d = 12.30;
socket_thread_spec = "M12x1.5";

// V22：按要求去掉 M12 电极夹孔上方的环形 O 型圈座。
// 如后续又需要端面 O 型圈槽，可把 include_socket_oring_seat 改回 true。
include_socket_oring_seat = false;
socket_oring_cross_section = 2.0;
socket_oring_target_compression = 0.25; // 目标压缩率约 25%
socket_oring_groove_width = 2.8;
socket_oring_groove_depth = socket_oring_cross_section * (1 - socket_oring_target_compression); // 约 1.5 mm
socket_oring_groove_d = socket_tap_pilot_d + 2*socket_oring_groove_width; // 浅环形座外径

// 取消外凸耳座：M12 孔直接在 half_frame 本体顶部开口
// 因此这里不再额外设置顶部加厚块/耳座

// V35：A/B 两块均改为单电极孔。
// A 块只保留原孔；B 块只保留一个孔，并要求其孔中心与 A 块孔中心相距 5 mm。
// 这里采用 X 方向错位实现：A 孔中心 x = -7.5 mm，B 孔中心 x = -2.5 mm，中心距 = 5.0 mm。
A_socket_x = -7.5 * footprint_scale;                  // A 块保留孔
B_socket_x = -2.5 * footprint_scale;                  // B 块唯一孔，与 A 块孔中心距 5 mm
AB_socket_center_distance = abs(B_socket_x - A_socket_x);
// A 原孔不动；仅 A 新增一个 M12 接口。蓝色 A 片原孔轴线 z=+2 mm，新增孔轴线 z=-2 mm。
// 这一位置使两个 M12 螺纹的外缘保持实体隔离，并避开四角 M7 周围的 6.5 mm 干区。
// 这里的 M12 是 10.6 mm 攻丝预孔，实际内螺纹需打印后攻丝形成。
A_include_second_electrode_socket = true;
B_include_second_electrode_socket = false;
A_second_socket_x = 6.0 * footprint_scale;            // 新增 A 孔：X=+6.0 mm，不侵入右上 M7 保护圈
A_second_socket_z_offset = -4.0;    // 相对 A 原孔 z=+2 mm 向外侧移动 4 mm，新孔 z=-2 mm
B_second_socket_x = -9.0 * footprint_scale;           // 预留参数，当前关闭

// V25：电极夹孔局部加高/延长座。
// 这里的“加高”是沿电极夹插入方向，也就是 +Y 顶部方向局部外扩 8 mm。
// 作用：让较长的黑色电极夹接口有更多进入/攻丝长度，而不是很快顶到液腔。
include_socket_raised_boss = true;
socket_boss_extra_Y = 8.0;     // 局部向顶部外扩高度/长度
socket_boss_overlap_Y = 4.0;   // V26：加高座向主体内部重叠 4 mm，保证不是只贴边连接
socket_boss_X = 24.0;          // 加高座左右宽度，围住 M12 孔，V26 稍微加宽
socket_boss_R = 3.0;           // 加高座外角圆角

// V22：电极夹孔向靠近膜的一侧平移。
// A 片靠膜侧为 +Z，B 片靠膜侧为 -Z；half_frame() 会自动按 A/B 方向处理。
socket_shift_to_membrane = 2.0;

// M12 孔从顶部贯通到 43x43 液腔，进入液腔少许，确保不是盲孔
socket_entry_into_chamber = 2.0;
socket_top_extra = 0.4;

// V22：M12 大孔与液腔之间增加缩颈小孔
// 上部仍是 10.6 mm 攻丝预孔；靠近液腔的一小段收缩为 6.65 mm。
// 这样黑色电极夹孔不会以大开口直接暴露到 43x43 液腔中。
socket_chamber_opening_d = 6.65;              // 与内部液腔连接处的小开口直径

// V27：限制电极夹口深度。
// 这里指顶部 10.6 mm 的 M12 攻丝预孔深度，V28 从 10 mm 加深到 15 mm。
// 下面继续用 6.65 mm 小孔连接到内部液腔，避免电极夹接口继续深入液腔。
socket_main_bore_depth = 15.0;
socket_main_bore_stop_above_chamber = 0.8;    // 保留旧参数，但 V27 的大孔底部改由 socket_main_bore_depth 控制

// 多单元堆叠示意
stack_units = 3;
stack_gap = 0.08;

// V23：A/B 两片同平面平铺打印间距
flat_print_gap = 10.0;

// =========================
// 基础模块
// =========================
module rounded_rect_2d(w, h, r=0) {
    if (r <= 0) {
        square([w, h], center=true);
    } else {
        offset(r=r)
            square([w-2*r, h-2*r], center=true);
    }
}

module bolt_holes_2d(d=bolt_d) {
    for (x=[-bolt_x, bolt_x])
        for (y=[-bolt_y, bolt_y])
            translate([x, y]) circle(d=d);
}

module side_compression_holes_2d(d=side_compression_hole_d) {
    // 四边中部辅助压紧孔模块保留但 V21 默认关闭
    for (p=[[ side_compression_offset, 0], [-side_compression_offset, 0],
            [0,  side_compression_offset], [0, -side_compression_offset]])
        translate(p) circle(d=d);
}

module chamber_void_2d() {
    // 目标内腔为 43x43，但四角避让 M7 孔，避免液腔与螺丝孔连通。
    // 如果强行用完整直角 43x43，四角会切到 M7 螺丝孔，运行时会漏。
    difference() {
        rounded_rect_2d(chamber_L, chamber_W, chamber_R);
        for (x=[-bolt_x, bolt_x])
            for (y=[-bolt_y, bolt_y])
                translate([x, y]) circle(d=chamber_bolt_keepout_d);
    }
}

module interface_gasket_pocket_2d() {
    // V32 中间液腔密封槽：
    // 不是整张大垫片槽，而是紧贴 43x43 实际液腔外轮廓的一圈“环形密封槽”。
    // 它负责阻断“从 A/B 两片中间缝流出”的路径。
    // 同时在四角螺丝孔周围扣除更大的干区，避免中间垫片槽把液体引到螺丝孔。
    difference() {
        offset(delta=gasket_ring_width)
            chamber_void_2d();
        chamber_void_2d();

        // 螺丝孔附近留干区：中间垫片槽不要进入这个区域
        bolt_holes_2d(gasket_bolt_dry_zone_d);

        if (include_side_compression_holes)
            side_compression_holes_2d(side_compression_hole_d + 2*gasket_pocket_bolt_clearance);
    }
}

module interface_gasket_pocket_cut(face_side=1) {
    // face_side = +1：在 +Z 膜接触面开槽；face_side = -1：在 -Z 膜接触面开槽
    zc = face_side*(half_frame_T/2 - gasket_pocket_depth/2 + 0.02);
    translate([0,0,zc])
        linear_extrude(height=gasket_pocket_depth + 0.08, center=true)
            interface_gasket_pocket_2d();
}

module bolt_washer_seat_cut(face_side=1) {
    // V30：四角螺丝孔外侧浅台阶垫圈座。
    // face_side = +1 表示在 +Z 外侧面开座；face_side = -1 表示在 -Z 外侧面开座。
    // 这里只在每片模块远离膜的外侧面开座，避免破坏中间夹膜密封面。
    zc = face_side*(half_frame_T/2 - bolt_washer_seat_depth/2 + 0.02);
    translate([0,0,zc])
        linear_extrude(height=bolt_washer_seat_depth + 0.08, center=true)
            bolt_holes_2d(bolt_washer_seat_d);
}

function socket_hole_d() = (socket_mode == "tap") ? socket_tap_pilot_d : socket_clearance_d;

module y_axis_cylinder_between(y_top, y_bottom, d, x=0, z=0) {
    len = y_top - y_bottom;
    translate([x, (y_top + y_bottom)/2, z])
        rotate([90, 0, 0]) cylinder(h=len, d=d, center=true);
}

module frame_body() {
    difference() {
        linear_extrude(height=half_frame_T, center=true)
            rounded_rect_2d(outer_L, outer_W, outer_R);

        // 43 x 43 中央贯穿液腔，四角自动避让 M7 螺丝孔
        linear_extrude(height=half_frame_T + 0.4, center=true)
            chamber_void_2d();

        // 四角 M7 通孔
        linear_extrude(height=half_frame_T + 0.4, center=true)
            bolt_holes_2d(bolt_d);

        // 四边中部辅助压紧孔已默认关闭
        if (include_side_compression_holes)
            linear_extrude(height=half_frame_T + 0.4, center=true)
                side_compression_holes_2d(side_compression_hole_d);
    }
}

module socket_raised_boss(socket_x=0) {
    // 电极夹孔局部加高座：
    // V25 是从主体边缘向外加 8 mm；
    // V26 在此基础上向主体内部重叠 socket_boss_overlap_Y，
    // 这样加高座和主体是实心重叠连接，不是只在边界处贴合。
    boss_total_Y = socket_boss_extra_Y + socket_boss_overlap_Y;
    boss_center_Y = outer_W/2 + (socket_boss_extra_Y - socket_boss_overlap_Y)/2;
    translate([socket_x, boss_center_Y, 0])
        linear_extrude(height=half_frame_T, center=true)
            rounded_rect_2d(socket_boss_X, boss_total_Y, socket_boss_R);
}

module socket_bore(socket_x=0, socket_z=0) {
    // V22 分段孔：
    // 1) 从顶部向下 15 mm，为 10.6 mm M12 攻丝预孔；
    // 2) 15 mm 以下到液腔之间改为 6.65 mm 小孔，与 43x43 内部液腔连通；
    // 3) 整个孔沿 Z 方向向膜侧平移 socket_shift_to_membrane。
    y_top = outer_W/2 + (include_socket_raised_boss ? socket_boss_extra_Y : 0) + socket_top_extra;
    // V28：10.6 mm 大孔/攻丝孔从顶部向下最多 15 mm
    y_main_bottom = y_top - socket_main_bore_depth;
    y_small_bottom = chamber_W/2 - socket_entry_into_chamber;

    // M12 攻丝预孔段，不直接进入液腔
    y_axis_cylinder_between(y_top, y_main_bottom, socket_hole_d(), socket_x, socket_z);

    // 与液腔连接的小孔段，液腔侧开口直径为 6.65 mm
    y_axis_cylinder_between(y_main_bottom + 0.05, y_small_bottom, socket_chamber_opening_d, socket_x, socket_z);
}

module socket_oring_seat(socket_x=0, socket_z=0) {
    // V22 默认关闭：保留模块只是为了以后需要时可重新开启。
    y_top = outer_W/2 + (include_socket_raised_boss ? socket_boss_extra_Y : 0) + 0.08;
    y_bottom = y_top - socket_oring_groove_depth;
    y_axis_cylinder_between(y_top, y_bottom, socket_oring_groove_d, socket_x, socket_z);
}

module electrode_rails(rail_side=-1) {
    // rail_side = -1：电极靠 -Z 侧；rail_side = +1：电极靠 +Z 侧
    zc = rail_side*(half_frame_T/2 - rail_T/2 - rail_clearance_z);
    for (sx=[-1, 1]) {
        translate([sx*(chamber_L/2 - rail_w/2), 0, zc])
            cube([rail_w, rail_len, rail_T], center=true);
    }
}

module half_frame(socket_x=0, rail_side=-1, include_second_socket=false, second_socket_x=0, second_socket_z_offset=0) {
    // rail_side = -1 时是 A 片，靠膜方向为 +Z；
    // rail_side = +1 时是 B 片，靠膜方向为 -Z。
    socket_z = -rail_side * socket_shift_to_membrane;

    difference() {
        union() {
            frame_body();

            if (include_electrode_socket && include_socket_raised_boss) {
                socket_raised_boss(socket_x);
                if (include_second_socket)
                    socket_raised_boss(second_socket_x);
            }

            if (include_electrode_rails)
                electrode_rails(rail_side);
        }

        // 膜接触面的垫片定位浅槽：A/B 两片分别开在靠膜的一侧
        if (include_interface_gasket_pocket)
            interface_gasket_pocket_cut(-rail_side);

        // V30：外侧四角螺丝孔垫圈座。
        // A 片外侧是 -Z，B 片外侧是 +Z；rail_side 正好表示外侧方向。
        if (include_bolt_washer_seats)
            bolt_washer_seat_cut(rail_side);

        // 顶部 M12 端面 O 型圈座：V22 默认关闭
        if (include_electrode_socket && include_socket_oring_seat) {
            socket_oring_seat(socket_x, socket_z);
            if (include_second_socket)
                socket_oring_seat(second_socket_x, socket_z + second_socket_z_offset);
        }

        // 顶部 M12 电极孔，由 10.6 mm 主孔 + 6.65 mm 小孔组成。
        // A 片新增第二个孔（有厚度方向错位），B 片仍只有原有的一个孔。
        if (include_electrode_socket) {
            socket_bore(socket_x, socket_z);
            if (include_second_socket)
                socket_bore(second_socket_x, socket_z + second_socket_z_offset);
        }
    }
}

module membrane_template() {
    color([0.95, 0.85, 0.15, 0.55])
    difference() {
        linear_extrude(height=membrane_T, center=true)
            rounded_rect_2d(membrane_L, membrane_W, 1.0);
        if (membrane_has_bolt_holes)
            linear_extrude(height=membrane_T + 0.2, center=true)
                bolt_holes_2d(bolt_d + 0.2);
        if (membrane_has_bolt_holes && include_side_compression_holes)
            linear_extrude(height=membrane_T + 0.2, center=true)
                side_compression_holes_2d(side_compression_hole_d + 0.2);
    }
}

module gasket_cut_template() {
    // V28：定位槽形状单独建成一个薄片。
    // 用途：打印这个薄片后，可以压在硅胶/FKM/EPDM 垫片材料上描线，再按轮廓剪裁。
    // 它的轮廓与 interface_gasket_pocket_2d() 一致。
    color([1.0, 0.65, 0.05, 0.85])
    linear_extrude(height=gasket_template_T, center=true)
        interface_gasket_pocket_2d();
}

module electrode_reference() {
    color([0.55, 0.55, 0.55, 0.85])
    linear_extrude(height=electrode_T, center=true)
        square([electrode_L, electrode_W], center=true);
}

module side_module_reference(t=4.0) {
    color([0.15, 0.15, 0.15, 0.18])
    difference() {
        linear_extrude(height=t, center=true)
            rounded_rect_2d(outer_L, outer_W, outer_R);
        linear_extrude(height=t + 0.3, center=true)
            bolt_holes_2d(7.45); // 仅作原件视觉参考
        if (include_side_compression_holes)
            linear_extrude(height=t + 0.3, center=true)
                side_compression_holes_2d(side_compression_hole_d); // 仅示意外部压板可配合打孔
    }
}

// =========================
// V37 A/B 夹膜垫片面对面、投影重合装配
// =========================
// 装配时 A 靠膜面 = +Z；B 靠膜面 = -Z，密封槽正对。
// A/B 外轮廓、四角 M7 孔在 XY 完全对齐，A/B 原有电极孔沿 X 方向相距 5 mm；A 片新增一个顶部 M12 孔。
// 保留一层膜的名义间隙 0.18 mm，默认不生成膜实体，保证导出的文件仅包含 A 和 B 两块。
// 这是装配展示方向，不适合直接将上下重叠模型作为 3D 打印摆放。
AB_gasket_gap = membrane_T;        // 装配面之间距离，默认0.18mm
AB_exploded_extra_gap = 5.0;       // 仅在爆炸视图模式附加开距

module AB_gasket_face_to_face(extra_gap=0) {
    gap = AB_gasket_gap + extra_gap;
    translate([0, 0, -(half_frame_T + gap)/2])
        color([0.22, 0.48, 0.78, 1.0])
            half_frame(A_socket_x, -1, A_include_second_electrode_socket, A_second_socket_x, A_second_socket_z_offset);
    translate([0, 0,  (half_frame_T + gap)/2])
        color([0.82, 0.54, 0.20, 1.0])
            half_frame(B_socket_x, 1, B_include_second_electrode_socket, B_second_socket_x);
}

// =========================
// 装配预览
// =========================
module single_cell_assembly() {
    z_A = -membrane_T/2 - half_frame_T/2;
    z_B =  membrane_T/2 + half_frame_T/2;

    // A 片：电极在 -Z 侧；B 片：电极在 +Z 侧
    translate([0,0,z_A]) color([0.1,0.25,0.85,0.75]) half_frame(A_socket_x, -1, A_include_second_electrode_socket, A_second_socket_x, A_second_socket_z_offset);
    translate([0,0,z_B]) color([0.1,0.25,0.85,0.75]) half_frame(B_socket_x,  1, B_include_second_electrode_socket, B_second_socket_x);

    // 中间膜
    membrane_template();

    // 两片电极放在各自 half_frame 的液腔内部定位轨位置
    translate([0,0, z_A - (half_frame_T/2 - rail_T - electrode_T/2 - 0.04)]) electrode_reference();
    translate([0,0, z_B + (half_frame_T/2 - rail_T - electrode_T/2 - 0.04)]) electrode_reference();

    // 原电解池侧模块参考
    translate([0,0, z_A - half_frame_T/2 - electrode_T - 2.0]) side_module_reference(4.0);
    translate([0,0, z_B + half_frame_T/2 + electrode_T + 2.0]) side_module_reference(4.0);
}

module scale_stack_demo() {
    unit_pitch = 2*half_frame_T + membrane_T + electrode_T + stack_gap;
    for (i=[0:stack_units-1]) {
        z0 = (i - (stack_units-1)/2) * unit_pitch;
        translate([0,0,z0 - membrane_T/2 - half_frame_T/2]) color([0.1,0.25,0.85,0.60]) half_frame(A_socket_x, -1, A_include_second_electrode_socket, A_second_socket_x, A_second_socket_z_offset);
        translate([0,0,z0]) membrane_template();
        translate([0,0,z0 + membrane_T/2 + half_frame_T/2]) color([0.1,0.25,0.85,0.60]) half_frame(B_socket_x, 1, B_include_second_electrode_socket, B_second_socket_x);
    }
}

module half_frame_A_print() {
    // A 片打印姿态：夹膜面朝下，四角已填平的外侧面朝上。
    // A 片夹膜面在 +Z，所以绕 Y 轴翻转 180°。
    rotate([0, 180, 0]) half_frame(A_socket_x, -1, A_include_second_electrode_socket, A_second_socket_x, A_second_socket_z_offset);
}

module half_frame_B_print() {
    // B 片打印姿态：夹膜面朝下，四角已填平的外侧面朝上。
    // B 片夹膜面本来就在 -Z，所以不需要翻转。
    half_frame(B_socket_x, 1, B_include_second_electrode_socket, B_second_socket_x);
}

module flat_AB_print() {
    // A/B 两片均让四角已填平的外侧面朝上；底部为夹膜面。
    dx = outer_L/2 + flat_print_gap/2;
    translate([-dx, 0, 0]) half_frame_A_print();
    translate([ dx, 0, 0]) half_frame_B_print();
}

module half_frame_A_inner_groove_up_print() {
    // A 片夹膜面在 +Z，所以不翻转时中间垫片槽朝上。
    half_frame(A_socket_x, -1, A_include_second_electrode_socket, A_second_socket_x, A_second_socket_z_offset);
}

module half_frame_B_inner_groove_up_print() {
    // B 片夹膜面在 -Z，需要翻转后让中间垫片槽朝上。
    rotate([180, 0, 0]) half_frame(B_socket_x, 1, B_include_second_electrode_socket, B_second_socket_x);
}

module flat_AB_inner_groove_up_print() {
    // A/B 两片都以“中间夹膜垫片槽朝上”的姿态平铺。
    // 推荐用于优先保证中间液腔密封槽成型质量。
    dx = outer_L/2 + flat_print_gap/2;
    translate([-dx, 0, 0]) half_frame_A_inner_groove_up_print();
    translate([ dx, 0, 0]) half_frame_B_inner_groove_up_print();
}


// ============================================
// V37 附加示意：1号孔(B片) + 3号孔(A片)下方正交插入电极
// ============================================
// 仍沿用原有 half_frame() 真正打印几何，不影响 A/B 本体模型。
// 电解池大片表面位于 XY 平面，垂直电极片表面位于 YZ 平面。
// 因单侧腔体厚度 20mm，30x30电极不可能无干涉地垂直置入；
// 先用 Y向30mm × Z向14mm 的片形占位，后续应按真实电极尺寸再决定设计。
cross_plate_height_y = 30.0 * footprint_scale;   // 片高(Y轴): 30 mm
cross_plate_width_z = 14.0;    // 片宽(Z轴): 14 mm，单腔20mm内两侧留余量
cross_plate_thickness_x = 0.35;// 板厚(X轴): 0.35 mm
cross_plate_top_y = chamber_W/2 - 5.5;      // 片顶Y坐标；内腔顶Y=21.5mm
cross_rod_d = 3.0;             // 导电杆示意，非真实固定结构
cross_rod_y_top = outer_W/2 + socket_boss_extra_Y + 0.25;
cross_plate_A_color = [0.00, 0.76, 0.59, 1.0]; // 绿色: A片3号孔电极
cross_plate_B_color = [0.88, 0.22, 0.44, 1.0]; // 红色: B片1号孔电极
cross_frame_A_color = [0.17, 0.43, 0.95, 0.25];
cross_frame_B_color = [1.0, 0.59, 0.13, 0.25];
cross_show_membrane = true;
cross_show_rod = true;

// 板实体只在内部显示；不合并进反应器塑料结构。
module cross_electrode_under(x, z_world, c=[0.1,0.8,0.6,1]) {
    y_center = cross_plate_top_y - cross_plate_height_y/2;
    color(c)
        translate([x, y_center, z_world])
            cube([cross_plate_thickness_x, cross_plate_height_y, cross_plate_width_z], center=true);
    if (cross_show_rod) {
        color([0.85,0.85,0.88,1.0])
            y_axis_cylinder_between(cross_rod_y_top, cross_plate_top_y-1.0,
                                    cross_rod_d, x, z_world);
    }
}

// 组合示意。extra_gap=0为面对面正常间隙；正数用于观察内部电极。
module cross_electrode_assembly(extra_gap=0) {
    gap = AB_gasket_gap + extra_gap;
    z_A = -(half_frame_T + gap)/2;
    z_B = +(half_frame_T + gap)/2;
    // 保持垫片槽相对，外框和膜半透明（纯视觉，不修改CAD打印几何）
    translate([0,0,z_A])
        color(cross_frame_A_color)
            half_frame(A_socket_x, -1, A_include_second_electrode_socket,
                       A_second_socket_x, A_second_socket_z_offset);
    translate([0,0,z_B])
        color(cross_frame_B_color)
            half_frame(B_socket_x, 1, B_include_second_electrode_socket, B_second_socket_x);
    if (cross_show_membrane)
        color([0.94, 0.89, 0.21, 0.20]) membrane_template();
    // 孔3: A块第二M12，local Z = +2-4=-2
    cross_electrode_under(A_second_socket_x,
        z_A + socket_shift_to_membrane + A_second_socket_z_offset,
        cross_plate_A_color);
    // 孔1: B块唯一M12，local Z = -2
    cross_electrode_under(B_socket_x,
        z_B - socket_shift_to_membrane,
        cross_plate_B_color);
    // 孔2: A块旧孔保留接口，但不放电极片
}

// 两个腔体的线框装配示意：用矩形线条表示A/B外边界，
// 真实池体请切换到 cross_electrode_assembly / 原有打印模式。
module cross_wire_segment(p,q,d=0.65) {
    hull() {
        translate(p) sphere(d=d, $fn=12);
        translate(q) sphere(d=d, $fn=12);
    }
}
module cross_frame_wire(zmid, tint=[0.3,0.6,0.9,1]) {
    color(tint)
        for (zz=[-half_frame_T/2,half_frame_T/2]) {
            for (xx=[-outer_L/2,outer_L/2])
                cross_wire_segment([xx,-outer_W/2,zmid+zz],[xx,outer_W/2,zmid+zz]);
            for (yy=[-outer_W/2,outer_W/2])
                cross_wire_segment([-outer_L/2,yy,zmid+zz],[outer_L/2,yy,zmid+zz]);
        }
    color(tint)
        for (xx=[-outer_L/2,outer_L/2], yy=[-outer_W/2,outer_W/2])
            cross_wire_segment([xx,yy,zmid-half_frame_T/2],[xx,yy,zmid+half_frame_T/2]);
}
module cross_electrode_wireframe() {
    z_A=-(half_frame_T+AB_gasket_gap)/2;
    z_B=+(half_frame_T+AB_gasket_gap)/2;
    cross_frame_wire(z_A,[0.14,0.44,0.90,1]);
    cross_frame_wire(z_B,[0.99,0.60,0.17,1]);
    cross_electrodes_only();
}

// 单片局部示意，方便检查不同的孔和电极位置。
module cross_electrode_A_detail() {
    z_A=0;
    color(cross_frame_A_color)
        half_frame(A_socket_x, -1, A_include_second_electrode_socket,
                   A_second_socket_x, A_second_socket_z_offset);
    cross_electrode_under(A_second_socket_x, socket_shift_to_membrane + A_second_socket_z_offset, cross_plate_A_color);
}

module cross_electrode_B_detail() {
    color(cross_frame_B_color)
        half_frame(B_socket_x, 1, B_include_second_electrode_socket, B_second_socket_x);
    cross_electrode_under(B_socket_x, -socket_shift_to_membrane, cross_plate_B_color);
}

module cross_electrodes_only() {
    z_A=-(half_frame_T + membrane_T)/2;
    z_B=+(half_frame_T + membrane_T)/2;
    cross_electrode_under(A_second_socket_x,
        z_A + socket_shift_to_membrane + A_second_socket_z_offset, cross_plate_A_color);
    cross_electrode_under(B_socket_x,
        z_B - socket_shift_to_membrane, cross_plate_B_color);
}

// =========================
// 输出
// =========================
if (part == "cross_electrode_assembly") {
    cross_electrode_assembly();
} else if (part == "cross_electrode_exploded") {
    cross_electrode_assembly(8.0);
} else if (part == "cross_electrode_wireframe") {
    cross_electrode_wireframe();
} else if (part == "cross_electrode_A_detail") {
    cross_electrode_A_detail();
} else if (part == "cross_electrode_B_detail") {
    cross_electrode_B_detail();
} else if (part == "electrodes_only") {
    cross_electrodes_only();
} else if (part == "AB_gasket_face_to_face") {
    AB_gasket_face_to_face();
} else if (part == "AB_gasket_exploded") {
    AB_gasket_face_to_face(AB_exploded_extra_gap);
} else if (part == "single_cell_assembly") {
    single_cell_assembly();
} else if (part == "half_frame_A") {
    half_frame(A_socket_x, -1, A_include_second_electrode_socket, A_second_socket_x, A_second_socket_z_offset);
} else if (part == "half_frame_B") {
    half_frame(B_socket_x, 1, B_include_second_electrode_socket, B_second_socket_x);
} else if (part == "half_frame_A_print") {
    half_frame_A_print();
} else if (part == "half_frame_B_print") {
    half_frame_B_print();
} else if (part == "membrane_template") {
    membrane_template();
} else if (part == "gasket_cut_template") {
    gasket_cut_template();
} else if (part == "electrode_reference") {
    electrode_reference();
} else if (part == "scale_stack_demo") {
    scale_stack_demo();
} else if (part == "flat_AB_print") {
    flat_AB_print();
} else if (part == "half_frame_A_inner_groove_up_print") {
    half_frame_A_inner_groove_up_print();
} else if (part == "half_frame_B_inner_groove_up_print") {
    half_frame_B_inner_groove_up_print();
} else if (part == "flat_AB_inner_groove_up_print") {
    flat_AB_inner_groove_up_print();
} else {
    single_cell_assembly();
}
