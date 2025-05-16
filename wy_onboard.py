import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from os import environ as env
import platform
import subprocess
import shutil
from pathlib import Path
from datetime import datetime  # Ensure datetime is imported

# --- Configuration ---
APP_NAME = "Daycare Forms"
# IMPORTANT: SET THIS PATH TO YOUR ACTUAL FORMS DIRECTORY
# Example for Windows: FORMS_DIRECTORY_PATH = "C:/Users/YourUser/Documents/DaycareForms"
# Example for macOS/Linux: FORMS_DIRECTORY_PATH = "/Users/YourUser/Documents/DaycareForms"
FORMS_DIRECTORY_PATH = "REPLACE_WITH_YOUR_ACTUAL_FORMS_DIRECTORY_PATH"  # <<< SET THIS!!!

FILLED_FORMS_SUBDIR = "Filled_Forms"  # Subdirectory within the FORMS_DIRECTORY_PATH

# --- Theme and Appearance ---
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("700x550")

        # --- State Variables ---
        self.user_type = None  # Will be "Parent" or "Staff"
        self.opened_forms_paths = set()  # To track forms opened in this session
        self.available_forms = []  # List of (form_name, form_path) tuples

        # --- Main container for the form application part ---
        self.main_app_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_app_frame.grid_columnconfigure(0, weight=1)
        self.main_app_frame.grid_rowconfigure(1, weight=1)  # For the scrollable forms list

        # --- Setup UI elements (but don't show main_app_frame yet) ---
        self._setup_main_app_ui_elements()
        self._setup_user_type_selection_screen()

        # Configure the main window grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Show the user type selection screen first
        self.user_type_frame.grid(row=0, column=0, sticky="nsew")

    def _setup_user_type_selection_screen(self):
        self.user_type_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.user_type_frame.grid_rowconfigure(0, weight=1)  # Spacer
        self.user_type_frame.grid_rowconfigure(1, weight=0)  # Title
        self.user_type_frame.grid_rowconfigure(2, weight=0)  # Parent button
        self.user_type_frame.grid_rowconfigure(3, weight=0)  # Staff button
        self.user_type_frame.grid_rowconfigure(4, weight=1)  # Spacer
        self.user_type_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(self.user_type_frame, text="Welcome to Daycare Forms",
                                   font=ctk.CTkFont(size=28, weight="bold"))
        title_label.grid(row=1, column=0, padx=20, pady=(20, 30))

        subtitle_label = ctk.CTkLabel(self.user_type_frame, text="Please select user type:", font=ctk.CTkFont(size=18))
        subtitle_label.grid(row=2, column=0, padx=20, pady=(0, 20))

        button_width = 200
        button_height = 50
        font_button = ctk.CTkFont(size=16)

        parent_button = ctk.CTkButton(self.user_type_frame, text="Parent",
                                      command=lambda: self._select_user_type("Parent"),
                                      width=button_width, height=button_height, font=font_button)
        parent_button.grid(row=3, column=0, padx=20, pady=10)

        staff_button = ctk.CTkButton(self.user_type_frame, text="Staff",
                                     command=lambda: self._select_user_type("Staff"),
                                     width=button_width, height=button_height, font=font_button)
        staff_button.grid(row=4, column=0, padx=20, pady=10)

    def _select_user_type(self, user_type_selected):
        self.user_type = user_type_selected
        self.user_type_frame.grid_forget()  # Hide user type screen

        # Show the main application screen
        self.main_app_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.title(f"{APP_NAME} - {self.user_type}")  # Update window title
        self.header_title_label.configure(text=f"{APP_NAME} ({self.user_type})")  # Update header in main app

        if FORMS_DIRECTORY_PATH == "REPLACE_WITH_YOUR_ACTUAL_FORMS_DIRECTORY_PATH":
            messagebox.showerror("Configuration Error",
                                 "The forms directory path is not set in the script.\n"
                                 "Please edit the FORMS_DIRECTORY_PATH variable in the code.")
            self.quit_button.configure(text="Exit due to Config Error", command=self.destroy)
            return

        self.refresh_forms_list()

    def _setup_main_app_ui_elements(self):
        # --- Header (No longer has directory selection) ---
        self.header_frame = ctk.CTkFrame(self.main_app_frame, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))  # Removed padx for full width
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.header_title_label = ctk.CTkLabel(self.header_frame, text=APP_NAME,
                                               font=ctk.CTkFont(size=20, weight="bold"))
        self.header_title_label.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="w")

        # --- Forms List Area ---
        self.forms_list_frame = ctk.CTkScrollableFrame(self.main_app_frame, label_text="Available Forms",
                                                       label_font=ctk.CTkFont(size=16, weight="bold"))
        self.forms_list_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        self.forms_list_frame.grid_columnconfigure(0, weight=1)

        # --- User Info Input (Name) ---
        self.info_frame = ctk.CTkFrame(self.main_app_frame)
        self.info_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.info_frame, text="Your Name:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(10, 5),
                                                                                         pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self.info_frame, placeholder_text="e.g., Jane Doe (Required to open forms)")
        self.name_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ew")

        # --- Action Buttons (Footer) ---
        self.action_frame = ctk.CTkFrame(self.main_app_frame, corner_radius=0)
        self.action_frame.grid(row=3, column=0, sticky="ew")
        self.action_frame.grid_columnconfigure(1, weight=1)  # Allow theme options to be on left, quit on right

        self.appearance_mode_label = ctk.CTkLabel(self.action_frame, text="Theme:", anchor="w")
        self.appearance_mode_label.grid(row=0, column=0, padx=(20, 5), pady=10, sticky="w")
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.action_frame, values=["Light", "Dark", "System"],
                                                             command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=0, column=1, padx=0, pady=10, sticky="w")
        self.appearance_mode_optionemenu.set(ctk.get_appearance_mode())

        self.quit_button = ctk.CTkButton(self.action_frame, text="Quit", command=self.destroy, fg_color="transparent",
                                         border_width=2, text_color=("gray10", "#DCE4EE"))
        self.quit_button.grid(row=0, column=2, padx=(20, 20), pady=10, sticky="e")

    def refresh_forms_list(self):
        for widget in self.forms_list_frame.winfo_children():
            widget.destroy()

        self.available_forms = []
        current_dir = FORMS_DIRECTORY_PATH  # Use the hardcoded path

        if not os.path.isdir(current_dir):
            messagebox.showwarning("Forms Directory Not Found",
                                   f"The configured forms directory was not found:\n{current_dir}\n\n"
                                   "Please check the FORMS_DIRECTORY_PATH variable in the script.")
            ctk.CTkLabel(self.forms_list_frame,
                         text="Forms directory not found. Please check script configuration.").pack(pady=10, padx=10)
            return

        try:
            found_any = False
            sorted_items = sorted(Path(current_dir).iterdir(), key=lambda p: p.name.lower())

            for item in sorted_items:
                if item.is_file() and item.suffix.lower() in ['.pdf', '.docx', '.doc']:
                    form_name = item.name
                    original_form_path = str(item)
                    self.available_forms.append((form_name, original_form_path))

                    display_text = form_name
                    if original_form_path in self.opened_forms_paths:
                        display_text += "  ✓"  # Add checkmark if opened

                    form_button = ctk.CTkButton(
                        self.forms_list_frame,
                        text=display_text,
                        command=lambda p=original_form_path, n=form_name: self.open_form_for_filling(p, n),
                        anchor="w"
                    )
                    form_button.pack(pady=(2, 3), padx=10, fill="x")
                    found_any = True

            if not found_any:
                ctk.CTkLabel(self.forms_list_frame, text="No forms found in the directory.").pack(pady=10, padx=10)

        except Exception as e:
            messagebox.showerror("Error Reading Forms", f"An error occurred while reading forms: {e}")
            ctk.CTkLabel(self.forms_list_frame, text="Error loading forms.").pack(pady=10, padx=10)

    def open_form_for_filling(self, original_form_path, form_name):
        user_name = self.name_entry.get().strip()
        if not user_name:
            messagebox.showerror("Name Required", "Please enter Your Name before opening a form.")
            self.name_entry.focus()
            return

        # Ensure the base forms directory exists before creating subdirectories or files
        base_forms_dir = Path(FORMS_DIRECTORY_PATH)
        if not base_forms_dir.is_dir():
            messagebox.showerror("Error", f"Base forms directory not found: {base_forms_dir}")
            return

        filled_forms_path = base_forms_dir / FILLED_FORMS_SUBDIR
        filled_forms_path.mkdir(parents=True, exist_ok=True)

        base, ext = os.path.splitext(form_name)
        safe_user_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in user_name)
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

        copied_form_name = f"{base}_{safe_user_name}_{timestamp_str}{ext}"
        copied_form_path = filled_forms_path / copied_form_name

        try:
            shutil.copy2(original_form_path, copied_form_path)

            if platform.system() == 'Darwin':
                subprocess.call(('open', str(copied_form_path)))
            elif platform.system() == 'Windows':
                os.startfile(str(copied_form_path))
            else:
                subprocess.call(('xdg-open', str(copied_form_path)))

            # Add to opened set and refresh list to show checkmark
            self.opened_forms_paths.add(original_form_path)
            self.refresh_forms_list()

            # Modified message
            messagebox.showinfo("Form Ready",
                                f"A copy of '{form_name}' has been opened for '{user_name}'.\n\n"
                                "Please fill it out and SAVE IT using the external application.")

        except FileNotFoundError:
            messagebox.showerror("Error", f"Original form not found: {original_form_path}")
        except Exception as e:
            messagebox.showerror("Error Opening Form", f"Could not open form: {e}")

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    # Critical check for the placeholder path
    if FORMS_DIRECTORY_PATH == "REPLACE_WITH_YOUR_ACTUAL_FORMS_DIRECTORY_PATH":
        # Create a temporary root to show the error if the main app can't initialize properly
        root = ctk.CTk()
        root.withdraw()  # Hide the empty root window
        messagebox.showerror("Configuration Needed",
                             "CRITICAL: The FORMS_DIRECTORY_PATH is not set in the script.\n"
                             "Please edit this variable at the top of the Python file before running.")
        root.destroy()
    else:
        app = App()
        app.mainloop()