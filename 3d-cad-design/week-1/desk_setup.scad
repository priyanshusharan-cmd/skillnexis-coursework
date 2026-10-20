// Parametric desk setup study. Units: millimeters.
// Objects: desk top, four legs, laptop base, screen, mug, pen cup, book = 10+ parts.
$fn=48;
module block(size,pos,rad=0) { translate(pos) minkowski(){ cube([size[0]-2*rad,size[1]-2*rad,size[2]-2*rad],center=true); sphere(r=rad); } }
// Desk top and four legs
color("saddlebrown") block([1200,650,35],[0,0,735],4);
for (x=[-540,540], y=[-265,265]) color("dimgray") block([45,45,730],[x,y,365],3);
// Laptop base and tilted display (display represented as a thin panel)
color("silver") block([360,240,16],[0,70,762],8);
color("black") translate([0,170,855]) rotate([12,0,0]) block([360,18,230],[0,0,0],6);
color("deepskyblue") translate([0,157,855]) rotate([12,0,0]) block([320,2,190],[0,0,0],2);
// Mug with handle
color("white") difference(){ translate([390,90,762]) cylinder(h=105,r=42); translate([390,90,770]) cylinder(h=98,r=34); }
color("white") translate([433,90,815]) rotate_extrude() translate([47,0,0]) circle(r=8);
// Pen cup and pens
color("goldenrod") difference(){ translate([-430,90,762]) cylinder(h=110,r=42); translate([-430,90,770]) cylinder(h=104,r=34); }
for (a=[0:4]) color("navy") translate([-448+a*9,90,850]) cylinder(h=120-(a%2)*25,r=3);
// Book and a standing phone
color("tomato") block([190,140,22],[-370,-90,763],2);
color("darkslategray") block([65,20,130],[470,-80,810],5);
// Render plan: camera (1600,-2100,1550), target (0,0,700); key at (-900,-800,1500), fill (900,-400,1100), rim (0,700,1400).
