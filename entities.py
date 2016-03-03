'''
Created on Apr 26, 2015

@author: petera
'''

import random
import world
import retro
import ui

THING_OPENABLE = True

SIZE_HUGE = 3
SIZE_BIG = 2
SIZE_NORMAL = 1
SIZE_SMALL = 0

WEIGHT_MASSIVE = 3
WEIGHT_HEAVY = 2
WEIGHT_MEDIUM = 1
WEIGHT_LITTLE = 0

class Entity(object):
    ''' Entity class '''
    def __init__(self, w, name, namePluralis="", genus=""):
        ''' Constructor '''
        self.v_name = name # ex "banan"
        if len(namePluralis) == 0:
            self.v_namePluralis = name + "er"
        else:
            self.v_namePluralis = namePluralis # ex "bananer"
        if len(genus) == 0:
            self.v_genus = "1"
        else:
            self.v_genus = genus # ex "en"
        self.v_preposition = "i"
            
        self.v_ticker = None
        self.v_container = list()
        self.v_failMsg = None
        self.v_world = w
        
        
    def description(self):
        ''' Returns description of an entity '''
        return world.stringify(self.descr)
    
    def name(self):
        ''' Returns name of this entity '''
        return world.stringify(self.v_name)
    
    def contains(self):
        ''' Returns what this entity contains '''
        return list(self.v_container)

    def use(self):
        #pylint: disable=no-self-use
        ''' Default use command '''
        return False
    
    def kick(self):
        #pylint: disable=no-self-use
        ''' Default kick command '''
        return False
    
    def failMsg(self):
        ''' Returns error string on failed operation '''
        s = self.v_failMsg
        self.v_failMsg = None
        return s
        
class Person(Entity):
    ''' Person class '''
    def __init__(self, w, name):
        ''' Constructor '''
        super().__init__(w, name)
        self.roomIx = 0
        self.homeRoomIx = 0
        self.opStack = list()
        self.opTimer = 0
        self.curOp = None
        self.toilet = 0
        self.talk = 0
        self.eat = 0
        self.workMin = 30
        self.workMax = 30
        self.sleeping = False

    def description(self):
        ''' Returns description of a person '''
        s = random.choice([
            "En ståtlig herre!", "Ett utmärkt exemplar!", "En underbar människa!", "En hyvens karl!",
            "En fantastisk medarbetare!", "En person utan motstycke!", "Helt klart en presidentkandidat!",
            "En riktig hunk!"
            ])
        if random.randint(0, 10) == 5:
            s += " " + world.stringify(self.descr)
        
        return s
    
    def pushOperation(self, op, arg=None):
        ''' Pushes an operation for this person '''
        self.opStack.insert(0, {"func" : op, "arg" : arg})
        
    def popOperation(self):
        ''' Pops current operation '''
        if len(self.opStack) > 0:
            self.opStack.pop(0)
        
    def peekOperation(self):
        ''' Peeks current operation '''
        if len(self.opStack) == 0:
            return {"func":None, "arg":None}
        return self.opStack[0]
    
    def curOperation(self):
        ''' Checks current operation '''
        return self.curOp

    def unseat(self):
        ''' Unseats if sitting '''
        stuff = self.v_world.getAccessibleThingsInRoom(self.roomIx)
        myChair = next((thing for thing in stuff if isinstance(thing, Chair) \
            and thing.sitterPerson == self.name()), None)
        if myChair != None:
            myChair.sitterPerson = None

    def use(self):
        ''' Person use command '''
        if self.curOp["func"] == "speakto" or self.curOp["func"] == "etermeeting":
            self.v_failMsg = "{} pratar redan med {}.".format(self.name(), self.curOp["arg"])
            return False
        if self.name() == "Gringo" and not self.v_world.checkAchievment(world.ACH_GRINGO_KEY):
            self.v_failMsg = random.choice( \
                ["Gringo: 'Hej {}, hinner inte snacka nu. Sorry.'".format(self.v_world.player.name()), \
                "Gringo: '{} - lite busy nu. Senare.'".format(self.v_world.player.name()), \
                "Gringo: 'Fullt ös medvetslös, kommer förbi när jag hinner.'" \
                ])
            return False
        world.enterConversation(self.v_world, self)
        return True
        
class Player(Entity):
    ''' Player class '''
    def __init__(self, w, name):
        ''' Constructor '''
        super().__init__(w, name)
        self.roomIx = 0
        self.elevated = False
    
    def moveRoom(self, delta):
        ''' Moves player relative to current room '''
        self.elevated = False
        self.roomIx += delta
        

        
class Room(Entity):
    ''' Room class '''

    def __init__(self, w, name, roomIx):
        ''' Constructor '''
        super().__init__(w, name)
        self.roomIx = roomIx
        self.descr = "N/A"
        

class Thing(Entity):
    ''' Thing class '''
    
    #pylint: disable=too-many-arguments
    def __init__(self, w, name, namePluralis="", genus="", lid=False, weight=WEIGHT_MASSIVE, size=SIZE_HUGE):
        ''' Constructor '''
        super().__init__(w, name, namePluralis, genus)
        self.v_lid = lid
        if lid:
            self.closed = True
        self.v_parentEntity = None
        self.v_weight = weight
        self.v_size = size
    
    def open(self):
        ''' Default open operation '''
        if self.v_lid:
            self.closed = False
            return True
        else:
            return False        
    
    def close(self):
        ''' Default close operation '''
        if self.v_lid:
            self.closed = True
            return True
        else:
            return False        
    
    def take(self):
        ''' Default take operation '''
        self.v_parentEntity.v_container.remove(self)
        self.v_world.player.v_container.append(self)
        self.v_parentEntity = self.v_world.player
        return True

    def drop(self):
        ''' Default drop operation '''
        self.v_parentEntity.v_container.remove(self)
        self.v_world.roomForIndex(self.v_world.player.roomIx).v_container.append(self)
        self.v_parentEntity = self.v_world.roomForIndex(self.v_world.player.roomIx)
        return True
    
    def putInto(self, containable):
        ''' Default put into operation '''
        self.v_parentEntity.v_container.remove(self)
        containable.v_container.append(self)
        self.v_parentEntity = containable
        return True
    
    def move(self, delta):
        ''' Default move command '''
        #pylint: disable=unused-argument, no-self-use
        return False
    
    def currentRoomIx(self):
        ''' Figures out the room ix for this thing '''
        curObj = self
        while curObj != None and not hasattr(curObj, "roomIx"):
            if not hasattr(curObj, "v_parentEntity"):
                return 0
            curObj = curObj.v_parentEntity
        
        if not hasattr(curObj, "roomIx"):
            return 0
        else:
            return curObj.roomIx
    
class Menu(Thing):
    ''' Menu class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "meny", "menyer", "en", size=SIZE_HUGE)
        self.written = False

    def description(self):
        ''' Returns description  '''
        s = "En restaurangmeny skriven på whiteboard. Det står:\n"
        if self.written:
            s += "          ~~~ Dagens rätt ~~~\nSuper nyttig bön sallad med kul potatis.\n"
        else:
            s += "           ~~~ Dagens rätt ~~~\nMustig kött gryta och stekt kyckling lever.\n"
        return s

class Microwave(Thing):
    ''' Microwave class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "mikro", "mikros", "en", THING_OPENABLE, size=SIZE_HUGE, weight=WEIGHT_HEAVY)

    def description(self):
        ''' Returns description  '''
        return "En vit mikrovågsugn, rätt kladdig."
    
    def use(self):
        ''' Microwave use operation '''
        prilla = world.getEntity(self.v_world.player, "prilla")
        if prilla != None:
            mikro = world.getEntity(self.v_world.playerRoom(), "mikro")
            prilla.dry = True
            prilla.putInto(mikro)
            mikro.closed = True
            self.v_world.output(["Jag stoppar in prillan i mikron och sätter den på maxeffekt i 3 sekunder...", \
                3.0, "*Pling*"])
            return True
        
        return False
 

class Drawer(Thing):
    ''' Drawer class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "hurts", "hurtsar", "en", THING_OPENABLE, size=SIZE_HUGE, weight=WEIGHT_MASSIVE)

    def description(self):
        ''' Returns description  '''
        return "En vit hurts." 

class Chair(Thing):
    ''' Chair class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "stol", "stolar", "en", size=SIZE_HUGE, weight=WEIGHT_HEAVY)
        self.sitterPerson = None

    def description(self):
        ''' Returns description  '''
        s = "En ergonomiskt utformad svart snurrstol. "
        if self.sitterPerson != None:
            s += self.sitterPerson + " sitter i den."
        return s 
    
    def use(self):
        ''' Chair use command '''
        if self.sitterPerson != None:
            self.v_failMsg = "{} verkar inte vilja ha mig i knät.".format(self.sitterPerson)
        else:
            if self.v_world.playerRoomIx() != 3:
                self.v_failMsg = "Mysigt. Men här kan jag inte sitta hela dan."
            else:
                self.v_world.output(["Hmmm.. Istället för att sätta mig klättrar jag upp på stolen.", 1.9, "Så ja."])
                self.v_world.player.elevated = True
                return True
        return False
    
    def move(self, delta):
        ''' Chair move command  '''
        if self.sitterPerson != None:
            s = self.sitterPerson + ": " + random.choice(["Hallå! Lägg av!", "Nähä du!", "Vad håller du på med?"])
            self.v_failMsg = s
            return False
        else:
            self.v_parentEntity.v_container.remove(self)
            self.v_parentEntity = self.v_world.roomForIndex(self.currentRoomIx() + delta)
            self.v_parentEntity.v_container.append(self)
            return True

class Fruitbowl(Thing):
    ''' Fruitbowl class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "fruktskål", "fruktskålar", "en", size=SIZE_HUGE, weight=WEIGHT_MEDIUM)
        self.v_ticker = self.fruitbowlTicker
        self._tickCount = 0
        
    def fruitbowlTicker(self, bowl):
        ''' Ticks the fruit bowl '''
        self._tickCount += 1
        if self._tickCount >= 10:
            self._tickCount = 0
        else:
            return
        # self == bowl here, but we use bowl to avoid pylint unused arg warning
        # refill fruit bowl if empty and not player is in room
        if len(bowl.v_container) == 0 and bowl.v_world.playerRoom() != bowl.v_parentEntity:
            x = random.randint(2, 6)
            while x > 0:
                i = random.randint(1, 3)
                if i == 1:
                    o = Banana(bowl.v_world)
                elif i == 2:
                    o = Apple(bowl.v_world)
                else:
                    o = Orange(bowl.v_world)
                bowl.v_container.append(o)
                o.v_parentEntity = bowl
                x -= 1

    def description(self):
        ''' Returns description  '''
        return "En blå fruktskål med vita fåglar på." 


class Banana(Thing):
    ''' Banana class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "banan", "bananer", "en", size=SIZE_BIG, weight=WEIGHT_MEDIUM)

    def description(self):
        ''' Returns description  '''
        return "En ekologisk banan. Gul och böjd." 

    def use(self):
        ''' Orange use func '''
        self.v_parentEntity.v_container.remove(self) 
        self.v_parentEntity = None
        self.v_world.output("Smasksmasksmask...")
        pedrik = next((p for p in self.v_world.persons if p.name() == "Pedrik"), None)
        if pedrik.roomIx == self.v_world.playerRoomIx():
            self.v_world.output(["Pedrik: 'Aaaaaaaaaah! Banaaaan!!!'", \
            "Pedrik kör ner näven i fickan och fiskar upp en handfull allergitabletter.", \
            "Efter han krasat i sig allihop ser han extremt sömnig ut.", \
            "Han hasar hastigt iväg mot toan."])
            self.v_world.addAchievment(world.ACH_REZOMBIFICATOR)
            pedrik.sleeping = True
            pedrik.roomix = 0
            toa = self.v_world.roomForIndex(3)
            door = world.getEntity(toa, "dörr")
            door.closed = True
            door.locked = True
        return True 

class Apple(Thing):
    ''' Apple class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "äpple", "äpplen", "ett", size=SIZE_NORMAL, weight=WEIGHT_MEDIUM)

    def description(self):
        ''' Returns description  '''
        return "Ett ekologiskt rött äpple." 

    def use(self):
        ''' Orange use func '''
        self.v_parentEntity.v_container.remove(self) 
        self.v_parentEntity = None
        self.v_world.output("Glufsglufsglufs...") 
        return True 

class Orange(Thing):
    ''' Orange class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "apelsin", "apelsiner", "en", size=SIZE_NORMAL, weight=WEIGHT_MEDIUM)

    def description(self):
        ''' Returns description  '''
        return "En ekologisk gul apelsin."
    
    def use(self):
        ''' Orange use func '''
        self.v_parentEntity.v_container.remove(self) 
        self.v_parentEntity = None
        self.v_world.output("Nomnomnom...")
        return True 

class Prilla(Thing):
    ''' Orange class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "prilla", "prillor", "en", size=SIZE_SMALL, weight=WEIGHT_LITTLE)
        self.inRoof = True
        self.dry = False
        
    def description(self):
        ''' Returns description  '''
        s = "En gammal prilla. "
        if self.inRoof:
            s += "Den sitter i taket, väldigt högt upp."
        else:
            if self.dry:
                s += "Mikrad, torr och fin - nästan som ny."
            else:
                s += "Den är alldeles kladdig. Uäck!"
        return s 
    
    def take(self):
        ''' Prilla take operation '''
        if self.inRoof:
            if self.v_world.player.elevated:
                res = super().take()
                if res:
                    self.inRoof = False
                    self.v_world.player.elevated = False
            else:
                self.v_failMsg = "Prillan sitter upp i taket, men jag ... försöker ... " + \
                    "nå ... den... Nä, den är för högt uppe."
                res = False 
        else:
            res = super().take()
        return res
    
    def use(self):
        ''' Prilla use command '''
        if self.inRoof:
            self.v_failMsg = "Den sitter fast upp i taket. Når den inte."
        else:
            persons = self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())
            if any(person.name() == "Jean" for person in persons):
                if self.dry:
                    self.v_world.output(["Jag räcker fram prillan till Jean.", \
                        "Jean bara stirrar på min hand.", \
                        "Helt plötsligt rycker han till och sliter åt sig prillan. Sakta stoppar " + \
                        "han den under läppen.",\
                        "Jean: 'Mmmmmmm... Tusen tack alltså. Känns genast bättre. Det var sista " + \
                        "gången jag slog dumma vad.'"])
                    self.v_parentEntity.v_container.remove(self)
                    self.v_parentEntity = None
                    self.v_world.addAchievment(world.ACH_JEAN_NICOTINATED)
                    return True
                else:
                    self.v_failMsg = "Jean: 'En gammal fuktig prilla? Nä tack! " + \
                        "Torr och ny ska den vara. Gärna lite varm.'"
            else:
                if self.dry:
                    self.v_failMsg = "Nej tack. Håller mig till tuggummi."
                else:
                    self.v_failMsg = "Om jag nu ska börja snusa gör jag inte det med en använd prilla."
            
        return False
    


class Battery(Thing):
    ''' Battery class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "batteri", "batterier", "ett", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "Ett blankt Painassonik batteri." 

    def use(self):
        ''' Battery use operation '''
        fan = world.getEntity(self.v_world.player, "fläkt")
        if fan != None:
            self.v_world.output("Jag sätter i det nya batteriet i fläkten.")
            self.v_parentEntity.v_container.remove(self)
            self.v_parentEntity = None
            fan.outOfBattery = False
            return True
            
        return False

class Fan(Thing):
    ''' Fan class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "fläkt", "fläktar", "en", size=SIZE_NORMAL, weight=WEIGHT_MEDIUM)
        self.outOfBattery = True

    def description(self):
        ''' Returns description  '''
        return "En liten röd handfläkt för varma dagar. Jättegullig!" 
    
    def use(self):
        ''' Fan use operation '''
        if self.outOfBattery:
            self.v_failMsg = "Den funkar inte. Batteriet verkar vara kass."
        else:
            # check Pedrik
            pedrik = next((p for p in self.v_world.persons if p.name() == "Pedrik"), None)
            coffee = next((c for c in self.v_world.player.contains() if isinstance(c, Coffee)), None)
            if pedrik.sleeping and self.v_world.playerRoomIx() == 3 and coffee != None:

                self.v_world.output("Jag håller det rykande kaffet precis vid springan till toalettdörren. Sen drar "+ \
                    "jag igång fläkten så doften verkligen kommer in." + \
                    " Jag hör ett hasande inifrån toaletten, sen börjar någon fumla med handtaget och låset. Pedrik "+ \
                    "ramlar ut, hugger åt sig muggen och drar i sig kaffet i ett svep.\n" + \
                    "Pedrik: 'Öööööååååuuueeehhhh...!'")
                pedrik.roomIx = 3
                pedrik.sleeping = False
                
                coffee.v_parentEntity.v_container.remove(coffee)
                coffee.v_parentEntity = None
                
                door = world.getEntity(self.v_world.roomForIndex(3), "dörr")
                door.locked = False
                
                self.v_world.addAchievment(world.ACH_PEDRIK_WOKEN)
            else:
                self.v_world.output("Den går igång med ett bzzzzz.")

            return True
        return False


class Oscilloscope(Thing):
    ''' Oscilloscope class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "oscilloskop", "oscilloskop", "ett", size=SIZE_BIG, weight=WEIGHT_HEAVY)

    def description(self):
        ''' Returns description  '''
        return "Ett fyrkanals- 200MHz Craptronix oscilloskop." 
    
    def take(self):
        ''' Oscilloscope take operation '''
        if not self.v_world.checkAchievment(world.ACH_HELPED_GUNTHER):
            persons = self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())
            if any(person.name() == "Gunther" for person in persons):
                self.v_failMsg = "När jag försöker ta oscilloskopet säger Gunther:\nGunther: 'Nein, " + \
                random.choice(["jag arbeitet mit dem oscilloskop.", "jag brauche es nu.", \
                               "verdammtes Mann! Siehst du nicht att jag använder det?",
                               "entschuldigung. Aber jag måste ha det nu."]) + "'"
            else:
                self.v_failMsg = "Nä, det är uppkopplat mot utvecklingskortet. Gunther kommer bli stocksauer."
            return False
        else:
            return super().take()

    def use(self):
        ''' Oscilloscope use operation '''
        if not self.v_world.checkAchievment(world.ACH_HELPED_GUNTHER):
            self.v_failMsg = "Gunther använder det nu."
        else:
            if self.v_world.playerRoomIx() == 2:
                if self.v_world.checkAchievment(world.ACH_FOUND_COFFEE_BUG):
                    self.v_failMsg = "Meeh - jag har ju redan hittat felet på kaffemaskinen."
                else:
                    self.v_world.output("Jag plockar av panelen till kaffemaskinen och kopplar in oscilloskopet.\n" + \
                        "När jag försöker köra en kopp kaffe ser jag på oscilloskopet att pumpen verkar styras med " + \
                        "I2C, men att högflankerna på datasignalen " + \
                        "stiger alltför sakta. Jag följer tracen i maskinen på DAT signalen - och " + \
                        "där! Det verkar ha kommit wiener melange på pull-up resistorn så den har " + \
                        "blivit kortsluten med 230V AC.\n\n" + \
                        "Den har helt brunnit upp! Jag kan pilla bort den med fingrarna. Hmm, bara jag " + \
                        "hade nåt att ersätta den med...")
                    self.v_world.addAchievment(world.ACH_FOUND_COFFEE_BUG)
                    return True
        return False

class DevboardGunther(Thing):
    ''' DevboardGunter class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "utvecklingskort", "utvecklingskort", "ett", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "Ett utvecklingskort, markerat med SMT32G413." 
    
    def take(self):
        ''' DevboardGunter take operation '''
        persons = self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())
        if any(person.name() == "Gunther" for person in persons):
            self.v_failMsg = "När jag försöker ta utvecklingskortet säger Gunther:\nGunther: 'Nein, " + \
            random.choice(["was machst du Mann!", "siesht du nicht att jag använder det?", \
                           "röhren nicht die kablarna!",
                           "bitte nicht! Ich debuggen för fullt ju."]) + "'"
        else:
            self.v_failMsg = "Nä, det är uppkopplat med massa sladdar. Gunther blir nog wütend om jag tar det."
        return False

    def use(self):
        ''' Oscilloscope use operation '''
        self.v_failMsg = "Gunther använder det nu."
        return False

class Datasheet(Thing):
    ''' Datasheet class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "datablad", "datablad", "ett", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "Ett datablad för SMT32G413 utvecklingskortet." 

    def use(self):
        ''' Datasheet use operation '''
        persons = self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())
        if any(person.name() == "Gunther" for person in persons):
            if self.v_world.playerRoomIx() == 6:
                self.v_world.output("Jag ger Gunther databladet.\n" + \
                    "Gunther: 'Ja! Es stimmt! Nu ska vi se vad som fallieren.'\n" + \
                    "Han bläddrar till slutet på databladet och lusläser schemat.\n" + \
                    "Gunther: 'Hmmm. Det ser ut som nån har placiert ein pull-up " + \
                    "resistor på MOSI bussen. Verdammt!'\n" + \
                    "Gunther trollar fram en lödkolv och löder av resistorn.\n" + \
                    "Gunther: 'Ok, ich probiere.... Jaaa! Es funkar! Vielen Dank für die Hilfe!'\n" + \
                    "Han ger mig en stor kram. Sen han kopplar ur oscilloskopet från kortet och slänger " + \
                    "resistorn det längsta " + \
                    "han kan, samtidigt som han vrålar något tyskt okvädningsord.")

                self.v_parentEntity.v_container.remove(self)
                self.v_parentEntity = None
                
                resistor = Resistor(self.v_world)
                resistor.v_parentEntity = self.v_world.roomForIndex(6) 
                resistor.v_parentEntity.v_container.append(resistor)

                self.v_world.addAchievment(world.ACH_HELPED_GUNTHER)
                return True
            else:
                self.v_failMsg = "Gunther: 'Ja.. ja! Det ser mycket intressant ut, aber jag minns inte om det är " + \
                    "rätt datablad. Bitte kom förbi min arbeitsplats och visa det sen.'"
        else:
            if self.v_world.playerRoomIx() == 6:
                self.v_failMsg = "Jag kan inte visa databladet för Gunther. Han är inte här."
            else:
                self.v_failMsg = "Kan inte använda databladet här."

        return False

class Resistor(Thing):
    ''' Resistor class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "resistor", "resistorer", "en", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "En 0402 resistor. Verkar vara 4,7 kOhm."
    
    def use(self):
        ''' Resistor use func '''
        if self.v_world.playerRoomIx() == 2 and self.v_world.checkAchievment(world.ACH_FOUND_COFFEE_BUG):
            self.v_world.output("Jag torkar bort wiener melangen med skjortärmen och pillar dit resistorn " + \
                "på DAT-tracen. Fäster den med ett gammalt tuggummi.\nSen skruvar jag ihop allt och kör " + \
                "en testrunda - voilà!")
            self.v_parentEntity.v_container.remove(self) 
            self.v_parentEntity = None
            self.v_world.addAchievment(world.ACH_FIXED_COFFEE_BUG)
            return True
        else:
            self.v_failMsg = "Jag vet inte vad jag ska göra med den."
            return False

class Coffee(Thing):
    ''' Coffee class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "kaffemugg", "kaffemuggar", "en", size=SIZE_NORMAL, weight=WEIGHT_MEDIUM)

    def description(self):
        ''' Returns description  '''
        return "En pappersmugg - med kaffe. Luktar gott."
    
    def use(self):
        ''' Coffe use func '''
        self.v_failMsg = random.choice(["Jag blir så kissig!", "Är inte sugen nu!", "Min mage blir så körd!"])
        return False

class CoffeeMachine(Thing):
    ''' CoffeeMachine class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "kaffemaskin", "kaffemaskiner", "en")
        self.broken = True

    def description(self):
        ''' Returns description  '''
        return "En kaffemaskin som kan brygga liten kaffe, stor kaffe, frappuchino, caffe latte, " + \
            "espresso, choklad och wiener melange." 

    def use(self):
        ''' CoffeMachine use func '''
        if self.v_world.checkAchievment(world.ACH_FIXED_COFFEE_BUG):
            if any(isinstance(thing, Coffee) for thing in self.v_world.player.contains()):
                self.v_failMsg = "Jag har ju redan en mugg med kaffe."
            elif any(isinstance(thing, Coffee) for thing in self.contains()):
                self.v_failMsg = "Det står ju redan en mugg med kaffe i maskinen."
            else:
                self.v_world.output("Kaffemojjan spottar ut en pappersmugg och fyller på den med nåt svart.")
                coffee = Coffee(self.v_world)
                coffee.v_parentEntity = self 
                self.v_container.append(coffee)
                return True
        else:
            self.v_failMsg = "Maskinen säger bara pip - på displayen står det 'UNABLE TO COMMUNICATE WITH PUMP'. " + \
                "Hmm, bara jag hade nåt att felsöka den med skulle jag nog kunna fixa det."
        return False


class ArcadeGame(Thing):
    ''' ArcadeGame class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "arkadspel", "arkadspel", "ett")
        self.highscore = 355840
        self.highscoreHolder = "Fratrik"

    def description(self):
        ''' Returns description '''
        return "Ett gammalt klassiskt Missile Command arkadspel från 1980. Ser lite skraltigt ut. " + \
            "Det sitter en lapp på det där det står:\n     ÖMTÅLIGT!\n  AKTAS FÖR STÖTAR!"
            
    def use(self):
        ''' Use the arcadegame func '''
        ret = retro.start(self.v_world.player.name(), self.highscore, self.highscoreHolder)
        self.highscore, self.highscoreHolder = ret
        ui.reset()
        if self.highscoreHolder == self.v_world.player.name():
            self.v_world.addAchievment(world.ACH_MISSILE_COMMANDER)
        return True
    
    def kick(self):
        ''' Kick the arcadegame func '''
        muts = next((p for p in self.v_world.persons if p.name() == "Muts"), None)
        if muts.roomIx == self.v_world.playerRoomIx():
            self.v_failMsg = "Jag måttar en spark - men innan jag hinner kicka till springer " + \
            "Muts fram och hindrar mig.\n" + \
            "Muts: 'Nej nej nej, ser du inte lappen? Den är omtålig!'"
            if muts.curOperation()["func"] == "work":
                muts.popOperation()
                muts.pushOperation("trywork")
                muts.opTimer = 2
                
            return False
        else:
            self.v_world.output("Jag ger den en rejäl spark - och skärmen blir blank. Efter några sekunder " + \
                "verkar den boota om.")
            self.highscore = 0
            return True

class Pen(Thing):
    ''' Pen class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "whiteboardpenna", "whiteboardpennor", "en", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "En whiteboardpenna med sparkling-pink färg." 

    def use(self):
        ''' Use the pen func '''
        menu = world.getEntity(self.v_world.playerRoom(), "meny")
        if menu != None and not menu.written:
            self.v_world.output("Ok - jag suddar ut den nuvarande menyn. Sen skriver jag en ny rätt " + \
                "i samma stil som tidigare meny så ingen misstänker nåt.\nJag: 'Bwa-hahahaha!'")
            menu.written = True
            self.v_world.addAchievment(world.ACH_MENU)
            return True
        else:
            return False

class Key(Thing):
    ''' Key class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "cykelnyckel", "cykelnycklar", "en", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "En cykelnyckel, fäst i en nyckelring med ett hjärta i silver. På hjärtat är det ingraverat " + \
            "'I LUV MY BIKE - Property of Gringo'. Herrejösses..."
            
    def use(self):
        ''' Key use operation '''
        if any(person.name() == "Gringo" for person in self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())):
            self.v_world.output("Jag ger Gringo nyckeln.\n" + \
                "Gringo: 'Åh tack! Tack! Jag är dig evigt tacksam!'\n" + \
                "Med tårar i ögonen ger han mig en stor kram. När jag hämtat andan igen säger jag:\n" + \
                "Jag: 'Du kanske ska ha den på något annat ställe eftersom .. ööh.. saker kommer ivägen " + \
                "för dig ibland.'\n" + \
                "Gringo: 'Det är faktiskt en bra idé. Att jag inte tänkt på det innan!'\n" + \
                "Gringo spänner ut spandexbyxorna och släpper ner nyckeln. Brrrr....")
            self.v_parentEntity.v_container.remove(self)
            self.v_parentEntity = None
            self.v_world.addAchievment(world.ACH_GRINGO_KEY)
            return True
        else:
            self.v_failMsg = "Det är rätt svårt att ge Gringo nyckeln när han inte är här."
            return False

class ToiletDoor(Thing):
    ''' ToiletDoor class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "dörr", "dörrar", "en", THING_OPENABLE)
        self.locked = True
        self.v_preposition = "bakom"

    def description(self):
        ''' Returns description  '''
        s = "En toalettdörr. "
        if not self.v_world.checkAchievment(world.ACH_PEDRIK_WOKEN):
            s += random.choice(["Någon snarkar där inne.", "Det är någon som mumlar där inne.", \
                "Det låter något därinifrån."])
        else:
            if self.locked:
                s += "Den är låst."
        return s
    
    def open(self):
        ''' ToiletDoor open operation '''
        if self.locked:
            self.v_failMsg = "Dörren är låst inifrån. Förresten är det inte bra för karman att rycka i en låst toadörr."
            return False
        else:
            self.closed = False
            return True
    
class Toilet(Thing):
    ''' Toilet class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "toalett", "toaletter", "en")
        self.locked = True

    def description(self):
        ''' Returns description  '''
        s = "Någon borde lära sig använda toaborsten..."
        return s
    
class Table(Thing):
    ''' Table class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "bord", "bord", "ett", size=SIZE_HUGE, weight=WEIGHT_MEDIUM)
        self.v_preposition = "på"

    def description(self):
        ''' Returns description  '''
        return "Ett typiskt arbetsbord." 

class Computer(Thing):
    ''' Computer class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "dator", "datorer", "en", size=SIZE_NORMAL, weight=WEIGHT_MEDIUM)

    def description(self):
        ''' Returns description  '''
        return "En linuxburk. Orkar inte rada upp specarna." 
    
    def take(self):
        ''' Computer take operation '''
        self.v_failMsg = "Jag kan ju inte ta datorn, den stängs av då. Dessutom är den för stor."
        return False
    
    def use(self):
        ''' Computer use operation '''
        roomIx = self.v_world.playerRoomIx()
        persons = self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())
        ticks = self.v_world.ticks + 100
        if roomIx == 5:
            self.v_failMsg = ("Jag har {0} olästa mail, {1} granskningar att ta hand om och {2} kommande möten. " + \
                "Baaahh....").format(int(ticks/2), int(ticks/5), int(ticks/11))
        else:
            if len(persons) == 0:
                self.v_failMsg = "Skärmen är låst."
            else:
                self.v_failMsg = "{} använder datorn just nu.".format(persons[0].name())
                
        return False   

class RedHerring(Thing):
    ''' Red herring class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "sill", "sillar", "en", size=SIZE_NORMAL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "Sillen är alldeles röd. Skumt." 
    
    def use(self):
        ''' RedHerring use operation '''
        persons = self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())
        if len(persons) > 0:
            name = persons[0].name()
            self.v_world.output(["Från ingenstans börjar orkestral musik att spela. Konstigt...", \
                "Jag tar den röda sillen i min hand och dansar lite.", \
                "Jag lavettar {} i ansiktet med sillen.".format(name), \
                "{} tar fram en gigantisk hälleflundra ur tomma luften.".format(name), \
                "{} bankar till mig i huvudet med flundran så jag trillar omkull.".format(name), \
                "\nHmm.. Det där var absurt."])
            self.v_world.addAchievment(world.ACH_FISH_DANCE)
            self.v_world.player.v_container.remove(self)
            return True
     
        return False   

class BadPen(Thing):
    ''' BadPen class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "penna", "pennor", "en", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "En trasig bläckpenna." 

class PostIt(Thing):
    ''' PostIt class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "post-it", "post-its", "en", size=SIZE_SMALL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "En post-it lapp. Det är kluddat något oläsligt på den." 

class Devboard(Thing):
    ''' DevBoard class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "utvecklingskort", "utvecklingskort", "ett", size=SIZE_NORMAL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "Ett utvecklingskort, ser gammalt och dammigt ut. Nån har lödat på det." 

class Cable(Thing):
    ''' Cable class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "kabel", "kablar", "en", size=SIZE_NORMAL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "Ser ut som en USB-A kabel." 

class BadMug(Thing):
    ''' BadMug class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "kaffemugg", "kaffemuggar", "en", size=SIZE_NORMAL, weight=WEIGHT_LITTLE)

    def description(self):
        ''' Returns description  '''
        return "En kaffemugg av papper. Det är något obeskrivligt i bottnen som verkar ha frätit hål." 

class Book(Thing):
    ''' Book class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "bok", "böcker", "en", size=SIZE_NORMAL, weight=WEIGHT_MEDIUM)

class DatasheetOther(Thing):
    ''' Datasheet1 class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "datablad", "datablad", "ett", size=SIZE_SMALL, weight=WEIGHT_LITTLE)
        
    def use(self):
        ''' OtherDatasheet use operation '''
        persons = self.v_world.getPersonsInRoom(self.v_world.playerRoomIx())
        if any(person.name() == "Gunther" for person in persons):
            if self.v_world.playerRoomIx() == 6:
                self.v_failMsg = "Jag ger Gunther databladet.\n" + \
                    "Gunther: 'Nein, was für ein datablad ist es?'\n" + \
                    "Gunther ger tillbaka databladet."
            else:
                self.v_failMsg = "Gunther: 'Det ser mycket intressant ut, aber jag minns inte om det är " + \
                    "rätt datablad. Bitte kom förbi min arbeitsplats och visa det sen.'"
        else:
            if self.v_world.playerRoomIx() == 6:
                self.v_failMsg = "Jag kan inte visa databladet för Gunther. Han är inte här."
            else:
                self.v_failMsg = "Kan inte använda databladet här."

        return False

class Copier(Thing):
    ''' Copier class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "kopieringsmaskin", "kopieringsmaskiner", "en", size=SIZE_HUGE, weight=WEIGHT_MASSIVE)
        self.kicks = 0

    def description(self):
        ''' Returns description  '''
        return "Jaha, trasig även den."
    
    def kick(self):
        ''' Kick the Copier func '''
        self.kicks += 1
        if self.kicks < 5:
            self.v_world.output(random.choice(["*KAPOW*\nAj, min fot!", "*ZLONK*\nAj, mitt knä!", \
                "*VRONK*\nAj, min benhinna!"]))
        elif self.kicks == 5:
            self.v_world.output("*CLANK*\nHoppsan! Den öppnade sig. Ser ut som om nån har stoppat i nåt i den.")
            tri = Tricorder(self.v_world)
            self.v_container.append(tri)
            tri.v_parentEntity = self
        else:
            self.v_world.output("Nä, nu har den stackars maskinen fått tillräckligt med smörj.")
        return True

class Tricorder(Thing):
    ''' Tricorder class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "tricorder", "tricordrar", "en", size=SIZE_SMALL, weight=WEIGHT_MEDIUM)

    def description(self):
        ''' Returns description  '''
        return "En grunka av nåt slag. Ser ut som en modifierad tricorder."
    
    def use(self):
        ''' Tricorder use operation '''
        triRes = "PERIFER SKANNING KLAR, RESULTAT\n" + \
            "  individ        placering                      hjärnvågsanalys\n" + \
            "  -------        ---------                      ---------------\n"
        for p in self.v_world.persons:
            if p.roomIx == 0:
                roomName = "På toaletten"
            else:
                roomName = self.v_world.roomForIndex(p.roomIx).name()
            if p.sleeping:
                action = "Sover"
            else:
                action = world.getActionDescription(p) 
            triRes += "  {:<14} {:<30} {}\n".format(p.name(), roomName, action)
        triRes += "  {:<14} {:<30} {}\n".format(self.v_world.player.name(), \
            self.v_world.playerRoom().name(), "Flatline")
        self.v_world.output("Tricorden blippar till. På skärmen står det:\n\n" + triRes)
        self.v_world.addAchievment(world.ACH_MINDREADER)
        return True

class Cat(Thing):
    ''' Status class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "katt", "katter", "en", size=SIZE_BIG, weight=WEIGHT_MEDIUM)

    def description(self):
        ''' Returns description  '''
        return "Den är uppstoppad. Förhoppningsvis hade den ett lyckligt liv."
    
    def use(self):
        ''' Cat use operation '''
        pedrik = next((p for p in self.v_world.persons if p.name() == "Pedrik"), None)
        fratrik = next((p for p in self.v_world.persons if p.name() == "Fratrik"), None)
        jean = next((p for p in self.v_world.persons if p.name() == "Jean"), None)
        prix = self.v_world.player.roomIx
        if pedrik.roomIx == prix and fratrik.roomIx == prix and jean.roomIx == prix:
            self.v_world.output("Fratrik tar fram en kamera.\n" + \
                "Pedrik plockar fram en färgkarta.\n" + \
                "Jag och Jean kastar katten mellan varandra medan Fratrik tar bilder.\n")
            self.v_world.addAchievment(world.ACH_CATTOSSER)
            return True
        return False

class ExitDoor(Thing):
    ''' ExitDoor class '''
    def __init__(self, w):
        ''' Ctor '''
        super().__init__(w, "dörr", "dörrar", "en", THING_OPENABLE, size=SIZE_HUGE, weight=WEIGHT_MASSIVE)

    def description(self):
        ''' Returns description  '''
        return "Vägen ut till frihet. Det sitter en skylt ovanför där det står 'EXIT'."

    def open(self):
        ''' ExitDoor open operation '''
        pedrik = next((p for p in self.v_world.persons if p.name() == "Pedrik"), None)
        fratrik = next((p for p in self.v_world.persons if p.name() == "Fratrik"), None)
        jean = next((p for p in self.v_world.persons if p.name() == "Jean"), None)
        crew = [pedrik, fratrik, jean]
        
        if pedrik.roomIx != 1 and fratrik.roomIx != 1 and jean.roomIx != 1:
            self.v_failMsg = "Jag kan ju inte gå ut utan mina kollegor."
        elif pedrik.roomIx == 1 and fratrik.roomIx == 1 and jean.roomIx == 1:
            world.success(self.v_world)
            return True
        else:
            missing = [p.name() for p in crew if p.roomIx != 1]
            self.v_failMsg = "Jag kan ju inte gå ut utan " + " och ".join(missing) + "."
        
        return False

