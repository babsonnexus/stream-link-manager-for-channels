import os
import sys
import shutil
import socket
import csv
import pandas as pd
import pandasql as psql
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
import gzip
import io
import ast
from flask import Flask, render_template, render_template_string, request, redirect, url_for, Response, send_file, Request, make_response, stream_with_context
from jinja2 import TemplateNotFound
import yt_dlp
import streamlink
from collections import OrderedDict
from youtubesearchpython import VideosSearch as youtube_search_videos
from youtubesearchpython import ChannelsSearch as youtube_search_channels
from youtubesearchpython import Playlist as get_youtube_playlist_info
from youtubesearchpython.core.utils import playlist_from_channel_id as get_youtube_channel_info
from youtubesearchpython import Video as get_youtube_video_info

# Top Controls
slm_environment_version = "PRERELEASE"
slm_environment_port = None

# Current Stable Release
slm_version = "v2025.08.27.1520"
slm_port = os.environ.get("SLM_PORT")

# Current Development State
if slm_environment_version == "PRERELEASE":
    slm_version = "v2025.12.07.0951"
if slm_environment_port == "PRERELEASE":
    slm_port = None

if slm_port is None:
    slm_port = 5000
else:
    try:
        slm_port = int(slm_port)
    except:
        slm_port = 5000

app = Flask(__name__)

# Control how many data elements can be saved at a time from the webpage to the code. Modify values higher if continual 413 issues.
class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super(CustomRequest, self).__init__(*args, **kwargs)
        self.max_form_parts = 1000000                       # Individual web components
        self.max_form_memory_size = 1024 * 1024 * 1024      # Last number is MB for form data

app.request_class = CustomRequest
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024       # Last number is MB for submitting requests/files

# Home webpage
@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def webpage_home():
    return render_template(
        'main/index.html',
        segment = 'index',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_notifications = notifications
    )

# Adds a notification
def notification_add(notification):
    global notifications
    notifications.insert(0, notification)
    print(notification)

# Webpage and functions to add, modify, and manage programs
@app.route('/manage_programs', methods=['GET', 'POST'])
def webpage_manage_programs():
    # Global Page Management
    global slm_manage_programs_main_flag
    global slm_manage_programs_search_results_flag
    global slm_manage_programs_modify_program_flag
    global slm_manage_programs_modify_program_scollbar_flag

    if not any((
        slm_manage_programs_search_results_flag,
        slm_manage_programs_modify_program_flag
    )):
        slm_manage_programs_main_flag = True

    import_metadata_options_flag = None
    if slm_channels_dvr_integration or slm_media_players_integration:
        import_metadata_options_flag = True

    # Global Previously Bookmarked Selections
    global modify_entry_id 

    # Global Search, Manual, and Import Selections
    global program_add_prior
    global program_add_manual_prior
    global program_add_import_playlist_prior

    # Global New & Recent Selections
    global date_new_default_start_prior
    if date_new_default_start_prior is None or date_new_default_start_prior == '':
        date_new_default_start_prior = datetime.datetime.now().strftime('%Y-%m-%d')
    global date_new_default_end_prior
    if date_new_default_end_prior is None or date_new_default_end_prior == '':
        date_new_default_end_prior = datetime.datetime.now().strftime('%Y-%m-%d')

    # Global Search Results
    global program_search_results_prior
    global program_search_results_resort_alpha_flag
    global slm_manage_programs_program_modify_available_flag

    # Global Add/Modify Selection
    global select_programs_to_edit
    global settings_country_code_input_prior
    global settings_language_code_input_prior

    # Global Edit Selection
    global entry_id_selected_prior
    global object_type_selected_prior
    global bookmark_action_prior
    global override_program_sort_prior
    global program_modify_bookmark_selected_prior
    global program_modify_label_maps_selected_prior
    global program_modify_details_selected_prior
    global filter_modify_program_season_episode_prefix
    global filter_modify_program_season_episode
    global filter_modify_program_stream_link
    global filter_modify_program_stream_link_override
    global filter_modify_program_special_action
    global filter_modify_program_original_release_date
    global filter_modify_program_override_episode_title
    global filter_modify_program_override_summary
    global filter_modify_program_override_image
    global filter_modify_program_override_duration

    # Inititialize Settings and Other Elements
    manage_programs_message = ''
    settings_num_results = None
    settings_search_selection = None
    settings_provider_status = None
    settings_hide_bookmarked = None
    settings_country_code = None
    settings_language_code = None
    settings_minimum_video_length = None
    settings_show_hidden_programs = None
    settings_use_feed_map = None
    sorted_bookmarks = []
    provider_statuses = []
    provider_groups = []
    bookmark_actions = []
    special_actions = []
    new_special_actions = []
    override_program_image_types = []
    override_program_sorts = []
    bookmark_selected_actions = []
    program_modify_details_actions = []
    add_program_modify_details_actions = []
    program_modify_global_selections = []
    search_selections = []
    program_types = []
    search_results_actions_movie = []
    search_results_actions_show = []
    search_results_actions_video = []
    search_results_actions_channel = []
    date_new_default_range = []
    search_results_labels = []
    program_feed_rule_date_ranges = []
    program_feed_rule_actions = []
    new_program_feed_rule_actions = []
    program_feed_map_source_fields = []
    program_feed_map_target_actions = []
    program_feed_map_actions = []
    new_program_feed_map_actions = []
    feed_items = []
    feed_maps = []
    feed_rules = []
    feed_map_source_providers = []

    search_results_actions_default = [
        {'search_results_action_id': 'none', 'search_results_action_name': 'None'},
        {'search_results_action_id': 'hide', 'search_results_action_name': 'Hide'}
    ]

    if slm_process_active_flag:
        manage_programs_message = f"{current_time()} WARNING: A SLM process is currently underway and, due to this, 'Manage Programs' functionality cannot be run at this time. If you were executing an action, your last position will be saved and be available when the process completes. Please try again later."

    elif request.method == 'POST':
        manage_programs_action = request.form['action']

        if manage_programs_action in [
            'search_defaults_save',
            'program_modify_edit',
            'program_modify_available',
            'program_add_search',
            'program_new_search',
            'program_new_today',
            'program_add_manual',
            'program_add_import_playlist',
            'slm_manage_programs_search_results_save',
            'program_feed_update',
            'program_feed_view'
        ]:
            
            if manage_programs_action in [
                'search_defaults_save',
                'program_modify_edit',
                'program_modify_available',
                'program_add_search',
                'program_new_search',
                'program_new_today',
                'program_feed_update',
                'program_feed_view'
            ]:

                if manage_programs_action in [
                    'search_defaults_save',
                    'program_add_search',
                    'program_new_search',
                    'program_new_today',
                    'program_feed_update',
                    'program_feed_view'
                ]:
                    
                    settings_country_code_input_prior = request.form.get('settings_country_code')
                    settings_language_code_input_prior = request.form.get('settings_language_code')
                    
                    if manage_programs_action in [
                        'search_defaults_save',
                        'program_add_search',
                        'program_new_search',
                        'program_new_today'
                    ]:
                        
                        settings_hide_bookmarked_input = "On" if request.form.get('settings_hide_bookmarked') in ['on', 'On'] else "Off"
                        settings_minimum_video_length_input = request.form.get('settings_minimum_video_length')
                        settings_minimum_video_length_test = None
                        settings_minimum_video_length_test = positive_integer_test(settings_minimum_video_length_input, True)
                        settings_provider_status_input = request.form.get('select_provider_status')

                        if manage_programs_action in [
                            'search_defaults_save',
                            'program_add_search'
                        ]:

                            settings_search_selection_input = request.form.get('select_search_selection')
                            settings_num_results_input = request.form.get('settings_num_results')
                            settings_num_results_test = None
                            settings_num_results_test = positive_integer_test(settings_num_results_input, False)

                            if manage_programs_action == 'search_defaults_save':
                                settings_show_hidden_programs_input = "On" if request.form.get('settings_show_hidden_programs') in ['on', 'On'] else "Off"
                                settings_use_feed_map_input = "On" if request.form.get('settings_use_feed_map') in ['on', 'On'] else "Off"

                                if settings_num_results_test != "pass":

                                    if settings_num_results_test == 'unknown':
                                        manage_programs_message = f"{current_time()} ERROR: While other 'Settings & Options' saved, an unknown issue happened in relation to 'Quantity'. As such, it has reverted to the prior value."
                                    elif settings_num_results_test == 'missing':
                                        manage_programs_message = f"{current_time()} ERROR: While other 'Settings & Options' saved, a 'Quantity' is required. As such, it has reverted to the prior value."
                                    elif settings_num_results_test == 'not_number':
                                        manage_programs_message = f"{current_time()} ERROR: While other 'Settings & Options' saved, a number is required for 'Quantity'. As such, it has reverted to the prior value."
                                    elif settings_num_results_test == 'not_positive':
                                        manage_programs_message = f"{current_time()} ERROR: While other 'Settings & Options' saved, a positive integer is required for 'Quantity'. As such, it has reverted to the prior value."
                                    else:
                                        manage_programs_message = f"{current_time()} ERROR: While other 'Settings & Options' saved, 'Quantity' was unable to be evaluated. As such, it has reverted to the prior value."

                                if settings_minimum_video_length_test != "pass":

                                    if manage_programs_message not in [None, '']:
                                        manage_programs_message += f"\n"

                                    if settings_minimum_video_length_test == 'unknown':
                                        manage_programs_message += f"{current_time()} ERROR: While other 'Settings & Options' saved, an unknown issue happened in relation to 'Minimum Video Length (Seconds)'. As such, it has reverted to the prior value."
                                    elif settings_minimum_video_length_test == 'missing':
                                        manage_programs_message += f"{current_time()} ERROR: While other 'Settings & Options' saved, 'Minimum Video Length (Seconds)' is required. As such, it has reverted to the prior value."
                                    elif settings_minimum_video_length_test == 'not_number':
                                        manage_programs_message += f"{current_time()} ERROR: While other 'Settings & Options' saved, a number is required for 'Minimum Video Length (Seconds)'. As such, it has reverted to the prior value."
                                    elif settings_minimum_video_length_test == 'not_positive':
                                        manage_programs_message += f"{current_time()} ERROR: While other 'Settings & Options' saved, a positive integer is required for 'Minimum Video Length (Seconds)'. As such, it has reverted to the prior value."
                                    else:
                                        manage_programs_message += f"{current_time()} ERROR: While other 'Settings & Options' saved, 'Minimum Video Length (Seconds)' was unable to be evaluated. As such, it has reverted to the prior value."

                                settings = read_data(csv_settings)
                                settings_country_code_prior = settings[2]["settings"]               # [2]  Search Defaults: Country Code

                                if settings_num_results_test == "pass":
                                    settings[4]["settings"] = settings_num_results_input              # [4]  Search Defaults: Number of Results
                                settings[64]["settings"] = settings_search_selection_input            # [64] SLM: 'Add Programs' Search Selection (Default)
                                settings[47]["settings"] = settings_provider_status_input             # [47] SLM: Search Default for Provider Status
                                settings[9]["settings"] = settings_hide_bookmarked_input              # [9]  Search Defaults: Filter out already bookmarked
                                settings[2]["settings"] = settings_country_code_input_prior           # [2]  Search Defaults: Country Code
                                settings[3]["settings"] = settings_language_code_input_prior          # [3]  Search Defaults: Language Code
                                if settings_minimum_video_length_test == "pass":
                                    settings[65]["settings"] = settings_minimum_video_length_input    # [65] SLM: Minimum Video Length (in Seconds) for Search
                                settings[66]["settings"] = settings_show_hidden_programs_input        # [66] SLM: Show 'Hidden Programs' in Dropdown Selection (Default)
                                settings[67]["settings"] = settings_use_feed_map_input                # [67] SLM: Use the 'Feed & Auto-Mapping' functionality
                                write_data(csv_settings, settings)

                                if settings_country_code_input_prior != settings_country_code_prior:
                                    update_streaming_services()
                            
                            elif manage_programs_action == 'program_add_search':
                                program_add_prior = request.form.get('field_program_add')

                                if settings_num_results_test == "pass":

                                    if settings_minimum_video_length_test == "pass":
                                        movies_shows_search_results = []
                                        videos_search_results = []
                                        channels_search_results = []

                                        if settings_search_selection_input in ['all', 'movies_shows_videos', 'movies_shows']:
                                            movies_shows_search_results = search_bookmark(settings_country_code_input_prior, settings_language_code_input_prior, settings_num_results_input, program_add_prior)
                                        if settings_search_selection_input in ['all', 'movies_shows_videos', 'videos_channels', 'videos']:
                                            videos_search_results, manage_programs_message = search_video_providers(video_providers, program_add_prior, 'videos', settings_num_results_input, settings_language_code_input_prior, settings_country_code_input_prior)
                                        if settings_search_selection_input in ['all', 'videos_channels', 'channels']:
                                            channels_search_results, manage_programs_message = search_video_providers(video_providers, program_add_prior, 'channels', settings_num_results_input, settings_language_code_input_prior, settings_country_code_input_prior)

                                        if 'ERROR' not in manage_programs_message:
                                            
                                            if movies_shows_search_results:
                                                program_search_results_prior = program_search_results_prior + movies_shows_search_results
                                            if videos_search_results:
                                                program_search_results_prior = program_search_results_prior + videos_search_results
                                            if channels_search_results:
                                                program_search_results_prior = program_search_results_prior + channels_search_results

                                            if program_search_results_prior:
                                                if program_add_prior is None or program_add_prior == '':
                                                    manage_programs_message = f"{current_time()} INFO: Displaying most popular programs."
                                                else:
                                                    manage_programs_message = f"{current_time()} INFO: Displaying results for searched term '{program_add_prior}'."
                                            
                                            else:
                                                manage_programs_message = f"{current_time()} INFO: No results for search."

                                    else:

                                        if settings_minimum_video_length_test == 'unknown':
                                            manage_programs_message = f"{current_time()} ERROR: For 'Search', an unknown issue happened in relation to 'Minimum Video Length (Seconds)'."
                                        elif settings_minimum_video_length_test == 'missing':
                                            manage_programs_message = f"{current_time()} ERROR: For 'Search', 'Minimum Video Length (Seconds)' is required."
                                        elif settings_minimum_video_length_test == 'not_number':
                                            manage_programs_message = f"{current_time()} ERROR: For 'Search', please enter a number for 'Minimum Video Length (Seconds)'."
                                        elif settings_minimum_video_length_test == 'not_positive':
                                            manage_programs_message = f"{current_time()} ERROR: For 'Search', please enter a positive integer for 'Minimum Video Length (Seconds)'."
                                        else:
                                            manage_programs_message = f"{current_time()} ERROR: For 'Search', unable to test the value for 'Minimum Video Length (Seconds)'."

                                else:

                                    if settings_num_results_test == 'unknown':
                                        manage_programs_message = f"{current_time()} ERROR: For 'Search', an unknown issue happened in relation to 'Quantity'."
                                    elif settings_num_results_test == 'missing':
                                        manage_programs_message = f"{current_time()} ERROR: For 'Search', a 'Quantity' is required."
                                    elif settings_num_results_test == 'not_number':
                                        manage_programs_message = f"{current_time()} ERROR: For 'Search', please enter a number for 'Quantity'."
                                    elif settings_num_results_test == 'not_positive':
                                        manage_programs_message = f"{current_time()} ERROR: For 'Search', please enter a positive integer for 'Quantity'."
                                    else:
                                        manage_programs_message = f"{current_time()} ERROR: For 'Search', unable to test the value for 'Quantity'."

                        elif manage_programs_action in [
                            'program_new_search',
                            'program_new_today'
                        ]:

                            if manage_programs_action == 'program_new_search':
                                date_new_default_start_prior = request.form.get('field_date_new_default_start')
                                date_new_default_end_prior = request.form.get('field_date_new_default_end')

                            elif manage_programs_action == 'program_new_today':
                                date_new_default_start_prior = datetime.datetime.now().strftime('%Y-%m-%d')
                                date_new_default_end_prior = datetime.datetime.now().strftime('%Y-%m-%d')

                            date_new_default_range = [
                                (datetime.datetime.strptime(date_new_default_start_prior, '%Y-%m-%d') + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
                                for i in range((datetime.datetime.strptime(date_new_default_end_prior, '%Y-%m-%d') - datetime.datetime.strptime(date_new_default_start_prior, '%Y-%m-%d')).days + 1)
                            ]

                            settings_num_results_input = 100 # Maximum number of new programs

                            if date_new_default_range:
                                program_search_results_prior = get_program_new(date_new_default_range, settings_country_code_input_prior, settings_language_code_input_prior, settings_num_results_input, settings_provider_status_input, video_providers)

                            if program_search_results_prior:
                                manage_programs_message = f"{current_time()} INFO: Displaying 'New & Updated' results on your selected provider(s)."
                            else:
                                manage_programs_message = f"{current_time()} INFO: No 'New & Updated' results on your selected provider(s)."

                    elif manage_programs_action in [
                        'program_feed_update',
                        'program_feed_view'
                    ]:

                        if manage_programs_action == 'program_feed_update':
                            run_slm_update_feed()

                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{current_time()} INFO: Feed has been manually refreshed!"

                        feed_items = read_data(csv_slm_feed_items)

                        for item in feed_items:
                            offers_raw = item.get("offers_list")
                            if isinstance(offers_raw, str):
                                try:
                                    item["offers_list"] = ast.literal_eval(offers_raw)
                                except (ValueError, SyntaxError):
                                    print(f"{current_time()} ERROR: For 'Feed Items', unable to convert 'Offers List' to a list.")

                        if feed_items:
                            program_search_results_prior = feed_items
                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{current_time()} INFO: Displaying feed results..."
                        else:
                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{current_time()} INFO: Your feed is currently empty. Please check again later!"

                elif manage_programs_action in [
                    'program_modify_edit',
                    'program_modify_available'
                ]:
                    
                    modify_entry_id = request.form.get('select_previously_bookmarked')
                    bookmarks = read_data(csv_bookmarks)

                    if manage_programs_action == 'program_modify_edit':
                        for bookmark in bookmarks:
                            if modify_entry_id == bookmark['entry_id']:
                                select_programs_to_edit.append({
                                    'entry_id': modify_entry_id,
                                    'object_type': bookmark['object_type']
                                })
                                break

                        if not select_programs_to_edit:
                            manage_programs_message = f"{current_time()} ERROR: Unable to edit program."
                    
                    elif manage_programs_action == 'program_modify_available':
                        if not modify_entry_id.startswith('slm') and not modify_entry_id.startswith('int'):

                            for bookmark in bookmarks:
                                if bookmark['entry_id'] == modify_entry_id:
                                    title = bookmark['title']
                                    release_year = bookmark['release_year']
                                    object_type = bookmark['object_type']
                                    country_code = bookmark['country_code']
                                    language_code = bookmark['language_code']
                                    short_description = bookmark['override_program_summary']
                                    break

                            movies_shows_search_results = search_bookmark(country_code, language_code, 99, title)

                            if movies_shows_search_results:
                                for movies_shows_search_result in movies_shows_search_results:
                                    if movies_shows_search_result['entry_id'] == modify_entry_id:
                                        program_search_results_prior.append(movies_shows_search_result)
                                        break
                            
                            if program_search_results_prior:
                                manage_programs_message = f"{current_time()} INFO: Displaying information for selected program."

                            else:
                                stream_link_details = get_offers(modify_entry_id, country_code, language_code)

                                if stream_link_details:
                                    stream_link_offers = extract_offer_info(stream_link_details)
                                    stream_link_offers_sorted = sorted(stream_link_offers, key=lambda x: sort_key(x["name"]))

                                    offers_list = []
                                    for offer in stream_link_offers_sorted:
                                        offers_list.append(offer['icon'])

                                    offers_list = list(dict.fromkeys(offers_list))

                                    program_search_results_prior.append({
                                        "entry_id": modify_entry_id,
                                        "title": title,
                                        "release_year": release_year,
                                        "object_type": object_type,
                                        "url": '',
                                        "short_description": short_description,
                                        "poster": '',
                                        "score": '',
                                        "offers_list": offers_list
                                    })

                                    manage_programs_message = f"{current_time()} INFO: Displaying limited information for selected program after it was not found using normal methods."

                                else:
                                    manage_programs_message = f"{current_time()} ERROR: Unable to find information using any method for selected program."

                            if program_search_results_prior:
                                slm_manage_programs_program_modify_available_flag = True

                        else:
                            manage_programs_message = f"{current_time()} ERROR: Manual programs, Video Groups, and internal lists cannot be checked for availability."

                if program_search_results_prior:
                    if 'feed' not in manage_programs_action and not slm_manage_programs_program_modify_available_flag:

                        program_search_results_check = program_search_results_prior.copy()
                        filter_clean_message = None
                        program_search_results_prior, filter_clean_message = filter_clean_slm_search_results(program_search_results_check, settings_hide_bookmarked_input, settings_minimum_video_length_input, slm_manage_programs_program_modify_available_flag)

                        if filter_clean_message not in [None, '']:
                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += filter_clean_message

                    if program_search_results_prior:
                        slm_manage_programs_search_results_flag = True

            elif manage_programs_action in [
                'program_add_manual',
                'program_add_import_playlist',
                'slm_manage_programs_search_results_save'
            ]:

                program_search_results_base_submissions = []

                if manage_programs_action in [
                    'program_add_manual',
                    'program_add_import_playlist'
                ]:

                    if manage_programs_action == 'program_add_manual':

                        select_program_type_manual_input = request.form.get('select_program_type_manual')
                        field_program_add_manual_input = request.form.get('field_program_add_manual')
                        field_release_year_manual_input = request.form.get('field_release_year_manual')
                        field_release_year_manual_test = None
                        field_release_year_manual_test = get_release_year(field_release_year_manual_input)

                        if field_program_add_manual_input is None or field_program_add_manual_input == '':
                            manage_programs_message = f"{current_time()} ERROR: For 'Create Manual', a 'Title' is required."
                        else:
                            program_add_manual_prior = field_program_add_manual_input

                        if field_release_year_manual_test != "pass":

                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{field_release_year_manual_test}"

                        elif program_add_manual_prior is not None and program_add_manual_prior != '':

                            program_search_results_base_submissions.append({
                                'program_search_results_entry_id_input': 'manual',
                                'program_search_results_title_input': field_program_add_manual_input,
                                'program_search_results_release_year_input': field_release_year_manual_input,
                                'program_search_results_object_type_input': select_program_type_manual_input,
                                'program_search_results_url_input': '',
                                'program_search_results_short_description_input': '',
                                'program_search_results_poster_input': '',
                                'program_search_results_score_input': '',
                                'program_search_results_labels_input': [],
                                'program_search_results_status_input': 'unwatched',
                                'program_search_results_action_input': 'manual'
                            })

                    elif manage_programs_action == 'program_add_import_playlist':
                        field_program_add_import_playlist_input = request.form.get('field_program_add_import_playlist')

                        if field_program_add_import_playlist_input is None or field_program_add_import_playlist_input == '':
                            manage_programs_message = f"{current_time()} ERROR: For 'Video Playlist', a 'Link' is required."

                        elif 'youtu' not in field_program_add_import_playlist_input:
                            manage_programs_message = f"{current_time()} ERROR: Only YouTube Playlists can be imported/sync'd at this time."

                        else:
                            program_add_import_playlist_prior = field_program_add_import_playlist_input
                            
                            program_search_results_videos, manage_programs_message = search_video_providers(video_providers, program_add_import_playlist_prior, 'videos_from_playlist', 100, settings_language_code_input_prior, settings_country_code_input_prior)

                            if manage_programs_message is None or manage_programs_message == '':

                                if program_search_results_videos:
                                    for program_search_results_video in program_search_results_videos:

                                        program_search_results_base_submissions.append({
                                            'program_search_results_entry_id_input': program_search_results_video['entry_id'],
                                            'program_search_results_title_input': program_search_results_video['title'],
                                            'program_search_results_release_year_input': program_search_results_video['release_year'],
                                            'program_search_results_object_type_input': program_search_results_video['object_type'],
                                            'program_search_results_url_input': program_search_results_video['url'],
                                            'program_search_results_short_description_input': program_search_results_video['short_description'],
                                            'program_search_results_poster_input': program_search_results_video['poster'],
                                            'program_search_results_score_input': program_search_results_video['score'],
                                            'program_search_results_labels_input': [],
                                            'program_search_results_status_input': 'unwatched',
                                            'program_search_results_action_input': 'playlist'
                                        })

                                else:
                                    manage_programs_message = f"{current_time()} ERROR: No videos found in entered 'Video Playlist'."

                elif manage_programs_action == 'slm_manage_programs_search_results_save':
                    program_search_results_entry_id_inputs = {}
                    program_search_results_title_inputs = {}
                    program_search_results_release_year_inputs = {}
                    program_search_results_object_type_inputs = {}
                    program_search_results_short_description_inputs = {}
                    program_search_results_url_inputs = {}
                    program_search_results_poster_inputs = {}
                    program_search_results_score_inputs = {}
                    program_search_results_status_inputs = {}
                    program_search_results_labels_inputs = {}
                    program_search_results_action_inputs = {}

                    for key in request.form.keys():

                        if key.startswith('program_search_results_entry_id_'):
                            index = key.split('_')[-1]
                            program_search_results_entry_id_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_title_'):
                            index = key.split('_')[-1]
                            program_search_results_title_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_release_year_'):
                            index = key.split('_')[-1]
                            program_search_results_release_year_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_object_type_'):
                            index = key.split('_')[-1]
                            program_search_results_object_type_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_short_description_'):
                            index = key.split('_')[-1]
                            program_search_results_short_description_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_url_'):
                            index = key.split('_')[-1]
                            program_search_results_url_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_poster_'):
                            index = key.split('_')[-1]
                            program_search_results_poster_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_score_'):
                            index = key.split('_')[-1]
                            program_search_results_score_inputs[index] = request.form.get(key)

                        if key.startswith('program_search_results_labels_'):
                            index = key.split('_')[-1]
                            program_search_results_labels_inputs[index] = request.form.getlist(key)

                        if key.startswith('program_search_results_status_'):
                            index = key.split('_')[-1]
                            program_search_results_status_inputs[index] = 'unwatched' if request.form.get(key) in ['on', 'On', 'ON'] else 'watched'

                        if key.startswith('program_search_results_action_'):
                            index = key.split('_')[-1]
                            program_search_results_action_inputs[index] = request.form.get(key)

                    for row in program_search_results_entry_id_inputs:
                        program_search_results_entry_id_input = None
                        program_search_results_title_input = None
                        program_search_results_release_year_input = None
                        program_search_results_object_type_input = None
                        program_search_results_short_description_input = None
                        program_search_results_url_input = None
                        program_search_results_poster_input = None
                        program_search_results_score_input = None
                        program_search_results_labels_input = []
                        program_search_results_status_input = None
                        program_search_results_action_input = None

                        program_search_results_entry_id_input = program_search_results_entry_id_inputs.get(row)
                        program_search_results_title_input = program_search_results_title_inputs.get(row)
                        program_search_results_release_year_input = program_search_results_release_year_inputs.get(row)
                        program_search_results_object_type_input = program_search_results_object_type_inputs.get(row)
                        program_search_results_short_description_input = program_search_results_short_description_inputs.get(row)
                        program_search_results_url_input = program_search_results_url_inputs.get(row)
                        program_search_results_poster_input = program_search_results_poster_inputs.get(row)
                        program_search_results_score_input = program_search_results_score_inputs.get(row)
                        program_search_results_labels_input = program_search_results_labels_inputs.get(row, [])
                        program_search_results_status_input = program_search_results_status_inputs.get(row, 'watched')
                        program_search_results_action_input = program_search_results_action_inputs.get(row)

                        program_search_results_base_submissions.append({
                            'program_search_results_entry_id_input': program_search_results_entry_id_input,
                            'program_search_results_title_input': program_search_results_title_input,
                            'program_search_results_release_year_input': program_search_results_release_year_input,
                            'program_search_results_object_type_input': program_search_results_object_type_input,
                            'program_search_results_short_description_input': program_search_results_short_description_input,
                            'program_search_results_url_input': program_search_results_url_input,
                            'program_search_results_poster_input': program_search_results_poster_input,
                            'program_search_results_score_input': program_search_results_score_input,
                            'program_search_results_labels_input': program_search_results_labels_input,
                            'program_search_results_status_input': program_search_results_status_input,
                            'program_search_results_action_input': program_search_results_action_input
                        })

                bookmarking_actions_message, clear_results_flag = run_slm_bookmarking_actions(program_search_results_base_submissions)

                if clear_results_flag:
                    slm_manage_programs_search_results_flag = None
                    program_search_results_prior = []

                if bookmarking_actions_message:
                    if manage_programs_message not in [None, '']:
                        manage_programs_message += f"\n"
                    manage_programs_message += bookmarking_actions_message

        elif manage_programs_action == 'program_feed_execute':

            # Baseline
            feed_rules = read_data(csv_slm_feed_rules)
            feed_maps = read_data(csv_slm_feed_maps)

            write_feed_rules = False
            write_feed_maps = False

            if feed_rules:
                temp_record_feed_rules = create_temp_record(feed_rules[0].keys())
            else:
                temp_record_feed_rules = initial_data(csv_slm_feed_rules)[0]
            run_empty_rows_feed_rules = False

            if feed_maps:
                temp_record_feed_maps = create_temp_record(feed_maps[0].keys())
            else:
                temp_record_feed_maps = initial_data(csv_slm_feed_maps)[0]
            run_empty_rows_feed_maps = False

            feed_rules_add_count = 0
            feed_rules_save_count = 0
            feed_rules_delete_count = 0
            feed_maps_add_count = 0
            feed_maps_save_count = 0
            feed_maps_delete_count = 0

            # Get new Feed Rule
            program_feed_rule_action_new_input = None
            program_feed_rule_action_new_input = request.form.get('program_feed_rule_action_new', 'error')

            if program_feed_rule_action_new_input == 'error':
                if manage_programs_message not in [None, '']:
                    manage_programs_message += f"\n"
                manage_programs_message += f"{current_time()} ERROR: Unable to run action against new 'Feed Rule'."

            elif program_feed_rule_action_new_input == 'add':
                program_feed_rule_override_min_video_length_new_input = None
                program_feed_rule_override_min_video_length_new_input = request.form.get('program_feed_rule_override_min_video_length_new', None)

                program_feed_rule_override_min_video_length_new_test = None
                if program_feed_rule_override_min_video_length_new_input in ['', None]:
                    program_feed_rule_override_min_video_length_new_test = 'pass'
                else:
                    program_feed_rule_override_min_video_length_new_test = positive_integer_test(program_feed_rule_override_min_video_length_new_input, True)

                if program_feed_rule_override_min_video_length_new_test != 'pass':

                    if manage_programs_message not in [None, '']:
                        manage_programs_message += f"\n"

                    if program_feed_rule_override_min_video_length_new_test == 'unknown':
                        manage_programs_message += f"{current_time()} ERROR: An unknown issue happened in relation to 'Override Minimum Video Length (Seconds)'. As such, the new 'Feed Rule' was not saved."
                    elif program_feed_rule_override_min_video_length_new_test == 'not_number':
                        manage_programs_message += f"{current_time()} ERROR: A number is required for 'Override Minimum Video Length (Seconds)'. As such, the new 'Feed Rule' was not saved."
                    elif program_feed_rule_override_min_video_length_new_test == 'not_positive':
                        manage_programs_message += f"{current_time()} ERROR: A positive integer is required for 'Override Minimum Video Length (Seconds)'. As such, the new 'Feed Rule' was not saved."
                    else:
                        manage_programs_message += f"{current_time()} ERROR: 'Override Minimum Video Length (Seconds)' was unable to be evaluated. As such, the new 'Feed Rule' was not saved."

                else:
                    write_feed_rules = True
                    feed_rules_add_count = int(feed_rules_add_count) + 1

                    program_feed_rule_active_new_input = None
                    program_feed_rule_name_new_input = None
                    program_feed_rule_provider_new_input = None
                    program_feed_rule_date_range_new_input = None

                    program_feed_rule_active_new_input = 'On' if request.form.get('program_feed_rule_active_new', None) in ['on', 'On', 'ON'] else 'Off'
                    program_feed_rule_name_new_input = request.form.get('program_feed_rule_name_new', None)
                    program_feed_rule_provider_new_input = request.form.get('program_feed_rule_provider_new', None)
                    program_feed_rule_date_range_new_input = request.form.get('program_feed_rule_date_range_new', None)

                    feed_rules.append({
                        'feed_rule_id': get_next_feed_rule_id(feed_rules),
                        'feed_rule_active': program_feed_rule_active_new_input,
                        'feed_rule_name': program_feed_rule_name_new_input,
                        'provider': program_feed_rule_provider_new_input,
                        'date_range': program_feed_rule_date_range_new_input,
                        'override_min_video_length': program_feed_rule_override_min_video_length_new_input
                    })

            # Get new Feed Map
            program_feed_map_action_new_input = None
            program_feed_map_action_new_input = request.form.get('program_feed_map_action_new', 'error')

            if program_feed_map_action_new_input == 'error':
                if manage_programs_message not in [None, '']:
                    manage_programs_message += f"\n"
                manage_programs_message += f"{current_time()} ERROR: Unable to run action against new 'Feed Map'."

            elif program_feed_map_action_new_input == 'add':
                program_feed_map_source_field_compare_id_new_input = None
                program_feed_map_source_field_string_new_input = None

                program_feed_map_source_field_compare_id_new_input = request.form.get('program_feed_map_source_field_compare_id_new', None)
                program_feed_map_source_field_string_new_input = request.form.get('program_feed_map_source_field_string_new', None)

                program_feed_map_source_field_string_new_test = None

                if program_feed_map_source_field_string_new_input in ['', None]:
                    program_feed_map_source_field_string_new_test = 'blank'
                elif program_feed_map_source_field_compare_id_new_input in ['greater', 'greater_equal', 'less', 'less_equal']:
                    program_feed_map_source_field_string_new_test = positive_integer_test(program_feed_map_source_field_string_new_input, True)
                else:
                    program_feed_map_source_field_string_new_test = 'pass'

                if program_feed_map_source_field_string_new_test != 'pass':

                    if manage_programs_message not in [None, '']:
                        manage_programs_message += f"\n"

                    if program_feed_map_source_field_string_new_test == 'blank':
                        manage_programs_message += f"{current_time()} ERROR: 'THIS value' is required and cannot be left blank. As such, the new 'Feed Map' was not saved."
                    elif program_feed_map_source_field_string_new_test == 'unknown':
                        manage_programs_message += f"{current_time()} ERROR: An unknown issue happened in relation to 'THIS value'. As such, the new 'Feed Map' was not saved."
                    elif program_feed_map_source_field_string_new_test == 'not_number':
                        manage_programs_message += f"{current_time()} ERROR: When using a relational operator for 'THEN check IF field', a number is required for 'THIS value'. As such, the new 'Feed Map' was not saved."
                    elif program_feed_map_source_field_string_new_test == 'not_positive':
                        manage_programs_message += f"{current_time()} ERROR: When using a relational operator for 'THEN check IF field', a positive integer is required for 'THIS value'. As such, the new 'Feed Map' was not saved."
                    else:
                        manage_programs_message += f"{current_time()} ERROR: 'THIS value' was unable to be evaluated. As such, the new 'Feed Map' was not saved."

                else:
                    write_feed_maps = True
                    feed_maps_add_count = int(feed_maps_add_count) + 1

                    program_feed_map_active_new_input = None
                    program_feed_map_name_new_input = None
                    program_feed_map_source_provider_new_input = None
                    program_feed_map_source_field_solo_new_input = None
                    program_feed_map_target_status_new_input = None
                    program_feed_map_target_label_ids_new_input = []
                    program_feed_map_target_action_new_input = None

                    program_feed_map_active_new_input = 'On' if request.form.get('program_feed_map_active_new', None) in ['on', 'On', 'ON'] else 'Off'
                    program_feed_map_name_new_input = request.form.get('program_feed_map_name_new', None)
                    program_feed_map_source_provider_new_input = request.form.get('program_feed_map_source_provider_new', None)
                    program_feed_map_source_field_solo_new_input = request.form.get('program_feed_map_source_field_solo_new', None)
                    program_feed_map_target_status_new_input = 'unwatched' if request.form.get('program_feed_map_target_status_new', None) in ['on', 'On', 'ON', 'unwatched', 'Unwatched', 'UNWATCHED'] else 'watched'
                    program_feed_map_target_label_ids_new_input = request.form.getlist('program_feed_map_target_label_ids_new')
                    program_feed_map_target_action_new_input = request.form.get('program_feed_map_target_action_new', None)

                    feed_maps.append({
                        'feed_map_id': get_next_feed_map_id(feed_maps),
                        'feed_map_active': program_feed_map_active_new_input,
                        'feed_map_name': program_feed_map_name_new_input,
                        'source_provider': program_feed_map_source_provider_new_input,
                        'source_field': program_feed_map_source_field_solo_new_input,
                        'source_field_compare_id': program_feed_map_source_field_compare_id_new_input,
                        'source_field_string': program_feed_map_source_field_string_new_input,
                        'target_status': program_feed_map_target_status_new_input,
                        'target_label_ids': program_feed_map_target_label_ids_new_input,
                        'target_action': program_feed_map_target_action_new_input
                    })

            # Get existing Feed Rules
            program_feed_rule_id_inputs = {}
            program_feed_rule_active_inputs = {}
            program_feed_rule_name_inputs = {}
            program_feed_rule_provider_inputs = {}
            program_feed_rule_date_range_inputs = {}
            program_feed_rule_override_min_video_length_inputs = {}
            program_feed_rule_action_inputs = {}
            feed_rules_inputs = []
            delete_feed_rules_inputs = []
            save_feed_rules_inputs = []

            for key in request.form.keys():

                if key.startswith('program_feed_rule_id_'):
                    index = key.split('_')[-1]
                    program_feed_rule_id_inputs[index] = request.form.get(key, 'error')

                if key.startswith('program_feed_rule_active_'):
                    index = key.split('_')[-1]
                    program_feed_rule_active_inputs[index] = 'On' if request.form.get(key, None) in ['on', 'On', 'ON'] else 'Off'

                if key.startswith('program_feed_rule_name_'):
                    index = key.split('_')[-1]
                    program_feed_rule_name_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_rule_provider_'):
                    index = key.split('_')[-1]
                    program_feed_rule_provider_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_rule_date_range_'):
                    index = key.split('_')[-1]
                    program_feed_rule_date_range_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_rule_override_min_video_length_'):
                    index = key.split('_')[-1]
                    program_feed_rule_override_min_video_length_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_rule_action_'):
                    index = key.split('_')[-1]
                    program_feed_rule_action_inputs[index] = request.form.get(key, 'none')

            for row in program_feed_rule_id_inputs:
                program_feed_rule_id_input = None
                program_feed_rule_active_input = None
                program_feed_rule_name_input = None
                program_feed_rule_provider_input = None
                program_feed_rule_date_range_input = None
                program_feed_rule_override_min_video_length_input = None
                program_feed_rule_action_input = None

                program_feed_rule_id_input = program_feed_rule_id_inputs.get(row, None)
                program_feed_rule_active_input = program_feed_rule_active_inputs.get(row, None)
                program_feed_rule_name_input = program_feed_rule_name_inputs.get(row, None)
                program_feed_rule_provider_input = program_feed_rule_provider_inputs.get(row, None)
                program_feed_rule_date_range_input = program_feed_rule_date_range_inputs.get(row, None)
                program_feed_rule_override_min_video_length_input = program_feed_rule_override_min_video_length_inputs.get(row, None)
                program_feed_rule_action_input = program_feed_rule_action_inputs.get(row, None)

                feed_rules_inputs.append({
                    'feed_rule_id': program_feed_rule_id_input,
                    'feed_rule_active': program_feed_rule_active_input,
                    'feed_rule_name': program_feed_rule_name_input,
                    'provider': program_feed_rule_provider_input,
                    'date_range': program_feed_rule_date_range_input,
                    'override_min_video_length': program_feed_rule_override_min_video_length_input,
                    'action': program_feed_rule_action_input
                })

            for feed_rules_input in feed_rules_inputs:

                if feed_rules_input['action'] == 'delete':
                    delete_feed_rules_inputs.append(feed_rules_input['feed_rule_id'])

                elif feed_rules_input['action'] == 'save':
                    save_feed_rules_inputs.append(feed_rules_input)

            if delete_feed_rules_inputs or save_feed_rules_inputs:
                write_feed_rules = True

                if delete_feed_rules_inputs:
                    feed_rules_delete_count = len(delete_feed_rules_inputs)

                if save_feed_rules_inputs:
                    feed_rules_save_count = len(save_feed_rules_inputs)

            for save_feed_rules_input in save_feed_rules_inputs:
                for feed_rule in feed_rules:
                    if save_feed_rules_input['feed_rule_id'] == feed_rule['feed_rule_id']:
                        feed_rule['feed_rule_active'] = save_feed_rules_input['feed_rule_active']
                        feed_rule['feed_rule_name'] = save_feed_rules_input['feed_rule_name']

                        if feed_rule['feed_rule_name'] in ['', None]:
                            feed_rule_name = f"Unnamed - ID {feed_rule['feed_rule_id']}"
                        else:
                            feed_rule_name = feed_rule['feed_rule_name']

                        feed_rule['provider'] = save_feed_rules_input['provider']
                        feed_rule['date_range'] = save_feed_rules_input['date_range']

                        program_feed_rule_override_min_video_length_test = None
                        if save_feed_rules_input['override_min_video_length'] in ['', None]:
                            program_feed_rule_override_min_video_length_test = 'pass'
                        else:
                            program_feed_rule_override_min_video_length_test = positive_integer_test(save_feed_rules_input['override_min_video_length'], True)

                        if program_feed_rule_override_min_video_length_test != 'pass':

                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"

                            if program_feed_rule_override_min_video_length_new_test == 'unknown':
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Rule '{feed_rule_name}', an unknown issue happened in relation to 'Override Minimum Video Length (Seconds)'. As such, this field has reverted to its previous value."
                            elif program_feed_rule_override_min_video_length_new_test == 'not_number':
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Rule '{feed_rule_name}', a number is required for 'Override Minimum Video Length (Seconds)'. As such, this field has reverted to its previous value."
                            elif program_feed_rule_override_min_video_length_new_test == 'not_positive':
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Rule '{feed_rule_name}', a positive integer is required for 'Override Minimum Video Length (Seconds)'. As such, this field has reverted to its previous value."
                            else:
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Rule '{feed_rule_name}', 'Override Minimum Video Length (Seconds)' was unable to be evaluated. As such, this field has reverted to its previous value."

                        else:
                            feed_rule['override_min_video_length'] = save_feed_rules_input['override_min_video_length']

            feed_rules = [feed_rule for feed_rule in feed_rules if feed_rule['feed_rule_id'] not in delete_feed_rules_inputs]

            # Get existing Feed Maps
            program_feed_map_id_inputs = {}
            program_feed_map_active_inputs = {}
            program_feed_map_name_inputs = {}
            program_feed_map_source_provider_inputs = {}
            program_feed_map_source_field_solo_inputs = {}
            program_feed_map_source_field_compare_id_inputs = {}
            program_feed_map_source_field_string_inputs = {}
            program_feed_map_target_status_inputs = {}
            program_feed_map_target_label_ids_inputs = {}
            program_feed_map_target_action_inputs = {}
            program_feed_map_action_inputs = {}
            feed_maps_inputs = []
            delete_feed_maps_inputs = []
            save_feed_maps_inputs = []

            for key in request.form.keys():

                if key.startswith('program_feed_map_id_'):
                    index = key.split('_')[-1]
                    program_feed_map_id_inputs[index] = request.form.get(key, 'error')

                if key.startswith('program_feed_map_active_'):
                    index = key.split('_')[-1]
                    program_feed_map_active_inputs[index] = 'On' if request.form.get(key, None) in ['on', 'On', 'ON'] else 'Off'

                if key.startswith('program_feed_map_name_'):
                    index = key.split('_')[-1]
                    program_feed_map_name_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_map_source_provider_'):
                    index = key.split('_')[-1]
                    program_feed_map_source_provider_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_map_source_field_solo_'):
                    index = key.split('_')[-1]
                    program_feed_map_source_field_solo_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_map_source_field_compare_id_'):
                    index = key.split('_')[-1]
                    program_feed_map_source_field_compare_id_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_map_source_field_string_'):
                    index = key.split('_')[-1]
                    program_feed_map_source_field_string_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_map_target_status_'):
                    index = key.split('_')[-1]
                    program_feed_map_target_status_inputs[index] = 'unwatched' if request.form.get(key, None) in ['on', 'On', 'ON', 'unwatched', 'Unwatched', 'UNWATCHED'] else 'watched'

                if key.startswith('program_feed_map_target_label_ids_'):
                    index = key.split('_')[-1]
                    program_feed_map_target_label_ids_inputs[index] = request.form.getlist(key)

                if key.startswith('program_feed_map_target_action_'):
                    index = key.split('_')[-1]
                    program_feed_map_target_action_inputs[index] = request.form.get(key, None)

                if key.startswith('program_feed_map_action_'):
                    index = key.split('_')[-1]
                    program_feed_map_action_inputs[index] = request.form.get(key, None)

            for row in program_feed_map_id_inputs:
                program_feed_map_id_input = None
                program_feed_map_active_input = None
                program_feed_map_name_input = None
                program_feed_map_source_provider_input = None
                program_feed_map_source_field_solo_input = None
                program_feed_map_source_field_compare_id_input = None
                program_feed_map_source_field_string_input = None
                program_feed_map_target_status_input = None
                program_feed_map_target_label_ids_input = []
                program_feed_map_target_action_input = None
                program_feed_map_action_input = None

                program_feed_map_id_input = program_feed_map_id_inputs.get(row, None)
                program_feed_map_active_input = program_feed_map_active_inputs.get(row, None)
                program_feed_map_name_input = program_feed_map_name_inputs.get(row, None)
                program_feed_map_source_provider_input = program_feed_map_source_provider_inputs.get(row, None)
                program_feed_map_source_field_solo_input = program_feed_map_source_field_solo_inputs.get(row, None)
                program_feed_map_source_field_compare_id_input = program_feed_map_source_field_compare_id_inputs.get(row, None)
                program_feed_map_source_field_string_input = program_feed_map_source_field_string_inputs.get(row, None)
                program_feed_map_target_status_input = program_feed_map_target_status_inputs.get(row, None)
                program_feed_map_target_label_ids_input = program_feed_map_target_label_ids_inputs.get(row, [])
                program_feed_map_target_action_input = program_feed_map_target_action_inputs.get(row, None)
                program_feed_map_action_input = program_feed_map_action_inputs.get(row, None)

                feed_maps_inputs.append({
                    'feed_map_id': program_feed_map_id_input,
                    'feed_map_active': program_feed_map_active_input,
                    'feed_map_name': program_feed_map_name_input,
                    'source_provider': program_feed_map_source_provider_input,
                    'source_field': program_feed_map_source_field_solo_input,
                    'source_field_compare_id': program_feed_map_source_field_compare_id_input,
                    'source_field_string': program_feed_map_source_field_string_input,
                    'target_status': program_feed_map_target_status_input,
                    'target_label_ids': program_feed_map_target_label_ids_input,
                    'target_action': program_feed_map_target_action_input,
                    'action': program_feed_map_action_input
                })

            for feed_maps_input in feed_maps_inputs:

                if feed_maps_input['action'] == 'delete':
                    delete_feed_maps_inputs.append(feed_maps_input['feed_map_id'])

                elif feed_maps_input['action'] == 'save':
                    save_feed_maps_inputs.append(feed_maps_input)

            if delete_feed_maps_inputs or save_feed_maps_inputs:
                write_feed_maps = True

                if delete_feed_maps_inputs:
                    feed_maps_delete_count = len(delete_feed_maps_inputs)

                if save_feed_maps_inputs:
                    feed_maps_save_count = len(save_feed_maps_inputs)

            for save_feed_maps_input in save_feed_maps_inputs:
                for feed_map in feed_maps:
                    if save_feed_maps_input['feed_map_id'] == feed_map['feed_map_id']:
                        feed_map['feed_map_active'] = save_feed_maps_input['feed_map_active']
                        feed_map['feed_map_name'] = save_feed_maps_input['feed_map_name']

                        if feed_map['feed_map_name'] in ['', None]:
                            feed_map_name = f"Unnamed - ID {feed_map['feed_map_id']}"
                        else:
                            feed_map_name = feed_map['feed_map_name']

                        feed_map['source_provider'] = save_feed_maps_input['source_provider']
                        feed_map['source_field'] = save_feed_maps_input['source_field']
                        feed_map['target_status'] = save_feed_maps_input['target_status']
                        feed_map['target_label_ids'] = save_feed_maps_input['target_label_ids']
                        feed_map['target_action'] = save_feed_maps_input['target_action']
                        feed_map['action'] = save_feed_maps_input['action']

                        program_feed_map_source_field_string_test = None

                        if save_feed_maps_input['source_field_string'] in ['', None]:
                            program_feed_map_source_field_string_test = 'blank'
                        elif save_feed_maps_input['source_field_compare_id'] in ['greater', 'greater_equal', 'less', 'less_equal']:
                            program_feed_map_source_field_string_test = positive_integer_test(save_feed_maps_input['source_field_string'], True)
                        else:
                            program_feed_map_source_field_string_test = 'pass'

                        if program_feed_map_source_field_string_test != 'pass':

                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"

                            if program_feed_map_source_field_string_test == 'blank':
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Map '{feed_map_name}', 'THIS value' is required and cannot be left blank. As such, this field, along with 'THEN check IF field' have reverted to their previous values."
                            elif program_feed_map_source_field_string_test == 'unknown':
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Map '{feed_map_name}', an unknown issue happened in relation to 'THIS value', along with 'THEN check IF field'. As such, these fields have reverted to their previous values."
                            elif program_feed_map_source_field_string_test == 'not_number':
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Map '{feed_map_name}', when using a relational operator for 'THEN check IF field', a number is required for 'THIS value'. As such, these fields have reverted to their previous values."
                            elif program_feed_map_source_field_string_test == 'not_positive':
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Map '{feed_map_name}', when using a relational operator for 'THEN check IF field', a positive integer is required for 'THIS value'. As such, these fields have reverted to their previous values."
                            else:
                                manage_programs_message += f"{current_time()} ERROR: For saved Feed Map '{feed_map_name}', 'THIS value' was unable to be evaluated, along with 'THEN check IF field'. As such, these fields have reverted to their previous values."

                        else:

                            feed_map['source_field_compare_id'] = save_feed_maps_input['source_field_compare_id']
                            feed_map['source_field_string'] = save_feed_maps_input['source_field_string']

            feed_maps = [feed_map for feed_map in feed_maps if feed_map['feed_map_id'] not in delete_feed_maps_inputs]

            # Write data back to files
            if write_feed_rules:

                if not feed_rules:
                    feed_rules.append(temp_record_feed_rules)
                    run_empty_rows_feed_rules = True

                write_data(csv_slm_feed_rules, feed_rules)
                if run_empty_rows_feed_rules:
                    remove_empty_row(csv_slm_feed_rules)

            if write_feed_maps:

                if not feed_maps:
                    feed_maps.append(temp_record_feed_maps)
                    run_empty_rows_feed_maps = True

                write_data(csv_slm_feed_maps, feed_maps)
                if run_empty_rows_feed_maps:
                    remove_empty_row(csv_slm_feed_maps)

            if manage_programs_message not in [None, '']:
                manage_programs_message += f"\n"

            if (
                ( int(feed_rules_add_count) == 0 ) and
                ( int(feed_rules_save_count) == 0 ) and
                ( int(feed_rules_delete_count) == 0 ) and
                ( int(feed_maps_add_count) == 0 ) and
                ( int(feed_maps_save_count) == 0 ) and
                ( int(feed_maps_delete_count) == 0 )
            ):

                manage_programs_message += f"{current_time()} WARNING: No actions and/or allowable actions selected for 'Feed Rules' and 'Feed Maps', therefore nothing has been executed."

            else:

                manage_programs_message += f"{current_time()} INFO: Summary of 'Feed Rules' and 'Feed Maps' actions that have been executed:"
                if int(feed_rules_add_count) > 0:
                    manage_programs_message += f"\n"
                    manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    manage_programs_message += f"Feed Rules Add(s): {feed_rules_add_count}"
                if int(feed_rules_save_count) > 0:
                    manage_programs_message += f"\n"
                    manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    manage_programs_message += f"Feed Rules Save(s): {feed_rules_save_count}"
                if int(feed_rules_delete_count) > 0:
                    manage_programs_message += f"\n"
                    manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    manage_programs_message += f"Feed Rules Delete(s): {feed_rules_delete_count}"
                if int(feed_maps_add_count) > 0:
                    manage_programs_message += f"\n"
                    manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    manage_programs_message += f"Feed Maps Add(s): {feed_maps_add_count}"
                if int(feed_maps_save_count) > 0:
                    manage_programs_message += f"\n"
                    manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    manage_programs_message += f"Feed Maps Save(s): {feed_maps_save_count}"
                if int(feed_maps_delete_count) > 0:
                    manage_programs_message += f"\n"
                    manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    manage_programs_message += f"Feed Maps Delete(s): {feed_maps_delete_count}"

        elif manage_programs_action in [
            'manage_programs_cancel',
            'slm_manage_programs_search_results_cancel'
        ]:
            slm_manage_programs_search_results_flag = None
            slm_manage_programs_modify_program_flag = None
            slm_manage_programs_modify_program_scollbar_flag = None
            slm_manage_programs_program_modify_available_flag = None
            program_search_results_prior = []
            program_search_results_resort_alpha_flag = True
            select_programs_to_edit = []
            settings_country_code_input_prior = None
            settings_language_code_input_prior = None
            entry_id_selected_prior = None
            program_modify_details_selected_prior = []

            if manage_programs_action == 'manage_programs_cancel':
                modify_entry_id = None
                program_add_prior = ''
                program_add_manual_prior = ''
                program_add_import_playlist_prior = ''
                date_new_default_start_prior = datetime.datetime.now().strftime('%Y-%m-%d')
                date_new_default_end_prior = datetime.datetime.now().strftime('%Y-%m-%d')

        if select_programs_to_edit or entry_id_selected_prior:
            bookmarks = read_data(csv_bookmarks)
            bookmarks_statuses = read_data(csv_bookmarks_status)
            slm_labels = read_data(csv_slm_labels)
            label_maps = read_data(csv_slm_label_maps)
            subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)

            # Write (or skip) item updates
            if manage_programs_action.startswith('program_modify_execute_'):

                if manage_programs_action.startswith('program_modify_execute_yes_'):

                    if object_type_selected_prior == 'CHANNEL':

                        subscribed_video_channel_active_selected_input = None
                        subscribed_video_channel_name_selected_input = None
                        subscribed_video_channel_user_selected_input = None
                        subscribed_video_channel_description_selected_input = None
                        subscribed_video_channel_image_selected_input = None
                        subscribed_video_channel_streaming_service_group_selected_input = None

                        subscribed_video_channel_selected_action_input = request.form.get('subscribed_video_channel_selected_action')
                        subscribed_video_channel_name_selected_input = request.form.get('subscribed_video_channel_name_selected')

                        if subscribed_video_channel_selected_action_input in ['save', 'delete']:

                            if len(subscribed_video_channels) > 0:
                                if subscribed_video_channels:
                                    temp_record = create_temp_record(subscribed_video_channels[0].keys())
                                else:
                                    temp_record = initial_data(csv_slm_subscribed_video_channels)[0]
                                run_empty_rows = False

                            for subscribed_video_channel in subscribed_video_channels:
                                if subscribed_video_channel['channel_id'] == entry_id_selected_prior:

                                    if subscribed_video_channel_selected_action_input == 'delete':

                                        subscribed_video_channels.remove(subscribed_video_channel)
                                        entry_id_selected_prior = None
                                        object_type_selected_prior = None
                                        bookmark_action_prior = None
                                        override_program_sort_prior = None
                                        
                                        manage_programs_message = f"{current_time()} INFO: Video Channel '{subscribed_video_channel_name_selected_input}' deleted."

                                    elif subscribed_video_channel_selected_action_input == 'save':

                                        subscribed_video_channel_active_selected_input = 'On' if request.form.get('subscribed_video_channel_active_selected') in ['On', 'on'] else 'Off'
                                        subscribed_video_channel_user_selected_input = request.form.get('subscribed_video_channel_user_selected')
                                        subscribed_video_channel_description_selected_input = request.form.get('subscribed_video_channel_description_selected')
                                        subscribed_video_channel_image_selected_input = request.form.get('subscribed_video_channel_image_selected')
                                        subscribed_video_channel_streaming_service_group_selected_input = request.form.get('subscribed_video_channel_streaming_service_group_selected')

                                        subscribed_video_channel['channel_active'] = subscribed_video_channel_active_selected_input
                                        subscribed_video_channel['channel_name'] = subscribed_video_channel_name_selected_input
                                        subscribed_video_channel['channel_user'] = subscribed_video_channel_user_selected_input
                                        subscribed_video_channel['channel_description'] = subscribed_video_channel_description_selected_input
                                        subscribed_video_channel['channel_image'] = subscribed_video_channel_image_selected_input
                                        subscribed_video_channel['channel_streaming_service_group'] = subscribed_video_channel_streaming_service_group_selected_input
                                        
                                        manage_programs_message = f"{current_time()} INFO: Updates to Video Channel '{subscribed_video_channel_name_selected_input}' saved."

                                    break

                            if not subscribed_video_channels:
                                subscribed_video_channels.append(temp_record)
                                run_empty_rows = True

                            if len(subscribed_video_channels) > 1:
                                subscribed_video_channels = sorted(subscribed_video_channels, key=lambda x: sort_key(x["channel_name"].casefold()))

                            write_data(csv_slm_subscribed_video_channels, subscribed_video_channels)
                            if run_empty_rows:
                                remove_empty_row(csv_slm_subscribed_video_channels)

                        elif subscribed_video_channel_selected_action_input == 'none':

                            manage_programs_message = f"{current_time()} INFO: Nothing modified for Video Channel '{subscribed_video_channel_name_selected_input}'. Please select an action to perform first!"

                    else:
                        
                        # Bookmarks
                        field_bookmark_selected_action_input = None
                        field_title_selected_input = None
                        field_release_year_selected_input = None
                        field_release_year_selected_test = None
                        field_bookmark_action_selected_input = None
                        field_bookmark_action_selected_prior = None
                        field_override_program_sort_input = None
                        field_override_program_sort_prior = None
                        field_url_prior = None
                        field_country_code_prior = None
                        field_language_code_prior = None
                        field_short_description = None
                        field_poster = None
                        
                        field_bookmark_selected_action_input = request.form.get('field_bookmark_selected_action')

                        temp_record = create_temp_record(bookmarks[0].keys())
                        run_empty_rows = False

                        for bookmark in bookmarks:

                            if bookmark['entry_id'] == entry_id_selected_prior:

                                field_url_prior = bookmark['url']
                                field_country_code_prior = bookmark['country_code']
                                field_language_code_prior = bookmark['language_code']

                                if object_type_selected_prior == 'VIDEO':
                                    field_override_program_sort_input = request.form.get('field_override_program_sort_selected')
                                    field_override_program_sort_prior = bookmark['override_program_sort']

                                if field_bookmark_selected_action_input == 'delete':

                                    bookmarks.remove(bookmark)

                                elif field_bookmark_selected_action_input == 'save':

                                    field_title_selected_input = request.form.get('field_title_selected')

                                    if field_title_selected_input is None or field_title_selected_input == '':
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} ERROR: A 'Title' is required! Reverting to previous value."

                                    else:
                                        bookmark['title'] = field_title_selected_input

                                    field_release_year_selected_input = request.form.get('field_release_year_selected')
                                    field_release_year_selected_test = get_release_year(field_release_year_selected_input)

                                    if field_release_year_selected_test != "pass":
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{field_release_year_selected_test} Reverting to previous value."

                                    else:
                                        bookmark['release_year'] = field_release_year_selected_input

                                    field_bookmark_action_selected_input = request.form.get('field_bookmark_action_selected')
                                    field_bookmark_action_selected_prior = bookmark['bookmark_action']
                                    bookmark['bookmark_action'] = field_bookmark_action_selected_input

                                    if import_metadata_options_flag:

                                        if object_type_selected_prior in ['MOVIE', 'SHOW']:
                                            bookmark['override_program_title'] = request.form.get('field_override_program_title_selected')

                                        if object_type_selected_prior in ['SHOW', 'VIDEO']:
                                            bookmark['override_program_summary'] = request.form.get('field_override_program_summary_selected')
                                            bookmark['override_program_image_type'] = request.form.get('field_override_program_image_type_selected')
                                            bookmark['override_program_image_manual'] = request.form.get('field_override_program_image_manual_selected')

                                        if object_type_selected_prior == 'VIDEO':
                                            bookmark['override_program_sort'] = field_override_program_sort_input

                                elif field_bookmark_selected_action_input == 'import':

                                    if not entry_id_selected_prior.startswith('slm') and not entry_id_selected_prior.startswith('int') and object_type_selected_prior in ['MOVIE', 'SHOW']:

                                        movies_shows_search_results = []
                                        movies_shows_search_results = search_bookmark(bookmark['country_code'], bookmark['language_code'], 99, bookmark['title'])
                                        movies_shows_search_results_found_flag = False

                                        if movies_shows_search_results:

                                            for movies_shows_search_result in movies_shows_search_results:
                                                if movies_shows_search_result['entry_id'] == entry_id_selected_prior:

                                                    movies_shows_search_results_found_flag = True

                                                    bookmark['override_program_title'] = movies_shows_search_result['title']

                                                    if object_type_selected_prior == 'SHOW':
                                                        bookmark['override_program_summary'] = movies_shows_search_result['short_description']
                                                        bookmark['override_program_image_type'] = 'manual'
                                                        bookmark['override_program_image_manual'] = movies_shows_search_result['poster']

                                                    elif object_type_selected_prior == 'MOVIE':
                                                        field_short_description = movies_shows_search_result['short_description']
                                                        field_poster = movies_shows_search_result['poster']
                                                    
                                                    break

                                            if not movies_shows_search_results_found_flag:
                                                if manage_programs_message not in [None, '']:
                                                    manage_programs_message += f"\n"
                                                manage_programs_message += f"{current_time()} WARNING: Cannot find program-level metadata."

                                        else:
                                            if manage_programs_message not in [None, '']:
                                                manage_programs_message += f"\n"
                                            manage_programs_message += f"{current_time()} WARNING: No entries found to import program-level metadata."

                                    else:
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} WARNING: Cannot import program-level metadata for manual entries, video groups, or internal control lists."

                                break

                        if not bookmarks:
                            bookmarks.append(temp_record)
                            run_empty_rows = True

                        temp_bookmarks = read_data(csv_bookmarks)
                        if temp_bookmarks != bookmarks:
                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{current_time()} INFO: Executed program-level actions."
                        
                        elif temp_bookmarks == bookmarks and field_bookmark_selected_action_input == 'save':
                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{current_time()} WARNING: Program-level data was saved, but nothing changed from previous values."

                        write_data(csv_bookmarks, bookmarks)
                        if run_empty_rows:
                            remove_empty_row(csv_bookmarks)

                        bookmarks_bookmark_action_lookup = {}
                        bookmarks_bookmark_action_lookup = {bookmark['entry_id']: bookmark['bookmark_action'] for bookmark in bookmarks}

                        # Bookmarks Statuses
                        program_modify_add_episode_selected_action_input = None
                        program_modify_add_episode_selected_action_import_metadata_flag = None
                        program_modify_add_episode_season_input = None
                        program_modify_add_episode_episode_input = None
                        program_modify_add_episode_season_episode_input = None
                        program_modify_add_episode_stream_link_override_input = None
                        program_modify_add_episode_special_action_input = None
                        program_modify_add_episode_season_episode_prefix_input = None
                        program_modify_add_episode_stream_link_override_input = None
                        program_modify_add_episode_special_action_input = None
                        program_modify_add_episode_season_episode_prefix_input = None
                        program_modify_add_episode_override_episode_title_input = None
                        program_modify_add_episode_override_summary_input = None
                        program_modify_add_episode_override_image_input = None
                        program_modify_add_episode_override_duration_input = None
                        program_modify_add_episode_manual_order_input = None

                        program_modify_global_change_selection_input = 'none'
                        program_modify_global_change_selection_input_season_number = None
                        program_modify_global_change_bookmarks_statuses_selected_action_input = 'none'
                        program_modify_global_selection_status_input = None
                        program_modify_global_selection_stream_link_override_input = None
                        program_modify_global_selection_special_action_input = None
                        program_modify_global_selection_season_episode_prefix_input = None
                        program_modify_global_selection_override_episode_title_input = None
                        program_modify_global_selection_override_summary_input = None
                        program_modify_global_selection_override_image_input = None
                        program_modify_global_selection_override_duration_input = None
                        program_modify_global_change_stream_link_override_input = None
                        program_modify_global_change_special_action_input = None
                        program_modify_global_change_season_episode_prefix_input = None
                        program_modify_global_change_override_episode_title_input = None
                        program_modify_global_change_override_summary_input = None
                        program_modify_global_change_override_image_input = None
                        program_modify_global_change_override_duration_input = None

                        program_modify_other_actions_save_manual_order_input = None
                        raw_manual_order_videos_inputs = None
                        manual_order_videos_inputs = []
                        field_manual_order_lookup = {}

                        prior_season_episode_inputs = {}
                        field_status_inputs = {}
                        field_season_episode_inputs = {}
                        field_stream_link_override_inputs = {}
                        field_special_action_inputs = {}
                        field_season_episode_prefix_inputs = {}
                        field_override_episode_title_inputs = {}
                        field_override_summary_inputs = {}
                        field_override_image_inputs = {}
                        field_override_duration_inputs = {}
                        field_bookmarks_statuses_selected_action_inputs = {}

                        prior_season_episode_lookup = {}
                        field_status_lookup = {}
                        field_season_episode_lookup = {}
                        field_stream_link_override_lookup = {}
                        field_special_action_lookup = {}
                        field_season_episode_prefix_lookup = {}
                        field_override_episode_title_lookup = {}
                        field_override_summary_lookup = {}
                        field_override_image_lookup = {}
                        field_override_duration_lookup = {}
                        field_bookmarks_statuses_selected_action_lookup = {}

                        season_episodes = []
                        season_episodes_original_release_date_lookup = {}
                        season_episodes_override_episode_title_lookup = {}
                        season_episodes_override_summary_lookup = {}
                        season_episodes_override_duration_lookup = {}

                        bookmarks_statuses_save_count = 0
                        bookmarks_statuses_save_fail_count = 0
                        bookmarks_statuses_import_count = 0
                        bookmarks_statuses_import_fail_count = 0
                        bookmarks_statuses_hide_count = 0
                        bookmarks_statuses_move_count = 0
                        bookmarks_statuses_hide_move_fail_count = 0
                        bookmarks_statuses_delete_count = 0
                        bookmarks_statuses_delete_list = []

                        if object_type_selected_prior in ['SHOW', 'VIDEO'] and bookmark_action_prior != 'Hide':

                            ### New Episodes/Videos
                            program_modify_add_episode_selected_action_input = request.form.get('program_modify_add_episode_selected_action')

                            if program_modify_add_episode_selected_action_input.startswith('add'):

                                if object_type_selected_prior == 'SHOW':
                                    program_modify_add_episode_season_input = request.form.get('program_modify_add_episode_season')

                                program_modify_add_episode_episode_input = request.form.get('program_modify_add_episode_episode')

                                new_season_episode_test = 0

                                if object_type_selected_prior == "SHOW":

                                    try:
                                        new_episode_num = int(program_modify_add_episode_episode_input)
                                        if new_episode_num >= 0:
                                            new_season_episode_test = new_season_episode_test + 1
                                        else:
                                            if manage_programs_message not in [None, '']:
                                                manage_programs_message += f"\n"
                                            manage_programs_message += f"{current_time()} ERROR: For 'New Episode | Episode Number', please enter a valid numeric value."
                                    except ValueError:
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} ERROR: Invalid input. For 'New Episode | Episode Number', please enter a numeric value."

                                    try:
                                        new_season_num = int(program_modify_add_episode_season_input)
                                        if new_season_num >= 0:
                                            new_season_episode_test = new_season_episode_test + 1
                                        else:
                                            if manage_programs_message not in [None, '']:
                                                manage_programs_message += f"\n"
                                            manage_programs_message += f"{current_time()} ERROR: For 'New Episode | Season Number', please enter a valid numeric value."
                                    except ValueError:
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} ERROR: Invalid input. For 'New Episode | Season Number', please enter a numeric value."

                                elif object_type_selected_prior == "VIDEO":

                                    if program_modify_add_episode_episode_input is None or program_modify_add_episode_episode_input == '':
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} ERROR: Video Name is required for new Videos."
                                    else:
                                        new_season_episode_test = 2

                                if new_season_episode_test == 2:

                                    new_season_episode_error = None

                                    if object_type_selected_prior == "SHOW":

                                        formatted_season = f"S{new_season_num:02d}"
                                        formatted_episode = f"E{new_episode_num:02d}"

                                        program_modify_add_episode_season_episode_input = formatted_season + formatted_episode

                                    elif object_type_selected_prior == "VIDEO":

                                        program_modify_add_episode_season_episode_input = program_modify_add_episode_episode_input

                                    for bookmarks_status in bookmarks_statuses:
                                        if bookmarks_status['entry_id'] == entry_id_selected_prior:
                                            if bookmarks_status['season_episode'] == program_modify_add_episode_season_episode_input:
                                                new_season_episode_error = True
                                                break

                                    if new_season_episode_error:
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} ERROR: '{program_modify_add_episode_season_episode_input}' already exists! Please try again."

                                    else:
                                        program_modify_add_episode_stream_link_override_input = request.form.get('program_modify_add_episode_stream_link_override')
                                        program_modify_add_episode_special_action_input = request.form.get('program_modify_add_episode_special_action')
                                        if object_type_selected_prior == 'SHOW':
                                            program_modify_add_episode_season_episode_prefix_input = request.form.get('program_modify_add_episode_season_episode_prefix')
                                        if import_metadata_options_flag:
                                            program_modify_add_episode_override_episode_title_input = request.form.get('program_modify_add_episode_override_episode_title')
                                            program_modify_add_episode_override_summary_input = request.form.get('program_modify_add_episode_override_summary')
                                            program_modify_add_episode_override_image_input = request.form.get('program_modify_add_episode_override_image')
                                            program_modify_add_episode_override_duration_input = request.form.get('program_modify_add_episode_override_duration')

                                            if program_modify_add_episode_override_duration_input not in ('', None):
                                                try:
                                                    value = int(program_modify_add_episode_override_duration_input)
                                                    if value <= 0:
                                                        program_modify_add_episode_override_duration_input = ''
                                                        if manage_programs_message not in [None, '']:
                                                            manage_programs_message += f"\n"
                                                        manage_programs_message += f"{current_time()} WARNING: New entry added, but if entering a 'Duration Override', it must be a positive integer. Your invalid entry has been removed. Please modify directly."
                                                        program_modify_add_episode_override_duration_input = ''
                                                except (ValueError, TypeError):
                                                    program_modify_add_episode_override_duration_input = ''
                                                    if manage_programs_message not in [None, '']:
                                                        manage_programs_message += f"\n"
                                                    manage_programs_message += f"{current_time()} WARNING: New entry added, but 'Duration Override' must be a positive integer or blank. Your invalid entry has been removed. Please modify directly."
                                                    program_modify_add_episode_override_duration_input = ''

                                        if field_override_program_sort_input == 'manual':
                                            if field_override_program_sort_prior == 'manual':
                                                program_modify_add_episode_manual_order_input = max((int(bookmark_status['manual_order']) for bookmark_status in bookmarks_statuses if bookmark_status['entry_id'] == entry_id_selected_prior and bookmark_status['manual_order'] is not None), default=0) + 1

                                        bookmarks_statuses.append({
                                            "entry_id": entry_id_selected_prior,
                                            "season_episode_id": None,
                                            "season_episode_prefix": program_modify_add_episode_season_episode_prefix_input,
                                            "season_episode": program_modify_add_episode_season_episode_input,
                                            "status": "unwatched",
                                            "stream_link": None,
                                            "stream_link_override": program_modify_add_episode_stream_link_override_input,
                                            "stream_link_file": None,
                                            "special_action": program_modify_add_episode_special_action_input,
                                            "original_release_date": None,
                                            "override_episode_title": program_modify_add_episode_override_episode_title_input,
                                            "override_summary": program_modify_add_episode_override_summary_input,
                                            "override_image": program_modify_add_episode_override_image_input,
                                            "override_duration": program_modify_add_episode_override_duration_input,
                                            "channels_id": None,
                                            "manual_order": program_modify_add_episode_manual_order_input
                                        })

                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} INFO: Added '{program_modify_add_episode_season_episode_input}'! Please review 'Program Details'."

                                        if program_modify_add_episode_selected_action_input.endswith('import'):
                                            program_modify_add_episode_selected_action_import_metadata_flag = True

                            if program_modify_details_selected_prior:

                                ### Global Episodes/Videos Controls
                                program_modify_global_change_selection_input = request.form.get('program_modify_global_change_selection')

                                if program_modify_global_change_selection_input != 'none':

                                    if object_type_selected_prior == 'SHOW' and 'season' in program_modify_global_change_selection_input:
                                        program_modify_global_change_selection_input_season_number = int(program_modify_global_change_selection_input.split('_')[-1][1:])

                                    program_modify_global_change_bookmarks_statuses_selected_action_input = request.form.get('program_modify_global_change_bookmarks_statuses_selected_action')

                                    if program_modify_global_change_bookmarks_statuses_selected_action_input == 'save':

                                        program_modify_global_selection_status_input = request.form.get('program_modify_global_selection_status')
                                        program_modify_global_selection_special_action_input = request.form.get('program_modify_global_selection_special_action')
                                        if import_metadata_options_flag:
                                            program_modify_global_selection_override_episode_title_input = request.form.get('program_modify_global_selection_override_episode_title')
                                            program_modify_global_selection_override_summary_input = request.form.get('program_modify_global_selection_override_summary')
                                            program_modify_global_selection_override_image_input = request.form.get('program_modify_global_selection_override_image')
                                            program_modify_global_selection_override_duration_input = request.form.get('program_modify_global_selection_override_duration')
                                        if object_type_selected_prior == 'SHOW':
                                            program_modify_global_selection_stream_link_override_input = request.form.get('program_modify_global_selection_stream_link_override')
                                            program_modify_global_selection_season_episode_prefix_input = request.form.get('program_modify_global_selection_season_episode_prefix')

                                        if program_modify_global_selection_status_input == 'on':
                                            program_modify_global_change_status_input = 'unwatched' if request.form.get('program_modify_global_change_status') in ['on', 'On', 'ON'] else 'watched'
                                        if program_modify_global_selection_special_action_input == 'on':
                                            program_modify_global_change_special_action_input = request.form.get('program_modify_global_change_special_action')
                                        if import_metadata_options_flag:
                                            if program_modify_global_selection_override_episode_title_input == 'on':
                                                program_modify_global_change_override_episode_title_input = request.form.get('program_modify_global_change_override_episode_title')
                                            if program_modify_global_selection_override_summary_input == 'on':
                                                program_modify_global_change_override_summary_input = request.form.get('program_modify_global_change_override_summary')
                                            if program_modify_global_selection_override_image_input == 'on':
                                                program_modify_global_change_override_image_input = request.form.get('program_modify_global_change_override_image')
                                            if program_modify_global_selection_override_duration_input == 'on':
                                                program_modify_global_change_override_duration_input = request.form.get('program_modify_global_change_override_duration')
                                        if object_type_selected_prior == 'SHOW':
                                            if program_modify_global_selection_stream_link_override_input == 'on':
                                                program_modify_global_change_stream_link_override_input = request.form.get('program_modify_global_change_stream_link_override')
                                            if program_modify_global_selection_season_episode_prefix_input == 'on':
                                                program_modify_global_change_season_episode_prefix_input = request.form.get('program_modify_global_change_season_episode_prefix')

                                        list_program_modify_global_selections = [
                                            program_modify_global_selection_status_input,
                                            program_modify_global_selection_special_action_input,
                                            program_modify_global_selection_override_episode_title_input,
                                            program_modify_global_selection_override_summary_input,
                                            program_modify_global_selection_override_image_input,
                                            program_modify_global_selection_override_duration_input,
                                            program_modify_global_selection_stream_link_override_input,
                                            program_modify_global_selection_season_episode_prefix_input
                                        ]

                                        if not any(list_program_modify_global_selection == 'on' for list_program_modify_global_selection in list_program_modify_global_selections):
                                            if manage_programs_message not in [None, '']:
                                                manage_programs_message += f"\n"
                                            manage_programs_message += f"{current_time()} WARNING: Global action set to 'save', but no fields set as active. Nothing has been updated."

                                ### Manual Order
                                if object_type_selected_prior == 'VIDEO' and field_override_program_sort_input == 'manual' and field_override_program_sort_prior == 'manual':
                                    program_modify_other_actions_save_manual_order_input = request.form.get('program_modify_other_actions_save_manual_order')

                                    if program_modify_other_actions_save_manual_order_input == 'on':

                                        raw_manual_order_videos_inputs = request.form.get('manual_order_videos')
                                        manual_order_videos_inputs = json.loads(raw_manual_order_videos_inputs)
                                        field_manual_order_lookup = {manual_order_videos_input['season_episode']: manual_order_videos_input['manual_order'] for manual_order_videos_input in manual_order_videos_inputs}

                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        manage_programs_message += f"{current_time()} INFO: 'Manual Order' saved!"

                        ### Program Details
                        for key in request.form.keys():

                            if key.startswith('prior_season_episode_'):
                                index = key.split('_')[-1]
                                prior_season_episode_inputs[index] = request.form.get(key)

                            if key.startswith('field_status_'):
                                index = key.split('_')[-1]
                                field_status_inputs[index] = 'unwatched' if request.form.get(key) in ['on', 'On', 'ON'] else 'watched'

                            if object_type_selected_prior != 'MOVIE':
                                if key.startswith('field_season_episode_'):
                                    index = key.split('_')[-1]
                                    field_season_episode_inputs[index] = request.form.get(key)

                            if key.startswith('field_stream_link_override_'):
                                index = key.split('_')[-1]
                                field_stream_link_override_inputs[index] = request.form.get(key)

                            if key.startswith('field_special_action_'):
                                index = key.split('_')[-1]
                                field_special_action_inputs[index] = request.form.get(key)

                            if object_type_selected_prior == 'SHOW':
                                if key.startswith('field_season_episode_prefix_'):
                                    index = key.split('_')[-1]
                                    field_season_episode_prefix_inputs[index] = request.form.get(key)

                            if import_metadata_options_flag:

                                if object_type_selected_prior != 'MOVIE':

                                    if key.startswith('field_override_episode_title_'):
                                        index = key.split('_')[-1]
                                        field_override_episode_title_inputs[index] = request.form.get(key)

                                if key.startswith('field_override_summary_'):
                                    index = key.split('_')[-1]
                                    field_override_summary_inputs[index] = request.form.get(key)

                                if key.startswith('field_override_image_'):
                                    index = key.split('_')[-1]
                                    field_override_image_inputs[index] = request.form.get(key)

                                if key.startswith('field_override_duration_'):
                                    index = key.split('_')[-1]
                                    field_override_duration_inputs[index] = request.form.get(key)

                            if key.startswith('field_bookmarks_statuses_selected_action_'):
                                index = key.split('_')[-1]
                                field_bookmarks_statuses_selected_action_inputs[index] = request.form.get(key)

                        submitted_bookmarks_statuses = []
                        for row in prior_season_episode_inputs:
                            field_status_input = None
                            field_season_episode_input = None
                            field_stream_link_override_input = None
                            field_special_action_input = None
                            field_season_episode_prefix_input = None
                            field_override_episode_title_input = None
                            field_override_summary_input = None
                            field_override_image_input = None
                            field_override_duration_input = None
                            field_bookmarks_statuses_selected_action_input = None
                            prior_season_episode_input = None

                            prior_season_episode_input = prior_season_episode_inputs.get(row)
                            field_status_input = field_status_inputs.get(row, 'watched')
                            if object_type_selected_prior != 'MOVIE':
                                field_season_episode_input = field_season_episode_inputs.get(row)
                            field_stream_link_override_input = field_stream_link_override_inputs.get(row)
                            field_special_action_input = field_special_action_inputs.get(row)
                            if object_type_selected_prior == 'SHOW':
                                field_season_episode_prefix_input = field_season_episode_prefix_inputs.get(row)
                            if import_metadata_options_flag:
                                if object_type_selected_prior != 'MOVIE':
                                    field_override_episode_title_input = field_override_episode_title_inputs.get(row)
                                field_override_summary_input = field_override_summary_inputs.get(row)
                                field_override_image_input = field_override_image_inputs.get(row)
                                field_override_duration_input = field_override_duration_inputs.get(row)
                            field_bookmarks_statuses_selected_action_input = field_bookmarks_statuses_selected_action_inputs.get(row)
                            
                            submitted_bookmarks_statuses.append({
                                'prior_season_episode': prior_season_episode_input,
                                'status': field_status_input,
                                'season_episode': field_season_episode_input,
                                'stream_link_override': field_stream_link_override_input,
                                'special_action': field_special_action_input,
                                'season_episode_prefix': field_season_episode_prefix_input,
                                'override_episode_title': field_override_episode_title_input,
                                'override_summary': field_override_summary_input,
                                'override_image': field_override_image_input,
                                'override_duration': field_override_duration_input,
                                'bookmarks_statuses_selected_action': field_bookmarks_statuses_selected_action_input
                            })

                        prior_season_episode_lookup = {submitted_bookmarks_status['prior_season_episode'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                        field_status_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['status'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                        if object_type_selected_prior != 'MOVIE':
                            field_season_episode_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['season_episode'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                        field_stream_link_override_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['stream_link_override'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                        field_special_action_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['special_action'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                        if object_type_selected_prior == 'SHOW':
                            field_season_episode_prefix_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['season_episode_prefix'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                        if import_metadata_options_flag:
                            if object_type_selected_prior != 'MOVIE':
                                field_override_episode_title_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['override_episode_title'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                            field_override_summary_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['override_summary'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                            field_override_image_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['override_image'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                            field_override_duration_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['override_duration'] for submitted_bookmarks_status in submitted_bookmarks_statuses}
                        field_bookmarks_statuses_selected_action_lookup = {submitted_bookmarks_status['prior_season_episode']: submitted_bookmarks_status['bookmarks_statuses_selected_action'] for submitted_bookmarks_status in submitted_bookmarks_statuses}

                        ### Reload Episode List
                        if object_type_selected_prior == 'SHOW' and not entry_id_selected_prior.startswith('slm') and not entry_id_selected_prior.startswith('int'):
                            if (
                                ( 'import' in field_bookmarks_statuses_selected_action_lookup.values() ) or
                                ( program_modify_global_change_selection_input != 'none' and program_modify_global_change_bookmarks_statuses_selected_action_input == 'import' ) or
                                ( field_bookmark_action_selected_input != 'Hide' and field_bookmark_action_selected_prior == 'Hide' )
                            ):

                                season_episodes = get_episode_list(entry_id_selected_prior, field_url_prior, field_country_code_prior, field_language_code_prior)
                                season_episodes_original_release_date_lookup = {season_episode['season_episode_id']: season_episode['original_release_date'] for season_episode in season_episodes}
                                season_episodes_override_episode_title_lookup = {season_episode['season_episode_id']: season_episode['override_episode_title'] for season_episode in season_episodes}
                                season_episodes_override_summary_lookup = {season_episode['season_episode_id']: season_episode['override_summary'] for season_episode in season_episodes}
                                season_episodes_override_duration_lookup = {season_episode['season_episode_id']: season_episode['override_duration'] for season_episode in season_episodes}

                        ### Add Back Unhidden
                        if field_bookmark_action_selected_input != 'Hide' and field_bookmark_action_selected_prior == 'Hide':
                            if object_type_selected_prior == 'MOVIE':
                                original_release_date_raw = None
                                unhide_original_release_date = ''
                                original_release_date_raw = get_movie_show_metadata_item(entry_id_selected_prior, field_country_code_prior, field_language_code_prior, 'originalReleaseDate')
                                if original_release_date_raw:
                                    unhide_original_release_date = original_release_date_raw

                                bookmarks_statuses.append({
                                    "entry_id": entry_id_selected_prior,
                                    "season_episode_id": None,
                                    "season_episode_prefix": None,
                                    "season_episode": None,
                                    "status": "unwatched",
                                    "stream_link": None,
                                    "stream_link_override": None,
                                    "stream_link_file": None,
                                    "special_action": "None",
                                    "original_release_date": unhide_original_release_date,
                                    "override_episode_title": None,
                                    "override_summary": None,
                                    "override_image": None,
                                    "override_duration": None,
                                    "channels_id": None,
                                    "manual_order": None
                                })

                            elif object_type_selected_prior == 'SHOW':
                                for season_episode in season_episodes:
                                    bookmarks_statuses.append({
                                        "entry_id": entry_id_selected_prior,
                                        "season_episode_id": season_episode['season_episode_id'],
                                        "season_episode_prefix": None,
                                        "season_episode": season_episode['season_episode'],
                                        "status": "unwatched",
                                        "stream_link": None,
                                        "stream_link_override": None,
                                        "stream_link_file": None,
                                        "special_action": "None",
                                        "original_release_date": season_episode['original_release_date'],
                                        "override_episode_title": None,
                                        "override_summary": None,
                                        "override_image": None,
                                        "override_duration": None,
                                        "channels_id": None,
                                        "manual_order": None
                                    })  

                        ### Modify Bookmarks Statuses
                        if bookmarks_statuses:
                            temp_record = create_temp_record(bookmarks_statuses[0].keys())
                        else:
                            temp_record = initial_data(csv_bookmarks_status)[0]
                        run_empty_rows = False

                        new_manual_order = max((int(bookmark_status['manual_order']) for bookmark_status in bookmarks_statuses if bookmark_status['entry_id'] == entry_id_selected_prior and not bookmark_status['manual_order'] in [None, '']), default=0) + 1

                        for bookmarks_status in bookmarks_statuses:
                            if bookmarks_status['entry_id'] == entry_id_selected_prior:

                                check_season_episode = bookmarks_status['season_episode']
                                check_season_episode_id = bookmarks_status['season_episode_id']
                                bookmarks_statuses_selected_action = field_bookmarks_statuses_selected_action_lookup.get(check_season_episode, 'none')

                                check_season_episode_season_number = None
                                if object_type_selected_prior == 'SHOW' and 'season' in program_modify_global_change_selection_input:
                                    check_season_episode_season_number = int(check_season_episode.split('E')[0][1:])

                                global_match_season_episode = False
                                if object_type_selected_prior in ['SHOW', 'VIDEO'] and program_modify_global_change_selection_input != 'none':
                                    if (
                                        ( program_modify_global_change_selection_input == 'all' ) or
                                        ( program_modify_global_change_selection_input == 'visible' and check_season_episode in prior_season_episode_lookup ) or
                                        ( program_modify_global_change_selection_input.startswith('all_season_') and int(check_season_episode_season_number) == int(program_modify_global_change_selection_input_season_number) ) or
                                        ( program_modify_global_change_selection_input.startswith('before_season_') and int(check_season_episode_season_number) <= int(program_modify_global_change_selection_input_season_number) )
                                    ):
                                        global_match_season_episode = True

                                ###### Delete or Hide Program
                                if(
                                    ( field_bookmark_selected_action_input == 'delete' ) or
                                    ( bookmarks_statuses_selected_action ==  'delete' ) or
                                    ( field_bookmark_action_selected_input == 'Hide' and field_bookmark_action_selected_prior != 'Hide' and object_type_selected_prior in ['MOVIE', 'SHOW'] ) or
                                    ( global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input == 'delete' )
                                ):

                                    bookmarks_statuses_delete_list.append(bookmarks_status)
                                    bookmarks_statuses_delete_count = int(bookmarks_statuses_delete_count) + 1

                                ###### Move or Hide Item
                                elif(
                                    ( bookmarks_statuses_selected_action.startswith('move') ) or
                                    ( global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input.startswith('move') ) or
                                    ( field_bookmark_action_selected_input == 'Hide' and field_bookmark_action_selected_prior != 'Hide' and object_type_selected_prior == 'VIDEO' )
                                ):

                                    move_entry_id = None
                                    if bookmarks_statuses_selected_action.startswith('move'):
                                        move_entry_id = bookmarks_statuses_selected_action.split('_')[1]
                                    elif global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input.startswith('move'):
                                        move_entry_id = program_modify_global_change_bookmarks_statuses_selected_action_input.split('_')[1]
                                    elif field_bookmark_action_selected_input == 'Hide' and field_bookmark_action_selected_prior != 'Hide' and object_type_selected_prior == 'VIDEO':
                                        move_entry_id = hidden_videos_entry_id

                                    if move_entry_id is not None and move_entry_id != '' and bookmarks_status['entry_id'] != move_entry_id and bookmarks_bookmark_action_lookup.get(move_entry_id, "None") != 'Hide':

                                        if bookmarks_status['entry_id'] == hidden_videos_entry_id:
                                            bookmarks_status['status'] = 'unwatched'

                                        if move_entry_id == hidden_videos_entry_id:
                                            bookmarks_status['status'] = 'watched'
                                            bookmarks_statuses_hide_count = int(bookmarks_statuses_hide_count) + 1
                                        else:
                                            bookmarks_statuses_move_count = int(bookmarks_statuses_move_count) + 1

                                        bookmarks_status['entry_id'] = move_entry_id

                                    else:
                                        if manage_programs_message not in [None, '']:
                                            manage_programs_message += f"\n"
                                        if bookmarks_status['entry_id'] == move_entry_id:
                                            if move_entry_id == hidden_videos_entry_id:
                                                manage_programs_message += f"{current_time()} ERROR: '{bookmarks_status['season_episode']}' is already hidden!"
                                            else:
                                                manage_programs_message += f"{current_time()} WARNING: Cannot move '{bookmarks_status['season_episode']}' to its already assigned entry."
                                        elif bookmarks_bookmark_action_lookup.get(move_entry_id, "None") == 'Hide':
                                            manage_programs_message += f"{current_time()} ERROR: Cannot move '{bookmarks_status['season_episode']}' to an entry that is hidden."
                                        else:
                                            manage_programs_message += f"{current_time()} ERROR: Could not move '{bookmarks_status['season_episode']}' to selected entry."
                                        bookmarks_statuses_hide_move_fail_count = int(bookmarks_statuses_hide_move_fail_count) + 1

                                elif(
                                    ( bookmarks_statuses_selected_action ==  'save' ) or
                                    ( global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input == 'save' and any(list_program_modify_global_selection == 'on' for list_program_modify_global_selection in list_program_modify_global_selections) ) or
                                    ( field_override_program_sort_input == 'manual' and field_override_program_sort_prior == 'manual' and program_modify_other_actions_save_manual_order_input == 'on' ) or
                                    ( field_override_program_sort_input == 'manual' and field_override_program_sort_prior != 'manual' ) or
                                    ( field_override_program_sort_input != 'manual' and field_override_program_sort_prior == 'manual' ) or
                                    ( field_bookmark_selected_action_input == 'import' and object_type_selected_prior == 'MOVIE' ) or
                                    ( bookmarks_statuses_selected_action ==  'import' ) or
                                    ( global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input == 'import' ) or
                                    ( program_modify_add_episode_selected_action_import_metadata_flag and check_season_episode == program_modify_add_episode_season_episode_input )
                                ):

                                    field_stream_link_override = None
                                    field_special_action = 'None'
                                    field_original_release_date = None
                                    field_override_episode_title = None
                                    field_override_summary = None
                                    field_override_image = None
                                    field_override_duration = None

                                    field_stream_link_override = bookmarks_status['stream_link_override']
                                    field_special_action = bookmarks_status['special_action']
                                    field_original_release_date = bookmarks_status['original_release_date']
                                    if import_metadata_options_flag:
                                        if object_type_selected_prior in ['SHOW', 'VIDEO']:
                                            field_override_episode_title = bookmarks_status['override_episode_title']
                                        field_override_summary = bookmarks_status['override_summary']
                                        field_override_image = bookmarks_status['override_image']
                                        field_override_duration = bookmarks_status['override_duration']

                                    ###### Save
                                    if(
                                        ( bookmarks_statuses_selected_action ==  'save' ) or
                                        ( global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input == 'save' and any(list_program_modify_global_selection == 'on' for list_program_modify_global_selection in list_program_modify_global_selections) ) or
                                        ( field_override_program_sort_input == 'manual' and field_override_program_sort_prior == 'manual' and program_modify_other_actions_save_manual_order_input == 'on' ) or
                                        ( field_override_program_sort_input == 'manual' and field_override_program_sort_prior != 'manual' ) or
                                        ( field_override_program_sort_input != 'manual' and field_override_program_sort_prior == 'manual' )
                                    ):

                                        field_status = 'unwatched'
                                        field_season_episode_prefix = None
                                        field_season_episode = check_season_episode

                                        field_status = bookmarks_status['status']

                                        if bookmarks_statuses_selected_action ==  'save':
                                            field_status = field_status_lookup.get(check_season_episode, field_status)
                                            field_stream_link_override = field_stream_link_override_lookup.get(check_season_episode, field_stream_link_override)
                                            field_special_action = field_special_action_lookup.get(check_season_episode, field_special_action)
                                            if import_metadata_options_flag:
                                                field_override_summary = field_override_summary_lookup.get(check_season_episode, field_override_summary)
                                                field_override_image = field_override_image_lookup.get(check_season_episode, field_override_image)
                                                field_override_duration = field_override_duration_lookup.get(check_season_episode, field_override_duration)

                                        if object_type_selected_prior in ['SHOW', 'VIDEO']:

                                            if object_type_selected_prior == 'SHOW':
                                                field_season_episode_prefix = bookmarks_status['season_episode_prefix']

                                            if object_type_selected_prior == 'VIDEO':
                                                field_season_episode = bookmarks_status['season_episode']

                                            if bookmarks_statuses_selected_action ==  'save':
                                                if import_metadata_options_flag:
                                                    field_override_episode_title = field_override_episode_title_lookup.get(check_season_episode, field_override_episode_title)

                                                if object_type_selected_prior == 'SHOW':
                                                    field_season_episode_prefix = field_season_episode_prefix_lookup.get(check_season_episode, field_season_episode_prefix)

                                                if object_type_selected_prior == 'VIDEO':
                                                    temp_field_season_episode = field_season_episode_lookup.get(check_season_episode, field_season_episode)
                                                    if check_season_episode == temp_field_season_episode:
                                                        field_season_episode = temp_field_season_episode
                                                    else:
                                                        field_season_episode = check_video_name_unique(bookmarks_statuses, bookmarks_status['entry_id'], temp_field_season_episode)

                                                    if field_season_episode != temp_field_season_episode:
                                                        if manage_programs_message not in [None, '']:
                                                            manage_programs_message += f"\n"
                                                        manage_programs_message += f"{current_time()} WARNING: '{temp_field_season_episode}' already exists in this Video Group and has been renamed to '{field_season_episode}'. Please modify to a unique name, if desired."

                                            if global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input == 'save' and any(list_program_modify_global_selection == 'on' for list_program_modify_global_selection in list_program_modify_global_selections):

                                                if program_modify_global_selection_status_input == 'on':
                                                    field_status = program_modify_global_change_status_input
                                                if program_modify_global_selection_special_action_input == 'on':
                                                    field_special_action = program_modify_global_change_special_action_input
                                                if import_metadata_options_flag:
                                                    if program_modify_global_selection_override_episode_title_input == 'on':
                                                        field_override_episode_title = program_modify_global_change_override_episode_title_input
                                                    if program_modify_global_selection_override_summary_input == 'on':
                                                        field_override_summary = program_modify_global_change_override_summary_input
                                                    if program_modify_global_selection_override_image_input == 'on':
                                                        field_override_image = program_modify_global_change_override_image_input
                                                    if program_modify_global_selection_override_duration_input == 'on':
                                                        field_override_duration = program_modify_global_change_override_duration_input
                                                if object_type_selected_prior == 'SHOW':
                                                    if program_modify_global_selection_stream_link_override_input == 'on':
                                                        field_stream_link_override = program_modify_global_change_stream_link_override_input
                                                    if program_modify_global_selection_season_episode_prefix_input == 'on':
                                                        field_season_episode_prefix = program_modify_global_change_season_episode_prefix_input

                                            if object_type_selected_prior == 'VIDEO':

                                                if(
                                                    ( field_override_program_sort_input == 'manual' and field_override_program_sort_prior == 'manual' and program_modify_other_actions_save_manual_order_input == 'on' ) or
                                                    ( field_override_program_sort_input == 'manual' and field_override_program_sort_prior != 'manual' )
                                                ):

                                                    if field_override_program_sort_input == 'manual' and field_override_program_sort_prior == 'manual' and program_modify_other_actions_save_manual_order_input == 'on':
                                                        bookmarks_status['manual_order'] = field_manual_order_lookup.get(check_season_episode, new_manual_order)

                                                    elif field_override_program_sort_input == 'manual' and field_override_program_sort_prior != 'manual':
                                                        bookmarks_status['manual_order'] = new_manual_order
                                                    
                                                    if bookmarks_status['manual_order'] == new_manual_order:
                                                        new_manual_order = int(new_manual_order) + 1

                                                elif field_override_program_sort_input != 'manual' and field_override_program_sort_prior == 'manual':
                                                    bookmarks_status['manual_order'] = None                                        

                                        bookmarks_status['status'] = field_status
                                        bookmarks_status['stream_link_override'] = field_stream_link_override
                                        bookmarks_status['special_action'] = field_special_action
                                        if object_type_selected_prior in ['SHOW', 'VIDEO']:
                                            if object_type_selected_prior == 'SHOW':
                                                bookmarks_status['season_episode_prefix'] = field_season_episode_prefix
                                            if object_type_selected_prior == 'VIDEO':
                                                bookmarks_status['season_episode'] = field_season_episode

                                        if(
                                            ( bookmarks_statuses_selected_action ==  'save' ) or
                                            ( global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input == 'save' and any(list_program_modify_global_selection == 'on' for list_program_modify_global_selection in list_program_modify_global_selections) )

                                        ):
                                            bookmarks_statuses_save_count = int(bookmarks_statuses_save_count) + 1
                                    
                                    ###### Import Metadata
                                    elif(
                                        ( field_bookmark_selected_action_input == 'import' and object_type_selected_prior == 'MOVIE' ) or
                                        ( bookmarks_statuses_selected_action ==  'import' ) or
                                        ( global_match_season_episode and program_modify_global_change_bookmarks_statuses_selected_action_input == 'import' ) or
                                        ( program_modify_add_episode_selected_action_import_metadata_flag and check_season_episode == program_modify_add_episode_season_episode_input )
                                    ):

                                        if field_special_action == 'Make SLM Stream' and not field_stream_link_override in [None, '']:
                                            field_original_release_date, field_override_episode_title, field_override_summary, field_override_image, field_override_duration = get_video_metadata(field_stream_link_override)

                                        if object_type_selected_prior == 'SHOW':
                                            if not entry_id_selected_prior.startswith('slm') and not check_season_episode_id in [None, '']:
                                                field_original_release_date = season_episodes_original_release_date_lookup.get(check_season_episode_id, None)
                                                if field_special_action != 'Make SLM Stream' or ( field_special_action == 'Make SLM Stream' and field_stream_link_override in [None, ''] ):
                                                    field_override_episode_title = season_episodes_override_episode_title_lookup.get(check_season_episode_id, None)
                                                    field_override_summary = season_episodes_override_summary_lookup.get(check_season_episode_id, None)
                                                    field_override_duration = season_episodes_override_duration_lookup.get(check_season_episode_id, None)
                                            elif entry_id_selected_prior.startswith('slm') or check_season_episode_id in [None, '']:
                                                if field_special_action != 'Make SLM Stream' or ( field_special_action == 'Make SLM Stream' and field_stream_link_override in [None, ''] ):
                                                    field_original_release_date = None
                                                    field_override_episode_title = None
                                                    field_override_summary = None
                                                    field_override_image = None
                                                    field_override_duration = None

                                        if object_type_selected_prior == 'MOVIE':
                                            if not entry_id_selected_prior.startswith('slm'):
                                                field_original_release_date = get_movie_show_metadata_item(entry_id_selected_prior, field_country_code_prior, field_language_code_prior, 'originalReleaseDate')
                                                if field_bookmark_selected_action_input == 'import':
                                                    field_override_summary = field_short_description
                                                    field_override_image = field_poster
                                                if field_special_action != 'Make SLM Stream' or ( field_special_action == 'Make SLM Stream' and field_stream_link_override in [None, ''] ):
                                                    field_override_duration = get_movie_show_metadata_item(entry_id_selected_prior, field_country_code_prior, field_language_code_prior, 'runtime')
                                            elif entry_id_selected_prior.startswith('slm'):
                                                if field_bookmark_selected_action_input == 'import':
                                                    if field_special_action != 'Make SLM Stream' or ( field_special_action == 'Make SLM Stream' and field_stream_link_override in [None, ''] ):
                                                        field_original_release_date = None
                                                        field_override_summary = None
                                                        field_override_image = None
                                                        field_override_duration = None
                                            field_override_episode_title = None

                                        if ( 
                                            ( field_original_release_date is None or field_original_release_date == '' ) and
                                            ( field_override_episode_title is None or field_override_episode_title == '' ) and
                                            ( field_override_summary is None or field_override_summary == '' ) and
                                            ( field_override_image is None or field_override_image == '' ) and
                                            ( field_override_duration is None or field_override_duration == '' )
                                        ):

                                            bookmarks_statuses_import_fail_count = int(bookmarks_statuses_import_fail_count) + 1

                                            if manage_programs_message not in [None, '']:
                                                manage_programs_message += f"\n"

                                            manage_programs_message += f"{current_time()} WARNING: Unable to import metadata for "
                                            if object_type_selected_prior == 'MOVIE':
                                                manage_programs_message += f"this movie."
                                            elif object_type_selected_prior in ['SHOW', 'VIDEO']:
                                                manage_programs_message += f"'{bookmarks_status['season_episode']}'."

                                            if field_special_action != 'Make SLM Stream':
                                                if ( 
                                                    ( entry_id_selected_prior.startswith('slm') ) or
                                                    ( object_type_selected_prior == 'SHOW' and bookmarks_status['season_episode_id'] in [None, ''] )
                                                ):
                                                    manage_programs_message += f" Manual and video entries must have a special action of 'Make SLM Stream'!"

                                        else:

                                            bookmarks_statuses_import_count = int(bookmarks_statuses_import_count) + 1

                                    bookmarks_status['original_release_date'] = field_original_release_date
                                    if import_metadata_options_flag:
                                        if object_type_selected_prior in ['SHOW', 'VIDEO']:
                                            bookmarks_status['override_episode_title'] = field_override_episode_title
                                        bookmarks_status['override_summary'] = field_override_summary
                                        bookmarks_status['override_image'] = field_override_image
                                        bookmarks_status['override_duration'] = field_override_duration

                        if bookmarks_statuses_delete_count > 0:
                            bookmarks_statuses = [bookmarks_status for bookmarks_status in bookmarks_statuses if bookmarks_status not in bookmarks_statuses_delete_list]

                        if not bookmarks_statuses:
                            bookmarks_statuses.append(temp_record)
                            run_empty_rows = True

                        write_data(csv_bookmarks_status, bookmarks_statuses)
                        if run_empty_rows:
                            remove_empty_row(csv_bookmarks_status)

                        temp_manage_programs_message = ''
                        if(
                            ( int(bookmarks_statuses_save_count) > 0 ) or
                            ( int(bookmarks_statuses_save_fail_count) > 0 ) or
                            ( int(bookmarks_statuses_import_count) > 0 ) or
                            ( int(bookmarks_statuses_import_fail_count) > 0 ) or
                            ( int(bookmarks_statuses_hide_count) > 0 ) or
                            ( int(bookmarks_statuses_move_count) > 0 ) or
                            ( int(bookmarks_statuses_hide_move_fail_count) > 0 ) or
                            ( int(bookmarks_statuses_delete_count) > 0 )
                        ):

                            temp_manage_programs_message = f"{current_time()} INFO: Program Details Selected Action(s) Summary..."
                            if int(bookmarks_statuses_save_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Save(s) - Success: {bookmarks_statuses_save_count}"
                            if int(bookmarks_statuses_save_fail_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Save(s) - Fail: {bookmarks_statuses_save_fail_count}"
                            if int(bookmarks_statuses_import_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Metadata Import(s) - Success: {bookmarks_statuses_import_count}"
                            if int(bookmarks_statuses_import_fail_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Metadata Import(s) - Fail: {bookmarks_statuses_import_fail_count}"
                            if int(bookmarks_statuses_hide_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Hide(s) - Success: {bookmarks_statuses_hide_count}"
                            if int(bookmarks_statuses_move_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Move(s) - Success: {bookmarks_statuses_move_count}"
                            if int(bookmarks_statuses_hide_move_fail_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Hide(s) and Move(s) - Fail: {bookmarks_statuses_hide_move_fail_count}"
                            if int(bookmarks_statuses_delete_count) > 0:
                                temp_manage_programs_message += f"\n"
                                temp_manage_programs_message += f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                temp_manage_programs_message += f"Delete(s) - Success: {bookmarks_statuses_delete_count}"

                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += temp_manage_programs_message

                        # Labels
                        program_modify_add_label_input = request.form.get('program_modify_add_label')
                        program_modify_add_label_new = None

                        if program_modify_add_label_input is not None and program_modify_add_label_input != '':

                            program_modify_add_label_new = get_next_label_id(slm_labels)

                            slm_labels.append({
                                "label_id": program_modify_add_label_new,
                                "label_active": 'On',
                                "label_name": program_modify_add_label_input,
                                "label_description": ''
                            })

                            if len(slm_labels) > 1:
                                slm_labels = sorted(slm_labels, key=lambda x: sort_key(x["label_name"].casefold()))

                            write_data(csv_slm_labels, slm_labels)

                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{current_time()} INFO: Added and assigned Label '{program_modify_add_label_input}'. Please modify in 'Manage Providers', if desired."

                        # Label Maps
                        program_modify_other_actions_save_labels_input = request.form.get('program_modify_other_actions_save_labels')

                        if program_modify_other_actions_save_labels_input == 'on' or program_modify_add_label_new or field_bookmark_selected_action_input == 'delete':

                            if program_modify_other_actions_save_labels_input == 'on' or field_bookmark_selected_action_input == 'delete':

                                webpage_label_active_inputs = {}
                                webpage_label_id_inputs = {}

                                webpage_label_maps = get_webpage_label_maps()
                                total_number_of_checkboxes = len(webpage_label_maps)
                                webpage_label_active_inputs = {str(i): 'Off' for i in range(1, total_number_of_checkboxes + 1)}

                            if program_modify_add_label_new and field_bookmark_selected_action_input != 'delete':
                                label_maps.append({
                                    'label_id': program_modify_add_label_new,
                                    'entry_id': entry_id_selected_prior
                                })

                            if label_maps:
                                temp_record = create_temp_record(label_maps[0].keys())
                            else:
                                temp_record = initial_data(csv_slm_label_maps)[0]
                            run_empty_rows = False

                            if program_modify_other_actions_save_labels_input == 'on' or field_bookmark_selected_action_input == 'delete':

                                for key in request.form.keys():
                                    if key.startswith('webpage_label_active_'):
                                        index = key.split('_')[-1]
                                        webpage_label_active_inputs[index] = 'On' if request.form.get(key) == 'on' else 'Off'                        

                                    if key.startswith('webpage_label_id_'):
                                        index = key.split('_')[-1]
                                        webpage_label_id_inputs[index] = request.form.get(key)

                                for index in webpage_label_active_inputs.keys():
                                    webpage_label_active_input = webpage_label_active_inputs.get(index)
                                    webpage_label_id_input = webpage_label_id_inputs.get(index)
                                    label_exists = False

                                    for label_map in label_maps:
                                        if label_map['entry_id'] == entry_id_selected_prior and label_map['label_id'] == webpage_label_id_input:
                                            if webpage_label_active_input == "Off" or field_bookmark_selected_action_input == 'delete':
                                                label_maps.remove(label_map)
                                            label_exists = True
                                            break

                                    if not label_exists and field_bookmark_selected_action_input != 'delete':
                                        if webpage_label_active_input == "On":
                                            label_maps.append({
                                                'label_id': webpage_label_id_input,
                                                'entry_id': entry_id_selected_prior
                                            })

                            if not label_maps:
                                label_maps.append(temp_record)
                                run_empty_rows = True

                            temp_label_maps = read_data(csv_slm_label_maps)
                            if temp_label_maps != label_maps and field_bookmark_selected_action_input != 'delete':
                                if manage_programs_message not in [None, '']:
                                    manage_programs_message += f"\n"
                                manage_programs_message += f"{current_time()} INFO: Updated label assignments!"

                            write_data(csv_slm_label_maps, label_maps)
                            if run_empty_rows:
                                remove_empty_row(csv_slm_label_maps)                        

                        # Final Wrap-Up
                        if field_bookmark_selected_action_input == 'delete':
                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += f"{current_time()} INFO: Deleted program ({entry_id_selected_prior})!"
                            entry_id_selected_prior = None
                            object_type_selected_prior = None
                            bookmark_action_prior = None
                            override_program_sort_prior = None

                        if field_bookmark_selected_action_input == 'generate':
                            if manage_programs_message not in [None, '']:
                                manage_programs_message += f"\n"
                            manage_programs_message += generate_stream_links_single(entry_id_selected_prior)
                            bookmarks_statuses = read_data(csv_bookmarks_status)

                        if field_bookmark_selected_action_input in ['delete', 'generate'] or int(bookmarks_statuses_delete_count) > 0:
                            movie_path, tv_path, video_path = get_movie_tv_path()
                            print(f"{current_time()} INFO: Removed files/directories:")
                            remove_rogue_empty(movie_path, tv_path, video_path, bookmarks_statuses)

                if manage_programs_action.endswith('finish'):
                    entry_id_selected_prior = None
                    object_type_selected_prior = None
                    bookmark_action_prior = None
                    override_program_sort_prior = None
                    filter_modify_program_season_episode_prefix  = ''
                    filter_modify_program_season_episode  = ''
                    filter_modify_program_stream_link  = ''
                    filter_modify_program_stream_link_override  = ''
                    filter_modify_program_special_action  = ''
                    filter_modify_program_original_release_date  = ''
                    filter_modify_program_override_episode_title  = ''
                    filter_modify_program_override_summary  = ''
                    filter_modify_program_override_image  = ''
                    filter_modify_program_override_duration  = ''

                    if '_yes_' in manage_programs_action:
                        if manage_programs_message not in [None, '']:
                            manage_programs_message += f"\n"
                        manage_programs_message += f"{current_time()} INFO: Finished last item after executing additional selected actions."

                    elif '_no_' in manage_programs_action:
                        if manage_programs_message not in [None, '']:
                            manage_programs_message += f"\n"
                        manage_programs_message += f"{current_time()} INFO: Finished last item without executing any additional actions."

                else:

                    if manage_programs_message is None or manage_programs_message == '':
                        manage_programs_message = f"{current_time()} WARNING: Nothing executed because no actions were selected."

                    if object_type_selected_prior in ['SHOW', 'VIDEO'] and program_modify_details_selected_prior:

                        if object_type_selected_prior == 'SHOW':
                            filter_modify_program_season_episode_prefix = request.form.get('filter_modify_program_season_episode_prefix')
                            filter_modify_program_stream_link = request.form.get('filter_modify_program_stream_link')

                        filter_modify_program_season_episode = request.form.get('filter_modify_program_season_episode')
                        filter_modify_program_stream_link_override = request.form.get('filter_modify_program_stream_link_override')
                        filter_modify_program_special_action = request.form.get('filter_modify_program_special_action')
                        filter_modify_program_original_release_date = request.form.get('filter_modify_program_original_release_date')
                        filter_modify_program_override_episode_title = request.form.get('filter_modify_program_override_episode_title')
                        filter_modify_program_override_summary = request.form.get('filter_modify_program_override_summary')
                        filter_modify_program_override_image = request.form.get('filter_modify_program_override_image')
                        filter_modify_program_override_duration = request.form.get('filter_modify_program_override_duration')

                program_modify_bookmark_selected_prior = []
                program_modify_label_maps_selected_prior = []
                program_modify_details_selected_prior = []

            # Get next item
            if not entry_id_selected_prior:
                for select_program_to_edit in select_programs_to_edit:
                    entry_id_selected_prior = select_program_to_edit['entry_id']
                    object_type_selected_prior = select_program_to_edit['object_type']
                    select_programs_to_edit.remove(select_program_to_edit)
                    break

            # Read item details
            if entry_id_selected_prior:
                slm_manage_programs_modify_program_flag = True
                bookmark_action_prior = None
                override_program_sort_prior = None

                if object_type_selected_prior == 'CHANNEL':
                    subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)

                    for subscribed_video_channel in subscribed_video_channels:
                        if subscribed_video_channel['channel_id'] == entry_id_selected_prior:
                            program_modify_details_selected_prior.append(subscribed_video_channel)
                            break

                else:
                    bookmarks = read_data(csv_bookmarks)
                    bookmarks_statuses = read_data(csv_bookmarks_status)

                    for bookmark in bookmarks:
                        if bookmark['entry_id'] == entry_id_selected_prior:
                            program_modify_bookmark_selected_prior.append(bookmark)
                            bookmark_action_prior = bookmark['bookmark_action']
                            override_program_sort_prior = bookmark['override_program_sort']
                            break

                    program_modify_label_maps_selected_prior = get_webpage_label_maps()

                    for bookmarks_status in bookmarks_statuses:
                        if bookmarks_status['entry_id'] == entry_id_selected_prior:
                            program_modify_details_selected_prior.append(bookmarks_status)

                    if len(program_modify_details_selected_prior) > 1 and object_type_selected_prior in ['SHOW', 'VIDEO']:

                        slm_manage_programs_modify_program_scollbar_flag = True

                        if override_program_sort_prior == 'manual':
                            program_modify_details_selected_prior = sorted(program_modify_details_selected_prior, key=lambda x: int(x['manual_order']) if x['manual_order'].isdigit() else float('inf'))

                        elif override_program_sort_prior == 'dateadded_forward':
                            pass

                        elif override_program_sort_prior == 'dateadded_reverse':
                            program_modify_details_selected_prior.reverse()

                        elif override_program_sort_prior == 'dateoriginal_forward':
                            program_modify_details_selected_prior = sorted(program_modify_details_selected_prior, key=lambda x: sort_key(x['original_release_date'].casefold()))

                        elif override_program_sort_prior == 'dateoriginal_reverse':
                            program_modify_details_selected_prior = sorted(program_modify_details_selected_prior, key=lambda x: sort_key(x['original_release_date'].casefold()), reverse=True)

                        elif override_program_sort_prior in ['alpha_reverse', 'default_reverse']:
                            if object_type_selected_prior == 'VIDEO':
                                program_modify_details_selected_prior = sorted(
                                    program_modify_details_selected_prior,
                                    key=lambda x: sort_key((x['override_episode_title'] if x.get('override_episode_title') and str(x['override_episode_title']).strip() else x['season_episode']).casefold()),
                                    reverse=True
                                )
                            else:
                                program_modify_details_selected_prior = sorted(
                                    program_modify_details_selected_prior,
                                    key=lambda x: sort_key(x['season_episode'].casefold()),
                                    reverse=True
                                )

                        else: # ['na', 'alpha_forward', 'default_forward', 'remove']
                            if object_type_selected_prior == 'VIDEO':
                                program_modify_details_selected_prior = sorted(
                                    program_modify_details_selected_prior,
                                    key=lambda x: sort_key((x['override_episode_title'] if x.get('override_episode_title') and str(x['override_episode_title']).strip() else x['season_episode']).casefold())
                                )
                            else:
                                program_modify_details_selected_prior = sorted(
                                    program_modify_details_selected_prior,
                                    key=lambda x: sort_key(x['season_episode'].casefold())
                                )

                    else:

                        slm_manage_programs_modify_program_scollbar_flag = None

            else:
                slm_manage_programs_modify_program_flag = None
                slm_manage_programs_modify_program_scollbar_flag = None

        if any((
            slm_manage_programs_search_results_flag,
            slm_manage_programs_modify_program_flag
        )):
            slm_manage_programs_main_flag = None
        else:
            slm_manage_programs_main_flag = True

        if manage_programs_action in [
            'program_modify_available',
            'program_add_search',
            'program_new_search',
            'program_new_today',
            'slm_manage_programs_search_results_resort_alpha',
            'program_feed_update',
            'program_feed_view'
        ]:

            if program_search_results_prior:

                if len(program_search_results_prior) == 1 or manage_programs_action in [
                    'program_new_search',
                    'program_new_today',
                    'slm_manage_programs_search_results_resort_alpha',
                    'program_feed_update',
                    'program_feed_view'
                ]:

                    if manage_programs_action in [
                        'program_new_search',
                        'program_new_today',
                        'slm_manage_programs_search_results_resort_alpha',
                        'program_feed_update',
                        'program_feed_view'
                    ]:
                        program_search_results_prior = sorted(program_search_results_prior, key=lambda x: sort_key(x["title"].casefold()))

                    if manage_programs_action == 'slm_manage_programs_search_results_resort_alpha':
                        manage_programs_message = f"{current_time()} INFO: Resorted search results alphabetically."

                    program_search_results_resort_alpha_flag = None

    if slm_manage_programs_main_flag or slm_manage_programs_search_results_flag or slm_manage_programs_modify_program_flag:

        if slm_manage_programs_main_flag or slm_manage_programs_search_results_flag:

            # Labels
            slm_labels = read_data(csv_slm_labels)
            if len(slm_labels) > 0:
                for slm_label in slm_labels:
                    if slm_label['label_active'] == 'On':
                        search_results_labels.append({
                            'label_id': slm_label['label_id'],
                            'label_name': slm_label['label_name']
                        })

                if len(search_results_labels) > 1:
                    search_results_labels = sorted(search_results_labels, key=lambda x: sort_key(x["label_name"].casefold()))

        if slm_manage_programs_main_flag:

            # Search/Modify Settings
            settings = read_data(csv_settings)

            ### Search Controls
            settings_num_results = settings[4]["settings"]                      # [4]  Search Defaults: Number of Results
            settings_search_selection = settings[64]["settings"]                # [64] SLM: 'Add Programs' Search Selection (Default)
            settings_provider_status = settings[47]["settings"]                 # [47] SLM: Search Default for Provider Status

            ### Search Settings
            settings_use_feed_map = settings[67]["settings"]                    # [67] SLM: Use the 'Feed & Auto-Mapping' functionality
            settings_hide_bookmarked = settings[9]["settings"]                  # [9]  Search Defaults: Filter out already bookmarked
            settings_country_code = settings[2]["settings"]                     # [2]  Search Defaults: Country Code
            settings_language_code = settings[3]["settings"]                    # [3]  Search Defaults: Language Code
            settings_minimum_video_length = settings[65]["settings"]            # [65] SLM: Minimum Video Length (in Seconds) for Search

            ### Modify Settings
            settings_show_hidden_programs = settings[66]["settings"]            # [66] SLM: Show 'Hidden Programs' in Dropdown Selection (Default)

            # Search Selections
            search_selections = [
                {'search_selection_id': 'all', 'search_selection_name': 'Everything'},
                {'search_selection_id': 'movies_shows_videos', 'search_selection_name': 'Movies, TV Shows, & Videos'},
                {'search_selection_id': 'videos_channels', 'search_selection_name': 'Videos & Channels'},
                {'search_selection_id': 'movies_shows', 'search_selection_name': 'Movies & TV Shows'},
                {'search_selection_id': 'videos', 'search_selection_name': 'Videos'},
                {'search_selection_id': 'channels', 'search_selection_name': 'Channels'}
            ]

            # Settings for Manual Program Types
            program_types = [
                {'program_type_id': 'MOVIE', 'program_type_name': 'Movie'},
                {'program_type_id': 'SHOW', 'program_type_name': 'TV Show'},
                {'program_type_id': 'VIDEO', 'program_type_name': 'Video Group'}
            ]

            # Provider Lists
            provider_statuses = [
                "All Providers",
                "Active Providers",
                "Inactive Providers",
                "All Movie & TV Show Providers",
                "Active Movie & TV Show Providers",
                "Inactive Movie & TV Show Providers",
                "All Video Providers",
                "Active Video Providers",
                "Inactive Video Providers"
            ]

        provider_groups = provider_groups_default.copy()
    
        ### Append Groups
        provider_groups_raw = read_data(csv_provider_groups)
        if provider_groups_raw:
            provider_groups_raw = sorted(provider_groups_raw, key=lambda x: sort_key(x["provider_group_name"].casefold()))

            for provider_group_raw in provider_groups_raw:
                if provider_group_raw["provider_group_active"] == "On":

                    if slm_manage_programs_main_flag:
                        provider_statuses.append(f"GROUP: {provider_group_raw['provider_group_name']}")

                    provider_groups.append({
                        "provider_group_id": provider_group_raw["provider_group_id"],
                        "provider_group_name": f"GROUP: {provider_group_raw['provider_group_name']}"
                    })

        if slm_manage_programs_main_flag:

            ### Append MOVIE and SHOW Streaming Services
            streaming_services = read_data(csv_streaming_services)
            streaming_services_subscribed_raw = [streaming_service for streaming_service in streaming_services if streaming_service['streaming_service_subscribe'] == 'True']
            streaming_services_subscribed = sorted(streaming_services_subscribed_raw, key=lambda x: sort_key(x["streaming_service_name"]))
            
            for streaming_service in streaming_services_subscribed:
                provider_statuses.append(f"PROVIDER (MOVIES & SHOWS): {streaming_service['streaming_service_name']}")
            
            ### Append VIDEO Channels
            subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
            if subscribed_video_channels:
                visible_subscribed_video_channels = [subscribed_video_channel for subscribed_video_channel in subscribed_video_channels if subscribed_video_channel['channel_hidden'] == 'False']
            else:
                visible_subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
            
            for visible_subscribed_video_channel in visible_subscribed_video_channels:
                provider_statuses.append(f"PROVIDER (VIDEOS): {visible_subscribed_video_channel['channel_name']}")

        # Bookmarked Programs
        bookmarks = read_data(csv_bookmarks)
        if settings_show_hidden_programs == "Off":
            sorted_bookmarks = sorted((bookmark for bookmark in bookmarks if bookmark['bookmark_action'] != 'Hide' and not bookmark['entry_id'].startswith('int')), key=lambda x: sort_key(x["title"]))
        else:
            sorted_bookmarks = sorted((bookmark for bookmark in bookmarks), key=lambda x: sort_key(x["title"]))

        if slm_manage_programs_main_flag:

            # Settings for Feeds and Auto-Mapping
            if settings_use_feed_map == 'On':
                feed_maps = read_data(csv_slm_feed_maps)
                feed_rules = read_data(csv_slm_feed_rules)

                feed_map_source_providers = [
                    {'feed_map_source_provider_id': 'movie_show_video', 'feed_map_source_provider_name': 'Movie, TV Show, or Video'},
                    {'feed_map_source_provider_id': 'movie_show', 'feed_map_source_provider_name': 'Movie or TV Show'},
                    {'feed_map_source_provider_id': 'movie', 'feed_map_source_provider_name': 'Movie'},
                    {'feed_map_source_provider_id': 'show', 'feed_map_source_provider_name': 'TV Show'},
                    {'feed_map_source_provider_id': 'video', 'feed_map_source_provider_name': 'Video'}
                ]

                for visible_subscribed_video_channel in visible_subscribed_video_channels:
                    feed_map_source_providers.append({
                        'feed_map_source_provider_id': visible_subscribed_video_channel['channel_id'],
                        'feed_map_source_provider_name': f"VIDEO CHANNEL: {visible_subscribed_video_channel['channel_name']}"
                    })

                program_feed_rule_date_ranges = [
                    {'program_feed_rule_date_range_id': '0', 'program_feed_rule_date_range_name': 'Today'},
                    {'program_feed_rule_date_range_id': '1', 'program_feed_rule_date_range_name': 'Today and Yesterday'},
                    {'program_feed_rule_date_range_id': '2', 'program_feed_rule_date_range_name': 'Today and Prior 2 Days'},
                    {'program_feed_rule_date_range_id': '3', 'program_feed_rule_date_range_name': 'Today and Prior 3 Days'},
                    {'program_feed_rule_date_range_id': '4', 'program_feed_rule_date_range_name': 'Today and Prior 4 Days'},
                    {'program_feed_rule_date_range_id': '5', 'program_feed_rule_date_range_name': 'Today and Prior 5 Days'},
                    {'program_feed_rule_date_range_id': '6', 'program_feed_rule_date_range_name': 'Today and Prior 6 Days'}
                ]

                program_feed_rule_actions = [
                    {'program_feed_rule_action_id': 'none', 'program_feed_rule_action_name': 'None'},
                    {'program_feed_rule_action_id': 'save', 'program_feed_rule_action_name': 'Save'},
                    {'program_feed_rule_action_id': 'delete', 'program_feed_rule_action_name': 'Delete'}
                ]

                new_program_feed_rule_actions = [
                    {'program_feed_rule_action_id': 'none', 'program_feed_rule_action_name': "Make an 'Add' Selection"},
                    {'program_feed_rule_action_id': 'add', 'program_feed_rule_action_name': 'Add'}
                ]

                program_feed_map_source_fields = [
                    {'program_feed_map_source_field_id': 'all', 'program_feed_map_source_field_name': 'Any Field'},
                    {'program_feed_map_source_field_id': 'title', 'program_feed_map_source_field_name': 'Name'},
                    {'program_feed_map_source_field_id': 'release_year', 'program_feed_map_source_field_name': "Core Info ( Movie / TV Show 'Release Year' [Only Number] | Video 'Channel' [Only Name] )"},
                    {'program_feed_map_source_field_id': 'short_description', 'program_feed_map_source_field_name': 'Description'},
                    {'program_feed_map_source_field_id': 'score', 'program_feed_map_source_field_name': "Other Info ( Movie / TV Show 'IMDB Rating' [Only Number] | Video 'Duration' [Seconds] )"}
                ]

                program_feed_map_target_actions = [
                    {'program_feed_map_target_action_id': 'hide', 'program_feed_map_target_action_name': "Hide"},
                    {'program_feed_map_target_action_id': 'bookmark', 'program_feed_map_target_action_name': "IF 'Movie' or 'TV Show', THEN Bookmark"},
                    {'program_feed_map_target_action_id': 'bookmark_import', 'program_feed_map_target_action_name': "IF 'Movie' or 'TV Show', THEN Bookmark plus Import Metadata"},
                    {'program_feed_map_target_action_id': 'bookmark_generate', 'program_feed_map_target_action_name': "IF 'Movie' or 'TV Show', THEN Bookmark and Generate Stream Link(s)"},
                    {'program_feed_map_target_action_id': 'bookmark_import_generate', 'program_feed_map_target_action_name': "IF 'Movie' or 'TV Show', THEN Bookmark and Generate Stream Link(s) plus Import Metadata"}
                ]

                for sorted_bookmark in sorted_bookmarks:
                    if sorted_bookmark['object_type'] == "VIDEO" and not sorted_bookmark['entry_id'].startswith('int'):
                        program_feed_map_target_actions.append({
                            'program_feed_map_target_action_id': f"add_{sorted_bookmark['entry_id']}",
                            'program_feed_map_target_action_name': f"IF 'Video', THEN ADD TO: {sorted_bookmark['title']} ({sorted_bookmark['release_year']})"
                        })

                for sorted_bookmark in sorted_bookmarks:
                    if sorted_bookmark['object_type'] == "VIDEO" and not sorted_bookmark['entry_id'].startswith('int'):
                        program_feed_map_target_actions.append({
                            'program_feed_map_target_action_id': f"add_generate_{sorted_bookmark['entry_id']}",
                            'program_feed_map_target_action_name': f"IF 'Video', THEN ADD TO AND GENERATE STREAM LINKS FOR: {sorted_bookmark['title']} ({sorted_bookmark['release_year']})"
                        })

                program_feed_map_actions = [
                    {'program_feed_map_action_id': 'none', 'program_feed_map_action_name': 'None'},
                    {'program_feed_map_action_id': 'save', 'program_feed_map_action_name': 'Save'},
                    {'program_feed_map_action_id': 'delete', 'program_feed_map_action_name': 'Delete'}
                ]

                new_program_feed_map_actions = [
                    {'program_feed_map_action_id': 'none', 'program_feed_map_action_name': "Make an 'Add' Selection"},
                    {'program_feed_map_action_id': 'add', 'program_feed_map_action_name': 'Add'}
                ]

        if slm_manage_programs_search_results_flag:

            # Search Result Actions: Movies
            search_results_actions_movie = search_results_actions_default.copy()
            search_results_actions_movie_items = [
                {
                'search_results_action_id': 'bookmark',
                'search_results_action_name': 'Bookmark Movie'
                },
                {
                'search_results_action_id': 'bookmark_import',
                'search_results_action_name': 'Bookmark Movie plus Import Metadata'
                },
                {
                'search_results_action_id': 'bookmark_generate',
                'search_results_action_name': 'Bookmark Movie and Generate Stream Link'
                },
                {
                'search_results_action_id': 'bookmark_import_generate',
                'search_results_action_name': 'Bookmark Movie and Generate Stream Link plus Import Metadata'
                },
                {
                'search_results_action_id': 'bookmark_edit',
                'search_results_action_name': 'Bookmark and Edit Movie'
                },
                {
                'search_results_action_id': 'bookmark_edit_import',
                'search_results_action_name': 'Bookmark and Edit Movie plus Import Metadata'
                }
            ]

            for item in search_results_actions_movie_items:
                search_results_actions_movie.append(item)

            # Search Result Actions: TV Shows
            search_results_actions_show = search_results_actions_default.copy()
            search_results_actions_show_items = [
                {
                'search_results_action_id': 'bookmark',
                'search_results_action_name': 'Bookmark TV Show'
                },
                {
                'search_results_action_id': 'bookmark_import',
                'search_results_action_name': 'Bookmark TV Show plus Import Metadata'
                },
                {
                'search_results_action_id': 'bookmark_disable',
                'search_results_action_name': 'Bookmark TV Show plus Disable Get New Episodes'
                },
                {
                'search_results_action_id': 'bookmark_import_disable',
                'search_results_action_name': 'Bookmark TV Show plus Import Metadata and Disable Get New Episodes'
                },
                {
                'search_results_action_id': 'bookmark_generate',
                'search_results_action_name': 'Bookmark TV Show and Generate Stream Links'
                },
                {
                'search_results_action_id': 'bookmark_import_generate',
                'search_results_action_name': 'Bookmark TV Show and Generate Stream Links plus Import Metadata'
                },
                {
                'search_results_action_id': 'bookmark_disable_generate',
                'search_results_action_name': 'Bookmark TV Show and Generate Stream Links plus Disable Get New Episodes'
                },
                {
                'search_results_action_id': 'bookmark_import_disable_generate',
                'search_results_action_name': 'Bookmark TV Show and Generate Stream Links plus Import Metadata and Disable Get New Episodes'
                },
                {
                'search_results_action_id': 'bookmark_edit',
                'search_results_action_name': 'Bookmark and Edit TV Show'
                },
                {
                'search_results_action_id': 'bookmark_edit_import',
                'search_results_action_name': 'Bookmark and Edit TV Show plus Import Metadata'
                },
                {
                'search_results_action_id': 'bookmark_edit_disable',
                'search_results_action_name': 'Bookmark and Edit TV Show plus Disable Get New Episodes'
                },
                {
                'search_results_action_id': 'bookmark_edit_import_disable',
                'search_results_action_name': 'Bookmark and Edit TV Show plus Import Metadata and Disable Get New Episodes'
                }
            ]

            for item in search_results_actions_show_items:
                search_results_actions_show.append(item)

            # Search Result Actions: Videos
            search_results_actions_video = search_results_actions_default.copy()

            search_results_actions_video_items = [
                {
                'search_results_action_id': 'new_unique',
                'search_results_action_name': 'ADD TO: Unique New Video Group (Playlist)'
                },
                {
                'search_results_action_id': 'new_same',
                'search_results_action_name': 'ADD TO: Same New Video Group (Playlist)'
                }
            ]

            for item in search_results_actions_video_items:
                search_results_actions_video.append(item)

            for sorted_bookmark in sorted_bookmarks:
                if sorted_bookmark['object_type'] == "VIDEO" and not sorted_bookmark['entry_id'].startswith('int'):
                    search_results_actions_video.append({
                        'search_results_action_id': f"add_{sorted_bookmark['entry_id']}",
                        'search_results_action_name': f"ADD TO: {sorted_bookmark['title']} ({sorted_bookmark['release_year']})"
                    })

            for sorted_bookmark in sorted_bookmarks:
                if sorted_bookmark['object_type'] == "VIDEO" and not sorted_bookmark['entry_id'].startswith('int'):
                    search_results_actions_video.append({
                        'search_results_action_id': f"add_generate_{sorted_bookmark['entry_id']}",
                        'search_results_action_name': f"ADD TO AND GENERATE STREAM LINKS FOR: {sorted_bookmark['title']} ({sorted_bookmark['release_year']})"
                    })

            for sorted_bookmark in sorted_bookmarks:
                if sorted_bookmark['object_type'] == "VIDEO" and not sorted_bookmark['entry_id'].startswith('int'):
                    search_results_actions_video.append({
                        'search_results_action_id': f"add_edit_{sorted_bookmark['entry_id']}",
                        'search_results_action_name': f"ADD TO AND EDIT: {sorted_bookmark['title']} ({sorted_bookmark['release_year']})"
                    })

            # Search Result Actions: Video Channels
            search_results_actions_channel = search_results_actions_default.copy()
            search_results_actions_channel_items = [
                {
                'search_results_action_id': 'subscribe',
                'search_results_action_name': 'Subscribe to Channel'
                },
                {
                'search_results_action_id': 'subscribe_edit',
                'search_results_action_name': 'Subscribe to and Edit Channel'
                }
            ]

            for item in search_results_actions_channel_items:
                search_results_actions_channel.append(item)

            if provider_groups:
                for provider_group in provider_groups:
                    search_results_actions_channel.append({
                        'search_results_action_id': f"subscribe_{provider_group['provider_group_id']}",
                        'search_results_action_name': f"Subscribe to Channel plus Assign to '{provider_group['provider_group_name']}'"
                    })

                for provider_group in provider_groups:
                    search_results_actions_channel.append({
                        'search_results_action_id': f"subscribe_edit_{provider_group['provider_group_id']}",
                        'search_results_action_name': f"Subscribe to and Edit Channel plus Assign to '{provider_group['provider_group_name']}'"
                    })

        if slm_manage_programs_modify_program_flag:

            program_modify_details_actions.extend([
                {'program_modify_details_action_id': 'none', 'program_modify_details_action_name': 'None'},
                {'program_modify_details_action_id': 'save', 'program_modify_details_action_name': 'Save'}
            ])

            if object_type_selected_prior != 'CHANNEL':

                if object_type_selected_prior == 'VIDEO':
                    special_actions = special_actions_default.copy()
                else:
                    special_actions = get_special_actions()

                new_special_actions = special_actions_default.copy()

                bookmark_actions = get_bookmark_actions(object_type_selected_prior)

                bookmark_selected_actions.extend([
                    {'bookmark_selected_action_id': 'none', 'bookmark_selected_action_name': 'None'},
                    {'bookmark_selected_action_id': 'save', 'bookmark_selected_action_name': 'Save'}
                ])

                if object_type_selected_prior != 'VIDEO':
                    if import_metadata_options_flag:
                        bookmark_selected_actions.extend([
                            {'bookmark_selected_action_id': 'import', 'bookmark_selected_action_name': 'Import Program Metadata'}
                        ])

                bookmark_selected_actions.extend([
                    {'bookmark_selected_action_id': 'delete', 'bookmark_selected_action_name': 'Delete'},
                    {'bookmark_selected_action_id': 'generate', 'bookmark_selected_action_name': 'Generate Stream Links/Files'}
                ])

                if object_type_selected_prior in ['SHOW', 'VIDEO']:

                    add_program_modify_details_actions.extend([
                        {'add_program_modify_details_action_id': 'none', 'add_program_modify_details_action_name': "Make an 'Add' Selection"}
                    ])

                    program_modify_global_selections.extend([
                        {'program_modify_global_selection_id': 'none', 'program_modify_global_selection_name': "Make a 'Global' Selection"}
                    ])

                    override_program_image_types = [
                        {'override_id': 'na', 'override_name': 'N/A'},
                        {'override_id': 'manual', 'override_name': 'Manual (Enter Link)'},
                        {'override_id': 'first', 'override_name': 'Use First Episode/Video Image'},
                        {'override_id': 'remove', 'override_name': 'Remove Previous Selection'}
                    ]

                    if object_type_selected_prior == 'SHOW':

                        if import_metadata_options_flag:
                            program_modify_details_actions.append(
                                {'program_modify_details_action_id': 'import', 'program_modify_details_action_name': "Import Episode Metadata (Requires a natural episode or a 'Special Action' set to 'Make SLM Stream' and a valid link)"}
                            )

                        add_program_modify_details_actions.extend([
                            {'add_program_modify_details_action_id': 'add', 'add_program_modify_details_action_name': 'Add Episode'},
                            {'add_program_modify_details_action_id': 'add_import', 'add_program_modify_details_action_name': "Add Episode and Import Metadata (Requires 'Special Action' set to 'Make SLM Stream' and a valid link)"}
                        ])

                        program_modify_global_selections.extend([
                            {'program_modify_global_selection_id': 'all', 'program_modify_global_selection_name': "All Episodes"},
                            {'program_modify_global_selection_id': 'visible', 'program_modify_global_selection_name': "All Visible Episodes"}
                        ])

                        season_list = []
                        for program_modify_detail_selected_prior in program_modify_details_selected_prior:
                            season = program_modify_detail_selected_prior['season_episode'].split('E')[0]

                            if season not in season_list:
                                season_list.append(season)

                                program_modify_global_selections.extend([
                                    {'program_modify_global_selection_id': f"all_season_{season}", 'program_modify_global_selection_name': f"All {season} Episodes"}
                                ])

                        if season_list:
                            for season in season_list:
                                program_modify_global_selections.extend([
                                    {'program_modify_global_selection_id': f"before_season_{season}", 'program_modify_global_selection_name': f"All Episodes Through {season}"}
                                ])

                    elif object_type_selected_prior == 'VIDEO':
                        override_program_sorts = [
                            {'override_id': 'na', 'override_name': 'N/A'},
                            {'override_id': 'default_forward', 'override_name': 'Default (Forward)'},
                            {'override_id': 'default_reverse', 'override_name': 'Default (Reverse)'},
                            {'override_id': 'alpha_forward', 'override_name': 'Alphabetical (Forward)'},
                            {'override_id': 'alpha_reverse', 'override_name': 'Alphabetical (Reverse)'},
                            {'override_id': 'dateoriginal_forward', 'override_name': 'Original Air Date (Forward)'},
                            {'override_id': 'dateoriginal_reverse', 'override_name': 'Original Air Date (Reverse)'},
                            {'override_id': 'dateadded_forward', 'override_name': 'Date Added (Forward)'},
                            {'override_id': 'dateadded_reverse', 'override_name': 'Date Added (Reverse)'},
                            {'override_id': 'manual', 'override_name': 'Manual'},
                            {'override_id': 'remove', 'override_name': 'Remove Previous Selection'}
                        ]

                        if import_metadata_options_flag:
                            program_modify_details_actions.extend([
                                {'program_modify_details_action_id': 'import', 'program_modify_details_action_name': 'Import Video Medata'}
                            ])

                        program_modify_details_actions.extend([
                            {'program_modify_details_action_id': f"move_{hidden_videos_entry_id}", 'program_modify_details_action_name': 'Hide'}
                        ])

                        program_modify_global_selections.extend([
                            {'program_modify_global_selection_id': 'all', 'program_modify_global_selection_name': "All Videos in Group"},
                            {'program_modify_global_selection_id': 'visible', 'program_modify_global_selection_name': "All Visible Videos"}
                        ])

                        for sorted_bookmark in sorted_bookmarks:
                            if sorted_bookmark['object_type'] == "VIDEO" and sorted_bookmark['entry_id'] != entry_id_selected_prior:
                                program_modify_details_actions.append({
                                    'program_modify_details_action_id': f"move_{sorted_bookmark['entry_id']}",
                                    'program_modify_details_action_name': f"MOVE TO: {sorted_bookmark['title']} ({sorted_bookmark['release_year']})"
                                })

                        add_program_modify_details_actions.extend([
                            {'add_program_modify_details_action_id': 'add_import', 'add_program_modify_details_action_name': 'Add Video and Import Metadata'},
                            {'add_program_modify_details_action_id': 'add', 'add_program_modify_details_action_name': 'Add Video'}
                        ])

                    program_modify_details_actions.append(
                        {'program_modify_details_action_id': 'delete', 'program_modify_details_action_name': 'Delete'}
                    )

    return render_template(
        'main/slm_manage_programs.html',
        segment = 'manage_programs',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_notifications = notifications,
        html_manage_programs_message = manage_programs_message.replace('\n', '<br>'),
        html_slm_process_active_flag = slm_process_active_flag,
        html_import_metadata_options_flag = import_metadata_options_flag,
        html_slm_manage_programs_main_flag = slm_manage_programs_main_flag,
        html_slm_manage_programs_search_results_flag = slm_manage_programs_search_results_flag,
        html_slm_manage_programs_modify_program_flag = slm_manage_programs_modify_program_flag,
        html_slm_manage_programs_modify_program_scollbar_flag = slm_manage_programs_modify_program_scollbar_flag,
        html_slm_manage_programs_program_modify_available_flag = slm_manage_programs_program_modify_available_flag,
        html_modify_entry_id = modify_entry_id,
        html_program_add_prior = program_add_prior,
        html_program_add_manual_prior = program_add_manual_prior,
        html_program_add_import_playlist_prior = program_add_import_playlist_prior,
        html_date_new_default_end_prior = date_new_default_end_prior,
        html_date_new_default_start_prior = date_new_default_start_prior,
        html_program_search_results_prior = program_search_results_prior,
        html_program_search_results_resort_alpha_flag = program_search_results_resort_alpha_flag,
        html_entry_id_selected_prior = entry_id_selected_prior,
        html_object_type_selected_prior = object_type_selected_prior,
        html_bookmark_action_prior = bookmark_action_prior,
        html_override_program_sort_prior = override_program_sort_prior,
        html_program_modify_bookmark_selected_prior = program_modify_bookmark_selected_prior,
        html_program_modify_label_maps_selected_prior = program_modify_label_maps_selected_prior,
        html_program_modify_details_selected_prior = program_modify_details_selected_prior,
        html_settings_num_results = settings_num_results,
        html_settings_search_selection = settings_search_selection,
        html_settings_provider_status = settings_provider_status,
        html_settings_hide_bookmarked = settings_hide_bookmarked,
        html_settings_country_code = settings_country_code,
        html_settings_language_code = settings_language_code,
        html_settings_minimum_video_length = settings_minimum_video_length,
        html_settings_show_hidden_programs = settings_show_hidden_programs,
        html_settings_use_feed_map = settings_use_feed_map,
        html_sorted_bookmarks = sorted_bookmarks,
        html_provider_statuses = provider_statuses,
        html_provider_groups = provider_groups,
        html_bookmark_actions = bookmark_actions,
        html_special_actions = special_actions,
        html_new_special_actions = new_special_actions,
        html_override_program_image_types = override_program_image_types,
        html_override_program_sorts = override_program_sorts,
        html_program_types = program_types,
        html_search_selections = search_selections,
        html_valid_country_codes = valid_country_codes,
        html_valid_language_codes = valid_language_codes,
        html_search_results_actions_movie = search_results_actions_movie,
        html_search_results_actions_show = search_results_actions_show,
        html_search_results_actions_video = search_results_actions_video,
        html_search_results_actions_channel = search_results_actions_channel,
        html_bookmark_selected_actions = bookmark_selected_actions,
        html_program_modify_details_actions = program_modify_details_actions,
        html_add_program_modify_details_actions = add_program_modify_details_actions,
        html_program_modify_global_selections = program_modify_global_selections,
        html_filter_modify_program_season_episode_prefix  = filter_modify_program_season_episode_prefix,
        html_filter_modify_program_season_episode  = filter_modify_program_season_episode,
        html_filter_modify_program_stream_link  = filter_modify_program_stream_link,
        html_filter_modify_program_stream_link_override  = filter_modify_program_stream_link_override,
        html_filter_modify_program_special_action  = filter_modify_program_special_action,
        html_filter_modify_program_original_release_date  = filter_modify_program_original_release_date,
        html_filter_modify_program_override_episode_title  = filter_modify_program_override_episode_title,
        html_filter_modify_program_override_summary  = filter_modify_program_override_summary,
        html_filter_modify_program_override_image  = filter_modify_program_override_image,
        html_filter_modify_program_override_duration  = filter_modify_program_override_duration,
        html_all_compare_options = all_compare_options,
        html_search_results_labels = search_results_labels,
        html_program_feed_rule_date_ranges = program_feed_rule_date_ranges,
        html_program_feed_rule_actions = program_feed_rule_actions,
        html_new_program_feed_rule_actions = new_program_feed_rule_actions,
        html_program_feed_map_source_fields = program_feed_map_source_fields,
        html_program_feed_map_target_actions = program_feed_map_target_actions,
        html_program_feed_map_actions = program_feed_map_actions,
        html_new_program_feed_map_actions = new_program_feed_map_actions,
        html_feed_maps = feed_maps,
        html_feed_rules = feed_rules,
        html_feed_map_source_providers = feed_map_source_providers
    )

# Search for country code
def get_country_code():
    settings = read_data(csv_settings)
    country_code = settings[2]["settings"]
    country_code_input = None
    country_code_new = None

    global timeout_occurred
    timeout_occurred = False
    print(f"{current_time()} Searching for country code for Streaming Services...")
    print(f"{current_time()} Please wait or press 'Ctrl+C' to stop and continue the initialization process.")

    # Search times out after 30 seconds
    timer = threading.Timer(30, timeout_handler)
    timer.start()

    try:
        response = requests.get('https://ipapi.co/json/', headers=url_headers)
        data = response.json()
        user_country_code = data.get('country', '').upper()
        
        if user_country_code in valid_country_codes:
            country_code_input = user_country_code
    except TimeoutError:
        print(f"{current_time()} INFO: Search timed out. Continuing to next step...")
    except KeyboardInterrupt:
        print(f"{current_time()} INFO: Search interrupted by user. Continuing to next step...")
    except Exception as e:
        print(f"{current_time()} INFO: Error getting geolocation: {e}. Continuing to next step...")
    finally:
        timer.cancel()  # Disable the timer

    if country_code_input:
        print(f"{current_time()} INFO: Country found!")
        country_code_new = country_code_input.upper()
    else:
        print(f"{current_time()} INFO: Country not found, using default value. Please set your Country in 'Settings'.")
        country_code_new = country_code

    print(f"{current_time()} INFO: Country Code set to '{country_code_new}'")

    return country_code_new

# Creates the dropdown list of 'Special Actions'
def get_special_actions():
    services = []
    check_services = []
    
    services = read_data(csv_streaming_services)
    check_services = [service for service in services if service["streaming_service_subscribe"] == "True"]
    check_services.sort(key=lambda x: int(x.get("streaming_service_priority", float("inf"))))
    
    # Initialize special_actions with a copy of the default list
    special_actions = special_actions_default.copy()
    
    for check_service in check_services:
        prefer = f"Prefer: {check_service['streaming_service_name']}"
        special_actions.append(prefer)
    
    return special_actions

# Creates the dropdown list of 'Bookmark Actions'
def get_bookmark_actions(object_type):
    bookmark_actions = bookmark_actions_default.copy()

    if object_type == "SHOW":
        for action in bookmark_actions_default_show_only:
            bookmark_actions.append(action)

    elif object_type == "VIDEO":
        for action in bookmark_actions_default_video_only:
            bookmark_actions.append(action)

    return bookmark_actions

# Runs a test to see if the value is a positive integer
def positive_integer_test(number, zero_okay):
    result = 'unknown'

    try:
        if not number:
            result = 'missing'
        number_int = int(number)
        if number_int > 0 or ( zero_okay is True and number_int == 0 ):
            result = "pass"
        else:
            result = 'not_positive'
    except ValueError:
        result = 'not_number'

    return result

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

# For videos, converts duration value into seconds for filtering out
def parse_duration_to_seconds(duration_str):
    total_seconds = 0

    if "Unknown" not in duration_str:
        # Find all time components using regex
        time_matches = re.findall(r'(\d+)\s*(hours?|minutes?|seconds?)', duration_str)

        # Map units to their multiplier
        unit_multipliers = {
            'hour': 3600,
            'hours': 3600,
            'minute': 60,
            'minutes': 60,
            'second': 1,
            'seconds': 1
        }

        # Accumulate total seconds
        for value, unit in time_matches:
            total_seconds += int(value) * unit_multipliers[unit]

    return total_seconds

# Checks a video name (season_episode) to see if it is unique within the Video Group
def check_video_name_unique(bookmarks_statuses, entry_id, video_name):
    season_episode_exists = False
    new_video_name = video_name
    new_video_name_appendage = ' - SLM Duplicate '
    new_video_name_number = 1
    duplicate_video_name = f"{video_name}{new_video_name_appendage}"
    existing_duplicates = []

    if bookmarks_statuses:

        for bookmarks_status in bookmarks_statuses:
            if ( 
                ( bookmarks_status['entry_id'] == entry_id ) and
                ( bookmarks_status['season_episode'] == video_name )
            ):
                season_episode_exists = True
                break

        if season_episode_exists:

            existing_duplicates = [
                bookmarks_status['season_episode']
                for bookmarks_status in bookmarks_statuses
                if bookmarks_status['entry_id'] == entry_id
                and duplicate_video_name in bookmarks_status['season_episode']
            ]

            if existing_duplicates:
                new_video_name_number = int(new_video_name_number) + max( (int(existing_duplicate.split(duplicate_video_name)[-1]) for existing_duplicate in existing_duplicates), default = 0 )
    
            new_video_name = f"{duplicate_video_name}{new_video_name_number}"

    return new_video_name

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
            icon
            clearName
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
                icon
                clearName
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
        print(f"{current_time()} WARNING: {e}. Skipping, please try again.")

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
        poster_raw = node.get("content", {}).get("posterUrl")
        if poster_raw is not None and poster_raw != '':
            poster = f"{engine_image_url}{poster_raw}"
            poster = poster.replace('{profile}', engine_image_profile_poster)
            poster = poster.replace('{format}', 'jpg')
        else:
            poster = None
        score_raw = node.get("content", {}).get("scoring", {}).get("imdbScore")
        try:
            score = f"{float(score_raw):.1f}"
        except (ValueError, TypeError):
            score = "N/A"  # Handle the case where the score is not a valid number
        
        offers_raw = node.get("offers")
        offers_raw_list = []
        for offer_raw in offers_raw:
            offer_raw_icon = offer_raw["package"]["icon"]
            offer_raw_icon = f"{engine_image_url}{offer_raw_icon}"
            offer_raw_icon = offer_raw_icon.replace('{profile}', engine_image_profile_icon)
            offer_raw_icon = offer_raw_icon.replace('{format}', 'png')
            offer_raw_clearname = offer_raw["package"]["clearName"]
            offers_raw_list.append({"icon": offer_raw_icon, "sort": offer_raw_clearname})

        offers_raw_list_sorted = sorted(offers_raw_list, key=lambda x: sort_key(x["sort"]))
        icons_list = []
        icons_list = [offer["icon"] for offer in offers_raw_list_sorted]

        offers_list = list(dict.fromkeys(icons_list))

        extracted_data.append({
            "entry_id": entry_id,
            "title": title,
            "release_year": release_year,
            "object_type": object_type,
            "url": url,
            "short_description": short_description,
            "poster": poster,
            "score": score,
            "offers_list": offers_list
        })

    return extracted_data

# Searches video providers to return a list of videos, channels, or videos within a Playlist or Channel
def search_video_providers(providers, query, search_type, num_results, language_code, country_code):
    default_poster_url = 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Missing_barnstar.jpg'
    extracted_data = []
    message = ''
    
    if int(num_results) > 100:
        num_results = '100'

    for provider in providers:
        base_results = {}
        base_info = {}
        
        if provider == 'youtube':
            offers_list = ["https://images.justwatch.com/icon/59562423/s100/youtube.png"]

            try:
                if search_type.startswith("videos"):
                    object_type = "VIDEO"
                    
                    if search_type == "videos":
                        base_results = youtube_search_videos(query, limit=int(num_results), language=language_code, region=country_code).result()
                    
                    elif search_type == "videos_from_playlist":
                        base_results = get_youtube_playlist_info(query)
                        if base_results:
                            base_info = base_results.info.get('info', {})

                    elif search_type == "videos_from_channel":
                        base_results = get_youtube_playlist_info(get_youtube_channel_info(query))

                elif search_type == "channels":
                    object_type = "CHANNEL"
                    base_results = youtube_search_channels(query, limit=int(num_results), language=language_code, region=country_code).result()
            
            except Exception as e:
                message = f"{current_time()} ERROR: Retrieving videos from YouTube. Returned: {str(e)}"

            if base_results:
                if search_type in ["videos", "channels"]:
                    processed_results = base_results.get('result', [])
                elif search_type.startswith("videos_"):
                    processed_results = base_results.videos
                
                for processed_result in processed_results:
                    title = processed_result.get('title', 'Unknown Title')

                    if search_type.startswith("videos"):
                        channel = processed_result.get('channel', {}).get('name', 'Unknown Channel')
                        release_year = f"Channel: {channel}"                      
                    elif search_type == "channels":
                        release_year = processed_result.get('subscribers', 'Unknown subscribers')
                        
                    url = processed_result.get('link', 'http://url_not_found')
                    if search_type.startswith("videos_"):
                        url = url.split('&list=')[0]
                    
                    desc_snippet = processed_result.get('descriptionSnippet') or []
                    short_description = "".join([d.get('text', '') for d in desc_snippet if 'text' in d])
                    
                    thumbnails = processed_result.get('thumbnails', [])
                    if thumbnails:
                        poster = max(thumbnails, key=lambda t: t.get('width', 0)).get('url', default_poster_url)
                    else:
                        poster = default_poster_url
                    if search_type == "channels":
                        poster = f"https:{poster}"
                    
                    if search_type == "channels":
                        score = f"Subscribe"
                    elif search_type == "videos_from_playlist":
                        score = base_info.get('title', 'Unknown Playlist Name')
                    elif search_type in ["videos", "videos_from_channel"]:
                        score = f"Duration: {processed_result.get('accessibility', {}).get('duration', 'Unknown')}"

                    extracted_data.append({
                        "entry_id": search_type,
                        "title": title,
                        "release_year": release_year,
                        "object_type": object_type,
                        "url": url,
                        "short_description": short_description,
                        "poster": poster,
                        "score": score,
                        "offers_list": offers_list
                    })

    return extracted_data, message

# Find new programs on selected Streaming Services
def get_program_new(date_new_default_range, country_code, language_code, num_results, provider_status, video_providers):
    program_new_results_json_array_extracted_unique = []

    provider_groups = read_data(csv_provider_groups)

    streaming_services_map = []
    streaming_services_map = get_streaming_services_map()
    
    services = read_data(csv_streaming_services)
    check_services = [service for service in services if service["streaming_service_subscribe"] == "True"]
    check_services.sort(key=lambda x: int(x.get("streaming_service_priority", float("inf"))))

    check_services_codes = []
    for check_service in check_services:
        for streaming_service in streaming_services_map:
            if check_service['streaming_service_name'] == streaming_service['streaming_service_name']:
                provider_group_name = next(
                    (provider_group['provider_group_name'] for provider_group in provider_groups if provider_group['provider_group_id'] == check_service['streaming_service_group']),
                    None
                )

                if (
                    ( provider_status == "All Providers" ) or
                    ( provider_status == "Active Providers" and check_service['streaming_service_active'] == "On" ) or
                    ( provider_status == "Inactive Providers" and check_service['streaming_service_active'] == "Off" ) or
                    ( provider_status == "All Movie & TV Show Providers" ) or
                    ( provider_status == "Active Movie & TV Show Providers" and check_service['streaming_service_active'] == "On" ) or
                    ( provider_status == "Inactive Movie & TV Show Providers" and check_service['streaming_service_active'] == "Off" ) or
                    ( provider_status.startswith("GROUP: ") and provider_group_name == provider_status.split(": ")[1] ) or
                    ( provider_status.startswith("PROVIDER (MOVIES & SHOWS): ") and check_service['streaming_service_name'] == provider_status.split(": ")[1] )
                ):
                    check_services_codes.append(streaming_service['streaming_service_code'])

    _GRAPHQL_GetNewTitles = """
    query GetNewTitles($country: Country!, $date: Date!, $language: Language!, $filter: TitleFilter, $after: String, $first: Int! = 10, $profile: PosterProfile, $format: ImageFormat, $backdropProfile: BackdropProfile, $priceDrops: Boolean!, $platform: Platform!, $bucketType: NewDateRangeBucket, $pageType: NewPageType! = NEW, $showDateBadge: Boolean!, $availableToPackages: [String!], $allowSponsoredRecommendations: SponsoredRecommendationsInput) {
    newTitles(
        country: $country
        date: $date
        filter: $filter
        after: $after
        first: $first
        priceDrops: $priceDrops
        bucketType: $bucketType
        pageType: $pageType
        allowSponsoredRecommendations: $allowSponsoredRecommendations
    ) {
        totalCount
        edges {
        ...NewTitleGraphql
        __typename
        }
        sponsoredAd {
        ...SponsoredAd
        __typename
        }
        pageInfo {
        endCursor
        hasPreviousPage
        hasNextPage
        __typename
        }
        __typename
    }
    }

    fragment NewTitleGraphql on NewTitlesEdge {
    cursor
    newOffer(platform: $platform) {
        id
        standardWebURL
        package {
        id
        packageId
        clearName
        shortName
        icon
        __typename
        }
        retailPrice(language: $language)
        retailPriceValue
        lastChangeRetailPrice(language: $language)
        lastChangeRetailPriceValue
        lastChangePercent
        currency
        presentationType
        monetizationType
        newElementCount
        __typename
    }
    node {
        id
        objectId
        objectType
        content(country: $country, language: $language) {
        title
        originalReleaseYear
        shortDescription
        fullPath
        scoring {
            imdbVotes
            imdbScore
            tmdbPopularity
            tmdbScore
            tomatoMeter
            certifiedFresh
            __typename
        }
        posterUrl(profile: $profile, format: $format)
        runtime
        genres {
            translation(language: $language)
            __typename
        }
        ... on SeasonContent {
            seasonNumber
            __typename
        }
        upcomingReleases @include(if: $showDateBadge) {
            releaseDate
            package {
            id
            shortName
            icon
            clearName
            __typename
            }
            releaseCountDown(country: $country)
            __typename
        }
        isReleased
        __typename
        }
        availableTo(
        country: $country
        platform: $platform
        packages: $availableToPackages
        ) @include(if: $showDateBadge) {
        availableCountDown(country: $country)
        package {
            id
            shortName
            icon
            clearName
            __typename
        }
        availableToDate
        __typename
        }
        ... on Movie {
        likelistEntry {
            createdAt
            __typename
        }
        dislikelistEntry {
            createdAt
            __typename
        }
        seenlistEntry {
            createdAt
            __typename
        }
        watchlistEntryV2 {
            createdAt
            __typename
        }
        __typename
        }
        ... on Season {
        show {
            id
            objectId
            objectType
            content(country: $country, language: $language) {
            title
            originalReleaseYear
            shortDescription
            fullPath
            scoring {
                imdbVotes
                imdbScore
                tmdbPopularity
                tmdbScore
                __typename
            }
            posterUrl(profile: $profile, format: $format)
            runtime
            genres {
                translation(language: $language)
                __typename
            }
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
            watchlistEntryV2 {
            createdAt
            __typename
            }
            seenState(country: $country) {
            progress
            __typename
            }
            __typename
        }
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
                icon
                clearName
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

    # Movies & TV Shows
    program_new_results_json_array_extracted = []

    for date_new in date_new_default_range:
        program_new_results = []
        program_new_results_json = []
        program_new_results_json_array = []
        
        json_data = {
            'query': _GRAPHQL_GetNewTitles,
            'variables': {
                "first": num_results,
                "pageType": "NEW",
                "date": date_new,
                "filter": {
                    "ageCertifications": [],
                    "excludeGenres": [],
                    "excludeProductionCountries": [],
                    "objectTypes": [],
                    "productionCountries": [],
                    "subgenres": [],
                    "genres": [],
                    "packages": check_services_codes,
                    "excludeIrrelevantTitles": False,
                    "presentationTypes": [],
                    "monetizationTypes": []
                },
                "language": language_code,
                "country": country_code,
                "priceDrops": False,
                "platform": "WEB",
                "showDateBadge": False,
                "availableToPackages": check_services_codes,
                "backdropProfile": "S1440",
                "allowSponsoredRecommendations": {
                    "pageType": "NEW",
                    "placement": "NEW_TIMELINE",
                    "language": language_code,
                    "country": country_code,
                    "applicationContext": {
                    "appID": "3.8.2-webapp#a85a1b3",
                    "platform": "webapp",
                    "version": "3.8.2",
                    "build": "a85a1b3",
                    "isTestBuild": False
                    },
                    "appId": "3.8.2-webapp#a85a1b3",
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
                    "testingModeForceHoldoutGroup": False,
                    "testingMode": False
                }
            },
            'operationName': 'GetNewTitles',
        }

        if check_services_codes:
            try:
                program_new_results = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
                program_new_results_json = program_new_results.json()
            except requests.RequestException as e:
                print(f"{current_time()} WARNING: {e}. Skipping, please try again.")

        if program_new_results_json:
            program_new_results_json_array = program_new_results_json["data"]["newTitles"]["edges"]

        if program_new_results_json_array:
            for record in program_new_results_json_array:
                node = None
                show = None
                node = record["node"]
                show = node.get("show")
        
                if show:
                    entry_id = show["id"]
                    title = show["content"]["title"]
                    release_year = show["content"]["originalReleaseYear"]
                    object_type = show["objectType"]
                    href = show["content"]["fullPath"]
                    short_description = show["content"]["shortDescription"]
                    poster_raw = show["content"]["posterUrl"]
                    score_raw = show["content"]["scoring"]["imdbScore"]
                else:
                    entry_id = node["id"]
                    title = node["content"]["title"]
                    release_year = node["content"]["originalReleaseYear"]
                    object_type = node["objectType"]
                    href = node["content"]["fullPath"]
                    short_description = node["content"]["shortDescription"]
                    poster_raw = node["content"]["posterUrl"]
                    score_raw = node["content"]["scoring"]["imdbScore"]
                        
                if href is not None and href != '':
                    url = f"{engine_url}{href}"  # Concatenate with the prefix
                else:
                    url = None

                if poster_raw is not None and poster_raw != '':
                    poster = f"{engine_image_url}{poster_raw}"
                    poster = poster.replace('{profile}', engine_image_profile_poster)
                    poster = poster.replace('{format}', 'jpg')
                else:
                    poster = None

                try:
                    score = f"{float(score_raw):.1f}"
                except (ValueError, TypeError):
                    score = "N/A"  # Handle the case where the score is not a valid number`

                offers_raw_list = []
                try:
                    offer_raw_icon = record["newOffer"]["package"]["icon"]
                    offer_raw_icon = f"{engine_image_url}{offer_raw_icon}"
                    offer_raw_icon = offer_raw_icon.replace('{profile}', engine_image_profile_icon)
                    offer_raw_icon = offer_raw_icon.replace('{format}', 'png')
                    offer_raw_clearname = record["newOffer"]["package"]["clearName"]
                    offers_raw_list.append({"icon": offer_raw_icon, "sort": offer_raw_clearname})
                except:
                    print(f"{current_time()} WARNING: Unable to find offer icon for {record}. Skipping...")

                offers_raw_list_sorted = sorted(offers_raw_list, key=lambda x: sort_key(x["sort"]))
                icons_list = []
                icons_list = [offer["icon"] for offer in offers_raw_list_sorted]

                offers_list = list(dict.fromkeys(icons_list))

                program_new_results_json_array_extracted.append({
                    "entry_id": entry_id,
                    "title": title,
                    "release_year": release_year,
                    "object_type": object_type,
                    "url": url,
                    "short_description": short_description,
                    "poster": poster,
                    "score": score,
                    "offers_list": offers_list
                })

    if program_new_results_json_array_extracted:
        seen_entries = set()

        for record in program_new_results_json_array_extracted:
            identifier = (record['entry_id'], record['title'], record['release_year'], record['object_type'], record['url'])
    
            if identifier not in seen_entries:
                seen_entries.add(identifier)
                program_new_results_json_array_extracted_unique.append(record)

    # Videos
    subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
    if subscribed_video_channels:
        check_video_services = [subscribed_video_channel for subscribed_video_channel in subscribed_video_channels if subscribed_video_channel['channel_hidden'] == 'False']
    else:
        check_video_services = read_data(csv_slm_subscribed_video_channels)

    check_video_services_codes = []
    for check_video_service in check_video_services:
        channel_query = None
        provider_group_name = next(
            (provider_group['provider_group_name'] for provider_group in provider_groups if provider_group['provider_group_id'] == check_video_service['channel_streaming_service_group']),
            None
        )
        
        if (
            ( provider_status == "All Providers" ) or
            ( provider_status == "Active Providers" and check_video_service['channel_active'] == "On" ) or
            ( provider_status == "Inactive Providers" and check_video_service['channel_active'] == "Off" ) or
            ( provider_status == "All Video Providers" ) or
            ( provider_status == "Active Video Providers" and check_video_service['channel_active'] == "On" ) or
            ( provider_status == "Inactive Video Providers" and check_video_service['channel_active'] == "Off" ) or
            ( provider_status.startswith("GROUP: ") and provider_group_name == provider_status.split(": ")[1] ) or
            ( provider_status.startswith("PROVIDER (VIDEOS): ") and check_video_service['channel_name'] == provider_status.split(": ")[1] )
        ):

            if 'youtu' in check_video_service['channel_url']:
                channel_query = check_video_service['channel_url'].rstrip('/').split('/')[-1]

            check_video_services_codes.append(channel_query)

    if check_video_services_codes:
        for check_video_services_code in check_video_services_codes:
            check_video_services_code_result = None
            check_video_services_code_result, message_throwaway = search_video_providers(video_providers, check_video_services_code, 'videos_from_channel', num_results, language_code, country_code)
            if check_video_services_code_result:
                program_new_results_json_array_extracted_unique.extend(check_video_services_code_result)

    return program_new_results_json_array_extracted_unique

# Get a map for Streaming Services from "Clear Name" to "Short Name"
def get_streaming_services_map():
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
        shortName
        addons(country: $country, platform: $platform) {
          clearName
          shortName
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
        print(f"{current_time()} WARNING: {e}. Skipping, please try again.")

    if provider_results:
        provider_results_json = provider_results.json()
        provider_results_json_array = provider_results_json["data"]["packages"]

        for provider in provider_results_json_array :
            provider_addons = []

            entry = {
                "streaming_service_name": provider["clearName"],
                "streaming_service_code": provider["shortName"]
            }
            provider_results_json_array_results.append(entry)

            provider_addons = provider["addons"]

            if provider_addons:
                for provider_addon in provider_addons:
                    entry = {
                        "streaming_service_name": provider_addon["clearName"],
                        "streaming_service_code": provider_addon["shortName"]
                    }
                    provider_results_json_array_results.append(entry)

    return provider_results_json_array_results

# Runs the process to update the SLM Feed and do auto-mapping
def run_slm_update_feed():
    if slm_process_active_flag:
        print(f"{current_time()} WARNING: The 'SLM Feed' cannot be updated at this time because another SLM process is currently underway. Please try again later.")

    else:
        settings = read_data(csv_settings)
        settings_use_feed_map = settings[67]["settings"]                    # [67] SLM: Use the 'Feed & Auto-Mapping' functionality
        settings_hide_bookmarked = settings[9]["settings"]                  # [9]  Search Defaults: Filter out already bookmarked
        settings_country_code = settings[2]["settings"]                     # [2]  Search Defaults: Country Code
        settings_language_code = settings[3]["settings"]                    # [3]  Search Defaults: Language Code
        settings_minimum_video_length = settings[65]["settings"]            # [65] SLM: Minimum Video Length (in Seconds) for Search

        if settings_use_feed_map == 'On':

            feed_rules = read_data(csv_slm_feed_rules)
            feed_maps = read_data(csv_slm_feed_maps)
            feed_items = read_data(csv_slm_feed_items)
            if feed_items:
                original_feed_items = feed_items.copy()
            else:
                original_feed_items = []

            entry_id_feed_items_lookup = {}
            url_feed_items_lookup = {}
            if feed_items:
                entry_id_feed_items_lookup = {feed_item['entry_id'] for feed_item in feed_items if 'video' not in feed_item['entry_id']}
                url_feed_items_lookup = {feed_item['url'] for feed_item in feed_items if 'video' in feed_item['entry_id']}

            feed_search_results_combined = []
            feed_search_results_post_map = []

            for feed_rule in feed_rules:

                if feed_rule['feed_rule_active'] == 'On':

                    date_new_default_range = []
                    feed_search_results_base = []
                    feed_search_results_filtered = []

                    date_new_default_range = [
                        (datetime.date.today() - datetime.timedelta(days=int(feed_rule['date_range'])) + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
                        for i in range(int(feed_rule['date_range']) + 1)
                    ]  
                    
                    num_results = 100 # Maximum number of new programs

                    if date_new_default_range:
                        feed_search_results_base = get_program_new(date_new_default_range, settings_country_code, settings_language_code, num_results, feed_rule['provider'], video_providers)

                    if feed_search_results_base:
                        if feed_rule['override_min_video_length'] not in ['', None]:
                            minimum_video_length = feed_rule['override_min_video_length']
                        else:
                            minimum_video_length = settings_minimum_video_length

                        feed_search_results_filtered, filter_clean_message = filter_clean_slm_search_results(feed_search_results_base, settings_hide_bookmarked, minimum_video_length, None)

                    if feed_search_results_filtered:
                        feed_search_results_combined += feed_search_results_filtered

            if feed_search_results_combined:

                if feed_maps:

                    for item in feed_maps:
                        target_label_ids_raw = item.get("target_label_ids")
                        if isinstance(target_label_ids_raw, str):
                            try:
                                item["target_label_ids"] = ast.literal_eval(target_label_ids_raw)
                            except (ValueError, SyntaxError):
                                print(f"{current_time()} ERROR: For 'Feed Maps', unable to convert 'Target Labels' to a list.")

                    feed_search_results_post_map = run_slm_feed_maps(feed_maps, feed_search_results_combined)

                else:
                    feed_search_results_post_map = feed_search_results_combined.copy()

            if feed_search_results_post_map:

                for item in feed_search_results_post_map:

                    if (
                        ( 'video' not in item['entry_id'] and item['entry_id'] not in entry_id_feed_items_lookup ) or
                        ( 'video' in item['entry_id'] and item['url'] not in url_feed_items_lookup )                            
                    ):
                        
                        feed_items.append(item)

            if feed_items != original_feed_items:
                write_data(csv_slm_feed_items, feed_items)

# Runs the sub-process for feed maps and returning a filtered list of non-mapped items
def run_slm_feed_maps(feed_maps, search_results_base):
    search_results = []
    search_results_base_remove = []
    search_results_base_submissions = []

    subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
    subscribed_video_channels_lookup = {}

    if subscribed_video_channels:
        subscribed_video_channels_lookup = {subscribed_video_channel['channel_id']: subscribed_video_channel['channel_name'] for subscribed_video_channel in subscribed_video_channels}

    if feed_maps and search_results_base:

        active_feed_maps = [feed_map for feed_map in feed_maps if feed_map['feed_map_active'] == 'On']

        for item in search_results_base:

            object_type = item['object_type']
            run_action = False

            for feed_map in active_feed_maps:

                feed_map_name = None
                source_provider = None
                source_field = None
                source_field_compare_id = None
                source_field_string = None
                target_status = None
                target_label_ids = []
                target_action = None

                target_action = feed_map['target_action']
                if (
                    ( target_action == 'hide' ) or
                    ( object_type in ['MOVIE', 'SHOW'] and 'bookmark' in target_action ) or
                    ( object_type == 'VIDEO' and 'add' in target_action )
                ):

                    feed_map_name = feed_map['feed_map_name']
                    if feed_map_name in [None, '']:
                        feed_map_name = f"Unnamed - ID {feed_map['feed_map_id']}"

                    source_provider = feed_map['source_provider']

                    video_channel_name = None
                    if object_type == 'VIDEO' and source_provider.startswith('slmchn_'):
                        video_channel_name = f"Channel: {subscribed_video_channels_lookup[source_provider]}"

                    if (
                        ( object_type == 'MOVIE' and 'movie' in source_provider ) or
                        ( object_type == 'SHOW' and 'show' in source_provider ) or
                        ( object_type == 'VIDEO' and 'video' in source_provider ) or
                        ( object_type == 'VIDEO' and item['release_year'] == video_channel_name )
                    ):

                        source_field = feed_map['source_field']

                        check_fields = []
                        if source_field in ['all', 'title']:
                            check_fields.append('title')
                        if source_field in ['all', 'release_year']:
                            check_fields.append('release_year')
                        if source_field in ['all', 'short_description']:
                            check_fields.append('short_description')
                        if source_field in ['all', 'score']:
                            check_fields.append('score')

                        source_field_compare_id = feed_map['source_field_compare_id']
                        source_field_string = feed_map['source_field_string']
                        target_status = feed_map['target_status']
                        target_label_ids = feed_map['target_label_ids']

                        for check_field in check_fields:

                            source_field_value = None
                            source_field_value = item[check_field]
                            source_field_value_number = None

                            try:
                                if object_type in ['MOVIE', 'SHOW']:

                                    if source_field_compare_id in ['greater', 'greater_equal', 'less', 'less_equal']:
                                        
                                        if check_field == 'release_year':
                                            source_field_value_number = int(source_field_value)

                                        if check_field == 'score':
                                            source_field_value_number = int(float(source_field_value))

                                elif object_type == 'VIDEO':

                                    if check_field == 'score':
                                        source_field_value_number = int(parse_duration_to_seconds(source_field_value))
                                        source_field_value = f"{source_field_value_number}"

                            except:
                                print(f"{current_time()} ERROR: Could not convert '{check_field} == {source_field_value}' to an integer.")

                            if ( 
                                    ( source_field_compare_id == 'equal' and source_field_value == source_field_string ) or 
                                    ( source_field_compare_id == 'equal_not' and source_field_value != source_field_string ) or
                                    ( source_field_compare_id == 'contain' and source_field_string in source_field_value ) or
                                    ( source_field_compare_id == 'contain_not' and source_field_string not in source_field_value ) or
                                    ( source_field_compare_id == 'begin' and source_field_value.startswith(source_field_string) ) or
                                    ( source_field_compare_id == 'begin_not' and not source_field_value.startswith(source_field_string) ) or
                                    ( source_field_compare_id == 'end' and source_field_value.endswith(source_field_string) ) or
                                    ( source_field_compare_id == 'end_not' and not source_field_value.endswith(source_field_string) ) or
                                    ( source_field_compare_id == 'regex' and re.search(source_field_string, source_field_value) ) or
                                    ( source_field_compare_id == 'regex_not' and not re.search(source_field_string, source_field_value) ) 
                                ):

                                    run_action = True

                            elif source_field_value_number:

                                if ( 
                                        ( source_field_compare_id == 'greater' and int(source_field_value_number) > int(source_field_string) ) or 
                                        ( source_field_compare_id == 'greater_equal' and int(source_field_value_number) >= int(source_field_string) ) or
                                        ( source_field_compare_id == 'less' and int(source_field_value_number) < int(source_field_string) ) or 
                                        ( source_field_compare_id == 'less_equal' and int(source_field_value_number) <= int(source_field_string) )
                                    ):

                                        run_action = True

                            if run_action:
                                
                                search_results_base_remove.append(item)

                                search_results_base_submissions.append({
                                    'program_search_results_entry_id_input': item['entry_id'],
                                    'program_search_results_title_input': item['title'],
                                    'program_search_results_release_year_input': item['release_year'],
                                    'program_search_results_object_type_input': item['object_type'],
                                    'program_search_results_short_description_input': item['short_description'],
                                    'program_search_results_url_input': item['url'],
                                    'program_search_results_poster_input': item['poster'],
                                    'program_search_results_score_input': item['score'],
                                    'program_search_results_labels_input': target_label_ids,
                                    'program_search_results_status_input': target_status,
                                    'program_search_results_action_input': target_action
                                })

                                print(f"{current_time()} INFO: Bookmarked '{item['title']} ({item['release_year']}) | {item['object_type']}' using Feed Map '{feed_map_name}'.")

                                break

                    if run_action:
                        break

        if search_results_base_submissions:
            bookmarking_actions_message, clear_results_flag = run_slm_bookmarking_actions(search_results_base_submissions)
            print(bookmarking_actions_message)

        search_results = [item for item in search_results_base if item not in search_results_base_remove]

    else:
        search_results = search_results_base.copy()

    return search_results

# Filters and cleans SLM Search Results
def filter_clean_slm_search_results(program_search_results_check, hide_bookmarked, minimum_video_length, modify_flag):
    message = None

    if not modify_flag:
        bookmarks = read_data(csv_bookmarks)
        bookmarks_statuses = read_data(csv_bookmarks_status)
        subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)

        # Filter out previously bookmarked
        if hide_bookmarked == "On":
            bookmarked_entry_ids = {}
            bookmarks_statuses_slm_stream_urls = {}
            subscribed_video_channels_url_lookup = {}

            if bookmarks:
                bookmarked_entry_ids = {bookmark['entry_id'] for bookmark in bookmarks}
            if bookmarks_statuses:
                bookmarks_statuses_slm_stream_urls = {bookmarks_status["stream_link_override"] for bookmarks_status in bookmarks_statuses if bookmarks_status['special_action'] == "Make SLM Stream"}
            if subscribed_video_channels:
                subscribed_video_channels_url_lookup = {subscribed_video_channel["channel_url"] for subscribed_video_channel in subscribed_video_channels}

            program_search_results_check = [entry for entry in program_search_results_check if entry['entry_id'] not in bookmarked_entry_ids and entry['url'] not in bookmarks_statuses_slm_stream_urls and entry['url'] not in subscribed_video_channels_url_lookup]

        # Do not show already hidden
        hidden_bookmarks = {}
        hidden_videos = {}
        hidden_subscribed_video_channels = {}

        if bookmarks:
            hidden_bookmarks = {bookmark['entry_id'] for bookmark in bookmarks if bookmark['bookmark_action'] == "Hide"}
        if bookmarks_statuses:
            hidden_videos = {bookmarks_status["stream_link_override"] for bookmarks_status in bookmarks_statuses if bookmarks_status['entry_id'] == hidden_videos_entry_id}
        if subscribed_video_channels:
            hidden_subscribed_video_channels = {subscribed_video_channel["channel_url"] for subscribed_video_channel in subscribed_video_channels if subscribed_video_channel["channel_hidden"] == "True"}
        
        program_search_results_check = [entry for entry in program_search_results_check if entry['entry_id'] not in hidden_bookmarks and entry['url'] not in hidden_videos and entry['url'] not in hidden_subscribed_video_channels]

        # Filter out videos with durations less than xxx seconds
        below_minimum_video_length_lookup = [program_search_result['url'] for program_search_result in program_search_results_check if program_search_result['object_type'] == "VIDEO" and int(parse_duration_to_seconds(program_search_result['score'])) <= int(minimum_video_length) ]
        program_search_results_check = [entry for entry in program_search_results_check if entry['url'] not in below_minimum_video_length_lookup]

    if program_search_results_check:
        # Replace None in 'poster' with the default URL
        default_poster_url = 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Missing_barnstar.jpg'
        for entry in program_search_results_check:
            if entry['poster'] is None or entry['poster'] == '':
                entry['poster'] = default_poster_url

    else:
        message = f"{current_time()} INFO: After filtering for bookmarked and/or hidden content, no additional results available."

    return program_search_results_check, message

# Runs the necessary bookmarking actions
def run_slm_bookmarking_actions(program_search_results_base_submissions):
    set_slm_process_active_flag('single_on')

    bookmarks = read_data(csv_bookmarks)
    bookmarks_entry_id_lookup = {bookmark["entry_id"] for bookmark in bookmarks}
    write_bookmarks_flag = False

    bookmarks_statuses = read_data(csv_bookmarks_status)
    bookmarks_statuses_slm_stream_urls = {bookmarks_status["stream_link_override"] for bookmarks_status in bookmarks_statuses if bookmarks_status['special_action'] == "Make SLM Stream"}
    write_bookmarks_statuses_flag = False

    subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
    subscribed_video_channels_url_lookup = {subscribed_video_channel["channel_url"] for subscribed_video_channel in subscribed_video_channels}
    write_subscribed_video_channels_flag = False

    label_maps = read_data(csv_slm_label_maps)
    write_label_maps_flag = False

    bookmarked_count = 0
    hide_bookmarked_count = 0
    previously_bookmarked_count = 0
    generate_stream_links_count = 0
    metadata_import_error_count = 0
    new_video_group_count = 1
    program_search_results_submissions = []
    generate_stream_links_entry_ids = []
    manual_entry_id = None

    message = None
    clear_results_flag = None

    if program_search_results_base_submissions:

        for program_search_results_base_submission in program_search_results_base_submissions:

            if program_search_results_base_submission['program_search_results_action_input'] != 'none':

                # Reject existing bookmarks
                if (
                    ( program_search_results_base_submission['program_search_results_object_type_input'] in ["MOVIE", "SHOW"] and program_search_results_base_submission['program_search_results_entry_id_input'] in bookmarks_entry_id_lookup )
                    or ( program_search_results_base_submission['program_search_results_object_type_input'] == "VIDEO" and program_search_results_base_submission['program_search_results_url_input'] in bookmarks_statuses_slm_stream_urls )
                    or ( program_search_results_base_submission['program_search_results_object_type_input'] == "CHANNEL" and program_search_results_base_submission['program_search_results_url_input'] in subscribed_video_channels_url_lookup ) 
                ):
                    previously_bookmarked_count = int(previously_bookmarked_count) + 1

                else:
                    program_search_results_submissions.append(program_search_results_base_submission)

        if program_search_results_submissions or previously_bookmarked_count > 0:

            if program_search_results_submissions:

                video_group_entry_id_same = None
                entry_id_feed_items_remove_lookup = []
                url_feed_items_remove_lookup = []
                
                for program_search_results_submission in program_search_results_submissions:

                    field_entry_id = program_search_results_submission['program_search_results_entry_id_input']
                    field_title = program_search_results_submission['program_search_results_title_input']
                    field_release_year = program_search_results_submission['program_search_results_release_year_input']
                    field_object_type = program_search_results_submission['program_search_results_object_type_input']
                    field_short_description = program_search_results_submission['program_search_results_short_description_input']
                    field_url = program_search_results_submission['program_search_results_url_input']
                    field_poster = program_search_results_submission['program_search_results_poster_input']
                    field_score = program_search_results_submission['program_search_results_score_input']
                    field_labels = program_search_results_submission['program_search_results_labels_input']
                    field_status = program_search_results_submission['program_search_results_status_input']
                    field_action = program_search_results_submission['program_search_results_action_input']

                    if field_action == 'hide':
                        hide_bookmarked_count = int(hide_bookmarked_count) + 1
                    else:
                        bookmarked_count = int(bookmarked_count) + 1

                    if field_object_type in ['MOVIE', 'SHOW', 'VIDEO']:
                        season_episode_prefix = None
                        stream_link = None
                        stream_link_file = None
                        channels_id = None

                        entry_id = None
                        if field_action == 'manual' or field_object_type == 'VIDEO':

                            if field_action.startswith('add'):
                                entry_id = field_action.split('_')[-1]

                            elif field_action in ['manual', 'playlist', 'new_unique', 'new_same']:

                                manual_entry_id = get_manual_entry_id(bookmarks)

                                if (
                                    ( field_action in ['manual', 'new_unique'] )
                                    or ( field_action in ['playlist', 'new_same'] and ( video_group_entry_id_same is None or video_group_entry_id_same == '' ) )
                                ):

                                    entry_id = manual_entry_id

                                    if field_action in ['playlist', 'new_same']:
                                        video_group_entry_id_same = entry_id

                                else:
                                    entry_id = video_group_entry_id_same

                            elif field_action == 'hide':
                                entry_id = hidden_videos_entry_id

                        elif field_object_type in ['MOVIE', 'SHOW']:
                            entry_id = field_entry_id
                            entry_id_feed_items_remove_lookup.append(entry_id)

                        if 'generate' in field_action:
                            generate_stream_links_entry_ids.append(entry_id)

                        status = None
                        if field_action == 'hide':
                            status = 'watched'

                        else:
                            status = field_status

                        bookmarks_status_items = []
                        if field_object_type == 'VIDEO' or ( field_object_type in ['MOVIE', 'SHOW'] and field_action != 'hide' ):

                            season_episodes = []
                            if field_action == 'manual' and field_object_type in ['SHOW', 'VIDEO']:

                                if field_object_type == 'SHOW':
                                    end_season = int(request.form.get('last_season_number'))

                                    season_episodes_manual = {}
                                    for i in range(1, end_season + 1):
                                        season_episodes_manual[i] = request.form.get(f'season_episode_number_{i}')

                                    season_episodes = get_episode_list_manual(end_season, season_episodes_manual)

                                elif field_object_type == 'VIDEO':
                                    number_of_videos_input = int(request.form.get('number_of_videos'))

                                    for i in range(1, int(number_of_videos_input) + 1):
                                        video_season_episode = f"Input name for Video {i:02d}"
                                        season_episodes.append({
                                            "season_episode_id": '',
                                            "season_episode": video_season_episode,
                                            "status": "unwatched",
                                            "override_episode_title": '',
                                            "override_summary": '',
                                            "override_duration": '',
                                            'original_release_date': ''
                                        })

                            elif field_object_type == 'SHOW':
                                season_episodes = get_episode_list(field_entry_id, field_url, settings_country_code_input_prior, settings_language_code_input_prior)
                            
                            else:
                                season_episodes.append({
                                    "season_episode_id": 'single',
                                    "season_episode": '',
                                    "status": '',
                                    "override_episode_title": '',
                                    "override_summary": '',
                                    "override_duration": ''
                                })

                            for season_episode in season_episodes:

                                field_season_episode_id = ''
                                if season_episode['season_episode_id'] != 'single':
                                    field_season_episode_id = season_episode['season_episode_id']
                                    
                                field_season_episode = ''
                                if field_object_type == 'SHOW' or ( field_action == 'manual' and field_object_type == 'VIDEO' ):
                                    field_season_episode = season_episode['season_episode']
                                elif field_object_type == 'VIDEO':
                                    field_season_episode = check_video_name_unique(bookmarks_statuses, entry_id, f"{field_title} ({field_release_year})")

                                field_stream_link_override = ''
                                if field_object_type == 'VIDEO' and field_action != 'manual':
                                    field_stream_link_override = field_url
                                    url_feed_items_remove_lookup.append(field_stream_link_override)

                                field_special_action = 'None'
                                if field_object_type == 'VIDEO':
                                    field_special_action = 'Make SLM Stream'

                                field_original_release_date = ''
                                field_override_episode_title = ''
                                field_override_summary = ''
                                field_override_image = ''
                                field_override_duration = ''
                                if not field_action in ['manual', 'hide']:

                                    if field_object_type in ['MOVIE', 'SHOW']:

                                        if field_object_type == 'MOVIE':
                                            original_release_date_raw =  get_movie_show_metadata_item(entry_id, settings_country_code_input_prior, settings_language_code_input_prior, 'originalReleaseDate')
                                            if original_release_date_raw:
                                                field_original_release_date = original_release_date_raw

                                        elif field_object_type == 'SHOW':
                                            field_original_release_date = season_episode['original_release_date']

                                        if 'import' in field_action:

                                            if field_object_type == 'MOVIE':
                                                field_override_summary = field_short_description
                                                field_override_image = field_poster
                                                field_override_duration = get_movie_show_metadata_item(entry_id, settings_country_code_input_prior, settings_language_code_input_prior, 'runtime')

                                            elif field_object_type == 'SHOW':
                                                field_override_episode_title = season_episode['override_episode_title']
                                                field_override_summary = season_episode['override_summary']
                                                field_override_duration = season_episode['override_duration']

                                    elif field_object_type == 'VIDEO':
                                        field_original_release_date, field_override_episode_title, field_override_summary, field_override_image, field_override_duration = get_video_metadata(field_stream_link_override)

                                    if field_object_type == 'VIDEO' or ( field_object_type in ['MOVIE', 'SHOW'] and 'import' in field_action ):
                                        if ( 
                                            ( field_original_release_date is None or field_original_release_date == '' ) and
                                            ( field_override_episode_title is None or field_override_episode_title == '' ) and
                                            ( field_override_summary is None or field_override_summary == '' ) and
                                            ( field_override_image is None or field_override_image == '' ) and
                                            ( field_override_duration is None or field_override_duration == '' )
                                        ):
                                            metadata_import_error_count = int(metadata_import_error_count) + 1

                                field_manual_order = ''
                                if field_object_type == 'VIDEO' and field_action != 'manual':
                                    for bookmark in bookmarks:
                                        if bookmark['entry_id'] == entry_id:
                                            if bookmark['override_program_sort'] == 'manual':
                                                field_manual_order = max(int(bookmarks_status['manual_order']) for bookmarks_status in bookmarks_statuses if bookmarks_status['entry_id'] == entry_id) + 1
                                            break

                                bookmarks_status_items.append({
                                    'season_episode_id': field_season_episode_id,
                                    'season_episode': field_season_episode,
                                    'stream_link_override': field_stream_link_override,
                                    'special_action': field_special_action,
                                    'original_release_date': field_original_release_date,
                                    'override_episode_title': field_override_episode_title,
                                    'override_summary': field_override_summary,
                                    'override_image': field_override_image,
                                    'override_duration': field_override_duration,
                                    'manual_order': field_manual_order
                                })

                        if bookmarks_status_items:

                            write_bookmarks_statuses_flag = True

                            for bookmarks_status_item in bookmarks_status_items:
                                season_episode_id = None
                                season_episode = None
                                stream_link_override = None
                                special_action = None
                                original_release_date = None
                                override_episode_title = None
                                override_summary = None
                                override_image = None
                                override_duration = None
                                manual_order = None

                                season_episode_id = bookmarks_status_item['season_episode_id']
                                season_episode = bookmarks_status_item['season_episode']
                                stream_link_override = bookmarks_status_item['stream_link_override']
                                special_action = bookmarks_status_item['special_action']
                                original_release_date = bookmarks_status_item['original_release_date']
                                override_episode_title = bookmarks_status_item['override_episode_title']
                                override_summary = bookmarks_status_item['override_summary']
                                override_image = bookmarks_status_item['override_image']
                                override_duration = bookmarks_status_item['override_duration']
                                manual_order = bookmarks_status_item['manual_order']

                                bookmarks_statuses.append({
                                    "entry_id": entry_id,
                                    "season_episode_id": season_episode_id,
                                    "season_episode_prefix": season_episode_prefix,
                                    "season_episode": season_episode,
                                    "status": status,
                                    "stream_link": stream_link,
                                    "stream_link_override": stream_link_override,
                                    "stream_link_file": stream_link_file,
                                    "special_action": special_action,
                                    "original_release_date": original_release_date,
                                    "override_episode_title": override_episode_title,
                                    "override_summary": override_summary,
                                    "override_image": override_image,
                                    "override_duration": override_duration,
                                    "channels_id": channels_id,
                                    "manual_order": manual_order
                                })

                        bookmarks_entry_id_lookup = {bookmark["entry_id"] for bookmark in bookmarks}
                        if entry_id not in bookmarks_entry_id_lookup:
                            write_bookmarks_flag = True

                            object_type = field_object_type

                            title = ''
                            if entry_id == hidden_videos_entry_id:
                                title = 'SLM INTERNAL ONLY: Hidden Videos'
                            elif field_action == 'playlist':
                                title = field_score
                            elif object_type == 'VIDEO' and field_action != 'manual':
                                title = f"New Video Group (Playlist) #{new_video_group_count}"
                                new_video_group_count = int(new_video_group_count) + 1
                            elif object_type in ['MOVIE', 'SHOW'] or field_action == 'manual':
                                title = field_title

                            release_year = '1888'
                            if entry_id != hidden_videos_entry_id:
                                if object_type == 'VIDEO' and field_action != 'manual':
                                    release_year = 'change'
                                else:
                                    release_year = field_release_year

                            url = ''
                            if field_action == 'playlist':
                                url = program_add_import_playlist_prior
                            elif object_type in ['MOVIE', 'SHOW'] and field_action != 'manual':
                                url = field_url

                            country_code = ''
                            language_code = ''
                            if field_action != 'manual' and entry_id != hidden_videos_entry_id:
                                country_code = settings_country_code_input_prior
                                language_code = settings_language_code_input_prior

                            bookmark_action = 'None'
                            if field_action == 'hide' and entry_id != hidden_videos_entry_id:
                                bookmark_action = 'Hide'
                            elif object_type == 'SHOW' and field_action != 'manual':
                                if 'disable' in field_action:
                                    bookmark_action = 'Disable Get New Episodes'
                                elif 'import' in field_action:
                                    bookmark_action = 'Import New Episode Metadata'

                            channels_id = ''

                            override_program_title = ''
                            override_program_summary = ''
                            override_program_image_type = 'na'
                            override_program_image_manual = ''
                            override_program_sort = 'na'

                            if field_action != 'manual':

                                if object_type == 'VIDEO':
                                    if field_action == 'playlist':
                                        override_program_summary = field_short_description
                                    override_program_image_type = 'first'
                                    override_program_sort = 'dateoriginal_forward'
                                
                                elif object_type in ['MOVIE', 'SHOW'] and 'import' in field_action:
                                    override_program_title = field_title

                                    if object_type == 'SHOW':
                                        override_program_summary = field_short_description
                                        override_program_image_type = 'manual'
                                        override_program_image_manual = field_poster

                            bookmarks.append({
                                'entry_id': entry_id,
                                'title': title,
                                'release_year': release_year,
                                'object_type': object_type,
                                'url': url,
                                'country_code': country_code,
                                'language_code': language_code,
                                'bookmark_action': bookmark_action,
                                'channels_id': channels_id,
                                'override_program_title': override_program_title,
                                'override_program_summary': override_program_summary,
                                'override_program_image_type': override_program_image_type,
                                'override_program_image_manual': override_program_image_manual,
                                'override_program_sort': override_program_sort
                            })

                        if field_labels:

                            write_label_maps_flag = True

                            for field_label in field_labels:
                                label_maps.append({
                                    'label_id': field_label,
                                    'entry_id': entry_id
                                })

                    elif field_object_type == "CHANNEL":

                        write_subscribed_video_channels_flag = True
                        channel_id = get_next_video_channel_id(subscribed_video_channels)

                        if field_status == 'watched' or field_action == 'hide':
                            channel_active = 'Off'

                        else:
                            channel_active = 'On'

                        if field_action == 'hide':
                            channel_hidden = 'True'

                        else:
                            channel_hidden = 'False'

                        if field_action in ['hide', 'subscribe', 'subscribe_edit']:
                            channel_streaming_service_group = 'None'
                        else:
                            channel_streaming_service_group = f"slmpg_{field_action.split('_')[-1]}"

                        subscribed_video_channels.append({
                            'channel_id': channel_id,
                            'channel_active': channel_active,
                            'channel_name': field_title,
                            'channel_user': field_release_year,
                            'channel_description': field_short_description,
                            'channel_url': field_url,
                            'channel_image': field_poster,
                            'channel_streaming_service_group': channel_streaming_service_group,
                            'channel_hidden': channel_hidden
                        })

                    if any(term in field_action for term in ['edit', 'manual', 'playlist', 'new']):
                        edit_entry_id = None

                        if field_object_type == "CHANNEL":
                            edit_entry_id = channel_id
                        else:
                            edit_entry_id = entry_id

                        select_programs_to_edit_lookup = []
                        select_programs_to_edit_lookup = ( select_program_to_edit['entry_id'] for select_program_to_edit in select_programs_to_edit )
                        if edit_entry_id not in select_programs_to_edit_lookup:
                            select_programs_to_edit.append({
                                'entry_id': edit_entry_id,
                                'object_type': field_object_type
                            })

                feed_items = read_data(csv_slm_feed_items)
                if feed_items and ( len(entry_id_feed_items_remove_lookup) > 0 or len(url_feed_items_remove_lookup) > 0 ):

                    temp_record = create_temp_record(feed_items[0].keys())
                    run_empty_rows = False

                    feed_items = [feed_item for feed_item in feed_items if not feed_item['entry_id'] in entry_id_feed_items_remove_lookup and not feed_item['url'] in url_feed_items_remove_lookup]

                    if not feed_items:
                        feed_items.append(temp_record)
                        run_empty_rows = True

                    write_data(csv_slm_feed_items, feed_items)
                    if run_empty_rows:
                        remove_empty_row(csv_slm_feed_items)

                message = f"{current_time()} INFO: After selections/imports, {bookmarked_count} item(s) bookmarked, {hide_bookmarked_count} item(s) hidden, and {previously_bookmarked_count} item(s) skipped due to already being previously bookmarked."

            elif previously_bookmarked_count > 0:
                message = f"{current_time()} WARNING: Nothing was bookmarked due to all selected/imported items already being previously bookmarked."

            clear_results_flag = True

        else:
            if message is None or message == '':
                if message not in [None, '']:
                    message += f"\n"
                message += f"{current_time()} WARNING: Nothing was bookmarked due to no actions selected. Please try again or clear results."

    if int(metadata_import_error_count) > 0:                    
        if message not in [None, '']:
            message += f"\n"
        message += f"{current_time()} ERROR: Metadata was unable to be imported for {metadata_import_error_count} items. Please review and verify item details."

    if write_bookmarks_flag:
        for bookmark in bookmarks:
            if bookmark['release_year'] == 'change':
                bookmark['release_year'] = min(int(bookmarks_status['original_release_date'][:4]) for bookmarks_status in bookmarks_statuses if bookmarks_status['entry_id'] == bookmark['entry_id'])
        write_data(csv_bookmarks, bookmarks)

    if write_bookmarks_statuses_flag:
        write_data(csv_bookmarks_status, bookmarks_statuses)
    
    if write_label_maps_flag:
        write_data(csv_slm_label_maps, label_maps)

    if write_subscribed_video_channels_flag:
        if len(subscribed_video_channels) > 1:
            subscribed_video_channels = sorted(subscribed_video_channels, key=lambda x: sort_key(x["channel_name"].casefold()))
        write_data(csv_slm_subscribed_video_channels, subscribed_video_channels)

    set_slm_process_active_flag('single_off')

    if generate_stream_links_entry_ids:
        unique_generate_stream_links_entry_ids = []

        for generate_stream_links_entry_id in generate_stream_links_entry_ids:
            if generate_stream_links_entry_id not in unique_generate_stream_links_entry_ids:
                unique_generate_stream_links_entry_ids.append(generate_stream_links_entry_id)

        for generate_stream_links_entry_id in unique_generate_stream_links_entry_ids:
            generate_stream_links_single(generate_stream_links_entry_id)
            generate_stream_links_count = int(generate_stream_links_count) + 1

        if int(generate_stream_links_count) > 0:
            message += f"\n"
            message += f"{current_time()} INFO: Also generated Stream Links for {generate_stream_links_count} program(s)."

    return message, clear_results_flag

# Create a new entry_id for manual programs
def get_manual_entry_id(bookmarks):

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

# Create a new label_id for an added Label
def get_next_label_id(slm_labels):
    next_label_id = f"slmlbl_{max((int(slm_label['label_id'].split('_')[1]) for slm_label in slm_labels), default=0) + 1:04d}"
    return next_label_id

# Create a new channel_id for an added Video Channel
def get_next_video_channel_id(subscribed_video_channels):
    next_channel_id = f"slmchn_{max((int(subscribed_video_channel['channel_id'].split('_')[1]) for subscribed_video_channel in subscribed_video_channels), default=0) + 1:04d}"
    return next_channel_id

# Create a new feed_rule_id for an added Feed Rule
def get_next_feed_rule_id(feed_rules):
    next_feed_rule_id = f"slmfr_{max((int(feed_rule['feed_rule_id'].split('_')[1]) for feed_rule in feed_rules), default=0) + 1:04d}"
    return next_feed_rule_id

# Create a new feed_map_id for an added Feed map
def get_next_feed_map_id(feed_maps):
    next_feed_map_id = f"slmfm_{max((int(feed_map['feed_map_id'].split('_')[1]) for feed_map in feed_maps), default=0) + 1:04d}"
    return next_feed_map_id

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
        season_episodes_results.append({
            "season_episode_id": None,
            "season_episode": season_episode,
            "status": "unwatched",
            "override_episode_title": '',
            "override_summary": '',
            "override_duration": '',
            'original_release_date': ''
        })

    season_episodes_sorted = sorted(season_episodes_results, key=lambda d: d['season_episode'])

    return season_episodes_sorted

# Get a list of labels and status for a specific program
def get_webpage_label_maps():
    labels = read_data(csv_slm_labels)
    label_maps = read_data(csv_slm_label_maps)
    entry_id_label_maps = [label_map['label_id'] for label_map in label_maps if label_map['entry_id'] == entry_id_selected_prior]
    webpage_label_maps = []

    for label in labels:
        if label['label_active'] == "On":

            if label['label_id'] in entry_id_label_maps:
                webpage_label_active = "On"
            else:
                webpage_label_active = "Off"

            webpage_label_maps.append({
                'webpage_label_active': webpage_label_active,
                'webpage_label_id': label['label_id'],
                'webpage_label_name': label['label_name']
            })

    return webpage_label_maps

# Get metadata for SLM Stream videos
def get_video_metadata(url):
    info_dict = {}
    default_poster_url = 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Missing_barnstar.jpg'

    original_release_date = None
    override_episode_title = None
    override_summary = None
    override_image = None
    override_duration = None

    metadata_items = [
        original_release_date,
        override_episode_title,
        override_summary,
        override_image,
        override_duration
    ]

    m3u8_url, m3u8_protocol, info_dict = get_online_video(url, "metadata")

    if info_dict:

        original_release_date = info_dict.get('upload_date', None)
        if original_release_date:
            original_release_date = f"{original_release_date[:4]}-{original_release_date[4:6]}-{original_release_date[6:]}"
        override_episode_title = info_dict.get('title', None)
        override_summary = info_dict.get('description', None)
        override_image = info_dict.get('thumbnail', None)
        override_duration = info_dict.get('duration', None)

        if not override_image:
            thumbnails = info_dict.get('thumbnails', [])
            if thumbnails:
                override_image = thumbnails[0].get('url', None)

        for metadata_item in metadata_items:
            if metadata_item is not None:
                if metadata_item.lower() == "null":
                    metadata_item = None

    else:

        video_id = None

        if 'youtube' in url:
            video_id = url.split('?v=')[1]
        elif 'youtu.' in url:
            video_id = url.split('/')[1]

        if video_id:
            try:
                info_dict = get_youtube_video_info.getInfo(video_id)
            except Exception as error:
                print(f"{current_time()} ERROR: While processing {url} using secondary method, error was: {error}")

        if info_dict:
            original_release_date = '9999-12-31'
            override_episode_title = info_dict.get('title', None)
            override_summary = info_dict.get('description', None)
            thumbnails = info_dict.get('thumbnails', [])
            if thumbnails:
                override_image = max(thumbnails, key=lambda t: t.get('width', 0)).get('url', default_poster_url)
            override_duration = info_dict.get('duration', {}).get('secondsText', None)
            if override_duration == '0' or int(override_duration) == 0:
                override_duration = None

    if override_duration == '0' or int(override_duration) == 0:
        override_duration = ''

    return original_release_date, override_episode_title, override_summary, override_image, override_duration

# Manage Providers Webpage
@app.route('/manage_providers', methods=['GET', 'POST'])
def webpage_manage_providers():
    global slm_stream_address_prior
    settings_anchor_id = None
    run_empty_row = None

    action_to_anchor = {
        'streaming_services': 'streaming_services_anchor',
        'ssss': 'ssss_anchor',
        'provider_group': 'provider_group_anchor',
        'slmapping': 'slmapping_anchor',
        'slm_stream_address': 'slm_stream_address_anchor',
        'slm_label': 'slm_label_anchor',
        'subscribed_video_channel':'subscribed_video_channels_anchor',
        'show_hidden_subscribed_video_channel':'subscribed_video_channels_anchor',
        'file_name_options': 'file_name_options_anchor'
    }

    # Streaming Services
    streaming_services = read_data(csv_streaming_services)
    streaming_services_subscribed_raw = [streaming_service for streaming_service in streaming_services if streaming_service['streaming_service_subscribe'] == 'True']
    streaming_services_subscribed = sorted(streaming_services_subscribed_raw, key=lambda x: sort_key(x["streaming_service_name"]))

    # Subscribed Video Channels
    subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
    if subscribed_video_channels:
        visible_subscribed_video_channels = [subscribed_video_channel for subscribed_video_channel in subscribed_video_channels if subscribed_video_channel['channel_hidden'] == 'False']
    else:
        visible_subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
    subscribed_video_channels_message = ''

    # Provider Groups
    provider_groups_raw = read_data(csv_provider_groups)
    provider_groups = provider_groups_default.copy()
    if provider_groups_raw:
        provider_groups_raw = sorted(provider_groups_raw, key=lambda x: sort_key(x["provider_group_name"].casefold()))
        for provider_group_raw in provider_groups_raw:
            if provider_group_raw["provider_group_active"] == "On":
                provider_groups.append({
                    "provider_group_id": provider_group_raw["provider_group_id"],
                    "provider_group_name": f"GROUP: {provider_group_raw['provider_group_name']}"
                })

    # Stream Link Mappings
    slmappings = read_data(csv_slmappings)
    slmappings_object_type = [
        "MOVIE or SHOW",
        "MOVIE",
        "SHOW"
    ]

    slmappings_replace_type = [
        "Replace string with...",
        "Replace pattern (REGEX) with...",
        "Replace entire Stream Link with..."
    ]

    # Labels
    slm_labels = read_data(csv_slm_labels)

    # SLM Stream Address
    settings = read_data(csv_settings)
    slm_stream_address = settings[46]['settings']                               # [46] SLM: SLM Stream Address
    if slm_stream_address_prior is None or slm_stream_address_prior == '':
        slm_stream_address_prior = slm_stream_address
    slm_stream_address_message = ""    

    # File Name Management
    settings_slm_add_show_title = settings[73]['settings']                      # [73] SLM: Add TV Show Title to File Name On/Off
    settings_slm_add_episode_title = settings[74]['settings']                   # [74] SLM: Add Episode Title to TV Show File Name On/Off

    if request.method == 'POST':
        settings_action = request.form['action']
        slm_stream_address_input = request.form.get('slm_stream_address')
        streaming_services_input = request.form.get('streaming_services')

        for prefix, anchor_id in action_to_anchor.items():
            if settings_action.startswith(prefix):
                settings_anchor_id = anchor_id
                break

        checks = ['slmapping_', 'slm_stream_address_', 'streaming_services_', 'ssss_', 'provider_group_', 'slm_label_', 'subscribed_video_channel_', 'file_name_options_']
        if any(settings_action.startswith(check) for check in checks):

            interior_checks = ['slmapping_', 'provider_group_', 'slm_label_', 'subscribed_video_channel_']
            if ( any(settings_action.startswith(interior_check) for interior_check in interior_checks) or '_save' in settings_action ) and ( 'cancel' not in settings_action ):

                write_csv = True

                if settings_action in ['slm_stream_address_save',
                                       'file_name_options_save'
                                      ]:

                    if settings_action == 'slm_stream_address_save':
                        settings[46]["settings"] = slm_stream_address_input
                        slm_stream_address_prior = slm_stream_address_input

                    if settings_action == 'file_name_options_save':
                        settings[73]['settings'] = 'On' if request.form.get('settings_slm_add_show_title') in ['on', 'On', 'ON'] else 'Off'
                        settings[74]['settings'] = 'On' if request.form.get('settings_slm_add_episode_title') in ['on', 'On', 'ON'] else 'Off'

                    csv_to_write = csv_settings
                    data_to_write = settings

                elif 'ssss_save' in settings_action or settings_action in ['streaming_services_save'
                                                                          ]:

                    csv_to_write = csv_streaming_services

                    if settings_action == 'streaming_services_save':
                        streaming_services_input_json = json.loads(streaming_services_input)
                        data_to_write = streaming_services_input_json

                    elif 'ssss_save' in settings_action:
                        ssss_inputs = []
                        
                        ssss_streaming_service_active_inputs = {}
                        ssss_streaming_service_name_inputs = {}
                        ssss_streaming_service_group_inputs = {}

                        total_number_of_checkboxes = len(streaming_services_subscribed)
                        ssss_streaming_service_active_inputs = {str(i): 'Off' for i in range(1, total_number_of_checkboxes + 1)}

                        for key in request.form.keys():
                            if key.startswith('ssss_streaming_service_active_'):
                                index = key.split('_')[-1]
                                ssss_streaming_service_active_inputs[index] = request.form.get(key)
                            
                            if key.startswith('ssss_streaming_service_name_'):
                                index = key.split('_')[-1]
                                ssss_streaming_service_name_inputs[index] = request.form.get(key)
                            
                            if key.startswith('ssss_streaming_service_group_'):
                                index = key.split('_')[-1]
                                ssss_streaming_service_group_inputs[index] = request.form.get(key)

                        for row in ssss_streaming_service_active_inputs:
                            ssss_streaming_service_active_input = ssss_streaming_service_active_inputs.get(row)
                            ssss_streaming_service_name_input = ssss_streaming_service_name_inputs.get(row)
                            ssss_streaming_service_group_input = ssss_streaming_service_group_inputs.get(row)

                            for idx, streaming_service in enumerate(streaming_services_subscribed):
                                if idx == int(row) - 1:
                                    ssss_inputs.append({
                                        "streaming_service_name": ssss_streaming_service_name_input,
                                        "streaming_service_active": ssss_streaming_service_active_input,
                                        "streaming_service_group": ssss_streaming_service_group_input
                                    })

                        if settings_action.endswith('all'):
                            for streaming_service in streaming_services:
                                for ssss_input in ssss_inputs:
                                    if streaming_service['streaming_service_name'] == ssss_input['streaming_service_name']:
                                        streaming_service['streaming_service_active'] = ssss_input['streaming_service_active']
                                        streaming_service['streaming_service_group'] = ssss_input['streaming_service_group']
                        
                        else:
                            ssss_index = int(settings_action.split('_')[-1]) - 1
                            for streaming_service in streaming_services:
                                if streaming_service['streaming_service_name'] == ssss_inputs[ssss_index]['streaming_service_name']:
                                    streaming_service['streaming_service_active'] = ssss_inputs[ssss_index]['streaming_service_active']
                                    streaming_service['streaming_service_group'] = ssss_inputs[ssss_index]['streaming_service_group']

                        data_to_write = streaming_services

                elif settings_action.startswith('provider_group_'):

                    # Add a record
                    if settings_action == 'provider_group_new':
                        provider_group_id_new_input = f"slmpg_{max((int(provider_group_raw['provider_group_id'].split('_')[1]) for provider_group_raw in provider_groups_raw), default=0) + 1:04d}"
                        provider_group_active_new_input = 'On' if request.form.get('provider_group_active_new') == 'on' else 'Off'
                        provider_group_name_new_input = request.form.get('provider_group_name_new')
                        provider_group_description_new_input = request.form.get('provider_group_description_new')

                        provider_groups_raw.append({
                            "provider_group_id": provider_group_id_new_input,
                            "provider_group_active": provider_group_active_new_input,
                            "provider_group_name": provider_group_name_new_input,
                            "provider_group_description": provider_group_description_new_input
                        })

                    # Delete a record
                    elif settings_action.startswith('provider_group_delete_'):
                        provider_group_delete_index = int(settings_action.split('_')[-1]) - 1

                        # Create a temporary record with fields set to None
                        temp_record = create_temp_record(provider_groups_raw[0].keys())

                        if 0 <= provider_group_delete_index < len(provider_groups_raw):
                            provider_groups_raw.pop(provider_group_delete_index)

                            # If the list is now empty, add the temp record to keep headers
                            if not provider_groups_raw:
                                provider_groups_raw.append(temp_record)
                                run_empty_row = True

                    # Save record modifications
                    elif settings_action == 'provider_group_save':
                        provider_group_id_inputs = {}
                        provider_group_active_inputs = {}
                        provider_group_name_inputs = {}
                        provider_group_description_inputs = {}

                        total_number_of_checkboxes = len(provider_groups_raw)
                        provider_group_active_inputs = {str(i): 'Off' for i in range(1, total_number_of_checkboxes + 1)}

                        for key in request.form.keys():
                            if key.startswith('provider_group_id_'):
                                index = key.split('_')[-1]
                                provider_group_id_inputs[index] = request.form.get(key)

                            if key.startswith('provider_group_active_'):
                                index = key.split('_')[-1]
                                provider_group_active_inputs[index] = request.form.get(key)

                            if key.startswith('provider_group_name_'):
                                index = key.split('_')[-1]
                                provider_group_name_inputs[index] = request.form.get(key)

                            if key.startswith('provider_group_description_'):
                                index = key.split('_')[-1]
                                provider_group_description_inputs[index] = request.form.get(key)

                        provider_groups_raw = []

                        for row in provider_group_id_inputs:
                            provider_group_id_input = provider_group_id_inputs.get(row)
                            provider_group_active_input = provider_group_active_inputs.get(row)
                            provider_group_name_input = provider_group_name_inputs.get(row)
                            provider_group_description_input = provider_group_description_inputs.get(row)

                            provider_groups_raw.append({
                                'provider_group_id': provider_group_id_input,
                                'provider_group_active': provider_group_active_input,
                                'provider_group_name': provider_group_name_input,
                                'provider_group_description': provider_group_description_input
                            })

                    if not run_empty_row:
                        provider_groups_raw = sorted(provider_groups_raw, key=lambda x: sort_key(x["provider_group_name"].casefold()))

                    csv_to_write = csv_provider_groups
                    data_to_write = provider_groups_raw

                elif settings_action.startswith('slm_label_'):

                    # Add a record
                    if settings_action == 'slm_label_new':
                        slm_label_id_new_input = get_next_label_id(slm_labels)
                        slm_label_active_new_input = 'On' if request.form.get('slm_label_active_new') == 'on' else 'Off'
                        slm_label_name_new_input = request.form.get('slm_label_name_new')
                        slm_label_description_new_input = request.form.get('slm_label_description_new')

                        slm_labels.append({
                            "label_id": slm_label_id_new_input,
                            "label_active": slm_label_active_new_input,
                            "label_name": slm_label_name_new_input,
                            "label_description": slm_label_description_new_input
                        })

                    # Save record modifications
                    elif settings_action == 'slm_label_save':
                        slm_label_id_inputs = {}
                        slm_label_active_inputs = {}
                        slm_label_name_inputs = {}
                        slm_label_description_inputs = {}

                        total_number_of_checkboxes = len(slm_labels)
                        slm_label_active_inputs = {str(i): 'Off' for i in range(1, total_number_of_checkboxes + 1)}

                        for key in request.form.keys():
                            if key.startswith('slm_label_id_'):
                                index = key.split('_')[-1]
                                slm_label_id_inputs[index] = request.form.get(key)

                            if key.startswith('slm_label_active_'):
                                index = key.split('_')[-1]
                                slm_label_active_inputs[index] = request.form.get(key)

                            if key.startswith('slm_label_name_'):
                                index = key.split('_')[-1]
                                slm_label_name_inputs[index] = request.form.get(key)

                            if key.startswith('slm_label_description_'):
                                index = key.split('_')[-1]
                                slm_label_description_inputs[index] = request.form.get(key)

                        slm_labels = []

                        for row in slm_label_id_inputs:
                            slm_label_id_input = slm_label_id_inputs.get(row)
                            slm_label_active_input = slm_label_active_inputs.get(row)
                            slm_label_name_input = slm_label_name_inputs.get(row)
                            slm_label_description_input = slm_label_description_inputs.get(row)

                            slm_labels.append({
                                'label_id': slm_label_id_input,
                                'label_active': slm_label_active_input,
                                'label_name': slm_label_name_input,
                                'label_description': slm_label_description_input
                            })

                    elif settings_action.startswith('slm_label_delete_') or settings_action == 'slm_label_import':

                        # Create a temporary record with fields set to None
                        if slm_labels:
                            temp_record = create_temp_record(slm_labels[0].keys())
                        else:
                            temp_record = initial_data(csv_slm_labels)[0]

                        # Delete a record
                        if settings_action.startswith('slm_label_delete_'):
                            slm_label_delete_index = int(settings_action.split('_')[-1]) - 1

                            slm_label_delete_id = slm_labels[slm_label_delete_index]['label_id']
                            remove_row_csv(csv_slm_label_maps, slm_label_delete_id)

                            if 0 <= slm_label_delete_index < len(slm_labels):
                                slm_labels.pop(slm_label_delete_index)

                        # Import Labels from Channels
                        elif settings_action == 'slm_label_import':
                            print(f"{current_time()} INFO: Starting importing labels from Channels DVR...")

                            dvr_files, dvr_groups = get_slm_channels_info()

                            base_labels = []

                            for dvr_file in dvr_files:
                                item_labels = dvr_file.get('Labels', [])
                                if item_labels:
                                    for item_label in item_labels:
                                        if item_label not in base_labels:
                                            base_labels.append(item_label)

                            for dvr_group in dvr_groups:
                                item_labels = dvr_group.get('Labels', [])
                                if item_labels:
                                    for item_label in item_labels:
                                        if item_label not in base_labels:
                                            base_labels.append(item_label)

                            for base_label in base_labels:
                                if base_label not in [slm_label['label_name'] for slm_label in slm_labels]:
                                    slm_label_id_new_input = get_next_label_id(slm_labels)
                                    slm_label_active_new_input = 'On'
                                    slm_label_name_new_input = base_label
                                    slm_label_description_new_input = ''

                                    slm_labels.append({
                                        "label_id": slm_label_id_new_input,
                                        "label_active": slm_label_active_new_input,
                                        "label_name": slm_label_name_new_input,
                                        "label_description": slm_label_description_new_input
                                    })

                            if slm_labels:
                                bookmarks = read_data(csv_bookmarks)
                                label_maps = read_data(csv_slm_label_maps)

                                for bookmark in bookmarks:
                                    channels_id = bookmark['channels_id']
                                    entry_id = bookmark['entry_id']
                                    channels_labels = []
                                    mapped_channels_labels = []

                                    if bookmark['object_type']  == "MOVIE":
                                        for dvr_file in dvr_files:
                                            if channels_id == dvr_file["File ID"]:
                                                channels_labels = dvr_file.get('Labels', [])
                                                break

                                    else:
                                        for dvr_group in dvr_groups:
                                            if channels_id == dvr_group["Group ID"]:
                                                channels_labels = dvr_group.get('Labels', [])
                                                break

                                    for channels_label in channels_labels:
                                        for slm_label in slm_labels:
                                            if channels_label == slm_label['label_name']:
                                                mapped_channels_labels.append(slm_label['label_id'])
                                                break

                                    for mapped_channels_label in mapped_channels_labels:
                                        label_exists = False

                                        for label_map in label_maps:
                                            if label_map['entry_id'] == entry_id and label_map['label_id'] == mapped_channels_label:
                                                label_exists = True
                                                break

                                        if not label_exists:
                                            label_maps.append({
                                                'label_id': mapped_channels_label,
                                                'entry_id': entry_id
                                            })

                                if label_maps:
                                    write_data(csv_slm_label_maps, label_maps)

                            print(f"{current_time()} INFO: Finished importing labels from Channels DVR.")

                        # If the list is now empty, add the temp record to keep headers
                        if not slm_labels:
                            slm_labels.append(temp_record)
                            run_empty_row = True

                    if not run_empty_row:
                        slm_labels = sorted(slm_labels, key=lambda x: sort_key(x["label_name"].casefold()))

                    csv_to_write = csv_slm_labels
                    data_to_write = slm_labels

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

                        # Create a temporary record with fields set to None
                        temp_record = create_temp_record(slmappings[0].keys())

                        if 0 <= slmapping_action_delete_index < len(slmappings):
                            slmappings.pop(slmapping_action_delete_index)

                            # If the list is now empty, add the temp record to keep headers
                            if not slmappings:
                                slmappings.append(temp_record)
                                run_empty_row = True

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

                elif settings_action.startswith('subscribed_video_channel_'):
                    
                    # Add a record
                    if settings_action == 'subscribed_video_channel_new':
                        subscribed_video_channel_id_new_input = get_next_video_channel_id(subscribed_video_channels)
                        subscribed_video_channel_active_new_input = 'On' if request.form.get('subscribed_video_channel_active_new') == 'on' else 'Off'
                        subscribed_video_channel_name_new_input = request.form.get('subscribed_video_channel_name_new')
                        subscribed_video_channel_user_new_input = request.form.get('subscribed_video_channel_user_new')
                        subscribed_video_channel_description_new_input = request.form.get('subscribed_video_channel_description_new')
                        subscribed_video_channel_url_new_input = request.form.get('subscribed_video_channel_url_new')
                        subscribed_video_channel_image_new_input = request.form.get('subscribed_video_channel_image_new')
                        subscribed_video_channel_streaming_service_group_new_input = request.form.get('subscribed_video_channel_streaming_service_group_new')

                        subscribed_video_channel_url_new_input_valid, subscribed_video_channels_message = check_video_channel_url(subscribed_video_channel_url_new_input, subscribed_video_channels, subscribed_video_channel_id_new_input)

                        if subscribed_video_channel_url_new_input_valid:
                            subscribed_video_channels.append({
                                "channel_id": subscribed_video_channel_id_new_input,
                                "channel_active": subscribed_video_channel_active_new_input,
                                "channel_name": subscribed_video_channel_name_new_input,
                                "channel_user": subscribed_video_channel_user_new_input,
                                "channel_description": subscribed_video_channel_description_new_input,
                                "channel_url": subscribed_video_channel_url_new_input,
                                "channel_image": subscribed_video_channel_image_new_input,
                                "channel_streaming_service_group": subscribed_video_channel_streaming_service_group_new_input,
                                "channel_hidden": "False"
                            })
                            
                        else:
                            write_csv = False

                    # Save all records or delete a record
                    elif settings_action.startswith('subscribed_video_channel_delete_') or settings_action == 'subscribed_video_channel_save':
                        subscribed_video_channel_id_inputs = {}
                        subscribed_video_channel_active_inputs = {}
                        subscribed_video_channel_name_inputs = {}
                        subscribed_video_channel_user_inputs = {}
                        subscribed_video_channel_description_inputs = {}
                        subscribed_video_channel_url_inputs = {}
                        subscribed_video_channel_image_inputs = {}
                        subscribed_video_channel_streaming_service_group_inputs = {}

                        total_number_of_checkboxes = len(subscribed_video_channels)
                        subscribed_video_channel_active_inputs = {str(i): 'Off' for i in range(1, total_number_of_checkboxes + 1)}

                        for key in request.form.keys():
                            if key.startswith('subscribed_video_channel_id_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_id_inputs[index] = request.form.get(key)

                            if key.startswith('subscribed_video_channel_active_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_active_inputs[index] = request.form.get(key)

                            if key.startswith('subscribed_video_channel_name_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_name_inputs[index] = request.form.get(key)

                            if key.startswith('subscribed_video_channel_user_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_user_inputs[index] = request.form.get(key)

                            if key.startswith('subscribed_video_channel_description_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_description_inputs[index] = request.form.get(key)

                            if key.startswith('subscribed_video_channel_url_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_url_inputs[index] = request.form.get(key)

                            if key.startswith('subscribed_video_channel_image_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_image_inputs[index] = request.form.get(key)

                            if key.startswith('subscribed_video_channel_streaming_service_group_'):
                                index = key.split('_')[-1]
                                subscribed_video_channel_streaming_service_group_inputs[index] = request.form.get(key)

                        if settings_action.startswith('subscribed_video_channel_delete_'):
                            subscribed_video_channel_delete_index = int(settings_action.split('_')[-1])
                            subscribed_video_channel_id_delete = subscribed_video_channel_id_inputs[str(subscribed_video_channel_delete_index)]
                            temp_record = create_temp_record(subscribed_video_channels[0].keys())

                        subscribed_video_channels_save_errors = 0
                        subscribed_video_channels_delete_break = False

                        for row in subscribed_video_channel_id_inputs:
                            subscribed_video_channel_id_input = subscribed_video_channel_id_inputs.get(row)
                            subscribed_video_channel_active_input = subscribed_video_channel_active_inputs.get(row)
                            subscribed_video_channel_name_input = subscribed_video_channel_name_inputs.get(row)
                            subscribed_video_channel_user_input = subscribed_video_channel_user_inputs.get(row)
                            subscribed_video_channel_description_input = subscribed_video_channel_description_inputs.get(row)
                            subscribed_video_channel_url_input = subscribed_video_channel_url_inputs.get(row)
                            subscribed_video_channel_image_input = subscribed_video_channel_image_inputs.get(row)
                            subscribed_video_channel_streaming_service_group_input = subscribed_video_channel_streaming_service_group_inputs.get(row)

                            for subscribed_video_channel in subscribed_video_channels:
                                if subscribed_video_channel_id_input == subscribed_video_channel['channel_id']:
                                    
                                    # Save record modifications
                                    if settings_action == 'subscribed_video_channel_save':
                                        subscribed_video_channel['channel_active'] = subscribed_video_channel_active_input
                                        subscribed_video_channel['channel_name'] = subscribed_video_channel_name_input
                                        subscribed_video_channel['channel_user'] = subscribed_video_channel_user_input
                                        subscribed_video_channel['channel_description'] = subscribed_video_channel_description_input
                                        subscribed_video_channel_url_input_valid, subscribed_video_channels_message = check_video_channel_url(subscribed_video_channel_url_input, subscribed_video_channels, subscribed_video_channel_id_input)
                                        if subscribed_video_channel_url_input_valid:
                                            subscribed_video_channel['channel_url'] = subscribed_video_channel_url_input
                                        else:
                                            subscribed_video_channels_save_errors = int(subscribed_video_channels_save_errors) +1
                                        subscribed_video_channel['channel_image'] = subscribed_video_channel_image_input
                                        subscribed_video_channel['channel_streaming_service_group'] = subscribed_video_channel_streaming_service_group_input
                                        if subscribed_video_channel_active_input == "On" and subscribed_video_channel['channel_hidden'] == "True":
                                            subscribed_video_channel['channel_hidden'] = "False"

                                    # Delete a record
                                    elif settings_action.startswith('subscribed_video_channel_delete_'):
                                        if subscribed_video_channel_id_delete == subscribed_video_channel['channel_id']:
                                            subscribed_video_channels.remove(subscribed_video_channel)
                                            subscribed_video_channels_delete_break = True                                              
                                    
                                    break
                                
                            if subscribed_video_channels_delete_break:
                                # If the list is now empty, add the temp record to keep headers
                                if not subscribed_video_channels:
                                    subscribed_video_channels.append(temp_record)
                                    run_empty_row = True
                                break

                        if int(subscribed_video_channels_save_errors) > 0:
                            subscribed_video_channels_message = f"{current_time()} WARNING: Subscribed Video Channels saved, but there was/were {subscribed_video_channels_save_errors} issue(s) with the Link(s). Please review and correct."

                    if not run_empty_row:
                        subscribed_video_channels = sorted(subscribed_video_channels, key=lambda x: sort_key(x["channel_name"].casefold()))

                    csv_to_write = csv_slm_subscribed_video_channels
                    data_to_write = subscribed_video_channels

                if write_csv:
                    write_data(csv_to_write, data_to_write)
                if run_empty_row:
                    remove_empty_row(csv_to_write)

            elif settings_action == 'streaming_services_update':
                update_streaming_services()
                time.sleep(2)

            elif settings_action == 'slm_stream_address_cancel':
                slm_stream_address_prior = slm_stream_address

            elif settings_action == 'slm_stream_address_test':
                slm_stream_address_prior = slm_stream_address_input
                slm_stream_address_okay = check_channels_url(slm_stream_address_input)
                if slm_stream_address_okay:
                    slm_stream_address_message = f"{current_time()} INFO: '{slm_stream_address_input}' responded as expected!"
                else:
                    slm_stream_address_message = f"{current_time()} WARNING: Nothing found at '{slm_stream_address_input}'. Please update!"

        settings = read_data(csv_settings)
        slm_stream_address = settings[46]['settings']                               # [46] SLM: SLM Stream Address
        if slm_stream_address_prior is None or slm_stream_address_prior == '':
            slm_stream_address_prior = slm_stream_address
        settings_slm_add_show_title = settings[73]['settings']                      # [73] SLM: Add TV Show Title to File Name On/Off
        settings_slm_add_episode_title = settings[74]['settings']                   # [74] SLM: Add Episode Title to TV Show File Name On/Off

        streaming_services = read_data(csv_streaming_services)
        streaming_services_subscribed_raw = [streaming_service for streaming_service in streaming_services if streaming_service['streaming_service_subscribe'] == 'True']
        streaming_services_subscribed = sorted(streaming_services_subscribed_raw, key=lambda x: sort_key(x["streaming_service_name"]))

        provider_groups_raw = read_data(csv_provider_groups)
        provider_groups = provider_groups_default.copy()
        if provider_groups_raw:
            provider_groups_raw = sorted(provider_groups_raw, key=lambda x: sort_key(x["provider_group_name"].casefold()))
            for provider_group_raw in provider_groups_raw:
                if provider_group_raw["provider_group_active"] == "On":
                    provider_groups.append({
                        "provider_group_id": provider_group_raw["provider_group_id"],
                        "provider_group_name": f"GROUP: {provider_group_raw['provider_group_name']}"
                    })

        slmappings = read_data(csv_slmappings)

        slm_labels = read_data(csv_slm_labels)
        
        subscribed_video_channels = read_data(csv_slm_subscribed_video_channels)
        if settings_action == 'show_hidden_subscribed_video_channels':
            visible_subscribed_video_channels = subscribed_video_channels
        else:
            visible_subscribed_video_channels = [subscribed_video_channel for subscribed_video_channel in subscribed_video_channels if subscribed_video_channel['channel_hidden'] == 'False']

    response = make_response(render_template(
        'main/slm_manage_providers.html',
        segment='manage_providers',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_settings_anchor_id = settings_anchor_id,
        html_slm_stream_address = slm_stream_address,
        html_slm_stream_address_prior = slm_stream_address_prior,
        html_streaming_services = streaming_services,
        html_streaming_services_subscribed = streaming_services_subscribed,
        html_slm_stream_address_message = slm_stream_address_message,
        html_slmappings = slmappings,
        html_slmappings_object_type = slmappings_object_type,
        html_slmappings_replace_type = slmappings_replace_type,
        html_provider_groups = provider_groups,
        html_provider_groups_raw = provider_groups_raw,
        html_slm_labels = slm_labels,
        html_subscribed_video_channels = visible_subscribed_video_channels,
        html_subscribed_video_channels_message = subscribed_video_channels_message,
        html_settings_slm_add_show_title = settings_slm_add_show_title,
        html_settings_slm_add_episode_title = settings_slm_add_episode_title
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'

    return response

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
        print(f"{current_time()} WARNING: {e}. Skipping, please try again.")

    if provider_results:
        provider_results_json = provider_results.json()
        provider_results_json_array = provider_results_json["data"]["packages"]

        for provider in provider_results_json_array :
            provider_addons = []

            entry = {
                "streaming_service_name": provider["clearName"],
                "streaming_service_subscribe": False,
                "streaming_service_priority": None,
                "streaming_service_active": "On",
                "streaming_service_group": "None"
            }
            provider_results_json_array_results.append(entry)

            provider_addons = provider["addons"]

            if provider_addons:
                for provider_addon in provider_addons:
                    entry = {
                        "streaming_service_name": provider_addon["clearName"],
                        "streaming_service_subscribe": False,
                        "streaming_service_priority": None,
                        "streaming_service_active": "On",
                        "streaming_service_group": "None"
                    }
                    provider_results_json_array_results.append(entry)

    return provider_results_json_array_results

# Update Streaming Services
def update_streaming_services():
    data = get_streaming_services()
    update_rows(csv_streaming_services, data, "streaming_service_name", None)

# Check Video Channel URL validity
def check_video_channel_url(url, subscribed_video_channels, channel_id):
    valid = False
    message = ''
    
    patterns = [
        r'^https?://(?:www\.)?youtu.*?/channel/.+'
    ]
    
    existing_urls_lookup = {subscribed_video_channel['channel_url'] for subscribed_video_channel in subscribed_video_channels if subscribed_video_channel['channel_id'] != channel_id}
    
    if any(re.match(pattern, url) for pattern in patterns):
        if url not in existing_urls_lookup:
            valid = True
        else:
            message = f"{current_time()} ERROR: '{url}' is already assoicated with another Subscribed Video Channel."
    else:
        message = f"{current_time()} ERROR: '{url}' is an invalid link format. Video Channel has not been added."
    
    return valid, message

# Playlists webpage and actions
@app.route('/playlists', defaults={'sub_page': 'plm_main'}, methods=['GET', 'POST'])
@app.route('/playlists/<sub_page>', methods=['GET', 'POST'])
def webpage_playlists(sub_page):
    global filter_title_assigned
    global filter_m3u_name_assigned
    global filter_description_assigned
    global filter_parent_assigned
    global filter_stream_format_override_assigned
    global filter_station_status_assigned
    global filter_title_unassigned
    global filter_m3u_name_unassigned
    global filter_description_unassigned
    global filter_parent_unassigned
    global filter_stream_format_override_unassigned
    global filter_station_status_unassigned
    global filter_parent_title
    global filter_parent_tvg_id_override
    global filter_parent_tvg_logo_override
    global filter_parent_channel_number_override
    global filter_parent_tvc_guide_stationid_override
    global filter_parent_preferred_playlist
    global parent_channel_id_prior
    global plm_streaming_stations
    global plm_check_child_station_status_global

    templates = {
        'plm_main': 'main/playlists_main.html',
        'plm_modify_unassigned_stations': 'main/playlists_modify_unassigned_stations.html',
        'plm_modify_assigned_stations': 'main/playlists_modify_assigned_stations.html',
        'plm_parent_stations': 'main/playlists_parent_stations.html',
        'plm_manage': 'main/playlists_manage.html'
    }

    template = templates.get(sub_page, 'main/playlists_main.html')

    settings = read_data(csv_settings)
    station_start_number = settings[11]['settings']
    max_stations = settings[12]['settings']
    plm_url_tag_in_m3us = settings[42]['settings']                              # [42] PLM: URL Tag in m3u(s) On/Off
    plm_check_child_station_status = settings[59]['settings']                   # [59] PLM/MTM: Check Child Station Status On/Off
    plm_internal_pbs_stations = settings[48]['settings']                        # [48] PLM: Internal PBS Stations On/Off
    plm_internal_pbs_url_base = settings[49]['settings']                        # [49] PLM: VLC Bridge PBS Base URL
    settings_message = ''

    playlists_anchor_id = None
    run_empty_row = None

    playlists = read_data(csv_playlistmanager_playlists)
    parents = read_data(csv_playlistmanager_parents)
    child_to_parents = read_data(csv_playlistmanager_child_to_parent)
    station_mappings = read_data(csv_playlistmanager_station_mappings)

    action_to_anchor = {
        'playlists': 'playlists_anchor',
        'priority_playlists': 'priority_playlists_anchor',
        'parents': 'parents_anchor',
        'unassigned_child_to_parents': 'unassigned_child_to_parents_anchor',
        'assigned_child_to_parents': 'assigned_child_to_parents_anchor',
        'final_playlists': 'final_playlists_anchor',
        'playlist_file_add_to': 'final_playlists_anchor',
        'uploaded_playlists': 'uploaded_playlists_anchor',
        'generated_playlists': 'uploaded_playlists_anchor',
        'internal_playlists': 'internal_playlists_anchor',
        'child_station_mapping': 'child_station_mappings_anchor',
        'priority_child_station_mapping': 'priority_child_station_mappings_anchor'
    }

    preferred_playlists = []
    preferred_playlists_default = [
        {'m3u_id': 'None', 'prefer_name': 'None'},
        {'m3u_id': 'Delete', 'prefer_name': 'Delete'}
    ]
    preferred_playlists = get_preferred_playlists(preferred_playlists_default)

    child_to_parent_mappings = []
    child_to_parent_mappings_default_base_01 = [
        { 'parent_channel_id': 'Unassigned', 'parent_title': 'Unassigned' }
    ]
    child_to_parent_mappings_default_base_02 = [
        { 'parent_channel_id': 'Ignore', 'parent_title': 'Ignore' },
        { 'parent_channel_id': 'Make Parent', 'parent_title': 'Make Parent' }
    ]
    child_to_parent_mappings_default = child_to_parent_mappings_default_base_01 + child_to_parent_mappings_default_base_02
    child_to_parent_mappings = get_child_to_parent_mappings(child_to_parent_mappings_default)

    unassigned_child_to_parents = []
    assigned_child_to_parents = []
    all_child_to_parents_stats = {}
    unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count = get_child_to_parents(sub_page)

    playlist_files = []
    playlist_files = get_playlist_files()
    uploaded_playlist_files = []
    uploaded_playlist_files = get_uploaded_playlist_files()
    uploaded_playlists_message = ''
    current_path = request.path.rstrip('/')
    
    stream_formats_overrides = ["None"]
    for stream_format in stream_formats:
        stream_formats_overrides.append(stream_format)

    station_mapping_source_m3u_ids, station_mapping_source_fields, station_mapping_target_fields, station_mapping_target_parent_channel_ids = get_station_mapping_data(playlists, child_to_parent_mappings_default_base_02)

    if request.method == 'POST':
        playlists_action = request.form['action']

        for prefix, anchor_id in action_to_anchor.items():
            if playlists_action.startswith(prefix):
                playlists_anchor_id = anchor_id
                break

        posts = ['_cancel', '_save', 'save_all', '_new']
        inposts = ['_delete_', '_update_','_make_parent_', '_set_parent_', '_examine_', '_add_to_', '_more_']
        if playlists_action.endswith('_settings'):

            if playlists_action in ['playlist_manager_save_settings', 'internal_playlists_save_settings']:

                if playlists_action == 'playlist_manager_save_settings':
                    station_start_number_input = request.form.get('station_start_number')
                    max_stations_input = request.form.get('max_stations')
                    plm_url_tag_in_m3us_input = request.form.get('plm_url_tag_in_m3us')
                    plm_check_child_station_status_input = request.form.get('plm_check_child_station_status')

                    try:
                        if int(station_start_number_input) > 0 and int(max_stations_input) > 0:
                            
                            settings[11]['settings'] = int(station_start_number_input)
                            settings[12]['settings'] = int(max_stations_input)
                            settings[42]['settings'] = "On" if plm_url_tag_in_m3us_input == 'on' else "Off"
                            settings[59]['settings'] = "On" if plm_check_child_station_status_input == 'on' else "Off"
                            plm_check_child_station_status_global = True if settings[59]['settings'] == "On" else None
                            if settings[42]['settings'] == "On":
                                settings[43]['settings'] = f"{request.url_root}"

                        else:
                            settings_message = f"{current_time()} ERROR: 'Station Start Number' and 'Max Stations per m3u' must be positive integers."
                    except ValueError:
                        settings_message = f"{current_time()} ERROR: 'Station Start Number' and 'Max Stations per m3u' must be numbers."

                elif playlists_action == 'internal_playlists_save_settings':
                    plm_streaming_stations_input = request.form.get('plm_streaming_stations')
                    plm_internal_pbs_stations_input = request.form.get('plm_internal_pbs_stations')
                    plm_internal_pbs_url_base_input = request.form.get('plm_internal_pbs_url_base')
                    if plm_internal_pbs_url_base_input == '' or plm_internal_pbs_url_base_input is None:
                        plm_internal_pbs_url_base_input = 'http://[address_required]:[port_required]'

                    # Streaming Stations
                    settings[39]["settings"] = "On" if plm_streaming_stations_input == 'on' else "Off"
                    if plm_streaming_stations_input == 'on':
                        plm_streaming_stations = True
                        check_and_create_csv(csv_playlistmanager_streaming_stations)
                    else:
                        plm_streaming_stations = None

                    # PBS Stations
                    settings[48]['settings'] = "On" if plm_internal_pbs_stations_input == 'on' else "Off"
                    settings[49]['settings'] = plm_internal_pbs_url_base_input

                write_data(csv_settings, settings)
                read_data(csv_settings)
                station_start_number = settings[11]['settings']
                max_stations = settings[12]['settings']
                plm_url_tag_in_m3us = settings[42]['settings']                              # [42] PLM: URL Tag in m3u(s) On/Off
                plm_check_child_station_status = settings[59]['settings']                   # [59] PLM/MTM: Check Child Station Status On/Off
                plm_internal_pbs_stations = settings[48]['settings']                        # [48] PLM: Internal PBS Stations On/Off
                plm_internal_pbs_url_base = settings[49]['settings']                        # [49] PLM: VLC Bridge PBS Base URL

                uploaded_playlist_files = get_uploaded_playlist_files()

        elif any(playlists_action.endswith(post) for post in posts) or any(inpost in playlists_action for inpost in inposts):

            filter_inposts = ['_save', '_new', '_delete_', '_set_parent_', '_examine_', '_more_']
            if any(filter_inpost in playlists_action for filter_inpost in filter_inposts):
                if sub_page is None or sub_page == 'plm_modify_unassigned_stations':
                    filter_title_unassigned = request.form.get('filter-title')
                    filter_m3u_name_unassigned = request.form.get('filter-m3u-name')
                    filter_description_unassigned = request.form.get('filter-description')
                    filter_parent_unassigned = request.form.get('filter-parent')
                    filter_stream_format_override_unassigned = request.form.get('filter-stream-format-override')
                    filter_station_status_unassigned = request.form.get('filter-station-status')

                elif sub_page == 'plm_modify_assigned_stations':
                    filter_title_assigned = request.form.get('filter-title')
                    filter_m3u_name_assigned = request.form.get('filter-m3u-name')
                    filter_description_assigned = request.form.get('filter-description')
                    filter_parent_assigned = request.form.get('filter-parent')
                    filter_stream_format_override_assigned = request.form.get('filter-stream-format-override')
                    filter_station_status_assigned = request.form.get('filter-station-status')
                
                elif sub_page == 'plm_parent_stations':
                    filter_parent_title = request.form.get('filter-parent-title')
                    filter_parent_tvg_id_override = request.form.get('filter-parent-tvg-id-override')
                    filter_parent_tvg_logo_override = request.form.get('filter-parent-tvg-logo-override')
                    filter_parent_channel_number_override = request.form.get('filter-parent-channel-number-override')
                    filter_parent_tvc_guide_stationid_override = request.form.get('filter-parent-tvc-guide-stationid-override')
                    filter_parent_preferred_playlist = request.form.get('filter-parent-preferred-playlist')
                
                elif sub_page == 'plm_manage':
                    pass

            this_posts = ['_save', '_new']
            this_inposts = ['_delete_', '_upload_', '_make_parent_', '_more_']
            if any(playlists_action.endswith(this_post) for this_post in this_posts) or any(this_inpost in playlists_action for this_inpost in this_inposts):

                if playlists_action.startswith('playlists_action_') or playlists_action.startswith('priority_playlists_action_'):

                    if playlists_action == "playlists_action_save":
                        playlists_m3u_id_inputs = {}
                        playlists_m3u_name_inputs = {}
                        playlists_m3u_url_inputs = {}
                        playlists_epg_xml_inputs = {}
                        playlists_stream_format_inputs = {}
                        playlists_m3u_active_inputs = {}
                        playlists_m3u_priority_inputs = {}
                        playlists_station_check_inputs = {}

                        for key in request.form.keys():
                            if key.startswith('playlists_m3u_id_'):
                                index = key.split('_')[-1]
                                playlists_m3u_id_inputs[index] = request.form.get(key)

                            if key.startswith('playlists_m3u_name_'):
                                index = key.split('_')[-1]
                                playlists_m3u_name_inputs[index] = request.form.get(key)

                            if key.startswith('playlists_m3u_url_'):
                                index = key.split('_')[-1]
                                playlists_m3u_url_inputs[index] = request.form.get(key)

                            if key.startswith('playlists_epg_xml_'):
                                index = key.split('_')[-1]
                                playlists_epg_xml_inputs[index] = request.form.get(key)

                            if key.startswith('playlists_stream_format_'):
                                index = key.split('_')[-1]
                                playlists_stream_format_inputs[index] = request.form.get(key)

                            if key.startswith('playlists_m3u_active_'):
                                index = key.split('_')[-1]
                                playlists_m3u_active_inputs[index] = request.form.get(key)

                            if key.startswith('playlists_m3u_priority_'):
                                index = key.split('_')[-1]
                                playlists_m3u_priority_inputs[index] = request.form.get(key)

                            if key.startswith('playlists_station_check_'):
                                index = key.split('_')[-1]
                                playlists_station_check_inputs[index] = request.form.get(key)

                        for row in playlists_m3u_id_inputs:
                            playlists_m3u_id_input =  playlists_m3u_id_inputs.get(row)
                            playlists_m3u_name_input = playlists_m3u_name_inputs.get(row)
                            playlists_m3u_url_input = playlists_m3u_url_inputs.get(row)
                            playlists_epg_xml_input = playlists_epg_xml_inputs.get(row)
                            playlists_stream_format_input = playlists_stream_format_inputs.get(row)
                            playlists_m3u_active_input = "On" if playlists_m3u_active_inputs.get(row) == 'on' else "Off"
                            playlists_m3u_priority_input = playlists_m3u_priority_inputs.get(row)
                            playlists_station_check_input = "On" if playlists_station_check_inputs.get(row) == 'on' else "Off"

                            for idx, playlist in enumerate(playlists):
                                if idx == int(row) - 1:
                                    playlist['m3u_id'] = playlists_m3u_id_input
                                    playlist['m3u_name'] = playlists_m3u_name_input
                                    playlist['m3u_url'] = playlists_m3u_url_input
                                    playlist['epg_xml'] = playlists_epg_xml_input
                                    playlist['stream_format'] = playlists_stream_format_input
                                    playlist['m3u_active'] = playlists_m3u_active_input
                                    playlist['m3u_priority'] = playlists_m3u_priority_input
                                    playlist['station_check'] = playlists_station_check_input

                    elif playlists_action == "playlists_action_new":
                        playlists_m3u_id_input = f"m3u_{max((int(playlist['m3u_id'].split('_')[1]) for playlist in playlists), default=0) + 1:04d}"
                        playlists_m3u_name_input = request.form.get('playlists_m3u_name_new')
                        playlists_m3u_url_input = request.form.get('playlists_m3u_url_new')
                        playlists_epg_xml_input = request.form.get('playlists_epg_xml_new')
                        playlists_stream_format_input = request.form.get('playlists_stream_format_new')
                        playlists_m3u_active_input = "On" if request.form.get('playlists_m3u_active_new') == 'on' else "Off"
                        playlists_m3u_priority_input = max((int(playlist['m3u_priority']) for playlist in playlists), default=0) + 1
                        playlists_station_check_input = "On" if request.form.get('playlists_station_check_new') == 'on' else "Off"

                        playlists.append({
                            "m3u_id": playlists_m3u_id_input,
                            "m3u_name": playlists_m3u_name_input,
                            "m3u_url": playlists_m3u_url_input,
                            "epg_xml": playlists_epg_xml_input,
                            "stream_format": playlists_stream_format_input,
                            "m3u_active": playlists_m3u_active_input,
                            "m3u_priority": playlists_m3u_priority_input,
                            "station_check": playlists_station_check_input
                        })

                    elif playlists_action.startswith('playlists_action_delete_'):
                        playlists_action_delete_index = int(playlists_action.split('_')[-1]) - 1

                        # Create a temporary record with fields set to None
                        temp_record = create_temp_record(playlists[0].keys())

                        if 0 <= playlists_action_delete_index < len(playlists):
                            combined_children = read_data(csv_playlistmanager_combined_m3us)
                            for combined_child in combined_children:
                                if combined_child['m3u_id'] == playlists[playlists_action_delete_index]['m3u_id']:
                                    remove_row_csv(csv_playlistmanager_combined_m3us, combined_child['station_playlist'])

                            write_station_mappings = False
                            for station_mapping in station_mappings:
                                if station_mapping['source_m3u_id'] == playlists[playlists_action_delete_index]['m3u_id']:
                                    station_mapping['source_m3u_id'] = 'remove_warning'
                                    station_mapping['station_mapping_active'] = 'Off'
                                    write_station_mappings = True

                            if write_station_mappings:
                                write_data(csv_playlistmanager_station_mappings, station_mappings)

                            playlists.pop(playlists_action_delete_index)

                            # If the list is now empty, add the temp record to keep headers
                            if not playlists:
                                playlists.append(temp_record)
                                run_empty_row = True

                        if len (playlists) > 1:
                            for index, playlist in enumerate(sorted(playlists, key=lambda x: int(x['m3u_priority'])), start=1):
                                playlist['m3u_priority'] = str(index)
                        else:
                            if playlists[0]['m3u_id'] is None or playlists[0]['m3u_id'] == '':
                                pass
                            else:
                                playlists[0]['m3u_priority'] = 1

                    elif playlists_action == "priority_playlists_action_save":
                        priority_playlists_input = request.form.get('priority_playlists')
                        priority_playlists_input_json = json.loads(priority_playlists_input)
                        playlists = priority_playlists_input_json

                    if len(playlists) > 1:
                        playlists = sorted(playlists, key=lambda x: sort_key(x["m3u_name"].casefold()))

                    csv_to_write = csv_playlistmanager_playlists
                    data_to_write = playlists

                elif playlists_action.startswith('uploaded_playlists_'):

                    if playlists_action.startswith('uploaded_playlists_action_delete_'):
                        uploaded_playlists_action_delete_index = int(playlists_action.split('_')[-1]) - 1
                        uploaded_playlists_action_delete_filename = uploaded_playlist_files[uploaded_playlists_action_delete_index]['file_link']
                        uploaded_playlists_action_delete_filename_combined = os.path.join(playlists_uploads_dir_name, uploaded_playlists_action_delete_filename)

                        last_period_index = uploaded_playlists_action_delete_filename_combined.rfind('.')

                        if last_period_index != -1:
                            before_last_period = uploaded_playlists_action_delete_filename_combined[:last_period_index]
                            after_last_period = uploaded_playlists_action_delete_filename_combined[last_period_index + 1:]
                        else:
                            before_last_period = uploaded_playlists_action_delete_filename_combined
                            after_last_period = ''

                        file_delete(program_files_dir, before_last_period, after_last_period)

                    elif playlists_action == "uploaded_playlists_action_new":
                        file = None
                        filename = None
                        uploaded_playlists_message = ''
                        temp_upload = os.path.join(playlists_uploads_dir_name, "temp_upload.txt")
                        upload_extensions = [
                            "m3u",
                            "xml",
                            "gz",
                            "m3u8"
                        ]

                        file = request.files.get('uploaded_playlists_action_new_file')
                        
                        if file:
                            filename = file.filename

                            last_period_index = filename.rfind('.')

                            if last_period_index != -1:
                                before_last_period = filename[:last_period_index]
                                after_last_period = filename[last_period_index + 1:]
                            else:
                                before_last_period = filename
                                after_last_period = ''

                            if after_last_period in upload_extensions:
                                final_filename = filename.replace(' ', '_')
                                final_upload = os.path.join(playlists_uploads_dir_name, final_filename)
                                file.save(full_path(temp_upload))
                                os.replace(full_path(temp_upload), full_path(final_upload))
                            
                            else:
                                uploaded_playlists_message = "Incorrect format. Files must be 'm3u', 'm3u8', 'xml', or 'gz'."    

                        else:
                            uploaded_playlists_message = "No selected file"

                    uploaded_playlist_files = get_uploaded_playlist_files()
                    csv_to_write = None
                    data_to_write = None

                elif playlists_action.startswith('parents_action_') or '_make_parent_' in playlists_action:

                    if playlists_action == "parents_action_save" or playlists_action.startswith('parents_action_delete_') or playlists_action.startswith('parents_action_more_'):

                        parents_delete_on_save_flag = None

                        parents_parent_channel_id_inputs = {}
                        parents_parent_active_inputs = {}
                        parents_parent_title_inputs = {}
                        parents_parent_tvg_id_override_inputs = {}
                        parents_parent_tvg_logo_override_inputs = {}
                        parents_parent_channel_number_override_inputs = {}
                        parents_parent_tvc_guide_stationid_override_inputs = {}
                        parents_parent_preferred_playlist_inputs = {}

                        for key in request.form.keys():
                            if key.startswith('parents_parent_channel_id_'):
                                index = key.split('_')[-1]
                                parents_parent_channel_id_inputs[index] = request.form.get(key)

                            if key.startswith('parents_parent_active_'):
                                index = key.split('_')[-1]
                                parents_parent_active_inputs[index] =  "On" if request.form.get(key) == 'on' else "Off"

                            if key.startswith('parents_parent_title_'):
                                index = key.split('_')[-1]
                                parents_parent_title_inputs[index] = request.form.get(key)

                            if key.startswith('parents_parent_tvg_id_override_'):
                                index = key.split('_')[-1]
                                parents_parent_tvg_id_override_inputs[index] = request.form.get(key)

                            if key.startswith('parents_parent_tvg_logo_override_'):
                                index = key.split('_')[-1]
                                parents_parent_tvg_logo_override_inputs[index] = request.form.get(key)

                            if key.startswith('parents_parent_channel_number_override_'):
                                index = key.split('_')[-1]
                                parents_parent_channel_number_override_inputs[index] = request.form.get(key)

                            if key.startswith('parents_parent_tvc_guide_stationid_override_'):
                                index = key.split('_')[-1]
                                parents_parent_tvc_guide_stationid_override_inputs[index] = request.form.get(key)

                            if key.startswith('parents_parent_preferred_playlist_'):
                                index = key.split('_')[-1]
                                parents_parent_preferred_playlist_inputs[index] = request.form.get(key)

                        if playlists_action == "parents_action_save" or playlists_action.startswith('parents_action_more_'):
                            temp_parents = []

                            for row in parents_parent_channel_id_inputs:
                                parents_parent_channel_id_input =  parents_parent_channel_id_inputs.get(row)
                                parents_parent_active_input = parents_parent_active_inputs.get(row)
                                parents_parent_title_input = parents_parent_title_inputs.get(row)
                                parents_parent_tvg_id_override_input = parents_parent_tvg_id_override_inputs.get(row)
                                parents_parent_tvg_logo_override_input = parents_parent_tvg_logo_override_inputs.get(row)
                                parents_parent_channel_number_override_input = parents_parent_channel_number_override_inputs.get(row)
                                parents_parent_tvc_guide_stationid_override_input = parents_parent_tvc_guide_stationid_override_inputs.get(row)
                                parents_parent_preferred_playlist_input = parents_parent_preferred_playlist_inputs.get(row)
                                if parents_parent_preferred_playlist_input == "None":
                                    parents_parent_preferred_playlist_input = None
                                elif parents_parent_preferred_playlist_input == "Delete":
                                    parents_delete_on_save_flag = True

                                temp_parents.append({
                                    'parent_channel_id': parents_parent_channel_id_input,
                                    'parent_active': parents_parent_active_input,
                                    'parent_title': parents_parent_title_input,
                                    'parent_tvg_id_override': parents_parent_tvg_id_override_input,
                                    'parent_tvg_logo_override': parents_parent_tvg_logo_override_input,
                                    'parent_channel_number_override': parents_parent_channel_number_override_input,
                                    'parent_tvc_guide_stationid_override': parents_parent_tvc_guide_stationid_override_input,
                                    'parent_preferred_playlist': parents_parent_preferred_playlist_input
                                })

                            if playlists_action.startswith('parents_action_more_'):
                                parents_action_more_index = int(playlists_action.split('_')[-1]) - 1
                                parent_channel_id_prior = temp_parents[parents_action_more_index]['parent_channel_id']
                                return redirect('/playlists/plm_parent_stations_more')

                            elif playlists_action == "parents_action_save":

                                for parent in parents:
                                    for temp_parent in temp_parents:
                                        if parent['parent_channel_id'] == temp_parent['parent_channel_id']:
                                            parent['parent_active'] = temp_parent['parent_active']
                                            parent['parent_title'] = temp_parent['parent_title']
                                            parent['parent_tvg_id_override'] = temp_parent['parent_tvg_id_override']
                                            parent['parent_tvg_logo_override'] = temp_parent['parent_tvg_logo_override']
                                            parent['parent_channel_number_override'] = temp_parent['parent_channel_number_override']
                                            parent['parent_tvc_guide_stationid_override'] = temp_parent['parent_tvc_guide_stationid_override']
                                            parent['parent_preferred_playlist'] = temp_parent['parent_preferred_playlist']

                        if playlists_action.startswith('parents_action_delete_') or parents_delete_on_save_flag:
                            
                            parents_delete_list = []
                            
                            if playlists_action.startswith('parents_action_delete_'):
                                parents_action_delete_index = int(playlists_action.split('_')[-1])
                                parents_delete_list.append(parents_parent_channel_id_inputs[str(parents_action_delete_index)])
                            elif parents_delete_on_save_flag:
                                for parent in parents:
                                    if parent['parent_preferred_playlist'] == "Delete":
                                        parents_delete_list.append(parent['parent_channel_id'])

                            for delete_parent_channel_id in parents_delete_list:

                                # Create a temporary record with fields set to None
                                temp_record = create_temp_record(parents[0].keys())

                                # Remove the record
                                for parent in parents:
                                    if parent['parent_channel_id'] == delete_parent_channel_id:
                                        parents.remove(parent)
                                        break
                                
                                # If the list is now empty, add the temp record to keep headers
                                if not parents:
                                    parents.append(temp_record)
                                    run_empty_row = True

                                # Unassign children with that parent
                                child_to_parents = read_data(csv_playlistmanager_child_to_parent)
                                unassign_children = []
                                
                                for child_to_parent in child_to_parents:
                                    if child_to_parent['parent_channel_id'] == delete_parent_channel_id:
                                        unassign_children.append(child_to_parent)

                                if unassign_children:
                                    for unassign_child in unassign_children:
                                        set_child_to_parent(unassign_child['child_m3u_id_channel_id'], "Unassigned", unassign_child['stream_format_override'], parents, unassign_child['enable_child_station_check'])

                                # Unassign station mappings with that parent
                                write_station_mappings = False
                                for station_mapping in station_mappings:
                                    if station_mapping['target_parent_channel_id'] == delete_parent_channel_id:
                                        station_mapping['target_parent_channel_id'] = 'remove_warning'
                                        station_mapping['station_mapping_active'] = 'Off'
                                        write_station_mappings = True

                                if write_station_mappings:
                                    write_data(csv_playlistmanager_station_mappings, station_mappings)

                            unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count = get_child_to_parents(sub_page)

                    elif playlists_action == "parents_action_new" or '_make_parent_' in playlists_action:
                        
                        parents_parent_channel_id_input = f"plm_{max((int(parent['parent_channel_id'].split('_')[1]) for parent in parents), default=0) + 1:04d}"

                        # Placeholder values for extended functionality
                        parents_parent_tvc_guide_art_override_input = None
                        parents_parent_tvc_guide_tags_override_input = None
                        parents_parent_tvc_guide_genres_override_input = None
                        parents_parent_tvc_guide_categories_override_input = None
                        parents_parent_tvc_guide_placeholders_override_input = None
                        parents_parent_tvc_stream_vcodec_override_input = None
                        parents_parent_tvc_stream_acodec_override_input = None
                        parents_parent_tvg_description_override_input = None
                        parents_parent_group_title_override_input = None

                        if playlists_action == "parents_action_new":
                            parents_parent_active_input = "On" if request.form.get('parents_parent_active_new') == 'on' else "Off"
                            parents_parent_title_input = request.form.get('parents_parent_title_new')
                            parents_parent_tvg_id_override_input = request.form.get('parents_parent_tvg_id_override_new')
                            parents_parent_tvg_logo_override_input = request.form.get('parents_parent_tvg_logo_override_new')
                            parents_parent_channel_number_override_input = request.form.get('parents_parent_channel_number_override_new')
                            parents_parent_tvc_guide_stationid_override_input = request.form.get('parents_parent_tvc_guide_stationid_override_new')
                            parents_parent_preferred_playlist_input = request.form.get('parents_parent_preferred_playlist_new')
                            if parents_parent_preferred_playlist_input == "None":
                                parents_parent_preferred_playlist_input = None
                            elif parents_parent_preferred_playlist_input == "Delete":
                                parents_parent_preferred_playlist_input = None

                        elif '_make_parent_' in playlists_action:
                            child_to_parents_action_make_parent_index = int(playlists_action.split('_')[-1]) - 1

                            if playlists_action.startswith("unassigned"):
                                keycheck_prefix = "unassigned"
                            elif playlists_action.startswith("assigned"):
                                keycheck_prefix = "assigned"

                            # Add to Parents table
                            child_to_parents_title_inputs = {}

                            keycheck_base = "_child_to_parents_title_"
                            keycheck = f"{keycheck_prefix}{keycheck_base}"
                            for key in request.form.keys():
                                if key.startswith(keycheck):
                                    index = key.split('_')[-1]
                                    child_to_parents_title_inputs[index] = request.form.get(key)

                            child_to_parents_title_inputs = list(child_to_parents_title_inputs.values())

                            parents_parent_active_input = "On"
                            parents_parent_title_input = child_to_parents_title_inputs[child_to_parents_action_make_parent_index]
                            parents_parent_tvg_id_override_input = None
                            parents_parent_tvg_logo_override_input = None
                            parents_parent_channel_number_override_input = None
                            parents_parent_tvc_guide_stationid_override_input = None
                            parents_parent_preferred_playlist_input = None

                            # Modify Child to Parent table
                            child_to_parents_channel_id_inputs = {}
                            child_to_parents_stream_format_override_inputs = {}
                            child_to_parents_enable_child_station_check_inputs = {}

                            keycheck_base = "_child_to_parents_channel_id_"
                            keycheck = f"{keycheck_prefix}{keycheck_base}"
                            for key in request.form.keys():
                                if key.startswith(keycheck):
                                    index = key.split('_')[-1]
                                    child_to_parents_channel_id_inputs[index] = request.form.get(key)

                            keycheck_base = "_child_to_parents_stream_format_override_"
                            keycheck = f"{keycheck_prefix}{keycheck_base}"
                            for key in request.form.keys():
                                if key.startswith(keycheck):
                                    index = key.split('_')[-1]
                                    child_to_parents_stream_format_override_inputs[index] = request.form.get(key)

                            keycheck_base = "_child_to_parents_enable_child_station_check_"
                            keycheck = f"{keycheck_prefix}{keycheck_base}"
                            for key in request.form.keys():
                                if key.startswith(keycheck):
                                    index = key.split('_')[-1]
                                    child_to_parents_enable_child_station_check_inputs[index] = request.form.get(key)

                            child_to_parents_channel_id_inputs = list(child_to_parents_channel_id_inputs.values())
                            child_to_parents_channel_id = child_to_parents_channel_id_inputs[child_to_parents_action_make_parent_index]

                            child_to_parents_stream_format_override_inputs = list(child_to_parents_stream_format_override_inputs.values())
                            child_to_parents_stream_format_override = child_to_parents_stream_format_override_inputs[child_to_parents_action_make_parent_index]

                            child_to_parents_enable_child_station_check_inputs = list(child_to_parents_enable_child_station_check_inputs.values())
                            child_to_parents_enable_child_station_check = "On" if child_to_parents_enable_child_station_check_inputs[child_to_parents_action_make_parent_index] == "on" else "Off"

                            set_child_to_parent(child_to_parents_channel_id, parents_parent_channel_id_input, child_to_parents_stream_format_override, parents, child_to_parents_enable_child_station_check)
                            unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count = get_child_to_parents(sub_page)

                        parents.append({
                            "parent_channel_id": parents_parent_channel_id_input,
                            "parent_title": parents_parent_title_input,
                            "parent_tvg_id_override": parents_parent_tvg_id_override_input,
                            "parent_tvg_logo_override": parents_parent_tvg_logo_override_input,
                            "parent_channel_number_override": parents_parent_channel_number_override_input,
                            "parent_tvc_guide_stationid_override": parents_parent_tvc_guide_stationid_override_input,
                            "parent_tvc_guide_art_override": parents_parent_tvc_guide_art_override_input,
                            "parent_tvc_guide_tags_override": parents_parent_tvc_guide_tags_override_input,
                            "parent_tvc_guide_genres_override": parents_parent_tvc_guide_genres_override_input,
                            "parent_tvc_guide_categories_override": parents_parent_tvc_guide_categories_override_input,
                            "parent_tvc_guide_placeholders_override": parents_parent_tvc_guide_placeholders_override_input,
                            "parent_tvc_stream_vcodec_override": parents_parent_tvc_stream_vcodec_override_input,
                            "parent_tvc_stream_acodec_override": parents_parent_tvc_stream_acodec_override_input,
                            "parent_preferred_playlist": parents_parent_preferred_playlist_input,
                            "parent_active": parents_parent_active_input,
                            "parent_tvg_description_override": parents_parent_tvg_description_override_input,
                            "parent_group_title_override": parents_parent_group_title_override_input
                        })

                    if len(parents) > 1:
                        parents = sorted(parents, key=lambda x: sort_key(x["parent_title"].casefold()))

                    csv_to_write = csv_playlistmanager_parents
                    data_to_write = parents

                elif playlists_action.startswith('child_station_mapping_') or playlists_action.startswith('priority_child_station_mapping_'):

                    if playlists_action == "child_station_mapping_save":
                        child_station_mapping_station_mapping_id_inputs = {}
                        child_station_mapping_station_mapping_name_inputs = {}
                        child_station_mapping_station_mapping_active_inputs = {}
                        child_station_mapping_station_mapping_priority_inputs = {}
                        child_station_mapping_source_m3u_id_inputs = {}
                        child_station_mapping_source_field_selected_inputs = {}
                        child_station_mapping_source_field_compare_id_inputs = {}
                        child_station_mapping_source_field_string_inputs = {}
                        child_station_mapping_target_field_selected_inputs = {}
                        child_station_mapping_target_field_compare_replace_id_inputs = {}
                        child_station_mapping_target_field_string_inputs = {}
                        child_station_mapping_target_parent_channel_id_inputs = {}
                        child_station_mapping_target_stream_format_override_inputs = {}

                        for key in request.form.keys():
                            if key.startswith('child_station_mapping_station_mapping_id_'):
                                index = key.split('_')[-1]
                                child_station_mapping_station_mapping_id_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_station_mapping_name_'):
                                index = key.split('_')[-1]
                                child_station_mapping_station_mapping_name_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_station_mapping_active_'):
                                index = key.split('_')[-1]
                                child_station_mapping_station_mapping_active_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_station_mapping_priority_'):
                                index = key.split('_')[-1]
                                child_station_mapping_station_mapping_priority_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_source_m3u_id_'):
                                index = key.split('_')[-1]
                                child_station_mapping_source_m3u_id_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_source_field_selected_'):
                                index = key.split('_')[-1]
                                child_station_mapping_source_field_selected_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_source_field_compare_id_'):
                                index = key.split('_')[-1]
                                child_station_mapping_source_field_compare_id_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_source_field_string_'):
                                index = key.split('_')[-1]
                                child_station_mapping_source_field_string_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_target_field_selected_'):
                                index = key.split('_')[-1]
                                child_station_mapping_target_field_selected_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_target_field_compare_replace_id_'):
                                index = key.split('_')[-1]
                                child_station_mapping_target_field_compare_replace_id_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_target_field_string_'):
                                index = key.split('_')[-1]
                                child_station_mapping_target_field_string_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_target_parent_channel_id_'):
                                index = key.split('_')[-1]
                                child_station_mapping_target_parent_channel_id_inputs[index] = request.form.get(key)

                            if key.startswith('child_station_mapping_target_stream_format_override_'):
                                index = key.split('_')[-1]
                                child_station_mapping_target_stream_format_override_inputs[index] = request.form.get(key)

                        for row in child_station_mapping_station_mapping_id_inputs:
                            child_station_mapping_station_mapping_id_input =  child_station_mapping_station_mapping_id_inputs.get(row)
                            child_station_mapping_station_mapping_name_input = child_station_mapping_station_mapping_name_inputs.get(row)
                            child_station_mapping_station_mapping_active_input = "On" if child_station_mapping_station_mapping_active_inputs.get(row) == 'on' else "Off"
                            child_station_mapping_station_mapping_priority_input = child_station_mapping_station_mapping_priority_inputs.get(row)
                            child_station_mapping_source_m3u_id_input = child_station_mapping_source_m3u_id_inputs.get(row)
                            child_station_mapping_source_field_selected_input = child_station_mapping_source_field_selected_inputs.get(row)
                            child_station_mapping_source_field_compare_id_input = child_station_mapping_source_field_compare_id_inputs.get(row)
                            child_station_mapping_source_field_string_input = child_station_mapping_source_field_string_inputs.get(row)
                            child_station_mapping_target_field_selected_input = child_station_mapping_target_field_selected_inputs.get(row)
                            child_station_mapping_target_field_compare_replace_id_input = child_station_mapping_target_field_compare_replace_id_inputs.get(row)
                            child_station_mapping_target_field_string_input = child_station_mapping_target_field_string_inputs.get(row)
                            child_station_mapping_target_parent_channel_id_input = child_station_mapping_target_parent_channel_id_inputs.get(row)
                            child_station_mapping_target_stream_format_override_input = child_station_mapping_target_stream_format_override_inputs.get(row)
                            
                            for idx, station_mapping in enumerate(station_mappings):
                                if idx == int(row) - 1:
                                    station_mapping['station_mapping_id'] = child_station_mapping_station_mapping_id_input
                                    station_mapping['station_mapping_name'] = child_station_mapping_station_mapping_name_input
                                    station_mapping['station_mapping_active'] = child_station_mapping_station_mapping_active_input
                                    station_mapping['station_mapping_priority'] = child_station_mapping_station_mapping_priority_input
                                    station_mapping['source_m3u_id'] = child_station_mapping_source_m3u_id_input
                                    station_mapping['source_field'] = child_station_mapping_source_field_selected_input
                                    station_mapping['source_field_compare_id'] = child_station_mapping_source_field_compare_id_input
                                    station_mapping['source_field_string'] = child_station_mapping_source_field_string_input
                                    station_mapping['target_field'] = child_station_mapping_target_field_selected_input
                                    station_mapping['target_field_compare_replace_id'] = child_station_mapping_target_field_compare_replace_id_input
                                    station_mapping['target_field_string'] = child_station_mapping_target_field_string_input
                                    station_mapping['target_parent_channel_id'] = child_station_mapping_target_parent_channel_id_input
                                    station_mapping['target_stream_format_override'] = child_station_mapping_target_stream_format_override_input
                                    
                    elif playlists_action == "child_station_mapping_new":
                        child_station_mapping_station_mapping_id_input = f"plmmap_{max((int(station_mapping['station_mapping_id'].split('_')[1]) for station_mapping in station_mappings), default=0) + 1:04d}"
                        child_station_mapping_station_mapping_name_input = request.form.get('child_station_mapping_station_mapping_name_new')
                        child_station_mapping_station_mapping_active_input = "On" if request.form.get('child_station_mapping_station_mapping_active_new') == 'on' else "Off"
                        child_station_mapping_station_mapping_priority_input = max((int(station_mapping['station_mapping_priority']) for station_mapping in station_mappings), default=0) + 1
                        child_station_mapping_source_m3u_id_input = request.form.get('child_station_mapping_source_m3u_id_new')
                        child_station_mapping_source_field_selected_input = request.form.get('child_station_mapping_source_field_selected_new')
                        child_station_mapping_source_field_compare_id_input = request.form.get('child_station_mapping_source_field_compare_id_new')
                        child_station_mapping_source_field_string_input = request.form.get('child_station_mapping_source_field_string_new')
                        child_station_mapping_target_field_selected_input = request.form.get('child_station_mapping_target_field_selected_new')
                        child_station_mapping_target_field_compare_replace_id_input = request.form.get('child_station_mapping_target_field_compare_replace_id_new')
                        child_station_mapping_target_field_string_input = request.form.get('child_station_mapping_target_field_string_new')
                        child_station_mapping_target_parent_channel_id_input = request.form.get('child_station_mapping_target_parent_channel_id_new')
                        child_station_mapping_target_stream_format_override_input = request.form.get('child_station_mapping_target_stream_format_override_new')
                        
                        station_mappings.append({
                            "station_mapping_id": child_station_mapping_station_mapping_id_input,
                            "station_mapping_name": child_station_mapping_station_mapping_name_input,
                            "station_mapping_active": child_station_mapping_station_mapping_active_input,
                            "station_mapping_priority": child_station_mapping_station_mapping_priority_input,
                            "source_m3u_id": child_station_mapping_source_m3u_id_input,
                            "source_field": child_station_mapping_source_field_selected_input,
                            "source_field_compare_id": child_station_mapping_source_field_compare_id_input,
                            "source_field_string": child_station_mapping_source_field_string_input,
                            "target_field": child_station_mapping_target_field_selected_input,
                            "target_field_compare_replace_id": child_station_mapping_target_field_compare_replace_id_input,
                            "target_field_string": child_station_mapping_target_field_string_input,
                            "target_parent_channel_id": child_station_mapping_target_parent_channel_id_input,
                            "target_stream_format_override": child_station_mapping_target_stream_format_override_input
                        })

                    elif playlists_action.startswith('child_station_mapping_delete_'):
                        child_station_mapping_delete_index = int(playlists_action.split('_')[-1]) - 1

                        # Create a temporary record with fields set to None
                        temp_record = create_temp_record(station_mappings[0].keys())

                        if 0 <= child_station_mapping_delete_index < len(station_mappings):
                            station_mappings.pop(child_station_mapping_delete_index)

                            # If the list is now empty, add the temp record to keep headers
                            if not station_mappings:
                                station_mappings.append(temp_record)
                                run_empty_row = True

                        if len (station_mappings) > 1:
                            for index, station_mapping in enumerate(sorted(station_mappings, key=lambda x: int(x['station_mapping_priority'])), start=1):
                                station_mapping['station_mapping_priority'] = str(index)
                        else:
                            if station_mappings[0]['station_mapping_id'] is None or station_mappings[0]['station_mapping_id'] == '':
                                pass
                            else:
                                station_mappings[0]['station_mapping_priority'] = 1

                    elif playlists_action == "priority_child_station_mapping_save":
                        priority_child_station_mappings_input = request.form.get('priority_child_station_mappings')
                        priority_child_station_mappings_input_json = json.loads(priority_child_station_mappings_input)
                        station_mappings = priority_child_station_mappings_input_json

                    if len(station_mappings) > 1:
                        station_mappings = sorted(station_mappings, key=lambda x: sort_key(x["station_mapping_name"].casefold()))

                    csv_to_write = csv_playlistmanager_station_mappings
                    data_to_write = station_mappings

                if csv_to_write:

                    write_data(csv_to_write, data_to_write)

                    if run_empty_row:
                        remove_empty_row(csv_to_write)

                        if csv_to_write == csv_playlistmanager_playlists:
                            delete_all_rows_except_header(csv_playlistmanager_child_to_parent)
                            delete_all_rows_except_header(csv_playlistmanager_combined_m3us)

                    if csv_to_write in [csv_playlistmanager_playlists, csv_playlistmanager_parents, csv_playlistmanager_station_mappings]:
                        station_mappings = read_data(csv_playlistmanager_station_mappings)
                        station_mapping_source_m3u_ids, station_mapping_source_fields, station_mapping_target_fields, station_mapping_target_parent_channel_ids = get_station_mapping_data(playlists, child_to_parent_mappings_default_base_02)

                    if csv_to_write == csv_playlistmanager_playlists:
                        playlists = read_data(csv_playlistmanager_playlists)
                        preferred_playlists = get_preferred_playlists(preferred_playlists_default)                           
                    elif csv_to_write == csv_playlistmanager_parents:
                        parents = read_data(csv_playlistmanager_parents)
                        child_to_parent_mappings = get_child_to_parent_mappings(child_to_parent_mappings_default)

            elif playlists_action.endswith('_save_all') or '_set_parent_' in playlists_action or '_examine_' in playlists_action:

                if '_child_to_parents_action_' in playlists_action:

                    send_child_to_parents = []

                    if playlists_action.startswith("unassigned"):
                        keycheck_prefix = "unassigned"
                    elif playlists_action.startswith("assigned"):
                        keycheck_prefix = "assigned"

                    keycheck_base = "_child_to_parents_"
                    keycheck_start = f"{keycheck_prefix}{keycheck_base}"

                    child_to_parents_channel_id_inputs = {}
                    child_to_parents_parent_channel_id_inputs = {}
                    child_to_parents_stream_format_override_inputs = {}
                    child_to_parents_enable_child_station_check_inputs = {}

                    for key in request.form.keys():
                        
                        if not key.endswith('all'):

                            keycheck = f"{keycheck_start}channel_id_"
                            if key.startswith(keycheck):
                                index = key.split('_')[-1]
                                child_to_parents_channel_id_inputs[index] = request.form.get(key)

                            keycheck = f"{keycheck_start}parent_channel_id_"
                            if key.startswith(keycheck):
                                index = key.split('_')[-1]
                                if playlists_action.endswith('_set_parent_all'):
                                    all_key = f"{keycheck}all"
                                    child_to_parents_parent_channel_id_inputs[index] = request.form.get(all_key)
                                else:
                                    child_to_parents_parent_channel_id_inputs[index] = request.form.get(key)

                            keycheck = f"{keycheck_start}stream_format_override_"
                            if key.startswith(keycheck):
                                index = key.split('_')[-1]
                                if playlists_action.endswith('_set_parent_all'):
                                    all_key = f"{keycheck}all"
                                    child_to_parents_stream_format_override_inputs[index] = request.form.get(all_key)
                                else:
                                    child_to_parents_stream_format_override_inputs[index] = request.form.get(key)

                            keycheck = f"{keycheck_start}enable_child_station_check_"
                            if key.startswith(keycheck):
                                index = key.split('_')[-1]
                                if playlists_action.endswith('_set_parent_all'):
                                    all_key = f"{keycheck}all"
                                    child_to_parents_enable_child_station_check_inputs[index] = request.form.get(all_key)
                                else:
                                    child_to_parents_enable_child_station_check_inputs[index] = request.form.get(key)

                    keycheck = f"{keycheck_start}enable_child_station_check_all"
                    if playlists_action.endswith('_set_parent_all'):
                        child_to_parents_enable_child_station_check_all = "On" if request.form.get(keycheck) == "on" else "Off"
                    else:
                        child_to_parents_enable_child_station_check_all = None

                    for index in child_to_parents_channel_id_inputs.keys():
                        child_to_parents_channel_id_input = child_to_parents_channel_id_inputs.get(index)
                        child_to_parents_stream_format_override_input = child_to_parents_stream_format_override_inputs.get(index)
                        if child_to_parents_enable_child_station_check_all:
                            child_to_parents_enable_child_station_check_input = child_to_parents_enable_child_station_check_all
                        else:
                            child_to_parents_enable_child_station_check_input = "On" if child_to_parents_enable_child_station_check_inputs.get(index) == "on" else "Off"
                        
                        if child_to_parents_parent_channel_id_inputs.get(index) == "Make Parent":
                            stations = read_data(csv_playlistmanager_combined_m3us)
                            save_all_parent_channel_id = f"plm_{max((int(parent['parent_channel_id'].split('_')[1]) for parent in parents), default=0) + 1:04d}"

                            for station in stations:
                                check_m3u_id_channel_id = f"{station['m3u_id']}_{station['channel_id']}"
                                if check_m3u_id_channel_id == child_to_parents_channel_id_input:
                                    save_all_parent_title = station['title']

                            parents.append({
                                "parent_channel_id": save_all_parent_channel_id,
                                "parent_title": save_all_parent_title,
                                "parent_tvg_id_override": None,
                                "parent_tvg_logo_override": None,
                                "parent_channel_number_override": None,
                                "parent_tvc_guide_stationid_override": None,
                                "parent_tvc_guide_art_override": None,
                                "parent_tvc_guide_tags_override": None,
                                "parent_tvc_guide_genres_override": None,
                                "parent_tvc_guide_categories_override": None,
                                "parent_tvc_guide_placeholders_override": None,
                                "parent_tvc_stream_vcodec_override": None,
                                "parent_tvc_stream_acodec_override": None,
                                "parent_preferred_playlist": None,
                                "parent_active": "On",
                                "parent_tvg_description_override": None,
                                "parent_group_title_override": None
                            })

                            child_to_parents_parent_channel_id_input = save_all_parent_channel_id

                        else:
                            child_to_parents_parent_channel_id_input = child_to_parents_parent_channel_id_inputs.get(index)

                        send_child_to_parents.append({'child_m3u_id_channel_id': child_to_parents_channel_id_input, 'parent_channel_id': child_to_parents_parent_channel_id_input, 'stream_format_override': child_to_parents_stream_format_override_input, 'enable_child_station_check': child_to_parents_enable_child_station_check_input})

                    if '_set_parent_' in playlists_action or '_examine_' in playlists_action:

                        if playlists_action.endswith('_set_parent_all'):
                            pass

                        # This is currently removed from the webpage, but leaving the backend code in case it is decided to add this function back in. Also still using for Examine.
                        else:
                            send_child_to_parents_single = []
                            child_to_parents_action_set_parent_index = int(playlists_action.split('_')[-1]) - 1

                            child_to_parents_channel_id_input_single = send_child_to_parents[child_to_parents_action_set_parent_index]['child_m3u_id_channel_id']
                            child_to_parents_parent_channel_id_input_single = send_child_to_parents[child_to_parents_action_set_parent_index]['parent_channel_id']
                            child_to_parents_stream_format_override_input_single = send_child_to_parents[child_to_parents_action_set_parent_index]['stream_format_override']
                            child_to_parents_enable_child_station_check_input_single = send_child_to_parents[child_to_parents_action_set_parent_index]['enable_child_station_check']

                            send_child_to_parents_single.append({'child_m3u_id_channel_id': child_to_parents_channel_id_input_single, 'parent_channel_id': child_to_parents_parent_channel_id_input_single, 'stream_format_override': child_to_parents_stream_format_override_input_single, 'enable_child_station_check': child_to_parents_enable_child_station_check_input_single})

                            send_child_to_parents = send_child_to_parents_single

                    if '_examine_' in playlists_action:
                        get_station_status(child_to_parents_channel_id_input_single, None)
                        return redirect('/playlists/station_status')

                    else:

                        # Write back
                        for send_child_to_parent in send_child_to_parents:
                            child_to_parents_channel_id = send_child_to_parent['child_m3u_id_channel_id']
                            child_to_parents_parent_channel_id = send_child_to_parent['parent_channel_id']
                            child_to_parents_stream_format_override = send_child_to_parent['stream_format_override']
                            child_to_parents_enable_child_station_check = send_child_to_parent['enable_child_station_check']
                            set_child_to_parent(child_to_parents_channel_id, child_to_parents_parent_channel_id, child_to_parents_stream_format_override, parents, child_to_parents_enable_child_station_check)
                        
                        parents = sorted(parents, key=lambda x: sort_key(x["parent_title"].casefold()))
                        write_data(csv_playlistmanager_parents, parents)
                        parents = read_data(csv_playlistmanager_parents)
                        child_to_parent_mappings = get_child_to_parent_mappings(child_to_parent_mappings_default)
                        unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count = get_child_to_parents(sub_page)

            elif '_update_' in playlists_action:

                if playlists_action == 'final_playlists_action_update_station_list':
                    get_combined_m3us()
                    unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count = get_child_to_parents(sub_page)

                elif playlists_action == 'final_playlists_action_update_m3u_epg':
                    get_final_m3us_epgs()
                    playlist_files = get_playlist_files()

            elif '_add_to_' in playlists_action:
                make_playlist_name = ''
                make_playlist_type = ''
                make_playlist_source = 'URL'
                make_playlist_url = ''
                make_playlist_text = ''
                make_playlist_refresh = '24'
                make_playlist_limit = ''
                make_playlist_satip = ''
                make_playlist_numbering = ''
                make_playlist_logos = ''
                make_playlist_xmltv_url = ''
                make_playlist_xmltv_refresh = '3600'

                playlists_action_add_to_index = int(playlists_action.split('_')[-1]) - 1

                if playlists_action.startswith('playlist_file_add_to_'):
                    make_playlist_url = f"{request.url_root}playlists/files/{playlist_files[playlists_action_add_to_index]['playlist_filename']}"

                elif playlists_action.startswith('generated_playlists_action_add_to_'):
                    make_playlist_url = f"{request.url_root}playlists/uploads/{uploaded_playlist_files[playlists_action_add_to_index]['file_link']}"

                if make_playlist_url:

                    make_playlist_number = None
                    if 'plm' in make_playlist_url:
                        make_playlist_number = make_playlist_url.split('_')[-1].split('.')[0]

                    if make_playlist_number:
                        if 'hls' in make_playlist_url:
                            make_playlist_type = 'HLS'
                        elif 'mpeg_ts' in make_playlist_url:
                            make_playlist_type = 'MPEG-TS'
                        elif 'strmlnk' in make_playlist_url:
                            make_playlist_type = 'STRMLNK'

                        if 'gracenote_' in make_playlist_url:
                            make_playlist_name_base = f"Gracenote"
                        elif 'epg_' in make_playlist_url:
                            make_playlist_name_base = f"Non-Gracenote"
                        elif 'plmss_' in make_playlist_url:
                            make_playlist_name_base = f"Streaming Stations"
                        elif 'int_' in make_playlist_url:
                            if 'pbs' in make_playlist_url:
                                make_playlist_name_base = f"PBS Stations"

                        make_playlist_name = f"PLM - {make_playlist_name_base} ({make_playlist_type}) [{make_playlist_number}]"

                        if 'epg_' in make_playlist_url:
                            make_playlist_xmltv_url = make_playlist_url.replace('.m3u', '.xml')

                    else:
                        file_check = uploaded_playlist_files[playlists_action_add_to_index]['file_link']
                        make_playlist_type = 'HLS'
                        make_playlist_name_base = f"Uploaded Playlist"
                        make_playlist_name = f"PLM - {make_playlist_name_base} ({make_playlist_type}) [{file_check}]"
                        
                        if file_check.endswith('.m3u'):
                            guide_check = file_check.replace('.m3u', '.xml')
                        elif file_check.endswith('.m3u8'):
                            guide_check = file_check.replace('.m3u8', '.xml')
                        
                        guide_check_path = full_path(os.path.join(playlists_uploads_dir_name, guide_check))
                        if os.path.exists(guide_check_path):
                            make_playlist_xmltv_url = f"{request.url_root}playlists/uploads/{guide_check}"

                    json_data = {
                        "name": make_playlist_name,
                        "type": make_playlist_type,
                        "source": make_playlist_source,
                        "url": make_playlist_url,
                        "text": make_playlist_text,
                        "refresh": make_playlist_refresh,
                        "limit": make_playlist_limit,
                        "satip": make_playlist_satip,
                        "numbering": make_playlist_numbering,
                        "logos": make_playlist_logos,
                        "xmltv_url": make_playlist_xmltv_url,
                        "xmltv_refresh": make_playlist_xmltv_refresh
                    }

                    make_playlist_name_clean = re.sub(r'[^a-zA-Z0-9]', '', make_playlist_name)
                    make_playlist_route = f"/providers/m3u/sources/{make_playlist_name_clean}"

                    if 'add_to_channels' in playlists_action:
                        put_channels_dvr_json(make_playlist_route, json_data)

                    elif 'add_to_plm' in playlists_action:

                        for playlist in playlists:
                            if make_playlist_url in playlist['m3u_url']:
                                uploaded_playlists_message = f"'{make_playlist_url}' is already assigned to '{playlist['m3u_name']}'."
                                break

                        if not uploaded_playlists_message:
                            playlists_m3u_id_input = f"m3u_{max((int(playlist['m3u_id'].split('_')[1]) for playlist in playlists), default=0) + 1:04d}"
                            playlists_m3u_name_input = make_playlist_name
                            playlists_m3u_url_input = make_playlist_url
                            playlists_epg_xml_input = make_playlist_xmltv_url
                            playlists_stream_format_input = make_playlist_type
                            playlists_m3u_active_input = "On"
                            playlists_m3u_priority_input = max((int(playlist['m3u_priority']) for playlist in playlists), default=0) + 1
                            playlists_station_check_input = "Off"

                            playlists.append({
                                "m3u_id": playlists_m3u_id_input,
                                "m3u_name": playlists_m3u_name_input,
                                "m3u_url": playlists_m3u_url_input,
                                "epg_xml": playlists_epg_xml_input,
                                "stream_format": playlists_stream_format_input,
                                "m3u_active": playlists_m3u_active_input,
                                "m3u_priority": playlists_m3u_priority_input,
                                "station_check": playlists_station_check_input
                            })

                            playlists = sorted(playlists, key=lambda x: sort_key(x["m3u_name"].casefold()))
                            write_data(csv_playlistmanager_playlists, playlists)
                            playlists = read_data(csv_playlistmanager_playlists)
                            preferred_playlists = get_preferred_playlists(preferred_playlists_default)
                            station_mapping_source_m3u_ids, station_mapping_source_fields, station_mapping_target_fields, station_mapping_target_parent_channel_ids = get_station_mapping_data(playlists, child_to_parent_mappings_default_base_02)

            elif '_cancel' in playlists_action:

                if sub_page is None or sub_page == 'plm_main':
                    pass
                
                elif sub_page == 'plm_modify_unassigned_stations':
                    filter_title_unassigned = ''
                    filter_m3u_name_unassigned = ''
                    filter_description_unassigned = ''
                    filter_parent_unassigned = ''
                    filter_stream_format_override_unassigned = ''
                    filter_station_status_unassigned = ''

                elif sub_page == 'plm_modify_assigned_stations':
                    filter_title_assigned = ''
                    filter_m3u_name_assigned = ''
                    filter_description_assigned = ''
                    filter_parent_assigned = ''
                    filter_stream_format_override_assigned = ''
                    filter_station_status_assigned = ''
                
                elif sub_page == 'plm_parent_stations':
                    filter_parent_title = ''
                    filter_parent_tvg_id_override = ''
                    filter_parent_tvg_logo_override = ''
                    filter_parent_channel_number_override = ''
                    filter_parent_tvc_guide_stationid_override = ''
                    filter_parent_preferred_playlist = ''                
                
                elif sub_page == 'plm_manage':
                    pass

    response = make_response(render_template(
        template,
        segment = sub_page,
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_playlists_anchor_id = playlists_anchor_id,
        html_playlists = playlists,
        html_preferred_playlists = preferred_playlists,
        html_parents = parents,
        html_stream_formats = stream_formats,
        html_stream_formats_overrides = stream_formats_overrides,
        html_child_to_parent_mappings = child_to_parent_mappings,
        html_unassigned_child_to_parents = unassigned_child_to_parents,
        html_assigned_child_to_parents = assigned_child_to_parents,
        html_all_child_to_parents_stats = all_child_to_parents_stats,
        html_playlists_station_count = playlists_station_count,
        html_playlist_files = playlist_files,
        html_uploaded_playlist_files = uploaded_playlist_files,
        html_current_path = current_path,
        html_uploaded_playlists_message = uploaded_playlists_message,
        html_filter_title_assigned = filter_title_assigned,
        html_filter_m3u_name_assigned = filter_m3u_name_assigned,
        html_filter_description_assigned = filter_description_assigned,
        html_filter_parent_assigned = filter_parent_assigned,
        html_filter_stream_format_override_assigned = filter_stream_format_override_assigned,
        html_filter_station_status_assigned = filter_station_status_assigned,
        html_filter_title_unassigned = filter_title_unassigned,
        html_filter_m3u_name_unassigned = filter_m3u_name_unassigned,
        html_filter_description_unassigned = filter_description_unassigned,
        html_filter_parent_unassigned = filter_parent_unassigned,
        html_filter_stream_format_override_unassigned = filter_stream_format_override_unassigned,
        html_filter_station_status_unassigned = filter_station_status_unassigned,
        html_filter_parent_title = filter_parent_title,
        html_filter_parent_tvg_id_override = filter_parent_tvg_id_override,
        html_filter_parent_tvg_logo_override = filter_parent_tvg_logo_override,
        html_filter_parent_channel_number_override = filter_parent_channel_number_override,
        html_filter_parent_tvc_guide_stationid_override = filter_parent_tvc_guide_stationid_override,
        html_filter_parent_preferred_playlist = filter_parent_preferred_playlist,
        html_station_start_number = station_start_number,
        html_max_stations = max_stations,
        html_plm_url_tag_in_m3us = plm_url_tag_in_m3us,
        html_plm_check_child_station_status = plm_check_child_station_status,
        html_settings_message = settings_message,
        html_plm_internal_pbs_stations = plm_internal_pbs_stations,
        html_plm_internal_pbs_url_base = plm_internal_pbs_url_base,
        html_station_mappings = station_mappings,
        html_station_mapping_source_m3u_ids = station_mapping_source_m3u_ids,
        html_station_mapping_source_fields = station_mapping_source_fields,
        html_compare_options = compare_options,
        html_station_mapping_target_fields = station_mapping_target_fields,
        html_compare_replace_options = compare_replace_options,
        html_station_mapping_target_parent_channel_ids = station_mapping_target_parent_channel_ids
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'

    if playlists_anchor_id:
        response.headers['Location'] = f'/playlists/{sub_page}#{playlists_anchor_id}'

    return response

# Used to download an m3u or XML EPG
@app.route('/playlists/files/<filename>')
def download_m3u_epg(filename):
    return export_csv(filename)

# Used to retrieve an uploaded or generated file
@app.route('/playlists/uploads/<filename>')
def download_uploads(filename):
    filename = os.path.join(playlists_uploads_dir_name, filename)
    return export_csv(filename)

# Used to dynamically create an internal file
@app.route('/playlists/uploads/internal/<filename>')
def download_internal(filename):
    settings = read_data(csv_settings)
    plm_internal_pbs_stations = settings[48]['settings']                        # [48] PLM: Internal PBS Stations On/Off
    plm_internal_pbs_url_base = settings[49]['settings']                        # [49] PLM: VLC Bridge PBS Base URL
    pbs_csv_url = 'https://raw.githubusercontent.com/babsonnexus/stream-link-manager-for-channels/refs/heads/main/executables/pbs_stations.csv'

    source_records = []
    final_m3us = []

    if filename == 'plmint_pbs_mpeg_ts_m3u_01.m3u' and plm_internal_pbs_stations == "On":
        waste_results, source_records, waste_message = parse_csv_url(pbs_csv_url)

    if source_records:

        for source_record in source_records:
            title = None
            tvc_guide_title = None
            channel_id = None
            tvg_id = None
            tvg_name = None
            tvg_logo = None
            tvg_chno = None
            channel_number = None
            tvg_description = None
            tvc_guide_description = None
            group_title = None
            tvc_guide_stationid = None
            tvc_guide_art = None
            tvc_guide_tags = None
            tvc_guide_genres = None
            tvc_guide_categories = None
            tvc_guide_placeholders = None
            tvc_stream_vcodec = None
            tvc_stream_acodec = None
            url = None
            stream_format = None
            run_append = True

            if filename == 'plmint_pbs_mpeg_ts_m3u_01.m3u':

                if source_record['status'] == "Good":
                    title = source_record['clean_name']
                    tvc_guide_title = title
                    channel_id = source_record['channel_id']
                    tvg_id = ''
                    tvg_name = title
                    tvg_logo = source_record['logo_color']
                    tvg_chno = source_record['unique_station_num']
                    channel_number = tvg_chno
                    tvg_description = ''
                    tvc_guide_description = tvg_description
                    group_title = ''
                    tvc_guide_stationid = source_record['gracenote_id']
                    tvc_guide_art = tvg_logo
                    tvc_guide_tags =''
                    tvc_guide_genres = ''
                    tvc_guide_categories = ''
                    tvc_guide_placeholders = ''
                    tvc_stream_vcodec = ''
                    tvc_stream_acodec = ''
                    url = f"{plm_internal_pbs_url_base}/pbs/watch/{source_record['station_id']}"
                    stream_format = "MPEG-TS"

                else:
                    run_append = False

            if run_append:
                final_m3us.append({
                    "title": title,
                    "tvc_guide_title": tvc_guide_title,
                    "channel_id": channel_id,
                    "tvg_id": tvg_id,
                    "tvg_name": tvg_name,
                    "tvg_logo": tvg_logo,
                    "tvg_chno": tvg_chno,
                    "channel_number": channel_number,
                    "tvg_description": tvg_description,
                    "tvc_guide_description": tvc_guide_description,
                    "group_title": group_title,
                    "tvc_guide_stationid": tvc_guide_stationid,
                    "tvc_guide_art": tvc_guide_art,
                    "tvc_guide_tags": tvc_guide_tags,
                    "tvc_guide_genres": tvc_guide_genres,
                    "tvc_guide_categories": tvc_guide_categories,
                    "tvc_guide_placeholders": tvc_guide_placeholders,
                    "tvc_stream_vcodec": tvc_stream_vcodec,
                    "tvc_stream_acodec": tvc_stream_acodec,
                    "url": url,
                    "stream_format": stream_format
                })

    if final_m3us:
        m3u_content = "#EXTM3U\n"
    
        for item in final_m3us:
            m3u_content += f'\n#EXTINF:-1 tvc-guide-title="{item["tvc_guide_title"]}"'
            m3u_content += f' channel-id="{item["channel_id"]}"'
            m3u_content += f' tvg-id="{item["tvg_id"]}"'
            m3u_content += f' tvg-name="{item["tvg_name"]}"'
            m3u_content += f' tvg-logo="{item["tvg_logo"]}"'
            m3u_content += f' tvg-chno="{item["tvg_chno"]}"'
            m3u_content += f' channel-number="{item["channel_number"]}"'
            m3u_content += f' tvg-description="{item["tvg_description"]}"'
            m3u_content += f' tvc-guide-description="{item["tvc_guide_description"]}"'
            m3u_content += f' group-title="{item["group_title"]}"'
            m3u_content += f' tvc-guide-stationid="{item["tvc_guide_stationid"]}"'
            m3u_content += f' tvc-guide-art="{item["tvc_guide_art"]}"'
            m3u_content += f' tvc-guide-tags="{item["tvc_guide_tags"]}"'
            m3u_content += f' tvc-guide-genres="{item["tvc_guide_genres"]}"'
            m3u_content += f' tvc-guide-categories="{item["tvc_guide_categories"]}"'
            m3u_content += f' tvc-guide-placeholders="{item["tvc_guide_placeholders"]}"'
            m3u_content += f' tvc-stream-vcodec="{item["tvc_stream_vcodec"]}"'
            m3u_content += f' tvc-stream-acodec="{item["tvc_stream_acodec"]}"'
            m3u_content += f',{item["title"]}\n'
            m3u_content += f'{item["url"]}\n'

        m3u_content = m3u_content.replace('"None"', '""')

        return m3u_content

    else:
        return f"{current_time()} ERROR: '{filename}' does not exist or is not turned on."

# Goes through each of the playlists and combines all m3us together into a single list
def get_combined_m3us():
    playlists = read_data(csv_playlistmanager_playlists)
    combined_m3us = []

    print(f"{current_time()} Starting combination of playlists...")

    for playlist in playlists:
        response = None
        response = fetch_url(playlist['m3u_url'], 3, 10)
        if response:
            combined_m3us.extend(parse_m3u(playlist['m3u_id'], playlist['m3u_name'], response))

    id_field = "station_playlist"
    update_rows(csv_playlistmanager_combined_m3us, combined_m3us, id_field, True)

    stations = read_data(csv_playlistmanager_combined_m3us)
    maps = read_data(csv_playlistmanager_child_to_parent)

    if stations:
        for station in stations:
            check_m3u_id_channel_id = f"{station['m3u_id']}_{station['channel_id']}"
            if check_m3u_id_channel_id not in [map['child_m3u_id_channel_id'] for map in maps]:
                new_row = { 'child_m3u_id_channel_id': check_m3u_id_channel_id, 'parent_channel_id': 'Unassigned', 'stream_format_override': 'None', 'child_station_check': '', 'enable_child_station_check': 'On' }
                append_data(csv_playlistmanager_child_to_parent, new_row)

    print(f"{current_time()} Finished combination of playlists.")

    run_child_station_mapping()
    check_child_station_status(None, None)

# Does the child station mapping
def run_child_station_mapping():
    print(f"{current_time()} Starting child station mapping...")

    stations = read_data(csv_playlistmanager_combined_m3us)
    station_mappings = read_data(csv_playlistmanager_station_mappings)
    filtered_station_mappings = [station_mapping for station_mapping in station_mappings if station_mapping['station_mapping_active'] == 'On' and station_mapping['source_m3u_id'] != 'remove_warning' and station_mapping['target_parent_channel_id'] != 'remove_warning']
    filtered_station_mappings.sort(key=lambda x: int(x.get("station_mapping_priority", float("inf"))))
    child_to_parent_maps = read_data(csv_playlistmanager_child_to_parent)
    child_to_parent_map_parent_channel_id_lookup = {child_to_parent_map['child_m3u_id_channel_id']: child_to_parent_map['parent_channel_id'] for child_to_parent_map in child_to_parent_maps}
    child_to_parent_map_stream_format_override_lookup = {child_to_parent_map['child_m3u_id_channel_id']: child_to_parent_map['stream_format_override'] for child_to_parent_map in child_to_parent_maps}
    child_to_parent_map_enable_child_station_check_lookup = {child_to_parent_map['child_m3u_id_channel_id']: child_to_parent_map['enable_child_station_check'] for child_to_parent_map in child_to_parent_maps}
    parents = read_data(csv_playlistmanager_parents)

    if station_mappings:

        write_stations = False
        write_parents = False

        for station_mapping in filtered_station_mappings:

            for station in stations:

                for field in plm_fields_base:

                    if station_mapping['source_field'] == field['field_id'] or station_mapping['source_field'] == 'all':

                        source_field_value = station[field['field_id']]
                        if station_mapping['target_field'] == 'source':
                            target_field = field['field_id']
                        else:
                            target_field = station_mapping['target_field']

                        if ( 
                                ( station_mapping['source_field_compare_id'] == 'equal' and source_field_value == station_mapping['source_field_string'] ) or 
                                ( station_mapping['source_field_compare_id'] == 'equal_not' and source_field_value != station_mapping['source_field_string'] ) or
                                ( station_mapping['source_field_compare_id'] == 'contain' and station_mapping['source_field_string'] in source_field_value ) or
                                ( station_mapping['source_field_compare_id'] == 'contain_not' and station_mapping['source_field_string'] not in source_field_value ) or
                                ( station_mapping['source_field_compare_id'] == 'begin' and source_field_value.startswith(station_mapping['source_field_string']) ) or
                                ( station_mapping['source_field_compare_id'] == 'begin_not' and not source_field_value.startswith(station_mapping['source_field_string']) ) or
                                ( station_mapping['source_field_compare_id'] == 'end' and source_field_value.endswith(station_mapping['source_field_string']) ) or
                                ( station_mapping['source_field_compare_id'] == 'end_not' and not source_field_value.endswith(station_mapping['source_field_string']) ) or
                                ( station_mapping['source_field_compare_id'] == 'regex' and re.search(station_mapping['source_field_string'], source_field_value) ) or
                                ( station_mapping['source_field_compare_id'] == 'regex_not' and not re.search(station_mapping['source_field_string'], source_field_value) ) 
                            ):

                                if station_mapping['target_field'] != 'no_field' and station_mapping['target_field_compare_replace_id'] != 'na':

                                    if station_mapping['source_m3u_id'] == station['m3u_id'] or station_mapping['source_m3u_id'] == 'all':
                        
                                        target_field_base = station[target_field]
                                        target_field_value = None

                                        if station_mapping['target_field_compare_replace_id'].startswith('replace'):
                                            if station_mapping['source_field_compare_id'] == 'equal' or station_mapping['target_field_compare_replace_id'] == 'replace_all':
                                                target_field_value = station_mapping['target_field_string']
                                            elif station_mapping['source_field_compare_id'] in ['contain', 'begin', 'end']:
                                                target_field_value = target_field_base.replace(station_mapping['source_field_string'], station_mapping['target_field_string'])
                                            elif station_mapping['source_field_compare_id'] == 'regex':
                                                target_field_value = re.sub(station_mapping['source_field_string'], station_mapping['target_field_string'], target_field_base)

                                        elif station_mapping['target_field_compare_replace_id'].startswith('append'):
                                            if station_mapping['source_field_compare_id'] == 'equal' or station_mapping['target_field_compare_replace_id'] == 'append_all':
                                                target_field_value = f"{target_field_base}{station_mapping['target_field_string']}"
                                            elif station_mapping['source_field_compare_id'] in ['contain', 'begin', 'end']:
                                                target_field_value = target_field_base.replace(station_mapping['source_field_string'], f"{station_mapping['source_field_string']}{station_mapping['target_field_string']}")
                                            elif station_mapping['source_field_compare_id'] == 'regex':
                                                target_field_value = re.sub(station_mapping['source_field_string'], f"{station_mapping['source_field_string']}{station_mapping['target_field_string']}", target_field_base)

                                        elif station_mapping['target_field_compare_replace_id'].startswith('prepend'):
                                            if station_mapping['source_field_compare_id'] == 'equal' or station_mapping['target_field_compare_replace_id'] == 'prepend_all':
                                                target_field_value = f"{station_mapping['target_field_string']}{target_field_base}"
                                            elif station_mapping['source_field_compare_id'] in ['contain', 'begin', 'end']:
                                                target_field_value = target_field_base.replace(station_mapping['source_field_string'], f"{station_mapping['target_field_string']}{station_mapping['source_field_string']}")
                                            elif station_mapping['source_field_compare_id'] == 'regex':
                                                target_field_value = re.sub(station_mapping['source_field_string'], f"{station_mapping['target_field_string']}{station_mapping['source_field_string']}", target_field_base)

                                        station[target_field] = target_field_value
                                        write_stations = True
                                        notification_add(f"    MAPPED: {station['station_playlist']}")

                                if station_mapping['target_parent_channel_id'] != 'manual' or station_mapping['target_stream_format_override'] != 'None':

                                    child_m3u_id_channel_id = f"{station['m3u_id']}_{station['channel_id']}"
                                    target_parent = None
                                    target_stream_format_override = None

                                    if station_mapping['target_parent_channel_id'] != 'manual':

                                        if station_mapping['target_parent_channel_id'] == 'Make Parent':

                                            if child_to_parent_map_parent_channel_id_lookup[child_m3u_id_channel_id] == 'Unassigned':
                                                write_parents = True
                                                target_parent = f"plm_{max((int(parent['parent_channel_id'].split('_')[1]) for parent in parents), default=0) + 1:04d}"

                                                parents.append({
                                                    "parent_channel_id": target_parent,
                                                    "parent_title": station['title'],
                                                    "parent_tvg_id_override": None,
                                                    "parent_tvg_logo_override": None,
                                                    "parent_channel_number_override": None,
                                                    "parent_tvc_guide_stationid_override": None,
                                                    "parent_tvc_guide_art_override": None,
                                                    "parent_tvc_guide_tags_override": None,
                                                    "parent_tvc_guide_genres_override": None,
                                                    "parent_tvc_guide_categories_override": None,
                                                    "parent_tvc_guide_placeholders_override": None,
                                                    "parent_tvc_stream_vcodec_override": None,
                                                    "parent_tvc_stream_acodec_override": None,
                                                    "parent_preferred_playlist": None,
                                                    "parent_active": "On",
                                                    "parent_tvg_description_override": None,
                                                    "parent_group_title_override": None
                                                })

                                        else:
                                            target_parent = station_mapping['target_parent_channel_id']

                                    if station_mapping['target_stream_format_override'] != 'None':
                                        target_stream_format_override = station_mapping['target_stream_format_override']

                                    if target_parent or target_stream_format_override:
                                        if target_parent:
                                            parent_channel_id = target_parent
                                        else:
                                            parent_channel_id = child_to_parent_map_parent_channel_id_lookup[child_m3u_id_channel_id]

                                        if target_stream_format_override:
                                            stream_format_override = target_stream_format_override
                                        else:
                                            stream_format_override = child_to_parent_map_stream_format_override_lookup[child_m3u_id_channel_id]

                                        enable_child_station_check = child_to_parent_map_enable_child_station_check_lookup[child_m3u_id_channel_id]

                                        set_child_to_parent(child_m3u_id_channel_id, parent_channel_id, stream_format_override, parents, enable_child_station_check)
                                        child_to_parent_maps = read_data(csv_playlistmanager_child_to_parent)
                                        child_to_parent_map_parent_channel_id_lookup = {child_to_parent_map['child_m3u_id_channel_id']: child_to_parent_map['parent_channel_id'] for child_to_parent_map in child_to_parent_maps}
                                        child_to_parent_map_stream_format_override_lookup = {child_to_parent_map['child_m3u_id_channel_id']: child_to_parent_map['stream_format_override'] for child_to_parent_map in child_to_parent_maps}
                                        child_to_parent_map_enable_child_station_check_lookup = {child_to_parent_map['child_m3u_id_channel_id']: child_to_parent_map['enable_child_station_check'] for child_to_parent_map in child_to_parent_maps}

        if write_stations:
            write_data(csv_playlistmanager_combined_m3us, stations)

        if write_parents:
            if len(parents) > 1:
                parents = sorted(parents, key=lambda x: sort_key(x["parent_title"].casefold()))
            write_data(csv_playlistmanager_parents, parents)
        
    else:
        print(f"{current_time()} INFO: No station mappings found. Skipping child station mapping.")

    print(f"{current_time()} Finished child station mapping.")

# Checks that status of child stations
def check_child_station_status(check_child_station_status_single, check_child_station_status_single_url):
    print(f"{current_time()} Starting check of child stations...")

    settings = read_data(csv_settings)
    plm_check_child_station_status = settings[59]['settings']                   # [59] PLM/MTM: Check Child Station Status On/Off
    plm_station_status_skip_after_fails = int(settings[63]['settings'])         # [63] PLM/MTM: Check Child Station Status Skip Playlist After Fails (0 = Disabled)

    playlists_fail_count = {}
    skip_playlists = []
    message = None
    stream_metadata = []

    stations = read_data(csv_playlistmanager_combined_m3us)
    maps = read_data(csv_playlistmanager_child_to_parent)
    playlists = read_data(csv_playlistmanager_playlists)

    if maps:
        temp_record = create_temp_record(maps[0].keys())
    else:
        temp_record = initial_data(csv_playlistmanager_child_to_parent)[0]
    run_empty_rows = False

    map_lookup = {map['child_m3u_id_channel_id']: map['parent_channel_id'] for map in maps}
    enable_child_station_check_lookup = {map['child_m3u_id_channel_id'] for map in maps if map['enable_child_station_check'] == "On"}
    playlist_active_lookup = {playlist['m3u_id']: playlist['m3u_active'] for playlist in playlists}
    playlist_station_check_lookup = {playlist['m3u_id']: playlist['station_check'] for playlist in playlists}

    not_ignore_stations = []
    disable_child_stations = []
    skipped_child_stations = []
    drm_child_stations = []
    hls_child_stations = []
    mpegts_child_stations = []

    if plm_check_child_station_status == "On":
        
        if check_child_station_status_single:
            
            if check_child_station_status_single == 'm3u_0000_manual':
                not_ignore_stations.append({
                    'station_playlist': f"Manual ({check_child_station_status_single_url})",
                    'm3u_id': 'm3u_0000',
                    'title': "Manual",
                    'tvc_guide_title': "Manual",
                    'channel_id': 'manual',
                    'tvg_id': '',
                    'tvg_name': '',
                    'tvg_logo': '',
                    'tvg_chno': '',
                    'channel_number': '',
                    'tvg_description': '',
                    'tvc_guide_description': '',
                    'group_title': '',
                    'tvc_guide_stationid': '',
                    'tvc_guide_art': '',
                    'tvc_guide_tags': '',
                    'tvc_guide_genres': '',
                    'tvc_guide_categories': '',
                    'tvc_guide_placeholders': '',
                    'tvc_stream_vcodec': '',
                    'tvc_stream_acodec': '',
                    'url': check_child_station_status_single_url
                })
            
            else:
                for station in stations:
                    check_m3u_id_channel_id = f"{station['m3u_id']}_{station['channel_id']}"
                    if check_m3u_id_channel_id == check_child_station_status_single:
                        not_ignore_stations.append(station)
                        break
            
        else:
            for station in stations:
                if station['m3u_id'] in playlist_active_lookup and station['m3u_id'] in playlist_station_check_lookup:
                    if playlist_active_lookup[station['m3u_id']] == 'On' and playlist_station_check_lookup[station['m3u_id']] == 'On':
                        check_m3u_id_channel_id = f"{station['m3u_id']}_{station['channel_id']}"
                        parent_channel_id = map_lookup.get(check_m3u_id_channel_id)
                        if parent_channel_id and parent_channel_id != 'Ignore' and check_m3u_id_channel_id in enable_child_station_check_lookup:
                            not_ignore_stations.append(station)

        if not_ignore_stations:
            for not_ignore_station in not_ignore_stations:
                check_m3u_id_channel_id = f"{not_ignore_station['m3u_id']}_{not_ignore_station['channel_id']}"
                check_m3u_id_channel_id_url = not_ignore_station['url']
                station_check_response = None

                if not_ignore_station['m3u_id'] in skip_playlists:
                    station_check_response = 'Skipped'
                else:
                    station_check_response, stream_metadata = test_video_stream(check_m3u_id_channel_id_url)
                message = f"{current_time()} INFO: {not_ignore_station['station_playlist']} responded '{station_check_response}'."
                print(f"{message}")

                if station_check_response == 'fail':
                    disable_child_stations.append(check_m3u_id_channel_id)

                    # Increment the fail count for the playlist
                    if not_ignore_station['m3u_id'] in playlists_fail_count:
                        playlists_fail_count[not_ignore_station['m3u_id']] += 1
                    else:
                        playlists_fail_count[not_ignore_station['m3u_id']] = 1

                    # If the fail count exceeds the threshold, add to skip list
                    if plm_station_status_skip_after_fails != 0 and playlists_fail_count[not_ignore_station['m3u_id']] >= plm_station_status_skip_after_fails:
                        skip_playlists.append(not_ignore_station['m3u_id'])                    

                elif station_check_response == 'Skipped':
                    skipped_child_stations.append(check_m3u_id_channel_id)
                    
                elif station_check_response == 'DRM':
                    drm_child_stations.append(check_m3u_id_channel_id)

                elif station_check_response == 'HLS':
                    hls_child_stations.append(check_m3u_id_channel_id)
                
                elif station_check_response == 'MPEG-TS':
                    mpegts_child_stations.append(check_m3u_id_channel_id)

    else:
        print(f"{current_time()} INFO: Check of child stations is disabled.")

    if check_child_station_status_single != 'm3u_0000_manual':
        for map in maps:
            if map['child_m3u_id_channel_id'] in disable_child_stations:
                map['child_station_check'] = 'Disabled'
            elif map['child_m3u_id_channel_id'] in skipped_child_stations:
                map['child_station_check'] = 'Disabled (Skipped Check)'
            elif map['child_m3u_id_channel_id'] in drm_child_stations:
                map['child_station_check'] = 'Disabled (DRM)'
            elif map['child_m3u_id_channel_id'] in hls_child_stations:
                map['child_station_check'] = 'HLS'
            elif map['child_m3u_id_channel_id'] in mpegts_child_stations:
                map['child_station_check'] = 'MPEG-TS'
            elif check_child_station_status_single is None or check_child_station_status_single == '':
                map['child_station_check'] = ''

        if not maps:
            maps.append(temp_record)
            run_empty_rows = True

        write_data(csv_playlistmanager_child_to_parent, maps)
        if run_empty_rows:
            remove_empty_row(csv_playlistmanager_child_to_parent)

    print(f"{current_time()} Finished check of child stations.")
    
    return stream_metadata, message

# Parse the m3u Playlist to get all the details
def parse_m3u(m3u_id, m3u_name, response):
    print(f"{current_time()} INFO: Beginning parse of {m3u_name} ({m3u_id}).")

    skip_lines = [  '#EXTVLCOPT', 
                    '#EXT-X-STREAM-INF',
                    '#EXT-X-MEDIA', 
                    '#EXT-X-MAP'
                 ]

    data = response.text.splitlines()
    cleaned_data = clean_m3u(data)
    
    records = []
    current_record = None
    for line in cleaned_data:
        channel_id_replacement = None

        if line.startswith('#EXTINF'):
            if current_record:
                records.append(current_record)

            match = re.match(r'#EXTINF:(.*)', line)
            if match:
                fields = match.group(1)
                metadata = {
                    "tvc-guide-title": "",
                    "channel-id": "",
                    "tvg-id": "",
                    "tvg-name": "",
                    "tvg-logo": "",
                    "tvg-chno": "",
                    "channel-number": "",
                    "tvg-description": "",
                    "tvc-guide-description": "",
                    "group-title": "",
                    "tvc-guide-stationid": "",
                    "tvc-guide-art": "",
                    "tvc-guide-tags": "",
                    "tvc-guide-genres": "",
                    "tvc-guide-categories": "",
                    "tvc-guide-placeholders": "",
                    "tvc-stream-vcodec": "",
                    "tvc-stream-acodec": ""
                }

                # Extract known fields
                for key in metadata.keys():
                    pattern = re.compile(rf'{key}="(.*?)"')
                    result = pattern.search(fields)
                    if result:
                        metadata[key] = result.group(1)
                        fields = fields.replace(result.group(0), "")

                # What remains is the title
                if ',' in fields:
                    _, title = fields.rsplit(',', 1)
                    metadata["title"] = title.strip()
                else:
                    metadata["title"] = fields.strip()
                
                if metadata["channel-id"] is None or metadata["channel-id"] == '':
                    channel_id_replacement = f"{m3u_name}_{metadata['title']}"
                    channel_id_replacement = channel_id_replacement.replace(' ', '_')
                    channel_id_replacement = channel_id_replacement.lower()
                    metadata["channel-id"] = channel_id_replacement

                current_record = {
                    'station_playlist': f"{metadata['title']} on {m3u_name} [{metadata['channel-id']}]",
                    'm3u_id': m3u_id,
                    'title': metadata["title"],
                    'tvc_guide_title': metadata["tvc-guide-title"],
                    'channel_id': metadata["channel-id"],
                    'tvg_id': metadata["tvg-id"],
                    'tvg_name': metadata["tvg-name"],
                    'tvg_logo': metadata["tvg-logo"],
                    'tvg_chno': metadata["tvg-chno"],
                    'channel_number': metadata["channel-number"],
                    'tvg_description': metadata["tvg-description"],
                    'tvc_guide_description': metadata["tvc-guide-description"],
                    'group_title': metadata["group-title"],
                    'tvc_guide_stationid': metadata["tvc-guide-stationid"],
                    'tvc_guide_art': metadata["tvc-guide-art"],
                    'tvc_guide_tags': metadata["tvc-guide-tags"],
                    'tvc_guide_genres': metadata["tvc-guide-genres"],
                    'tvc_guide_categories': metadata["tvc-guide-categories"],
                    'tvc_guide_placeholders': metadata["tvc-guide-placeholders"],
                    'tvc_stream_vcodec': metadata["tvc-stream-vcodec"],
                    'tvc_stream_acodec': metadata["tvc-stream-acodec"],
                    'url': ""
                }
        elif ( line.startswith('http') or '://' in line ) and not any(skip_line in line for skip_line in skip_lines):
            if current_record:
                current_record['url'] = line.strip()
                records.append(current_record)
                current_record = None

    if current_record:
        records.append(current_record)

    print(f"{current_time()} INFO: Initial parse of {m3u_name} ({m3u_id}) complete. Beginning check for unique 'channel-id' values.")

    # Ensure unique channel-id
    channel_id_counts = {}
    for record in records:
        channel_id = record['channel_id']
        if channel_id in channel_id_counts:
            channel_id_counts[channel_id] += 1
            new_channel_id = f"{channel_id}_{channel_id_counts[channel_id]:04d}"
            record['channel_id'] = new_channel_id
            record['station_playlist'] = f"{record['title']} on {m3u_name} [{new_channel_id}]"
        else:
            channel_id_counts[channel_id] = 0

    print(f"{current_time()} INFO: Finished parse of {m3u_name} ({m3u_id}).")

    return records

# Removes extra carriage returns that mess up reading the data
def clean_m3u(data):
    cleaned_lines = []
    for i, line in enumerate(data):
        if not (line.startswith('http') or line.startswith('#EXTINF:') or '://' in line):
            if i > 0:
                cleaned_lines[-1] += ' ' + line.strip()
            else:
                cleaned_lines.append(line.strip())
        else:
            cleaned_lines.append(line.strip())
    return cleaned_lines

# Creates the dropdown list of 'Preferred Playlists'
def get_preferred_playlists(preferred_playlists_default):
    playlists = []
    sorted_playlists = []
    
    playlists = read_data(csv_playlistmanager_playlists)
    sorted_playlists = sorted(playlists, key=lambda x: sort_key(x["m3u_name"].casefold()))
    
    # Initialize preferred_playlists with a copy of the default list
    preferred_playlists = preferred_playlists_default.copy()
    
    for sorted_playlist in sorted_playlists:
        prefer = f"Prefer: {sorted_playlist['m3u_name']}"
        preferred_playlists.append({
            'm3u_id': sorted_playlist['m3u_id'],
            'prefer_name': prefer
        })
    
    return preferred_playlists

# Data for station mapping
def get_station_mapping_data(playlists, child_to_parent_mappings_default_base_02):

    station_mapping_source_m3u_ids = [{'m3u_id': 'all', 'm3u_name': 'All Source Playlists'}]
    for playlist in playlists:
        station_mapping_source_m3u_ids.append({
            'm3u_id': playlist['m3u_id'],
            'm3u_name': f"PLAYLIST: {playlist['m3u_name']}"
        })
    station_mapping_source_m3u_ids.append({'m3u_id': 'remove_warning','m3u_name': 'WARNING: Source Playlists Deleted'})

    station_mapping_source_fields_base = [
        {'field_id': 'all', 'field_name': 'All Fields'}
    ]

    station_mapping_target_fields_base = [
        {'field_id': 'no_field', 'field_name': 'No Field'},
        {'field_id': 'source', 'field_name': 'Source Field'}
    ]

    station_mapping_source_fields = station_mapping_source_fields_base + plm_fields_base
    station_mapping_target_fields = station_mapping_target_fields_base + plm_fields_base

    station_mapping_target_parent_channel_ids = []
    station_mapping_target_parent_channel_ids_default_base_01 = [
        { 'parent_channel_id': 'manual', 'parent_title': 'Manual Assignment' }
    ]
    station_mapping_target_parent_channel_ids_default = station_mapping_target_parent_channel_ids_default_base_01 + child_to_parent_mappings_default_base_02
    station_mapping_target_parent_channel_ids = get_child_to_parent_mappings(station_mapping_target_parent_channel_ids_default)
    station_mapping_target_parent_channel_ids.append({'parent_channel_id': 'remove_warning','parent_title': 'WARNING: Assigned Parent Deleted'})

    return station_mapping_source_m3u_ids, station_mapping_source_fields, station_mapping_target_fields, station_mapping_target_parent_channel_ids

# Creates the dropdown list of 'Parent Station'
def get_child_to_parent_mappings(child_to_parent_mappings_default):
    child_to_parent_mappings = []
    sorted_child_to_parent_mappings = []
    
    child_to_parent_mappings = read_data(csv_playlistmanager_parents)
    if len(child_to_parent_mappings) > 1:
        sorted_child_to_parent_mappings = sorted(child_to_parent_mappings, key=lambda x: sort_key(x["parent_title"].casefold()))
    else:
        sorted_child_to_parent_mappings = child_to_parent_mappings
    
    # Initialize with a copy of the default list
    final_child_to_parent_mappings = child_to_parent_mappings_default.copy()
    
    for sorted_child_to_parent_mapping in sorted_child_to_parent_mappings:
        final = f"Station: {sorted_child_to_parent_mapping['parent_title']}"
        final_child_to_parent_mappings.append({
            'parent_channel_id': sorted_child_to_parent_mapping['parent_channel_id'],
            'parent_title': final
        })
    
    return final_child_to_parent_mappings

# Creates the list of Unassigned and Assigned stations on the webpage
def get_child_to_parents(sub_page):
    playlists = read_data(csv_playlistmanager_playlists)
    combined_m3us = read_data(csv_playlistmanager_combined_m3us)
    child_to_parents = read_data(csv_playlistmanager_child_to_parent)

    playlists_station_count = []
    all_child_to_parents = []
    sorted_all_child_to_parents = []
    unassigned_child_to_parents = []
    assigned_child_to_parents = []
    all_child_to_parents_stats = {}

    if sub_page == 'plm_manage':
        for playlist in playlists:
            station_count = sum(1 for record in combined_m3us if record['m3u_id'] == playlist['m3u_id'])
            playlists_station_count.append({
                'm3u_id': playlist['m3u_id'],
                'station_count': station_count
            })

    if sub_page is None or sub_page in ['plm_main', 'plm_modify_unassigned_stations', 'plm_modify_assigned_stations']:
        combined_m3u_dict = {f"{m3u['m3u_id']}_{m3u['channel_id']}": m3u for m3u in combined_m3us}
        playlist_dict = {playlist['m3u_id']: playlist for playlist in playlists}

        for child_to_parent in child_to_parents:
            check_m3u_id_channel_id = child_to_parent['child_m3u_id_channel_id']
            if check_m3u_id_channel_id in combined_m3u_dict:
                combined_m3u = combined_m3u_dict[check_m3u_id_channel_id]
                child_to_parent_channel_id = f"{combined_m3u['m3u_id']}_{combined_m3u['channel_id']}"
                child_to_parent_title = combined_m3u['title']

                playlist = playlist_dict.get(combined_m3u['m3u_id'])
                if playlist:
                    child_to_parent_m3u_name = f"{playlist['m3u_name']} [{child_to_parent_channel_id}]"
                    all_child_to_parents_append = playlist['m3u_active'] == "On"

                    if combined_m3u['tvc_guide_description']:
                        child_to_parent_description = combined_m3u['tvc_guide_description']
                    elif combined_m3u['tvg_description']:
                        child_to_parent_description = combined_m3u['tvg_description']
                    else:
                        child_to_parent_description = "No description available..."

                    child_to_parent_parent_channel_id = child_to_parent['parent_channel_id']
                    child_to_parent_parent_stream_format_override = child_to_parent['stream_format_override']
                    child_to_parent_parent_child_station_check = child_to_parent['child_station_check']
                    child_to_parent_parent_enable_child_station_check = child_to_parent['enable_child_station_check']

                    if all_child_to_parents_append:
                        all_child_to_parents.append({
                            'channel_id': child_to_parent_channel_id,
                            'title': child_to_parent_title,
                            'm3u_name': child_to_parent_m3u_name,
                            'description': child_to_parent_description,
                            'parent_channel_id': child_to_parent_parent_channel_id,
                            'stream_format_override': child_to_parent_parent_stream_format_override,
                            'child_station_check': child_to_parent_parent_child_station_check,
                            'enable_child_station_check': child_to_parent_parent_enable_child_station_check
                        })

        # Split unassigned and assigned
        sorted_all_child_to_parents = sorted(all_child_to_parents, key=lambda x: sort_key(x["title"].casefold()))
        for sorted_all_child_to_parent in sorted_all_child_to_parents:
            if sorted_all_child_to_parent['parent_channel_id'] == "Unassigned":
                unassigned_child_to_parents.append({
                    'channel_id': sorted_all_child_to_parent['channel_id'],
                    'title': sorted_all_child_to_parent['title'],
                    'm3u_name': sorted_all_child_to_parent['m3u_name'],
                    'description': sorted_all_child_to_parent['description'],
                    'parent_channel_id': sorted_all_child_to_parent['parent_channel_id'],
                    'stream_format_override': sorted_all_child_to_parent['stream_format_override'],
                    'child_station_check': sorted_all_child_to_parent['child_station_check'],
                    'enable_child_station_check': sorted_all_child_to_parent['enable_child_station_check']
                })
            else:
                assigned_child_to_parents.append({
                    'channel_id': sorted_all_child_to_parent['channel_id'],
                    'title': sorted_all_child_to_parent['title'],
                    'm3u_name': sorted_all_child_to_parent['m3u_name'],
                    'description': sorted_all_child_to_parent['description'],
                    'parent_channel_id': sorted_all_child_to_parent['parent_channel_id'],
                    'stream_format_override': sorted_all_child_to_parent['stream_format_override'],
                    'child_station_check': sorted_all_child_to_parent['child_station_check'],
                    'enable_child_station_check': sorted_all_child_to_parent['enable_child_station_check']
                })

    # Create statistics
    if sub_page is None or sub_page == 'plm_main':
        total_records = len(all_child_to_parents)

        disabled_count = sum(1 for record in all_child_to_parents if record['child_station_check'].startswith("Disabled"))
        unassigned_count = sum(1 for record in all_child_to_parents if record['parent_channel_id'] == "Unassigned" and not record['child_station_check'].startswith("Disabled"))
        ignore_count = sum(1 for record in all_child_to_parents if record['parent_channel_id'] == "Ignore")

        assigned_to_parent_ids = {record['parent_channel_id'] for record in all_child_to_parents if record['parent_channel_id'] not in ["Unassigned", "Ignore"] and not record['child_station_check'].startswith("Disabled")}
        assigned_to_parent_count = len(assigned_to_parent_ids)

        redundant_count = total_records - (unassigned_count + ignore_count + assigned_to_parent_count + disabled_count)
        
        all_child_to_parents_stats = {
            'total_records': total_records,
            'unassigned_count': unassigned_count,
            'unassigned_percentage': calc_percentage(unassigned_count, total_records),
            'ignore_count': ignore_count,
            'ignore_percentage': calc_percentage(ignore_count, total_records),
            'assigned_to_parent_count': assigned_to_parent_count,
            'assigned_to_parent_percentage': calc_percentage(assigned_to_parent_count, total_records),
            'redundant_count': redundant_count,
            'redundant_percentage': calc_percentage(redundant_count, total_records),
            'disabled_count': disabled_count,
            'disabled_percentage': calc_percentage(disabled_count, total_records)
        }

    return unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count

# Sets a child to a parent for a station
def set_child_to_parent(child_m3u_id_channel_id, parent_channel_id, stream_format_override, parents, enable_child_station_check):
    child_to_parents = read_data(csv_playlistmanager_child_to_parent)

    for child_to_parent in child_to_parents:
        if child_to_parent['child_m3u_id_channel_id'] == child_m3u_id_channel_id:

            if parent_channel_id not in [parent['parent_channel_id'] for parent in parents] and parent_channel_id not in ["Unassigned", "Ignore"]:
                parent_channel_id = "Unassigned"

            child_to_parent['parent_channel_id'] = parent_channel_id
            child_to_parent['stream_format_override'] = stream_format_override
            child_to_parent['enable_child_station_check'] = enable_child_station_check
            break

    write_data(csv_playlistmanager_child_to_parent, child_to_parents)

# Creates the m3u(s) and XML EPG(s)
def get_final_m3us_epgs():
    notification_add(f"{current_time()} Starting generation of final m3u(s) and XML EPG(s)...")

    settings = read_data(csv_settings)

    station_start_number = int(settings[11]['settings'])
    max_stations = int(settings[12]['settings'])

    parents = read_data(csv_playlistmanager_parents)
    maps = read_data(csv_playlistmanager_child_to_parent)
    combined_children = read_data(csv_playlistmanager_combined_m3us)
    playlists = read_data(csv_playlistmanager_playlists)
    playlists.sort(key=lambda x: int(x.get("m3u_priority", float("inf"))))

    fields = [
        "tvg_id",
        "tvg_name",
        "tvg_logo",
        "tvg_description",
        "tvc_guide_description",
        "group_title",
        "tvc_guide_stationid",
        "tvc_guide_art",
        "tvc_guide_tags",
        "tvc_guide_genres",
        "tvc_guide_categories",
        "tvc_guide_placeholders",
        "tvc_stream_vcodec",
        "tvc_stream_acodec",
        "url",
        "stream_format"
    ]

    final_m3us = []

    for parent in parents:

        if parent['parent_active'] == "On":

            title = None
            tvc_guide_title = None
            channel_id = None
            tvg_id = None
            tvg_name = None
            tvg_logo = None
            tvg_chno = None
            channel_number = None
            tvg_description = None
            tvc_guide_description = None
            group_title = None
            tvc_guide_stationid = None
            tvc_guide_art = None
            tvc_guide_tags = None
            tvc_guide_genres = None
            tvc_guide_categories = None
            tvc_guide_placeholders = None
            tvc_stream_vcodec = None
            tvc_stream_acodec = None
            url = None
            stream_format = None

            channel_id = parent['parent_channel_id']

            playlist_preferences = []

            if parent['parent_preferred_playlist'] is not None and parent['parent_preferred_playlist'] != '':
                playlist_preferences.append(parent['parent_preferred_playlist'])

            inactive_playlists = []
            for playlist in playlists:
                if playlist['m3u_active'] == "On":
                    playlist_preferences.append(playlist['m3u_id'])
                else:
                    inactive_playlists.append(playlist['m3u_id'])
            
            if parent['parent_preferred_playlist'] in inactive_playlists:
                playlist_preferences.remove(parent['parent_preferred_playlist'])

            children = []
            for map in maps:
                if map['parent_channel_id'] == channel_id and not map['child_station_check'].startswith('Disabled'):
                    children.append(map)

            children = [child for child in children if re.search(r'm3u_\d{4}', child['child_m3u_id_channel_id']).group(0) in playlist_preferences]

            children = sorted(
                children,
                key=lambda child: (
                    playlist_preferences.index(re.match(r'm3u_\d{4}', child['child_m3u_id_channel_id']).group(0)),
                    re.sub(r'^m3u_\d{4}_', '', child['child_m3u_id_channel_id'])
                )
            )

            for field in fields:
                field_value = None
                field_value = get_m3u_field_value(field, combined_children, children)

                if field == "tvg_id":
                    if parent['parent_tvg_id_override'] is not None and parent['parent_tvg_id_override'] != '':
                        tvg_id = parent['parent_tvg_id_override']
                    else:
                        tvg_id = field_value

                elif field == "tvg_name":
                    tvg_name = field_value

                elif field == "tvg_logo":
                    if parent['parent_tvg_logo_override'] is not None and parent['parent_tvg_logo_override'] != '':
                        tvg_logo = parent['parent_tvg_logo_override']
                    else:
                        tvg_logo = field_value

                elif field == "tvg_description":
                    if parent['parent_tvg_description_override'] is not None and parent['parent_tvg_description_override'] != '':
                        tvg_description = parent['parent_tvg_description_override']
                    else:
                        tvg_description = field_value
                
                elif field == "tvc_guide_description":
                    tvc_guide_description = field_value

                    if tvc_guide_description is not None and tvc_guide_description != '':
                        tvg_description = tvc_guide_description
                    elif tvg_description is not None and tvg_description != '':
                        tvc_guide_description = tvg_description
                    else:
                        tvg_description = f"No description available..."
                        tvc_guide_description = tvg_description

                elif field == "group_title":
                    if parent['parent_group_title_override'] is not None and parent['parent_group_title_override'] != '':
                        group_title = parent['parent_group_title_override']
                    else:
                        group_title = field_value

                elif field == "tvc_guide_stationid":
                    if parent['parent_tvc_guide_stationid_override'] is not None and parent['parent_tvc_guide_stationid_override'] != '':
                        tvc_guide_stationid = parent['parent_tvc_guide_stationid_override']
                    else:
                        tvc_guide_stationid = field_value

                    # Check if tvc_guide_stationid (Gracenote ID) only has numeric characters
                    if tvc_guide_stationid:
                        if not tvc_guide_stationid.isdigit():
                            tvc_guide_stationid = None

                elif field == "tvc_guide_art":
                    if parent['parent_tvc_guide_art_override'] is not None and parent['parent_tvc_guide_art_override'] != '':
                        tvc_guide_art = parent['parent_tvc_guide_art_override']
                    else:
                        tvc_guide_art = field_value

                elif field == "tvc_guide_tags":
                    if parent['parent_tvc_guide_tags_override'] is not None and parent['parent_tvc_guide_tags_override'] != '':
                        tvc_guide_tags = parent['parent_tvc_guide_tags_override']
                    else:
                        tvc_guide_tags = field_value

                elif field == "tvc_guide_genres":
                    if parent['parent_tvc_guide_genres_override'] is not None and parent['parent_tvc_guide_genres_override'] != '':
                        tvc_guide_genres = parent['parent_tvc_guide_genres_override']
                    else:
                        tvc_guide_genres = field_value

                elif field == "tvc_guide_categories":
                    if parent['parent_tvc_guide_categories_override'] is not None and parent['parent_tvc_guide_categories_override'] != '':
                        tvc_guide_categories = parent['parent_tvc_guide_categories_override']
                    else:
                        tvc_guide_categories = field_value

                elif field == "tvc_guide_placeholders":
                    if parent['parent_tvc_guide_placeholders_override'] is not None and parent['parent_tvc_guide_placeholders_override'] != '':
                        tvc_guide_placeholders = parent['parent_tvc_guide_placeholders_override']
                    else:
                        tvc_guide_placeholders = field_value

                elif field == "tvc_stream_vcodec":
                    if parent['parent_tvc_stream_vcodec_override'] is not None and parent['parent_tvc_stream_vcodec_override'] != '':
                        tvc_stream_vcodec = parent['parent_tvc_stream_vcodec_override']
                    else:
                        tvc_stream_vcodec = field_value

                elif field == "tvc_stream_acodec":
                    if parent['parent_tvc_stream_acodec_override'] is not None and parent['parent_tvc_stream_acodec_override'] != '':
                        tvc_stream_acodec = parent['parent_tvc_stream_acodec_override']
                    else:
                        tvc_stream_acodec = field_value

                elif field == "url":
                    url = field_value

                elif field == "stream_format":
                    stream_format = field_value

            if url:
                title = parent['parent_title']
                tvc_guide_title = title

                if parent['parent_channel_number_override'] is not None and parent['parent_channel_number_override'] != '':
                    tvg_chno = parent['parent_channel_number_override']
                else:
                    tvg_chno = int(channel_id.split('_')[-1]) + int(station_start_number)
                
                channel_number = tvg_chno

            if title:
                final_m3us.append({
                    "title": title,
                    "tvc_guide_title": tvc_guide_title,
                    "channel_id": channel_id,
                    "tvg_id": tvg_id,
                    "tvg_name": tvg_name,
                    "tvg_logo": tvg_logo,
                    "tvg_chno": tvg_chno,
                    "channel_number": channel_number,
                    "tvg_description": tvg_description,
                    "tvc_guide_description": tvc_guide_description,
                    "group_title": group_title,
                    "tvc_guide_stationid": tvc_guide_stationid,
                    "tvc_guide_art": tvc_guide_art,
                    "tvc_guide_tags": tvc_guide_tags,
                    "tvc_guide_genres": tvc_guide_genres,
                    "tvc_guide_categories": tvc_guide_categories,
                    "tvc_guide_placeholders": tvc_guide_placeholders,
                    "tvc_stream_vcodec": tvc_stream_vcodec,
                    "tvc_stream_acodec": tvc_stream_acodec,
                    "url": url,
                    "stream_format": stream_format
                })
    
    gracenote_hls_final_m3us = []
    gracenote_mpeg_ts_final_m3us = []
    gracenote_strmlnk_final_m3us = []
    epg_hls_final_m3us = []
    epg_mpeg_ts_final_m3us = []
    epg_strmlnk_final_m3us = []

    for final_m3u in final_m3us:
        if final_m3u['tvc_guide_stationid'] is not None and final_m3u['tvc_guide_stationid'] != '':
            if final_m3u['stream_format'] == "HLS":
                gracenote_hls_final_m3us.append(final_m3u)
            elif final_m3u['stream_format'] == "MPEG-TS":
                gracenote_mpeg_ts_final_m3us.append(final_m3u)
            elif final_m3u['stream_format'] == "STRMLNK":
                gracenote_strmlnk_final_m3us.append(final_m3u)
        else:
            if final_m3u['stream_format'] == "HLS":
                epg_hls_final_m3us.append(final_m3u)
            elif final_m3u['stream_format'] == "MPEG-TS":
                epg_mpeg_ts_final_m3us.append(final_m3u)
            elif final_m3u['stream_format'] == "STRMLNK":
                epg_strmlnk_final_m3us.append(final_m3u)

    extensions = ['m3u']
    all_prior_files = []
    all_prior_files = get_all_prior_files(program_files_dir, extensions)
    for all_prior_file in all_prior_files:
        file_delete(program_files_dir, all_prior_file['filename'], all_prior_file['extension'])

    create_chunk_files(gracenote_hls_final_m3us, "plm_gracenote_hls_m3u", "m3u", max_stations)
    create_chunk_files(gracenote_mpeg_ts_final_m3us, "plm_gracenote_mpeg_ts_m3u", "m3u", max_stations)
    create_chunk_files(gracenote_strmlnk_final_m3us, "plm_gracenote_strmlnk_m3u", "m3u", max_stations)
    create_chunk_files(epg_hls_final_m3us, "plm_epg_hls_m3u", "m3u", max_stations)
    create_chunk_files(epg_mpeg_ts_final_m3us, "plm_epg_mpeg_ts_m3u", "m3u", max_stations)
    create_chunk_files(epg_strmlnk_final_m3us, "plm_epg_strmlnk_m3u", "m3u", max_stations)
    get_epgs_for_m3us()

    notification_add(f"{current_time()} Finished generation of final m3u(s) and XML EPG(s).")

# Runs through all the records to find a valid value to return
def get_m3u_field_value(field, combined_children, children):
    field_original = None
    field_value = None

    if field == "stream_format":
        field_original = field
        field = "url"

    for child in children:
        for combined_child in combined_children:
            check_m3u_id_channel_id = f"{combined_child['m3u_id']}_{combined_child['channel_id']}"
            if child['child_m3u_id_channel_id'] == check_m3u_id_channel_id:
                if combined_child[field] is None or combined_child[field] == '':
                    pass

                else:

                    if field_original == "stream_format":

                        if child['stream_format_override'] == "None":

                            playlists = read_data(csv_playlistmanager_playlists)
                            for playlist in playlists:
                                if playlist['m3u_id'] == combined_child['m3u_id']:
                                    if child['child_station_check'] is None or child['child_station_check'] == '' or child['child_station_check'] == playlist['stream_format']:
                                        field_value = playlist['stream_format']
                                    else:
                                        field_value = child['child_station_check']
                                    break

                        else:
                            field_value = child['stream_format_override']

                    else:
                        field_value = combined_child[field]

                    break

        if field_value:
            break

    return field_value

# Generates m3u content from the data list
def generate_m3u_content(data_list, base_filename, index):
    settings = read_data(csv_settings)
    plm_url_tag_in_m3us = settings[42]['settings']                              # [42] PLM: URL Tag in m3u(s) On/Off
    plm_url_tag_in_m3us_preferred_url_root = settings[43]['settings']           # [43] PLM: URL Tag in m3u(s) Preferred URL Root
    xml_guide = f"{plm_url_tag_in_m3us_preferred_url_root}playlists/files/{base_filename}_{index+1:02d}.xml"

    if plm_url_tag_in_m3us == "On" and base_filename.startswith("plm_epg"):
        m3u_content = f"#EXTM3U url-tvg=\"{xml_guide}\"\n"
    else:
        m3u_content = "#EXTM3U\n"
    
    for item in data_list:
        m3u_content += f'\n#EXTINF:-1 tvc-guide-title="{item["tvc_guide_title"]}"'
        m3u_content += f' channel-id="{item["channel_id"]}"'
        m3u_content += f' tvg-id="{item["tvg_id"]}"'
        m3u_content += f' tvg-name="{item["tvg_name"]}"'
        m3u_content += f' tvg-logo="{item["tvg_logo"]}"'
        m3u_content += f' tvg-chno="{item["tvg_chno"]}"'
        m3u_content += f' channel-number="{item["channel_number"]}"'
        m3u_content += f' tvg-description="{item["tvg_description"]}"'
        m3u_content += f' tvc-guide-description="{item["tvc_guide_description"]}"'
        m3u_content += f' group-title="{item["group_title"]}"'
        m3u_content += f' tvc-guide-stationid="{item["tvc_guide_stationid"]}"'
        m3u_content += f' tvc-guide-art="{item["tvc_guide_art"]}"'
        m3u_content += f' tvc-guide-tags="{item["tvc_guide_tags"]}"'
        m3u_content += f' tvc-guide-genres="{item["tvc_guide_genres"]}"'
        m3u_content += f' tvc-guide-categories="{item["tvc_guide_categories"]}"'
        m3u_content += f' tvc-guide-placeholders="{item["tvc_guide_placeholders"]}"'
        m3u_content += f' tvc-stream-vcodec="{item["tvc_stream_vcodec"]}"'
        m3u_content += f' tvc-stream-acodec="{item["tvc_stream_acodec"]}"'
        m3u_content += f',{item["title"]}\n'
        m3u_content += f'{item["url"]}\n'

    m3u_content = m3u_content.replace('"None"', '""')

    return m3u_content

# Wrapper for getting m3u and XML EPG files
def get_playlist_files():
    extensions = ['m3u', 'xml']
    all_prior_files = get_all_prior_files(program_files_dir, extensions)

    playlist_files = []
    for all_prior_file in all_prior_files:
        playlist_extension = all_prior_file['extension']
        playlist_filename = f"{all_prior_file['filename']}.{playlist_extension}"
        playlist_number = all_prior_file['filename'].split('_')[-1]

        station_count = None
        station_word = None
        playlist_label = None

        if playlist_extension == "m3u":
            with open(full_path(playlist_filename), 'r', encoding='utf-8') as file:
                content = file.read()
            station_count = content.count("channel-id")
            if int(station_count) > 1:
                station_word = "Stations"
            else:
                station_word = "Station"

            if 'gracenote_' in playlist_filename:
                if 'hls' in playlist_filename:
                    playlist_label = f"m3u Playlist - Gracenote (HLS) [{playlist_number}] ({station_count} {station_word}): "
                elif 'mpeg_ts' in playlist_filename:
                    playlist_label = f"m3u Playlist - Gracenote (MPEG-TS) [{playlist_number}] ({station_count} {station_word}): "
                elif 'strmlnk' in playlist_filename:
                    playlist_label = f"m3u Playlist - Gracenote (STRMLNK) [{playlist_number}] ({station_count} {station_word}): "

            elif 'epg_' in playlist_filename:
                if 'hls' in playlist_filename:
                    playlist_label = f"m3u Playlist - Non-Gracenote (HLS) [{playlist_number}] ({station_count} {station_word}): "
                elif 'mpeg_ts' in playlist_filename:
                    playlist_label = f"m3u Playlist - Non-Gracenote (MPEG-TS) [{playlist_number}] ({station_count} {station_word}): "
                elif 'strmlnk' in playlist_filename:
                    playlist_label = f"m3u Playlist - Non-Gracenote (STRMLNK) [{playlist_number}] ({station_count} {station_word}): "

        elif playlist_extension == "xml":
            if 'epg_' in playlist_filename:
                if 'hls' in playlist_filename:
                    playlist_label = f"XML EPG for Non-Gracenote (HLS) [{playlist_number}]: "
                elif 'mpeg_ts' in playlist_filename:
                    playlist_label = f"XML EPG for Non-Gracenote (MPEG-TS) [{playlist_number}]: "
                elif 'strmlnk' in playlist_filename:
                    playlist_label = f"XML EPG for Non-Gracenote (STRMLNK) [{playlist_number}]: "

        playlist_files.append({'playlist_label': playlist_label, 'playlist_filename': playlist_filename})
        
    playlist_files = sorted(playlist_files, key=lambda x: (not "gracenote" in x['playlist_filename'], x['playlist_filename']))
    return playlist_files

# Wrapper for getting uploaded and generated m3u and XML EPG files
def get_uploaded_playlist_files():
    extensions = ['m3u', 'xml', 'gz', 'm3u8']
    all_prior_files = get_all_prior_files(playlists_uploads_dir, extensions)

    playlist_files = []
    for all_prior_file in all_prior_files:
        playlist_extension = all_prior_file['extension']
        playlist_filename = f"{all_prior_file['filename']}.{playlist_extension}"

        if playlist_extension == 'xml':
            playlist_filetype = "Uploaded Guide Data (Standard)"

        elif playlist_extension == 'gz':
            playlist_filetype = "Uploaded Guide Data (Compressed)"

        elif 'plmss' in playlist_filename:

            playlist_number = playlist_filename.split('_')[-1].split('.')[0]

            if playlist_number:

                if 'hls' in playlist_filename:
                    playlist_type = 'HLS'
                elif 'mpeg_ts' in playlist_filename:
                    playlist_type = 'MPEG-TS'
                elif 'strmlnk' in playlist_filename:
                    playlist_type = 'STRMLNK'

                if 'plmss_' in playlist_filename:
                    playlist_name_base = f"Streaming Stations"

                playlist_filetype = f"PLM - {playlist_name_base} ({playlist_type}) [{playlist_number}]"

        else:
            playlist_filetype = "Uploaded Playlist"

        playlist_files.append({
            'file_type': playlist_filetype,
            'file_link': playlist_filename
            })
    
    settings = read_data(csv_settings)
    plm_internal_pbs_stations = settings[48]['settings']                        # [48] PLM: Internal PBS Stations On/Off

    if plm_internal_pbs_stations == "On":
        playlist_files.append({
            'file_type': "PLM - PBS Stations (MPEG-TS) [01]",
            'file_link': "internal/plmint_pbs_mpeg_ts_m3u_01.m3u"
        })

    playlist_files = sorted(playlist_files, key=lambda x: sort_key(x['file_type'].casefold()))
    return playlist_files

# Gets the XML EPG for each m3u that needs one
def get_epgs_for_m3us():
    temp_content = get_combined_xml_guide()

    extensions = ['m3u']
    m3u_files = get_all_prior_files(program_files_dir, extensions)

    # Filter the list to include only values that contain '_epg_'
    filtered_files = [filtered_file for filtered_file in m3u_files if '_epg_' in filtered_file['filename']]

    for filtered_file in filtered_files:
        tvg_ids = []  # Reset the list for each playlist
        channel_patterns = []
        programme_patterns = []
        all_patterns = []
        playlist_extension = filtered_file['extension']
        playlist_filename = f"{filtered_file['filename']}.{playlist_extension}"
        epg_filename = f"{filtered_file['filename']}.xml"
        epg_filename_tmp = f"{epg_filename}.tmp"

        # Read the M3U file content
        with open(full_path(playlist_filename), "r", encoding="utf-8") as file:
            content = file.read()
            # Extract tvg-id values
            tvg_ids.extend(re.findall(r'tvg-id="(.*?)"', content))

        # Write the EPG data to a variable
        epg_content = [
            "<?xml version='1.0' encoding='utf-8'?>",
            "<!DOCTYPE tv SYSTEM \"xmltv.dtd\">",
            "<tv generator-info-name=\"SLM\" generated-ts=\"\">"
        ]

        # Extract relevant sections from temp_content
        for tvg_id in tvg_ids:
            channel_patterns.append(re.compile(rf'<channel\b[^>]*\bid="{tvg_id}"[^>]*>.*?</channel>', re.DOTALL))
            programme_patterns.append(re.compile(rf'<programme\b[^>]*\bchannel="{tvg_id}"[^>]*>.*?</programme>', re.DOTALL))
        all_patterns = channel_patterns + programme_patterns

        for all_pattern in all_patterns:
            for match in all_pattern.finditer(temp_content):
                epg_content.append("  " + match.group(0))  # 2 spaces for indentation
            time.sleep(0.2)  # Small delay between processing each pattern to release system resources

        # Write the closing tag
        epg_content.append("</tv>")

        # Write the EPG content to the physical file
        with open(full_path(epg_filename_tmp), "w", encoding="utf-8") as epg_file:
            epg_file.write("\n".join(epg_content))

    extensions = ['xml']
    all_prior_files = get_all_prior_files(program_files_dir, extensions)
    for all_prior_file in all_prior_files:
        file_delete(program_files_dir, all_prior_file['filename'], all_prior_file['extension'])

    rename_files_suffix(program_files_dir, ".xml.tmp", ".xml")

# Combines all XML EPGs into one large XML guide
def get_combined_xml_guide():
    playlists = read_data(csv_playlistmanager_playlists)
    temp_content = ""

    # Fetch EPG XML data
    for playlist in playlists:
        if playlist['m3u_active'] == "On" and playlist['epg_xml']:
            response = fetch_url(playlist['epg_xml'], 5, 10)
            if response:
                # Get the final URL after redirection
                final_url = response.url

                # Handle .gz files
                if final_url.endswith('.gz'):
                    gz = gzip.GzipFile(fileobj=io.BytesIO(response.content))
                    response_text = gz.read().decode('utf-8')
                else:
                    response_text = response.content.decode('utf-8')

                temp_content += response_text

    return temp_content

# More parent station settings
@app.route('/playlists/plm_parent_stations_more', methods=['GET', 'POST'])
def webpage_playlists_parent_stations_more():
    global parent_channel_id_prior

    preferred_playlists = []
    preferred_playlists_default = [
        {'m3u_id': 'None', 'prefer_name': 'None'}    ]
    preferred_playlists = get_preferred_playlists(preferred_playlists_default)

    parents = read_data(csv_playlistmanager_parents)
    parent_title = ''
    parent_tvg_id_override = ''
    parent_tvg_logo_override = ''
    parent_channel_number_override = ''
    parent_tvc_guide_stationid_override = ''
    parent_tvc_guide_art_override = ''
    parent_tvc_guide_tags_override = ''
    parent_tvc_guide_genres_override = ''
    parent_tvc_guide_categories_override = ''
    parent_tvc_guide_placeholders_override = ''
    parent_tvc_stream_vcodec_override = ''
    parent_tvc_stream_acodec_override = ''
    parent_preferred_playlist = ''
    parent_active = ''
    parent_tvg_description_override = ''
    parent_group_title_override = ''

    if parent_channel_id_prior:
        for parent in parents:
            if parent['parent_channel_id'] == parent_channel_id_prior:
                parent_title = parent['parent_title']
                parent_tvg_id_override = parent['parent_tvg_id_override']
                parent_tvg_logo_override = parent['parent_tvg_logo_override']
                parent_channel_number_override = parent['parent_channel_number_override']
                parent_tvc_guide_stationid_override = parent['parent_tvc_guide_stationid_override']
                parent_tvc_guide_art_override = parent['parent_tvc_guide_art_override']
                parent_tvc_guide_tags_override = parent['parent_tvc_guide_tags_override']
                parent_tvc_guide_genres_override = parent['parent_tvc_guide_genres_override']
                parent_tvc_guide_categories_override = parent['parent_tvc_guide_categories_override']
                parent_tvc_guide_placeholders_override = parent['parent_tvc_guide_placeholders_override']
                parent_tvc_stream_vcodec_override = parent['parent_tvc_stream_vcodec_override']
                parent_tvc_stream_acodec_override = parent['parent_tvc_stream_acodec_override']
                parent_preferred_playlist = parent['parent_preferred_playlist']
                parent_active = parent['parent_active']
                parent_tvg_description_override = parent['parent_tvg_description_override']
                parent_group_title_override = parent['parent_group_title_override']
                break

    if request.method == 'POST':
        action = request.form['action']

        if action.endswith('_cancel'):
            parent_channel_id_prior = None
            parent_title = ''
            parent_tvg_id_override = ''
            parent_tvg_logo_override = ''
            parent_channel_number_override = ''
            parent_tvc_guide_stationid_override = ''
            parent_tvc_guide_art_override = ''
            parent_tvc_guide_tags_override = ''
            parent_tvc_guide_genres_override = ''
            parent_tvc_guide_categories_override = ''
            parent_tvc_guide_placeholders_override = ''
            parent_tvc_stream_vcodec_override = ''
            parent_tvc_stream_acodec_override = ''
            parent_preferred_playlist = ''
            parent_active = ''
            parent_tvg_description_override = ''
            parent_group_title_override = ''

        elif action.endswith('_save') or action.endswith('_edit'):
            parent_channel_id_input = request.form.get('more_parent_channel_id')
            parent_channel_id_prior = parent_channel_id_input

            if action.endswith('_edit'):

                for parent in parents:
                    if parent['parent_channel_id'] == parent_channel_id_prior:
                        parent_title = parent['parent_title']
                        parent_tvg_id_override = parent['parent_tvg_id_override']
                        parent_tvg_logo_override = parent['parent_tvg_logo_override']
                        parent_channel_number_override = parent['parent_channel_number_override']
                        parent_tvc_guide_stationid_override = parent['parent_tvc_guide_stationid_override']
                        parent_tvc_guide_art_override = parent['parent_tvc_guide_art_override']
                        parent_tvc_guide_tags_override = parent['parent_tvc_guide_tags_override']
                        parent_tvc_guide_genres_override = parent['parent_tvc_guide_genres_override']
                        parent_tvc_guide_categories_override = parent['parent_tvc_guide_categories_override']
                        parent_tvc_guide_placeholders_override = parent['parent_tvc_guide_placeholders_override']
                        parent_tvc_stream_vcodec_override = parent['parent_tvc_stream_vcodec_override']
                        parent_tvc_stream_acodec_override = parent['parent_tvc_stream_acodec_override']
                        parent_preferred_playlist = parent['parent_preferred_playlist']
                        parent_active = parent['parent_active']
                        parent_tvg_description_override = parent['parent_tvg_description_override']
                        parent_group_title_override = parent['parent_group_title_override']
                        break

            elif action.endswith('_save'):

                parent_title_input = request.form.get('more_parent_title')
                parent_tvg_id_override_input = request.form.get('more_parent_tvg_id_override')
                parent_tvg_logo_override_input = request.form.get('more_parent_tvg_logo_override')
                parent_channel_number_override_input = request.form.get('more_parent_channel_number_override')
                parent_tvc_guide_stationid_override_input = request.form.get('more_parent_tvc_guide_stationid_override')
                parent_tvc_guide_art_override_input = request.form.get('more_parent_tvc_guide_art_override')
                parent_tvc_guide_tags_override_input = request.form.get('more_parent_tvc_guide_tags_override')
                parent_tvc_guide_genres_override_input = request.form.get('more_parent_tvc_guide_genres_override')
                parent_tvc_guide_categories_override_input = request.form.get('more_parent_tvc_guide_categories_override')
                parent_tvc_guide_placeholders_override_input = request.form.get('more_parent_tvc_guide_placeholders_override')
                parent_tvc_stream_vcodec_override_input = request.form.get('more_parent_tvc_stream_vcodec_override')
                parent_tvc_stream_acodec_override_input = request.form.get('more_parent_tvc_stream_acodec_override')
                parent_preferred_playlist_input = request.form.get('more_parent_preferred_playlist')
                if parent_preferred_playlist_input == "None":
                    parent_preferred_playlist_input = None
                parent_active_input = "On" if request.form.get('more_parent_active') == 'on' else "Off"
                parent_tvg_description_override_input = request.form.get('more_parent_tvg_description_override')
                parent_group_title_override_input = request.form.get('more_parent_group_title_override')

                for parent in parents:
                    if parent['parent_channel_id'] == parent_channel_id_prior:
                        parent['parent_title'] = parent_title_input
                        parent['parent_tvg_id_override'] = parent_tvg_id_override_input
                        parent['parent_tvg_logo_override'] = parent_tvg_logo_override_input
                        parent['parent_channel_number_override'] = parent_channel_number_override_input
                        parent['parent_tvc_guide_stationid_override'] = parent_tvc_guide_stationid_override_input
                        parent['parent_tvc_guide_art_override'] = parent_tvc_guide_art_override_input
                        parent['parent_tvc_guide_tags_override'] = parent_tvc_guide_tags_override_input
                        parent['parent_tvc_guide_genres_override'] = parent_tvc_guide_genres_override_input
                        parent['parent_tvc_guide_categories_override'] = parent_tvc_guide_categories_override_input
                        parent['parent_tvc_guide_placeholders_override'] = parent_tvc_guide_placeholders_override_input
                        parent['parent_tvc_stream_vcodec_override'] = parent_tvc_stream_vcodec_override_input
                        parent['parent_tvc_stream_acodec_override'] = parent_tvc_stream_acodec_override_input
                        parent['parent_preferred_playlist'] = parent_preferred_playlist_input
                        parent['parent_active'] = parent_active_input
                        parent['parent_tvg_description_override'] = parent_tvg_description_override_input
                        parent['parent_group_title_override'] = parent_group_title_override_input
                        break

                parents = sorted(parents, key=lambda x: sort_key(x["parent_title"].casefold()))
                write_data(csv_playlistmanager_parents, parents)
                parents = read_data(csv_playlistmanager_parents)

                for parent in parents:
                    if parent['parent_channel_id'] == parent_channel_id_prior:
                        parent_title = parent['parent_title']
                        parent_tvg_id_override = parent['parent_tvg_id_override']
                        parent_tvg_logo_override = parent['parent_tvg_logo_override']
                        parent_channel_number_override = parent['parent_channel_number_override']
                        parent_tvc_guide_stationid_override = parent['parent_tvc_guide_stationid_override']
                        parent_tvc_guide_art_override = parent['parent_tvc_guide_art_override']
                        parent_tvc_guide_tags_override = parent['parent_tvc_guide_tags_override']
                        parent_tvc_guide_genres_override = parent['parent_tvc_guide_genres_override']
                        parent_tvc_guide_categories_override = parent['parent_tvc_guide_categories_override']
                        parent_tvc_guide_placeholders_override = parent['parent_tvc_guide_placeholders_override']
                        parent_tvc_stream_vcodec_override = parent['parent_tvc_stream_vcodec_override']
                        parent_tvc_stream_acodec_override = parent['parent_tvc_stream_acodec_override']
                        parent_preferred_playlist = parent['parent_preferred_playlist']
                        parent_active = parent['parent_active']
                        parent_tvg_description_override = parent['parent_tvg_description_override']
                        parent_group_title_override = parent['parent_group_title_override']
                        break                

    return render_template(
        'main/playlists_parent_stations_more.html',
        segment = 'plm_parent_stations_more',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_parents = parents,
        html_parent_channel_id_prior = parent_channel_id_prior,
        html_parent_title = parent_title,
        html_parent_tvg_id_override = parent_tvg_id_override,
        html_parent_tvg_logo_override = parent_tvg_logo_override,
        html_parent_channel_number_override = parent_channel_number_override,
        html_parent_tvc_guide_stationid_override = parent_tvc_guide_stationid_override,
        html_parent_tvc_guide_art_override = parent_tvc_guide_art_override,
        html_parent_tvc_guide_tags_override = parent_tvc_guide_tags_override,
        html_parent_tvc_guide_genres_override = parent_tvc_guide_genres_override,
        html_parent_tvc_guide_categories_override = parent_tvc_guide_categories_override,
        html_parent_tvc_guide_placeholders_override = parent_tvc_guide_placeholders_override,
        html_parent_tvc_stream_vcodec_override = parent_tvc_stream_vcodec_override,
        html_parent_tvc_stream_acodec_override = parent_tvc_stream_acodec_override,
        html_parent_preferred_playlist = parent_preferred_playlist,
        html_parent_active = parent_active,
        html_parent_tvg_description_override = parent_tvg_description_override,
        html_parent_group_title_override = parent_group_title_override,
        html_preferred_playlists = preferred_playlists
    )

# Add streaming stations from particular sources
@app.route('/playlists/streams', methods=['GET', 'POST'])
def webpage_playlists_streams():
    global streaming_stations_source_test_prior
    global streaming_stations_url_test_prior
    global filter_streams_source
    global filter_streams_url
    global filter_streams_title
    global filter_streams_tvg_logo
    global filter_streams_tvg_description
    global filter_streams_tvc_guide_tags
    global filter_streams_tvc_guide_genres
    global filter_streams_tvc_guide_categories
    global filter_streams_tvc_guide_placeholders
    global filter_streams_tvc_stream_vcodec
    global filter_streams_tvc_stream_acodec

    settings = read_data(csv_settings)
    plm_streaming_stations_station_start_number = settings[40]['settings']      # [40] PLM: Streaming Stations Starting station number
    plm_streaming_stations_max_stations = settings[41]['settings']              # [41] PLM: Streaming Stations Max number of stations per m3u
    settings_message = ''

    streaming_stations = read_data(csv_playlistmanager_streaming_stations)

    streaming_station_options = [
        "Custom (HLS)",
        "Custom (MPEG-TS)",
        "Stream Link (STRMLNK)",
        "Live Stream (HLS)",
        "Live Stream (MPEG-TS)"
    ]

    test_url = ''
    run_empty_row = None

    if request.method == 'POST':
        action = request.form['action']

        if action.endswith('settings'):

            if action == 'plm_streaming_stations_save_settings':
                plm_streaming_stations_station_start_number_input = request.form.get('plm_streaming_stations_station_start_number')
                plm_streaming_stations_max_stations_input = request.form.get('plm_streaming_stations_max_stations')

                try:
                    if int(plm_streaming_stations_station_start_number_input) > 0 and int(plm_streaming_stations_max_stations_input) > 0:
                        settings[40]['settings'] = int(plm_streaming_stations_station_start_number_input)
                        settings[41]['settings'] = int(plm_streaming_stations_max_stations_input)

                    else:
                        settings_message = f"{current_time()} ERROR: For Streaming Stations, 'Station Start Number' and 'Max Stations per m3u' must be positive integers."
                
                except ValueError:
                    settings_message = f"{current_time()} ERROR: For Streaming Stations, 'Station Start Number' and 'Max Stations per m3u' must be numbers."

                write_data(csv_settings, settings)
                settings = read_data(csv_settings)
                plm_streaming_stations_station_start_number = settings[40]['settings']      # [40] PLM: Streaming Stations Starting station number
                plm_streaming_stations_max_stations = settings[41]['settings']              # [41] PLM: Streaming Stations Max number of stations per m3u

        elif action.endswith('test'):
            streaming_stations_source_test_input = request.form.get('streaming_stations_source_test')
            streaming_stations_url_test_input = request.form.get('streaming_stations_url_test')

            streaming_stations_source_test_prior = streaming_stations_source_test_input
            streaming_stations_url_test_prior = streaming_stations_url_test_input

            if streaming_stations_url_test_input is not None and streaming_stations_url_test_input != '':
                if streaming_stations_source_test_input.startswith('Custom'):
                    test_url = streaming_stations_url_test_input

                elif streaming_stations_source_test_input == 'Live Stream (HLS)':
                    test_url = f"{request.url_root}playlists/streams/stream?url={streaming_stations_url_test_input}"

                elif streaming_stations_source_test_input == 'Live Stream (MPEG-TS)':
                    test_url = f"{request.url_root}playlists/streams/stream_mpegts?url={streaming_stations_url_test_input}"

        elif action.endswith('new') or action.endswith('save') or 'delete' in action:
            filter_streams_source = request.form.get('filter-source')
            filter_streams_url = request.form.get('filter-url')
            filter_streams_title = request.form.get('filter-title')
            filter_streams_tvg_logo = request.form.get('filter-tvg-logo')
            filter_streams_tvg_description = request.form.get('filter-tvg-description')
            filter_streams_tvc_guide_tags = request.form.get('filter-tvc-guide-tags')
            filter_streams_tvc_guide_genres = request.form.get('filter-tvc-guide-genres')
            filter_streams_tvc_guide_categories = request.form.get('filter-tvc-guide-categories')
            filter_streams_tvc_guide_placeholders = request.form.get('filter-tvc-guide-placeholders')
            filter_streams_tvc_stream_vcodec = request.form.get('filter-tvc-stream-vcodec')
            filter_streams_tvc_stream_acodec = request.form.get('filter-tvc-stream-acodec')

            streaming_stations_channel_id_input = None
            streaming_stations_source_input = None
            streaming_stations_url_input = None
            streaming_stations_title_input = None
            streaming_stations_tvg_logo_input = None
            streaming_stations_tvg_description_input = None
            streaming_stations_tvc_guide_tags_input = None
            streaming_stations_tvc_guide_genres_input = None
            streaming_stations_tvc_guide_categories_input = None
            streaming_stations_tvc_guide_placeholders_input = None
            streaming_stations_tvc_stream_vcodec_input = None
            streaming_stations_tvc_stream_acodec_input = None

            if action.endswith('save') or 'delete' in action:

                streaming_stations_channel_id_inputs = {}
                streaming_stations_source_inputs = {}
                streaming_stations_url_inputs = {}
                streaming_stations_title_inputs = {}
                streaming_stations_tvg_logo_inputs = {}
                streaming_stations_tvg_description_inputs = {}
                streaming_stations_tvc_guide_tags_inputs = {}
                streaming_stations_tvc_guide_genres_inputs = {}
                streaming_stations_tvc_guide_categories_inputs = {}
                streaming_stations_tvc_guide_placeholders_inputs = {}
                streaming_stations_tvc_stream_vcodec_inputs = {}
                streaming_stations_tvc_stream_acodec_inputs = {}

                for key in request.form.keys():
                    if key.startswith('streaming_stations_channel_id_'):
                        index = key.split('_')[-1]
                        streaming_stations_channel_id_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_source_'):
                        index = key.split('_')[-1]
                        streaming_stations_source_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_url_'):
                        index = key.split('_')[-1]
                        streaming_stations_url_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_title_'):
                        index = key.split('_')[-1]
                        streaming_stations_title_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvg_logo_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvg_logo_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvg_description_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvg_description_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvc_guide_tags_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvc_guide_tags_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvc_guide_genres_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvc_guide_genres_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvc_guide_categories_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvc_guide_categories_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvc_guide_placeholders_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvc_guide_placeholders_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvc_stream_vcodec_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvc_stream_vcodec_inputs[index] = request.form.get(key)

                    if key.startswith('streaming_stations_tvc_stream_acodec_'):
                        index = key.split('_')[-1]
                        streaming_stations_tvc_stream_acodec_inputs[index] = request.form.get(key)

                if action.endswith('save'):
                    temp_records = []

                    for row in streaming_stations_channel_id_inputs:
                        streaming_stations_channel_id_input = streaming_stations_channel_id_inputs.get(row)
                        streaming_stations_source_input = streaming_stations_source_inputs.get(row)
                        streaming_stations_url_input = streaming_stations_url_inputs.get(row)
                        streaming_stations_title_input = streaming_stations_title_inputs.get(row)
                        streaming_stations_tvg_logo_input = streaming_stations_tvg_logo_inputs.get(row)
                        streaming_stations_tvg_description_input = streaming_stations_tvg_description_inputs.get(row)
                        streaming_stations_tvc_guide_tags_input = streaming_stations_tvc_guide_tags_inputs.get(row)
                        streaming_stations_tvc_guide_genres_input = streaming_stations_tvc_guide_genres_inputs.get(row)
                        streaming_stations_tvc_guide_categories_input = streaming_stations_tvc_guide_categories_inputs.get(row)
                        streaming_stations_tvc_guide_placeholders_input = streaming_stations_tvc_guide_placeholders_inputs.get(row)
                        streaming_stations_tvc_stream_vcodec_input = streaming_stations_tvc_stream_vcodec_inputs.get(row)
                        streaming_stations_tvc_stream_acodec_input = streaming_stations_tvc_stream_acodec_inputs.get(row)

                        temp_records.append({
                            'channel_id': streaming_stations_channel_id_input,
                            'source': streaming_stations_source_input,
                            'url': streaming_stations_url_input,
                            'title': streaming_stations_title_input,
                            'tvg_logo': streaming_stations_tvg_logo_input,
                            'tvg_description': streaming_stations_tvg_description_input,
                            'tvc_guide_tags': streaming_stations_tvc_guide_tags_input,
                            'tvc_guide_genres': streaming_stations_tvc_guide_genres_input,
                            'tvc_guide_categories': streaming_stations_tvc_guide_categories_input,
                            'tvc_guide_placeholders': streaming_stations_tvc_guide_placeholders_input,
                            'tvc_stream_vcodec': streaming_stations_tvc_stream_vcodec_input,
                            'tvc_stream_acodec': streaming_stations_tvc_stream_acodec_input
                        })

                    for streaming_station in streaming_stations:
                        for temp_record in temp_records:
                            if streaming_station['channel_id'] == temp_record['channel_id']:
                                streaming_station['source'] = temp_record['source']
                                streaming_station['url'] = temp_record['url']
                                streaming_station['title'] = temp_record['title']
                                streaming_station['tvg_logo'] = temp_record['tvg_logo']
                                streaming_station['tvg_description'] = temp_record['tvg_description']
                                streaming_station['tvc_guide_tags'] = temp_record['tvc_guide_tags']
                                streaming_station['tvc_guide_genres'] = temp_record['tvc_guide_genres']
                                streaming_station['tvc_guide_categories'] = temp_record['tvc_guide_categories']
                                streaming_station['tvc_guide_placeholders'] = temp_record['tvc_guide_placeholders']
                                streaming_station['tvc_stream_vcodec'] = temp_record['tvc_stream_vcodec']
                                streaming_station['tvc_stream_acodec'] = temp_record['tvc_stream_acodec']

                elif 'delete' in action:
                    action_delete_index = int(action.split('_')[-1])
                    delete_channel_id = streaming_stations_channel_id_inputs.get(str(action_delete_index))

                    # Create a temporary record with fields set to None
                    temp_record = create_temp_record(streaming_stations[0].keys())

                    if 0 <= action_delete_index < len(streaming_stations) + 1:
                        for streaming_station in streaming_stations:
                            if streaming_station['channel_id'] == delete_channel_id:
                                streaming_stations.remove(streaming_station)
                                break

                        # If the list is now empty, add the temp record to keep headers
                        if not streaming_stations:
                            streaming_stations.append(temp_record)
                            run_empty_row = True

            elif action.endswith('new'):
                    streaming_stations_channel_id_input = f"plmss_{max((int(streaming_station['channel_id'].split('_')[1]) for streaming_station in streaming_stations), default=0) + 1:04d}"
                    streaming_stations_source_input = request.form.get('streaming_stations_source_new')
                    streaming_stations_url_input = request.form.get('streaming_stations_url_new')
                    streaming_stations_title_input = request.form.get('streaming_stations_title_new')
                    streaming_stations_tvg_logo_input = request.form.get('streaming_stations_tvg_logo_new')
                    streaming_stations_tvg_description_input = request.form.get('streaming_stations_tvg_description_new')
                    streaming_stations_tvc_guide_tags_input = request.form.get('streaming_stations_tvc_guide_tags_new')
                    streaming_stations_tvc_guide_genres_input = request.form.get('streaming_stations_tvc_guide_genres_new')
                    streaming_stations_tvc_guide_categories_input = request.form.get('streaming_stations_tvc_guide_categories_new')
                    streaming_stations_tvc_guide_placeholders_input = request.form.get('streaming_stations_tvc_guide_placeholders_new')
                    streaming_stations_tvc_stream_vcodec_input = request.form.get('streaming_stations_tvc_stream_vcodec_new')
                    streaming_stations_tvc_stream_acodec_input = request.form.get('streaming_stations_tvc_stream_acodec_new')

                    streaming_stations.append({
                        'channel_id': streaming_stations_channel_id_input,
                        'source': streaming_stations_source_input,
                        'url': streaming_stations_url_input,
                        'title': streaming_stations_title_input,
                        'tvg_logo': streaming_stations_tvg_logo_input,
                        'tvg_description': streaming_stations_tvg_description_input,
                        'tvc_guide_tags': streaming_stations_tvc_guide_tags_input,
                        'tvc_guide_genres': streaming_stations_tvc_guide_genres_input,
                        'tvc_guide_categories': streaming_stations_tvc_guide_categories_input,
                        'tvc_guide_placeholders': streaming_stations_tvc_guide_placeholders_input,
                        'tvc_stream_vcodec': streaming_stations_tvc_stream_vcodec_input,
                        'tvc_stream_acodec': streaming_stations_tvc_stream_acodec_input
                    })

            if len(streaming_stations) > 1:
                streaming_stations = sorted(streaming_stations, key=lambda x: sort_key(x['title'].casefold()))

            write_data(csv_playlistmanager_streaming_stations, streaming_stations)
            if run_empty_row:
                remove_empty_row(csv_playlistmanager_streaming_stations)
    
            make_streaming_stations_m3us()

        elif action.endswith('cancel'):
            streaming_stations_source_test_prior = ''
            streaming_stations_url_test_prior = ''
            filter_streams_source = ''
            filter_streams_url = ''
            filter_streams_title = ''
            filter_streams_tvg_logo = ''
            filter_streams_tvg_description = ''
            filter_streams_tvc_guide_tags = ''
            filter_streams_tvc_guide_genres = ''
            filter_streams_tvc_guide_categories = ''
            filter_streams_tvc_guide_placeholders = ''
            filter_streams_tvc_stream_vcodec = ''
            filter_streams_tvc_stream_acodec = ''

        streaming_stations = read_data(csv_playlistmanager_streaming_stations)

    return render_template(
        'main/playlists_streams.html',
        segment = 'plm_streams',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_streaming_stations = streaming_stations,
        html_streaming_station_options = streaming_station_options,
        html_streaming_stations_source_test_prior = streaming_stations_source_test_prior,
        html_streaming_stations_url_test_prior = streaming_stations_url_test_prior,
        html_test_url = test_url,
        html_filter_streams_source = filter_streams_source,
        html_filter_streams_url = filter_streams_url,
        html_filter_streams_title = filter_streams_title,
        html_filter_streams_tvg_logo = filter_streams_tvg_logo,
        html_filter_streams_tvg_description = filter_streams_tvg_description,
        html_filter_streams_tvc_guide_tags = filter_streams_tvc_guide_tags,
        html_filter_streams_tvc_guide_genres = filter_streams_tvc_guide_genres,
        html_filter_streams_tvc_guide_categories = filter_streams_tvc_guide_categories,
        html_filter_streams_tvc_guide_placeholders = filter_streams_tvc_guide_placeholders,
        html_filter_streams_tvc_stream_vcodec = filter_streams_tvc_stream_vcodec,
        html_filter_streams_tvc_stream_acodec = filter_streams_tvc_stream_acodec,
        html_plm_streaming_stations_station_start_number = plm_streaming_stations_station_start_number,
        html_plm_streaming_stations_max_stations = plm_streaming_stations_max_stations,
        html_settings_message = settings_message
    )

# Check a Station Status and get additional details
@app.route('/playlists/station_status', methods=['GET', 'POST'])
def webpage_playlists_station_status():
    global station_status_child_m3u_id_channel_id_prior
    global station_status_manual_link_prior
    global station_status_results_prior
    global station_status_message_prior

    settings = read_data(csv_settings)
    plm_station_status_number_attempts = settings[61]['settings']           # [61] PLM/MTM: Check Child Station Status Max Number of Retry Attempts
    plm_station_status_delay_attempts = settings[62]['settings']            # [62] PLM/MTM: Check Child Station Status Retry Delay in Seconds
    plm_station_status_skip_after_fails = settings[63]['settings']          # [63] PLM/MTM: Check Child Station Status Skip Playlist After Fails (0 = Disabled)
    settings_message = ''
    
    station_status_child_m3u_id_channel_id_input = None
    station_status_manual_link_input = None
    
    station_status_selections = [{
        'child_m3u_id_channel_id': 'm3u_0000_manual',
        'station_playlist': 'Manual (Input Link Below)'
    }]
    
    stations = read_data(csv_playlistmanager_combined_m3us)
    stations = sorted(stations, key=lambda x: sort_key(x["station_playlist"].casefold()))
    
    for station in stations:
        station_status_selections.append({
            'child_m3u_id_channel_id': f"{station['m3u_id']}_{station['channel_id']}",
            'station_playlist': station['station_playlist']
        })

    if request.method == 'POST':
        action = request.form['action']

        if action.endswith('settings'):

            if action == 'plm_station_status_save_settings':
                plm_station_status_number_attempts_input = request.form.get('plm_station_status_number_attempts')
                plm_station_status_delay_attempts_input = request.form.get('plm_station_status_delay_attempts')
                plm_station_status_skip_after_fails_input = request.form.get('plm_station_status_skip_after_fails')

                try:
                    if int(plm_station_status_number_attempts_input) > 0 and int(plm_station_status_delay_attempts_input) > 0 and int(plm_station_status_skip_after_fails_input) >= 0:
                        settings[61]['settings'] = int(plm_station_status_number_attempts_input)
                        settings[62]['settings'] = int(plm_station_status_delay_attempts_input)
                        settings[63]['settings'] = int(plm_station_status_skip_after_fails_input)

                    else:
                        settings_message = f"{current_time()} ERROR: For Station Status 'Number of Attempts' and 'Delay Between Attempts' must be positive integers, and 'Skip Playlist After Fails' must be the same or zero to disable."
                
                except ValueError:
                    settings_message = f"{current_time()} ERROR: For Station Status, 'Number of Attempts', 'Delay Between Attempts', and 'Skip Playlist After Fails' must be numbers."

                write_data(csv_settings, settings)
                settings = read_data(csv_settings)
                plm_station_status_number_attempts = settings[61]['settings']           # [61] PLM/MTM: Check Child Station Status Max Number of Retry Attempts
                plm_station_status_delay_attempts = settings[62]['settings']            # [62] PLM/MTM: Check Child Station Status Retry Delay in Seconds
                plm_station_status_skip_after_fails = settings[63]['settings']          # [63] PLM/MTM: Check Child Station Status Skip Playlist After Fails (0 = Disabled)

        if action.startswith('station_status'):
            
            if action.endswith('examine'):
                station_status_child_m3u_id_channel_id_input = request.form.get('station_status_child_m3u_id_channel_id')
                
                if station_status_child_m3u_id_channel_id_input == 'm3u_0000_manual':
                    station_status_manual_link_input = request.form.get('station_status_manual_link')
                    
                get_station_status(station_status_child_m3u_id_channel_id_input, station_status_manual_link_input)

            elif action.endswith('cancel'):
                station_status_child_m3u_id_channel_id_prior = 'm3u_0000_manual'
                station_status_manual_link_prior = ''
                station_status_results_prior = []
                station_status_message_prior = ''

    return render_template(
        'main/playlists_station_status.html',
        segment = 'plm_station_status',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_settings_message = settings_message,
        html_plm_station_status_number_attempts = plm_station_status_number_attempts,
        html_plm_station_status_delay_attempts = plm_station_status_delay_attempts,
        html_plm_station_status_skip_after_fails = plm_station_status_skip_after_fails,
        html_station_status_selections = station_status_selections,
        html_station_status_child_m3u_id_channel_id_prior = station_status_child_m3u_id_channel_id_prior,
        html_station_status_manual_link_prior = station_status_manual_link_prior,
        html_station_status_results_prior = station_status_results_prior,
        html_station_status_message_prior = station_status_message_prior
    )

# Gets the Station Status for a single child station
def get_station_status(station_status_child_m3u_id_channel_id_input, station_status_manual_link_input):
    global station_status_child_m3u_id_channel_id_prior
    global station_status_manual_link_prior
    global station_status_results_prior
    global station_status_message_prior

    station_status_results_input = []
    station_status_message_input = ''

    if station_status_child_m3u_id_channel_id_input:
        
        if station_status_manual_link_input is None or station_status_manual_link_input == '':
            if station_status_child_m3u_id_channel_id_input == 'm3u_0000_manual':
                station_status_manual_link_input = "You must enter a link to use the 'Manual' examination"
            else:
                station_status_manual_link_input = ''
                
        station_status_manual_link_prior = station_status_manual_link_input
            
        station_status_results_input, station_status_message_input = check_child_station_status(station_status_child_m3u_id_channel_id_input, station_status_manual_link_input)

    station_status_child_m3u_id_channel_id_prior = station_status_child_m3u_id_channel_id_input
    
    if station_status_results_input:                      
        station_status_results_prior = station_status_results_input    
    else:
        station_status_results_prior = []

    if station_status_message_input:
        station_status_message_prior = station_status_message_input
    else:
        station_status_message_prior = ''

# Creates an m3u8 or video file for an individual live stream (HLS) or static video
@app.route('/playlists/streams/stream', methods=['GET'])
@app.route('/playlists/streams/youtubelive', methods=['GET']) # Old method, to be removed in the future
def streams_live():
    response = "URL is required"
    url = request.args.get('url', type=str)

    if url:
    
        sanitized_url = sanitize_name(url)

        m3u8_url, m3u8_protocol, info_dict = get_online_video(url, "all")
        
        if m3u8_url:
            
            if m3u8_protocol == 'm3u8':
                filename = f"{sanitized_url}.m3u8"
                playlist = f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n"
                response = Response(playlist, content_type='application/vnd.apple.mpegurl')

            elif m3u8_protocol == 'm3u8_combined':
                filename = f"{sanitized_url}_combined.m3u8"
                response = Response(m3u8_url, content_type='application/vnd.apple.mpegurl')

            elif m3u8_protocol == 'http':
                filename = f"{sanitized_url}.mp4"
                response = Response(stream_with_context(stream_video(m3u8_url)), content_type='video/mp4')

            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'        
        
        else:
            response = f"Failed to retrieve manifest for URL {url}"

    return response

# Streams the video content from the URL
def stream_video(url):
    with requests.get(url, stream=True) as r:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

# Gets the manifest needed for the live stream or static video
def get_online_video(url, parse_type):
    print(f"{current_time()} INFO: Starting to retrieve manifest for {url}.")

    youtube_player_clients = ['web_safari', 'web']

    m3u8_url = None
    m3u8_protocol = None
    info_dict = {}

    for youtube_player_client in youtube_player_clients:

        ydl_opts = {
            'verbose': True,                                        # Get verbose output
            'no_warnings': False,                                   # Show warnings
            'format': 'all',                                        # Check all formats
            'retries': 0,                                           # Retry up to 0 times in case of failure
            'fragment_retries': 0,                                  # Retry up to 0 times for each fragment
            'logger': YTDLLogger(),                                 # Pass the custom logger
            'extractor_args': {                                     # Set extractor arguments for specific websites
                'youtube': {
                    'player_client': [youtube_player_client],       # Force player API client to specific client(s) in order to speed up finding a compatible format
                    'formats': ['missing_pot'],                     # Stop testing for PO token
                    'player_skip': ['configs', 'webpage', 'js'],    # Skip player configuration, webpage, and JavaScript
                    'skip': ['dash', 'translated_subs']             # Skip DASH manifests and translated subtitles
                }
            }
        }

        m3u8_url, m3u8_protocol, info_dict = parse_online_video(url, ydl_opts, parse_type)

        if (m3u8_url and m3u8_protocol) or (not 'youtu' in url) or (parse_type == "metadata"):
            break

    return m3u8_url, m3u8_protocol, info_dict

# Parses a URL to extract and select the optimal video or audio stream based on language preferences
def parse_online_video(url, ydl_opts, parse_type):
    settings = read_data(csv_settings)
    country_code = settings[2]["settings"]
    language_code = settings[3]["settings"]
    language_country_code = f"{language_code}-{country_code}"

    language_preferences = [
        language_country_code.strip().lower(),
        language_code.strip().lower()
    ]

    m3u8_url = None
    m3u8_protocol = None
    info_dict = {}
    formats = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"{current_time()} INFO: Extracting info from {url}...")
            info_dict, formats = parse_online_video_info_dict_formats(ydl, url, parse_type)

            if info_dict and not formats and parse_type == "all":
                url_override = info_dict.get("url")
                if url_override:
                    print(f"{current_time()} INFO: URL redirected to {url_override}.")
                    info_dict, formats = parse_online_video_info_dict_formats(ydl, url_override, parse_type)

            if info_dict:
                print(f"{current_time()} INFO: Extraction successful for {url}.")
                if parse_type == "all":
                    
                    if formats:
                        print(f"{current_time()} INFO: Found {len(formats)} formats.")

                        protocol_m3u8_formats = []
                        protocol_http_formats = []
                        audio_formats = []
                        video_formats = []

                        for format in formats:
                            # print(f"{current_time()} INFO: Found format: {format}") # Keep this for testing but not production

                            if format.get("has_drm") is False:
                                acodec = format.get("acodec")
                                vcodec = format.get("vcodec")
                                protocol = format.get("protocol", "")

                                if acodec != "none" and vcodec != "none":
                                    if "m3u8" in protocol:
                                        protocol_m3u8_formats.append(format)
                                    elif "http" in protocol:
                                        protocol_http_formats.append(format)

                                elif acodec == "none" and vcodec != "none":
                                    video_formats.append(format)

                                else:
                                    audio_formats.append(format)

                        best_format = parse_online_video_formats(protocol_m3u8_formats, language_preferences)
                        if best_format:
                            m3u8_protocol = "m3u8"
                            m3u8_url = best_format.get("url")
                            print(f"{current_time()} INFO: Best format URL found using m3u8: {m3u8_url}")

                        else:
                            best_format = parse_online_video_formats(protocol_http_formats, language_preferences)
                            if best_format:
                                m3u8_protocol = "http"
                                m3u8_url = best_format.get("url")
                                print(f"{current_time()} INFO: Best format URL found using http: {m3u8_url}")

                        if not best_format and video_formats and audio_formats:
                            print(f"{current_time()} INFO: No single-stream found. Combining audio + video tracks.")
                            best_video = parse_online_video_formats(video_formats, language_preferences)

                            sorted_audio_formats = sorted(
                                audio_formats,
                                key=lambda f: (
                                    language_preferences.index((f.get("language") or "").strip().lower())
                                    if (f.get("language") or "").strip().lower() in language_preferences
                                    else len(language_preferences)
                                )
                            )

                            manifest_lines = ["#EXTM3U"]
                            manifest_lines.append(
                                f'#EXT-X-STREAM-INF:BANDWIDTH={best_video.get("tbr", 0)},AUDIO="audio"'
                            )
                            manifest_lines.append(best_video.get("url"))

                            for audio_format in sorted_audio_formats:
                                audio_url = audio_format.get("url")
                                if audio_url:
                                    track_name = audio_format.get("format_note") or audio_format.get("language") or "Unknown"
                                    manifest_lines.append(
                                        f'#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",'
                                        f'NAME="{track_name}",DEFAULT=NO,AUTOSELECT=YES,URI="{audio_url}"'
                                    )

                            m3u8_protocol = "m3u8_combined"
                            m3u8_url = "\n".join(manifest_lines)
                            print(f"{current_time()} INFO: Combined manifest created with m3u8_combined protocol.")

                    else:
                        print(f"{current_time()} WARNING: No formats available for {url}.")
            else:
                print(f"{current_time()} ERROR: Failed to extract info for {url}.")

        except Exception as error:
            print(f"{current_time()} ERROR: While processing {url}, error was: {error}")

    return m3u8_url, m3u8_protocol, info_dict

# Parses the online video info dictionary and formats
def parse_online_video_info_dict_formats(ydl, url, parse_type):
    info_dict = {}
    formats = {}

    info_dict = ydl.extract_info(url, download=False, process=False)
    if info_dict and parse_type == "all":
        formats = info_dict.get('formats', None)

    return info_dict, formats

# Selects the highest-bitrate format matching language preferences or falls back to the overall highest bitrate
def parse_online_video_formats(formats, language_preferences):
    best_format = None

    for format in formats:
        format["_lang_norm"] = (format.get("language") or "").strip().lower()

    for preferred_language in language_preferences:
        candidates = [
            format for format in formats
            if format["_lang_norm"] == preferred_language
        ]
        if candidates:
            best_format = max(candidates, key=lambda f: f.get("tbr", 0))
            break

    if not best_format and formats:
        best_format = max(formats, key=lambda f: f.get("tbr", 0))

    return best_format

# Gets the PO token for a YouTube static video
### NOTICE: This is currently not needed, but saving here for the future as this solution did work when necessary
# def get_youtube_po_token(url):
#     po_token = 'unable_to_determine_po_token'
#     video_id = None
#     max_wait = 15
#     parsed_url = urllib.parse.urlparse(url)

#     if "youtu.be" in parsed_url.netloc:
#         video_id = parsed_url.path[1:]

#     elif "youtube.com" in parsed_url.netloc:
#         query_params = urllib.parse.parse_qs(parsed_url.query)
#         video_id = query_params.get("v", [""])[0]

#     if not video_id:
#         print(f"{current_time()} ERROR: Invalid video ID for {url}.")

#     else:
#         embed_url = f"https://www.youtube.com/embed/{video_id}"

#         # Set up Selenium options and enable performance logging
#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")
#         options.add_argument("--disable-gpu")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--mute-audio") 
#         options.add_experimental_option("excludeSwitches", ["enable-logging"])
#         capabilities = DesiredCapabilities.CHROME.copy()
#         capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
#         options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

#         # Initialize the WebDriver with the updated options
#         driver = webdriver.Chrome(options=options)

#         try:
#             # Open the embed URL
#             driver.get(embed_url)

#             try:
#                 # Wait for the video player to load
#                 play_button = WebDriverWait(driver, max_wait).until(
#                     EC.element_to_be_clickable((By.CLASS_NAME, "ytp-large-play-button"))
#                 )

#                 # Simulate clicking the play button
#                 ActionChains(driver).move_to_element(play_button).click(play_button).perform()

#                 # Let the video play for a few seconds
#                 time.sleep(2)

#                 # Fetch logs and extract the PO token
#                 logs = driver.get_log("performance")
#                 for entry in logs:
#                     log = entry["message"]
#                     if "googlevideo.com" in log and "pot=" in log:
#                         # Use regex to extract the `pot` parameter value
#                         match = re.search(r"pot=([^&]+)", log)
#                         if match:
#                             po_token = match.group(1)

#             except Exception as e:
#                 print(f"{current_time()} ERROR: During playback simulation, saw {e}")

#         finally:
#             driver.quit()

#     return po_token

# Play live streams as MPEG-TS using Streamlink
@app.route('/playlists/streams/stream_mpegts', methods=['GET'])
def streams_live_mpegts():
    url = request.args.get('url', type=str)
    response = "URL is required"
    print_response = True

    streams = None
    stream = None
    fd = None

    if url:

        try:
            session = streamlink.Streamlink()
            session.set_option("ffmpeg-ffmpeg", "ffmpeg")  # Ensure ffmpeg is used
            session.set_option("ffmpeg-fout", "mpegts")   # Force MPEG-TS output
            session.set_option("mux-subtitles", False)    # Avoid subtitle muxing issues
            streams = session.streams(url)

            if streams:
                stream = streams.get("best") or next(iter(streams.values()))
            else:
                response = f"No streams found for URL {url}"
            
            if stream:
                fd = stream.open()
            else:
                response = f"No suitable stream found for URL {url}"

            if fd:
                response = Response(stream_with_context(chunk_play_stream(fd)), content_type='video/MP4')
                print_response = False
            else:
                response = f"Failed to open stream for URL {url}"

        except Exception as e:
            response = f"Playing Live Stream (MPEG-TS) resulted in error: {e}"

    if print_response:
        print(f"{current_time()} INFO: {response}")

    return response

# Generates a stream of chunks for a MPEG-TS stream
def chunk_play_stream(fd):
    try:
        while True:
            chunk = fd.read(8192)
            if not chunk:
                break
            yield chunk
    finally:
        fd.close()

# Creates the m3u(s) for Streaming Stations
def make_streaming_stations_m3us():
    settings = read_data(csv_settings)

    station_start_number = int(settings[40]['settings'])
    max_stations = int(settings[41]['settings'])

    streaming_stations = read_data(csv_playlistmanager_streaming_stations)

    final_m3us = []

    for streaming_station in streaming_stations:
        title = None
        tvc_guide_title = None
        channel_id = None
        tvg_id = None
        tvg_name = None
        tvg_logo = None
        tvg_chno = None
        channel_number = None
        tvg_description = None
        tvc_guide_description = None
        group_title = None
        tvc_guide_stationid = None
        tvc_guide_art = None
        tvc_guide_tags = None
        tvc_guide_genres = None
        tvc_guide_categories = None
        tvc_guide_placeholders = None
        tvc_stream_vcodec = None
        tvc_stream_acodec = None
        url = None
        stream_format = None

        title = streaming_station['title']
        tvc_guide_title = title
        channel_id = streaming_station['channel_id']
        tvg_id = ''
        tvg_name = title
        tvg_logo = streaming_station['tvg_logo']
        tvg_chno = int(channel_id.split('_')[-1]) + int(station_start_number)
        channel_number = tvg_chno
        tvg_description = streaming_station['tvg_description']
        tvc_guide_description = tvg_description
        group_title = ''
        tvc_guide_stationid = ''
        tvc_guide_art = tvg_logo
        tvc_guide_tags = streaming_station['tvc_guide_tags']
        tvc_guide_genres = streaming_station['tvc_guide_genres']
        tvc_guide_categories = streaming_station['tvc_guide_categories']
        tvc_guide_placeholders = streaming_station['tvc_guide_placeholders']
        tvc_stream_vcodec = streaming_station['tvc_stream_vcodec']
        tvc_stream_acodec = streaming_station['tvc_stream_acodec']
        if streaming_station['source'] == 'Live Stream (HLS)':
            url = f"{request.url_root}playlists/streams/stream?url={streaming_station['url']}"
        elif streaming_station['source'] == 'Live Stream (MPEG-TS)':
            url = f"{request.url_root}playlists/streams/stream_mpegts?url={streaming_station['url']}"
        else:
            url = streaming_station['url']
        if 'HLS' in streaming_station['source']:
            stream_format = "HLS"
        elif 'MPEG-TS' in streaming_station['source']:
            stream_format = "MPEG-TS"
        elif 'STRMLNK' in streaming_station['source']:
            stream_format = "STRMLNK"

        final_m3us.append({
            "title": title,
            "tvc_guide_title": tvc_guide_title,
            "channel_id": channel_id,
            "tvg_id": tvg_id,
            "tvg_name": tvg_name,
            "tvg_logo": tvg_logo,
            "tvg_chno": tvg_chno,
            "channel_number": channel_number,
            "tvg_description": tvg_description,
            "tvc_guide_description": tvc_guide_description,
            "group_title": group_title,
            "tvc_guide_stationid": tvc_guide_stationid,
            "tvc_guide_art": tvc_guide_art,
            "tvc_guide_tags": tvc_guide_tags,
            "tvc_guide_genres": tvc_guide_genres,
            "tvc_guide_categories": tvc_guide_categories,
            "tvc_guide_placeholders": tvc_guide_placeholders,
            "tvc_stream_vcodec": tvc_stream_vcodec,
            "tvc_stream_acodec": tvc_stream_acodec,
            "url": url,
            "stream_format": stream_format
        })
    
    plmss_hls_final_m3us = []
    plmss_mpeg_ts_final_m3us = []
    plmss_strmlnk_final_m3us = []

    for final_m3u in final_m3us:
        if final_m3u['stream_format'] == "HLS":
            plmss_hls_final_m3us.append(final_m3u)
        elif final_m3u['stream_format'] == "MPEG-TS":
            plmss_mpeg_ts_final_m3us.append(final_m3u)
        elif final_m3u['stream_format'] == "STRMLNK":
            plmss_strmlnk_final_m3us.append(final_m3u)

    extensions = ['m3u']
    all_prior_files = []
    all_prior_files = get_all_prior_files(playlists_uploads_dir, extensions)
    for all_prior_file in all_prior_files:
    	if 'plmss' in all_prior_file['filename']:
            file_delete(playlists_uploads_dir, all_prior_file['filename'], all_prior_file['extension'])

    create_chunk_files(plmss_hls_final_m3us, os.path.join(playlists_uploads_dir_name, "plmss_hls_m3u"), "m3u", max_stations)
    create_chunk_files(plmss_mpeg_ts_final_m3us, os.path.join(playlists_uploads_dir_name, "plmss_mpeg_ts_m3u"), "m3u", max_stations)
    create_chunk_files(plmss_strmlnk_final_m3us, os.path.join(playlists_uploads_dir_name, "plmss_strmlnk_m3u"), "m3u", max_stations)

# Reports / Queries webpage
@app.route('/reports_queries', methods=['GET', 'POST'])
def webpage_reports_queries():
    global slm_query
    global select_report_query_prior
    slm_query_raw = []

    reports_queries_lists = [{'name': 'Select a Report or Query...', 'value': 'reports_queries_cancel'}]

    if slm_stream_link_file_manager:
        reports_queries_lists.append({'name': 'On-Demand: Summary', 'value': 'query_slm_summary'})
        reports_queries_lists.append({'name': 'On-Demand: Currently Unavailable', 'value': 'query_currently_unavailable'})
        reports_queries_lists.append({'name': 'On-Demand: Previously Watched', 'value': 'query_previously_watched'})
        reports_queries_lists.append({'name': "On-Demand: Movies / Shows - Last 30 Days Original Release Date with Availablity*", 'value': 'query_slm_recent_releases_30_days'})
        reports_queries_lists.append({'name': "On-Demand: Movies / Shows - Last 90 Days Original Release Date with Availablity*", 'value': 'query_slm_recent_releases_90_days'})
        reports_queries_lists.append({'name': "On-Demand: Movies / Shows - Not on JustWatch*", 'value': 'query_not_on_justwatch'})

    if slm_channels_dvr_integration:
        reports_queries_lists.append({'name': 'Channels DVR: Movies / Shows / Video Groups by Library Collection', 'value': 'query_mtm_programs_by_library_collection'})
        reports_queries_lists.append({'name': 'Channels DVR: Movies / Shows / Video Groups by Number of Files', 'value': 'query_mtm_programs_by_number_of_files'})
        reports_queries_lists.append({'name': 'Channels DVR: Movies / Shows / Video Groups by Size on Disk', 'value': 'query_mtm_programs_by_size_on_disk'})
        reports_queries_lists.append({'name': 'Channels DVR: Movies / Shows / Video Groups by Average Size per File', 'value': 'query_mtm_programs_by_average_file_size'})
        reports_queries_lists.append({'name': 'Channels DVR: Movies / Shows / Video Groups by Duration', 'value': 'query_mtm_programs_by_duration'})
        reports_queries_lists.append({'name': 'Channels DVR: Movies / Shows / Video Groups by Average Size per Duration', 'value': 'query_mtm_programs_by_average_file_size_per_duration'})

    if slm_playlist_manager:
        reports_queries_lists.append({'name': 'Linear: Stations - Parents and Children', 'value': 'query_plm_parent_children'})
        reports_queries_lists.append({'name': 'Linear: Combined XML Guide Stations', 'value': 'query_plm_combined_xml_guide_stations'})
        if slm_channels_dvr_integration:
            reports_queries_lists.append({'name': 'Channels DVR: Stations by Channel Collection', 'value': 'query_mtm_stations_by_channel_collection'})

    if request.method == 'POST':
        action = request.form['action']
        select_report_query_input = request.form.get('select_report_query')
        select_report_query_prior = select_report_query_input

        if "reports_queries_cancel" in [action, select_report_query_input]:
            slm_query_raw = []
            slm_query = None
            select_report_query_prior = 'reports_queries_cancel'

        elif action == 'reports_queries_view':
            slm_query_raw = run_query(select_report_query_input)

            if select_report_query_input in [
                            "query_currently_unavailable",
                            "query_previously_watched",
                            "query_not_on_justwatch"
                         ]:
                slm_query_raw = sorted(slm_query_raw, key=lambda x: (x["Type"], sort_key(x["Name"].casefold())))

            slm_query = view_csv(slm_query_raw, "library", None)

    return render_template(
        'main/tools_reports_queries.html',
        segment='reports_queries',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_slm_query = slm_query,
        html_reports_queries_lists = reports_queries_lists,
        html_select_report_query_prior = select_report_query_prior
    )

# Run a SQL-like Query
def run_query(query_name):
    run_query = None
    results = []

    # GEN
    settings_data = read_data(csv_settings)
    channels_url = settings_data[0]["settings"]

    # SLM
    bookmarks_data = read_data(csv_bookmarks)
    bookmarks_status_data = read_data(csv_bookmarks_status)
    slmappings_data = read_data(csv_slmappings)
    streaming_services_data = read_data(csv_streaming_services)
    slm_labels_data = read_data(csv_slm_labels)
    slm_label_maps_data = read_data(csv_slm_label_maps)

    # PLM
    plm_child_to_parent_maps_data = read_data(csv_playlistmanager_child_to_parent)
    plm_all_stations_data = read_data(csv_playlistmanager_combined_m3us)
    plm_parents_data = read_data(csv_playlistmanager_parents)
    plm_playlists_data = read_data(csv_playlistmanager_playlists)
    plm_streaming_stations_data = read_data(csv_playlistmanager_streaming_stations)
    plm_station_mappings_data = read_data(csv_playlistmanager_station_mappings)

    # Convert the data into pandas DataFrames
    settings = pd.DataFrame(settings_data)
    bookmarks = pd.DataFrame(bookmarks_data)
    bookmarks_status = pd.DataFrame(bookmarks_status_data)
    slmappings = pd.DataFrame(slmappings_data)
    streaming_services = pd.DataFrame(streaming_services_data)
    slm_labels = pd.DataFrame(slm_labels_data)
    slm_label_maps = pd.DataFrame(slm_label_maps_data)
    plm_child_to_parent_maps = pd.DataFrame(plm_child_to_parent_maps_data)
    plm_all_stations = pd.DataFrame(plm_all_stations_data)
    plm_parents = pd.DataFrame(plm_parents_data)
    plm_playlists = pd.DataFrame(plm_playlists_data)
    plm_streaming_stations = pd.DataFrame(plm_streaming_stations_data)
    plm_station_mappings = pd.DataFrame(plm_station_mappings_data)

    if query_name in [
                        'query_slm_summary',
                        'query_currently_unavailable',
                        'query_previously_watched',
                        'query_slm_recent_releases_30_days',
                        'query_slm_recent_releases_90_days',
                        'query_not_on_justwatch'
                     ]:

        if bookmarks.empty or bookmarks_status.empty:
            pass

        else:

            run_query = True

            # Safety check in case there are no label maps
            if 'entry_id' not in slm_label_maps.columns:
                slm_label_maps['entry_id'] = pd.Series(dtype='object')
            if 'label_id' not in slm_label_maps.columns:
                slm_label_maps['label_id'] = pd.Series(dtype='object')

            if query_name == 'query_slm_summary':
                # Merge bookmarks with slm_label_maps_data to get label_ids for each entry_id
                bookmarks_with_labels = pd.merge(
                    bookmarks,
                    slm_label_maps,
                    on='entry_id',
                    how='left'
                )

                # Merge the result with slm_labels_data to get label_name for each label_id
                bookmarks_with_labels = pd.merge(
                    bookmarks_with_labels,
                    slm_labels[slm_labels['label_active'] == "On"],  # Only include active labels
                    on='label_id',
                    how='left'
                )

                # Group by entry_id and aggregate label_name into a comma-delimited list
                bookmarks_with_labels = bookmarks_with_labels.groupby(
                    ['entry_id', 'object_type', 'title', 'release_year', 'url', 'country_code', 'language_code', 'bookmark_action']
                )['label_name'].apply(lambda x: ', '.join(x.dropna()) if not x.dropna().empty else "No Assigned Labels").reset_index()

                # Rename the aggregated column to 'labels'
                bookmarks_with_labels.rename(columns={'label_name': 'labels'}, inplace=True)

                query = """
                SELECT
                    bookmarks_with_labels.object_type AS "Type",
                    bookmarks_with_labels.title || " (" || bookmarks_with_labels.release_year || ")" AS "Name",
                    CASE
                        WHEN bookmarks_with_labels.object_type = 'SHOW' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                        WHEN bookmarks_with_labels.object_type = 'VIDEO' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                        ELSE ''
                    END AS "# Episodes/Videos",
                    SUM(CASE WHEN bookmarks_status.status = 'unwatched' THEN 1 ELSE 0 END) AS "# Unwatched",
                    SUM(CASE WHEN bookmarks_status.status = 'watched' THEN 1 ELSE 0 END) AS "# Watched",
                    bookmarks_with_labels.labels AS "Labels"
                FROM
                    bookmarks_with_labels
                INNER JOIN
                    bookmarks_status
                ON
                    bookmarks_with_labels.entry_id = bookmarks_status.entry_id
                GROUP BY
                    bookmarks_with_labels.object_type,
                    bookmarks_with_labels.title || " (" || bookmarks_with_labels.release_year || ")",
                    bookmarks_with_labels.labels
                ORDER BY
                    bookmarks_with_labels.object_type,
                    bookmarks_with_labels.title || " (" || bookmarks_with_labels.release_year || ")"
                """

            elif query_name in [
                                'query_currently_unavailable',
                                'query_previously_watched'
                             ]:

                # Add a new column for the season using string slicing
                bookmarks_status['Season'] = bookmarks_status['season_episode'].apply(lambda x: x[:3] if isinstance(x, str) and x.startswith('S') else '')

                if query_name == 'query_currently_unavailable':

                    query = """
                    SELECT 
                        bookmarks.object_type AS "Type", 
                        bookmarks.title || " (" || bookmarks.release_year || ")" AS "Name", 
                        bookmarks_status.Season, 
                        CASE 
                            WHEN bookmarks.object_type = 'SHOW' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                            WHEN bookmarks.object_type = 'VIDEO' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                            ELSE ''
                        END AS "# Episodes/Videos"
                    FROM 
                        bookmarks 
                    INNER JOIN 
                        bookmarks_status 
                    ON 
                        bookmarks.entry_id = bookmarks_status.entry_id
                    WHERE 
                        bookmarks_status.status = 'unwatched' 
                        AND bookmarks_status.stream_link_file = ''
                    GROUP BY 
                        bookmarks.object_type, 
                        bookmarks.title || " (" || bookmarks.release_year || ")", 
                        bookmarks_status.Season
                    ORDER BY 
                        bookmarks.object_type, 
                        bookmarks.title || " (" || bookmarks.release_year || ")"
                    """

                elif query_name == 'query_previously_watched':

                    query = """
                    SELECT 
                        bookmarks.object_type AS "Type", 
                        bookmarks.title || " (" || bookmarks.release_year || ")" AS "Name", 
                        bookmarks_status.Season, 
                        CASE 
                            WHEN bookmarks.object_type = 'SHOW' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                            WHEN bookmarks.object_type = 'VIDEO' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                            ELSE ''
                        END AS "# Episodes/Videos"
                    FROM 
                        bookmarks 
                    INNER JOIN 
                        bookmarks_status 
                    ON 
                        bookmarks.entry_id = bookmarks_status.entry_id
                    WHERE 
                        bookmarks_status.status = 'watched'
                    GROUP BY 
                        bookmarks.object_type, 
                        bookmarks.title || " (" || bookmarks.release_year || ")", 
                        bookmarks_status.Season
                    ORDER BY 
                        bookmarks.object_type, 
                        bookmarks.title || " (" || bookmarks.release_year || ")"
                    """

            elif query_name in ['query_slm_recent_releases_30_days', 'query_slm_recent_releases_90_days']:
                # Step 1: Filter bookmarks_status_data for entries within the last xxx days
                if query_name == 'query_slm_recent_releases_30_days':
                    query_days = 30
                elif query_name == 'query_slm_recent_releases_90_days':
                    query_days = 90

                days_ago = (datetime.datetime.today() - datetime.timedelta(days=query_days)).strftime('%Y-%m-%d')
                today = datetime.datetime.today().strftime('%Y-%m-%d')

                bookmarks_status_filtered_data = (
                    bookmarks_status[
                        (bookmarks_status['original_release_date'] >= days_ago) &
                        (bookmarks_status['original_release_date'] <= today) &
                        (bookmarks_status['original_release_date'] != '')
                    ]
                    .sort_values(by='original_release_date', ascending=False)
                )

                bookmarks_status_filtered_data = bookmarks_status_filtered_data[
                    bookmarks_status_filtered_data['entry_id'].map(bookmarks.set_index('entry_id')['object_type']) != "VIDEO"
                ]

                # Step 2: Add node_id, country_code, and language_code
                bookmarks_status_filtered_data['node_id'] = bookmarks_status_filtered_data.apply(
                    lambda row: row['season_episode_id'] if row['season_episode_id'] != '' else row['entry_id'], axis=1
                )

                bookmarks_status_filtered_data['country_code'] = bookmarks_status_filtered_data['entry_id'].map(
                    bookmarks.set_index('entry_id')['country_code']
                )

                bookmarks_status_filtered_data['language_code'] = bookmarks_status_filtered_data['entry_id'].map(
                    bookmarks.set_index('entry_id')['language_code']
                )

                # Step 3: Fetch and process stream link offers
                bookmarks_status_filtered_data['offer_icons'] = None

                for index, row in bookmarks_status_filtered_data.iterrows():
                    node_id = row['node_id']
                    country_code = row['country_code']
                    language_code = row['language_code']

                    # Fetch stream link details
                    stream_link_details = get_offers(node_id, country_code, language_code)
                    stream_link_offers = extract_offer_info(stream_link_details)

                    # Sort offers and extract unique icons
                    stream_link_offers_sorted = sorted(stream_link_offers, key=lambda x: sort_key(x["name"]))
                    offer_icons = [offer['icon'] for offer in stream_link_offers_sorted]
                    offer_icons = list(dict.fromkeys(offer_icons))  # Remove duplicates

                    # Add offer icons to the row
                    bookmarks_status_filtered_data.at[index, 'offer_icons'] = offer_icons

                # Step 4: Convert the processed data back into a DataFrame
                bookmarks_status_filtered = pd.DataFrame(bookmarks_status_filtered_data)

                # Step 5: Preprocess the offer_icons column for rendering
                bookmarks_status_filtered['offer_icons'] = bookmarks_status_filtered['offer_icons'].apply(
                    lambda icons: ''.join(
                        f'<img src="{icon}" style="width: 55px; height: 55px; margin-right: 5px; margin-top: 5px; object-fit: contain;">'
                        for icon in icons
                    ) if isinstance(icons, list) else ''
                )

                # Step 6: Final Query
                query = """
                SELECT 
                    bookmarks_status_filtered.original_release_date AS "Original Release Date",
                    bookmarks.object_type AS "Type", 
                    bookmarks.title || " (" || bookmarks.release_year || ")" AS "Name",  
                    CASE 
                        WHEN bookmarks.object_type = 'MOVIE'
                        THEN ''
                        ELSE bookmarks_status_filtered.season_episode
                    END AS "Season/Episode",
                    CASE 
                        WHEN bookmarks_status_filtered.stream_link != '' OR bookmarks_status_filtered.stream_link_override != '' 
                        THEN 'TRUE'
                        ELSE 'FALSE'
                    END AS "Has Stream Link/File",
                    bookmarks_status_filtered.offer_icons AS "Available On"
                FROM 
                    bookmarks 
                INNER JOIN 
                    bookmarks_status_filtered
                ON 
                    bookmarks.entry_id = bookmarks_status_filtered.entry_id
                WHERE 
                    bookmarks_status_filtered.original_release_date <= DATE('now') 
                    AND bookmarks_status_filtered.original_release_date != ''
                GROUP BY
                    bookmarks_status_filtered.original_release_date,
                    bookmarks.object_type, 
                    bookmarks.title || " (" || bookmarks.release_year || ")", 
                    bookmarks_status_filtered.season_episode,
                    bookmarks_status_filtered.stream_link,
                    bookmarks_status_filtered.stream_link_override,
                    bookmarks_status_filtered.offer_icons
                ORDER BY
                    bookmarks_status_filtered.original_release_date DESC,
                    bookmarks.object_type, 
                    bookmarks.title || " (" || bookmarks.release_year || ")"
                """

            elif query_name == 'query_not_on_justwatch':

                query = """
                SELECT 
                    bookmarks.object_type AS "Type", 
                    bookmarks.title || " (" || bookmarks.release_year || ")" AS "Name",  
                    CASE 
                        WHEN bookmarks.object_type = 'MOVIE'
                        THEN ''
                        ELSE bookmarks_status.season_episode
                    END AS "Season/Episode"
                FROM 
                    bookmarks 
                INNER JOIN 
                    bookmarks_status 
                ON 
                    bookmarks.entry_id = bookmarks_status.entry_id
                WHERE 
                    bookmarks_status.original_release_date = '9999-12-31'
                    AND bookmarks.object_type != 'VIDEO'
                GROUP BY 
                    bookmarks.object_type, 
                    bookmarks.title || " (" || bookmarks.release_year || ")", 
                    bookmarks_status.season_episode
                ORDER BY 
                    bookmarks.object_type, 
                    bookmarks.title || " (" || bookmarks.release_year || ")"
                """

    elif query_name in [
                            'query_plm_parent_children'
                       ]:

        if plm_playlists.empty or plm_all_stations.empty or plm_parents.empty:
            results = []

        else:

            run_query = True

            if query_name == 'query_plm_parent_children':

                query = """
                    WITH parent_child_base AS (
                        SELECT
                            CASE
                                WHEN plm_child_to_parent_maps.parent_channel_id IN ('Ignore', 'Unassigned') THEN plm_child_to_parent_maps.parent_channel_id
                                ELSE plm_parents.parent_title
                            END AS "Parent Station",
                            plm_all_stations.station_playlist AS "Child Station",
                            COALESCE(plm_parents.parent_tvc_guide_stationid_override, '') AS "Gracenote ID (Override)",
                            COALESCE(plm_all_stations.tvc_guide_stationid, '') AS "Gracenote ID (Imported)",
                            COALESCE(plm_child_to_parent_maps.child_station_check, '') AS "Child Station Status",
                            plm_parents.parent_preferred_playlist,
                            plm_all_stations.m3u_id,
                            plm_playlists.m3u_priority
                        FROM plm_child_to_parent_maps
                        LEFT JOIN plm_parents ON plm_child_to_parent_maps.parent_channel_id = plm_parents.parent_channel_id
                        LEFT JOIN plm_all_stations ON plm_child_to_parent_maps.child_m3u_id_channel_id = plm_all_stations.m3u_id || '_' || plm_all_stations.channel_id
                        LEFT JOIN plm_playlists ON plm_all_stations.m3u_id = plm_playlists.m3u_id
                        WHERE plm_all_stations.station_playlist IS NOT NULL
                    ),
                    parent_list AS (
                        SELECT DISTINCT
                            CASE
                                WHEN parent_channel_id IN ('Ignore', 'Unassigned') THEN parent_channel_id
                                ELSE parent_title
                            END AS "Parent Station"
                        FROM plm_parents
                        UNION
                        SELECT DISTINCT parent_channel_id FROM plm_child_to_parent_maps WHERE parent_channel_id IN ('Ignore', 'Unassigned')
                    ),
                    parent_child_full AS (
                        SELECT
                            p."Parent Station",
                            b."Child Station",
                            b."Gracenote ID (Override)",
                            b."Gracenote ID (Imported)",
                            b."Child Station Status",
                            b.parent_preferred_playlist,
                            b.m3u_id,
                            b.m3u_priority
                        FROM parent_list p
                        LEFT JOIN parent_child_base b ON p."Parent Station" = b."Parent Station"
                    ),
                    parent_child_with_none AS (
                        SELECT
                            "Parent Station",
                            COALESCE("Child Station", 'None') AS "Child Station",
                            CASE WHEN "Child Station" IS NULL THEN '' ELSE "Gracenote ID (Override)" END AS "Gracenote ID (Override)",
                            CASE WHEN "Child Station" IS NULL THEN '' ELSE "Gracenote ID (Imported)" END AS "Gracenote ID (Imported)",
                            CASE WHEN "Child Station" IS NULL THEN '' ELSE "Child Station Status" END AS "Child Station Status",
                            parent_preferred_playlist,
                            m3u_id,
                            m3u_priority
                        FROM parent_child_full
                    ),
                    available_children_status AS (
                        SELECT
                            "Parent Station",
                            CASE
                                WHEN COUNT(*) = 1 AND MAX("Child Station") = 'None' THEN 'False'
                                WHEN SUM(CASE WHEN "Child Station Status" LIKE '%Disabled%' THEN 1 ELSE 0 END) = COUNT(*) THEN 'False'
                                ELSE 'True'
                            END AS "Available Children"
                        FROM parent_child_with_none
                        GROUP BY "Parent Station"
                    )
                    SELECT
                        pc."Parent Station",
                        pc."Child Station",
                        ac."Available Children",
                        pc."Gracenote ID (Override)",
                        pc."Gracenote ID (Imported)",
                        pc."Child Station Status"
                    FROM parent_child_with_none pc
                    LEFT JOIN available_children_status ac ON pc."Parent Station" = ac."Parent Station"
                    ORDER BY
                        CASE
                            WHEN pc."Parent Station" IN ('Ignore', 'Unassigned') THEN 2
                            ELSE 1
                        END,
                        pc."Parent Station",
                        CASE
                            WHEN pc.parent_preferred_playlist IS NOT NULL AND pc.parent_preferred_playlist != ''
                                THEN CASE WHEN pc.m3u_id = pc.parent_preferred_playlist THEN 0 ELSE CAST(pc.m3u_priority AS INTEGER) END
                            ELSE CAST(pc.m3u_priority AS INTEGER)
                        END,
                        pc."Child Station"
                """

    elif query_name in [
                            'query_mtm_stations_by_channel_collection'
                       ]:

        # Get list of all Channels DVR Stations
        all_stations_data = get_channels_dvr_json('all_stations')

        # Get list of Stations by Collection
        channel_collections_data = get_channels_dvr_json('channel_collections')

        # If have both, then set query and run_query to True
        if all_stations_data and channel_collections_data:
            run_query = True

            all_stations = pd.DataFrame(all_stations_data)
            channel_collections = pd.DataFrame(channel_collections_data)

            query = """
            SELECT
                all_stations."Station Number",
                all_stations."Station Name",
                all_stations."Station ID",
                all_stations."Source Name",
                COALESCE(channel_collections."Channel Collection Name", 'No Channel Collection Found') AS "Channel Collection Name"
            FROM
                all_stations
            LEFT JOIN
                channel_collections
            ON
                all_stations."Station ID" = channel_collections."Station ID"
            ORDER BY
                all_stations."Station Name"
            """

    elif query_name in [
                            'query_mtm_programs_by_library_collection',
                            'query_mtm_programs_by_size_on_disk',
                            'query_mtm_programs_by_number_of_files',
                            'query_mtm_programs_by_average_file_size',
                            'query_mtm_programs_by_duration',
                            'query_mtm_programs_by_average_file_size_per_duration'
                       ]:

        # Get a list of Channels DVR Movies
        channels_movies_url = f"{channels_url}/api/v1/movies?format=csv"
        waste_results, channels_movies_data, waste_message = parse_csv_url(channels_movies_url)

        # Get a list of Channels DVR Shows
        channels_shows_url = f"{channels_url}/api/v1/shows?format=csv"
        waste_results, channels_shows_data, waste_message = parse_csv_url(channels_shows_url)

        # Get a list of Channels DVR Video Groups
        channels_video_groups_url = f"{channels_url}/api/v1/video_groups?format=csv"
        waste_results, channels_video_groups_data, waste_message = parse_csv_url(channels_video_groups_url)

        # Combine the list of Channels DVR Movies and Shows
        channels_programs_data = []

        if channels_movies_data:
            for item in channels_movies_data:
                channels_programs_data.append(
                    {
                        "program_type": "MOVIE",
                        "program_id": item.get("ID", ''),
                        "program_title": item.get("Title", ''),
                        "program_year": '' if item.get("Release Year", 0) == 0 else item.get("Release Year", ''),
                        "program_labels": item.get("Labels", '')
                    }
                )

        if channels_shows_data:
            for item in channels_shows_data:
                channels_programs_data.append(
                    {
                        "program_type": "SHOW",
                        "program_id": item.get("ID", ''),
                        "program_title": item.get("Name", ''),
                        "program_year": '' if item.get("Release Year", 0) == 0 else item.get("Release Year", ''),
                        "program_labels": item.get("Labels", '')
                    }
                )

        if channels_video_groups_data:
            for item in channels_video_groups_data:
                channels_programs_data.append(
                    {
                        "program_type": "VIDEO",
                        "program_id": item.get("ID", ''),
                        "program_title": item.get("Name", ''),
                        "program_year": '' if item.get("Release Year", 0) == 0 else item.get("Release Year", ''),
                        "program_labels": item.get("Labels", '')
                    }
                )

        if channels_programs_data:

            channels_programs = pd.DataFrame(channels_programs_data)

            if query_name == 'query_mtm_programs_by_library_collection':

                # Get a list of Channels DVR Library Collections and item assignments
                items_by_library_collection_data = get_channels_dvr_json('items_by_library_collection')

                # If have both, then set query and run_query to True
                if items_by_library_collection_data:
                    run_query = True
                    items_by_library_collection = pd.DataFrame(items_by_library_collection_data)

                    query = """
                    SELECT
                        channels_programs.program_type AS "Type",
                        channels_programs.program_title || 
                            CASE 
                                WHEN channels_programs.program_type = 'SHOW' THEN ' (' || channels_programs.program_year || ')' 
                                ELSE '' 
                            END AS "Name",
                        channels_programs.program_labels AS "Labels",
                        CASE
                            WHEN GROUP_CONCAT(items_by_library_collection.library_collection_name, ', ') IS NULL THEN 'No Library Collection'
                            ELSE GROUP_CONCAT(items_by_library_collection.library_collection_name, ', ')
                        END AS "Library Collection"
                    FROM
                        channels_programs
                    LEFT JOIN
                        items_by_library_collection
                    ON
                        channels_programs.program_id = items_by_library_collection.program_id
                    GROUP BY
                        channels_programs.program_type,
                        channels_programs.program_title,
                        channels_programs.program_year,
                        channels_programs.program_labels
                    """

            elif query_name in [
                                    'query_mtm_programs_by_size_on_disk',
                                    'query_mtm_programs_by_number_of_files',
                                    'query_mtm_programs_by_average_file_size',
                                    'query_mtm_programs_by_duration',
                                    'query_mtm_programs_by_average_file_size_per_duration'
                            ]:

                dvr_files_data = get_channels_dvr_json('dvr_files')

                if dvr_files_data:
                    run_query = True

                    dvr_files_data_processed = []
                    for item in dvr_files_data:
                        dvr_files_data_processed.append({
                            "File ID": item.get("File ID", ''),
                            "Group ID": item.get("Group ID", ''),
                            "File Size": item.get("File Size", 0),
                            "Duration": item.get("Duration", 0)
                        })

                    dvr_files = pd.DataFrame(dvr_files_data_processed)

                    query = """
                    SELECT
                        channels_programs.program_type AS "Type",
                        channels_programs.program_title || 
                            CASE 
                                WHEN channels_programs.program_type = 'SHOW' THEN ' (' || channels_programs.program_year || ')' 
                                ELSE '' 
                            END AS "Name",
                        channels_programs.program_labels AS "Labels",
                        COUNT(
                            CASE 
                                WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN 1
                                WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN 1
                                ELSE NULL
                            END
                        ) AS "# of Files",
                        CASE
                            WHEN SUM(
                                CASE 
                                    WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN dvr_files."File Size"
                                    WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN dvr_files."File Size"
                                    ELSE 0
                                END
                            ) / 1073741824.0 < 0.1 THEN '<0.1 GB'
                            ELSE ROUND(
                                SUM(
                                    CASE 
                                        WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        ELSE 0
                                    END
                                ) / 1073741824.0, 1
                            ) || ' GB'
                        END AS "Size on Disk",
                        CASE
                            WHEN COUNT(
                                CASE 
                                    WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN 1
                                    WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN 1
                                    ELSE NULL
                                END
                            ) = 0 THEN NULL
                            WHEN ROUND(
                                SUM(
                                    CASE 
                                        WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        ELSE 0
                                    END
                                ) / COUNT(
                                    CASE 
                                        WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN 1
                                        WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN 1
                                        ELSE NULL
                                    END
                                ) / 1073741824.0, 1
                            ) < 0.1 THEN '<0.1 GB'
                            ELSE ROUND(
                                SUM(
                                    CASE 
                                        WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        ELSE 0
                                    END
                                ) / COUNT(
                                    CASE 
                                        WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN 1
                                        WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN 1
                                        ELSE NULL
                                    END
                                ) / 1073741824.0, 1
                            ) || ' GB'
                        END AS "Average Size per File",
                        CASE
                            WHEN SUM(
                                CASE 
                                    WHEN dvr_files."Duration" < 0 THEN 0
                                    ELSE dvr_files."Duration"
                                END
                            ) IS NULL THEN NULL
                            ELSE
                                printf(
                                    '%04d Hour(s) | %02d Minute(s)',
                                    CAST(
                                        (CAST(CEIL(SUM(
                                            CASE 
                                                WHEN dvr_files."Duration" < 0 THEN 0
                                                ELSE dvr_files."Duration"
                                            END
                                        ) / 60.0) AS INTEGER)) / 60
                                    AS INTEGER),
                                    CAST(
                                        (CAST(CEIL(SUM(
                                            CASE 
                                                WHEN dvr_files."Duration" < 0 THEN 0
                                                ELSE dvr_files."Duration"
                                            END
                                        ) / 60.0) AS INTEGER)) % 60
                                    AS INTEGER)
                                )
                        END AS "Total Duration",
                        CASE
                            WHEN SUM(
                                CASE 
                                    WHEN dvr_files."Duration" < 0 THEN 0
                                    ELSE dvr_files."Duration"
                                END
                            ) IS NULL OR SUM(
                                CASE 
                                    WHEN dvr_files."Duration" < 0 THEN 0
                                    ELSE dvr_files."Duration"
                                END
                            ) = 0 THEN '<0.1 GB/Hour'
                            WHEN ROUND(
                                (SUM(
                                    CASE 
                                        WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        ELSE 0
                                    END
                                ) / 1073741824.0) /
                                (SUM(
                                    CASE 
                                        WHEN dvr_files."Duration" < 0 THEN 0
                                        ELSE dvr_files."Duration"
                                    END
                                ) / 60.0 / 60.0), 1
                            ) < 0.1 THEN '<0.1 GB/Hour'
                            ELSE ROUND(
                                (SUM(
                                    CASE 
                                        WHEN channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        WHEN channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id THEN dvr_files."File Size"
                                        ELSE 0
                                    END
                                ) / 1073741824.0) /
                                (SUM(
                                    CASE 
                                        WHEN dvr_files."Duration" < 0 THEN 0
                                        ELSE dvr_files."Duration"
                                    END
                                ) / 60.0 / 60.0), 1
                            ) || ' GB/Hour'
                        END AS "Average Size per Duration"
                    FROM
                        channels_programs
                    LEFT JOIN
                        dvr_files
                    ON
                        (channels_programs.program_type = 'MOVIE' AND dvr_files."File ID" = channels_programs.program_id)
                        OR
                        (channels_programs.program_type != 'MOVIE' AND dvr_files."Group ID" = channels_programs.program_id)
                    GROUP BY
                        channels_programs.program_type,
                        channels_programs.program_title,
                        channels_programs.program_year,
                        channels_programs.program_labels
                    """

    elif query_name in [
                            'query_plm_combined_xml_guide_stations'
                       ]:
        
        combined_xml_guide_stations_data = get_combined_xml_guide_stations()

        if combined_xml_guide_stations_data:
            run_query = True

            for row in combined_xml_guide_stations_data:
                logo_url = row.get('Station EPG Logo', '')
                if logo_url:
                    row['Station EPG Logo'] = (
                        f'<img src="{logo_url}" '
                        'style="width:55px;height:55px;object-fit:contain;display:block;margin-left:auto;margin-right:auto;vertical-align:middle;">'
                    )
                else:
                    row['Station EPG Logo'] = ''

            combined_xml_guide_stations = pd.DataFrame(combined_xml_guide_stations_data)

            query = """
            SELECT
                "Station EPG Logo",
                "Station EPG Name",
                "Station EPG Guide ID"
            FROM
                combined_xml_guide_stations
            ORDER BY
                "Station EPG Name",
                "Station EPG Guide ID"
            """

    # Execute the query
    if run_query:
        results = psql.sqldf(query, locals()).to_dict(orient='records')

        if query_name == 'query_mtm_stations_by_channel_collection':
            results = sorted(results, key=lambda x: (sort_key(x["Station Name"].casefold()), sort_key(x["Channel Collection Name"].casefold())))

        elif query_name == 'query_mtm_programs_by_library_collection':
            results = sorted(results, key=lambda x: (x["Type"], sort_key(x["Name"].casefold()), sort_key(x["Library Collection"].casefold())))

        elif query_name == 'query_mtm_programs_by_size_on_disk':
            results = sorted(results, key=lambda x: (
                -float(x["Size on Disk"].split()[0]) if x["Size on Disk"] not in ["<0.1 GB", None, ""] else 0,
                x["Type"].casefold(),
                x["Name"].casefold()
            ))

        elif query_name == 'query_mtm_programs_by_number_of_files':
            results = sorted(results, key=lambda x: (-x["# of Files"], sort_key(x["Type"].casefold()), sort_key(x["Name"].casefold())))

        elif query_name == 'query_mtm_programs_by_average_file_size':
            results = sorted(results, key=lambda x: (
                -float(x["Average Size per File"].split()[0]) if x["Average Size per File"] not in ["<0.1 GB", None, ""] else 0,
                x["Type"].casefold(),
                x["Name"].casefold()
            ))

        elif query_name == 'query_mtm_programs_by_duration':
            results = sorted(results, key=lambda x: (
                -parse_total_duration(x.get("Total Duration", "")),
                x["Type"].casefold(),
                x["Name"].casefold()
            ))

        elif query_name == 'query_mtm_programs_by_average_file_size_per_duration':
            results = sorted(results, key=lambda x: (
                -float(x["Average Size per Duration"].split()[0]) if x["Average Size per Duration"] not in ["<0.1 GB/Hour", None, ""] else 0,
                x["Type"].casefold(),
                x["Name"].casefold()
            ))

        elif query_name == 'query_plm_combined_xml_guide_stations':
            results = sorted(results, key=lambda x: (sort_key(x["Station EPG Name"].casefold()), sort_key(x["Station EPG Guide ID"].casefold())))

        elif query_name == 'query_plm_parent_children':
            def parent_sort_key(row):
                parent = row["Parent Station"]
                if parent in ("Ignore", "Unassigned"):
                    return (1, "")
                return (0, sort_key(parent.casefold()))

            # Group rows by parent, preserving order
            grouped = OrderedDict()
            for row in results:
                parent = row["Parent Station"]
                if parent not in grouped:
                    grouped[parent] = []
                grouped[parent].append(row)

            # Resort parent groups using parent_sort_key, but keep child order as in SQL
            sorted_results = []
            for parent, rows in sorted(grouped.items(), key=lambda item: parent_sort_key(item[1][0])):
                sorted_results.extend(rows)

            results = sorted_results

    return results

# Parse "Total Duration" as hours and minutes for sorting
def parse_total_duration(duration_str):
    if not duration_str or "|" not in duration_str:
        return 0
    try:
        hours_part, minutes_part = duration_str.split("|")
        hours = int(hours_part.strip().split()[0])
        minutes = int(minutes_part.strip().split()[0])
        return hours * 60 + minutes
    except Exception:
        return 0

# Creates a list of guide stations from the combined XML guide
def get_combined_xml_guide_stations():
    temp_content = get_combined_xml_guide()
    lines = temp_content.splitlines()
    results = []
    write_results = False
    get_more = False
    channel_id = ''
    logo = ''
    display_name = ''
    inside_display_name = False
    display_name_buffer = []

    for line in lines:

        try:

            if "channel id=" in line:
                channel_id = re.search(r'id="([^"]+)"', line).group(1)
                get_more = True

            if get_more:
                if not inside_display_name and re.search(r'<\s*display-name\s*>', line, re.IGNORECASE):
                    match = re.search(r'<\s*display-name\s*>(.*?)<\s*/\s*display-name\s*>', line, re.IGNORECASE)
                    if match:
                        display_name = match.group(1).strip()
                    else:
                        inside_display_name = True
                        after_open = re.split(r'<\s*display-name\s*>', line, flags=re.IGNORECASE)[-1]
                        display_name_buffer = [after_open]
                elif inside_display_name:
                    if re.search(r'<\s*/\s*display-name\s*>', line, re.IGNORECASE):
                        before_close = re.split(r'<\s*/\s*display-name\s*>', line, flags=re.IGNORECASE)[0]
                        display_name_buffer.append(before_close)
                        display_name = ' '.join(display_name_buffer).strip()
                        inside_display_name = False
                        display_name_buffer = []
                    else:
                        display_name_buffer.append(line)

                if "icon src" in line:
                    logo = re.search(r'icon src="([^"]+)"', line).group(1)

            if "</channel>" in line:
                write_results = True

            if write_results:
                results.append({
                    'Station EPG Logo': logo,
                    'Station EPG Name': display_name,
                    'Station EPG Guide ID': channel_id
                })

                write_results = False
                get_more = False
                channel_id = ''
                logo = ''
                display_name = ''

        except Exception as e:
            print(f"{current_time()} ERROR: While processing line '{line}', encountered '{e}'")

    return results

# Webpage - Tools - Gracenote Search
@app.route('/tools_gracenotesearch', methods=['GET', 'POST'])
def webpage_tools_gracenotesearch():
    global gracenote_search_results
    global gracenote_search_entry_prior

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    gracenote_search_web = '/tms/stations/'
    gracenote_search_url = f"{channels_url}{gracenote_search_web}"
    gracenote_search_message = ''
    gracenote_search_results_base = None
    gracenote_search_results_base_json = None
    gracenote_search_results_library = []

    if request.method == 'POST':
        action = request.form['action']

        if action == 'gracenote_search_search':
            channels_url_okay = check_channels_url(None)

            if channels_url_okay:
                gracenote_search_entry_input = request.form.get('gracenote_search_entry')
                gracenote_search_entry_prior = gracenote_search_entry_input
                gracenote_search_url_entry = f"{gracenote_search_url}{gracenote_search_entry_input}"
                gracenote_search_results = None

                try:
                    gracenote_search_results_base = requests.get(gracenote_search_url_entry, headers=url_headers)
                except requests.RequestException as e:
                    gracenote_search_message = f"{current_time()} ERROR: During search, received {e}. Please try again."

            else:
                gracenote_search_message = f"{current_time()} ERROR: Channels URL is incorrect. Please update in the 'Settings' area."

            if gracenote_search_message is not None and gracenote_search_message != '':
                print(f"{gracenote_search_message}")

            if gracenote_search_results_base:
                gracenote_search_results_base_json = gracenote_search_results_base.json()

                for result in gracenote_search_results_base_json:
                    gracenote_search_result_gracenote_id = result.get("stationId", '')
                    gracenote_search_result_logo = result.get("preferredImage", {}).get("uri", '')
                    if gracenote_search_result_logo is None or gracenote_search_result_logo == '':
                        gracenote_search_result_logo = 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Missing_barnstar.jpg'
                    gracenote_search_result_name = result.get("name", '')
                    gracenote_search_result_affiliate_call_sign = result.get("affiliateCallSign", '')
                    gracenote_search_result_type = result.get("type", '')
                    gracenote_search_result_video_type = result.get("videoQuality", {}).get("videoType", '')
                    gracenote_search_result_language_main = result.get("bcastLangs", [''])[0]
                    gracenote_search_result_call_sign = result.get("callSign", '')

                    gracenote_search_results_library.append({
                        "Gracenote ID": gracenote_search_result_gracenote_id,
                        "Logo": gracenote_search_result_logo,
                        "Name": gracenote_search_result_name,
                        "Affiliate": gracenote_search_result_affiliate_call_sign,
                        "Type": gracenote_search_result_type,
                        "Video": gracenote_search_result_video_type,
                        "Primary Language": gracenote_search_result_language_main,
                        "Call Sign": gracenote_search_result_call_sign
                    })

                gracenote_search_results = view_csv(gracenote_search_results_library, "library", True)

        elif action == 'gracenote_search_cancel':
            gracenote_search_entry_prior = ''
            gracenote_search_results = None

    return render_template(
        'main/tools_gracenotesearch.html',
        segment = 'tools_gracenotesearch',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_gracenote_search_results = gracenote_search_results,
        html_gracenote_search_entry_prior = gracenote_search_entry_prior,
        html_gracenote_search_message = gracenote_search_message
    )

# Webpage - Tools - CSV Explorer
@app.route('/tools_csvexplorer', methods=['GET', 'POST'])
def webpage_tools_csvexplorer():
    global csv_explorer_results
    global csv_explorer_entry_prior

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    channels_api_web = '/admin/api_explorer'
    channels_api_url = f"{channels_url}{channels_api_web}"
    tools_csvexplorer_message = ''

    if request.method == 'POST':
        action = request.form['action']

        if action == 'csv_explorer_search':
            csv_explorer_entry_input = request.form.get('csv_explorer_entry')
            csv_explorer_entry_prior = csv_explorer_entry_input
            csv_explorer_results = None

            if csv_explorer_entry_input is None or csv_explorer_entry_input == '':
                tools_csvexplorer_message = f"{current_time()} WARNING: Link is empty. Please enter a valid value."
            
            else:
                csv_explorer_results, waste_library, tools_csvexplorer_message = parse_csv_url(csv_explorer_entry_input)

            if tools_csvexplorer_message is not None and tools_csvexplorer_message != '':
                print(f"{tools_csvexplorer_message}")

        elif action == 'csv_explorer_cancel':
            csv_explorer_entry_prior = ''
            csv_explorer_results = None

    return render_template(
        'main/tools_csvexplorer.html',
        segment = 'tools_csvexplorer',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_channels_api_url = channels_api_url,
        html_tools_csvexplorer_message = tools_csvexplorer_message,
        html_csv_explorer_results = csv_explorer_results,
        html_csv_explorer_entry_prior = csv_explorer_entry_prior
    )

# Pareses a CSV file and tests for validity
def parse_csv_url(url):
    results_base = None
    results_text = None
    results_library = []
    results = None
    message = ''

    results_base = fetch_url(url, 3, 5)

    if results_base:
        results_text = results_base.content.decode('utf-8-sig')
        
        if is_valid_csv(results_text):
            results_library = [row for row in csv.DictReader(io.StringIO(results_text))]
            results = view_csv(results_library, "library", True)
        
        else:
            message = f"{current_time()} WARNING: Link does not contain a valid CSV. Please try again."
    
    else:
        message = f"{current_time()} WARNING: Unable to connect to link. Please try again."

    return results, results_library, message

# Tests to see if the link references really is a CSV
def is_valid_csv(content):
    try:
        # Try reading the content as CSV
        csv.reader(io.StringIO(content))
        # Parse and validate that content is not JSON
        json.loads(content)
        # If it parses as JSON as well, it's likely not a valid CSV
        return False
    except json.JSONDecodeError:
        # If the content raises JSON decoding error, it's likely a valid CSV
        return True
    except csv.Error:
        # If the content raises a CSV parsing error, it's likely not a valid CSV
        return False

# Webpage - Tools - Channels Clients
@app.route('/tools_channelsclients', methods=['GET', 'POST'])
def webpage_tools_channelsclients():
    global local_channels_client_selected

    # Connection Variables
    client_port = ':57000'
    retries = 3
    delay = 5
    # Non-API GET paths
    client_log_path = '/log'
    # API GET paths
    client_api_status = '/api/status'                               # Player's current status
    client_api_favorite_channels = '/api/favorite_channels'         # List of favorite channels
    # API POST paths
    client_api_toggle_mute = '/api/toggle_mute'                     # Toggle mute on and off
    client_api_toggle_cc = '/api/toggle_cc'                         # Toggle captions on and off
    client_api_toggle_pip = '/api/toggle_pip'                       # Toggle Picture in Picture on and off
    client_api_channel_up = '/api/channel_up'                       # Change the channel
    client_api_channel_down = '/api/channel_down'                   # Change the channel
    client_api_previous_channel = '/api/previous_channel'           # Jump to the previous channel
    client_api_toggle_pause = '/api/toggle_pause'                   # Pause or resume playback based on current playing state
    client_api_toggle_record = '/api/toggle_record'                 # Record the program playing on the current channel
    client_api_pause = '/api/pause'                                 # Pause playback
    client_api_resume = '/api/resume'                               # Resume playback
    client_api_stop = '/api/stop'                                   # Stop playback
    client_api_seek = '/api/seek/'                                  # {seconds} Seek in timeline by seconds
    client_api_seek_forward = '/api/seek_forward'                   # Seek ahead duration in settings
    client_api_seek_backward = '/api/seek_backward'                 # Seek back duration in settings
    client_api_skip_forward = '/api/skip_forward'                   # Skip to the next chapter mark
    client_api_skip_backward = '/api/skip_backward'                 # Skip to the previous chapter mark
    client_api_play_channel = '/api/play/channel/'                  # {channel_number} Play a channel
    client_api_play_recording = '/api/play/recording/'              # {recording_id} Play a recording
    client_api_navigate = '/api/navigate/'                          # {section_name} Change to a section of the app by providing its name. EX, Guide, Library, Live TV
    client_api_notify = '/api/notify'                               # Present a notification while playing video' - example payload: {"title":"Arrived home", "message":"Jon has arrived home"} 

    client_hostname = None
    url_base = None
    tools_channelsclients_message = ''
    client_log = []
    local_channels_client_notify_title = ''
    local_channels_client_notify_message = ''
    local_channels_client_notify_timeout = '30'
    local_channels_client_notify_pass = None

    channels_clients = get_channels_dvr_json('channels_clients')
    local_channels_clients = [channels_client for channels_client in channels_clients if channels_client['Seen From'] == 'local']
    csv_channels_clients = view_csv(channels_clients, "library", None)

    if request.method == 'POST':
        action = request.form['action']
        local_channels_client_selected_input = request.form.get('local_channels_client_selected')
        local_channels_client_selected = local_channels_client_selected_input

        for channels_client in channels_clients:
            if channels_client['Client ID'] == local_channels_client_selected_input:
                url_base = f"http://{channels_client['Local IP']}{client_port}"
                client_hostname = channels_client['Hostname']
                break

        if action == 'client_non_api_get_log':
            url = f"{url_base}{client_log_path}"            
            response = fetch_url(url, retries, delay)
            
            if response:
                client_log = response.text.splitlines()
                client_log = [line for line in client_log if line != '']
            else:
                tools_channelsclients_message = f"{current_time()} ERROR: Unable to retrieve log from {client_hostname}. Please try again."

        elif action == 'client_api_post_notify':
            local_channels_client_notify_title_input = request.form.get('local_channels_client_notify_title')
            local_channels_client_notify_message_input = request.form.get('local_channels_client_notify_message')
            local_channels_client_notify_timeout_input = request.form.get('local_channels_client_notify_timeout')

            local_channels_client_notify_title = local_channels_client_notify_title_input
            local_channels_client_notify_message = local_channels_client_notify_message_input
            local_channels_client_notify_timeout = local_channels_client_notify_timeout_input

            url = f"{url_base}{client_api_notify}"

            if local_channels_client_notify_title_input is None or local_channels_client_notify_title_input == '':
                tools_channelsclients_message = f"{current_time()} ERROR: 'Title' is empty. Please enter a valid value."
            
            elif local_channels_client_notify_message_input is None or local_channels_client_notify_message_input == '':
                tools_channelsclients_message = f"{current_time()} ERROR: 'Message' is empty. Please enter a valid value."

            else:
                try:
                    if int(local_channels_client_notify_timeout_input) > 0:
                        local_channels_client_notify_pass = True
                    else:
                        tools_channelsclients_message = f"{current_time()} ERROR: For 'Display For', please enter a positive integer."
                except ValueError:
                    tools_channelsclients_message = f"{current_time()} ERROR: 'Display For' must be a number in seconds."

                if local_channels_client_notify_pass:
                    json_data = { "title": local_channels_client_notify_title_input, "message": local_channels_client_notify_message_input, "timeout": local_channels_client_notify_timeout_input }
                    response = post_url(url, json_data, retries, delay)

                    if response:
                        tools_channelsclients_message = f"{current_time()} INFO: Notification sent to {client_hostname}."
                    else:
                        tools_channelsclients_message = f"{current_time()} ERROR: Unable to send notification to {client_hostname}. Please try again."

    return render_template(
        'main/tools_channelsclients.html',
        segment = 'tools_channelsclients',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_tools_channelsclients_message = tools_channelsclients_message,
        html_channels_clients = channels_clients,
        html_local_channels_clients = local_channels_clients,
        html_csv_channels_clients = csv_channels_clients,
        html_local_channels_client_selected = local_channels_client_selected,
        html_client_log = client_log,
        html_local_channels_client_notify_title = local_channels_client_notify_title,
        html_local_channels_client_notify_message = local_channels_client_notify_message,
        html_local_channels_client_notify_timeout = local_channels_client_notify_timeout
    )

# Webpage - Tools - Automation
@app.route('/tools_automation', methods=['GET', 'POST'])
def webpage_tools_automation():
    settings = read_data(csv_settings)
    gen_backup_schedule = settings[19]["settings"]
    gen_backup_schedule_time = settings[20]["settings"]
    gen_backup_schedule_frequency = settings[21]["settings"]
    gen_backup_max_backups = settings[22]["settings"]
    gen_upgrade_schedule = settings[25]["settings"]
    gen_upgrade_schedule_time = settings[26]["settings"]
    gen_upgrade_schedule_frequency = settings[27]["settings"]
    try:
        auto_update_schedule = settings[8]["settings"]
    except (IndexError, KeyError):
        auto_update_schedule = 'Off'
    auto_update_schedule_time = settings[6]["settings"]
    auto_update_schedule_frequency = settings[18]["settings"]
    plm_update_stations_schedule = settings[13]["settings"]
    plm_update_stations_schedule_time = settings[14]["settings"]
    plm_update_stations_schedule_frequency = settings[44]["settings"]               # [44] PLM: Update Stations Process Schedule Frequency
    plm_update_m3us_epgs_schedule = settings[15]["settings"]
    plm_update_m3us_epgs_schedule_time = settings[16]["settings"]
    plm_update_m3us_epgs_schedule_frequency = settings[17]["settings"]
    reset_channels_passes = settings[29]["settings"]                                # [29] MTM: Automation - Reset Channels DVR Passes On/Off
    reset_channels_passes_time = settings[30]["settings"]                           # [30] MTM: Automation - Reset Channels DVR Passes Start Time
    reset_channels_passes_frequency = settings[31]["settings"]                      # [31] MTM: Automation - Reset Channels DVR Passes Frequency
    slm_new_recent_releases = settings[32]["settings"]                              # [32] MTM: Automation - SLM New & Recent Releases On/Off
    slm_new_recent_releases_time = settings[33]["settings"]                         # [33] MTM: Automation - SLM New & Recent Releases Start Time
    slm_new_recent_releases_frequency = settings[34]["settings"]                    # [34] MTM: Automation - SLM New & Recent Releases Frequency
    slm_new_recent_releases_when = settings[35]["settings"]                         # [35] MTM: Automation - SLM New & Recent Releases Hours Past to Consider
    refresh_channels_m3u_playlists = settings[36]["settings"]                       # [36] MTM: Automation - Refresh Channels M3U Playlists On/Off
    refresh_channels_m3u_playlists_exclude_never_refresh = settings[60]["settings"] # [60] MTM: Automation - Refresh Channels DVR m3u Playlists - Exclude 'Never Refresh URL' On/Off
    refresh_channels_m3u_playlists_time = settings[37]["settings"]                  # [37] MTM: Automation - Refresh Channels M3U Playlists Start Time
    refresh_channels_m3u_playlists_frequency = settings[38]["settings"]             # [38] MTM: Automation - Refresh Channels M3U Playlists Frequency
    mtm_channels_remove_old_logs_recording = settings[51]["settings"]               # [51] MTM: Remove old Channels DVR Recording Logs On/Off
    mtm_channels_remove_old_logs_recording_time = settings[52]["settings"]          # [52] MTM: Remove old Channels DVR Recording Logs Start Time
    mtm_channels_remove_old_logs_recording_frequency = settings[53]["settings"]     # [53] MTM: Remove old Channels DVR Recording Logs Frequency
    mtm_channels_remove_old_logs_recording_days = settings[54]["settings"]          # [54] MTM: Remove old Channels DVR Recording Logs Days to Keep
    mtm_channels_remove_old_backups = settings[55]["settings"]                      # [55] MTM: Remove old Channels DVR Backups On/Off
    mtm_channels_remove_old_backups_time = settings[56]["settings"]                 # [56] MTM: Remove old Channels DVR Backups Start Time
    mtm_channels_remove_old_backups_frequency = settings[57]["settings"]            # [57] MTM: Remove old Channels DVR Backups Frequency
    mtm_channels_remove_old_backups_days = settings[58]["settings"]                 # [58] MTM: Remove old Channels DVR Backups Days to Keep
    settings_use_feed_map = settings[67]["settings"]                                # [67] SLM: Use the 'Feed & Auto-Mapping' functionality
    slm_update_feed =  settings[68]["settings"]                                     # [68] MTM: Run SLM 'Feed & Auto-Mapping' Functionality On/Off
    slm_update_feed_time = settings[69]["settings"]                                 # [69] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Start Time
    slm_update_feed_frequency = settings[70]["settings"]                            # [70] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Frequency

    automation_message = ''
    action_friendly_name = ''
    automation_frequencies = [
        "Every 1 hour",
        "Every 2 hours",
        "Every 3 hours",
        "Every 4 hours",
        "Every 6 hours",
        "Every 8 hours",
        "Every 12 hours",
        "Every 24 hours"
    ]
    plm_m3us_epgs_schedule_frequencies = [
        "Every 1 hour",
        "Every 3 hours",
        "Every 6 hours",
        "Every 12 hours",
        "Every 24 hours"
    ]
    slm_end_to_end_frequencies = [
        "Every 8 hours",
        "Every 12 hours",
        "Every 24 hours"
    ]
    gen_backup_frequencies = [
        "Every 1 hour",
        "Every 2 hours",
        "Every 4 hours",
        "Every 8 hours",
        "Every 12 hours",
        "Every 24 hours"
    ]
    gen_upgrade_frequencies = [
        "Every 1 hour",
        "Every 12 hours",
        "Every 24 hours"
    ]

    trim_values = [
        '_run',
        '_save',
        '_cancel'
    ]
    other_actions = [
        'update_streaming_services',
        'get_new_episodes',
        'import_program_updates',
        'generate_stream_links',
        'prune_scan_channels'
    ]
    trimmed_action = None
    anchor_base = None
    anchor = None

    if request.method == 'POST':
        action = request.form['action']

        for trim_value in trim_values:
            if action.endswith(trim_value):
                trimmed_action = action[:-len(trim_value)]
                break

        if trimmed_action:
            anchor_base = 'end_to_end_process' if trimmed_action in other_actions else trimmed_action
            anchor = 'anchor_' + anchor_base

        if action.endswith('_run'):

            if action.startswith('reset_channels_passes'):
                automation_message = run_reset_channels_passes()

            elif action.startswith('refresh_channels_m3u_playlists'):
                automation_message = run_refresh_channels_m3u_playlists()

            elif action.startswith('mtm_channels_remove_old'):

                if 'logs_recording' in action:
                    action_type = 'channels_recording_logs'
                elif 'backups' in action:
                    action_type = 'channels_backups'

                automation_message = run_channels_remove_old_files_empty_directories(action_type)

            else:

                if action.startswith('gen_backup_process'):
                    action_friendly_name = 'Backup Process'
                    if os.path.exists(program_files_dir):
                        create_backup()

                elif action.startswith('gen_upgrade_process'):
                    action_friendly_name = 'Upgrade Process'
                    check_upgrade()

                elif action.startswith('end_to_end_process'):
                    action_friendly_name = 'Stream Links/Files: End-to-End Process'
                    end_to_end()

                elif action.startswith('slm_new_recent_releases'):
                    action_friendly_name = 'Stream Links: New & Recent Releases'
                    run_slm_new_recent_releases()

                elif action.startswith('plm_update_stations_process'):
                    action_friendly_name = 'Playlist Manager: Update Station List'
                    get_combined_m3us()

                elif action.startswith('plm_update_m3us_epgs_process'):
                    action_friendly_name = 'Playlist Manager: Update m3u(s) & XML EPG(s)'
                    get_final_m3us_epgs()

                elif action.startswith('update_streaming_services'):
                    action_friendly_name = 'Update Streaming Services'
                    update_streaming_services()

                elif action.startswith('get_new_episodes'):
                    action_friendly_name = 'Get New Episodes'
                    get_new_episodes(None)

                elif action.startswith('import_program_updates'):
                    action_friendly_name = 'Import Updates from '
                    if slm_channels_dvr_integration:
                        action_friendly_name += 'Channels DVR'
                    elif slm_media_players_integration:
                        action_friendly_name += 'Media Player'
                    import_program_updates()

                elif action.startswith('generate_stream_links'):
                    action_friendly_name = 'Generate Stream Links/Files'
                    generate_stream_links(None)

                elif action.startswith('prune_scan_channels'):
                    action_friendly_name = 'Run Updates in Channels'
                    prune_scan_channels()

                elif action.startswith('slm_update_feed'):
                    action_friendly_name = 'Stream Links: Update Feeds and Run Auto-Mapping'
                    run_slm_update_feed()

                automation_message = f"{current_time()} INFO: '{action_friendly_name}' completed. See 'Logs' for more details."
                print(f"{automation_message}")

        elif action.endswith('_save') or action.endswith('_cancel'):

            if action.endswith('_save'):

                if action.startswith('reset_channels_passes'):
                    reset_channels_passes_input = request.form.get('reset_channels_passes')
                    reset_channels_passes_time_input = request.form.get('reset_channels_passes_time')
                    reset_channels_passes_frequency_input = request.form.get('reset_channels_passes_frequency')

                    settings[29]["settings"] = "On" if reset_channels_passes_input == 'on' else "Off"
                    settings[30]["settings"] = reset_channels_passes_time_input
                    settings[31]["settings"] = reset_channels_passes_frequency_input

                elif action.startswith('refresh_channels_m3u_playlists'):
                    refresh_channels_m3u_playlists_input = request.form.get('refresh_channels_m3u_playlists')
                    refresh_channels_m3u_playlists_exclude_never_refresh_input = request.form.get('refresh_channels_m3u_playlists_exclude_never_refresh')
                    refresh_channels_m3u_playlists_time_input = request.form.get('refresh_channels_m3u_playlists_time')
                    refresh_channels_m3u_playlists_frequency_input = request.form.get('refresh_channels_m3u_playlists_frequency')

                    settings[36]["settings"] = "On" if refresh_channels_m3u_playlists_input == 'on' else "Off"
                    settings[60]["settings"] = "On" if refresh_channels_m3u_playlists_exclude_never_refresh_input == 'on' else "Off"
                    settings[37]["settings"] = refresh_channels_m3u_playlists_time_input
                    settings[38]["settings"] = refresh_channels_m3u_playlists_frequency_input

                elif action.startswith('gen_backup_process'):
                    gen_backup_schedule_input = request.form.get('gen_backup_schedule')
                    gen_backup_schedule_time_input = request.form.get('gen_backup_schedule_time')
                    gen_backup_schedule_frequency_input = request.form.get('gen_backup_schedule_frequency')
                    gen_backup_max_backups_input = request.form.get('gen_backup_max_backups')

                    settings[19]["settings"] = "On" if gen_backup_schedule_input == 'on' else "Off"
                    settings[20]["settings"] = gen_backup_schedule_time_input
                    settings[21]["settings"] = gen_backup_schedule_frequency_input
                    try:
                        if int(gen_backup_max_backups_input) > 0:
                            settings[22]["settings"] = int(gen_backup_max_backups_input)
                        else:
                            automation_message = f"{current_time()} ERROR: For 'Max Backups', please enter a positive integer."
                    except ValueError:
                        automation_message = f"{current_time()} ERROR: 'Max Backups' must be a number."

                elif action.startswith('gen_upgrade_process'):
                    gen_upgrade_schedule_input = request.form.get('gen_upgrade_schedule')
                    gen_upgrade_schedule_time_input = request.form.get('gen_upgrade_schedule_time')
                    gen_upgrade_schedule_frequency_input = request.form.get('gen_upgrade_schedule_frequency')

                    settings[25]["settings"] = "On" if gen_upgrade_schedule_input == 'on' else "Off"
                    settings[26]["settings"] = gen_upgrade_schedule_time_input
                    settings[27]["settings"] = gen_upgrade_schedule_frequency_input

                elif action.startswith('end_to_end_process'):
                    auto_update_schedule_input = request.form.get('auto_update_schedule')
                    auto_update_schedule_time_input = request.form.get('auto_update_schedule_time')
                    auto_update_schedule_frequency_input = request.form.get('auto_update_schedule_frequency')

                    try:
                        settings[8]["settings"] = "On" if auto_update_schedule_input == 'on' else "Off"
                    except (IndexError, KeyError):
                        settings.append({"settings": "On" if auto_update_schedule_input == 'on' else "Off"})
                    settings[6]["settings"] = auto_update_schedule_time_input
                    settings[18]["settings"] = auto_update_schedule_frequency_input

                elif action.startswith('slm_new_recent_releases'):
                    slm_new_recent_releases_input = request.form.get('slm_new_recent_releases')
                    slm_new_recent_releases_time_input = request.form.get('slm_new_recent_releases_time')
                    slm_new_recent_releases_frequency_input = request.form.get('slm_new_recent_releases_frequency')
                    slm_new_recent_releases_when_input = request.form.get('slm_new_recent_releases_when')

                    settings[32]["settings"] = "On" if slm_new_recent_releases_input == 'on' else "Off"
                    settings[33]["settings"] = slm_new_recent_releases_time_input
                    settings[34]["settings"] = slm_new_recent_releases_frequency_input
                    try:
                        if int(slm_new_recent_releases_when_input) > 0:
                            settings[35]["settings"] = int(slm_new_recent_releases_when_input)
                        else:
                            automation_message = f"{current_time()} ERROR: For 'Recent Hours', please enter a positive integer."
                    except ValueError:
                        automation_message = f"{current_time()} ERROR: 'Recent Hours' must be a number."

                elif action.startswith('plm_update_stations_process'):
                    plm_update_stations_schedule_input = request.form.get('plm_update_stations_schedule')
                    plm_update_stations_schedule_time_input = request.form.get('plm_update_stations_schedule_time')
                    plm_update_stations_schedule_frequency_input = request.form.get('plm_update_stations_schedule_frequency')

                    settings[13]["settings"] = "On" if plm_update_stations_schedule_input == 'on' else "Off"
                    settings[14]["settings"] = plm_update_stations_schedule_time_input
                    settings[44]["settings"] = plm_update_stations_schedule_frequency_input

                elif action.startswith('plm_update_m3us_epgs_process'):
                    plm_update_m3us_epgs_schedule_input = request.form.get('plm_update_m3us_epgs_schedule')
                    plm_update_m3us_epgs_schedule_time_input = request.form.get('plm_update_m3us_epgs_schedule_time')
                    plm_update_m3us_epgs_schedule_frequency_input = request.form.get('plm_update_m3us_epgs_schedule_frequency')

                    settings[15]["settings"] = "On" if plm_update_m3us_epgs_schedule_input == 'on' else "Off"
                    settings[16]["settings"] = plm_update_m3us_epgs_schedule_time_input
                    settings[17]["settings"] = plm_update_m3us_epgs_schedule_frequency_input

                elif action.startswith('mtm_channels_remove_old_logs_recording'):
                    mtm_channels_remove_old_logs_recording_input = request.form.get('mtm_channels_remove_old_logs_recording')
                    mtm_channels_remove_old_logs_recording_time_input = request.form.get('mtm_channels_remove_old_logs_recording_time')
                    mtm_channels_remove_old_logs_recording_frequency_input = request.form.get('mtm_channels_remove_old_logs_recording_frequency')
                    mtm_channels_remove_old_logs_recording_days_input = request.form.get('mtm_channels_remove_old_logs_recording_days')

                    settings[51]["settings"] = "On" if mtm_channels_remove_old_logs_recording_input == 'on' else "Off"
                    settings[52]["settings"] = mtm_channels_remove_old_logs_recording_time_input
                    settings[53]["settings"] = mtm_channels_remove_old_logs_recording_frequency_input
                    try:
                        if int(mtm_channels_remove_old_logs_recording_days_input) > 0:
                            settings[54]["settings"] = int(mtm_channels_remove_old_logs_recording_days_input)
                        else:
                            automation_message = f"{current_time()} ERROR: For 'Days to Keep', please enter a positive integer."
                    except ValueError:
                        automation_message = f"{current_time()} ERROR: 'Days to Keep' must be a number."

                elif action.startswith('mtm_channels_remove_old_backups'):
                    mtm_channels_remove_old_backups_input = request.form.get('mtm_channels_remove_old_backups')
                    mtm_channels_remove_old_backups_time_input = request.form.get('mtm_channels_remove_old_backups_time')
                    mtm_channels_remove_old_backups_frequency_input = request.form.get('mtm_channels_remove_old_backups_frequency')
                    mtm_channels_remove_old_backups_days_input = request.form.get('mtm_channels_remove_old_backups_days')

                    settings[55]["settings"] = "On" if mtm_channels_remove_old_backups_input == 'on' else "Off"
                    settings[56]["settings"] = mtm_channels_remove_old_backups_time_input
                    settings[57]["settings"] = mtm_channels_remove_old_backups_frequency_input
                    try:
                        if int(mtm_channels_remove_old_backups_days_input) > 0:
                            settings[58]["settings"] = int(mtm_channels_remove_old_backups_days_input)
                        else:
                            automation_message = f"{current_time()} ERROR: For 'Days to Keep', please enter a positive integer."
                    except ValueError:
                        automation_message = f"{current_time()} ERROR: 'Days to Keep' must be a number."

                elif action.startswith('slm_update_feed'):
                    slm_update_feed_input = request.form.get('slm_update_feed')
                    slm_update_feed_time_input = request.form.get('slm_update_feed_time')
                    slm_update_feed_frequency_input = request.form.get('slm_update_feed_frequency')

                    settings[68]["settings"] = "On" if slm_update_feed_input == 'on' else "Off"
                    settings[69]["settings"] = slm_update_feed_time_input
                    settings[70]["settings"] = slm_update_feed_frequency_input

                csv_to_write = csv_settings
                data_to_write = settings
                write_data(csv_to_write, data_to_write)

            # Reset all values to current
            settings = read_data(csv_settings)
            gen_backup_schedule = settings[19]["settings"]
            gen_backup_schedule_time = settings[20]["settings"]
            gen_backup_schedule_frequency = settings[21]["settings"]
            gen_backup_max_backups = settings[22]["settings"]
            gen_upgrade_schedule = settings[25]["settings"]
            gen_upgrade_schedule_time = settings[26]["settings"]
            gen_upgrade_schedule_frequency = settings[27]["settings"]
            try:
                auto_update_schedule = settings[8]["settings"]
            except (IndexError, KeyError):
                auto_update_schedule = 'Off'
            auto_update_schedule_time = settings[6]["settings"]
            auto_update_schedule_frequency = settings[18]["settings"]
            plm_update_stations_schedule = settings[13]["settings"]
            plm_update_stations_schedule_time = settings[14]["settings"]
            plm_update_stations_schedule_frequency = settings[44]["settings"]               # [44] PLM: Update Stations Process Schedule Frequency
            plm_update_m3us_epgs_schedule = settings[15]["settings"]
            plm_update_m3us_epgs_schedule_time = settings[16]["settings"]
            plm_update_m3us_epgs_schedule_frequency = settings[17]["settings"]
            reset_channels_passes = settings[29]["settings"]                                # [29] MTM: Automation - Reset Channels DVR Passes On/Off
            reset_channels_passes_time = settings[30]["settings"]                           # [30] MTM: Automation - Reset Channels DVR Passes Start Time
            reset_channels_passes_frequency = settings[31]["settings"]                      # [31] MTM: Automation - Reset Channels DVR Passes Frequency
            slm_new_recent_releases = settings[32]["settings"]                              # [32] MTM: Automation - SLM New & Recent Releases On/Off
            slm_new_recent_releases_time = settings[33]["settings"]                         # [33] MTM: Automation - SLM New & Recent Releases Start Time
            slm_new_recent_releases_frequency = settings[34]["settings"]                    # [34] MTM: Automation - SLM New & Recent Releases Frequency
            slm_new_recent_releases_when = settings[35]["settings"]                         # [35] MTM: Automation - SLM New & Recent Releases Hours Past to Consider
            refresh_channels_m3u_playlists = settings[36]["settings"]                       # [36] MTM: Automation - Refresh Channels M3U Playlists On/Off
            refresh_channels_m3u_playlists_exclude_never_refresh = settings[60]["settings"] # [60] MTM: Automation - Refresh Channels DVR m3u Playlists - Exclude 'Never Refresh URL' On/Off
            refresh_channels_m3u_playlists_time = settings[37]["settings"]                  # [37] MTM: Automation - Refresh Channels M3U Playlists Start Time
            refresh_channels_m3u_playlists_frequency = settings[38]["settings"]             # [38] MTM: Automation - Refresh Channels M3U Playlists Frequency
            mtm_channels_remove_old_logs_recording = settings[51]["settings"]               # [51] MTM: Remove old Channels DVR Recording Logs On/Off
            mtm_channels_remove_old_logs_recording_time = settings[52]["settings"]          # [52] MTM: Remove old Channels DVR Recording Logs Start Time
            mtm_channels_remove_old_logs_recording_frequency = settings[53]["settings"]     # [53] MTM: Remove old Channels DVR Recording Logs Frequency
            mtm_channels_remove_old_logs_recording_days = settings[54]["settings"]          # [54] MTM: Remove old Channels DVR Recording Logs Days to Keep
            mtm_channels_remove_old_backups = settings[55]["settings"]                      # [55] MTM: Remove old Channels DVR Backups On/Off
            mtm_channels_remove_old_backups_time = settings[56]["settings"]                 # [56] MTM: Remove old Channels DVR Backups Start Time
            mtm_channels_remove_old_backups_frequency = settings[57]["settings"]            # [57] MTM: Remove old Channels DVR Backups Frequency
            mtm_channels_remove_old_backups_days = settings[58]["settings"]                 # [58] MTM: Remove old Channels DVR Backups Days to Keep
            slm_update_feed =  settings[68]["settings"]                                     # [68] MTM: Run SLM 'Feed & Auto-Mapping' Functionality On/Off
            slm_update_feed_time = settings[69]["settings"]                                 # [69] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Start Time
            slm_update_feed_frequency = settings[70]["settings"]                            # [70] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Frequency

    return render_template(
        'main/tools_automation.html',
        segment = 'tools_automation',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_anchor = anchor,
        html_automation_message = automation_message,
        html_automation_frequencies = automation_frequencies,
        html_reset_channels_passes = reset_channels_passes,
        html_reset_channels_passes_time = reset_channels_passes_time,
        html_reset_channels_passes_frequency = reset_channels_passes_frequency,
        html_auto_update_schedule = auto_update_schedule,
        html_auto_update_schedule_time = auto_update_schedule_time,
        html_plm_update_stations_schedule = plm_update_stations_schedule,
        html_plm_update_stations_schedule_time = plm_update_stations_schedule_time,
        html_plm_update_stations_schedule_frequency = plm_update_stations_schedule_frequency,
        html_slm_end_to_end_frequencies = slm_end_to_end_frequencies,
        html_auto_update_schedule_frequency = auto_update_schedule_frequency,
        html_plm_update_m3us_epgs_schedule = plm_update_m3us_epgs_schedule,
        html_plm_update_m3us_epgs_schedule_time = plm_update_m3us_epgs_schedule_time,
        html_plm_m3us_epgs_schedule_frequencies = plm_m3us_epgs_schedule_frequencies,
        html_plm_update_m3us_epgs_schedule_frequency = plm_update_m3us_epgs_schedule_frequency,
        html_gen_backup_frequencies = gen_backup_frequencies,
        html_gen_backup_schedule = gen_backup_schedule,
        html_gen_backup_schedule_time = gen_backup_schedule_time,
        html_gen_backup_schedule_frequency = gen_backup_schedule_frequency,
        html_gen_backup_max_backups = gen_backup_max_backups,
        html_gen_upgrade_frequencies = gen_upgrade_frequencies,
        html_gen_upgrade_schedule = gen_upgrade_schedule,
        html_gen_upgrade_schedule_time = gen_upgrade_schedule_time,
        html_gen_upgrade_schedule_frequency = gen_upgrade_schedule_frequency,
        html_slm_new_recent_releases = slm_new_recent_releases,
        html_slm_new_recent_releases_time = slm_new_recent_releases_time,
        html_slm_new_recent_releases_frequency = slm_new_recent_releases_frequency,
        html_slm_new_recent_releases_when = slm_new_recent_releases_when,
        html_refresh_channels_m3u_playlists = refresh_channels_m3u_playlists,
        html_refresh_channels_m3u_playlists_exclude_never_refresh = refresh_channels_m3u_playlists_exclude_never_refresh,
        html_refresh_channels_m3u_playlists_time = refresh_channels_m3u_playlists_time,
        html_refresh_channels_m3u_playlists_frequency = refresh_channels_m3u_playlists_frequency,
        html_mtm_channels_remove_old_logs_recording = mtm_channels_remove_old_logs_recording,
        html_mtm_channels_remove_old_logs_recording_time = mtm_channels_remove_old_logs_recording_time,
        html_mtm_channels_remove_old_logs_recording_frequency = mtm_channels_remove_old_logs_recording_frequency,
        html_mtm_channels_remove_old_logs_recording_days = mtm_channels_remove_old_logs_recording_days,
        html_mtm_channels_remove_old_backups = mtm_channels_remove_old_backups,
        html_mtm_channels_remove_old_backups_time = mtm_channels_remove_old_backups_time,
        html_mtm_channels_remove_old_backups_frequency = mtm_channels_remove_old_backups_frequency,
        html_mtm_channels_remove_old_backups_days = mtm_channels_remove_old_backups_days,
        html_settings_use_feed_map = settings_use_feed_map,
        html_slm_update_feed = slm_update_feed,
        html_slm_update_feed_time = slm_update_feed_time,
        html_slm_update_feed_frequency = slm_update_feed_frequency
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

# Background process to check the schedule
def check_schedule():
    while True:
        settings = read_data(csv_settings)
        wait_trigger = None
        current_time = datetime.datetime.now().strftime('%H:%M')
        current_hour = datetime.datetime.now().hour
        current_minute = datetime.datetime.now().minute

        gen_backup_schedule = settings[19]["settings"]
        gen_backup_schedule_time = settings[20]["settings"]
        gen_backup_schedule_frequency = settings[21]["settings"]
        gen_backup_schedule_frequency_parsed = int(re.search(r'\d+', gen_backup_schedule_frequency).group())
        gen_upgrade_schedule = settings[25]["settings"]
        gen_upgrade_schedule_time = settings[26]["settings"]
        gen_upgrade_schedule_frequency = settings[27]["settings"]
        gen_upgrade_schedule_frequency_parsed = int(re.search(r'\d+', gen_upgrade_schedule_frequency).group())
        try:
            auto_update_schedule = settings[8]["settings"]
        except (IndexError, KeyError):
            auto_update_schedule = 'Off'           
        auto_update_schedule_time = settings[6]["settings"]
        auto_update_schedule_frequency = settings[18]["settings"]
        auto_update_schedule_frequency_parsed = int(re.search(r'\d+', auto_update_schedule_frequency).group())
        plm_update_stations_schedule = settings[13]["settings"]
        plm_update_stations_schedule_time = settings[14]["settings"]
        plm_update_stations_schedule_frequency = settings[44]["settings"]               # [44] PLM: Update Stations Process Schedule Frequency
        plm_update_stations_schedule_frequency_parsed = int(re.search(r'\d+', plm_update_stations_schedule_frequency).group())
        plm_update_m3us_epgs_schedule = settings[15]["settings"]
        plm_update_m3us_epgs_schedule_time = settings[16]["settings"]
        plm_m3us_epgs_schedule_frequency = settings[17]["settings"]
        plm_m3us_epgs_schedule_frequency_parsed = int(re.search(r'\d+', plm_m3us_epgs_schedule_frequency).group())
        reset_channels_passes = settings[29]["settings"]                                # [29] MTM: Automation - Reset Channels DVR Passes On/Off
        reset_channels_passes_time = settings[30]["settings"]                           # [30] MTM: Automation - Reset Channels DVR Passes Start Time
        reset_channels_passes_frequency = settings[31]["settings"]                      # [31] MTM: Automation - Reset Channels DVR Passes Frequency
        reset_channels_passes_frequency_parsed = int(re.search(r'\d+', reset_channels_passes_frequency).group())
        slm_new_recent_releases = settings[32]["settings"]                              # [32] MTM: Automation - SLM New & Recent Releases On/Off
        slm_new_recent_releases_time = settings[33]["settings"]                         # [33] MTM: Automation - SLM New & Recent Releases Start Time
        slm_new_recent_releases_frequency = settings[34]["settings"]                    # [34] MTM: Automation - SLM New & Recent Releases Frequency
        slm_new_recent_releases_frequency_parsed = int(re.search(r'\d+', slm_new_recent_releases_frequency).group())
        refresh_channels_m3u_playlists = settings[36]["settings"]                       # [36] MTM: Automation - Refresh Channels M3U Playlists On/Off
        refresh_channels_m3u_playlists_time = settings[37]["settings"]                  # [37] MTM: Automation - Refresh Channels M3U Playlists Start Time
        refresh_channels_m3u_playlists_frequency = settings[38]["settings"]             # [38] MTM: Automation - Refresh Channels M3U Playlists Frequency
        refresh_channels_m3u_playlists_frequency_parsed = int(re.search(r'\d+', refresh_channels_m3u_playlists_frequency).group())
        mtm_channels_remove_old_logs_recording = settings[51]["settings"]               # [51] MTM: Remove old Channels DVR Recording Logs On/Off
        mtm_channels_remove_old_logs_recording_time = settings[52]["settings"]          # [52] MTM: Remove old Channels DVR Recording Logs Start Time
        mtm_channels_remove_old_logs_recording_frequency = settings[53]["settings"]     # [53] MTM: Remove old Channels DVR Recording Logs Frequency
        mtm_channels_remove_old_logs_recording_frequency_parsed = int(re.search(r'\d+', mtm_channels_remove_old_logs_recording_frequency).group())
        mtm_channels_remove_old_backups = settings[55]["settings"]                      # [55] MTM: Remove old Channels DVR Backups On/Off
        mtm_channels_remove_old_backups_time = settings[56]["settings"]                 # [56] MTM: Remove old Channels DVR Backups Start Time
        mtm_channels_remove_old_backups_frequency = settings[57]["settings"]            # [57] MTM: Remove old Channels DVR Backups Frequency
        mtm_channels_remove_old_backups_frequency_parsed = int(re.search(r'\d+', mtm_channels_remove_old_backups_frequency).group())
        slm_update_feed =  settings[68]["settings"]                                     # [68] MTM: Run SLM 'Feed & Auto-Mapping' Functionality On/Off
        slm_update_feed_time = settings[69]["settings"]                                 # [69] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Start Time
        slm_update_feed_frequency = settings[70]["settings"]                            # [70] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Frequency
        slm_update_feed_frequency_parsed = int(re.search(r'\d+', slm_update_feed_frequency).group())

        if gen_backup_schedule == 'On' and gen_backup_schedule_time:
            gen_backup_schedule_hour, gen_backup_schedule_minute = map(int, gen_backup_schedule_time.split(':'))

            if current_minute == gen_backup_schedule_minute and (current_hour - gen_backup_schedule_hour) % gen_backup_schedule_frequency_parsed == 0:
                threading.Thread(target=create_backup).start()
                wait_trigger = True

        if gen_upgrade_schedule == 'On' and gen_upgrade_schedule_time:
            gen_upgrade_schedule_hour, gen_upgrade_schedule_minute = map(int, gen_upgrade_schedule_time.split(':'))

            if current_minute == gen_upgrade_schedule_minute and (current_hour - gen_upgrade_schedule_hour) % gen_upgrade_schedule_frequency_parsed == 0:
                threading.Thread(target=check_upgrade).start()
                wait_trigger = True

        if auto_update_schedule == 'On' and auto_update_schedule_time:
            auto_update_schedule_hour, auto_update_schedule_minute = map(int, auto_update_schedule_time.split(':'))

            if current_minute == auto_update_schedule_minute and (current_hour - auto_update_schedule_hour) % auto_update_schedule_frequency_parsed == 0:
                threading.Thread(target=end_to_end).start()
                wait_trigger = True

        if slm_new_recent_releases == 'On' and slm_new_recent_releases_time:
            slm_new_recent_releases_hour, slm_new_recent_releases_minute = map(int, slm_new_recent_releases_time.split(':'))

            if current_minute == slm_new_recent_releases_minute and (current_hour - slm_new_recent_releases_hour) % slm_new_recent_releases_frequency_parsed == 0:
                threading.Thread(target=run_slm_new_recent_releases).start()
                wait_trigger = True

        if plm_update_stations_schedule == 'On' and plm_update_stations_schedule_time:
            plm_update_stations_schedule_hour, plm_update_stations_schedule_minute = map(int, plm_update_stations_schedule_time.split(':'))

            if current_minute == plm_update_stations_schedule_minute and (current_hour - plm_update_stations_schedule_hour) % plm_update_stations_schedule_frequency_parsed == 0:
                threading.Thread(target=get_combined_m3us).start()
                wait_trigger = True
        
        if plm_update_m3us_epgs_schedule == 'On' and plm_update_m3us_epgs_schedule_time:
            plm_update_m3us_epgs_schedule_hour, plm_update_m3us_epgs_schedule_minute = map(int, plm_update_m3us_epgs_schedule_time.split(':'))
            
            if current_minute == plm_update_m3us_epgs_schedule_minute and (current_hour - plm_update_m3us_epgs_schedule_hour) % plm_m3us_epgs_schedule_frequency_parsed == 0:
                threading.Thread(target=get_final_m3us_epgs).start()
                wait_trigger = True

        if reset_channels_passes == 'On' and reset_channels_passes_time:
            reset_channels_passes_hour, reset_channels_passes_minute = map(int, reset_channels_passes_time.split(':'))

            if current_minute == reset_channels_passes_minute and (current_hour - reset_channels_passes_hour) % reset_channels_passes_frequency_parsed == 0:
                threading.Thread(target=run_reset_channels_passes).start()
                wait_trigger = True

        if refresh_channels_m3u_playlists == 'On' and refresh_channels_m3u_playlists_time:
            refresh_channels_m3u_playlists_hour, refresh_channels_m3u_playlists_minute = map(int, refresh_channels_m3u_playlists_time.split(':'))

            if current_minute == refresh_channels_m3u_playlists_minute and (current_hour - refresh_channels_m3u_playlists_hour) % refresh_channels_m3u_playlists_frequency_parsed == 0:
                threading.Thread(target=run_refresh_channels_m3u_playlists).start()
                wait_trigger = True

        if mtm_channels_remove_old_logs_recording == 'On' and mtm_channels_remove_old_logs_recording_time:
            mtm_channels_remove_old_logs_recording_hour, mtm_channels_remove_old_logs_recording_minute = map(int, mtm_channels_remove_old_logs_recording_time.split(':'))

            if current_minute == mtm_channels_remove_old_logs_recording_minute and (current_hour - mtm_channels_remove_old_logs_recording_hour) % mtm_channels_remove_old_logs_recording_frequency_parsed == 0:
                threading.Thread(target=run_channels_remove_old_files_empty_directories, args=('channels_recording_logs',)).start()
                wait_trigger = True

        if mtm_channels_remove_old_backups == 'On' and mtm_channels_remove_old_backups_time:
            mtm_channels_remove_old_backups_hour, mtm_channels_remove_old_backups_minute = map(int, mtm_channels_remove_old_backups_time.split(':'))

            if current_minute == mtm_channels_remove_old_backups_minute and (current_hour - mtm_channels_remove_old_backups_hour) % mtm_channels_remove_old_backups_frequency_parsed == 0:
                threading.Thread(target=run_channels_remove_old_files_empty_directories, args=('channels_backups',)).start()
                wait_trigger = True

        if slm_update_feed == 'On' and slm_update_feed_time:
            slm_update_feed_hour, slm_update_feed_minute = map(int, slm_update_feed_time.split(':'))

            if current_minute == slm_update_feed_minute and (current_hour - slm_update_feed_hour) % slm_update_feed_frequency_parsed == 0:
                threading.Thread(target=run_slm_update_feed).start()
                wait_trigger = True

        if wait_trigger:
            time.sleep(65)  # Wait a bit longer to avoid multiple triggers within the same minute+
            wait_trigger = None

        time.sleep(1)  # Check every second

# Create a backup of program files and remove old backups
def create_backup():
    src_dir = program_files_dir
    dst_dir = backup_dir

    # List of items to be excluded from backup
    exclude_items = [
                        'temp.txt'
                    ]

    # Determine the max number of backups to keep
    max_backups = 3
    try:
        if os.path.exists(full_path(csv_settings)):
            settings = read_data(csv_settings)
            if len(settings) > 22:
                max_backups = int(settings[22]["settings"])
    except (FileNotFoundError, KeyError, IndexError) as e:
        pass

    # Copy the contents of src_dir to the backup subdirectory
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    backup_subdir = os.path.join(dst_dir, timestamp)
    os.makedirs(backup_subdir, exist_ok=True)
    for item in os.listdir(src_dir):
        if item not in exclude_items:
            src_item = os.path.join(src_dir, item)
            if os.path.isfile(src_item):
                shutil.copy2(src_item, backup_subdir)

    # Clean up old backups if there are more than max_backups
    backups = sorted([d for d in os.listdir(dst_dir) if os.path.isdir(os.path.join(dst_dir, d))])
    if len(backups) > max_backups:
        oldest_backups = backups[:len(backups) - max_backups]
        for old_backup in oldest_backups:
            try:
                shutil.rmtree(os.path.join(dst_dir, old_backup))
            except OSError as e:
                os.chmod(os.path.join(dst_dir, old_backup), stat.S_IWRITE)  # Mark the folder as writable
                shutil.rmtree(os.path.join(dst_dir, old_backup))

# Checks to see if an upgrade is available
def check_upgrade():
    global gen_upgrade_flag
    response = None
    response_text = None
    current_version = None
    check_line = 'slm_version = "'
    start_index = len(check_line)
    check_url = f"{github_url_raw}slm.py"

    response = fetch_url(check_url, 5, 10)
    if response:
        response_text = response.text.splitlines()

        for line in response_text:
            if line.startswith(check_line):
                current_version = line[start_index:start_index + 16]
                break

    if current_version == slm_version or current_version == None or slm_environment_version == 'PRERELEASE':
        gen_upgrade_flag = None
    else:
        notification_add(f"{current_time()} Upgrade available ({current_version})! Please follow directions at '{github_url}/wiki/Upgrade-‐-Overview'.")
        gen_upgrade_flag = True

# SLM: End-to-End Update Process
def end_to_end():
    print("\n==========================================================")
    print("|                                                        |")
    print("|             SLM: End-to-End Update Process             |")
    print("|                                                        |")
    print("==========================================================\n")

    notification_add(f"{current_time()} Beginning SLM end-to-end update process...")

    set_slm_process_active_flag('process_on')

    start_time = time.time()

    update_streaming_services()
    time.sleep(2)
    get_new_episodes(None)
    time.sleep(2)
    if slm_channels_dvr_integration or slm_media_players_integration:
        import_program_updates()
        time.sleep(2)
    generate_stream_links(None)
    time.sleep(2)
    if slm_channels_dvr_integration:
        prune_scan_channels()
        time.sleep(2)

    end_time = time.time()

    elapsed_seconds = end_time - start_time

    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    notification_add(f"{current_time()} SLM End-to-end update process completed in {int(hours)} hours | {int(minutes)} minutes | {int(seconds)} seconds.")

    set_slm_process_active_flag('process_off')

# Check and set the SLM process active flag
def set_slm_process_active_flag(flag_type):
    global slm_process_active_flag
    global slm_process_active_flag_turn_off

    if flag_type.endswith('on'):
        if slm_process_active_flag is None or slm_process_active_flag == '':
            slm_process_active_flag = True

            if flag_type.startswith('single'):
                slm_process_active_flag_turn_off = True

    elif flag_type.endswith('off'):
        if slm_process_active_flag_turn_off or flag_type.startswith('process'):
            slm_process_active_flag = None
            slm_process_active_flag_turn_off = None

# Check for new episodes
def get_new_episodes(entry_id_filter):
    print("\n==========================================================")
    print("|                                                        |")
    print("|             Check for New Episodes & Videos            |")
    print("|                                                        |")
    print("==========================================================\n")

    print(f"{current_time()} Scanning for new episodes and videos...")

    set_slm_process_active_flag('single_on')

    bookmarks = []
    show_bookmarks = []
    video_bookmarks = []
    episodes = []
    bookmarks_name_lookup = {}
    bookmarks_country_code_lookup = {}
    bookmarks_language_code_lookup = {}
    slm_streams_lookup = {}
    show_bookmarks_entry_id_lookups = {}
    video_bookmarks_entry_id_lookups = {}
    episodes_write_flag = None

    import_metadata_options_flag = None
    if slm_channels_dvr_integration or slm_media_players_integration:
        import_metadata_options_flag = True

    bookmarks = read_data(csv_bookmarks)

    if bookmarks:
        bookmarks_name_lookup = {bookmark['entry_id']: f"{bookmark['title']} ({bookmark['release_year']})" for bookmark in bookmarks}
        bookmarks_country_code_lookup = {bookmark['entry_id']: bookmark['country_code'] for bookmark in bookmarks}
        bookmarks_language_code_lookup = {bookmark['entry_id']: bookmark['language_code'] for bookmark in bookmarks}

        show_bookmarks = [
            bookmark for bookmark in bookmarks 
            if not bookmark['entry_id'].startswith('slm') 
            and bookmark['object_type'] == "SHOW"
            and bookmark['bookmark_action'] not in ["Hide", "Disable Get New Episodes"]
        ]

        video_bookmarks = [
            bookmark for bookmark in bookmarks 
            if not bookmark['entry_id'].startswith('int')
            and bookmark['object_type'] == "VIDEO"
            and bookmark['bookmark_action'] not in ["Hide"]
        ]

        if entry_id_filter not in [None, '']:
            show_bookmarks = [
                show_bookmark for show_bookmark in show_bookmarks
                if show_bookmark['entry_id'] == entry_id_filter
            ]
            video_bookmarks = [
                video_bookmark for video_bookmark in video_bookmarks
                if video_bookmark['entry_id'] == entry_id_filter
            ]

        if show_bookmarks:
            show_bookmarks_entry_id_lookups = {show_bookmark['entry_id'] for show_bookmark in show_bookmarks if show_bookmark['bookmark_action'] == 'Import New Episode Metadata'}
            if len(show_bookmarks) > 1:
                show_bookmarks = sorted(show_bookmarks, key=lambda x: sort_key(x["title"].casefold()))

        if video_bookmarks:
            video_bookmarks_entry_id_lookups = {video_bookmark['entry_id'] for video_bookmark in video_bookmarks}

    episodes = read_data(csv_bookmarks_status)
    if episodes:
        slm_streams_lookup = {episode['stream_link_override'] for episode in episodes if episode['special_action'] == 'Make SLM Stream'}

    if show_bookmarks:

        for show_bookmark in show_bookmarks:

            print(f"{current_time()} INFO: Checking for new episodes and updated metadata in the TV Show '{bookmarks_name_lookup[show_bookmark['entry_id']]}'...")

            existing_episodes = [episode for episode in episodes if show_bookmark['entry_id'] == episode['entry_id']]

            # Function times out after 10 minutes
            timer = threading.Timer(600, timeout_handler)
            timer.start()

            season_episode = []
            try:
                season_episodes = get_episode_list(show_bookmark['entry_id'], show_bookmark['url'], show_bookmark['country_code'], show_bookmark['language_code'])
            except TimeoutError:
                print(f"    ERROR: Searching for episodes timed out after 10 minutes. Moving to next show...")
            except Exception as e:
                print(f"    ERROR: Unable to get episode list: {e}. Continuing to next show...")
            finally:
                timer.cancel()  # Disable the timer

            if season_episodes:

                for season_episode in season_episodes:

                    field_original_release_date = None
                    field_override_episode_title = None
                    field_override_summary = None
                    field_override_image = None
                    field_override_duration = None

                    field_original_release_date = season_episode['original_release_date']
                    if show_bookmark['bookmark_action'] == 'Import New Episode Metadata' and import_metadata_options_flag:
                        field_override_episode_title = season_episode['override_episode_title']
                        field_override_summary = season_episode['override_summary']
                        field_override_duration = season_episode['override_duration']

                    if season_episode['season_episode'] not in [existing_episode['season_episode'] for existing_episode in existing_episodes]:

                        episodes.append({
                            "entry_id": show_bookmark['entry_id'],
                            "season_episode_id": season_episode['season_episode_id'],
                            "season_episode_prefix": None,
                            "season_episode": season_episode['season_episode'],
                            "status": "unwatched",
                            "stream_link": None,
                            "stream_link_override": None,
                            "stream_link_file": None,
                            "special_action": "None",
                            "original_release_date": field_original_release_date,
                            "override_episode_title": field_override_episode_title,
                            "override_summary": field_override_summary,
                            "override_image": field_override_image,
                            "override_duration": field_override_duration,
                            "channels_id": None,
                            "manual_order": None
                        })

                        episodes_write_flag = True
                        notification_add(f"    For TV Show '{bookmarks_name_lookup[show_bookmark['entry_id']]}', added '{season_episode['season_episode']}'")

                    if episodes:

                        for episode in episodes:

                            if (
                                ( episode['entry_id'] == show_bookmark['entry_id'] ) and 
                                ( episode['season_episode_id'] == season_episode['season_episode_id'] ) and 
                                ( episode['status'] == 'unwatched' ) 
                            ):

                                episode_original_release_date = episode['original_release_date']
                                episode_override_episode_title = episode['override_episode_title']
                                episode_override_summary = episode['override_summary']
                                episode_override_duration = episode['override_duration']

                                if (
                                    ( episode_original_release_date in ['1900-01-01', '', None] ) or
                                    ( 
                                        ( episode['entry_id'] in show_bookmarks_entry_id_lookups and import_metadata_options_flag ) and
                                        (
                                            ( episode_override_episode_title in ['', None] ) or
                                            ( episode_override_episode_title.startswith('Episode ') ) or
                                            ( episode_override_summary in ['', None] ) or
                                            ( episode_override_duration in [0, '0', '', None] )
                                        )
                                    )
                                
                                ):

                                    if field_original_release_date != episode_original_release_date:
                                        if episode_original_release_date in ['1900-01-01', '', None]:
                                            episode['original_release_date'] = field_original_release_date

                                    if episode['entry_id'] in show_bookmarks_entry_id_lookups and import_metadata_options_flag:

                                        if field_override_episode_title != episode_override_episode_title:
                                            if episode_override_episode_title in ['', None] or episode_override_episode_title.startswith('Episode '):
                                                episode['override_episode_title'] = field_override_episode_title

                                        if field_override_summary != episode_override_summary:
                                            if episode_override_summary in ['', None]:
                                                episode['override_summary'] = field_override_summary

                                        if field_override_duration != episode_override_duration:
                                            if episode_override_duration in [0, '0', '', None]:
                                                episode['override_duration'] = field_override_duration

                                if (
                                    ( episode['original_release_date'] != episode_original_release_date ) or
                                    ( episode['override_episode_title']  != episode_override_episode_title ) or
                                    ( episode['override_summary'] != episode_override_summary ) or
                                    ( episode['override_duration'] != episode_override_duration )
                                ):

                                    notification_add(f"    Updated metadata for '{season_episode['season_episode']}' in TV Show '{bookmarks_name_lookup[show_bookmark['entry_id']]}'.")
                                    episodes_write_flag = True

            else:
                notification_add(f"    WARNING: No episodes found for '{bookmarks_name_lookup[show_bookmark['entry_id']]}' | {show_bookmark['object_type']}.")

    if video_bookmarks:

        for video_bookmark in video_bookmarks:

            if video_bookmark['bookmark_action'] == 'Sync Online Playlist':

                print(f"{current_time()} INFO: Checking for new videos in the Video Group '{bookmarks_name_lookup[video_bookmark['entry_id']]}'...")

                if not video_bookmark['url'] in [None, '']:
                    playlist_videos, message_throwaway = search_video_providers(video_providers, video_bookmark['url'], 'videos_from_playlist', 100, video_bookmark['language_code'], video_bookmark['country_code'])

                    if playlist_videos:
                        for playlist_video in playlist_videos:

                            field_stream_link_override = None
                            field_stream_link_override = playlist_video['url']

                            if field_stream_link_override and field_stream_link_override not in slm_streams_lookup:

                                field_season_episode = None
                                field_original_release_date = None
                                field_override_episode_title = None
                                field_override_summary = None
                                field_override_image = None
                                field_override_duration = None
                                field_manual_order = None

                                bookmarks_statuses = read_data(csv_bookmarks_status)
                                field_season_episode = check_video_name_unique(bookmarks_statuses, video_bookmark['entry_id'], f"{playlist_video['title']} ({playlist_video['release_year']})")

                                if import_metadata_options_flag:
                                    field_original_release_date, field_override_episode_title, field_override_summary, field_override_image, field_override_duration = get_video_metadata(field_stream_link_override)

                                    if ( 
                                        ( field_original_release_date is None or field_original_release_date == '' ) and
                                        ( field_override_episode_title is None or field_override_episode_title == '' ) and
                                        ( field_override_summary is None or field_override_summary == '' ) and
                                        ( field_override_image is None or field_override_image == '' ) and
                                        ( field_override_duration is None or field_override_duration == '' )
                                    ):
                                        
                                        notification_add(f"    ERROR: No metadata found for Video Group '{bookmarks_name_lookup[video_bookmark['entry_id']]}'.")

                                if video_bookmark['override_program_sort'] == 'manual':
                                    field_manual_order = max((int(episode['manual_order']) for episode in episodes if episode['entry_id'] == video_bookmark['entry_id'] and not episode['manual_order'] in [None, '']), default=0) + 1

                                episodes.append({
                                    "entry_id": video_bookmark['entry_id'],
                                    "season_episode_id": None,
                                    "season_episode_prefix": None,
                                    "season_episode": field_season_episode,
                                    "status": "unwatched",
                                    "stream_link": None,
                                    "stream_link_override": field_stream_link_override,
                                    "stream_link_file": None,
                                    "special_action": "Make SLM Stream",
                                    "original_release_date": field_original_release_date,
                                    "override_episode_title": field_override_episode_title,
                                    "override_summary": field_override_summary,
                                    "override_image": field_override_image,
                                    "override_duration": field_override_duration,
                                    "channels_id": None,
                                    "manual_order": field_manual_order
                                })

                                episodes_write_flag = True
                                notification_add(f"    For Video Group '{bookmarks_name_lookup[video_bookmark['entry_id']]}', added '{field_override_episode_title}'")

                    else:
                        notification_add(f"    ERROR: No videos found online for the Video Group '{bookmarks_name_lookup[video_bookmark['entry_id']]}.")

                else:
                    notification_add(f"    WARNING: URL needed for sync'ing is missing for the Video Group '{bookmarks_name_lookup[video_bookmark['entry_id']]}.")

        if episodes:

            for episode in episodes:

                if (
                    ( episode['entry_id'] in video_bookmarks_entry_id_lookups ) and
                    ( episode['special_action'] == 'Make SLM Stream' ) and
                    ( episode['stream_link_override'] not in [None, ''] ) and
                    ( episode['original_release_date'] == '9999-12-31' )
                ):

                    print(f"{current_time()} INFO: Attempting to update metadata for a video in '{bookmarks_name_lookup[episode['entry_id']]}'...")
                    field_original_release_date, field_override_episode_title, field_override_summary, field_override_image, field_override_duration = get_video_metadata(episode['stream_link_override'])

                    if field_original_release_date != episode['original_release_date']:
                        episode['original_release_date'] = field_original_release_date
                        episode['override_episode_title'] = field_override_episode_title
                        episode['override_summary'] = field_override_summary
                        episode['override_image'] = field_override_image
                        episode['override_duration'] = field_override_duration
                        
                        episodes_write_flag = True
                        notification_add(f"    Updated metadata for '{field_override_episode_title}' in Video Group '{bookmarks_name_lookup[episode['entry_id']]}'.")

                    else:
                        notification_add(f"    No metadata updated for '{field_override_episode_title}' in Video Group '{bookmarks_name_lookup[episode['entry_id']]}'.")

    if episodes_write_flag:
        write_data(csv_bookmarks_status, episodes)

    print(f"{current_time()} Finished scanning for new episodes and videos.")

    set_slm_process_active_flag('single_off')

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
            icon
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
            icon
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
            clearName
            icon
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
        originalReleaseDate
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
            icon
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
            clearName
            icon
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
                clearName
                icon
                __typename
            }
            __typename
            }
            isReleased
            runtime
            originalReleaseYear
            originalReleaseDate
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
            originalReleaseDate
            runtime
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
            originalReleaseDate
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
            originalReleaseDate
            runtime
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
                icon
                clearName
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
                    originalReleaseDate
                    scoring {
                    imdbScore
                    __typename
                    }
                    isReleased
                    runtime
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
        originalReleaseDate
        runtime
        upcomingReleases {
        releaseDate
        label
        package {
            id
            packageId
            icon
            clearName
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
            icon
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
            icon
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
            clearName
            icon
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
            clearName
            icon
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
                clearName
                icon
                __typename
            }
            __typename
            }
            isReleased
            runtime
            originalReleaseYear
            originalReleaseDate
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
            originalReleaseDate
            runtime
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
            originalReleaseDate
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
            originalReleaseDate
            runtime
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
                icon
                clearName
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
                    originalReleaseDate
                    scoring {
                    imdbScore
                    __typename
                    }
                    isReleased
                    runtime
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
        originalReleaseDate
        runtime
        upcomingReleases {
        releaseDate
        label
        package {
            id
            packageId
            icon
            clearName
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

                for season_episode_json_episodes_array in season_episodes_json_episodes_array:
                    season_number_digit = int(season_episode_json_episodes_array["content"]["seasonNumber"])
                    episode_number_digit = int(season_episode_json_episodes_array["content"]["episodeNumber"])

                    digits_season = len(str(season_number_digit))
                    digits_episode = len(str(episode_number_digit))

                    max_digits_season = max(max_digits_season, digits_season)
                    max_digits_episode = max(max_digits_episode, digits_episode)

                max_digits_season = max(max_digits_season, 2)
                max_digits_episode = max(max_digits_episode, 2)

                for season_episode_json_episodes_array in season_episodes_json_episodes_array:
                    season_episode_id = season_episode_json_episodes_array["id"]

                    season_number = int(season_episode_json_episodes_array.get("content", {}).get("seasonNumber", 0))
                    episode_number = int(season_episode_json_episodes_array.get("content", {}).get("episodeNumber", 0))
                    formatted_season = f"{season_number:0{max_digits_season}d}"
                    formatted_episode = f"{episode_number:0{max_digits_episode}d}"
                    season_episode = f"S{formatted_season}E{formatted_episode}"

                    override_episode_title = season_episode_json_episodes_array.get("content", {}).get("title", "")
                    override_summary = season_episode_json_episodes_array.get("content", {}).get("shortDescription", "")
                    override_duration = int(season_episode_json_episodes_array.get("content", {}).get("runtime", 0)) * 60
                    if override_duration == '0' or int(override_duration) == 0:
                        override_duration = ''
                    original_release_date = season_episode_json_episodes_array.get("content", {}).get("originalReleaseDate", "")
                    if original_release_date in ['', None]:
                        original_release_date = '1900-01-01'

                    season_episodes_results.append({
                        "season_episode_id": season_episode_id,
                        "season_episode": season_episode,
                        "status": "unwatched",
                        "override_episode_title": override_episode_title,
                        "override_summary": override_summary,
                        "override_duration": override_duration,
                        "original_release_date": original_release_date
                    })

                season_episodes_sorted = sorted(season_episodes_results, key=lambda d: d['season_episode'])

            except requests.RequestException as e:
                print(f"{current_time()} WARNING: {e}. Skipping, please try again. (entry_id: {entry_id})")
            except KeyError as e:
                print(f"{current_time()} WARNING: Missing key {e}. Skipping, please try again. (entry_id: {entry_id})")
            except Exception as e:
                print(f"{current_time()} WARNING: An unexpected error occurred: {e}. Skipping, please try again. (entry_id: {entry_id})")

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
        print(f"{current_time()} WARNING: {e}. Skipping, please try again.")

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
    if slm_channels_dvr_integration:
        print("|       Import Program Updates from Channels DVR         |")
    elif slm_media_players_integration:
        print("|         Import Program Updates from Media Player       |")
    print("|                                                        |")
    print("==========================================================\n")

    set_slm_process_active_flag('single_on')

    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]
    bookmarks_statuses = read_data(csv_bookmarks_status)

    run_import = None

    if not os.path.exists(channels_directory):
        notification_add(f"{current_time()} WARNING: {channels_directory} does not exist, skipping import. Please change the 'Stream Links/Files and Media Base Directory' in the Settings menu.")
    else:
        run_import = True
        
    if run_import:
        print(f"{current_time()} Checking for removed Stream Links/Files...")

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

        print(f"{current_time()} Finished checking for removed Stream Links/Files.")

    set_slm_process_active_flag('off')

# Find if a stream link is available for bookmarked programs, create stream link files if true, remove files if false
def generate_stream_links(original_release_date_list):
    print("\n==========================================================")
    print("|                                                        |")
    print("|                  Generate Stream Links                 |")
    print("|                                                        |")
    print("==========================================================\n")

    set_slm_process_active_flag('single_on')

    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]
    bookmarks = read_data(csv_bookmarks)
    auto_bookmarks = [
        bookmark for bookmark in bookmarks 
        if not bookmark['entry_id'].startswith('slm') 
        and not bookmark['entry_id'].startswith('int') 
        and bookmark['bookmark_action'] not in ["Hide"]
    ]

    run_generation = None

    if ( slm_channels_dvr_integration or slm_media_players_integration ) and not os.path.exists(channels_directory):
        notification_add(f"{current_time()} WARNING: {channels_directory} does not exist, skipping generation. Please change the 'Stream Links/Files and Media Base Directory' in the Settings menu.")
    else:
        run_generation = True
        
    if run_generation:
        print(f"{current_time()} START: Generating Stream Links...")

        print(f"{current_time()} Getting Stream Links...")
        find_stream_links(auto_bookmarks, original_release_date_list)
        print(f"{current_time()} Finished getting Stream Links.")

        if slm_channels_dvr_integration or slm_media_players_integration:

            if slm_channels_dvr_integration and original_release_date_list is None:
                print(f"{current_time()} Checking Channels DVR for changes from last run...")
                get_stream_link_ids()
                print(f"{current_time()} Finished checking Channels DVR for changes from last run.")

            print(f"{current_time()} Creating and removing Stream Link/File files and directories...")
            create_stream_link_files(bookmarks, True, original_release_date_list)
            print(f"{current_time()} Finished creating and removing Stream Link/File files and directories.")

        print(f"{current_time()} END: Finished Generating Stream Links.")

    set_slm_process_active_flag('off')

# Run Stream Link Generation and File Creation on one program
def generate_stream_links_single(entry_id):

    set_slm_process_active_flag('single_on')

    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]

    bookmarks = read_data(csv_bookmarks)
    modify_bookmarks = [bookmark for bookmark in bookmarks if bookmark['entry_id'] == entry_id]

    generate_stream_links_single_message = None
    run_generation = None

    if ( slm_channels_dvr_integration or slm_media_players_integration ) and not os.path.exists(channels_directory):
        generate_stream_links_single_message = f"{current_time()} WARNING: '{channels_directory}' does not exist, skipping generation. Please change the 'Stream Link/Files Base Directory' in the Settings menu."
    else:
        run_generation = True
        
    if run_generation:
        if not entry_id.startswith('slm') and not entry_id.startswith('int'):
            find_stream_links(modify_bookmarks, None)

        if entry_id.startswith('int'):
            generate_stream_links_single_message = f"{current_time()} INFO: 'SLM INTERNAL' selections cannot generate Stream Links/Files."

        elif slm_channels_dvr_integration or slm_media_players_integration:
            create_stream_link_files(modify_bookmarks, None, None)

            if slm_channels_dvr_integration:
                generate_stream_links_single_message = f"{current_time()} INFO: Finished generating Stream Links/Files! Please execute process 'Run Updates in Channels' in order to see this program."
            
            elif slm_media_players_integration:
                generate_stream_links_single_message = f"{current_time()} INFO: Finished generating Stream Links/Files! Please execute the refresh process in your media player in order to see this program."

        else:
            generate_stream_links_single_message = f"{current_time()} INFO: Finished generating Stream Links/Files! Please use 'Modify Programs' to see values."

    set_slm_process_active_flag('off')

    return generate_stream_links_single_message

# Get the valid Stream Links (if available) and write to the appropriate table
def find_stream_links(auto_bookmarks, original_release_date_list):

    if len(auto_bookmarks) > 1:
        auto_bookmarks = sorted(auto_bookmarks, key=lambda x: sort_key(x["title"].casefold()))

    bookmarks_statuses = read_data(csv_bookmarks_status)

    for auto_bookmark in auto_bookmarks:

        print(f"{current_time()} INFO: Generating Stream Link(s) for {auto_bookmark['title']} ({auto_bookmark['release_year']}) | {auto_bookmark['object_type']} ...")

        for bookmarks_status in bookmarks_statuses:

            if auto_bookmark['entry_id'] == bookmarks_status['entry_id']:

                if auto_bookmark['object_type'] == "MOVIE":
                    node_id = bookmarks_status['entry_id']
                elif auto_bookmark['object_type'] == "SHOW":
                    node_id = bookmarks_status['season_episode_id']
                else:
                    print(f"{current_time()} ERROR: Invalid object_type")

                special_action = bookmarks_status['special_action']

                stream_link_dirty = None
                stream_link_reason = None

                if slm_channels_dvr_integration or slm_media_players_integration:
                    pass
                else:
                    bookmarks_status['stream_link_file'] = ''
        
                if bookmarks_status['status'].lower() == "unwatched":

                    if special_action == "Make STRM" and original_release_date_list is None:

                        stream_link_dirty = "https://strm_must_use_override"

                    elif special_action == "Make SLM Stream" and original_release_date_list is None:

                        stream_link_dirty = "http://slm_stream_must_use_override"

                    elif bookmarks_status['stream_link_override'] != "" and original_release_date_list is None:

                        stream_link_dirty = "https://skipped_for_override"

                    else:

                        for attempt in range(3):  # Limit retries to 3 attempts
                            try:
                                
                                if original_release_date_list is None or node_id in original_release_date_list:
                                    stream_link_details = get_offers(node_id, auto_bookmark['country_code'], auto_bookmark['language_code'])
                                    stream_link_offers = extract_offer_info(stream_link_details)
                                    stream_link_dirty = get_stream_link(stream_link_offers, special_action)

                                    if stream_link_dirty is None or stream_link_dirty == '':
                                        stream_link_reason = "None due to not found on your selected streaming services"

                                break  # Break out of the retry loop if successful
                            
                            except Exception as e:
                                print(f"{current_time()} ERROR: {e}. Retrying...")

                        else:
                            print(f"{current_time()} ERROR: Could not find Stream Link after 3 attempts.")
                            if bookmarks_status['stream_link'] != "":
                                print(f"{current_time()} INFO: Assigning prior Stream Link.")
                                stream_link_dirty = bookmarks_status['stream_link']
                            else:
                                print(f"{current_time()} INFO: No prior Stream Link to assign. Try again later.")
                            pass

                else:

                    stream_link_reason = "None due to 'Watched' status"

                if original_release_date_list is None or node_id in original_release_date_list:

                    if stream_link_dirty:
                        stream_link = clean_stream_link(stream_link_dirty, auto_bookmark['object_type'])
                    else:
                        stream_link = ''

                    bookmarks_status['stream_link'] = stream_link

                    assignment_text = None
                    if auto_bookmark['object_type'] in ['MOVIE', 'SHOW']:
                        assignment_text = "    "

                        if auto_bookmark['object_type'] == 'MOVIE':
                            assignment_text += "Movie "

                        elif auto_bookmark['object_type'] == 'SHOW':

                            if bookmarks_status['season_episode_prefix'] not in [None, '']:
                                assignment_text += f"{bookmarks_status['season_episode_prefix']} "

                            assignment_text += f"{bookmarks_status['season_episode']} "

                        assignment_text += "assigned Stream Link: "

                        if stream_link_reason:
                            assignment_text += f"{stream_link_reason}"
                        else:
                            assignment_text += f"{stream_link}"

                    else:
                        assignment_test = "    ERROR: Invalid 'Object Type'. Only Movies and TV Shows can generate Stream Links."

                    if assignment_text:
                        print(assignment_text)

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
        print(f"{current_time()} WARNING: {e}. Skipping, please try again.")

    return offers_json_offers_array

# Extract the offers in a usable list
def extract_offer_info(offers_json):
    result = []

    if offers_json:
        for field, offers in offers_json.items():
            if isinstance(offers, list):
                for offer in offers:
                    name = offer.get('package', {}).get('clearName')
                    url = urllib.parse.unquote(offer.get('standardWebURL'))  # Decode the URL
                    offer_raw_icon = offer.get('package', {}).get('icon')
                    offer_raw_icon = f"{engine_image_url}{offer_raw_icon}"
                    offer_raw_icon = offer_raw_icon.replace('{profile}', engine_image_profile_icon)
                    offer_raw_icon = offer_raw_icon.replace('{format}', 'png')
                    result.append({"name": name, "url": url, "icon": offer_raw_icon})

    return result

# Parse through all Offers and find Stream Links based upon priority of Streaming Services
def get_stream_link(offers, special_action):
    check_services_final = []
    special_action_extract = None

    if special_action.startswith('Prefer: '):
        special_action_extract = special_action.split('Prefer: ')[1]
        check_services_final.append(special_action_extract)

    services = read_data(csv_streaming_services)
    check_services = [service for service in services if service["streaming_service_subscribe"] == "True" and service["streaming_service_active"] == "On"]
    check_services.sort(key=lambda x: int(x.get("streaming_service_priority", float("inf"))))

    for check_service in check_services:
        check_services_final.append(check_service['streaming_service_name'])

    # Initialize Stream Link as None
    stream_link = None
    
    # If offers is not empty, iterate through check_services
    if offers:
        for check_service in check_services_final:
            for offer in offers:
                if check_service == offer['name']:
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
            "amazon."
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
                if slmapping['object_type'] == "MOVIE or SHOW" or slmapping['object_type'] == object_type:
                    if stream_link.__contains__(slmapping['contains_string']) and slmapping['replace_type'] in ["Replace string with...", "Replace entire Stream Link with..."]:
                        if slmapping['replace_type'] == "Replace string with...":
                            stream_link = stream_link.replace(slmapping['contains_string'], slmapping['replace_string'])
                        elif slmapping['replace_type'] == "Replace entire Stream Link with...":
                            stream_link = slmapping['replace_string']
                    elif re.compile(slmapping['contains_string']).search(stream_link) and slmapping['replace_type'] == "Replace pattern (REGEX) with...":
                        stream_link = re.sub(re.compile(slmapping['contains_string']), slmapping['replace_string'], stream_link)

    return stream_link

# Gets a list of of the IDs of all Stream Link entries created by Stream Link Manager that are now different
def get_stream_link_ids():
    global stream_link_ids_changed

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    api_url_stream_link = f"{channels_url}/api/v1/all?source=stream-links"
    api_url_stream_file = f"{channels_url}/api/v1/all?source=stream-files"
    api_urls = [
        api_url_stream_link,
        api_url_stream_file
    ]
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

        for api_url in api_urls:
            try:
                response = requests.get(api_url, headers=url_headers)
                response.raise_for_status()  # Raise an exception if the response status code is not 200 (OK)
                data = response.json()
                data_filtered = [item for item in data if "slm/" in clean_comparison_path(item["path"])] # Filter the items where the "path" contains "slm/" (after cleaning)

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
                            print(f"{current_time()} WARNING: Could not find {original_path}. Skipping check.")

                        stream_link_ids.append({
                            "path": path,
                            "id": id,
                            "stream_link_prior": stream_link_prior
                        })

            except requests.RequestException as e:
                print(f"{current_time()} ERROR: From Channels API... {e}")

        for slm_stream_link in slm_stream_links:
            for stream_link_id in stream_link_ids:
                if clean_comparison_path(slm_stream_link["path"]) == clean_comparison_path(stream_link_id["path"]):
                    if slm_stream_link["stream_link_current"] != stream_link_id["stream_link_prior"]:
                        stream_link_ids_changed.append(stream_link_id["id"])

    else:
        notification_add(f"{current_time()} INFO: Cannot check for changes from last run due to Channels URL error.")

# Creates Stream Link Files and removes invalid ones and empty directories (for TV)
def create_stream_link_files(base_bookmarks, remove_choice, original_release_date_list):
    settings = read_data(csv_settings)
    slm_stream_address = settings[46]["settings"]
    slm_stream_address_full = f"{slm_stream_address}/playlists/streams/stream?url="

    settings_slm_add_show_title = settings[73]['settings']                      # [73] SLM: Add TV Show Title to File Name On/Off
    settings_slm_add_episode_title = settings[74]['settings']                   # [74] SLM: Add Episode Title to TV Show File Name On/Off

    bookmarks = [
        base_bookmark for base_bookmark in base_bookmarks 
        if base_bookmark['bookmark_action'] not in ["Hide"]
        and not base_bookmark['entry_id'].startswith('int') 
    ]

    if len(bookmarks) > 1:
        bookmarks = sorted(bookmarks, key=lambda x: sort_key(x["title"].casefold()))

    bookmarks_statuses = read_data(csv_bookmarks_status)

    movie_path, tv_path, video_path = get_movie_tv_path()

    create_directory(movie_path)
    create_directory(tv_path)
    create_directory(video_path)

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
                    stream_link_file_name = ''

                    if bookmark_status['season_episode_prefix'] != "":
                        stream_link_file_name += f"{sanitize_name(bookmark_status['season_episode_prefix'])} "

                    if settings_slm_add_show_title == 'On':
                        stream_link_file_name += f"{title_full} - "

                    if settings_slm_add_episode_title == 'On' and bookmark_status['override_episode_title'] not in [None, '']:
                        stream_link_file_name += f"{sanitize_name(bookmark_status['override_episode_title'])} - "

                    stream_link_file_name += f"{bookmark_status['season_episode']}"

                    season_number, episode_number = re.match(r"S(\d+)E(\d+)", bookmark_status['season_episode']).groups()
                    season_folder_name = f"Season {season_number}"
                    stream_link_path = os.path.join(tv_path, title_full, season_folder_name)

                elif bookmark['object_type'] == "VIDEO":
                    stream_link_path = os.path.join(video_path, title_full)
                    stream_link_file_name = sanitize_name(bookmark_status['season_episode'])

                special_action = bookmark_status['special_action']

                if bookmark_status['stream_link_override'] != "":
                    if special_action != "Make SLM Stream":
                        stream_link_url = bookmark_status['stream_link_override']
                    elif special_action == "Make SLM Stream":
                        stream_link_url = f"{slm_stream_address_full}{bookmark_status['stream_link_override']}"
                elif bookmark_status['stream_link'] != "":
                    if special_action in ["Make STRM", "Make SLM Stream"]:
                        pass
                    else:
                        stream_link_url = bookmark_status['stream_link']

                if bookmark_status['status'].lower() == "unwatched" and stream_link_url:

                    if ( 
                        ( original_release_date_list is None ) or 
                        ( bookmark['object_type'] == "MOVIE" and bookmark_status['entry_id'] in original_release_date_list ) or 
                        ( bookmark['object_type'] == "SHOW" and bookmark_status['season_episode_id'] in original_release_date_list ) or
                        ( bookmark['object_type'] == "VIDEO" and bookmark_status['season_episode'] in original_release_date_list )
                    ):

                        if bookmark['object_type'] == "SHOW" or bookmark['object_type'] == "VIDEO":
                            if bookmark['object_type'] == "SHOW":
                                create_directory(os.path.join(tv_path, title_full))
                            create_directory(stream_link_path)

                        file_path_return = create_file(stream_link_path, stream_link_file_name, stream_link_url, special_action)
                        file_path_return = normalize_path(file_path_return)
                        bookmark_status['stream_link_file'] = file_path_return

                elif ( 
                    ( bookmark_status['status'].lower() == "watched" ) or 
                    ( bookmark_status['stream_link'] == "" ) or 
                    ( special_action in ["Make STRM", "Make SLM Stream"] and bookmark_status['stream_link_override'] == "" )
                ):

                    for condition in special_actions_default:
                        file_delete(stream_link_path, stream_link_file_name, condition)

                    bookmark_status['stream_link_file'] = None

    if remove_choice:
        remove_rogue_empty(movie_path, tv_path, video_path, bookmarks_statuses)

    write_data(csv_bookmarks_status, bookmarks_statuses)

# Runs the necessary updates in Channels and gets info afterwards
def prune_scan_channels():
    print("\n==========================================================")
    print("|                                                        |")
    print("|                Update Media in Channels                |")
    print("|                                                        |")
    print("==========================================================\n")

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    prune_url = f"{channels_url}/dvr/scanner/imports/prune"
    scan_url = f"{channels_url}/dvr/scanner/scan"
    channels_prune = settings[7]["settings"]
    channels_labels = settings[50]["settings"]                      # [50] SLM: Update Labels in Channels DVR On/Off

    channels_url_okay = check_channels_url(None)

    if channels_url_okay:
        # Prune
        if channels_prune == "On":
            print(f"{current_time()} Beginning Prune request...")
            try:
                requests.put(prune_url)
            except requests.RequestException as e:
                print(f"{current_time()} WARNING: {e}. Skipping, please try again.")
            print(f"{current_time()} Prune requested.")
        else:
            print(f"{current_time()} INFO: Prune disabled, skipping step.")

        # Scan
        print(f"{current_time()} Beginning scan request...")
        try:
            requests.put(scan_url)
        except requests.RequestException as e:
            print(f"{current_time()} WARNING: {e}. Skipping, please try again.")
        print(f"{current_time()} Scan requested.")

        # Reprocess
        if stream_link_ids_changed:
            print(f"{current_time()} Beginning Reprocess requests...")
            asyncio.run(get_reprocess_requests(channels_url))
            print(f"{current_time()} Finished Reprocess requests")
        else:
            print(f"{current_time()} INFO: Nothing to reprocess, skipping step.")

        if channels_prune == "On":
            if stream_link_ids_changed:
                print(f"{current_time()} Prune, Scan, and Reprocess underway.")
            else:
                print(f"{current_time()} Prune and Scan underway.")
        else:
            if stream_link_ids_changed:
                print(f"{current_time()} Scan and Reprocess underway.")
            else:
                print(f"{current_time()} Scan underway.")

        while True:
            time.sleep(5)
            channels_dvr_activity = get_channels_dvr_activity()

            if '6-scanner' in channels_dvr_activity or '5-pruner' in channels_dvr_activity:
                if channels_prune == "On":
                    print(f"{current_time()} INFO: Prune and/or Scan still active. Checking again in 5 seconds...")
                else:
                    print(f"{current_time()} INFO: Scan still active. Checking again in 5 seconds...")
                
            else:
                if channels_prune == "On":
                    if stream_link_ids_changed:
                        notification_add(f"{current_time()} Prune and Scan complete. Check Channels DVR for Reprocess status.")
                    else:
                        notification_add(f"{current_time()} Prune and Scan complete.")
                else:
                    if stream_link_ids_changed:
                        notification_add(f"{current_time()} Scan complete. Check Channels DVR for Reprocess status.")
                    else:
                        notification_add(f"{current_time()} Scan complete.")
                break

        # Channels DVR Metadata
        print(f"{current_time()} INFO: Connecting SLM and Channels DVR metadata...")
        get_slm_channels_info()

        ### Labels
        if channels_labels == "On":
            print(f"{current_time()} INFO: Updating Channels DVR labels...")
            asyncio.run(update_labels())
            notification_add(f"{current_time()} Label assignments complete.")

        ### Channels DVR Overrides
        print(f"{current_time()} INFO: Updating Channels DVR metadata overrides...")
        asyncio.run(gather_channels_dvr_overrides())
        notification_add(f"{current_time()} Overrides for Channels DVR metadata complete.")

        ### End connecting SLM and Channels DVR metadata

        notification_add(f"{current_time()} Connecting SLM and Channels DVR metadata complete.")

    else:
        notification_add(f"{current_time()} INFO: Skipped 'Update Media in Channels DVR' due to Channels URL error.")

# Get file sort and file sort order from bookmarks
def get_file_sort_and_order(bookmarks, entry_id):
    file_sort = None
    file_sort_order = None

    for bookmark in bookmarks:
        if bookmark['entry_id'] == entry_id:

            if bookmark['override_program_sort'] != "na":

                if bookmark['override_program_sort'] == "remove":
                    file_sort = ''
                    file_sort_order = ''
                
                elif bookmark['override_program_sort'] == "manual":
                    file_sort = bookmark['override_program_sort']
                    file_sort_order = "forward"
                    
                else:
                    file_sort, file_sort_order = bookmark['override_program_sort'].split('_', 1)

            break

    return file_sort, file_sort_order

# Sort videos by selection
def get_sorted_episodes_videos(entry_id, file_sort, file_sort_order):
    bookmarks_statuses = read_data(csv_bookmarks_status)

    sorted_episodes_videos = []
    
    for bookmarks_status in bookmarks_statuses:
        if entry_id == bookmarks_status['entry_id'] and bookmarks_status['status'].lower() == "unwatched":
            sorted_episodes_videos.append(bookmarks_status)

    if sorted_episodes_videos:
        for sorted_episodes_video in sorted_episodes_videos:
            sorted_episodes_video['alpha_title'] = sorted_episodes_video['override_episode_title'] if sorted_episodes_video.get('override_episode_title') else sorted_episodes_video.get('season_episode')

    if file_sort and file_sort != '':
        if file_sort == "alpha" and file_sort_order == "forward":
            sorted_episodes_videos = sorted(sorted_episodes_videos, key=lambda x: sort_key(x["alpha_title"].casefold()))

        elif file_sort == "alpha" and file_sort_order == "reverse":
            sorted_episodes_videos = sorted(sorted_episodes_videos, key=lambda x: sort_key(x["alpha_title"].casefold()), reverse=True)

        elif file_sort == "dateoriginal" and file_sort_order == "forward":
            sorted_episodes_videos = sorted(
                sorted_episodes_videos,
                key=lambda x: (not x.get("original_release_date"), x.get("original_release_date") or "9999-12-31")
            )

        elif file_sort == "dateoriginal" and file_sort_order == "reverse":
            sorted_episodes_videos = sorted(
                sorted_episodes_videos,
                key=lambda x: (not x.get("original_release_date"), x.get("original_release_date") or "0000-01-01"),
                reverse=True
            )                             

        elif file_sort == "dateadded" and file_sort_order == "forward":
            sorted_episodes_videos = sorted_episodes_videos

        elif file_sort == "dateadded" and file_sort_order == "reverse":
            sorted_episodes_videos = list(reversed(sorted_episodes_videos))

        elif file_sort == "manual":
            sorted_episodes_videos = sorted(sorted_episodes_videos, key=lambda x: (x.get("manual_order", float("inf"))))

    return sorted_episodes_videos

# Asycnronous request of Stream Link reprocessing
async def get_reprocess_requests(channels_url):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as reprocess_session:
        tasks = [send_reprocess_requests(reprocess_session, f"{channels_url}/dvr/files/{stream_link_id}/reprocess") for stream_link_id in stream_link_ids_changed]
        try:
            await asyncio.gather(*tasks)
        except asyncio.TimeoutError:
            notification_add(f"{current_time()} ERROR: Reprocessing requests timed out.")

# Build list of Stream Link reprocess requests
async def send_reprocess_requests(reprocess_session, reprocess_url):
    try:
        await reprocess_session.put(reprocess_url)
    except asyncio.TimeoutError:
        notification_add(f"{current_time()} ERROR: Request for {reprocess_url} timed out.")

# Gets info from Channels DVR and adds it to SLM
def get_slm_channels_info():
    print(f"{current_time()} INFO: Importing Channels DVR info...")

    bookmarks = read_data(csv_bookmarks)
    bookmarks_statuses = read_data(csv_bookmarks_status)

    # Get dvr_files and dvr_groups as they are
    dvr_files = get_channels_dvr_json('dvr_files')
    dvr_groups = get_channels_dvr_json('dvr_groups')

    # Create a dictionary for efficient DVR file lookups
    dvr_files_lookup = {
        clean_comparison_path(dvr_file['Path']): dvr_file for dvr_file in dvr_files if dvr_file['Path']
    }

    bookmark_entry_id_to_channels_id_lookup = {}

    for bookmarks_status in bookmarks_statuses:
        remove_channels_id = True

        if bookmarks_status['stream_link_file']:
            stream_link_file_path_check = f"slm/{clean_comparison_path(bookmarks_status['stream_link_file']).split('slm/', 1)[1]}"

            if stream_link_file_path_check in dvr_files_lookup:
                entry_id = bookmarks_status['entry_id']
                
                if entry_id not in bookmark_entry_id_to_channels_id_lookup:
                    bookmark_entry_id_to_channels_id_lookup[entry_id] = {
                        'File ID': dvr_files_lookup[stream_link_file_path_check]['File ID'],
                        'Group ID': dvr_files_lookup[stream_link_file_path_check]['Group ID']
                    }
                
                bookmarks_status['channels_id'] = dvr_files_lookup[stream_link_file_path_check]['File ID']
                remove_channels_id = False

        if remove_channels_id:
            bookmarks_status['channels_id'] = ''

    for bookmark in bookmarks:
        remove_channels_id = True
        entry_id = bookmark['entry_id']

        if entry_id in bookmark_entry_id_to_channels_id_lookup:
            if bookmark['object_type'] == "MOVIE":
                bookmark['channels_id'] = bookmark_entry_id_to_channels_id_lookup[entry_id]['File ID']
            else:
                bookmark['channels_id'] = bookmark_entry_id_to_channels_id_lookup[entry_id]['Group ID']
            remove_channels_id = False

        if remove_channels_id:
            bookmark['channels_id'] = ''

    # Write updated bookmarks back to the file
    if bookmarks:
        write_data(csv_bookmarks, bookmarks)

    if bookmarks_statuses:
        write_data(csv_bookmarks_status, bookmarks_statuses)

    print(f"{current_time()} INFO: Finished importing Channels DVR info.")

    # Return dvr_files and dvr_groups as they are
    return dvr_files, dvr_groups

# Runs the process to update Labels in Channels DVR
async def update_labels():
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    bookmarks = read_data(csv_bookmarks)
    slm_labels = read_data(csv_slm_labels)
    slm_label_maps = read_data(csv_slm_label_maps)

    async with aiohttp.ClientSession() as session:
        tasks = [
            process_bookmark_labels(session, bookmark, slm_labels, slm_label_maps, channels_url)
            for bookmark in bookmarks
        ]
        await asyncio.gather(*tasks)

# Asynchronous function to process bookmark labels
async def process_bookmark_labels(session, bookmark, slm_labels, slm_label_maps, channels_url):
    channels_id = bookmark['channels_id']
    bookmark_item = f"{bookmark['title']} ({bookmark['release_year']}) | {bookmark['object_type']}"
    bookmark_label_maps = []
    bookmark_labels = []

    if channels_id is not None and channels_id != "":
        # Map labels
        for slm_label_map in slm_label_maps:
            if bookmark['entry_id'] == slm_label_map['entry_id']:
                bookmark_label_maps.append(slm_label_map['label_id'])

        for slm_label in slm_labels:
            if slm_label['label_id'] in bookmark_label_maps and slm_label['label_active'] == "On":
                bookmark_labels.append(slm_label['label_name'])

        # Set the base routes
        route = f"/dvr/files/{channels_id}" if bookmark['object_type'] == "MOVIE" else f"/dvr/groups/{channels_id}"
        url_base = f"{channels_url}{route}"

        # Fetch the current labels
        current_labels = await fetch_current_labels(session, url_base)
        if current_labels is None:
            return

        url = f"{url_base}/labels"

        # Delete labels not in bookmark_labels
        await delete_labels(session, url, current_labels, bookmark_labels, bookmark_item)

        # Add labels in bookmark_labels that are not in current_labels
        await add_labels(session, url, current_labels, bookmark_labels, bookmark_item)

# Asynchronous request to fetch current labels
async def fetch_current_labels(session, url_base):
    try:
        async with session.get(url_base, headers=url_headers) as response:
            response.raise_for_status()
            json_response = await response.json()  # Await the coroutine
            return json_response.get("Labels", [])  # Access the "Labels" key
    except aiohttp.ClientError as e:
        print(f"ERROR: Failed to fetch current labels for {url_base}: {e}")
        return None

# Asynchronous request to delete labels not in bookmark_labels
async def delete_labels(session, url, current_labels, bookmark_labels, bookmark_item):
    for current_label in current_labels:
        if current_label not in bookmark_labels or not bookmark_labels:
            delete_url = f"{url}/{urllib.parse.quote(current_label)}"
            try:
                async with session.delete(delete_url, headers=url_headers) as response:
                    response.raise_for_status()
                    print(f"{current_time()} INFO: Deleted label '{current_label}' from {bookmark_item}.")
            except aiohttp.ClientError as e:
                print(f"{current_time()} ERROR: Failed to delete label '{current_label}' from {bookmark_item}: {e}")

# Asynchronous request to add labels in bookmark_labels that are not in current_labels
async def add_labels(session, url, current_labels, bookmark_labels, bookmark_item):
    for bookmark_label in bookmark_labels:
        if bookmark_label not in current_labels or not current_labels:
            put_url = f"{url}/{urllib.parse.quote(bookmark_label)}"
            try:
                async with session.put(put_url, headers=url_headers) as response:
                    response.raise_for_status()
                    print(f"{current_time()} INFO: Added label '{bookmark_label}' to {bookmark_item}.")
            except aiohttp.ClientError as e:
                print(f"{current_time()} ERROR: Failed to add label '{bookmark_label}' to {bookmark_item}: {e}")

# Gathers the overrides to be sent to Channels DVR
async def gather_channels_dvr_overrides():
    bookmarks = read_data(csv_bookmarks)
    bookmarks_statuses = read_data(csv_bookmarks_status)

    base_files_route = f"/dvr/files/"
    base_groups_route = f"/dvr/groups/"
    object_type_lookup = {bookmark['entry_id']: bookmark['object_type'] for bookmark in bookmarks}
    override_program_sort_lookup = {bookmark['entry_id']: bookmark['override_program_sort'] for bookmark in bookmarks}

    async with aiohttp.ClientSession() as session:
        tasks = []

        for bookmark_status in bookmarks_statuses:
            channels_id = bookmark_status['channels_id']
            entry_id = bookmark_status['entry_id']
            object_type = object_type_lookup.get(entry_id, None)
            override_program_sort = override_program_sort_lookup.get(entry_id, "na")
            json_data = {"Airing": {}}
            run_put = False

            if not channels_id in [None, '']:
                route = f"{base_files_route}{channels_id}"

                if bookmark_status['override_duration']:
                    json_data["Duration"] = int(bookmark_status['override_duration'])
                    run_put = True

                airing_data = {}
                if bookmark_status['override_episode_title']:
                    airing_data["EpisodeTitle"] = bookmark_status['override_episode_title']
                if bookmark_status['override_summary']:
                    airing_data["Summary"] = bookmark_status['override_summary']
                if bookmark_status['override_image']:
                    airing_data["Image"] = bookmark_status['override_image']
                if object_type == "VIDEO":
                    if bookmark_status['original_release_date']:
                        airing_data["OriginalDate"] = bookmark_status['original_release_date']
                    if bookmark_status['manual_order'] and override_program_sort == "manual":
                        airing_data["SeasonNumber"] = 1
                        airing_data["EpisodeNumber"] = int(bookmark_status['manual_order'])

                if airing_data:
                    json_data["Airing"] = airing_data
                    run_put = True

                if run_put:
                    tasks.append(put_channels_dvr_json_async(session, route, json_data))

        for bookmark in bookmarks:
            channels_id = bookmark['channels_id']
            run_put = False
            file_sort = None
            file_sort_order = None

            if not channels_id in [None, '']:

                if bookmark['object_type'] == 'MOVIE':
                    route = f"{base_files_route}{channels_id}"
                    json_data = {"Airing": {}}
                    airing_data = {}
                    if bookmark['override_program_title']:
                        airing_data["Title"] = bookmark['override_program_title']
                    if airing_data:
                        json_data["Airing"] = airing_data
                        run_put = True

                else:
                    route = f"{base_groups_route}{channels_id}"
                    json_data = {}
                    if bookmark['override_program_title']:
                        json_data["Name"] = bookmark['override_program_title']
                        run_put = True
                    if bookmark['override_program_summary']:
                        json_data["Summary"] = bookmark['override_program_summary']
                        run_put = True
                    if bookmark['override_program_sort'] != "na":
                        file_sort, file_sort_order = get_file_sort_and_order(bookmarks, bookmark['entry_id'])
                        if file_sort in ["alpha", "remove"]:
                            json_data["FileSort"] = file_sort
                        elif file_sort == "manual":
                            json_data["FileSort"] = "season"
                        elif file_sort == "dateoriginal":
                            json_data["FileSort"] = "originalAirDate"
                        elif file_sort == "dateadded":
                            json_data["FileSort"] = "createdAt"
                        json_data["FileSortOrder"] = file_sort_order
                        run_put = True
                    if bookmark['override_program_image_type'] != "na":
                        if bookmark['override_program_image_type'] == "manual" and bookmark['override_program_image_manual']:
                            json_data["Image"] = bookmark['override_program_image_manual']
                        elif bookmark['override_program_image_type'] == "first":
                            sorted_episodes_videos = get_sorted_episodes_videos(bookmark['entry_id'], file_sort, file_sort_order)
                            if sorted_episodes_videos:
                                json_data["Image"] = sorted_episodes_videos[0]['override_image']
                            else:
                                json_data["Image"] = ""
                        else:
                            json_data["Image"] = ""
                        run_put = True

                if run_put:
                    tasks.append(put_channels_dvr_json_async(session, route, json_data))

        await asyncio.gather(*tasks)

# Automation - Generate Stream Links for New & Recent Releases Only
def run_slm_new_recent_releases():
    print("\n==========================================================")
    print("|                                                        |")
    print("|           SLM: New & Recent Releases Process           |")
    print("|                                                        |")
    print("==========================================================\n")

    notification_add(f"{current_time()} Beginning SLM New & Recent Releases process...")

    set_slm_process_active_flag('process_on')

    start_time = time.time()

    # Get new episodes
    get_new_episodes(None)
    time.sleep(2)
    
    # Generate Stream Links for New & Recent Releases
    original_release_date_list = get_original_release_date_list()
    generate_stream_links(original_release_date_list)
    time.sleep(2)

    # Run scan in Channels DVR
    if slm_channels_dvr_integration:
        # Temp turn off Prune
        settings = read_data(csv_settings)
        channels_prune = settings[7]["settings"]
        settings[7]["settings"] = "Off"
        write_data(csv_settings, settings)

        # Run scan
        prune_scan_channels()

        # Turn Prune back on
        settings[7]["settings"] = channels_prune
        write_data(csv_settings, settings)

        time.sleep(2)

    end_time = time.time()

    elapsed_seconds = end_time - start_time

    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    notification_add(f"{current_time()} SLM New & Recent Releases process completed in {int(hours)} hours | {int(minutes)} minutes | {int(seconds)} seconds.")

    set_slm_process_active_flag('process_off')

# Create a list of Node IDs for New & Recent Releases
def get_original_release_date_list():
    print("\n==========================================================")
    print("|                                                        |")
    print("|               Get Original Release Dates               |")
    print("|                                                        |")
    print("==========================================================\n")

    print(f"{current_time()} Gathering original release dates...")

    bookmarks = read_data(csv_bookmarks)
    auto_bookmarks = [
        bookmark for bookmark in bookmarks 
        if bookmark['bookmark_action'] not in ["Hide", "Disable Get New Episodes"]
    ]
    bookmarks_statuses = read_data(csv_bookmarks_status)
    settings = read_data(csv_settings)
    slm_new_recent_releases_when = settings[35]["settings"]

    current_date = datetime.datetime.now()
    original_release_date_list = []

    for auto_bookmark in auto_bookmarks:
        for bookmarks_status in bookmarks_statuses:
            if auto_bookmark['entry_id'] == bookmarks_status['entry_id']:
                if bookmarks_status['status'].lower() == "unwatched":

                    if (
                        ( auto_bookmark['object_type'] in ["MOVIE", "SHOW"] and not auto_bookmark['entry_id'].startswith('slm') ) or
                        ( auto_bookmark['object_type'] == "VIDEO" and not auto_bookmark['entry_id'].startswith('int') )
                    ):

                        node_id = None
                        original_release_date_raw = None
                        original_release_date = None

                        if auto_bookmark['object_type'] == "MOVIE":
                            node_id = bookmarks_status['entry_id']
                        elif auto_bookmark['object_type'] == "SHOW":
                            node_id = bookmarks_status['season_episode_id']
                        elif auto_bookmark['object_type'] == "VIDEO":
                            node_id = bookmarks_status['season_episode']
                        else:
                            print(f"{current_time()} ERROR: Invalid object_type")
                            continue

                        if node_id:
                            country_code = auto_bookmark['country_code']
                            language_code = auto_bookmark['language_code']

                            if bookmarks_status['original_release_date'] is None or bookmarks_status['original_release_date'] == '':

                                if auto_bookmark['object_type'] in ["MOVIE", "SHOW"]:
                                    original_release_date_raw =  get_movie_show_metadata_item(node_id, country_code, language_code, 'originalReleaseDate')

                                elif auto_bookmark['object_type'] == "VIDEO" and bookmarks_status['special_action'] == 'Make SLM Stream' and not bookmarks_status['stream_link_override'] in [None, '']:
                                    original_release_date_raw, throwaway_override_episode_title, throwaway_override_summary, throwaway_override_image, throwaway_override_duration = get_video_metadata(bookmarks_status['stream_link_override'])

                                if original_release_date_raw:
                                    bookmarks_status['original_release_date'] = original_release_date_raw
                                    
                            else:
                                original_release_date_raw = bookmarks_status['original_release_date']
                            
                        if original_release_date_raw is not None and original_release_date_raw != '':
                            original_release_date = datetime.datetime.strptime(original_release_date_raw, "%Y-%m-%d")
                            time_difference = current_date - original_release_date
                            hours_since_release = int(time_difference.total_seconds() // 3600)

                            if 0 <= int(hours_since_release) <= int(slm_new_recent_releases_when):
                                original_release_date_list.append(node_id)

    write_data(csv_bookmarks_status, bookmarks_statuses)

    print(f"{current_time()} Finished gathering original release dates.")

    return original_release_date_list

# Gets the original release date or other info based on query type for individual movies/episodes
def get_movie_show_metadata_item(node_id, country_code, language_code, query_type):
    results = []
    results_json = []
    result = None

    _GRAPHQL_GetOriginalReleaseDate = """
        query GetOriginalReleaseDate($nodeId: ID!, $country: Country!, $language: Language!) {
            node(id: $nodeId) {
                id
                __typename
                ... on MovieOrShowOrSeasonOrEpisode {
                    content(country: $country, language: $language) {
                        originalReleaseDate
                        runtime
                        title
                        shortDescription
                    }
                }
            }
        }
    """

    json_data = {
        'query': _GRAPHQL_GetOriginalReleaseDate,
        'variables': {
            "platform": "WEB",
            "nodeId": node_id,
            "country": country_code,
            "language": language_code,
        },
        'operationName': 'GetOriginalReleaseDate',
    }

    try:
        results = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
        results_json = results.json()
        node_data = results_json.get('data', {}).get('node', {})
        if node_data is not None:
            if query_type == 'originalReleaseDate':
                result = node_data.get('content', {}).get('originalReleaseDate', None)
                if result is None or result == '' or result =='None':
                    result = "1900-01-01"

            elif query_type == 'runtime':
                result = node_data.get('content', {}).get('runtime', None)
                if result is not None and result != '':
                    result = int(result) * 60
                    if int(result) == 0:
                        result = ''

            elif query_type == 'title':
                result = node_data.get('content', {}).get('title', None)

            elif query_type == 'shortDescription':
                result = node_data.get('content', {}).get('shortDescription', None)

        else:
            if query_type == 'originalReleaseDate':
                result = "9999-12-31"
            else:
                result = ''

    except aiohttp.ClientError as e:
        print(f"{current_time()} WARNING: {e}. Skipping '{node_id}', please try again.")

    return result

# Automation - Reset Channels DVR Passes
def run_reset_channels_passes():
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    passes_url = '/dvr/rules/'
    channels_passes_url = f"{channels_url}{passes_url}"
    passes_pause = '/pause'
    passes_resume = '/resume'
    passes_message = ''
    passes_results_base = None
    passes_results_base_json = None
    passes_results_dictionary = []
    passes_results_dictionary_active = []
    passes_error = None

    notification_add(f"{current_time()} Beginning 'Reset Channels DVR Passes' Automation...")

    channels_url_okay = check_channels_url(None)

    if channels_url_okay:
        try:
            passes_results_base = requests.get(channels_passes_url, headers=url_headers)
        except requests.RequestException as e:
            passes_message = f"{current_time()} ERROR: During process, received {e}. Please try again."
    else:
        passes_message = f"{current_time()} ERROR: Channels URL is incorrect. Please update in the 'Settings' area."

    if passes_results_base:
        passes_results_base_json = passes_results_base.json()

        for result in passes_results_base_json:
            passes_result_paused = result.get("Paused", '')
            passes_result_id = result.get("ID", '')
            passes_result_priority = result.get("Priority", '')

            passes_results_dictionary.append({
                "passes_result_paused": passes_result_paused,
                "passes_result_id": passes_result_id,
                "passes_result_priority": passes_result_priority
            })

        for item in passes_results_dictionary:
            if item['passes_result_paused'] == False:
                passes_results_dictionary_active.append({
                    "passes_result_id": item['passes_result_id'],
                    "passes_result_priority": item['passes_result_priority']
                })

        # First sort with lowest priority on top to pause
        passes_results_dictionary_active.sort(key=lambda x: int(x.get("passes_result_priority", float("inf"))))
        for item in passes_results_dictionary_active:
            print(f"{current_time()} INFO: Pausing pass with the id '{item['passes_result_id']}'.")
            url = f"{channels_passes_url}{item['passes_result_id']}{passes_pause}"
            try:
                requests.put(url)
            except requests.RequestException as e:
                notification_add(f"{current_time()} WARNING: For pass with the id '{item['passes_result_id']}', received error {e}. Skipping pause...")
                passes_error = True

        # Resort with highest priority on top to resume
        passes_results_dictionary_active.sort(key=lambda x: int(x.get("passes_result_priority", float("inf"))), reverse=True)
        for item in passes_results_dictionary_active:
            print(f"{current_time()} INFO: Resuming pass with the id '{item['passes_result_id']}'.")
            url = f"{channels_passes_url}{item['passes_result_id']}{passes_resume}"
            try:
                requests.put(url)
            except requests.RequestException as e:
                notification_add(f"{current_time()} WARNING: For pass with the id '{item['passes_result_id']}', received error {e}. Skipping resume...")
                passes_error = True

        if passes_error:
            passes_message = f"{current_time()} ERROR: 'Reset Channels DVR Passes' completed with an issue, see log for details."
        else:
            passes_message = f"{current_time()} INFO: 'Reset Channels DVR Passes' completed successfully."

    if passes_message is not None and passes_message != '':
        print(f"{passes_message}")

    notification_add(f"{current_time()} Finished 'Reset Channels DVR Passes' Automation.")

    return passes_message

# Automation - Refresh Channels DVR m3u Playlists
def run_refresh_channels_m3u_playlists():
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    refresh_channels_m3u_playlists_exclude_never_refresh = settings[60]["settings"] # [60] MTM: Automation - Refresh Channels DVR m3u Playlists - Exclude 'Never Refresh URL' On/Off
    providers_web = '/dvr/lineups'
    refresh_web_pt1 = '/providers/m3u/sources/'
    refresh_web_pt3 = '/refresh'
    providers_url = f"{channels_url}{providers_web}"
    refresh_url_pt1 = f"{channels_url}{refresh_web_pt1}"
    message = ''
    automation_error = None
    providers_results_base = None
    providers_results_base_json = None
    providers_results_dictionary = []

    notification_add(f"{current_time()} Beginning 'Refresh Channels DVR m3u Playlists' Automation...")

    channels_url_okay = check_channels_url(None)

    if channels_url_okay:
        try:
            providers_results_base = requests.get(providers_url, headers=url_headers)
        except requests.RequestException as e:
            message = f"{current_time()} ERROR: During process, received {e}. Please try again."
    else:
        message = f"{current_time()} ERROR: Channels URL is incorrect. Please update in the 'Settings' area."

    if providers_results_base:
        providers_results_base_json = providers_results_base.json()
        if providers_results_base_json:
                for key in providers_results_base_json.keys():
                    if key.startswith("M3U-"):
                        providers_results_dictionary.append(key[4:])

        if providers_results_dictionary:
            for provider in providers_results_dictionary:
                details_url = f"{refresh_url_pt1}{provider}"
                details_response = None
                details_json = None
                detail_refresh = None

                try:
                    details_response = requests.get(details_url, headers=url_headers)
                    details_response.raise_for_status()
                    details_json = details_response.json()
                    detail_refresh = details_json.get('refresh', None)
                except requests.RequestException as e:
                    print(f"{current_time()} ERROR: For m3u Playlist '{provider}', received error {e}. Skipping refresh...")

                if refresh_channels_m3u_playlists_exclude_never_refresh == "Off" or (refresh_channels_m3u_playlists_exclude_never_refresh == "On" and detail_refresh):
                    refresh_url = f"{details_url}{refresh_web_pt3}"

                    for attempt in range(3):
                        try:
                            requests.post(refresh_url, timeout=60)
                            break  # Exit the retry loop if the request is successful
                        except requests.Timeout:
                            if attempt < 2:  # Only log a warning if we will retry
                                print(f"{current_time()} WARNING: For m3u Playlist '{provider}', request timed out. Retrying...")
                            else:
                                print(f"{current_time()} ERROR: For m3u Playlist '{provider}', request timed out. Skipping refresh...")
                                automation_error = True
                        except requests.RequestException as e:
                            print(f"{current_time()} ERROR: For m3u Playlist '{provider}', received error {e}. Skipping refresh...")
                            automation_error = True
                            break  # Exit the retry loop on other exceptions

                else:
                    print(f"{current_time()} INFO: For m3u Playlist '{provider}', 'Never Refresh URL' is set. Skipping refresh...")

            if automation_error:
                message = f"{current_time()} ERROR: 'Refresh Channels DVR m3u Playlists' completed with an issue, see log for details."
            else:
                message = f"{current_time()} INFO: 'Refresh Channels DVR m3u Playlists' completed successfully."

        else:
            message = f"{current_time()} INFO: For 'Refresh Channels DVR m3u Playlists', no matching valid m3u playlists were found."

    notification_add(f"{current_time()} Finished 'Refresh Channels DVR m3u Playlists' Automation.")

    return message

# Automation - In Channels DVR, remove files older than a certain number of day and empty directories
def run_channels_remove_old_files_empty_directories(action_type):
    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]                            # [1] Stream Link/Files Base Directory
    mtm_channels_remove_old_logs_recording_days = settings[54]["settings"]  # [54] MTM: Remove old Channels DVR Recording Logs Days to Keep
    mtm_channels_remove_old_backups_days = settings[58]["settings"]         # [58] MTM: Remove old Channels DVR Backups Days to Keep
    message = ''

    if action_type == "channels_recording_logs":
        base_directory = os.path.join(channels_directory, "Logs", "recording")
        num_days = int(mtm_channels_remove_old_logs_recording_days)
        type_description = "Recording Logs"
    elif action_type == "channels_backups":
        base_directory = os.path.join(channels_directory, "Database")
        num_days = int(mtm_channels_remove_old_backups_days)
        type_description = "Backups"
    else:
        base_directory = None
        num_days = None
        message = f"{current_time()} ERROR: Invalid type for Channels DVR old files and empty directories removal."
        print(message)

    if base_directory and num_days:
        notification_add(f"{current_time()} Beginning 'Remove Old Channels DVR {type_description}' Automation...")
        remove_old_files_and_empty_directories(base_directory, num_days)
        message = f"{current_time()} INFO: 'Remove Old Channels DVR {type_description}' completed. See logs for details."
        notification_add(f"{current_time()} Finished 'Remove Old Channels DVR {type_description}' Automation.")

    return message

# Files webpage
@app.route('/files', methods=['GET', 'POST'])
def webpage_files():
    global select_file_prior

    table_html = None
    replace_message = None

    file_lists = [
        {'file_name': 'Settings', 'file': csv_settings }
    ]

    stream_link_file_manager_file_lists = [
        {'file_name': 'Streaming Services', 'file': csv_streaming_services },
        {'file_name': 'Subscribed Video Channels', 'file': csv_slm_subscribed_video_channels },
        {'file_name': 'Provider Groups', 'file': csv_provider_groups },
        {'file_name': 'Stream Link Mappings', 'file': csv_slmappings },
        {'file_name': 'Bookmarks', 'file': csv_bookmarks },
        {'file_name': 'Bookmarks Statuses', 'file': csv_bookmarks_status },
        {'file_name': 'Labels', 'file': csv_slm_labels },
        {'file_name': 'Label Maps', 'file': csv_slm_label_maps }
    ]

    plm_file_lists = [
        {'file_name': 'Playlists', 'file': csv_playlistmanager_playlists },
        {'file_name': 'Parent Station', 'file': csv_playlistmanager_parents },
        {'file_name': 'Child to Parent Station Map', 'file': csv_playlistmanager_child_to_parent },
        {'file_name': 'All Stations', 'file': csv_playlistmanager_combined_m3us },
        {'file_name': 'Station Mappings', 'file': csv_playlistmanager_station_mappings }
    ]

    plm_streaming_stations_file_lists = [
        {'file_name': 'Streaming Stations', 'file': csv_playlistmanager_streaming_stations }
    ]

    if slm_stream_link_file_manager:
        for stream_link_file_manager_file_list in stream_link_file_manager_file_lists:
            file_lists.append({'file_name': stream_link_file_manager_file_list['file_name'], 'file': stream_link_file_manager_file_list['file']})

    if slm_playlist_manager:
        for plm_file_list in plm_file_lists:
            file_lists.append({'file_name': plm_file_list['file_name'], 'file': plm_file_list['file']})

    if plm_streaming_stations:
        for plm_streaming_stations_file_list in plm_streaming_stations_file_lists:
            file_lists.append({'file_name': plm_streaming_stations_file_list['file_name'], 'file': plm_streaming_stations_file_list['file']})

    if request.method == 'POST':
        action = request.form['action']

        select_file_input = request.form.get('select_file')
        select_file_prior = select_file_input
        select_file_input_csv = None
        for file_list in file_lists:
            if file_list['file_name'] == select_file_input:
                select_file_input_csv = file_list['file']
                break

        if action == 'view_file':
            table_html = view_csv(select_file_input_csv, "csv", None)
        elif action == 'export_file':
            return export_csv(select_file_input_csv)
        elif action == 'replace_file':
            replace_message = replace_csv(select_file_input_csv, 'file_file')

    return render_template(
        'main/general_files.html',
        segment='files',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        table_html=table_html,
        replace_message=replace_message,
        html_file_lists = file_lists,
        html_select_file_prior = select_file_prior
    )

# Makes CSV file able to be viewable in HTML
def view_csv(csv_file, type, image_flag):
    if type == "csv":
        data = read_data(csv_file)
    elif type == "library":
        data = csv_file

    if data is None:
        return "Error reading data"

    if not data:
        return "No Data"

    headers = data[0].keys()
    table_html = '<thead><tr>'
    for header, value in zip(headers, data[0].values()):
        if is_image_url(value) and image_flag:
            table_html += f'<th style="text-align: center;"><input type="text" readonly style="background-color: #d1cdcde5; width: 10%;"><br>{header}</th>'
        else:
            table_html += f'<th style="text-align: center;"><input type="text" class="filter-input"><br>{header}</th>'
    table_html += '</tr></thead><tbody>'

    for row in data:
        table_html += '<tr>'
        for value in row.values():
            if is_image_url(value) and image_flag:
                table_html += f'<td><img src="{value}" class="image-cell" alt="Image"></td>'
            else:
                table_html += f'<td>{value}</td>'
        table_html += '</tr>'

    table_html += '</tbody>'

    return render_template_string(table_html)

# Check for common image extensions and presence of a dot (.) before the extension
def is_image_url(url):
    response = None
    extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".svg", ".psd",
                  ".raw", ".arw", ".cr2", ".nef", ".orf", ".dng", ".hdr", ".jxr", ".pcd", ".eps")
    
    if isinstance(url, str) and url:
        if url.startswith(('http://', 'https://')) and any(ext in url.lower() for ext in extensions):
            response = True

    return response

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
    with open(log_filename_fullpath, 'r', encoding="utf-8", errors='ignore') as file:
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
        'main/general_logs.html',
        segment='logs',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_log_filename_fullpath=log_filename_fullpath,
        html_page_lines=page_lines,
        html_page=page,
        html_has_previous=has_previous,
        html_has_next=has_next,
        total_pages=total_pages
    )

# Settings webpage and actions
@app.route('/settings', methods=['GET', 'POST'])
def webpage_settings():
    global channels_url_prior
    global slm_playlist_manager
    global slm_stream_link_file_manager
    global slm_channels_dvr_integration
    global slm_media_players_integration
    global slm_media_tools_manager
    settings_anchor_id = None
    run_empty_row = None

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    if channels_url_prior is None or channels_url_prior == '':
        channels_url_prior = channels_url
    channels_directory = settings[1]["settings"]
    channels_prune = settings[7]["settings"]
    channels_labels = settings[50]["settings"]                      # [50] SLM: Update Labels in Channels DVR On/Off

    settings_articles = []
    settings_articles_raw = settings[71]["settings"]
    if settings_articles_raw:
        if isinstance(settings_articles_raw, str):
            try:
                settings_articles = ast.literal_eval(settings_articles_raw)
            except (ValueError, SyntaxError):
                print(f"{current_time()} ERROR: For 'Articles', unable to convert to a list.")

    channels_url_message = ""
    channels_directory_message = ""
    advanced_experimental_message = ""

    action_to_anchor = {
        'channels_url': 'channels_url_anchor',
        'channels_directory': 'channels_directory_anchor',
        'channels_prune': 'advanced_experimental_anchor',
        'channels_labels': 'advanced_experimental_anchor',
        'playlist_manager': 'advanced_experimental_anchor',
        'stream_link_file_manager': 'advanced_experimental_anchor',
        'channels_dvr_integration': 'advanced_experimental_anchor',
        'media_tools_manager': 'advanced_experimental_anchor',
        'settings_articles': 'settings_articles_anchor'
    }

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
        channels_labels_input = request.form.get('channels_labels')
        playlist_manager_input = request.form.get('playlist_manager')
        stream_link_file_manager_input = request.form.get('stream_link_file_manager')
        channels_dvr_integration_input = request.form.get('channels_dvr_integration')
        media_players_integration_input = request.form.get('media_players_integration')
        media_tools_manager_input = request.form.get('media_tools_manager')
        settings_articles_input = [tag['value'].casefold() for tag in json.loads(request.form.get('settings_articles', '[]')) if 'value' in tag]

        for prefix, anchor_id in action_to_anchor.items():
            if settings_action.startswith(prefix):
                settings_anchor_id = anchor_id
                break

        if settings_action in [
            'channels_url_cancel',
            'channels_url_save',
            'channels_directory_save',
            'channels_dvr_integration_save',
            'settings_articles_save',
            'channels_url_test',
            'channels_url_scan'
        ]:

            if settings_action in [
                'channels_url_save',
                'channels_directory_save',
                'channels_dvr_integration_save',
                'settings_articles_save',
                'channels_url_scan'
            ]:

                if settings_action in [
                    'channels_url_save',
                    'channels_directory_save',
                    'channels_dvr_integration_save',
                    'settings_articles_save',
                    'channels_url_scan'
                ]:

                    if settings_action == 'channels_url_save':
                        settings[0]["settings"] = channels_url_input
                        channels_url_prior = channels_url_input

                    elif settings_action == 'channels_url_scan':
                        settings[0]["settings"], channels_url_message = get_channels_url()
                        channels_url_prior = settings[0]["settings"]

                    elif settings_action == 'channels_directory_save':
                        settings[1]["settings"] = channels_directory_input
                        current_directory = channels_directory_input                       

                    elif settings_action == 'channels_dvr_integration_save':
                        # Channels DVR Integration
                        settings[24]["settings"] = "On" if channels_dvr_integration_input == 'on' else "Off"
                        if channels_dvr_integration_input == 'on':
                            slm_channels_dvr_integration = True
                        else:
                            slm_channels_dvr_integration = None

                        if media_players_integration_input == 'on':
                            if settings[24]["settings"] == "On":
                                advanced_experimental_message = f"{current_time()} ERROR: 'Media Players Integration' cannot be initiated when 'Channels DVR Integration' is active. Please disable 'Channels DVR Integration' if you want to use 'Media Players Integration'."
                                media_players_integration_input = ''

                        settings[72]["settings"] = "On" if media_players_integration_input == 'on' else "Off"
                        if media_players_integration_input == 'on':
                            slm_media_players_integration = True
                        else:
                            slm_media_players_integration = None

                        # Channels DVR Prune
                        settings[7]["settings"] = "On" if channels_prune_input == 'on' else "Off"

                        # Channels DVR Labels
                        settings[50]["settings"] = "On" if channels_labels_input == 'on' else "Off"

                        # On-Demand: Stream Link/File Manager [SLM]
                        settings[23]["settings"] = "On" if stream_link_file_manager_input == 'on' else "Off"
                        if stream_link_file_manager_input == 'on':
                            slm_stream_link_file_manager = True
                        else:
                            slm_stream_link_file_manager = None

                        # Linear: Playlist Manager [PLM]
                        settings[10]["settings"] = "On" if playlist_manager_input == 'on' else "Off"
                        if playlist_manager_input == 'on':
                            slm_playlist_manager = True
                            plm_csv_files = [
                                csv_playlistmanager_playlists,
                                csv_playlistmanager_parents,
                                csv_playlistmanager_child_to_parent,
                                csv_playlistmanager_combined_m3us,
                                csv_playlistmanager_station_mappings
                            ]
                            for plm_csv_file in plm_csv_files:
                                check_and_create_csv(plm_csv_file)
                            create_directory(playlists_uploads_dir)
                        else:
                            slm_playlist_manager = None

                        # Tools: Media Tools Manager [MTM]
                        settings[28]["settings"] = "On" if media_tools_manager_input == 'on' else "Off"
                        if media_tools_manager_input == 'on':
                            slm_media_tools_manager = True
                        else:
                            slm_media_tools_manager = None

                    elif settings_action == 'settings_articles_save':
                        settings[71]["settings"] = settings_articles_input

                    csv_to_write = csv_settings
                    data_to_write = settings

                write_data(csv_to_write, data_to_write)
                if run_empty_row:
                    remove_empty_row(csv_to_write)

            elif settings_action == 'channels_url_cancel':
                channels_url_prior = channels_url

            elif settings_action == 'channels_url_test':
                channels_url_prior = channels_url_input
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

        settings = read_data(csv_settings)
        channels_url = settings[0]["settings"]
        if channels_url_prior is None or channels_url_prior == '':
            channels_url_prior = channels_url
        channels_directory = settings[1]["settings"]
        channels_prune = settings[7]["settings"]
        channels_labels = settings[50]["settings"]                      # [50] SLM: Update Labels in Channels DVR On/Off
        settings_articles = []
        settings_articles_raw = settings[71]["settings"]
        if settings_articles_raw:
            if isinstance(settings_articles_raw, str):
                try:
                    settings_articles = ast.literal_eval(settings_articles_raw)
                except (ValueError, SyntaxError):
                    print(f"{current_time()} ERROR: For 'Articles', unable to convert to a list.")

    if channels_directory_message in [None, '']:

        if slm_channels_dvr_integration:
            channels_directory_message = f"{current_time()} INFO: For Channels DVR users, the 'Stream Links/Files and Media Base Directory' should be set to the main Channels folder that contains the 'Imports' directory, among others like 'Database', 'Logs', 'Movies', etc...."

        elif slm_media_players_integration:
            channels_directory_message = f"{current_time()} INFO: For Media Players users, the 'Stream Links/Files and Media Base Directory' should be set to a location that is accesible for your media consumption program that can launch Stream Links/Files."

        if ( slm_channels_dvr_integration or slm_media_players_integration ):
            channels_directory_message += f" SLM will create structure under this location that goes '/Imports/[Movies | TV | Videos]/slm', and then further under those for TV Shows and Video Groups as needed for each program."

        if slm_channels_dvr_integration:
            channels_directory_message += f" Setting this incorrectly will mean Channels cannot see the Stream Link/File files, and therefore the programs will not appear in the interface. Additionally, this selection is used for some other functions like MTM Automation for managing Channels DVR logs and backups. Thus, even if you are not using SLM, this must be set correctly for this program to function normally."

    response = make_response(render_template(
        'main/general_settings.html',
        segment='settings',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_players_integration = slm_media_players_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_plm_check_child_station_status_global = plm_check_child_station_status_global,
        html_settings_anchor_id = settings_anchor_id,
        html_channels_url = channels_url,
        html_channels_url_prior = channels_url_prior,
        html_channels_directory = channels_directory,
        html_channels_prune = channels_prune,
        html_channels_labels = channels_labels,
        html_channels_url_message = channels_url_message,
        html_current_directory = current_directory,
        html_subdirectories = get_subdirectories(current_directory),
        html_channels_directory_message = channels_directory_message,
        html_advanced_experimental_message = advanced_experimental_message,
        html_settings_articles = settings_articles,
        html_base_articles = base_articles
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'

    return response

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
        print(f"{current_time()} WARNING: Channels URL not found at {channels_url}")
        print(f"{current_time()} WARNING: Please change Channels URL in settings")

    return channels_url_okay

# Attempts to find the Channels DVR path
def find_channels_dvr_path():
    global timeout_occurred
    timeout_occurred = False
    channels_dvr_path = script_dir
    channels_dvr_path_search = None
    root_path = os.path.abspath(os.sep)
    search_directory = "Imports"

    print(f"{current_time()} Searching for Channels DVR folder...")

    # Search times out after 60 seconds
    timer = threading.Timer(60, timeout_handler)
    timer.start()

    try:
        for root, dirs, _ in os.walk(root_path):
            if timeout_occurred:
                raise TimeoutError # Timeout if serach going for too long
            if search_directory in dirs or search_directory.lower() in dirs:
                if os.path.abspath(os.path.join(root)).lower().endswith("dvr") or os.path.abspath(os.path.join(root)).lower().endswith("channels_folder"):
                    channels_dvr_path_search = os.path.abspath(os.path.join(root))
                    break  # Stop searching once found
    except TimeoutError:
        print(f"{current_time()} INFO: Search timed out. Continuing to next step...")
    except KeyboardInterrupt:
        print(f"{current_time()} INFO: Search interrupted by user. Continuing to next step...")
    finally:
        timer.cancel()  # Disable the timer

    if channels_dvr_path_search:
        print(f"{current_time()} INFO: Channels DVR folder found!")
        channels_dvr_path = channels_dvr_path_search
    else:
        if os.path.exists(docker_channels_dir):
            print(f"{current_time()} INFO: Channels DVR folder not found, setting to Docker default...")
            channels_dvr_path = docker_channels_dir
        else:
            print(f"{current_time()} INFO: Channels DVR folder not found, defaulting to current directory. Please set your 'Stream Links/Files and Media Base Directory' in 'Settings'.")

    print(f"{current_time()} INFO: 'Stream Links/Files and Media Base Directory' set to '{channels_dvr_path}'. Please update in 'Settings' if this is incorrect or another location is desired.")

    return channels_dvr_path

# Displays the list of subdirectories in the given directory.
def get_subdirectories(directory):
    return [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]

# Catch-all for non-named pages
@app.route('/<template>')
def webpage_route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/main/FILE.html
        return render_template(
            "main/" + template,
            segment = segment,
            html_slm_version = slm_version,
            html_gen_upgrade_flag = gen_upgrade_flag,
            html_slm_playlist_manager = slm_playlist_manager,
            html_slm_stream_link_file_manager = slm_stream_link_file_manager,
            html_slm_channels_dvr_integration = slm_channels_dvr_integration,
            html_slm_media_players_integration = slm_media_players_integration,
            html_slm_media_tools_manager = slm_media_tools_manager,
            html_plm_streaming_stations = plm_streaming_stations
        )

    except TemplateNotFound:
        return render_template(
            'main/page-404.html',
            html_slm_version = slm_version,
            html_gen_upgrade_flag = gen_upgrade_flag,
            html_slm_playlist_manager = slm_playlist_manager,
            html_slm_stream_link_file_manager = slm_stream_link_file_manager,
            html_slm_channels_dvr_integration = slm_channels_dvr_integration,
            html_slm_media_players_integration = slm_media_players_integration,
            html_slm_media_tools_manager = slm_media_tools_manager,
            html_plm_streaming_stations = plm_streaming_stations
        ), 404

    except:
        return render_template(
            'main/page-500.html',
            html_slm_version = slm_version,
            html_gen_upgrade_flag = gen_upgrade_flag,
            html_slm_playlist_manager = slm_playlist_manager,
            html_slm_stream_link_file_manager = slm_stream_link_file_manager,
            html_slm_channels_dvr_integration = slm_channels_dvr_integration,
            html_slm_media_players_integration = slm_media_players_integration,
            html_slm_media_tools_manager = slm_media_tools_manager,
            html_plm_streaming_stations = plm_streaming_stations
        ), 500

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

# Web Error Handler
@app.after_request
def web_errors(response):
    if response.status_code >= 400:
        print(f"{current_time()} ERROR: Webpage responded... {response.status}")
        print(f"    Client IP: {request.remote_addr}")
        print(f"    Method: {request.method}")
        print(f"    URL: {request.url}")
        print("    Headers: ")
        for header, value in request.headers.items():
            print(f"        {header}: {value}")
        print(f"    User Agent: {request.user_agent}")
        print(f"    Args: {request.args}")
        if request.data:
            print(f"    Data: {request.data.decode('utf-8', 'ignore')}")
        else:
            print(f"    Data: No data")
        if request.form:
            print(f"    Form Data: {request.form}")

    return response

### Administative Functions
# Current date/time for logging
def current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + ": "

# Handler for timeout errors
def timeout_handler():
    global timeout_occurred
    timeout_occurred = True

# Remove invalid characters (e.g., colons, slashes, etc.)
def sanitize_name(name):
    sanitized = re.sub(r'[\\/:*?"<>|]', '', name)
    return sanitized

# Alphabetic sort ignoring user controlled articles and non-alphanumeric characters
def sort_key(title):
    cleaned_title = ''
    articles = []

    settings = read_data(csv_settings)
    articles_raw = settings[71]["settings"]

    if articles_raw:
        if isinstance(articles_raw, str):
            try:
                articles = ast.literal_eval(articles_raw)
            except (ValueError, SyntaxError):
                print(f"{current_time()} ERROR: For 'Articles', unable to convert to a list.")
    
    # Remove non-alphanumeric characters
    cleaned_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)

    # Remove articles
    if articles:
        words = cleaned_title.casefold().split()
        if words and words[0] in articles:
            cleaned_title = " ".join(words[1:])

    return cleaned_title.casefold()

# Normalize the file path for systems that can't handle certain characters like 'é'
def normalize_path(path):
    return unicodedata.normalize('NFKC', path)

# Clean a stored path value so it can used in comparisons
def clean_comparison_path(path):
    path_cleaned = None
    path_cleaned = path.replace("\\\\", "/").replace("\\", "/").replace("//", "/").replace("////", "/").lower()
    path_cleaned = normalize_path(path_cleaned)
    return path_cleaned

# Get the full path for a file
def full_path(file):
    full_path = os.path.join(program_files_dir, file)
    return full_path

# Get complete file path and name
def get_file_path(path, name, special_action):
    file_name_base = f"{name}"

    if special_action in ["Make STRM", "Make SLM Stream"]:
        file_name_extension = "strm"
    elif special_action in ['m3u', 'xml', 'gz', 'm3u8']:
        file_name_extension = special_action
    else:
        file_name_extension = "strmlnk"

    file_name = f"{file_name_base}.{file_name_extension}"
    file_path = os.path.join(path, file_name)
    file_path = normalize_path(file_path)
    return file_path

# Wrapper for searching for files with multiple extensions
def get_all_prior_files(search_directory, extensions):
    all_prior_files = []

    for extension in extensions:
        prior_files = search_directory_for_files_with_extensions(search_directory, extension)
        for prior_file in prior_files:
            all_prior_files.append({'filename': prior_file['filename'], 'extension': prior_file['extension']})

    return all_prior_files

# Finds files in a directory with a certain extension
def search_directory_for_files_with_extensions(search_directory, base_extension):
    result = []
    seen_files = set()  # Track seen files to avoid duplicates

    for file in os.listdir(search_directory):
        if file.endswith(base_extension):
            filename, extension = os.path.splitext(file)
            if filename not in seen_files:
                result.append({'filename': filename, 'extension': base_extension})
                seen_files.add(filename)  # Mark file as seen

    return result

# Get the path for Movies and TV Shows
def get_movie_tv_path():
    settings = read_data(csv_settings)
    channels_path = settings[1]["settings"]

    movie_path = os.path.join(channels_path, "Imports", "Movies", "slm")
    tv_path = os.path.join(channels_path, "Imports", "TV", "slm")
    video_path = os.path.join(channels_path, "Imports", "Videos", "slm")

    return movie_path, tv_path, video_path

# Create a directory if it doesn't exist.
def create_directory(directory_path):
    directory_path = normalize_path(directory_path)

    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
    except OSError as e:
        print(f"    Error creating directory {directory_path}: {e}")

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
                    notification_add(f"    Using read-only handle, removed empty directory: {dir_path}")
                except OSError as e:
                    notification_add(f"    Final error removing directory {dir_path}: {e}")

# Create a file
def create_file(path, name, url, special_action):
    file_path = get_file_path(path, name, special_action)
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

# Processes the data list into multiple chunks and saves files
def create_chunk_files(data_list, base_filename, extension, max):
    for index, chunk in enumerate(split_list(data_list, max)):
        if extension == "m3u":
            content = generate_m3u_content(chunk, base_filename, index)

        filename = f"{base_filename}_{index+1:02d}.{extension}"

        create_program_file(filename, content)

# Splits a data list into chunks of a specified size
def split_list(data_list, max):
    for i in range(0, len(data_list), max):
        yield data_list[i:i + max]

# Create a file in the Program Files directory
def create_program_file(filename, content):
    file_path = full_path(filename)

    try:
        with open(file_path, 'w', encoding="utf-8") as file:
            try:
                file.write(content)
                notification_add(f"    Created: {filename}")
            except OSError as e:
                notification_add(f"    Error creating file {filename}: {e}")

    except FileNotFoundError as fnf_error:
        notification_add(f"    Error with original path: {fnf_error}")

# Used to manage the potential of deleting all records
def create_temp_record(fields):
    return {field: None for field in fields}

# Loops through all the files in a directory and changes one suffix to another
def rename_files_suffix(directory, old_suffix, new_suffix):
    for filename in os.listdir(directory):
        if filename.endswith(old_suffix):
            old_file = os.path.join(directory, filename)
            new_filename = filename[:-len(old_suffix)] + new_suffix
            new_file = os.path.join(directory, new_filename)
            
            os.rename(old_file, new_file)

            notification_add(f"    Created: {new_filename}")

# Delete a file if it exists
def file_delete(path, name, special_action):
    file_path = get_file_path(path, name, special_action)
    file_path = normalize_path(file_path)

    try:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                if special_action in ['m3u', 'xml', 'gz', 'm3u8']:
                    notification_add(f"    Deleted: {name}.{special_action}")
                else:
                    notification_add(f"    Deleted: {file_path}")
        except OSError as e:
            notification_add(f"    Error removing file {file_path}: {e}")
    except FileNotFoundError as fnf_error:
        print(f"    Error removing file: {fnf_error}")

# Tries to remove a file, verifies its deletion, and retries if necessary.
def reliable_remove(filepath):
    max_retries=5
    wait_time=10

    for attempt in range(max_retries):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            if not os.path.exists(filepath):
                return True
        except Exception as e:
            print(f"{current_time()} WARNING: After {attempt + 1} attempt, failed to remove {filepath} due to: {e}")
        
        print(f"{current_time()} INFO: Waiting for {wait_time} seconds before next attempt...")
        time.sleep(wait_time)
    
    notification_add(f"{current_time()} ERROR: Failed to delete file '{filepath}' after {max_retries} attempts. Please manually delete and report this error along with other warnings and info in the logs.")
    return False

# Remove rogue files and empty directories
def remove_rogue_empty(movie_path, tv_path, video_path, bookmarks_statuses):
    all_files = []
    for path in [movie_path, tv_path, video_path]:
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
    directory_delete(video_path)

# Remove files older than a certain number of days and empty directories
def remove_old_files_and_empty_directories(base_directory, num_days):
    now = datetime.datetime.now()
    cutoff_time = now - datetime.timedelta(days=num_days)

    print(f"{current_time()} INFO: Removing files older than {num_days} days and empty directories from {base_directory}...")

    for dirpath, dirnames, filenames in os.walk(base_directory):
        for filename in filenames:
            file_path = normalize_path(os.path.join(dirpath, filename))
            try:
                file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mod_time < cutoff_time:
                    os.remove(file_path)
                    print(f"    Deleted old file: {file_path}")
            except Exception as e:
                print(f"    Error removing file {file_path}: {e}")

    # Remove empty directories
    directory_delete(base_directory)

    print(f"{current_time()} INFO: Finished removing files older than {num_days} days and empty directories from {base_directory}.")

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
        print(f"{current_time()} ERROR: Reading data... {e}")
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
        print(f"{current_time()} ERROR: Writing data... {e}")

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
        print(f"{current_time()} ERROR: Appending data... {e}")

# Removes rows in a CSV file based upon a value in the first column
def remove_row_csv(csv_file, field_value):
    full_path_file = full_path(csv_file)

    try:
        # Read the CSV file
        with open(full_path_file, 'r', encoding='utf-8') as inp:
            reader = csv.reader(inp)
            print(f"In {csv_file}, removed row:")

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

# Removes all rows in a file except the header
def delete_all_rows_except_header(csv_file):
    full_path_file = full_path(csv_file)
    
    # Ensure the file exists
    if os.path.exists(full_path_file):
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader)  # Read the header

        with open(full_path_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(header)  # Write the header back

    else:
        print(f"{current_time()} ERROR: File {csv_file} does not exist.")

# Function to add a new row if the row count is less than a certain number
def check_and_append(csv_file, new_row, threshold, purpose):
    row_count = count_rows(csv_file)
    
    if row_count < threshold:
        append_data(csv_file, new_row)
        notification_add(f"{current_time()} INFO: New row added to {csv_file}... it was for '{purpose}'.")

# Add new columns during upgrades
def check_and_add_column(csv_file, column_name, default_value):
    full_path_file = full_path(csv_file)
    
    # Read the CSV file
    with open(full_path_file, mode='r', newline='', encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Check if the column exists
    if column_name not in fieldnames:
        fieldnames.append(column_name)
        for row in rows:
            row[column_name] = default_value
    
    # Write the updated data back to the CSV file
    with open(full_path_file, mode='w', newline='', encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# Appends new rows. removes old rows, and updates modified rows from initialization data to be written to data files
def update_rows(csv_file, data, id_field, modify_flag):
    if data:
        new_rows = extract_new_rows(csv_file, data, id_field)
        if new_rows:
            print(f"{current_time()} INFO: Adding new rows to {csv_file}...")
            for new_row in new_rows:
                append_data(csv_file, new_row)
                notification_add(f"    ADDED: {new_row[id_field]}")
            print(f"{current_time()} INFO: Finished adding new rows.")

        old_rows = extract_old_rows(csv_file, data, id_field)
        if old_rows:
            print(f"{current_time()} INFO: Removing old rows from {csv_file}...")
            for old_row in old_rows:
                notification_add(f"    REMOVED: {old_row[id_field]}")
            remove_data(csv_file, old_rows, id_field)
            print(f"{current_time()} INFO: Finished removing old rows.")

        if modify_flag:
            modified_rows, no_notify_rows = extract_modified_rows(csv_file, data, id_field)
            if modified_rows:
                print(f"{current_time()} INFO: Updating modified rows in {csv_file}...")
                for modified_row in modified_rows:
                    if modified_row not in no_notify_rows:
                        notification_add(f"    MODIFIED: {modified_row[id_field]}")
                update_data(csv_file, modified_rows, id_field)
                print(f"{current_time()} INFO: Finished updating modified rows.")

            remove_duplicate_rows(csv_file)
            
    else:
        print(f"{current_time()} WARNING: No data to compare, skipping adding and removing rows in {csv_file}.")

# Extracts new rows from the library data that are not already present in the CSV file
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

# Extracts old rows from the CSV File that are no longer present in the library data
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

    # Extract old rows
    old_rows = []
    for row in existing_data:
        if row[id_field] not in existing_ids:
            old_rows.append(row)
    
    return old_rows

# Extracts modified rows from the library data that are present in the CSV file but have different content
def extract_modified_rows(csv_file, data, id_field):
    full_path_file = full_path(csv_file)

    # Read existing data (if any)
    existing_data = []
    if os.path.exists(full_path_file):
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            existing_data = [row for row in reader]
    
    # Create a dictionary for quick lookup of existing rows by id_field
    existing_data_dict = {row[id_field]: row for row in existing_data}

    # Extract modified rows and rows to not notify
    modified_rows = []
    no_notify_rows = []

    for row in data:
        if row[id_field] in existing_data_dict:
            existing_row = existing_data_dict[row[id_field]]
            if any(row[key] != existing_row[key] for key in row.keys() if key != id_field):
                modified_rows.append(row)
                # Check for ?X-Plex-Token= difference 
                differing_keys = [key for key in row.keys() if key != id_field and row[key] != existing_row[key]]
                if all('X-Plex-Token' in key or row[key].startswith(existing_row[key].split('?X-Plex-Token=')[0]) for key in differing_keys):
                    no_notify_rows.append(row)

    return modified_rows, no_notify_rows

# Updates rows in the CSV file with modified content
def update_data(csv_file, modified_rows, id_field):
    full_path_file = full_path(csv_file)

    # Read existing data (if any)
    existing_data = []
    if os.path.exists(full_path_file):
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            existing_data = [row for row in reader]

    # Create a dictionary for quick lookup of modified rows by id_field
    modified_data_dict = {row[id_field]: row for row in modified_rows}

    # Update the existing data with modified rows
    updated_data = [
        modified_data_dict[row[id_field]] if row[id_field] in modified_data_dict else row
        for row in existing_data
    ]

    # Write the updated data back to the CSV file
    fieldnames = updated_data[0].keys() if updated_data else []
    with open(full_path_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_data)

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

# Removes duplicate rows from the CSV file
def remove_duplicate_rows(csv_file):
    full_path_file = full_path(csv_file)
    
    if os.path.exists(full_path_file):
        with open(full_path_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            existing_data = [row for row in reader]

        # Remove duplicates
        unique_data = {tuple(row.items()): row for row in existing_data}.values()

        # Write the deduplicated data back to the CSV file
        fieldnames = existing_data[0].keys() if existing_data else []
        with open(full_path_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_data)
        
        print(f"{current_time()} INFO: Removed duplicate rows from {csv_file}.")

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
    max_retries = 3
    wait_time = 5
    for attempt in range(max_retries):
        try:
            os.replace(temp_file, full_path_file)
            break
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"{current_time()} WARNING: File is locked (attempt {attempt+1}/{max_retries}), retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"{current_time()} ERROR: Failed to replace file after {max_retries} attempts: {e}")
                raise

# Function to count rows in the CSV file
def count_rows(csv_file):
    full_path_file = full_path(csv_file)
    with open(full_path_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        return sum(1 for row in reader)

# Create missing data files, update data as needed
def check_and_create_csv(csv_file):
    full_path_file = full_path(csv_file)

    data = initial_data(csv_file)

    # Check if the file is empty or only contains blank lines; if so, delete it to start over
    if os.path.exists(full_path_file):
        with open(full_path_file, 'r', encoding="utf-8") as file:
            content = file.readlines()
        
        if all(line.strip() == '' for line in content):
            reliable_remove(full_path_file)

    # Check if the file exists, if not create it
    if not os.path.exists(full_path_file):
        # Write data to the file
        write_data(csv_file, data)
        remove_empty_row(csv_file)

        if csv_file == csv_settings:
            print(f"*** First Time Setup ***")
            settings = read_data(csv_settings)

            settings[0]['settings'], channels_url_message = get_channels_url()

            settings[1]['settings'] = find_channels_dvr_path()
            
            settings[2]['settings'] = get_country_code()
            
            write_data(csv_settings, settings)

    # Add columns for new functionality
    if csv_file == csv_bookmarks_status:
        check_and_add_column(csv_file, 'special_action', 'None')
        check_and_add_column(csv_file, 'original_release_date', '')
        check_and_add_column(csv_file, 'override_episode_title', '')
        check_and_add_column(csv_file, 'override_summary', '')
        check_and_add_column(csv_file, 'override_image', '')
        check_and_add_column(csv_file, 'override_duration', '')
        check_and_add_column(csv_file, 'channels_id', '')
        check_and_add_column(csv_file, 'manual_order', '')

    if csv_file == csv_bookmarks:
        check_and_add_column(csv_file, 'bookmark_action', 'None')
        check_and_add_column(csv_file, 'channels_id', '')
        check_and_add_column(csv_file, 'override_program_title', '')
        check_and_add_column(csv_file, 'override_program_summary', '')
        check_and_add_column(csv_file, 'override_program_image_type', 'na')
        check_and_add_column(csv_file, 'override_program_image_manual', '')
        check_and_add_column(csv_file, 'override_program_sort', 'na')

    if csv_file == csv_playlistmanager_playlists:
        check_and_add_column(csv_file, 'station_check', 'Off')

    if csv_file == csv_playlistmanager_parents:
        check_and_add_column(csv_file, 'parent_active', 'On')
        check_and_add_column(csv_file, 'parent_tvg_description_override', '')
        check_and_add_column(csv_file, 'parent_group_title_override', '')

    if csv_file == csv_playlistmanager_child_to_parent:
        check_and_add_column(csv_file, 'stream_format_override', 'None')
        check_and_add_column(csv_file, 'child_station_check', '')
        check_and_add_column(csv_file, 'enable_child_station_check', 'On')

    if csv_file == csv_streaming_services:
        check_and_add_column(csv_file, 'streaming_service_active', 'On')
        check_and_add_column(csv_file, 'streaming_service_group', 'None')

        # Fix in case records are missing a value
        streaming_services_update_flag = False
        streaming_services = read_data(csv_file)
        for streaming_service in streaming_services:
            if streaming_service['streaming_service_active'] == '':
                streaming_service['streaming_service_active'] = 'On'
                streaming_services_update_flag = True
            if streaming_service['streaming_service_group'] == '':
                streaming_service['streaming_service_group'] = 'None'
                streaming_services_update_flag = True
        if streaming_services_update_flag:
            write_data(csv_file, streaming_services)

    # Append/Remove rows to data that may update
    if csv_file == csv_streaming_services:
        id_field = "streaming_service_name"
        update_rows(csv_file, data, id_field, None)

    # Add rows for new functionality
    if csv_file == csv_settings:
        check_and_append(csv_file, {"settings": "Off"}, 11, "Search Defaults: Filter out already bookmarked")
        check_and_append(csv_file, {"settings": "On"}, 12, "Playlist Manager: On/Off")
        check_and_append(csv_file, {"settings": 1000}, 13, "Playlist Manager: Starting station number")
        check_and_append(csv_file, {"settings": 750}, 14, "Playlist Manager: Max number of stations per m3u")
        check_and_append(csv_file, {"settings": "Off"}, 15, "Playlist Manager: Update Stations Process Schedule On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 16, "Playlist Manager: Update Stations Process Schedule Time")
        check_and_append(csv_file, {"settings": "Off"}, 17, "Playlist Manager: Update m3u(s) and XML EPG(s) Process Schedule On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 18, "Playlist Manager: Update m3u(s) and XML EPG(s) Process Schedule Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 19, "Playlist Manager: Update m3u(s) and XML EPG(s) Process Schedule Frequency")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 20, "SLM: End-to-End Process Schedule Frequency")
        check_and_append(csv_file, {"settings": "On"}, 21, "GEN: Backup Process On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 22, "GEN: Backup Process Schedule Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 23, "GEN: Backup Process Schedule Frequency")
        check_and_append(csv_file, {"settings": 3}, 24, "GEN: Backup Process Max number of backups to keep")
        check_and_append(csv_file, {"settings": "On"}, 25, "Stream Link/Files Manager: On/Off")
        check_and_append(csv_file, {"settings": "On"}, 26, "GEN: Channels DVR Integration On/Off")
        check_and_append(csv_file, {"settings": "On"}, 27, "GEN: Check for Updates Process On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 28, "GEN: Check for Updates Process Schedule Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 29, "GEN: Check for Updates Process Schedule Frequency")
        check_and_append(csv_file, {"settings": "On"}, 30, "MTM: Media Tools Manager On/Off")
        check_and_append(csv_file, {"settings": "Off"}, 31, "MTM: Automation - Reset Channels DVR Passes On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 32, "MTM: Automation - Reset Channels DVR Passes Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 33, "MTM: Automation - Reset Channels DVR Passes Frequency")
        check_and_append(csv_file, {"settings": "Off"}, 34, "MTM: Automation - SLM New & Recent Releases On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 35, "MTM: Automation - SLM New & Recent Releases Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 36, "MTM: Automation - SLM New & Recent Releases Frequency")
        check_and_append(csv_file, {"settings": 72}, 37, "MTM: Automation - SLM New & Recent Releases Hours Past to Consider")
        check_and_append(csv_file, {"settings": "Off"}, 38, "MTM: Automation - Refresh Channels DVR m3u Playlists On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 39, "MTM: Automation - Refresh Channels DVR m3u Playlists Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 40, "MTM: Automation - Refresh Channels DVR m3u Playlists Frequency")
        check_and_append(csv_file, {"settings": "On"}, 41, "PLM: Streaming Stations On/Off")
        check_and_append(csv_file, {"settings": 2000}, 42, "PLM: Streaming Stations Starting station number")
        check_and_append(csv_file, {"settings": 750}, 43, "PLM: Streaming Stations Max number of stations per m3u")
        check_and_append(csv_file, {"settings": "Off"}, 44, "PLM: URL Tag in m3u(s) On/Off")
        check_and_append(csv_file, {"settings": "http://localhost:5000"}, 45, "PLM: URL Tag in m3u(s) Preferred URL Root")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 46, "PLM: Update Stations Process Schedule Frequency")
        check_and_append(csv_file, {"settings": "On"}, 47, "PLM: One-time fix for YouTube Live to Live Streams On/Off")
        check_and_append(csv_file, {"settings": f"http://{get_external_ip()}:{slm_port}"}, 48, "SLM: SLM Stream Address")
        check_and_append(csv_file, {"settings": "Active Providers"}, 49, "SLM: Search Default for Provider Status")
        check_and_append(csv_file, {"settings": "Off"}, 50, "PLM: Internal PBS Stations On/Off")
        check_and_append(csv_file, {"settings": "http://localhost:[PORT]"}, 51, "PLM: VLC Bridge PBS Base URL")
        check_and_append(csv_file, {"settings": "Off"}, 52, "SLM: Update Labels in Channels DVR On/Off")
        check_and_append(csv_file, {"settings": "Off"}, 53, "MTM: Remove old Channels DVR Recording Logs On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 54, "MTM: Remove old Channels DVR Recording Logs Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 55, "MTM: Remove old Channels DVR Recording Logs Frequency")
        check_and_append(csv_file, {"settings": 7}, 56, "MTM: Remove old Channels DVR Recording Logs Days to Keep")
        check_and_append(csv_file, {"settings": "Off"}, 57, "MTM: Remove old Channels DVR Backups On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 58, "MTM: Remove old Channels DVR Backups Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 59, "MTM: Remove old Channels DVR Backups Frequency")
        check_and_append(csv_file, {"settings": 7}, 60, "MTM: Remove old Channels DVR Backups Days to Keep")
        check_and_append(csv_file, {"settings": "Off"}, 61, "PLM/MTM: Check Child Station Status On/Off")
        check_and_append(csv_file, {"settings": "Off"}, 62, "MTM: Automation - Refresh Channels DVR m3u Playlists - Exclude 'Never Refresh URL' On/Off")
        check_and_append(csv_file, {"settings": 3}, 63, "PLM/MTM: Check Child Station Status Max Number of Retry Attempts")
        check_and_append(csv_file, {"settings": 5}, 64, "PLM/MTM: Check Child Station Status Retry Delay in Seconds")
        check_and_append(csv_file, {"settings": 0}, 65, "PLM/MTM: Check Child Station Status Skip Playlist After Fails (0 = Disabled)")
        check_and_append(csv_file, {"settings": "movies_shows"}, 66, "SLM: 'Add Programs' Search Selection (Default)")
        check_and_append(csv_file, {"settings": 0}, 67, "SLM: Minimum Video Length (in Seconds) for Search")
        check_and_append(csv_file, {"settings": "Off"}, 68, "SLM: Show 'Hidden Programs' in Dropdown Selection (Default)")
        check_and_append(csv_file, {"settings": "Off"}, 69, "SLM: Use the 'Feed & Auto-Mapping' functionality")
        check_and_append(csv_file, {"settings": "Off"}, 70, "MTM: Run SLM 'Feed & Auto-Mapping' Functionality On/Off")
        check_and_append(csv_file, {"settings": datetime.datetime.now().strftime('%H:%M')}, 71, "MTM: Run SLM 'Feed & Auto-Mapping' Functionality Start Time")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 72, "MTM: Run SLM 'Feed & Auto-Mapping' Functionality Frequency")
        check_and_append(csv_file, {"settings": [
                "the",
                "a",
                "an",
                "el",
                "la",
                "los",
                "las",
                "un",
                "una",
                "unos",
                "unas"
            ]}, 73, "GEN: Default list of 'Articles for Sorting'")
        check_and_append(csv_file, {"settings": "Off"}, 74, "GEN: Media Players Integration On/Off")
        check_and_append(csv_file, {"settings": "Off"}, 75, "SLM: Add TV Show Title to File Name On/Off")
        check_and_append(csv_file, {"settings": "Off"}, 76, "SLM: Add Episode Title to TV Show File Name On/Off")

# Data records for initialization files
def initial_data(csv_file):
    data = []

    if csv_file == csv_settings:
        data = [
            {"settings": f"http://dvr-{socket.gethostname().lower()}.local:8089"},     # [0]  Channels URL
            {"settings": script_dir},                                                  # [1]  Stream Links/Files Folder
            {"settings": "US"},                                                        # [2]  Search Defaults: Country Code
            {"settings": "en"},                                                        # [3]  Search Defaults: Language Code
            {"settings": "9"},                                                         # [4]  Search Defaults: Number of Results
            {"settings": "Off"},                                                       # DEPRECATED: [5] Hulu to Disney+ Automatic Conversion
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [6]  SLM: End-to-End Process Schedule Time
            {"settings": "On"},                                                        # [7]  Channels Prune
            {"settings": "Off"},                                                       # [8]  SLM: End-to-End Process Schedule On/Off
            {"settings": "Off"},                                                       # [9]  Search Defaults: Filter out already bookmarked
            {"settings": "On"},                                                        # [10] Playlist Manager: On/Off
            {"settings": 1000},                                                        # [11] Playlist Manager: Starting station number
            {"settings": 750},                                                         # [12] Playlist Manager: Max number of stations per m3u
            {"settings": "Off"},                                                       # [13] Playlist Manager: Update Stations Process Schedule On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [14] Playlist Manager: Update Stations Process Schedule Time
            {"settings": "Off"},                                                       # [15] Playlist Manager: Update m3u(s) and XML EPG(s) Process Schedule On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [16] Playlist Manager: Update m3u(s) and XML EPG(s) Process Schedule Start Time
            {"settings": "Every 24 hours"},                                            # [17] Playlist Manager: Update m3u(s) and XML EPG(s) Process Schedule Frequency
            {"settings": "Every 24 hours"},                                            # [18] SLM: End-to-End Process Schedule Frequency
            {"settings": "On"},                                                        # [19] GEN: Backup Process On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [20] GEN: Backup Process Schedule Start Time
            {"settings": "Every 24 hours"},                                            # [21] GEN: Backup Process Schedule Frequency
            {"settings": 3},                                                           # [22] GEN: Backup Process Max number of backups to keep
            {"settings": "On"},                                                        # [23] Stream Link/Files Manager: On/Off
            {"settings": "On"},                                                        # [24] GEN: Channels DVR Integration On/Off
            {"settings": "On"},                                                        # [25] GEN: Check for Updates Process On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [26] GEN: Check for Updates Process Schedule Start Time
            {"settings": "Every 24 hours"},                                            # [27] GEN: Check for Updates Process Schedule Frequency
            {"settings": "On"},                                                        # [28] MTM: Media Tools Manager On/Off
            {"settings": "Off"},                                                       # [29] MTM: Automation - Reset Channels DVR Passes On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [30] MTM: Automation - Reset Channels DVR Passes Start Time
            {"settings": "Every 24 hours"},                                            # [31] MTM: Automation - Reset Channels DVR Passes Frequency
            {"settings": "Off"},                                                       # [32] MTM: Automation - SLM New & Recent Releases On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [33] MTM: Automation - SLM New & Recent Releases Start Time
            {"settings": "Every 24 hours"},                                            # [34] MTM: Automation - SLM New & Recent Releases Frequency
            {"settings": 72},                                                          # [35] MTM: Automation - SLM New & Recent Releases Hours Past to Consider
            {"settings": "Off"},                                                       # [36] MTM: Automation - Refresh Channels DVR m3u Playlists On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [37] MTM: Automation - Refresh Channels DVR m3u Playlists Start Time
            {"settings": "Every 24 hours"},                                            # [38] MTM: Automation - Refresh Channels DVR m3u Playlists Frequency
            {"settings": "On"},                                                        # [39] PLM: Streaming Stations On/Off
            {"settings": 2000},                                                        # [40] PLM: Streaming Stations Starting station number
            {"settings": 750},                                                         # [41] PLM: Streaming Stations Max number of stations per m3u
            {"settings": "Off"},                                                       # [42] PLM: URL Tag in m3u(s) On/Off
            {"settings": "http://localhost:5000"},                                     # [43] PLM: URL Tag in m3u(s) Preferred URL Root
            {"settings": "Every 24 hours"},                                            # [44] PLM: Update Stations Process Schedule Frequency
            {"settings": "Off"},                                                       # [45] PLM: One-time fix for YouTube Live to Live Streams On/Off
            {"settings": f"http://{get_external_ip()}:{slm_port}"},                    # [46] SLM: SLM Stream Address
            {"settings": "Active Providers"},                                          # [47] SLM: Search Default for Provider Status
            {"settings": "Off"},                                                       # [48] PLM: Internal PBS Stations On/Off
            {"settings": "http://localhost:[PORT]"},                                   # [49] PLM: VLC Bridge PBS Base URL
            {"settings": "Off"},                                                       # [50] SLM: Update Labels in Channels DVR On/Off
            {"settings": "Off"},                                                       # [51] MTM: Remove old Channels DVR Recording Logs On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [52] MTM: Remove old Channels DVR Recording Logs Start Time
            {"settings": "Every 24 hours"},                                            # [53] MTM: Remove old Channels DVR Recording Logs Frequency
            {"settings": 7},                                                           # [54] MTM: Remove old Channels DVR Recording Logs Days to Keep
            {"settings": "Off"},                                                       # [55] MTM: Remove old Channels DVR Backups On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [56] MTM: Remove old Channels DVR Backups Start Time
            {"settings": "Every 24 hours"},                                            # [57] MTM: Remove old Channels DVR Backups Frequency
            {"settings": 7},                                                           # [58] MTM: Remove old Channels DVR Backups Days to Keep
            {"settings": "Off"},                                                       # [59] PLM/MTM: Check Child Station Status On/Off
            {"settings": "Off"},                                                       # [60] MTM: Automation - Refresh Channels DVR m3u Playlists - Exclude 'Never Refresh URL' On/Off
            {"settings": 3},                                                           # [61] PLM/MTM: Check Child Station Status Max Number of Retry Attempts
            {"settings": 5},                                                           # [62] PLM/MTM: Check Child Station Status Retry Delay in Seconds
            {"settings": 0},                                                           # [63] PLM/MTM: Check Child Station Status Skip Playlist After Fails (0 = Disabled)
            {"settings": "movies_shows"},                                              # [64] SLM: 'Add Programs' Search Selection (Default)
            {"settings": 0},                                                           # [65] SLM: Minimum Video Length (in Seconds) for Search
            {"settings": "Off"},                                                       # [66] SLM: Show 'Hidden Programs' in Dropdown Selection (Default)
            {"settings": "Off"},                                                       # [67] SLM: Use the 'Feed & Auto-Mapping' functionality
            {"settings": "Off"},                                                       # [68] MTM: Run SLM 'Feed & Auto-Mapping' Functionality On/Off
            {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [69] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Start Time
            {"settings": "Every 24 hours"},                                            # [70] MTM: Run SLM 'Feed & Auto-Mapping' Functionality Frequency
            {"settings": [
                "the",
                "a",
                "an",
                "el",
                "la",
                "los",
                "las",
                "un",
                "una",
                "unos",
                "unas"
            ]},                                                                        # [71] GEN: List of 'Articles for Sorting'
            {"settings": "Off"},                                                       # [72] GEN: Media Players Integration On/Off
            {"settings": "Off"},                                                       # [73] SLM: Add TV Show Title to File Name On/Off
            {"settings": "Off"}                                                        # [74] SLM: Add Episode Title to TV Show File Name On/Off
        ]

    # Stream Link/File Manager
    elif csv_file == csv_streaming_services:
        data = get_streaming_services()

    elif csv_file == csv_slm_subscribed_video_channels:
        data = [{
            "channel_id": None,
            "channel_active": None,
            "channel_name": None,
            "channel_user": None,
            "channel_description": None,
            "channel_url": None,
            "channel_image": None,
            "channel_streaming_service_group": None,
            "channel_hidden": None
        }]

    elif csv_file == csv_bookmarks:
        data = [{
            "entry_id": None,
            "title": None,
            "release_year": None,
            "object_type": None,
            "url": None,
            "country_code": None,
            "language_code": None,
            "bookmark_action": None,
            "channels_id": None,
            "override_program_title": None,
            "override_program_summary": None,
            "override_program_image_type": None,
            "override_program_image_manual": None,
            "override_program_sort": None
        }]

    elif csv_file == csv_bookmarks_status:
        data = [{
            "entry_id": None,
            "season_episode_id": None,
            "season_episode_prefix": None,
            "season_episode": None,
            "status": None,
            "stream_link": None,
            "stream_link_override": None,
            "stream_link_file": None,
            "special_action": None,
            "original_release_date": None,
            "override_episode_title": None,
            "override_summary": None,
            "override_image": None,
            "override_duration": None,
            "channels_id": None,
            "manual_order": None
        }]

    elif csv_file == csv_slmappings:
        data = [
            {
                "active": "Off",
                "contains_string": "hulu.com/watch",
                "object_type": "MOVIE or SHOW",
                "replace_type": "Replace string with...",
                "replace_string": "disneyplus.com/play"
            },
            {
                "active": "Off",
                "contains_string": "hulu\.com/series/.+?-([a-f0-9\-]{36})$",
                "object_type": "SHOW",
                "replace_type": "Replace pattern (REGEX) with...",
                "replace_string": "disneyplus.com/browse/entity-\1"
            },
            {
                "active": "On",
                "contains_string": "netflix.com/title",
                "object_type": "MOVIE",
                "replace_type": "Replace string with...",
                "replace_string": "netflix.com/watch"
            },
            {
                "active": "On",
                "contains_string": "disneyplus.com/browse/entity-",
                "object_type": "MOVIE",
                "replace_type": "Replace string with...",
                "replace_string": "disneyplus.com/play/"
            },
            {
                "active": "On",
                "contains_string": "watch.amazon.com/detail?gti=",
                "object_type": "MOVIE or SHOW",
                "replace_type": "Replace string with...",
                "replace_string": "www.amazon.com/gp/video/detail/"
            },
            {
                "active": "Off",
                "contains_string": "vudu.com",
                "object_type": "MOVIE or SHOW",
                "replace_type": "Replace entire Stream Link with...",
                "replace_string": "fandangonow://"
            },
            {
                "active": "On",
                "contains_string": "peacocktv.com/watch/asset/.+?/([a-zA-Z0-9\\\\-]+)$",
                "object_type": "MOVIE or SHOW",
                "replace_type": "Replace pattern (REGEX) with...",
                "replace_string": 'peacocktv.com/deeplink?deeplinkData={"pvid":"\\1","type":"PROGRAMME","action":"PLAY"}'
            }
        ]

    elif csv_file == csv_provider_groups:
        data = [{
            "provider_group_id": None,
            "provider_group_active": None,
            "provider_group_name": None,
            "provider_group_description": None
        }]

    elif csv_file == csv_slm_labels:
        data = [{
            "label_id": None,
            "label_active": None,
            "label_name": None,
            "label_description": None
        }]

    elif csv_file == csv_slm_label_maps:
        data = [{
            "label_id": None,
            "entry_id": None
        }]

    elif csv_file == csv_slm_feed_items:
        data = [{
            "entry_id": None,
            "title": None,
            "release_year": None,
            "object_type": None,
            "url": None,
            "short_description": None,
            "poster": None,
            "score": None,
            "offers_list": None
        }]

    elif csv_file == csv_slm_feed_rules:
        data = [{
            "feed_rule_id": None,
            "feed_rule_active": None,
            "feed_rule_name": None,
            "provider": None,
            "date_range": None,
            "override_min_video_length": None
        }]

    elif csv_file == csv_slm_feed_maps:
        data = [{
            "feed_map_id": None,
            "feed_map_active": None,
            "feed_map_name": None,
            "source_provider": None,
            "source_field": None,
            "source_field_compare_id": None,
            "source_field_string": None,
            "target_status": None,
            "target_label_ids": None,
            "target_action": None
        }]

    # Playlist Manager
    elif csv_file == csv_playlistmanager_playlists:
        data = [{
            "m3u_id": None,
            "m3u_name": None,
            "m3u_url": None,
            "epg_xml": None,
            "stream_format": None,
            "m3u_priority": None,
            "station_check": None
        }]

    elif csv_file == csv_playlistmanager_parents:
        data = [{
            "parent_channel_id": None,
            "parent_title": None,
            "parent_tvg_id_override": None,
            "parent_tvg_logo_override": None,
            "parent_channel_number_override": None,
            "parent_tvc_guide_stationid_override": None,
            "parent_tvc_guide_art_override": None,
            "parent_tvc_guide_tags_override": None,
            "parent_tvc_guide_genres_override": None,
            "parent_tvc_guide_categories_override": None,
            "parent_tvc_guide_placeholders_override": None,
            "parent_tvc_stream_vcodec_override": None,
            "parent_tvc_stream_acodec_override": None,
            "parent_preferred_playlist": None,
            "parent_active": None,
            "parent_tvg_description_override": None,
            "parent_group_title_override": None
        }]

    elif csv_file == csv_playlistmanager_child_to_parent:
        data = [{
            "child_m3u_id_channel_id": None,
            "parent_channel_id": None,
            "stream_format_override": None,
            "child_station_check": None,
            "enable_child_station_check": None
        }]    

    elif csv_file == csv_playlistmanager_combined_m3us:
        data = [{
            "station_playlist": None,
            "m3u_id": None,
            "title": None,
            "tvc_guide_title": None,
            "channel_id": None,
            "tvg_id": None,
            "tvg_name": None,
            "tvg_logo": None,
            "tvg_chno": None,
            "channel_number": None,
            "tvg_description": None,
            "tvc_guide_description": None,
            "group_title": None,
            "tvc_guide_stationid": None,
            "tvc_guide_art": None,
            "tvc_guide_tags": None,
            "tvc_guide_genres": None,
            "tvc_guide_categories": None,
            "tvc_guide_placeholders": None,
            "tvc_stream_vcodec": None,
            "tvc_stream_acodec": None,
            "url": None
        }]

    elif csv_file == csv_playlistmanager_streaming_stations:
        data = [{
            "channel_id": None,
            "source": None,
            "url": None,
            "title": None,
            "tvg_logo": None,
            "tvg_description": None,
            "tvc_guide_tags": None,
            "tvc_guide_genres": None,
            "tvc_guide_categories": None,
            "tvc_guide_placeholders": None,
            "tvc_stream_vcodec": None,
            "tvc_stream_acodec": None
        }]

    elif csv_file == csv_playlistmanager_station_mappings:
        data = [{
            "station_mapping_id": None,
            "station_mapping_name": None,
            "station_mapping_active": None,
            "station_mapping_priority": None,
            "source_m3u_id": None,
            "source_field": None,
            "source_field_compare_id": None,
            "source_field_string": None,
            "target_field": None,
            "target_field_compare_replace_id": None,
            "target_field_string": None,
            "target_parent_channel_id": None,
            "target_stream_format_override": None
        }]

    return data

# Website check in loop
def check_website(url):
    while True:
        try:
            response = requests.get(url, headers=url_headers)
            if response.status_code == 200:
                print(f"{current_time()} SUCCESS: {url} is accessible. Continuing...")
                break
            else:
                print(f"{current_time()} ERROR: {url} reports {response.status_code}")
        except requests.RequestException as e:
            print(f"{current_time()} ERROR: {url} reports {e}")
        
        print(f"{current_time()} INFO: Retrying in 1 minute...")
        time.sleep(60)

# Check if a video stream is working and determine its type (HLS or MPEG-TS)
def test_video_stream(url):
    status = None

    settings = read_data(csv_settings)
    retries = int(settings[61]['settings'])  # [61] PLM/MTM: Check Child Station Status Max Number of Retry Attempts
    delay = int(settings[62]['settings'])    # [62] PLM/MTM: Check Child Station Status Retry Delay in Seconds

    for attempt in range(retries):
        try:
            with requests.Session() as session:
                resp = session.get(url, headers=url_headers, stream=True, timeout=10, allow_redirects=True)

                with session.get(resp.url, headers=url_headers, stream=True, timeout=10) as response:
                    if response.status_code == 200:
                        first_byte = None
                        for chunk in response.iter_content(chunk_size=1):
                            if chunk:
                                first_byte = chunk[0:1]
                                break

                        if first_byte is not None:
                            if first_byte == b'G' or first_byte == b'\x47':
                                status = "MPEG-TS"
                            elif first_byte == b'#':
                                status = "HLS"
                            else:
                                status = "okay"
                        else:
                            status = "fail"
                    else:
                        status = "fail"

        except Exception as e:
            print(f"{current_time()} ERROR: {url} reports {e}")
            status = "fail"

        if status in ("HLS", "MPEG-TS", "okay"):
            break
        elif attempt < retries - 1:
            print(f"{current_time()} INFO: '{url}' failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        else:
            print(f"{current_time()} INFO: '{url}' still failed after {retries} attempts.")

    stream_metadata = []
    if status in ("HLS", "MPEG-TS", "okay"):
        try:
            with requests.Session() as session:
                response = session.get(url, headers=url_headers, stream=True, timeout=10, allow_redirects=True)
                # HTTP headers
                for k, v in response.headers.items():
                    stream_metadata.append({"field": f"Header: {k}", "value": v})

                # Content-Type
                if "Content-Type" in response.headers:
                    stream_metadata.append({"field": "Content Type", "value": response.headers["Content-Type"]})

                # Content-Length
                if "Content-Length" in response.headers:
                    stream_metadata.append({"field": "Content Length", "value": response.headers["Content-Length"]})

                # DRM detection (headers)
                drm_detected = False
                drm_headers = ["x-drm", "drm-type", "x-playready", "x-widevine", "x-fairplay", "license", "x-license-url"]
                for h in drm_headers:
                    if h in response.headers:
                        stream_metadata.append({"field": "DRM Detected", "value": True})
                        stream_metadata.append({"field": "DRM Type", "value": response.headers[h]})
                        drm_detected = True
                        break

                # Manifest/playlist inspection for HLS/DASH
                content_type = response.headers.get("Content-Type", "")
                manifest_drm_type = None
                if status == "HLS" or "application/vnd.apple.mpegurl" in content_type or url.endswith(".m3u8"):
                    manifest = response.content.decode(errors="ignore")
                    if "#EXT-X-STREAM-INF" in manifest:
                        stream_metadata.append({"field": "HLS Variant Playlist", "value": True})
                    codecs_found = []
                    resolutions_found = []
                    for line in manifest.splitlines():
                        if line.startswith("#EXT-X-STREAM-INF"):
                            # Extract RESOLUTION
                            res_match = re.search(r'RESOLUTION=([0-9]+x[0-9]+)', line)
                            if res_match:
                                resolutions_found.append(res_match.group(1))
                            # Extract CODECS
                            codecs_match = re.search(r'CODECS="([^"]+)"', line)
                            if codecs_match:
                                codecs_found.append(codecs_match.group(1))
                    if codecs_found:
                        stream_metadata.append({"field": "Codecs", "value": "; ".join(codecs_found)})
                    if resolutions_found:
                        stream_metadata.append({"field": "Resolutions", "value": ", ".join(resolutions_found)})
                    # DRM in manifest
                    if "widevine" in manifest.lower():
                        stream_metadata.append({"field": "DRM Detected (HLS)", "value": True})
                        stream_metadata.append({"field": "DRM Type (HLS)", "value": "Widevine"})
                        drm_detected = True
                        manifest_drm_type = "Widevine"
                    elif "playready" in manifest.lower():
                        stream_metadata.append({"field": "DRM Detected (HLS)", "value": True})
                        stream_metadata.append({"field": "DRM Type (HLS)", "value": "PlayReady"})
                        drm_detected = True
                        manifest_drm_type = "PlayReady"
                    elif "fairplay" in manifest.lower():
                        stream_metadata.append({"field": "DRM Detected (HLS)", "value": True})
                        stream_metadata.append({"field": "DRM Type (HLS)", "value": "FairPlay"})
                        drm_detected = True
                        manifest_drm_type = "FairPlay"

                # MPEG-TS advanced inspection (pure Python)
                if status == "MPEG-TS":
                    try:
                        ts_bytes = response.raw.read(188 * 1000)
                        ts_info = inspect_mpeg_ts_stream(ts_bytes)
                        if ts_info.get("pids"):
                            stream_metadata.append({"field": "MPEG-TS PIDs", "value": str(ts_info["pids"])})
                        if ts_info.get("programs"):
                            stream_metadata.append({"field": "MPEG-TS Programs", "value": str(ts_info["programs"])})
                        if ts_info.get("streams"):
                            stream_metadata.append({"field": "MPEG-TS Streams", "value": str(ts_info["streams"])})
                        if ts_info.get("codec_hints"):
                            stream_metadata.append({"field": "MPEG-TS Codecs", "value": ", ".join(ts_info["codec_hints"])})
                        # MPEG-TS DRM detection (heuristic)
                        if ts_info.get("drm_detected"):
                            stream_metadata.append({"field": "DRM Detected (MPEG-TS)", "value": True})
                            stream_metadata.append({"field": "DRM Type (MPEG-TS)", "value": ts_info.get("drm_type", "Conditional Access/ECM/EMM/Private Data")})
                            drm_detected = True
                    except Exception as e:
                        stream_metadata.append({"field": "MPEG-TS Inspect Error", "value": str(e)})

                # If DRM detected, update status
                if drm_detected or manifest_drm_type:
                    status = "DRM"

        except Exception as e:
            stream_metadata.append({"field": "Metadata Error", "value": str(e)})

    return status, stream_metadata

# Inspect MPEG-TS stream bytes and extract basic metadata. Returns a dict with PIDs, program info, stream types, and DRM heuristic.
def inspect_mpeg_ts_stream(ts_bytes, max_packets=1000):
    from collections import defaultdict

    PACKET_SIZE = 188
    pids = set()
    programs = {}
    streams = defaultdict(list)
    codec_hints = set()
    pat_pid = 0x0000
    pmt_pids = set()
    program_map = {}
    drm_detected = False
    drm_type = None

    # Common CA/DRM PIDs and stream types
    drm_pids = {0x0B, 0x09, 0x0E, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x1FFF}
    drm_stream_types = {0x06}  # Private data, often used for ECM/EMM

    def parse_pat(packet):
        section_length = ((packet[6] & 0x0F) << 8) | packet[7]
        i = 8
        while i < 8 + section_length - 4:
            program_number = (packet[i] << 8) | packet[i+1]
            pid = ((packet[i+2] & 0x1F) << 8) | packet[i+3]
            if program_number != 0:
                program_map[program_number] = pid
                pmt_pids.add(pid)
            i += 4

    def parse_pmt(packet):
        nonlocal drm_detected, drm_type
        section_length = ((packet[6] & 0x0F) << 8) | packet[7]
        program_info_length = ((packet[10] & 0x0F) << 8) | packet[11]
        i = 12 + program_info_length
        while i < 8 + section_length - 4:
            if i+4 > len(packet):
                break
            stream_type = packet[i]
            elementary_pid = ((packet[i+1] & 0x1F) << 8) | packet[i+2]
            streams[elementary_pid].append(stream_type)
            # Codec hints
            if stream_type == 0x1B:
                codec_hints.add("H.264/AVC")
            elif stream_type == 0x24:
                codec_hints.add("H.265/HEVC")
            elif stream_type == 0x0F:
                codec_hints.add("AAC")
            elif stream_type == 0x03 or stream_type == 0x04:
                codec_hints.add("MPEG-2 Audio")
            elif stream_type == 0x02:
                codec_hints.add("MPEG-2 Video")
            elif stream_type == 0x06:
                codec_hints.add("Private data")
            # Heuristic DRM detection
            if elementary_pid in drm_pids or stream_type in drm_stream_types:
                drm_detected = True
                drm_type = "Conditional Access/ECM/EMM/Private Data"
            i += 5

    for i in range(0, min(len(ts_bytes), PACKET_SIZE * max_packets), PACKET_SIZE):
        packet = ts_bytes[i:i+PACKET_SIZE]
        if len(packet) < PACKET_SIZE or packet[0] != 0x47:
            continue
        pid = ((packet[1] & 0x1F) << 8) | packet[2]
        pids.add(pid)
        payload_unit_start = (packet[1] & 0x40) != 0
        if pid == pat_pid and payload_unit_start:
            pointer_field = packet[4]
            pat_start = 5 + pointer_field
            parse_pat(packet[pat_start:])
        elif pid in pmt_pids and payload_unit_start:
            pointer_field = packet[4]
            pmt_start = 5 + pointer_field
            parse_pmt(packet[pmt_start:])

    return {
        "pids": sorted(pids),
        "programs": program_map,
        "streams": {pid: types for pid, types in streams.items()},
        "codec_hints": sorted(codec_hints),
        "drm_detected": drm_detected,
        "drm_type": drm_type
    }

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Used to loop through a URL that might error
def fetch_url(url, retries, delay):
    timeout_duration = 120

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=url_headers, timeout=timeout_duration)
            
            if response.status_code == 200:
                return response

            elif response.status_code == 403:
                print(f"{current_time()} ERROR: For '{url}', connection was refused with a {response.status_code} error, indicating a check for human interaction. Streaming Library Manager cannot automatically simulate this, therefore you should download the file directly and manually upkeep.")
                break
                
            else:
                raise Exception(f"HTTP Status Code {response.status_code}")
            
        except Exception as e:
            if attempt < retries - 1:
                print(f"{current_time()} WARNING: For '{url}', encountered an error ({e}). Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                notification_add(f"{current_time()} ERROR: For '{url}', after {retries} attempts, could not resolve error ({e}). Skipping...")

# Used to send a post command to a URL that might error
def post_url(url, json_data, retries, delay):
    timeout_duration = 120

    for attempt in range(retries):
        try:
            if json_data:
                response = requests.post(url, headers=url_headers, json=json_data, timeout=timeout_duration)
            else:
                response = requests.post(url, headers=url_headers, timeout=timeout_duration)

            if response.status_code == 200:
                return response
            else:
                raise Exception(f"HTTP Status Code {response.status_code}")
            
        except Exception as e:
            if attempt < retries - 1:
                print(f"{current_time()} WARNING: For '{url}', encountered an error ({e}). Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                notification_add(f"{current_time()} ERROR: For '{url}', after {retries} attempts, could not resolve error ({e}). Skipping...") 

# Searches for an IP Address on the LAN that responds to Port 8089
def get_channels_url():
    local_ip = socket.gethostbyname(socket.gethostname())
    ip_parts = local_ip.split('.')
    base_ip = '.'.join(ip_parts[:-1]) + '.'
    start_ip = int(ip_parts[-1])
    port = 8089
    machine_name = None
    machine_name_flag = None
    docker_test = None
    docker_test_url = f"http://host.docker.internal:8089"
    channels_url = None
    channels_url_message = None
    bad_urls = [
        "docker",
        "tailscale"
    ]

    print(f"{current_time()} Searching for Channels URL...")

    # Search times out after 60 seconds
    timer = threading.Timer(60, timeout_handler)
    timer.start()

    try:
        machine_name = check_ip_range(start_ip, start_ip + 1, base_ip, port)
        if machine_name:
            machine_name = socket.gethostname().lower()

        if machine_name is None or machine_name == '':
            machine_name = check_ip_range(start_ip + 1, 256, base_ip, port)

        if machine_name is None or machine_name == '':
            machine_name = check_ip_range(1, start_ip, base_ip, port)

        if machine_name:
            for bad_url in bad_urls:
                if machine_name.__contains__(bad_url):
                    machine_name = "[ERROR_READ_WRONG_NAME_UPDATE_SETTINGS]"
                    machine_name_flag = True
                    break

        if machine_name is None or machine_name == '':
            docker_test = check_channels_url(docker_test_url)

        if docker_test:
            channels_url_message = f"{current_time()} INFO: External Channels URL not found, but was discovered with the Docker link! Please verify in Settings and change there, if desired."
            channels_url = docker_test_url
        elif machine_name:
            if machine_name_flag:
                channels_url_message = f"{current_time()} INFO: Error in discovering Channels URL. Please manually update in Settings."
            else:
                channels_url_message = f"{current_time()} INFO: Potential Channels URL found! Please verify in Settings."
            channels_url = f"http://dvr-{machine_name}.local:8089"
        else:
            channels_url_message = f"{current_time()} INFO: Channels URL not found. Please manually update in Settings."
            channels_url = f"http://[CHANNELS_URL_NOT_FOUND_UPDATE_SETTINGS]:8089"
    except TimeoutError:
        channels_url_message = f"{current_time()} INFO: Search timed out. Continuing to next step..."
    except KeyboardInterrupt:
        channels_url_message = f"{current_time()} INFO: Search interrupted by user. Continuing to next step..."
    finally:
        timer.cancel()  # Disable the timer

    if channels_url:
        pass
    else:
        channels_url_message = f"{current_time()} INFO: Channels URL not found. Please manually update in Settings."
        channels_url = f"http://[CHANNELS_URL_NOT_FOUND_UPDATE_SETTINGS]:8089"

    print(f"{channels_url_message}")
    print(f"{current_time()} INFO: Channels URL set to '{channels_url}'")

    return channels_url, channels_url_message

# Loops through the IP Addresses as part of the check for the open Port 8089
def check_ip_range(start, end, base_ip, port):
    machine_name = None
    port_test = None

    for i in range(start, end):
        ip = base_ip + str(i)
        print(f"    Checking IP: {ip}")
        try:
            port_test = socket.create_connection((ip, port), timeout=0.1)
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass
        if port_test:
            machine_name = socket.gethostbyaddr(ip)[0].lower()
            break

    return machine_name

# Connects to an external server to determine the route
def get_external_ip():
    ip_address = None

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Google's public DNS server
            ip_address = s.getsockname()[0]
    except Exception as e:
        ip_address = "unable_to_determine_set_manually"

    return ip_address

# Gets JSON data from Channels DVR
def get_channels_dvr_json(selection):
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    route = None
    url = None
    results_base = None
    results_base_json = None
    results_library = []

    if selection == 'all_stations':
        route = '/api/v1/channels'
    elif selection == 'channel_collections':
        route = '/dvr/collections/channels'
    elif selection == 'channels_clients':
        route = '/settings'
    elif selection == 'items_by_library_collection':
        route = '/dvr/collections/content'
    elif selection == 'dvr_status':
        route = '/dvr'
    elif selection == 'dvr_files':
        route = '/dvr/files'
    elif selection == 'dvr_groups':
        route = '/dvr/groups'

    if route:
        url = f"{channels_url}{route}"

    if url:

        channels_url_okay = check_channels_url(None)

        if channels_url_okay:
            try:
                results_base = requests.get(url, headers=url_headers)
            except requests.RequestException as e:
                print(f"{current_time()} ERROR: While performing {selection}, received {e}.")

            if results_base:
                results_base_json = results_base.json()

                if selection == 'all_stations':
                    for result in results_base_json:
                        id = result.get("id", '')
                        name = result.get("name", '')
                        number = result.get("number", '')
                        logo_url = result.get("logo_url", '')
                        hd = result.get("hd", '')
                        favorited = result.get("favorited", '')
                        source_name = result.get("source_name", '')
                        source_id = result.get("source_id", '')
                        station_id = result.get("station_id", '')
                    
                        results_library.append({
                            "Station ID": id,
                            "Station Name": name,
                            "Station Number": number,
                            "Station Logo": logo_url,
                            "Is HD?": hd,
                            "Is Favorite?": favorited,
                            "Source Name": source_name,
                            "Source ID": source_id,
                            "Station Channels ID": station_id
                        })

                    results_library = sorted(results_library, key=lambda x: sort_key(x["Station Name"].casefold()))

                elif selection == 'channel_collections':
                    for result in results_base_json:
                        name = result.get("name", '')
                        items = result.get("items", [])

                        for item in items:
                            results_library.append({
                                "Station ID": item,
                                "Channel Collection Name": name
                                })
                        
                    results_library = sorted(results_library, key=lambda x: (sort_key(x["Station ID"].casefold()), sort_key(x["Channel Collection Name"].casefold())))

                elif selection == 'channels_clients':
                    clients_info = {}
                    for key, value in results_base_json.items():
                        if key.startswith('clients.info.'):
                            parts = key.split('.')
                            client_id = parts[2]
                            field = parts[3]
                            if client_id not in clients_info:
                                clients_info[client_id] = {
                                    'alias': '',
                                    'hostname': '',
                                    'local_ip': '',
                                    'machine_id': '',
                                    'remote_ip': '',
                                    'seen_at': '',
                                    'seen_from': '',
                                    'user_agent': ''
                                }
                            clients_info[client_id][field] = value

                    for client_id, client_data in clients_info.items():
                        results_library.append({
                            'Hostname': client_data['hostname'],
                            'Alias': client_data['alias'],
                            'User Agent': client_data['user_agent'],
                            'Seen From': client_data['seen_from'],
                            'Local IP': client_data['local_ip'],
                            'Remote IP': client_data['remote_ip'],
                            'Client ID': client_id,
                            'Machine ID': client_data['machine_id'],
                            'Seen At': client_data['seen_at']
                        })

                    results_library = sorted(results_library, key=lambda x: sort_key(x["Hostname"].casefold()))

                elif selection == 'items_by_library_collection':
                    for collection in results_base_json:
                        collection_name = collection.get("Name", "Unknown Collection")
                        items = collection.get("Items", [])
                        for item in items:
                            results_library.append({
                                "program_id": item,
                                "library_collection_name": collection_name
                            })

                    results_library = sorted(results_library, key=lambda x: sort_key(x["library_collection_name"].casefold()))                    

                elif selection == 'dvr_status':
                    activity = results_base_json.get("activity", '')
                    busy = results_base_json.get("busy", '')
                    disk_free = results_base_json.get("disk", '').get("free", '')
                    disk_total = results_base_json.get("disk", '').get("total", '')
                    disk_used = results_base_json.get("disk", '').get("used", '')
                    enabled = results_base_json.get("enabled", '')
                    extra_paths = results_base_json.get("extra_paths", [])
                    guide_num_lineups = results_base_json.get("guide", {}).get("num_lineups", '')
                    guide_num_shows = results_base_json.get("guide", {}).get("num_shows", '')
                    guide_num_airings = results_base_json.get("guide", {}).get("num_airings", '')
                    guide_disk_size = results_base_json.get("guide", {}).get("disk_size", '')
                    guide_updated_at = results_base_json.get("guide", {}).get("updated_at", '')
                    has_live_tv_sources = results_base_json.get("has_live_tv_sources", '')
                    has_scannable_sources = results_base_json.get("has_scannable_sources", '')
                    keep_num = results_base_json.get("keep", '').get("num", '')
                    keep_only = results_base_json.get("keep", '').get("only", '')
                    last_backup = results_base_json.get("last_backup", '')
                    padding_end = results_base_json.get("padding", {}).get("end", '')
                    padding_start = results_base_json.get("padding", {}).get("start", '')
                    path = results_base_json.get("path", '')
                    stats_groups = results_base_json.get("stats", {}).get("groups", [])
                    stats_files = results_base_json.get("stats", {}).get("files", [])
                    stats_jobs = results_base_json.get("stats", {}).get("jobs", [])
                    stats_rules = results_base_json.get("stats", {}).get("rules", [])
                    status = results_base_json.get("status", '')
                    transcoder_cache_size = results_base_json.get("transcoder_cache", {}).get("size", '')
                    trash_after = results_base_json.get("trash", {}).get("after", '')

                    results_library.append({
                        "activity": activity,
                        "busy": busy,
                        "disk_free": disk_free,
                        "disk_total": disk_total,
                        "disk_used": disk_used,
                        "enabled": enabled,
                        "extra_paths": extra_paths,
                        "guide_num_lineups": guide_num_lineups,
                        "guide_num_shows": guide_num_shows,
                        "guide_num_airings": guide_num_airings,
                        "guide_disk_size": guide_disk_size,
                        "guide_updated_at": guide_updated_at,
                        "has_live_tv_sources": has_live_tv_sources,
                        "has_scannable_sources": has_scannable_sources,
                        "keep_num": keep_num,
                        "keep_only": keep_only,
                        "last_backup": last_backup,
                        "padding_end": padding_end,
                        "padding_start": padding_start,
                        "path": path,
                        "stats_groups": stats_groups,
                        "stats_files": stats_files,
                        "stats_jobs": stats_jobs,
                        "stats_rules": stats_rules,
                        "status": status,
                        "transcoder_cache_size": transcoder_cache_size,
                        "trash_after": trash_after
                    })

                elif selection == 'dvr_files':
                    for result in results_base_json:
                        dvr_files_id = result.get("ID", '')
                        dvr_files_group_id = result.get("GroupID", '')
                        dvr_files_path = result.get("Path", '')
                        dvr_files_checksum = result.get("Checksum", '')
                        dvr_files_created_at = result.get("CreatedAt", '')
                        dvr_files_fileSize = result.get("FileSize", '')
                        dvr_files_duration = result.get("Duration", '')
                        dvr_files_completed = result.get("Completed", '')
                        dvr_files_processed = result.get("Processed", '')
                        dvr_files_updated_at = result.get("UpdatedAt", '')
                        dvr_files_version = result.get("Version", '')
                        dvr_files_labels = result.get("Labels", [])
                        dvr_files_import_path = result.get("ImportPath", '')
                        dvr_files_import_query = result.get("ImportQuery", '')
                        dvr_files_import_group = result.get("ImportGroup", '')
                        dvr_files_imported_at = result.get("ImportedAt", '')
                    
                        results_library.append({
                            "File ID": dvr_files_id,
                            "Group ID": dvr_files_group_id,
                            "Path": dvr_files_path,
                            "Checksum": dvr_files_checksum,
                            "Created At": dvr_files_created_at,
                            "File Size": dvr_files_fileSize,
                            "Duration": dvr_files_duration,
                            "Completed": dvr_files_completed,
                            "Processed": dvr_files_processed,
                            "Updated At": dvr_files_updated_at,
                            "Version": dvr_files_version,
                            "Labels": dvr_files_labels,
                            "Import Path": dvr_files_import_path,
                            "Import Query": dvr_files_import_query,
                            "Import Group": dvr_files_import_group,
                            "Imported At": dvr_files_imported_at
                        })

                elif selection == 'dvr_groups':
                    for result in results_base_json:
                        dvr_groups_id = result.get("ID", '')
                        dvr_groups_name = result.get("Name", '')
                        dvr_groups_series_id = result.get("SeriesID", '')
                        dvr_groups_summary = result.get("Summary", '')
                        dvr_groups_image = result.get("Image", '')
                        dvr_groups_categories = result.get("Categories", [])
                        dvr_groups_genres = result.get("Genres", [])
                        dvr_groups_file_id = result.get("FileID", [])
                        dvr_groups_created_at = result.get("CreatedAt", '')
                        dvr_groups_recorded_at = result.get("RecordedAt", '')
                        dvr_groups_updated_at = result.get("UpdatedAt", '')
                        dvr_groups_refreshed_at = result.get("RefreshedAt", '')
                        dvr_groups_release_date = result.get("ReleaseDate", '')
                        dvr_groups_release_year = result.get("ReleaseYear", '')
                        dvr_groups_imported_at = result.get("ImportedAt", '')
                        dvr_groups_import_id = result.get("ImportID", [])
                        dvr_groups_labels = result.get("Labels", [])
                        dvr_groups_version = result.get("Version", '')
                        dvr_groups_num_unwatched = result.get("NumUnwatched", '')

                        results_library.append({
                            "Group ID": dvr_groups_id,
                            "Name": dvr_groups_name,
                            "Series ID": dvr_groups_series_id,
                            "Summary": dvr_groups_summary,
                            "Image": dvr_groups_image,
                            "Categories": dvr_groups_categories,
                            "Genres": dvr_groups_genres,
                            "File IDs": dvr_groups_file_id,
                            "Created At": dvr_groups_created_at,
                            "Recorded At": dvr_groups_recorded_at,
                            "Updated At": dvr_groups_updated_at,
                            "Refreshed At": dvr_groups_refreshed_at,
                            "Release Date": dvr_groups_release_date,
                            "Release Year": dvr_groups_release_year,
                            "Imported At": dvr_groups_imported_at,
                            "Import IDs": dvr_groups_import_id,
                            "Labels": dvr_groups_labels,
                            "Version": dvr_groups_version,
                            "Number Unwatched": dvr_groups_num_unwatched
                        })

    return results_library

def get_channels_dvr_activity():
    results_library = []
    results_library = get_channels_dvr_json('dvr_status')

    results = None
    results = results_library[0]['activity']

    return results

# Puts JSON data into Channels DVR
def put_channels_dvr_json(route, json_data):
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    full_url = f"{channels_url}{route}"
    results = None

    try:
        response = requests.put(full_url, headers=url_headers, json=json_data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        results = response

    except requests.RequestException as e:
        # Log error details
        print(f"{current_time()} ERROR: PUT request to {full_url} failed: {e}")
        if response is not None:
            print(f"{current_time()} ERROR: Response Status Code: {response.status_code}")
            print(f"{current_time()} ERROR: Response Body: {response.text}")

    return results

# Puts JSON data into Channels DVR simultaneously using async
async def put_channels_dvr_json_async(session, route, json_data):
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    full_url = f"{channels_url}{route}"
    result = {}
    
    try:
        async with session.put(full_url, headers=url_headers, json=json_data) as response:
            response.raise_for_status()
            result["status"] = response.status
            result["body"] = await response.text()
            result["error"] = None

    except Exception as e:
        result["status"] = None
        result["body"] = None
        result["error"] = str(e)
        print(f"{current_time()} ERROR: PUT request to {full_url} failed: {e}")

    return result

# Calculate percentages or set to zero if total_records is zero
def calc_percentage(count, total):
    return f"{round((count / total) * 100, 1)}%" if total > 0 else "0.0%"

# Global Variables

### [GEN] System
script_dir = os.path.dirname(os.path.abspath(__file__))
script_filename = os.path.basename(__file__)
log_filename = os.path.splitext(script_filename)[0] + '.log'
docker_channels_dir = os.path.join(script_dir, "channels_folder")
program_files_dir = os.path.join(script_dir, "program_files")
backup_dir = os.path.join(program_files_dir, "backups")
playlists_uploads_dir_name = "playlists_uploads"
playlists_uploads_dir = os.path.join(program_files_dir, playlists_uploads_dir_name)
csv_settings = "StreamLinkManager_Settings.csv"
csv_streaming_services = "StreamLinkManager_StreamingServices.csv"
csv_slm_subscribed_video_channels = "StreamLinkManager_SubscribedVideoChannels.csv"
csv_bookmarks = "StreamLinkManager_Bookmarks.csv"
csv_bookmarks_status = "StreamLinkManager_BookmarksStatus.csv"
csv_slmappings = "StreamLinkManager_SLMappings.csv"
csv_provider_groups = "StreamLinkManager_ProviderGroups.csv"
csv_slm_labels = "StreamLinkManager_Labels.csv"
csv_slm_label_maps = "StreamLinkManager_LabelMaps.csv"
csv_slm_feed_items = "StreamLinkManager_FeedItems.csv"
csv_slm_feed_rules = "StreamLinkManager_FeedRules.csv"
csv_slm_feed_maps = "StreamLinkManager_FeedMaps.csv"
csv_playlistmanager_playlists = "PlaylistManager_Playlists.csv"
csv_playlistmanager_combined_m3us = "PlaylistManager_Combinedm3us.csv"
csv_playlistmanager_parents = "PlaylistManager_Parents.csv"
csv_playlistmanager_child_to_parent = "PlaylistManager_ChildToParent.csv"
csv_playlistmanager_streaming_stations = "PlaylistManager_StreamingStations.csv"
csv_playlistmanager_station_mappings = "PlaylistManager_StationMappings.csv"
csv_files = [
    csv_settings,
    csv_streaming_services,
    csv_slm_subscribed_video_channels,
    csv_bookmarks,
    csv_bookmarks_status,
    csv_slmappings,
    csv_provider_groups,
    csv_slm_labels,
    csv_slm_label_maps,
    csv_slm_feed_items,
    csv_slm_feed_rules,
    csv_slm_feed_maps,
    csv_playlistmanager_playlists,
    csv_playlistmanager_combined_m3us,
    csv_playlistmanager_parents,
    csv_playlistmanager_child_to_parent,
    csv_playlistmanager_streaming_stations,
    csv_playlistmanager_station_mappings
]
program_files = csv_files + [log_filename]
gen_upgrade_flag = None
github_url = "https://github.com/babsonnexus/stream-link-manager-for-channels"
github_url_raw = "https://raw.githubusercontent.com/babsonnexus/stream-link-manager-for-channels/refs/heads/main/"
url_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
}
notifications = []
timeout_occurred = None

### [GEN] Settings and Other
channels_url_prior = None
select_file_prior = None
base_compare_options = [
    {'compare_id': 'equal', 'compare_name': 'Equals...'},
    {'compare_id': 'equal_not', 'compare_name': 'Does not equal...'},
]
numeric_compare_options = [
    {'compare_id': 'greater', 'compare_name': 'Greater than...'},
    {'compare_id': 'greater_equal', 'compare_name': 'Greater than or Equal to...'},
    {'compare_id': 'less', 'compare_name': 'Less than...'},
    {'compare_id': 'less_equal', 'compare_name': 'Less than or Equal to...'}
]
text_compare_options = [
    {'compare_id': 'contain', 'compare_name': 'Contains...'},
    {'compare_id': 'contain_not', 'compare_name': 'Does not contain...'},
    {'compare_id': 'begin', 'compare_name': 'Begins with...'},
    {'compare_id': 'begin_not', 'compare_name': 'Does not begin with...'},
    {'compare_id': 'end', 'compare_name': 'Ends with...'},
    {'compare_id': 'end_not', 'compare_name': 'Does not end with...'},
    {'compare_id': 'regex', 'compare_name': 'Matches REGEX...'},
    {'compare_id': 'regex_not', 'compare_name': 'Does not match REGEX...'}
]
compare_options = base_compare_options + text_compare_options
all_compare_options = base_compare_options + numeric_compare_options + text_compare_options
compare_replace_options = [
    {'compare_replace_id': 'na', 'compare_replace_name': 'N/A (Doing nothing with...)'},
    {'compare_replace_id': 'replace_string', 'compare_replace_name': 'Replacing string/pattern with...'},
    {'compare_replace_id': 'replace_all', 'compare_replace_name': 'Replacing entire contents with...'},
    {'compare_replace_id': 'append_string', 'compare_replace_name': 'Appending string/pattern with...'},
    {'compare_replace_id': 'append_all', 'compare_replace_name': 'Appending entire contents with...'},
    {'compare_replace_id': 'prepend_string', 'compare_replace_name': 'Prepending string/pattern with...'},
    {'compare_replace_id': 'prepend_all', 'compare_replace_name': 'Prepending entire contents with...'}
]
raw_articles = {
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
base_articles = []
for art_list in raw_articles.values():
    base_articles.extend(art_list)
base_articles = sorted(set(base_articles))

### [SLM] General
engine_url = "https://www.justwatch.com"
_GRAPHQL_API_URL = "https://apis.justwatch.com/graphql"
engine_image_url = "https://images.justwatch.com"
engine_image_profile_poster = "s718"
engine_image_profile_backdrop = "s1920"
engine_image_profile_icon = "s100"
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
    "ZM"
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
    "zh"
]
special_actions_default = [
    "None",
    "Make STRM",
    "Make SLM Stream"
]
video_providers = [
    "youtube"
]

### [SLM] Search / Add / Modify Programs
modify_entry_id = None
program_add_prior = ''
date_new_default_start_prior = None
date_new_default_end_prior = None
program_add_manual_prior = ''
program_add_import_playlist_prior = ''
program_search_results_prior = []
program_search_results_resort_alpha_flag = True
select_programs_to_edit = []
hidden_videos_entry_id = 'intHiddenVideos'
settings_country_code_input_prior = None
settings_language_code_input_prior = None
entry_id_selected_prior = None
object_type_selected_prior = None
bookmark_action_prior = None
override_program_sort_prior = None
program_modify_bookmark_selected_prior = []
program_modify_label_maps_selected_prior = []
program_modify_details_selected_prior = []
slm_manage_programs_main_flag = True
slm_manage_programs_search_results_flag = None
slm_manage_programs_modify_program_flag = None
slm_manage_programs_modify_program_scollbar_flag = None
slm_manage_programs_program_modify_available_flag = None
bookmark_actions_default = [
    "None",
    "Hide"
]
bookmark_actions_default_show_only = [
    "Disable Get New Episodes",
    "Import New Episode Metadata"
]
bookmark_actions_default_video_only = [
    "Sync Online Playlist"
]
provider_groups_default = [
    {
        "provider_group_id": "None",
        "provider_group_name": "None"
    }
]

### [SLM] Settings and Automation
slm_stream_address_prior = None
stream_link_ids_changed = []
slm_process_active_flag = None
slm_process_active_flag_turn_off = None

### [PLM] General
stream_formats = [
    "HLS",
    "MPEG-TS",
    "STRMLNK"
]
filter_title_assigned = ''
filter_m3u_name_assigned = ''
filter_description_assigned = ''
filter_parent_assigned = ''
filter_stream_format_override_assigned = ''
filter_station_status_assigned = ''
filter_title_unassigned = ''
filter_m3u_name_unassigned = ''
filter_description_unassigned = ''
filter_parent_unassigned = ''
filter_stream_format_override_unassigned = ''
filter_station_status_unassigned = ''
filter_parent_title = ''
filter_parent_tvg_id_override = ''
filter_parent_tvg_logo_override = ''
filter_parent_channel_number_override = ''
filter_parent_tvc_guide_stationid_override = ''
filter_parent_preferred_playlist = ''
filter_streams_source = ''
filter_streams_url = ''
filter_streams_title = ''
filter_streams_tvg_logo = ''
filter_streams_tvg_description = ''
filter_streams_tvc_guide_tags = ''
filter_streams_tvc_guide_genres = ''
filter_streams_tvc_guide_categories = ''
filter_streams_tvc_guide_placeholders = ''
filter_streams_tvc_stream_vcodec = ''
filter_streams_tvc_stream_acodec = ''
filter_modify_program_season_episode_prefix  = ''
filter_modify_program_season_episode  = ''
filter_modify_program_stream_link  = ''
filter_modify_program_stream_link_override  = ''
filter_modify_program_special_action  = ''
filter_modify_program_original_release_date  = ''
filter_modify_program_override_episode_title  = ''
filter_modify_program_override_summary  = ''
filter_modify_program_override_image  = ''
filter_modify_program_override_duration  = ''
parent_channel_id_prior = None
station_status_child_m3u_id_channel_id_prior = 'm3u_0000_manual'
station_status_manual_link_prior = ''
station_status_results_prior = []
station_status_message_prior = ''
streaming_stations_source_test_prior = ''
streaming_stations_url_test_prior = ''

### [PLM] Settings and Automation
plm_fields_base = [
    {'field_id': 'channel_id', 'field_name': 'Channel ID (channel-id)'},
    {'field_id': 'title', 'field_name': 'Station Name'},
    {'field_id': 'tvg_name', 'field_name': 'Guide Station Name/Callsign (tvg-name)'},
    {'field_id': 'tvg_description', 'field_name': 'Station Description (tvg-description)'},
    {'field_id': 'tvg_logo', 'field_name': 'Station Logo (tvg-logo)'},
    {'field_id': 'tvg_chno', 'field_name': 'Channel Number (tvg-chno)'},
    {'field_id': 'channel_number', 'field_name': 'Channel Number (channel-number)'},
    {'field_id': 'tvc_guide_stationid', 'field_name': 'Gracenote ID (tvc-guide-stationid)'},
    {'field_id': 'tvg_id', 'field_name': 'XML EPG Guide ID (tvg-id)'},
    {'field_id': 'tvc_guide_placeholders', 'field_name': 'Guide Placeholders (tvc-guide-placeholders)'},
    {'field_id': 'group_title', 'field_name': 'Categories (group-title)'},
    {'field_id': 'tvc_stream_vcodec', 'field_name': 'Stream Video Codec (tvc-stream-vcodec)'},
    {'field_id': 'tvc_stream_acodec', 'field_name': 'Stream Audio Codec (tvc-stream-acodec)'},
    {'field_id': 'tvc_guide_title', 'field_name': 'Guide Item Title (tvc-guide-title)'},
    {'field_id': 'tvc_guide_description', 'field_name': 'Guide Item Description (tvc-guide-description)'},
    {'field_id': 'tvc_guide_art', 'field_name': 'Guide Item Art (tvc-guide-art)'},
    {'field_id': 'tvc_guide_tags', 'field_name': 'Guide Item Tags (tvc-guide-tags)'},
    {'field_id': 'tvc_guide_genres', 'field_name': 'Guide Item Genres (tvc-guide-genres)'},
    {'field_id': 'tvc_guide_categories', 'field_name': 'Guide Item Categories (tvc-guide-categories)'},
    {'field_id': 'url', 'field_name': 'URL'}
]

### [MTM] Tools
select_report_query_prior = 'reports_queries_cancel'
slm_query = None
gracenote_search_results = None
gracenote_search_entry_prior = ''
csv_explorer_results = None
csv_explorer_entry_prior = ''
local_channels_client_selected = None

# Start-up process and safety checks
### Program directories
program_directories = [
    program_files_dir,
    backup_dir,
    playlists_uploads_dir
]
for program_directory in program_directories:
    create_directory(program_directory)

### Make a backup and remove old backups
if os.path.exists(program_files_dir):
    create_backup()

### Set up session logging
###### Custom logger to write yt-dlp output to your log file
class YTDLLogger:
    def debug(self, msg):
        log.write(msg + "\n")

    def info(self, msg):
        log.write(msg + "\n")

    def warning(self, msg):
        log.write("[WARNING] " + msg + "\n")

    def error(self, msg):
        log.write("[ERROR] " + msg + "\n")

###### Log Setup
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

###### Lower specific loggers to WARNING to reduce verbosity
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("chardet").setLevel(logging.WARNING)
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
logging.getLogger("streamlink").setLevel(logging.WARNING)
logging.getLogger("streamlink.session").setLevel(logging.WARNING)
logging.getLogger("streamlink.plugin").setLevel(logging.WARNING)
logging.getLogger("streamlink.stream").setLevel(logging.WARNING)
logging.getLogger("streamlink.cli").setLevel(logging.WARNING)

log = logger()

### Initialization
notification_add(f"{current_time()} Beginning Initialization Process (see log for details)...")

check_website(engine_url)

for csv_file in csv_files:
    check_and_create_csv(csv_file)

global_settings = read_data(csv_settings)

slm_playlist_manager = None
if global_settings[10]['settings'] == "On":
    slm_playlist_manager = True

slm_stream_link_file_manager = None
if global_settings[23]['settings'] == "On":
    slm_stream_link_file_manager = True

slm_channels_dvr_integration = None
if global_settings[24]['settings'] == "On":
    slm_channels_dvr_integration = True

slm_media_players_integration = None
if global_settings[72]['settings'] == "On":
    slm_media_players_integration = True

slm_media_tools_manager = None
if global_settings[28]['settings'] == "On":
    slm_media_tools_manager = True

plm_streaming_stations = None
if global_settings[39]['settings'] == "On":
    plm_streaming_stations = True

    if global_settings[45]['settings'] == "On":
        streaming_stations = read_data(csv_playlistmanager_streaming_stations)

        for streaming_station in streaming_stations:
            if streaming_station['source'] == 'YouTube Live (HLS)':
                streaming_station['source'] = 'Live Stream (HLS)'

        write_data(csv_playlistmanager_streaming_stations, streaming_stations)

        # Turn off to not run again
        global_settings[45]['settings'] = "Off"
        write_data(csv_settings, global_settings)

plm_check_child_station_status_global = None
if global_settings[59]['settings'] == "On":
    plm_check_child_station_status_global = True

if slm_channels_dvr_integration:
    check_channels_url(None)

check_upgrade()

### Start the background thread
thread = threading.Thread(target=check_schedule)
thread.daemon = True
thread.start()

if slm_channels_dvr_integration:
    notification_add(f"{current_time()} Initialization Complete. Starting Streaming Library Manager for Channels DVR...")
elif slm_media_players_integration:
    notification_add(f"{current_time()} Initialization Complete. Starting Streaming Library Manager for Media Players...")
else:
    notification_add(f"{current_time()} Initialization Complete. Starting Streaming Library Manager...")

### Start Server
if __name__ == "__main__":
    notification_add(f"{current_time()} INFO: Server starting on port {slm_port}")
    app.run(host='0.0.0.0', port=slm_port)
