import os
import shutil
import random
from emoji import EMOJI_ALIAS_UNICODE as EMOJIS

from .players import RPSPlayer

from ..common import GameBase
from ..common import GameClasses
from ..common import GameExceptions
        
DiscordGame = GameBase.getBaseGameClass()
class RockPaperScissors(DiscordGame):
    
    _all_states = ["player_select", "throw", "result"]
    
    _emoji_dict = {
        EMOJIS[":fist:"] : "Rock",
        EMOJIS[":raised_hand:"] : "Paper",
        EMOJIS[":v:"] : "Scissors"
    }
    
    def __init__(self, debug):
        self.debug = debug
    
        self.state = "player_select"
        self.controls = {}
        self.records = []
        self.result = None
    
    def validate_player_name(self, player_name):
    
        character_whitelist = "abcdefghijklmnopqrstuvwxyz0123456789"
    
        for char in player_name.lower():
        
            if char not in character_whitelist:
            
                return False
                
        return True            
           
    def reset_player(self, player):
        player.clear_game_fields()
    
    def reset_game(self):
        
        for player in self.get_players_in_registry():
            self.reset_player(player)
            
        self.result = None
        self.state = "player_select"     
    
    def process_throws(self, throws):
    
        for player_name, selection in throws.items():
            player = self.get_player_from_name(player_name)
            if len(selection) == 0:
                raise GameExceptions.DiscordGameError(f"{player_name} never made a choice and timed out! Please Reset Game.")
            elif len(selection) == 1:
                pass
            else:
                raise GameExceptions.DiscordGameError(f"{player_name} managed to pick more than one choice: {selection}")
            
            throw = self._emoji_dict.get(list(selection)[0])
            
            if throw == "Rock":
                player.throw_rock()
                
            elif throw == "Paper":
                player.throw_paper()
                
            elif throw == "Scissors":
                player.throw_scissors()
                
            else:
                raise GameExceptions.DiscordGameError(f"Unknown Throw Registered: player = {player_name} | throw = {selection[0]}")
            
        return self.process_result()
    
    def process_result(self, message = None):
        """
        Once both players have choosen figure out who won and display it
        """
        
        if message is None:
            message = []
        
        players = self.get_players_in_registry()
        
        player_1 = players[0]
        player_2 = players[1]
                
        winning_message = ["==========================================="]
        winning_message += [f"{player_1.name} vs. {player_2.name}",f"{player_1.name} choose {player_1.throw}",f"{player_2.name} choose {player_2.throw}"]
        
        #figure out who won
        if player_1.throw == player_2.throw:
            winning_message.append("It's a Tie!")
        elif player_1 > player_2:
            winning_message.append(f"{player_1.name} wins!")
        elif player_1 < player_2:
            winning_message.append(f"{player_2.name} wins!")
        else:
            raise GameExceptions.DiscordGameError(f"Unknown result with {player_1.throw} and {player_2.throw} chosen respectively")
                    
        #save a permanent record
        self.records.append("\n".join(winning_message))
        
        #add the record to the message
        message.append("\n".join(winning_message))
        
        message.append("\nUse the Command 'reset' to go back to player select!") 
        
        #set the result
        self.result = "\n".join(winning_message)
        
        #move to 'result' and return the message
        self.state = "result"
        return message      
     
    @DiscordGame.command(player=_all_states, help="reset the game (go back to 'player_select')", requires_lock = True)
    def reset(self):
        """
        Command: Go back to Player Select
        """
        
        self.reset_game()
        
        return "Restarting Game! Choose Players!"
    
    @DiscordGame.command(player=["player_select"], help="start the game! set {arg1} to 'manual' to play in 'manual' mode", requires_lock = True)
    def play(self, mode = ""):
        """
        Command: Play a Game once Two Players have been selected
        """
        
        players = self.get_players_in_registry()
        
        #check to see that there are exactly two players
        player_count = len(players)
    
        if player_count < 2:
            raise GameExceptions.DiscordGameIllegalMove("Too Few Players! Need 2 to play")
        elif player_count == 2:
            pass
        else:
            raise GameExceptions.DiscordGameIllegalMove("Too Many Players! Need 2 to play")
                        
        #advance the game state to 'throw' and return the message
        self.state = "throw"
        
        #if playing in button mode, send prompts
        if mode != "manual":
        
            #send each player a prompt to throw Rock Paper or Scissors
            title = "Choose Rock, Paper, or Scissors!"
            description = "\n".join([f"{choice} : {emoji}" for emoji,choice in self._emoji_dict.items()])
            prompts = [GameClasses.CommandResultPrompt(player = player, title = title, func_name = "process_throws", dm = True, description = description, emojis = list(self._emoji_dict.keys())) for player in players]
        
            message = ["Both Players: Throw 'Rock', 'Paper', or 'Scissors'!"]
            message += prompts
            
        else:
        
            #send dm's to each player if in manual mode
            message = [GameClasses.CommandResultMessage(destination = player.discord_channel, text = f"{player.name}: Throw 'Rock', 'Paper', or 'Scissors'! ['throw <selection>']") for player in players]
        
            #put a message in the main chat letting everyone know the players are choosing
            message.append("Both Players: Throw 'Rock', 'Paper', or 'Scissors'! ['throw <selection>']")
        
        return message 
    
    @DiscordGame.command(player=["throw"], help="Throw either 'Rock', 'Paper', or 'Scissors'!", requires_lock = True)
    def throw(self, option, *, DiscordAuthorContext):
        """
        Command: Let's a Player Throw their choice. Automatically moves to game_state 'result' if both have thrown
        """
        
        #find which player this person controls
        player_name = self.controls[str(DiscordAuthorContext)]
        player = self.get_player_from_name(player_name)
        
        #have the player throw their choice
        option = option.lower()
        
        if option == "rock":
            player.throw_rock()
        elif option == "paper":
            player.throw_paper()
        elif option == "scissors":
            player.throw_scissors()
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot Throw '{option}'. Throw 'Rock', 'Paper', or 'Scissors'")
        
        #message the player that they made a particular choice
        message = [player.create_message_for(text = f"You threw {option}!")]
        
        #message the main channel indicating that the player has chosen
        message.append(f"\n{player.name} has made their choice!")
        
        #check to see if both players have chosen
        players = self.get_players_in_registry()
             
        if all([player.throw is not None for player in players]):
            return self.process_result(message)
        else:
            return message            
    
    @DiscordGame.command(user = _all_states, help="Get the current game info")
    def info(self, *, DiscordChannelContext):
        
        players = self.get_players_in_registry()
        
        if self.state == "player_select":
                        
            message = ["The following players are in the game:"]
            message += [player.name for player in players]
            
            if len(players) == 2:
                message += ["\nsend the command 'play' to begin!"]
                
            return GameClasses.CommandResultMessage(text = "\n".join(message), destination = DiscordChannelContext)
            
        elif self.state == "throw":
        
            message = [f"{[player.name for player in players]} are playing a game of Rock, Paper, Scissors!"]
            message += [f"{player.name} has chosen!" for player in players if player.throw is not None]
            message += [f"{player.name} has not choosen yet!" for player in players if player.throw is None]
            
            return GameClasses.CommandResultMessage(text ="\n".join(message), destination = DiscordChannelContext)
            
        elif self.state == "result":
        
            return self.result
            
        else:
           
           raise GameExceptions.DiscordGameError(f"Reached Unknown Game State: {self.state}")               
    
    @DiscordGame.command(user = _all_states, help = "check the record of who beat who in this game session")
    def record(self, *, DiscordChannelContext):
        
        return [GameClasses.CommandResultMessage(text = record, destination = DiscordChannelContext) for record in self.records]        
    
    @DiscordGame.command(player = _all_states, help="take control of a player", debug = True)
    def control(self, player_name, *, DiscordAuthorContext, DiscordChannelContext):
        """
        Command (debug): Take control of a player by name in debug mode
        """
        
        player = self.get_player_from_name(player_name)
        if player.discord_name == str(DiscordAuthorContext):
            self.controls[str(DiscordAuthorContext)] = player_name
            return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = f"{str(DiscordAuthorContext)} is now controlling {player_name}")
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"{str(DiscordAuthorContext)} doesn't own {player_name}")
        
    @DiscordGame.command(user= _all_states, help="see who's controlling which player", debug=True)
    def check_control(self):
        """
        Command (debug): When in debug mode, check to see who control which player
        """
        
        return [f"{key} is controlling {self.controls[key]}" for key in self.controls]

    @DiscordGame.command(user=["player_select"], help="join game as {arg1}")
    def join(self, player_name, *, DiscordAuthorContext):
        """
        Command: Let's a player join the game as 'player_name'
        """
        
        #validate the player_name
        if not self.validate_player_name(player_name):
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot Join Game as: {player_name}. Allowed character set: 'a-z', 'A-Z', '0-9'")
        
        players = self.get_users_players(DiscordAuthorContext)
        
        #prevent a player from joining the game if they already are in it (unless in debug mode)
        if self.debug or not len(players):
        
            #register the player, give the author control over that player, and give that player the role 'player'
            player = self.register_player(DiscordAuthorContext, player_name, RPSPlayer)
            player.give_role("player")
            self.controls[str(DiscordAuthorContext)] = player_name
            self.reset_player(player)
            
            return f"{DiscordAuthorContext} joined as {player_name}"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot Join Game, You've already joined as {[player.name for player in players]}")
            
    @DiscordGame.command(player=["player_select"], help="remove player {arg1} from the game")
    def kick(self, player_name):
        """
        Command: Kick a player from the game
        """
    
        if self.check_player_registry(player_name):
            player = self.get_player_from_name(player_name) 
            self.remove_player(player_name)
            
            return f"{player_name} as been kicked"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"{player_name} not found")