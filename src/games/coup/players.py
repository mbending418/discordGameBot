from ..common import GameClasses

class CoupPlayer(GameClasses.Player):

    def __init__(self, DiscordAuthorContext, name = None):
        
        super().__init__(DiscordAuthorContext, name)
        
        self.player_id = f"{self.discord_name}: {self.name}"
        self.clear_game_fields()
        
    def clear_game_fields(self):
             
        self.public_info = ["blank", "blank"]
        self.cards = []
        self.money = 0
    
    def give_cards(self, *cards):
        self.cards += cards
        
    def take_cards(self, *cards):
        for card in cards:
            self.cards.remove(card)
     
    def get_card_count(self, card):
        #return how many copies of a particular card this player has_key
        count = 0
        for c in self.cards:
            if c == card:
                count += 1
                
        return count
     
    def create_card_messages(self):
        if len(self.cards) == 0:
            return [self.create_message_for(text = "You have no cards in hand and you are out of the game!")]
        
        text = f"{self.name}: Your cards in hand are:\n" + "\n".join([card.name for card in self.cards])
        message = [self.create_message_for(text = text, image = self.cards[0].get_card_image(), send_both = True)]
        
        if len(self.cards) > 1:
            message += [self.create_message_for(image = card.get_card_image()) for card in self.cards[1:]]
            
        return message
        
        