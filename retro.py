#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Missile Command

Move around with arrow keys or asdw and mark missile target with space.

Defend your cities!
"""

import time
import curses
import math
import random

cities = list()
friendlyMissiles = list()
enemyMissiles = list()
nukes = list()

nuke_slowness = 9
# max missiles per city
max_missiles = 5

game_stats = dict()

def drawCross(scr, cross, char=''):
    """
    Draw the cross at its position.
    """
    x, y = cross["x"], cross["y"]

    if char == '':
        char = 'X'

    scr.addstr(y, x, char, curses.A_BOLD)



def moveCross(scr, cross, x, y):
    """
    Move and re-draw the cross.
    """
    max_y, max_x = scr.getmaxyx()


    if cross["x"] + x < 1 or cross["x"] + x > max_x - 2 \
    or cross["y"] + y < 1 or cross["y"] + y > max_y - 8:
        return

    # Clear the cross
    drawCross(scr, cross, ' ')
    
    # Move the cross
    cross["x"] += x
    cross["y"] += y

    
def paintAllTargets(scr):
    """
    Paints all target markers
    """
    for target in friendlyMissiles:
        scr.addstr(target["y"], target["x"], "+")



def markTarget(scr, cross):
    """
    Mark a missile missile at cross position
    """
    
    # Get dimensions
    max_y, max_x = scr.getmaxyx()

    # find available cities with missiles
    available = list()

    for c in cities:
        if not c["nuked"] and c["missiles"] > 0:
            available.append(c)
            
    # no available missiles
    if len(available) == 0:
        return

    # find nearest
    minDist = max_x
    for c in available:
        d = abs(c["x"] - cross["x"])
        if d < minDist:
            minDist = d 
            city = c
    
    city["missiles"] -= 1
    
    missile = {
        "x" : cross["x"],
        "y" : cross["y"],
        "vx" : 0,
        "vy" : 0,
        "cx" : float(city["x"] + 2),
        "cy" : float(max_y - 4),
        "friendly" : True
        }
        
    # calculate missile vector
    dx = missile["x"] - missile["cx"]
    dy = missile["y"] - missile["cy"]
    d = math.sqrt(dx ** 2 + dy ** 2)
    missile["vx"] = dx / d
    missile["vy"] = dy / d
    
    friendlyMissiles.append(missile)



def updateMissiles(scr, missiles):
    """
    Updates and paints friendly missiles
    """
    hits = list()
    
    for m in missiles:
        # erase old missile gfx
        scr.addstr(round(m["cy"]), round(m["cx"]), ' ')

        m["cx"] += m["vx"]
        m["cy"] += m["vy"]
        
        icx = round(m["cx"])
        icy = round(m["cy"])
        
        # draw new missile gfx
        scr.addstr(icy, icx, '*')
        
        if icx == m["x"] and icy == m["y"] or \
        isWithinExplosion(icx, icy):
            hits.append(m)
            addExplosion(icx, icy)
    
    for h in hits:
        if h["friendly"]:
            # remove target marker
            scr.addstr(h["y"], h["x"], ' ')
        missiles.remove(h)
        
        
        
def isWithinExplosion(x, y):
    """
    Checks if coordinate is within explosion
    """
    for n in nukes:
        dist = getExplosionDist(n["t"] // nuke_slowness)
        dx = x - n["x"]
        dy = y - n["y"]
        d = math.sqrt(dx ** 2 + (dy * 2) ** 2)
        if d <= dist:
            return True
    
    return False


def getExplosionDist(t):
    """
    Calculates explosion distance depending on time
    """
    if t < 5:
        dist = 3 + t
    else:
        dist = 3 + 7 - t
        
    return dist



def addExplosion(x, y):
    """
    Adds a new explosion
    """
    ex = {
        "x" : x,
        "y" : y,
        "t" : 0
        }
    
    nukes.append(ex)


def paintExplosion(scr, nuke, draw):
    """
    Paints or clears an explosion
    """
    
    t = nuke["t"] // nuke_slowness
    dist = getExplosionDist(t)
    x = nuke["x"]
    y = nuke["y"]
    
    # Get dimensions
    max_y, max_x = scr.getmaxyx()

    if not draw:
        char = ' '
    else:
        if t < 5:
            char = '@'
        else:
            char = 'Xx*~- '[t - 5]

    for gy in range(y - dist // 2, y + dist // 2 + 1):
        for gx in range(x - dist, x + dist + 1):
            dx = gx - x
            dy = gy - y
            d = math.sqrt(dx ** 2 + (dy * 2) ** 2)
            if d <= dist and gx >= 1 and gx < max_x - 1 and \
            gy >= 1 and gy < max_y - 1:
                scr.addstr(gy, gx, char)
    
    
def updateExplosions(scr):
    """
    Updates and paints explosions
    """
    
    finishedNukes = list()
    
    for n in nukes:
        
        paintExplosion(scr, n, False)
        
        if n["t"] > 10 * nuke_slowness:
            finishedNukes.append(n)
        else:
            n["t"] += 1
            paintExplosion(scr, n, True)
    
    for n in finishedNukes:
        nukes.remove(n)
        
        
        
def updateCities(scr):
    """
    Paints cities
    """
    # Get dimensions
    dim = scr.getmaxyx()
    
    nuked = list()
    
    for c in cities:
        # check if being nuked
        if not c["nuked"]:
            if isWithinExplosion(c["x"] + 2, dim[0] - 4):
                # city nuked
                c["nuked"] = True
                addExplosion(c["x"] + 2, dim[0] - 3)

        # draw missile count
        for m in range(max_missiles):
            if m < c["missiles"] and not c["nuked"]:
                scr.addstr(dim[0] - 1, c["x"] + m, "*")
            else:
                scr.addstr(dim[0] - 1, c["x"] + m, " ")
                
        # draw city
        if not c["nuked"]:
            scr.addstr(dim[0] - 5, c["x"], "   H ")
            scr.addstr(dim[0] - 4, c["x"], " H H ")
            scr.addstr(dim[0] - 3, c["x"], " H H|")
            scr.addstr(dim[0] - 2, c["x"], "=H=H=")
        else:
            scr.addstr(dim[0] - 5, c["x"], "     ")
            scr.addstr(dim[0] - 4, c["x"], "     ")
            scr.addstr(dim[0] - 3, c["x"], "     ")
            scr.addstr(dim[0] - 2, c["x"], "_____")
            nuked.append(c)
            
    for c in nuked:
        cities.remove(c)
                
                
            
def updateEnemy(scr, game):
    """
    Ticks the super smart enemy AI
    """
    
    if random.randrange(0, game["enemyRandom"]) > 0 or game["enemyMissiles"] == 0:
        return
    
    # Get dimensions
    max_y, max_x = scr.getmaxyx()

    # select a city to attack
    available = list()

    for c in cities:
        if not c["nuked"]:
            available.append(c)
            
    # evilness won!
    if len(available) == 0:
        return

    game["enemyMissiles"] -= 1

    city = random.choice(available)
    
    missile = {
        "x" : city["x"] + 2,
        "y" : max_y - 2,
        "vx" : 0,
        "vy" : 0,
        "cx" : float(random.randrange(1, max_x)),
        "cy" : 1.0,
        "friendly" : False
    }
        
    # calculate missile vector
    dx = missile["x"] - missile["cx"]
    dy = missile["y"] - missile["cy"]
    d = math.sqrt(dx ** 2 + dy ** 2)
    d *= game["enemyMissileSlowness"]
    missile["vx"] = dx / d
    missile["vy"] = dy / d
    
    enemyMissiles.append(missile)



def initGame(scr, game, cross):
    """
    Initiates a clean game
    """ 
    # Get dimensions
    max_y, max_x = scr.getmaxyx()
    
    # clear missile and explosion lists
    friendlyMissiles.clear()
    enemyMissiles.clear()
    nukes.clear()

    # setup cities
    cities.clear()
    for i in range(0, 5):
        cities.append({
            "x" : 5 + (i * (max_x - 15) // 4),
            "missiles" : max_missiles,
            "nuked" : False
            })

    # setup game
    game["enemyMissileSlowness"] = 20
    game["enemyStartMissiles"] = 5
    game["enemyMissiles"] = 5
    game["enemyRandom"] = 100
    game["score"] = 0

    # setup cursor
    cross["x"] = max_x // 2
    cross["y"] = max_y // 2
    
    
    
def nextLevel(game):
    """
    Next game level
    """
    
    # more enemy missiles
    if game["enemyStartMissiles"] < 5 * (max_missiles + 1):
        game["enemyStartMissiles"] += 3
    else: 
        game["enemyStartMissiles"] = 5 * (max_missiles + 1)
    game["enemyMissiles"] = game["enemyStartMissiles"]
    
    # faster enemy missles
    if game["enemyMissileSlowness"] > 1:
        game["enemyMissileSlowness"] -= 1
        
    # missiles more often
    if game["enemyRandom"] > 10:
        game["enemyRandom"] -= 4
        
    # calc score, restore cities missile stash
    for c in cities:
        if not c["nuked"]:
            game["score"] += 100  
            game["score"] += 20 * c["missiles"]  
            c["missiles"] = max_missiles

    if game["score"] > game["highscore"]:
        game["highscore"] = game["score"]
        game["highscoreholder"] = game["playername"]

    # clear missile and explosion lists
    friendlyMissiles.clear()
    enemyMissiles.clear()
    
    game["timer"] = 250


def mainLoop(scr):
    """
    Main game loop
    """
    global game_stats

    # Don't stop the while-loop while waiting for input
    scr.nodelay(1)

    # Enable keypad mode
    scr.keypad(True)
    
    # Make cursor invisible
    curses.curs_set(0)

    # cursor
    cross = dict()
    
    # intial game stats
    
    if game_stats == None:
        game_stats = dict()
    game_stats["mode"] = 3
    game_stats["score"] = 0
    if "highscore" not in game_stats:
        game_stats["highscore"] = 0
    if "highscoreholder" not in game_stats:
        game_stats["highscoreholder"] = "none"
    if "playername" not in game_stats:
        game_stats["playername"] = "me"

    game = game_stats
    # Do until exit
    while True:
        # Get input from user and flush the input buffer
        ch = scr.getch()
        curses.flushinp()
        
        if game["mode"] == 0:
            # reset game and restart 
            initGame(scr, game, cross)
            game["mode"] = 1
        elif game["mode"] == 1:
            # game
            modeGame(scr, cross, game, ch)
        elif game["mode"] == 2:
            # intermission
            modeNextLevel(scr, game)
        elif game["mode"] == 3:
            # game over screen
            modeGameOver(scr, game, ch)
            
        if ch == ord("q"):
            break


        scr.refresh()

        # Sleep until next round
        time.sleep(0.02)
        
    return (game_stats["highscore"], game_stats["highscoreholder"])

def modeGameOver(scr, game, ch):
    """
    Game over screen
    """
    scr.clear()
    
    # Get dimensions
    max_y, max_x = scr.getmaxyx()
    
    s = "M I S S I L E   C O M M A N D"
    scr.addstr(max_y // 2 - 5, (max_x - len(s)) // 2, s)

    s = "G A M E   O V E R"
    scr.addstr(max_y // 2 - 3, (max_x - len(s)) // 2, s)

    s = "Score: {0}".format(game["score"])
    scr.addstr(max_y // 2 - 1, (max_x - len(s)) // 2, s)

    s = "High score: {0} by {1}".format(game["highscore"], game["highscoreholder"])
    scr.addstr(max_y // 2 + 1, (max_x - len(s)) // 2, s)

    s = "Move cursor with arrow keys and press SPACE to mark target"
    scr.addstr(max_y // 2 + 3, (max_x - len(s)) // 2, s)
    
    s = "Press SPACE to start or q to quit"
    scr.addstr(max_y // 2 + 5, (max_x - len(s)) // 2, s)
    
    if ch == ord(' '):
        scr.clear()
        game["mode"] = 0
      
    
def modeNextLevel(scr, game):
    """
    Screen for next level
    """
    max_y, max_x = scr.getmaxyx()
    
    s = "Score: {0}".format(game["score"])
    scr.addstr(max_y // 2 - 1, (max_x - len(s)) // 2, s)

    s = "Prepare for next attack"
    scr.addstr(max_y // 2 + 1, (max_x - len(s)) // 2, s)
    
    if game["timer"] > 0:
        game["timer"] -= 1
    else:
        scr.clear()
        game["mode"] = 1
    
    

def modeGame(scr, cross, game, ch):
    """
    Perform the actual game loop
    """
    # tick evilness
    updateEnemy(scr, game)
    
    # draw cities
    updateCities(scr)
    
    # update and draw missiles
    updateMissiles(scr, friendlyMissiles)
    updateMissiles(scr, enemyMissiles)
    
    # update and draw explosions
    updateExplosions(scr)

    
    # Check if a key was pressed and update
    if ch == curses.KEY_LEFT or ch == ord('a'):
        moveCross(scr, cross, -1, 0)

    elif ch == curses.KEY_RIGHT or ch == ord('d'):
        moveCross(scr, cross, 1, 0)

    elif ch == curses.KEY_UP or ch == ord('w'):
        moveCross(scr, cross, 0, -1)

    elif ch == curses.KEY_DOWN or ch == ord('s'):
        moveCross(scr, cross, 0, 1)

    elif ch == ord(' '):
        markTarget(scr, cross)

    # paint cross
    drawCross(scr, cross)

    # paint all target markers
    paintAllTargets(scr)

    # check stats
    if len(cities) == 0:
        # game over
        game["mode"] = 3

    if game["enemyMissiles"] == 0 and len(enemyMissiles) == 0 and len(nukes) == 0:
        # next level
        nextLevel(game)
        game["mode"] = 2

def start(playerName="me", highscore=0, highscoreHolder="none"):
    """ Start game """
    global game_stats
    game_stats = dict()
    game_stats["playername"] = playerName
    game_stats["highscore"] = highscore
    game_stats["highscoreholder"] = highscoreHolder
    result = curses.wrapper(mainLoop)
    return result

if __name__ == "__main__":
    print(__doc__)
    input("Press enter to begin playing...")
    start()
