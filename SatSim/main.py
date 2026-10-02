import tkinter as tk
import ttkbootstrap as ttk

from SatSim.app import App


def main():
    # See https://www.ttkbootstrap.org/en/latest/themes.html for themes
    app = ttk.App(title="Satellite Orbit Simulator", theme="vapor-dark")

    App(app)

    app.mainloop()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
