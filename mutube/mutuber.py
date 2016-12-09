""" mutuber
Coordinate posting to YouTube playlist of videos scraped from 4chan.
"""

from .exceptions import NoPlaylist, BadVideo
from .playlister import Playlister, encode_tag, HttpError
from .scraper import Scraper
import time

class Mutuber():
    """ Scrape from 4chan and post to YouTube playlists. """

    def __init__(self, scraper, playlister, current_only=False):
        """ Initialise mutuber with attached scraper, playlister instances.
        Args:
            board ::: (str) abbreviated name of 4chan board to scrape
            subjects ::: (list) titles of `board` threads to scrape
            prefix, time_format ::: (str) playlist tag specs, see documentation
            client_json ::: (str) path to YouTube OAuth 2.0 client credentials
                JSON file (see ...)
            current_only ::: (bool) `True` to search only currently active
                playlist for duplicates, `False` to consider all specified
        """
        # Initialise objects
        self.scraper = scraper
        self.playlister = playlister

        # Initialise options 
        self.current_only = current_only

        # Get existing id's
        if not self.current_only:
            self.existing_ids = self.get_all_existing_ids()

    def run_forever(self, playlister_pause=1, scraper_pause=30):
        """ Run continuous scrape-post cycles.
        Args:
            playlister_pause, scraper_pause ::: (int) minutes to pause between
            playlist insertions and scrape cycles, respectively
        """
        delay = scraper_pause * 60
        while True:
            self.run_once(playlister_pause)
            print("Playlist updated, sleeping for {} seconds".format(delay))
            time.sleep(delay) # space out scrapes

    def run_once(self, playlister_pause=1):
        """ Scrape videos from active thread and insert to current playlist."""
        # Get current playlist
        self.playlist = self.get_current_playlist()
        
        # Update set of existing ids
        if self.current_only: # reset existing ids in current only mode
            self.scraper.yt_ids = set() # flush out scrape history
            self.existing_ids = self.playlister.get_posted_yt_ids(
                    self.playlist) # only consider active playlist
        
        # Sync scraper with existing ids (to make scrape messages accurate)
        self.scraper.yt_ids.update(self.existing_ids)
        
        # Scrape new videos from active threads
        self.scraper.scrape()
        
        # Insert new videos
        self.insert_videos_to_playlist(playlister_pause)

    def get_current_ids(self):
        """ Return all video_ids posted in current playlist. """
        playlist = self.playlister.get_current_playlist()
        return set(self.playlister.get_posted_yt_ids(playlist))

    def get_all_existing_ids(self):
        """ Return all video_ids posted in playlists tagged as specified. """
        playlists = self.playlister.get_tagged_playlists()
        existing_ids = set()
        for playlist in playlists.values():
            existing_ids.update(self.playlister.get_posted_yt_ids(playlist))
        
        return existing_ids 

    def get_current_playlist(self):
        """ Return current tagged playlist, creating one if necessary. """
        # Create current tag
        tag = encode_tag(self.playlister.prefix, time.localtime(),
                         self.playlister.time_format) 
        try: # retrieve existing playlist
            playlist = self.playlister.get_playlist(tag)
            print("Retrieved playlist for tag: {}".format(tag))
        except NoPlaylist: # create new playlist
            playlist = self.playlister.create_new_playlist(tag)
            print("Created new playlist for tag: {}".format(tag))
    
        return playlist

    def insert_videos_to_playlist(self, playlister_pause):
        """ Insert all new videos to current playlist. """
        # Add scraped videos to playlist
        for yt_id in self.scraper.yt_ids - self.existing_ids: # new videos only
            try:
                response = self.playlister.insert_vid_to_playlist(
                        self.playlist, yt_id)
                self.existing_ids.add(yt_id)
                print('Inserted: {}'.format(yt_id))
            except BadVideo: # skip dead links
                    print('Failed to insert: {}'.format(yt_id))
    
            time.sleep(playlister_pause * 60) # space out write requests
