"""
Particle and Grinding Media Collision Dynamics (DEM approximation) and Nanoparticle Comminution Kinetics.
Models ball trajectories under Coriolis/centrifugal acceleration, impact energy spectra,
collision frequencies, and top-down nanoscale size reduction (micro-to-nano transition).
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
from .kinematics import PlanetaryKinematics


@dataclass
class GrindingMediaMaterial:
    name: str
    density_kg_m3: float
    hardness_hv: float
    thermal_conductivity_w_mk: float
    specific_heat_j_kgk: float
    recommended_for: str


MEDIA_DATABASE = {
    "Tungsten Carbide (WC-Co)": GrindingMediaMaterial(
        name="Tungsten Carbide (WC-Co)",
        density_kg_m3=14900.0,
        hardness_hv=1600.0,
        thermal_conductivity_w_mk=84.0,
        specific_heat_j_kgk=210.0,
        recommended_for="Maximum kinetic energy, rapid milling of hard ceramics & oxides.",
    ),
    "Zirconia (ZrO2 - YSZ)": GrindingMediaMaterial(
        name="Zirconia (ZrO2 - YSZ)",
        density_kg_m3=6000.0,
        hardness_hv=1250.0,
        thermal_conductivity_w_mk=2.7,
        specific_heat_j_kgk=450.0,
        recommended_for="Zero iron contamination, pharmaceutical, battery cathode/anode nanomaterials.",
    ),
    "Stainless Steel (AISI 316)": GrindingMediaMaterial(
        name="Stainless Steel (AISI 316)",
        density_kg_m3=7900.0,
        hardness_hv=350.0,
        thermal_conductivity_w_mk=16.3,
        specific_heat_j_kgk=500.0,
        recommended_for="General metallic alloys, economic non-reactive dry milling.",
    ),
    "Agate (SiO2)": GrindingMediaMaterial(
        name="Agate (SiO2)",
        density_kg_m3=2650.0,
        hardness_hv=700.0,
        thermal_conductivity_w_mk=3.3,
        specific_heat_j_kgk=790.0,
        recommended_for="Gentle grinding, geosciences, low metal contamination.",
    ),
}


class BallMillDEM:
    """
    Simplified Discrete Element Method (DEM) / kinematic ball collision model
    calculating ball departure angles, impact velocity, impact energy, and collision frequency.
    """

    def __init__(
        self,
        kinematics: PlanetaryKinematics,
        media_material: str = "Zirconia (ZrO2 - YSZ)",
        ball_diameter_mm: float = 8.0,
        num_balls_per_vial: int = 45,
        powder_mass_per_vial_g: float = 25.0,
    ):
        self.kin = kinematics
        self.mat = MEDIA_DATABASE.get(media_material, MEDIA_DATABASE["Zirconia (ZrO2 - YSZ)"])
        self.ball_d_m = ball_diameter_mm * 1e-3
        self.num_balls = num_balls_per_vial
        self.powder_mass_g = powder_mass_per_vial_g

    @property
    def single_ball_mass_kg(self) -> float:
        """Mass of one spherical grinding ball."""
        radius = self.ball_d_m / 2.0
        volume = (4.0 / 3.0) * np.pi * (radius ** 3)
        return volume * self.mat.density_kg_m3

    @property
    def total_media_mass_per_vial_kg(self) -> float:
        """Total mass of grinding media inside one vial."""
        return self.num_balls * self.single_ball_mass_kg

    @property
    def ball_to_powder_ratio(self) -> float:
        """Ball-to-Powder Mass Ratio (BPR), typically 5:1 to 20:1 for nanoparticles."""
        powder_kg = self.powder_mass_g * 1e-3
        return self.total_media_mass_per_vial_kg / powder_kg if powder_kg > 0 else 0.0

    @property
    def vial_filling_ratio(self) -> float:
        """Fraction of inner vial volume occupied by grinding balls."""
        vial_vol = np.pi * (self.kin.geom.vial_radius_m ** 2) * self.kin.geom.vial_height_m
        media_vol = self.num_balls * (4.0 / 3.0) * np.pi * ((self.ball_d_m / 2.0) ** 3)
        return media_vol / vial_vol

    def calculate_collision_dynamics(self) -> Dict[str, Any]:
        """
        Estimates detachment trajectory, collision velocity, impact energy,
        and total specific milling power based on Burgio/Basset/Magini kinetic models.
        """
        R = self.kin.geom.sun_radius_m
        r = self.kin.geom.vial_radius_m
        Omega = self.kin.sun_omega
        k = self.kin.gear_ratio_k

        # Theoretical relative impact velocity of ball hitting opposite wall:
        # V_imp ~ 2 * Omega * R * sqrt(1 + k^2 - 2*k*(r/R)) * geometric_factor
        k_abs = abs(k)
        geo_factor = np.sqrt(max(0.01, 1.0 + (k ** 2) * (r / R) ** 2 - 2.0 * k_abs * (r / R)))
        v_impact_nominal = Omega * R * geo_factor

        # Inelastic damping & wall contact factor (~0.72)
        v_impact_eff = v_impact_nominal * 0.72

        # Kinetic energy of one impact
        e_impact_j = 0.5 * self.single_ball_mass_kg * (v_impact_eff ** 2)

        # Collision frequency per ball (collisions/sec):
        # Driven by the relative slip between vial rotation and sun disc
        f_single_ball_hz = abs(self.kin.vial_omega_rel - self.kin.sun_omega) / (2.0 * np.pi) * 1.8
        f_total_vial_hz = f_single_ball_hz * self.num_balls

        # Dissipated impact power per vial (Watts)
        p_impact_vial_w = e_impact_j * f_total_vial_hz

        # Specific milling power (Watts per gram of powder)
        spec_power_w_per_g = p_impact_vial_w / self.powder_mass_g if self.powder_mass_g > 0 else 0.0

        return {
            "single_ball_mass_g": round(self.single_ball_mass_kg * 1e3, 3),
            "total_media_mass_g": round(self.total_media_mass_per_vial_kg * 1e3, 1),
            "bpr": round(self.ball_to_powder_ratio, 1),
            "vial_filling_ratio_pct": round(self.vial_filling_ratio * 100.0, 1),
            "nominal_impact_velocity_m_s": round(v_impact_nominal, 2),
            "effective_impact_velocity_m_s": round(v_impact_eff, 2),
            "single_impact_energy_mj": round(e_impact_j * 1e3, 3),
            "total_collision_frequency_hz": round(f_total_vial_hz, 0),
            "dissipated_impact_power_vial_w": round(p_impact_vial_w, 1),
            "total_milling_power_all_vials_w": round(p_impact_vial_w * self.kin.geom.num_vials, 1),
            "specific_power_w_per_g": round(spec_power_w_per_g, 2),
        }

    def simulate_sample_trajectories(self, num_points: int = 150) -> Dict[str, np.ndarray]:
        """
        Simulates representative 2D flight paths of grinding balls inside the rotating vial frame.
        Useful for 2D/3D visualization of cataracting trajectories.
        """
        r_v = self.kin.geom.vial_radius_m
        R_s = self.kin.geom.sun_radius_m
        Omega = self.kin.sun_omega
        omega = self.kin.vial_omega_rel

        # Generate vial inner circular perimeter
        theta = np.linspace(0, 2 * np.pi, 100)
        vial_wall_x = r_v * np.cos(theta)
        vial_wall_y = r_v * np.sin(theta)

        # Approximate flight paths of 3 balls launched at detachment angles
        launch_angles = [np.pi * 0.75, np.pi * 0.90, np.pi * 1.05]
        trajectories = []

        dyn = self.calculate_collision_dynamics()
        v_eff = dyn["effective_impact_velocity_m_s"]

        for phi in launch_angles:
            x0 = r_v * 0.92 * np.cos(phi)
            y0 = r_v * 0.92 * np.sin(phi)
            # Initial launch velocity vector directed across vial due to Coriolis
            vx = -v_eff * 0.7 * np.sin(phi)
            vy = v_eff * 0.7 * np.cos(phi)

            dt = (2.0 * r_v / v_eff) / num_points
            traj_x = [x0]
            traj_y = [y0]

            curr_x, curr_y = x0, y0
            curr_vx, curr_vy = vx, vy

            for _ in range(num_points):
                # Coriolis acceleration in vial frame: a_cor = 2 * Omega * v
                # Centrifugal accelerations
                ax = 2.0 * Omega * curr_vy + (omega ** 2) * curr_x
                ay = -2.0 * Omega * curr_vx + (omega ** 2) * curr_y

                curr_vx += ax * dt
                curr_vy += ay * dt
                curr_x += curr_vx * dt
                curr_y += curr_vy * dt

                # Check if ball hits opposite wall
                dist = np.sqrt(curr_x ** 2 + curr_y ** 2)
                if dist >= r_v * 0.92:
                    # Clip at wall
                    curr_x = (curr_x / dist) * r_v * 0.92
                    curr_y = (curr_y / dist) * r_v * 0.92
                    traj_x.append(curr_x)
                    traj_y.append(curr_y)
                    break
                traj_x.append(curr_x)
                traj_y.append(curr_y)

            trajectories.append((np.array(traj_x), np.array(traj_y)))

        return {
            "vial_wall_x": vial_wall_x,
            "vial_wall_y": vial_wall_y,
            "trajectories": trajectories,
        }


class NanoparticleKinetics:
    """
    Kinetics model for nanoparticle synthesis via high-energy ball milling.
    Models size reduction from micrometers down to tens of nanometers,
    including Hall-Petch dislocation limit and powder agglomeration equilibrium.
    """

    def __init__(
        self,
        specific_power_w_per_g: float,
        initial_d50_um: float = 45.0,       # Initial powder size in microns (e.g. 45 um = 45,000 nm)
        material_fracture_toughness_kic: float = 2.5,  # MPa * m^0.5 (e.g. Titanium/Oxide powder)
        use_surfactant_pca: bool = True,    # Process Control Agent (prevents cold-welding/agglomeration)
    ):
        self.spec_power = specific_power_w_per_g
        self.d0_nm = initial_d50_um * 1e3
        self.kic = material_fracture_toughness_kic
        self.use_pca = use_surfactant_pca

    def simulate(self, milling_hours: float = 12.0, num_steps: int = 200) -> Dict[str, np.ndarray]:
        """
        Integrates the comminution rate equation:
        d(D50)/dt = - K_break * (P_spec / Kic) * (D50 - D_limit) + K_agglom * D50^1.5
        """
        time_hours = np.linspace(0, milling_hours, num_steps)
        dt = (milling_hours * 3600.0) / num_steps

        # Theoretical minimum grain/particle limit (nanometers) based on dislocation pile-up limit
        # With surfactant, limit can be ~15 - 30 nm. Without surfactant, agglomeration limits to ~120 - 250 nm.
        d_limit_nm = 18.0 if self.use_pca else 140.0

        # Rate coefficients
        k_break = 0.00045 * (self.spec_power / max(1.0, self.kic))
        k_agglom = 0.00000008 if self.use_pca else 0.00000085

        d50_nm = np.zeros(num_steps)
        d90_nm = np.zeros(num_steps)
        ssa_m2_g = np.zeros(num_steps)  # Specific surface area
        crystallite_nm = np.zeros(num_steps)

        curr_d50 = self.d0_nm
        # Powder density assumption for surface area (g/cm^3)
        rho_powder = 4.5

        for i, t_h in enumerate(time_hours):
            d50_nm[i] = curr_d50
            d90_nm[i] = curr_d50 * 2.3  # Log-normal distribution spread
            # Specific surface area SSA = 6 / (rho * D_sauter)
            ssa_m2_g[i] = 6000.0 / (rho_powder * max(curr_d50, 1.0))
            # Crystallite size decreases faster than aggregate particle size
            crystallite_nm[i] = max(12.0, curr_d50 * 0.42 / (1.0 + 0.15 * t_h))

            # Rate of change
            breakage_rate = k_break * (curr_d50 - d_limit_nm)
            agglom_rate = k_agglom * (curr_d50 ** 1.35)
            net_rate = -breakage_rate + agglom_rate

            curr_d50 = max(d_limit_nm, curr_d50 + net_rate * dt)

        return {
            "time_hours": time_hours,
            "d50_nm": d50_nm,
            "d90_nm": d90_nm,
            "crystallite_nm": crystallite_nm,
            "ssa_m2_g": ssa_m2_g,
            "final_d50_nm": d50_nm[-1],
            "d_limit_nm": d_limit_nm,
        }
