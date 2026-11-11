import tkinter as tk
import ttkbootstrap as ttk

from SatSim.app import App


def main():
    # See https://www.ttkbootstrap.org/en/latest/themes.html for themes
    app = ttk.App(title="Satellite Orbit Simulator", theme="vapor-dark")

    app.state('zoomed')
    # # Get screen dimensions
    # screen_width = app.winfo_screenwidth() * 0.75
    # screen_height = app.winfo_screenheight() * 0.75

    # # Clamp width and height so they do not exceed screen dimensions
    # final_width = max(app.winfo_width(), screen_width)
    # final_height = max(app.winfo_height(), screen_height)

    # # Optional: center the window or set initial geometry
    # x_pos = (screen_width - final_width) // 2
    # y_pos = (screen_height - final_height) // 2

    # app.geometry(f"{final_width}x{final_height}+{x_pos}+{y_pos}")

    App(app)
    app.mainloop()


if __name__ == '__main__':
    main()
