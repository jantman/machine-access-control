$fn = 360;

include <config.scad>
use <modules.scad>

projection(cut=true) {
    translate([0, 0, -1 * (rfid_material_thickness / 2)]) {
        top_layer();
    }
}
