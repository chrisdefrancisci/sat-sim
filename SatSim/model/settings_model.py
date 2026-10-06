
from SatSim.model.orbit_model import OrbitModel

class SettingsModel:
    """
    Model to represent the data for user-configurable settings.
    """
    def __init__(self):
        self.target_orbit = OrbitModel()
        self.chaser_orbit = OrbitModel()
        self.orbit_maneuvers = []

    def get(self) -> dict:
        target = self.target_orbit.get()
        chaser = self.chaser_orbit.get()

        return {"orbits" : {"target": target, "chaser": chaser},
                "maneuvers": [man.get() for man in self.orbit_maneuvers]}

    def set(self, settings) -> None:
        self.target_orbit.set(**settings["orbits"]["target"])
        self.chaser_orbit.set(**settings["orbits"]["chaser"])
        self.orbit_maneuvers = []
        # for man in settings["maneuvers"]: