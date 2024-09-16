// FROM: https://github.com/jantman/machine-access-control ; MIT license
// dimensioned in inches
$fn = 360;

//neopixel();

module neopixel() {
    protrusion_dia = 0.301;
    union() {
        translate([0, 0, -1.38]) {
            cylinder(h=1.38, d=0.5);
        }
        translate([0, 0, 0.301 / 2]) {
            sphere(d=protrusion_dia);
        }
        cylinder(d=0.301, h=0.301/2);
    }
}
