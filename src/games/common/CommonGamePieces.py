import random

from . import GameExceptions

class DeckOfCards:
    def __init__(self, cards, shuffle=True, autoreshuffle=False):
        
        self.deck = list(cards)
        self.autoreshuffle = autoreshuffle
        self.discard = []
        
        if shuffle:
            self.shuffle()
            
    def shuffle(self):
        random.shuffle(self.deck)
    
    def draw(self, number = 1, from_top = True):
        if number > len(self.deck):
            if self.autoreshuffle and (number <= len(self.deck + self.discard)):
                random.shuffle(self.discard)
                self.deck += self.discard
                return self.draw(number, from_top)
            else:
                raise GameExceptions.DiscordGameError("Not enough cards to draw from deck")
        
        if from_top:
            drawn = self.deck[:number]
            rest = self.deck[number:]
        else:
            drawn = self.deck[(-1*number):]
            rest = self.deck[:(-1*number)]
            
        self.deck = rest
        return drawn
    
    def mill(self, number = 1, from_top = True):
        milled_cards = self.draw(number, from_top)
        self.discard = milled_cards + self.discard
        return milled_cards
        
    def peak(self, number = 1, from_top = True):
        if number > len(self.deck):
            if self.autoreshuffle and (number <= len(self.deck + self.discard)):
                random.shuffle(self.discard)
                self.deck += self.discard
                return self.draw(number, from_top)
            else:
                raise GameExceptions.DiscordGameError("Not enough cards to in deck")
        
        if from_top:
            drawn = self.deck[:number]
        else:
            drawn = self.deck[(-1*number):]
            
        return drawn
    
    def add_to_deck(self, cards, on_top = True):
        if on_top:
            self.deck = cards + self.deck
        else:
            self.deck += cards
     
    def add_to_discard(self, cards):
        self.discard = cards + self.discard
        