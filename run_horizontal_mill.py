"""
Runner Script for Horizontal Roller Jar Mill Simulation & 3D CAD Suite.
Executes kinematic analysis, critical speed (% Nc) calculations, power sizing,
and exports OpenSCAD CAD files, binary STL meshes, and interactive 3D WebGL viewers.
"""

import os
import shutil
from horizontal_mill.kinematics import HorizontalMillGeometry, HorizontalJarMillKinematics
from horizontal_mill.cad_generator import HorizontalJarMillCADGenerator


def run_horizontal_jar_mill_simulation(output_dir: str = "horizontal_mill/output"):
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 72)
    print(" HORIZONTAL ROLLER JAR MILL: 3D CAD & COMMINUTION SIMULATION")
    print("=" * 72)

    # 1. Initialize Kinematics & Geometry
    geom = HorizontalMillGeometry(
        jar_inner_diameter_m=0.200,   # 200 mm ID jar
        jar_outer_diameter_m=0.220,   # 220 mm OD jar
        jar_length_m=0.280,           # 280 mm length (~8.8 L)
        jar_mass_empty_kg=7.50,
        roller_diameter_m=0.065,      # 65 mm rubber roller
        roller_length_m=0.650,        # 650 mm length
        roller_center_distance_m=0.160,# 160 mm center-to-center
        media_ball_diameter_m=0.020,  # 20 mm balls
        media_density_kg_m3=6000.0,   # Zirconia ZrO2
        media_filling_fraction=0.35,  # 35% J
        powder_mass_kg=1.20,
    )
    
    # Run at optimal cataracting speed: 75% Nc
    kin = HorizontalJarMillKinematics(geometry=geom, jar_rpm=75.0)
    summary = kin.summary()

    print(f"\n[1/4] KINEMATICS & CRITICAL SPEED (Nc):")
    print(f"  - Theoretical Critical Speed (Nc): {summary['critical_speed_rpm']} RPM")
    print(f"  - Operating Jar Speed: {summary['jar_rpm']} RPM ({summary['percent_critical_speed']}% Nc)")
    print(f"  - Roller-to-Jar Friction Ratio: {summary['roller_to_jar_ratio']} (1:{1.0/summary['roller_to_jar_ratio']:.2f})")
    print(f"  - Required Motorized Roller Speed: {summary['required_roller_rpm']} RPM")
    print(f"  - Jar Peripheral Surface Speed: {summary['jar_surface_speed_m_s']} m/s")
    print(f"  - Active Operating Regime: {summary['regime']['regime']}")

    print(f"\n[2/4] IMPACT COMMINUTION KINETICS:")
    kinetics = summary['kinetics']
    print(f"  - Media Detachment Angle (alpha_d): {kinetics['detachment_angle_deg']} deg")
    print(f"  - Single Ball Impact Velocity: {kinetics['impact_velocity_m_s']} m/s")
    print(f"  - Single Ball Kinetic Energy: {kinetics['impact_energy_mJ']} mJ")
    print(f"  - Total Charge Media Balls: {kinetics['total_media_balls']} balls")
    print(f"  - Estimated Collision Frequency: {kinetics['estimated_collision_rate_hz']} Hz")

    print(f"\n[3/4] POWER DRAW & MOTOR DRIVE SIZING:")
    drive = summary['drive']
    print(f"  - Net Comminution Power (Hogg-Fuerstenau): {drive['net_milling_power_w']} W")
    print(f"  - Total Supported Mass (Jar + Media + Powder): {drive['total_supported_mass_kg']} kg")
    print(f"  - Continuous Jar Shaft Torque: {drive['jar_continuous_torque_nm']} Nm")
    print(f"  - Continuous Drive Roller Torque: {drive['roller_continuous_torque_nm']} Nm")
    print(f"  - Normal Force per Rubber Roller: {drive['normal_force_per_roller_n']} N")
    print(f"  - Friction Traction Slip Safety Factor: {drive['slip_safety_factor']}x (Slip-free)")
    print(f"  - Recommended Electric Motor Rating: {drive['recommended_motor_rating_w']} W ({drive['recommended_motor_hp']} HP)")

    print(f"\n[4/4] GENERATING 3D MODELS & INTERACTIVE VIEWERS...")
    cad = HorizontalJarMillCADGenerator(kinematics=kin)
    
    # OpenSCAD CAD Model
    scad_path = os.path.join(output_dir, "horizontal_jar_mill.scad")
    cad.export_openscad_file(scad_path)
    print(f"  [+] OpenSCAD Parametric CAD: {scad_path}")

    # Binary STL
    stl_path = os.path.join(output_dir, "horizontal_jar_mill.stl")
    cad.export_stl_file(stl_path)
    print(f"  [+] Binary STL Mesh: {stl_path}")

    # Interactive 3D WebGL Viewer in separate folder
    html_path = os.path.join(output_dir, "horizontal_jar_mill_3d_viewer.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(cad.generate_interactive_html())
    print(f"  [+] Interactive 3D WebGL Viewer (Separate Folder): {html_path}")

    # Also make a copy into main output/ directory for instant dual-viewing convenience
    main_output_dir = "output"
    os.makedirs(main_output_dir, exist_ok=True)
    main_html_copy = os.path.join(main_output_dir, "horizontal_jar_mill_3d_viewer.html")
    shutil.copyfile(html_path, main_html_copy)
    print(f"  [+] Convenience Copy in Main Output: {main_html_copy}")

    # Engineering Report
    rep_path = os.path.join(output_dir, "horizontal_jar_mill_report.md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(f"""# Horizontal Roller Jar Mill Engineering & Comminution Report

## 1. Machine Architecture & Geometry
- **Mill Type**: Laboratory/Pilot Dual-Roller Friction Jar Mill
- **Jar Inner Diameter ($D_i$)**: {geom.jar_inner_diameter_m * 1000.0:.1f} mm
- **Jar Outer Diameter ($D_o$)**: {geom.jar_outer_diameter_m * 1000.0:.1f} mm
- **Jar Internal Length ($L$)**: {geom.jar_length_m * 1000.0:.1f} mm
- **Roller Diameter ($D_r$)**: {geom.roller_diameter_m * 1000.0:.1f} mm (Polyurethane Rubber)
- **Roller Spacing ($S_r$)**: {geom.roller_center_distance_m * 1000.0:.1f} mm

## 2. Kinematics & Critical Speed
- **Theoretical Critical Speed ($N_c$)**: {summary['critical_speed_rpm']} RPM
- **Operating Jar Speed**: {summary['jar_rpm']} RPM ({summary['percent_critical_speed']}% $N_c$)
- **Required Roller Speed**: {summary['required_roller_rpm']} RPM
- **Friction Drive Speed Ratio**: {summary['roller_to_jar_ratio']}
- **Comminution Operating Regime**: **{summary['regime']['regime']}**
- **Detachment Shoulder Angle ($\\alpha_d$)**: {kinetics['detachment_angle_deg']}°

## 3. Comminution Dynamics & Energy
- **Single Ball Impact Velocity ($v_{{\\text{{imp}}}}$)**: {kinetics['impact_velocity_m_s']} m/s
- **Impact Kinetic Energy**: {kinetics['impact_energy_mJ']} mJ
- **Estimated Collision Rate**: {kinetics['estimated_collision_rate_hz']} Hz
- **Net Milling Power Draw ($P_{{\\text{{net}}}}$)**: {drive['net_milling_power_w']} W
- **Continuous Jar Torque**: {drive['jar_continuous_torque_nm']} Nm
- **Recommended Drive Motor**: **{drive['recommended_motor_rating_w']} W ({drive['recommended_motor_hp']} HP)**

## 4. Interactive 3D CAD & Viewers
- Interactive WebGL 3D Viewer (in separate folder): [`horizontal_mill/output/horizontal_jar_mill_3d_viewer.html`](file:///{os.path.abspath(html_path)})
- OpenSCAD Parametric Fabrication Model: [`horizontal_mill/output/horizontal_jar_mill.scad`](file:///{os.path.abspath(scad_path)})
- Binary STL 3D Mesh: [`horizontal_mill/output/horizontal_jar_mill.stl`](file:///{os.path.abspath(stl_path)})
""")

    print(f"  [+] Markdown Engineering Report: {rep_path}")
    print("\n" + "=" * 72)
    print(" ALL ARTIFACTS GENERATED SUCCESSFULLY!")
    print(f" Direct Viewer URL: file:///{os.path.abspath(html_path)}")
    print("=" * 72)


if __name__ == "__main__":
    run_horizontal_jar_mill_simulation()
