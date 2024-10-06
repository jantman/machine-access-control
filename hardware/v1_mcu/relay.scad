// FROM: https://github.com/jantman/machine-access-control ; MIT license
// dimensioned in inches
$fn = 360;

relay();

module relay() {
    include <config.scad>;
    translate([0, 0, 0]) {
        difference() {
            union() {
                cube([relay_length, relay_width, 0.060]); // PCB
                translate([(relay_length-2.375)/2, (relay_width-0.622)/2, -1 * 0.0975]) {
                    cube([2.375, 0.622, 0.609 + 0.060 + 0.0975]);
                }
            }
            relay_mounting_holes();
        }
    }
}

module relay_mounting_holes() {
    include <config.scad>;
    translate([(relay_length-2.601)/2, (0.622-0.518)/2, -0.5]) {
        cylinder(d=0.101, h=1);
    }
    translate([(relay_length-2.601)/2, ((0.622-0.518)/2) + 0.518, -0.5]) {
        cylinder(d=0.101, h=1);
    }
    translate([((relay_length-2.601)/2) + 2.601, (0.622-0.501)/2, -0.5]) {
        cylinder(d=0.101, h=1);
    }
    translate([((relay_length-2.601)/2) + 2.601, ((0.622-0.501)/2) + 0.501, -0.5]) {
        cylinder(d=0.101, h=1);
    }
}
