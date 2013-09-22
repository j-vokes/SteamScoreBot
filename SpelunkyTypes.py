from datetime import datetime

class SpelunkyScore:
    def __init__(self, user, steamname, permalink, link, steamprofilelink):
      self.user = user
      self.steamname = steamname
      self.score = 0
      self.level = ""
      self.permalink = permalink
      self.link = link
      self.steamprofilelink = steamprofilelink
      self.date = datetime.today()
      self.valid = False

class SpelunkyPost:
    def __init__(self, postid, date, type):
      self.postid = postid
      self.date = date
      #Since enums don't exist natively in Python 3.3 (in 3.4 they do) we'll use ints as types.
      #0 = Tracked - Post gets updated when new scores are posted
      #1 = Untracked - Post has not been removed yet but will not be checked for updates
      #2 = Leaderboard - Post to complie scores from multiple days.
      self.type = type