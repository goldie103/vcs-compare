import os.path
import sqlite3
import json

from re import match
from shutil import rmtree
from urllib.parse import urlparse
from urllib.request import Request, urlopen

VERBOSE = True
TESTING = False

GH_HOST = "GH"
BB_HOST = "BB"

TABLE = "Repositories"
DB_PATH = "repositories.db"
COLS = ["id INTEGER PRIMARY KEY NOT NULL",
        "host TEXT NOT NULL",
        "name TEXT",
        "description TEXT"]
keys = [i.split(" ")[0] for i in COLS] # keys to keep in each repo


def vprint(*args):
  """Print a string only if VERBOSE is true"""
  if VERBOSE:
    print(*args)


def next_page(url, host):
  """Write a response to a file; return the next url and the number of items"""
  # file name is the last part of the url i.e. "repositories-per_page=100.txt"
  urlp = urlparse(url)
  fpath = os.path.join(host, "{}-{}.txt".format(os.path.basename(urlp.path),
                                                urlp.query, ".txt"))
  fexists = os.path.isfile(fpath)

  if fexists:
    os.remove(fpath)

  vprint("  Requesting", url, "...")
  req = Request(url)

  # explicitly request v3 version of the Github API
  if host == GH_HOST:
    req.add_header("Accept", "application/vnd.github.v3+json")

  resp = urlopen(req)
  page = resp.read().decode()

  with open(fpath, 'w') as f:
    f.write(page)

  # return the link to the next page
  if host == BB_HOST:
    link = json.loads(page)["next"]
  else:
    link = match('<(.*?)>; rel="next"', resp.getheader('Link')).group(1)
  return link


def populate(host):
  """Populate the folder with raw data retrieved from the API"""

  ITEMS_REQUIRED = 600  # number of total repos to get
  PER_PAGE = 100

  vprint("Populating", host)
  if host == GH_HOST:
    url = "https://api.github.com/repositories"  # Github API ignores per_page
  else:
    url = "https://api.bitbucket.org/2.0/repositories?pagelen=" + str(PER_PAGE)

  vprint("  Making new", host, "directory...")
  if os.path.isdir(host):
    rmtree(host)
  os.mkdir(host)

  per_host = int(ITEMS_REQUIRED / 2) if not TESTING else PER_PAGE
  link = url
  count = 0
  while count < per_host:
    link = next_page(link, host)
    count += PER_PAGE
  vprint("Finished populating", host)


def raw_gen():
  """Populate Github and Bitbucket repositories."""
  vprint("\nBeginning populating repositories")
  populate(GH_HOST)
  populate(BB_HOST)
  vprint("Finished populating repositories")


def create_db(path):
  """Return a database, removing existing databases if needed"""
  # remove any existing database
  if os.path.isfile(path):
    vprint("  Removing existing", path, "file...")
    os.remove(path)

  vprint("  Creating new", path, "file...")
  # connect and create the initial table
  db = sqlite3.connect(path)
  db.execute("CREATE TABLE {} ({})".format(TABLE, ", ".join(COLS)))
  return db


def read_host(host, db):
  """Read the contents of a host folder and add its repos"""
  vprint("Adding", host, "repositories...")
  files = os.listdir(host)
  for fpath in files:
    vprint("  Reading", fpath, "into database...")
    with open(os.path.join(host, fpath)) as f:
      page = json.loads(f.read())
      repos = page if host == GH_HOST else page["values"]
    for repo in repos:
      prep_repo(repo, host)
      add_repo(repo, db)
    vprint("Finished adding", host, "repositories")


def prep_repo(repo, host):
  """Remove unwanted keys and add the host"""
  # remove unwanted keys
  for key in set(repo.keys()) - set(keys):
    del repo[key]
  # add the host
  repo["host"] = host


def add_repo(repo, db):
  """Add a repository to the database"""
  db.execute(
    # first value as NULL to force auto-incrementing id
    "INSERT INTO {} VALUES (NULL,{})".format(
      TABLE, ",".join(list("?"*(len(keys) - 1)))),
    # each value in the order they need to be added, excluding id
    [repo[i] for i in keys[1:]])


def close_db(db):
  """Commit and close the database"""
  vprint("Committing database changes...")
  db.commit()
  db.close()


def db_gen():
  """Generate a database from host folders"""
  vprint("\nBeginning populating database", DB_PATH)
  db = create_db(DB_PATH)
  read_host(GH_HOST, db)
  read_host(BB_HOST, db)
  close_db(db)
  vprint("Finished populating database", DB_PATH)


raw_gen()
db_gen()
