import tkinter as tk
from tkinter import filedialog
import os
from main import load_settings_from_json, save_settings_to_json
from pynput import keyboard
from multiprocessing import Process
import threading

NOT_RUNNING_MSG = 'Not running. Click a button to start.'
RUNNING_MSG = 'Running. Press Shift to stop.'
APP_EXPLANATION ='''This app allows you to duplicate your sensitivity settings for each hero across accounts. 
To stop the script running at any time, press the shift key.\n
Retrieve the settings from one account by running 'Get settings'.
This will save your settings to the designated json file.
Log into another account and run 'Set settings' to duplicate the saved settings.'''

class SensitivitySettingsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sensitivity Settings App")
        self.settings_file = tk.StringVar(value='settings.json')
        self.human_movement = tk.BooleanVar()
        self.set_button_state = tk.StringVar()
        self.running_state = tk.StringVar(value=NOT_RUNNING_MSG)
        self.set_button_state.set("normal")
        self.get_thread = None
        self.set_thread = None
        self.listen_thread = None
        self.terminate_flag = False

        self.create_widgets()
        self.listen_for_break()

    def create_widgets(self):
        # Frame for settings-related widgets
        settings_frame = tk.Frame(self)
        settings_frame.pack(pady=(10, 5), padx=30)
        
        app_label = tk.Label(settings_frame, text="Overwatch Settings Duplicator", font=("Arial", 16, "bold"))
        app_label.pack(side="top")
        # Instructions label
        explanation_text = tk.Text(settings_frame, wrap="word", height=8, width=55, font=("Arial", 10))
        explanation_text.pack(pady=10)
        explanation_text.insert(tk.END, APP_EXPLANATION)
        explanation_text.config(state=tk.DISABLED)
        
        settings_label = tk.Label(settings_frame, text="Settings File:")
        settings_label.pack(side="left")

        settings_entry = tk.Entry(settings_frame, textvariable=self.settings_file, width=40)
        settings_entry.pack(side="left", padx=10)

        browse_button = tk.Button(settings_frame, text="Browse", command=self.browse_settings_file)
        browse_button.pack(side="left")

        # Checkbox for enabling human movement
        # human_movement_checkbox = tk.Checkbutton(self, text="Human Movement", variable=self.human_movement)
        # human_movement_checkbox.pack()
        running_label = tk.Label(self, textvariable=self.running_state)
        running_label.pack(pady=(0, 5))
        # Frame for action buttons
        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=(0, 15))

        set_button = tk.Button(buttons_frame, text="Set Settings", command=self.set_settings, state=self.set_button_state.get())
        set_button.pack(side="left", padx=10)

        get_button = tk.Button(buttons_frame, text="Get Settings", command=self.get_settings)
        get_button.pack(side="left", padx=10, )
        
        
    def browse_settings_file(self):
        initial_dir = os.getcwd()
        file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[('JSON Files', '*.json')])
        if file_path:
            self.settings_file.set(file_path)
            self.set_button_state.set("normal")
        else:
            self.set_button_state.set("disabled")

    def listen_for_break(self):
        def on_press(key):
            if key == keyboard.Key.shift:
                self.kill_script()

        listener = keyboard.Listener(on_press=on_press, on_release=None)
        listener.start()

    def set_settings(self):
        self.start_timer()
        self.running_state.set(RUNNING_MSG)
        self.set_thread = Process(target=load_settings_from_json, args=(self.settings_file.get(), self.human_movement.get(),))
        self.set_thread.start()
        threading.Thread(target=self.wait_for_process, args=(self.set_thread,)).start()

    def get_settings(self):
        self.start_timer()
        self.running_state.set(RUNNING_MSG)
        self.get_thread = Process(target=save_settings_to_json, args=(self.settings_file.get(), self.human_movement.get(),))
        self.get_thread.start()
        threading.Thread(target=self.wait_for_process, args=(self.get_thread,)).start()

    def wait_for_process(self, process):
        process.join()  # Wait for the process to finish
        self.running_state.set(NOT_RUNNING_MSG)
        
    def start_timer(self):
        countdown_window = tk.Toplevel(self)
        countdown_label = tk.Label(countdown_window, font=("Helvetica", 48))
        countdown_label.pack(padx=20, pady=10)
        countdown_window.attributes("-topmost", True)  # Ensure the countdown window is always on top

        for i in range(3, 0, -1):
            countdown_label.configure(text=str(i))
            countdown_window.update()  # Update the countdown window to show the current countdown number
            countdown_window.after(1000)  # Delay for 1 second
            if self.terminate_flag:
                break

        countdown_window.destroy()  # Close the countdown window

    def kill_script(self):
        if self.get_thread:
            self.get_thread.terminate()
        if self.set_thread:
            self.set_thread.terminate()
            
        self.running_state.set(NOT_RUNNING_MSG)
        


if __name__ == "__main__":
    app = SensitivitySettingsApp()
    app.mainloop()
