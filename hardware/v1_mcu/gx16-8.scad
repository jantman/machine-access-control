// FROM: https://github.com/jantman/machine-access-control ; MIT license
// dimensioned in inches
$fn = 360;

module gx16_8() {
    include <config.scad>
    panel_setback = 0.813 - (0.219 + 0.058);
    translate([0, 0, -1 * panel_setback]) {
        union() {
            cylinder(d=0.615, h=0.813);
            translate([0, 0, panel_setback]) {
                cylinder(d=0.715, h=0.058);
            }
            translate([0, 0, panel_setback - wall_thickness - 0.134]) {
                cylinder(d=0.842, h=0.134, $fn=6);
            }
        }
    }
}
