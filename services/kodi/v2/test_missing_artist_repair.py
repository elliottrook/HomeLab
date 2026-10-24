import sqlite3
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).parent/'tools'))
from repair_missing_artist import fingerprints,plan,repair


class MissingArtistTests(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:')
        self.c.executescript('''CREATE TABLE artist(idArtist INTEGER,strArtist TEXT,strMusicBrainzArtistID TEXT);
        CREATE TABLE song(idSong INTEGER,strArtistDisp TEXT,strArtistSort TEXT,iTimesPlayed INTEGER,lastplayed TEXT);
        CREATE TABLE song_artist(idArtist INTEGER,idSong INTEGER,idRole INTEGER,iOrder INTEGER,strArtist TEXT);
        CREATE TABLE removed_link(idArtist INTEGER,idMedia INTEGER,idRole INTEGER);
        INSERT INTO artist VALUES(1,'[Missing Tag]','Artist Tag Missing');
        INSERT INTO song VALUES(10,'',NULL,8,'yesterday');
        INSERT INTO song VALUES(20,'Known',NULL,3,'today');
        INSERT INTO song_artist VALUES(2,20,1,0,'Known');
        CREATE TRIGGER t AFTER INSERT ON song_artist BEGIN
        DELETE FROM removed_link WHERE idArtist=NEW.idArtist AND idMedia=NEW.idSong AND idRole=NEW.idRole;END;''')

    def tearDown(self):self.c.close()

    def test_repairs_only_unknown_placeholder_link_and_preserves_every_other_table(self):
        before=fingerprints(self.c);result=repair(self.c,expected_count=1)
        self.assertEqual(result['repaired_count'],1)
        self.assertEqual(self.c.execute('SELECT * FROM song WHERE idSong=10').fetchone(),(10,'',None,8,'yesterday'))
        after=fingerprints(self.c)
        self.assertTrue(all(before[t]==after[t] for t in before if t!='song_artist'))

    def test_nonempty_credit_is_not_replaced_with_unknown(self):
        self.c.execute("UPDATE song SET strArtistDisp='Unverified' WHERE idSong=10");self.c.commit()
        with self.assertRaisesRegex(ValueError,'source-verification'):repair(self.c,expected_count=1)
        self.assertEqual(self.c.execute('SELECT count(*) FROM song_artist').fetchone()[0],1)

    def test_modified_placeholder_and_unexpected_count_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'count'):plan(self.c)
        self.c.execute("UPDATE artist SET strArtist='Real person'");self.c.commit()
        with self.assertRaisesRegex(ValueError,'canonical'):repair(self.c,expected_count=1)

    def test_trigger_side_effect_is_refused(self):
        self.c.execute('INSERT INTO removed_link VALUES(1,10,1)');self.c.commit()
        with self.assertRaisesRegex(ValueError,'trigger'):repair(self.c,expected_count=1)
        self.assertEqual(self.c.execute('SELECT count(*) FROM removed_link').fetchone()[0],1)

    def test_secondary_credit_is_not_overwritten(self):
        self.c.execute("INSERT INTO song_artist VALUES(2,10,2,0,'Composer')");self.c.commit()
        with self.assertRaisesRegex(ValueError,'secondary'):repair(self.c,expected_count=1)


if __name__=='__main__':unittest.main()
