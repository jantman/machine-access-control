lcd();

module lcd(display_padding = 0.030) {
    hole_dia = 0.120;
    translate([0, 0, -0.064]) {
        difference() {
            union() {
                cube([3.152, 1.420, 0.064]); // PCB
                translate([0.170 - (display_padding / 2), 0.205 - (display_padding / 2) + (hole_dia / 2), 0]) {
                    cube([2.805 + display_padding, 0.960 + display_padding, 0.275]); // display
                }
                i2c_height = (0.690 - (0.275 + 0.064));
                translate([0, 1.420 - (0.790 + 0.040), -1 * i2c_height]) {
                    cube([2.160, 0.790, i2c_height]); // I2C backpack
                }
                translate([0.170 + 2.805, 0.447, 0]) {
                    linear_extrude(height=0.110, center=false) {
                        polygon(points=[[0, 0], [0.113, 0.103], [0.113, 0.393], [0, 0.496]]); // backlight
                    }
                }
            }
            lcd_mounting_holes();
        }
    }
}

module lcd_mounting_holes() {
    $fn = 360;
    hole_dia = 0.120;
    hole_x_inset = 0.042;
    hole_x_spacing = 2.970;
    hole_y_inset = 0.042;
    hole_y_spacing = 1.218;
    translate([hole_x_inset + (hole_dia / 2), hole_y_inset + hole_dia, -0.5]) {
        cylinder(d=hole_dia, h=1);
    }
    translate([hole_x_inset + (hole_dia / 2), hole_y_inset + hole_dia + hole_y_spacing, -0.5]) {
        cylinder(d=hole_dia, h=1);
    }
    translate([hole_x_inset + (hole_dia / 2) + hole_x_spacing, hole_y_inset + hole_dia, -0.5]) {
        cylinder(d=hole_dia, h=1);
    }
    translate([hole_x_inset + (hole_dia / 2) + hole_x_spacing, hole_y_inset + hole_dia + hole_y_spacing, -0.5]) {
        cylinder(d=hole_dia, h=1);
    }
}
