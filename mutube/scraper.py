""" scraper 

Scrape YouTube links from 4chan threads.
"""
import json
import time
from .compat import HTTPError, URLError, parse_qs, urlopen, urlparse
from bs4 import BeautifulSoup


class Scraper():                                                                
    """ Scraper for YouTube links from 4chan threads. """

    def __init__(self, board, matching_func=None, bad_posters=None,
                 **matching_kwargs):
        """ Set up scraper for `board` with specified scraping criteria.
    
    Args:
            board ::: str abbreviated name of 4chan board to scrape
                      eg : 'mu' : http://boards.4chan.org/mu/
            matching ::: either of:
                      :: (callable, opt) function returning bool indicating
                         whether thread is to be scraped based on it's subject
                         call signature: matching(subject, **matching_kwargs)
                         if matching=None, `subjects` must be supplied (see
                         below)
            bad_posters (opt) ::: list of posting names (sans trip) to ignore
                            e.g. : ['Tinytrip', 'ennui']
            **matching_kwargs ::: keyword args to pass to matching_func, e.g:
            subjects ::: (iterable) str thread subjects, passed to `is_in_list`
                         function to identify threads to scrape by simple (case
                         insensitive) text matching
                         e.g. : ['/punk/', 'punk', 'punk general']
                         `[]` will identify no new threads; only manual
                         additions to self.thread_nums are scraped
        """    
        self.board = board
        # Specify matching criteria
        if matching_func is None: # use simple matching
            self.matching_func = is_in_list
        else:
            self.matching_func = matching_func
        self.matching_kwargs = matching_kwargs
        
        # Initialise set and list attributes
        self.thread_nums = set()
        self.closed_threads = set()
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
        yt_ids, closed_threads = self._scrape_catalog()
        new_ids = yt_ids.difference(self.yt_ids)
        self.yt_ids.update(new_ids)
        
        # Remove closed threads
        self.thread_nums -= closed_threads
        self.closed_threads.update(closed_threads)

        if verbose:
            print("Scraped {} new links from {} threads".format(
                    len(new_ids), len(self.thread_nums)),
                    "({} new threads added, {} closed threads removed)".format(
                        len(new_threads), len(closed_threads)))

    def _get_catalog(self):                                                   
        """ Retrieve an up-to-date JSON catalog of the 4chan board. """
        catalog_url = '/'.join(['https://a.4cdn.org', self.board,
                'catalog.json'])
        
        # Retrieve catalog
        catalog = None
        while not catalog:
            try:
                catalog = self._get_json_data(catalog_url)
            except URLError as e: # try again if connection reset by peer
                try:
                    if e.reason.errno == 104:
                        print('Connection reset error, waiting 5 minutes')
                        time.sleep(300)
                    else:
                        raise e
                except AttributeError:
                    raise e
                
        self.catalog = catalog

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
        
        Returns:
            yt_ids ::: set of video ids of scraped YouTube links
            closed_threads ::: set of numbers of closed/archived/404 threads
        """
        # Scrape links from each comment in each thread
        yt_ids = set()
        closed_threads = set()
        for thread_num in self.thread_nums:
            try:
                thread = self._get_thread(thread_num) # retrieve thread JSON
                yt_ids.update(self._scrape_thread(thread)) # scrape thread
                # Flag closed threads
                if thread['posts'][0].get('closed', False):
                    closed_threads.add(thread_num)
            except(HTTPError): # flag inaccesible threads
                closed_threads.add(thread_num)
        
        return yt_ids, closed_threads

    def _scrape_thread(self, thread):
        """ Return any YouTube links scraped from posts in `thread`. """
        # Extract posts
        yt_ids = set()
        for post in thread['posts']:
            # Skip undesirable posters
            if post.get('name', '') in self.bad_posters: 
                continue
            try:
                yt_ids.update(self._scrape_comment(post['com']))
            except(KeyError): # skip blank posts
                pass
        return yt_ids

    def _filter_catalog(self):
        """ Return thread numbers in catalog which meet matching criteria.
        """ 
        thread_nums = set()

        # Trawl through catalog for threads
        for page in self.catalog:                                               
            for thread in page['threads']:
                thread_no = int(thread['no'])
                subject = thread.get('sub', '')
                # Filter catalogs by subject
                if self.matching_func(subject, **self.matching_kwargs):
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

""" Helper functions """

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

def is_in_list(subject, subjects):
    return True if subject.lower() in subjects else False
