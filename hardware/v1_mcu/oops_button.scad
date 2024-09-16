// FROM: https://github.com/jantman/machine-access-control ; MIT license
// dimensioned in inches
$fn = 360;

//oops_button();

module oops_button() {
    conn_diameter = 0.625;
    h=0.790+0.300;
    translate([0, 0, 0]) {
        union() {
            translate([0.878/-2, 0.954/-2, 0]) {
                cube([0.878, 0.954, 0.578]);
            }
            translate([0, 0, -1 * h]) {
                cylinder(d=conn_diameter, h=h);
            }
        }
    }
}
