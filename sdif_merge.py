# Test basic functions
import customtkinter as ctk  # type: ignore
import sdif_merge_ui as ui
from version import APP_VERSION
from config import appConfig
import logging
import os
import sys
import app_version
from requests.exceptions import RequestException


def check_for_update() -> None:
    """Notifies if there's a newer released version"""
    current_version = APP_VERSION
    try:
        latest_version = app_version.latest()
        if latest_version is not None and not app_version.is_latest_version(latest_version, current_version):
            logging.info(f"New version available {latest_version.tag}")
            logging.info(f"Download URL: {latest_version.url}")
    #           Make it clickable???  webbrowser.open(latest_version.url))
    except RequestException as ex:
        logging.warning("Error checking for update: %s", ex)


def main():
    """Runs the application"""

    bundle_dir = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))

    root = ctk.CTk()
    config = appConfig()
    ctk.set_appearance_mode(config.get_str("Theme"))  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme(config.get_str("Colour"))  # Themes: "blue" (standard), "green", "dark-blue"
    new_scaling_float = int(config.get_str("Scaling").replace("%", "")) / 100
    #    ctk.set_widget_scaling(new_scaling_float)
    #    ctk.set_window_scaling(new_scaling_float)
    root.title("Swimming Canada - SDIF Merge")
    icon_file = os.path.abspath(os.path.join(bundle_dir, "media", "SplashUtilities.ico"))
    root.iconbitmap(icon_file)
    #    root.geometry(f"{850}x{1050}")
    #    root.minsize(800, 900)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.resizable(True, True)
    content = ui.mainApp(root, config)
    content.grid(column=0, row=0, sticky="news")
    check_for_update()

    try:
        root.update()
        # pylint: disable=import-error,import-outside-toplevel
        import pyi_splash  # type: ignore

        if pyi_splash.is_alive():
            pyi_splash.close()
    except ModuleNotFoundError:
        pass
    except RuntimeError:
        pass

    root.mainloop()

    config.save()


if __name__ == "__main__":
    main()
