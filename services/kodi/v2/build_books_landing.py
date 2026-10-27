"""Build the exact-successor HP Books recommendation landing."""
import argparse,ast,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from books_hero_ui import extend_books_data,extend_home,extend_includes

HERE=Path(__file__).resolve().parent
EXPECTED={
 'hub_feeds.py':'07296c7987b0383b9c5134b9ea72368d5d30604eef7beae686f30e558a79ff58',
 'refresh_books.py':'c7c0f856ac3b158ecc464411f7854c5826994217120b12b9c8b6e88487a9f55f',
 'books_data.py':'079dd4d66486877dfd7dd52dbdb7dda15b591c57567470a0f7b8ccc5b81943de',
 'IncludesBooks.xml':'2fefdd5bbbe08ee53d392ad2e9a126c3f187e504ee33a921ac5702de80f34973',
 'custom_1110_books.xml':'77666f780e53e72e75ad1cc0a935294ae07016bbfcff50c3564eef9cbc15c005'}
TARGET={
 'hub_feeds.py':'tools/hub_feeds.py','refresh_books.py':'tools/refresh_books.py',
 'books_data.py':'tools/books_data.py','IncludesBooks.xml':'1080i/IncludesBooks.xml',
 'custom_1110_books.xml':'1080i/custom_1110_books.xml'}
SKIN='.kodi/addons/skin.asterhome/'

def sha(value):
 return hashlib.sha256(value if isinstance(value,bytes) else Path(value).read_bytes()).hexdigest()
def raw(value):return (json.dumps(value,indent=2)+'\n').encode()

def build(snapshot,output):
 snapshot,output=Path(snapshot),Path(output)
 if output.exists():raise ValueError('immutable-books-landing-output')
 sources={}
 for name,digest in EXPECTED.items():
  data=(snapshot/name).read_bytes()
  if sha(data)!=digest:raise ValueError('books-landing-predecessor:'+name)
  sources[name]=data
 files={
  'tools/hub_feeds.py':(Path('services/kodi/skin.asterhome/tools/hub_feeds.py')).read_bytes(),
  'tools/refresh_books.py':(Path('services/kodi/skin.asterhome/tools/refresh_books.py')).read_bytes(),
  'tools/books_data.py':extend_books_data(sources['books_data.py']),
  '1080i/IncludesBooks.xml':extend_includes(sources['IncludesBooks.xml']),
  '1080i/custom_1110_books.xml':extend_home(sources['custom_1110_books.xml']),
  'tools/books_landing.py':(HERE/'books_landing.py').read_bytes()}
 output.mkdir(parents=True)
 records=[]
 before={TARGET[name]:digest for name,digest in EXPECTED.items()}
 for name,data in sorted(files.items()):
  if name.endswith('.py'):ast.parse(data)
  else:ET.fromstring(data)
  target=output/'payload'/SKIN/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  records.append(dict(path=SKIN+name,sha256=sha(data),bytes=len(data),before_sha256=before.get(name)))
 manifest=dict(schema=1,kind='hp-owned-books-landing',files=records,
  prerequisite={SKIN+'tools/owned_landing.py':'915dc1773e29bc2ca812930ca4b2434890747eddbdf59673e79774af37305326'},
  feed='.kodi/userdata/addon_data/skin.asterhome/feeds/books.json')
 helpers={'books_landing_install.py':HERE/'books_landing_install.py',
          'deploy_books_landing.py':HERE/'tools/deploy_books_landing.py',
          'digest_news_install.py':HERE/'digest_news_install.py'}
 manifest['helpers']={}
 for name,source in helpers.items():
  data=source.read_bytes();(output/name).write_bytes(data);manifest['helpers'][name]=sha(data)
 (output/'manifest.json').write_bytes(raw(manifest));return sha(raw(manifest))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 print(build(a.snapshot,a.output))
