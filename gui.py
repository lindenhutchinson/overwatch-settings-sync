import tkinter as tk
from tkinter import filedialog
import os
from main import load_settings_from_json, save_settings_to_json

# todo: 
# - implement threading on button actions (stop the gui freezing while execution)
# - implement an escape button to cancel execution of program

class SensitivitySettingsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sensitivity Settings App")
        self.settings_file = tk.StringVar(value='settings.json')
        self.human_movement = tk.BooleanVar()
        self.set_button_state = tk.StringVar()
        self.set_button_state.set("normal")
        self.create_widgets()

    def create_widgets(self):
        settings_frame = tk.Frame(self)
        settings_frame.pack(pady=10)

        settings_label = tk.Label(settings_frame, text="Settings File:")
        settings_label.pack(side="left")

        settings_entry = tk.Entry(settings_frame, textvariable=self.settings_file, width=40)
        settings_entry.pack(side="left", padx=10)

        browse_button = tk.Button(settings_frame, text="Browse", command=self.browse_settings_file)
        browse_button.pack(side="left")

        human_movement_checkbox = tk.Checkbutton(self, text="Human Movement", variable=self.human_movement)
        human_movement_checkbox.pack()

        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=10)

        set_button = tk.Button(buttons_frame, text="Set Settings", command=self.set_settings, state=self.set_button_state.get())
        set_button.pack(side="left")

        get_button = tk.Button(buttons_frame, text="Get Settings", command=self.get_settings)
        get_button.pack(side="left")

    def browse_settings_file(self):
        initial_dir = os.getcwd()
        file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[('JSON Files', '*.json')])
        if file_path:
            self.settings_file.set(file_path)
            self.set_button_state.set("normal")
        else:
            self.set_button_state.set("disabled")

    def set_settings(self):
        load_settings_from_json(self.settings_file.get(), self.human_movement.get())
        

    def get_settings(self):
        save_settings_to_json(self.settings_file.get(), self.human_movement.get())
        

if __name__ == "__main__":
    app = SensitivitySettingsApp()
    app.mainloop()
