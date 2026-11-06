#!/usr/bin/env python3
"""Add existing digest story artwork metadata to the v3 player list."""


def add_story_art(source: str) -> str:
    old = """            item.setProperty('Clock', clock(row.start))
            item.setProperty('Active', 'false')
            control.addItem(item)
"""
    new = """            item.setProperty('Clock', clock(row.start))
            item.setProperty('Source', row.source)
            item.setProperty('Active', 'false')
            item.setArt({'thumb': row.image or 'special://skin/media/30-aster-news-logo.png'})
            control.addItem(item)
"""
    if source.count(old) != 1:
        raise ValueError('digest-story-art-baseline-drift')
    return source.replace(old, new)
