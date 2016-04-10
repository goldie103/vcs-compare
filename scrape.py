import json
import re

from urllib.request import Request, urlopen
from urllib.parse import urljoin

ITEMS_REQUIRED = 600
NEXT_LINK_PAT = re.compile(r'^<(.*?)>; rel="next"')
DESIRED_COLS = ["id", "fork", "name"]

github_initial_url = "https://api.github.com/repositories?q=per_page=" + str(GITHUB_PER_PAGE)

repos = []

def cleaned(repo):
  return {i: repo[i] for i in repo if i in DESIRED_COLS}

def next_page(repos, url):
  req = Request(url)
  # explicitly request v3 version of the API
  req.add_header("Accept", "application/vnd.github.v3+json")

  response = urlopen(req)

  link_next = re.match(NEXT_LINK_PAT, response.getheader('Link')).group(1)

  # parse the returned data from json
  page = json.loads(response.read().decode())

  for repo in page:
    repos.append(cleaned(repo))

  return link_next


# populate repos with the required number of entries
next_url = next_page(repos, github_initial_url)
for _ in range(GITHUB_PER_PAGE, ITEMS_REQUIRED + 1, GITHUB_PER_PAGE):
  next_url = next_page(repos, next_url)


print(repos[:50])
