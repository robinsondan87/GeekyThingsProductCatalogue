// 'Customizable Filament Box Socket' by wstein 
// is licensed under the Attribution - Non-Commercial - Share Alike license. 
// Version 2.0 (c) August 2015
// please refer the complete license here: http://creativecommons.org/licenses/by-nc-sa/3.0/legalcode

// Version 1.0a: parts renamed as customizer can't handle whitespace in part parameter.
// Version 2.0: customizer calculates the correct tube length 
// Version 2.0.1: fix for latest customizer version 

// preview[view:west, tilt:top diagonal]

//to show.
part="preview_"; //[preview_:Preview,socket_:Socket,drilling_jig_:Drilling Jig]

/*[Socket]*/
//M4 is 6.9mm
socket_plate_thickness=5;
hex_nut_width=6.9;
screw_hole_diameter=4.0;
backlash=0.5;

/*[Box Size]*/

//default values are for IKEA SAMLA 22l/6gallons
box_bottom_width=215;
box_bottom_length=300;
box_top_width=250;
box_top_length=330;
box_height=230;

/*[Tube]*/

tube_diameter=32;
// distance between bottom of box and center of tube.
tube_height=140;

/*[Drilling Jig]*/

template_tube_center_width=80;
template_bottom_width=100;
template_thickness=3;
template_drill_diameter=4;

/*[Hidden]*/
$fn=150;

wall_degree=asin((box_top_length-box_bottom_length)/box_height/2);
sin_wall=(box_top_length-box_bottom_length)/box_height/2;
cos_wall=cos(wall_degree);

box_tube_width=box_bottom_length+(box_top_length-box_bottom_length)/box_height*tube_height;
box_tube_lower_width=box_bottom_length+(box_top_length-box_bottom_length)/box_height*(tube_height-tube_diameter/2);
box_tube_upper_width=box_bottom_length+(box_top_length-box_bottom_length)/box_height*(tube_height+tube_diameter/2);
echo(box_tube_width=box_tube_width);
echo(box_tube_lower_width=box_tube_lower_width);

tube_length=min(box_tube_upper_width-5,box_tube_lower_width-1.2);
echo(tube_length=tube_length);

if(part=="preview_")
preview();

if(part=="drilling_jig_")
drilling_jig();

if(part=="socket_")
socket();

module preview()
intersection()
{

	union()
	{
		color("yellow")
		for(m=[0,1])
		mirror([0,m,0])
		translate([0,box_tube_width/2,tube_height])
		rotate([90-wall_degree,0,0])
		socket();
	
		color("silver")
		translate([0,0,tube_height])
		rotate([90,0,0])
		cylinder(r=tube_diameter/2+backlash,h=tube_length+2*backlash,center=true,$fn=$fn*2);

        color("black")
        translate([-tube_diameter-backlash,0,tube_height-tube_diameter/2-backlash])
        rotate([0,0,-90])
        linear_extrude(1,convexity=10)
        resize([tube_length*.9,0], auto=true)
        text(str("tube length = ",round(tube_length*10.0)/10.0,"mm"),size=16,valign="center",halign="center");
	}	
	
	%linear_extrude(height=box_height,scale=[box_top_width/box_bottom_width,box_top_length/box_bottom_length],convexity=20)
	square([box_bottom_width,box_bottom_length],center=true);
}

module drilling_jig()
assign(x1=template_tube_center_width/2,x2=template_bottom_width/2,y1=0,y2=sqrt(pow((box_top_length-box_bottom_length)/2,2)+tube_height*tube_height))
difference()
{
	union()
	{
		hull()
		triangle()	
		cylinder(r=template_drill_diameter/2+backlash+4,h=template_thickness);

		translate([-x2,-y2-template_thickness,template_thickness])
		cube([x2*2,template_thickness,10]);

		assign(templ_points=[[-x1+(template_drill_diameter/2+backlash+4),y1],[x1-(template_drill_diameter/2+backlash+4),y1],[x2-(template_drill_diameter/2+backlash+4),-y2],[-x2+(template_drill_diameter/2+backlash+4),-y2]])
		assign(templ_points2=[[-x1+(template_drill_diameter/2+backlash+4)+template_drill_diameter/2+6,y1-template_drill_diameter/2-6],[x1-(template_drill_diameter/2+backlash+4)-template_drill_diameter/2-6,y1-template_drill_diameter/2-6],[x2-(template_drill_diameter/2+backlash+4)-template_drill_diameter/2-6,-y2+template_drill_diameter/2+6],[-x2+(template_drill_diameter/2+backlash+4)+template_drill_diameter/2+6,-y2+template_drill_diameter/2+6]])
		difference()
		{
			hull()
			for(pos=templ_points)
			translate(pos)
			cylinder(r=template_drill_diameter/2+backlash+4,h=template_thickness);
	
			hull()
			for(pos=templ_points2)
			translate(concat(pos,-.1))
			cylinder(r=template_drill_diameter/2,h=template_thickness+.2);
		}
	}

	hull()
	triangle(-4-6)	
	translate([0,0,-.1])
	cylinder(r=2,h=template_thickness+.2);

	triangle()	
	translate([0,0,-.1])
	cylinder(r=template_drill_diameter/2+backlash,h=template_thickness+.2);
}

module socket()
difference()
{
	union()
	{
        linear_extrude(socket_plate_thickness,convexity=10)
        difference()
        {
            hull()
            {
                circle(r=tube_diameter/2+3);	

                triangle()	
                circle(r=hex_nut_width/2+2);
            }
            
            triangle()	
            circle(r=screw_hole_diameter/2+backlash);
        }
		rotate([wall_degree,0,0])
		cylinder(r=tube_diameter/2+3,h=(box_tube_width-tube_length+16+socket_plate_thickness)/2);
	}

echo((box_tube_width-tube_length)/2);
	rotate([wall_degree,0,0])
	for(pos=[[0,0,(box_tube_width-tube_length)/2],[0,.75*(tube_diameter+backlash*2),(box_tube_width-tube_length)/2-.8]])
	translate(pos)
	rotate([0,0,90])
	cylinder(r=tube_diameter/2+backlash,h=20,$fn=$fn*2);

	// build insert ramp
	translate([0,0,(box_tube_width-tube_length+0)/2]) // replace -1 with +10
	assign(x1=tube_diameter*1.3/2,x2=tube_diameter/2,y10=tube_diameter/2+3.1,y2=0,z10=3,z2=8,z3=10+5)
	assign(y1=y10*cos_wall-z10*sin_wall,z1=y10*sin_wall+z10*cos_wall)
	polyhedron([[-x1,y1,z1],[x1,y1,z1],[x2,y2,z2],[-x2,y2,z2],[-x1,y1,z3],[x1,y1,z3],[x2,y2,z3],[-x2,y2,z3]], [[0,3,2,1],[2,3,7,6],[1,2,6,5],[0,1,5,4],[0,4,7,3],[4,5,6,7]], convexity=20);

	translate([0,0,-(tube_diameter+backlash/2+6)/2])
	cube(tube_diameter+backlash/2+6,center=true);

    // nuts
	translate([0,0,2])
	triangle()	
	cylinder(r=hex_nut_width*sqrt(1.25)/2+backlash,h=3.1,$fn=6);
}

module triangle(offset=0)		
for(a=[30:120:359])
rotate([0,0,a])
translate([tube_diameter/2+hex_nut_width/2+3.55+offset,0,0])
rotate([0,0,30])
children(0);

