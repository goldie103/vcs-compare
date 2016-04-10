import re

from json import loads
from urllib.request import Request, urlopen
from urllib.parse import urljoin

ITEMS_REQUIRED = 600

def read_json(response):
  return loads(response.read().decode())


def clean(repo, wanted):
  for key in set(repo.keys()) - set(wanted):
    del repo[key]


def github_repos(items_required):
  NEXT_LINK_PAT = re.compile(r'^<(.*?)>; rel="next"')
  PER_PAGE = 100
  DESIRED_KEYS = ["id", "name", "description"]

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
      clean(repo, DESIRED_KEYS)
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


URL = "https://api.bitbucket.org/2.0/repositories"
items = 0
repos = []

def next_page(repos, url, items):
  DESIRED_KEYS = ["uuid", "name", "description"]
  # get data from server
  response = urlopen(url)

  # parse returned data and send to total data set
  page = read_json(response)
  for repo in page["values"]:
    clean(repo, DESIRED_KEYS)
    repos.append(repo)

  return items + page["pagelen"], page["next"]


items, next_url = next_page(repos, URL, items)
while items <= ITEMS_REQUIRED:
  items, next_url = next_page(repos, URL, items)
