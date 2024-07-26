"""Update functions for Splash Utilities"""

from config import appConfig
from threading import Thread
from version import CLUB_CSV_URL

# import requests
import csv
import logging
import os
import zipfile
import io
import re
import requests
import datetime


class SDIF_Merge(Thread):
    def __init__(self, config: appConfig):
        super().__init__()
        self._config: appConfig = config

    def run(self):
        logging.info("Merging SDIF files...")

        self._entry_file_directory = self._config.get_str("entry_file_directory")
        self._output_sd3_file = self._config.get_str("output_sd3_file")
        self._output_report_file = self._config.get_str("output_report_file")
        self._csv_file = self._config.get_str("csv_file")
        self._set_country = self._config.get_bool("set_country")
        self._set_region = self._config.get_bool("set_region")

        logging.info("Merging SDIF files...")

        self.merge_sdif_files(self._entry_file_directory, self._output_sd3_file)

    def fix_c1_record(self, clubdata, line):
        # Update the C1 record with the correct country and region codes

        prov_code = line[11:12].strip()
        team_code = line[13:17].strip() + line[149:150].strip()
        cur_country = line[139:142].strip()
        cur_name = line[17:47].strip()

        mylist = list(filter(lambda person: person["Club Code"] == team_code, clubdata))

        # The club list should only have one entry per club. If there is more than one, we have a problem and we skip it

        if len(mylist) == 1:
            if self._set_country and (cur_country != "CAN" or cur_country == None):
                logging.info("Country code updated for club %s %s", team_code, cur_name)
                line = line[:139] + "CAN" + line[142:]
            if self._set_region and (prov_code != mylist[0]["Province"]):
                logging.info("Region code updated for club %s %s", team_code, cur_name)
                line = line[:11] + mylist[0]["Province"] + line[13:]
        return line

    def merge_sdif_files(self, directory, output_file):
        # Get a list of all the files in the directory
        files = os.listdir(directory)
        # Create a list of files to process
        files_to_process = [f for f in files if f.endswith(".sd3") or f.endswith(".zip")]

        if len(files_to_process) == 0:
            logging.info("No SD3 or zip files to process")
            return

        if self._set_country or self._set_region:
            clubdata = self.load_remote_csv_file(CLUB_CSV_URL)
            # Be sure we have somehting
            if len(clubdata) == 0:
                logging.error("Club CSV File not found - unable to set country and region codes")
                return


        merged_a0_record = "A01V3      01                              SDIF MERGE UTILITY            SDIF MERGE          unknown     07012024                                               "
        current_date = datetime.datetime.now().strftime("%m%d%Y")
        merged_a0_record = merged_a0_record[:80] + current_date + merged_a0_record[88:]

        try:
            report_file = open(self._output_report_file, "w")
        except FileNotFoundError:
            logging.error("Unable to open report file: %s", self._output_report_file)
            return

        report_file.write("SDIF Merge Report\n")
        report_file.write("====================================\n\n")
        report_file.write(f"Entry File Directory: {directory}\n")
        report_file.write(f"Output SD3 File: {output_file}\n\n")
        report_file.write(f"Files Processed:\n\n")

        with open(output_file, "w") as out:
            # File Processing
            # The first two characters represent the record type.
            # A0 - Generating Program Information
            # B1 - Meet Data
            # C1 - Club Data
            # D0 - Athlete Individual Entry
            # D3 - Extended Athlete data
            # E0 - Relay Team Entry
            # F0 - Relay Athlete Entry
            # Z0 - End of File Record
            # When merging, use the A0 and B1 record from the first file to start the output file.
            # For each file copy all records except the A0, B1 and Z0 records to the output file. Keep a count of each record type.
            # At the end copy the last Z0 record to the output file.

            files_processed = 0
            latest_Z0 = None

            for f in files_to_process:
                if f.endswith(".sd3"):
                    with open(os.path.join(directory, f), "r") as file:
                        for line in file:
                            if line.startswith("A0") and files_processed == 0:
                                # Add logic to change the date in the A0 record
                                out.write(merged_a0_record)
                            elif line.startswith("B1") and files_processed == 0:
                                out.write(line)
                            elif line.startswith("C1") and (self._set_country or self._set_region):
                                line = self.fix_c1_record(clubdata, line)
                                out.write(line)
                            elif line.startswith("Z0"):
                                latest_Z0 = line
                            else:
                                out.write(line)
                    logging.info("Processed file: %s", f)
                    report_file.write(f"Processed file: {f}\n")
                    files_processed += 1
                elif f.endswith(".zip"):
                    with zipfile.ZipFile(os.path.join(directory, f), "r") as zfile:
                        for zf in zfile.infolist():
                            if re.match(r".*\.sd3", zf.filename):
                                compressed_file = zfile.open(zf)
                                sd3_file = io.TextIOWrapper(compressed_file)
                                with sd3_file as file:
                                    for line in file:
                                        if line.startswith("A0") and files_processed == 0:
                                            # Add logic to change the date in the A0 record
                                            out.write(merged_a0_record)
                                        elif line.startswith("B1") and files_processed == 0:
                                            out.write(line)
                                        elif line.startswith("C1") and (self._set_country or self._set_region):
                                            line = self.fix_c1_record(clubdata, line)
                                            out.write(line)
                                        elif line.startswith("Z0"):
                                            latest_Z0 = line
                                        else:
                                            out.write(line)
                                logging.info("Processed file: %s in zip file: %s", zf.filename, f)
                                report_file.write(f"Processed file: {zf.filename} in zip file: {f}\n")
                                files_processed += 1
            out.write(latest_Z0)
            logging.info("Processed %s files", files_processed)
            report_file.write(f"Processed {files_processed} files\n")

    def csv_to_dict(self, file_path):
        data_dict = []
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_dict.append(row)
        return data_dict

    def load_remote_csv_file(self, url) -> list:
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error("Error downloading CSV file")
            logging.error(e)
            return []
        
        csv_data = io.StringIO(response.text)
        reader = csv.DictReader(csv_data)

        data = [row for row in reader]
        return data
    
    
        


if __name__ == "__main__":
    x = SDIF_Merge(appConfig())
    clublist = x.load_remote_csv_file(CLUB_CSV_URL)
    print(clublist)