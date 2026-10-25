"""Strict explicit News handoff; no runtime commands or I/O."""
from datetime import datetime
import math
import re


def request(args, source):
    if not args and source == 10000: return None
    if source != 11111 or len(args) != 4 or args[0] != 'news' or args[1] not in ('full', 'story'):
        raise ValueError('explicit-news-request-required')
    mode, position, generation = args[1:]
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', position): raise ValueError('invalid-news-position')
    position = float(position)
    if not math.isfinite(position) or not 0 <= position <= 14400: raise ValueError('invalid-news-position')
    if mode == 'full' and position != 0: raise ValueError('full-opening-required')
    if not re.fullmatch(r'[0-9TZ:.+\-]{10,40}', generation): raise ValueError('invalid-news-generation')
    if datetime.fromisoformat(generation.replace('Z', '+00:00')).tzinfo is None:
        raise ValueError('news-timezone-required')
    return dict(mode=mode, position=position, generation=generation)


def row_for(requested, snapshot):
    if requested is None: return None
    if requested['generation'] != snapshot.generated_at: raise ValueError('news-edition-changed')
    if requested['mode'] == 'full': return 0
    matches = [i for i, row in enumerate(snapshot.entries) if row.start == requested['position']]
    if len(matches) != 1: raise ValueError('news-story-not-found')
    return matches[0]
