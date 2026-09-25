"""
Horizontal Jar Mill Simulation & CAD Suite.
Covers roller bench laboratory jar mills with dual polyurethane drive rollers,
friction-driven horizontal milling jars, critical speed (% Nc) kinematics,
cascading/cataracting/centrifuging DEM dynamics, and interactive 3D WebGL viewers.
"""

from .kinematics import HorizontalMillGeometry, HorizontalJarMillKinematics
from .cad_generator import HorizontalJarMillCADGenerator

__all__ = [
    "HorizontalMillGeometry",
    "HorizontalJarMillKinematics",
    "HorizontalJarMillCADGenerator",
]
