"""Update functions for Splash Utilities"""

from config import appConfig
from threading import Thread
import requests
import pyodbc  # type: ignore
import csv
import logging
import os
import zipfile
import io
import re


class Update_Clubs(Thread):
    def __init__(self, config: appConfig):
        super().__init__()
        self._config: appConfig = config

    def run(self):
        logging.info("Updating Region (Province) Code on all Clubs...")

        _splash_db_file = self._config.get_str("splash_db")
        _splash_db_driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"
        _csv_file = self._config.get_str("csv_file")
        _update_db = self._config.get_bool("update_database")
        _update_db = False
        try:
            logging.info("Reading CSV File...")
            data = self.csv_to_dict(_csv_file)
            logging.info("  CSV File Read - Total Clubs = %s", len(data))
        except FileNotFoundError:
            logging.error("CSV File not found")
            return

        logging.info("Reading Splash Database...")

        connection_string = "DRIVER={};DBQ={};".format(_splash_db_driver, _splash_db_file)
        try:
            con = pyodbc.connect(connection_string)
        except pyodbc.Error as ex:
            logging.error("Error connecting to database")
            logging.error(ex)
            return

        SQL = "SELECT CLUBID, CODE, NAME, NATION, REGION " "FROM CLUB "

        # iterate over the returned rows and set the region code to the province field from the CSV file

        cursor = con.cursor()
        try:
            cursor.execute(SQL)
            rows = cursor.fetchall()
        except:
            logging.error("Error reading database")
            return

        logging.info("  Splash Database Read - Total Clubs = %s", len(rows))

        _count_clubs = 0
        _count_club_names = 0

        for row in rows:
            club_id = row[0]
            club_code = row[1]
            club_name = row[2]
            club_nation = row[3]
            club_region = row[4]

            # if the club is not Canadian, skip it
            if club_nation != "CAN":
                continue

            mylist = list(filter(lambda person: person["Club Code"] == club_code, data))

            if len(mylist) != 1:
                logging.error("Club Code %s not found in CSV file", club_code)
                continue

            province = mylist[0]["Province"]
            clubname = mylist[0]["Club Name"]
            preferred_club_name = mylist[0]["Preferred Club Name"]

            # update the region code in the database only if it is different from the province field in the CSV file

            if club_region != province:
                SQL = "UPDATE CLUB SET REGION = ? WHERE CLUBID = ? "
                _count_clubs += 1
                if _update_db:
                    cursor.execute(SQL, (province, club_id))
                    con.commit()

                logging.info("Club Code %s updated to Province %s", club_code, province)

            # Set the preferred club long name if one is set.
            if preferred_club_name is not None:
                if (preferred_club_name != club_name) and (len(preferred_club_name) > 1):
                    SQL = "UPDATE CLUB SET NAME = ? WHERE CLUBID = ? "
                    _count_club_names += 1
                    if _update_db:
                        cursor.execute(SQL, (preferred_club_name, club_id))
                        con.commit()
                    logging.info(
                        "Club Code %s not preferred name. <%s> updated to <%s>",
                        club_code,
                        club_name,
                        preferred_club_name,
                    )

        con.close()
        logging.info("Update Complete - %s Clubs updated, %s Club Names updated", _count_clubs, _count_club_names)

    def csv_to_dict(self, file_path):
        data_dict = []
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_dict.append(row)
        return data_dict


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

        if len(mylist) == 1:
            if self._set_country and (cur_country != 'CAN' or cur_country == None):
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
            try:
                clubdata = self.csv_to_dict(self._csv_file)
            except FileNotFoundError:
                logging.error("Club CSV File not found - unable to set country and region codes")
                return

        merged_a0_record = "A01V3      01                              SPLASH Team Manager #79765    Splash Software     unknown     07012024                                               "
        #        merged_a0_record = "A01V3      01                              SPLASH Team Manager #79765    Splash Software     unknown     07012024                                               "
        #        merged_a0_record = "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
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
    
if __name__ == "__main__":
    print("Hello World")
