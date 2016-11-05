""" scraper 

Scrape YouTube links from 4chan threads.
"""
import json                                                                     
from .compat import HTTPError, parse_qs, urlopen, urlparse
from bs4 import BeautifulSoup


class Scraper():                                                                
    """ Scraper for YouTube links from 4chan threads. """

    def __init__(self, board, subjects, bad_posters=None):
        """ Set up scraper for `board`, with optional `subjects`.
    
    Args:
            board ::: str abbreviated name of 4chan board to scrape
                      eg : 'mu' : http://boards.4chan.org/mu/
            subjects ::: either:
                      :: list str thread subjects to which scraping is
                         restricted (case insensitive)
                         e.g. : ['/punk/', 'punk', 'punk general']
                      :: [] : No new threads identified for scraping
                         (only scrape manual additions to self.thread_nums)
                      :: None : All threads scraped
            bad_posters ::: (opt) list of posting names (sans trip) to ignore
                            e.g. : ['Tinytrip', 'ennui'] 
        """    
        self.board = board
        self.subjects = subjects
        self.thread_nums = set()
        self.dead_threads = set()
        self.yt_ids = set()
        self.bad_posters = [] if bad_posters is None else bad_posters

    def scrape(self, verbose=True):
        """ Scrape YouTube links from up-to-date catalog with current settings.
        
        Args:
            verbose ::: bool whether to describe scraping (default True)
        """
        # Update thread numbers from up-to-date catalog
        self._get_catalog()
        thread_nums = self._filter_catalog()
        new_threads = thread_nums.difference(self.thread_nums)
        self.thread_nums.update(thread_nums)
        
        # Scrape all threads for links
        yt_ids, dead_threads = self._scrape_catalog()
        new_ids = yt_ids.difference(self.yt_ids)
        self.yt_ids.update(new_ids)
        
        # Remove dead threads
        self.thread_nums -= dead_threads
        self.dead_threads.update(dead_threads)

        if verbose:
            print("Scraped {} new links from {} threads".format(
                    len(new_ids), len(self.thread_nums)),
                    "({} new threads added, {} dead threads removed)".format(
                        len(new_threads), len(dead_threads)))

    def _get_catalog(self):                                                   
        """ Retrieve an up-to-date JSON catalog of the 4chan board. """
        catalog_url = '/'.join(['https://a.4cdn.org', self.board,
                'catalog.json'])
        self.catalog = self._get_json_data(catalog_url)

    def _get_thread(self, thread_num):
        """ Retreive and return the JSON of the thread at `thread_num`. """
        # Get thread JSON
        thread_url = '/'.join(['https://a.4cdn.org', self.board, 
                               'thread', str(thread_num)]) + '.json'
        thread = self._get_json_data(thread_url)
        return thread 

    def _get_json_data(self, url):
        """ Return the json data located at `url`. """
        response = urlopen(url)
        content = response.read()
        data = json.loads(content.decode("utf8"))
        return data

    def _scrape_catalog(self):
        """ Scrape (optionally filtered) board catalog for YouTube links 
        
        Args:
            subjects (opt) ::: list of str, thread subjects to filter
        """
        # Scrape links from each comment in each thread
        yt_ids = set()
        dead_threads = set()
        for thread_num in self.thread_nums:
            try:
                yt_ids.update(self._scrape_thread(thread_num))
            except(HTTPError):
                dead_threads.add(thread_num)
        return yt_ids, dead_threads

    def _scrape_thread(self, thread_num):
        """ Return any YouTube links scraped from posts at `thread_num`. """
        #Extract posts
        yt_ids = set()
        for post in self._get_thread(thread_num)['posts']:
            if post.get('name', '') in self.bad_posters: # skip undesirable posters
                continue
            try:
                yt_ids.update(self._scrape_comment(post['com']))
            except(KeyError): # skip blank posts
                pass
        return yt_ids

    def _filter_catalog(self):
        """ Return thread numbers in catalog which match `self.subjects`.
            (no filtering if `self.subjects=None` or is otherwise invalid)
        """ 
        thread_nums = set()

        # Trawl through catalog for threads
        for page in self.catalog:                                               
            for thread in page['threads']:
                thread_no = int(thread['no'])
                subject = thread.get('sub', '')
                try: # Return matching, or return all threads
                    if subject.lower() in self.subjects:                                 
                        thread_nums.add(thread_no)
                except(TypeError): # Yield all if no (or invalid) subjects
                    thread_nums.add(thread_no)
        return thread_nums

    def _scrape_posts(self, thread):
        """ Return any YouTube video ids from an iterable of JSON posts. """
        for post in thread:
            try:
                self._scrape_comment(post['com'])
            except(KeyError): # skip blank posts
                pass

    def _scrape_comment(self, comment):
        """ Return any YouTube video ids in a 4chan comment. """
        yt_ids = set()
        # Attempt to parse every space delineated substring
        for string in self._strip_break_tags(comment).split():
            try:
                yt_ids.add(get_yt_video_id(string))
            except(TypeError, ValueError): # when nothing can be scraped
                pass
        return yt_ids

    def _strip_break_tags(self, comment):
        """ Remove <wbr> and <br> tags from string.
        
        Args:
            comment ::: str raw HTML 4chan post comment, from JSON 
        Returns:
            str `comment`, <wbr> removed and <br> replaced with ' '
        """
        soup = BeautifulSoup(comment, 'html.parser')

        # Remove <wbr> tags
        for wbr in soup.find_all('wbr'):
            wbr.unwrap()

        # Remove <br> tags
        for br in soup.find_all('br'):
            br.insert_before(' ') # seperate with whitespace
            br.unwrap()

        return str(soup) 

    def generate_links(self):
        """ Return self.yt_ids as a list of YouTube links. """
        return ['https://www.youtube.com/watch?v='+yt_id
                for yt_id in self.yt_ids]

def get_yt_video_id(url):
    """ Return the video id from a Youtube url.

    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',

      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',

    Reqs:
        urlparse, parse_qs from urllib.parse 

    # modified from gist by Mikhail Kashkin(http://stackoverflow.com/users/85739/mikhail-kashkin)
    # initial version: http://stackoverflow.com/a/7936523/617185 \
    """
    if url.startswith(('youtu', 'www')):
        url = 'http://' + url

    query = urlparse(url)

    if 'youtube' in query.hostname:
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return query.path.split('/')[2]
        else: 
            raise ValueError
    elif 'youtu.be' in query.hostname:
        return query.path[1:]
    else:
        raise ValueError
