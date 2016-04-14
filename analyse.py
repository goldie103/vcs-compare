import sqlite3

from config import *


db = sqlite3.connect(DB_PATH)

def db_exec(query, format_args=None, *exec_args):
  """Return a Cursor object from executing a db query"""
  return db.execute(query.format(TABLE if format_args is None else format_args),
                    tuple(exec_args))

def max_row(col):
  """Return a row containing the maximum value of a column"""
  return db.execute("SELECT * FROM {} ORDER BY ? DESC".format(TABLE), (col,)).fetchone()


def most_common_names(host):
  """Return the names that occur most often for this host"""
  names = db.execute(
    """SELECT COUNT(name), name
    FROM {}
    WHERE host=?
    GROUP BY name
    ORDER BY COUNT(name) DESC""".format(TABLE),
    (host,)).fetchall()
  highest = names[0][0]
  common_names = []
  for count, name in names:
    if count != highest:
      break
    common_names.append(name)

  return common_names


def search_description(host, s):
  """Return entries with the description containing a string"""
  descriptions = db.execute(
    "SELECT description FROM {} WHERE description LIKE ?".format(TABLE),
    ("%" + s + "%",)).fetchall()
  return len(descriptions), [i[0] for i in descriptions]


names = most_common_names("BB")
print("The most common repository names on Bitbucket are:")
print(*names, sep=", ")

for i in names:
  count, descriptions = search_description("GH", i)
  if count == 0:
    continue
  print("\nThere are {} repositories with a description containing {}:".format(
    count, i))
  for i in descriptions:
    print('"{}"'.format(i))

