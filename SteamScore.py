import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import math
import socket


def populateScores(scores, date):
    #Get the root Spelunky leaderboard page
    directoryTree = getXML('http://steamcommunity.com/stats/247080/leaderboards/?xml=1')
    root = directoryTree.getroot()
    #Find the link to today's leaderboard
    for leaderboard in root.findall("leaderboard"):
        if '{d.day}/{d.month}/{d.year}'.format(d=date) in leaderboard.find('name').text:
            correctBoard = leaderboard.find('url').text
            break
            
    leaderboardTree = getXML(correctBoard)
    root = leaderboardTree.getroot()
    for score in scores:
        #If we already have their steam name and steam ID we can just move on
        if score.steamname and score.steamid:
            continue
        #If the SteamID was given then let's get their "Steam Name"
        elif score.steamid:
            steamPageTree = getXML('http://steamcommunity.com/profiles/'+score.steamid+'?xml=1')
            try:
                score.steamname = steamPageTree.find('steamID').text
            except:
                continue
        #Else let's try get their Steam ID from their name.                
        else:
            steamName = score.steamname
            steamPageTree = getXML('http://steamcommunity.com/id/'+steamName+'?xml=1')
            try:
                score.steamid = steamPageTree.find('steamID64').text
            except:
                continue

    resultscores = [];
    #From the leaderboard start filling in scores.
    for entry in root.find("entries"):
        for i, score in enumerate(scores):
            if score.steamid is "":
                continue
            if score.steamid in entry.find('steamid').text:
                score.score = int(entry.find('score').text)
                score.level = getLevel(entry.find('details').text)
                score.steamprofilelink = "http://steamcommunity.com/profiles/"+score.steamid
                score.date = date
                score.valid = True
                score.rank = int(entry.find('rank').text)
                resultscores.append(score)
                del scores[i]
                break

    return resultscores

def getXML(page):
    for attempt in range(5):
        try:
            returnpage = ET.parse(urllib.request.urlopen(page, timeout=10))
        except socket.timeout:
            print("Timed out!", attempt, page)
            continue
        except urllib.error.URLError:
            print("Timed out!", attempt, page)
            continue
        except ET.ParseError:
            return ""
        except Exception as inst:
            print(page)
            print(type(inst))     #Default catch. Print it to track in the future.
        break
    else:
        print('Page timed out too many times.')
        return ""
    return returnpage

def getLevel(details):
    for i, num in enumerate(details):
        if i == 1:
            world = num
        if i == 9:
            stage = num
    return str(world)+"-"+str(stage)
