"""GMAT spacecraft, force model, propagator, and data structures.

Builds Satellite instances, force model (gravity, drag, SRP, point masses),
propagator and integrator, and initializes data dictionaries for magnetic,
dynamics/kinematics, position/velocity, and geodetic data.

GMAT is initialized and propagator prepared at import time.
"""

from load_gmat import gmat, get_gmat_data_path

from config.constants import Constants


class Satellite:
    """GMAT spacecraft wrapper with Keplerian state and get_state via gator."""

    def __init__(self, name, sma, ecc, inc, ra, aop, ta, srp_area, cr, cd, dry_mass, drag_area):
        self.spacecraft = gmat.Construct("Spacecraft", name)
        self.setup_spacecraft(sma, ecc, inc, ra, aop, ta, srp_area, cr, cd, dry_mass, drag_area)

    def setup_spacecraft(self, sma, ecc, inc, ra, aop, ta, srp_area, cr, cd, dry_mass, drag_area):
        """Set GMAT spacecraft fields (epoch, frame, Keplerian, mass, areas)."""
        self.spacecraft.SetField("DateFormat", "UTCGregorian")
        self.spacecraft.SetField("Epoch", "20 Jul 2020 12:00:00.000")
        self.spacecraft.SetField("CoordinateSystem", "EarthMJ2000Eq")
        self.spacecraft.SetField("DisplayStateType", "Keplerian")
        self.spacecraft.SetField("SMA", sma)
        self.spacecraft.SetField("ECC", ecc)
        self.spacecraft.SetField("INC", inc)
        self.spacecraft.SetField("RAAN", ra)
        self.spacecraft.SetField("AOP", aop)
        self.spacecraft.SetField("TA", ta)
        self.spacecraft.SetField("SRPArea", srp_area)
        self.spacecraft.SetField("Cr", cr)
        self.spacecraft.SetField("Cd", cd)
        self.spacecraft.SetField("DryMass", dry_mass)
        self.spacecraft.SetField("DragArea", drag_area)

    def get_state(self, gator):
        """Return current state from propagator (position + velocity)."""
        return gator.GetState()

    def get_name(self):
        """Return spacecraft name string."""
        return self.spacecraft.GetName()


def create_satellite(name, ta):
    """Create a Satellite with Constants.SATELLITE_PARAMS and given true anomaly.

    Args:
        name: Spacecraft name (e.g. Taurus1).
        ta: True anomaly in degrees.

    Returns:
        Satellite: Configured GMAT spacecraft instance.
    """
    params = Constants.SATELLITE_PARAMS
    return Satellite(
        name=name,
        sma=params["sma"],
        ecc=params["ecc"],
        inc=params["inc"],
        ra=params["ra"],
        aop=params["aop"],
        ta=ta,
        srp_area=params["srp_area"],
        cr=params["cr"],
        cd=params["cd"],
        dry_mass=params["dry_mass"],
        drag_area=params["drag_area"],
    )


# List of Satellite instances; built at import from Constants.TRUE_ANOMALIES.
satellites = []
for k, ta in enumerate(Constants.TRUE_ANOMALIES):
    satellite = create_satellite(name=f"Taurus{k + 1}", ta=ta)
    satellites.append(satellite)

# Force model
fm = gmat.Construct("ForceModel", "FM")
earthgrav = gmat.Construct("GravityField")
earthgrav.SetField("BodyName", "Earth")
earthgrav.SetField("PotentialFile", get_gmat_data_path("gravity", "earth", "EGM96.cof"))
earthgrav.SetField("Degree", 8)
earthgrav.SetField("Order", 8)

moongrav = gmat.Construct("PointMassForce")
moongrav.SetField("BodyName", "Luna")
sungrav = gmat.Construct("PointMassForce")
sungrav.SetField("BodyName", "Sun")

jrdrag = gmat.Construct("DragForce")
jrdrag.SetField("AtmosphereModel", "JacchiaRoberts")
jrdrag.SetField("MagneticIndex", 6)
atmos = gmat.Construct("JacchiaRoberts")
jrdrag.SetReference(atmos)

srp = gmat.Construct("SolarRadiationPressure", "SRP")

fm.AddForce(earthgrav)
fm.AddForce(jrdrag)
fm.AddForce(moongrav)
fm.AddForce(sungrav)
fm.AddForce(srp)

gmat.Initialize()

pdprop = gmat.Construct("Propagator", "PDProp")
gator = gmat.Construct("PrinceDormand78", "Gator")
pdprop.SetReference(gator)
pdprop.SetReference(fm)
pdprop.SetField("InitialStepSize", 60)
pdprop.SetField("Accuracy", 1.0e-12)
pdprop.SetField("MinStep", 0.0)
pdprop.SetField("MaxStep", Constants.STEP)

for satellite in satellites:
    pdprop.AddPropObject(satellite.spacecraft)
pdprop.PrepareInternals()

gator = pdprop.GetPropagator()


def initialize_data_structures(satellites):
    """Build empty data dicts for magnetic, dynamics/kinematics, PV, and geodetic.

    Args:
        satellites: List of Satellite instances (each has get_name()).

    Returns:
        tuple: (data_magnetic, data_dyn_kin, data_PV, data_geodetic), each
            a dict keyed by spacecraft name with list fields as in original script.
    """
    data_magnetic = {
        sc.get_name(): {
            "Bint_ECI": [],
            "Bext_ECI": [],
            "Btot_ECI": [],
            "Btot_body": [],
            "Btot_ECEF": [],
        }
        for sc in satellites
    }

    data_dyn_kin = {
        sc.get_name(): {
            "w": [],
            "q": [],
            "DCM": [],
            "euler": [],
            "quat_turn": [],
        }
        for sc in satellites
    }

    data_PV = {
        sc.get_name(): {
            "R_ECI": [],
            "R_Body": [],
            "velocity": [],
        }
        for sc in satellites
    }

    data_geodetic = {
        sc.get_name(): {
            "latitude": [],
            "longitude": [],
            "altitude": [],
        }
        for sc in satellites
    }

    return data_magnetic, data_dyn_kin, data_PV, data_geodetic
