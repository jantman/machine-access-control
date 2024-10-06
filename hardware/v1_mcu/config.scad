function inch(n) = n * 25.4;
function mm(n) = n;
function mm_inside_inch_scale(n) = n / 25.4;
include <dims.scad>;

// BEGIN YAPPbox
wallThickness       = mm(4.0);
basePlaneThickness  = mm(4.0);
baseWallHeight      = inch(1.5);
// END YAPPbox

panel_thickness = 0.15; // front/top wall thickness (where the controls are)
wall_thickness = 0.15; // thickness of all other walls

lcd_display_depth = 0.110;
lcd_display_height = 0.960;
lcd_hole_dia = 0.120;
lcd_display_padding = 0.030;
lcd_display_y_inset = 0.205 - (lcd_display_padding / 2) + (lcd_hole_dia / 2);
lcd_centerline = (lcd_display_height / 2) + lcd_display_y_inset;
lcd_hole_x_inset = 0.042;
lcd_hole_x_spacing = 2.970;
lcd_hole_y_inset = 0.042;
lcd_hole_y_spacing = 1.218;

relay_length = 2.765;
relay_width = 0.685;

esp32_hole_dia = 0.118;
esp32_hole_x_inset = 0.742 + (esp32_hole_dia / 2);
esp32_hole_x_spacing = 0.397;
esp32_hole_y_inset = 0.588 + (esp32_hole_dia / 2);
esp32_hole_y_spacing = 1.397;

// for mounting nut catches
initial_layer_height = 0.2; // mm
layer_height = 0.16; // mm
wall_line_width = 0.4; // mm
mounting_nut_key = 7; // 7mm for M4 hex nut
mounting_nut_height = 3.2; // 3.2mm for M4 hex nut
mounting_screw_bore_dia = m4_clearance;
mounting_screw_bore_length = 9; // let's try that, about 3x the nut height
mounting_screw_block_width = 12;
side_mounting_center_to_center = inch(1.912);
mount_extra_height = (baseWallHeight - mounting_screw_block_width) / 2;
