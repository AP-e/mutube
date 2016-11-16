""" playlister """

from .exceptions import NoTag, NoPlaylist
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
import json
import httplib2
import time

# YouTube API information
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

class Playlister():
    """ Create YouTube playlists. """
    
    def __init__(self, stump, time_format, client_json='client_id.json'):
        """ 
        Args:
            stump :::  
            time_format :::
            client_json ::: str path to .JSON file containing OAuth 2.0
                            client credentials (see ...)
        """
        self.youtube = self._build_resource(client_json)
        self.stump = stump
        self.time_format = time_format

    def _build_resource(self, client_json):
        """ Create the resource object to interact with YouTube API.
        Args:
            client_json ::: path to .JSON file containing OAuth 2.0 client credentials
        """
        
        # Get project id
        with open(client_json) as o:
            project_id = json.load(o)['installed']['project_id']
        
        # Build OAuth flow object
        flow = flow_from_clientsecrets(filename=client_json, 
                                       scope=YOUTUBE_READ_WRITE_SCOPE)
        
        # Load/create credentials
        storage = Storage("{}-oauth2.json".format(project_id))
        credentials = storage.get()
        if credentials is None or credentials.invalid: # request authorisation
            credentials = run_flow(flow, storage) # ! warning: fails in ipynb
        
        # Build YouTube resource object
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                        http=credentials.authorize(httplib2.Http()))
        
        return youtube
    
    def _extract_tag_from_title(self, title):
        """ Return a valid tag from playlist title."""
        
        tag = title.split()[0] # assume tag is first 'unit' of title
        if self._validate_tag(tag):
            return tag
        else:
            raise NoTag("No valid tag in: \n\t{}".format(title))

    def _validate_tag(self, tag):
        """ Return True if `tag` matches the initialised tag format. """
        
        valid = False
        try: # assess tag
            stump, time_tuple = decode_tag(tag, self.time_format)
            if stump == self.stump:
                valid = True
        except ValueError: # if decoding fails
            pass
        
        return valid

    def get_tagged_playlists(self):
        """ Return a dict of playlist (responses) matching the specified tag format. """
        
        # Fetch list of playlists
        all_playlists = self.youtube.playlists().list(part='snippet', mine=True).execute()['items']
        
        # Filter playlists
        tagged_playlists = {}
        for playlist in all_playlists:
            try: # store playlist
                tag = self._extract_tag_from_title(playlist['snippet']['title'])
                tagged_playlists[tag] = playlist # ! duplicates get shadowed
            except NoTagError:
                pass
        
        return tagged_playlists
    
    def create_new_playlist(self, title):
        """ Create an empty public playlist with `title`. """
        
        # Create request
        request = self.youtube.playlists().insert(
            part="snippet,status",
            body=dict(snippet=dict(title=title),
                      status=dict(privacyStatus="public")))
        
        return request.execute()

    def get_playlist(self, tag):
        """ Return a playlist matching `tag`."""
        
        tagged_playlists = self.get_tagged_playlists()
        playlist = tagged_playlists.get(tag)
        if playlist is None:
            raise NoPlaylist("No playlist found matching tag: {}".format(tag))

        return playlist
    
    def get_posted_yt_ids(self, playlist):
        """ Return a set of video ids for a given playlist."""
        
        # Make initial request
        request = self.youtube.playlistItems().list(
            playlistId=playlist['id'], part="snippet", maxResults=50)

        posted_ids = set()
        while request: # get the entire playlist
            response = request.execute()
            for item in response['items']:
                posted_ids.add(item['snippet']['resourceId']['videoId'])
            request = self.youtube.playlistItems().list_next(request, response) # next page
        
        return posted_ids
    
    def insert_vid_to_playlist(self, playlist, yt_id):
        """ Insert `yt_id` to playlist, returning response. """
        # Build insert request
        request = youtube.playlistItems().insert(part='snippet', body={'snippet':{
            'playlistId': playlist['id'],
            'resourceId': {'kind': 'youtube#video',
                           'videoId': yt_id}}})
        return request.execute()


# Helper functions
def encode_tag(stump, time_tuple, time_format):
    """ Return current playlist tag as formatted by args.
    Args:
        stump ::: str text to prepend to date
        time_tuple ::: `time.struct_time` time tuple to encode as date
                           `time.localtime()` used if `None`
    Returns:
        tag ::: str tag for playlist, e.g:
            >>> playlister._encode_tag(stump='DAILY') # during April 2017
            [KPOP:2017-04]
    """      
    # Build tag 
    datestr = time.strftime(time_format, time_tuple)
    return '[{}]'.format(':'.join([stump, datestr]))

def decode_tag(tag, time_format):
    """ Return the stump str and time tuple object encoded in `tag`. """
    stump, datestr = tag.strip('[]').split(':')
    time_tuple = time.strptime(datestr, time_format)
    return stump, time_tuple
