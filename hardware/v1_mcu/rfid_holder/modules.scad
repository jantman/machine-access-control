module rfid_holder_mounting_holes() {
    include <./config.scad>
    //
    // mounting holes
    //
    // bottom left
    translate([rfid_side_support_width / 2, rfid_bottom_support_height / 2, -0.1]) {
        cylinder(d=rfid_mounting_hole_dia, h=rfid_material_thickness + 200);
    }
    // bottom right
    translate([rfid_side_support_width + rfid_card_cutout_width + (rfid_side_support_width / 2), rfid_bottom_support_height / 2, -0.1]) {
        cylinder(d=rfid_mounting_hole_dia, h=rfid_material_thickness + 200);
    }
    // middle left
    translate([rfid_side_support_width / 2, rfid_overall_height / 2, -0.1]) {
        cylinder(d=rfid_mounting_hole_dia, h=rfid_material_thickness + 200);
    }
    // middle right
    translate([rfid_side_support_width + rfid_card_cutout_width + (rfid_side_support_width / 2), rfid_overall_height / 2, -0.1]) {
        cylinder(d=rfid_mounting_hole_dia, h=rfid_material_thickness + 200);
    }
    // top left
    translate([rfid_side_support_width / 2, rfid_overall_height - (rfid_bottom_support_height / 2) - rfid_top_tab_height, -0.1]) {
        cylinder(d=rfid_mounting_hole_dia, h=rfid_material_thickness + 200);
    }
    // top right
    translate([rfid_side_support_width + rfid_card_cutout_width + (rfid_side_support_width / 2), rfid_overall_height - (rfid_bottom_support_height / 2) - rfid_top_tab_height, -0.1]) {
        cylinder(d=rfid_mounting_hole_dia, h=rfid_material_thickness + 200);
    }
}

module bottom_layer() {
    include <config.scad>
    difference() {
        my_roundedcube(rfid_overall_width, rfid_overall_height, rfid_material_thickness, 1/8);
        // card cutout
        translate([rfid_side_support_width, rfid_bottom_support_height, -0.1]) {
            my_roundedcube(rfid_card_cutout_width, rfid_overall_height, rfid_material_thickness + 0.2, 1/4);
        }
        // card cutout left fillet
        translate([rfid_side_support_width + 0.001, rfid_overall_height, -0.1]) {
            shoulder_fillet(1/8, rfid_material_thickness + 0.2, on_side="left");
        }
        // card cutout right fillet
        translate([rfid_overall_width - rfid_side_support_width - 0.001, rfid_overall_height, -0.1]) {
            shoulder_fillet(1/8, rfid_material_thickness + 0.2, on_side="right");
        }
        // drain slot
        translate([rfid_overall_width / 2, rfid_bottom_support_height + 0.001, 0]) {
            drain_slot(width = 0.25);
        }
        rfid_holder_mounting_holes();
    }
}

module middle_layer() {
    include <config.scad>
    difference() {
        my_roundedcube(rfid_overall_width, rfid_cover_plate_height, rfid_material_thickness, 1/8);
        // fob cutout
        translate([(rfid_overall_width - rfid_fob_cutout_width) / 2, rfid_cover_plate_height - fob_cutout_depth, -0.1]) {
            my_roundedcube(rfid_fob_cutout_width, fob_cutout_depth + 1/4, rfid_material_thickness + 0.2, 1/4);
        }
        // drain slot
        translate([rfid_overall_width / 2, (rfid_cover_plate_height - fob_cutout_depth) + 0.001, 0]) {
            drain_slot(width = 0.25, fillet_radius = 0.25);
        }
        // fob cutout left fillet
        translate([((rfid_overall_width - rfid_fob_cutout_width) / 2) + 0.001, rfid_cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, rfid_material_thickness + 0.2, on_side="left");
        }
        // fob cutout right fillet
        translate([((rfid_overall_width - rfid_fob_cutout_width) / 2) + rfid_fob_cutout_width - 0.001, rfid_cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, rfid_material_thickness + 0.2, on_side="right");
        }
        rfid_holder_mounting_holes();
    }
}

module top_layer() {
    include <config.scad>
    difference() {
        my_roundedcube(rfid_overall_width, rfid_cover_plate_height, rfid_material_thickness, 1/8);
        // fob keychain cutout
        translate([(rfid_overall_width - rfid_fob_slot_width) / 2, rfid_cover_plate_height - fob_cutout_depth, -0.1]) {
            my_roundedcube(rfid_fob_slot_width, fob_cutout_depth + 1/4, rfid_material_thickness + 0.2, 1/8);
        }
        // card cutout left fillet
        translate([((rfid_overall_width - rfid_fob_slot_width) / 2) + 0.001, rfid_cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, rfid_material_thickness + 0.2, on_side="left");
        }
        // card cutout right fillet
        translate([((rfid_overall_width - rfid_fob_slot_width) / 2) + rfid_fob_slot_width - 0.001, rfid_cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, rfid_material_thickness + 0.2, on_side="right");
        }
        rfid_holder_mounting_holes();
    }
}

module drain_slot(width = 0.5, fillet_radius = 0.5) {
    include <config.scad>
    translate([0, 0, -0.1]) {
        union() {
            translate([-1 * (width / 2), -4, 0]) {
                cube([width, 4, rfid_material_thickness + 0.2]);
            }
            translate([(-1 * (width / 2)) + 0.001, 0, 0]) {
                shoulder_fillet(fillet_radius, rfid_material_thickness + 0.2, on_side="left");
            }
            translate([((width / 2)) - 0.001, 0, 0]) {
                shoulder_fillet(fillet_radius, rfid_material_thickness + 0.2, on_side="right");
            }
        }
    }
}

module shoulder_fillet(r, t, on_side = "left") {
    include <config.scad>
    xtcorner = (on_side == "left") ? r : 0;
    xtobj = (on_side == "left") ? -2 * r : 0;
    translate([xtobj, -2 * r, 0]) {
        intersection() {
            difference() {
                cube([r * 2, r * 2, t]);
                translate([r, r, -0.1]) {
                    cylinder(r=r, h=t + 0.2);
                }
            }
            translate([xtcorner, r, 0]) {
                cube([r, r, t]);
            }
        }
    }
}

module my_roundedcube(x, y, t, r) {
    // x = x width
    // y = y length
    // t = thickness
    // r = corner radius
    $fn = 50;
    translate([r, r, 0]) {
        minkowski() {
            cube([x - (r * 2), y - (r * 2), t / 2]);
            cylinder(r=r, h=t/2);
        }
    }
}
