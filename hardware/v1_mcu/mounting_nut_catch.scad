difference() {
  mounting_nut_catch(part="block", face="wall", wall_centerline_height = 6);
  mounting_nut_catch(part="hole", face="wall", wall_centerline_height = 6);
}

translate([20, 0, 0]) {
  difference() {
    mounting_nut_catch(part="block");
    mounting_nut_catch(part="hole");
  }
}

module mounting_nut_catch(part = "block", face = "base", wall_centerline_height = 0) {
  /*
  Generates the mounting nut catches, either the support block (part == block) or the difference object for the screw hole and nut catch (part == hole).
  Parts are generated with the origin at the outside end of the screw clearance hole (Z), centered on its axis (X and Y).
  If face == "base", the part is oriented for use on the base and raised the appropriate height over the base plane for a 2-layer outside skin over the hole.
  If face == "wall", the part is oriented for use on a side wall and inset the appropriate height from the outside wall edge for a 2-layer outside skin over the hole.
  If face == "wall", set wall_centerline_height to the height that you want the screw centerline at, if higher than the default (mounting_screw_block_width / 2).
  */
  include <config.scad>;
  assert((part == "block" || part == "hole"), "mounting_nut_catch part must be block or hole");
  assert((face == "base" || face == "wall"), "mounting_nut_catch face must be base or wall");
  trans_vec = face == "base"
    ? [0, 0, initial_layer_height + layer_height]
    : [0, wall_line_width * 2, (mounting_screw_block_width / 2)];
  rot_vec = face == "base"
    ? [0, 0, 0]
    : [-90, 0, 0];
  block_trans_z = face == "base" ? (-1 * (initial_layer_height + layer_height)) : 0;
  translate(trans_vec) {
    rotate(rot_vec) {
      if(part == "block") {
        translate([mounting_screw_block_width / -2, (mounting_screw_block_width / -2) - wall_centerline_height, block_trans_z]) { // translate to center on XY
          cube([mounting_screw_block_width, mounting_screw_block_width + wall_centerline_height, mounting_screw_bore_length + mounting_nut_height]);
        } // translate to center on XY
      } else {
        translate([0, -1 * wall_centerline_height, 0]) {
          // nut trap itself
          translate([0, 0, mounting_screw_bore_length - 0.01]) {
            cylinder(r = mounting_nut_key / 2 / cos(180 / 6) + 0.05, h=mounting_nut_height + 0.1, $fn=6);
          } // translate
          // the screw clearance bore
          cylinder(d=mounting_screw_bore_dia, h=mounting_screw_bore_length, $fn=360);
        } // translate
      } // if part
    } // rotate
  } // translate
}

module mounting_nut_block_with_hole(face = "base", wall_centerline_height = 0) {
  include <config.scad>;
  difference() {
    mounting_nut_catch(part="block", face = "base", wall_centerline_height = 0);
    tr = face == "base" ? [0, 0, (-1 * (initial_layer_height + layer_height + 0.001))] : [0, 0, 0];
    translate(tr) {
      mounting_nut_catch(part="hole", face = "base", wall_centerline_height = 0);
    }
  }
}
