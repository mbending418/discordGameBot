from ..common import GameClasses

class AvalonPlayer(GameClasses.Player):

    def __init__(self, DiscordAuthorContext, name = None):
        
        super().__init__(DiscordAuthorContext, name)
        
        self.player_id = f"{self.discord_name}: {self.name}"
        self.clear_game_fields()
        
    def clear_game_fields(self):
     
        self.public_info = [".","."]
        self.private_info = "."
        self.character = "."
        self.vote = None
        self.mission_card = None