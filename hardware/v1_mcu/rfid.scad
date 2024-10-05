// FROM: https://github.com/jantman/machine-access-control ; MIT license
// dimensioned in inches
$fn = 360;

rfid();

module rfid() {
    hole_dia = 0.131;
    translate([0, 0, 0]) {
        difference() {
            union() {
                cube([1.860, 1.030, 0.040]);
                translate([0, (1.030-0.45)/2, 0.040]) {
                    cube([0.178, 0.45, 0.145]); // connector
                }
                translate([0.425, (1.030-1.000)/2, 0.040]) {
                    cube([1.000, 1.000, 0.092]); // antenna
                }
            }
            rfid_mounting_holes();
        }
    }
}

module rfid_mounting_holes() {
    hole_dia = 0.131;
    translate([0.137 + (hole_dia/2), 1.030 - (0.140 + (hole_dia/2)), -0.5]) {
        cylinder(d=hole_dia, h=1);
    }
    translate([1.860 - (0.130 + (hole_dia/2)), 0.132 + (hole_dia/2), -0.5]) {
        cylinder(d=hole_dia, h=1);
    }
}
