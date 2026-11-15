import sys
import ttkbootstrap as ttk

from SatSim.app import App


def main():
    # See https://www.ttkbootstrap.org/en/latest/themes.html for themes
    app = ttk.App(title="Satellite Orbit Simulator", theme="vapor-dark")

    if sys.platform.startswith("linux"):
        app.attributes("-zoomed", True)
    else:
        app.state('zoomed')

    App(app)
    app.mainloop()


if __name__ == '__main__':
    main()
