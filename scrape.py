"""
Kelly Stewart

Get data of all repos from Github and Bitbucket APIs
"""

import re

from json import loads
from urllib.request import Request, urlopen
from urllib.parse import urljoin

ITEMS_REQUIRED = 600

def read_json(response):
  return loads(response.read().decode())


def clean(repo, keys):
  for key in set(repo.keys()) - set(keys):
    del repo[key]


def github_repos(items_required, keys=["id", "name", "description"]):
  NEXT_LINK_PAT = re.compile(r'^<(.*?)>; rel="next"')
  PER_PAGE = 100

  url = "https://api.github.com/repositories?q=per_page=" + str(per_page)
  repos = []


  def next_page(repos, url):
    # get data from server
    req = Request(url)
    # explicitly request v3 version of the API
    req.add_header("Accept", "application/vnd.github.v3+json")
    response = urlopen(req)

    # parse the returned data and send to the total data set
    page = read_json(response)
    for repo in page:
      clean(repo, keys)
      repos.append(repo)

    # return the link required to access the next page
    return re.match(NEXT_LINK_PAT, response.getheader('Link')).group(1)

  # populate repos with the required number of entries
  # this assumes that the amount of entries specified per page will always be
  # the amount of entries given
  next_url = next_page(repos, url)
  for _ in range(PER_PAGE, items_required + 1, PER_PAGE):
    next_url = next_page(repos, next_url)

  return repos


def bitbucket_repos(items_required, keys=["uuid", "name", "description"]):
  """Return a cleaned list of Bitbucket repos"""
  URL = "https://api.bitbucket.org/2.0/repositories"
  items = 0
  repos = []

  def next_page(repos, url, items):
    # get data from server
    response = urlopen(url)

    # parse returned data and send to total data set
    page = read_json(response)
    for repo in page["values"]:
      clean(repo, keys)
      repos.append(repo)

    # return new number of entries, next url to follow
    return items + page["pagelen"], page["next"]


  # populate repos with required number of entries
  items, next_url = next_page(repos, URL, items)
  while items <= items_required:
    items, next_url = next_page(repos, URL, items)



bitbucket = bitbucket_repos(ITEMS_REQUIRED)
github = github_repos(ITEMS_REQUIRED)
