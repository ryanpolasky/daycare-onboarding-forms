import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import platform
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

# --- Env Variables ---
dotenv_path = find_dotenv(usecwd=True, raise_error_if_not_found=False)
if dotenv_path:
    print(f"Loading .env file from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("No .env file found. Using default directory settings.")

# --- Config ---
DAYCARE_NAME_FROM_ENV = os.getenv("DAYCARE_NAME", "Daycare")  # Default to "Daycare"
APP_NAME = f"{DAYCARE_NAME_FROM_ENV} Onboarding Forms"
FILLED_FORMS_SUBDIR = "Filled_Forms"  # Subdirectory within the active forms directory

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- Path Config ---
SCRIPT_ROOT_DIR = Path(__file__).resolve().parent

# Get paths from .env
env_parent_forms_dir_str = os.getenv("PARENT_FORMS_DIR")
env_staff_forms_dir_str = os.getenv("STAFF_FORMS_DIR")

# Determine paths
if env_parent_forms_dir_str and Path(env_parent_forms_dir_str).is_dir():
    ACTUAL_PARENT_FORMS_DIR = Path(env_parent_forms_dir_str)
    PARENT_DIR_SOURCE_MSG = f"Using PARENT_FORMS_DIR from .env: {ACTUAL_PARENT_FORMS_DIR}"
else:
    ACTUAL_PARENT_FORMS_DIR = SCRIPT_ROOT_DIR
    if env_parent_forms_dir_str:  # If a path was given but invalid
        PARENT_DIR_SOURCE_MSG = f"Warning: PARENT_FORMS_DIR '{env_parent_forms_dir_str}' from .env is invalid. Defaulting to script root: {SCRIPT_ROOT_DIR}"
    else:
        PARENT_DIR_SOURCE_MSG = f"PARENT_FORMS_DIR not in .env. Defaulting to script root: {SCRIPT_ROOT_DIR}"
print(PARENT_DIR_SOURCE_MSG)

if env_staff_forms_dir_str and Path(env_staff_forms_dir_str).is_dir():
    ACTUAL_STAFF_FORMS_DIR = Path(env_staff_forms_dir_str)
    STAFF_DIR_SOURCE_MSG = f"Using STAFF_FORMS_DIR from .env: {ACTUAL_STAFF_FORMS_DIR}"
else:
    ACTUAL_STAFF_FORMS_DIR = SCRIPT_ROOT_DIR
    if env_staff_forms_dir_str:  # If a path was given but invalid
        STAFF_DIR_SOURCE_MSG = f"Warning: STAFF_FORMS_DIR '{env_staff_forms_dir_str}' from .env is invalid. Defaulting to script root: {SCRIPT_ROOT_DIR}"
    else:
        STAFF_DIR_SOURCE_MSG = f"STAFF_FORMS_DIR not in .env. Defaulting to script root: {SCRIPT_ROOT_DIR}"
print(STAFF_DIR_SOURCE_MSG)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("700x650")  # Increased height for debug info

        # --- State ---
        self.user_type = None
        self.active_forms_directory = None
        self.opened_forms_paths = set()
        self.available_forms = []
        self.debug_mode_var = tk.BooleanVar(value=False)  # For the checkbox on the first screen

        # --- Main container ---
        self.main_app_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_app_frame.grid_columnconfigure(0, weight=1)
        self.main_app_frame.grid_rowconfigure(1, weight=1)  # Forms list

        self._setup_main_app_ui_elements()  # Set up frames but don't show them
        self._setup_user_type_selection_screen()

        # Configure the main window grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Show the user type selection screen first
        self.user_type_frame.grid(row=0, column=0, sticky="nsew")

    def _setup_user_type_selection_screen(self):
        self.user_type_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Centering content
        self.user_type_frame.grid_rowconfigure(0, weight=1)
        self.user_type_frame.grid_rowconfigure(1, weight=0)
        self.user_type_frame.grid_rowconfigure(2, weight=0)
        self.user_type_frame.grid_rowconfigure(3, weight=0)
        self.user_type_frame.grid_rowconfigure(4, weight=0)
        self.user_type_frame.grid_rowconfigure(5, weight=0)
        self.user_type_frame.grid_rowconfigure(6, weight=1)
        self.user_type_frame.grid_columnconfigure(0, weight=1)

        title_text = f"Welcome to {DAYCARE_NAME_FROM_ENV} Forms"
        title_label = ctk.CTkLabel(self.user_type_frame, text=title_text, font=ctk.CTkFont(size=28, weight="bold"))
        title_label.grid(row=1, column=0, padx=20, pady=(20, 10))

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

        # Debug checkbox on the initial screen
        self.debug_checkbox = ctk.CTkCheckBox(self.user_type_frame, text="Enable Debug Info on Next Screen",
                                              variable=self.debug_mode_var, onvalue=True, offvalue=False)
        self.debug_checkbox.grid(row=5, column=0, padx=20, pady=(20, 10))

    def _select_user_type(self, user_type_selected):
        self.user_type = user_type_selected

        if self.user_type == "Parent":
            self.active_forms_directory = ACTUAL_PARENT_FORMS_DIR
        elif self.user_type == "Staff":
            self.active_forms_directory = ACTUAL_STAFF_FORMS_DIR
        else:
            messagebox.showerror("Error", "Invalid user type selected.")
            return

        self.user_type_frame.grid_forget()  # Hide user type screen
        self.main_app_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)  # Show main app screen
        self.title(f"{APP_NAME} - {self.user_type}")
        self.header_title_label.configure(text=f"{APP_NAME} ({self.user_type} Forms)")
        self.forms_list_frame.configure(label_text=f"Available {self.user_type} Forms")

        self._update_debug_info_display()  # Setup debug panel based on checkbox state
        self.refresh_forms_list()

    def _setup_main_app_ui_elements(self):
        # Header
        self.header_frame = ctk.CTkFrame(self.main_app_frame, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_title_label = ctk.CTkLabel(self.header_frame, text=APP_NAME,
                                               font=ctk.CTkFont(size=20, weight="bold"))
        self.header_title_label.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="w")

        # Forms List
        self.forms_list_frame = ctk.CTkScrollableFrame(self.main_app_frame, label_text="Available Forms",
                                                       label_font=ctk.CTkFont(size=16, weight="bold"))
        self.forms_list_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        self.forms_list_frame.grid_columnconfigure(0, weight=1)

        # User Info
        self.info_frame = ctk.CTkFrame(self.main_app_frame)
        self.info_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.info_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.info_frame, text="Your Full Name:", font=ctk.CTkFont(size=12)).grid(row=0, column=0,
                                                                                              padx=(10, 5),
                                                                                              pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self.info_frame, placeholder_text="e.g., Jane Doe (Required to open forms)")
        self.name_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ew")

        # Debug Info Frame
        self.debug_info_display_frame = ctk.CTkFrame(self.main_app_frame, fg_color="transparent")
        self.debug_info_display_frame.grid_columnconfigure(0, weight=1)
        self.debug_info_label = ctk.CTkLabel(self.debug_info_display_frame, text="", font=ctk.CTkFont(size=10),
                                             justify="left", anchor="w")

        # Action Frame
        self.action_frame = ctk.CTkFrame(self.main_app_frame, corner_radius=0)
        self.action_frame.grid(row=4, column=0, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=0)
        self.action_frame.grid_columnconfigure(1, weight=0)
        self.action_frame.grid_columnconfigure(2, weight=1)
        self.action_frame.grid_columnconfigure(3, weight=0)

        self.appearance_mode_label = ctk.CTkLabel(self.action_frame, text="Theme:", anchor="w")
        self.appearance_mode_label.grid(row=0, column=0, padx=(20, 5), pady=10, sticky="w")
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.action_frame, values=["Light", "Dark", "System"],
                                                             command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=0, column=1, padx=0, pady=10, sticky="w")
        self.appearance_mode_optionemenu.set(ctk.get_appearance_mode())

        self.quit_button = ctk.CTkButton(self.action_frame, text="Quit", command=self.destroy, fg_color="transparent",
                                         border_width=2, text_color=("gray10", "#DCE4EE"))
        self.quit_button.grid(row=0, column=3, padx=(0, 20), pady=10, sticky="e")

    def _update_debug_info_display(self):
        if self.debug_mode_var.get():
            debug_text_lines = [
                f"--- Debug Information ---",
                f"Daycare Name (from .env or default): {DAYCARE_NAME_FROM_ENV}",
                f"Script Root Directory: {SCRIPT_ROOT_DIR}",
                f"Parent Forms Dir Source: {PARENT_DIR_SOURCE_MSG.split(': ', 1)[0]}",
                f"  -> Resolved Path: {ACTUAL_PARENT_FORMS_DIR}",
                f"Staff Forms Dir Source: {STAFF_DIR_SOURCE_MSG.split(': ', 1)[0]}",
                f"  -> Resolved Path: {ACTUAL_STAFF_FORMS_DIR}",
            ]
            if self.user_type and self.active_forms_directory:
                debug_text_lines.append(f"Active User Type: {self.user_type}")
                debug_text_lines.append(f"Currently Active Forms Directory: {self.active_forms_directory}")
            else:
                debug_text_lines.append("Active User Type: Not yet selected or error.")
                debug_text_lines.append("Active Forms Directory: Not yet set or error.")

            self.debug_info_label.configure(text="\n".join(debug_text_lines))

            # Ensure the frame is gridded and the label is packed
            self.debug_info_display_frame.grid(row=3, column=0, sticky="ew", pady=(5, 5), padx=0)
            if not self.debug_info_label.winfo_ismapped():  # Pack only if not already packed
                self.debug_info_label.pack(pady=5, padx=10, fill="x", anchor="w")
        else:
            # Hide the debug info
            self.debug_info_label.pack_forget()
            self.debug_info_display_frame.grid_forget()

    def refresh_forms_list(self):
        for widget in self.forms_list_frame.winfo_children():
            widget.destroy()
        self.available_forms = []

        if not self.active_forms_directory:
            if self.user_type:
                messagebox.showerror("Error", "Forms directory not set. Please check configuration.")
            return

        if not self.active_forms_directory.is_dir():
            messagebox.showwarning("Forms Directory Not Found",
                                   f"The forms directory for {self.user_type} was not found:\n'{self.active_forms_directory}'\n\n"
                                   "Please check your .env file or ensure the default directory contains forms.")
            ctk.CTkLabel(self.forms_list_frame, text=f"{self.user_type} forms directory not found.").pack(pady=10,
                                                                                                          padx=10)
            return

        try:
            found_any = False
            sorted_items = sorted(self.active_forms_directory.iterdir(), key=lambda p: p.name.lower())
            for item in sorted_items:
                if item.is_file() and item.suffix.lower() in ['.pdf', '.docx', '.doc']:
                    form_name = item.name
                    original_form_path = str(item)
                    self.available_forms.append((form_name, original_form_path))
                    display_text = form_name
                    if original_form_path in self.opened_forms_paths:
                        display_text += "  ✓"
                    form_button = ctk.CTkButton(
                        self.forms_list_frame, text=display_text,
                        command=lambda p=original_form_path, n=form_name: self.open_form_for_filling(p, n),
                        anchor="w"
                    )
                    form_button.pack(pady=(2, 3), padx=10, fill="x")
                    found_any = True
            if not found_any:
                ctk.CTkLabel(self.forms_list_frame,
                             text=f"No {self.user_type.lower()} forms found in '{self.active_forms_directory.name}'.").pack(
                    pady=10, padx=10)
        except Exception as e:
            messagebox.showerror("Error Reading Forms", f"An error occurred while reading forms: {e}")
            ctk.CTkLabel(self.forms_list_frame, text="Error loading forms.").pack(pady=10, padx=10)

    def open_form_for_filling(self, original_form_path_str, form_name):
        user_name = self.name_entry.get().strip()
        if not user_name:
            messagebox.showerror("Name Required", "Please enter your full name before opening a form.")
            self.name_entry.focus()
            return
        if not self.active_forms_directory or not self.active_forms_directory.is_dir():
            messagebox.showerror("Error", f"Active forms directory for {self.user_type} is not valid.")
            return

        filled_forms_path_dir = self.active_forms_directory / FILLED_FORMS_SUBDIR
        filled_forms_path_dir.mkdir(parents=True, exist_ok=True)
        base, ext = os.path.splitext(form_name)
        safe_user_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in user_name)
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        copied_form_name = f"{base}_{self.user_type}_{safe_user_name}_{timestamp_str}{ext}"
        copied_form_path = filled_forms_path_dir / copied_form_name
        try:
            shutil.copy2(original_form_path_str, copied_form_path)
            if platform.system() == 'Darwin':
                subprocess.call(('open', str(copied_form_path)))
            elif platform.system() == 'Windows':
                os.startfile(str(copied_form_path))
            else:
                subprocess.call(('xdg-open', str(copied_form_path)))
            self.opened_forms_paths.add(original_form_path_str)
            self.refresh_forms_list()
            messagebox.showinfo("Form Ready",
                                f"A copy of '{form_name}' has been opened for '{user_name}'.\n\n"
                                "Please fill it out and SAVE IT using the external application.")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Original form not found: {original_form_path_str}")
        except Exception as e:
            messagebox.showerror("Error Opening Form", f"Could not open form: {e}")

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    app = App()
    app.mainloop()
