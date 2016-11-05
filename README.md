# mutube
Scrape YouTube links from 4chan threads.

## Requires
[Python (2.7 or 3.x)](https://www.python.org/) with the BeautifulSoup package ([`bs4`](https://www.crummy.com/software/BeautifulSoup/), will be installed automatically by `pip`).

## Install (Linux)
Either download and unzip this repository, or clone it using git:

    $ git clone https://github.com/AP-e/mutube.git

`cd` into `mutube` and install using pip:

    $ pip install .
    
## Use
`muscrape` provides the class `Scraper`, which is initialised with:

- `board`: the abbreviation of the 4chan board to be scraped, e.g. `'mu'` or `'tv'`
- `subjects`: either:
  - a list of thread subjects to identify and scrape (e.g. `['kpop', '/kpop/' ,'kpop general']`, case-insensitive)
  - `None` to identify all threads in the catalog for scraping
  - an empty list (`[]`) to identify no threads for scraping
- `bad_posters`: optional list of names of posters to ignore (e.g. `['Hampus', 'Biotroll']`)

To manually add or remove threads for scraping (including those in the archive), modify the `thread_nums` attribute. The method `scrape()` searches for YouTube links in every thread in `thread_nums` — inaccessible threads are transferred to the `dead_threads` attribute — storing a set of their unique video ids in `yt_ids` attribute. Store these as-is, or use the `generate_links()` method to output these as valid YouTube urls.

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
    >>> print(scraper.generate_links()) # get yt_ids as a list of YouTube links
    ['https://www.youtube.com/watch?v=V9Ty3YnWN80', 'https://www.youtube.com/watch?v=aGQECkbhpow', 'https://www.youtube.com/watch?v=Ytyw1PC0m80', 'https://www.youtube.com/watch?v=mvPIvoJkmGs', 'https://www.youtube.com/watch?v=NR7_TbMIVnA', 'https://www.youtube.com/watch?v=Jx2fp-kKOIw', 'https://www.youtube.com/watch?v=6tiq9rzQp-I', 'https://www.youtube.com/watch?v=ejAEx_kWmko', 'https://www.youtube.com/watch?v=5eZ_TgE3x_A', 'https://www.youtube.com/watch?v=2EkzNGkIPdE', 'https://www.youtube.com/watch?v=JzRTzj7YEh4', 'https://www.youtube.com/watch?v=VoQzuWyz08M']

## Never Asked Questions
**Why are no threads being scraped?**

None of your `subjects` match any thread the board.

**Why are so many threads being scraped?**

You probably supplied a string as the `subjects` arguments, when it should be a list (i.e. use `subjects=['/metal/']` instead of `subjects='metal'`

**Why is there so much nonsense printed by `scrape()`?**

`BeautifulSoup` is a bit lippy, but it's easy to [suppress these warnings](https://docs.python.org/2/library/warnings.html#temporarily-suppressing-warnings).

**Why am I getting an HTTPError **

The board catalog cannot be reached. It may be that 4chan is down, though it's more likely that you spelt the the board name wrongly.
