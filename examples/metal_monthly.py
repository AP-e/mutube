""" Metal monthly

This script automatically generates monthly playlists of YouTube links posted
to the /metal/ general threads on 4chan's /mu/.
"""
from mutube import Mutuber

if __name__ == "__main__":                                                      
    # Initialise mutuber object                                             
    mutuber = Mutuber(
            board = 'mu',
            subjects = ['/metal/'],
            prefix = r'\m/',
            time_format = '%b %Y', # i.e. "Nov 2016" 
            client_json = 'client_id.json',
            current_only = False, # ignore all previously posted links
            playlister_pause = 1, # one insertion per minute
            scraper_pause = 60) # scrape once per hour
    mutuber.run_forever()

