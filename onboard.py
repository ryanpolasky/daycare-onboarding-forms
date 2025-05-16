import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import platform
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

# --- Env Variables ---
dotenv_path = find_dotenv(usecwd=True, raise_error_if_not_found=False)
if dotenv_path:
    print(f"Loading .env file from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("No .env file found. Using default directory settings.")

# --- Config ---
DAYCARE_NAME_FROM_ENV = os.getenv("DAYCARE_NAME", "Daycare")
APP_NAME = f"{DAYCARE_NAME_FROM_ENV} Onboarding Forms"
FILLED_FORMS_SUBDIR = "Filled_Forms"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- Path Config ---
SCRIPT_ROOT_DIR = Path(__file__).resolve().parent

env_parent_forms_dir_str = os.getenv("PARENT_FORMS_DIR")
env_staff_forms_dir_str = os.getenv("STAFF_FORMS_DIR")

if env_parent_forms_dir_str and Path(env_parent_forms_dir_str).is_dir():
    ACTUAL_PARENT_FORMS_DIR = Path(env_parent_forms_dir_str)
    PARENT_DIR_SOURCE_MSG = f"Using PARENT_FORMS_DIR from .env: {ACTUAL_PARENT_FORMS_DIR}"
else:
    ACTUAL_PARENT_FORMS_DIR = SCRIPT_ROOT_DIR
    if env_parent_forms_dir_str:
        PARENT_DIR_SOURCE_MSG = f"Warning: PARENT_FORMS_DIR '{env_parent_forms_dir_str}' from .env is invalid. Defaulting to script root: {SCRIPT_ROOT_DIR}"
    else:
        PARENT_DIR_SOURCE_MSG = f"PARENT_FORMS_DIR not in .env. Defaulting to script root: {SCRIPT_ROOT_DIR}"
print(PARENT_DIR_SOURCE_MSG)

if env_staff_forms_dir_str and Path(env_staff_forms_dir_str).is_dir():
    ACTUAL_STAFF_FORMS_DIR = Path(env_staff_forms_dir_str)
    STAFF_DIR_SOURCE_MSG = f"Using STAFF_FORMS_DIR from .env: {ACTUAL_STAFF_FORMS_DIR}"
else:
    ACTUAL_STAFF_FORMS_DIR = SCRIPT_ROOT_DIR
    if env_staff_forms_dir_str:
        STAFF_DIR_SOURCE_MSG = f"Warning: STAFF_FORMS_DIR '{env_staff_forms_dir_str}' from .env is invalid. Defaulting to script root: {SCRIPT_ROOT_DIR}"
    else:
        STAFF_DIR_SOURCE_MSG = f"STAFF_FORMS_DIR not in .env. Defaulting to script root: {SCRIPT_ROOT_DIR}"
print(STAFF_DIR_SOURCE_MSG)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("700x700")

        self.user_type = None
        self.active_forms_directory = None
        self.available_forms = []
        self.debug_mode_var = tk.BooleanVar(value=False)

        self.current_session_user_name = None
        self.opened_original_forms_for_user = set()
        self.user_specific_copied_forms = {}
        self.all_forms_popup_shown_for_current_user_set = False

        self.user_type_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._setup_user_type_selection_screen()

        self.name_entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._setup_name_entry_screen()

        self.main_app_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_app_frame.grid_columnconfigure(0, weight=1)
        self.main_app_frame.grid_rowconfigure(1, weight=1)
        self._setup_main_app_ui_elements()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.user_type_frame.grid(row=0, column=0, sticky="nsew")

    def _setup_user_type_selection_screen(self):
        self.user_type_frame.grid_rowconfigure((0, 6), weight=1)
        self.user_type_frame.grid_rowconfigure((1, 2, 3, 4, 5), weight=0)
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

        self.debug_checkbox = ctk.CTkCheckBox(self.user_type_frame, text="Enable Debug Info",
                                              variable=self.debug_mode_var, onvalue=True, offvalue=False)
        self.debug_checkbox.grid(row=5, column=0, padx=20, pady=(20, 10))

    def _setup_name_entry_screen(self):
        self.name_entry_frame.grid_rowconfigure((0, 5), weight=1)
        self.name_entry_frame.grid_rowconfigure((1, 2, 3, 4), weight=0)
        self.name_entry_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(self.name_entry_frame, text="Enter Your Name",
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=1, column=0, padx=20, pady=(20, 10))

        name_entry_frame_inner = ctk.CTkFrame(self.name_entry_frame, fg_color="transparent")
        name_entry_frame_inner.grid(row=2, column=0, padx=20, pady=10)
        name_entry_frame_inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(name_entry_frame_inner, text="First Name:", font=ctk.CTkFont(size=16)).grid(
            row=0, column=0, padx=(0, 10), pady=(10, 5), sticky="e")
        self.name_entry_first_name_entry = ctk.CTkEntry(name_entry_frame_inner, placeholder_text="e.g., Jane",
                                                        width=300, font=ctk.CTkFont(size=14))
        self.name_entry_first_name_entry.grid(row=0, column=1, pady=(10, 5), sticky="w")

        ctk.CTkLabel(name_entry_frame_inner, text="Last Name:", font=ctk.CTkFont(size=16)).grid(
            row=1, column=0, padx=(0, 10), pady=(5, 10), sticky="e")
        self.name_entry_last_name_entry = ctk.CTkEntry(name_entry_frame_inner, placeholder_text="e.g., Doe",
                                                       width=300, font=ctk.CTkFont(size=14))
        self.name_entry_last_name_entry.grid(row=1, column=1, pady=(5, 10), sticky="w")

        button_font = ctk.CTkFont(size=16)
        continue_button = ctk.CTkButton(self.name_entry_frame, text="Continue",
                                        command=self._submit_name_and_show_forms,
                                        width=150, height=40, font=button_font)
        continue_button.grid(row=4, column=0, padx=20, pady=10)

    def _reset_user_session_state(self):
        self.current_session_user_name = None
        self.opened_original_forms_for_user.clear()
        self.user_specific_copied_forms.clear()
        self.all_forms_popup_shown_for_current_user_set = False
        if hasattr(self, 'name_entry_first_name_entry'):
            self.name_entry_first_name_entry.delete(0, tk.END)
        if hasattr(self, 'name_entry_last_name_entry'):
            self.name_entry_last_name_entry.delete(0, tk.END)
        if hasattr(self, 'display_full_name_label'):
            self.display_full_name_label.configure(text="")

    def _select_user_type(self, user_type_selected):
        self.user_type = user_type_selected
        if self.user_type == "Parent":
            self.active_forms_directory = ACTUAL_PARENT_FORMS_DIR
        elif self.user_type == "Staff":
            self.active_forms_directory = ACTUAL_STAFF_FORMS_DIR
        else:
            messagebox.showerror("Error", "Invalid user type selected.")
            return

        self._reset_user_session_state()

        self.user_type_frame.grid_forget()
        self.name_entry_frame.grid(row=0, column=0, sticky="nsew")
        self.title(f"{APP_NAME} - Enter Name ({self.user_type})")
        self.name_entry_first_name_entry.focus()

    def _go_back_to_user_type_selection(self):
        self.name_entry_frame.grid_forget()
        self.user_type_frame.grid(row=0, column=0, sticky="nsew")
        self.title(APP_NAME)
        self._reset_user_session_state()

    def _submit_name_and_show_forms(self):
        first_name = self.name_entry_first_name_entry.get().strip()
        last_name = self.name_entry_last_name_entry.get().strip()

        if not first_name:
            messagebox.showerror("First Name Required", "Please enter First Name.", parent=self.name_entry_frame)
            self.name_entry_first_name_entry.focus()
            return
        if not last_name:
            messagebox.showerror("Last Name Required", "Please enter Last Name.", parent=self.name_entry_frame)
            self.name_entry_last_name_entry.focus()
            return

        self.current_session_user_name = f"{first_name} {last_name}"
        self.display_full_name_label.configure(text=self.current_session_user_name)

        self.name_entry_frame.grid_forget()
        self.main_app_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.title(f"{APP_NAME} - {self.user_type} ({self.current_session_user_name})")
        self.header_title_label.configure(text=f"{APP_NAME} ({self.user_type} Forms)")
        self.forms_list_frame.configure(
            label_text=f"Available {self.user_type} Forms for {self.current_session_user_name}")

        self._update_debug_info_display()
        self.refresh_forms_list()

    def _setup_main_app_ui_elements(self):
        self.header_frame = ctk.CTkFrame(self.main_app_frame, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_title_label = ctk.CTkLabel(self.header_frame, text=APP_NAME,
                                               font=ctk.CTkFont(size=20, weight="bold"))
        self.header_title_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")

        self.name_display_frame = ctk.CTkFrame(self.header_frame)
        self.name_display_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.name_display_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.name_display_frame, text="Name:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0,
                                                                                                           column=0,
                                                                                                           padx=(0, 5),
                                                                                                           pady=(5, 5),
                                                                                                           sticky="w")
        self.display_full_name_label = ctk.CTkLabel(self.name_display_frame, text="", font=ctk.CTkFont(size=12))
        self.display_full_name_label.grid(row=0, column=1, padx=(0, 5), pady=(5, 5), sticky="w")

        self.forms_list_frame = ctk.CTkScrollableFrame(self.main_app_frame, label_text="Available Forms",
                                                       label_font=ctk.CTkFont(size=16, weight="bold"))
        self.forms_list_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.forms_list_frame.grid_columnconfigure(0, weight=1)

        self.debug_info_display_frame = ctk.CTkFrame(self.main_app_frame, fg_color="transparent")
        self.debug_info_display_frame.grid_columnconfigure(0, weight=1)
        self.debug_info_label = ctk.CTkLabel(self.debug_info_display_frame, text="", font=ctk.CTkFont(size=10),
                                             justify="left", anchor="w")

        self.action_frame = ctk.CTkFrame(self.main_app_frame, corner_radius=0)
        self.action_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.action_frame.grid_columnconfigure(2, weight=1)

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
                f"Daycare Name: {DAYCARE_NAME_FROM_ENV}",
                f"Script Root: {SCRIPT_ROOT_DIR}",
                f"Parent Forms Path: {ACTUAL_PARENT_FORMS_DIR} ({PARENT_DIR_SOURCE_MSG.split(': ', 1)[0]})",
                f"Staff Forms Path: {ACTUAL_STAFF_FORMS_DIR} ({STAFF_DIR_SOURCE_MSG.split(': ', 1)[0]})",
            ]
            if self.user_type and self.active_forms_directory:
                debug_text_lines.extend([
                    f"Active User Type: {self.user_type}",
                    f"Active Forms Directory: {self.active_forms_directory}",
                    f"Current Session User Name: {self.current_session_user_name}",
                    f"Opened Original Forms Count: {len(self.opened_original_forms_for_user)}",
                    f"All Forms Popup Shown: {self.all_forms_popup_shown_for_current_user_set}"
                ])
            else:
                debug_text_lines.append("User Type/Active Directory: Not yet set.")

            self.debug_info_label.configure(text="\n".join(debug_text_lines))
            self.debug_info_display_frame.grid(row=2, column=0, sticky="ew", pady=(5, 5), padx=0)
            if not self.debug_info_label.winfo_ismapped():
                self.debug_info_label.pack(pady=5, padx=10, fill="x", anchor="w")
        else:
            self.debug_info_label.pack_forget()
            self.debug_info_display_frame.grid_forget()

    def refresh_forms_list(self):
        for widget in self.forms_list_frame.winfo_children():
            widget.destroy()
        self.available_forms = []

        if not self.active_forms_directory:
            if self.user_type:
                messagebox.showerror("Error", "Forms directory not set.")
            return

        if not self.active_forms_directory.is_dir():
            messagebox.showwarning("Forms Directory Not Found",
                                   f"Directory for {self.user_type} not found:\n'{self.active_forms_directory}'")
            ctk.CTkLabel(self.forms_list_frame, text=f"{self.user_type} forms directory not found.").pack(pady=10,
                                                                                                          padx=10)
            return

        try:
            found_any = False
            sorted_items = sorted(self.active_forms_directory.iterdir(), key=lambda p: p.name.lower())
            for item in sorted_items:
                if item.is_file() and item.suffix.lower() in ['.pdf', '.docx', '.doc']:
                    form_name = item.name
                    original_form_path_str = str(item)
                    self.available_forms.append((form_name, original_form_path_str))

                    display_text = form_name
                    if original_form_path_str in self.opened_original_forms_for_user:
                        display_text += "  ✓"

                    form_button = ctk.CTkButton(
                        self.forms_list_frame, text=display_text,
                        command=lambda p=original_form_path_str, n=form_name: self.open_form_for_filling(p, n),
                        anchor="w"
                    )
                    form_button.pack(pady=(2, 3), padx=10, fill="x")
                    found_any = True
            if not found_any:
                ctk.CTkLabel(self.forms_list_frame,
                             text=f"No {self.user_type.lower()} forms found in '{self.active_forms_directory.name}'.").pack(
                    pady=10, padx=10)
        except Exception as e:
            messagebox.showerror("Error Reading Forms", f"Error reading forms: {e}")
            ctk.CTkLabel(self.forms_list_frame, text="Error loading forms.").pack(pady=10, padx=10)
        self._update_debug_info_display()

    def _check_and_show_all_forms_opened_popup(self):
        if self.all_forms_popup_shown_for_current_user_set:
            return
        if self.available_forms and len(self.opened_original_forms_for_user) == len(self.available_forms):
            messagebox.showinfo("All Forms Processed",
                                f"All forms have been opened for {self.current_session_user_name}.\n\n"
                                "Once done with all forms, please return laptop to office staff.")
            self.all_forms_popup_shown_for_current_user_set = True
            self._update_debug_info_display()

    def open_form_for_filling(self, original_form_path_str, form_name):
        if not self.current_session_user_name:
            messagebox.showerror("Error", "User name not set. Please restart the selection process.")
            self._go_back_to_user_type_selection()
            return

        if not self.active_forms_directory or not self.active_forms_directory.is_dir():
            messagebox.showerror("Error", f"Active forms directory for {self.user_type} is not valid.")
            return

        filled_forms_path_dir = self.active_forms_directory / FILLED_FORMS_SUBDIR
        filled_forms_path_dir.mkdir(parents=True, exist_ok=True)
        base, ext = os.path.splitext(form_name)
        safe_user_name = "".join(
            c if c.isalnum() or c in " _-" else "_" for c in self.current_session_user_name)

        # Use datetime from the datetime module, not ctk
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        copied_form_name = f"{base}_{self.user_type}_{safe_user_name}_{timestamp_str}{ext}"
        target_copied_form_path = filled_forms_path_dir / copied_form_name

        path_to_open = None
        opened_existing = False

        if original_form_path_str in self.user_specific_copied_forms:
            existing_copied_path = self.user_specific_copied_forms[original_form_path_str]
            if existing_copied_path == target_copied_form_path and existing_copied_path.exists():
                path_to_open = existing_copied_path
                opened_existing = True
                print(f"Reopening existing file for '{self.current_session_user_name}': {path_to_open}")
            else:
                print(
                    f"Recorded path {existing_copied_path} for '{original_form_path_str}' "
                    f"is invalid or non-existent for user '{self.current_session_user_name}'. "
                    f"Will attempt to create a new copy."
                )
                del self.user_specific_copied_forms[original_form_path_str]

        if not path_to_open:
            try:
                shutil.copy2(original_form_path_str, target_copied_form_path)
                self.user_specific_copied_forms[original_form_path_str] = target_copied_form_path
                path_to_open = target_copied_form_path
                print(f"Copied new file to: {path_to_open} for user '{self.current_session_user_name}'")
            except FileNotFoundError:
                messagebox.showerror("Error", f"Original form not found: {original_form_path_str}")
                self._update_debug_info_display()
                return
            except Exception as e:
                messagebox.showerror("Error Copying Form", f"Could not copy form: {e}")
                self._update_debug_info_display()
                return

        try:
            if platform.system() == 'Darwin':
                subprocess.call(('open', str(path_to_open)))
            elif platform.system() == 'Windows':
                os.startfile(str(path_to_open))
            else:
                subprocess.call(('xdg-open', str(path_to_open)))

            self.opened_original_forms_for_user.add(original_form_path_str)
            if not opened_existing:
                self.refresh_forms_list()

            if opened_existing:
                messagebox.showinfo("Form Reopened",
                                    f"Existing copy of '{form_name}' for '{self.current_session_user_name}' reopened.\n\n"
                                    "Please continue filling it out and SAVE IT.")
            else:
                messagebox.showinfo("Form Ready",
                                    f"New copy of '{form_name}' created and opened for '{self.current_session_user_name}'.\n\n"
                                    "Please fill it out and SAVE IT.")

            self._check_and_show_all_forms_opened_popup()

        except Exception as e:
            messagebox.showerror("Error Opening Form", f"Could not open file '{path_to_open.name}': {e}")

        self._update_debug_info_display()

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    app = App()
    app.mainloop()
