""" Daily daily

This script automatically generates daily playlists of YouTube links posted
to the /daily/ general threads on 4chan's /mu/.
"""
from mutube import Mutuber

if __name__ == "__main__":                                                      
    # Initialise mutuber object                                                 
    mutuber = Mutuber(                                           
            board = 'mu',
            subjects = ['/daily/'],
            prefix = 'daylist',
            time_format = '%A %d.%m.%Y', # i.e. "Thursday 23.06.2016"
            client_json = 'client_id.json',
            current_only = True, # allow reposting between different playlists
            playlister_pause = 1, # one insertion per minute
            scraper_pause = 10) # scrape every 10 minutes
    mutuber.run_forever() 
