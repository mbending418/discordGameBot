from ..common import GameClasses
from ..common import GameExceptions

class RPSPlayer(GameClasses.Player):

    def __init__(self, DiscordAuthorContext, name = None):
        
        super().__init__(DiscordAuthorContext, name)
        
        self.player_id = f"{self.discord_name}: {self.name}"
        self.clear_game_fields()
        
    def clear_game_fields(self):
     
        self.throw = None

    def throw_rock(self):
        
        if self.throw is None:
            self.throw = "Rock"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot throw Rock! {self.name} has already chosen {self.throw}")
        
    def throw_paper(self):
        
        if self.throw is None:
            self.throw = "Paper"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot throw Paper! {self.name} has already chosen {self.throw}")
        
    def throw_scissors(self):
    
        if self.throw is None:
            self.throw = "Scissors"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot throw Scissors! {self.name} has already chosen {self.throw}")
        
    def to_number(self):
       
        if self.throw == "Rock":
            return 0
           
        elif self.throw == "Paper":
            return 1
            
        elif self.throw == "Scissors":
            return 2
            
        else:
            raise GameExceptions.DiscordGameError(f"{self.name} has an unknown throw registered: {self.throw}")
            
    def __gt__(self, rpsplayer):
        """
        Returns True iff self's throw beats rpsplayer's throw
        """
        
        if isinstance(rpsplayer, RPSPlayer):
            
            if self.throw is None:
                raise GameExceptions.DiscordGameError(f"{self.name} has not thrown anything!")
            elif rpsplayer.throw is None:
                raise GameExceptions.DiscordGameError(f"{rpsplayer.name} has not thrown anything!")
            else:               
                result = self.to_number() - rpsplayer.to_number()
                
                #modular arithmetic maaaaagic
                if result < 0:
                    result+=3
                    
                if result == 0 or result == 2:
                    return False
                elif result == 1:
                    return True
                else:
                    GameExceptions.DiscordGameError(f"Unknown result for '{self.throw}' < '{rpsplayer.throw}'")
        else:
            raise GameExceptions.DiscordGameError(f"unsupported operand types(s) for >: {type(self)} and {type(rpsplayer)}")
            
    def __lt__(self, rpsplayer):
        """
        Returns True iff self's throw loses to rpsplayer's throw
        """
        
        if isinstance(rpsplayer, RPSPlayer):
            
            if self.throw is None:
                raise GameExceptions.DiscordGameError(f"{self.name} has not thrown anything!")
            elif rpsplayer.throw is None:
                raise GameExceptions.DiscordGameError(f"{rpsplayer.name} has not thrown anything!")
            else:
                return rpsplayer > self
                
        else:
            raise GameExceptions.DiscordGameError(f"unsupported operand types(s) for <: {type(self)} and {type(rpsplayer)}")
                