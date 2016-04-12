import sqlite3


# will change these to import from other python file when refactoring into
# proper OOP structure
DB_PATH = "repositories.db"
TABLE = "Repositories"

db = sqlite3.connect(DB_PATH)

def most_common_names(host):
  """Return the names that occur most often for this host"""
  names = db.execute(
    "SELECT COUNT(name), name FROM {} WHERE host=? GROUP BY name".format(TABLE),
    (host,)).fetchall()
  names.sort(reverse=True)
  highest = names[0][0]
  common_names = []
  for count, name in names:
    if count == highest:
      common_names.append(name)
    else:
      break
  return common_names

def search_description(host, s):
  """Return entries with the description matching a SQL regex"""
  descriptions = db.execute(
    "SELECT description FROM {} WHERE description LIKE ?".format(TABLE),
    ("%" + s + "%",)).fetchall()
  return len(descriptions), [i[0] for i in descriptions]


names = most_common_names("BB")
print("The most common repository names on Bitbucket are:")
print(*names, sep=", ")

for i in names:
  count, descriptions = search_description("GH", i)
  print("There are {} repositories with a description containing {}:".format(
    count, i))
  print(*descriptions, sep="\n\n", end="\n\n\n")

