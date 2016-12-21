""" Daily daily

This script automatically generates daily playlists of YouTube links posted
to the /daily/ general threads on 4chan's /mu/.
"""
from mutube import Scraper, Playlister, Mutuber, ResourceBuilder

def first_word_matcher(subject, general):
    """ Determine whether first word in `subject` == `general`.
    Args:
        subject ::: (str) thread subject
        general ::: (str) general name
    """
    return True if subject.split('-')[0].strip() == general else False

if __name__ == "__main__":
    # Initialise objects
    scraper = Scraper(board='mu',
                      matching_func=first_word_matcher, # custom matching 
                      general="/daily/") # argument to matching function 
    resource = ResourceBuilder.from_client_credentials_file('client_id.json') 
    playlister = Playlister(resource=resource, prefix='DAYLIST',
                            time_format='%A %d.%m.%Y') # e.g. Thursday 23.06.2016
    mutuber = Mutuber(scraper, playlister,
                      current_only=True) # repost between different playlists
    
    # Run continuously 
    mutuber.run_forever(
        playlister_pause = 1, # one insertion per minute
        scraper_pause = 10) # scrape every 10 minutes
