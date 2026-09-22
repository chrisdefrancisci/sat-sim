import tkinter as tk

from SatSim.app import App


def main():
    root = tk.Tk()
    root.title("Satellite Orbit Simulator")
    root.geometry("1000x800")

    app = App(root)

    root.mainloop()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
