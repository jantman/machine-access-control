$fn = 360;

include <config.scad>
use <modules.scad>

//show_stacked = "true";
show_stacked = "false";
sliced = "true";

if(show_stacked == "true") {
    bottom_layer();
    translate([0, 0, rfid_material_thickness]) {
        middle_layer();
    }
    translate([0, 0, rfid_material_thickness * 2]) {
        top_layer();
    }
} else {
    if(sliced == "true") {
        projection(cut=true) {
            translate([0, 0, -1 * (rfid_material_thickness / 2)]) {
                bottom_layer();
                translate([rfid_overall_width + rfid_multipart_offset, 0, 0]) {
                    middle_layer();
                }
                translate([(rfid_overall_width + rfid_multipart_offset) * 2, 0, 0]) {
                    top_layer();
                }
            }
        }
    } else {
        bottom_layer();
        translate([rfid_overall_width + rfid_multipart_offset, 0, 0]) {
            middle_layer();
        }
        translate([(rfid_overall_width + rfid_multipart_offset) * 2, 0, 0]) {
            top_layer();
        }
    }
}
