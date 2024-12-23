import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import time
import sys
import ctypes

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere boyutu ve yeniden boyutlandırılabilirlik
        self.title("Uygulama Açıcı")
        self.geometry("500x500")  # Ekran boyutunu 500x500 olarak ayarla
        self.resizable(False, False)  # Varsayılan olarak yeniden boyutlandırmayı kapat

        self.folder_path = ctk.StringVar()
        self.file_checkboxes = {}
        self.settings_file = self.setup_settings_file()
        self.settings = self.load_settings()

        # Uygulama ayarlarını yükle
        self.cooldown_enabled = self.settings.get("cooldown_enabled", True)
        self.autostart_enabled = self.settings.get("autostart_enabled", False)
        self.resizing_enabled = self.settings.get("resizing_enabled", False)
        self.uac_bypass_enabled = self.settings.get("uac_bypass_enabled", False)
        self.supported_extensions = self.settings.get("supported_extensions", [".exe", ".bat", ".sh", ".py"])

        # Varsayılan yeniden boyutlandırılabilirlik durumunu uygula
        self.apply_resizing_setting()

        # Başlık
        self.title_label = ctk.CTkLabel(self, text="Klasör Seç ve Uygulamaları Kontrol Et", font=("Arial", 16))
        self.title_label.pack(pady=10)

        # Klasör seçme kısmı
        self.folder_entry = ctk.CTkEntry(self, textvariable=self.folder_path, width=400, placeholder_text="Klasör seçin")
        self.folder_entry.pack(pady=5)

        self.browse_button = ctk.CTkButton(self, text="Gözat", command=self.browse_folder)
        self.browse_button.pack(pady=5)

        # Dosyaların listeleneceği çerçeve
        self.files_frame = ctk.CTkScrollableFrame(self, width=800, height=300)
        self.files_frame.pack(pady=10, fill="both", expand=True)

        # "Başlat" butonu
        self.start_button = ctk.CTkButton(self, text="Başlat", command=self.open_selected_files)
        self.start_button.pack(pady=(5, 10))  # Daha dar bir boşluk bırakıldı

        # Desteklenmeyen dosya mesajı
        self.unsupported_label = ctk.CTkLabel(self, text="", text_color="orange", font=("Arial", 12))
        self.unsupported_label.pack(pady=5)

        # Dosya bilgileri (sayı ve boyut)
        self.file_info_label = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.file_info_label.pack(pady=5)

        # Başarı ve hata mesajları
        self.success_label = ctk.CTkLabel(self, text="", text_color="green", font=("Arial", 12))
        self.success_label.pack(pady=5)
        self.error_label = ctk.CTkLabel(self, text="", text_color="red", font=("Arial", 12))
        self.error_label.pack(pady=5)

        # Klavye dinleme
        self.bind("<Control-n>", self.open_settings)

        # UAC kontrolü
        if self.uac_bypass_enabled:
            self.run_as_admin()

    def setup_settings_file(self):
        documents_folder = os.path.expanduser("~/Documents")
        napes_folder = os.path.join(documents_folder, "Napes Studios")
        autofo_folder = os.path.join(napes_folder, "AutoFO")

        os.makedirs(autofo_folder, exist_ok=True)

        settings_file = os.path.join(autofo_folder, "settings.json")
        if not os.path.exists(settings_file):
            # Varsayılan ayarlarla bir settings.json oluştur
            default_settings = {
                "cooldown_enabled": True,
                "autostart_enabled": False,
                "resizing_enabled": False,
                "uac_bypass_enabled": False,
                "supported_extensions": [".exe", ".bat", ".sh", ".py"]
            }
            with open(settings_file, "w") as file:
                json.dump(default_settings, file, indent=4)

        return settings_file

    def load_settings(self):
        with open(self.settings_file, "r") as file:
            return json.load(file)

    def save_settings(self):
        self.settings["cooldown_enabled"] = self.cooldown_enabled
        self.settings["autostart_enabled"] = self.autostart_enabled
        self.settings["resizing_enabled"] = self.resizing_enabled
        self.settings["uac_bypass_enabled"] = self.uac_bypass_enabled
        self.settings["supported_extensions"] = self.supported_extensions

        with open(self.settings_file, "w") as file:
            json.dump(self.settings, file, indent=4)

    def apply_resizing_setting(self):
        """Yeniden boyutlandırılabilirliği ayarlama."""
        self.resizable(self.resizing_enabled, self.resizing_enabled)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.list_files(folder_selected)

            if self.autostart_enabled:
                self.open_selected_files()

    def list_files(self, folder):
        # Önceki dosya listelerini temizle
        for widget in self.files_frame.winfo_children():
            widget.destroy()

        self.file_checkboxes = {}
        self.unsupported_label.configure(text="")
        self.success_label.configure(text="")
        self.error_label.configure(text="")
        self.file_info_label.configure(text="")

        unsupported_files = []
        total_size = 0
        file_count = 0

        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            if os.path.isfile(item_path):
                if any(item.endswith(ext) for ext in self.supported_extensions):
                    file_count += 1
                    total_size += os.path.getsize(item_path)
                    var = ctk.BooleanVar(value=True)
                    checkbox = ctk.CTkCheckBox(self.files_frame, text=item, variable=var)
                    checkbox.pack(anchor="w", padx=10, pady=5)
                    self.file_checkboxes[item_path] = var
                else:
                    unsupported_files.append(item)

        # Dosya bilgilerini göster
        size_text = self.format_size(total_size)
        self.file_info_label.configure(
            text=f"Dosya Sayısı: {file_count}, Toplam Boyut: {size_text}"
        )

        # Desteklenmeyen dosya mesajı
        if unsupported_files:
            unsupported_text = f"A file is not displayed: {', '.join(unsupported_files)}"
            self.unsupported_label.configure(text=unsupported_text)

    @staticmethod
    def format_size(size_in_bytes):
        """Dosya boyutunu uygun birimle formatla (KB, MB, GB)."""
        if size_in_bytes < 1024:
            return f"{size_in_bytes} B"
        elif size_in_bytes < 1024 ** 2:
            return f"{size_in_bytes / 1024:.2f} KB"
        elif size_in_bytes < 1024 ** 3:
            return f"{size_in_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_in_bytes / (1024 ** 3):.2f} GB"

    def open_selected_files(self):
        selected_files = [path for path, var in self.file_checkboxes.items() if var.get()]

        if not selected_files:
            messagebox.showwarning("Uyarı", "Hiçbir dosya seçilmedi!")
            return

        self.success_label.configure(text="")
        self.error_label.configure(text="")

        opened_files = []
        failed_files = []

        for file in selected_files:
            try:
                subprocess.Popen(file, shell=True)
                opened_files.append(file)
                self.success_label.configure(
                    text=f"A file was opened successfully: {', '.join(os.path.basename(f) for f in opened_files)}\n"
                         f"Total files opened successfully: {len(opened_files)}"
                )
                self.update_idletasks()

                if self.cooldown_enabled:
                    time.sleep(0.2)
            except Exception:
                failed_files.append(file)

        if failed_files:
            failed_text = f"One or more files could not be opened: {', '.join(os.path.basename(f) for f in failed_files)}"
            self.error_label.configure(text=failed_text)

    def open_settings(self, event=None):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Ayarlar")
        settings_window.geometry("400x400")

        # Cooldown ayarı
        cooldown_switch = ctk.CTkSwitch(
            settings_window,
            text="File opening cooldown",
            command=self.toggle_cooldown,
            onvalue=True,
            offvalue=False
        )
        cooldown_switch.pack(pady=10)
        if self.cooldown_enabled:
            cooldown_switch.select()
        else:
            cooldown_switch.deselect()

        # Autostart ayarı
        autostart_switch = ctk.CTkSwitch(
            settings_window,
            text="Autostart files in the selected folder (NOT RECOMMENDED)",
            command=self.toggle_autostart,
            onvalue=True,
            offvalue=False
        )
        autostart_switch.pack(pady=10)
        if self.autostart_enabled:
            autostart_switch.select()
        else:
            autostart_switch.deselect()

        # Window resizing ayarı
        resizing_switch = ctk.CTkSwitch(
            settings_window,
            text="Window resizing",
            command=self.toggle_resizing,
            onvalue=True,
            offvalue=False
        )
        resizing_switch.pack(pady=10)
        if self.resizing_enabled:
            resizing_switch.select()
        else:
            resizing_switch.deselect()

        # UAC bypass ayarı
        uac_switch = ctk.CTkSwitch(
            settings_window,
            text="Bypass UAC (NOT RECOMMENDED)",
            command=self.toggle_uac_bypass,
            onvalue=True,
            offvalue=False
        )
        uac_switch.pack(pady=10)
        if self.uac_bypass_enabled:
            uac_switch.select()
        else:
            uac_switch.deselect()

        # Desteklenen uzantıları ekleme
        extension_label = ctk.CTkLabel(settings_window, text="Add to the list of supported files:")
        extension_label.pack(pady=10)
        extension_entry = ctk.CTkEntry(settings_window, placeholder_text=".png, .jpg")
        extension_entry.pack(pady=5)
        add_button = ctk.CTkButton(
            settings_window,
            text="Add",
            command=lambda: self.add_supported_extension(extension_entry.get())
        )
        add_button.pack(pady=10)

    def toggle_cooldown(self):
        self.cooldown_enabled = not self.cooldown_enabled
        self.save_settings()

    def toggle_autostart(self):
        self.autostart_enabled = not self.autostart_enabled
        self.save_settings()
        self.start_button.pack_forget() if self.autostart_enabled else self.start_button.pack(pady=(5, 10))

    def toggle_resizing(self):
        self.resizing_enabled = not self.resizing_enabled
        self.save_settings()
        self.apply_resizing_setting()

    def toggle_uac_bypass(self):
        self.uac_bypass_enabled = not self.uac_bypass_enabled
        self.save_settings()
        if self.uac_bypass_enabled:
            self.run_as_admin()

    def add_supported_extension(self, extension):
        extension = extension.strip()
        if extension and extension not in self.supported_extensions:
            self.supported_extensions.append(extension)
            self.save_settings()
            messagebox.showinfo("Başarılı", f"{extension} uzantısı desteklenen dosyalar listesine eklendi.")

    def run_as_admin(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            except Exception as e:
                messagebox.showerror("Hata", f"Yönetici izni alınamadı: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
