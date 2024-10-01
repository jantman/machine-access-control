
module bottom_layer() {
    include <config.scad>
    difference() {
        my_roundedcube(overall_width, overall_height, material_thickness, 1/8);
        // card cutout
        translate([side_support_width, bottom_support_height, -0.1]) {
            my_roundedcube(card_cutout_width, overall_height, material_thickness + 0.2, 1/4);
        }
        // card cutout left fillet
        translate([side_support_width + 0.001, overall_height, -0.1]) {
            shoulder_fillet(1/8, material_thickness + 0.2, on_side="left");
        }
        // card cutout right fillet
        translate([overall_width - side_support_width - 0.001, overall_height, -0.1]) {
            shoulder_fillet(1/8, material_thickness + 0.2, on_side="right");
        }
        // drain slot
        translate([overall_width / 2, bottom_support_height + 0.001, 0]) {
            drain_slot(width = 0.25);
        }
        //
        // mounting holes
        //
        // bottom left
        translate([side_support_width / 2, bottom_support_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // bottom right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), bottom_support_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // middle left
        translate([side_support_width / 2, overall_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // middle right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), overall_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // top left
        translate([side_support_width / 2, overall_height - (bottom_support_height / 2) - top_tab_height, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // top right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), overall_height - (bottom_support_height / 2) - top_tab_height, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
    }
}

module middle_layer() {
    include <config.scad>
    difference() {
        my_roundedcube(overall_width, cover_plate_height, material_thickness, 1/8);
        // fob cutout
        translate([(overall_width - fob_cutout_width) / 2, cover_plate_height - fob_cutout_depth, -0.1]) {
            my_roundedcube(fob_cutout_width, fob_cutout_depth + 1/4, material_thickness + 0.2, 1/4);
        }
        // drain slot
        translate([overall_width / 2, (cover_plate_height - fob_cutout_depth) + 0.001, 0]) {
            drain_slot(width = 0.25, fillet_radius = 0.25);
        }
        // fob cutout left fillet
        translate([((overall_width - fob_cutout_width) / 2) + 0.001, cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, material_thickness + 0.2, on_side="left");
        }
        // fob cutout right fillet
        translate([((overall_width - fob_cutout_width) / 2) + fob_cutout_width - 0.001, cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, material_thickness + 0.2, on_side="right");
        }
        //
        // mounting holes
        //
        // bottom left
        translate([side_support_width / 2, bottom_support_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // bottom right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), bottom_support_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // middle left
        translate([side_support_width / 2, overall_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // middle right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), overall_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // top left
        translate([side_support_width / 2, overall_height - (bottom_support_height / 2) - top_tab_height, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // top right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), overall_height - (bottom_support_height / 2) - top_tab_height, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
    }
}

module top_layer() {
    include <config.scad>
    difference() {
        my_roundedcube(overall_width, cover_plate_height, material_thickness, 1/8);
        // fob keychain cutout
        translate([(overall_width - fob_slot_width) / 2, cover_plate_height - fob_cutout_depth, -0.1]) {
            my_roundedcube(fob_slot_width, fob_cutout_depth + 1/4, material_thickness + 0.2, 1/8);
        }
        // card cutout left fillet
        translate([((overall_width - fob_slot_width) / 2) + 0.001, cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, material_thickness + 0.2, on_side="left");
        }
        // card cutout right fillet
        translate([((overall_width - fob_slot_width) / 2) + fob_slot_width - 0.001, cover_plate_height, -0.1]) {
            shoulder_fillet(1/8, material_thickness + 0.2, on_side="right");
        }
        //
        // mounting holes
        //
        // bottom left
        translate([side_support_width / 2, bottom_support_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // bottom right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), bottom_support_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // middle left
        translate([side_support_width / 2, overall_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // middle right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), overall_height / 2, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // top left
        translate([side_support_width / 2, overall_height - (bottom_support_height / 2) - top_tab_height, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
        // top right
        translate([side_support_width + card_cutout_width + (side_support_width / 2), overall_height - (bottom_support_height / 2) - top_tab_height, -0.1]) {
            cylinder(d=mounting_hole_dia, h=material_thickness + 0.2);
        }
    }
}

module drain_slot(width = 0.5, fillet_radius = 0.5) {
    include <config.scad>
    translate([0, 0, -0.1]) {
        union() {
            translate([-1 * (width / 2), -4, 0]) {
                cube([width, 4, material_thickness + 0.2]);
            }
            translate([(-1 * (width / 2)) + 0.001, 0, 0]) {
                shoulder_fillet(fillet_radius, material_thickness + 0.2, on_side="left");
            }
            translate([((width / 2)) - 0.001, 0, 0]) {
                shoulder_fillet(fillet_radius, material_thickness + 0.2, on_side="right");
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
