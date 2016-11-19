"""
Script to scrape /bleep/ and post to YouTube playlist
Upcoming improvements include
    Management of `live_threads`.
    This could then be presented as a combination of a module and a script,
    with command line argument parsing, and inserted to mutube
"""

from .exceptions import NoPlaylist, BadVideo
from .playlister import Playlister, encode_tag, HttpError
from .scraper import Scraper
import time

class Mutuber():
    """ Scrape from 4chan and post to YouTube playlists. """
 
    def __init__(self, board, subjects, prefix, time_format, client_json,
                 playlister_pause=1, scraper_pause=None):

        """ . 
        Args:
            board ::: (str) abbreviated name of 4chan board to scrape
            subjects ::: (list) titles of `board` threads to scrape
            prefix, time_format ::: (str) playlist tag specs, see documentation
            playlister_pause, scraper_pause ::: (int) minutes to pause between
                posting to playlist and between scrape cycles, respectively
            client_json ::: (str) path to YouTube OAuth 2.0 client credentials JSON
        """
        # Initialise objects
        self.scraper = Scraper(board, subjects)
        self.playlister = Playlister(prefix, time_format, client_json)

        # Initialise options ! should check within acceptable ranges
        self.playlister_pause = playlister_pause
        self.scraper_pause = scraper_pause
        
        #! should not be on init -- let user choose whether to consider all playlists or just current
        self.existing_ids = self.get_existing_ids()

    def run_forever(self):
        """ Run continuous scrape-post cycles, with a delay. """
        while True:
            self.run_once()
            time.sleep(self.scraper_pause * 60) # space out scrapes

    def run_once(self):
        self.playlist = self.get_current_playlist() # get current playlist
        self.scrape_and_insert_videos_to_playlist()

    # Should be optionable for 'all' or 'current'
    def get_existing_ids(self):
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

    def scrape_and_insert_videos_to_playlist(self):
        """ Scrape videos from 4chan and post to specified playlist. """
        # Scrape videos from 4chan
        self.scraper.scrape()
        
        # Add scraped videos to playlist
        for yt_id in self.scraper.yt_ids - self.existing_ids: # new videos only
            try:
                response = self.playlister.insert_vid_to_playlist(self.playlist,
                                                                  yt_id)
                self.existing_ids.add(yt_id)
                print('Inserted: {}'.format(yt_id))
            except BadVideo: # skip dead links
                    print('Failed to insert: {}'.format(yt_id))
    
            time.sleep(self.playlister_pause * 60) # space out write requests
