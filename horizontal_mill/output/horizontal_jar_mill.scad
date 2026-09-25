// ======================================================================
// PARAMETRIC 3D CAD MODEL: HORIZONTAL ROLLER JAR BALL MILL
// Laboratory / Pilot High-Energy Friction Roller Milling Machine
// ======================================================================

$fn = 64;

// Machine Geometry Parameters (mm)
D_jar_outer = 220.0;
D_jar_inner = 200.0;
L_jar = 280.0;
D_roller = 65.0;
L_roller = 650.0;
S_roller = 160.0;
Y_jar_elevation = 117.92;

// Frame Dimensions
frame_w = S_roller + 180.0;
frame_l = L_roller + 120.0;
frame_h = 75.0;

module base_frame() {
    color([0.25, 0.28, 0.32]) {
        // C-Channel Side Beams
        translate([-frame_w/2, -frame_l/2, -frame_h])
            cube([frame_w, 20, frame_h]);
        translate([-frame_w/2, frame_l/2 - 20, -frame_h])
            cube([frame_w, 20, frame_h]);
        // Longitudinal cross members
        translate([-frame_w/2, -frame_l/2, -frame_h])
            cube([20, frame_l, frame_h]);
        translate([frame_w/2 - 20, -frame_l/2, -frame_h])
            cube([20, frame_l, frame_h]);
        
        // 4x Rubber Leveling Isolation Feet
        for (x = [-frame_w/2 + 25, frame_w/2 - 25]) {
            for (y = [-frame_l/2 + 25, frame_l/2 - 25]) {
                translate([x, y, -frame_h - 18])
                    cylinder(r=22, h=18);
            }
        }
    }
}

module pillow_block_bearing(x_pos, y_pos) {
    color([0.35, 0.40, 0.45]) {
        translate([x_pos, y_pos, -15]) {
            // Cast iron base
            difference() {
                cube([45, 80, 20], center=true);
                // Bolt holes
                translate([0, 28, 0]) cylinder(r=5, h=25, center=true);
                translate([0, -28, 0]) cylinder(r=5, h=25, center=true);
            }
            // Bearing housing arch
            translate([0, 0, 10])
                rotate([90, 0, 0])
                    cylinder(r=24, h=30, center=true);
        }
    }
}

module roller_assembly(x_offset) {
    translate([x_offset, 0, 0]) {
        // Polyurethane High-Traction Rubber Roller Sleeve
        color([0.18, 0.20, 0.22]) {
            rotate([90, 0, 0])
                cylinder(r=D_roller/2, h=L_roller, center=true);
        }
        // Precision Ground Steel Core Shaft
        color([0.78, 0.82, 0.86]) {
            rotate([90, 0, 0])
                cylinder(r=12.5, h=L_roller + 100, center=true);
        }
        // Bearings at both ends
        pillow_block_bearing(0, -L_roller/2 - 25);
        pillow_block_bearing(0, L_roller/2 + 25);
    }
}

module motor_and_drive() {
    translate([-S_roller/2 - 80, -L_roller/2 - 20, -20]) {
        // Electric Drive Motor Body
        color([0.20, 0.45, 0.70]) {
            rotate([90, 0, 0])
                cylinder(r=45, h=120, center=true);
            // Terminal box
            translate([0, 0, 45])
                cube([40, 50, 30], center=true);
        }
        // Motor Pulley
        color([0.80, 0.80, 0.80]) {
            translate([0, 65, 0])
                rotate([90, 0, 0])
                    cylinder(r=22, h=22, center=true);
        }
        // Timing Belt Protective Steel Guard
        color([0.90, 0.65, 0.15, 0.85]) {
            translate([40, 65, 10])
                cube([100, 26, 80], center=true);
        }
    }
}

module horizontal_jar() {
    translate([0, 0, Y_jar_elevation]) {
        rotate([90, 0, 0]) {
            // Ceramic / Stainless Steel Jar Cylindrical Shell
            color([0.92, 0.94, 0.96, 0.85]) {
                difference() {
                    cylinder(r=D_jar_outer/2, h=L_jar, center=true);
                    cylinder(r=D_jar_inner/2, h=L_jar - 24, center=true);
                }
            }
            // Anti-Drift Rubber Guide Rings
            color([0.15, 0.15, 0.15]) {
                for (z = [-L_jar/2 + 25, L_jar/2 - 25]) {
                    translate([0, 0, z])
                        difference() {
                            cylinder(r=D_jar_outer/2 + 6, h=14, center=true);
                            cylinder(r=D_jar_outer/2 - 0.5, h=16, center=true);
                        }
                }
            }
            // Jar Lid & Clamp Crossbar
            color([0.75, 0.20, 0.20]) {
                translate([0, 0, L_jar/2 + 8]) {
                    cylinder(r=D_jar_outer/2 - 5, h=16, center=true);
                    // Quick-release clamp bar
                    cube([D_jar_outer + 20, 28, 12], center=true);
                    // Central Handwheel clamping screw
                    translate([0, 0, 16])
                        cylinder(r=18, h=12, center=true);
                }
            }
        }
    }
}

// Complete Machine Assembly
base_frame();
roller_assembly(-S_roller/2);  // Motorized Drive Roller
roller_assembly(S_roller/2);   // Supporting Idler Roller
motor_and_drive();
horizontal_jar();
