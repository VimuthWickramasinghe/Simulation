"""
Interactive Streamlit Application for NanoMill Ball Milling Machine Design & Simulation.
Run locally via:
    streamlit run app.py
"""

import streamlit as st
import numpy as np
import os
import matplotlib.pyplot as plt

from nanomill.kinematics import PlanetaryKinematics, MillGeometry, DriveSystemSizing
from nanomill.particles import BallMillDEM, NanoparticleKinetics, MEDIA_DATABASE
from nanomill.thermal import MillingThermalModel, VIAL_THERMAL_DATABASE
from nanomill.cad_generator import BallMillCADGenerator
from nanomill.report import EngineeringReportGenerator

st.set_page_config(
    page_title="NanoMill: Nanoparticle Ball Mill Designer & Multiphysics Studio",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚙️ NanoMill: Planetary Ball Mill Designer & Multiphysics Studio")
st.caption("Engineered for Nanoparticle Synthesis | Mechanical Dynamics • DEM Collisions • Nanoscale Kinetics • Thermal Dissipation • AI 3D CAD")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🛠️ Design Parameters")

with st.sidebar.expander("1. Kinematics & Geometry", expanded=True):
    sun_rpm = st.slider("Sun Disk Speed (RPM)", min_value=100.0, max_value=1000.0, value=500.0, step=25.0)
    gear_ratio_k = st.slider("Transmission Ratio (k = ω/Ω)", min_value=-4.0, max_value=-1.0, value=-2.0, step=0.25,
                             help="Negative indicates counter-rotation, maximizing impact energy.")
    sun_radius_mm = st.number_input("Sun Disk Radius (mm)", min_value=80.0, max_value=350.0, value=160.0, step=10.0)
    vial_radius_mm = st.number_input("Inner Vial Radius (mm)", min_value=25.0, max_value=100.0, value=45.0, step=5.0)
    vial_height_mm = st.number_input("Inner Vial Height (mm)", min_value=40.0, max_value=200.0, value=90.0, step=10.0)
    num_vials = st.selectbox("Number of Vials", options=[2, 4, 8], index=1)

with st.sidebar.expander("2. Grinding Media & Powder", expanded=True):
    media_name = st.selectbox("Grinding Media Material", options=list(MEDIA_DATABASE.keys()), index=1)
    ball_diam_mm = st.slider("Ball Diameter (mm)", min_value=2.0, max_value=20.0, value=8.0, step=1.0)
    num_balls = st.slider("Balls per Vial", min_value=10, max_value=250, value=50, step=5)
    powder_mass_g = st.number_input("Powder Charge per Vial (g)", min_value=5.0, max_value=200.0, value=25.0, step=5.0)

with st.sidebar.expander("3. Comminution & Nanoparticles", expanded=False):
    initial_d50_um = st.number_input("Initial Particle Size D50 (µm)", min_value=1.0, max_value=250.0, value=45.0, step=5.0)
    milling_hours = st.slider("Milling Duration (Hours)", min_value=1.0, max_value=48.0, value=12.0, step=1.0)
    use_pca = st.checkbox("Use Surfactant / PCA (Anti-Agglomeration)", value=True,
                          help="Prevents cold welding and enables sub-50 nm particles.")

with st.sidebar.expander("4. Thermal & Dissipation", expanded=False):
    vial_mat_name = st.selectbox("Vial Shell Material", options=list(VIAL_THERMAL_DATABASE.keys()), index=1)
    ambient_temp = st.number_input("Ambient Temperature (°C)", min_value=10.0, max_value=45.0, value=25.0, step=1.0)

# --- RUN COMPUTATIONS ---
geom = MillGeometry(
    sun_radius_m=sun_radius_mm * 1e-3,
    vial_radius_m=vial_radius_mm * 1e-3,
    vial_height_m=vial_height_mm * 1e-3,
    num_vials=num_vials,
    vial_mass_kg=1.4,
)
kin = PlanetaryKinematics(geometry=geom, sun_rpm=sun_rpm, gear_ratio_k=gear_ratio_k)
kin_s = kin.summary()

dem = BallMillDEM(
    kinematics=kin,
    media_material=media_name,
    ball_diameter_mm=ball_diam_mm,
    num_balls_per_vial=num_balls,
    powder_mass_per_vial_g=powder_mass_g,
)
dyn = dem.calculate_collision_dynamics()

kinetics = NanoparticleKinetics(
    specific_power_w_per_g=dyn["specific_power_w_per_g"],
    initial_d50_um=initial_d50_um,
    use_surfactant_pca=use_pca,
)
kin_res = kinetics.simulate(milling_hours=milling_hours)

thermal = MillingThermalModel(
    kinematics=kin,
    milling_power_per_vial_w=dyn["dissipated_impact_power_vial_w"],
    vial_material=vial_mat_name,
    ambient_temp_c=ambient_temp,
)
therm_res = thermal.simulate_transient(total_milling_time_min=120.0)

drive = DriveSystemSizing(kinematics=kin)
drive_s = drive.calculate_motor_requirements(dyn["total_milling_power_all_vials_w"])

cad = BallMillCADGenerator(kinematics=kin)

# --- KPI METRICS ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Centrifugal Force", f"{kin_s['g_force_sun']} G", f"{kin_s['regime'][:11]}")
col2.metric("Impact Velocity", f"{dyn['effective_impact_velocity_m_s']} m/s", f"{dyn['single_impact_energy_mj']} mJ/hit")
col3.metric("Predicted D50", f"{kin_res['final_d50_nm']:.1f} nm", f"Limit: {kin_res['d_limit_nm']:.0f} nm")
col4.metric("Steady Temp", f"{therm_res['steady_state_temp_c']} °C", f"Safe < {therm_res['max_safe_temp_c']}°C")
col5.metric("Motor Sizing", f"{drive_s['recommended_motor_w']} W", f"{drive_s['recommended_motor_hp']} HP")

# --- TABS INTERFACE ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐 Interactive 3D Model",
    "📈 Kinematics & DEM Trajectories",
    "🔬 Nanoparticle Comminution",
    "🔥 Thermal Dissipation",
    "📄 Engineering Report & CAD Export",
])

# TAB 1: 3D MODEL
with tab1:
    st.subheader("🌐 Interactive 3D Planetary Ball Mill (Light Mode with Black CAD Edges)")
    st.caption("Studio CAD View: Inspect the central stationary Sun Gear, rotating Planet Gears, Annular Cooling Fins on jars, and Directional Rotational Indicators. Test different gear ratios live using the selector buttons in the 3D viewport!")

    # Display gear specifications
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)
    g_col1.metric("Gear Ratio (k = ω/Ω)", f"{kin.gear_ratio_k:.2f}", "Counter-Rotation")
    g_col2.metric("Sun Gear (Zs)", f"{kin.gears.sun_teeth} Teeth", f"Ø {kin.gears.sun_pitch_diameter_mm:.1f} mm Pitch")
    g_col3.metric("Planet Gear (Zp)", f"{kin.gears.planet_teeth} Teeth", f"Ø {kin.gears.planet_pitch_diameter_mm:.1f} mm Pitch")
    g_col4.metric("Jar Spin Speed (ω)", f"{kin.vial_rpm_rel:.0f} RPM", f"Rel to Disc ({kin.sun_rpm:.0f} RPM)")

    html_3d = cad.generate_interactive_html(width="100%", height="580px")
    st.components.v1.html(html_3d, height=610, scrolling=False)

    colA, colB = st.columns(2)
    with colA:
        st.download_button(
            label="⬇️ Download OpenSCAD Code (.scad) - With Gears & Cooling Fins",
            data=cad.generate_openscad_code(),
            file_name="planetary_ball_mill_gears_fins.scad",
            mime="text/plain",
            help="OpenSCAD code with mechanical gears, cooling fins, and rotational indicators."
        )
    with colB:
        st.download_button(
            label="⬇️ Download Binary STL 3D Mesh (.stl) - With Gears & Fins",
            data=cad.generate_pure_stl_mesh(),
            file_name="planetary_ball_mill_gears_fins.stl",
            mime="application/sla",
            help="Direct 3D printable mesh with gears, cooling fins, and indicator bars."
        )

# TAB 2: KINEMATICS & TRAJECTORIES
with tab2:
    st.subheader("Kinematics & Non-Inertial Coriolis Dynamics")
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Trajectories
    traj_data = dem.simulate_sample_trajectories()
    ax1.plot(traj_data["vial_wall_x"] * 1e3, traj_data["vial_wall_y"] * 1e3, "k-", lw=2.5, label="Vial Wall")
    colors = ["#2563eb", "#ea580c", "#16a34a"]
    for idx, (tx, ty) in enumerate(traj_data["trajectories"]):
        ax1.plot(tx * 1e3, ty * 1e3, color=colors[idx % len(colors)], lw=2.0, ls="--", label=f"Ball Path #{idx+1}")
        ax1.plot(tx[-1] * 1e3, ty[-1] * 1e3, "ro", ms=7)
    ax1.set_aspect("equal")
    ax1.set_xlabel("Vial X (mm)")
    ax1.set_ylabel("Vial Y (mm)")
    ax1.set_title("Ball Cataracting Trajectories in Rotating Frame", fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right")

    # Accel
    theta = np.linspace(0, 2 * np.pi, 200)
    accel_data = kin.calculate_acceleration_field(theta)
    ax2.plot(np.degrees(theta), accel_data["g_force"], color="#7c3aed", lw=2.5)
    ax2.axhline(kin.g_force_sun(), color="#0284c7", ls="--", label=f"Sun G-Force ({kin.g_force_sun():.1f} G)")
    ax2.set_xlabel("Vial Angle θ (degrees)")
    ax2.set_ylabel("Effective Acceleration (G-force)")
    ax2.set_title("Circumferential G-Force Distribution", fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend()
    fig1.tight_layout()
    st.pyplot(fig1)

# TAB 3: NANOPARTICLE KINETICS
with tab3:
    st.subheader("Nanoscale Comminution Kinetics")
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(12, 5))
    ax3.semilogy(kin_res["time_hours"], kin_res["d50_nm"], color="#0284c7", lw=2.5, label="D50 Median Size")
    ax3.semilogy(kin_res["time_hours"], kin_res["d90_nm"], color="#9333ea", lw=2.0, ls="--", label="D90 Top Cut")
    ax3.axhline(100.0, color="#dc2626", ls=":", lw=1.8, label="Nanoparticle Threshold (100 nm)")
    ax3.axhline(kin_res["d_limit_nm"], color="#16a34a", ls="-.", label=f"Grind Limit ({kin_res['d_limit_nm']:.0f} nm)")
    ax3.set_xlabel("Milling Time (hours)")
    ax3.set_ylabel("Particle Size (nm) [Log Scale]")
    ax3.set_title("Nanoparticle Size Evolution vs Time", fontweight="bold")
    ax3.grid(True, which="both", linestyle=":", alpha=0.6)
    ax3.legend()

    ax4.plot(kin_res["time_hours"], kin_res["ssa_m2_g"], color="#059669", lw=2.5)
    ax4.set_xlabel("Milling Time (hours)")
    ax4.set_ylabel("Specific Surface Area (m²/g)")
    ax4.set_title("Specific Surface Area (SSA) Evolution", fontweight="bold")
    ax4.grid(True, linestyle=":", alpha=0.6)
    fig2.tight_layout()
    st.pyplot(fig2)

# TAB 4: THERMAL PROFILE
with tab4:
    st.subheader("Vial Heat Dissipation & Thermal Equilibrium")
    fig3, ax5 = plt.subplots(figsize=(8, 4))
    ax5.plot(therm_res["time_minutes"], therm_res["internal_temp_c"], color="#e11d48", lw=2.5, label="Internal Temp T(t)")
    ax5.axhline(therm_res["ambient_temp_c"], color="#64748b", ls="--", label=f"Ambient ({therm_res['ambient_temp_c']}°C)")
    ax5.axhline(therm_res["max_safe_temp_c"], color="#b91c1c", ls="-.", lw=2.0, label=f"Safe Threshold ({therm_res['max_safe_temp_c']}°C)")
    ax5.axhline(therm_res["steady_state_temp_c"], color="#d97706", ls=":", label=f"Equilibrium ({therm_res['steady_state_temp_c']}°C)")
    ax5.set_xlabel("Continuous Operation Time (minutes)")
    ax5.set_ylabel("Temperature (°C)")
    ax5.set_title(f"Thermal Profile: {thermal.mat.name} Vial", fontweight="bold")
    ax5.grid(True, linestyle=":", alpha=0.6)
    ax5.legend()
    fig3.tight_layout()
    st.pyplot(fig3)
    st.info(f"**Thermal Recommendation:** {therm_res['cooling_recommendation']}")

# TAB 5: REPORT & BOM
with tab5:
    st.subheader("Engineering Design & Simulation Report")
    reporter = EngineeringReportGenerator(
        kinematics=kin,
        drive_sizing=drive,
        dem=dem,
        kinetics=kinetics,
        thermal=thermal,
    )
    md_report = reporter.generate_markdown_report()
    st.markdown(md_report)
    st.download_button(
        label="⬇️ Download Full Engineering Report (.md)",
        data=md_report,
        file_name="nanomill_engineering_report.md",
        mime="text/markdown",
    )
