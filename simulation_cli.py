"""
CLI Entry Point for NanoMill Ball Milling Simulation & CAD Generator.
Runs mechanical, DEM particle, and thermal simulations, generates 3D models (OpenSCAD, STL, WebGL HTML),
and exports the complete engineering design report.
"""

import argparse
import os
import sys

from nanomill.kinematics import PlanetaryKinematics, MillGeometry, DriveSystemSizing
from nanomill.particles import BallMillDEM, NanoparticleKinetics
from nanomill.thermal import MillingThermalModel
from nanomill.cad_generator import BallMillCADGenerator
from nanomill.report import EngineeringReportGenerator


def run_full_simulation(
    sun_rpm: float = 450.0,
    gear_ratio_k: float = -2.0,
    sun_radius_mm: float = 160.0,
    vial_radius_mm: float = 45.0,
    vial_height_mm: float = 90.0,
    num_vials: int = 4,
    media_material: str = "Zirconia (ZrO2 - YSZ)",
    ball_diameter_mm: float = 8.0,
    num_balls: int = 50,
    powder_mass_g: float = 25.0,
    initial_d50_um: float = 45.0,
    milling_hours: float = 12.0,
    vial_material: str = "Stainless Steel (AISI 316)",
    ambient_temp_c: float = 25.0,
    output_dir: str = "output",
):
    print("=" * 70)
    print(" NANOMILL: HIGH-ENERGY BALL MILLING SIMULATION & 3D CAD SUITE")
    print("=" * 70)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Kinematics
    geom = MillGeometry(
        sun_radius_m=sun_radius_mm * 1e-3,
        vial_radius_m=vial_radius_mm * 1e-3,
        vial_height_m=vial_height_mm * 1e-3,
        num_vials=num_vials,
        vial_mass_kg=1.4,
    )
    kin = PlanetaryKinematics(geometry=geom, sun_rpm=sun_rpm, gear_ratio_k=gear_ratio_k)
    kin_summary = kin.summary()
    print(f"\n[1/5] KINEMATICS & G-FORCE:")
    print(f"  - Sun Speed: {kin_summary['sun_rpm']} RPM ({kin_summary['sun_omega_rad_s']} rad/s)")
    print(f"  - Vial Relative Speed: {kin_summary['vial_rpm_rel']} RPM")
    print(f"  - Transmission Ratio (k): {kin_summary['gear_ratio_k']}")
    print(f"  - Centrifugal G-Force: {kin_summary['g_force_sun']} G")
    print(f"  - Milling Regime: {kin_summary['regime']}")

    # 2. Collision Dynamics & Comminution Kinetics
    dem = BallMillDEM(
        kinematics=kin,
        media_material=media_material,
        ball_diameter_mm=ball_diameter_mm,
        num_balls_per_vial=num_balls,
        powder_mass_per_vial_g=powder_mass_g,
    )
    dyn = dem.calculate_collision_dynamics()
    print(f"\n[2/5] DEM COLLISION DYNAMICS:")
    print(f"  - Media Material: {dem.mat.name}")
    print(f"  - Ball-to-Powder Ratio (BPR): {dyn['bpr']}:1")
    print(f"  - Impact Velocity: {dyn['effective_impact_velocity_m_s']} m/s")
    print(f"  - Single Ball Impact Energy: {dyn['single_impact_energy_mj']} mJ")
    print(f"  - Total Collision Frequency: {dyn['total_collision_frequency_hz']} Hz (per vial)")
    print(f"  - Specific Milling Power: {dyn['specific_power_w_per_g']} W/g powder")

    kinetics = NanoparticleKinetics(
        specific_power_w_per_g=dyn["specific_power_w_per_g"],
        initial_d50_um=initial_d50_um,
        use_surfactant_pca=True,
    )
    kin_res = kinetics.simulate(milling_hours=milling_hours)
    print(f"\n[3/5] NANOPARTICLE SIZE REDUCTION KINETICS:")
    print(f"  - Starting Particle Size: {initial_d50_um:.1f} um ({initial_d50_um * 1000:.0f} nm)")
    print(f"  - Predicted D50 after {milling_hours:.0f} hrs: {kin_res['final_d50_nm']:.1f} nm")
    print(f"  - Theoretical Grind Limit: {kin_res['d_limit_nm']:.0f} nm")

    # 3. Thermal Modeling
    thermal = MillingThermalModel(
        kinematics=kin,
        milling_power_per_vial_w=dyn["dissipated_impact_power_vial_w"],
        vial_material=vial_material,
        ambient_temp_c=ambient_temp_c,
    )
    therm_res = thermal.simulate_transient(total_milling_time_min=120.0)
    print(f"\n[4/5] THERMAL & HEAT DISSIPATION:")
    print(f"  - Vial Material: {thermal.mat.name}")
    print(f"  - Heat Generation per Vial: {therm_res['q_gen_w']} W")
    print(f"  - Equilibrium Temperature (T_eq): {therm_res['steady_state_temp_c']} °C")
    print(f"  - Max Safe Temperature: {therm_res['max_safe_temp_c']} °C")
    print(f"  - Status: {'SAFE' if therm_res['is_thermally_safe'] else 'COOLING REQUIRED'}")

    # 4. Drive Sizing
    drive = DriveSystemSizing(kinematics=kin)
    drive_s = drive.calculate_motor_requirements(dyn["total_milling_power_all_vials_w"])
    print(f"\n[5/5] MOTOR & DRIVE SIZING:")
    print(f"  - Total Inertia: {drive_s['I_total_kg_m2']} kg*m^2")
    print(f"  - Continuous Milling Torque: {drive_s['continuous_torque_nm']} Nm")
    print(f"  - Required Continuous Electrical Power: {drive_s['required_continuous_elec_power_w']} W")
    print(f"  - Recommended Motor: {drive_s['recommended_motor_w']} W ({drive_s['recommended_motor_hp']} HP)")

    # 5. Export 3D Models
    print(f"\n--> GENERATING 3D MODELS...")
    cad = BallMillCADGenerator(kinematics=kin)
    scad_file = cad.export_openscad_file(os.path.join(output_dir, "ball_mill_assembly.scad"))
    stl_file = cad.export_stl_file(os.path.join(output_dir, "ball_mill_assembly.stl"))
    html_3d_file = os.path.join(output_dir, "ball_mill_3d_viewer.html")
    with open(html_3d_file, "w", encoding="utf-8") as f:
        f.write(cad.generate_interactive_html())

    print(f"  [+] OpenSCAD Model (AI-editable): {scad_file}")
    print(f"  [+] Binary STL Mesh (3D print/CAD): {stl_file}")
    print(f"  [+] Interactive 3D WebGL Viewer: {html_3d_file}")

    # 6. Export Technical Report
    print(f"\n--> GENERATING ENGINEERING REPORT & FIGURES...")
    reporter = EngineeringReportGenerator(
        kinematics=kin,
        drive_sizing=drive,
        dem=dem,
        kinetics=kinetics,
        thermal=thermal,
    )
    rep_files = reporter.export_full_report(output_dir)
    print(f"  [+] Markdown Report: {rep_files['markdown_report']}")
    print(f"  [+] Printable HTML Report: {rep_files['html_report']}")
    for k, v in rep_files["figures"].items():
        print(f"  [+] Chart: {v}")

    print("\n" + "=" * 70)
    print(" SIMULATION COMPLETE! ALL ARTIFACTS READY IN: " + os.path.abspath(output_dir))
    print("=" * 70)
    return rep_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run NanoMill Simulation & CAD Suite")
    parser.add_argument("--sun-rpm", type=float, default=450.0, help="Sun wheel RPM")
    parser.add_argument("--gear-ratio", type=float, default=-2.0, help="Gear ratio k (e.g. -2.0 for counter-rotation)")
    parser.add_argument("--media", type=str, default="Zirconia (ZrO2 - YSZ)", help="Grinding media material")
    parser.add_argument("--ball-diam", type=float, default=8.0, help="Ball diameter in mm")
    parser.add_argument("--hours", type=float, default=12.0, help="Milling duration in hours")
    parser.add_argument("--output", type=str, default="output", help="Output directory")

    args = parser.parse_args()
    run_full_simulation(
        sun_rpm=args.sun_rpm,
        gear_ratio_k=args.gear_ratio,
        media_material=args.media,
        ball_diameter_mm=args.ball_diam,
        milling_hours=args.hours,
        output_dir=args.output,
    )
