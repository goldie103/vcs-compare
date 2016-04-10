from urllib.request import Request, urlopen

GITHUB_URL = "https://api.github.com"

req = Request(GITHUB_URL)
# explicitly request v3 version of the API
req.add_header("Accept", "application/vnd.github.v3+json")

response = urlopen(req)

print(response.read())
