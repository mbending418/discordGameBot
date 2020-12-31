import os

from ..common import GameClasses
from ..common import utils

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
     
    def create_card_messages(self, temp_dir):
        text = f"{self.name}'s hand:\n"
        
        if len(self.cards) == 0:
            return [GameClasses.CommandResultMessage(destination = self.discord_channel, text=text + "\nYou have no cards in hand and you are out of the game!")]
        
        text += "\n".join([card.name for card in self.cards])
        
        output_file = os.path.join(temp_dir, self.name + ".jpg")
        utils.merge_image_files([card.card_image for card in self.cards], output_file)
        
        return [GameClasses.CommandResultMessage(destination=self.discord_channel, text=text, image = output_file, send_both=True)]
        
        
        