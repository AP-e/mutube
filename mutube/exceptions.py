""" exceptions """

class NoTag(ValueError):
    """ When no tag is found in a string. """
    pass

class NoPlaylist(ValueError):
    """ When no matching playlist is found. """
    pass

class BadVideo(ValueError):
    """ When the YouTube video id does not lead to a real video """
    pass
