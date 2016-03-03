#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Person AI
"""

import entities
import random
import world

FOREVER = 999999

def personTick(person):
    ''' Ticks a person entity '''
    if person.sleeping:
        return
    
    if person.opTimer == FOREVER:
        return
    
    if person.opTimer > 0:
        person.opTimer -= 1
        return
    
    if len(person.opStack) == 0:
        person.pushOperation("trywork")
        
    op = person.peekOperation()
    person.curOp = op
    func = _funcSpecs[op["func"]]
    func(person.v_world, person, op["arg"])
    
def personActionDescription(person):
    ''' Returns a description of what the person is doing '''
    if person.curOp == None:
        return None
    op = person.curOp
    if op["func"] == "go":
        if len(person.opStack) == 0:
            return None
        else:
            op = person.peekOperation()
        
    if op["func"] == "work":
        if random.randint(0, 1) == 0:
            s = "{person} sitter vid datorn. När jag sneglar på hans skärm ser det ut som "
            s += random.choice(["YouTube", "ebay", "Minecraft", "en googlesökning på getter", \
                "en wiki över konspirationsteorier", "en site som säljer spandex i lösvikt"])
            s += ". När {person} märker att jag tittar flippar han snabbt bort det och "
            s += random.choice(["visslar falskt", "rodnar", "låtsas att det regnar", \
                "tittar upp i taket", "mumlar nåt ohörbart", "stirrar in i skärmen"])
            s += "."
        else:
            s = "{person} sitter och jobbar."
    elif op["func"] == "trywork":
        s = "{person} är på väg mot sin arbetsplats."
    elif op["func"].startswith("findchair"):
        s = "{person} letar efter en stol."
    elif op["func"] == "tryspeakto":
        s = "{person} letar efter " + op["arg"] + "."
    elif op["func"] == "speakto":
        s = "{person} pratar med " + op["arg"] + "."
    elif op["func"] == "tryusetoilet":
        s = "{person} är på väg mot toan."
    elif op["func"] == "usetoilet":
        s = "{person} sitter på dass."
    elif op["func"] == "eatfruit":
        s = "{person} ser hungrig ut."
    elif op["func"].startswith("findkey"):
        s = "{person} letar frenetiskt efter nåt."
    elif op["func"] == "hall":
        s = "{person} väntar på att vi ska ut och käka burgare."
    elif op["func"] == "etermeeting":
        s = "{person} har ett möte."
    else:
        return None
    
    return s.format(person=person.name())
    
def personTricorderDescription(person):
    ''' Returns a description of what the person is doing '''
    if person.curOp == None:
        return "Okänt"
    op = person.curOp
    if op["func"] == "go":
        if len(person.opStack) == 0:
            return "Går"
        else:
            op = person.peekOperation()
        
    if op["func"] == "work":
        s = "Arbetar"
    elif op["func"] == "trywork":
        s = "Försöker arbeta"
    elif op["func"].startswith("findchair"):
        s = "Letar stol"
    elif op["func"] == "tryspeakto":
        s = "Letar efter " + op["arg"]
    elif op["func"] == "speakto":
        s = "Pratar med " + op["arg"]
    elif op["func"] == "tryusetoilet":
        s = "Nödig"
    elif op["func"] == "usetoilet":
        s = "Avlägsnar biprodukter"
    elif op["func"] == "eatfruit":
        s = "Vill äta"
    elif op["func"].startswith("findkey"):
        s = "Letar nyckel"
    elif op["func"] == "hall":
        s = "Väntar"
    elif op["func"] == "etermeeting":
        s = "I möte"
    else:
        return "Okänt"
    
    return s
    
def opWork(w, person, arg):
    ''' operation for work '''
    #pylint: disable=unused-argument
    if person.roomIx != person.homeRoomIx:
        person.popOperation()
        person.pushOperation("trywork")
        person.opTimer = 0
        return
    if person.name() == "Gringo" and not w.checkAchievment(world.ACH_GRINGO_KEY):
        key = world.getEntity(person, "cykelnyckel")
        if key == None:
            s = random.choice(["Min cykelnyckel! Min cykelnyckel! Var är den?", \
                "Nooooooh! Jag har tappat min cykelnyckel!", \
                "Herrejistanes! Min cykelnyckel är borta!"])
            w.onPersonSpeech(person, s)
            person.popOperation()
            person.pushOperation("findkeyforw")
            person.opTimer = 0
            return
    
    person.opTimer = random.randint(person.workMin, person.workMax)
    if random.randint(0, 100) < person.talk:
        others = list(w.persons)
        others.remove(person)
        person.popOperation()
        person.pushOperation("tryspeakto", random.choice(others).name())
    elif random.randint(0, 100) < person.eat:
        person.popOperation()
        person.pushOperation("eatfruit")
    elif random.randint(0, 100) < person.toilet:
        person.popOperation()
        person.pushOperation("tryusetoilet")
        
    return
        
def opTryWork(w, person, arg):
    ''' operation for trying to work '''
    #pylint: disable=unused-argument
    person.opTimer = 1

    # check if home
    if person.roomIx != person.homeRoomIx:
        world.dbg(person.name() + " tries to work but not home")
        if person.roomIx < person.homeRoomIx:
            person.pushOperation("go", 1)
        else:
            person.pushOperation("go", -1)
    else:
        # check if free chair is here or a chair that person is already sitting in
        stuff = w.getAccessibleThingsInRoom(person.roomIx)
        freeChair = next((thing for thing in stuff if isinstance(thing, entities.Chair) \
            and (thing.sitterPerson == None or thing.sitterPerson == person.name())), None)
        if freeChair != None:
            freeChair.sitterPerson = person.name()
            person.popOperation()
            w.onPersonGeneric(person, "{} sätter sig ner och börjar knattra på datorn.".format(person.name()))
            person.pushOperation("work")
            world.dbg(person.name() + " takes a chair")
        else:
            w.onPersonSpeech(person, random.choice(["Vem har snott min stol!?", \
                "Har nån sett min stol?", "Var i böfvelen är min kära stol?"]))
            world.dbg(person.name() + " finds no chair start searching for one")
            person.pushOperation("findchairback")
            
def opGo(w, person, arg):
    ''' operation for going forward or backward '''
    person.opTimer = random.randint(7, 12)
    person.unseat()
    if arg > 0:
        if person.roomIx < len(w.rooms):
            person.roomIx += 1
            w.onPersonMovement(person, person.roomIx - 1)
            world.dbg(person.name() + " goes back")
    else:
        if person.roomIx > 1:
            person.roomIx -= 1
            w.onPersonMovement(person, person.roomIx + 1)
            world.dbg(person.name() + " goes forward")
    
    if person.name() == "Gringo" and random.randint(0, 1) == 1:
        stuff = w.getAccessibleThingsInRoom(person.roomIx, False)
        bigStuff = [thing for thing in stuff if thing.v_size >= entities.SIZE_BIG]
        if len(bigStuff) > 0:
            thing = random.choice(bigStuff)
            world.dbg(person.name() + " collides with " + world.determinedForm(thing))
            s = random.choice(["{} går rätt in i {}.", "{} snubblar på {}.", \
                               "{} dunkar huvudet i {}.", "{} trillar över {}."])
            w.onPersonGeneric(person, s.format(person.name(), world.determinedForm(thing)))
            w.onPersonSpeech(person, random.choice(["Aj!", "Attans!", "Hoppsan!", \
                "Sablar!", "Men för jäsicken!", "Jösses då!", "#@$*!", "Balle!"]))
            key = world.getEntity(person, "cykelnyckel")
            if key != None and random.randint(0, 1) == 1:
                key.v_parentEntity.v_container.remove(key)
                w.roomForIndex(person.roomIx).v_container.append(key)
                key.v_parentEntity = w.roomForIndex(person.roomIx)
                w.onPersonGeneric(person, "{} tappade nåt i kollisionen.".format(person.name()))


    
    person.popOperation()
    
def findChair(w, person, arg):
    ''' helper for operation for finding a free chair '''
    #pylint: disable=unused-argument
    person.opTimer = 1
    # check if free chair is here or a chair that person is already sitting in
    stuff = w.getAccessibleThingsInRoom(person.roomIx)
    freeChair = next((thing for thing in stuff if isinstance(thing, entities.Chair) \
        and (thing.sitterPerson == None or thing.sitterPerson == person.name())), None)
    if freeChair != None:
        # have a chair
        freeChair.sitterPerson = person.name()
        if person.roomIx == person.homeRoomIx:
            world.dbg(person.name() + " finds a chair at home, findChair pop")
            person.popOperation()
        else:
            freeChair.sitterPerson = None
            world.dbg(person.name() + " finds a chair away, moves it home")
            if person.roomIx < person.homeRoomIx:
                freeChair.move(1)
                person.pushOperation("go", 1)
            else:
                freeChair.move(-1)
                person.pushOperation("go", -1)
            w.onPersonGeneric(person, "{} flyttar stolen.".format(person.name()))

            freeChair.sitterPerson = person.name()
        return True
    else:
        world.dbg(person.name() + " finds no chair, will search for one")
        return False
            
def opFindChairBack(w, person, arg):
    ''' operation for finding a free chair going backwards '''
    foundChair = findChair(w, person, arg)
    if not foundChair:
        if person.roomIx >= len(w.rooms):
            person.popOperation()
            world.dbg(person.name() + " looked for chair all the way back, try other direction")
            person.pushOperation("findchairforw")
        else:
            person.pushOperation("go", 1)
        
def opFindChairForward(w, person, arg):
    ''' operation for finding a free chair going forwards '''
    foundChair = findChair(w, person, arg)
    if not foundChair:
        if person.roomIx <= 1:
            person.popOperation()
            world.dbg(person.name() + " looked for chair all the way forward, try other direction")
            person.pushOperation("findchairback")
        else:
            person.pushOperation("go", -1)
            
def opTrySpeakTo(w, person, arg):
    ''' operation for trying to speak to someone '''
    other = next((person for person in w.persons if person.name() == arg), None)
    if other == None or other.roomIx == 0:
        world.dbg(person.name() + " cannot speak to " + arg)
        person.popOperation()
        person.opTimer = 1
    elif other.roomIx == person.roomIx:
        if other.curOp["func"] == "speakto":
            world.dbg(person.name() + " cannot speak to " + other.name() + \
                ", already speaking to " + other.curOp["arg"])
            person.popOperation()
            person.opTimer = 0
        else:
            world.dbg(person.name() + " starts speaking to " + arg)
            person.popOperation()
            person.pushOperation("speakto", arg)
            w.onPersonGeneric(person, "{} börjar prata med {}.".format(person.name(), other.name()))
            other.pushOperation("speakto", person.name())
            person.opTimer = 0
            other.opTimer = 0
    else:
        world.dbg(person.name() + " is finding " + arg + " to speak to")
        person.opTimer = 1
        if person.roomIx < other.roomIx:
            person.pushOperation("go", 1)
        else:
            person.pushOperation("go", -1)
        
def opSpeakTo(w, person, arg):
    ''' operation for speaking to someone '''
    #pylint: disable=unused-argument
    world.dbg(person.name() + " is speaking to " + arg)
    if arg == "_player":
        person.opTimer = FOREVER
    else:
        person.opTimer = 30
    person.popOperation()
            
def opTryUseToilet(w, person, arg):
    ''' operation for trying to use toilet '''
    #pylint: disable=unused-argument
    person.opTimer = 0
    if person.roomIx != 3:
        world.dbg(person.name() + " is heading for the loo")
        if person.roomIx < 3:
            person.pushOperation("go", 1)
        else:
            person.pushOperation("go", -1)
    else:
        wc = w.roomForIndex(3)
        door = world.getEntity(wc, "dörr")
        if door.locked:
            world.dbg(person.name() + " darn - loo busy")
            person.popOperation()
        else:
            door.locked = True
            door.closed = True
            world.dbg(person.name() + " entering loo")
            w.onPersonGeneric(person, "{} går in på toaletten med en suck.".format(person.name()))
            person.opTimer = 35
            person.roomIx = 0
            person.popOperation()
            person.pushOperation("usetoilet")

def opUseToilet(w, person, arg):
    ''' operation for use toilet '''
    #pylint: disable=unused-argument
    person.opTimer = 0
    wc = w.roomForIndex(3)
    door = world.getEntity(wc, "dörr")
    door.locked = False
    person.roomIx = 3
    w.onPersonGeneric(person, ("Nån spolar på toan, och {} kommer ut från toaletten med " + \
        "ett leende.").format(person.name()))
    person.popOperation()
    world.dbg(person.name() + " leaving loo")
    
 
def findKey(w, person, arg):
    ''' helper for operation for finding the key '''
    #pylint: disable=unused-argument
    person.opTimer = 0
    
    if w.checkAchievment(world.ACH_GRINGO_KEY):
        # got it!
        person.popOperation()
        return True

    stuff = w.getAccessibleThingsInRoom(person.roomIx)
    key = next((thing for thing in stuff if isinstance(thing, entities.Key)), None)
    if key != None:
        world.dbg(person.name() + " finds key")
        key.v_parentEntity.v_container.remove(key)
        person.v_container.append(key)
        key.v_parentEntity = person
        w.onPersonSpeech(person, "Åh tack gode Gud - jag hittade min cykelnyckel!")
        person.popOperation()
        return True
    else:
        world.dbg(person.name() + " finds no key")
        s = random.choice(["Har nån sett min cykelnyckel?", "Min kära cykelnyckel.. Var är du?", \
            "Komsi komsi cykelnyckeln! Komsi!", "Cykelnyckeln? Snälla, säg du har sett min cykelnyckel!", \
            "*mummel mummel* nyckel *snyft*"])
        w.onPersonSpeech(person, s)
        return False
            
def opFindKeyBack(w, person, arg):
    ''' operation for finding key going backwards '''
    foundKey = findKey(w, person, arg)
    if not foundKey:
        if person.roomIx >= len(w.rooms):
            person.popOperation()
            world.dbg(person.name() + " looked for key all the way back, try other direction")
            person.pushOperation("findkeyforw")
        else:
            person.pushOperation("go", 1)
        
def opFindKeyForward(w, person, arg):
    ''' operation for finding key forwards '''
    foundKey = findKey(w, person, arg)
    if not foundKey:
        if person.roomIx <= 1:
            person.popOperation()
            world.dbg(person.name() + " looked for key all the way forward, try other direction")
            person.pushOperation("findkeyback")
        else:
            person.pushOperation("go", -1)
            
def opEat(w, person, arg):
    ''' operation for finding fruit '''
    #pylint: disable=unused-argument
    person.opTimer = 0
    if person.roomIx == 2:
        fruitbowl = world.getEntity(w.roomForIndex(2), "fruktskål")
        if len(fruitbowl.contains()) == 0:
            w.onPersonSpeech(person, random.choice(["Var är all frukt?", "Ingen frukt? Jag som var så hungrig.", \
                "Är det du som käkat all frukt?", "Nån som vet när de fyller på fruktskålen?"]))
        else:
            fruit = random.choice(fruitbowl.contains())
            if person.name == "Pedrik" and fruit.name() == "banan":
                w.onPersonSpeech(person, "Aargh! Jag rörde vid en banan! It burns!")
            else:
                w.onPersonGeneric(person, "{} glufsar i sig {} {}.".format(person.name(), fruit.v_genus, fruit.name()))
                fruit.v_parentEntity.v_container.remove(fruit)
                fruit.v_parentEntity = None
                world.dbg(person.name() + " consumes a " + fruit.name())
                person.opTimer = 15
        person.popOperation()
    elif person.roomIx < 2:
        world.dbg(person.name() + " is heading for fruit")
        person.pushOperation("go", 1)
    else:
        world.dbg(person.name() + " is heading for fruit")
        person.pushOperation("go", -1)
        
def opCheckHighScore(w, person, arg):
    ''' operation for checking highscore '''
    #pylint: disable=unused-argument
    world.dbg(person.name() + " is checking highscore @ room " + str(person.roomIx))
    person.opTimer = 0
    if person.roomIx == 2:
        if w.playerRoomIx() == 2:
            world.outputDirect("Fratrik går fram till arkadspelet.")
            world.outputDirect("Fratrik: 'Noooooooooooooooooooooooooooooo!!!'")
        else:
            world.outputDirect("Jag hör ett vrål från Fikarummet: 'Noooooooooooooooooooooooooooooo!!!'\n" + \
                "Det låter som Fratrik.")
        w.addAchievment(world.ACH_FRATRIK_BEATEN)
        person.popOperation()
    elif person.roomIx < 2:
        world.dbg(person.name() + " is checking highscore")
        person.pushOperation("go", 1)
    else:
        world.dbg(person.name() + " is checking highscore")
        person.pushOperation("go", -1)
        
def opCheckMenu(w, person, arg):
    ''' operation for checking menu '''
    #pylint: disable=unused-argument
    person.opTimer = 0
    if person.roomIx == 1:
        person.popOperation()
        w.onPersonSpeech(person, "Vafanken?")
        if person.name() == "Jean":
            w.addAchievment(world.ACH_JEAN_MENU_CHECK)
        else:
            w.addAchievment(world.ACH_PEDRIK_MENU_CHECK)
    elif person.roomIx < 1:
        world.dbg(person.name() + " is checking menu")
        person.pushOperation("go", 1)
    else:
        world.dbg(person.name() + " is checking menu")
        person.pushOperation("go", -1)
        
def opMutsMeeting(w, person, arg):
    ''' operation for calling muts to gringos room for eternal talk '''
    #pylint: disable=unused-argument
    person.opTimer = 0
    muts = next((p for p in w.persons if p.name() == "Muts"), None)
    if muts.curOperation()["func"] != "mutsmeeting":
        # add same op to muts
        muts.opStack = list()
        muts.pushOperation("mutsmeeting")
        muts.opTimer = 0
        
    if person.name() == "Gringo" and person.roomIx == 7 and muts.roomIx == 7:
        muts.popOperation()
        person.popOperation()
        person.pushOperation("etermeeting", "Muts")
        muts.pushOperation("etermeeting", "Gringo")
        w.onPersonGeneric(person, "{} börjar prata med {}.".format(person.name(), muts.name()))
    else:
        if person.roomIx < 7:
            world.dbg(person.name() + " heading for meeting")
            person.pushOperation("go", 1)
        elif person.roomIx > 7:
            world.dbg(person.name() + " is heading for meeting")
            person.pushOperation("go", -1)
        
        
def opEternalMeeting(w, person, arg):
    ''' operation for meeting with someone '''
    #pylint: disable=unused-argument
    world.dbg(person.name() + " is speaking to " + arg)
    person.opTimer = FOREVER
            
def opGotoHall(w, person, arg):
    ''' operation for meeting with someone '''
    #pylint: disable=unused-argument
    if person.roomIx > 1:
        world.dbg(person.name() + " is heading for hall")
        person.pushOperation("go", -1)
        person.opTimer = 0
    else:
        person.opTimer = FOREVER
            

_funcSpecs = { \
    "trywork" : opTryWork, \
    "work" : opWork, \
    "go" : opGo, \
    "findchairback" : opFindChairBack, \
    "findchairforw" : opFindChairForward, \
    "tryspeakto" : opTrySpeakTo, \
    "speakto" : opSpeakTo, \
    "tryusetoilet" : opTryUseToilet, \
    "usetoilet" : opUseToilet, \
    "eatfruit" : opEat, \
    "findkeyforw" : opFindKeyForward, \
    "findkeyback" : opFindKeyBack, \
    "checkhighscore" : opCheckHighScore, \
    "checkmenu" : opCheckMenu, \
    "mutsmeeting" : opMutsMeeting, \
    "etermeeting" : opEternalMeeting, \
    "hall" : opGotoHall, \
    }
