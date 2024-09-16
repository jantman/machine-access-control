//esp32();

module esp32() {
    board_thickness = 0.060;
    board_width = 2.000;
    board_depth = 2.700;
    bottom_pin_length = 0.483 - (0.060 + 0.342);
    difference() {
        union() {
            cube([board_width, board_depth, board_thickness]);
            translate([0.175, 0.039, -1 * bottom_pin_length]) {
                cube([0.282, 2.642, 0.483]); // left screw terminals
            }
            translate([board_width - (0.175 + 0.282), 0.039, -1 * bottom_pin_length]) {
                cube([0.282, 2.642, 0.483]); // left screw terminals
            }
            translate([0.175 + 0.282, 0.393, 0]) {
                cube([1.108, 2.171, 0.616]); // ESP
            }
        }
        esp32_hole_pattern();
    }
}

module esp32_hole_pattern() {
    $fn = 360;
    hole_dia = 0.118;
    hole_x_inset = 0.742 + (hole_dia / 2);
    hole_x_spacing = 0.397;
    hole_y_inset = 0.588 + (hole_dia / 2);
    hole_y_spacing = 1.397;
    translate([hole_x_inset, hole_y_inset, -0.01]) {
        cylinder(d=hole_dia, h=1);
    }
    translate([hole_x_inset + hole_x_spacing, hole_y_inset, -0.01]) {
        cylinder(d=hole_dia, h=1);
    }
    translate([hole_x_inset, hole_y_inset + hole_y_spacing, -0.01]) {
        cylinder(d=hole_dia, h=1);
    }
    translate([hole_x_inset + hole_x_spacing, hole_y_inset + hole_y_spacing, -0.01]) {
        cylinder(d=hole_dia, h=1);
    }
}
