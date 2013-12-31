import re

def parse_markup(text):
    # Replace mentions with links to the mentioned entity.
    mention_re = re.compile('''
        @\[
        (?P<mention>[^]]+)\]
        \((?P<type>[a-z]+):
        (?P<id>[a-z0-9]+)\)
    ''', re.VERBOSE)
    text = mention_re.sub('<a href="/\g<type>s/\g<id>">\g<mention></a>', text)

    # Add markup for flags.
    flag_re = re.compile('%(?P<flag>[^\s]+)')
    return flag_re.sub('<span class="flag">\g<flag></span> ', text).strip()

def ago(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc

    From: http://stackoverflow.com/a/1551394
    """
    from datetime import datetime
    now = datetime.utcnow()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time 
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"

from user import User
from comment import Comment
from event import Event
from issue import Issue
from project import Project
