""" Metal monthly

This script automatically generates monthly playlists of YouTube links posted
to the /metal/ general threads on 4chan's /mu/.
"""
from mutube import Scraper, Playlister, Mutuber, ResourceBuilder

if __name__ == "__main__":
    # Initialise mutuber object                                             
    scraper = Scraper(board='mu', subjects=['/metal/',
                                            '/metal/ - Metal General'])
    resource = ResourceBuilder.from_user_credentials_file('client_id.json')
    playlister = Playlister(resource=resource, prefix=r'\m/',
                            time_format = '%b %Y') # i.e. "Nov 2016"
    mutuber = Mutuber(scraper, playlister)
    mutuber.run_forever()

