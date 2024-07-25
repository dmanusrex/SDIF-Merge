""" TimeValidate Main Screen """

import os
import pandas as pd
import logging
import customtkinter as ctk  # type: ignore
import webbrowser

import tkinter as tk
from tkinter import filedialog, BooleanVar, StringVar, HORIZONTAL
from typing import Any
from platformdirs import user_config_dir
import pathlib

# Appliction Specific Imports
from config import appConfig
from version import APP_VERSION
from sdif_merge_core import SDIF_Merge

tkContainer = Any


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state="normal")
            self.text.insert(tk.END, msg + "\n")
            self.text.configure(state="disabled")
            # Autoscroll to the bottom
            self.text.yview(tk.END)

        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


class _Splash_Fixes_Tab(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    """Main Ui Window to apply the various changes"""

    def __init__(self, container: tkContainer, config: appConfig):
        super().__init__(container)
        self._config = config

        self._entry_file_directory = StringVar(value=self._config.get_str("entry_file_directory"))
        self._output_sd3_file = StringVar(value=self._config.get_str("output_sd3_file"))
        self._output_report_file = StringVar(value=self._config.get_str("output_report_file"))
        self._csv_file = StringVar(value=self._config.get_str("csv_file"))
        self._set_country = BooleanVar(value=self._config.get_bool("set_country"))
        self._set_region = BooleanVar(value=self._config.get_bool("set_region"))

        # self is a vertical container that will contain 3 frames
        self.columnconfigure(0, weight=1)
        # Options Frame - Left and Right Panels

        optionsframe = ctk.CTkFrame(self)
        optionsframe.grid(column=0, row=2, sticky="news")

        filesframe = ctk.CTkFrame(optionsframe)
        filesframe.grid(column=0, row=0, sticky="new", padx=10, pady=10)
        filesframe.rowconfigure(0, weight=1)
        filesframe.rowconfigure(1, weight=1)
        filesframe.rowconfigure(2, weight=1)

        right_optionsframe = ctk.CTkFrame(optionsframe)
        right_optionsframe.grid(column=1, row=0, sticky="new", padx=10, pady=10)
        right_optionsframe.rowconfigure(0, weight=1)

        buttonsframe = ctk.CTkFrame(self)
        buttonsframe.grid(column=0, row=4, sticky="news")
        buttonsframe.rowconfigure(0, weight=0)

        # Files Section
        ctk.CTkLabel(filesframe, text="Files").grid(column=0, row=0, sticky="w", padx=10)

        btn1 = ctk.CTkButton(filesframe, text="Entry File Directory", command=self._handle_entry_file_directory_browse)
        btn1.grid(column=0, row=1, padx=20, pady=10)
        ctk.CTkLabel(filesframe, textvariable=self._entry_file_directory).grid(
            column=1, row=1, sticky="w", padx=(0, 10)
        )

        btn2 = ctk.CTkButton(filesframe, text="Output SD3 File", command=self._handle_output_sd3_file_browse)
        btn2.grid(column=0, row=2, padx=20, pady=10)
        ctk.CTkLabel(filesframe, textvariable=self._output_sd3_file).grid(column=1, row=2, sticky="w", padx=(0, 10))

        btn3 = ctk.CTkButton(filesframe, text="Output Report File", command=self._handle_output_report_file_browse)
        btn3.grid(column=0, row=3, padx=20, pady=10)
        ctk.CTkLabel(filesframe, textvariable=self._output_report_file).grid(column=1, row=3, sticky="w", padx=(0, 10))

        btn4 = ctk.CTkButton(filesframe, text="Club CSV File", command=self._handle_csv_file_browse)
        btn4.grid(column=0, row=4, padx=20, pady=10)
        ctk.CTkLabel(filesframe, textvariable=self._csv_file).grid(column=1, row=4, sticky="w", padx=(0, 10))

        # Right options frame for status options

        ctk.CTkLabel(right_optionsframe, text="Program Options").grid(column=0, row=0, sticky="nw", padx=10)

        # Switches

        ctk.CTkSwitch(
            right_optionsframe, text="Update Country", variable=self._set_country, onvalue=True, offvalue=False
        ).grid(column=0, row=2, sticky="w", padx=20, pady=10)

        ctk.CTkSwitch(
            right_optionsframe, text="Update Region", variable=self._set_region, onvalue=True, offvalue=False
        ).grid(column=0, row=4, sticky="w", padx=20, pady=10)

        # Buttons Section - Merge Files

        ctk.CTkLabel(buttonsframe, text="Actions").grid(column=0, row=0, sticky="w", padx=10, pady=10)

        self.merge_btn = ctk.CTkButton(buttonsframe, text="Merge SDIF Files", command=self._handle_merge_btn)
        self.merge_btn.grid(column=0, row=1, sticky="news", padx=20, pady=10)

    def _handle_entry_file_directory_browse(self) -> None:
        entry_file_directory = filedialog.askdirectory(
            title="Entry File Directory", initialdir=self._entry_file_directory.get()
        )
        if len(entry_file_directory) == 0:
            return
        self._config.set_str("entry_file_directory", entry_file_directory)
        self._entry_file_directory.set(entry_file_directory)

    def _handle_output_sd3_file_browse(self) -> None:
        output_sd3_file = filedialog.asksaveasfilename(
            filetypes=[("SD3 File", "*.sd3")],
            defaultextension=".sd3",
            title="Output SD3 File",
            initialfile=self._output_sd3_file.get(),
        )
        if len(output_sd3_file) == 0:
            return
        self._config.set_str("output_sd3_file", output_sd3_file)
        self._output_sd3_file.set(output_sd3_file)

    def _handle_output_report_file_browse(self) -> None:
        output_report_file = filedialog.asksaveasfilename(
            filetypes=[("Text File", "*.txt")],
            defaultextension=".txt",
            title="Output Report File",
            initialfile=self._output_report_file.get(),
        )
        if len(output_report_file) == 0:
            return
        self._config.set_str("output_report_file", output_report_file)
        self._output_report_file.set(output_report_file)
    
    def _handle_csv_file_browse(self) -> None:
        csv_file = filedialog.askopenfilename(
            filetypes=[("CSV File", "*.csv")],
            defaultextension=".csv",
            title="CSV File",
            initialfile=self._csv_file.get(),
        )
        if len(csv_file) == 0:
            return
        self._config.set_str("csv_file", csv_file)
        self._csv_file.set(csv_file)

    def _handle_merge_btn(self) -> None:
        self.merge_btn.configure(state="disabled")

        merge_thread = SDIF_Merge(self._config)
        merge_thread.start()
        self.monitor_merge_thread(merge_thread)
    
    def monitor_merge_thread(self, thread):
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitor_merge_thread(thread))
        else:
            self.merge_btn.configure(state="enabled")
            thread.join()
    
    def _handle_update_country(self) -> None:
        self._config.set_bool("set_country", self._set_country.get())

    def _handle_update_region(self) -> None:
        self._config.set_bool("set_region", self._set_region.get())

    def buttons(self, newstate) -> None:
        """Enable/disable all buttons"""
        self.merge_btn.configure(state=newstate)



class _Configuration_Tab(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    """Configuration Tab"""

    def __init__(self, container: tkContainer, config: appConfig):
        super().__init__(container)
        self._config = config

        self._ctk_theme = StringVar(value=self._config.get_str("Theme"))
        self._ctk_size = StringVar(value=self._config.get_str("Scaling"))
        self._ctk_colour = StringVar(value=self._config.get_str("Colour"))

        # self is a vertical container that will contain 3 frames
        self.columnconfigure(0, weight=1)

        optionsframe = ctk.CTkFrame(self)
        optionsframe.grid(column=0, row=2, sticky="news")

        # Options Frame - Left and Right Panels

        left_optionsframe = ctk.CTkFrame(optionsframe)
        left_optionsframe.grid(column=0, row=0, sticky="news", padx=10, pady=10)
        left_optionsframe.rowconfigure(0, weight=1)
        right_optionsframe = ctk.CTkFrame(optionsframe)
        right_optionsframe.grid(column=1, row=0, sticky="new", padx=10, pady=10)
        right_optionsframe.rowconfigure(0, weight=1)
        right_optionsframe.rowconfigure(1, weight=1)
        right_optionsframe.rowconfigure(2, weight=1)
        right_optionsframe.rowconfigure(3, weight=1)

        # Program Options on the left frame

        ctk.CTkLabel(left_optionsframe, text="UI Appearance").grid(column=0, row=0, sticky="w", padx=10)

        ctk.CTkLabel(left_optionsframe, text="Appearance Mode", anchor="w").grid(row=1, column=1, sticky="w")
        ctk.CTkOptionMenu(
            left_optionsframe,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
            variable=self._ctk_theme,
        ).grid(row=1, column=0, padx=20, pady=10)

        ctk.CTkLabel(left_optionsframe, text="UI Scaling", anchor="w").grid(row=2, column=1, sticky="w")
        ctk.CTkOptionMenu(
            left_optionsframe,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event,
            variable=self._ctk_size,
        ).grid(row=2, column=0, padx=20, pady=10)

        ctk.CTkLabel(left_optionsframe, text="Colour (Restart Required)", anchor="w").grid(row=3, column=1, sticky="w")
        ctk.CTkOptionMenu(
            left_optionsframe,
            values=["blue", "green", "dark-blue"],
            command=self.change_colour_event,
            variable=self._ctk_colour,
        ).grid(row=3, column=0, padx=20, pady=10)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self._config.set_str("Theme", new_appearance_mode)

    def change_scaling_event(self, new_scaling: str) -> None:
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        self._config.set_str("Scaling", new_scaling)

    def change_colour_event(self, new_colour: str) -> None:
        logging.info("Changing colour to : " + new_colour)
        ctk.set_default_color_theme(new_colour)
        self._config.set_str("Colour", new_colour)


class _Logging(ctk.CTkFrame):  # pylint: disable=too-many-ancestors,too-many-instance-attributes
    """Logging Window"""

    def __init__(self, container: ctk.CTk, config: appConfig):
        super().__init__(container)
        self._config = config
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)

        ctk.CTkLabel(self, text="Messages").grid(column=0, row=0, sticky="ws", padx=(10, 0), pady=10)

        self.logwin = ctk.CTkTextbox(self, state="disabled")
        self.logwin.grid(column=0, row=2, sticky="new", padx=(10, 10), pady=(0, 10))
        self.logwin.configure(height=100, wrap="word")
        # Logging configuration
        userconfdir = user_config_dir("SDIFMerge", "Swimming Canada")
        pathlib.Path(userconfdir).mkdir(parents=True, exist_ok=True)
        logfile = os.path.join(userconfdir, "sdif_merge.log")

        logging.basicConfig(filename=logfile, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        # Create textLogger
        text_handler = TextHandler(self.logwin)
        text_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        # Add the handler to logger
        logger = logging.getLogger()
        logger.addHandler(text_handler)


class mainApp(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    """Main Appliction"""

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(self, container: ctk.CTk, config: appConfig):
        super().__init__(container)
        self._config = config

        self.grid(column=0, row=0, sticky="news")
        self.columnconfigure(0, weight=1)
        # Odd rows are empty filler to distribute vertical whitespace
        for i in [1, 3]:
            self.rowconfigure(i, weight=1)

        self.tabview = ctk.CTkTabview(self, width=container.winfo_width())
        self.tabview.grid(row=0, column=0, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.tabview.add("SDIF Merge")
        self.tabview.add("Configuration")

        # Generate Documents Tab
        self.tabview.tab("SDIF Merge").grid_columnconfigure(0, weight=1)
        self.SDIFMergeTab = _Splash_Fixes_Tab(self.tabview.tab("SDIF Merge"), self._config)
        self.SDIFMergeTab.grid(column=0, row=0, sticky="news")

        self.tabview.tab("Configuration").grid_columnconfigure(0, weight=1)
        self.configinfo = _Configuration_Tab(self.tabview.tab("Configuration"), self._config)
        self.configinfo.grid(column=0, row=0, sticky="news")

        # Logging Window
        loggingwin = _Logging(self, self._config)
        loggingwin.grid(column=0, row=2, padx=(20, 20), pady=(20, 0), sticky="new")

        # Info panel
        fr8 = ctk.CTkFrame(self)
        fr8.grid(column=0, row=4, sticky="news", pady=(10, 0))
        fr8.rowconfigure(0, weight=1)
        fr8.columnconfigure(0, weight=1)
        link_label = ctk.CTkLabel(fr8, text="Documentation: Coming Soon...")
        link_label.grid(column=0, row=0, sticky="w", padx=10)
        # Custom Tkinter clickable label example https://github.com/TomSchimansky/CustomTkinter/issues/1208
        link_label.bind(
            "<Button-1>", lambda event: webbrowser.open("https://www.swimming.ca")
        )  # link the command function
        link_label.bind("<Enter>", lambda event: link_label.configure(font=("", 13, "underline"), cursor="hand2"))
        link_label.bind("<Leave>", lambda event: link_label.configure(font=("", 13), cursor="arrow"))
        version_label = ctk.CTkLabel(fr8, text="Version " + APP_VERSION)
        version_label.grid(column=1, row=0, sticky="nes", padx=(0, 10))


def main():
    """testing"""
    root = ctk.CTk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.resizable(True, True)
    options = appConfig()
    settings = mainApp(root, options)
    settings.grid(column=0, row=0, sticky="news")
    logging.info("Hello World")
    root.mainloop()


if __name__ == "__main__":
    main()
