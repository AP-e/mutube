#!/usr/bin/env python

"""
Script to scrape /bleep/ and post to YouTube playlist
This works, but has issues:
    The `scraper` and `playlister` objects are constantly being passed around.
    Instead, the function "main" could instead be a `Mutuber` class, storing
    `scraper`, `playlister` and `existing_ids` as attributes. This would also
    make management of a `live_threads` attribute easier.
    This could then be presented as a combination of a module and a script,
    with command line argument parsing, and inserted to mutube
"""

from mutube import(Playlister, Scraper, encode_tag,
                   NoPlaylist, BadVideo, HttpError)
import time

# Scraper options
board = 'mu'
subjects = ['/bleep/']
# Playlister options
prefix = 'YOTB' 
time_format = '%Y-%m'
client_json = 'client_id.json'
playlister_pause = 1 # minutes between playlist inserts
scraper_pause = 30 # minutes between scrapes

def main(board, subjects, prefix, time_format,
        playlister_pause, scraper_pause, client_json):
    """ Continously scrape specified threads and post videos to playlists.
    
    Args:
        board ::: (str) abbreviated name of 4chan board to scrape
        subjects ::: (list) titles of `board` threads to scrape
        prefix, time_format ::: (str) playlist tag specs, see documentation
        playlister_pause, scraper_pause ::: (int) minutes to pause between
            posting to playlist and between scrape cycles, respectively
        client_json ::: (str) path to YouTube OAuth 2.0 client credentials JSON
    """
    
    # Initialise objects
    scraper = Scraper(board, subjects, client_json)
    playlister = Playlister(prefix, time_format)
    existing_ids = get_existing_ids(playlister)

    while True:
        playlist = get_current_playlist(playlister) # get current playlist
        scrape_and_insert_videos_to_playlist(playlister, scraper, existing_ids,
                                 playlist, playlister_pause) 
        time.sleep(scraper_pause * 60) # space out scrapes

def get_existing_ids(playlister):
    """ Return all video_ids posted in playlists tagged as specified. """
    playlists = playlister.get_tagged_playlists()
    existing_ids = set()
    for playlist in playlists.values():
        existing_ids.update(playlister.get_posted_yt_ids(playlist))
    
    return existing_ids 

def get_current_playlist(playlister):
    """ Return current tagged playlist, creating one if necessary. """
    # Create current tag
    tag = encode_tag(playlister.prefix, time.localtime(),
                     playlister.time_format) 
    try: # retrieve existing playlist
        playlist = playlister.get_playlist(tag)
        print("Retrieved playlist for tag: {}".format(tag))
    except NoPlaylist: # create new playlist
        playlist = playlister.create_new_playlist(tag)
        print("Created new playlist for tag: {}".format(tag))

    return playlist

def scrape_and_insert_videos_to_playlist(playlister, scraper, existing_ids,
                                         playlist, playlister_pause):
    """ Scrape videos from 4chan and post to specified playlist. """
    # Scrape videos from 4chan
    scraper.scrape()
    
    # Add scraped videos to playlist
    for yt_id in scraper.yt_ids - existing_ids: # new videos only
        try:
            response = playlister.insert_vid_to_playlist(playlist, yt_id)
            existing_ids.add(yt_id)
            print('Inserted: {}'.format(yt_id))
        except BadVideo: # skip dead links
                print('Failed to insert: {}'.format(yt_id))

        time.sleep(playlister_pause * 60) # space out write requests

if __name__ == "__main__":
    main(board, subjects, prefix, time_format, playlister_pause, scraper_pause,
         client_json)
