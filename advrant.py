#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Person dialogue system
"""

import world

class Rant:
    ''' Question and answer class '''
    def __init__(self, jRant):
        ''' Ctor, created from a json dict '''
        self.question = jRant["q"]
        self.answer = jRant["a"]
        self.prereqs = jRant["prereq"].split(",")
        self.triggers = jRant["trigger"].split(",")
        
    def validate(self, w, person):
        ''' validates if this question is ok given the circumstances '''
        valid = True
        
        for p in self.prereqs:
            negate = False
            if len(p) == 0:
                continue
            if p[0:1] == '!':
                negate = True
                p = p[1:]
            ptype = p[0:2] 
            p = p[2:]
            if ptype == "p_":
                if person.name().lower() == p and negate or person.name().lower() != p:
                    valid = False
                    break
            elif ptype == "s_":
                if p in w.staticRants:
                    if  negate:
                        valid = False
                        break
                else:
                    if not negate:
                        valid = False
                        break
            elif  ptype == "a_":
                if p in w.achievements:
                    if  negate:
                        valid = False
                        break
                else:
                    if not negate:
                        valid = False
                        break
            else:
                valid = False
                world.dbg("  INVALIDATED, UNKNOWN PREREQ:" + p)
                break
        
        return valid
    
    def trigger(self, w, person):
        ''' Triggers actions on answer '''
        endRant = False
        for t in self.triggers:
            if t == "endrant":
                endRant = True
                continue
            ttype = t[0:2] 
            t = t[2:]
            if ttype == "s_":
                if not t in w.staticRants:
                    w.staticRants.append(t)
            elif ttype == "o_":
                person.pushOperation(t)
                person.opTimer = 0
            elif ttype == "a_":
                w.addAchievment(t)
        return endRant

_rants = list()
_curRants = None
_person = None

def buildRants(jRants):
    ''' build rant objects from json dicts '''
    for jRant in jRants:
        r = Rant(jRant)
        _rants.append(r)
        world.dbg(r.question)
        
def displayRants(w, person, displayHeader=True):
    ''' Display list of valid rants '''
    global _curRants, _person
    _curRants = [rant for rant in _rants if rant.validate(w, person)]
    _person = person
    ix = 1
    if len(_curRants) > 0 and displayHeader:
        world.outputDirect("Tala med {}".format(person.name()))
    for rant in _curRants:
        q = world.stringify(rant.question).format(player=w.player.name())
        world.outputDirect("   {:>2}. {}".format(ix, q))
        ix += 1
    if len(_curRants) > 0:
        world.outputDirect("    0. Sluta snacka")
        return True
    else:
        return False
        
def parseQuestion(w, line):
    ''' parses user input '''
    try:
        ix = int(line)
        if ix > len(_curRants) or ix < 0:
            world.outputDirect("Ge mig en siffra som passar tack.")
        elif ix == 0:
            world.leaveConversation(w, _person)      
        else:
            rant = _curRants[ix - 1]
            q = world.stringify(rant.question).format(player=w.player.name())
            a = world.stringify(rant.answer).format(player=w.player.name())
            if q.startswith("'"):
                world.outputDirect("Jag: {}".format(q))
            
            world.outputDirect("{}: '{}'".format(_person.name(), a))
            
            endConversation = rant.trigger(w, _person)
            if endConversation:
                world.leaveConversation(w, _person)
            else:
                world.outputDirect("")
                if not displayRants(w, _person, False):
                    world.leaveConversation(w, _person)
    except ValueError:
        world.outputDirect("Ge mig en siffra tack.")
