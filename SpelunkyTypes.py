from datetime import datetime

class SpelunkyUser:
    def __init__(self, steamname, steamid):
      self.steamname = steamname
      self.steamid = steamid

class SpelunkyScore:
    def __init__(self, user, steamname, permalink, link, steamid):
      self.user = user
      self.steamname = steamname
      self.score = 0
      self.level = ""
      self.permalink = permalink
      self.link = link
      self.steamid = steamid
      self.date = datetime.today()
      self.valid = False
      self.commentText = ""

class SpelunkyPost:
    def __init__(self, postid, date, type):
      self.postid = postid
      self.date = date
      #Since enums don't exist natively in Python 3.3 (in 3.4 they do) we'll use ints as types.
      #0 = Tracked - Post gets updated when new scores are posted
      #1 = Semi-tracked - Poat is not authored by bot but will be tracked
      #2 = Leaderboard - Post to complie scores from multiple days.
      self.type = type