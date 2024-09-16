// FROM: https://github.com/jantman/machine-access-control ; MIT license
// dimensioned in inches
$fn = 360;

relay();

module relay() {
    translate([0, 0, 0]) {
        difference() {
            union() {
                cube([2.765, 0.685, 0.060]); // PCB
                translate([(2.765-2.375)/2, (0.685-0.622)/2, -1 * 0.0975]) {
                    cube([2.375, 0.622, 0.609 + 0.060 + 0.0975]);
                }
            }
            relay_mounting_holes();
        }
    }
}

module relay_mounting_holes() {
    translate([(2.765-2.601)/2, (0.622-0.518)/2, -0.5]) {
        cylinder(d=0.101, h=1);
    }
    translate([(2.765-2.601)/2, ((0.622-0.518)/2) + 0.518, -0.5]) {
        cylinder(d=0.101, h=1);
    }
    translate([((2.765-2.601)/2) + 2.601, (0.622-0.501)/2, -0.5]) {
        cylinder(d=0.101, h=1);
    }
    translate([((2.765-2.601)/2) + 2.601, ((0.622-0.501)/2) + 0.501, -0.5]) {
        cylinder(d=0.101, h=1);
    }
}
