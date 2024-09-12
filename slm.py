import os
import sys
import shutil
import socket
import csv
import json
import re
import urllib.parse
import requests
import datetime
import time
import threading
import logging
import aiohttp
import asyncio
import stat
import unicodedata
from pytimedinput import timedInput
from flask import Flask, render_template, render_template_string, request, redirect, url_for, Response, send_file, Request, make_response
from jinja2 import TemplateNotFound

# Control how many data elements can be saved at a time from the webpage to the code
class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super(CustomRequest, self).__init__(*args, **kwargs)
        self.max_form_parts = 100000 # Modify value higher if continual 413 issues

# Global Variables
slm_version = "v2024.09.12.1808"
slm_port = os.environ.get("SLM_PORT")
if slm_port is None:
    slm_port = 5000
else:
    try:
        slm_port = int(slm_port)
    except:
        slm_port = 5000
app = Flask(__name__)
app.request_class = CustomRequest
script_dir = os.path.dirname(os.path.abspath(__file__))
script_filename = os.path.basename(__file__)
log_filename = os.path.splitext(script_filename)[0] + '.log'
program_files_dir = os.path.join(script_dir, "program_files")
backup_dir = os.path.join(program_files_dir, "backups")
max_backups = 3
csv_settings = "StreamLinkManager_Settings.csv"
csv_streaming_services = "StreamLinkManager_StreamingServices.csv"
csv_bookmarks = "StreamLinkManager_Bookmarks.csv"
csv_bookmarks_status = "StreamLinkManager_BookmarksStatus.csv"
csv_slmappings = "StreamLinkManager_SLMappings.csv"
csv_files = [
    csv_settings,
    csv_streaming_services,
    csv_bookmarks,
    csv_bookmarks_status,
    csv_slmappings  #,
    # Add more rows as needed
]
program_files = csv_files + [log_filename]
engine_url = "https://www.justwatch.com"
url_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
_GRAPHQL_API_URL = "https://apis.justwatch.com/graphql"
valid_country_codes = [
    "AD",
    "AE",
    "AG",
    "AL",
    "AR",
    "AT",
    "AU",
    "BA",
    "BB",
    "BE",
    "BG",
    "BH",
    "BM",
    "BO",
    "BR",
    "BS",
    "CA",
    "CH",
    "CI",
    "CL",
    "CO",
    "CR",
    "CU",
    "CV",
    "CZ",
    "DE",
    "DK",
    "DO",
    "DZ",
    "EC",
    "EE",
    "EG",
    "ES",
    "FI",
    "FJ",
    "FR",
    "GB",
    "GF",
    "GG",
    "GH",
    "GI",
    "GQ",
    "GR",
    "GT",
    "HK",
    "HN",
    "HR",
    "HU",
    "ID",
    "IE",
    "IL",
    "IN",
    "IQ",
    "IS",
    "IT",
    "JM",
    "JO",
    "JP",
    "KE",
    "KR",
    "KW",
    "LB",
    "LI",
    "LT",
    "LV",
    "LY",
    "MA",
    "MC",
    "MD",
    "MK",
    "MT",
    "MU",
    "MX",
    "MY",
    "MZ",
    "NE",
    "NG",
    "NL",
    "NO",
    "NZ",
    "OM",
    "PA",
    "PE",
    "PF",
    "PH",
    "PK",
    "PL",
    "PS",
    "PT",
    "PY",
    "QA",
    "RO",
    "RS",
    "RU",
    "SA",
    "SC",
    "SE",
    "SG",
    "SI",
    "SK",
    "SM",
    "SN",
    "SV",
    "TC",
    "TH",
    "TN",
    "TR",
    "TT",
    "TW",
    "TZ",
    "UG",
    "US",
    "UY",
    "VA",
    "VE",
    "XK",
    "YE",
    "ZA",
    "ZM" #, Add more as needed
]
valid_language_codes = [
    "ar",
    "bg",
    "bs",
    "ca",
    "cs",
    "de",
    "el",
    "en",
    "es",
    "fi",
    "fr",
    "he",
    "hr",
    "hu",
    "is",
    "it",
    "ja",
    "ko",
    "mk",
    "mt",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "sl",
    "sq",
    "sr",
    "sw",
    "tr",
    "ur",
    "zh" #, Add more as needed
]
notifications = []
stream_link_ids_changed = []
program_search_results_prior = []
country_code_input_prior = None
language_code_input_prior = None
entry_id_prior = None
title_selected_prior = None
release_year_selected_prior = None
object_type_selected_prior = None
season_episodes_prior = []
bookmarks_statuses_selected_prior = []
edit_flag = None

# Adds a notification
def notification_add(notification):
    global notifications
    notifications.insert(0, notification)
    print(notification)

# Get the full path for a file
def full_path(file):
    full_path = os.path.join(program_files_dir, file)
    return full_path

# Get the previous full path for a file after upgrade
def full_path_old(file):
    full_path = os.path.join(script_dir, file)
    return full_path

# Normalize the file path for systems that can't handle certain characters like 'é'
def normalize_path(path):
    return unicodedata.normalize('NFKC', path)

# Create a directory if it doesn't exist.
def create_directory(directory_path):
    directory_path = normalize_path(directory_path)

    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
    except OSError as e:
        print(f"    Error creating directory {directory_path}: {e}")

# Create a backup of program files and remove old backups
def create_backup(src_dir, dst_dir, max_backups):
    # Copy the contents of src_dir to the backup subdirectory
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    backup_subdir = os.path.join(dst_dir, timestamp)
    os.makedirs(backup_subdir, exist_ok=True)
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        if os.path.isfile(src_item):
            shutil.copy2(src_item, backup_subdir)

    # Clean up old backups if there are more than max_backups
    backups = sorted(os.listdir(dst_dir))
    if len(backups) > max_backups:
        oldest_backups = backups[:len(backups) - max_backups]
        for old_backup in oldest_backups:
            shutil.rmtree(os.path.join(dst_dir, old_backup))

# Make sure all files and directories are in the correct place
### Program directories
create_directory(program_files_dir)
create_directory(backup_dir)

### Move old program files if they exist
for program_file in program_files:
    old_path = full_path_old(program_file)
    new_path = full_path(program_file)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)

### Make a backup and remove old backups
if os.path.exists(program_files_dir):
    create_backup(program_files_dir, backup_dir, max_backups)

# Set up session logging
log_filename_fullpath = full_path(log_filename)
open(log_filename_fullpath, 'w', encoding="utf-8").close()
class logger(object):
    def __init__(self, filename=log_filename_fullpath, mode="ab", buff=0):
        self.stdout = sys.stdout
        self.stdin = sys.stdin
        self.file = open(filename, mode, buff)
        sys.stdout = self
        sys.stdin = self
    def readline(self):
        user_input = self.stdin.readline()
        self.file.write(user_input.encode("utf-8"))
        return user_input
    def __del__(self):
        self.close()
    def __enter__(self):
        pass
    def __exit__(self, *args):
        self.close()
    def write(self, message):
        self.stdout.write(message)
        self.file.write(message.encode("utf-8"))
    def flush(self):
        self.stdout.flush()
        self.file.flush()
        os.fsync(self.file.fileno())
    def close(self):
        if self.stdout != None:
            sys.stdout = self.stdout
            self.stdout = None
        if self.stdin != None:
            sys.stdin = self.stdin
            self.stdin = None
        if self.file != None:
            self.file.close()
            self.file = None
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s | %(asctime)s] - %(message)s",
    filename=log_filename_fullpath,
    filemode="a",
)
log = logger()

# Current date/time for logging
def current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + ": "

notification_add(f"\n{current_time()} Beginning Initialization Process (see log for details)...\n")

# Start-up process and safety checks
def check_website(url):
    try:
        response = requests.get(url, headers=url_headers)
        if response.status_code != 200:
            print(f"\n{current_time()} ERROR: {url} reports {response.status_code}")
            timedInput(f"\nPress enter to exit (or timeout in 30 seconds)...", timeout=30)
            exit()
    except requests.RequestException as e:
        print(f"\n{current_time()} ERROR: {url} reports {e}")
        timedInput(f"\nPress enter to exit (or timeout in 30 seconds)...", timeout=30)
        exit(1)

check_website(engine_url)

# Create missing data files, update data as needed
def check_and_create_csv(csv_file):
    full_path_file = full_path(csv_file)

    data = initial_data(csv_file)
    
    # Check if the file exists, if not create it
    if not os.path.exists(full_path_file):
        # Write data to the file
        write_data(csv_file, data)
        remove_empty_row(csv_file)

        if csv_file == csv_settings:
            print(f"\n*** First Time Setup ***")
            settings = read_data(csv_settings)

            settings[1]['settings'] = find_channels_dvr_path()
            
            print(f"\nSet country code for Streaming Services...")
            settings[2]['settings'] = get_country_code()
            
            write_data(csv_settings, settings)

    # Append/Remove rows to data that may update
    if csv_file == csv_streaming_services:
        id_field = "streaming_service_name"
        update_rows(csv_file, data, id_field)

# Clean up empty data files
def remove_empty_row(csv_file):
    # Create a temporary file to write non-empty rows
    temp_file = full_path("temp.csv")
    full_path_file = full_path(csv_file)

    with open(full_path_file, "r", encoding="utf-8") as infile, open(temp_file, "w", newline="", encoding="utf-8") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Write the header (first row) to the new file
        header = next(reader)
        writer.writerow(header)

        # Process each row
        for row in reader:
            # Check if the row contains any data (non-empty)
            if any(cell.strip() for cell in row):
                writer.writerow(row)

    # Replace the original file with the temporary file
    os.replace(temp_file, full_path_file)

# Appends new rows and removes old rows from initialization data to be writen to data files
def update_rows(csv_file, data, id_field):
    if data:
        new_rows = []
        new_rows = extract_new_rows(csv_file, data, id_field)
        if new_rows:
            print(f"\n{current_time()} INFO: Adding new rows to {csv_file}...\n")
            for new_row in new_rows:
                append_data(csv_file, new_row)
                notification_add(f"    ADDED: {new_row['streaming_service_name']}")
            print(f"\n{current_time()} INFO: Finished adding new rows.\n")
 
        old_rows = []
        old_rows = extract_old_rows(csv_file, data, id_field)
        if old_rows:
            print(f"\n{current_time()} INFO: Removing old rows from {csv_file}...\n")
            for old_row in old_rows:
                notification_add(f"    REMOVED: {old_row['streaming_service_name']}")
            remove_data(csv_file, old_rows, id_field)
            print(f"\n{current_time()} INFO: Finished removing old rows.\n")

    else:
        print(f"\n{current_time()} WARNING: No data to compare, skipping adding and removing rows in {csv_file}.\n")

# Extracts new rows from the library data that are not already present in the CSV file.
def extract_new_rows(csv_file, data, id_field):
    full_path_file = full_path(csv_file)
    
    # Read existing data (if any)
    existing_data = []
    if os.path.exists(full_path_file):
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            existing_data = [row for row in reader]
    
    # Check for duplicate IDs
    existing_ids = {row[id_field] for row in existing_data}
    
    # Extract new rows
    new_rows = []
    for row in data:
        if row[id_field] not in existing_ids:
            new_rows.append(row)
    
    return new_rows

# Extracts old rows from the CSV File that are no longer present in the library data.
def extract_old_rows(csv_file, data, id_field):
    full_path_file = full_path(csv_file)
    
    # Read existing data (if any)
    existing_data = []
    if os.path.exists(full_path_file):
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            existing_data = [row for row in reader]
    
    # Check for duplicate IDs
    existing_ids = {row[id_field] for row in data}
    
    # Extract new rows
    old_rows = []
    for row in existing_data:
        if row[id_field] not in existing_ids:
            old_rows.append(row)
    
    return old_rows

# Data records for initialization files
def initial_data(csv_file):
    if csv_file == csv_settings:
        data = [
                    {"settings": f"http://dvr-{socket.gethostname().lower()}.local:8089"},     # [0] Channels URL
                    {"settings": script_dir},                                                  # [1] Channels Folder
                    {"settings": "US"},                                                        # [2] Search Defaults: Country Code
                    {"settings": "en"},                                                        # [3] Search Defaults: Language Code
                    {"settings": "9"},                                                         # [4] Search Defaults: Number of Results
                    {"settings": "Off"},                                                       # DEPRECATED: [5] Hulu to Disney+ Automatic Conversion
                    {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [6] End-to-End Process Schedule Time
                    {"settings": "On"},                                                        # [7] Channels Prune
                    {"settings": "Off"} #,                                                     # [8] End-to-End Process Schedule On/Off
                    # Add more rows as needed
        ]        
    elif csv_file == csv_streaming_services:
        data = get_streaming_services()
    elif csv_file == csv_bookmarks:
        data = [
            {"entry_id": None,"title": None, "release_year": None, "object_type": None, "url": None, "country_code": None, "language_code": None}
        ]
    elif csv_file == csv_bookmarks_status:
        data = [
            {"entry_id": None, "season_episode_id": None, "season_episode_prefix": None, "season_episode": None, "status": None, "stream_link": None, "stream_link_override": None, "stream_link_file": None}
        ]
    elif csv_file == csv_slmappings:
        data = [
            {"active": "Off", "contains_string": "hulu.com/watch", "object_type": "MOVIE or SHOW", "replace_type": "Replace string with...", "replace_string": "disneyplus.com/play"},
            {"active": "On", "contains_string": "netflix.com/title", "object_type": "MOVIE", "replace_type": "Replace string with...", "replace_string": "netflix.com/watch"},
            {"active": "On", "contains_string": "watch.amazon.com/detail?gti=", "object_type": "MOVIE or SHOW", "replace_type": "Replace string with...", "replace_string": "www.amazon.com/gp/video/detail/"},
            {"active": "Off", "contains_string": "vudu.com", "object_type": "MOVIE or SHOW", "replace_type": "Replace entire Stream Link with...", "replace_string": "fandangonow://"} #,
            # Add more rows as needed
        ]

    return data

# Handler for timeout errors
def timeout_handler():
    global timeout_occurred
    timeout_occurred = True

# Attempts to find the Channels DVR path
def find_channels_dvr_path():
    global timeout_occurred
    timeout_occurred = False
    channels_dvr_path = script_dir
    channels_dvr_path_search = None
    root_path = os.path.abspath(os.sep)
    search_directory = "Imports"

    print(f"\n{current_time()} Searching for Channels DVR folder...")
    print(f"{current_time()} Please wait or press 'Ctrl+C' to stop and continue the initialization process.\n")

    # Search times out after 60 seconds
    timer = threading.Timer(60, timeout_handler)
    timer.start()

    try:
        for root, dirs, _ in os.walk(root_path):
            if timeout_occurred:
                raise TimeoutError # Timeout if serach going for too long
            if search_directory in dirs or search_directory.lower() in dirs:
                if os.path.abspath(os.path.join(root)).lower().endswith("dvr"):
                    channels_dvr_path_search = os.path.abspath(os.path.join(root))
                    break  # Stop searching once found
    except TimeoutError:
        print(f"{current_time()} INFO: Search timed out. Continuing to next step...\n")
    except KeyboardInterrupt:
        print(f"{current_time()} INFO: Search interrupted by user. Continuing to next step...\n")
    finally:
        timer.cancel()  # Disable the timer

    if channels_dvr_path_search:
        print(f"{current_time()} INFO: Channels DVR folder found!\n")
        channels_dvr_path = channels_dvr_path_search
    else:
        print(f"{current_time()} INFO: Channels DVR folder not found, defaulting to current directory. Please set your Channels DVR folder in 'Settings'.\n")

    return channels_dvr_path

# Find all available streaming services for the country
def get_streaming_services():
    settings = read_data(csv_settings)
    country_code = settings[2]['settings']
    
    provider_results = []
    provider_results_json = []
    provider_results_json_array = []
    provider_results_json_array_results = []

    _GRAPHQL_GetProviders = """
    query GetProviders($country: Country!, $platform: Platform!) {
      packages(country: $country, platform: $platform) {
        clearName
        addons(country: $country, platform: $platform) {
          clearName
        }
      }
    }
    """

    json_data = {
        'query': _GRAPHQL_GetProviders,
        'variables': {
            "country": country_code,
            "platform": "WEB"
        },
        'operationName': 'GetProviders',
    }

    try:
        provider_results = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
    except requests.RequestException as e:
        print(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")

    if provider_results:
        provider_results_json = provider_results.json()
        provider_results_json_array = provider_results_json["data"]["packages"]

        for provider in provider_results_json_array :
            provider_addons = []

            entry = {
                "streaming_service_name": provider["clearName"],
                "streaming_service_subscribe": False,
                "streaming_service_priority": None
            }
            provider_results_json_array_results.append(entry)

            provider_addons = provider["addons"]

            if provider_addons:
                for provider_addon in provider_addons:
                    entry = {
                        "streaming_service_name": provider_addon["clearName"],
                        "streaming_service_subscribe": False,
                        "streaming_service_priority": None
                    }
                    provider_results_json_array_results.append(entry)

    return provider_results_json_array_results

# Update Streaming Services
def update_streaming_services():
    data = get_streaming_services()
    update_rows(csv_streaming_services, data, "streaming_service_name")

# Read data from a CSV file.
def read_data(csv_file):
    full_path_file = full_path(csv_file)
    data = []

    try:
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data
    except Exception as e:
        print(f"\n{current_time()} ERROR: Reading data... {e}\n")
        return None

# Write data back to a CSV file.
def write_data(csv_file, data):
    full_path_file = full_path(csv_file)

    try:
        with open(full_path_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()  # Write the header row

            # Write each row from the data list
            writer.writerows(data)
    except Exception as e:
        print(f"\n{current_time()} ERROR: Writing data... {e}\n")

# Appends a new row to an existing CSV file.
def append_data(csv_file, new_row):
    # Get the full path to the CSV file
    full_path_file = full_path(csv_file)
    
    # Check if the file is empty (contains only the header row)
    is_empty = os.path.getsize(full_path_file) == 0
    
    try:
        # Open the file in append mode with UTF-8 encoding
        with open(full_path_file, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=new_row.keys())
            
            # Write the header row if the file is empty
            if is_empty:
                writer.writeheader()
            
            # Append the new row
            writer.writerow(new_row)
    except Exception as e:
        print(f"\n{current_time()} ERROR: Appending data... {e}\n")

# Removes rows from the CSV file
def remove_data(csv_file, old_rows, id_field):
    full_path_file = full_path(csv_file)

    # Read existing data (if any)
    existing_data = []
    if os.path.exists(full_path_file):
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            existing_data = [row for row in reader]

    # Check for duplicate IDs
    existing_ids = set()
    if old_rows:
        existing_ids = {row[id_field] for row in old_rows}

    # Filter out matching rows
    new_rows = [row for row in existing_data if row[id_field] not in existing_ids]

    # Write the new rows back to the CSV file
    write_data(csv_file, new_rows)

# Search for country code
def get_country_code():
    settings = read_data(csv_settings)
    country_code = settings[2]["settings"]
    country_code_input = None
    country_code_new = None

    global timeout_occurred
    timeout_occurred = False
    print(f"\n{current_time()} Searching for country...")
    print(f"{current_time()} Please wait or press 'Ctrl+C' to stop and continue the initialization process.\n")

    # Search times out after 30 seconds
    timer = threading.Timer(30, timeout_handler)
    timer.start()

    try:
        response = requests.get('https://ipinfo.io')
        data = response.json()
        user_country_code = data.get('country').upper()
        
        if user_country_code in valid_country_codes:
            country_code_input = user_country_code
    except TimeoutError:
        print(f"{current_time()} INFO: Search timed out. Continuing to next step...\n")
    except KeyboardInterrupt:
        print(f"{current_time()} INFO: Search interrupted by user. Continuing to next step...\n")
    except Exception as e:
        print(f"{current_time()} INFO: Error getting geolocation: {e}. Continuing to next step...\n")
    finally:
        timer.cancel()  # Disable the timer

    if country_code_input:
        print(f"{current_time()} INFO: Country found! Setting to '{country_code_input.upper()}'.\n")
        country_code_new = country_code_input.upper()
    else:
        print(f"{current_time()} INFO: Country not found, using default value. Please set your Country in 'Settings'.\n")
        country_code_new = country_code

    return country_code_new

for csv_file in csv_files:
    check_and_create_csv(csv_file)

# Check if Channels URL is correct
def check_channels_url(channels_url_input):
    if channels_url_input:
        channels_url = channels_url_input
    else:
        settings = read_data(csv_settings)
        channels_url = settings[0]["settings"]
    
    channels_url_okay = None
    
    try:
        response = requests.get(channels_url, headers=url_headers)
        if response:
            channels_url_okay = True
    except requests.RequestException:
        print(f"\n{current_time()} WARNING: Channels URL not found at {channels_url}")
        print(f"{current_time()} WARNING: Please change Channels URL in settings")

    return channels_url_okay

check_channels_url(None)

notification_add(f"\n{current_time()} Initialization Complete. Starting Stream Link Manager for Channels...\n")

# Home webpage and actions
@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def main_menu():
    return render_template(
        'main/index.html',
        segment = 'index',
        html_slm_version = slm_version,
        html_notifications = notifications
    )

# Settings webpage and actions
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    channels_directory = settings[1]["settings"]
    country_code = settings[2]["settings"]
    language_code = settings[3]["settings"]
    num_results = settings[4]["settings"]
    try:
        auto_update_schedule = settings[8]["settings"]
    except (IndexError, KeyError):
        auto_update_schedule = 'Off'
    auto_update_schedule_time = settings[6]["settings"]
    channels_prune = settings[7]["settings"]

    streaming_services = read_data(csv_streaming_services)

    slmappings = read_data(csv_slmappings)
    slmappings_object_type = [
        "MOVIE or SHOW",
        "MOVIE",
        "SHOW"
    ]
    slmappings_replace_type = [
        "Replace string with...",
        "Replace entire Stream Link with..."
    ]

    redirect_error_handler = None
    channels_url_message = ""
    channels_directory_message = ""
    search_defaults_message = ""

    if not os.path.exists(channels_directory):
        channels_directory_message = f"{current_time()} WARNING: '{channels_directory}' does not exist. Please select a new directory!"
        current_directory = script_dir
    else:
        channels_directory_message = ""
        current_directory = channels_directory

    if request.method == 'POST':
        settings_action = request.form['action']
        channels_url_input = request.form.get('channels_url')
        channels_directory_input = request.form.get('current_directory')
        channels_directory_manual_path = request.form.get('channels_directory_manual_path')
        channels_prune_input = request.form.get('channels_prune')
        country_code_input = request.form.get('country_code')
        language_code_input = request.form.get('language_code')
        num_results_input = request.form.get('num_results')
        streaming_services_input = request.form.get('streaming_services')
        auto_update_schedule_input = request.form.get('auto_update_schedule')
        auto_update_schedule_time_input = request.form.get('auto_update_schedule_time')

        if settings_action.startswith('slmapping_') or settings_action in ['channels_url_cancel',
                                                                           'channels_directory_cancel',
                                                                           'channels_prune_cancel',
                                                                           'search_defaults_cancel',
                                                                           'streaming_services_cancel',
                                                                           'end_to_end_process_cancel',
                                                                           'channels_url_save',
                                                                           'channels_directory_save',
                                                                           'channels_prune_save',
                                                                           'search_defaults_save',
                                                                           'streaming_services_save',
                                                                           'end_to_end_process_save',
                                                                           'streaming_services_update'
                                                                        ]:

            if settings_action.startswith('slmapping_action_') or settings_action in ['channels_url_save',
                                                                                      'channels_directory_save',
                                                                                      'channels_prune_save',
                                                                                      'search_defaults_save',
                                                                                      'streaming_services_save',
                                                                                      'end_to_end_process_save'
                                                                                    ]:

                if settings_action in ['channels_url_save',
                                    'channels_directory_save',
                                    'channels_prune_save',
                                    'search_defaults_save',
                                    'end_to_end_process_save'
                                    ]:

                    if settings_action == 'channels_url_save':
                        settings[0]["settings"] = channels_url_input

                    elif settings_action == 'channels_directory_save':
                        settings[1]["settings"] = channels_directory_input

                    elif settings_action == 'search_defaults_save':
                            settings[2]["settings"] = country_code_input
                            settings[3]["settings"] = language_code_input
                            try:
                                if int(num_results_input) > 0:
                                    settings[4]["settings"] = int(num_results_input)
                                    redirect_error_handler = None
                                else:
                                    search_defaults_message = f"{current_time()} ERROR: For 'Number of Results', please enter a positive integer."
                                    redirect_error_handler = "skip"
                            except ValueError:
                                search_defaults_message = f"{current_time()} ERROR: 'Number of Results' must be a number."
                                redirect_error_handler = "skip"
                    
                    elif settings_action == 'end_to_end_process_save':
                        try:
                            settings[8]["settings"] = "On" if auto_update_schedule_input == 'on' else "Off"
                        except (IndexError, KeyError):
                            settings.append({"settings": "On" if auto_update_schedule_input == 'on' else "Off"})
                        settings[6]["settings"] = auto_update_schedule_time_input

                    elif settings_action == 'channels_prune_save':
                        settings[7]["settings"] = "On" if channels_prune_input == 'on' else "Off"

                    csv_to_write = csv_settings
                    data_to_write = settings

                elif settings_action == 'streaming_services_save':
                    streaming_services_input_json = json.loads(streaming_services_input)
                    csv_to_write = csv_streaming_services
                    data_to_write = streaming_services_input_json

                elif settings_action.startswith('slmapping_action_'):

                    # Add a map
                    if settings_action == 'slmapping_action_new':
                        slmapping_active_new_input = 'On' if request.form.get('slmapping_active_new') == 'on' else 'Off'
                        slmapping_contains_string_new_input = request.form.get('slmapping_contains_string_new')
                        slmapping_object_type_new_input = request.form.get('slmapping_object_type_new')
                        slmapping_replace_type_new_input = request.form.get('slmapping_replace_type_new')
                        slmapping_replace_string_new_input = request.form.get('slmapping_replace_string_new')

                        slmappings.append({
                            "active": slmapping_active_new_input,
                            "contains_string": slmapping_contains_string_new_input,
                            "object_type": slmapping_object_type_new_input,
                            "replace_type": slmapping_replace_type_new_input,
                            "replace_string": slmapping_replace_string_new_input
                        })

                    # Delete a map
                    elif settings_action.startswith('slmapping_action_delete_'):
                        slmapping_action_delete_index = int(settings_action.split('_')[-1]) - 1

                        if 0 <= slmapping_action_delete_index < len(slmappings):
                            slmappings.pop(slmapping_action_delete_index)

                    # Save map modifications
                    elif settings_action == 'slmapping_action_save':
                        slmapping_active_existing_inputs = {}
                        slmapping_contains_string_existing_inputs = {}
                        slmapping_object_type_existing_inputs = {}
                        slmapping_replace_type_existing_inputs = {}
                        slmapping_replace_string_existing_inputs = {}

                        total_number_of_checkboxes = len(slmappings)
                        slmapping_active_existing_inputs = {str(i): 'Off' for i in range(1, total_number_of_checkboxes + 1)}

                        for key in request.form.keys():
                            if key.startswith('slmapping_active_existing_'):
                                index = key.split('_')[-1]
                                slmapping_active_existing_inputs[index] = request.form.get(key)

                            if key.startswith('slmapping_contains_string_existing_'):
                                index = key.split('_')[-1]
                                slmapping_contains_string_existing_inputs[index] = request.form.get(key)

                            if key.startswith('slmapping_object_type_existing_'):
                                index = key.split('_')[-1]
                                slmapping_object_type_existing_inputs[index] = request.form.get(key)

                            if key.startswith('slmapping_replace_type_existing_'):
                                index = key.split('_')[-1]
                                slmapping_replace_type_existing_inputs[index] = request.form.get(key)

                            if key.startswith('slmapping_replace_string_existing_'):
                                index = key.split('_')[-1]
                                slmapping_replace_string_existing_inputs[index] = request.form.get(key)

                        for row in slmapping_active_existing_inputs:
                            slmapping_active_existing_input = slmapping_active_existing_inputs.get(row)
                            slmapping_contains_string_existing_input = slmapping_contains_string_existing_inputs.get(row)
                            slmapping_object_type_existing_input = slmapping_object_type_existing_inputs.get(row)
                            slmapping_replace_type_existing_input = slmapping_replace_type_existing_inputs.get(row)
                            slmapping_replace_string_existing_input = slmapping_replace_string_existing_inputs.get(row)

                            for idx, slmapping in enumerate(slmappings):
                                if idx == int(row) - 1:
                                    slmapping['active'] = slmapping_active_existing_input
                                    slmapping['contains_string'] = slmapping_contains_string_existing_input
                                    slmapping['object_type'] = slmapping_object_type_existing_input
                                    slmapping['replace_type'] = slmapping_replace_type_existing_input
                                    slmapping['replace_string'] = slmapping_replace_string_existing_input

                    csv_to_write = csv_slmappings
                    data_to_write = slmappings

                write_data(csv_to_write, data_to_write)

                if settings_action == 'search_defaults_save':
                    update_streaming_services()
                    time.sleep(5)

            elif settings_action == 'streaming_services_update':
                update_streaming_services()
                time.sleep(5)

            if not redirect_error_handler:
                return redirect(url_for('settings'))

        elif settings_action == 'channels_url_test':
            channels_url_okay = check_channels_url(channels_url_input)
            if channels_url_okay:
                channels_url_message = f"{current_time()} INFO: '{channels_url_input}' responded as expected!"
            else:
                channels_url_message = f"{current_time()} WARNING: Channels URL not found at '{channels_url_input}'. Please update!"

        elif settings_action == 'channels_directory_nav_up':
            current_directory = os.path.dirname(channels_directory_input)
        
        elif settings_action == 'channels_directory_manual_go':
            if os.path.isdir(channels_directory_manual_path):
                current_directory = channels_directory_manual_path
            else:
                channels_directory_message = f"{current_time()} ERROR: Invalid path. Try again."
        
        elif settings_action.startswith('channels_directory_nav_'):
            # Navigate directories
            try:
                selected_index = int(settings_action.split('_')[-1]) - 1
                subdirectories = get_subdirectories(channels_directory_input)
                if 0 <= selected_index < len(subdirectories):
                    current_directory = os.path.join(channels_directory_input, subdirectories[selected_index])
                else:
                    channels_directory_message = f"{current_time()} ERROR: Invalid selection. Try again."
            except ValueError:
                channels_directory_message = f"{current_time()} ERROR: Invalid input. Try again."

    response = make_response(render_template(
        'main/settings.html',
        segment='settings',
        html_slm_version=slm_version,
        html_channels_url=channels_url,
        html_channels_directory=channels_directory,
        html_valid_country_codes=valid_country_codes,
        html_country_code=country_code,
        html_valid_language_codes=valid_language_codes,
        html_language_code=language_code,
        html_num_results=num_results,
        html_auto_update_schedule=auto_update_schedule,
        html_auto_update_schedule_time=auto_update_schedule_time,
        html_channels_prune=channels_prune,
        html_streaming_services=streaming_services,
        html_channels_url_message=channels_url_message,
        html_current_directory=current_directory,
        html_subdirectories=get_subdirectories(current_directory),
        html_channels_directory_message=channels_directory_message,
        html_search_defaults_message=search_defaults_message,
        html_slmappings=slmappings,
        html_slmappings_object_type=slmappings_object_type,
        html_slmappings_replace_type=slmappings_replace_type
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Displays the list of subdirectories in the given directory.
def get_subdirectories(directory):
    return [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]

# Seach for and bookmark programs, or add manual ones
@app.route('/addprograms', methods=['GET', 'POST'])
def add_programs():
    global program_search_results_prior
    global country_code_input_prior 
    global language_code_input_prior
    global entry_id_prior
    global season_episodes_prior

    settings = read_data(csv_settings)
    country_code = settings[2]["settings"]
    language_code = settings[3]["settings"]
    num_results = settings[4]["settings"]
    program_types = [
                        "MOVIE",
                        "SHOW"
                    ]
    program_type_default = "MOVIE"

    program_add_message = ""
    program_search_results = []
    season_episodes = []
    season_episode_manual_flag = None
    end_season = None
    season_episodes_manual = {}
    stream_link_override_movie_flag = None
    done_generate_flag = None

    if request.method == 'POST':
        add_programs_action = request.form['action']
        program_add_input = request.form.get('program_add')

        # Cancel and restart the page
        if add_programs_action == 'program_add_cancel':
            return redirect(url_for('add_programs'))
        
        # Search for a program
        elif add_programs_action == 'program_add_search':
            country_code_input = request.form.get('country_code')
            language_code_input = request.form.get('language_code')
            num_results_input = request.form.get('num_results')
            num_results_test = get_num_results(num_results_input)

            if num_results_test == "pass":
                program_search_results = search_bookmark(country_code_input, language_code_input, num_results_input, program_add_input)
                program_search_results_prior = program_search_results
                country_code_input_prior = country_code_input
                language_code_input_prior = language_code_input

            else:
                program_add_message = num_results_test

        # Select a program from the search
        elif add_programs_action.startswith('program_search_result_'):
            program_search_index = int(add_programs_action.split('_')[-1]) - 1
            program_add_message, entry_id, season_episodes, object_type = search_bookmark_select(program_search_results_prior, program_search_index, country_code_input_prior, language_code_input_prior)

            test_terms = ("WARNING: ", "ERROR: ")
            if any(term in program_add_message for term in test_terms):
                pass
            else:
                entry_id_prior = entry_id
                season_episodes_prior = season_episodes
                if not season_episodes:
                    if object_type == "MOVIE":
                        stream_link_override_movie_flag = True
                    elif object_type == "SHOW":
                        program_add_message = f"{current_time()} WARNING: Selected show has no episodes, but is bookmarked in case episodes are added later."
                done_generate_flag = True

        # Add a manual program
        elif add_programs_action == 'program_add_manual':
            release_year_input = request.form.get('release_year')
            program_type_input = request.form.get('program_type')

            if program_add_input is None or program_add_input == '':
                program_add_message = f"{current_time()} ERROR: A program name is required for manual additions."

            else:
                release_year_test = get_release_year(release_year_input)
                
                if release_year_test == "pass":
                    entry_id = get_manual_entry_id()
                    entry_id_prior = entry_id
                    set_bookmarks(entry_id, program_add_input, release_year_input, program_type_input, "N/A", "N/A", "N/A", "manual")
                    program_add_message = f"{current_time()} You manually added: {program_add_input} ({release_year_input}) | {program_type_input} (ID: {entry_id})"
                    if program_type_input == "SHOW":
                        season_episode_manual_flag = True
                    else:
                        stream_link_override_movie_flag = True
                        done_generate_flag = True
                
                else:
                    program_add_message = release_year_test

        # Create season/episode list for manual shows
        elif add_programs_action == 'season_episode_manual_next':
            end_season = int(request.form.get('last_season_number'))
            for i in range(1, end_season + 1):
                season_episodes_manual[i] = request.form.get(f'season_episode_number_{i}')

            season_episodes = get_episode_list_manual(end_season, season_episodes_manual)
            season_episodes_prior = season_episodes
            done_generate_flag = True

        # Finish or Generate Stream Links. Also save Season/Episode statuses.
        elif add_programs_action in [
                                    'program_add_done',
                                    'program_add_generate'
                                    ]:
               
            bookmarks_statuses = read_data(csv_bookmarks_status)

            # Get settings for season/episodes
            if season_episodes_prior:
                field_status_inputs = {}
                field_season_episode_inputs = {}
                field_stream_link_override_inputs = {}
                field_season_episode_prefix_inputs = {}

                for key in request.form.keys():
                    if key.startswith('field_status_'):
                        index = key.split('_')[-1]
                        field_status_inputs[index] = 'unwatched' if request.form.get(key) == 'on' else 'watched'
                    
                    if key.startswith('field_season_episode_'):
                        index = key.split('_')[-1]
                        field_season_episode_inputs[index] = request.form.get(key)
			    
                    if key.startswith('field_stream_link_override_'):
                        index = key.split('_')[-1]
                        field_stream_link_override_inputs[index] = request.form.get(key)

                    if key.startswith('field_episode_prefix_'):
                        index = key.split('_')[-1]
                        field_season_episode_prefix_inputs[index] = request.form.get(key)

                for index in field_season_episode_inputs.keys():
                    season_episode_id = None
                    season_episode_prefix = field_season_episode_prefix_inputs.get(index)
                    season_episode = field_season_episode_inputs.get(index)
                    if field_status_inputs.get(index) == "unwatched":
                        status = field_status_inputs.get(index)
                    else:
                        status = "watched"
                    stream_link_override = field_stream_link_override_inputs.get(index)

                    for item in season_episodes_prior:
                        if item["season_episode"] == season_episode:
                            season_episode_id = item["season_episode_id"]
                            break

                    bookmarks_statuses.append({
                        "entry_id": entry_id_prior,
                        "season_episode_id": season_episode_id,
                        "season_episode_prefix": season_episode_prefix,
                        "season_episode": season_episode,
                        "status": status,
                        "stream_link": None,
                        "stream_link_override": stream_link_override,
                        "stream_link_file": None
                    })

            # Get Stream Link Override for a Movie and write back
            else:
                stream_link_override_movie_input = request.form.get('stream_link_override_movie')

                for bookmark_status in bookmarks_statuses:
                    if bookmark_status['entry_id'] == entry_id_prior:
                        bookmark_status['stream_link_override'] = stream_link_override_movie_input

            write_data(csv_bookmarks_status, bookmarks_statuses)

            if add_programs_action == 'program_add_generate':
                program_add_message = generate_stream_links_single(entry_id_prior)
            else:
                program_add_message = f"{current_time()} INFO: Finished adding! Please remember to generate stream links and update in Channels to see this program."

            program_search_results_prior = []
            country_code_input_prior = None
            language_code_input_prior = None
            entry_id_prior = None
            season_episodes_prior = []

    return render_template(
        'main/addprograms.html',
        segment='addprograms',
        html_slm_version = slm_version,
        html_valid_country_codes = valid_country_codes,
        html_country_code = country_code,
        html_valid_language_codes = valid_language_codes,
        html_language_code = language_code,
        html_num_results = num_results,
        html_program_types = program_types,
        html_program_type_default = program_type_default,
        html_program_add_message = program_add_message,
        html_program_search_results = program_search_results,
        html_season_episodes = season_episodes,
        html_season_episode_manual_flag = season_episode_manual_flag,
        html_stream_link_override_movie_flag = stream_link_override_movie_flag,
        html_done_generate_flag = done_generate_flag
    )

# Input the number of search results to return
def get_num_results(num_results_input):
    num_results_test = None

    try:
        if not num_results_input:
            num_results_test = f"{current_time()} ERROR: 'Number of Results' is required."
        num_results = int(num_results_input)
        if num_results > 0:
            num_results_test = "pass"
        else:
            num_results_test = f"{current_time()} ERROR: For 'Number of Results', please enter a positive integer."
    except ValueError:
        num_results_test = f"{current_time()} ERROR: 'Number of Results' must be a number."

    return num_results_test

# Rules for a release year
def get_release_year(release_year_input):
    release_year_test = None
    release_year_min = 1888
    release_year_max = datetime.datetime.now().year + 2

    try:
        if not release_year_input:
            release_year_test = f"{current_time()} ERROR: 'Release Year' is required."
        release_year = int(release_year_input)
        if release_year_min <= release_year <= release_year_max:
            release_year_test = "pass"
        else:
            release_year_test = f"{current_time()} ERROR: For 'Release Year', please enter a valid 4-digit year between {release_year_min} and {release_year_max}."
    except ValueError:
        release_year_test = f"{current_time()} ERROR: For 'Release Year', please enter a numeric value."

    return release_year_test

# Search for a program to bookmark
def search_bookmark(country_code, language_code, num_results, program_search):
    program_search_base = get_program_search(program_search, country_code, language_code, num_results)
    program_search_results = extract_program_search(program_search_base)

    return program_search_results

# Search for a Program on JustWatch
def get_program_search(program_search, country_code, language_code, num_results):
    program_search_results = []
    program_search_results_json = []

    _GRAPHQL_GetSearchTitles = """
    query GetSearchTitles($allowSponsoredRecommendations: SponsoredRecommendationsInput, $backdropProfile: BackdropProfile, $country: Country!, $first: Int! = 5, $format: ImageFormat, $language: Language!, $platform: Platform! = WEB, $profile: PosterProfile, $searchAfterCursor: String, $searchTitlesFilter: TitleFilter, $searchTitlesSortBy: PopularTitlesSorting! = POPULAR, $sortRandomSeed: Int! = 0) {
    popularTitles(
        after: $searchAfterCursor
        allowSponsoredRecommendations: $allowSponsoredRecommendations
        country: $country
        filter: $searchTitlesFilter
        first: $first
        sortBy: $searchTitlesSortBy
        sortRandomSeed: $sortRandomSeed
    ) {
        edges {
        ...SearchTitleGraphql
        __typename
        }
        pageInfo {
        startCursor
        endCursor
        hasPreviousPage
        hasNextPage
        __typename
        }
        sponsoredAd {
        ...SponsoredAd
        __typename
        }
        totalCount
        __typename
    }
    }

    fragment SearchTitleGraphql on PopularTitlesEdge {
    cursor
    node {
        id
        objectId
        objectType
        content(country: $country, language: $language) {
        title
        fullPath
        originalReleaseYear
        shortDescription
        genres {
            shortName
            __typename
        }
        scoring {
            imdbScore
            imdbVotes
            tmdbScore
            tmdbPopularity
            __typename
        }
        posterUrl(profile: $profile, format: $format)
        backdrops(profile: $backdropProfile, format: $format) {
            backdropUrl
            __typename
        }
        upcomingReleases(releaseTypes: [DIGITAL]) {
            releaseDate
            __typename
        }
        __typename
        }
        watchNowOffer(country: $country, platform: WEB) {
        id
        standardWebURL
        __typename
        }
        offers(country: $country, platform: WEB) {
        monetizationType
        presentationType
        standardWebURL
        package {
            id
            packageId
            __typename
        }
        id
        __typename
        }
        __typename
    }
    __typename
    }

    fragment SponsoredAd on SponsoredRecommendationAd {
    bidId
    holdoutGroup
    campaign {
        name
        externalTrackers {
        type
        data
        __typename
        }
        hideRatings
        hideDetailPageButton
        promotionalImageUrl
        promotionalVideo {
        url
        __typename
        }
        promotionalTitle
        promotionalText
        promotionalProviderLogo
        watchNowLabel
        watchNowOffer {
        standardWebURL
        presentationType
        monetizationType
        package {
            id
            packageId
            shortName
            clearName
            icon
            __typename
        }
        __typename
        }
        nodeOverrides {
        nodeId
        promotionalImageUrl
        watchNowOffer {
            standardWebURL
            __typename
        }
        __typename
        }
        node {
        nodeId: id
        __typename
        ... on MovieOrShowOrSeason {
            content(country: $country, language: $language) {
            fullPath
            posterUrl
            title
            originalReleaseYear
            scoring {
                imdbScore
                __typename
            }
            externalIds {
                imdbId
                __typename
            }
            backdrops(format: $format, profile: $backdropProfile) {
                backdropUrl
                __typename
            }
            isReleased
            __typename
            }
            objectId
            objectType
            offers(country: $country, platform: $platform) {
            monetizationType
            presentationType
            package {
                id
                packageId
                __typename
            }
            id
            __typename
            }
            __typename
        }
        ... on MovieOrShow {
            watchlistEntryV2 {
            createdAt
            __typename
            }
            __typename
        }
        ... on Show {
            seenState(country: $country) {
            seenEpisodeCount
            __typename
            }
            __typename
        }
        ... on Season {
            content(country: $country, language: $language) {
            seasonNumber
            __typename
            }
            show {
            __typename
            id
            content(country: $country, language: $language) {
                originalTitle
                __typename
            }
            watchlistEntryV2 {
                createdAt
                __typename
            }
            }
            __typename
        }
        ... on GenericTitleList {
            followedlistEntry {
            createdAt
            name
            __typename
            }
            id
            type
            content(country: $country, language: $language) {
            name
            visibility
            __typename
            }
            titles(country: $country, first: 40) {
            totalCount
            edges {
                cursor
                node: nodeV2 {
                content(country: $country, language: $language) {
                    fullPath
                    posterUrl
                    title
                    originalReleaseYear
                    scoring {
                    imdbScore
                    __typename
                    }
                    isReleased
                    __typename
                }
                id
                objectId
                objectType
                __typename
                }
                __typename
            }
            __typename
            }
            __typename
        }
        }
        __typename
    }
    __typename
    }
    """

    json_data = {
        'query': _GRAPHQL_GetSearchTitles,
        'variables': {
            "first": num_results,
            "platform": "WEB",
            "searchTitlesSortBy": "POPULAR",
            "sortRandomSeed": 0,
            "searchAfterCursor": "",
            "searchTitlesFilter": {
                "personId": None,
                "includeTitlesWithoutUrl": True,
                "searchQuery": program_search
            },
            "language": language_code,
            "country": country_code,
            "allowSponsoredRecommendations": {
                "pageType": "VIEW_SEARCH",
                "placement": "SEARCH_PAGE",
                "language": language_code,
                "country": country_code,
                "geoCountry": country_code,
                "appId": "3.8.2-webapp#eb6ba36",
                "platform": "WEB",
                "supportedFormats": [
                "IMAGE",
                "VIDEO"
                ],
                "supportedObjectTypes": [
                "MOVIE",
                "SHOW",
                "GENERIC_TITLE_LIST",
                "SHOW_SEASON"
                ],
                "testingMode": False,
                "testingModeCampaignName": None
            }
        },
        'operationName': 'GetSearchTitles',
    }

    try:
        program_search_results = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
        program_search_results_json = program_search_results.json()
    except requests.RequestException as e:
        print(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")

    return program_search_results_json

# Extract the entry_id, title, release_year, object_type, url, and short_description from the response
def extract_program_search(program_search_json):
    extracted_data = []
    edges = program_search_json.get("data", {}).get("popularTitles", {}).get("edges", [])
    
    for edge in edges:
        node = edge.get("node", {})
        entry_id = node.get("id")
        title = node.get("content", {}).get("title")
        release_year = node.get("content", {}).get("originalReleaseYear")
        object_type = node.get("objectType")
        href = node.get("content", {}).get("fullPath")
        if href is not None and href != '':
            url = f"{engine_url}{href}"  # Concatenate with the prefix
        else:
            url = None
        short_description = node.get("content", {}).get("shortDescription")
        
        extracted_data.append({
            "entry_id": entry_id,
            "title": title,
            "release_year": release_year,
            "object_type": object_type,
            "url": url,
            "short_description": short_description
        })
    
    return extracted_data

# Select a program to bookmark
def search_bookmark_select(program_search_results, program_search_index, country_code, language_code):
    program_search_selected_message = None
    program_search_selected_entry_id = None
    program_search_selected_title = None
    program_search_selected_release_year = None
    program_search_selected_object_type = None
    program_search_selected_url = None
    season_episodes = []

    try:
        if 0 <= int(program_search_index) < len(program_search_results):
            program_search_selected_entry_id = program_search_results[program_search_index]['entry_id']
            program_search_selected_title = program_search_results[program_search_index]['title']
            program_search_selected_release_year = program_search_results[program_search_index]['release_year']
            program_search_selected_object_type = program_search_results[program_search_index]['object_type']
            program_search_selected_url = program_search_results[program_search_index]['url']

            program_search_selected_message = f"{current_time()} You selected: {program_search_selected_title} ({program_search_selected_release_year}) | {program_search_selected_object_type} (ID: {program_search_selected_entry_id})"

            # Check versus already bookmarked
            bookmarks = read_data(csv_bookmarks)
            bookmarks_append = True
            
            # Reject existing bookmark
            for bookmark in bookmarks:
                if bookmark["entry_id"] == program_search_selected_entry_id:
                    program_search_selected_message = f"{current_time()} WARNING: {program_search_selected_title} ({program_search_selected_release_year}) | {program_search_selected_object_type} (ID: {program_search_selected_entry_id}) already bookmarked!"
                    bookmarks_append = False

            # Write new rows to the bookmark tables
            if bookmarks_append:
                season_episodes = set_bookmarks(program_search_selected_entry_id, program_search_selected_title, program_search_selected_release_year, program_search_selected_object_type, program_search_selected_url, country_code, language_code, "search")

        else:
            program_search_selected_message = f"{current_time()} ERROR: Invalid selection. Please choose a valid option."

    except ValueError:
       program_search_selected_message = f"{current_time()} ERROR: Invalid input. Please enter a valid option."

    return program_search_selected_message, program_search_selected_entry_id, season_episodes, program_search_selected_object_type

# Create a new entry_id for manual programs
def get_manual_entry_id():
    bookmarks = read_data(csv_bookmarks)

    # Extract all entry IDs starting with "slm"
    slm_bookmarks = [bookmark for bookmark in bookmarks if bookmark['entry_id'].startswith('slm')]

    if slm_bookmarks:
        # Find the maximum numeric value after "slm"
        max_numeric_value = max(int(re.search(r'\d+', bookmark['entry_id']).group()) for bookmark in slm_bookmarks)
        next_numeric_value = max_numeric_value + 1
        next_entry_id = f"slm{next_numeric_value:05d}"
    else:
        # No "slm" entries found, start with "slm00001"
        next_entry_id = "slm00001"

    return next_entry_id

# Create a list of episodes for manual shows
def get_episode_list_manual(end_season, season_episodes_manual):
    # Initialize an empty dictionary to store the season and episode data
    episode_data = {}

    # Iterate through each season
    for season_num in range(1, end_season + 1):
        # Get the number of episodes for the current season
        num_episodes = int(season_episodes_manual.get(season_num, 0))

        # Generate the formatted season and episode information
        for episode_num in range(1, num_episodes + 1):
            # Format the season and episode numbers with leading zeros if needed
            formatted_season = f"S{season_num:02d}"
            formatted_episode = f"E{episode_num:02d}"

            # Create the combined season_episode string
            season_episode = formatted_season + formatted_episode

            # Add the season_episode to the dictionary
            episode_data[season_episode] = season_episode

    # Sort the dictionary keys alphabetically
    season_episodes_results = []
    for season_episode in episode_data:
        season_episodes_results.append({"season_episode_id": None, "season_episode": season_episode})

    season_episodes_sorted = sorted(season_episodes_results, key=lambda d: d['season_episode'])

    return season_episodes_sorted

# Create the bookmark and status for the selected program
def set_bookmarks(entry_id, title, release_year, object_type, url, country_code, language_code, type):
    season_episodes = []

    new_row = {'entry_id': entry_id, 'title': title, 'release_year': release_year, 'object_type': object_type, 'url': url, "country_code": country_code, "language_code": language_code}
    append_data(csv_bookmarks, new_row)

    if object_type == "MOVIE":
        new_row = {"entry_id": entry_id, "season_episode_id": None, "season_episode_prefix": None, "season_episode": None, "status": "unwatched", "stream_link": None, "stream_link_override": None, "stream_link_file": None}
        append_data(csv_bookmarks_status, new_row)
    elif object_type == "SHOW":
        if type == "search":
            season_episodes = get_episode_list(entry_id, url, country_code, language_code)

    if type == "search":
        return season_episodes

# Run Stream Link Generation and File Creation on one program
def generate_stream_links_single(entry_id):
    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]

    bookmarks = read_data(csv_bookmarks)
    modify_bookmarks = [bookmark for bookmark in bookmarks if bookmark['entry_id'] == entry_id]

    generate_stream_links_single_message = None
    run_generation = None

    if not os.path.exists(channels_directory):
        generate_stream_links_single_message = f"{current_time()} WARNING: {channels_directory} does not exist, skipping generation. Please change the Channels directory in the Settings menu."
    else:
        run_generation = True
        
    if run_generation:
        if not entry_id.startswith('slm'):
            find_stream_links(modify_bookmarks)
        create_stream_link_files(modify_bookmarks, None)
        generate_stream_links_single_message = f"{current_time()} INFO: Finished generating Stream Links! Please execute process 'Run Updates in Channels' in order to see this program."

    return generate_stream_links_single_message

# Modify existing programs
@app.route('/modifyprograms', methods=['GET', 'POST'])
def modify_programs():
    global entry_id_prior
    global title_selected_prior
    global release_year_selected_prior
    global object_type_selected_prior
    global bookmarks_statuses_selected_prior
    global edit_flag

    bookmarks = read_data(csv_bookmarks)
    bookmarks_statuses = read_data(csv_bookmarks_status)

    sorted_bookmarks = sorted(bookmarks, key=lambda x: sort_key(x["title"]))
    program_modify_message = ''
    bookmarks_statuses_selected = []

    if request.method == 'POST':
        modify_programs_action = request.form['action']
        entry_id_input = request.form.get('entry_id')
        field_title_input = request.form.get('field_title')
        field_release_year_input = request.form.get('field_release_year')

        if modify_programs_action in [
                                        'program_modify_edit',
                                        'program_modify_delete',
                                        'program_modify_generate'
                                     ]:
            
            entry_id_prior = entry_id_input

            if modify_programs_action in [
                                            'program_modify_edit',
                                            'program_modify_delete'
                                        ]:

                for bookmark in bookmarks:
                    if bookmark['entry_id'] == entry_id_prior:
                        title_selected_prior = bookmark['title']
                        release_year_selected_prior = bookmark['release_year']
                        object_type_selected_prior = bookmark['object_type']

                # Opens the edit frame
                if modify_programs_action == 'program_modify_edit':
                    edit_flag = True

                    for bookmark_status in bookmarks_statuses:
                        if bookmark_status['entry_id'] == entry_id_prior:
                            bookmarks_statuses_selected.append(bookmark_status)

                    bookmarks_statuses_selected_sorted = sorted(bookmarks_statuses_selected, key=lambda x: x["season_episode"].casefold())
                    bookmarks_statuses_selected_prior = bookmarks_statuses_selected_sorted

                # Deletes the program
                elif modify_programs_action == 'program_modify_delete':
                    remove_row_csv(csv_bookmarks, entry_id_prior)
                    remove_row_csv(csv_bookmarks_status, entry_id_prior)

                    bookmarks = read_data(csv_bookmarks)
                    sorted_bookmarks = sorted(bookmarks, key=lambda x: sort_key(x["title"]))
                    bookmarks_statuses = read_data(csv_bookmarks_status)

                    movie_path, tv_path = get_movie_tv_path()

                    print(f"\nRemoved files/directories:\n")
                    remove_rogue_empty(movie_path, tv_path, bookmarks_statuses)

                    if object_type_selected_prior == "MOVIE":
                        program_modify_message = f"{current_time()} INFO: {title_selected_prior} ({release_year_selected_prior}) | {object_type_selected_prior} removed/deleted"

                    elif object_type_selected_prior == "SHOW":
                        program_modify_message = f"{current_time()} INFO: {title_selected_prior} ({release_year_selected_prior}) | {object_type_selected_prior} and all episodes removed/deleted"
                    
                    else:
                        program_modify_message = f"{current_time()} ERROR: Invalid object_type"

                    entry_id_prior = None
                    title_selected_prior = None
                    release_year_selected_prior = None
                    object_type_selected_prior = None

            # Generates Stream Links for the program
            elif modify_programs_action == 'program_modify_generate':
                program_modify_message = generate_stream_links_single(entry_id_prior)

        elif modify_programs_action.startswith('program_modify_delete_episode_') or modify_programs_action in [
                                                                                                                'program_modify_add_episode',
                                                                                                                'program_modify_save'
                                                                                                              ]:
            edit_flag = True

            # Add an episode
            if modify_programs_action == 'program_modify_add_episode':
                program_modify_add_episode_season_input = request.form.get('program_modify_add_episode_season')
                program_modify_add_episode_episode_input = request.form.get('program_modify_add_episode_episode')
                program_modify_add_episode_episode_prefix_input = request.form.get('program_modify_add_episode_episode_prefix')
                program_modify_add_episode_stream_link_override_input = request.form.get('program_modify_add_episode_stream_link_override')

                new_season_episode_test = 0

                try:
                    new_episode_num = int(program_modify_add_episode_episode_input)
                    if new_episode_num >= 0:
                        new_season_episode_test = new_season_episode_test + 1
                    else:
                        program_modify_message = f"{current_time()} ERROR: For 'New Episode | Episode Number', please enter a valid numeric value."
                except ValueError:
                    program_modify_message = f"{current_time()} ERROR: Invalid input. For 'New Episode | Episode Number', please enter a numeric value."

                try:
                    new_season_num = int(program_modify_add_episode_season_input)
                    if new_season_num >= 0:
                        new_season_episode_test = new_season_episode_test + 1
                    else:
                        program_modify_message = f"{current_time()} ERROR: For 'New Episode | Season Number', please enter a valid numeric value."
                except ValueError:
                    program_modify_message = f"{current_time()} ERROR: Invalid input. For 'New Episode | Season Number', please enter a numeric value."

                if new_season_episode_test == 2:

                    formatted_season = f"S{new_season_num:02d}"
                    formatted_episode = f"E{new_episode_num:02d}"

                    new_season_episode = formatted_season + formatted_episode

                    new_season_episode_error = 0

                    for bookmark_status in bookmarks_statuses:
                        if bookmark_status['entry_id'] == entry_id_prior:
                            if bookmark_status['season_episode'] == new_season_episode:
                                new_season_episode_error = int(new_season_episode_error) + 1

                    if int(new_season_episode_error) > 0:
                        program_modify_message = f"{current_time()} WARNING: {new_season_episode} already exists. Try again."

                    else:
                        if program_modify_add_episode_episode_prefix_input == '':
                            new_episode_prefix = None
                        else:
                            new_episode_prefix = program_modify_add_episode_episode_prefix_input
                        
                        if program_modify_add_episode_stream_link_override_input == '':
                            new_stream_link = None
                        else:
                            new_stream_link = program_modify_add_episode_stream_link_override_input

                        new_row = {"entry_id": entry_id_prior, "season_episode_id": None, "season_episode_prefix": new_episode_prefix, "season_episode": new_season_episode, "status": "unwatched", "stream_link": None, "stream_link_override": new_stream_link, "stream_link_file": None}
                        append_data(csv_bookmarks_status, new_row)

            elif modify_programs_action.startswith('program_modify_delete_episode_') or modify_programs_action == 'program_modify_save':

                # Delete an episode
                if modify_programs_action.startswith('program_modify_delete_episode_'):
                    program_modify_delete_episode_index = int(modify_programs_action.split('_')[-1]) - 1

                    try:
                        if 0 <= int(program_modify_delete_episode_index) < len(bookmarks_statuses_selected_prior):
                            program_modify_delete_episode_entry_id = bookmarks_statuses_selected_prior[program_modify_delete_episode_index]['entry_id']
                            program_modify_delete_episode_season_episode = bookmarks_statuses_selected_prior[program_modify_delete_episode_index]['season_episode']

                            for bookmark_status in bookmarks_statuses:
                                if bookmark_status['entry_id'] == program_modify_delete_episode_entry_id and bookmark_status['season_episode'] == program_modify_delete_episode_season_episode:
                                    bookmarks_statuses.remove(bookmark_status)
                                    break

                            movie_path, tv_path = get_movie_tv_path()

                            print(f"\nRemoved files/directories:\n")
                            remove_rogue_empty(movie_path, tv_path, bookmarks_statuses)

                            program_modify_message = f"{current_time()} INFO: {program_modify_delete_episode_season_episode} deleted."

                        else:
                            program_modify_message = f"{current_time()} ERROR: Invalid selection for episode delete. Please choose a valid option."

                    except ValueError:
                        program_modify_message = f"{current_time()} ERROR: Invalid input for episode delete. Please enter a valid option."

                # Save modifcations
                elif modify_programs_action == 'program_modify_save':
                    # Modify Bookmarks
                    save_error_bookmarks = 0

                    release_year_test = get_release_year(field_release_year_input)
                    if release_year_test == "pass":
                        new_release_year = field_release_year_input
                    else:
                        program_modify_message = release_year_test
                        save_error_bookmarks = save_error_bookmarks + 1

                    if field_title_input != "":
                        new_title = field_title_input
                    else:
                        program_modify_message = f"{current_time()} ERROR: 'Title' cannot be empty."
                        save_error_bookmarks = save_error_bookmarks + 1

                    if save_error_bookmarks == 0:

                        title_selected_prior = new_title
                        release_year_selected_prior = new_release_year

                        program_modify_message = f"{current_time()} INFO: Save successful!"

                        for bookmark in bookmarks:
                            if bookmark["entry_id"] == entry_id_prior:
                                bookmark['title'] = new_title
                                bookmark['release_year'] = new_release_year

                        write_data(csv_bookmarks, bookmarks)
                        bookmarks = read_data(csv_bookmarks)
                        sorted_bookmarks = sorted(bookmarks, key=lambda x: sort_key(x["title"]))

                    # Modify Bookmarks Statuses
                    field_object_type_input = request.form.get('field_object_type')
                    field_status_inputs = {}
                    field_stream_link_override_inputs = {}
                    field_season_episode_inputs = {}
                    field_season_episode_prefix_inputs = {}

                    status_missing = True

                    for key in request.form.keys():
                        if key.startswith('field_status_'):
                            index = key.split('_')[-1]
                            field_status_inputs[index] = 'unwatched' if request.form.get(key) == 'on' else 'watched'
                            status_missing = None

                        if key.startswith('field_stream_link_override_'):
                            index = key.split('_')[-1]
                            if status_missing:
                                field_status_inputs[index] = 'watched'
                            field_stream_link_override_inputs[index] = request.form.get(key)

                        if field_object_type_input == 'SHOW':
                            if key.startswith('field_season_episode_'):
                                index = key.split('_')[-1]
                                field_season_episode_inputs[index] = request.form.get(key)

                            if key.startswith('field_episode_prefix_'):
                                index = key.split('_')[-1]
                                field_season_episode_prefix_inputs[index] = request.form.get(key)

                    if field_object_type_input == 'SHOW':
                        for index in field_season_episode_inputs.keys():
                            field_status_input = field_status_inputs.get(index)
                            field_stream_link_override_input = field_stream_link_override_inputs.get(index)
                            field_season_episode_input = field_season_episode_inputs.get(index)
                            field_season_episode_prefix_input = field_season_episode_prefix_inputs.get(index)

                            for bookmarks_status in bookmarks_statuses:
                                if bookmarks_status['entry_id'] == entry_id_prior and bookmarks_status['season_episode'] == field_season_episode_input:
                                    bookmarks_status['status'] = field_status_input
                                    bookmarks_status['stream_link_override'] = field_stream_link_override_input
                                    bookmarks_status['season_episode_prefix'] = field_season_episode_prefix_input

                    elif field_object_type_input == 'MOVIE':
                        for index in field_status_inputs.keys():
                            field_status_input = field_status_inputs.get(index)
                            field_stream_link_override_input = field_stream_link_override_inputs.get(index)

                            for bookmarks_status in bookmarks_statuses:
                                if bookmarks_status['entry_id'] == entry_id_prior:
                                    bookmarks_status['status'] = field_status_input
                                    bookmarks_status['stream_link_override'] = field_stream_link_override_input

                write_data(csv_bookmarks_status, bookmarks_statuses)

            bookmarks_statuses = read_data(csv_bookmarks_status)

            for bookmark_status in bookmarks_statuses:
                if bookmark_status['entry_id'] == entry_id_prior:
                    bookmarks_statuses_selected.append(bookmark_status)

            bookmarks_statuses_selected_sorted = sorted(bookmarks_statuses_selected, key=lambda x: x["season_episode"].casefold())
            bookmarks_statuses_selected_prior = bookmarks_statuses_selected_sorted

        # Cancel changes or finish
        elif modify_programs_action == 'program_modify_cancel':
            edit_flag = None
            entry_id_prior = None
            title_selected_prior = None
            release_year_selected_prior = None
            object_type_selected_prior = None
            bookmarks_statuses_selected_prior = []

    return render_template(
        'main/modifyprograms.html',
        segment = 'modifyprograms',
        html_slm_version = slm_version,
        html_sorted_bookmarks = sorted_bookmarks,
        html_entry_id_selected = entry_id_prior,
        html_program_modify_message = program_modify_message,
        html_edit_flag = edit_flag,
        html_title_selected = title_selected_prior,
        html_release_year_selected = release_year_selected_prior,
        html_object_type_selected = object_type_selected_prior,
        html_bookmarks_statuses_selected = bookmarks_statuses_selected_prior
    )

# Alphabetic sort ignoring common articles in various Latin script languages
def sort_key(title):
    articles = {
        "english": ["the", "a", "an"],
        "spanish": ["el", "la", "los", "las", "un", "una", "unos", "unas"],
        "portuguese": ["o", "a", "os", "as", "um", "uma", "uns", "umas"],
        "french": ["le", "la", "les", "un", "une", "des"],
        "german": ["der", "die", "das", "ein", "eine", "einen"],
        "italian": ["il", "lo", "la", "i", "gli", "le", "un", "una", "uno"],
        "bosnian": ["taj", "ta", "to", "jedan", "jedna", "jedno"],
        "catalan": ["el", "la", "els", "les", "un", "una", "uns", "unes"],
        "czech": ["ten", "ta", "to", "jeden", "jedna", "jedno"],
        "finnish": ["se", "yksi"],
        "croatian": ["taj", "ta", "to", "jedan", "jedna", "jedno"],
        "hungarian": ["a", "az", "egy"],
        "icelandic": ["það", "þessi", "einn", "ein", "eitt"],
        "maltese": ["il", "l-", "xi", "wieħed", "waħda"],
        "polish": ["ten", "ta", "to", "jeden", "jedna", "jedno"],
        "romanian": ["cel", "cea", "cei", "cele", "un", "o", "niște"],
        "slovak": ["ten", "tá", "to", "jeden", "jedna", "jedno"],
        "slovenian": ["ta", "ta", "to", "en", "ena", "eno"],
        "albanian": ["një", "një", "një"],
        "swahili": ["huyu", "hii", "hiki", "moja"],
        "turkish": ["bir"]
    }
    
    words = title.casefold().split()
    for lang, art_list in articles.items():
        if words[0] in art_list:
            return " ".join(words[1:])
    return title.casefold()

# Removes rows in a CSV file based upon a value in the first column
def remove_row_csv(csv_file, field_value):
    full_path_file = full_path(csv_file)

    try:
        # Read the CSV file
        with open(full_path_file, 'r', encoding='utf-8') as inp:
            reader = csv.reader(inp)
            print(f"\nIn {csv_file}, removed row:\n")

            rows_to_keep = []
            for row in reader:
                if row[0] == field_value:  # Assuming field_value is in the first column
                    print(f"    {row}")
                else:
                    rows_to_keep.append(row)

        # Write the non-matching rows back to the same file
        with open(full_path_file, 'w', encoding='utf-8', newline='') as out:
            writer = csv.writer(out)
            writer.writerows(rows_to_keep)

    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
    except Exception as e:
        print(f"Error: {e}")

# Files webpage
@app.route('/files', methods=['GET', 'POST'])
def webpage_files():
    table_html = None
    replace_message = None

    if request.method == 'POST':
        action = request.form['action']
        if action == 'view_settings':
            table_html = view_csv(csv_settings)
        elif action == 'export_settings':
            return export_csv(csv_settings)
        elif action == 'replace_settings':
            replace_message = replace_csv(csv_settings, 'file_settings')
        elif action == 'view_streaming_services':
            table_html = view_csv(csv_streaming_services)
        elif action == 'export_streaming_services':
            return export_csv(csv_streaming_services)
        elif action == 'replace_streaming_services':
            replace_message = replace_csv(csv_streaming_services, 'file_streaming_services')
        elif action == 'view_slmappings':
            table_html = view_csv(csv_slmappings)
        elif action == 'export_slmappings':
            return export_csv(csv_slmappings)
        elif action == 'replace_slmappings':
            replace_message = replace_csv(csv_slmappings, 'file_slmappings')
        elif action == 'view_bookmarks':
            table_html = view_csv(csv_bookmarks)
        elif action == 'export_bookmarks':
            return export_csv(csv_bookmarks)
        elif action == 'replace_bookmarks':
            replace_message = replace_csv(csv_bookmarks, 'file_bookmarks')
        elif action == 'view_bookmarks_statuses':
            table_html = view_csv(csv_bookmarks_status)
        elif action == 'export_bookmarks_statuses':
            return export_csv(csv_bookmarks_status)
        elif action == 'replace_bookmarks_statuses':
            replace_message = replace_csv(csv_bookmarks_status, 'file_bookmarks_statuses')

    return render_template(
        'main/files.html',
        segment='files',
        html_slm_version=slm_version,
        table_html=table_html,
        replace_message=replace_message
    )

# Makes CSV file able to be viewable in HTML
def view_csv(csv_file):
    data = read_data(csv_file)
    if data is None:
        return "Error reading data"
    
    if not data:
        return "No Data"
    
    headers = data[0].keys()
    table_html = '<table class="table table-striped"><thead><tr>'
    for header in headers:
        table_html += f'<th>{header}</th>'
    table_html += '</tr></thead><tbody>'
    
    if len(data) == 1 and all(not row for row in data):
        table_html += '<tr>' + ''.join(f'<td></td>' for _ in headers) + '</tr>'
    else:
        for row in data:
            table_html += '<tr>'
            for header in headers:
                table_html += f'<td>{row[header]}</td>'
            table_html += '</tr>'
    
    table_html += '</tbody></table>'
    
    return render_template_string(table_html)

# Exports a CSV file to the user's local disk
def export_csv(csv_file):
    return send_file(full_path(csv_file), as_attachment=True)

# Imports a file as a replacement
def replace_csv(csv_file, file_key):
    replace_message = None
    temp_upload = "temp_upload.csv"

    if file_key not in request.files:
        replace_message = "No file part"
 
    else:
        file = request.files[file_key]

        if file:
            file.save(full_path(temp_upload))
            os.replace(full_path(temp_upload), full_path(csv_file))
            replace_message = "File replaced successfully"

        else:
            replace_message = "No selected file"

    return replace_message

# Log file webpage
@app.route('/logs', methods=['GET', 'POST'])
def webpage_logs():
    lines_per_page = 10000

    # Read the file and get the total number of lines
    with open(log_filename_fullpath, 'r', encoding="utf-8") as file:
        lines = [line.rstrip('\n') for line in file]
    total_lines = len(lines)
    total_pages = (total_lines - 1) // lines_per_page + 1

    # Determine the current page
    if request.method == 'POST':
        page = int(request.form.get('page', 1))
    else:
        page = int(request.args.get('page', total_pages))

    action = request.form.get('action')

    if action == 'first':
        page = 1
    elif action == 'previous':
        page = max(1, page - 1)
    elif action == 'next':
        page = min(total_pages, page + 1)
    elif action == 'last':
        page = total_pages
    elif action == 'go':
        try:
            go_page = int(request.form.get('go_page'))
            page = max(1, min(total_pages, go_page))
        except (ValueError, TypeError):
            pass  # Ignore invalid input

    # Recalculate the start and end indices for the current page
    start_idx = (page - 1) * lines_per_page
    end_idx = start_idx + lines_per_page

    # Get the lines for the current page
    page_lines = lines[start_idx:end_idx]

    # Determine if there are previous or next pages
    has_previous = start_idx > 0
    has_next = end_idx < total_lines

    return render_template(
        'main/logs.html',
        segment='logs',
        html_slm_version=slm_version,
        html_log_filename_fullpath=log_filename_fullpath,
        html_page_lines=page_lines,
        html_page=page,
        html_has_previous=has_previous,
        html_has_next=has_next,
        total_pages=total_pages
    )

# Run Processes Webpage
@app.route('/runprocess', methods=['GET', 'POST'])
def webpage_runprocess():

    if request.method == 'POST':
        action = request.form['action']

        if action == 'end_to_end':
            end_to_end()
        elif action == 'backup_now':
            if os.path.exists(program_files_dir):
                create_backup(program_files_dir, backup_dir, max_backups)
        elif action == 'update_streaming_services':
            update_streaming_services()
        elif action == 'get_new_episodes':
            get_new_episodes()
        elif action == 'import_program_updates':
            import_program_updates()
        elif action == 'generate_stream_links':
            generate_stream_links()
        elif action == 'prune_scan_channels':
            prune_scan_channels()

    return render_template(
        'main/runprocess.html',
        segment = 'runprocess',
        html_slm_version = slm_version
    )

# Create a continous stream of the log file
@app.route('/stream_log')
def stream_log():
    def generate():
        with open(log_filename_fullpath, encoding="utf-8") as f:
            f.seek(0, 2)  # Move the cursor to the end of the file
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                yield f"data:{line}\n\n"
    return Response(generate(), mimetype='text/event-stream')

# Check for new episodes
def get_new_episodes():
    print("\n==========================================================")
    print("|                                                        |")
    print("|                 Check for New Episodes                 |")
    print("|                                                        |")
    print("==========================================================")

    print(f"\n{current_time()} Scanning for new episodes...\n")
    
    bookmarks = read_data(csv_bookmarks)
    show_bookmarks = [bookmark for bookmark in bookmarks if not bookmark['entry_id'].startswith('slm') and bookmark['object_type'] == "SHOW"]

    episodes = read_data(csv_bookmarks_status)

    for show_bookmark in show_bookmarks:
        existing_episodes = [episode for episode in episodes if show_bookmark['entry_id'] == episode['entry_id']]
        season_episodes = get_episode_list(show_bookmark['entry_id'], show_bookmark['url'], show_bookmark['country_code'], show_bookmark['language_code'])

        if season_episodes:
            for season_episode in season_episodes:
                if season_episode['season_episode'] not in [existing_episode['season_episode'] for existing_episode in existing_episodes]:
                    new_row = {"entry_id": show_bookmark['entry_id'], "season_episode_id": season_episode['season_episode_id'], "season_episode_prefix": None, "season_episode": season_episode['season_episode'], "status": "unwatched", "stream_link": None, "stream_link_override": None, "stream_link_file": None}
                    append_data(csv_bookmarks_status, new_row)
                    notification_add(f"    For {show_bookmark['title']} ({show_bookmark['release_year']}), added {season_episode['season_episode']}")
        else:
            notification_add(f"\n{current_time()} WARNING: No episodes found for {show_bookmark['title']} ({show_bookmark['release_year']}) | {show_bookmark['object_type']}.\n")

    print(f"\n{current_time()} Finished scanning for new episodes.\n")

# Searches JustWatch website to get the list of season/episode values
def get_episode_list(entry_id, url, country_code, language_code):
    season_episodes_results = []
    season_episodes_sorted = []

    _GRAPHQL_GetUrlTitleDetails = """
    query GetUrlTitleDetails(
        $fullPath: String!, 
        $country: Country!, 
        $language: Language!, 
        $episodeMaxLimit: Int, 
        $platform: Platform! = WEB, 
        $allowSponsoredRecommendations: SponsoredRecommendationsInput, 
        $format: ImageFormat, 
        $backdropProfile: BackdropProfile, 
        $streamingChartsFilter: StreamingChartsFilter
    ) {
    urlV2(fullPath: $fullPath) {
        id
        metaDescription
        metaKeywords
        metaRobots
        metaTitle
        heading1
        heading2
        htmlContent
        node {
        ...TitleDetails
        __typename
        }
        __typename
    }
    }

    fragment TitleDetails on Node {
    id
    __typename
    ... on MovieOrShowOrSeason {
        plexPlayerOffers: offers(
        country: $country
        platform: $platform
        filter: {packages: ["pxp"]}
        ) {
        id
        standardWebURL
        package {
            id
            packageId
            clearName
            technicalName
            shortName
            __typename
        }
        __typename
        }
        maxOfferUpdatedAt(country: $country, platform: WEB)
        appleOffers: offers(
        country: $country
        platform: $platform
        filter: {packages: ["atp", "itu"]}
        ) {
        ...TitleOffer
        __typename
        }
        disneyOffersCount: offerCount(
        country: $country
        platform: $platform
        filter: {packages: ["dnp"]}
        )
        starOffersCount: offerCount(
        country: $country
        platform: $platform
        filter: {packages: ["srp"]}
        )
        objectType
        objectId
        offerCount(country: $country, platform: $platform)
        offers(country: $country, platform: $platform) {
        monetizationType
        elementCount
        package {
            id
            packageId
            clearName
            __typename
        }
        __typename
        }
        watchNowOffer(country: $country, platform: $platform) {
        id
        standardWebURL
        __typename
        }
        promotedBundles(country: $country, platform: $platform) {
        promotionUrl
        __typename
        }
        availableTo(country: $country, platform: $platform) {
        availableCountDown(country: $country)
        availableToDate
        package {
            id
            shortName
            __typename
        }
        __typename
        }
        fallBackClips: content(country: "US", language: "en") {
        videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
        }
        dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
        }
        __typename
        }
        content(country: $country, language: $language) {
        backdrops {
            backdropUrl
            __typename
        }
        fullBackdrops: backdrops(profile: S1920, format: JPG) {
            backdropUrl
            __typename
        }
        clips {
            ...TrailerClips
            __typename
        }
        videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
        }
        dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
        }
        externalIds {
            imdbId
            __typename
        }
        fullPath
        genres {
            shortName
            __typename
        }
        posterUrl
        fullPosterUrl: posterUrl(profile: S718, format: JPG)
        runtime
        isReleased
        scoring {
            imdbScore
            imdbVotes
            tmdbPopularity
            tmdbScore
            jwRating
            __typename
        }
        shortDescription
        title
        originalReleaseYear
        originalReleaseDate
        upcomingReleases(releaseTypes: DIGITAL) {
            releaseCountDown(country: $country)
            releaseDate
            label
            package {
            id
            packageId
            shortName
            clearName
            __typename
            }
            __typename
        }
        ... on MovieOrShowContent {
            originalTitle
            ageCertification
            credits {
            role
            name
            characterName
            personId
            __typename
            }
            interactions {
            dislikelistAdditions
            likelistAdditions
            votesNumber
            __typename
            }
            productionCountries
            __typename
        }
        ... on SeasonContent {
            seasonNumber
            interactions {
            dislikelistAdditions
            likelistAdditions
            votesNumber
            __typename
            }
            __typename
        }
        __typename
        }
        popularityRank(country: $country) {
        rank
        trend
        trendDifference
        __typename
        }
        streamingCharts(country: $country, filter: $streamingChartsFilter) {
        edges {
            streamingChartInfo {
            rank
            trend
            trendDifference
            updatedAt
            daysInTop10
            daysInTop100
            daysInTop1000
            daysInTop3
            topRank
            __typename
            }
            __typename
        }
        __typename
        }
        __typename
    }
    ... on MovieOrShow {
        watchlistEntryV2 {
        createdAt
        __typename
        }
        likelistEntry {
        createdAt
        __typename
        }
        dislikelistEntry {
        createdAt
        __typename
        }
        customlistEntries {
        createdAt
        genericTitleList {
            id
            __typename
        }
        __typename
        }
        similarTitlesV2(
        country: $country
        allowSponsoredRecommendations: $allowSponsoredRecommendations
        ) {
        sponsoredAd {
            ...SponsoredAd
            __typename
        }
        __typename
        }
        __typename
    }
    ... on Movie {
        permanentAudiences
        seenlistEntry {
        createdAt
        __typename
        }
        __typename
    }
    ... on Show {
        permanentAudiences
        totalSeasonCount
        seenState(country: $country) {
        progress
        seenEpisodeCount
        __typename
        }
        tvShowTrackingEntry {
        createdAt
        __typename
        }
        seasons(sortDirection: DESC) {
        id
        objectId
        objectType
        totalEpisodeCount
        availableTo(country: $country, platform: $platform) {
            availableToDate
            availableCountDown(country: $country)
            package {
            id
            shortName
            __typename
            }
            __typename
        }
        content(country: $country, language: $language) {
            posterUrl
            seasonNumber
            fullPath
            title
            upcomingReleases(releaseTypes: DIGITAL) {
            releaseDate
            releaseCountDown(country: $country)
            package {
                id
                shortName
                __typename
            }
            __typename
            }
            isReleased
            originalReleaseYear
            __typename
        }
        show {
            id
            objectId
            objectType
            watchlistEntryV2 {
            createdAt
            __typename
            }
            content(country: $country, language: $language) {
            title
            __typename
            }
            __typename
        }
        __typename
        }
        recentEpisodes: episodes(
        sortDirection: DESC
        limit: 3
        releasedInCountry: $country
        ) {
        ...Episode
        __typename
        }
        __typename
    }
    ... on Season {
        totalEpisodeCount
        episodes(limit: $episodeMaxLimit) {
        ...Episode
        __typename
        }
        show {
        id
        objectId
        objectType
        totalSeasonCount
        customlistEntries {
            createdAt
            genericTitleList {
            id
            __typename
            }
            __typename
        }
        tvShowTrackingEntry {
            createdAt
            __typename
        }
        fallBackClips: content(country: "US", language: "en") {
            videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
            }
            dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
            }
            __typename
        }
        content(country: $country, language: $language) {
            title
            ageCertification
            fullPath
            genres {
            shortName
            __typename
            }
            credits {
            role
            name
            characterName
            personId
            __typename
            }
            productionCountries
            externalIds {
            imdbId
            __typename
            }
            upcomingReleases(releaseTypes: DIGITAL) {
            releaseDate
            __typename
            }
            backdrops {
            backdropUrl
            __typename
            }
            posterUrl
            isReleased
            videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
            }
            dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
            }
            __typename
        }
        seenState(country: $country) {
            progress
            __typename
        }
        watchlistEntryV2 {
            createdAt
            __typename
        }
        dislikelistEntry {
            createdAt
            __typename
        }
        likelistEntry {
            createdAt
            __typename
        }
        similarTitlesV2(
            country: $country
            allowSponsoredRecommendations: $allowSponsoredRecommendations
        ) {
            sponsoredAd {
            ...SponsoredAd
            __typename
            }
            __typename
        }
        __typename
        }
        seenState(country: $country) {
        progress
        __typename
        }
        __typename
    }
    }

    fragment TitleOffer on Offer {
    id
    presentationType
    monetizationType
    retailPrice(language: $language)
    retailPriceValue
    currency
    lastChangeRetailPriceValue
    type
    package {
        id
        packageId
        clearName
        technicalName
        icon(profile: S100)
        __typename
    }
    standardWebURL
    elementCount
    availableTo
    deeplinkRoku: deeplinkURL(platform: ROKU_OS)
    subtitleLanguages
    videoTechnology
    audioTechnology
    audioLanguages
    __typename
    }

    fragment TrailerClips on Clip {
    sourceUrl
    externalId
    provider
    name
    __typename
    }

    fragment SponsoredAd on SponsoredRecommendationAd {
    bidId
    holdoutGroup
    campaign {
        name
        externalTrackers {
        type
        data
        __typename
        }
        hideRatings
        hideDetailPageButton
        promotionalImageUrl
        promotionalVideo {
        url
        __typename
        }
        promotionalTitle
        promotionalText
        promotionalProviderLogo
        watchNowLabel
        watchNowOffer {
        standardWebURL
        presentationType
        monetizationType
        package {
            id
            packageId
            shortName
            clearName
            icon
            __typename
        }
        __typename
        }
        nodeOverrides {
        nodeId
        promotionalImageUrl
        watchNowOffer {
            standardWebURL
            __typename
        }
        __typename
        }
        node {
        nodeId: id
        __typename
        ... on MovieOrShowOrSeason {
            content(country: $country, language: $language) {
            fullPath
            posterUrl
            title
            originalReleaseYear
            scoring {
                imdbScore
                __typename
            }
            externalIds {
                imdbId
                __typename
            }
            backdrops(format: $format, profile: $backdropProfile) {
                backdropUrl
                __typename
            }
            isReleased
            __typename
            }
            objectId
            objectType
            offers(country: $country, platform: $platform) {
            monetizationType
            presentationType
            package {
                id
                packageId
                __typename
            }
            id
            __typename
            }
            __typename
        }
        ... on MovieOrShow {
            watchlistEntryV2 {
            createdAt
            __typename
            }
            __typename
        }
        ... on Show {
            seenState(country: $country) {
            seenEpisodeCount
            __typename
            }
            __typename
        }
        ... on Season {
            content(country: $country, language: $language) {
            seasonNumber
            __typename
            }
            show {
            __typename
            id
            content(country: $country, language: $language) {
                originalTitle
                __typename
            }
            watchlistEntryV2 {
                createdAt
                __typename
            }
            }
            __typename
        }
        ... on GenericTitleList {
            followedlistEntry {
            createdAt
            name
            __typename
            }
            id
            type
            content(country: $country, language: $language) {
            name
            visibility
            __typename
            }
            titles(country: $country, first: 40) {
            totalCount
            edges {
                cursor
                node: nodeV2 {
                content(country: $country, language: $language) {
                    fullPath
                    posterUrl
                    title
                    originalReleaseYear
                    scoring {
                    imdbScore
                    __typename
                    }
                    isReleased
                    __typename
                }
                id
                objectId
                objectType
                __typename
                }
                __typename
            }
            __typename
            }
            __typename
        }
        }
        __typename
    }
    __typename
    }

    fragment Episode on Episode {
    id
    objectId
    seenlistEntry {
        createdAt
        __typename
    }
    content(country: $country, language: $language) {
        title
        shortDescription
        episodeNumber
        seasonNumber
        isReleased
        upcomingReleases {
        releaseDate
        label
        package {
            id
            packageId
            __typename
        }
        __typename
        }
        __typename
    }
    __typename
    }
    """

    _GRAPHQL_GetNodeTitleDetails = """
    query GetNodeTitleDetails($entityId: ID!, $country: Country!, $language: Language!, $episodeMaxLimit: Int, $platform: Platform! = WEB, $allowSponsoredRecommendations: SponsoredRecommendationsInput, $format: ImageFormat, $backdropProfile: BackdropProfile, $streamingChartsFilter: StreamingChartsFilter) {
    node(id: $entityId) {
        ... on Url {
        metaDescription
        metaKeywords
        metaRobots
        metaTitle
        heading1
        heading2
        htmlContent
        __typename
        }
        ...TitleDetails
        __typename
    }
    }

    fragment TitleDetails on Node {
    id
    __typename
    ... on MovieOrShowOrSeason {
        plexPlayerOffers: offers(
        country: $country
        platform: $platform
        filter: {packages: ["pxp"]}
        ) {
        id
        standardWebURL
        package {
            id
            packageId
            clearName
            technicalName
            shortName
            __typename
        }
        __typename
        }
        maxOfferUpdatedAt(country: $country, platform: WEB)
        appleOffers: offers(
        country: $country
        platform: $platform
        filter: {packages: ["atp", "itu"]}
        ) {
        ...TitleOffer
        __typename
        }
        disneyOffersCount: offerCount(
        country: $country
        platform: $platform
        filter: {packages: ["dnp"]}
        )
        starOffersCount: offerCount(
        country: $country
        platform: $platform
        filter: {packages: ["srp"]}
        )
        objectType
        objectId
        offerCount(country: $country, platform: $platform)
        uniqueOfferCount: offerCount(
        country: $country
        platform: $platform
        filter: {bestOnly: true}
        )
        offers(country: $country, platform: $platform) {
        monetizationType
        elementCount
        package {
            id
            packageId
            clearName
            __typename
        }
        __typename
        }
        watchNowOffer(country: $country, platform: $platform) {
        id
        standardWebURL
        __typename
        }
        promotedBundles(country: $country, platform: $platform) {
        promotionUrl
        __typename
        }
        availableTo(country: $country, platform: $platform) {
        availableCountDown(country: $country)
        availableToDate
        package {
            id
            shortName
            __typename
        }
        __typename
        }
        fallBackClips: content(country: "US", language: "en") {
        videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
        }
        dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
        }
        __typename
        }
        content(country: $country, language: $language) {
        backdrops {
            backdropUrl
            __typename
        }
        fullBackdrops: backdrops(profile: S1920, format: JPG) {
            backdropUrl
            __typename
        }
        clips {
            ...TrailerClips
            __typename
        }
        videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
        }
        dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
        }
        externalIds {
            imdbId
            __typename
        }
        fullPath
        posterUrl
        fullPosterUrl: posterUrl(profile: S718, format: JPG)
        runtime
        isReleased
        scoring {
            imdbScore
            imdbVotes
            tmdbPopularity
            tmdbScore
            jwRating
            __typename
        }
        shortDescription
        title
        originalReleaseYear
        originalReleaseDate
        upcomingReleases(releaseTypes: DIGITAL) {
            releaseCountDown(country: $country)
            releaseDate
            label
            package {
            id
            packageId
            shortName
            clearName
            icon(profile: S100)
            hasRectangularIcon(country: $country, platform: WEB)
            __typename
            }
            __typename
        }
        genres {
            shortName
            translation(language: $language)
            __typename
        }
        subgenres {
            content(country: $country, language: $language) {
            shortName
            name
            __typename
            }
            __typename
        }
        ... on MovieContent {
            subgenres {
            content(country: $country, language: $language) {
                url: moviesUrl {
                fullPath
                __typename
                }
                __typename
            }
            __typename
            }
            __typename
        }
        ... on ShowContent {
            subgenres {
            content(country: $country, language: $language) {
                url: showsUrl {
                fullPath
                __typename
                }
                __typename
            }
            __typename
            }
            __typename
        }
        ... on SeasonContent {
            subgenres {
            content(country: $country, language: $language) {
                url: showsUrl {
                fullPath
                __typename
                }
                __typename
            }
            __typename
            }
            __typename
        }
        ... on MovieOrShowContent {
            originalTitle
            ageCertification
            credits {
            role
            name
            characterName
            personId
            __typename
            }
            interactions {
            dislikelistAdditions
            likelistAdditions
            votesNumber
            __typename
            }
            productionCountries
            __typename
        }
        ... on SeasonContent {
            seasonNumber
            interactions {
            dislikelistAdditions
            likelistAdditions
            votesNumber
            __typename
            }
            __typename
        }
        __typename
        }
        popularityRank(country: $country) {
        rank
        trend
        trendDifference
        __typename
        }
        streamingCharts(country: $country, filter: $streamingChartsFilter) {
        edges {
            streamingChartInfo {
            rank
            trend
            trendDifference
            updatedAt
            daysInTop10
            daysInTop100
            daysInTop1000
            daysInTop3
            topRank
            __typename
            }
            __typename
        }
        __typename
        }
        __typename
    }
    ... on MovieOrShow {
        watchlistEntryV2 {
        createdAt
        __typename
        }
        likelistEntry {
        createdAt
        __typename
        }
        dislikelistEntry {
        createdAt
        __typename
        }
        customlistEntries {
        createdAt
        genericTitleList {
            id
            __typename
        }
        __typename
        }
        similarTitlesV2(
        country: $country
        allowSponsoredRecommendations: $allowSponsoredRecommendations
        ) {
        sponsoredAd {
            ...SponsoredAd
            __typename
        }
        __typename
        }
        __typename
    }
    ... on Movie {
        permanentAudiences
        seenlistEntry {
        createdAt
        __typename
        }
        __typename
    }
    ... on Show {
        permanentAudiences
        totalSeasonCount
        seenState(country: $country) {
        progress
        seenEpisodeCount
        __typename
        }
        tvShowTrackingEntry {
        createdAt
        __typename
        }
        seasons(sortDirection: DESC) {
        id
        objectId
        objectType
        totalEpisodeCount
        availableTo(country: $country, platform: $platform) {
            availableToDate
            availableCountDown(country: $country)
            package {
            id
            shortName
            __typename
            }
            __typename
        }
        content(country: $country, language: $language) {
            posterUrl
            seasonNumber
            fullPath
            title
            upcomingReleases(releaseTypes: DIGITAL) {
            releaseDate
            releaseCountDown(country: $country)
            package {
                id
                shortName
                __typename
            }
            __typename
            }
            isReleased
            originalReleaseYear
            __typename
        }
        show {
            id
            objectId
            objectType
            watchlistEntryV2 {
            createdAt
            __typename
            }
            content(country: $country, language: $language) {
            title
            __typename
            }
            __typename
        }
        fallBackClips: content(country: "US", language: "en") {
            videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
            }
            dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
            }
            __typename
        }
        __typename
        }
        recentEpisodes: episodes(
        sortDirection: DESC
        limit: 3
        releasedInCountry: $country
        ) {
        ...Episode
        __typename
        }
        __typename
    }
    ... on Season {
        totalEpisodeCount
        episodes(limit: $episodeMaxLimit) {
        ...Episode
        __typename
        }
        show {
        id
        objectId
        objectType
        totalSeasonCount
        customlistEntries {
            createdAt
            genericTitleList {
            id
            __typename
            }
            __typename
        }
        tvShowTrackingEntry {
            createdAt
            __typename
        }
        fallBackClips: content(country: "US", language: "en") {
            videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
            }
            dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
            }
            __typename
        }
        content(country: $country, language: $language) {
            title
            ageCertification
            fullPath
            genres {
            shortName
            __typename
            }
            credits {
            role
            name
            characterName
            personId
            __typename
            }
            productionCountries
            externalIds {
            imdbId
            __typename
            }
            upcomingReleases(releaseTypes: DIGITAL) {
            releaseDate
            __typename
            }
            backdrops {
            backdropUrl
            __typename
            }
            posterUrl
            isReleased
            videobusterClips: clips(providers: [VIDEOBUSTER]) {
            ...TrailerClips
            __typename
            }
            dailymotionClips: clips(providers: [DAILYMOTION]) {
            ...TrailerClips
            __typename
            }
            __typename
        }
        seenState(country: $country) {
            progress
            __typename
        }
        watchlistEntryV2 {
            createdAt
            __typename
        }
        dislikelistEntry {
            createdAt
            __typename
        }
        likelistEntry {
            createdAt
            __typename
        }
        similarTitlesV2(
            country: $country
            allowSponsoredRecommendations: $allowSponsoredRecommendations
        ) {
            sponsoredAd {
            ...SponsoredAd
            __typename
            }
            __typename
        }
        __typename
        }
        seenState(country: $country) {
        progress
        __typename
        }
        __typename
    }
    }

    fragment TitleOffer on Offer {
    id
    presentationType
    monetizationType
    retailPrice(language: $language)
    retailPriceValue
    currency
    lastChangeRetailPriceValue
    type
    package {
        id
        packageId
        clearName
        technicalName
        icon(profile: S100)
        planOffers(country: $country, platform: WEB) {
        title
        retailPrice(language: $language)
        isTrial
        durationDays
        __typename
        }
        hasRectangularIcon(country: $country, platform: WEB)
        __typename
    }
    standardWebURL
    elementCount
    availableTo
    deeplinkRoku: deeplinkURL(platform: ROKU_OS)
    subtitleLanguages
    videoTechnology
    audioTechnology
    audioLanguages(language: $language)
    __typename
    }

    fragment TrailerClips on Clip {
    sourceUrl
    externalId
    provider
    name
    __typename
    }

    fragment SponsoredAd on SponsoredRecommendationAd {
    bidId
    holdoutGroup
    campaign {
        name
        externalTrackers {
        type
        data
        __typename
        }
        hideRatings
        hideDetailPageButton
        promotionalImageUrl
        promotionalVideo {
        url
        __typename
        }
        promotionalTitle
        promotionalText
        promotionalProviderLogo
        watchNowLabel
        watchNowOffer {
        standardWebURL
        presentationType
        monetizationType
        package {
            id
            packageId
            shortName
            clearName
            icon
            __typename
        }
        __typename
        }
        nodeOverrides {
        nodeId
        promotionalImageUrl
        watchNowOffer {
            standardWebURL
            __typename
        }
        __typename
        }
        node {
        nodeId: id
        __typename
        ... on MovieOrShowOrSeason {
            content(country: $country, language: $language) {
            fullPath
            posterUrl
            title
            originalReleaseYear
            scoring {
                imdbScore
                __typename
            }
            externalIds {
                imdbId
                __typename
            }
            backdrops(format: $format, profile: $backdropProfile) {
                backdropUrl
                __typename
            }
            isReleased
            __typename
            }
            objectId
            objectType
            offers(country: $country, platform: $platform) {
            monetizationType
            presentationType
            package {
                id
                packageId
                __typename
            }
            id
            __typename
            }
            __typename
        }
        ... on MovieOrShow {
            watchlistEntryV2 {
            createdAt
            __typename
            }
            __typename
        }
        ... on Show {
            seenState(country: $country) {
            seenEpisodeCount
            __typename
            }
            __typename
        }
        ... on Season {
            content(country: $country, language: $language) {
            seasonNumber
            __typename
            }
            show {
            __typename
            id
            content(country: $country, language: $language) {
                originalTitle
                __typename
            }
            watchlistEntryV2 {
                createdAt
                __typename
            }
            }
            __typename
        }
        ... on GenericTitleList {
            followedlistEntry {
            createdAt
            name
            __typename
            }
            id
            type
            content(country: $country, language: $language) {
            name
            visibility
            __typename
            }
            titles(country: $country, first: 40) {
            totalCount
            edges {
                cursor
                node: nodeV2 {
                content(country: $country, language: $language) {
                    fullPath
                    posterUrl
                    title
                    originalReleaseYear
                    scoring {
                    imdbScore
                    __typename
                    }
                    isReleased
                    __typename
                }
                id
                objectId
                objectType
                __typename
                }
                __typename
            }
            __typename
            }
            __typename
        }
        }
        __typename
    }
    __typename
    }

    fragment Episode on Episode {
    id
    objectId
    seenlistEntry {
        createdAt
        __typename
    }
    content(country: $country, language: $language) {
        title
        shortDescription
        episodeNumber
        seasonNumber
        isReleased
        runtime
        upcomingReleases {
        releaseDate
        label
        package {
            id
            packageId
            __typename
        }
        __typename
        }
        __typename
    }
    __typename
    }
    """

    seasons = get_season_list(entry_id, url, country_code, language_code, _GRAPHQL_GetUrlTitleDetails, _GRAPHQL_GetNodeTitleDetails)

    if seasons:
        for season in seasons:
            if url is not None and url != '' and season.startswith('http'):
                full_href = season

                json_data = {
                    'query': _GRAPHQL_GetUrlTitleDetails,
                    'variables': {
                        "platform": "WEB",
                        "fullPath": full_href,
                        "language": language_code,
                        "country": country_code,
                        "episodeMaxLimit": 999,
                        "allowSponsoredRecommendations": {
                            "pageType": "VIEW_TITLE_DETAIL",
                            "placement": "DETAIL_PAGE",
                            "country": country_code,
                            "language": language_code,
                            "appId": "3.8.2-webapp#de387c7",
                            "platform": "WEB",
                            "supportedFormats": [
                            "IMAGE",
                            "VIDEO"
                            ],
                            "supportedObjectTypes": [
                            "MOVIE",
                            "SHOW",
                            "GENERIC_TITLE_LIST",
                            "SHOW_SEASON"
                            ],
                            "testingMode": False,
                            "testingModeCampaignName": None
                        }
                    },
                    'operationName': 'GetUrlTitleDetails',
                }

            else:
                season_id = season

                json_data = {
                    'query': _GRAPHQL_GetNodeTitleDetails,
                    'variables': {
                        "platform": "WEB",
                        "fullPath": "/",
                        "entityId": season_id,
                        "language": language_code,
                        "country": country_code,
                        "episodeMaxLimit": 999,
                        "allowSponsoredRecommendations": {
                            "pageType": "VIEW_TITLE_DETAIL",
                            "placement": "DETAIL_PAGE",
                            "language": language_code,
                            "country": country_code,
                            "appId": "3.8.2-webapp#b19435c",
                            "platform": "WEB",
                            "supportedFormats": [
                                "IMAGE",
                                "VIDEO"
                            ],
                            "supportedObjectTypes": [
                                "MOVIE",
                                "SHOW",
                                "GENERIC_TITLE_LIST",
                                "SHOW_SEASON"
                            ],
                            "testingMode": False,
                            "testingModeCampaignName": None
                        }
                    },
                    'operationName': 'GetNodeTitleDetails',
                }

            try:
                season_episodes_base = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
                season_episodes_json = season_episodes_base.json()
                if url is not None and url != '' and season.startswith('http'):
                    season_episodes_json_episodes_array = season_episodes_json["data"]["urlV2"]["node"]["episodes"]
                else:
                    season_episodes_json_episodes_array = season_episodes_json["data"]["node"]["episodes"]

                # Get maxium digits for Season/Episode number length
                max_digits_season = 0
                max_digits_episode = 0

                for season_episode in season_episodes_json_episodes_array:
                    season_number_digit = int(season_episode["content"]["seasonNumber"])
                    episode_number_digit = int(season_episode["content"]["episodeNumber"])

                    digits_season = len(str(season_number_digit))
                    digits_episode = len(str(episode_number_digit))

                    max_digits_season = max(max_digits_season, digits_season)
                    max_digits_episode = max(max_digits_episode, digits_episode)

                max_digits_season = max(max_digits_season, 2)
                max_digits_episode = max(max_digits_episode, 2)

                for season_episode in season_episodes_json_episodes_array:
                    season_episode_id = season_episode["id"]
                    season_number = int(season_episode["content"]["seasonNumber"])
                    episode_number = int(season_episode["content"]["episodeNumber"])
                    formatted_season = f"{season_number:0{max_digits_season}d}"
                    formatted_episode = f"{episode_number:0{max_digits_episode}d}"
                    season_episode = f"S{formatted_season}E{formatted_episode}"
                    season_episodes_results.append({"season_episode_id": season_episode_id, "season_episode": season_episode})

                season_episodes_sorted = sorted(season_episodes_results, key=lambda d: d['season_episode'])

            except requests.RequestException as e:
                print(f"\n{current_time()} WARNING: {e}. Skipping, please try again. (entry_id: {entry_id})")
            except KeyError as e:
                print(f"\n{current_time()} WARNING: Missing key {e}. Skipping, please try again. (entry_id: {entry_id})")
            except Exception as e:
                print(f"\n{current_time()} WARNING: An unexpected error occurred: {e}. Skipping, please try again. (entry_id: {entry_id})")

    return season_episodes_sorted

# Get a list of seasons for TV Shows   
def get_season_list(entry_id, url, country_code, language_code, _GRAPHQL_GetUrlTitleDetails, _GRAPHQL_GetNodeTitleDetails):
    season_list = []
    season_list_json = []
    season_list_json_array = []
    season_list_json_array_results = []

    if url is not None and url != '':
        json_data = {
            'query': _GRAPHQL_GetUrlTitleDetails,
            'variables': {
                "platform": "WEB",
                "fullPath": url,
                "language": language_code,
                "country": country_code,
                "episodeMaxLimit": 999,
                "allowSponsoredRecommendations": {
                    "pageType": "VIEW_TITLE_DETAIL",
                    "placement": "DETAIL_PAGE",
                    "country": country_code,
                    "language": language_code,
                    "appId": "3.8.2-webapp#de387c7",
                    "platform": "WEB",
                    "supportedFormats": [
                    "IMAGE",
                    "VIDEO"
                    ],
                    "supportedObjectTypes": [
                    "MOVIE",
                    "SHOW",
                    "GENERIC_TITLE_LIST",
                    "SHOW_SEASON"
                    ],
                    "testingMode": False,
                    "testingModeCampaignName": None
                }
            },
            'operationName': 'GetUrlTitleDetails',
        }

    else:
        json_data = {
            'query': _GRAPHQL_GetNodeTitleDetails,
            'variables': {
                "platform": "WEB",
                "fullPath": "/",
                "entityId": entry_id,
                "language": language_code,
                "country": country_code,
                "episodeMaxLimit": 999,
                "allowSponsoredRecommendations": {
                    "pageType": "VIEW_TITLE_DETAIL",
                    "placement": "DETAIL_PAGE",
                    "language": language_code,
                    "country": country_code,
                    "appId": "3.8.2-webapp#b19435c",
                    "platform": "WEB",
                    "supportedFormats": [
                        "IMAGE",
                        "VIDEO"
                    ],
                    "supportedObjectTypes": [
                        "MOVIE",
                        "SHOW",
                        "GENERIC_TITLE_LIST",
                        "SHOW_SEASON"
                    ],
                    "testingMode": False,
                    "testingModeCampaignName": None
                }
            },
            'operationName': 'GetNodeTitleDetails',
        }

    try:
        season_list = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
    except requests.RequestException as e:
        print(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")

    if season_list:
        season_list_json = season_list.json()
        if url is not None and url != '':
            season_list_json_array = season_list_json["data"]["urlV2"]["node"]["seasons"]
        else:
            season_list_json_array = season_list_json["data"]["node"]["seasons"]

        for season in season_list_json_array:
            if url is not None and url != '':
                if season["content"]["fullPath"] is not None and season["content"]["fullPath"] !='':
                    href = season["content"]["fullPath"]
                    full_href = f"{engine_url}{href}"
                    season_list_json_array_results.append(full_href)
                else:
                    season_id = season["id"]
                    season_list_json_array_results.append(season_id)                    
            else:
                season_id = season["id"]
                season_list_json_array_results.append(season_id)

    return season_list_json_array_results

# Import program updates from Channels
def import_program_updates():
    print("\n==========================================================")
    print("|                                                        |")
    print("|         Import Program Updates from Channels           |")
    print("|                                                        |")
    print("==========================================================")

    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]
    bookmarks_statuses = read_data(csv_bookmarks_status)

    run_import = None

    if not os.path.exists(channels_directory):
        notification_add(f"\n{current_time()} WARNING: {channels_directory} does not exist, skipping import. Please change the Channels directory in the Settings menu.\n")
    else:
        run_import = True
        
    if run_import:
        print(f"\n{current_time()} Checking for removed Stream Links...\n")

        for bookmark_status in bookmarks_statuses:
            stream_link_file_raw = normalize_path(bookmark_status['stream_link_file'])

            if stream_link_file_raw != "":
                normalized_path = stream_link_file_raw.lower()
                pattern = re.compile(r"[\\/]+imports[\\/]+")
                match = pattern.search(normalized_path)
                split_index = match.start() if match else -1
                stream_link_file_channels_path = stream_link_file_raw[:split_index]
                stream_link_file_relative_path = stream_link_file_raw[split_index:]
                
                if stream_link_file_channels_path.lower() == channels_directory.lower():
                    stream_link_file = stream_link_file_raw
                else:
                    stream_link_file = f"{channels_directory}{stream_link_file_relative_path}"
                
                if not os.path.exists(stream_link_file):
                    bookmark_status['status'] = "watched"
                    bookmark_status['stream_link_file'] = None
                    notification_add(f"    REMOVED: {stream_link_file}")

        write_data(csv_bookmarks_status, bookmarks_statuses)

        print(f"\n{current_time()} Finished checking for removed Stream Links.\n")

# Find if a stream link is available for bookmakred programs, create stream link files if true, remove files if false
def generate_stream_links():
    print("\n==========================================================")
    print("|                                                        |")
    print("|                  Generate Stream Links                 |")
    print("|                                                        |")
    print("==========================================================")

    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]
    bookmarks = read_data(csv_bookmarks)
    auto_bookmarks = [bookmark for bookmark in bookmarks if not bookmark['entry_id'].startswith('slm')]

    run_generation = None

    if not os.path.exists(channels_directory):
        notification_add(f"\n{current_time()} WARNING: {channels_directory} does not exist, skipping generation. Please change the Channels directory in the Settings menu.\n")
    else:
        run_generation = True
        
    if run_generation:
        print(f"\n{current_time()} START: Generating Stream Links...")

        print(f"\n{current_time()} Getting Stream Links...\n")
        find_stream_links(auto_bookmarks)
        print(f"\n{current_time()} Finished getting Stream Links.")

        print(f"\n{current_time()} Checking for changes from last run...\n")
        get_stream_link_ids()
        print(f"\n{current_time()} Finished checking for changes from last run.\n")

        print(f"\n{current_time()} Creating and removing Stream Link files and directories...\n")
        create_stream_link_files(bookmarks, True)
        print(f"\n{current_time()} Finished creating and removing Stream Link files and directories.")

        print(f"\n{current_time()} END: Finished Generating Stream Links.\n")

# Get the valid Stream Links (if available) and write to the appropriate table
def find_stream_links(auto_bookmarks):
    bookmarks_statuses = read_data(csv_bookmarks_status)

    for auto_bookmark in auto_bookmarks:

        for bookmarks_status in bookmarks_statuses:

            if auto_bookmark['entry_id'] == bookmarks_status['entry_id']:

                stream_link_dirty = None
                stream_link_reason = None
        
                if bookmarks_status['status'].lower() == "unwatched":

                    if bookmarks_status['stream_link_override'] != "":

                        stream_link_dirty = "https://skipped_for_override"

                    else:

                        for attempt in range(3):  # Limit retries to 3 attempts
                            try:

                                if auto_bookmark['object_type'] == "MOVIE":
                                    node_id = bookmarks_status['entry_id']
                                elif auto_bookmark['object_type'] == "SHOW":
                                    node_id = bookmarks_status['season_episode_id']
                                else:
                                    print(f"\n{current_time()} ERROR: Invalid object_type\n")

                                stream_link_details = get_offers(node_id, auto_bookmark['country_code'], auto_bookmark['language_code'])
                                stream_link_offers = extract_offer_info(stream_link_details)
                                stream_link_dirty = get_stream_link(stream_link_offers)

                                if stream_link_dirty is None or stream_link_dirty == '':
                                    stream_link_reason = "None due to not found on your selected streaming services"

                                break  # Break out of the retry loop if successful
                            
                            except Exception as e:
                                print(f"\n{current_time()} ERROR: {e}. Retrying...\n")

                        else:
                            print(f"\n{current_time()} ERROR: Could not find Stream Link after 3 attempts.")
                            if bookmarks_status['stream_link'] != "":
                                print(f"{current_time()} INFO: Assigning prior Stream Link.\n")
                                stream_link_dirty = bookmarks_status['stream_link']
                            else:
                                print(f"{current_time()} INFO: No prior Stream Link to assign. Try again later.\n")
                            pass

                else:

                    stream_link_reason = "None due to 'Watched' status"

                stream_link = clean_stream_link(stream_link_dirty, auto_bookmark['object_type'])

                bookmarks_status['stream_link'] = stream_link

                if auto_bookmark['object_type'] == "MOVIE":
                    if stream_link_reason:
                        print(f"    {auto_bookmark['title']} ({auto_bookmark['release_year']}) assigned Stream Link: {stream_link_reason}")
                    else:
                        print(f"    {auto_bookmark['title']} ({auto_bookmark['release_year']}) assigned Stream Link: {stream_link}")
                elif auto_bookmark['object_type'] == "SHOW":
                    if stream_link_reason:
                        if bookmarks_status['season_episode_prefix'] != "":
                            print(f"    {auto_bookmark['title']} ({auto_bookmark['release_year']}) | {bookmarks_status['season_episode_prefix']} {bookmarks_status['season_episode']} assigned Stream Link: {stream_link_reason}")
                        else:
                            print(f"    {auto_bookmark['title']} ({auto_bookmark['release_year']}) | {bookmarks_status['season_episode']} assigned Stream Link: {stream_link_reason}")
                    else:
                        if bookmarks_status['season_episode_prefix'] != "":
                            print(f"    {auto_bookmark['title']} ({auto_bookmark['release_year']}) | {bookmarks_status['season_episode_prefix']} {bookmarks_status['season_episode']} assigned Stream Link: {stream_link}")
                        else:
                            print(f"    {auto_bookmark['title']} ({auto_bookmark['release_year']}) | {bookmarks_status['season_episode']} assigned Stream Link: {stream_link}")
                else:
                    print(f"\n{current_time()} ERROR: Invalid object_type\n")

    write_data(csv_bookmarks_status, bookmarks_statuses)

# Gets the offers for individual movies/episodes
def get_offers(node_id, country_code, language_code):
    offers = []
    offers_json = []
    offers_json_offers_array = []

    _GRAPHQL_GetTitleOffers = """
    query GetTitleOffers(
    $nodeId: ID!
    $country: Country!
    $language: Language!
    $filterFlatrate: OfferFilter!
    $filterBuy: OfferFilter!
    $filterRent: OfferFilter!
    $filterFree: OfferFilter!
    $platform: Platform! = WEB
    ) {
    node(id: $nodeId) {
        id
        __typename
        ... on MovieOrShowOrSeasonOrEpisode {
        offerCount(country: $country, platform: $platform)
        maxOfferUpdatedAt(country: $country, platform: $platform)
        flatrate: offers(
            country: $country
            platform: $platform
            filter: $filterFlatrate
        ) {
            ...TitleOffer
            __typename
        }
        buy: offers(country: $country, platform: $platform, filter: $filterBuy) {
            ...TitleOffer
            __typename
        }
        rent: offers(
            country: $country
            platform: $platform
            filter: $filterRent
        ) {
            ...TitleOffer
            __typename
        }
        free: offers(
            country: $country
            platform: $platform
            filter: $filterFree
        ) {
            ...TitleOffer
            __typename
        }
        fast: offers(
            country: $country
            platform: $platform
            filter: { monetizationTypes: [FAST], bestOnly: true }
        ) {
            ...FastOffer
            __typename
        }
        __typename
        }
    }
    }

    fragment TitleOffer on Offer {
    id
    presentationType
    monetizationType
    retailPrice(language: $language)
    retailPriceValue
    currency
    lastChangeRetailPriceValue
    type
    package {
        id
        packageId
        clearName
        technicalName
        icon(profile: S100)
        __typename
    }
    standardWebURL
    elementCount
    availableTo
    deeplinkRoku: deeplinkURL(platform: ROKU_OS)
    subtitleLanguages
    videoTechnology
    audioTechnology
    audioLanguages
    __typename
    }

    fragment FastOffer on Offer {
    ...TitleOffer
    availableTo
    availableFromTime
    availableToTime
    __typename
    }
    """

    json_data = {
        'query': _GRAPHQL_GetTitleOffers,
        'variables': {
            "platform": "WEB",
            "nodeId": node_id,
            "country": country_code,
            "language": language_code,
            "filterBuy": {
                "monetizationTypes": [
                "BUY"
                ],
                "bestOnly": True
            },
            "filterFlatrate": {
                "monetizationTypes": [
                "FLATRATE",
                "FLATRATE_AND_BUY",
                "ADS",
                "FREE",
                "CINEMA"
                ],
                "bestOnly": True
            },
            "filterRent": {
                "monetizationTypes": [
                "RENT"
                ],
                "bestOnly": True
            },
            "filterFree": {
                "monetizationTypes": [
                "ADS",
                "FREE"
                ],
                "bestOnly": True
            }
        },
        'operationName': 'GetTitleOffers',
    }

    try:
        offers = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
        offers_json = offers.json()
        offers_json_offers_array = offers_json["data"]["node"]
    except requests.RequestException as e:
        print(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")

    return offers_json_offers_array

# Extract the offers in a usable list
def extract_offer_info(offers_json):
    result = []
    for field, offers in offers_json.items():
        if isinstance(offers, list):
            for offer in offers:
                name = offer.get('package', {}).get('clearName')
                url = urllib.parse.unquote(offer.get('standardWebURL'))  # Decode the URL
                result.append({"name": name, "url": url})

    return result

# Parse through all Offers and find Stream Links based upon priority of Streaming Services
def get_stream_link(offers):
    services = read_data(csv_streaming_services)
    check_services = [service for service in services if service["streaming_service_subscribe"] == "True"]
    check_services.sort(key=lambda x: int(x.get("streaming_service_priority", float("inf"))))

    # Initialize Stream Link as None
    stream_link = None
    
    # If offers is not empty, iterate through check_services
    if offers:
        for check_service in check_services:
            for offer in offers:
                if check_service['streaming_service_name'] == offer['name']:
                    stream_link = offer['url']
                    break  # Stop checking once a match is found
            else:
                continue  # Continue to the next check_service if no match was found
            break  # Exit the outer loop once a match is made
    
    return stream_link

# Cleans out Stream Links of tracking information and other issues
def clean_stream_link(stream_link_dirty, object_type):
    slmappings = read_data(csv_slmappings)

    stream_link_cleaned = None
    stream_link = None

    if stream_link_dirty:
        stream_link_cleaned = stream_link_dirty

        # Remove affiliate tracker (Start)
        if 'u=' in stream_link_cleaned:
            stream_link_cleaned = stream_link_cleaned.split('u=')[1]

        # Remove affiliate tracker (End)
        if '&subId' in stream_link_cleaned:
            stream_link_cleaned = stream_link_cleaned.split('&subId')[0]

        # Remove tracker elements
        not_remove_trackers = [
            "amazon.com" #,
            # Add more as needed
        ]
        if '?' in stream_link_cleaned and not any(not_remove_tracker in stream_link_cleaned for not_remove_tracker in not_remove_trackers):
            stream_link_cleaned = stream_link_cleaned.split('?')[0]

        # Parse the URL to make sure it is in regular characters
        stream_link = urllib.parse.unquote(stream_link_cleaned)

    # Advanced Settings and other modifications
    if stream_link:

        # Stream Link Mappings
        for slmapping in slmappings:
            if slmapping['active'].lower() == "on":
                if stream_link.__contains__(slmapping['contains_string']):
                    if slmapping['object_type'] == "MOVIE or SHOW" or slmapping['object_type'] == object_type:
                        if slmapping['replace_type'] == "Replace string with...":
                            stream_link = stream_link.replace(slmapping['contains_string'], slmapping['replace_string'])
                        elif slmapping['replace_type'] == "Replace entire Stream Link with...":
                            stream_link = slmapping['replace_string']

    return stream_link

# Gets a list of of the IDs of all Stream Link entries created by Stream Link Manager that are now different
def get_stream_link_ids():
    global stream_link_ids_changed

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    api_url = f"{channels_url}/api/v1/all?source=stream-links"
    bookmarks_statuses = read_data(csv_bookmarks_status)
    filtered_bookmarks_statuses = [bookmarks_status for bookmarks_status in bookmarks_statuses if bookmarks_status['stream_link'] != ""]
    slm_stream_links = []
    stream_link_ids = []
    stream_link_ids_changed = []

    channels_url_okay = check_channels_url(None)

    if channels_url_okay:

        for filtered_bookmarks_status in filtered_bookmarks_statuses:
            original_path = filtered_bookmarks_status["stream_link_file"].lower()
            imports_index = original_path.find("imports")
            path = original_path[imports_index:]
            if filtered_bookmarks_status["stream_link_override"] != "":
                stream_link_current = filtered_bookmarks_status["stream_link_override"].lower()
            else:
                stream_link_current = filtered_bookmarks_status["stream_link"].lower()

            slm_stream_links.append({
                "path": path,
                "stream_link_current": stream_link_current
            })

        try:
            response = requests.get(api_url, headers=url_headers)
            response.raise_for_status()  # Raise an exception if the response status code is not 200 (OK)
            data = response.json()
            data_filtered = [item for item in data if "\\slm\\" in item["path"]] # Filter the items where the "path" contains "\slm\"

            for item in data_filtered:
                if os.path.exists(item["path"]):
                    original_path = item["path"].lower()
                    imports_index = original_path.find("imports")
                    path = original_path[imports_index:]
                    id = item["id"]
                    if os.path.exists(original_path):
                        with open(original_path, 'r', encoding="utf-8") as file:
                            stream_link_prior = file.read().rstrip().lower()
                    else:
                        stream_link_prior = None
                        print(f"\n{current_time()} WARNING: Could not find {original_path}. Skipping check.")

                    stream_link_ids.append({
                        "path": path,
                        "id": id,
                        "stream_link_prior": stream_link_prior
                    })

        except requests.RequestException as e:
            print(f"\n{current_time()} ERROR: From Channels API... {e}")

        for slm_stream_link in slm_stream_links:
            for stream_link_id in stream_link_ids:
                if slm_stream_link["path"] == stream_link_id["path"]:
                    if slm_stream_link["stream_link_current"] != stream_link_id["stream_link_prior"]:
                        stream_link_ids_changed.append(stream_link_id["id"])

    else:
        notification_add(f"\n{current_time()} INFO: Cannot check for changes from last run due to Channels URL error.\n")

# Creates Stream Link Files and removes invalid ones and empty directories (for TV)
def create_stream_link_files(bookmarks, remove_choice):
    bookmarks_statuses = read_data(csv_bookmarks_status)

    movie_path, tv_path = get_movie_tv_path()

    create_directory(movie_path)
    create_directory(tv_path)

    for bookmark in bookmarks:
        for bookmark_status in bookmarks_statuses:
            if bookmark['entry_id'] == bookmark_status['entry_id']:

                title_clean = sanitize_name(bookmark['title'])
                title_full = f"{title_clean} ({bookmark['release_year']})"

                stream_link_path = None
                stream_link_file_name = None
                stream_link_url = None

                if bookmark['object_type'] == "MOVIE":
                    stream_link_path = movie_path
                    stream_link_file_name = title_full
                elif bookmark['object_type'] == "SHOW":
                    if bookmark_status['season_episode_prefix'] != "":
                        stream_link_file_name = f"{bookmark_status['season_episode_prefix']} {bookmark_status['season_episode']}"
                    else:
                        stream_link_file_name = bookmark_status['season_episode']
                    season_number, episode_number = re.match(r"S(\d+)E(\d+)", bookmark_status['season_episode']).groups()
                    season_folder_name = f"Season {season_number}"
                    stream_link_path = os.path.join(tv_path, title_full, season_folder_name)

                if bookmark_status['stream_link_override'] != "":
                    stream_link_url = bookmark_status['stream_link_override']
                elif bookmark_status['stream_link'] != "":
                    stream_link_url = bookmark_status['stream_link']

                if bookmark_status['status'].lower() == "unwatched" and stream_link_url:
                    if bookmark['object_type'] == "SHOW":
                        create_directory(os.path.join(tv_path, title_full))
                        create_directory(stream_link_path)

                    file_path_return = create_file(stream_link_path, stream_link_file_name, stream_link_url)
                    file_path_return = normalize_path(file_path_return)
                    bookmark_status['stream_link_file'] = file_path_return

                elif bookmark_status['status'].lower() == "watched" or bookmark_status['stream_link'] == "":

                    file_delete(stream_link_path, stream_link_file_name)
                    bookmark_status['stream_link_file'] = None

    if remove_choice:
        remove_rogue_empty(movie_path, tv_path, bookmarks_statuses)

    write_data(csv_bookmarks_status, bookmarks_statuses)

# Get the path for Movies and TV Shows
def get_movie_tv_path():
    settings = read_data(csv_settings)
    channels_path = settings[1]["settings"]

    movie_path = os.path.join(channels_path, "Imports", "Movies", "slm")
    tv_path = os.path.join(channels_path, "Imports", "TV", "slm")

    return movie_path, tv_path

# Remove rogue files and empty directories
def remove_rogue_empty(movie_path, tv_path, bookmarks_statuses):
    all_files = []
    for path in [movie_path, tv_path]:
        for dirpath, dirnames, filenames in os.walk(path):
            all_files.extend([normalize_path(os.path.join(dirpath, filename)) for filename in filenames])

    slm_files = []
    for bookmark_status in bookmarks_statuses:
        if bookmark_status['stream_link_file']:
            slm_files.append(normalize_path(bookmark_status['stream_link_file']))

    rogue_files = [file_path for file_path in all_files if file_path not in slm_files]

    for rogue_file in rogue_files:
        try:
            os.remove(rogue_file)
            notification_add(f"    Deleted Rogue File: {rogue_file}")
        except OSError as e:
            notification_add(f"    Error removing Rogue File {rogue_file}: {e}")

    # Remove empty directories
    directory_delete(tv_path)

# Remove invalid characters (e.g., colons, slashes, etc.)
def sanitize_name(name):
    sanitized = re.sub(r'[\\/:*?"<>|]', '', name)
    return sanitized

# Create Stream Link file
def create_file(path, name, url):
    file_path = get_file_path(path, name)
    file_path = normalize_path(file_path)
    file_path_return = None

    try:
        with open(file_path, 'w', encoding="utf-8") as file:
            try:
                file.write(url)
                print(f"    Created: {file_path}")
                file_path_return = file_path
            except OSError as e:
                print(f"    Error creating file {file_path}: {e}")

    except FileNotFoundError as fnf_error:
        print(f"    Error with original path: {fnf_error}")

    return file_path_return

# Delete Stream Link file if it exists
def file_delete(path, name):
    file_path = get_file_path(path, name)
    file_path = normalize_path(file_path)

    try:
        try:
            if  os.path.exists(file_path):
                os.remove(file_path)
                notification_add(f"    Deleted: {file_path}")
        except OSError as e:
            notification_add(f"    Error removing file {file_path}: {e}")
    except FileNotFoundError as fnf_error:
        print(f"    Error removing file: {fnf_error}")

# Get complete file path and name
def get_file_path(path, name):
    file_name = f"{name}"
    file_name += ".strmlnk"
    file_path = os.path.join(path, file_name)
    file_path = normalize_path(file_path)
    return file_path

# Remove empty subdirectories without prompting
def directory_delete(base_directory):
    for root, dirs, _ in os.walk(base_directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    notification_add(f"    Removed empty directory: {dir_path}")
            except OSError as e:
                print(f"    Error removing directory {dir_path}: {e}")
                print(f"    Attempting to remove via read-only handle...")
                try:
                    os.chmod(dir_path, stat.S_IWRITE)  # Mark the folder as writable
                    os.rmdir(dir_path)
                    notification_add(f"    On second attempt, removed empty directory: {dir_path}")
                except OSError as e:
                    notification_add(f"    Second error removing directory {dir_path}: {e}")

# Runs a prune/scan in Channels
def prune_scan_channels():
    print("\n==========================================================")
    print("|                                                        |")
    print("|                Update Media in Channels                |")
    print("|                                                        |")
    print("==========================================================")

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    prune_url = f"{channels_url}/dvr/scanner/imports/prune"
    scan_url = f"{channels_url}/dvr/scanner/scan"
    channels_prune = settings[7]["settings"]

    channels_url_okay = check_channels_url(None)

    if channels_url_okay:
        # Prune
        if channels_prune == "On":
            notification_add(f"\n{current_time()} Beginning Prune request...")
            try:
                requests.put(prune_url)
            except requests.RequestException as e:
                notification_add(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")
            notification_add(f"\n{current_time()} Prune requested.")
        else:
            notification_add(f"\n{current_time()} INFO: Prune disabled, skipping step.")

        # Scan
        notification_add(f"\n{current_time()} Beginning scan request...")
        try:
            requests.put(scan_url)
        except requests.RequestException as e:
            notification_add(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")
        notification_add(f"\n{current_time()} Scan requested.")

        # Reprocess
        if stream_link_ids_changed:
            notification_add(f"\n{current_time()} Beginning Reprocess requests...")
            asyncio.run(get_reprocess_requests(channels_url))
            notification_add(f"\n{current_time()} Finished Reprocess requests")
        else:
            notification_add(f"\n{current_time()} INFO: Nothing to reprocess, skipping step.")

        if channels_prune == "On":
            if stream_link_ids_changed:
                notification_add(f"\n{current_time()} Prune, Scan, and Reprocess underway. Check Channels for status.\n")
            else:
                notification_add(f"\n{current_time()} Prune and Scan underway. Check Channels for status.\n")
        else:
            if stream_link_ids_changed:
                notification_add(f"\n{current_time()} Scan and Reprocess underway. Check Channels for status.\n")
            else:
                notification_add(f"\n{current_time()} Scan underway. Check Channels for status.\n")
    else:
        notification_add(f"\n{current_time()} INFO: Skipped Prune, Scan, and Reprocess due to Channels URL error.\n")

# Asycnronous request of Stream Link reprocessing
async def get_reprocess_requests(channels_url):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as reprocess_session:
        tasks = [send_reprocess_requests(reprocess_session, f"{channels_url}/dvr/files/{stream_link_id}/reprocess") for stream_link_id in stream_link_ids_changed]
        try:
            await asyncio.gather(*tasks)
        except asyncio.TimeoutError:
            notification_add(f"\n{current_time()} ERROR: Reprocessing requests timed out.")

# Build list of Stream Link reprocess requests
async def send_reprocess_requests(reprocess_session, reprocess_url):
    try:
        await reprocess_session.put(reprocess_url)
    except asyncio.TimeoutError:
        notification_add(f"\n{current_time()} ERROR: Request for {reprocess_url} timed out.")

# End-to-End Update Process
def end_to_end():
    print("\n==========================================================")
    print("|                                                        |")
    print("|               End-to-End Update Process                |")
    print("|                                                        |")
    print("==========================================================")

    notification_add(f"\n{current_time()} Beginning end-to-end update process...\n")

    start_time = time.time()

    if os.path.exists(program_files_dir):
        create_backup(program_files_dir, backup_dir, max_backups)
    time.sleep(2)
    update_streaming_services()
    time.sleep(2)
    get_new_episodes()
    time.sleep(2)
    import_program_updates()
    time.sleep(2)
    generate_stream_links()
    time.sleep(2)
    prune_scan_channels()
    time.sleep(2)

    end_time = time.time()

    elapsed_seconds = end_time - start_time

    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    notification_add(f"\n{current_time()} Total Elapsed Time: {int(hours)} hours | {int(minutes)} minutes | {int(seconds)} seconds")

    notification_add(f"\n{current_time()} End-to-end update process complete\n")

# Background process to check the schedule
def check_schedule():
    while True:
        settings = read_data(csv_settings)
        try:
            auto_update_schedule = settings[8]["settings"]
        except (IndexError, KeyError):
            auto_update_schedule = 'Off'
        auto_update_schedule_time = settings[6]["settings"] 

        if auto_update_schedule == 'On' and auto_update_schedule_time:
            current_time = datetime.datetime.now().strftime('%H:%M')
            if current_time == auto_update_schedule_time:
                end_to_end()
                time.sleep(60)  # Wait a minute to avoid multiple triggers within the same minute
        time.sleep(1)  # Check every second

# Start the background thread
thread = threading.Thread(target=check_schedule)
thread.daemon = True
thread.start()

# Get any webpage not already called out
def get_segment(request):
    segment = None

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

    except:
        segment = None
    
    return segment

@app.route('/<template>')
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/main/FILE.html
        return render_template(
            "main/" + template,
            segment = segment,
            html_slm_version = slm_version
        )

    except TemplateNotFound:
        return render_template(
            'main/page-404.html',
            html_slm_version = slm_version
        ), 404

    except:
        return render_template(
            'main/page-500.html',
            html_slm_version = slm_version
        ), 500

# Start-up Check
if __name__ == "__main__":
    notification_add(f"\n{current_time()} INFO: Server starting on port {slm_port}\n")
    app.run(host='0.0.0.0', port=slm_port)
