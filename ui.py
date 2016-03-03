#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Office Adventure UI

@author: petera
'''


import world
import entities
import random
#import time
import advterm
import advrant

commandDefs = dict()
_access_lastThing = None
_kill_next = False

def reset():
    ''' Resets ui '''
    advterm.clear()
    
def updateInputPrefix(w):
    ''' updates input prefix '''
    if world.inConversation:
        advterm.inputPrefix("[" + w.playerRoom().name() + ":" + world.conversationPerson.name() + "" +"] ")
    else:
        advterm.inputPrefix("[" + w.playerRoom().name() + "] ")

def out(s):
    ''' Outputs stuff to user '''
    advterm.output(s + "\n")
    #print(s)

def sleep(secs):
    ''' Sleeps for given seconds '''
    #time.sleep(secs)
    advterm.sleep(0 * secs)

def outNoThing(s, op):
    ''' prints that I don't know of that '''
    if op == cmdDrop or op == cmdUse:
        out(world.capitalizeFirst(world.stringify(["Har ingen {}.", "Vilken {}?", \
            "Håller inte i någon {}."]).format(s)))
    else:
        out(world.capitalizeFirst(world.stringify(["Här finns ingen {}.", "Vilken {}?", \
            "Kan inte se någon {}."]).format(s)))

def outFailMsg(thing, default):
    ''' prints error message on failed thing op '''
    errMsg = thing.failMsg()
    world.dbg("outFailMsg {} errMsg:{} def:{}".format(thing.name(), errMsg, default))
    if errMsg == None:
        out(default)
    else:
        out(errMsg)

def cmdHelp(w, args):
    ''' prints help '''
    #pylint: disable=unused-argument
    keys = list(sorted(commandDefs.keys()))
    while len(keys) > 0:
        cmds = list()
        cmdDef = commandDefs[keys[0]]
        for cmdKey in commandDefs:
            if commandDefs[cmdKey] == cmdDef:
                cmds.append(cmdKey)
                keys.remove(cmdKey)
        cmds = sorted(cmds, reverse=True)

        out("{:<40} {}".format(",".join(cmds) + " " + cmdDef[2], cmdDef[1]))
        
def cmdRoomInfo(w, args):
    ''' prints room description '''
    #pylint: disable=unused-argument
    out("*** " + w.playerRoom().name() + " ***")
    out(w.playerRoom().description())

    ways = ""
    if w.playerRoomIx() > 1:
        ways += w.roomForIndex(w.playerRoomIx() - 1).name() + " ligger framåt. "
    if w.playerRoomIx() < len(w.rooms):
        ways += w.roomForIndex(w.playerRoomIx() + 1).name() + " ligger bakåt."
    out(world.stringify(ways))
    
    persons = w.getPersonsInRoom(w.playerRoomIx())
    if len(persons) > 0:
        out("{0} är här.".format(world.stringify(world.listify(persons))))

def cmdForward(w, args):
    ''' Go forward '''
    #pylint: disable=unused-argument
    if w.player.roomIx > 1:
        w.player.moveRoom(-1)
        updateInputPrefix(w)
        cmdRoomInfo(w, args)
    else:
        out("Det går ju inte.")
    

def cmdBack(w, args):
    ''' Go back '''
    #pylint: disable=unused-argument
    if w.player.roomIx < len(w.rooms):
        w.player.moveRoom(1)
        updateInputPrefix(w)
        cmdRoomInfo(w, args)
    else:
        out("Det går ju inte.")

def cmdExamine(w, args):
    ''' Examine object or room when no args '''
    global _access_lastThing
    if len(args) == 0:
        out(w.playerRoom().description())
        persons = w.getPersonsInRoom(w.playerRoomIx())
        if len(persons) > 0:
            out("{0} är här.".format(world.stringify(world.listify(persons))))
        stuff = w.getAccessibleThingsInRoom(w.playerRoomIx(), False)
        if len(stuff) > 0:
            out("Det finns " + world.stringifyContents(stuff) + " här.")
    else:
        stuff = w.getAllAccessibleEntitiesInCurrentRoom()
        thing = world.findInEntityList(stuff, args[0], _access_lastThing)
        if thing != None:
            desc = world.getDetailedDescription(thing) 
            out(desc)
            _access_lastThing = thing
        else:
            _access_lastThing = None
            outNoThing(args[0], cmdExamine)
    
def cmdObjects(w, args):
    ''' Lists all objects in room '''
    #pylint: disable=unused-argument
    stuff = w.getAccessibleThingsInRoom(w.playerRoomIx(), False)
    for thing in stuff:
        out(world.capitalizeFirst(thing.name()) + ": " + world.getDetailedDescription(thing))
    persons = w.getPersonsInRoom(w.playerRoomIx())
    if len(persons) > 0:
        out("{0} är här.".format(world.stringify(world.listify(persons))))
    
def cmdOpen(w, args):
    ''' Opens a thing '''
    if len(args) == 0:
        out("Jag öppnar ingenting, och häpnar över att inget händer!")
        return
    stuff = w.getAllAccessibleEntitiesInCurrentRoom()
    thing = world.findInEntityList(stuff, args[0])
    if thing == None:
        outNoThing(args[0], cmdOpen)
        return
    
    if isinstance(thing, entities.Thing) and thing.v_lid:
        if not thing.closed:
            out("Redan öppen ju.")
        else:
            res = thing.open()
            if not res:
                outFailMsg(thing, "Det gick inte att öppna {}.".format(world.determinedForm(thing)))
            else:
                if not isinstance(thing, entities.ExitDoor):
                    out(world.getDetailedDescription(thing))
    else:
        out("Kan ju inte öppna {}.".format(args[0]))  
    
def cmdClose(w, args):
    ''' Closes a thing '''
    if len(args) == 0:
        out("Jag stänger ingenting, och häpnar över att inget händer!")
        return
    stuff = w.getAllAccessibleEntitiesInCurrentRoom()
    thing = world.findInEntityList(stuff, args[0])
    if thing == None:
        outNoThing(args[0], cmdClose)
        return
    
    if isinstance(thing, entities.Thing) and thing.v_lid:
        if thing.closed:
            out("Redan stängd ju.")
        else:
            res = thing.close()
            if not res:
                outFailMsg(thing, "Det gick inte att stänga {}.".format(world.determinedForm(thing)))
            else:
                out("Jag stänger {}.".format(world.determinedForm(thing)))

    else:
        out("Jag kan ju inte stänga {}.".format(args[0]))  
    
def cmdInventory(w, args):
    ''' Shows inventory '''
    #pylint: disable=unused-argument
    backpack = w.player.contains()
    if len(backpack) == 0:
        out("Jag bär ingenting.")
    else:
        out("Jag bär på " + world.stringifyContents(backpack) + ".")
        for thing in backpack:
            out(world.capitalizeFirst(thing.name()) + ": " + world.getDetailedDescription(thing))

    
def cmdTake(w, args):
    ''' Takes thing '''
    if len(args) == 0:
        out("Jag tar ingenting, och känner mig lite fattig.")
        return
    stuff = w.getAccessibleThingsInRoom(w.playerRoomIx())
    stuff += w.getPersonsInRoom(w.playerRoomIx())
    thing = world.findInEntityList(stuff, args[0])
    if thing == None:
        outNoThing(args[0], cmdTake)
        return
    
    if isinstance(thing, entities.Thing):
        postAdj = ""
        if thing.v_genus == "ett":
            postAdj = "t"
        if w.inventoryCount() >= 10:
            out("Jag har bara två händer!")
        elif w.inventorySize() + thing.v_size >= 7:
            out("Jag får inte plats med fler grejor!")
        elif w.inventoryWeight() + thing.v_weight >= 7:
            out("Jag orkar inte bära fler grejor!")
        elif thing.v_size > entities.SIZE_BIG:
            out("{} är för stor{}.".format(world.determinedForm(thing, True), postAdj))
        elif thing.v_weight > entities.WEIGHT_HEAVY:
            out("{} är för tung{}.".format(world.determinedForm(thing, True), postAdj))
        else:
            res = thing.take()
            if not res:
                outFailMsg(thing, "Det gick inte att ta {}.".format(world.determinedForm(thing)))
            else:
                out("Jag tar {0}. {1}".format(world.determinedForm(thing), \
                    world.getDetailedDescription(thing)))
    else:
        out("Jag kan ju inte ta {}.".format(args[0]))  
    
def cmdDrop(w, args):
    ''' Drops thing '''
    if len(args) == 0:
        out("Jag släpper ingenting, och känner mig aningens snål.")
        return
    stuff = w.player.contains()
    stuff += w.getPersonsInRoom(w.playerRoomIx())
    thing = world.findInEntityList(stuff, args[0])
    if thing == None:
        outNoThing(args[0], cmdDrop)
        return
    
    if isinstance(thing, entities.Thing):
        res = thing.drop()
        if not res:
            outFailMsg(thing, "Det gick inte att släppa {}.".format(world.determinedForm(thing)))
        else:
            out("Jag släpper {}.".format(world.determinedForm(thing)))

    else:
        out("Jag kan ju inte släppa {}.".format(args[0]))  
    
def cmdUse(w, args):
    ''' Uses a thing '''
    global _access_lastThing
    if len(args) == 0:
        out("Jag använder ingenting, men blir ändå trött.")
        return
    stuff = w.getAllAccessibleEntitiesInCurrentRoom()
    thing = world.findInEntityList(stuff, args[0], _access_lastThing)
    if thing == None:
        _access_lastThing = None
        outNoThing(args[0], cmdUse)
        return
    
    _access_lastThing = thing
    res = thing.use()
    if not res:
        outFailMsg(thing, "Det funkade inte.")
    
def cmdTalk(w, args):
    ''' Talks to someone '''
    if len(args) == 0:
        out(random.choice(["Jag pratar rätt ut i luften. Dåligt tecken.", \
            "Jag pratar rätt ut i luften. Konstigt nog får jag svar. Synd jag glömt vad jag sa."]))
        return
    stuff = w.getAllAccessibleEntitiesInCurrentRoom()
    thing = world.findInEntityList(stuff, args[0], _access_lastThing)
    if thing == None:
        outNoThing(args[0], cmdTalk)
        return
    
    if isinstance(thing, entities.Person):
        res = thing.use()
        if not res:
            outFailMsg(thing, "Det funkade inte.")
    else:
        out("Jag viskar ömt till {}, men den svarar inte.".format(world.determinedForm(thing)))
        
        
    
    
def cmdMove(w, args):
    ''' Moves a thing '''
    if len(args) == 0:
        out("Jag flyttar ingenting, men ändå ser jag rörelse.")
        return
    elif len(args) == 1:
        out("Flytta vart? Fram eller bak?")
        return
    elif args[1].lower() not in ["fram", "bak", "fr", "ba"]:
        out("Alltså, jag fattar inte åt vilket håll {} är. Fram eller bak?".format(args[1]))
        return
    stuff = w.getAccessibleThingsInRoom(w.playerRoomIx())
    stuff += w.getPersonsInRoom(w.playerRoomIx())
    thing = world.findInEntityList(stuff, args[0])
    
    # Hack to try to find a free chair
    while isinstance(thing, entities.Chair) and thing.sitterPerson != None:
        stuff.remove(thing)
        nextThing = world.findInEntityList(stuff, args[0])
        if nextThing != None:
            thing = nextThing 
        else:
            break
    
    if thing == None:
        outNoThing(args[0], cmdMove)
        return
    
    if args[1].lower() in ["fram", "fr"]:
        delta = -1
    else:
        delta = 1
    
    if isinstance(thing, entities.Thing):
        if w.playerRoomIx() == 1 and delta < 0 or w.playerRoomIx() == len(w.rooms) and delta > 0:
            out("Det går inte att flytta {} dit ju.".format(world.determinedForm(thing)))
            return
        
        res = thing.move(delta)
        if not res:
            failReason = ["Hnnnngggg.. Gwwwaaah! Ah, det går inte.",
                          "{} vägrar röra på sig.".format(world.determinedForm(thing, True)),
                          "Komsi komsi.. Nä. Gick inte."]
            outFailMsg(thing, random.choice(failReason))
        else:
            out("Flyttade in {} i {}.".format(world.determinedForm(thing), \
                w.roomForIndex(w.playerRoomIx() + delta).name()))
            w.player.moveRoom(delta)
            updateInputPrefix(w)
            cmdRoomInfo(w, args)

    else:
        out("Jag kan ju inte flytta på {}.".format(args[0]))  
    
def cmdKick(w, args):
    ''' Kicks a thing '''
    if len(args) == 0:
        out("Jag sparkar i luften, råkar göra en halv saltomoral och landar på ryggen. " + \
            "Skadade som tur var inget, förutom min självkänsla.")
        return
    stuff = w.getAllAccessibleEntitiesInCurrentRoom()
    thing = world.findInEntityList(stuff, args[0])
    if thing == None:
        outNoThing(args[0], cmdKick)
        return
    
    if isinstance(thing, entities.Thing):
        res = thing.kick()
        if not res:
            if thing.v_size == entities.SIZE_HUGE or thing.v_weight >= entities.WEIGHT_HEAVY:
                defFailMsg = "Äh, skulle bara få ont i foten."
            elif thing.v_size == entities.SIZE_SMALL:
                defFailMsg = "Äh, skulle bara få missa den."
            else:
                defFailMsg = "Nä, jag tänker inte sparka {}.".format(world.determinedForm(thing))
                
            outFailMsg(thing, defFailMsg)
    else:
        out(random.choice(["Make love not war", "Jag tror inte på våld.", "Jag är inget psyko."]))
        
def cmdSave(w, args):
    ''' Stores world to disk '''
    if len(args) == 0:
        fname = "adsave.json"
    else:
        fname = args[0]
    w.storeWorld(fname) 
    
def cmdLoad(w, args):
    ''' Restores world from disk '''
    if len(args) == 0:
        fname = "adsave.json"
    else:
        fname = args[0]
    w.loadWorld(fname)
    
def cmdExit(w, args):
    ''' Exits game '''
    #pylint: disable=unused-argument
    kill()
    
def parseLine(w, line):
    ''' Parses a line of input '''
    cmds = line.split(" ")
    if not cmds[0] in commandDefs.keys():
        out(world.stringify(["Vad betyder det?", "Va?", "Öööh...", "Fattar inte.", "Does not compute.", \
            "Ingår inte i min vokabulär.", "Syntaktiskt fel.", "{}?".format(cmds[0]), "Illegal exception.", \
            "Just what do you think you're doing, {}?".format(w.player.name()), \
            "Det finns pingviner som skriver bättre än så."]))
    else:
        w.lock.acquire()
        commandDefs[cmds[0]][0](w, cmds[1:])
        if len(w.outputQueue) > 0:
            for outputSpec in w.outputQueue:
                for e in outputSpec:
                    if isinstance(e, float):
                        sleep(e)
                    else:
                        out(e)
        w.outputQueue = list()
        w.lock.release()
        
_w = None

def outputDirect(line):
    ''' outputs something directly '''
    out(line)

def advterm_line_cb(line):
    ''' advterm line callback '''
    if _kill_next:
        kill()
    else:
        if world.inConversation:
            advrant.parseQuestion(_w, line)
        else:
            parseLine(_w, line)
        
def kill():
    ''' Ends the UI '''
    advterm.kill()

def killNext():
    ''' Ends the UI on next input '''
    global _kill_next
    advterm.inputPrefix("")
    _kill_next = True

def start(w, startText):
    ''' Starts the UI '''
    global _w
    _w = w
    commandDefs["i"] = (cmdRoomInfo, "Beskriver rummet.", "")
    commandDefs["info"] = commandDefs["i"]
    commandDefs["h"] = (cmdHelp, "Visar möjliga kommandon.", "")
    commandDefs["hjälp"] = commandDefs["h"]
    commandDefs["?"] = commandDefs["h"]
    commandDefs["fr"] = (cmdForward, "Gå framåt.", "")
    commandDefs["fram"] = commandDefs["fr"]
    commandDefs["ba"] = (cmdBack, "Gå bakåt.", "")
    commandDefs["bak"] = commandDefs["ba"]
    commandDefs["t"] = (cmdExamine, "Undersök rum eller sak.", "(<sak>)")
    commandDefs["titta"] = commandDefs["t"]
    commandDefs["o"] = (cmdObjects, "Lista alla saker i rummet.", "")
    commandDefs["objekt"] = commandDefs["o"]
    commandDefs["se"] = commandDefs["t"]
    commandDefs["ö"] = (cmdOpen, "Öppnar sak.", "<sak>")
    commandDefs["öppna"] = commandDefs["ö"]
    commandDefs["st"] = (cmdClose, "Stänger sak.", "<sak>")
    commandDefs["stäng"] = commandDefs["st"]
    commandDefs["inv"] = (cmdInventory, "Lista alla saker jag bär på.", "")
    commandDefs["inventarier"] = commandDefs["inv"]
    commandDefs["ta"] = (cmdTake, "Ta en sak.", "<sak>")
    commandDefs["sl"] = (cmdDrop, "Släpp en sak.", "<sak>")
    commandDefs["släpp"] = commandDefs["sl"]
    commandDefs["a"] = (cmdUse, "Använd/ge en sak, prata med person.", "<sak|person>")
    commandDefs["använd"] = commandDefs["a"]
    commandDefs["p"] = (cmdTalk, "Prata med person.", "(<person>)")
    commandDefs["prata"] = commandDefs["p"]
    commandDefs["f"] = (cmdMove, "Flytta en sak framåt eller bakåt.", "<sak> <fram|fr|bak|ba>")
    commandDefs["flytta"] = commandDefs["f"]
    commandDefs["s"] = (cmdKick, "Sparka på en sak.", "<sak>")
    commandDefs["sparka"] = commandDefs["s"]
    commandDefs["save"] = (cmdSave, "Spara spelet", "(<filnamn>)")
    commandDefs["load"] = (cmdLoad, "Ladda sparat spel", "(<filnamn>)")
    commandDefs["exit"] = (cmdExit, "Avsluta spelet", "")
    
    #while w.isRunning():
    #    line = input("\n[{}] ".format(w.playerRoom().name()))
    #    parseLine(w, line)
    
    updateInputPrefix(w)
    advterm.startInput(advterm_line_cb, echo=True, initialText=startText)
