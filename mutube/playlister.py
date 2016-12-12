""" playlister """

from .exceptions import NoTag, NoPlaylist, BadVideo
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

    def __init__(self, prefix, time_format, client_json='client_id.json'):
        """
        Initialise YouTube client and specify tag format for playlist titles.

        Args:
            prefix ::: (str) unique identifier for playlist series
                        see `encode_tag` documentation
            time_format ::: (str) format specifier for `time.strftime`
                            see http://strftime.org/
            client_json ::: (str) path to .JSON file containing OAuth 2.0
                            client credentials, downloaded from:
                            https://console.developers.google.com/
        """
        self.youtube = self._build_resource(client_json)
        self.prefix = prefix
        self.time_format = time_format

    def _build_resource(self, client_json):
        """ Create the resource object to interact with YouTube API.

        Args:
            client_json ::: (str) path to .JSON file containing OAuth 2.0
                            client credentials
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
        """ Return tag found in `title` matching specified format."""

        tag = title.split(']')[0] # assume tag is at start of title
        tag = tag + ']' # reattach delimiter
        if self._validate_tag(tag):
            return tag
        else:
            raise NoTag("No valid tag in: \n\t{}".format(title))

    def _validate_tag(self, tag):
        """ Return True if `tag` matches specified tag format. """

        valid = False
        try: # assess tag
            prefix, time_tuple = decode_tag(tag, self.time_format)
            if prefix == self.prefix:
                valid = True
        except ValueError: # if decoding fails
            pass

        return valid

    def get_tagged_playlists(self):
        """ Return {tag: response} for appropriately tagged playlists. """

        # Fetch list of playlists
        all_playlists = []
        request = self.youtube.playlists().list(
                part='snippet', mine=True, maxResults=50)
        while request:
            response=request.execute()
            all_playlists.extend(response['items'])
            request = self.youtube.playlists().list_next(request, response)

        # Filter playlists
        tagged_playlists = {}
        for playlist in all_playlists:
            try: # store playlist
                tag = self._extract_tag_from_title(playlist['snippet']['title'])
                tagged_playlists[tag] = playlist # ! duplicates get shadowed
            except NoTag:
                pass

        return tagged_playlists

    def create_new_playlist(self, title):
        """ Create empty public playlist with `title`, returning response. """

        # Create request
        request = self.youtube.playlists().insert(
            part="snippet,status",
            body=dict(snippet=dict(title=title),
                      status=dict(privacyStatus="public")))
        
        return request.execute()

    def get_playlist(self, tag):
        """ Return any playlist whose title starts with `tag`.
        
        Note: if multiple playlists match `tag`, an arbitrary one is returned.
        """

        tagged_playlists = self.get_tagged_playlists()
        playlist = tagged_playlists.get(tag)
        if playlist is None:
            raise NoPlaylist("No playlist found matching tag: {}".format(tag))

        return playlist

    def get_posted_yt_ids(self, playlist):
        """ Return all YouTube video ids in a playlist.

        Args:
            playlist ::: (dict) containing `id` key for youtube playlist id
                         i.e. the response from youtube api playlist request
        Returns:
            yt_ids ::: (set) video ids for all videos in `playlist`
        """

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
        """ Insert video to playlist.

        Args:
            playlist ::: (dict) containing `id` key for youtube playlist id
                         i.e. the response from youtube api playlist request
            yt_id ::: (str) id of a YouTube video
        """
        # Build insert request
        request = self.youtube.playlistItems().insert(
            part='snippet', body={'snippet':{
                'playlistId': playlist['id'],
                'resourceId': {'kind': 'youtube#video',
                    'videoId': yt_id}}})

        # Return a valid response, or raise an error
        try: 
            return request.execute()
        except HttpError as err:
            if err.resp.status == 404: # "video not found" error
                raise BadVideo('video does not exist: {}'.format(yt_id))
            else:
                raise err

# Helper functions
def encode_tag(prefix, time_tuple, time_format):
    """ Create a [prefix:time] playlist tag using specified time formatting.

    Args:
        prefix ::: (str) unique identifier for playlist series
        time_tuple ::: (`time.struct_time` instance) time to encode in tag
        time_format ::: (str) format specifier for `time.strftime`
                        see http://strftime.org/
    Returns:
        tag ::: (str) playlist tag formatted as specified

    Example:
            >>> encode_tag(prefix='KPOP',
                           time_tuple=time.localtime(), # during April 2017
                           time_format='%Y-%m') 
            [KPOP:2017-04]
    """
    # Build tag
    datestr = time.strftime(time_format, time_tuple)
    return '[{}]'.format(':'.join([prefix, datestr]))

def decode_tag(tag, time_format):
    """ Return prefix and time represented by playlist tag.

    Args:
        tag ::: (str) playlist tag to decode
        time_format ::: (str) format specifier for `time.strftime`
                        see http://strftime.org/
    Returns:
        prefix ::: (str) unique identifier for playlist series
        time_tuple ::: (`time.struct_time` instance) time to encode in tag
    
    Example:
        >>> decode_tag(tag='[DAILY:Wed 16.11.2016]',
                        time_format='%a %d.%m.%Y')
        ('DAILY',
         time.struct_time(tm_year=2016, tm_mon=11, tm_mday=16, tm_hour=0,
             tm_min=0, tm_sec=0, tm_wday=2, tm_yday=321, tm_isdst=-1))
    
    """
    prefix, datestr = tag.strip('[]').split(':')
    time_tuple = time.strptime(datestr, time_format)
    
    return prefix, time_tuple
