import ttkbootstrap as ttk

from SatSim.controller.label_entry import LabelEntry
from SatSim.controller.array_entry import ArrayEntry, QuaternionEntry
from SatSim.model.settings_model import MekfSettingsModel

class EstimatorSettings(ttk.Frame):
    def __init__(self, parent, model: MekfSettingsModel):
        super().__init__(parent)
        ttk.Label(self, text="MEKF Settings").pack(side="top", fill="x", expand=False, pady=5)
        self.body = ttk.Frame(self)
        self.body.pack(side="top", fill="both", expand=True)

        self.entries = LabelEntry(self.body, ("dt", "bias", "var_ang_vel", "var_bias_walk"),
                                  ("Period (s)", "Init Gyro Bias (rad/s)", "Gyro noise var (rad^2/s)", "Gyro walk var (rad^2/s^3)"),
                                  variables=(model.dt, model.init_bias, model.var_ang_vel, model.var_bias_walk),
                                  orient="vertical")
        
        
        self.entries.grid(row=0, column=0, padx=(5,10), sticky="w")

        ttk.Label(self.body, text="Initial \nAttitude").grid(row=0, column=1, padx=(5,0), sticky="w")
        self.att_init = QuaternionEntry(self.body, model.init_attitude)
        self.att_init.grid(row=0, column=2, padx=(5,10), sticky="w")

        self.cov_init = ArrayEntry(self.body, shape=(2, 1), labels=("Att Var", "Bias Var"))
        self.cov_init.grid(row=0, column=3, padx=(5,10), sticky="w")
        
        self.body.rowconfigure((0,1), weight=0)
        self.body.rowconfigure((2,3), weight=1)

    