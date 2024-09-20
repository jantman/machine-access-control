use <esp32.scad>;
use <neopixel.scad>;
use <relay.scad>;
use <rfid.scad>;
use <esp32.scad>;
use <lcd.scad>;

$fn = 360;

intersection() {
    difference() {
        cube([5, 2.5, 1/8]);
        translate([0, 0, -0.05]) {
            translate([-0.5, -0.5, 0]) {
                esp32_hole_pattern();
            }
            translate([0.5, 0.875, 0]) {
                // GX16-8
                conn_diameter = 0.615;
                cylinder(d=conn_diameter + 0.020, h=1);
            }
            translate([1.25, 1.25, 0]) {
                // neopixel
                cylinder(d=0.301 + 0.020, h=1);
            }
            translate([1.25, 0.5, 0]) {
                // oops button
                conn_diameter = 0.625;
                cylinder(d=conn_diameter + 0.020, h=1);
            }
            translate([0, 0.125, 0]) {
                // relay mounting holes
                relay_mounting_holes();
            }
            translate([0.8, 0.14, 0]) {
                rfid_mounting_holes();
            }
            translate([1.5, 1, 0]) {
                lcd_hole_dia = 0.120;
                lcd();
                lcd_mounting_holes();
            }
        }
        // just to verify orientation
        translate([2, 2.3, -0.1]) {
            cube([0.1, 0.05, 1]);
        }
    }
    translate([1.5, 1, 0]) {
        cube([3.25, 1.420, 0.064]); // PCB
    }
}
