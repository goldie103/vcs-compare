"""
Kelly Stewart

Build a SQL database of a Github and Bitbucket repositories
"""

import sqlite3

from re import match
from json import loads as json_loads
from urllib.request import Request, urlopen

GH_HOST = "GH"
GH_URL = "https://api.github.com/repositories?q=per_page=100"
BB_HOST = "BB"
BB_URL = "https://api.bitbucket.org/2.0/repositories"

ITEMS_REQUIRED = 600
COLS = ["name TEXT NOT NULL", "description TEXT"]

# connect and create the initial table
db = sqlite3.connect("repositories.db")
db.execute("""CREATE TABLE Repositories
(id INTEGER PRIMARY KEY, host TEXT NOT NULL, ?)""", ", ".join(COLS))


def add_repo(repo, host):
  """Clean an entry and add it to the database

  Clean by removing unwanted keys, assuming wanted keys are only those in COLS
  also add a column specifying the host.
  """

  # remove unwanted keys
  for key in set(repo.keys()) - set(i.split(" ")[0] for i in COLS):
    del repo[key]
  # add a key specifying the host
  repo["host"] = host

  # add entry into database
  db.executemany("INSERT INTO Repositories VALUES (?,?,?)", repo.items())


def next_page(url, host):
  """Return the items in this page and the link to the next.

  Also add this page's repos to the database."""
  req = Request(url)

  # explicitly request v3 version of the Github API
  if host == GH_HOST:
    req.add_header("Accept", "application/vnd.github.v3+json")

  # parse the response from json
  page = json_loads(urlopen(req).read().decode())

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
  while items <= ITEMS_REQUIRED:
    item_count, link = next_page(link, host)
    items += item_count



populate(GH_URL, GH_HOST)
populate(BB_URL, BB_HOST)

db.commit()
db.close()
