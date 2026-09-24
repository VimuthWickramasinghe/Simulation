"""
NanoMill: Multiphysics Simulation and 3D Modeling Suite for Nanoparticle Ball Milling Machines.
Includes mechanical kinematics, DEM ball collision dynamics, nano-comminution kinetics,
thermal dissipation modeling, AI-friendly CAD generation (OpenSCAD/STL), and engineering reporting.
"""

from .kinematics import PlanetaryKinematics, DriveSystemSizing
from .particles import BallMillDEM, NanoparticleKinetics, GrindingMediaMaterial
from .thermal import MillingThermalModel, VialMaterialThermal
from .cad_generator import BallMillCADGenerator
from .report import EngineeringReportGenerator

__version__ = "1.0.0"
__all__ = [
    "PlanetaryKinematics",
    "DriveSystemSizing",
    "BallMillDEM",
    "NanoparticleKinetics",
    "GrindingMediaMaterial",
    "MillingThermalModel",
    "VialMaterialThermal",
    "BallMillCADGenerator",
    "EngineeringReportGenerator",
]
