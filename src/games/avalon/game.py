import os
import shutil
import random
from emoji import EMOJI_ALIAS_UNICODE as EMOJIS

from .board import GameBoard
from .players import AvalonPlayer

from ..common import GameBase
from ..common import GameClasses
from ..common import GameExceptions
from ..common import utils

RESOURCES_FOLDER = os.path.join("..", "resources")
  
AVALON_FOLDER=os.path.join(RESOURCES_FOLDER, "avalon")
CHARACTERS_FOLDER = os.path.join(RESOURCES_FOLDER, "avalon", "characters")

TEMP_BASE = os.path.join(RESOURCES_FOLDER, "temp")
if not os.path.isdir(TEMP_BASE):
    os.mkdir(TEMP_BASE)

class AvalonCharacter:
    def __init__(self, name, team, description, requires = None, prohibits = None, required_by = None, character_cards = None, special_character = False, hidden_from_merlin = False, hidden_from_evil = False):
   
        self.name = name
        self.team = team
        self.description = description
        
        #dependancies on other characters
        if requires is None:
            requires = set()
        if prohibits is None:
            prohibits = set()
        if required_by is None:
            required_by = set()
        
        self.requires = requires
        self.prohibits = prohibits
        self.required_by = required_by
        
        #location of character card files
        if character_cards is None:
            character_cards = [os.path.join(CHARACTERS_FOLDER, "unknown.jpg")]
        
        self.character_cards = character_cards
        
        #whether this is a special character or a Vanilla Character
        self.special_character = special_character
        
        #special rules
        self.hidden_from_merlin = hidden_from_merlin
        self.hidden_from_evil = hidden_from_evil
        
    def get_random_character_card(self):
    
        return random.choice(self.character_cards)
        
    def __str__(self):
        return str(self.name)
        
DiscordGame = GameBase.getBaseGameClass()
class Avalon(DiscordGame):
    
    _all_states = ["new_game", "team_select", "voting", "mission", "stab", "game_end"]
    
    _all_characters = [
    
        AvalonCharacter(name = "Vanilla Good",
                        team = "Team Good",
                        description = "Loyal Servant of Arthur (Team Good)",
                        character_cards = [os.path.join(CHARACTERS_FOLDER, f"Servant{i}.jpg") for i in [1,2,3,4,5]]
                        ),        

        AvalonCharacter(name = "Vanilla Evil",
                        team = "Team Evil",
                        description = "Minion of Mordred (Team Evil)",
                        character_cards = [os.path.join(CHARACTERS_FOLDER, f"Minion{i}.jpg") for i in [1,2,3]]
                        ),
    
        AvalonCharacter(name = "Merlin",
                        team = "Team Good",
                        description = "Knows Evil",
                        requires = {"Assassin"},
                        required_by = {"Assassin", "Percival", "Morgana", "Mordred", "Oberon", "Mordroberon"},
                        character_cards = [os.path.join(CHARACTERS_FOLDER, "Merlin.jpg")],
                        special_character = True
                        ),
                        
        AvalonCharacter(name = "Assassin",
                        team = "Team Evil",
                        description = "Attempts to Assassinate Merlin",
                        requires = {"Merlin"},
                        required_by = {"Merlin", "Percival", "Morgana", "Mordred", "Oberon", "Mordroberon"},
                        character_cards = [os.path.join(CHARACTERS_FOLDER, "Assassin.jpg")],
                        special_character = True
                        ),
                        
        AvalonCharacter(name = "Percival",
                        team = "Team Good",
                        description = "Knows Merlin",
                        requires = {"Merlin", "Assassin"},
                        required_by = {"Morgana"},
                        character_cards = [os.path.join(CHARACTERS_FOLDER, "Percival.jpg")],
                        special_character = True
                        ),

        AvalonCharacter(name = "Morgana",
                        team = "Team Evil",
                        description = "Appears as Merlin to Percival",
                        requires = {"Merlin", "Assassin", "Percival"},
                        character_cards = [os.path.join(CHARACTERS_FOLDER, "Morgana.jpg")],
                        special_character = True
                        ),

        AvalonCharacter(name = "Mordred",
                        team = "Team Evil",
                        description = "Unknown to Merlin",
                        requires = {"Merlin", "Assassin"},
                        prohibits = {"Mordroberon"},
                        character_cards = [os.path.join(CHARACTERS_FOLDER, "Mordred.jpg")],
                        special_character = True,
                        hidden_from_merlin = True
                        ),

        AvalonCharacter(name = "Oberon",
                        team = "Team Evil",
                        description = "Unknown to Evil",
                        requires = {"Merlin", "Assassin"},
                        prohibits = {"Mordroberon"},
                        character_cards = [os.path.join(CHARACTERS_FOLDER, "Oberon.jpg")],
                        special_character = True,
                        hidden_from_evil = True
                        ),       

        AvalonCharacter(name = "Mordroberon",
                        team = "Team Evil",
                        description = "Unknown to Merlin or Evil",
                        requires = {"Merlin", "Assassin"},
                        prohibits = {"Mordred", "Oberon"},
                        character_cards = [os.path.join(CHARACTERS_FOLDER, "Mordroberon.jpg")],
                        special_character = True,
                        hidden_from_merlin = True,
                        hidden_from_evil = True
                        )                          
    ]
    
    _all_enable_rules = {
    
        "mission_log" : {
            "description" : "Enable to allow checking the Mission Log with the Command 'check message_log'",
            "enable_message" : "Checking Mission Log Enabled! (check with command 'check mission_log')",
            "disable_message" : "Checking Mission Log Disabled!",
            "default" : False
        },
        
        "vote_log" : {
            "description" : "Enable to allow checking the Vote Log with the Command 'check vote_log'",
            "enable_message" : "Checking Vote Log Enabled! (check with command 'check vote_log')",
            "disable_message" : "Checking Vote Log Disabled!",
            "default" : False
        },
        
        "auto_next" : {
            "description" : "Enable to have the game automatically call 'next' when all votes/mission_cards are in (does nothing is button_prompts is enabled)",
            "enable_message" : "Auto Next Enabled! (game will now automatically call 'next' when votes/mission_cards are in)",
            "disable_message" : "Auto Next Disabled! ('next' will no longer be automatically called by the game",
            "default" : False
        },
        
        "emojis" : {
            "description" : "Enable to have game messages include emojis",
            "enable_message" : "Emojis Enabled for messages from the Game!",
            "disable_message" : "Emojis Disabled for messages from the Game!",
            "default" : True
        },

        "button_prompts" : {
            "description" : "Enable using Button Prompts perform in game actions",
            "enable_message" : "Button Prompts Enabled! (Now most in game actions will be controlled via Emoji Buttons)",
            "disable_message" : "Button Prompts Disabled!",
            "default" : True
        }
    
    }
    
    _message_symbols  = {
    
        "leader" : {"text" : "Team Leader", "emoji_text" : "Team Leader :crown:"},
        
        "hammer" : {"text" : "Hammer", "emoji_text" : ":hammer:"},
        
        "on mission" : {"text" : "On Mission", "emoji_text" : ":crossed_swords:"},
        
        "approve" : {"text" : "approve", "emoji_text" : ":white_check_mark:"},
        
        "reject" : {"text" : "reject", "emoji_text" : ":x:"},
        
        "Team Good" : {"text" : "", "emoji_text" : ":blue_circle:"},
        
        "Team Evil" : {"text" : "", "emoji_text" : ":red_circle:"}
    
    }
    
    _option_emojis = {
        
        EMOJIS[":one:"] : 1,
        EMOJIS[":two:"] : 2,
        EMOJIS[":three:"] : 3,
        EMOJIS[":four:"] : 4,
        EMOJIS[":five:"] : 5,
        EMOJIS[":six:"] : 6,
        EMOJIS[":seven:"] : 7,
        EMOJIS[":eight:"] : 8,
        EMOJIS[":nine:"] : 9,
        EMOJIS[":ten:"] : 10,
        EMOJIS[":white_check_mark:"] : "yes",
        EMOJIS[":x:"] : "no"
    
    }
    
    _yes_no_emojis = [EMOJIS[":white_check_mark:"], EMOJIS[":x:"]]
    _number_emojis = [EMOJIS[f":{key}:"] for key in ["one","two","three","four","five","six","seven","eight", "nine", "ten"]]
    
    _team_prompt_timeout = 300.0 #Give them 5 min to pick a team
    _vote_prompt_timeout = 120.0 #Give them 2 min to vote
    _mission_prompt_timeout = 120.0 #Give them 2 min to vote
    _stab_prompt_timeout = 300.0 #Give them 2 min to vote
    
    def __init__(self, debug):
        self.debug = debug
    
        self.state = "new_game"
        self.controls = {}
        
        self.game_board = None
        self.player_order = []
        
        self.special_characters = set()
        self.on_mission = set()
        self.mission_cards = []
        
        self.winning_team = None
        self.temp_dir = utils.generate_temp_dir(TEMP_BASE)
        
        self.lock_voting = False
        
        self.enable_mission_log = self._all_enable_rules["mission_log"]["default"]
        self.enable_vote_log = self._all_enable_rules["vote_log"]["default"]
        self.enable_auto_next = self._all_enable_rules["auto_next"]["default"]
        self.enable_emojis = self._all_enable_rules["emojis"]["default"]
        self.enable_button_prompts = self._all_enable_rules["button_prompts"]["default"]
    
    def validate_player_name(self, player_name):
    
        character_whitelist = "abcdefghijklmnopqrstuvwxyz0123456789"
    
        for char in player_name.lower():
        
            if char not in character_whitelist:
            
                return False
                
        return True            
    
    def get_message_symbol(self, symbol):
    
        if symbol in self._message_symbols:
        
            if self.enable_emojis:
                return self._message_symbols[symbol]["emoji_text"]
            else:
                return self._message_symbols[symbol]["text"]
        
        else:
            return symbol
    
    def get_character_from_name(self, character_name):
    
        for character in self._all_characters:
            if character.name == character_name:
                return character
         
        raise GameExceptions.DiscordGameError(f"Requested character name not found: {character_name}")   
    
    def add_character(self, character):
    
        if character in self.special_characters:
            raise GameExceptions.DiscordGameIllegalMove(f"{character} is already in the game!")
        else:
            message = [f"Added {character} to the game."]
    
        self.special_characters.add(character)
        special_character_names = [character.name for character in self.special_characters]
        
        to_add = [character_name for character_name in character.requires if character_name not in special_character_names]
        to_remove = [character_name for character_name in character.prohibits if character_name in special_character_names]
        
        [self.special_characters.add(self.get_character_from_name(character_name)) for character_name in to_add]
        [self.special_characters.remove(self.get_character_from_name(character_name)) for character_name in to_remove] 

        if len(to_add):
            message.append(f"Also added the following dependant characters from the game: {to_add}")
            
        if len(to_remove):
            message.append(f"Removed the following characters prohibited by {character}: {to_remove}")
            
        return message
        
    def remove_character(self, character):
    
        if character not in self.special_characters:
            raise GameExceptions.DiscordGameIllegalMove(f"{character} is not in the game!")
        else:
            message = [f"Removed {character} from the game"]
            
        self.special_characters.remove(character)
        special_character_names = [character.name for character in self.special_characters]
           
        to_remove = [character_name for character_name in character.required_by if character_name in special_character_names]
        
        [self.special_characters.remove(self.get_character_from_name(character_name)) for character_name in to_remove] 

        if len(to_remove):
            message.append(f"Removed the following characters that require {character}: {to_remove}")
            
        return message
    
    def kill_game(self):
        shutil.rmtree(self.temp_dir)
    
    def reset_player(self, player):
        player.clear_game_fields()
        player.remove_role("team_good", "team_evil", "leader", "team", "assassin")
    
    def reset_game(self):
        
        for player in self.get_players_in_registry():
            self.reset_player(player)
            
        self.game_board = None
        self.state = "new_game"
        self.on_mission = set()
        
        self.winning_team = None
        
        self.lock_voting = False
    
    def get_player_info(self, player):
    
        private_info = player.private_info
        return private_info   
        
    def get_public_player_info(self):
        player_objects = [self.get_player_from_name(player_name) for player_name in self.player_order]        
        player_info = [f"{player.player_id} | {player.public_info[0]} | {player.public_info[1]}" for player in player_objects]
        return "\n".join(player_info)
    
    def find_team_leader(self):
        team_leaders = [player for player in self.get_players_in_registry() if player.has_role('leader')]
        if len(team_leaders) == 0:
            raise GameExceptions.DiscordGameError(f"Somehow there's no Team Leader???")
        elif len(team_leaders) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"Somehow there's more than one Team Leader???: {team_leaders}")
            
        return team_leaders[0]
    
    def get_help_message(self):
    
        if self.state == "new_game":
            return "\nEveryone join and select the rules!"    
        
        elif self.state == "team_select":
            for player in self.get_players_in_registry():
                if player.has_role("leader"):
                    return f"\n{player.name} please choose {self.game_board.get_current_mission_count()} players for the mission [command: 'choose <player>']"
            
        elif self.state == "voting":
            return "\nEveryone vote approve or reject on the current mission! (Preferebly secretly) [command: 'vote approve' or 'vote reject']"
            
        elif self.state == "mission":
            return f"\n{', '.join([player.name for player in self.on_mission])} please select pass or fail [command: 'mission pass' of 'mission fail']"
        
        elif self.state == "stab":
            return "\nThree Missions have Passed!\nAssassin please try to stab Merlin"
        
        elif self.state == "game_end":
            return f"\n{self.winning_team}\n Play Again?"
            
        else:
        
            raise GameExceptions.DiscordGameError("Game in bad game state!")
    
    ################################
    #Normal Game Progress Functions#
    ################################
    
    def set_up_game(self):
    
        ##############################################
        #Generate Game Board and Shuffle Player Order#
        ##############################################
    
        self.game_board = GameBoard(len(self.get_players_in_registry()), self.temp_dir, AVALON_FOLDER)
       
        random.shuffle(self.player_order)
        
        #######################################################################
        #Determine Character Card Deck and assign each Player a Character Card#
        #######################################################################
        
        character_card_deck = list(self.special_characters)
        
        #count how many good/evil special characters there are
        evil_special_count = 0
        good_special_count = 0
        for character_card in character_card_deck:
            if character_card.team == "Team Evil":
                evil_special_count += 1
            elif character_card.team == "Team Good":
                good_special_count += 1
            else:
                raise GameExceptions.DiscordGameError(f"Character '{character_card}' has unknown team: {character_card.team}")
        
        #figure out how many players are on each team
        evil_player_count = self.game_board.get_team_evil_count()
        good_player_count = self.game_board.player_count - evil_player_count
        
        #figure out how many Vanilla Good/Evil Character Cards need to be added to Deck
        evil_vanilla_count = evil_player_count - evil_special_count
        good_vanilla_count = good_player_count - good_special_count
        
        #add Vanilla Evil Character Cards
        if evil_vanilla_count >= 0:
            character_card_deck += [self.get_character_from_name("Vanilla Evil")] * evil_vanilla_count
        else:
            self.reset_game()
            raise GameExceptions.DiscordGameIllegalMove("Too many evil special characters for current player count")
            
        #add Vanilla Good Character Cards
        if good_vanilla_count >= 0:
            character_card_deck += [self.get_character_from_name("Vanilla Good")] * good_vanilla_count
        else:
            self.reset_game()
            raise GameExceptions.DiscordGameIllegalMove("Too many good special characters for current player count")
        
        #Shuffle Character Deck
        random.shuffle(character_card_deck)
        
        #Assign Each Player a Character Card and subsequent roles: "team_evil", "team_good", "assassin", etc
        for player_name, character_card in zip(self.player_order, character_card_deck):
            
            player = self.get_player_from_name(player_name)
            player.character = character_card
            
            if player.character.team == "Team Evil":
                player.give_role("team_evil")
            elif player.character.team == "Team Good":
                player.give_role("team_good")
            else:
                raise GameExceptions.DiscordGameError(f"Character '{character_card}' has unknown team: {character_card.team}")
                
            if player.character.name == "Assassin":
                player.give_role("assassin")
        
        ##########################################        
        #Determine private info each player knows#
        ##########################################
        
        #merlin knows all the non Mordred/Mordroberon Spies
        merlin_info = [player.name for player in self.get_players_in_registry() if (player.character.team == "Team Evil" and (not player.character.hidden_from_merlin))]
        
        #percival knows Merlin and Morgana
        percival_info = [player.name for player in self.get_players_in_registry() if (player.character.name in ["Merlin", "Morgana"])]
        
        #Team Evil (except for Mordroberon/Oberon) knows who's on Team Evil (except for Mordroberon/Oberon)
        evil_info = [player.name for player in self.get_players_in_registry() if (player.character.team == "Team Evil" and (not player.character.hidden_from_evil))]
        
        #shuffle the hidden information
        random.shuffle(merlin_info)
        random.shuffle(percival_info)
        random.shuffle(evil_info)
        
        #set each individual players private info
        for player_name in self.player_order:
            
            player = self.get_player_from_name(player_name)
            info = f"Your Player name is: {player.name}\n"
            info += f"Your Character is: {player.character.name}\n"
            info += f"You are on: {player.character.team}\n"
            
            #case: Merlin
            if player.character.name == "Merlin":
                info += "You know the following are members of Team Evil:\n  " + "\n  ".join(merlin_info)
                if "Mordred" in [special_character.name for special_character in self.special_characters]:
                    info += "\n\nHowever Mordred (evil) is unknown to you"
                if "Mordroberon" in [special_character.name for special_character in self.special_characters]:
                    info += "\n\nHowever Mordroberon (evil) is unknown to you"
            
            #case: Percival
            elif player.character.name == "Percival":
                info += "You see the following players:\n  " + "\n  ".join(percival_info)
                if len(percival_info) == 1:
                    info += "\n\nThis player is Merlin!"
                elif len(percival_info) == 2:
                    info += "\n\nOne of them in Merlin, the other Morgana"
                else:
                    self.reset_game()
                    raise DIscordGameError("Percival sees more than two characters???")

            #case: Team Evil but not 'hidden_from_evil'
            elif (player.character.team == "Team Evil") and (not player.character.hidden_from_evil):
                info += "You know the following are members of Team Evil:\n  " + "\n  ".join(evil_info)
                if "Oberon" in [special_character.name for special_character in self.special_characters]:
                    info += "\n\nHowever Oberon (evil) is unknown to you"
                if "Mordroberon" in [special_character.name for special_character in self.special_characters]:
                    info += "\n\nHowever Mordroberon (evil) is unknown to you"
            
            #case: 'hidden_from_evil' or Team Good and without special information
            else:
                info += "You don't know who anyone is. Good Luck!"
        
            character_card = player.character.get_random_character_card()
        
            player.private_info = player.create_message_for(text = info, image = character_card, send_both = True)
                        
        ####################################
        #Assign Team Leader to first Player#
        ####################################
        
        #assign team leader to 1st player
        starting_player = self.get_player_from_name(self.player_order[0])
        starting_player.give_role("leader")
        starting_player.public_info[0] = self.get_message_symbol("leader")
        
        #assign hammer to 5th Player
        hammer_player = self.get_player_from_name(self.player_order[4])
        hammer_player.public_info[0] = self.get_message_symbol("hammer")
        
        ##############################################################################################################
        #Create a Message with the game board, public player info, each players private info and poke the team leader#
        ##############################################################################################################
        
        #game board info
        message = self.game_board.generate_board()
        
        #public player info
        message.append(self.get_public_player_info())
        
        #private player info
        for player_name in self.player_order:
            player = self.get_player_from_name(player_name)
            message.append(self.get_player_info(player))
        
        #DM the Team Leader
        team_leader_message = starting_player.create_message_for(f"{starting_player.name}: You are the Team Leader! Choose {self.game_board.get_current_mission_count()} players for your Mission! [command: 'choose <player_name>']")
        message.append(team_leader_message)
        
        #####################################################################
        #Move to 'team_select', add the help message, and return the message#
        #####################################################################
        self.state = "team_select"
        self.on_mission = set()
        message.append(self.get_help_message())
        
        ##############################################
        #Create the CommandResultPrompt if neccessary#
        ##############################################
        
        #add a CommandResultPrompt if playing with "Button Prompts Enabled"
        if self.enable_button_prompts:
            message.append(self.create_team_select_prompt(starting_player))
        
        return message

    def start_vote(self):
       
        ###################################################################
        #check that the mission count matches number of players on mission#
        ###################################################################
       
        mission_count = self.game_board.get_current_mission_count()
        on_mission = len(self.on_mission)
        
        if on_mission < mission_count:
            raise GameExceptions.DiscordGameIllegalMove(f"Not enough players on the mission! Need {mission_count}")
        elif on_mission > mission_count:
            raise GameExceptions.DiscordGameIllegalMove(f"Too many players on the mission! Need {mission_count}")
        else:
            pass
        
        ################################################################################
        #Send each player a message telling them to vote and add public info to message#
        ################################################################################

        message = []
        #only DM players if button prompts is disabled
        if not self.enable_button_prompts:
        
            dm_message = f"Vote on the proposed Mission!\n"
            dm_message += f"     Team Leader: {self.find_team_leader().name}\n"
            dm_message += f"     Team: {[player.name for player in self.on_mission]}\n"
            dm_message += f"     Vote Track: {self.game_board.vote_track}\n"
            dm_message += f"     [command: 'vote approve' or 'vote reject']"
        
            message += [player.create_message_for(text = f"{player.name}: {dm_message}") for player in self.get_players_in_registry()]    
            message.append(self.get_public_player_info())        
        
        ################################################################
        #Move to 'voting', add the help message, and return the message#
        ################################################################
  
        self.state = "voting"
        message.append(self.get_help_message())
        
        ###############################################
        #Create the CommandResultPrompts if neccessary#
        ###############################################
        
        if self.enable_button_prompts:
            title = f"Vote to Approve or Reject the Mission\n"
            title += f"     Team Leader: {self.find_team_leader().name}\n"
            title += f"     Team: {[player.name for player in self.on_mission]}\n"
            title += f"     Vote Track: {self.game_board.vote_track}"
            description = f"Approve: {self._yes_no_emojis[0]} \n Reject: {self._yes_no_emojis[1]}"
            result_message = f"You chose:"
        
            for player in self.get_players_in_registry():
                message.append(GameClasses.CommandResultPrompt(player = player,
                                                               title = f"{player.name}:\n{title}",
                                                               func_name = "process_vote_prompt",
                                                               emojis = self._yes_no_emojis,
                                                               dm = True,
                                                               description = description,
                                                               result_message = result_message,
                                                               timeout = self._vote_prompt_timeout))
        
        return message
    
    def process_vote(self, message = None):
    
        if message is None:
            message = []
    
        ################################################
        #Determine how many approves/rejects there were#
        ################################################
        
        #Get a list of players in player order
        players = [self.get_player_from_name(player_name) for player_name in self.player_order]
        
        approve_count = 0
        reject_count = 0
        non_voters = []
        for player in players:
            if player.vote == None:
                non_voters.append(player.name)
            elif player.vote == "approve":
                approve_count += 1
            elif player.vote == "reject":
                reject_count += 1
            else:
                raise GameExceptions.DiscordGameError(f"Somehow managed to get unknown vote value: ({player.name},{player.vote})")
                
        if len(non_voters) > 0:
            raise GameExceptions.DiscordGameIllegalMove(f"The following players still need to vote: {non_voters}")
        
        ################################################
        #Create a Vote Log and reset each players' vote#
        ################################################
        
        #find the team leader
        team_leader = self.find_team_leader()        
        
        #create a vote log of how everyone voted and add that to the vote log and message
        vote_log = f"================================\nMISSION {self.game_board.current_mission + 1}\n"
        vote_log += f"Vote Track: {self.game_board.vote_track}\n"
        vote_log += f"Team Leader: {team_leader.name}\n"
        vote_log += f"Team: {[player.name for player in self.on_mission]}\n\n"
        vote_log += "\n".join([f"{player.name} : {self.get_message_symbol(player.vote)}" for player in players])
        vote_log += "\n"
        
        #add the vote log to the games vote log
        self.game_board.vote_log.append(vote_log)
        
        #start add the vote log to the message
        message.append(vote_log)
        
        #remove all the votes from each player
        for player in players:
            player.vote = None
        
        ###################################################
        #Process that the mission was approved or rejected#
        ###################################################
        
        if approve_count > reject_count:
            
            #######################
            #Mission approved path#
            #######################
            
            #mission approved message
            message.append("\nMISSION APPROVED\n")
            
            #assign the 'team' role to everyone on the mission
            for mission_player in self.on_mission:
                mission_player.give_role("team")
                
            #reset the vote track
            self.game_board.reset_vote_track()
            
            #send a message to each on mission player telling them to vote but only if button prompts are enabled
            if not self.enable_button_prompts:
                dm_message = f"Choose pass or fail for the Mission!\n"
                dm_message += f"   Team: {[player.name for player in self.on_mission]}\n"
                dm_message += f"   Fails Required: {self.game_board.number_fails_required(self.game_board.current_mission)}\n"
                dm_message += f"   [command: 'mission pass' or 'mission fail']"
                
                message += [player.create_message_for(text = f"{player.name}: {dm_message}") for player in self.on_mission]
            
            #move to next phase
            self.state = "mission"
            message += self.game_board.generate_board()
            message.append(self.get_help_message())
            
            ###############################################
            #Create the CommandResultPrompts if neccessary#
            ###############################################
            
            if self.enable_button_prompts:
        
                title = "Vote to Pass or Fail the Mission\n"
                title += f"     Team Leader: {self.find_team_leader().name}\n"
                title += f"     Team: {[player.name for player in self.on_mission]}\n"
                title += f"     Fails Required: {self.game_board.number_fails_required(self.game_board.current_mission)}\n"
                description = f"Pass: {self._yes_no_emojis[0]} \n Fail: {self._yes_no_emojis[1]}"
                result_message = f"You chose:"
        
                for player in self.on_mission:
                    message.append(GameClasses.CommandResultPrompt(player = player,
                                                       title = f"{player.name}:\n{title}",
                                                       func_name = "process_mission_prompt",
                                                       emojis = self._yes_no_emojis,
                                                       dm = True,
                                                       description = description,
                                                       result_message = result_message,
                                                       timeout = self._mission_prompt_timeout))
            
            return message
        
        else:
            #######################
            #Mission rejected path#
            #######################
            
            #mission rejected message
            message.append("\nMISSION REJECTED\n")
            
            #check to see if the game is over due to the vote track being at 5
            if self.game_board.vote_track >= 5:
                
                ############################
                #Game Over: Hammer Rejected#
                ############################
                
                #Create the game over message
                self.winning_team = "\n5 Teams got voted down in a row! Team Evil Wins!\n"
                
                #add people's characters to the public info cache
                for player in players:
                    player.public_info = [self.get_message_symbol(player.character.team), player.character.name]
                
                #reset the people on the mission
                self.on_mission = set()
                
                #move to the game end state
                self.state="game_end"
                message += self.game_board.generate_board()
                message.append(self.get_public_player_info())
                message.append(self.get_help_message())
                return message
                
            else:
            
                ###################################################
                #Advance Vote Track and Try to field a new mission#
                ###################################################
            
                #advance the vote track
                self.game_board.advance_vote_track()
                
                #clear on_mission
                self.on_mission = set()
                
                #clear public info
                for player in players:
                    player.public_info[1] = "."
                    
                #move the team leader to the next player
                
                #find current team leader
                current_leader = self.find_team_leader()
                current_leader.public_info[0] = "."
                        
                #find the next team leader
                leader_index = self.player_order.index(current_leader.name) + 1
                if leader_index == len(self.player_order):
                    leader_index = 0
                next_leader = self.get_player_from_name(self.player_order[leader_index])
                
                #remove leader role from current leader
                current_leader.remove_role("leader")
                #add leader role to next leader (if they are the hammer, add the leader symbol to the hammer symbol)
                next_leader.give_role("leader")
                if next_leader.public_info[0] == self.get_message_symbol("hammer"):
                    next_leader.public_info[0] = f"{self.get_message_symbol('leader')} | {self.get_message_symbol('hammer')}"
                else:
                    next_leader.public_info[0] = self.get_message_symbol("leader")
                
                #DM the Team Leader but only if button prompts are disabled
                team_leader_message = next_leader.create_message_for(f"{next_leader.name}: You are the Team Leader! Choose {self.game_board.get_current_mission_count()} players for your Mission! [command: 'choose <player_name>']" )
                message.append(team_leader_message)
                
                #go back to "team_select"
                self.state = "team_select"
                message += self.game_board.generate_board()
                message.append(self.get_public_player_info())
                message.append(self.get_help_message())
                
                ##############################################
                #Create the CommandResultPrompt if neccessary#
                ##############################################
                
                #add a CommandResultPrompt if playing with "Button Prompts Enabled"
                if self.enable_button_prompts:
                    message.append(self.create_team_select_prompt(next_leader))
                
                return message        
    
    def go_on_mission(self, message = None):
    
        if message is None:
            message = []
        
        ############################################
        #Determine how many passes/fails there were#
        #############################################
    
        passes = 0
        fails = 0
        players_not_voted = []
        for player in self.on_mission:
            mission_card = player.mission_card
            if mission_card is None:
                players_not_voted.append(player.name)
            elif mission_card == "pass":
                passes += 1
            elif mission_card == "fail":
                fails += 1
            else:
                raise GameExceptions.DiscordGameError("Unexpected Mission Card")
        
        #check to make sure everyone's voted
        if len(players_not_voted) > 0:
            raise GameExceptions.DiscordGameIllegalMove(f"The following players haven't played yet: {players_not_voted}")
        
        ###########################################
        #Determine, Log and Display Mission Result#
        ###########################################
        
        #Determine: pass or fail
        required_fails = self.game_board.number_fails_required(self.game_board.current_mission)
        mission_failure = fails >= required_fails
        
        #determine the team leader
        team_leader = self.find_team_leader()       
                
        #log the mission and player information
        mission_info = [f"================================\nMISSION {self.game_board.current_mission + 1}"]
        mission_info += [f"Team Leader: {team_leader.name}"]
        mission_info += [f"Team: {[player.name for player in self.on_mission]}"]
        
        msg_text = "\n".join(mission_info)        
        
        #add pass/fail count to message
        msg_text += f"\n\nThere were:\nPasses: {passes}\nFails: {fails}"
        
        #generate the image message (The Pass/Fail cards)
        mission_array = (["pass"] * passes) + (["fail"] * fails)
        file_name = f"mission_{self.game_board.current_mission}.jpg"
        self.game_board.create_mission_reveal(self.temp_dir, mission_array, file_name)
        
        msg_image = os.path.join(self.temp_dir, file_name)

        #create mission log message
        mission_log = GameClasses.CommandResultMessage(text = msg_text, image = msg_image, send_both=True)
        
        #Log Mission Results
        self.game_board.mission_log.append(msg_text)
        
        #Display Mission results
        message.append(mission_log)
        
        ########################
        #Process Mission Result#
        ########################
        
        if mission_failure:
            #####################
            #Mission Failed Path#
            #####################
            
            message.append("\nMISSION FAILED!\n")
            self.game_board.set_mission_results(self.game_board.current_mission, self.game_board._fail_token)
            self.game_board.failed_mission_count += 1
            
        else:
            #####################
            #Mission Passed Path#
            #####################
    
            message.append("\nMISSION PASSED!\n")
            self.game_board.set_mission_results(self.game_board.current_mission, self.game_board._pass_token)
            self.game_board.passed_mission_count += 1
 
        #render board
        self.game_board.render_board()
        
        #remove all the mission_cards from each player and remove each player from the mission
        players = self.get_players_in_registry()
        for player in players:
            player.mission_card = None
            player.remove_role("mission")
        
        #reset the people on the mission
        self.on_mission = set()
        
        if self.game_board.failed_mission_count >= 3:
        
            ##########################
            #Game Over Team Evil Wins#
            ##########################
            
            #Create the game over message
            self.winning_team = "\nThree Missions Have Failed! Team Evil Wins!\n"
                
            #add people's characters to the public info cache
            for player in players:
                player.public_info = [self.get_message_symbol(player.character.team), player.character.name]
               
            #go to the 'game end'
            self.state="game_end"
            message += self.game_board.generate_board()
            message.append(self.get_public_player_info())
            message.append(self.get_help_message())
            return message
        
        elif self.game_board.passed_mission_count >= 3:
        
            #############################
            #Team Good Passed 3 Missions#
            #############################
        
            if "Merlin" in [character.name for character in self.special_characters]:
        
                ########################
                #Move to the Stab Phase#
                ########################
        
                #remove info from public info cache
                for player in players:
                    player.public_info = [".","."]
               
                #DM the assassin(s) to try to stab Merlin
                message += [player.create_message_for(text = f"{player.name}: Consult with the rest of Team Evil and attemp to stab Merlin! [command: 'stab <player_name>']") for player in self.get_players_in_registry() if player.has_role("assassin")]
               
                #go to 'stab'
                self.state = "stab"
                message += self.game_board.generate_board()
                message.append(self.get_public_player_info())
                message.append(self.get_help_message())
                
                ##############################################
                #Create the CommandResultPrompt if neccessary#
                ##############################################
                
                #add a CommandResultPrompt if playing with "Button Prompts Enabled"
                if self.enable_button_prompts:
                
                    #find the assassin
                    assassin_player = None
                    for player in self.get_players_in_registry():
                        if player.has_role("assassin"):
                            if assassin_player is None:
                                assassin_player = player
                            else:
                                raise GameExceptions.DiscordGameError(f"Somehow there is more than one Assassin: {player.name} & {assassin_player.name}")                         
                
                    emojis = self._number_emojis[:self.game_board.player_count]
        
                    title = [f"Assassin: Please Try to Stab Merlin:"]
                    title += [f"{player_name} : {emoji}" for player_name, emoji in zip(self.player_order, emojis)]
                    title = "\n".join(title)
        
                    description = "Stab Merlin!"
        
                    result_message = "You chose the following player to stab:"
        
                    message.append(GameClasses.CommandResultPrompt(player = assassin_player,
                                               title = title,
                                               func_name = "process_stab_prompt",
                                               emojis = emojis,
                                               dm = False,
                                               count = 1,
                                               key = "stab_prompt",
                                               description = description,
                                               result_message = result_message,
                                               timeout = self._stab_prompt_timeout))
                                
                return message
                
            else:
                
                ##########################
                #Game Over Team Good Wins#
                ##########################
                
                #Create the game over message
                self.winning_team = "\nThree Missions Have Passed! Team Good Wins!\n"
                
                #add people's characters to the public info
                for player in players:
                    player.public_info = [self.get_message_symbol(player.character.team), player.character.name]
               
                #move to the game end state
                self.state="game_end"
                message += self.game_board.generate_board()
                message.append(self.get_public_player_info())
                message.append(self.get_help_message())
                return message
                
        else:
            ##########################
            #Move back to Team Select#
            ##########################
                
            #increment the current mission counter
            self.game_board.current_mission += 1
            
            #Mark current mission as current mission
            self.game_board.set_mission_results(self.game_board.current_mission, self.game_board._current_token)
            
            #clear public info
            for player in players:
                player.public_info = [".","."]
                    
            #move the team leader to the next player#

            #find the current team leader
            current_leader = self.find_team_leader()
                                    
            #find the next team leader
            leader_index = self.player_order.index(current_leader.name) + 1
            if leader_index == len(self.player_order):
                leader_index = 0
            next_leader = self.get_player_from_name(self.player_order[leader_index])
                
            #remove leader role from current leader
            current_leader.remove_role("leader")
            #add leader role to next leader
            next_leader.give_role("leader")
            next_leader.public_info[0] = self.get_message_symbol("leader")
            
            #add the hammer symbol the 5th player (assuming team leader is the 1st player)
            hammer_index = leader_index + 4
            if hammer_index >= len(self.player_order):
                hammer_index -= len(self.player_order)
            hammer_player = self.get_player_from_name(self.player_order[hammer_index])
            hammer_player.public_info[0] = self.get_message_symbol("hammer")
            
            #DM the Team Leader
            team_leader_message = next_leader.create_message_for(f"{next_leader.name}: You are the Team Leader! Choose {self.game_board.get_current_mission_count()} players for your Mission! [command: 'choose <player_name>']" )
            message.append(team_leader_message)
                
            #go back to "team_select"
            self.state = "team_select"
            message += self.game_board.generate_board()
            message.append(self.get_public_player_info())
            message.append(self.get_help_message())
            
            ##############################################
            #Create the CommandResultPrompt if neccessary#
            ##############################################
            
            #add a CommandResultPrompt if playing with "Button Prompts Enabled"
            if self.enable_button_prompts:
                message.append(self.create_team_select_prompt(next_leader))
            
            return message      
    
    def process_stab(self, assassin_name, guess):
        players = self.get_players_in_registry()       
        
        #find merlin
        merlins = [player.name for player in players if player.character.name == "Merlin"]
        if len(merlins) == 0:
            raise GameExceptions.DiscordGameError("Somehow there's no Merlin???")
        elif len(merlins) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError("Somehow there's more than one Merlin???")
        
        merlin = merlins[0]
         
        #let everyone know who the stab choice was
        message = [f"\n{assassin_name} stabbed {guess}"]
         
        if guess == merlin:
            #Case: Merlin was Stabbed
        
            message.append(f"\n{guess} was Merlin!\n")
            
            self.winning_team = "Merlin was stabbed! Team Evil wins!"
            
        else:
            #Case: Merline was not Stabbed!!
            message.append(f"\n{guess} was NOT Merlin! {merlin} was!\n")
            
            self.winning_team = "Merlin was NOT Stabbed! Team Good wins!"
            
        #add people's characters to the public info cache
        for player in players:
            player.public_info = [self.get_message_symbol(player.character.team), player.character.name]
               
        #move to the game end state
        self.state="game_end"
        message += self.game_board.generate_board()
        message.append(self.get_public_player_info())
        message.append(self.get_help_message())
        return message
    
    ###################################
    #Prompt Result Processing Functions#
    ###################################

    def process_team_prompt(self, results):
        
        #validate the result from the team prompt
        if len(results) == 0:
            raise GameExceptions.DiscordGameError("result from 'team prompt' is empty")
        elif len(results) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"result from 'team prompt' has too many results: {results.keys()}")
            
        if "team_prompt" not in results:
            raise GameExceptions.DiscordGameError(f"unexpected key from 'team prompt': {results.keys()}")
            
        results = results["team_prompt"]
        
        if results is None:
            self.lock_voting = False
            raise GameExceptions.DiscordGameIllegalMove(f"The Team Selection Prompt Timed Out. Please Select members for the Team Manually (with [choose <player>])")
        
        player_count = self.game_board.player_count
        
        for result in results:
            if result not in self._number_emojis[:player_count]:
                raise GameExceptions.DiscordGameError(f"unexpected emoji from 'team prompt': {result}")
        
        choices = [self._option_emojis[result] for result in results]
                
        #figure out which players were chosen
        chosen_player_names = [self.player_order[i-1] for i in choices] #the option emojis are 1 indexed so the option 1 corresponds to the 0th player in the player_order
        
        for player_name in chosen_player_names:
            player = self.get_player_from_name(player_name)
            player.public_info[1] = self.get_message_symbol("on mission")
            self.on_mission.add(player)
                   
        return self.start_vote() 
        
    def process_vote_prompt(self, results):
        
        player_count = self.game_board.player_count
        
        #validate the result from the vote prompt
        if len(results) < player_count:
            raise GameExceptions.DiscordGameError(f"Recieved Less Vote Prompt responses than Players: {results.keys()} ")

        vote_dict = {}
        for player_name, vote_emojis in results.items():
            
            #validate the result key (make sure it represents an actual player
            if player_name not in self.player_order:
                raise GameExceptions.DiscordGameError(f"Non-Registered Player voted in the Vote Prompt: {player_name} ")
            
            #validate that the player only voted for one thing
            if vote_emojis is None:
                self.lock_voting = False
                raise GameExceptions.DiscordGameIllegalMove(f"'{player_name}' took to long and their Vote Prompt Timed Out. All Players please vote Manually (with [vote <choice>])")
            elif len(vote_emojis) == 0:
                raise GameExceptions.DiscordGameError(f"{player_name} managed to vote for nothing somehow")
            elif len(vote_emojis) == 1:
                pass
            else:
                raise GameExceptions.DiscordGameError(f"{player_name} managed to vote for more than one option somehow")
            
            vote_emoji = list(vote_emojis)[0]
                        
            vote = self._option_emojis.get(vote_emoji, None)
            
            if vote == "yes":
                vote_dict[player_name] = "approve"
            elif vote == "no":
                vote_dict[player_name] = "reject"
            else:
                raise GameExceptions.DiscordGameError(f"'{player_name}' gave an unexpected vote: emoji= {vote_emoji} | vote={vote}")
                   
        for player_name, vote in vote_dict.items():
            player = self.get_player_from_name(player_name)
            player.vote = vote
            
        return self.process_vote()
        
    def process_mission_prompt(self, results):
               
        #validate the result from the vote prompt
        if len(results) < len(self.on_mission):
            raise GameExceptions.DiscordGameError(f"Recieved Less Mission Prompt responses than Players On Mission: {results.keys()}")

        mission_dict = {}
        for player_name, mission_emojis in results.items():
            
            player = self.get_player_from_name(player_name)
            
            #validate the result key (make sure it represents an actual player on the mission
            if player not in self.on_mission:
                raise GameExceptions.DiscordGameError(f"Player not on Mission Voted in Mission Prompt: {player_name} ")
            
            #validate that the player only voted for one thing
            if mission_emojis is None:
                self.lock_voting = False
                raise GameExceptions.DiscordGameIllegalMove(f"'{player_name}' took to long and their Mission Prompt Timed Out. All Players on Mission please vote Manually (with [mission <choice>])")
            elif len(mission_emojis) == 0:
                raise GameExceptions.DiscordGameError(f"{player_name} managed to choose nothing for the mission somehow")
            elif len(mission_emojis) == 1:
                pass
            else:
                raise GameExceptions.DiscordGameError(f"{player_name} managed to choose more than one option for the mission somehow")
            
            mission_emoji = list(mission_emojis)[0]
                        
            mission_card = self._option_emojis.get(mission_emoji, None)
            
            if mission_card == "yes":
                mission_dict[player_name] = "pass"
            elif mission_card == "no":
                mission_dict[player_name] = "fail"
            else:
                raise GameExceptions.DiscordGameError(f"'{player_name}' gave an unexpected choice for the mission: emoji= {mission_emoji} | choice={mission_card}")
                   
        for player_name, mission_card in mission_dict.items():
            player = self.get_player_from_name(player_name)
            player.mission_card = mission_card
            
        return self.go_on_mission()
        
    def process_stab_prompt(self, results):
               
        #validate the result from the stab prompt
        if len(results) == 0:
            raise GameExceptions.DiscordGameError("result from 'stab prompt' is empty")
        elif len(results) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"result from 'stab prompt' has too many results: {results.keys()}")
            
        if "stab_prompt" not in results:
            raise GameExceptions.DiscordGameError(f"unexpected key from 'stab prompt': {results.keys()}")
            
        stab_emojis = results["stab_prompt"]
        
        if stab_emojis is None:
            self.lock_voting = False
            raise GameExceptions.DiscordGameIllegalMove(f"The Merlin Stab Prompt Timed Out. Please Try to Stab Merlin Manually (with [stab <player>])")
        
        #find the assassin
        assassin_player = None
        for player in self.get_players_in_registry():
            if player.has_role("assassin"):
                if assassin_player is None:
                    assassin_player = player
                else:
                    raise GameExceptions.DiscordGameError(f"Somehow there is more than one Assassin: {player.name} & {assassin_player.name}")
        
        if len(stab_emojis) == 0:
            raise GameExceptions.DiscordGameError(f"{assassin_player.name} managed to choose nothing for stabbing Merlin")
        elif len(stab_emojis) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"{assassin_player.name} managed to choose more than one option for stabbing Merlin somehow")
        
        stab_emoji = list(stab_emojis)[0]
        player_count = self.game_board.player_count
        
        if stab_emoji not in self._number_emojis[:player_count]:
            raise GameExceptions.DiscordGameError(f"unexpected emoji from 'stab prompt': {stab_emoji}")
                
        stab_choice = self._option_emojis[stab_emoji]
                
        #figure out which player was chosen
        chosen_player = self.player_order[stab_choice-1] #the option emojis are 1 indexed so the option 1 corresponds to the 0th player in the player_order
                    
        return self.process_stab(assassin_player.name, chosen_player)
    
    #############################
    #create CommandResultPrompts#
    #############################
    
    def create_team_select_prompt(self, team_leader):
        
        emojis = self._number_emojis[:self.game_board.player_count]
        mission_count = self.game_board.get_current_mission_count()
        
        title = [f"{team_leader.name}: Choose {mission_count} players for the mission:"]
        title += [f"{player_name} : {emoji}" for player_name, emoji in zip(self.player_order, emojis)]
        title = "\n".join(title)
        
        description = "Choose Team"
        
        result_message = "You chose the players at the following positions:"
        
        return GameClasses.CommandResultPrompt(player = team_leader,
                                               title = title,
                                               func_name = "process_team_prompt",
                                               emojis = emojis,
                                               dm = False,
                                               count = mission_count,
                                               key = "team_prompt",
                                               description = description,
                                               result_message = result_message,
                                               timeout = self._team_prompt_timeout)
        
    
    ###############
    #Game Commands#
    ###############
    
    @DiscordGame.command(player=_all_states, help="restart the game (go back to 'new_game')", requires_lock = True)
    def restart(self):
        self.reset_game()
        
        return "Restarting Game!"
    
    @DiscordGame.command(player = _all_states, help="progress game to next phase", requires_lock = True)
    def next(self):
    
        try:
            #lock voting is button prompts enabled
            if self.enable_button_prompts:
                self.lock_voting = True
    
            if self.state == "new_game":
                return self.set_up_game()    
        
            elif self.state == "team_select":
                return self.start_vote()
            
            elif self.state == "voting":
                return self.process_vote()
            
            elif self.state == "mission":
                return self.go_on_mission()
        
            elif self.state == "stab":
                return ["Currently Waiting for the Assassin to Stab someone\n", self.get_help_message()]
        
            elif self.state == "game_end":
            
                self.reset_game()
                self.state = "new_game"
                return ["New Game!\n", self.get_public_player_info(), self.get_help_message()]
            
            else:
        
                raise GameExceptions.DiscordGameError("Game in bad game state!")
                
        except Exception as e:
            #if an exception was thrown unlock voting
            self.lock_voting = False
            raise e
    
    @DiscordGame.command(player = _all_states, help="take control of a player", debug = True)
    def control(self, player_name, *, DiscordAuthorContext, DiscordChannelContext):
        player = self.get_player_from_name(player_name)
        if player.discord_name == str(DiscordAuthorContext):
            self.controls[str(DiscordAuthorContext)] = player_name
            return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = f"{str(DiscordAuthorContext)} is now controlling {player_name}")
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"{str(DiscordAuthorContext)} doesn't own {player_name}")
        
    @DiscordGame.command(user= _all_states, help="see who's controlling which player", debug=True)
    def check_control(self):
        return [f"{key} is controlling {self.controls[key]}" for key in self.controls]

    @DiscordGame.command(user=["new_game"], help="join game as {arg1}")
    def join(self, player_name, *, DiscordAuthorContext):
        
        #validate the player_name
        if not self.validate_player_name(player_name):
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot Join Game as: {player_name}. Allowed character set: 'a-z', 'A-Z', '0-9'")
        
        players = self.get_users_players(DiscordAuthorContext)
        
        #prevent a player from joining the game if they already are in it (unless in debug mode)
        if self.debug or not len(players):
        
            player = self.register_player(DiscordAuthorContext, player_name, AvalonPlayer)
            player.give_role("player")
            self.controls[str(DiscordAuthorContext)] = player_name
            self.player_order.append(player_name)
            self.reset_player(player)
            
            return f"{DiscordAuthorContext} joined as {player_name}"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot Join Game, You've already joined as {[player.name for player in players]}")
            
    @DiscordGame.command(player=["new_game"], help="remove player {arg1} from the game")
    def kick(self, player_name):
        if self.check_player_registry(player_name):
            player = self.get_player_from_name(player_name) 
            self.player_order.remove(player_name)
            self.remove_player(player_name)
            
            return f"{player_name} as been kicked"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"{player_name} not found")
    
    @DiscordGame.command(player=_all_states, help="options: board, players, rules, my_info, help")
    def check(self, category, *, DiscordAuthorContext, DiscordChannelContext):
        
        category = category.lower()
        
        if category == "board":
            if self.game_board == None:
                return GameClasses.CommandResultMessage(text = "NEW GAME", destination = DiscordChannelContext)
            return self.game_board.generate_board(channel = DiscordChannelContext)
        
        elif category == "players":
            return GameClasses.CommandResultMessage(text = self.get_public_player_info(), destination = DiscordChannelContext)
            
        elif category == "rules":
            #special characters
            message = ["The special characters are:"] + [f"    {character} | {character.team} | {character.description}" for character in self.special_characters]
            
            message.append("")
            if self.enable_mission_log:
                message.append("'check mission_log' is enabled")
               
            if self.enable_vote_log:
                message.append("'check vote_log' is enabled")
                
            if self.enable_auto_next:
                message.append("Auto Next is enabled")
                
            if self.enable_emojis:
                message.append("Emojis in the Game Messages are enabled")
                
            if self.enable_button_prompts:
                message.append("Use of Button Prompts to take Game Actions is Enabled!")
            
            return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = "\n".join(message))
        
        elif category == "my_info":
            player_name = self.controls[str(DiscordAuthorContext)]
            player = self.get_player_from_name(player_name)
        
            return self.get_player_info(player)
        
        elif category == "help":
            
            return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = self.get_help_message())
      
        elif category == "mission_log":
        
            if self.enable_mission_log:
            
                if self.state == "new_game":
                
                    return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = "No Mission History Available")
                    
                else:
                
                    return [GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = log) for log in self.game_board.mission_log]
                    
            else:
            
                raise GameExceptions.DiscordGameIllegalMove("Checking the Mission Log is not enabled")    
        
        elif category == "vote_log":
        
            if self.enable_vote_log:
            
                if self.state == "new_game":
                
                    return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = "No Vote History Available")
                    
                else:
                
                    return [GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = log) for log in self.game_board.vote_log]
                    
            else:
            
                raise GameExceptions.DiscordGameIllegalMove("Checking the Vote Log is not enabled")
        
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"check option '{category}' not recognized")
    
    @DiscordGame.command(player=_all_states, help="print all currently available commands")
    def commands(self, *, DiscordChannelContext):
    
        commands = self.check_current_commands()
        
        message = [f"{command.name} | {command.help_message} | {roles}" for command, roles in commands.items()]
        
        return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = "\n".join(message))
    
    @DiscordGame.command(user=["new_game"], help="print the rule options (for change_rule)")
    def rule_options(self, *, DiscordChannelContext):
        
        message = []
        
        #add characters rules
        message.append("Special Characters:")
        for character in [character for character in self._all_characters if character.special_character]:
            message.append(f"rule: {character} | options: 'add' 'remove' | description: {character.description}")

        message.append("")
        
        #add enable rules
        message.append("Enable/Disable-able rules:")
        for rule, info in self._all_enable_rules.items():
            message.append(f"rule : '{rule}' | options: 'enable' 'disable' | description: {info['description']}")
            
        return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = "\n".join(message))         
    
    @DiscordGame.command(player=["new_game"], help="change a game rule (ex. change_rule Merlin add)")
    def change_rule(self, rule, value):
        
        value = value.lower()
        
        if rule in [character.name for character in self._all_characters if character.special_character]:
        
            if value == "add":
            
                return self.add_character(self.get_character_from_name(rule))
                
            elif value == "remove":
                
                return self.remove_character(self.get_character_from_name(rule))
                
            else:
            
                raise GameExceptions.DiscordGameIllegalMove(f"modifiyer not recognized, please select 'add' or 'remove' to change the character rule {rule}")
        
        elif rule in self._all_enable_rules:
        
            if value == "enable":
            
                rule_boolean = True
                message = self._all_enable_rules[rule]["enable_message"]
                
            elif value == "disable":
            
                rule_boolean = False
                message = self._all_enable_rules[rule]["disable_message"]
                
            else:
            
                raise GameExceptions.DiscordGameIllegalMove(f"modifiyer not recognized, please select 'enable' or 'disable' to change rule: {rule}")
                
            if rule == "mission_log":
                self.enable_mission_log = rule_boolean
            elif rule == "vote_log":
                self.enable_vote_log = rule_boolean
            elif rule == "auto_next":
                self.enable_auto_next = rule_boolean
            elif rule == "emojis":
                self.enable_emojis = rule_boolean
            elif rule == "button_prompts":
                self.enable_button_prompts = rule_boolean
            else:
                raise GameExceptions.DiscordGameError(f"Rule dictionary misconfigured for rule: {rule}")
                
            return message
                
        else:
        
            raise GameExceptions.DiscordGameIllegalMove(f"Rule not recognized: {rule}")
    
    @DiscordGame.command(leader=["team_select"], help="choose a player to add the the mission", requires_lock = True)
    def choose(self, player_name):
        
        player = self.get_player_from_name(player_name)
        if player in self.on_mission:
            raise GameExceptions.DiscordGameIllegalMove(f"{player_name} is already on the mission.")
        else:
            if len(self.on_mission) >= self.game_board.get_current_mission_count():
                raise GameExceptions.DiscordGameIllegalMove(f"There are already {len(self.on_mission)} people on the mission!")
            else:
                player.public_info[1] = self.get_message_symbol("on mission")
                self.on_mission.add(player)
                return f"{player_name} was added to the mission"
            
    @DiscordGame.command(leader=["team_select"], help="remove a player from the mission", requires_lock = True)
    def remove(self, player_name):
        
        player = self.get_player_from_name(player_name)
        if player in self.on_mission:
            player.public_info[1] = "."
            self.on_mission.remove(player)
            return f"{player_name} was removed from the mission"
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"{player_name} is NOT on the mission.")
        
    @DiscordGame.command(player=["voting"], help="vote 'approve' or 'reject' on the current mission")
    def vote(self, choice, *, DiscordAuthorContext):
        
        if self.lock_voting:
            raise GameExceptions.DiscordGameIllegalMove("Cannot Vote using the 'vote' Command while prompts are active!")
        
        choice = choice.lower()
        
        player_name = self.controls[str(DiscordAuthorContext)]
        player = self.get_player_from_name(player_name)
        
        if player.vote is not None:
            return player.create_message_for(text = "Vote failed: You already voted!")
            
        else:
            if choice == "approve":
                player.vote = "approve"
                message = player.create_message_for(text = f"You voted 'approve' as {player.name}")
            elif choice == "reject":
                player.vote = "reject"
                message = player.create_message_for(text = f"You voted 'reject' as {player.name}")
            else:
                return player.create_message_for(text = f"'{choice}' is not a valid option. Select 'approve' or 'reject'")
        
        #count which players haven't voted
        players_not_voted = []
        for player in self.get_players_in_registry():
            if player.vote is None:
                players_not_voted.append(player.name)
        
        #call next if all players have voted and auto next is enabled and button_prompts is diabled
        if (self.enable_auto_next) and (not self.enable_button_prompts) and (len(players_not_voted) == 0):
        
            return self.process_vote(message = [message])
                
        else:
            return message            
            
    @DiscordGame.command(team=["mission"], help="choose to play 'pass' or 'fail' into the current mission")
    def mission(self, choice, *, DiscordAuthorContext):
        
        if self.lock_voting:
            raise GameExceptions.DiscordGameIllegalMove("Cannot Choose a Mission Card using the 'mission' Command while prompts are active!")
        
        choice = choice.lower()
        
        player_name = self.controls[str(DiscordAuthorContext)]
        player = self.get_player_from_name(player_name)
        
        if player not in self.on_mission:
            return player.create_message_for(text = f"{player_name}, you are not on the Mission!")
        
        if player.mission_card is not None:
            return player.create_message_for(text = f"You've already selected: {player.mission_card}")
            
        else:
            if choice == "pass":
                player.mission_card = "pass"
                message = player.create_message_for(text = f"You chose 'pass' as {player.name}")
            elif choice == "fail":
            
                #only evil players can choose "fail"
                if player.has_role("team_evil"):
            
                    player.mission_card = "fail"
                    message = player.create_message_for(text = f"You voted 'fail' as {player.name}")
                    
                else:
                
                    return player.create_message_for(text = f"Cannot vote 'fail' as {player.name}! Only members of Team Evil can vote 'fail'.")
            else:
                return player.create_message_for(text = f"'{choice}' is not a valid option. Select 'pass' or 'fail'")
        
        #count which players haven't choosen a Mission Card
        players_not_voted = []
        for player in self.on_mission:
            if player.mission_card is None:
                players_not_voted.append(player.name)
        
        #call next if all players have voted and auto next is enabled and button_prompts is diabled
        if (self.enable_auto_next) and (not self.enable_button_prompts) and  (len(players_not_voted) == 0):
            
            return self.go_on_mission(message = [message])
                    
        else:
            return message        
                
    @DiscordGame.command(assassin=["stab"], help="choose who to stab as the assassin", requires_lock = True)
    def stab(self, guess, *, DiscordAuthorContext):
    
        #check to make sure an actual player was chosen
        if not self.check_player_registry(guess):
            raise GameExceptions.DiscordGameIllegalMove(f"{guess} is not a recognized player in the game! Choose again")
        
        return self.process_stab(self.controls[str(DiscordAuthorContext)], guess)
        
        #TO BE DELETED:    
        
        players = self.get_players_in_registry()       
        
        #find merlin
        merlins = [player.name for player in players if player.character.name == "Merlin"]
        if len(merlins) == 0:
            raise GameExceptions.DiscordGameError("Somehow there's no Merlin???")
        elif len(merlins) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError("Somehow there's more than one Merlin???")
        
        merlin = merlins[0]
         
        #let everyone know who the stab choice was
        message = [f"\n{self.controls[str(DiscordAuthorContext)]} stabbed {guess}"]
         
        if guess == merlin:
            #Case: Merlin was Stabbed
        
            message.append(f"\n{guess} was Merlin!\n")
            
            self.winning_team = "Merlin was stabbed! Team Evil wins!"
            
        else:
            #Case: Merline was not Stabbed!!
            message.append(f"\n{guess} was NOT Merlin! {merlin} was!\n")
            
            self.winning_team = "Merlin was NOT Stabbed! Team Good wins!"
            
        #add people's characters to the public info cache
        for player in players:
            player.public_info = [self.get_message_symbol(player.character.team), player.character.name]
               
        #move to the game end state
        self.state="game_end"
        message += self.game_board.generate_board()
        message.append(self.get_public_player_info())
        message.append(self.get_help_message())
        return message  