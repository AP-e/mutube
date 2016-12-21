""" resource builder

Create resource to interact with YouTube API.
"""
import httplib2
import json
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

# YouTube API information
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

class ResourceBuilder(object):
    """ Factory building resource object to make YouTube read/write requests. """
    
    @classmethod
    def from_credentials_object(cls, credentials):
        """ Return a resource object from a user credentials object.
        Args:
            credentials ::: `oauth2client.client.Credentials` instance
        Returns:
            youtube ::: YouTube `apiclient.discovery.Resource` instance
       """
        # Build YouTube resource object
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                        http=credentials.authorize(httplib2.Http()))
        return youtube

    @classmethod
    def from_user_credentials_file(cls, user_credentials_fname):
        """ Return a resource object from file containing user credentials.
        Args:
            user_credentials_fname ::: path to .json file to read
                                       contains OAuth 2.0 user credentials
                                       usually created by auth flow, see
                                       `from_client_credentials_fname` method
        Returns:
            youtube ::: YouTube `apiclient.discovery.Resource` instance
        """
        credentials = Storage(user_credentials_fname).get()
        return cls.from_credentials_object(credentials)

    @classmethod
    def from_client_credentials_file(cls, client_credentials_fname,
                                     user_credentials_fname=None):
        """ Request authorisation for an app client, returning resource object.
        Args:
            client_credentials_fname ::: path to .json file to read
                                         contains OAuth 2.0 client credentials,
                                         download from:
                                         https://console.developers.google.com/
            user_credentials_fname ::: path to .json file to write to
        Returns: 
            youtube ::: YouTube `apiclient.discovery.Resource` instance
        Creates:
            <user_credentials_fname> ::: .json file containing user credentials

        This method will try to open a link in the browser requesting that the
        user sign in to YouTube and authorise the app to modify data.
        This will not work if run inside of a Jupyter Notebook.
        """
        
        # Build OAuth flow object
        flow = flow_from_clientsecrets(filename=client_credentials_fname,
                                       scope=YOUTUBE_READ_WRITE_SCOPE)
        
        if user_credentials_fname is None: # autoname credentials file            
            with open(client_credentials_fname) as o: # extract project_id
                project_id = json.load(o)['installed']['project_id']
            user_credentials_fname = "{}-oauth2.json".format(project_id)

        # Load/create credentials
        storage = Storage(user_credentials_fname)
        credentials = storage.get()
        if credentials is None or credentials.invalid: 
            credentials = run_flow(flow, storage) # request authorisation
        
        return cls.from_credentials_object(credentials)
