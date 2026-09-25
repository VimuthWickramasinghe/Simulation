"""
Horizontal Jar Mill Kinematics, Dynamics, and Drive Sizing Module.
Calculates critical rotational speed (Nc), roller-to-jar friction drive ratio,
media cascading/cataracting/centrifuging operating regimes, detachment angles,
impact comminution velocities, power draw, and motor sizing.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional


@dataclass
class HorizontalMillGeometry:
    """
    Parametric geometry for a laboratory/pilot horizontal roller jar mill.
    """
    jar_inner_diameter_m: float = 0.200       # Internal jar diameter (200 mm)
    jar_outer_diameter_m: float = 0.220       # External jar diameter (220 mm)
    jar_length_m: float = 0.280               # Internal cylinder length (280 mm, ~8.8 L)
    jar_mass_empty_kg: float = 7.50           # Empty jar mass with lid and clamps (kg)
    
    roller_diameter_m: float = 0.065          # Polyurethane / rubber drive roller diameter (65 mm)
    roller_length_m: float = 0.650            # Roller length along horizontal axis (650 mm)
    roller_center_distance_m: float = 0.160   # Center-to-center distance between parallel rollers (160 mm)
    
    media_ball_diameter_m: float = 0.020      # Nominal grinding ball diameter (20 mm)
    media_density_kg_m3: float = 6000.0       # Media density (6000 kg/m^3 for ZrO2, 7850 for Steel, 3950 for Al2O3)
    media_filling_fraction: float = 0.35      # Volumetric media filling degree J (typically 0.30 - 0.40)
    
    powder_mass_kg: float = 1.20              # Charge dry powder mass (kg)
    powder_density_kg_m3: float = 2600.0      # Apparent powder bulk density (kg/m^3)
    friction_coeff_roller: float = 0.65       # Traction friction between rubber roller and jar shell


class HorizontalJarMillKinematics:
    """
    Complete kinematic and dynamic model for a Horizontal Roller Jar Mill.
    """

    def __init__(self, geometry: Optional[HorizontalMillGeometry] = None, jar_rpm: float = 75.0):
        self.geom = geometry or HorizontalMillGeometry()
        self.jar_rpm = float(jar_rpm)

    @property
    def critical_speed_rpm(self) -> float:
        """
        Theoretical critical rotational speed (Nc) in RPM.
        At Nc, centrifugal acceleration at jar inner radius balances gravitational acceleration g:
        omega_c^2 * (R_i - r_b) = g => Nc = 42.29 / sqrt(D_i - d_b)
        """
        effective_dia_m = max(0.01, self.geom.jar_inner_diameter_m - self.geom.media_ball_diameter_m)
        return 42.29 / np.sqrt(effective_dia_m)

    @property
    def speed_fraction_phi(self) -> float:
        """Fraction of critical speed: phi = N_jar / N_critical."""
        nc = self.critical_speed_rpm
        return (self.jar_rpm / nc) if nc > 0 else 0.0

    @property
    def percent_critical_speed(self) -> float:
        """Percentage of critical speed: % Nc."""
        return self.speed_fraction_phi * 100.0

    @property
    def roller_to_jar_ratio(self) -> float:
        """
        Speed transmission ratio between drive roller and jar outer circumference:
        N_jar = N_roller * (D_roller / D_jar_outer)
        ratio = D_roller / D_jar_outer
        """
        return self.geom.roller_diameter_m / max(0.01, self.geom.jar_outer_diameter_m)

    @property
    def required_roller_rpm(self) -> float:
        """Rotational speed of the motorized drive roller in RPM required to produce self.jar_rpm."""
        r = self.roller_to_jar_ratio
        return (self.jar_rpm / r) if r > 0 else 0.0

    @property
    def jar_tangential_velocity(self) -> float:
        """Linear peripheral surface velocity of the jar shell in m/s."""
        omega_jar = (self.jar_rpm * 2.0 * np.pi) / 60.0
        return omega_jar * (self.geom.jar_inner_diameter_m / 2.0)

    def classify_milling_regime(self) -> Dict[str, Any]:
        """
        Classifies operating comminution regime based on % Nc.
        """
        phi = self.speed_fraction_phi
        pct = phi * 100.0

        if pct <= 0.5:
            return {
                "regime": "System At Rest (0 RPM)",
                "color": "#64748b",
                "dominant_mechanism": "Static Equilibrium",
                "efficiency": 0.0,
                "description": "Drive motor is stopped. Media charge settles to the bottom of the horizontal jar."
            }
        elif pct < 45.0:
            return {
                "regime": "Sub-Critical Cascading",
                "color": "#d97706",
                "dominant_mechanism": "Inter-particle Friction & Attrition",
                "efficiency": 0.58,
                "description": "Media charge climbs smoothly up to 30-40 degrees and slides down the active surface. Low impact energy, excellent for gentle dispersion and fine polishing."
            }
        elif pct < 65.0:
            return {
                "regime": "Cascading (Abrasion Dominant)",
                "color": "#0284c7",
                "dominant_mechanism": "Shear, Rolling Friction & Attrition",
                "efficiency": 0.76,
                "description": "Continuous rolling layer with active charge surface. Uniform particle comminution via shear; minimum jar lining wear."
            }
        elif pct <= 85.0:
            return {
                "regime": "Optimal Cataracting",
                "color": "#16a34a",
                "dominant_mechanism": "Normal Ball Impact & Pinch Comminution",
                "efficiency": 0.96,
                "description": "Balls are lifted to the shoulder detachment angle and launch into true parabolic free flight, crashing violently into the toe zone. Maximum comminution kinetics!"
            }
        elif pct < 100.0:
            return {
                "regime": "Severe Cataracting (High-Throw)",
                "color": "#ea580c",
                "dominant_mechanism": "Direct Shell Impact & High Wear",
                "efficiency": 0.82,
                "description": "Balls launch very high and crash into the bare jar shell rather than the powder toe. Excessive jar lining wear and noise; reduce speed to 70-80% Nc."
            }
        else:
            return {
                "regime": "Centrifuging (Critical Stall)",
                "color": "#dc2626",
                "dominant_mechanism": "Wall Pinning (Zero Milling Action)",
                "efficiency": 0.05,
                "description": "Centrifugal acceleration exceeds gravity (g). Media balls remain pinned to the internal perimeter through 360 degrees. Grinding action ceases entirely!"
            }

    def calculate_detachment_angle_deg(self) -> float:
        """
        Angle alpha_d (degrees) where the outermost grinding ball detaches from the cylinder wall
        to begin parabolic free-flight cataracting:
        cos(alpha_d) = phi^2 = (N / N_c)^2
        alpha_d measured from the horizontal plane (0 deg = 3 o'clock, 90 deg = 12 o'clock apex).
        """
        phi = self.speed_fraction_phi
        if phi <= 0.0:
            return 90.0
        if phi >= 1.0:
            return 0.0  # Centrifuging (never detaches)
        cos_val = np.clip(phi ** 2, 0.0, 1.0)
        return float(np.degrees(np.arccos(cos_val)))

    def calculate_impact_kinetics(self) -> Dict[str, float]:
        """
        Computes single ball impact velocity, landing trajectory, and kinetic impact energy.
        """
        phi = self.speed_fraction_phi
        if phi <= 0.01:
            return {
                "detachment_angle_deg": 90.0,
                "impact_velocity_m_s": 0.0,
                "impact_energy_mJ": 0.0,
                "toe_landing_angle_deg": -60.0,
                "specific_impact_rate_hz": 0.0,
            }

        R = self.geom.jar_inner_diameter_m / 2.0
        omega = (self.jar_rpm * 2.0 * np.pi) / 60.0
        v0 = omega * R
        alpha_deg = self.calculate_detachment_angle_deg()
        alpha_rad = np.radians(alpha_deg)

        # In cataracting mode (0.65 <= phi <= 0.85), ball falls from apex zone to toe
        # Fall height delta_h ~ R * (1 + sin(alpha))
        delta_h = R * (1.0 + np.sin(alpha_rad)) if phi < 1.0 else 0.0
        v_impact = np.sqrt(max(0.0, v0**2 + 2.0 * 9.80665 * delta_h)) if phi < 1.0 else 0.0

        # Ball mass m_b
        r_b = self.geom.media_ball_diameter_m / 2.0
        v_b = (4.0 / 3.0) * np.pi * (r_b ** 3)
        m_b = v_b * self.geom.media_density_kg_m3
        e_impact_j = 0.5 * m_b * (v_impact ** 2)

        # Estimate collision rate across whole media charge
        v_jar = np.pi * (R ** 2) * self.geom.jar_length_m
        v_media = v_jar * self.geom.media_filling_fraction * 0.60 # bed packing
        num_balls = max(1, int(round(v_media / max(1e-7, v_b))))
        coll_freq_hz = num_balls * (self.jar_rpm / 60.0) * 4.8 * min(1.0, phi)

        return {
            "detachment_angle_deg": alpha_deg,
            "impact_velocity_m_s": round(float(v_impact), 2),
            "impact_energy_mJ": round(float(e_impact_j * 1e3), 3),
            "single_ball_mass_g": round(float(m_b * 1e3), 2),
            "total_media_balls": int(num_balls),
            "estimated_collision_rate_hz": round(float(coll_freq_hz), 1),
            "fall_height_mm": round(float(delta_h * 1e3), 1)
        }

    def calculate_power_and_drive_sizing(self) -> Dict[str, float]:
        """
        Computes mechanical milling power draw using the Hogg-Fuerstenau & Bond formulas,
        dynamic friction requirements, and motor drive sizing.
        """
        phi = self.speed_fraction_phi
        J = self.geom.media_filling_fraction
        L = self.geom.jar_length_m
        Di = self.geom.jar_inner_diameter_m
        
        # Apparent bulk density of charge (media + powder + void)
        rho_bulk = self.geom.media_density_kg_m3 * 0.60 + self.geom.powder_density_kg_m3 * 0.20

        # Hogg-Fuerstenau / Morrell mill power equation (kW):
        # P = 7.33 * J * (1 - 0.937 * J) * rho_app * L * Di^2.5 * phi * (1 - 0.1 / 2^(9 - 10 * phi))
        if phi > 0.0:
            phi_clamped = min(1.3, phi)
            centrifuging_factor = max(0.02, 1.0 - (0.1 / (2.0 ** max(0.1, 9.0 - 10.0 * phi_clamped))))
            p_net_kw = 7.33 * J * (1.0 - 0.937 * J) * (rho_bulk / 1000.0) * L * (Di ** 2.5) * phi_clamped * centrifuging_factor
            # Scale for lab scale jar mill (typically 40 W - 250 W)
            p_net_w = max(5.0, p_net_kw * 1000.0)
        else:
            p_net_w = 0.0

        # Total rotating mass: Jar + Media + Powder
        v_jar = np.pi * ((Di / 2.0) ** 2) * L
        m_media_kg = v_jar * J * self.geom.media_density_kg_m3 * 0.60
        m_total_jar_kg = self.geom.jar_mass_empty_kg + m_media_kg + self.geom.powder_mass_kg

        # Jar torque on horizontal axis: T = P / omega
        omega_jar = max(0.01, (self.jar_rpm * 2.0 * np.pi) / 60.0)
        t_jar_nm = (p_net_w / omega_jar) if self.jar_rpm > 0 else 0.0

        # Drive roller torque: T_roller = T_jar * (D_roller / D_jar)
        t_roller_nm = t_jar_nm * self.roller_to_jar_ratio

        # Friction limit: Normal reaction force on each roller
        # Symmetrical two-roller cradle support angle theta = arcsin(S_r / (D_jar + D_roller))
        s_r = self.geom.roller_center_distance_m
        d_sum = self.geom.jar_outer_diameter_m + self.geom.roller_diameter_m
        sin_theta = np.clip(s_r / d_sum, 0.1, 0.95)
        cos_theta = np.sqrt(1.0 - sin_theta**2)
        n_force_per_roller_n = (m_total_jar_kg * 9.80665) / (2.0 * cos_theta)
        f_max_traction_n = n_force_per_roller_n * self.geom.friction_coeff_roller
        t_max_traction_nm = f_max_traction_n * (self.geom.roller_diameter_m / 2.0)

        # Drive mechanical transmission efficiency
        eta_trans = 0.82
        required_continuous_motor_w = (p_net_w / eta_trans) if p_net_w > 0 else 0.0

        # Starting torque sizing (1.8x continuous torque for charge breakaway)
        recommended_motor_w = max(120.0, np.ceil(required_continuous_motor_w * 1.5 / 50.0) * 50.0)

        return {
            "net_milling_power_w": round(float(p_net_w), 1),
            "jar_continuous_torque_nm": round(float(t_jar_nm), 2),
            "roller_continuous_torque_nm": round(float(t_roller_nm), 2),
            "total_supported_mass_kg": round(float(m_total_jar_kg), 2),
            "media_charge_mass_kg": round(float(m_media_kg), 2),
            "normal_force_per_roller_n": round(float(n_force_per_roller_n), 1),
            "max_available_traction_nm": round(float(t_max_traction_nm), 2),
            "slip_safety_factor": round(float(t_max_traction_nm / max(0.1, t_roller_nm)), 2) if t_roller_nm > 0 else 99.0,
            "electrical_motor_power_w": round(float(required_continuous_motor_w), 1),
            "recommended_motor_rating_w": int(recommended_motor_w),
            "recommended_motor_hp": round(float(recommended_motor_w / 745.7), 2),
        }

    def summary(self) -> Dict[str, Any]:
        """Comprehensive summary of horizontal jar mill kinematics and sizing."""
        regime = self.classify_milling_regime()
        kinetics = self.calculate_impact_kinetics()
        drive = self.calculate_power_and_drive_sizing()
        return {
            "jar_rpm": self.jar_rpm,
            "critical_speed_rpm": round(self.critical_speed_rpm, 1),
            "percent_critical_speed": round(self.percent_critical_speed, 1),
            "roller_to_jar_ratio": round(self.roller_to_jar_ratio, 4),
            "required_roller_rpm": round(self.required_roller_rpm, 1),
            "jar_surface_speed_m_s": round(self.jar_tangential_velocity, 2),
            "regime": regime,
            "kinetics": kinetics,
            "drive": drive
        }
