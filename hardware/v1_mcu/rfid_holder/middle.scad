$fn = 360;

include <config.scad>
use <modules.scad>

projection(cut=true) {
    translate([0, 0, -1 * (rfid_material_thickness / 2)]) {
        intersection() {
            middle_layer();
            cube([rfid_overall_width / 2, rfid_overall_height, rfid_material_thickness]);
        }
    }
}
