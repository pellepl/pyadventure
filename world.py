#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Office Adventure
World engine

@author: petera
'''


import threading
import json
import time 
import random
import inspect

import entities
import advai
import advrant
import ui

DEBUG = True

ACH_PEDRIK_WOKEN = "pedrik_woken"
ACH_HELPED_GUNTHER = "gunther_help"
ACH_JEAN_NICOTINATED = "jean_nico"
ACH_FISH_DANCE = "fishdance"
ACH_GRINGO_KEY = "key_found"
ACH_MENU = "menu_altered"
ACH_FOUND_COFFEE_BUG = "coffe_bug_found"
ACH_FIXED_COFFEE_BUG = "coffe_bug_fixed"
ACH_MISSILE_COMMANDER = "missile_commander"
ACH_FRATRIK_BEATEN = "beat_fratrik"
ACH_JEAN_MENU_CHECK = "jean_menu_check"
ACH_PEDRIK_MENU_CHECK = "pedrik_menu_check"
ACH_REZOMBIFICATOR = "pedrik_rezombified"
ACH_MINDREADER = "mindreader"
ACH_CATTOSSER = "cattosser"

ACH_COUNT = 15

achievement_texts = dict()

inConversation = False
conversationPerson = None

class World:
    ''' World class '''
    
    def __init__(self):
        ''' Ctor '''
        # following must be persisted
        self.rooms = list()
        self.persons = list()
        self.player = None
        self.achievements = list()
        self.staticRants = list()
        
        # following is dynamic
        self.tickables = list()
        self.lock = threading.RLock()
        self.running = True
        self.ticks = 0
        self.outputQueue = list()
        
    def _createWorldFromDict(self, jGame):
        ''' Creates the world from a dict '''
        module = __import__("entities")
            
        # create rooms with their objects
        self.rooms = list()
        for jRoom in jGame["rooms"]:
            room = getattr(module, jRoom["v_class"])(self, jRoom["v_name"], jRoom["roomIx"])
            setAttributesForThing(room, jRoom)
            self.rooms.append(room)
            self._parseContainerTree(room, jRoom)
            
        # create persons
        self.persons = list()
        for jPerson in jGame["persons"]:
            person = getattr(module, jPerson["v_class"])(self, jPerson["v_name"])
            setAttributesForThing(person, jPerson)
            self.persons.append(person)
            self._parseContainerTree(person, jPerson)
        
        # create player
        self.player = entities.Player(self, jGame["player"]["v_name"])
        setAttributesForThing(self.player, jGame["player"])
        self._parseContainerTree(self.player, jGame["player"])

        self.player.roomIx = jGame["player"]["roomIx"]
        
        self.tickables = list()


    def buildDefaultWorld(self):
        ''' Builds the default world '''
        wfile = open("initial.json", "r")
        jGameState = json.load(wfile)
        jGame = jGameState["game"]
        self._createWorldFromDict(jGame)
        advrant.buildRants(jGame["rants"])
        
    def storeWorld(self, filename):
        ''' Stores the world as json '''
        top = dict()
        top["game"] = dict()
        game = top["game"]
        game["rooms"] = list()
        for room in self.rooms:
            dRoom = self._dictifyEntity(room)
            game["rooms"].append(dRoom)
        game["persons"] = list()
        for person in self.persons:
            dPerson = self._dictifyEntity(person)
            game["persons"].append(dPerson)
        game["player"] = self._dictifyEntity(self.player)
        game["achievements"] = list(self.achievements)  
        game["staticRants"] = list(self.staticRants)
        
        with open(filename, 'w') as outfile:
            json.dump(top, outfile, ensure_ascii=True, indent=2)
            outputDirect("[Sparade nuvarande spel som {}]".format(filename))
            
    def loadWorld(self, filename):
        ''' Loads the world from json '''
        global inConversation, conversationPerson
        inConversation = False
        conversationPerson = None
        wfile = open(filename, "r")
        jGameState = json.load(wfile)
        jGame = jGameState["game"]
        self._createWorldFromDict(jGame)
        self.setup()
        self.achievements = jGame["achievements"]
        self.staticRants = jGame["staticRants"]
        outputDirect("[Laddade spel från {}]".format(filename))
        ui.updateInputPrefix(self)
        
    def _dictifyEntity(self, e):
        ''' dictifies an entity '''
        d = dict()
        d["v_class"] = e.__class__.__name__
        members = vars(e)
        for m in members:
            if not m.startswith("v_") and not m.startswith("_"):
                d[m] = members[m]
            elif m == "v_name":
                d[m] = members[m]
        
        if "v_container" in members:
            d["v_container"] = list()
            for subE in e.v_container:
                d["v_container"].append(self._dictifyEntity(subE))
                
        
        return d
        
    def _parseContainerTree(self, thing, jSpec):
        ''' Traverses json tree and builds things thereafter '''
        if not "v_container" in jSpec:
            return
        module = __import__("entities")
        for jSubThing in jSpec["v_container"]:
            # create instance
            subThing = getattr(module, jSubThing["v_class"])(self)
            
            # other attributes
            setAttributesForThing(subThing, jSubThing)
            
            subThing.v_parentEntity = thing
            thing.v_container.append(subThing)
            dbg("adding {0} to {1}".format(subThing.v_name, thing.v_name))
    
            # parse further down
            self._parseContainerTree(subThing, jSubThing)
    


    def _traverseEntitiesForTickable(self, entity):
        ''' Traverses entity and its descendants looking for tick funcs '''
        if entity.v_ticker != None:
            self.tickables.append(entity)
        for subEntity in entity.v_container:
            self._traverseEntitiesForTickable(subEntity)
            
    def setup(self):
        ''' Collects necessary info on world before start '''
        # Make a list of all tickables
        for person in self.persons:
            person.v_ticker = advai.personTick
        for person in self.persons:
            self._traverseEntitiesForTickable(person)
        for room in self.rooms:
            self._traverseEntitiesForTickable(room)
            
    def roomForIndex(self, roomIx):
        ''' Returns room object for room index '''
        for room in self.rooms:
            if room.roomIx == roomIx:
                return room
        return None
    
    def addAchievment(self, achievement):
        ''' Adds an achievment '''
        if achievement not in self.achievements:
            self.achievements.append(achievement)
            if achievement in achievement_texts:
                self.output(["\n   *** {} klarade just prestationen {} ***\n".format(self.player.name(), \
                    achievement_texts[achievement])])
    
    def checkAchievment(self, achievement):
        ''' Checks an achievment '''
        return achievement in self.achievements
    
    def getAccessibleThingsInRoom(self, roomIx, recurse=True):
        ''' Returns list of all things that can be seen in a room '''
        room = self.roomForIndex(roomIx)
        objs = list()
        self._accessibleContainableRecurse(room, objs, recurse)
        return objs
        
    def _accessibleContainableRecurse(self, containable, objList, recurse):
        ''' Recurses thru containers collecting all things that can be seen '''
        if not hasattr(containable, "v_container"):
            return
        for thing in containable.v_container:
            objList.append(thing)
            if hasattr(thing, "v_lid") and thing.v_lid and thing.closed:
                continue
            if recurse:
                self._accessibleContainableRecurse(thing, objList, True)
            
    def getPersonsInRoom(self, roomIx):
        ''' Returns list of persons in room '''
        present = list()
        for person in self.persons:
            if person.roomIx == roomIx:
                present.append(person)
        return present
            
    def isRunning(self):
        ''' Returns if world is up or has ended '''
        return self.running
    
    def playerRoom(self):
        ''' Returns current room for player '''
        return self.roomForIndex(self.player.roomIx)
    
    def playerRoomIx(self):
        ''' Returns current room index for player '''
        return self.player.roomIx
    
    def getAllAccessibleEntitiesInCurrentRoom(self):
        ''' returns list of all accessible entities in current room '''
        things = self.getAccessibleThingsInRoom(self.playerRoomIx())
        things += self.player.contains()
        things += self.getPersonsInRoom(self.playerRoomIx())
        return things
    
    def inventoryCount(self):
        ''' returns number of items in inventory '''
        return len(self.player.v_container)

    def inventorySize(self):
        ''' returns summed size of inventory '''
        return sum(t.v_size for t in self.player.v_container)

    def inventoryWeight(self):
        ''' returns summed weight in inventory '''
        return sum(t.v_weight for t in self.player.v_container)
    
    def output(self, outputSpec):
        ''' queues a ui output, where spec is a list of strings and waitfloats '''
        if isinstance(outputSpec, str):
            outputSpec = [outputSpec]
        self.outputQueue.append(outputSpec)
        
    def onPersonSpeech(self, person, s):
        ''' output a persons exclamation '''
        if person.roomIx == self.playerRoomIx():
            outputDirect("{}: '{}'".format(person.name(), s))
        
    def onPersonMovement(self, person, preRoomIx):
        ''' Notifies that a person has moved '''
        if person.roomIx == self.playerRoomIx():
            outputDirect("{} kommer in i rummet.".format(person.name()))
        elif preRoomIx == self.playerRoomIx():
            outputDirect("{} går in till {}.".format(person.name(), \
                self.roomForIndex(person.roomIx).name()))
        
    def onPersonGeneric(self, person, s):
        ''' Notifies that a person does something '''
        if person.roomIx == self.playerRoomIx():
            outputDirect(s)
            
def success(w):
    ''' Game completed '''
    ui.reset()
    outputDirect("\n\nJag öppnar sakta dörren och får nästan blunda av det varma solskenet " + \
                 "som slår mot mitt ansikte. Jag hör fåglarna och människorna där ute.\n\n" + \
                 "När jag tittar på Jean har han ett brett leende på läpparna. " + \
                 "Fratrik skrattar, och Pedrik ser nästan ut att gråta (kan ju vara bananallergin).\n\n" + \
                 "Den varma brisen blåser i håret. Konstigt nog sker allt i slow motion. Vi fattar " + \
                 "varandras händer och tar hoppsasteg ut.\n\n" + \
                 "Ut, mot de väntande burgarna!\n\n" + \
                 "     *** SLUT ***\n\n")
    outputDirect("Du har upptäckt {}% av spelet.\n\n".format(int((100*len(w.achievements))/ACH_COUNT)))
    outputDirect("Tryck RETUR för att avsluta.\n")
    ui.killNext()
            
def enterConversation(w, person):
    ''' Enters converation mode '''
    global inConversation, conversationPerson
    if not advrant.displayRants(w, person):
        outputDirect("{} har inget att prata om.".format(person.name()))
        inConversation = False
    else:
        inConversation = True
        conversationPerson = person
        person.pushOperation("speakto", "_player")
        person.opTimer = 0
        ui.updateInputPrefix(w)

def leaveConversation(w, person):
    ''' Leaves conversation mode '''
    global inConversation
    outputDirect(random.choice(["Diskussionen med {} är avslutad.".format(person.name()), \
        "Färdigsnackat.", "Klart slut."]))
    inConversation = False
    ui.updateInputPrefix(w)
    person.opTimer = 0

def outputDirect(line):
    ''' outputs something directly '''
    ui.out(line)

def getEntity(containable, entityPath):
    '''
    Finds thing-object in given containable by path,
    returns None if not found
     
    e.g getEntity(world.roomForIndex(2), "fruktskål/banan")
    '''
    searchPath = entityPath.split("/")
     
    for curDir in searchPath:
        if containable == None:
            break
        dbg("finding {0} in {1}".format(curDir, containable.v_name))
        if hasattr(containable, "v_container"):
            if len(containable.v_container) == 0:
                containable = None
                break 
            for o in containable.v_container:
                dbg("  check {0}".format(o.v_name))
                if o.v_name == curDir:
                    containable = o
                    dbg("  found")
                    break
                else:
                    dbg("  not found")
                    containable = None
        else:
            dbg("  not a containable")
            containable = None
         
    return containable
    
def stringify(desc):
    ''' Concocts a string '''
    if isinstance(desc, str):
        ret = desc

    if isinstance(desc, list):
        ret = random.choice(desc)
        
    if isinstance(ret, list):
        l = ret
        ret = ""
        for s in l:
            if isinstance(s, str):
                ret += s
            elif isinstance(s, list):
                ret += random.choice(s)
    
    return ret

def listify(l):
    ''' Concocts a Swedish list '''
    ret = ""
    ix = 0
    for s in l:
        if isinstance(s, entities.Entity):
            ret += s.name()
        else:
            ret += s
        ix += 1
        if ix == len(l) - 1:
            ret += " och "
        elif ix < len(l) - 1:
            ret += ", "
    return ret

def stringifyContents(l):
    ''' Groups and returns a string describing all objects in given list '''
    stuff = list(l)
    strList = list()
    while len(stuff) > 0:
        preLen = len(stuff)
        thing = stuff[0]
        stuff.remove(thing)
        stuff = [otherThing for otherThing in stuff if otherThing.name() != thing.name()]
        count = preLen - len(stuff)
        if count > 12:
            strList.append("{} {}".format(count, thing.v_namePluralis))
        elif count == 1:
            strList.append("{} {}".format(thing.v_genus, thing.v_name))
        else:
            strList.append("{} {}".format(["två", "tre", "fyra", "fem", "sex", "sju", "åtta", \
                "nio", "tio", "elva", "tolv"][count - 2], thing.v_namePluralis))
            
    return listify(strList)

def capitalizeFirst(s):
    ''' Makes first letter uppercase '''
    return s[0:1].upper() + s[1:]

def determinedForm(thing, capitalize=False):
    ''' Returns Swedish determined form for a thing '''
    name = thing.name()
    if name[-1:] not in "aeiouyåäö" and name[-2:] not in ["or", "el", "er"]:
        name += "e"
    if thing.v_genus == "ett":
        name += "t"
    else:
        name += "n"
    if capitalize:
        return capitalizeFirst(name)
    else:
        return name

def getDetailedDescription(thing):
    ''' Returns a detailed description of the thing or entity ''' 
    desc = thing.description()
    if isinstance(thing, entities.Thing):
        if thing.v_lid and thing.closed:
            desc += " " + determinedForm(thing, True) + " är stängd."
        elif len(thing.contains()) > 0:
            desc += " Det finns " + stringifyContents(thing.contains()) + " " + \
                thing.v_preposition +" " + determinedForm(thing) + "."
        elif len(thing.contains()) == 0 and thing.v_lid:
            desc += " " + determinedForm(thing, True) + " är öppen men tom."
    elif isinstance(thing, entities.Person):
        pdesc = advai.personActionDescription(thing)
        if pdesc != None:
            desc += " " + pdesc
    return desc
    
def getActionDescription(person):
    ''' Returns a tricorder description of the persons actions ''' 
    return advai.personTricorderDescription(person)
    

def findInEntityList(l, name, startOffs=None):
    ''' Returns object with name in list, or None if nothing found '''
    offs = 0
    res = None
    if startOffs != None:
        try:
            offs = l.index(startOffs)
            offs += 1
        except ValueError:
            pass

    for i in range(0, len(l)):
        ix = (offs + i) % len(l)
        e = l[ix]
        if e.name().lower().startswith(name.lower()):
            res = e
            break
    return res
        
            
def setAttributesForThing(thing, jSpec):
    ''' Finds all nonsystem attributes and sets them on the object '''
    for attr in jSpec.keys():
        if attr.startswith("v_"):
            continue
        dbg("setting {0}.{1}={2}".format(thing.v_name, attr, jSpec[attr]))
        thing.__dict__[attr] = jSpec[attr]

def worldTicker(world):
    ''' Ticks the world one step '''
    while True:
        time.sleep(0.5)
        world.lock.acquire()
        for tickable in world.tickables:
            tickable.v_ticker(tickable)
        world.ticks += 1
        world.lock.release()

def startWorldTicker(world):
    ''' Starts the world clock '''
    timer = threading.Thread(target=worldTicker, name="WorldTicker", args=(world,))
    timer.setDaemon(True)
    timer.start()
    
def init(playerName, debug=False):
    ''' Initiates game '''
    global DEBUG
    DEBUG = debug
    
    achievement_texts[ACH_PEDRIK_WOKEN] = "DEZOMBIEFIKATOR"
    achievement_texts[ACH_JEAN_NICOTINATED] = "NIKOTINPUSHER"
    achievement_texts[ACH_HELPED_GUNTHER] = "SHEETSPRIDARE"
    achievement_texts[ACH_FISH_DANCE] = "FISKDANSARE"
    achievement_texts[ACH_GRINGO_KEY] = "NYCKELMÄSTARE"
    achievement_texts[ACH_MENU] = "MENYMANIPULATOR"
    achievement_texts[ACH_FIXED_COFFEE_BUG] = "KONTORSHJÄLTE"
    achievement_texts[ACH_MISSILE_COMMANDER] = "ARKADCHAMPION"
    achievement_texts[ACH_REZOMBIFICATOR] = "REZOMBIEFIKATOR"
    achievement_texts[ACH_MINDREADER] = "TANKELÄSARE"
    achievement_texts[ACH_CATTOSSER] = "KATTKASTARE"
    
    dbg("Game init...")
    w = World()
    w.buildDefaultWorld()
    w.player.v_name = playerName
    w.setup()
    startWorldTicker(w)
    dbg("Game initiated successfully...")
    return w
    
def dbg(s):
    ''' output debug info '''
    if DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        ui.out("\tDBG[{:<20}]: {}".format(calframe[1][3], s))

def main():
    ''' Test function '''
    init("Testplayer")

if __name__ == '__main__':
    main()
    