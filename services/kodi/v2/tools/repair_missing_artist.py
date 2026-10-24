"""Bounded HP structural repair, not an artist-credit inference engine.

Kodi 21.3 MusicDatabase.cpp uses artist 1 / Artist Tag Missing when a song
has no artist credits. This restores only those missing required relations.
Live use requires stopped Kodi, private verified SQLite backup and a dry run.
"""
import hashlib
import json
import sqlite3

MISSING="""SELECT s.idSong FROM song s WHERE
 NOT EXISTS(SELECT 1 FROM song_artist sa WHERE sa.idSong=s.idSong AND sa.idRole=1)
 ORDER BY s.idSong"""


def digest(connection,table):
    # Hash every original field, including history, without exporting its data.
    assert table.replace('_','').isalnum()
    columns=[r[1] for r in connection.execute('PRAGMA table_info("'+table+'")')]
    order=','.join('"'+c.replace('"','""')+'"' for c in columns)
    rows=connection.execute('SELECT * FROM "'+table+'" ORDER BY '+order)
    h=hashlib.sha256()
    for row in rows:
        h.update(repr(row).encode());h.update(b'\n')
    return h.hexdigest()


def fingerprints(connection):
    tables=[r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    return {t:digest(connection,t) for t in tables}


def plan(connection,*,expected_count=23):
    artist=connection.execute('SELECT idArtist,strArtist,strMusicBrainzArtistID FROM artist WHERE idArtist=1').fetchone()
    if artist!=(1,'[Missing Tag]','Artist Tag Missing'):
        raise ValueError('canonical-missing-artist-not-verified')
    ids=tuple(r[0] for r in connection.execute(MISSING))
    if len(ids)!=expected_count or not ids:raise ValueError('unexpected-missing-link-count')
    for identity in ids:
        row=connection.execute('SELECT strArtistDisp,strArtistSort FROM song WHERE idSong=?',(identity,)).fetchone()
        if row not in (('',None),('','')):raise ValueError('nonempty-credit-needs-source-verification')
        if connection.execute('SELECT count(*) FROM song_artist WHERE idSong=?',(identity,)).fetchone()[0]:
            raise ValueError('secondary-credits-present')
        if connection.execute('SELECT count(*) FROM removed_link WHERE idMedia=? AND idArtist=1 AND idRole=1',(identity,)).fetchone()[0]:
            raise ValueError('trigger-would-change-existing-removed-link')
    return ids


def repair(connection,*,expected_count=23):
    if connection.in_transaction:raise ValueError('unexpected-existing-transaction')
    connection.execute('BEGIN IMMEDIATE')
    try:
        ids=plan(connection,expected_count=expected_count)
        before=fingerprints(connection)
        original_links=tuple(connection.execute('SELECT * FROM song_artist ORDER BY idSong,idArtist,idRole,iOrder,strArtist'))
        connection.executemany('INSERT INTO song_artist(idArtist,idSong,idRole,iOrder,strArtist) VALUES(1,?,1,0,?)',
                               ((identity,'[Missing Tag]') for identity in ids))
        if connection.execute(MISSING).fetchall():raise ValueError('missing-links-remain')
        after=fingerprints(connection)
        if any(before[t]!=after[t] for t in before if t!='song_artist'):
            raise ValueError('unrelated-data-changed')
        placeholders=','.join('?' for _ in ids)
        unchanged=tuple(connection.execute('SELECT * FROM song_artist WHERE idSong NOT IN ('+placeholders+') ORDER BY idSong,idArtist,idRole,iOrder,strArtist',ids))
        if unchanged!=original_links:raise ValueError('existing-links-changed')
        rows=connection.execute('SELECT idSong,idArtist,idRole,iOrder,strArtist FROM song_artist WHERE idSong IN ('+placeholders+') ORDER BY idSong',ids).fetchall()
        if rows!=[(i,1,1,0,'[Missing Tag]') for i in ids]:raise ValueError('repair-verification-failed')
        if connection.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('integrity-check-failed')
        connection.commit()
        return {'repaired_count':len(ids),'changed_table':'song_artist',
                'all_other_table_hashes_unchanged':True,'artist_credit':'unknown / canonical missing tag',
                'song_ids':list(ids),'before_hashes':before,'after_hashes':after}
    except BaseException:
        connection.rollback();raise
