# -*- coding: utf-8 -*-
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# 

#Assuming I didn't screw up, this add-on overrides the Scheduler settings to remove the easy boost, hard penalty, lapse penalty, and ignore the multiplier for lapsed cards, which by default resets the interval.

'''In the nextLapseIvl function below, I have now added my modification of Dmitry Mikheev's modification of Luminous Spice's <a href="https://ankiweb.net/shared/info/1481634779" rel="nofollow">Another Retreat</a> add-on. :) - This add-on actually manages to replicate the failed card handling that happens to be used in a research model by Xiong, Wang, and Beck. It resets the lapsed card interval to the previous successful interval. To use it, comment out line 117 and remove the triple quotes from lines 118 and 122.'''

from __future__ import division
import time, random
from anki.utils import ids2str, intTime, fmtTimeSpan
from heapq import heappush
from anki.sched import Scheduler

def _answerLrnCard(self, card, ease): #commented out line 44 so that the interval for lapsed cards is unaffected
        # ease 1=no, 2=yes, 3=remove
        conf = self._lrnConf(card)
        if card.odid and not card.wasNew:
            type = 3
        elif card.type == 2:
            type = 2
        else:
            type = 0
        leaving = False
        # lrnCount was decremented once when card was fetched
        lastLeft = card.left
        # immediate graduate?
        if ease == 3:
            self._rescheduleAsRev(card, conf, True)
            leaving = True
        # graduation time?
        elif ease == 2 and (card.left%1000)-1 <= 0:
            self._rescheduleAsRev(card, conf, False)
            leaving = True
        else:
            # one step towards graduation
            if ease == 2:
                # decrement real left count and recalculate left today
                left = (card.left % 1000) - 1
                card.left = self._leftToday(conf['delays'], left)*1000 + left
            # failed
            else:
                card.left = self._startingLeft(card)
                resched = self._resched(card)
                if 'mult' in conf and resched:
                    # review that's lapsed
                    #card.ivl = max(1, conf['minInt'], card.ivl*conf['mult'])
					pass
					#card.ivl = nextLapseIvl(self, card, conf)
                else:
                    # new card; no ivl adjustment
                    pass
                if resched and card.odid:
                    card.odue = self.today + 1
            delay = self._delayForGrade(conf, card.left)
            if card.due < time.time():
                # not collapsed; add some randomness
                delay *= random.uniform(1, 1.25)
            card.due = int(time.time() + delay)
            # due today?
            if card.due < self.dayCutoff:
                self.lrnCount += card.left // 1000
                # if the queue is not empty and there's nothing else to do, make
                # sure we don't put it at the head of the queue and end up showing
                # it twice in a row
                card.queue = 1
                if self._lrnQueue and not self.revCount and not self.newCount:
                    smallestDue = self._lrnQueue[0][0]
                    card.due = max(card.due, smallestDue+1)
                heappush(self._lrnQueue, (card.due, card.id))
            else:
                # the card is due in one or more days, so we need to use the
                # day learn queue
                ahead = ((card.due - self.dayCutoff) // 86400) + 1
                card.due = self.today + ahead
                card.queue = 3
        self._logLrn(card, ease, conf, leaving, type, lastLeft)

	
def newRescheduleLapse(self, card): # no ease penalty, simply commented out line 16
	conf = self._lapseConf(card)
	card.lastIvl = card.ivl
	if self._resched(card):
		card.lapses += 1
		card.ivl = self._nextLapseIvl(card, conf)
		  # card.factor = max(1300, card.factor-200)
		card.due = self.today + card.ivl
		# if it's a filtered deck, update odue as well
		if card.odid:
			card.odue = card.due
	# if suspended as a leech, nothing to do
	delay = 0
	if self._checkLeech(card, conf) and card.queue == -1:
		return delay
	# if no relearning steps, nothing to do
	if not conf['delays']:
		return delay
	# record rev due date for later
	if not card.odue:
		card.odue = card.due
	delay = self._delayForGrade(conf, 0)
	card.due = int(delay + time.time())
	card.left = self._startingLeft(card)
	# queue 1
	if card.due < self.dayCutoff:
		self.lrnCount += card.left // 1000
		card.queue = 1
		heappush(self._lrnQueue, (card.due, card.id))
	else:
		# day learn queue
		ahead = ((card.due - self.dayCutoff) // 86400) + 1
		card.due = self.today + ahead
		card.queue = 3
	return delay
	
def nextLapseIvl(self, card, conf): # multiplier not honored, therefore card interval not reset or decreased - commented out and replaced line - to undo, just comment out line 48 and uncomment line 48
    #return max(conf['minInt'], int(card.ivl*conf['mult']))
    return max(conf['minInt'], conf['mult']*int(card.ivl))
    '''lastIvls = self.col.db.list("""select lastivl from revlog where cid = ? and lastivl < ? order by id desc LIMIT 1""", card.id, card.ivl)
    if lastIvls:
        return max( conf['minInt'], lastIvls[0])
    else:
        return max( conf['minInt'], int(card.ivl))'''

def newRescheduleRev(self, card, ease): # no ease boost or hard penalty - commented out line 55 so that card.factor not changed
	# update interval
	card.lastIvl = card.ivl
	if self._resched(card):
		self._updateRevIvl(card, ease)
		  # card.factor = max(1300, card.factor+[-150, 0, 150][ease-2])
		card.due = self.today + card.ivl
	else:
		card.due = card.odue
	if card.odid:
		card.did = card.odid
		card.odid = 0
		card.odue = 0
  
def nextRevIvl(self, card, ease): # only good interval - commented out 69 and 71
	"Ideal next interval for CARD, given EASE."
	delay = self._daysLate(card)
	conf = self._revConf(card)
	fct = card.factor / 1000
	# ivl2 = self._constrainedIvl((card.ivl + delay // 4) * 1.2, conf, card.ivl)
	ivl3 = self._constrainedIvl((card.ivl + delay // 2) * fct, conf, card.ivl) #card.ivl originally ivl2
	# ivl4 = self._constrainedIvl((card.ivl + delay) * fct * conf['ease4'], conf, ivl3)
	if ease == 2:
	    interval = ivl3
	elif ease == 3:
	    interval = ivl3
	elif ease == 4:
	    interval = ivl3
	# interval capped?
	return min(interval, conf['maxIvl'])
    
def dynIvlBoost(self, card): #replaced factor with fct
    assert card.odid and card.type == 2
    assert card.factor
    confL = self._lrnConf(card)
    elapsed = card.ivl - (card.odue - self.today)
    #factor = ((card.factor/1000)+1.2)/2
    fct = card.factor / 1000
    ivl = int(max(card.ivl, elapsed * fct, confL['minInt'])) #should maybe change 1 to minInt
    conf = self._revConf(card)
    return min(conf['maxIvl'], ivl)    

def newreschedCards(self, ids, imin, imax):
    "Put cards in review queue with a new interval in days (min, max)."
    d = []
    t = self.today
    mod = intTime()
    for id in ids:
        card = self.col.getCard(id)
        r = random.randint(imin, imax)
        d.append(dict(id=id, due=r+t, ivl=max(1, r), mod=mod,
                      usn=self.col.usn(), fact=card.factor))
    self.remFromDyn(ids)
    self.col.db.executemany("""
update cards set type=2,queue=2,ivl=:ivl,due=:due,odue=0,
usn=:usn,mod=:mod,factor=:fact where id=:id""",
                            d)
    self.col.log(ids)    

def newforgetCards(self, ids):
    "Put cards at the end of the new queue."
    d = []
    for id in ids:
        card = self.col.getCard(id)
        d.append(dict(id=id, fact=card.factor))
    self.remFromDyn(ids)        
    self.col.db.executemany("""
update cards set type=0,queue=0,ivl=0,due=0,odue=0,factor=:fact where id=:id""",
                            d)
    pmax = self.col.db.scalar(
        "select max(due) from cards where type=0") or 0
    # takes care of mod + usn
    self.sortCards(ids, start=pmax+1)
    self.col.log(ids)
    
Scheduler._rescheduleLapse = newRescheduleLapse
Scheduler._rescheduleRev = newRescheduleRev
Scheduler._nextRevIvl = nextRevIvl
Scheduler._nextLapseIvl = nextLapseIvl
Scheduler._dynIvlBoost = dynIvlBoost
Scheduler.reschedCards = newreschedCards
Scheduler.forgetCards = newforgetCards