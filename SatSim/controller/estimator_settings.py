import ttkbootstrap as ttk

from SatSim.controller.array_entry import QuaternionEntry

class EstimatorSettings(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Estimator Settings").pack(side="top", fill="x", expand=False, pady=5)
        self.body = ttk.Frame(self)
        self.body.pack(side="top", fill="both", expand=True)
        ttk.Label(self.body, text="Initial \nAttitude").grid(row=0, column=0, padx=(5,0), stick="w")
        self.att_init = QuaternionEntry(self.body)
        self.att_init.grid(row=0, column=1, padx=(5,10), stick="w")
        
        self.body.rowconfigure((0,), weight=0)
        self.body.rowconfigure((1,), weight=1)

    