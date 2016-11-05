""" compat
Variations in importing for python 2/ 3
"""

try: # python 3.x
    from urllib.request import urlopen
    from urllib.parse import urlparse, parse_qs
    from urllib.error import HTTPError

except(ImportError): # python 2.x
    from urllib2 import urlopen, urlparse, HTTPError
    from urlparse import parse_qs

