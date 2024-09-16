// FROM: https://github.com/jantman/machine-access-control ; MIT license
// dimensioned in inches
$fn = 360;

//gx16_8();

module gx16_8() {
    include <config.scad>
    conn_diameter = 0.615;
    panel_setback = 0.813 - (0.219 + 0.058);
    translate([0, 0, -1 * panel_setback]) {
        union() {
            cylinder(d=conn_diameter, h=0.813);
            translate([0, 0, panel_setback]) {
                cylinder(d=0.715, h=0.058);
            }
            translate([0, 0, panel_setback - wall_thickness - 0.134]) {
                cylinder(d=0.842, h=0.134, $fn=6);
            }
        }
    }
}
