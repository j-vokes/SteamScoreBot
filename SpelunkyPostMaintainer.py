#Maintains Posts
import praw
from SpelunkyTypes import SpelunkyScore, SpelunkyPost, SpelunkyUser
import configparser
import sys
import re
import SteamScore
import pickle
from datetime import date, timedelta

def main():
    #Read Config file
    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    #Read Banned User List file
    with open(config['Banned Users']['filename']) as f:
        bannedUsers = f.readlines()

    #Login
    r = praw.Reddit('Spelunky Daily Submission Maintainer by u/Avagad')
    r.login(config['User']['username'], config['User']['password'])

    #Get saved posts
    with open(config['Subreddit']['postdata'], "rb") as f:
        postdata = pickle.load(f)

    #Keep track of every score we read.        
    totalScores = []
    #Keep track of users' steam names and IDs so we don't have to search each time if a user submits scores over multiple days
    trackedusers = dict()
    #We'll go through all the dailies and collect all the scores and the dates they were from
    for post in (scoreposts for scoreposts in postdata if scoreposts.type==0):        
        print("Post ID:",post.postid,"Date:",post.date,"Type:",post.type)
        submission = r.get_submission(submission_id=post.postid)
    
        scores = getScores(submission, bannedUsers)

        #Fill out scores with extra info from our tracked users
        for score in scores:
            if trackedusers.get(score.user):
                score.steamid = trackedusers.get(score.user).steamid
                score.steamname = trackedusers.get(score.user).steamname

        scores = SteamScore.populateScores(scores, post.date)
        #Keep track of all scores
        for score in scores: totalScores.append(score)

        #Add users to our tracked users
        for score in scores:
            if score.user not in trackedusers:
                if score.steamname and score.steamid:
                    trackedusers[score.user] = SpelunkyUser(score.steamname,score.steamid)
        
        orderedScores = sortScores(scores, config['Sort']['type'])
                
        #Update Main post
        submissionBody = str(config['Daily Post']['bodytext']).replace("\\n","\n")
        submissionBody += createLine()
        submissionBody += createSubmissionTemplate()
        submissionBody += createLine()
        for comppost in postdata:
            timediff = post.date - comppost.date 
            if comppost.type==2 and timediff >= timedelta(0) and timediff < timedelta(days = 7):
                submissionBody += "[Weekly Post!](http://www.reddit.com/r/"+config['Subreddit']['name']+"/comments/"+comppost.postid+"/)"+"\n\n"
        submissionBody += createLine()
        submissionBody += createInitialTable(False)

        for position, score in enumerate(orderedScores, start=1):
            submissionBody += createScoreLine(score, position, False)

        submissionBody += createAuthorString()
        if submission.selftext.replace("amp;","") != submissionBody:
            submission.edit(submissionBody)

    #We'll go through any posts that were created by other people (we're not the author) that we want to track
    for post in (scoreposts for scoreposts in postdata if scoreposts.type==1):        
        print("Post ID:",post.postid,"Date:",post.date,"Type:",post.type)
        submission = r.get_submission(submission_id=post.postid)

        scores = getScores(submission, bannedUsers)

        #Fill out scores with extra info from our tracked users
        for score in scores:
            if trackedusers.get(score.user):
                score.steamid = trackedusers.get(score.user).steamid
                score.steamname = trackedusers.get(score.user).steamname

        scores = SteamScore.populateScores(scores, post.date)
        #Keep track of all scores
        for score in scores: totalScores.append(score)

        #Add users to our tracked users
        for score in scores:
            if score.user not in trackedusers:
                if score.steamname and score.steamid:
                    trackedusers[score.user] = SpelunkyUser(score.steamname,score.steamid)
                
        #Can't update Main post

    #Now that we've updated all the dailes and have a list of the scores they contain we'll update the compilation posts
    for comppost in (scoreposts for scoreposts in postdata if scoreposts.type==2):
        print("Post ID:",comppost.postid,"Date:",comppost.date,"Type:",comppost.type)
        #Now update leaderboard post
        totalcopy = totalScores[:]
        orderedScores = sortScores(totalcopy, config['Sort']['type'])
        
        submission = r.get_submission(submission_id=comppost.postid)
        #Update Main post
        submissionBody = str(config['Weekly Post']['bodytext']).replace("\\n","\n")
        submissionBody += createLine()
        submissionBody += createInitialTable(True)

        #Use the "for in generator" method we've used previously
        for position, score in enumerate((scores for scores in orderedScores if ((scores.date - comppost.date) < timedelta(days=7) and (scores.date - comppost.date) >= timedelta(0))), start=1):
            if position <= 25:
                submissionBody += createScoreLine(score, position, True)
            else:
                break

        submissionBody += createAuthorString()
        if submission.selftext.replace("amp;","") != submissionBody:
            submission.edit(submissionBody)

def getScores(submission, bannedUsers):
    flat_comments = praw.helpers.flatten_tree(submission.comments)
    scores = []
    authors = set()
    #Get Scores from comments - Make sure it's a top comment too
    for comment in (topcomments for topcomments in flat_comments if topcomments.is_root):
        #User
        try: #So PRAW tries to read deleted comments then freaks out when there's nothing to be read...
            user = comment.author.name
        except:
            continue #If I can't even read the username then forget that post and move on!
        if str(user) in bannedUsers:
            continue
        elif str(user) in authors:
            continue
        else:
            authors.add(str(user))
            

        #Steam Name
        steamName = ""
        steamid = ""
      
        #First search for the 17 digit SteamID
        try:
            steam17ID = re.search(r'\d{17}', comment.body).group(0)
        except:
            steam17ID = ""
         #Search for the STEAM_X:Y:Z version    
        try:
            steamIDText = re.search(r'\d\:[0|1]\:\d*', comment.body).group(0)
        except:
            steamIDText = ""
        if steam17ID:
            steamid = steam17ID
        elif steamIDText:
            steamid = str(get64ID(steamIDText))
        
        if not steamid:
            #Get the right line
            correctLine = re.search(r'(?i)Steam .*?: *[^\. \n]*', comment.body)
            if correctLine:
                #Get Steam Name               
                steamName = correctLine.group(0).split(':')[1].strip()
            else:    
                steamName = user
                
        #Permalink
        permalink = comment.permalink
            
        #Link
        link = ""
        #Get the right line
        correctLine = re.search(r'(?i)Link:.*', comment.body)
        if correctLine:
        #Get Link
            result = re.search(r'(?i)http(|s)://[^ )\]\n]*', correctLine.group(0))
            if result:
                link = result.group(0)
        #Just take the first link we find.
        else:
            result = re.search(r'(?i)http(|s)://[^ )\]\n]*', comment.body)
            if result:
                link = result.group(0).replace("amp;","")
                                

        x = SpelunkyScore(user, steamName, permalink, link, steamid)

        #Prune the comment text for the hover function 
        x.commentText = comment.body
        x.commentText = x.commentText.replace("amp;","")
        x.commentText = x.commentText.replace("\"","\'") #Replace any double quotes with single quotes.
        x.commentText = re.sub(r"Link:.*?http(|s)://[^ )\]\n]*","",x.commentText) #Drop the Link
        x.commentText = re.sub(r"(?i)Steam .*?: *[^\. \n]*","",x.commentText) #Drop the "Steam Name:" bit
        x.commentText = re.sub(r"\n+","  ",x.commentText) #Remove any newlines as this screws with the table markup
        x.commentText = x.commentText.strip()
        x.commentText = cap(x.commentText,250)
        scores.append(x)
    return scores

def sortScores(scores, sortType):
    orderedScores = []
    #By Score
    if sortType == "1":
        while scores:
            highLevel = "1-1"
            highScore = 0
            winner = scores[0]
            winnerIndex = 0
            for i, score in enumerate(scores):
                if score.score > highScore:
                    winner = score
                    winnerIndex = i
                    highLevel = winner.level
                    highScore = winner.score
                if score.score == highScore:
                    if score.level > highLevel:
                        winner = score
                        winnerIndex = i
                        highLevel = winner.level
                        highScore = winner.score

            if winner.valid:
                orderedScores.append(winner)
            del scores[winnerIndex]

    #By Level
    elif sortType == "2":
        while scores:
            highLevel = "1-1"
            highScore = 0
            winner = scores[0]
            winnerIndex = 0
            for i, score in enumerate(scores):
                if score.level > highLevel:
                    winner = score
                    winnerIndex = i
                    highLevel = winner.level
                    highScore = winner.score
                if score.level == highLevel:
                    if score.score > highScore:
                        print("")
                        winner = score
                        winnerIndex = i
                        highLevel = winner.level
                        highScore = winner.score

            if winner.valid:
               orderedScores.append(winner)
            del scores[winnerIndex]
         
    return orderedScores

def createScoreLine(score, position, includedate):
    resultString = ""
    resultString += str(position)+"|"
    if includedate: resultString += str(score.date.strftime("%Y-%m-%d"))+"|"
    if str(score.user) != str(score.steamname):
        resultString += str(score.user)+" ("+score.steamname+")"+"|"
    else:
        resultString += str(score.user)+"|"         
    resultString += str(score.level) +"|"
    resultString += "$" + str(score.score) +"|"
    resultString += "[Comment](" + str(score.permalink) +" \""+ score.commentText+"\"" +") |"
    if(score.link):
        resultString += "[Link](" + str(score.link) +")"+"|"
    else:
        resultString += "None" +"|"
    resultString += "[Profile](" + str(score.steamprofilelink) +")"+"\n"
    print(score.user, score.score, score.level)
    return resultString

def createInitialTable(includedate):
    if includedate:
        resultString = "\\*\\*\\*|Date|User|Level|Score|Comment|Video/Image Link|Steam Profile\n"
        resultString += ":--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:\n"
        return resultString
    else:
        resultString = "\\*\\*\\*|User|Level|Score|Comment|Video/Image Link|Steam Profile\n"
        resultString += ":--:|:--:|:--:|:--:|:--:|:--:|:--:\n"
        return resultString

def createAuthorString():
    resultString  = createLine()
    resultString  += "^[SpelunkyBot](http://www.reddit.com/user/SpelunkyBot) ^was ^created ^by ^[Avagad](http://www.reddit.com/user/Avagad). ^Any ^questions, ^complaints, ^or ^requests ^should ^be ^directed ^[here](http://www.reddit.com/message/compose/?to=Avagad&subject=SpelunkyBot)"
    return resultString

def createLine():
  return "*****\n\n"

def createSubmissionTemplate():
    resultString  = "Steam Name:" + "\n\n"
    resultString += "Link:" + "\n\n"
    return resultString

def get64ID(id):
    splitup = id.split(":")
    v = int(0x0110000100000000)
    x = int(splitup[0])
    y = int(splitup[1])
    z = int(splitup[2])
    return z*2+v+y

def cap(s, l):
    return s if len(s)<=l else s[0:l-3]+'...'

if __name__ == "__main__":
    main()