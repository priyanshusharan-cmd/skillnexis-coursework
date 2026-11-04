// Weather-resistant enclosure for the 85 x 62 mm agri-node PCB + one 18650 cell.
// Print in PETG or ASA (PLA softens in sun). 0.2 mm layers, 4 walls, 25 % infill.
//   openscad -D 'part="base"' -o base.stl enclosure.scad     (also: "lid", "assembly")
part = "assembly";

pcb = [85, 62, 1.6];
wall = 2.4;
gap = 1.0;                 // clearance around the PCB
floor_t = 2.4;
standoff_h = 6;            // PCB lifted above the floor (room for B-side solder joints)
devkit_clear = 22;         // DevKit on sockets + OLED/BME280 headers above the PCB
batt_bay = 24;             // 18650 holder beside the PCB (18 mm cell + holder walls)
inner = [pcb[0] + 2 * gap + batt_bay, pcb[1] + 2 * gap, standoff_h + pcb[2] + devkit_clear];
outer = [inner[0] + 2 * wall, inner[1] + 2 * wall, inner[2] + floor_t];
holes = [[4, 4], [81, 4], [4, 58], [81, 58]];   // M3 holes, same as the PCB
lid_t = 2.4;
lip = 2.0;                 // lid lip that sits inside the walls
$fn = 40;

module rounded_box(size, r = 3) {
    hull() for (x = [r, size[0] - r], y = [r, size[1] - r]) translate([x, y, 0]) cylinder(r = r, h = size[2]);
}

pcb_origin = [wall + gap + batt_bay, wall + gap, floor_t + standoff_h];

module base() {
    difference() {
        rounded_box(outer);
        translate([wall, wall, floor_t]) rounded_box([inner[0], inner[1], inner[2] + 1], 1.5);
        // cable glands (PG7, 12.5 mm) on the low side so water runs away from them
        for (z = [floor_t + 8]) {
            translate([pcb_origin[0] + 15, -1, z]) rotate([-90, 0, 0]) cylinder(d = 12.5, h = wall + 2);   // battery/solar
            translate([pcb_origin[0] + 43, -1, z]) rotate([-90, 0, 0]) cylinder(d = 12.5, h = wall + 2);   // pump
            translate([pcb_origin[0] + 70, -1, z]) rotate([-90, 0, 0]) cylinder(d = 12.5, h = wall + 2);   // soil probe, float
        }
        // drain/vent hole with a hydrophobic membrane patch inside
        translate([outer[0] / 2, outer[1] / 2, -1]) cylinder(d = 3, h = floor_t + 2);
    }
    // PCB standoffs with M3 heat-set insert holes
    for (h = holes) translate([pcb_origin[0] + h[0], pcb_origin[1] + h[1], floor_t])
        difference() { cylinder(d = 7, h = standoff_h); cylinder(d = 4.2, h = standoff_h + 1); }
    // 18650 holder cradle
    translate([wall + 2, wall + 8, floor_t]) difference() {
        cube([batt_bay - 4, 70, 10]);
        translate([(batt_bay - 4) / 2, -1, 10]) rotate([-90, 0, 0]) cylinder(d = 18.8, h = 72);
    }
    // lid screw bosses in the corners
    for (x = [wall + 4, outer[0] - wall - 4], y = [wall + 4, outer[1] - wall - 4])
        translate([x, y, floor_t]) difference() { cylinder(d = 8, h = inner[2] - 0.5); cylinder(d = 2.6, h = inner[2] + 1); }
}

module lid() {
    difference() {
        union() {
            rounded_box([outer[0], outer[1], lid_t]);
            translate([wall + 0.3, wall + 0.3, -lip]) difference() {     // lip + gasket groove
                rounded_box([inner[0] - 0.6, inner[1] - 0.6, lip], 1.2);
                translate([1.6, 1.6, -1]) rounded_box([inner[0] - 3.8, inner[1] - 3.8, lip + 2], 1);
            }
        }
        // OLED window: the 0.96" module is screwed under the lid (M2 bosses below) and wired to J7 with a short
        // 4-wire lead; 1 mm clear acrylic is glued over the 28 x 17 mm opening
        translate([pcb_origin[0] + 40, pcb_origin[1] + 22, -lip - 1]) cube([28, 17, lid_t + lip + 2]);
        // button access (plunger extension) over SW1
        translate([pcb_origin[0] + 6.25, pcb_origin[1] + 36.25, -lip - 1]) cylinder(d = 8, h = lid_t + lip + 2);
        // corner screws
        for (x = [wall + 4, outer[0] - wall - 4], y = [wall + 4, outer[1] - wall - 4])
            translate([x, y, -lip - 1]) cylinder(d = 3.2, h = lid_t + lip + 2);
    }
    for (dx = [-1.2, 29.2], dy = [-5, 22]) translate([pcb_origin[0] + 40 + dx, pcb_origin[1] + 22 + dy, -6])   // OLED M2 bosses
        difference() { cylinder(d = 4.5, h = 6); translate([0, 0, -1]) cylinder(d = 1.8, h = 6); }
}

module pcb_model() {
    color("darkgreen") translate(pcb_origin) difference() {
        cube(pcb);
        for (h = holes) translate([h[0], h[1], -1]) cylinder(d = 3.2, h = 4);
    }
    color("royalblue") translate(pcb_origin + [27, 4, pcb[2] + 8.5]) cube([28, 52, 1.6]);   // DevKit on its sockets
    color("orange") translate([wall + 2 + (batt_bay - 4) / 2, wall + 10, floor_t + 10]) rotate([-90, 0, 0]) cylinder(d = 18, h = 65);
}

if (part == "base") base();
else if (part == "lid") lid();
else {
    base();
    pcb_model();
    translate([0, 0, outer[2] + 25]) lid();
}
echo(str("outer size (mm): ", outer[0], " x ", outer[1], " x ", outer[2] + lid_t));
