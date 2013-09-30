import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import SpelunkyTypes
import math
import re
from datetime import date
import socket


def populateScores(scores, date):
    #Get the root Spelunky leaderboard page
    directoryTree = getXML('http://steamcommunity.com/stats/239350/leaderboards/?xml=1')
    root = directoryTree.getroot()
    #Find the link to today's leaderboard
    for leaderboard in root.findall("leaderboard"):
        if date.strftime("%m/%d/%Y") in leaderboard.find('name').text:
            correctBoard = leaderboard.find('url').text
            break
            
    leaderboardTree = getXML(correctBoard)
    root = leaderboardTree.getroot()
    for i, score in enumerate(scores):
        #If we already have their steam name and steam ID we can just move on
        if score.steamname and score.steamid:
            pass
        #If the SteamID was given then let's get their "Steam Name"
        elif score.steamid:
            steamPageTree = getXML('http://steamcommunity.com/id/'+score.steamid+'?xml=1')
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
        #From the leaderboard start filling in scores.
        for entry in root.find("entries"):
            if score.steamid in entry.find('steamid').text:
                score.score = int(entry.find('score').text)
                score.level = getLevel(entry.find('details').text)
                score.steamprofilelink = "http://steamcommunity.com/profiles/"+score.steamid
                score.date = date
                score.valid = True
                break

    return scores

def getXML(page):
    for attempt in range(3):
        try:
            print(page)
            returnpage = ET.parse(urllib.request.urlopen(page, timeout=5))
        except socket.timeout:
            #print("Timed out!", attempt)
            continue
        except ElementTree.ParseError:
            return ""
        except Exception as inst:
            print(page)
            print(type(inst))     #Default catch. Print it to track in the future.
        break
    else:
        raise NameError('Page timed out too many times. Try again later :(')
    return returnpage

def getLevel(details):
    for i, num in enumerate(details):
        if i == 8:
            part1 = num
        if i == 9:
            part2 = num

    rawLevel = int(part1+part2, 16)
    world = int(math.ceil(rawLevel / 4))
    stage = int(rawLevel % 4)
    if stage == 0:
        stage=4
    return str(world)+"-"+str(stage)
