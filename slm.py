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
from flask import Flask, render_template, render_template_string, request, redirect, url_for, Response, send_file, Request, make_response
from jinja2 import TemplateNotFound
import yt_dlp as youtube_dl

# Top Controls
slm_environment_version = None
slm_environment_port = None

# Current Stable Release
slm_version = "v2025.02.10.1635"
slm_port = os.environ.get("SLM_PORT")

# Current Development State
if slm_environment_version == "PRERELEASE":
    slm_version = "v2025.02.10.1635"
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
        self.max_form_parts = 1000000 # Individual web components

app.request_class = CustomRequest
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 200 # MB for submitting requests/files

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
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_notifications = notifications
    )

# Adds a notification
def notification_add(notification):
    global notifications
    notifications.insert(0, notification)
    print(notification)

# Seach for and bookmark programs, or add manual ones
@app.route('/addprograms', methods=['GET', 'POST'])
def webpage_add_programs():
    global program_search_results_prior
    global country_code_input_prior
    global language_code_input_prior
    global entry_id_prior
    global season_episodes_prior
    global date_new_default_prior
    global program_add_prior
    global program_add_resort_panel
    global program_add_filter_panel
    global title_selected_prior
    global release_year_selected_prior
    global bookmark_action_prior
    global select_program_to_bookmarks

    settings = read_data(csv_settings)
    country_code = settings[2]["settings"]
    language_code = settings[3]["settings"]
    num_results = settings[4]["settings"]
    hide_bookmarked = settings[9]["settings"]

    special_actions = []
    special_actions = get_special_actions()

    program_types = [
                        "MOVIE",
                        "SHOW",
                        "VIDEO"
                    ]
    program_type_default = "MOVIE"

    program_add_message = ""
    program_search_results = []
    season_episodes = []
    video_season_episodes = []
    season_episode_manual_flag = None
    video_manual_flag = None
    end_season = None
    season_episodes_manual = {}
    stream_link_override_movie_flag = None
    done_generate_flag = None
    num_results_test = None
    bookmark_actions = []

    date_new_default = datetime.datetime.now().strftime('%Y-%m-%d')
    if date_new_default_prior is None or date_new_default_prior == '':
        date_new_default_prior = date_new_default

    if request.method == 'POST':
        add_programs_action = request.form['action']
        program_add_input = request.form.get('program_add')
        program_add_prior = program_add_input

        # Cancel and restart the page
        if add_programs_action == 'program_add_cancel':
            program_add_prior = ''
            program_add_resort_panel = ''
            program_add_filter_panel = ''
        
        # Search for a program
        elif add_programs_action in ['program_add_search', 'program_new_search', 'program_new_today']:
            country_code_input = request.form.get('country_code')
            language_code_input = request.form.get('language_code')
            hide_bookmarked_input = request.form.get('hide_bookmarked')
            hide_bookmarked_input = "On" if hide_bookmarked_input == 'on' else "Off"

            if add_programs_action == 'program_add_search':
                num_results_input = request.form.get('num_results')
                num_results_test = get_num_results(num_results_input)

                if num_results_test == "pass":
                    program_search_results = search_bookmark(country_code_input, language_code_input, num_results_input, program_add_input)
                    country_code_input_prior = country_code_input
                    language_code_input_prior = language_code_input
                    program_add_resort_panel = 'on'
                    program_add_filter_panel = 'on'

                else:
                    program_add_message = num_results_test

            elif add_programs_action in ['program_new_search', 'program_new_today']:
                if add_programs_action == 'program_new_search':
                    date_new_input = request.form.get('date_new')
                elif add_programs_action == 'program_new_today':
                    date_new_input = date_new_default

                date_new_default_prior = date_new_input
                num_results_input = 100 # Maximum number of new programs

                program_search_results = get_program_new(date_new_input, country_code_input, language_code_input, num_results_input)
                program_search_results = sorted(program_search_results, key=lambda x: sort_key(x["title"].casefold()))
                country_code_input_prior = country_code_input
                language_code_input_prior = language_code_input
                program_add_resort_panel = ''
                program_add_filter_panel = 'on'

            if program_search_results:
                bookmarks = read_data(csv_bookmarks)

                if hide_bookmarked_input == "On":
                    bookmarked_entry_ids = {bookmark['entry_id'] for bookmark in bookmarks}
                    program_search_results = [entry for entry in program_search_results if entry['entry_id'] not in bookmarked_entry_ids]

                hidden_bookmarks = {bookmark['entry_id'] for bookmark in bookmarks if bookmark['bookmark_action'] == "Hide"}
                program_search_results = [entry for entry in program_search_results if entry['entry_id'] not in hidden_bookmarks]

                # Replace None in 'poster' with the default URL
                default_poster_url = 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Missing_barnstar.jpg'
                for entry in program_search_results:
                    if entry['poster'] is None:
                        entry['poster'] = default_poster_url

                program_search_results_prior = program_search_results

        # Filter and resort search results
        elif add_programs_action.startswith('program_add_resort_') or add_programs_action.startswith('hide_program_search_result_'):

            if add_programs_action == 'program_add_resort_alpha':
                program_search_results = sorted(program_search_results_prior, key=lambda x: sort_key(x["title"].casefold()))
                program_add_resort_panel = ''

            elif add_programs_action.startswith('program_add_resort_filter_'):

                if add_programs_action == 'program_add_resort_filter_movie':
                    program_search_results = [item for item in program_search_results_prior if item['object_type'] == 'MOVIE']

                elif add_programs_action == 'program_add_resort_filter_show':
                    program_search_results = [item for item in program_search_results_prior if item['object_type'] == 'SHOW']

                program_add_filter_panel = ''

            elif add_programs_action.startswith('hide_program_search_result_'):
                hide_programs = []
                
                if add_programs_action.endswith('selected'):
                    for key in request.form.keys():
                        if key.startswith('select_program_search_result_') and request.form.get(key) == 'on':
                            hide_program_index = int(key.split('_')[-1]) - 1
                            hide_programs.append(hide_program_index)

                else:
                    hide_program_index = int(add_programs_action.split('_')[-1]) - 1
                    hide_programs.append(hide_program_index)
                
                hide_programs.sort(reverse=True)

                program_search_results = program_search_results_prior

                for program_search_index in hide_programs:
                    program_search_results, program_add_message = hide_bookmark_select(program_search_results, program_search_index, country_code_input_prior, language_code_input_prior)
            
            program_search_results_prior = program_search_results

        # Select a program from the search
        elif add_programs_action.startswith('program_search_result_'):
            program_add_resort_panel = ''
            program_add_filter_panel = ''

            select_programs = []

            if add_programs_action.endswith('selected'):
                for key in request.form.keys():
                    if key.startswith('select_program_search_result_') and request.form.get(key) == 'on':
                        select_program_index = int(key.split('_')[-1]) - 1
                        select_programs.append(select_program_index)

            else:
                select_program_index = int(add_programs_action.split('_')[-1]) - 1
                select_programs.append(select_program_index)
            
            select_programs.sort(reverse=True)

            for program_search_index in select_programs:
                program_add_message, entry_id, season_episodes, object_type = search_bookmark_select(program_search_results_prior, program_search_index, country_code_input_prior, language_code_input_prior)

                select_program_to_bookmarks.append({
                    'program_add_message': program_add_message,
                    'entry_id': entry_id,
                    'season_episodes': season_episodes,
                    'object_type': object_type
                })

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
                    set_bookmarks(entry_id, program_add_input, release_year_input, program_type_input, "N/A", "N/A", "N/A", "manual", "None")
                    
                    program_add_message = f"{current_time()} You manually added: {program_add_input} ({release_year_input}) | {program_type_input} (ID: {entry_id})"
                    
                    bookmarks = read_data(csv_bookmarks)
                    for bookmark in bookmarks:
                        if bookmark['entry_id'] == entry_id_prior:
                            title_selected_prior = bookmark['title']
                            release_year_selected_prior = bookmark['release_year']
                            bookmark_action_prior = bookmark['bookmark_action']
                    
                    if program_type_input == "SHOW":
                        season_episode_manual_flag = True
                    elif program_type_input == "VIDEO":
                        video_manual_flag = True
                    else:
                        special_actions = special_actions_default.copy()
                        stream_link_override_movie_flag = True
                        done_generate_flag = True
                
                    bookmark_actions = get_bookmark_actions(program_type_input)

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
            special_actions = special_actions_default.copy()
            bookmark_actions = get_bookmark_actions("SHOW")

        # Create a video list for a manual video group
        elif add_programs_action == 'video_manual_next':
            number_of_videos_input = int(request.form.get('number_of_videos'))

            video_season_episodes = []

            for i in range(1, int(number_of_videos_input) + 1):
                video_season_episode = f"Input name for Video {i:02d}"
                video_season_episodes.append({
                    "season_episode_id": "VIDEO",
                    "season_episode": video_season_episode
                })

            season_episodes_prior = video_season_episodes
            done_generate_flag = True
            special_actions = special_actions_default.copy()
            bookmark_actions = get_bookmark_actions("VIDEO")

        # Finish or Generate Stream Links/Files. Also save Season/Episode statuses.
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
                field_special_action_inputs = {}
                video_names = []

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

                    if key.startswith('field_special_action_'):
                        index = key.split('_')[-1]
                        field_special_action_inputs[index] = request.form.get(key)

                for index in field_season_episode_inputs.keys():
                    season_episode_id = None
                    season_episode_prefix = field_season_episode_prefix_inputs.get(index)
                    
                    season_episode = field_season_episode_inputs.get(index)
                    if season_episodes_prior[int(index) - 1]['season_episode_id'] == "VIDEO":
                        if season_episode is None or season_episode == '':
                            season_episode = season_episodes_prior[int(index) - 1]['season_episode']
                        elif season_episode in video_names:
                            season_episode = f"Duplicate Video Name {int(index):02d}"
                        else:
                            video_names.append(season_episode)
                    
                    if field_status_inputs.get(index) == "unwatched":
                        status = field_status_inputs.get(index)
                    else:
                        status = "watched"
                    
                    stream_link_override = field_stream_link_override_inputs.get(index)
                    special_action = field_special_action_inputs.get(index)

                    if season_episodes_prior[int(index) - 1]['season_episode_id'] == "VIDEO":
                        pass
                    else:
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
                        "stream_link_file": None,
                        "special_action": special_action,
                        "original_release_date": None
                    })

            # Get settings for a Movie and write back
            else:
                status_movie_input = None
                stream_link_override_movie_input = None
                special_action_movie_input = None

                status_movie_input = 'unwatched' if request.form.get('status_movie') == 'on' else 'watched'
                if status_movie_input == "unwatched":
                    pass
                else:
                    status_movie_input = "watched"
                stream_link_override_movie_input = request.form.get('stream_link_override_movie')
                special_action_movie_input = request.form.get('special_action_movie')

                for bookmark_status in bookmarks_statuses:
                    if bookmark_status['entry_id'] == entry_id_prior:
                        bookmark_status['status'] = status_movie_input
                        bookmark_status['stream_link_override'] = stream_link_override_movie_input
                        bookmark_status['special_action'] = special_action_movie_input

            write_data(csv_bookmarks_status, bookmarks_statuses)

            if add_programs_action == 'program_add_generate':
                program_add_message = generate_stream_links_single(entry_id_prior)
            else:
                program_add_message = f"{current_time()} INFO: Finished adding! Please remember to generate stream links and update in Channels to see this program."

            # Get Bookmark Updates
            field_title_input = request.form.get('field_title')
            field_release_year_input = request.form.get('field_release_year')
            field_bookmark_action_input = request.form.get('field_bookmark_action')

            save_error_bookmarks = 0

            release_year_test = get_release_year(field_release_year_input)
            if release_year_test == "pass":
                new_release_year = field_release_year_input
            else:
                program_add_message = release_year_test
                program_add_message = f"{program_add_message} Saved with original 'Release Year'."
                save_error_bookmarks = save_error_bookmarks + 1

            if field_title_input != "":
                new_title = field_title_input
            else:
                program_add_message = f"{current_time()} ERROR: 'Title' cannot be empty. Saved with original 'Title'."
                save_error_bookmarks = save_error_bookmarks + 1

            new_bookmark_action = field_bookmark_action_input

            if save_error_bookmarks == 0:

                bookmarks = read_data(csv_bookmarks)

                for bookmark in bookmarks:
                    if bookmark["entry_id"] == entry_id_prior:
                        bookmark['title'] = new_title
                        bookmark['release_year'] = new_release_year
                        bookmark['bookmark_action'] = new_bookmark_action

                write_data(csv_bookmarks, bookmarks)

                if new_bookmark_action == "Hide":
                    remove_row_csv(csv_bookmarks_status, entry_id_prior)

            program_search_results_prior = []
            country_code_input_prior = None
            language_code_input_prior = None
            entry_id_prior = None
            season_episodes_prior = []
            program_add_prior = ''
            title_selected_prior = None
            release_year_selected_prior = None
            bookmark_action_prior = None

        if select_program_to_bookmarks:
            for select_program_to_bookmark in select_program_to_bookmarks:

                select_program_to_bookmarks.remove(select_program_to_bookmark)
                program_add_message = select_program_to_bookmark['program_add_message']
                entry_id = select_program_to_bookmark['entry_id']
                season_episodes = select_program_to_bookmark['season_episodes']
                object_type = select_program_to_bookmark['object_type']

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
                    bookmark_actions = get_bookmark_actions(object_type)

                    bookmarks = read_data(csv_bookmarks)
                    for bookmark in bookmarks:
                        if bookmark['entry_id'] == entry_id_prior:
                            title_selected_prior = bookmark['title']
                            release_year_selected_prior = bookmark['release_year']
                            bookmark_action_prior = bookmark['bookmark_action']
                            break

                    break

    return render_template(
        'main/addprograms.html',
        segment='addprograms',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_valid_country_codes = valid_country_codes,
        html_country_code = country_code,
        html_valid_language_codes = valid_language_codes,
        html_language_code = language_code,
        html_num_results = num_results,
        html_hide_bookmarked = hide_bookmarked,
        html_program_types = program_types,
        html_program_type_default = program_type_default,
        html_program_add_message = program_add_message,
        html_program_search_results = program_search_results,
        html_season_episodes = season_episodes,
        html_video_season_episodes = video_season_episodes,
        html_season_episode_manual_flag = season_episode_manual_flag,
        html_video_manual_flag = video_manual_flag,
        html_stream_link_override_movie_flag = stream_link_override_movie_flag,
        html_done_generate_flag = done_generate_flag,
        html_date_new_default = date_new_default_prior,
        html_program_add_prior = program_add_prior,
        html_special_actions = special_actions,
        html_program_add_resort_panel = program_add_resort_panel,
        html_program_add_filter_panel = program_add_filter_panel,
        html_bookmark_actions = bookmark_actions,
        html_title_selected = title_selected_prior,
        html_release_year_selected = release_year_selected_prior,
        html_bookmark_action_selected = bookmark_action_prior
    )

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
            action
            bookmark_actions.append(action)

    return bookmark_actions

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

# Find new programs on selected Streaming Services
def get_program_new(date_new, country_code, language_code, num_results):
    services = read_data(csv_streaming_services)
    check_services = [service for service in services if service["streaming_service_subscribe"] == "True"]
    check_services.sort(key=lambda x: int(x.get("streaming_service_priority", float("inf"))))
    streaming_services_map = []
    check_services_codes = []

    streaming_services_map = get_streaming_services_map()

    for check_service in check_services:
        for streaming_service in streaming_services_map:
            if check_service['streaming_service_name'] == streaming_service['streaming_service_name']: 
                check_services_codes.append(streaming_service['streaming_service_code'])

    program_new_results = []
    program_new_results_json = []
    program_new_results_json_array = []
    program_new_results_json_array_extracted = []
    program_new_results_json_array_extracted_unique = []

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

    try:
        program_new_results = requests.post(_GRAPHQL_API_URL, headers=url_headers, json=json_data)
        program_new_results_json = program_new_results.json()
    except requests.RequestException as e:
        print(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")

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
                print(f"\n{current_time()} WARNING: Unable to find offer icon for {record}. Skipping...")

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
        program_new_results_json_array_extracted_unique = []
        seen_entries = set()

        for record in program_new_results_json_array_extracted:
            identifier = (record['entry_id'], record['title'], record['release_year'], record['object_type'], record['url'])
    
            if identifier not in seen_entries:
                seen_entries.add(identifier)
                program_new_results_json_array_extracted_unique.append(record)

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
        print(f"\n{current_time()} WARNING: {e}. Skipping, please try again.")

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
                season_episodes = set_bookmarks(program_search_selected_entry_id, program_search_selected_title, program_search_selected_release_year, program_search_selected_object_type, program_search_selected_url, country_code, language_code, "search", "None")

        else:
            program_search_selected_message = f"{current_time()} ERROR: Invalid selection. Please choose a valid option."

    except ValueError:
       program_search_selected_message = f"{current_time()} ERROR: Invalid input. Please enter a valid option."

    return program_search_selected_message, program_search_selected_entry_id, season_episodes, program_search_selected_object_type

# Hides the selected program
def hide_bookmark_select(program_search_results, program_search_index, country_code, language_code):
    program_search_selected_message = ''
    program_search_selected_entry_id = None
    program_search_selected_title = None
    program_search_selected_release_year = None
    program_search_selected_object_type = None
    program_search_selected_url = None

    try:
        if 0 <= int(program_search_index) < len(program_search_results):
            program_search_selected_entry_id = program_search_results[program_search_index]['entry_id']
            program_search_selected_title = program_search_results[program_search_index]['title']
            program_search_selected_release_year = program_search_results[program_search_index]['release_year']
            program_search_selected_object_type = program_search_results[program_search_index]['object_type']
            program_search_selected_url = program_search_results[program_search_index]['url']

            # Check versus already bookmarked
            bookmarks = read_data(csv_bookmarks)
            bookmarks_append = True
            
            # Reject existing bookmark
            for bookmark in bookmarks:
                if bookmark["entry_id"] == program_search_selected_entry_id:
                    program_search_selected_message = f"{current_time()} WARNING: {program_search_selected_title} ({program_search_selected_release_year}) | {program_search_selected_object_type} (ID: {program_search_selected_entry_id}) already bookmarked!"
                    bookmarks_append = False

            # Write new rows to the bookmark tables and remove from list
            if bookmarks_append:
                new_row = {'entry_id': program_search_selected_entry_id, 'title': program_search_selected_title, 'release_year': program_search_selected_release_year, 'object_type': program_search_selected_object_type, 'url': program_search_selected_url, "country_code": country_code, "language_code": language_code, "bookmark_action": "Hide"}
                append_data(csv_bookmarks, new_row)

                program_search_results.pop(program_search_index)

        else:
            program_search_selected_message = f"{current_time()} ERROR: Invalid selection. Please choose a valid option."

    except ValueError:
       program_search_selected_message = f"{current_time()} ERROR: Invalid input. Please enter a valid option."

    return program_search_results, program_search_selected_message

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
def set_bookmarks(entry_id, title, release_year, object_type, url, country_code, language_code, type, bookmark_action):
    season_episodes = []

    new_row = {'entry_id': entry_id, 'title': title, 'release_year': release_year, 'object_type': object_type, 'url': url, "country_code": country_code, "language_code": language_code, "bookmark_action": bookmark_action}
    append_data(csv_bookmarks, new_row)

    if object_type == "MOVIE":
        new_row = {"entry_id": entry_id, "season_episode_id": None, "season_episode_prefix": None, "season_episode": None, "status": "unwatched", "stream_link": None, "stream_link_override": None, "stream_link_file": None, "special_action": None, "original_release_date": None}
        append_data(csv_bookmarks_status, new_row)
    elif object_type == "SHOW":
        if type == "search":
            season_episodes = get_episode_list(entry_id, url, country_code, language_code)

    if type == "search":
        return season_episodes

# Modify existing programs
@app.route('/modifyprograms', methods=['GET', 'POST'])
def webpage_modify_programs():
    global entry_id_prior
    global title_selected_prior
    global release_year_selected_prior
    global bookmark_action_prior
    global object_type_selected_prior
    global bookmarks_statuses_selected_prior
    global edit_flag
    global offer_icons
    global offer_icons_flag

    bookmarks = read_data(csv_bookmarks)
    bookmarks_statuses = read_data(csv_bookmarks_status)

    sorted_bookmarks = sorted((bookmark for bookmark in bookmarks if bookmark['bookmark_action'] != 'Hide'), key=lambda x: sort_key(x["title"]))
    program_modify_message = ''
    bookmarks_statuses_selected = []

    special_actions = []
    special_actions = get_special_actions()

    bookmark_actions = []
    new_bookmark_action = None

    if request.method == 'POST':
        modify_programs_action = request.form['action']
        entry_id_input = request.form.get('entry_id')
        field_title_input = request.form.get('field_title')
        field_release_year_input = request.form.get('field_release_year')
        field_bookmark_action_input = request.form.get('field_bookmark_action')

        if modify_programs_action in [
                                        'program_modify_edit',
                                        'program_modify_delete',
                                        'program_modify_generate',
                                        'program_modify_available'
                                     ]:
            
            entry_id_prior = entry_id_input
            offer_icons = []
            offer_icons_flag = None

            if modify_programs_action in [
                                            'program_modify_edit',
                                            'program_modify_delete'
                                        ]:

                for bookmark in bookmarks:
                    if bookmark['entry_id'] == entry_id_prior:
                        title_selected_prior = bookmark['title']
                        release_year_selected_prior = bookmark['release_year']
                        object_type_selected_prior = bookmark['object_type']
                        bookmark_action_prior = bookmark['bookmark_action']

                # Opens the edit frame
                if modify_programs_action == 'program_modify_edit':
                    edit_flag = True
                    bookmark_actions = get_bookmark_actions(object_type_selected_prior)

                    for bookmark_status in bookmarks_statuses:
                        if bookmark_status['entry_id'] == entry_id_prior:
                            bookmarks_statuses_selected.append(bookmark_status)

                    if object_type_selected_prior == "VIDEO":
                        bookmarks_statuses_selected_sorted = bookmarks_statuses_selected
                    else:
                        bookmarks_statuses_selected_sorted = sorted(bookmarks_statuses_selected, key=lambda x: x["season_episode"].casefold())
                    
                    bookmarks_statuses_selected_prior = bookmarks_statuses_selected_sorted

                    if entry_id_prior.startswith('slm'):
                        special_actions = special_actions_default.copy()

                # Deletes the program
                elif modify_programs_action == 'program_modify_delete':
                    remove_row_csv(csv_bookmarks, entry_id_prior)
                    remove_row_csv(csv_bookmarks_status, entry_id_prior)

                    bookmarks = read_data(csv_bookmarks)
                    sorted_bookmarks = sorted((bookmark for bookmark in bookmarks if bookmark['bookmark_action'] != 'Hide'), key=lambda x: sort_key(x["title"]))
                    bookmarks_statuses = read_data(csv_bookmarks_status)

                    movie_path, tv_path, video_path = get_movie_tv_path()

                    print(f"\nRemoved files/directories:\n")
                    remove_rogue_empty(movie_path, tv_path, video_path, bookmarks_statuses)

                    if object_type_selected_prior == "MOVIE":
                        program_modify_message = f"{current_time()} INFO: {title_selected_prior} ({release_year_selected_prior}) | {object_type_selected_prior} removed/deleted"

                    elif object_type_selected_prior == "SHOW":
                        program_modify_message = f"{current_time()} INFO: {title_selected_prior} ({release_year_selected_prior}) | {object_type_selected_prior} and all episodes removed/deleted"

                    elif object_type_selected_prior == "VIDEO":
                        program_modify_message = f"{current_time()} INFO: {title_selected_prior} ({release_year_selected_prior}) | {object_type_selected_prior} group and all videos removed/deleted"

                    else:
                        program_modify_message = f"{current_time()} ERROR: Invalid object_type"

                    entry_id_prior = None
                    title_selected_prior = None
                    release_year_selected_prior = None
                    object_type_selected_prior = None
                    bookmark_action_prior = None

            # Generates Stream Links for the program
            elif modify_programs_action == 'program_modify_generate':
                program_modify_message = generate_stream_links_single(entry_id_prior)

            # Checks the availability of a program
            elif modify_programs_action == 'program_modify_available':
                if not entry_id_prior.startswith('slm'):

                    bookmarks = read_data(csv_bookmarks)
                    modify_bookmarks = [bookmark for bookmark in bookmarks if bookmark['entry_id'] == entry_id_prior]

                    for modify_bookmark in modify_bookmarks:
                        node_id = modify_bookmark['entry_id']
                        country_code = modify_bookmark['country_code']
                        language_code = modify_bookmark['language_code']

                    stream_link_details = get_offers(node_id, country_code, language_code)
                    stream_link_offers = extract_offer_info(stream_link_details)
                    stream_link_offers_sorted = sorted(stream_link_offers, key=lambda x: sort_key(x["name"]))

                    for offer in stream_link_offers_sorted:
                        offer_icons.append(offer['icon'])

                    offer_icons = list(dict.fromkeys(offer_icons))
                    offer_icons_flag = True

                else:
                    program_modify_message = f"{current_time()} ERROR: Manual programs cannot be checked for availability."

        elif modify_programs_action.startswith('program_modify_delete_episode_') or modify_programs_action in [
                                                                                                                'program_modify_add_episode',
                                                                                                                'program_modify_save'
                                                                                                              ]:
            edit_flag = True

            if entry_id_prior.startswith('slm'):
                special_actions = special_actions_default.copy()

            # Add an episode
            if modify_programs_action == 'program_modify_add_episode':
                program_modify_add_episode_season_input = request.form.get('program_modify_add_episode_season')
                program_modify_add_episode_episode_input = request.form.get('program_modify_add_episode_episode')
                program_modify_add_episode_episode_prefix_input = request.form.get('program_modify_add_episode_episode_prefix')
                program_modify_add_episode_stream_link_override_input = request.form.get('program_modify_add_episode_stream_link_override')
                program_modify_add_episode_special_action_input = request.form.get('program_modify_add_episode_special_action')

                new_season_episode_test = 0

                if object_type_selected_prior == "SHOW":

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

                elif object_type_selected_prior == "VIDEO":

                    if program_modify_add_episode_episode_input is None or program_modify_add_episode_episode_input == '':
                        program_modify_message = f"{current_time()} ERROR: Video Name is required for new Videos."
                    else:
                        new_season_episode_test = 2

                if new_season_episode_test == 2:

                    new_season_episode_error = 0

                    if object_type_selected_prior == "SHOW":

                        formatted_season = f"S{new_season_num:02d}"
                        formatted_episode = f"E{new_episode_num:02d}"

                        new_season_episode = formatted_season + formatted_episode

                    elif object_type_selected_prior == "VIDEO":

                        new_season_episode = program_modify_add_episode_episode_input

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

                        if program_modify_add_episode_special_action_input == '':
                            new_special_action = None
                        else:
                            new_special_action = program_modify_add_episode_special_action_input

                        new_row = {"entry_id": entry_id_prior, "season_episode_id": None, "season_episode_prefix": new_episode_prefix, "season_episode": new_season_episode, "status": "unwatched", "stream_link": None, "stream_link_override": new_stream_link, "stream_link_file": None, "special_action": new_special_action, "original_release_date": None}
                        append_data(csv_bookmarks_status, new_row)

            elif modify_programs_action.startswith('program_modify_delete_episode_') or modify_programs_action == 'program_modify_save':

                rebuild_bookmark_status_trigger = None

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

                            movie_path, tv_path, video_path = get_movie_tv_path()

                            print(f"\nRemoved files/directories:\n")
                            remove_rogue_empty(movie_path, tv_path, video_path, bookmarks_statuses)

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

                    new_bookmark_action = field_bookmark_action_input

                    if save_error_bookmarks == 0:

                        if bookmark_action_prior == "Hide" and new_bookmark_action != "Hide":
                            rebuild_bookmark_status_trigger = True

                        title_selected_prior = new_title
                        release_year_selected_prior = new_release_year
                        bookmark_action_prior = new_bookmark_action

                        program_modify_message = f"{current_time()} INFO: Save successful!"

                        for bookmark in bookmarks:
                            if bookmark["entry_id"] == entry_id_prior:
                                bookmark['title'] = new_title
                                bookmark['release_year'] = new_release_year
                                bookmark['bookmark_action'] = new_bookmark_action

                        write_data(csv_bookmarks, bookmarks)
                        bookmarks = read_data(csv_bookmarks)
                        sorted_bookmarks = sorted((bookmark for bookmark in bookmarks if bookmark['bookmark_action'] != 'Hide'), key=lambda x: sort_key(x["title"]))

                    # Modify Bookmarks Statuses
                    field_object_type_input = request.form.get('field_object_type')
                    field_status_inputs = {}
                    field_stream_link_override_inputs = {}
                    field_season_episode_inputs = {}
                    field_season_episode_prefix_inputs = {}
                    field_special_action_inputs = {}

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

                        if key.startswith('field_special_action_'):
                            index = key.split('_')[-1]
                            field_special_action_inputs[index] = request.form.get(key)

                        if field_object_type_input == 'SHOW' or field_object_type_input == 'VIDEO':
                            if key.startswith('field_season_episode_'):
                                index = key.split('_')[-1]
                                field_season_episode_inputs[index] = request.form.get(key)

                            if key.startswith('field_episode_prefix_'):
                                index = key.split('_')[-1]
                                field_season_episode_prefix_inputs[index] = request.form.get(key)

                    if field_object_type_input == 'MOVIE':
                        for index in field_status_inputs.keys():
                            field_status_input = field_status_inputs.get(index)
                            field_stream_link_override_input = field_stream_link_override_inputs.get(index)
                            field_special_action_input = field_special_action_inputs.get(index)

                            for bookmarks_status in bookmarks_statuses:
                                if bookmarks_status['entry_id'] == entry_id_prior:
                                    bookmarks_status['status'] = field_status_input
                                    bookmarks_status['stream_link_override'] = field_stream_link_override_input
                                    bookmarks_status['special_action'] = field_special_action_input

                    elif field_object_type_input == 'SHOW' or field_object_type_input == 'VIDEO':
                        video_names = []

                        for index in field_season_episode_inputs.keys():
                            field_status_input = field_status_inputs.get(index)
                            field_stream_link_override_input = field_stream_link_override_inputs.get(index)
                            field_season_episode_input = field_season_episode_inputs.get(index)
                            field_season_episode_prefix_input = field_season_episode_prefix_inputs.get(index)
                            field_special_action_input = field_special_action_inputs.get(index)

                            video_instance_counter = 0

                            for bookmarks_status in bookmarks_statuses:

                                if field_object_type_input == 'VIDEO' and bookmarks_status['entry_id'] == entry_id_prior:
                                    video_instance_counter = int(video_instance_counter) + 1

                                if ( field_object_type_input == 'SHOW' and bookmarks_status['entry_id'] == entry_id_prior and bookmarks_status['season_episode'] == field_season_episode_input ) or ( field_object_type_input == 'VIDEO' and bookmarks_status['entry_id'] == entry_id_prior and int(video_instance_counter) == int(index) ):
                                    bookmarks_status['status'] = field_status_input
                                    bookmarks_status['stream_link_override'] = field_stream_link_override_input
                                    bookmarks_status['season_episode_prefix'] = field_season_episode_prefix_input
                                    bookmarks_status['special_action'] = field_special_action_input
                                    if field_object_type_input == 'VIDEO':
                                        if field_season_episode_input is None or field_season_episode_input == '':
                                            bookmarks_status['season_episode'] = f"Missing Video Name {int(index):02d}"
                                        elif field_season_episode_input in video_names:
                                            bookmarks_status['season_episode'] = f"Duplicate Video Name {int(index):02d}"
                                        else:
                                            bookmarks_status['season_episode'] = field_season_episode_input
                                            video_names.append(field_season_episode_input)

                write_data(csv_bookmarks_status, bookmarks_statuses)

                if new_bookmark_action == "Hide":
                    remove_row_csv(csv_bookmarks_status, entry_id_prior)

                if rebuild_bookmark_status_trigger:
                    if object_type_selected_prior == "MOVIE":
                        new_row = {"entry_id": entry_id_prior, "season_episode_id": None, "season_episode_prefix": None, "season_episode": None, "status": "unwatched", "stream_link": None, "stream_link_override": None, "stream_link_file": None, "special_action": None, "original_release_date": None}
                        append_data(csv_bookmarks_status, new_row)
                    elif object_type_selected_prior == "SHOW":
                        get_new_episodes(entry_id_prior)

            bookmarks_statuses = read_data(csv_bookmarks_status)

            for bookmark_status in bookmarks_statuses:
                if bookmark_status['entry_id'] == entry_id_prior:
                    bookmarks_statuses_selected.append(bookmark_status)

            if object_type_selected_prior == "VIDEO":
                bookmarks_statuses_selected_sorted = bookmarks_statuses_selected
            else:
                bookmarks_statuses_selected_sorted = sorted(bookmarks_statuses_selected, key=lambda x: x["season_episode"].casefold())
            bookmarks_statuses_selected_prior = bookmarks_statuses_selected_sorted

            bookmark_actions = get_bookmark_actions(object_type_selected_prior)

        # Cancel changes or finish
        elif modify_programs_action == 'program_modify_cancel':
            edit_flag = None
            title_selected_prior = None
            release_year_selected_prior = None
            object_type_selected_prior = None
            bookmark_action_prior = None
            bookmarks_statuses_selected_prior = []
            bookmark_actions = []
            new_bookmark_action = None

        elif modify_programs_action == 'program_modify_show_hidden':
            bookmarks = read_data(csv_bookmarks)
            bookmarks_statuses = read_data(csv_bookmarks_status)

            sorted_bookmarks = sorted(bookmarks, key=lambda x: sort_key(x["title"]))
            program_modify_message = ''
            bookmarks_statuses_selected = []

            special_actions = []
            special_actions = get_special_actions()

            bookmark_actions = []
            new_bookmark_action = None

    return render_template(
        'main/modifyprograms.html',
        segment = 'modifyprograms',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_sorted_bookmarks = sorted_bookmarks,
        html_entry_id_selected = entry_id_prior,
        html_program_modify_message = program_modify_message,
        html_edit_flag = edit_flag,
        html_title_selected = title_selected_prior,
        html_release_year_selected = release_year_selected_prior,
        html_object_type_selected = object_type_selected_prior,
        html_bookmarks_statuses_selected = bookmarks_statuses_selected_prior,
        html_special_actions = special_actions,
        html_offer_icons = offer_icons,
        html_offer_icons_flag = offer_icons_flag,
        html_bookmark_actions = bookmark_actions,
        html_bookmark_action_selected = bookmark_action_prior
    )

# Playlists webpage and actions
@app.route('/playlists', defaults={'sub_page': 'plm_main'}, methods=['GET', 'POST'])
@app.route('/playlists/<sub_page>', methods=['GET', 'POST'])
def webpage_playlists(sub_page):

    templates = {
        'plm_main': 'main/playlists.html',
        'plm_modify_assigned_stations': 'main/playlists_modify_assigned_stations.html',
        'plm_parent_stations': 'main/playlists_parent_stations.html',
        'plm_manage': 'main/playlists_manage.html'
    }

    template = templates.get(sub_page, 'main/playlists.html')

    playlists_anchor_id = None
    run_empty_row = None

    playlists = read_data(csv_playlistmanager_playlists)
    parents = read_data(csv_playlistmanager_parents)
    child_to_parents = read_data(csv_playlistmanager_child_to_parent)

    action_to_anchor = {
        'playlists': 'playlists_anchor',
        'priority_playlists': 'priority_playlists_anchor',
        'parents': 'parents_anchor',
        'unassigned_child_to_parents': 'unassigned_child_to_parents_anchor',
        'assigned_child_to_parents': 'assigned_child_to_parents_anchor',
        'final_playlists': 'final_playlists_anchor',
        'playlist_file_add_to': 'final_playlists_anchor',
        'uploaded_playlists': 'uploaded_playlists_anchor',
        'generated_playlists': 'uploaded_playlists_anchor'
    }

    preferred_playlists = []
    preferred_playlists_default = [
        {'m3u_id': 'None', 'prefer_name': 'None'},
        {'m3u_id': 'Delete', 'prefer_name': 'Delete'}
    ]
    preferred_playlists = get_preferred_playlists(preferred_playlists_default)

    child_to_parent_mappings = []
    child_to_parent_mappings_default = [
        { 'parent_channel_id': 'Unassigned', 'parent_title': 'Unassigned' },
        { 'parent_channel_id': 'Ignore', 'parent_title': 'Ignore' },
        { 'parent_channel_id': 'Make Parent', 'parent_title': 'Make Parent' }
    ]
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
    
    if request.method == 'POST':
        playlists_action = request.form['action']

        for prefix, anchor_id in action_to_anchor.items():
            if playlists_action.startswith(prefix):
                playlists_anchor_id = anchor_id
                break

        posts = ['_cancel', '_save', 'save_all', '_new']
        inposts = ['_delete_', '_update_','_make_parent_', '_set_parent_', '_add_to_']
        if any(playlists_action.endswith(post) for post in posts) or any(inpost in playlists_action for inpost in inposts):

            this_posts = ['_save', '_new']
            this_inposts = ['_delete_', '_upload_', '_make_parent_']
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

                        for row in playlists_m3u_id_inputs:
                            playlists_m3u_id_input =  playlists_m3u_id_inputs.get(row)
                            playlists_m3u_name_input = playlists_m3u_name_inputs.get(row)
                            playlists_m3u_url_input = playlists_m3u_url_inputs.get(row)
                            playlists_epg_xml_input = playlists_epg_xml_inputs.get(row)
                            playlists_stream_format_input = playlists_stream_format_inputs.get(row)
                            playlists_m3u_active_input = "On" if playlists_m3u_active_inputs.get(row) == 'On' else "Off"
                            playlists_m3u_priority_input = playlists_m3u_priority_inputs.get(row)

                            for idx, playlist in enumerate(playlists):
                                if idx == int(row) - 1:
                                    playlist['m3u_id'] = playlists_m3u_id_input
                                    playlist['m3u_name'] = playlists_m3u_name_input
                                    playlist['m3u_url'] = playlists_m3u_url_input
                                    playlist['epg_xml'] = playlists_epg_xml_input
                                    playlist['stream_format'] = playlists_stream_format_input
                                    playlist['m3u_active'] = playlists_m3u_active_input
                                    playlist['m3u_priority'] = playlists_m3u_priority_input

                    elif playlists_action == "playlists_action_new":
                        playlists_m3u_id_input = f"m3u_{max((int(playlist['m3u_id'].split('_')[1]) for playlist in playlists), default=0) + 1:04d}"
                        playlists_m3u_name_input = request.form.get('playlists_m3u_name_new')
                        playlists_m3u_url_input = request.form.get('playlists_m3u_url_new')
                        playlists_epg_xml_input = request.form.get('playlists_epg_xml_new')
                        playlists_stream_format_input = request.form.get('playlists_stream_format_new')
                        playlists_m3u_active_input = "On" if request.form.get('playlists_m3u_active_new') == 'On' else "Off"
                        playlists_m3u_priority_input = max((int(playlist['m3u_priority']) for playlist in playlists), default=0) + 1

                        playlists.append({
                            "m3u_id": playlists_m3u_id_input,
                            "m3u_name": playlists_m3u_name_input,
                            "m3u_url": playlists_m3u_url_input,
                            "epg_xml": playlists_epg_xml_input,
                            "stream_format": playlists_stream_format_input,
                            "m3u_active": playlists_m3u_active_input,
                            "m3u_priority": playlists_m3u_priority_input
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
                        uploaded_playlists_action_delete_filename = uploaded_playlist_files[uploaded_playlists_action_delete_index]
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

                    if playlists_action == "parents_action_save" or playlists_action.startswith('parents_action_delete_'):

                        parents_delete_on_save_flag = None

                        parents_parent_channel_id_inputs = {}
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

                        if playlists_action == "parents_action_save":
                            temp_parents = []

                            for row in parents_parent_channel_id_inputs:
                                parents_parent_channel_id_input =  parents_parent_channel_id_inputs.get(row)
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
                                    'parent_title': parents_parent_title_input,
                                    'parent_tvg_id_override': parents_parent_tvg_id_override_input,
                                    'parent_tvg_logo_override': parents_parent_tvg_logo_override_input,
                                    'parent_channel_number_override': parents_parent_channel_number_override_input,
                                    'parent_tvc_guide_stationid_override': parents_parent_tvc_guide_stationid_override_input,
                                    'parent_preferred_playlist': parents_parent_preferred_playlist_input
                                })

                            for parent in parents:
                                for temp_parent in temp_parents:
                                    if parent['parent_channel_id'] == temp_parent['parent_channel_id']:
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
                                        unassign_children.append(child_to_parent['child_m3u_id_channel_id'])

                                if unassign_children:
                                    for unassign_child in unassign_children:
                                        set_child_to_parent(unassign_child, "Unassigned")

                            unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count = get_child_to_parents(sub_page)

                    elif playlists_action == "parents_action_new" or '_make_parent_' in playlists_action:
                        
                        parents_parent_channel_id_input = f"plm_{max((int(parent['parent_channel_id'].split('_')[1]) for parent in parents), default=0) + 1:04d}"

                        # Placeholder values for potential future functionality expansion
                        parents_parent_tvc_guide_art_override_input = None
                        parents_parent_tvc_guide_tags_override_input = None
                        parents_parent_tvc_guide_genres_override_input = None
                        parents_parent_tvc_guide_categories_override_input = None
                        parents_parent_tvc_guide_placeholders_override_input = None
                        parents_parent_tvc_stream_vcodec_override_input = None
                        parents_parent_tvc_stream_acodec_override_input = None

                        if playlists_action == "parents_action_new":
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

                            parents_parent_title_input = child_to_parents_title_inputs[child_to_parents_action_make_parent_index]
                            parents_parent_tvg_id_override_input = None
                            parents_parent_tvg_logo_override_input = None
                            parents_parent_channel_number_override_input = None
                            parents_parent_tvc_guide_stationid_override_input = None
                            parents_parent_preferred_playlist_input = None

                            # Modify Child to Parent table
                            child_to_parents_channel_id_inputs = {}

                            keycheck_base = "_child_to_parents_channel_id_"
                            keycheck = f"{keycheck_prefix}{keycheck_base}"
                            for key in request.form.keys():
                                if key.startswith(keycheck):
                                    index = key.split('_')[-1]
                                    child_to_parents_channel_id_inputs[index] = request.form.get(key)

                            child_to_parents_channel_id_inputs = list(child_to_parents_channel_id_inputs.values())

                            child_to_parents_channel_id = child_to_parents_channel_id_inputs[child_to_parents_action_make_parent_index]

                            set_child_to_parent(child_to_parents_channel_id, parents_parent_channel_id_input)
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
                            "parent_preferred_playlist": parents_parent_preferred_playlist_input
                        })

                    if len(parents) > 1:
                        parents = sorted(parents, key=lambda x: sort_key(x["parent_title"].casefold()))

                    csv_to_write = csv_playlistmanager_parents
                    data_to_write = parents

                if csv_to_write:

                    write_data(csv_to_write, data_to_write)

                    if run_empty_row:
                        remove_empty_row(csv_to_write)

                        if csv_to_write == csv_playlistmanager_playlists:
                            delete_all_rows_except_header(csv_playlistmanager_child_to_parent)
                            delete_all_rows_except_header(csv_playlistmanager_combined_m3us)

                    if csv_to_write == csv_playlistmanager_playlists:
                        playlists = read_data(csv_playlistmanager_playlists)
                    elif csv_to_write == csv_playlistmanager_parents:
                        parents = read_data(csv_playlistmanager_parents)
                        child_to_parent_mappings = get_child_to_parent_mappings(child_to_parent_mappings_default)

            elif playlists_action.endswith('_save_all') or '_set_parent_' in playlists_action:

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

                    for index in child_to_parents_channel_id_inputs.keys():
                        child_to_parents_channel_id_input = child_to_parents_channel_id_inputs.get(index)
                        
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
                                "parent_preferred_playlist": None
                            })

                            child_to_parents_parent_channel_id_input = save_all_parent_channel_id

                        else:
                            child_to_parents_parent_channel_id_input = child_to_parents_parent_channel_id_inputs.get(index)

                        send_child_to_parents.append({'child_m3u_id_channel_id': child_to_parents_channel_id_input, 'parent_channel_id': child_to_parents_parent_channel_id_input})

                    if '_set_parent_' in playlists_action:

                        if playlists_action.endswith('_set_parent_all'):
                            pass

                        else:
                            send_child_to_parents_single = []
                            child_to_parents_action_set_parent_index = int(playlists_action.split('_')[-1]) - 1

                            child_to_parents_channel_id_input_single = send_child_to_parents[child_to_parents_action_set_parent_index]['child_m3u_id_channel_id']
                            child_to_parents_parent_channel_id_input_single = send_child_to_parents[child_to_parents_action_set_parent_index]['parent_channel_id']

                            send_child_to_parents_single.append({'child_m3u_id_channel_id': child_to_parents_channel_id_input_single, 'parent_channel_id': child_to_parents_parent_channel_id_input_single})

                            send_child_to_parents = send_child_to_parents_single

                    # Write back
                    for send_child_to_parent in send_child_to_parents:
                        child_to_parents_channel_id = send_child_to_parent['child_m3u_id_channel_id']
                        child_to_parents_parent_channel_id = send_child_to_parent['parent_channel_id']
                        set_child_to_parent(child_to_parents_channel_id, child_to_parents_parent_channel_id)
                    
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

                    make_playlist_name = f"PLM - {make_playlist_name_base} ({make_playlist_type}) [{make_playlist_number}]"

                    if 'epg_' in make_playlist_url:
                        make_playlist_xmltv_url = make_playlist_url.replace('.m3u', '.xml')

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

                    put_channels_dvr_json(make_playlist_route, json_data)

    response = make_response(render_template(
        template,
        segment = sub_page,
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_playlists_anchor_id = playlists_anchor_id,
        html_playlists = playlists,
        html_preferred_playlists = preferred_playlists,
        html_parents = parents,
        html_stream_formats = stream_formats,
        html_child_to_parent_mappings = child_to_parent_mappings,
        html_unassigned_child_to_parents = unassigned_child_to_parents,
        html_assigned_child_to_parents = assigned_child_to_parents,
        html_all_child_to_parents_stats = all_child_to_parents_stats,
        html_playlists_station_count = playlists_station_count,
        html_playlist_files = playlist_files,
        html_uploaded_playlist_files = uploaded_playlist_files,
        html_current_path = current_path,
        html_uploaded_playlists_message = uploaded_playlists_message
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

# Used to download an m3u or XML EPG
@app.route('/playlists/uploads/<filename>')
def download_uploads(filename):
    filename = os.path.join(playlists_uploads_dir_name, filename)
    return export_csv(filename)

# Goes through each of the playlists and combines all m3us together into a single list
def get_combined_m3us():
    playlists = read_data(csv_playlistmanager_playlists)
    combined_m3us = []

    print(f"\n{current_time()} Starting combination of playlists...")

    for playlist in playlists:
        response = None
        response = fetch_url(playlist['m3u_url'], 5, 10)
        if response:
            combined_m3us.extend(parse_m3u(playlist['m3u_id'], playlist['m3u_name'], response))

    id_field = "station_playlist"
    update_rows(csv_playlistmanager_combined_m3us, combined_m3us, id_field, True)

    stations = read_data(csv_playlistmanager_combined_m3us)
    maps = read_data(csv_playlistmanager_child_to_parent)

    for station in stations:
        check_m3u_id_channel_id = f"{station['m3u_id']}_{station['channel_id']}"
        if check_m3u_id_channel_id not in [map['child_m3u_id_channel_id'] for map in maps]:
            new_row = { 'child_m3u_id_channel_id': check_m3u_id_channel_id, 'parent_channel_id': 'Unassigned' }
            append_data(csv_playlistmanager_child_to_parent, new_row)

    print(f"\n{current_time()} Finished combination of playlists.")

# Parse the m3u Playlist to get all the details
def parse_m3u(m3u_id, m3u_name, response):
    print(f"\n{current_time()} INFO: Beginning parse of {m3u_name} ({m3u_id}).")

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
        elif line.startswith('http') or '://' in line:
            if current_record:
                current_record['url'] = line.strip()
                records.append(current_record)
                current_record = None

    if current_record:
        records.append(current_record)

    print(f"\n{current_time()} INFO: Initial parse of {m3u_name} ({m3u_id}) complete. Beginning check for unique 'channel-id' values.")

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

    print(f"\n{current_time()} INFO: Finished parse of {m3u_name} ({m3u_id}).")

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

    if sub_page is None or sub_page in ['plm_main', 'plm_modify_assigned_stations']:
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

                    if all_child_to_parents_append:
                        all_child_to_parents.append({
                            'channel_id': child_to_parent_channel_id,
                            'title': child_to_parent_title,
                            'm3u_name': child_to_parent_m3u_name,
                            'description': child_to_parent_description,
                            'parent_channel_id': child_to_parent_parent_channel_id
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
                    'parent_channel_id': sorted_all_child_to_parent['parent_channel_id']
                })
            else:
                assigned_child_to_parents.append({
                    'channel_id': sorted_all_child_to_parent['channel_id'],
                    'title': sorted_all_child_to_parent['title'],
                    'm3u_name': sorted_all_child_to_parent['m3u_name'],
                    'description': sorted_all_child_to_parent['description'],
                    'parent_channel_id': sorted_all_child_to_parent['parent_channel_id']
                })

    # Create statistics
    if sub_page is None or sub_page == 'plm_main':
        total_records = len(all_child_to_parents)

        unassigned_count = sum(1 for record in all_child_to_parents if record['parent_channel_id'] == "Unassigned")
        ignore_count = sum(1 for record in all_child_to_parents if record['parent_channel_id'] == "Ignore")

        assigned_to_parent_ids = {record['parent_channel_id'] for record in all_child_to_parents if record['parent_channel_id'] not in ["Unassigned", "Ignore"]}
        assigned_to_parent_count = len(assigned_to_parent_ids)

        redundant_count = total_records - (unassigned_count + ignore_count + assigned_to_parent_count)
        
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
        }

    return unassigned_child_to_parents, assigned_child_to_parents, all_child_to_parents_stats, playlists_station_count

# Sets a child to a parent for a station
def set_child_to_parent(child_m3u_id_channel_id, parent_channel_id):
    child_to_parents = read_data(csv_playlistmanager_child_to_parent)

    for child_to_parent in child_to_parents:
        if child_to_parent['child_m3u_id_channel_id'] == child_m3u_id_channel_id:
            child_to_parent['parent_channel_id'] = parent_channel_id
            break

    write_data(csv_playlistmanager_child_to_parent, child_to_parents)

# Creates the m3u(s) and XML EPG(s)
def get_final_m3us_epgs():
    notification_add(f"\n{current_time()} Starting generation of final m3u(s) and XML EPG(s)...\n")

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
            if map['parent_channel_id'] == channel_id:
                children.append(map['child_m3u_id_channel_id'])

        children = [child for child in children if re.search(r'm3u_\d{4}', child).group(0) in playlist_preferences]

        children = sorted(
            children,
            key=lambda child: (
                playlist_preferences.index(re.match(r'm3u_\d{4}', child).group(0)),
                re.sub(r'^m3u_\d{4}_', '', child)
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
    create_chunk_files(epg_strmlnk_final_m3us, "plm_strmlnk_m3u", "m3u", max_stations)
    get_epgs_for_m3us()

    notification_add(f"\n{current_time()} Finished generation of final m3u(s) and XML EPG(s).")

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
            if child == check_m3u_id_channel_id:
                if combined_child[field] is None or combined_child[field] == '':
                    pass
                else:
                    if field_original == "stream_format":
                        playlists = read_data(csv_playlistmanager_playlists)
                        for playlist in playlists:
                            if playlist['m3u_id'] == combined_child['m3u_id']:
                                field_value = playlist['stream_format']
                                break
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

# Wrapper for getting uploaded m3u and XML EPG files
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

            if 'hls' in playlist_filename:
                playlist_filetype = "Generated Streaming Stations Playlist (HLS)"

            elif 'mpeg_ts' in playlist_filename:
                playlist_filetype = "Generated Streaming Stations Playlist (MPEG-TS)"

            elif 'strmlnk' in playlist_filename:
                playlist_filetype = "Generated Stream Link Stations Playlist (STRMLNK)"

        else:
            playlist_filetype = "Uploaded Playlist"

        playlist_files.append({
            'file_type': playlist_filetype,
            'file_link': playlist_filename
            })
    
    playlist_files = sorted(playlist_files, key=lambda x: ['file_link'])
    return playlist_files

# Gets the XML EPG for each m3u that needs one
def get_epgs_for_m3us():
    playlists = read_data(csv_playlistmanager_playlists)
    temp_file_path = full_path("temp.txt")
    
    with open(temp_file_path, "a", encoding="utf-8") as temp_file:
        for playlist in playlists:
            if playlist['m3u_active'] == "On":
                if playlist['epg_xml'] is not None and playlist['epg_xml'] != '':
                    response = None
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
                        
                        temp_file.write(response_text + "\n")

    extensions = ['m3u']
    m3u_files = get_all_prior_files(program_files_dir, extensions)

    # Filter the list to include only values that contain '_epg_'
    filtered_files = [filtered_file for filtered_file in m3u_files if '_epg_' in filtered_file['filename']]

    for filtered_file in filtered_files:
        tvg_ids = []  # Reset the list for each playlist
        playlist_extension = filtered_file['extension']
        playlist_filename = f"{filtered_file['filename']}.{playlist_extension}"
        epg_filename = f"{filtered_file['filename']}.xml"
        epg_filename_tmp = f"{epg_filename}.tmp"

        # Read the M3U file content
        with open(full_path(playlist_filename), "r", encoding="utf-8") as file:
            content = file.read()
            # Extract tvg-id values
            ids = re.findall(r'tvg-id="(.*?)"', content)
            tvg_ids.extend(ids)

        # Ensure temp.txt exists before attempting to read it
        if os.path.exists(temp_file_path):
            # Write the EPG data to epg_filename
            with open(full_path(epg_filename_tmp), "w", encoding="utf-8") as epg_file:
                # Write the initial lines
                epg_file.write("<?xml version='1.0' encoding='utf-8'?>\n")
                epg_file.write("<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\n")
                epg_file.write("<tv generator-info-name=\"SLM\" generated-ts=\"\">\n")
                
                # Read temp.txt and extract relevant sections
                with open(temp_file_path, "r", encoding="utf-8") as temp_file:
                    temp_content = temp_file.read()
                    
                    # Extract <channel> sections
                    for tvg_id in tvg_ids:
                        channel_pattern = re.compile(rf'<channel\b[^>]*\bid="{tvg_id}"[^>]*>.*?</channel>', re.DOTALL)
                        channels = channel_pattern.findall(temp_content)
                        for channel in channels:
                            epg_file.write("  " + channel + "\n")  # 2 spaces for indentation
                        
                        # Extract <programme> sections
                        programme_pattern = re.compile(rf'<programme\b[^>]*\bchannel="{tvg_id}"[^>]*>.*?</programme>', re.DOTALL)
                        programmes = programme_pattern.findall(temp_content)
                        for programme in programmes:
                            epg_file.write("  " + programme + "\n")  # 2 spaces for indentation
                
                # Write the closing tag
                epg_file.write("</tv>\n")

    # Delete temp.txt after processing
    reliable_remove(temp_file_path)

    extensions = ['xml']
    all_prior_files = []
    all_prior_files = get_all_prior_files(program_files_dir, extensions)
    for all_prior_file in all_prior_files:
        file_delete(program_files_dir, all_prior_file['filename'], all_prior_file['extension'])

    rename_files_suffix(program_files_dir, ".xml.tmp", ".xml")

# Add streaming stations from particular sources
@app.route('/playlists/streams', methods=['GET', 'POST'])
def webpage_playlists_streams():
    global streaming_stations_source_test_prior
    global streaming_stations_url_test_prior

    streaming_stations = read_data(csv_playlistmanager_streaming_stations)

    streaming_station_options = [
        "Custom (HLS)",
        "Custom (MPEG-TS)",
        "Stream Link (STRMLNK)",
        "YouTube Live (HLS)"
    ]

    test_url = ''
    run_empty_row = None

    if request.method == 'POST':
        action = request.form['action']

        if action.endswith('test'):
            streaming_stations_source_test_input = request.form.get('streaming_stations_source_test')
            streaming_stations_url_test_input = request.form.get('streaming_stations_url_test')

            streaming_stations_source_test_prior = streaming_stations_source_test_input
            streaming_stations_url_test_prior = streaming_stations_url_test_input

            if streaming_stations_url_test_input is not None and streaming_stations_url_test_input != '':
                if streaming_stations_source_test_input.startswith('Custom'):
                    test_url = streaming_stations_url_test_input

                elif streaming_stations_source_test_input.startswith('YouTube Live'):
                    test_url = f"{request.url_root}playlists/streams/youtubelive?url={streaming_stations_url_test_input}"

        elif action.endswith('new') or action.endswith('save') or 'delete' in action:

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

        streaming_stations = read_data(csv_playlistmanager_streaming_stations)

    return render_template(
        'main/playlists_streams.html',
        segment = 'plm_streams',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_streaming_stations = streaming_stations,
        html_streaming_station_options = streaming_station_options,
        html_streaming_stations_source_test_prior = streaming_stations_source_test_prior,
        html_streaming_stations_url_test_prior = streaming_stations_url_test_prior,
        html_test_url = test_url
    )

# Creates an m3u8 for an individual YouTube Live stream
@app.route('/playlists/streams/youtubelive', methods=['GET'])
def streams_youtubelive():
    youtubelive_url = request.args.get('url', type=str)
    if not youtubelive_url:
        return "YouTube Live URL is required"
    
    m3u8_url = get_youtubelive_m3u8_manifest(youtubelive_url)
    
    if m3u8_url:
        # Extract the identifier from the URL
        video_id_match = re.search(r'v=([a-zA-Z0-9_-]+)', youtubelive_url)
        short_video_id_match = re.search(r'.be/([a-zA-Z0-9_-]+)', youtubelive_url)
        channel_name_match = re.search(r'@([^/]+)/live', youtubelive_url)
        
        if video_id_match:
            filename = f"{video_id_match.group(1)}.m3u8"
        elif short_video_id_match:
            filename = f"{short_video_id_match.group(1)}.m3u8"
        elif channel_name_match:
            filename = f"{channel_name_match.group(1)}.m3u8"
        else:
            filename = "youtubelive.m3u8"  # Fallback in case no match is found
        
        playlist = f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{m3u8_url}\n"
        
        # Return the Response with the filename
        response = Response(playlist, content_type='application/vnd.apple.mpegurl')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        return "Failed to retrieve m3u8 manifest URL"

# Gets the manifest needed for the YouTube Live stream
def get_youtubelive_m3u8_manifest(youtubelive_url):
    print(f"{current_time()} INFO: Starting to retrieve manifest for {youtubelive_url}.")
    ydl_opts = {
        'verbose': True,                                    # Get verbose output
        'no_warnings': False,                               # Show warnings
        'format': 'all',
        'retries': 10,                                      # Retry up to 10 times in case of failure
        'fragment_retries': 10,                             # Retry up to 10 times for each fragment
        'logger': YTDLLogger(),                             # Pass the custom logger
        'extractor_args': {                                 # Set extractor args correctly
            'youtube': {
                'player_client': ['web']                    # Force player API client to web
            }
        }
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"{current_time()} INFO: Extracting info from {youtubelive_url}...")
            info_dict = ydl.extract_info(youtubelive_url, download=False)
            if info_dict:
                print(f"{current_time()} INFO: Extraction successful for {youtubelive_url}.")
                formats = info_dict.get('formats', None)
                if formats:
                    print(f"{current_time()} INFO: Found {len(formats)} formats.")
                    best_format = None
                    for f in formats:
                        if 'm3u8' in f.get('protocol', '') and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                            if not best_format or f.get('tbr', 0) > best_format.get('tbr', 0):
                                best_format = f
                    if best_format:
                        print(f"{current_time()} INFO: Best format URL: {best_format.get('url')}")
                        return best_format.get('url')
                    else:
                        print(f"{current_time()} WARNING: No suitable m3u8 format found.")
                else:
                    print(f"{current_time()} WARNING: No formats found in info dictionary.")
            else:
                print(f"{current_time()} ERROR: Failed to extract info for {youtubelive_url}. Info dictionary is empty.")
        except Exception as e:
            print(f"{current_time()} ERROR: While attempting to retrieve {youtubelive_url}, received {e}.")
    print(f"{current_time()} ERROR: Manifest retrieval failed for {youtubelive_url}.")
    return None

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
        if 'YouTube Live' in streaming_station['source']:
            url = f"{request.url_root}playlists/streams/youtubelive?url={streaming_station['url']}"
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
    global slm_query_name
    slm_query_raw = []

    if request.method == 'POST':
        action = request.form['action']

        if action == "reports_queries_cancel":
            slm_query_raw = []
            slm_query = None
            slm_query_name = None

        else:
            slm_query_raw = run_query(action)

            if action in [
                            "query_currently_unavailable",
                            "query_previously_watched",
                            "query_not_on_justwatch"
                         ]:
                slm_query_raw = sorted(slm_query_raw, key=lambda x: (x["Type"], sort_key(x["Name"].casefold())))

                if action == "query_currently_unavailable":
                    slm_query_name = "Currently Unavailable"
                elif action == "query_previously_watched":
                    slm_query_name = "Previously Watched"
                elif action == "query_not_on_justwatch":
                    slm_query_name = "Not on JustWatch (Must run 'Stream Links: New & Recent Releases' first)"

            elif action in [
                                "query_plm_children",
                                "query_mtm_stations_by_channel_collection"
                           ]:
                
                if action == "query_plm_children":
                    slm_query_name = "Stations: Parents and Children"

                elif action == "query_mtm_stations_by_channel_collection":
                    slm_query_name = "Stations by Channel Collection"

            slm_query = view_csv(slm_query_raw, "library", None)

    return render_template(
        'main/reports_queries.html',
        segment='reports_queries',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_slm_query = slm_query,
        html_slm_query_name = slm_query_name
    )

# Run a SQL-like Query
def run_query(query_name):
    run_query = None
    results = []

    bookmarks_data = read_data(csv_bookmarks)
    bookmarks_status_data = read_data(csv_bookmarks_status)
    settings_data = read_data(csv_settings)
    slmappings_data = read_data(csv_slmappings)
    streaming_services_data = read_data(csv_streaming_services)
    plm_child_to_parent_maps_data = read_data(csv_playlistmanager_child_to_parent)
    plm_all_stations_data = read_data(csv_playlistmanager_combined_m3us)
    plm_parents_data = read_data(csv_playlistmanager_parents)
    plm_playlists_data = read_data(csv_playlistmanager_playlists)

    # Convert the data into pandas DataFrames
    bookmarks = pd.DataFrame(bookmarks_data)
    bookmarks_status = pd.DataFrame(bookmarks_status_data)
    settings = pd.DataFrame(settings_data)
    slmappings = pd.DataFrame(slmappings_data)
    streaming_services = pd.DataFrame(streaming_services_data)
    plm_child_to_parent_maps = pd.DataFrame(plm_child_to_parent_maps_data)
    plm_all_stations = pd.DataFrame(plm_all_stations_data)
    plm_parents = pd.DataFrame(plm_parents_data)
    plm_playlists = pd.DataFrame(plm_playlists_data)

    if query_name in [
                        'query_currently_unavailable',
                        'query_previously_watched',
                        'query_not_on_justwatch'
                     ]:

        if bookmarks.empty or bookmarks_status.empty:
            pass

        else:

            run_query = True

            if query_name == 'query_currently_unavailable':
                # Add a new column for the season using string slicing
                bookmarks_status['Season'] = bookmarks_status['season_episode'].str[:3]

                query = """
                SELECT 
                    bookmarks.object_type AS "Type", 
                    bookmarks.title || " (" || bookmarks.release_year || ")" AS "Name", 
                    bookmarks_status.Season, 
                    CASE 
                        WHEN bookmarks.object_type = 'SHOW' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                        ELSE ''
                    END AS "# Episodes"
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
                # Add a new column for the season using string slicing
                bookmarks_status['Season'] = bookmarks_status['season_episode'].str[:3]

                query = """
                SELECT 
                    bookmarks.object_type AS "Type", 
                    bookmarks.title || " (" || bookmarks.release_year || ")" AS "Name", 
                    bookmarks_status.Season, 
                    CASE 
                        WHEN bookmarks.object_type = 'SHOW' THEN CAST(COUNT(bookmarks_status.season_episode) AS INTEGER)
                        ELSE ''
                    END AS "# Episodes"
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
                SELECT
                    CASE
                        WHEN plm_child_to_parent_maps.parent_channel_id IN ('Ignore', 'Unassigned') THEN plm_child_to_parent_maps.parent_channel_id
                        ELSE plm_parents.parent_title
                    END AS "Parent Station",
                    plm_all_stations.station_playlist AS "Child Station",
                    COALESCE(plm_parents.parent_tvc_guide_stationid_override, '') AS "Gracenote ID (Override)",
                    COALESCE(plm_all_stations.tvc_guide_stationid, '') AS "Gracenote ID (Imported)"
                FROM plm_child_to_parent_maps
                LEFT JOIN plm_parents ON plm_child_to_parent_maps.parent_channel_id = plm_parents.parent_channel_id
                LEFT JOIN plm_all_stations ON plm_child_to_parent_maps.child_m3u_id_channel_id = plm_all_stations.m3u_id || '_' || plm_all_stations.channel_id
                LEFT JOIN plm_playlists ON plm_all_stations.m3u_id = plm_playlists.m3u_id
                WHERE plm_all_stations.station_playlist IS NOT NULL
                ORDER BY
                    CASE
                        WHEN plm_child_to_parent_maps.parent_channel_id IN ('Ignore', 'Unassigned') THEN 2
                        ELSE 1
                    END,
                    "Parent Station",
                    CASE
                        WHEN plm_parents.parent_preferred_playlist IS NOT NULL AND plm_parents.parent_preferred_playlist != '' THEN 
                            CASE 
                                WHEN plm_all_stations.m3u_id = plm_parents.parent_preferred_playlist THEN 0
                                ELSE CAST(plm_playlists.m3u_priority AS INTEGER)
                            END
                        ELSE CAST(plm_playlists.m3u_priority AS INTEGER)
                    END,
                    "Child Station"
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

    # Execute the query
    if run_query:
        results = psql.sqldf(query, locals()).to_dict(orient='records')

        if query_name == 'query_mtm_stations_by_channel_collection':
            results = sorted(results, key=lambda x: (sort_key(x["Station Name"].casefold()), sort_key(x["Channel Collection Name"].casefold())))

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
                    gracenote_search_message = f"\n{current_time()} ERROR: During search, received {e}. Please try again."

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
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
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
    csv_explorer_results_base = None

    if request.method == 'POST':
        action = request.form['action']

        if action == 'csv_explorer_search':
            csv_explorer_entry_input = request.form.get('csv_explorer_entry')
            csv_explorer_entry_prior = csv_explorer_entry_input
            csv_explorer_results = None
            csv_explorer_results_base = None
            csv_explorer_results_text = None

            if csv_explorer_entry_input is None or csv_explorer_entry_input == '':
                tools_csvexplorer_message = f"{current_time()} WARNING: Link is empty. Please enter a valid value."
            
            else:
                csv_explorer_results_base = fetch_url(csv_explorer_entry_input, 3, 5)

                if csv_explorer_results_base:
                    csv_explorer_results_text = csv_explorer_results_base.content.decode('utf-8')
                    
                    if is_valid_csv(csv_explorer_results_text):
                        csv_explorer_results_library = [row for row in csv.DictReader(io.StringIO(csv_explorer_results_text))]
                        csv_explorer_results = view_csv(csv_explorer_results_library, "library", True)
                    
                    else:
                        tools_csvexplorer_message = f"{current_time()} WARNING: Link does not contain a valid CSV. Please try again."
                
                else:
                    tools_csvexplorer_message = f"{current_time()} WARNING: Unable to connect to link. Please try again."

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
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_channels_api_url = channels_api_url,
        html_tools_csvexplorer_message = tools_csvexplorer_message,
        html_csv_explorer_results = csv_explorer_results,
        html_csv_explorer_entry_prior = csv_explorer_entry_prior
    )

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
    plm_update_stations_schedule_frequency = settings[44]["settings"]    # [44] PLM: Update Stations Process Schedule Frequency
    plm_update_m3us_epgs_schedule = settings[15]["settings"]
    plm_update_m3us_epgs_schedule_time = settings[16]["settings"]
    plm_update_m3us_epgs_schedule_frequency = settings[17]["settings"]
    reset_channels_passes = settings[29]["settings"]                     # [29] MTM: Automation - Reset Channels DVR Passes On/Off
    reset_channels_passes_time = settings[30]["settings"]                # [30] MTM: Automation - Reset Channels DVR Passes Start Time
    reset_channels_passes_frequency = settings[31]["settings"]           # [31] MTM: Automation - Reset Channels DVR Passes Frequency
    slm_new_recent_releases = settings[32]["settings"]                   # [32] MTM: Automation - SLM New & Recent Releases On/Off
    slm_new_recent_releases_time = settings[33]["settings"]              # [33] MTM: Automation - SLM New & Recent Releases Start Time
    slm_new_recent_releases_frequency = settings[34]["settings"]         # [34] MTM: Automation - SLM New & Recent Releases Frequency
    slm_new_recent_releases_when = settings[35]["settings"]              # [35] MTM: Automation - SLM New & Recent Releases Hours Past to Consider
    refresh_channels_m3u_playlists = settings[36]["settings"]            # [36] MTM: Automation - Refresh Channels M3U Playlists On/Off
    refresh_channels_m3u_playlists_time = settings[37]["settings"]       # [37] MTM: Automation - Refresh Channels M3U Playlists Start Time
    refresh_channels_m3u_playlists_frequency = settings[38]["settings"]  # [38] MTM: Automation - Refresh Channels M3U Playlists Frequency

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
            anchor_base = 'end_to_end_subprocesses' if trimmed_action in other_actions else trimmed_action
            anchor = 'anchor_' + anchor_base

        if action.endswith('_run'):

            if action.startswith('reset_channels_passes'):
                automation_message = run_reset_channels_passes()

            elif action.startswith('refresh_channels_m3u_playlists'):
                automation_message = run_refresh_channels_m3u_playlists()

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
                    action_friendly_name = 'Import Updates from Channels'
                    import_program_updates()

                elif action.startswith('generate_stream_links'):
                    action_friendly_name = 'Generate Stream Links/Files'
                    generate_stream_links(None)

                elif action.startswith('prune_scan_channels'):
                    action_friendly_name = 'Run Updates in Channels'
                    prune_scan_channels()

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
                    refresh_channels_m3u_playlists_time_input = request.form.get('refresh_channels_m3u_playlists_time')
                    refresh_channels_m3u_playlists_frequency_input = request.form.get('refresh_channels_m3u_playlists_frequency')

                    settings[36]["settings"] = "On" if refresh_channels_m3u_playlists_input == 'on' else "Off"
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
            plm_update_stations_schedule_frequency = settings[44]["settings"]    # [44] PLM: Update Stations Process Schedule Frequency
            plm_update_m3us_epgs_schedule = settings[15]["settings"]
            plm_update_m3us_epgs_schedule_time = settings[16]["settings"]
            plm_update_m3us_epgs_schedule_frequency = settings[17]["settings"]
            reset_channels_passes = settings[29]["settings"]                     # [29] MTM: Automation - Reset Channels DVR Passes On/Off
            reset_channels_passes_time = settings[30]["settings"]                # [30] MTM: Automation - Reset Channels DVR Passes Start Time
            reset_channels_passes_frequency = settings[31]["settings"]           # [31] MTM: Automation - Reset Channels DVR Passes Frequency
            slm_new_recent_releases = settings[32]["settings"]                   # [32] MTM: Automation - SLM New & Recent Releases On/Off
            slm_new_recent_releases_time = settings[33]["settings"]              # [33] MTM: Automation - SLM New & Recent Releases Start Time
            slm_new_recent_releases_frequency = settings[34]["settings"]         # [34] MTM: Automation - SLM New & Recent Releases Frequency
            slm_new_recent_releases_when = settings[35]["settings"]              # [35] MTM: Automation - SLM New & Recent Releases Hours Past to Consider
            refresh_channels_m3u_playlists = settings[36]["settings"]            # [36] MTM: Automation - Refresh Channels M3U Playlists On/Off
            refresh_channels_m3u_playlists_time = settings[37]["settings"]       # [37] MTM: Automation - Refresh Channels M3U Playlists Start Time
            refresh_channels_m3u_playlists_frequency = settings[38]["settings"]  # [38] MTM: Automation - Refresh Channels M3U Playlists Frequency

    return render_template(
        'main/tools_automation.html',
        segment = 'tools_automation',
        html_slm_version = slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
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
        html_refresh_channels_m3u_playlists_time = refresh_channels_m3u_playlists_time,
        html_refresh_channels_m3u_playlists_frequency = refresh_channels_m3u_playlists_frequency
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
        plm_update_stations_schedule_frequency = settings[44]["settings"]    # [44] PLM: Update Stations Process Schedule Frequency
        plm_update_stations_schedule_frequency_parsed = int(re.search(r'\d+', plm_update_stations_schedule_frequency).group())
        plm_update_m3us_epgs_schedule = settings[15]["settings"]
        plm_update_m3us_epgs_schedule_time = settings[16]["settings"]
        plm_m3us_epgs_schedule_frequency = settings[17]["settings"]
        plm_m3us_epgs_schedule_frequency_parsed = int(re.search(r'\d+', plm_m3us_epgs_schedule_frequency).group())
        reset_channels_passes = settings[29]["settings"]                     # [29] MTM: Automation - Reset Channels DVR Passes On/Off
        reset_channels_passes_time = settings[30]["settings"]                # [30] MTM: Automation - Reset Channels DVR Passes Start Time
        reset_channels_passes_frequency = settings[31]["settings"]           # [31] MTM: Automation - Reset Channels DVR Passes Frequency
        reset_channels_passes_frequency_parsed = int(re.search(r'\d+', reset_channels_passes_frequency).group())
        slm_new_recent_releases = settings[32]["settings"]                   # [32] MTM: Automation - SLM New & Recent Releases On/Off
        slm_new_recent_releases_time = settings[33]["settings"]              # [33] MTM: Automation - SLM New & Recent Releases Start Time
        slm_new_recent_releases_frequency = settings[34]["settings"]         # [34] MTM: Automation - SLM New & Recent Releases Frequency
        slm_new_recent_releases_frequency_parsed = int(re.search(r'\d+', slm_new_recent_releases_frequency).group())
        refresh_channels_m3u_playlists = settings[36]["settings"]            # [36] MTM: Automation - Refresh Channels M3U Playlists On/Off
        refresh_channels_m3u_playlists_time = settings[37]["settings"]       # [37] MTM: Automation - Refresh Channels M3U Playlists Start Time
        refresh_channels_m3u_playlists_frequency = settings[38]["settings"]  # [38] MTM: Automation - Refresh Channels M3U Playlists Frequency
        refresh_channels_m3u_playlists_frequency_parsed = int(re.search(r'\d+', refresh_channels_m3u_playlists_frequency).group())

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

            plm_update_m3us_epgs_schedule_minute_offset = (plm_update_m3us_epgs_schedule_minute + 30) % 60
            plm_update_m3us_epgs_schedule_hour_offset = (plm_update_m3us_epgs_schedule_hour + (plm_update_m3us_epgs_schedule_minute + 30) // 60) % 24

            if current_minute == plm_update_m3us_epgs_schedule_minute_offset and (current_hour - plm_update_m3us_epgs_schedule_hour_offset) % plm_m3us_epgs_schedule_frequency_parsed == 0:
                temp_file_path = full_path("temp.txt")
                reliable_remove(temp_file_path)
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
    backups = sorted(os.listdir(dst_dir))
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

    if current_version == slm_version or current_version == None:
        gen_upgrade_flag = None
    else:
        notification_add(f"\n{current_time()} Upgrade available ({current_version})! Please follow directions at '{github_url}/wiki/Upgrade-‐-Overview'.\n")
        gen_upgrade_flag = True

# SLM: End-to-End Update Process
def end_to_end():
    print("\n==========================================================")
    print("|                                                        |")
    print("|             SLM: End-to-End Update Process             |")
    print("|                                                        |")
    print("==========================================================")

    notification_add(f"\n{current_time()} Beginning SLM end-to-end update process...\n")

    start_time = time.time()

    update_streaming_services()
    time.sleep(2)
    get_new_episodes(None)
    time.sleep(2)
    if slm_channels_dvr_integration:
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

    notification_add(f"\n{current_time()} Total Elapsed Time: {int(hours)} hours | {int(minutes)} minutes | {int(seconds)} seconds")

    notification_add(f"\n{current_time()} SLM End-to-end update process complete\n")

# Check for new episodes
def get_new_episodes(entry_id_filter):
    print("\n==========================================================")
    print("|                                                        |")
    print("|                 Check for New Episodes                 |")
    print("|                                                        |")
    print("==========================================================")

    print(f"\n{current_time()} Scanning for new episodes...\n")
    
    bookmarks = read_data(csv_bookmarks)
    show_bookmarks = [
        bookmark for bookmark in bookmarks 
        if not bookmark['entry_id'].startswith('slm') 
        and bookmark['object_type'] == "SHOW"
        and bookmark['bookmark_action'] not in ["Hide", "Disable Get New Episodes"]
    ]

    if entry_id_filter is not None and entry_id_filter != '':
        show_bookmarks = [
            show_bookmark for show_bookmark in show_bookmarks
            if show_bookmark['entry_id'] == entry_id_filter
        ]

    episodes = read_data(csv_bookmarks_status)

    for show_bookmark in show_bookmarks:
        existing_episodes = [episode for episode in episodes if show_bookmark['entry_id'] == episode['entry_id']]
        season_episodes = get_episode_list(show_bookmark['entry_id'], show_bookmark['url'], show_bookmark['country_code'], show_bookmark['language_code'])

        if season_episodes:
            for season_episode in season_episodes:
                if season_episode['season_episode'] not in [existing_episode['season_episode'] for existing_episode in existing_episodes]:
                    new_row = {"entry_id": show_bookmark['entry_id'], "season_episode_id": season_episode['season_episode_id'], "season_episode_prefix": None, "season_episode": season_episode['season_episode'], "status": "unwatched", "stream_link": None, "stream_link_override": None, "stream_link_file": None, "special_action": "None", "original_release_date": None}
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

# Find if a stream link is available for bookmarked programs, create stream link files if true, remove files if false
def generate_stream_links(original_release_date_list):
    print("\n==========================================================")
    print("|                                                        |")
    print("|                  Generate Stream Links                 |")
    print("|                                                        |")
    print("==========================================================")

    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]
    bookmarks = read_data(csv_bookmarks)
    auto_bookmarks = [
        bookmark for bookmark in bookmarks 
        if not bookmark['entry_id'].startswith('slm') 
        and bookmark['bookmark_action'] not in ["Hide"]
    ]

    run_generation = None

    if slm_channels_dvr_integration and not os.path.exists(channels_directory):
        notification_add(f"\n{current_time()} WARNING: {channels_directory} does not exist, skipping generation. Please change the Channels directory in the Settings menu.\n")
    else:
        run_generation = True
        
    if run_generation:
        print(f"\n{current_time()} START: Generating Stream Links...")

        print(f"\n{current_time()} Getting Stream Links...\n")
        find_stream_links(auto_bookmarks, original_release_date_list)
        print(f"\n{current_time()} Finished getting Stream Links.")

        if slm_channels_dvr_integration:
            if original_release_date_list is None:
                print(f"\n{current_time()} Checking for changes from last run...\n")
                get_stream_link_ids()
                print(f"\n{current_time()} Finished checking for changes from last run.\n")

            print(f"\n{current_time()} Creating and removing Stream Link files and directories...\n")
            create_stream_link_files(bookmarks, True, original_release_date_list)
            print(f"\n{current_time()} Finished creating and removing Stream Link files and directories.")

        print(f"\n{current_time()} END: Finished Generating Stream Links.\n")

# Run Stream Link Generation and File Creation on one program
def generate_stream_links_single(entry_id):
    settings = read_data(csv_settings)
    channels_directory = settings[1]["settings"]

    bookmarks = read_data(csv_bookmarks)
    modify_bookmarks = [bookmark for bookmark in bookmarks if bookmark['entry_id'] == entry_id]

    generate_stream_links_single_message = None
    run_generation = None

    if slm_channels_dvr_integration and not os.path.exists(channels_directory):
        generate_stream_links_single_message = f"{current_time()} WARNING: {channels_directory} does not exist, skipping generation. Please change the Channels directory in the Settings menu."
    else:
        run_generation = True
        
    if run_generation:
        if not entry_id.startswith('slm'):
            find_stream_links(modify_bookmarks, None)

        if slm_channels_dvr_integration:
            create_stream_link_files(modify_bookmarks, None, None)
            generate_stream_links_single_message = f"{current_time()} INFO: Finished generating Stream Links! Please execute process 'Run Updates in Channels' in order to see this program."
        else:
            generate_stream_links_single_message = f"{current_time()} INFO: Finished generating Stream Links! Please use 'Modify Programs' to see values."

    return generate_stream_links_single_message

# Get the valid Stream Links (if available) and write to the appropriate table
def find_stream_links(auto_bookmarks, original_release_date_list):
    bookmarks_statuses = read_data(csv_bookmarks_status)

    for auto_bookmark in auto_bookmarks:

        for bookmarks_status in bookmarks_statuses:

            if auto_bookmark['entry_id'] == bookmarks_status['entry_id']:

                stream_link_dirty = None
                stream_link_reason = None

                if slm_channels_dvr_integration:
                    pass
                else:
                    bookmarks_status['stream_link_file'] = ''
        
                if bookmarks_status['status'].lower() == "unwatched":

                    special_action = bookmarks_status['special_action']

                    if special_action == "Make STRM" and original_release_date_list is None:

                        stream_link_dirty = "https://strm_must_use_override"

                    elif bookmarks_status['stream_link_override'] != "" and original_release_date_list is None:

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
                                
                                if original_release_date_list is None or node_id in original_release_date_list:
                                    stream_link_details = get_offers(node_id, auto_bookmark['country_code'], auto_bookmark['language_code'])
                                    stream_link_offers = extract_offer_info(stream_link_details)
                                    stream_link_dirty = get_stream_link(stream_link_offers, special_action)

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

                if stream_link_dirty:

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
    check_services = [service for service in services if service["streaming_service_subscribe"] == "True"]
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
            "amazon." #,
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
def create_stream_link_files(base_bookmarks, remove_choice, original_release_date_list):
    bookmarks = [
        base_bookmark for base_bookmark in base_bookmarks 
        if base_bookmark['bookmark_action'] not in ["Hide"]
    ]

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
                    if bookmark_status['season_episode_prefix'] != "":
                        stream_link_file_name = f"{bookmark_status['season_episode_prefix']} {bookmark_status['season_episode']}"
                    else:
                        stream_link_file_name = bookmark_status['season_episode']
                    season_number, episode_number = re.match(r"S(\d+)E(\d+)", bookmark_status['season_episode']).groups()
                    season_folder_name = f"Season {season_number}"
                    stream_link_path = os.path.join(tv_path, title_full, season_folder_name)
                if bookmark['object_type'] == "VIDEO":
                    stream_link_path = os.path.join(video_path, title_full)
                    stream_link_file_name = sanitize_name(bookmark_status['season_episode'])

                special_action = bookmark_status['special_action']

                if bookmark_status['stream_link_override'] != "":
                    stream_link_url = bookmark_status['stream_link_override']
                elif bookmark_status['stream_link'] != "":
                    if special_action == "Make STRM":
                        pass
                    else:
                        stream_link_url = bookmark_status['stream_link']

                if bookmark_status['status'].lower() == "unwatched" and stream_link_url:

                    if original_release_date_list is None or bookmark_status['entry_id'] in original_release_date_list or bookmark_status['season_episode_id'] in original_release_date_list:

                        if bookmark['object_type'] == "SHOW" or bookmark['object_type'] == "VIDEO":
                            if bookmark['object_type'] == "SHOW":
                                create_directory(os.path.join(tv_path, title_full))
                            create_directory(stream_link_path)

                        file_path_return = create_file(stream_link_path, stream_link_file_name, stream_link_url, special_action)
                        file_path_return = normalize_path(file_path_return)
                        bookmark_status['stream_link_file'] = file_path_return

                elif bookmark_status['status'].lower() == "watched" or bookmark_status['stream_link'] == "" or ( special_action == "Make STRM" and bookmark_status['stream_link_override'] == "" ):

                    for condition in special_actions_default:
                        file_delete(stream_link_path, stream_link_file_name, condition)

                    bookmark_status['stream_link_file'] = None

    if remove_choice:
        remove_rogue_empty(movie_path, tv_path, video_path, bookmarks_statuses)

    write_data(csv_bookmarks_status, bookmarks_statuses)

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

# Automation - Generate Stream Links for New & Recent Releases Only
def run_slm_new_recent_releases():
    print("\n==========================================================")
    print("|                                                        |")
    print("|           SLM: New & Recent Releases Process           |")
    print("|                                                        |")
    print("==========================================================")

    notification_add(f"\n{current_time()} Beginning SLM New & Recent Releases process...\n")

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

    notification_add(f"\n{current_time()} Total Elapsed Time: {int(hours)} hours | {int(minutes)} minutes | {int(seconds)} seconds")

    notification_add(f"\n{current_time()} SLM New & Recent Releases process complete.\n")

# Create a list of Node IDs for New & Recent Releases
def get_original_release_date_list():
    print("\n==========================================================")
    print("|                                                        |")
    print("|               Get Original Release Dates               |")
    print("|                                                        |")
    print("==========================================================")

    print(f"\n{current_time()} Gathering original release dates...\n")

    bookmarks = read_data(csv_bookmarks)
    auto_bookmarks = [
        bookmark for bookmark in bookmarks 
        if not bookmark['entry_id'].startswith('slm') 
        and bookmark['bookmark_action'] not in ["Hide"]
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

                    if bookmarks_status['special_action'] == "Make STRM" or bookmarks_status['stream_link_override'] != "":
                        continue

                    else:
                        original_release_date_raw = None
                        original_release_date = None

                        if auto_bookmark['object_type'] == "MOVIE":
                            node_id = bookmarks_status['entry_id']
                        elif auto_bookmark['object_type'] == "SHOW":
                            node_id = bookmarks_status['season_episode_id']
                        else:
                            print(f"\n{current_time()} ERROR: Invalid object_type\n")
                            continue

                        if node_id:
                            country_code = auto_bookmark['country_code']
                            language_code = auto_bookmark['language_code']

                            if bookmarks_status['original_release_date'] is None or bookmarks_status['original_release_date'] == '':
                                original_release_date_raw =  get_original_release_date(node_id, country_code, language_code)
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

    print(f"\n{current_time()} Finished gathering original release dates.\n")

    return original_release_date_list

# Gets the original release date for individual movies/episodes
def get_original_release_date(node_id, country_code, language_code):
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
            result = node_data.get('content', {}).get('originalReleaseDate', None)
            if result is None or result == '' or result =='None':
                result = "1900-01-01"
        else:
            result = "9999-12-31"
    except aiohttp.ClientError as e:
        print(f"\n{current_time()} WARNING: {e}. Skipping '{node_id}', please try again.")

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

    notification_add(f"\n{current_time()} Beginning 'Reset Channels DVR Passes' Automation...")

    channels_url_okay = check_channels_url(None)

    if channels_url_okay:
        try:
            passes_results_base = requests.get(channels_passes_url, headers=url_headers)
        except requests.RequestException as e:
            passes_message = f"\n{current_time()} ERROR: During process, received {e}. Please try again."
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
                notification_add(f"\n{current_time()} WARNING: For pass with the id '{item['passes_result_id']}', received error {e}. Skipping pause...")
                passes_error = True

        # Resort with highest priority on top to resume
        passes_results_dictionary_active.sort(key=lambda x: int(x.get("passes_result_priority", float("inf"))), reverse=True)
        for item in passes_results_dictionary_active:
            print(f"{current_time()} INFO: Resuming pass with the id '{item['passes_result_id']}'.")
            url = f"{channels_passes_url}{item['passes_result_id']}{passes_resume}"
            try:
                requests.put(url)
            except requests.RequestException as e:
                notification_add(f"\n{current_time()} WARNING: For pass with the id '{item['passes_result_id']}', received error {e}. Skipping resume...")
                passes_error = True

        if passes_error:
            passes_message = f"{current_time()} ERROR: 'Reset Channels DVR Passes' completed with an issue, see log for details."
        else:
            passes_message = f"{current_time()} INFO: 'Reset Channels DVR Passes' completed successfully."

    if passes_message is not None and passes_message != '':
        print(f"{passes_message}")

    notification_add(f"\n{current_time()} Finished 'Reset Channels DVR Passes' Automation.")

    return passes_message

# Automation - Refresh Channels DVR m3u Playlists
def run_refresh_channels_m3u_playlists():
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
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

    notification_add(f"\n{current_time()} Beginning 'Refresh Channels DVR m3u Playlists' Automation...")

    channels_url_okay = check_channels_url(None)

    if channels_url_okay:
        try:
            providers_results_base = requests.get(providers_url, headers=url_headers)
        except requests.RequestException as e:
            message = f"\n{current_time()} ERROR: During process, received {e}. Please try again."
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
                refresh_url = f"{refresh_url_pt1}{provider}{refresh_web_pt3}"
                for attempt in range(3):
                    try:
                        requests.post(refresh_url, timeout=60)
                        break  # Exit the retry loop if the request is successful
                    except requests.Timeout:
                        if attempt < 2:  # Only log a warning if we will retry
                            print(f"\n{current_time()} WARNING: For m3u Playlist '{provider}', request timed out. Retrying...")
                        else:
                            print(f"\n{current_time()} ERROR: For m3u Playlist '{provider}', request timed out. Skipping refresh...")
                            automation_error = True
                    except requests.RequestException as e:
                        print(f"\n{current_time()} ERROR: For m3u Playlist '{provider}', received error {e}. Skipping refresh...")
                        automation_error = True
                        break  # Exit the retry loop on other exceptions

            if automation_error:
                message = f"{current_time()} ERROR: 'Refresh Channels DVR m3u Playlists' completed with an issue, see log for details."
            else:
                message = f"{current_time()} INFO: 'Refresh Channels DVR m3u Playlists' completed successfully."

        else:
            message = f"\n{current_time()} INFO: For 'Refresh Channels DVR m3u Playlists', no matching valid m3u playlists were found."

    notification_add(f"\n{current_time()} Finished 'Refresh Channels DVR m3u Playlists' Automation.")

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
        {'file_name': 'Stream Link Mappings', 'file': csv_slmappings },
        {'file_name': 'Bookmarks', 'file': csv_bookmarks },
        {'file_name': 'Bookmarks Statuses', 'file': csv_bookmarks_status }
    ]

    plm_file_lists = [
        {'file_name': 'Playlists', 'file': csv_playlistmanager_playlists },
        {'file_name': 'Parent Station', 'file': csv_playlistmanager_parents },
        {'file_name': 'Child to Parent Station Map', 'file': csv_playlistmanager_child_to_parent },
        {'file_name': 'All Stations', 'file': csv_playlistmanager_combined_m3us }
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
        'main/files.html',
        segment='files',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
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
        'main/logs.html',
        segment='logs',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
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
    global slm_media_tools_manager
    global plm_streaming_stations
    settings_anchor_id = None
    run_empty_row = None

    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    channels_directory = settings[1]["settings"]
    if channels_url_prior is None or channels_url_prior == '':
        channels_url_prior = channels_url
    country_code = settings[2]["settings"]
    language_code = settings[3]["settings"]
    num_results = settings[4]["settings"]
    hide_bookmarked = settings[9]["settings"]
    channels_prune = settings[7]["settings"]
    station_start_number = settings[11]['settings']
    max_stations = settings[12]['settings']
    plm_streaming_stations_station_start_number = settings[40]['settings']      # [40] PLM: Streaming Stations Starting station number
    plm_streaming_stations_max_stations = settings[41]['settings']              # [41] PLM: Streaming Stations Max number of stations per m3u
    plm_url_tag_in_m3us = settings[42]['settings']                              # [42] PLM: URL Tag in m3u(s) On/Off

    streaming_services = read_data(csv_streaming_services)

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

    channels_url_message = ""
    channels_directory_message = ""
    search_defaults_message = ""
    advanced_experimental_message = ""

    action_to_anchor = {
        'streaming_services': 'streaming_services_anchor',
        'search_defaults': 'search_defaults_anchor',
        'slmapping': 'slmapping_anchor',
        'channels_url': 'channels_url_anchor',
        'channels_directory': 'channels_directory_anchor',
        'channels_prune': 'advanced_experimental_anchor',
        'playlist_manager': 'advanced_experimental_anchor',
        'stream_link_file_manager': 'advanced_experimental_anchor',
        'channels_dvr_integration': 'advanced_experimental_anchor',
        'media_tools_manager': 'advanced_experimental_anchor',
        'plm_streaming_stations': 'advanced_experimental_anchor'
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
        playlist_manager_input = request.form.get('playlist_manager')
        stream_link_file_manager_input = request.form.get('stream_link_file_manager')
        channels_dvr_integration_input = request.form.get('channels_dvr_integration')
        media_tools_manager_input = request.form.get('media_tools_manager')
        plm_streaming_stations_input = request.form.get('plm_streaming_stations')
        station_start_number_input = request.form.get('station_start_number')
        max_stations_input = request.form.get('max_stations')
        plm_url_tag_in_m3us_input = request.form.get('plm_url_tag_in_m3us')
        plm_streaming_stations_station_start_number_input = request.form.get('plm_streaming_stations_station_start_number')
        plm_streaming_stations_max_stations_input = request.form.get('plm_streaming_stations_max_stations')
        country_code_input = request.form.get('country_code')
        language_code_input = request.form.get('language_code')
        num_results_input = request.form.get('num_results')
        hide_bookmarked_input = request.form.get('hide_bookmarked')
        streaming_services_input = request.form.get('streaming_services')

        for prefix, anchor_id in action_to_anchor.items():
            if settings_action.startswith(prefix):
                settings_anchor_id = anchor_id
                break

        if settings_action.startswith('slmapping_') or settings_action in ['channels_url_cancel',
                                                                           'channels_directory_cancel',
                                                                           'channels_prune_cancel',
                                                                           'playlist_manager_cancel',
                                                                           'stream_link_file_manager_cancel',
                                                                           'channels_dvr_integration_cancel',
                                                                           'media_tools_manager_cancel',
                                                                           'plm_streaming_stations_cancel',
                                                                           'search_defaults_cancel',
                                                                           'streaming_services_cancel',
                                                                           'channels_url_save',
                                                                           'channels_directory_save',
                                                                           'channels_prune_save',
                                                                           'playlist_manager_save',
                                                                           'stream_link_file_manager_save',
                                                                           'channels_dvr_integration_save',
                                                                           'media_tools_manager_save',
                                                                           'plm_streaming_stations_save',
                                                                           'search_defaults_save',
                                                                           'streaming_services_save',
                                                                           'streaming_services_update',
                                                                           'channels_url_test',
                                                                           'channels_url_scan'
                                                                        ]:

            if settings_action.startswith('slmapping_action_') or settings_action in ['channels_url_save',
                                                                                      'channels_directory_save',
                                                                                      'channels_prune_save',
                                                                                      'playlist_manager_save',
                                                                                      'stream_link_file_manager_save',
                                                                                      'channels_dvr_integration_save',
                                                                                      'media_tools_manager_save',
                                                                                      'plm_streaming_stations_save',
                                                                                      'search_defaults_save',
                                                                                      'streaming_services_save',
                                                                                      'channels_url_scan'
                                                                                    ]:

                if settings_action in ['channels_url_save',
                                    'channels_directory_save',
                                    'channels_prune_save',
                                    'playlist_manager_save',
                                    'stream_link_file_manager_save',
                                    'channels_dvr_integration_save',
                                    'media_tools_manager_save',
                                    'plm_streaming_stations_save',
                                    'search_defaults_save',
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

                    elif settings_action == 'search_defaults_save':
                            settings[2]["settings"] = country_code_input
                            settings[3]["settings"] = language_code_input
                            try:
                                if int(num_results_input) > 0:
                                    settings[4]["settings"] = int(num_results_input)
                                else:
                                    search_defaults_message = f"{current_time()} ERROR: For 'Number of Results', please enter a positive integer."
                            except ValueError:
                                search_defaults_message = f"{current_time()} ERROR: 'Number of Results' must be a number."
                            settings[9]["settings"] = "On" if hide_bookmarked_input == 'on' else "Off"

                    elif settings_action == 'channels_prune_save':
                        settings[7]["settings"] = "On" if channels_prune_input == 'on' else "Off"

                    elif settings_action == 'playlist_manager_save':
                        try:
                            if int(station_start_number_input) > 0 and int(max_stations_input) > 0:
                                settings[10]["settings"] = "On" if playlist_manager_input == 'on' else "Off"
                                settings[11]['settings'] = int(station_start_number_input)
                                settings[12]['settings'] = int(max_stations_input)
                                settings[42]['settings'] = "On" if plm_url_tag_in_m3us_input == 'on' else "Off"
                                if settings[42]['settings'] == "On":
                                    settings[43]['settings'] = f"{request.url_root}"

                                if playlist_manager_input == 'on':
                                    slm_playlist_manager = True
                                    plm_csv_files = [
                                        csv_playlistmanager_playlists,
                                        csv_playlistmanager_parents,
                                        csv_playlistmanager_child_to_parent,
                                        csv_playlistmanager_combined_m3us
                                    ]

                                    for plm_csv_file in plm_csv_files:
                                        check_and_create_csv(plm_csv_file)
                                    
                                    create_directory(playlists_uploads_dir)
                                
                                else:
                                    slm_playlist_manager = None

                            else:
                                advanced_experimental_message = f"{current_time()} ERROR: 'Station Start Number' and 'Max Stations per m3u' must be positive integers."
                        except ValueError:
                            advanced_experimental_message = f"{current_time()} ERROR: 'Station Start Number' and 'Max Stations per m3u' must be numbers."

                    elif settings_action == 'stream_link_file_manager_save':
                        settings[23]["settings"] = "On" if stream_link_file_manager_input == 'on' else "Off"

                        if stream_link_file_manager_input == 'on':
                            slm_stream_link_file_manager = True
                        else:
                            slm_stream_link_file_manager = None

                    elif settings_action == 'channels_dvr_integration_save':
                        settings[24]["settings"] = "On" if channels_dvr_integration_input == 'on' else "Off"

                        if channels_dvr_integration_input == 'on':
                            slm_channels_dvr_integration = True
                        else:
                            slm_channels_dvr_integration = None

                    elif settings_action == 'media_tools_manager_save':
                        settings[28]["settings"] = "On" if media_tools_manager_input == 'on' else "Off"

                        if media_tools_manager_input == 'on':
                            slm_media_tools_manager = True
                        else:
                            slm_media_tools_manager = None

                    elif settings_action == 'plm_streaming_stations_save':
                        try:
                            if int(plm_streaming_stations_station_start_number_input) > 0 and int(plm_streaming_stations_max_stations_input) > 0:
                                settings[39]["settings"] = "On" if plm_streaming_stations_input == 'on' else "Off"
                                settings[40]['settings'] = int(plm_streaming_stations_station_start_number_input)
                                settings[41]['settings'] = int(plm_streaming_stations_max_stations_input)

                                if plm_streaming_stations_input == 'on':
                                    plm_streaming_stations = True
                                    plm_csv_file = csv_playlistmanager_streaming_stations
                                    check_and_create_csv(plm_csv_file)
                                else:
                                    plm_streaming_stations = None

                            else:
                                advanced_experimental_message = f"{current_time()} ERROR: For Streaming Stations, 'Station Start Number' and 'Max Stations per m3u' must be positive integers."
                        
                        except ValueError:
                            advanced_experimental_message = f"{current_time()} ERROR: For Streaming Stations, 'Station Start Number' and 'Max Stations per m3u' must be numbers."

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

                write_data(csv_to_write, data_to_write)
                if run_empty_row:
                    remove_empty_row(csv_to_write)

                if settings_action == 'search_defaults_save':
                    update_streaming_services()
                    time.sleep(5)

            elif settings_action == 'streaming_services_update':
                update_streaming_services()
                time.sleep(5)

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
        channels_directory = settings[1]["settings"]
        if channels_url_prior is None or channels_url_prior == '':
            channels_url_prior = channels_url
        country_code = settings[2]["settings"]
        language_code = settings[3]["settings"]
        num_results = settings[4]["settings"]
        hide_bookmarked = settings[9]["settings"]
        channels_prune = settings[7]["settings"]
        station_start_number = settings[11]['settings']
        max_stations = settings[12]['settings']
        plm_streaming_stations_station_start_number = settings[40]['settings']      # [40] PLM: Streaming Stations Starting station number
        plm_streaming_stations_max_stations = settings[41]['settings']              # [41] PLM: Streaming Stations Max number of stations per m3u
        plm_url_tag_in_m3us = settings[42]['settings']                              # [42] PLM: URL Tag in m3u(s) On/Off

        streaming_services = read_data(csv_streaming_services)

        slmappings = read_data(csv_slmappings)

    response = make_response(render_template(
        'main/settings.html',
        segment='settings',
        html_slm_version=slm_version,
        html_gen_upgrade_flag = gen_upgrade_flag,
        html_slm_playlist_manager = slm_playlist_manager,
        html_slm_stream_link_file_manager = slm_stream_link_file_manager,
        html_slm_channels_dvr_integration = slm_channels_dvr_integration,
        html_slm_media_tools_manager = slm_media_tools_manager,
        html_plm_streaming_stations = plm_streaming_stations,
        html_settings_anchor_id = settings_anchor_id,
        html_channels_url=channels_url,
        html_channels_url_prior = channels_url_prior,
        html_channels_directory = channels_directory,
        html_valid_country_codes = valid_country_codes,
        html_country_code = country_code,
        html_valid_language_codes = valid_language_codes,
        html_language_code = language_code,
        html_num_results = num_results,
        html_channels_prune = channels_prune,
        html_streaming_services = streaming_services,
        html_channels_url_message = channels_url_message,
        html_current_directory = current_directory,
        html_subdirectories = get_subdirectories(current_directory),
        html_channels_directory_message = channels_directory_message,
        html_search_defaults_message = search_defaults_message,
        html_slmappings = slmappings,
        html_slmappings_object_type = slmappings_object_type,
        html_slmappings_replace_type = slmappings_replace_type,
        html_hide_bookmarked = hide_bookmarked,
        html_station_start_number = station_start_number,
        html_max_stations = max_stations,
        html_plm_streaming_stations_station_start_number = plm_streaming_stations_station_start_number,
        html_plm_streaming_stations_max_stations = plm_streaming_stations_max_stations,
        html_plm_url_tag_in_m3us = plm_url_tag_in_m3us,
        html_advanced_experimental_message = advanced_experimental_message
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
    update_rows(csv_streaming_services, data, "streaming_service_name", None)

# Search for country code
def get_country_code():
    settings = read_data(csv_settings)
    country_code = settings[2]["settings"]
    country_code_input = None
    country_code_new = None

    global timeout_occurred
    timeout_occurred = False
    print(f"\n{current_time()} Searching for country code for Streaming Services...")
    print(f"{current_time()} Please wait or press 'Ctrl+C' to stop and continue the initialization process.\n")

    # Search times out after 30 seconds
    timer = threading.Timer(30, timeout_handler)
    timer.start()

    try:
        response = requests.get('https://ipinfo.io', headers=url_headers)
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
        print(f"{current_time()} INFO: Country found!")
        country_code_new = country_code_input.upper()
    else:
        print(f"{current_time()} INFO: Country not found, using default value. Please set your Country in 'Settings'.")
        country_code_new = country_code

    print(f"{current_time()} INFO: Country Code set to '{country_code_new}'\n")

    return country_code_new

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
                if os.path.abspath(os.path.join(root)).lower().endswith("dvr") or os.path.abspath(os.path.join(root)).lower().endswith("channels_folder"):
                    channels_dvr_path_search = os.path.abspath(os.path.join(root))
                    break  # Stop searching once found
    except TimeoutError:
        print(f"{current_time()} INFO: Search timed out. Continuing to next step...\n")
    except KeyboardInterrupt:
        print(f"{current_time()} INFO: Search interrupted by user. Continuing to next step...\n")
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
            print(f"{current_time()} INFO: Channels DVR folder not found, defaulting to current directory. Please set your Channels DVR folder in 'Settings'.")

    print(f"{current_time()} INFO: Channels DVR folder set to '{channels_dvr_path}'\n")

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
    
    # Remove non-alphabetic characters
    cleaned_title = re.sub(r'[^a-zA-Z\s]', '', title)
    words = cleaned_title.casefold().split()
    
    for lang, art_list in articles.items():
        if words and words[0] in art_list:
            return " ".join(words[1:])
    return cleaned_title.casefold()

# Normalize the file path for systems that can't handle certain characters like 'é'
def normalize_path(path):
    return unicodedata.normalize('NFKC', path)

# Get the full path for a file
def full_path(file):
    full_path = os.path.join(program_files_dir, file)
    return full_path

# Get complete file path and name
def get_file_path(path, name, special_action):
    file_name_base = f"{name}"

    if special_action == "Make STRM":
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
                    notification_add(f"    On second attempt, removed empty directory: {dir_path}")
                except OSError as e:
                    notification_add(f"    Second error removing directory {dir_path}: {e}")

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
            print(f"\n{current_time()} WARNING: After {attempt + 1} attempt, failed to remove {filepath} due to: {e}")
        
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
        notification_add(f"\n{current_time()} INFO: New row added to {csv_file}... it was for '{purpose}'.")

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
            print(f"\n{current_time()} INFO: Adding new rows to {csv_file}...\n")
            for new_row in new_rows:
                append_data(csv_file, new_row)
                notification_add(f"    ADDED: {new_row[id_field]}")
            print(f"\n{current_time()} INFO: Finished adding new rows.\n")

        old_rows = extract_old_rows(csv_file, data, id_field)
        if old_rows:
            print(f"\n{current_time()} INFO: Removing old rows from {csv_file}...\n")
            for old_row in old_rows:
                notification_add(f"    REMOVED: {old_row[id_field]}")
            remove_data(csv_file, old_rows, id_field)
            print(f"\n{current_time()} INFO: Finished removing old rows.\n")

        if modify_flag:
            modified_rows, no_notify_rows = extract_modified_rows(csv_file, data, id_field)
            if modified_rows:
                print(f"\n{current_time()} INFO: Updating modified rows in {csv_file}...\n")
                for modified_row in modified_rows:
                    if modified_row not in no_notify_rows:
                        notification_add(f"    MODIFIED: {modified_row[id_field]}")
                update_data(csv_file, modified_rows, id_field)
                print(f"\n{current_time()} INFO: Finished updating modified rows.\n")

            remove_duplicate_rows(csv_file)
            
    else:
        print(f"\n{current_time()} WARNING: No data to compare, skipping adding and removing rows in {csv_file}.\n")

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
        
        print(f"\n{current_time()} INFO: Removed duplicate rows from {csv_file}.\n")

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
            print(f"\n*** First Time Setup ***")
            settings = read_data(csv_settings)

            settings[0]['settings'], channels_url_message = get_channels_url()

            settings[1]['settings'] = find_channels_dvr_path()
            
            settings[2]['settings'] = get_country_code()
            
            write_data(csv_settings, settings)

    # Append/Remove rows to data that may update
    if csv_file == csv_streaming_services:
        id_field = "streaming_service_name"
        update_rows(csv_file, data, id_field, None)

    # Add columns for new functionality
    if csv_file == csv_bookmarks_status:
        check_and_add_column(csv_file, 'special_action', 'None')
        check_and_add_column(csv_file, 'original_release_date', '')

    if csv_file == csv_bookmarks:
        check_and_add_column(csv_file, 'bookmark_action', 'None')

    # Add rows for new functionality
    if csv_file == csv_settings:
        check_and_append(csv_file, {"settings": "Off"}, 11, "Search Defaults: Filter out already bookmarked")
        check_and_append(csv_file, {"settings": "Off"}, 12, "Playlist Manager: On/Off")
        check_and_append(csv_file, {"settings": 10000}, 13, "Playlist Manager: Starting station number")
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
        check_and_append(csv_file, {"settings": "Off"}, 41, "PLM: Streaming Stations On/Off")
        check_and_append(csv_file, {"settings": 5000}, 42, "PLM: Streaming Stations Starting station number")
        check_and_append(csv_file, {"settings": 750}, 43, "PLM: Streaming Stations Max number of stations per m3u")
        check_and_append(csv_file, {"settings": "Off"}, 44, "PLM: URL Tag in m3u(s) On/Off")
        check_and_append(csv_file, {"settings": "http://localhost:5000"}, 45, "PLM: URL Tag in m3u(s) Preferred URL Root")
        check_and_append(csv_file, {"settings": "Every 24 hours"}, 46, "PLM: Update Stations Process Schedule Frequency")

# Data records for initialization files
def initial_data(csv_file):
    if csv_file == csv_settings:
        data = [
                    {"settings": f"http://dvr-{socket.gethostname().lower()}.local:8089"},     # [0]  Channels URL
                    {"settings": script_dir},                                                  # [1]  Channels Folder
                    {"settings": "US"},                                                        # [2]  Search Defaults: Country Code
                    {"settings": "en"},                                                        # [3]  Search Defaults: Language Code
                    {"settings": "9"},                                                         # [4]  Search Defaults: Number of Results
                    {"settings": "Off"},                                                       # DEPRECATED: [5] Hulu to Disney+ Automatic Conversion
                    {"settings": datetime.datetime.now().strftime('%H:%M')},                   # [6]  SLM: End-to-End Process Schedule Time
                    {"settings": "On"},                                                        # [7]  Channels Prune
                    {"settings": "Off"},                                                       # [8]  SLM: End-to-End Process Schedule On/Off
                    {"settings": "Off"},                                                       # [9]  Search Defaults: Filter out already bookmarked
                    {"settings": "Off"},                                                       # [10] Playlist Manager: On/Off
                    {"settings": 10000},                                                       # [11] Playlist Manager: Starting station number
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
                    {"settings": "Off"},                                                       # [39] PLM: Streaming Stations On/Off
                    {"settings": 5000},                                                        # [40] PLM: Streaming Stations Starting station number
                    {"settings": 750},                                                         # [41] PLM: Streaming Stations Max number of stations per m3u
                    {"settings": "Off"},                                                       # [42] PLM: URL Tag in m3u(s) On/Off
                    {"settings": "http://localhost:5000"},                                     # [43] PLM: URL Tag in m3u(s) Preferred URL Root
                    {"settings": "Every 24 hours"}                                             # [44] PLM: Update Stations Process Schedule Frequency
        ]        
    elif csv_file == csv_streaming_services:
        data = get_streaming_services()
    elif csv_file == csv_bookmarks:
        data = [
            {"entry_id": None,"title": None, "release_year": None, "object_type": None, "url": None, "country_code": None, "language_code": None, "bookmark_action": None}
        ]
    elif csv_file == csv_bookmarks_status:
        data = [
            {"entry_id": None, "season_episode_id": None, "season_episode_prefix": None, "season_episode": None, "status": None, "stream_link": None, "stream_link_override": None, "stream_link_file": None, "special_action": None, "original_release_date": None}
        ]
    elif csv_file == csv_slmappings:
        data = [
            {"active": "Off", "contains_string": "hulu.com/watch", "object_type": "MOVIE or SHOW", "replace_type": "Replace string with...", "replace_string": "disneyplus.com/play"},
            {"active": "On", "contains_string": "netflix.com/title", "object_type": "MOVIE", "replace_type": "Replace string with...", "replace_string": "netflix.com/watch"},
            {"active": "On", "contains_string": "watch.amazon.com/detail?gti=", "object_type": "MOVIE or SHOW", "replace_type": "Replace string with...", "replace_string": "www.amazon.com/gp/video/detail/"},
            {"active": "Off", "contains_string": "vudu.com", "object_type": "MOVIE or SHOW", "replace_type": "Replace entire Stream Link with...", "replace_string": "fandangonow://"} #,
            # Add more rows as needed
        ]
    # Playlist Manager
    elif csv_file == csv_playlistmanager_playlists:
        data = [
            {"m3u_id": None, "m3u_name": None, "m3u_url": None, "epg_xml": None, "stream_format": None, "m3u_priority": None}
        ]
    elif csv_file == csv_playlistmanager_parents:
        data = [
            {"parent_channel_id": None, "parent_title": None, "parent_tvg_id_override": None, "parent_tvg_logo_override": None, "parent_channel_number_override": None, "parent_tvc_guide_stationid_override": None, "parent_tvc_guide_art_override": None, "parent_tvc_guide_tags_override": None, "parent_tvc_guide_genres_override": None, "parent_tvc_guide_categories_override": None, "parent_tvc_guide_placeholders_override": None, "parent_tvc_stream_vcodec_override": None, "parent_tvc_stream_acodec_override": None, "parent_preferred_playlist": None}
        ]
    elif csv_file == csv_playlistmanager_child_to_parent:
        data = [
            {"child_m3u_id_channel_id": None, "parent_channel_id": None}
        ]    
    elif csv_file == csv_playlistmanager_combined_m3us:
        data = [
            {"station_playlist": None, "m3u_id": None, "title": None, "tvc_guide_title": None, "channel_id": None, "tvg_id": None, "tvg_name": None, "tvg_logo": None, "tvg_chno": None, "channel_number": None, "tvg_description": None, "tvc_guide_description": None, "group_title": None, "tvc_guide_stationid": None, "tvc_guide_art": None, "tvc_guide_tags": None, "tvc_guide_genres": None, "tvc_guide_categories": None, "tvc_guide_placeholders": None, "tvc_stream_vcodec": None, "tvc_stream_acodec": None, "url": None}
        ]
    elif csv_file == csv_playlistmanager_streaming_stations:
        data = [
            {"channel_id": None, "source": None, "url": None, "title": None, "tvg_logo": None, "tvg_description": None,     "tvc_guide_tags": None, "tvc_guide_genres": None, "tvc_guide_categories": None, "tvc_guide_placeholders": None, "tvc_stream_vcodec": None, "tvc_stream_acodec": None}
        ]

    return data

# Website check in loop
def check_website(url):
    while True:
        try:
            response = requests.get(url, headers=url_headers)
            if response.status_code == 200:
                print(f"\n{current_time()} SUCCESS: {url} is accessible. Continuing...")
                break
            else:
                print(f"\n{current_time()} ERROR: {url} reports {response.status_code}")
        except requests.RequestException as e:
            print(f"\n{current_time()} ERROR: {url} reports {e}")
        
        print(f"\n{current_time()} INFO: Retrying in 1 minute...")
        time.sleep(60)

# Used to loop through a URL that might error
def fetch_url(url, retries, delay):
    timeout_duration = 120

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=url_headers, timeout=timeout_duration)
            if response.status_code == 200:
                return response
            else:
                raise Exception(f"HTTP Status Code {response.status_code}")
        except Exception as e:
            if attempt < retries - 1:
                print(f"\n{current_time()} WARNING: For '{url}', encountered an error ({e}). Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                notification_add(f"\n{current_time()} ERROR: For '{url}', after {retries} attempts, could not resolve error ({e}). Skipping...")

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

    print(f"\n{current_time()} Searching for Channels URL...")
    print(f"{current_time()} Please wait or press 'Ctrl+C' to stop and continue the initialization process.\n")

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

    print(f"\n{channels_url_message}")
    print(f"{current_time()} INFO: Channels URL set to '{channels_url}'\n")

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

    return results_library

# Puts JSON data into Channels DVR
def put_channels_dvr_json(route, json_data):
    settings = read_data(csv_settings)
    channels_url = settings[0]["settings"]
    full_url = f"{channels_url}{route}"
    results = None

    try:
        results = requests.put(full_url, headers=url_headers, json=json_data)
    except requests.RequestException as e:
        print(f"{current_time()} ERROR: While performing action on '{route}', received {e}.")

    return results

# Calculate percentages or set to zero if total_records is zero
def calc_percentage(count, total):
    return f"{round((count / total) * 100, 1)}%" if total > 0 else "0.0%"

# Global Variables
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
csv_bookmarks = "StreamLinkManager_Bookmarks.csv"
csv_bookmarks_status = "StreamLinkManager_BookmarksStatus.csv"
csv_slmappings = "StreamLinkManager_SLMappings.csv"
# Playlist Manager files only get created when turned on in Settings
csv_playlistmanager_playlists = "PlaylistManager_Playlists.csv"
csv_playlistmanager_combined_m3us = "PlaylistManager_Combinedm3us.csv"
csv_playlistmanager_parents = "PlaylistManager_Parents.csv"
csv_playlistmanager_child_to_parent = "PlaylistManager_ChildToParent.csv"
csv_playlistmanager_streaming_stations = "PlaylistManager_StreamingStations.csv"
csv_files = [
    csv_settings,
    csv_streaming_services,
    csv_bookmarks,
    csv_bookmarks_status,
    csv_slmappings  #,
    # Add more rows as needed
]
program_files = csv_files + [log_filename]
github_url = "https://github.com/babsonnexus/stream-link-manager-for-channels"
github_url_raw = "https://raw.githubusercontent.com/babsonnexus/stream-link-manager-for-channels/refs/heads/main/"
engine_url = "https://www.justwatch.com"
url_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
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
special_actions_default = [
    "None",
    "Make STRM" #, Add more as needed
]
notifications = []
timeout_occurred = None
stream_link_ids_changed = []
program_search_results_prior = []
country_code_input_prior = None
language_code_input_prior = None
entry_id_prior = None
title_selected_prior = None
release_year_selected_prior = None
object_type_selected_prior = None
bookmark_action_prior = None
season_episodes_prior = []
bookmarks_statuses_selected_prior = []
edit_flag = None
channels_url_prior = None
date_new_default_prior = None
program_add_prior = ''
program_add_resort_panel = ''
program_add_filter_panel = ''
slm_query = None
slm_query_name = None
offer_icons = []
offer_icons_flag = None
select_file_prior = None
bookmark_actions_default = [
    "None",
    "Hide" #, Add more as needed
]
bookmark_actions_default_show_only = [
    "Disable Get New Episodes" #, Add more as needed
]
stream_formats = [
    "HLS",
    "MPEG-TS",
    "STRMLNK"
]
select_program_to_bookmarks = []
gen_upgrade_flag = None
gracenote_search_results = None
gracenote_search_entry_prior = ''
csv_explorer_results = None
csv_explorer_entry_prior = ''
streaming_stations_source_test_prior = ''
streaming_stations_url_test_prior = ''

### Start-up process and safety checks
# Program directories
create_directory(program_files_dir)
create_directory(backup_dir)

# Make a backup and remove old backups
if os.path.exists(program_files_dir):
    create_backup()

# Set up session logging
### Custom logger to write yt-dlp output to your log file
class YTDLLogger:
    def debug(self, msg):
        log.write(msg + "\n")

    def info(self, msg):
        log.write(msg + "\n")

    def warning(self, msg):
        log.write("[WARNING] " + msg + "\n")

    def error(self, msg):
        log.write("[ERROR] " + msg + "\n")

### Log Setup
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

notification_add(f"\n{current_time()} Beginning Initialization Process (see log for details)...\n")

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
slm_media_tools_manager = None
if global_settings[28]['settings'] == "On":
    slm_media_tools_manager = True
plm_streaming_stations = None
if global_settings[39]['settings'] == "On":
    plm_streaming_stations = True

if slm_channels_dvr_integration:
    check_channels_url(None)

check_upgrade()

# Start the background thread
thread = threading.Thread(target=check_schedule)
thread.daemon = True
thread.start()

if slm_channels_dvr_integration:
    notification_add(f"\n{current_time()} Initialization Complete. Starting Streaming Library Manager for Channels...")
else:
    notification_add(f"\n{current_time()} Initialization Complete. Starting Streaming Library Manager...")

# Start Server
if __name__ == "__main__":
    notification_add(f"\n{current_time()} INFO: Server starting on port {slm_port}\n")
    app.run(host='0.0.0.0', port=slm_port)
