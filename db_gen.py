"""
Kelly Stewart

Build a SQL database of a Github and Bitbucket repositories
"""

import sqlite3
import os.path

from re import match
from json import loads as json_loads
from urllib.request import Request, urlopen

FORCE_RAW_GEN = False # whether to generate raw data even if it already exists
VERBOSE = True

GH_HOST = "GH"
GH_URL = "https://api.github.com/repositories?q=per_page=100"
GH_FILE = "github.txt"
BB_HOST = "BB"
BB_URL = "https://api.bitbucket.org/2.0/repositories"
BB_FILE = "bitbucket.txt"

ITEMS_REQUIRED = 600
items_per_host = int(ITEMS_REQUIRED / 2)
COLS = ["id INTEGER PRIMARY KEY NOT NULL", "host TEXT NOT NULL"]
VAR_COLS = ["name TEXT", "description TEXT"]

TABLE_NAME = "Repositories"
DB_PATH = "repositories.db"

RAW_DIR = "raw"

if not os.path.isdir: os.mkdir(RAW_DIR)

# remove any existing database
if os.path.isfile(DB_PATH):
  if VERBOSE: print("Removing existing database file...")
  os.remove(DB_PATH)

if VERBOSE: print("Creating new database file '{}'...".format(DB_PATH))
# connect and create the initial table
db = sqlite3.connect(DB_PATH)
db.execute("CREATE TABLE Repositories ({})".format(", ".join(COLS + VAR_COLS)))


def add_repo(repo, host):
  """Clean an entry and add it to the database

  Clean by removing unwanted keys, assuming wanted keys are only those in VAR_COLS
  also add a column specifying the host.
  """

  # remove unwanted keys
  for key in set(repo.keys()) - set(i.split(" ")[0] for i in VAR_COLS):
    del repo[key]

  # add a key specifying the host
  repo["host"] = host
  # add entry into database
  query = "INSERT INTO {} VALUES (NULL,{})".format(
    TABLE_NAME, ",".join(list("?"*len(repo))))
  # get a list of each value in the order they need to be passed to the query
  ordered_values = [repo[i.split(" ")[0]] for i in COLS[1:] + VAR_COLS]
  db.execute(query, ordered_values)


def next_page(url, host):
  """Return the items in this page and the link to the next.

  Also add this page's repos to the database."""
  req = Request(url)
  
  # explicitly request v3 version of the Github API
  if host == GH_HOST:
    req.add_header("Accept", "application/vnd.github.v3+json")

  response = urlopen(req)
  # parse the response from json
  if os.path.isfile(os.join(RAW_DIR, GH_FILE)):
    if FORCE_RAW_GEN: os.remove(os.join)
  with open(os.path.join(RAW_DIR, url + ".txt"), 'a') as f:
    d
  page = json_loads(response.read().decode())

  if host == GH_HOST:
    items = 100       # assume Github will always return the max items possible
    link = match('<(.*?)>; rel="next"', response.getheader('Link')).group(1)
    repos = page
  else:
    items = page["pagelen"]
    link = page["next"]
    repos = page["values"]

  for repo in repos:
    add_repo(repo, host)

  return items, link


def populate(url, host):
  """Populate the database with the required number of entries"""
  item_count, link = next_page(url, host)
  items = item_count
  while items <= items_per_host:
    if VERBOSE: print("Populated", items, link)
    item_count, link = next_page(link, host)
    items += item_count



if VERBOSE: print("Populating Github repositories from", GH_URL)
populate(GH_URL, GH_HOST)
if VERBOSE: print("Populating Bitbucket repositories from", BB_URL)
populate(BB_URL, BB_HOST)


if VERBOSE: print("Committing database changes...")
db.commit()
db.close()

print("Finished. Populated database is '{}'".format(DB_PATH))
