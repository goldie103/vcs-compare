import os.path
import sqlite3
import json

from re import match, sub
from shutil import rmtree
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError
from config import *


def vprint(*args):
  """Print a string only if VERBOSE is true"""
  if VERBOSE:
    print(*args)


def add_repo(repo):
  """Add a repository to the database"""
  db.execute(
    # first value as NULL to force auto-incrementing id
    "INSERT INTO {} VALUES (NULL,{})".format(
      TABLE, ",".join(list("?"*(len(keys) - 1)))),
    # each value in the order they need to be added, excluding id
    [repo[i] for i in keys[1:]])


def clean_date(s):
  """Return a ISO8601 timestamp with everything after and including 'T' removed"""
  new_timestamp = ""
  for char in s:
    if char == 'T':
      break
    s += char
  return s


def clean_description(s):
  """Return a string with all newlines turned to spaces"""
  return s.replace("\n", " ")


def next_gh(url):

  # return a parsed response from a url
  def get_gh(url, retLink=False):
    url = sub("{/.+?}", "", url)
    vprint("  Requesting", url, "...")

    url = Request(url)
    # explicitly request v3 version of the API
    # make github like me :(
    url.add_header("Accept", "application/vnd.github.v3+json")
    url.add_header("User-Agent", "miscoined")
    # so secure
    url.add_header("Authorization", "token " + OAUTH_TOKEN)

    resp = urlopen(url)
    parsed = json.loads(resp.read().decode())
    if retLink:
      return match('<(.*?)>; rel="next"', resp.getheader('Link')).group(1), parsed
    return parsed

  link, page = get_gh(url, retLink=True)

  for info in page:
    # populate dictionary with data
    info = get_gh("{}/{}".format(GH_URL[:-7], info["full_name"]))
    repo = {i: info[i] for i in ["name","language"]}
    repo["forks"] = info["forks_count"]
    repo["size"] = info["size"] * 1024
    repo["description"] = clean_description(info["description"])
    repo["updated"] = clean_date(info["updated_at"])
    repo["created"] = clean_date(info["created_at"])
    # repo["commits"] = len(get_gh(info["commits_url"]))
    # repo["issues"] = len(get_gh(info["issues_url"]))
    repo["host"] = GH_HOST

    # add repo to the database
    add_repo(repo)

  return link


def next_bb(url):

  # return a parsed response from a url
  def get_bb(url):
    vprint("  Requesting", url, "...")
    return json.loads(urlopen(url).read().decode())

  resp = get_bb(url)
  link = resp["pagelen"]
  page = resp["values"]

  for info in page:
    # populate dictionary with data
    repo = {i: info[i] for i in ["language", "size", "name"]}
    repo["description"] = clean_description(info["description"])
    repo["created"] = clean_date(info["created_on"])
    repo["updated"] = clean_date(info["updated_on"])
    repo["forks"] = len(get_bb(info["links"]["forks"]["href"])["values"])
    # repo["commits"] = len(get_bb(info["links"]["commits"]["href"])["values"])
    # repo["issues"] = int(get_bb("{}/{}/issues".format(BB_URL, info["full_name"]))["count"])
    repo["host"] = BB_HOST

    # add dictionary to the database
    add_repo(repo)

  return link


def populate(isGH=True):
  """Populate the database with prepared data retrieved from the API"""

  ITEMS_REQUIRED = 600  # number of total repos to get
  PER_PAGE = 100
  host = GH_HOST if isGH else BB_HOST

  vprint("Populating", host)

  per_host = int(ITEMS_REQUIRED / 2) if not TESTING else PER_PAGE
  link = GH_URL if isGH else BB_URL + "?pagelen=" + str(PER_PAGE)
  count = 0
  retry_count = 0
  while count < per_host:

    try:
      link = next_gh(link) if isGH else next_bb(link)
    except URLError as e:
      retry_count += 1
      if retry_count <= 5:
        print(e)
        print("An error occured retrieving", link, "retrying...")
        continue
      else:
        print("Retried 5 times, stopping here.")
        break

    count += PER_PAGE

  vprint("Commiting database changes for", host, "...")
  db.commit()


def remove_existing():
  if os.path.isfile(DB_PATH):
    vprint("Removing existing", DB_PATH, "file...")
    os.remove(DB_PATH)


def create_table():
  db.execute("CREATE TABLE {} ({})".format(TABLE, ", ".join(COLS)))

vprint("\nBeginning db generation")

# remove any existing database
remove_existing()

vprint("Connecting to", DB_PATH, "file...")
db = sqlite3.connect(DB_PATH)
create_table()

keys = [i.split(" ")[0] for i in COLS] # keys to keep in each repo
populate()
populate(isGH=False)

db.close()
vprint("Database", DB_PATH, "has been fully populated.")
