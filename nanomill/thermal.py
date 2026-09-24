"""
Thermal Simulation and Heat Dissipation Module for Ball Milling Vials.
Models inelastic collision heat generation, conduction through vial walls,
forced convective heat transfer from spinning vials to ambient air,
transient temperature curves, and safety thermal limits for nanoparticle preservation.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple
from .kinematics import PlanetaryKinematics


@dataclass
class VialMaterialThermal:
    name: str
    thermal_conductivity_w_mk: float  # k (W/m*K)
    density_kg_m3: float              # rho (kg/m^3)
    specific_heat_j_kgk: float        # Cp (J/kg*K)
    max_safe_temp_c: float = 180.0    # Max safe operating temp before seal failure/oxidation


VIAL_THERMAL_DATABASE = {
    "Zirconia (ZrO2)": VialMaterialThermal(
        name="Zirconia (ZrO2)",
        thermal_conductivity_w_mk=2.7,   # Ceramic insulator: traps internal heat
        density_kg_m3=6000.0,
        specific_heat_j_kgk=450.0,
        max_safe_temp_c=160.0,
    ),
    "Stainless Steel (AISI 316)": VialMaterialThermal(
        name="Stainless Steel (AISI 316)",
        thermal_conductivity_w_mk=16.3,
        density_kg_m3=7900.0,
        specific_heat_j_kgk=500.0,
        max_safe_temp_c=220.0,
    ),
    "Tungsten Carbide (WC)": VialMaterialThermal(
        name="Tungsten Carbide (WC)",
        thermal_conductivity_w_mk=84.0,  # Highly conductive: dissipates heat quickly
        density_kg_m3=14900.0,
        specific_heat_j_kgk=210.0,
        max_safe_temp_c=250.0,
    ),
}


class MillingThermalModel:
    """
    Transient and steady-state thermal model of a milling vial.
    Calculates internal temperature rise during high-energy nano-milling.
    """

    def __init__(
        self,
        kinematics: PlanetaryKinematics,
        milling_power_per_vial_w: float,
        vial_material: str = "Stainless Steel (AISI 316)",
        vial_wall_thickness_mm: float = 12.0,
        ambient_temp_c: float = 25.0,
        forced_fan_airflow_m_s: float = 2.5,  # Auxiliary enclosure ventilation fan speed
    ):
        self.kin = kinematics
        self.power_in_w = milling_power_per_vial_w
        self.mat = VIAL_THERMAL_DATABASE.get(
            vial_material, VIAL_THERMAL_DATABASE["Stainless Steel (AISI 316)"]
        )
        self.wall_th_m = vial_wall_thickness_mm * 1e-3
        self.t_amb = ambient_temp_c
        self.fan_speed = forced_fan_airflow_m_s

    @property
    def r_inner_m(self) -> float:
        return self.kin.geom.vial_radius_m

    @property
    def r_outer_m(self) -> float:
        return self.kin.geom.vial_radius_m + self.wall_th_m

    @property
    def vial_height_m(self) -> float:
        return self.kin.geom.vial_height_m

    def external_surface_area_m2(self) -> float:
        """Outer cylindrical surface area + top/bottom caps."""
        cyl_area = 2.0 * np.pi * self.r_outer_m * self.vial_height_m
        cap_area = 2.0 * np.pi * (self.r_outer_m ** 2)
        return cyl_area + cap_area

    def calculate_convective_heat_transfer_coefficient(self) -> float:
        """
        Calculates forced convective heat transfer coefficient h (W/m^2*K).
        Accounts for rotational peripheral velocity of vial through air + auxiliary fan.
        """
        # Peripheral linear velocity of vial center through air: v = Omega * R_sun
        v_rot = self.kin.sun_omega * self.kin.geom.sun_radius_m
        effective_air_velocity = np.sqrt(v_rot ** 2 + self.fan_speed ** 2)

        # Cylinder in crossflow correlation (simplified Churchill-Bernstein / Hilpert)
        # Air properties at ~50 deg C: nu = 1.79e-5 m^2/s, k_air = 0.027 W/m*K, Pr = 0.71
        d_outer = 2.0 * self.r_outer_m
        reynolds = (effective_air_velocity * d_outer) / 1.79e-5

        # Nusselt number approximation
        if reynolds < 4000:
            nusselt = 0.683 * (reynolds ** 0.466) * (0.71 ** 0.33)
        elif reynolds < 40000:
            nusselt = 0.193 * (reynolds ** 0.618) * (0.71 ** 0.33)
        else:
            nusselt = 0.027 * (reynolds ** 0.805) * (0.71 ** 0.33)

        h_conv = (nusselt * 0.027) / max(d_outer, 1e-3)
        return float(np.clip(h_conv, 15.0, 250.0))

    def thermal_resistances(self) -> Dict[str, float]:
        """Calculates conductive and convective thermal resistances in K/W."""
        # Radial conduction through cylindrical wall:
        # R_cond = ln(r_out / r_in) / (2 * pi * k * H)
        r_cond = np.log(self.r_outer_m / self.r_inner_m) / (
            2.0 * np.pi * self.mat.thermal_conductivity_w_mk * self.vial_height_m
        )

        # External convection:
        h_conv = self.calculate_convective_heat_transfer_coefficient()
        a_ext = self.external_surface_area_m2()
        r_conv = 1.0 / (h_conv * a_ext)

        r_total = r_cond + r_conv
        return {
            "r_cond_k_w": r_cond,
            "r_conv_k_w": r_conv,
            "r_total_k_w": r_total,
            "h_conv_w_m2k": h_conv,
        }

    def simulate_transient(self, total_milling_time_min: float = 120.0, num_steps: int = 200) -> Dict[str, Any]:
        """
        Integrates transient temperature rise:
        M_vial * Cp * dT/dt = Q_gen - (T - T_amb) / R_total
        where Q_gen ~ 90% of dissipated impact power.
        """
        # Inelastic mechanical dissipation to heat fraction
        eta_thermal = 0.90
        q_gen_w = self.power_in_w * eta_thermal

        res = self.thermal_resistances()
        r_tot = res["r_total_k_w"]

        # Vial mass (cylinder shell)
        vol_shell = np.pi * (self.r_outer_m ** 2 - self.r_inner_m ** 2) * self.vial_height_m
        m_vial_kg = vol_shell * self.mat.density_kg_m3
        c_th = m_vial_kg * self.mat.specific_heat_j_kgk  # Thermal capacitance (J/K)

        time_sec = np.linspace(0, total_milling_time_min * 60.0, num_steps)
        time_min = time_sec / 60.0

        # Steady-state temperature (deg C)
        delta_t_ss = q_gen_w * r_tot
        t_steady_state = self.t_amb + delta_t_ss

        # Thermal time constant tau = R * C (seconds)
        tau_sec = r_tot * c_th

        # Analytical transient solution
        t_internal_c = self.t_amb + delta_t_ss * (1.0 - np.exp(-time_sec / max(tau_sec, 1.0)))

        # Safety evaluation
        max_reached_temp = float(t_internal_c[-1])
        is_safe = max_reached_temp <= self.mat.max_safe_temp_c
        duty_cycle_recommendation = (
            "Continuous milling acceptable with adequate enclosure ventilation."
            if is_safe and max_reached_temp < 110.0
            else f"Pulsed milling recommended: 15 min ON / 15 min cooling PAUSE to maintain < {self.mat.max_safe_temp_c:.0f}°C."
        )

        return {
            "time_minutes": time_min,
            "internal_temp_c": t_internal_c,
            "ambient_temp_c": self.t_amb,
            "steady_state_temp_c": round(t_steady_state, 1),
            "max_reached_temp_c": round(max_reached_temp, 1),
            "max_safe_temp_c": self.mat.max_safe_temp_c,
            "thermal_time_constant_min": round(tau_sec / 60.0, 1),
            "q_gen_w": round(q_gen_w, 1),
            "h_conv_w_m2k": round(res["h_conv_w_m2k"], 1),
            "is_thermally_safe": is_safe,
            "cooling_recommendation": duty_cycle_recommendation,
        }
