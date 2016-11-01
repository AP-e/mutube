# mutube
Scrape YouTube links from 4chan threads.

## Requires
At the moment, mutube is written in [Python 3](https://www.python.org/), but it can be easily ported to Python 2.7. The only dependency is the package BeautifulSoup ([`bs4`](https://www.crummy.com/software/BeautifulSoup/)), but this will be installed automatically by `pip`.

## Install (Linux)
Either download and unzip this repository, or clone it using git:

    $ git clone https://github.com/AP-e/mutube.git

`cd` into `mutube` and install using pip:

    $ pip install .
    
## Use
`muscrape` provides the class `Scraper`, which is initialised with:

- `board`: the abbreviation of the 4chan board to be scraped, e.g. `'mu'` or `'tv'`
- `subjects`: either:
  - a list of thread subjects to identify and scrape, e.g. `['kpop', '/kpop/' ,'kpop general']` (case-insensitive)
  - `None` to identify all threads in the catalog for scraping
  - an empty list (`[]`) to identify no threads for scraping
To manually add or remove threads for scraping (including those in the archive), modify the `thread_nums` attribute. The method `scrape()` processes every thread in `thread_nums`, searching for YouTube links in any form and storing their unique video ids in a set. This set of video ids can be found at the `yt_ids` attribute — save these an do as thou wilt.

## Examples
    >>> from mutube import Scraper
    
    >>> scraper = Scraper(board='mu', subjects=['/dark/']) # automatically detect /dark/ threads
    >>> scraper.scrape()
    Scraped 26 new links from 1 threads (1 new)
    >>> print(scraper.yt_ids)
    {'1JFQjmMU0wA', '12QrHHBHEOA', 'eFmqHiHMC1Q', 'UvlG4Y0KJws', '9NSBVjRxgF4', 'WlUH-ljj01o', 'GXpNenuQrcY', 'KFPI9b9N6CQ', 'IN-vbMeJBHA', 'qXlaJ87nOtk', 'T5JoaaQbtpU', 'RZd17cD9nZg', 'vq6M2oTB8gk', 'zWbAbIybfCQ', 'WCqaXfFJD9c', 'ALk3o7m5Jt8', 'GzJA1xQxTCU', 'q1xd7dxBqOw', 'Okr2Xds7qr8', '-0uvwjXqSLo', 'RvhtpfPvYas', 'bRv5MFipqwU', 'QkZ2rdbDHM4', 'jrL455ClTro', 'Qj6xUzvlvNg', 'UKAQ3EbRn_g'}
    
    >>> scraper = Scraper('mu', []) # 'empty' scraper
    >>> scraper.thread_nums.add(68780725) # manually add thread to scrape
    >>> scraper.scrape()
    Scraped 12 new links from 1 threads (0 new)

## Never Asked Questions
**Why are no threads being scraped?**

None of your `subjects` match any thread the board.

**Why are so many threads being scraped?**

You probably supplied a string as the `subjects` arguments, when it should be a list (i.e. use `subjects=['/metal/']` instead of `subjects='metal'`

**Why is there so much nonsense printed by `scrape()`?**

`BeautifulSoup` is a bit lippy, but it's easy to [suppress these warnings](https://docs.python.org/2/library/warnings.html#temporarily-suppressing-warnings).

**Why am I getting an HTTPError upon scraper *initialisation*?**

The board catalog cannot be reached. 4chan may be down, but it's more likely that you spelt the the board name wrongly.

**Why am I getting an HTTPError during *scraping*?**

A thread has been fallen out the archive or has been deleted. Sorry.
