#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Office Adventure

@author: petera
'''


import sys
import os
import getopt
import world
import traceback
import ui
import getpass

#
# Add some stuff about this script
#
PROGRAM = os.path.basename(sys.argv[0])
AUTHOR = "Peter Andersson"
VERSION = "1.0.0"
GAMENAME = "Sökandet Efter Burgare"
USAGE = """{program} - {gamename}. By {author}, version {version}.

Usage:
  {program} [options] (<playername>)

General options:
  -h --help                              Display this help message.
  -i --info                              Displays the game concept.
  -v --version                           Print version and exit.
  -a --about                             Print nonsense about the author and exit.
  -c --cheat                             Print a full walkthrough and exit.
  -d --debug                             Enable ingame debug info.
""".format(program=PROGRAM, author=AUTHOR, version=VERSION, gamename=GAMENAME)

MSG_VERSION = "{program} version {version}.".format(program=PROGRAM, version=VERSION)
MSG_USAGE = "Use {program} --help to get usage.\n".format(program=PROGRAM)
MSG_ABOUT = "{author} är en blygsam superprogrammerare boende i Malmö, " + \
    "som sakta men säkert närmar sig 40.\n".format(author=AUTHOR)
MSG_INTRO = """*** {gamename} v{version} ***

Introduktion:

Jag sitter på mitt kära arbete CherryWar AB.

En helt vanlig morgon - kodat, haft några möten, snackat med mina kollegor och 
lunchrestaurangen erbjuder vedervärdig mat.

En burgare på stan hade suttit fint - faktum är att det snart är lunch. Men ack - 
när jag kollar efter plånboken visar det sig att jag glömt den hemma! Katastrof!

Men kanske inte allt är förlorat. Fratrik, Pedrik och Jean är ju skyldiga mig 
varsin slant. Tillsammans borde det räcka till en burgare! Dessutom är jag lite 
rädd för den arga burgarmånglaren, så jag beslutar mig att få med dem allihop 
till burgarstället.


           *** SPELETS MÅL ***
           
Få med Fratrik, Pedrik och Jean på burgare


Friskrivningsklausul: Alla likheter med verkliga personer och platser är 
                      fullkomligt tillfälliga.

Tips: Skriv '?' för att få en lista med kommandon.
      Du behöver bara skriva de första bokstäverna i objektet eller personen.
      Prata med personer för att få ledtrådar.


""".format(gamename=GAMENAME, version=VERSION)
MSG_INFO = """{gamename} är ett textbaserat äventyrsspel som utspelar sig på ett kontor 
någonstans i Malmö. Målet med spelet är att få med tre av sina kollegor ut på burgare
till lunch, då dessa är skyldiga dig pengar.

Det finns andra kollegor på kontoret. De flesta brukar sitta vid sina datorer, men 
ibland behöver de prata med någon, gå på toa eller äta lite frukt. Genom att prata med
sina medarbetare får man ledtrådar hur man ska få sina motsträviga kumpaner att följa
med på lunchburgare.
""".format(gamename=GAMENAME)
MSG_WALKTHRU = """
GENOMGÅNG.

Tänk på att karaktärerna går runt i spelet ibland. Alltså är de inte alltid på sina rum. 
Men väntar man bara en stund återvänder de till slut. Kan du inte hitta en karaktär alls är
personen på toa och återkommer snart.

Du börjar i ditt rum. Öppna hurtsen och ta whiteboardpennan. Gå bakåt.
I Jeans & Gunthers rum, öppna hurtsen och ta batteriet. Gå bakåt.
I Schtevens & Gringos rum, öppna hurtsen och ta fläkten. Gå framåt två gånger.
I ditt rum, flytta stolen framåt.
I Fratriks & Pedriks rum, öppna hurtsen och ta databladet. Flytta stolen framåt.
På Toan, använd stolen. Ta prillan. Gå framåt.
I Fikarummet, använd mikron, öppna mikron, ta prillan. Gå framåt.
I Hallen, använd whiteboardpennan. Gå bakåt fem gånger.
I Jeans & Gunthers rum, använd prillan (ge till Jean). Använd databladet (ge till Gunther). 
Ta oscilloskop och resistor. Gå framåt fyra gånger.
I Fikarummet, använd oscilloskopet, använd resistorn. Använd kaffemaskinen, ta kaffemugg.
Gå bakåt.
På Toan, använd batteri. Använd fläkt. Gå bakåt.
I Fratriks & Pedriks rum, prata med Pedrik. Fråga om burgare, fråga sen om grönsaker. Pedrik
går och kollar menyn. När Pedrik kommer tillbaka, prata med Pedrik igen och fråga om burgare.

Gå bakåt två gånger.
I Jeans & Gunthers rum, prata med Jean. Fråga om burgare, fråga sen om menyn. Jean går och
kollar menyn. När Jean kommer tillbaka, prata med Jean igen och fråga om burgare.

Följ efter Gringo. Varje gång Gringo går in i ett rum är det 50% chans han slår i nåt. Varje
gång Gringo slår i nåt är det 50% chans han tappar sin nyckel. Följ efter Gringo och titta i
varje rum. När du ser en cykelnyckel, ta den.
Använd cykelnyckeln när Gringo är i rummet. Prata med Gringo, be honom ta mötet med Muts nu
och i hans rum. Gå till Fikarummet.
I Fikarummet, sparka på arkadmaskinen. Använd arkadmaskinen. Spela åtminstone en runda, och
få Game Over sen. Avsluta spelet. Gå bakåt två gånger.
I Fratriks & Pedriks rum, prata med Fratrik. Tjata om burgare tills han inte vill prata mer.
Prata med Fratrik igen, be honom kolla in highscoret. Fratrik springer till arkadmaskinen.
När han kommer tillbaka, prata med Fratrik och häckla honom lite. Gå framåt tre gånger.

I Hallen, vänta om inte redan Pedrik, Fratrik och Jean är där. 
Öppna dörren.

Eller, så laddar du sparningen "theend.json" och bara öppnar dörren.

"""

#
# Global default settings affecting behaviour of script in several places
#
DEBUG = False

EXIT_SUCCESS = 0
EXIT_USAGE = 1
EXIT_FAILED = 2




def printUsage(exitStatus):
    """
    Print usage information about the script and exit.
    """
    print(USAGE)
    sys.exit(exitStatus)



def printVersion():
    """
    Print version information and exit.
    """
    print(MSG_VERSION)
    sys.exit(EXIT_SUCCESS)


def printAbout():
    """
    Print info on author and exit.
    """
    print(MSG_ABOUT)
    sys.exit(EXIT_SUCCESS)
    
    
def printInfo():
    """
    Print game info and exit.
    """
    print(MSG_INFO)
    sys.exit(EXIT_SUCCESS)


def printCheat():
    """
    Print game cheat and exit.
    """
    print(MSG_WALKTHRU)
    sys.exit(EXIT_SUCCESS)


def parseOptions():
    """
    Merge default options with incoming options and arguments and return them as a dictionary.
    """

    # Switch through all options
    try:
        global DEBUG

        opts, args = getopt.getopt(sys.argv[1:], "hivacd", \
                                   ["help", "info", "version", "about", "cheat", "debug"])

        if len(opts) > 0:
            for opt in opts[0]:
                
                if opt in ("-h", "--help"):
                    printUsage(EXIT_SUCCESS)
                elif opt in ("-i", "--info"):
                    printInfo()
                elif opt in ("-v", "--version"):
                    printVersion()
                elif opt in ("-a", "--about"):
                    printAbout()
                elif opt in ("-c", "--cheat"):
                    printCheat()
                elif opt in ("-d", "--debug"):
                    DEBUG = True

        if len(args) == 0:
            res = getpass.getuser()
        else:
            res = args[0]

    except Exception as err:
        print(err)
        print(MSG_USAGE)
        # Prints the callstack, good for debugging, comment out for production
        traceback.print_exception(Exception, err, None)
        sys.exit(EXIT_USAGE)

    return res




def main():
    """
    CLI entry function
    """
    
    playerName = parseOptions()
    
    try:
        gameWorld = world.init(playerName, DEBUG)
        ui.start(gameWorld, MSG_INTRO)
        ret = True
        
    except Exception as err:
        if DEBUG:
            traceback.print_exception(Exception, err, None)
        ret = False
            
    if not ret:
        sys.exit(EXIT_FAILED)
    else:
        sys.exit(EXIT_SUCCESS)

if __name__ == '__main__':
    main()
