"""
Planetary Ball Mill Kinematics and Drive Sizing Module.
Calculates rotational velocities, non-inertial acceleration fields (centrifugal + Coriolis),
G-forces, milling regimes, inertia, and motor power requirements.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple


@dataclass
class MillGeometry:
    sun_radius_m: float = 0.15       # Radius of sun disk (axis to vial center) in meters
    vial_radius_m: float = 0.045     # Internal radius of milling vial in meters
    vial_height_m: float = 0.090     # Internal height of milling vial in meters
    num_vials: int = 4               # Number of milling vials (typically 2 or 4)
    vial_mass_kg: float = 1.2        # Empty mass of one vial (e.g. Stainless Steel or Zirconia)


@dataclass
class PlanetaryGears:
    sun_teeth: int = 60
    planet_teeth: int = 30
    module_mm: float = 2.5

    @property
    def gear_ratio_k(self) -> float:
        """Gear ratio k = -Z_sun / Z_planet for counter-rotating planetary setup."""
        return -float(self.sun_teeth) / float(self.planet_teeth)

    @property
    def sun_pitch_diameter_mm(self) -> float:
        return self.module_mm * self.sun_teeth

    @property
    def planet_pitch_diameter_mm(self) -> float:
        return self.module_mm * self.planet_teeth

    @classmethod
    def from_ratio(cls, k: float, module_mm: float = 2.5) -> "PlanetaryGears":
        """Calculates standard gear teeth matching the given transmission ratio k."""
        k_abs = abs(k)
        planet_teeth = 30
        sun_teeth = int(round(k_abs * planet_teeth))
        return cls(sun_teeth=sun_teeth, planet_teeth=planet_teeth, module_mm=module_mm)


class PlanetaryKinematics:
    """
    Kinematic analysis of a planetary ball mill.
    Sun wheel rotates at Omega (rad/s), vials rotate around their own axes at omega (rad/s).
    """

    def __init__(
        self,
        geometry: MillGeometry = None,
        sun_rpm: float = 400.0,
        gear_ratio_k: float = -2.0,  # Negative denotes counter-rotation (standard high-energy mode)
    ):
        self.geom = geometry or MillGeometry()
        self.sun_rpm = sun_rpm
        self.gear_ratio_k = gear_ratio_k
        self.gears = PlanetaryGears.from_ratio(gear_ratio_k)

    @property
    def sun_omega(self) -> float:
        """Sun disk angular velocity in rad/s."""
        return self.sun_rpm * 2.0 * np.pi / 60.0

    @property
    def vial_omega_rel(self) -> float:
        """Vial angular velocity relative to sun disk in rad/s."""
        return self.gear_ratio_k * self.sun_omega

    @property
    def vial_rpm_rel(self) -> float:
        """Vial relative RPM."""
        return self.gear_ratio_k * self.sun_rpm

    @property
    def vial_omega_abs(self) -> float:
        """Absolute vial angular velocity in stationary lab frame in rad/s."""
        return self.sun_omega + self.vial_omega_rel

    def g_force_sun(self) -> float:
        """Centrifugal acceleration ratio at vial center due to sun disk rotation (G-factor)."""
        a_cent = (self.sun_omega ** 2) * self.geom.sun_radius_m
        return a_cent / 9.80665

    def g_force_vial_wall(self) -> float:
        """Peak centrifugal acceleration ratio at the inner vial wall."""
        a_cent_vial = (self.vial_omega_rel ** 2) * self.geom.vial_radius_m
        return a_cent_vial / 9.80665

    def calculate_acceleration_field(self, theta_rad: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculates non-inertial acceleration components around the inner vial perimeter.
        theta_rad is the angle along the vial circumference (0 to 2*pi).
        """
        R = self.geom.sun_radius_m
        r = self.geom.vial_radius_m
        Omega = self.sun_omega
        omega = self.vial_omega_rel

        # Centrifugal acceleration due to sun disk (along radial vector to vial center)
        a_sun = (Omega ** 2) * R
        # Centrifugal acceleration due to vial rotation (radially outward from vial axis)
        a_vial = (omega ** 2) * r

        # Net radial acceleration on a static ball on the vial wall
        # In non-inertial frame of vial:
        a_rad_net = a_vial + a_sun * np.cos(theta_rad)
        a_tang_net = -a_sun * np.sin(theta_rad)
        total_a = np.sqrt(a_rad_net ** 2 + a_tang_net ** 2)

        return {
            "theta": theta_rad,
            "radial_accel_m_s2": a_rad_net,
            "tangential_accel_m_s2": a_tang_net,
            "total_accel_m_s2": total_a,
            "g_force": total_a / 9.80665,
        }

    def milling_regime(self) -> Dict[str, Any]:
        """
        Determines the dominant milling motion regime:
        - Cataracting: High-energy ball detachment and free flight across vial (OPTIMUM for nanoparticles).
        - Cascading: Continuous rolling/sliding along wall (attrition milling).
        - Centrifuging: Balls pinned against outer wall by centrifugal force (zero milling efficiency).
        """
        k = abs(self.gear_ratio_k)
        R = self.geom.sun_radius_m
        r = self.geom.vial_radius_m

        # Ratio of planetary to vial radius
        radius_ratio = R / r

        # Critical gear ratio threshold for detachment:
        # Detachment occurs when Coriolis and sun centrifugal forces overcome vial centrifugal force
        # Burgio et al. / Magini formulation
        crit_k_lower = 1.0
        crit_k_upper = np.sqrt(radius_ratio)

        if k < crit_k_lower:
            regime = "Cascading (Friction & Attrition Dominant)"
            suitability = "Moderate for micro-scale grinding; too slow for rapid nanoparticle synthesis."
        elif crit_k_lower <= k <= crit_k_upper * 1.5:
            regime = "Cataracting (High-Energy Normal Impact Dominant)"
            suitability = "EXCELLENT. Optimum trajectory for nanoparticle formation via shock fracture."
        else:
            regime = "Centrifuging (Dead-Zone / Pinning)"
            suitability = "POOR. Balls remain pinned to vial walls due to excessive vial spin."

        return {
            "regime": regime,
            "suitability_for_nanoparticles": suitability,
            "gear_ratio_abs": k,
            "radius_ratio": radius_ratio,
            "critical_k_detachment": crit_k_upper,
        }

    def summary(self) -> Dict[str, Any]:
        """Returns key kinematic parameters."""
        regime_info = self.milling_regime()
        return {
            "sun_rpm": self.sun_rpm,
            "vial_rpm_rel": self.vial_rpm_rel,
            "gear_ratio_k": self.gear_ratio_k,
            "sun_omega_rad_s": round(self.sun_omega, 2),
            "vial_omega_rad_s": round(self.vial_omega_rel, 2),
            "g_force_sun": round(self.g_force_sun(), 1),
            "g_force_vial": round(self.g_force_vial_wall(), 1),
            "regime": regime_info["regime"],
            "suitability": regime_info["suitability_for_nanoparticles"],
        }


class DriveSystemSizing:
    """
    Sizing calculations for the mechanical drive, motor, and transmission.
    """

    def __init__(
        self,
        kinematics: PlanetaryKinematics,
        disk_mass_kg: float = 6.5,
        total_media_mass_kg: float = 1.8,
        total_powder_mass_kg: float = 0.2,
        accel_time_sec: float = 4.0,
        drive_efficiency: float = 0.82,
        service_factor: float = 1.35,
    ):
        self.kin = kinematics
        self.disk_mass = disk_mass_kg
        self.media_mass = total_media_mass_kg
        self.powder_mass = total_powder_mass_kg
        self.accel_time = accel_time_sec
        self.efficiency = drive_efficiency
        self.service_factor = service_factor

    def moments_of_inertia(self) -> Dict[str, float]:
        """Calculates moments of inertia (kg * m^2) about the central sun axis."""
        R_d = self.kin.geom.sun_radius_m * 1.25  # Disk outer radius
        # Sun disk inertia (solid cylinder approximation)
        I_disk = 0.5 * self.disk_mass * (R_d ** 2)

        # Loaded vials inertia about central axis via parallel axis theorem
        m_vial_total = (
            self.kin.geom.vial_mass_kg
            + (self.media_mass + self.powder_mass) / self.kin.geom.num_vials
        )
        r_v = self.kin.geom.vial_radius_m
        R_p = self.kin.geom.sun_radius_m
        N = self.kin.geom.num_vials

        I_one_vial = 0.5 * m_vial_total * (r_v ** 2) + m_vial_total * (R_p ** 2)
        I_all_vials = N * I_one_vial

        I_total = I_disk + I_all_vials
        return {
            "I_disk_kg_m2": I_disk,
            "I_vials_kg_m2": I_all_vials,
            "I_total_kg_m2": I_total,
        }

    def calculate_motor_requirements(self, milling_dissipated_power_w: float = 350.0) -> Dict[str, Any]:
        """
        Calculates required motor torque, acceleration torque, and electrical power.
        """
        inertias = self.moments_of_inertia()
        I_total = inertias["I_total_kg_m2"]
        Omega = self.kin.sun_omega

        # Acceleration angular acceleration alpha
        alpha = Omega / self.accel_time
        torque_accel = I_total * alpha

        # Steady-state torque to maintain milling dissipation + friction (assume 10% mechanical bearing friction)
        torque_milling = milling_dissipated_power_w / Omega if Omega > 0 else 0.0
        torque_friction = 0.10 * torque_milling + 0.35  # Bearing seal drag ~0.35 Nm

        peak_torque = torque_accel + torque_friction
        continuous_torque = torque_milling + torque_friction

        # Power ratings (Watts)
        p_continuous_mech = continuous_torque * Omega
        p_continuous_elec = (p_continuous_mech / self.efficiency) * self.service_factor

        p_peak_mech = peak_torque * Omega
        p_peak_elec = (p_peak_mech / self.efficiency)

        # Recommend standard motor
        standard_ratings_w = [250, 370, 550, 750, 1100, 1500, 2200]
        recommended_motor_w = standard_ratings_w[-1]
        for rating in standard_ratings_w:
            if rating >= p_continuous_elec:
                recommended_motor_w = rating
                break

        return {
            "I_total_kg_m2": round(I_total, 4),
            "acceleration_torque_nm": round(torque_accel, 2),
            "continuous_torque_nm": round(continuous_torque, 2),
            "peak_torque_nm": round(peak_torque, 2),
            "milling_power_w": round(milling_dissipated_power_w, 1),
            "required_continuous_elec_power_w": round(p_continuous_elec, 1),
            "required_peak_elec_power_w": round(p_peak_elec, 1),
            "recommended_motor_w": recommended_motor_w,
            "recommended_motor_hp": round(recommended_motor_w / 745.7, 2),
            "transmission_type": "Synchronous Timing Belt (HTD 5M or 8M) / Direct Planetary Helical Gearbox",
        }
