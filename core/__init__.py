"""Core simulation package: GMAT setup and satellite dynamics.

Provides:
    - ``Satellite``: GMAT spacecraft wrapper.
    - ``create_satellite``: Factory for satellites with given true anomaly.
    - ``satellites``: List of Satellite instances (built at import).
    - ``fm``, ``pdprop``, ``gator``: GMAT force model, propagator, integrator.
    - ``initialize_data_structures``: Build data_magnetic, data_dyn_kin, data_PV, data_geodetic.
    - ``SatelliteSimulator``: Attitude dynamics and magnetic field calculation.
    - ``MagneticFieldData``: Wrapper for exported simulation data for viz.
"""

from core.gmat_sim import (
    Satellite,
    create_satellite,
    satellites,
    fm,
    pdprop,
    gator,
    initialize_data_structures,
)
from core.satellite_simulator import SatelliteSimulator, MagneticFieldData

__all__ = [
    "Satellite",
    "create_satellite",
    "satellites",
    "fm",
    "pdprop",
    "gator",
    "initialize_data_structures",
    "SatelliteSimulator",
    "MagneticFieldData",
]
