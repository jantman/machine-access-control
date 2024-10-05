lcd();

module lcd() {
    include <config.scad>;
    translate([0, 0, -1 * lcd_display_depth]) {
        difference() {
            union() {
                cube([3.152, 1.520, 0.064]); // PCB
                translate([0.170 - (lcd_display_padding / 2), lcd_display_y_inset, 0]) {
                    cube([2.805 + lcd_display_padding, lcd_display_height + lcd_display_padding, 0.275]); // display
                }
                i2c_height = (0.690 - (0.275 + 0.064));
                translate([0, 1.420 - (0.790 + 0.040), -1 * i2c_height]) {
                    cube([2.160, 0.790, i2c_height]); // I2C backpack
                }
                translate([0.170 + 2.805, 0.447, 0]) {
                    linear_extrude(height=lcd_display_depth, center=false) {
                        polygon(points=[[0, 0], [0.113, 0.103], [0.113, 0.393], [0, 0.496]]); // backlight
                    }
                }
            }
            lcd_mounting_holes();
        }
    }
}

module lcd_mounting_holes() {
    include <config.scad>;
    $fn = 360;
    translate([lcd_hole_x_inset + (lcd_hole_dia / 2), lcd_hole_y_inset + lcd_hole_dia, -0.5]) {
        cylinder(d=lcd_hole_dia, h=1);
    }
    translate([lcd_hole_x_inset + (lcd_hole_dia / 2), lcd_hole_y_inset + lcd_hole_dia + lcd_hole_y_spacing, -0.5]) {
        cylinder(d=lcd_hole_dia, h=1);
    }
    translate([lcd_hole_x_inset + (lcd_hole_dia / 2) + lcd_hole_x_spacing, lcd_hole_y_inset + lcd_hole_dia, -0.5]) {
        cylinder(d=lcd_hole_dia, h=1);
    }
    translate([lcd_hole_x_inset + (lcd_hole_dia / 2) + lcd_hole_x_spacing, lcd_hole_y_inset + lcd_hole_dia + lcd_hole_y_spacing, -0.5]) {
        cylinder(d=lcd_hole_dia, h=1);
    }
}
