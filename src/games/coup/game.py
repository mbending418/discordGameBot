import os
import shutil
import random
from emoji import EMOJI_ALIAS_UNICODE as EMOJIS

from .players import CoupPlayer

from ..common import GameBase
from ..common import GameClasses
from ..common import GameExceptions
from ..common import utils
from ..common import CommonGamePieces

RESOURCES_FOLDER = os.path.join("..", "resources")
  
COUP_FOLDER=os.path.join(RESOURCES_FOLDER, "coup")

TEMP_BASE = os.path.join(RESOURCES_FOLDER, "temp")
if not os.path.isdir(TEMP_BASE):
    os.mkdir(TEMP_BASE)

class CoupCard:
    def __init__(self, name, action = None, effect = None, reaction = None, card_image = None):
   
        self.name = name
        self.action = action
        self.effect = effect
        self.reaction = reaction
        
        #location of card files
        if card_image is None:
           card_image = os.path.join(COUP_FOLDER, "unknown.jpg")
        
        self.card_image = card_image
        
    def get_card_image(self):
    
        return self.card_image
        
    def __str__(self):
        return str(self.name)
       
DiscordGame = GameBase.getBaseGameClass()
class Coup(DiscordGame):
    
    _all_states = ["new_game",
                   "action",
                   "lose_influence",
                   "reaction",
                   "challenge",
                   "reaction_challenge",
                   "reveal",
                   "exchange", 
                   "game_end"]
                   
    _all_turn_states = ["action",
                        "reaction",
                        "challenge",
                        "reaction_challenge",
                        "exchange"]
    
    _all_cards = [
    
        CoupCard(name = "duke",
                 action = "Tax",
                 effect = "Take 3 coins",
                 reaction= "Blocks Foreign Aid",
                 card_image = os.path.join(COUP_FOLDER, "duke.jpg")),
                 
        CoupCard(name = "assassin",
                 action = "Assassinate",
                 effect = "Pay 3 coins: Choose a player to lose an influence",
                 card_image = os.path.join(COUP_FOLDER, "assassin.jpg")),

        CoupCard(name = "ambassador",
                 action = "Exchange",
                 effect = "Exchange cards with the Court Deck",
                 reaction= "Blocks Steal",
                 card_image = os.path.join(COUP_FOLDER, "ambassador.jpg")),

        CoupCard(name = "captain",
                 action = "Steal",
                 effect = "Take 2 coins from another player",
                 reaction= "Blocks Steal",
                 card_image = os.path.join(COUP_FOLDER, "captain.jpg")),

        CoupCard(name = "contessa",
                 reaction= "Blocks Assassination",
                 card_image = os.path.join(COUP_FOLDER, "contessa.jpg")),                 
    ]
    
    _non_character_actions = [
        ["Income", "Take 1 coin"],
        ["Foreign Aid", "Take 2 coins"],
        ["Coup", "Pay 7 coins: Choose a player to lose an influence"]
    ]
    
    _all_game_actions = ["income", "foreign_aid", "coup", "tax", "assassinate", "steal", "exchange"]
    
    _message_symbols  = {
    
        "current_player" : {"text" : "Current Player", "emoji_text" : "Current Player :crown:"}
    
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
        EMOJIS[":x:"] : "no",
        
        EMOJIS[":dollar:"] : "income",
        EMOJIS[":customs:"] : "foreign_aid",
        EMOJIS[":crown:"] : "coup",
        EMOJIS[":money_bag:"] : "tax",
        EMOJIS[":dagger:"] : "assassinate",
        EMOJIS[":detective:"] : "steal",
        EMOJIS[":ferry:"] : "exchange", 
        
        EMOJIS[":blue_square:"] : "captain",
        EMOJIS[":green_square:"] : "ambassador",
        EMOJIS[":red_square:"] : "contessa",
        EMOJIS[":purple_square:"] : "duke",
        EMOJIS[":white_large_square:"] : "assassin"
    
    }
    
    _challenge_emoji = EMOJIS[":white_check_mark:"]
    _pass_emoji = EMOJIS[":x:"]
    _number_emojis = [EMOJIS[f":{key}:"] for key in ["one","two","three","four","five","six","seven","eight", "nine", "ten"]]
    
    _interrupt_timeout = 30.0 #Give them 30 seconds to challenge or respond
    _prompt_timeout = 120.0 #Give them 2 min to make a decision
    
    _all_enable_rules = {
        
        "emojis" : {
            "description" : "Enable to have game messages include emojis",
            "enable_message" : "Emojis Enabled for messages from the Game!",
            "disable_message" : "Emojis Disabled for messages from the Game!",
            "default" : True
        },

        "button_prompts" : {
            "description" : "Enable using Button Prompts to perform in game actions",
            "enable_message" : "Button Prompts Enabled! (Now most in game actions will be controlled via Emoji Buttons)",
            "disable_message" : "Button Prompts Disabled!",
            "default" : True
        },
        
        "interrupt_prompts" : {
            "description" : "Enable using Button Prompts perform to perform Interrupts (blocking/challenging)",
            "enable_message" : "Button Prompts Enabled! (Now Interrupts will use button prompts if 'Button Prompts' is also enabled)",
            "disable_message" : "Button Prompts Disabled!",
            "default" : True
        }
    
    }
    
    def __init__(self, debug):
        self.debug = debug
    
        self.state = "new_game"
        self.turn_state = None
        
        self.current_action = None
        self.current_action_target = None
        
        self.revealed_cards = []
        self.controls = {}
        
        self.player_order = []
        
        self.temp_dir = utils.generate_temp_dir(TEMP_BASE)
        
        self.enable_emojis = True
        self.enable_buttons = True
        self.enable_interrupts = True

            
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
    
    def kill_game(self):
        shutil.rmtree(self.temp_dir)
    
    def reset_player(self, player):
        player.remove_role("current_player")
        player.clear_game_fields()
    
    def reset_game(self):
        
        for player in self.get_players_in_registry():
            self.reset_player(player)
                    
        self.state = "new_game"
        self.turn_state = None
        
        self.current_action = None
        self.current_action_target = None
        self.reacting_player = None
        self.reacting_player_card = None
        
        self.revealed_cards = []
        self.deck = None
    
    def generate_board(self):   

        message = "======================================================\n"
        message += f"Revealed Cards: {[card.name for card in self.revealed_cards]}"        
        
        for player_name in self.player_order:
            player = self.get_player_from_name(player_name)
            message += f"\n\n{player.name} | cards: {len(player.cards)} | money: {player.money}"
            if player.has_role("current_player"):
                message += f"| {self.get_message_symbol('current_player')}"
        
        message += "\n======================================================\n\n"
        
        return GameClasses.CommandResultMessage(text = message)

    def get_card_from_name(self, card_name):
        
        for card in self._all_cards:
            if card.name == card_name:
                return card
               
        raise GameExceptions.DiscordGameError(f"Requested card name not found: {card_name}")  

    def find_current_player(self):
        current_players = [player for player in self.get_players_in_registry() if player.has_role('current_player')]
        if len(current_players) == 0:
            raise GameExceptions.DiscordGameError(f"Somehow there's no current player")
        elif len(current_players) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"Somehow there's more than current_player???: {current_players}")
            
        return current_players[0]

    def advance_turn_state(self, new_turn_state):
        """
        This function is called whenever the turn progresses to a new phase in: action -> challenge -> reaction -> reaction_challenge
        """
        
        if new_turn_state not in self._all_turn_states:
            raise GameExceptions.DiscordGameError(f"Attempting to advance to an invalid 'turn_state': {new_turn_state}")
        
        self.state = new_turn_state
        self.turn_state = new_turn_state

    def interrupt_turn(self, new_game_state):
        """
        This function is called whenever the current turn is interrupted by
        revealing cards, loss of influence, and/or exchaning cards with the court deck
        
        it caches the game state in the turn state iff. the current turn state isn't alreay being interrupted
        otherwise it just move the game state to the new game state (ie interrupting an interrupt)
        """
        
        if new_game_state not in self._all_states:
            raise GameExceptions.DiscordGameError(f"Attempting to advance to an invalid 'game_state': {new_game_state}")
        
        if self.state in self._all_turn_states:
            self.turn_state = self.state
        
        self.state = new_game_state
        
    def return_from_turn_interrupt(self):
        """
        return from an interrupted turn and move the game state to phase we are in the turn
        """
    
        self.state = self.turn_state

    ####################################
    #Create a given prompt for a player#
    ####################################
    
    def create_action_prompt(self, player):
    
        if player.money >= 10:
            #if they player has 10 or more money they have to coup
            pretitle = f"{player.name}: You have 10 or more coins and have to choose the action 'coup'"
            self.current_action = "coup"
            return self.create_target_prompt(player, pretitle)
            
        else:
            #if the player can actually pick what to do because they don't have to coup
            options = list(self._all_game_actions)
            
            #remove any options the player doesn't have enough money for
            if player.money < 3:
                options.remove("assassinate")
            if player.money < 7:
                options.remove("coup")
                
            #build the emoji list
            emojis = []
            for emoji, option in self._option_emojis.items():
                if option in options:
                    emojis.append(emoji)
            
            title = f"{player.name}: It is your turn. Choose a game action to take"
            description = "\n\n".join([f"{emoji} : {self._option_emojis[emoji]}" for emoji in emojis])
            result_message = "You chose to take the following action:"
    
            return GameClasses.CommandResultPrompt(player = player,
                                                   title = title,
                                                   func_name = "process_action_prompt_results",
                                                   emojis = emojis,
                                                   dm = False,
                                                   count = 1,
                                                   key = player.name,
                                                   description = description,
                                                   timeout = self._prompt_timeout)
     
    def create_target_prompt(self, player, pretitle = None):
    
        if pretitle is None:
            title = ""
        else:
            title = pretitle + "\n"
    
        #create a list of emojis and player names
        emojis = self._number_emojis[:len(self.player_order)]
        player_names = list(self.player_order)
        
        #remove the player and option for the player taking the action
        player_index = self.player_order.index(player.name)
        emojis.remove(emojis[player_index])
        player_names.remove(player_names[player_index])
            
        title += f"{player.name}: Choose a player to target with {self.current_action}"
        description = "\n".join([f"{emoji} : {player_name}" for emoji, player_name in zip(emojis, player_names)])
        result_message = "You chose player at postition:"
        
        return GameClasses.CommandResultPrompt(player = player,
                                               title = title,
                                               func_name = "process_target_prompt_results",
                                               emojis = emojis,
                                               dm = False,
                                               count = 1,
                                               key = player.name,
                                               description = description,
                                               timeout = self._prompt_timeout)
         
    def create_lose_influence_prompt(self, player):
    
        #create a list of emojis and card names
        emojis = self._number_emojis[:len(player.cards)]
        card_names = [card.name for card in player.cards]
        
        title = f"{player.name}: Choose a card from your hand to reveal and lose"
        description = "\n".join([f"{emoji} : {card_name}" for emoji, card_name in zip(emojis, card_names)])
        result_message = "You chose the card at position:"
        
        return GameClasses.CommandResultPrompt(player = player,
                                               title = title,
                                               func_name = "process_lose_influence_prompt_results",
                                               emojis = emojis,
                                               dm = True,
                                               count = 1,
                                               key = player.name,
                                               description = description,
                                               timeout = self._prompt_timeout)
        
    def create_exchange_prompt(self, player):
    
        #create a list of emojis and card names
        emojis = self._number_emojis[:len(player.cards)]
        card_names = [card.name for card in player.cards]
        
        title = f"{player.name}: Choose 2 cards to return to the court deck\n\n"
        title += "\n".join([f"{emoji} : {card_name}" for emoji, card_name in zip(emojis, card_names)])
        description = "Choose 2 cards"
        result_message = "You chose the cards at positions:"
        
        return GameClasses.CommandResultPrompt(player = player,
                                               title = title,
                                               func_name = "process_exchange_prompt_results",
                                               emojis = emojis,
                                               dm = True,
                                               count = 2,
                                               key = player.name,
                                               description = description,
                                               timeout = self._prompt_timeout)
        
    def create_reveal_prompt(self, player, claimed_card):
                    
        #create a list of emojis and card names
        emojis = self._number_emojis[:len(player.cards)]
        card_names = [card.name for card in player.cards]
        
        title = f"{player.name}:  Please reveal a {claimed_card} card from your hand; if you cannot, reveal a different card and lose that influence"
        description = "\n".join([f"{emoji} : {card_name}" for emoji, card_name in zip(emojis, card_names)])
        result_message = "You chose the card at position:"
        
        return GameClasses.CommandResultPrompt(player = player,
                                               title = title,
                                               func_name = "process_reveal_prompt_results",
                                               emojis = emojis,
                                               dm = True,
                                               count = 1,
                                               key = player.name,
                                               description = description,
                                               timeout = self._prompt_timeout)

    ##########################
    #Create a given interrupt#
    ##########################
    
    def create_challenge_interrupt(self):
    
        if self.state == "challenge":
            challenged_player = self.find_current_player()
            
            if self.current_action == "tax":
                claimed_card = "duke"
            elif self.current_action == "assassinate":
                claimed_card = "assassin"
            elif self.current_action == "steal":
                claimed_card = "captain"
            elif self.current_action == "exchange":
                claimed_card = "ambassador"
            else:
                raise GameExceptions.DiscordGameError(f"Game State Error: game_state='challenge', current_action='{self.current_action}' should not be possible")

        elif self.state == "reaction_challenge":
            challenged_player = self.reacting_player
            claimed_card = self.reacting_player_card
            
        else:
            raise GameExceptions.DiscordGameError(f"Game State Error: Cannot create challenge interrupt in game_state = {self.state}")
    
        #build the eligible players list (every player besides the challenged player)
        players = [self.get_player_from_name(player_name) for player_name in self.player_order if player_name != challenged_player.name]
    
        #build the emoji list
        emojis = [self._challenge_emoji]
        #find the "pass" emoji
        pass_emoji = self._pass_emoji
                
        title = f"Does anyone wish to challenge {challenged_player.name}'s claim of {claimed_card}?\n\n"
        title += f"Challenge: {emojis[0]}\n"
        title += f"Pass for Everyone: {pass_emoji}"
        
        return GameClasses.CommandResultInterrupt(title = title,
                                                  players = players,
                                                  func_name = "process_challenge_interrupt_results",
                                                  emojis = emojis,
                                                  end_emoji = pass_emoji,
                                                  max_responses = 1,
                                                  timeout=self._interrupt_timeout)
        
    def create_reaction_interrupt(self):
        
        current_player = self.find_current_player()
        
        #build the eligible players list (every player besides the current player)
        #players = [self.get_player_from_name(player_name) for player_name in self.player_order if player_name != current_player.name]
        
        if self.current_action == "foreign_aid":
            
            #the options to block foreign aid
            options = ["duke"]
            
            #build the eligible players list (every player besides the current player can block foreign aid)
            players = [self.get_player_from_name(player_name) for player_name in self.player_order if player_name != current_player.name]
            
        elif self.current_action == "steal":
        
            #the options to block steal
            options = ["captain", "ambassador"]
            
            #build the eligible players list (only the targeted player)
            players = [self.get_player_from_name(self.current_action_target)]
            
        elif self.current_action == "assassinate":
            
            #the options to block the assassination
            options = ["contessa"]
            
            #build the eligible players list (only the targeted player)
            players = [self.get_player_from_name(self.current_action_target)]
        else:
            raise GameExceptions.DiscordGameError(f"Game State Error: game_state='reaction', current_action='{self.current_action}' should not be possible") 
        
        #build the emoji list
        emojis = []
        for emoji, option in self._option_emojis.items():
            if option in options:
                emojis.append(emoji)
                
        #find the "pass" emoji
        pass_emoji = self._pass_emoji

        title = f"Does anyone wish to block {current_player.name}'s attempt at the action: {self.current_action}?\n"
        title += "\n".join([f"Block with {self._option_emojis[emoji]} : {emoji}" for emoji in emojis])
        title += f"\nPass for Everyone: {pass_emoji}"
        
        return GameClasses.CommandResultInterrupt(title = title,
                                                  players = players,
                                                  func_name = "process_reaction_interrupt_results",
                                                  emojis = emojis,
                                                  end_emoji = pass_emoji,
                                                  max_responses = 1,
                                                  timeout=self._interrupt_timeout)        

    ############################################
    #Follow up functions for prompts/interrupts#
    ############################################
    
    def process_action_prompt_results(self, prompt_results):
    
        if len(prompt_results) == 0:
            raise GameExceptions.DiscordGameError("result from 'action prompt' is empty")
        elif len(prompt_results) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"result from 'action prompt' has too many results: {prompt_results.keys()}")
            
        player_name = list(prompt_results.keys())[0]
        choices = prompt_results[player_name]
        
        if choices is None:
            raise GameExceptions.DiscordGameIllegalMove(f"The 'Action Prompt' Timed out. {player_name}: Please Select your Action manually (with 'action [action] [optional-target]')")
        elif len(choices) == 0:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to choose 0 actions")
        elif len(choices) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to more than one action: {choices}")
            
        choice = list(choices)[0]
        
        if choice not in self._option_emojis:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to select a nonvalid emoji: {choice}")
            
        action = self._option_emojis[choice]
                     
        if action in ["coup", "assassinate", "steal"]:
            #if this action requires a target
            self.current_action = action
            
            message = [f"{player_name} has chosen: {action}\nNow {player_name} must choose a target for {action}"]
            message.append(self.create_target_prompt(self.get_player_from_name(player_name)))
            return message
            
        else:
            #if this action does not require a target
            return self.process_action(player_name, action)
       
    def process_target_prompt_results(self, prompt_results):
        
        if len(prompt_results) == 0:
            raise GameExceptions.DiscordGameError("result from 'target prompt' is empty")
        elif len(prompt_results) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"result from 'target prompt' has too many results: {prompt_results.keys()}")
            
        player_name = list(prompt_results.keys())[0]
        choices = prompt_results[player_name]
        
        if choices is None:
            raise GameExceptions.DiscordGameIllegalMove(f"The 'Target Prompt' Timed out. {player_name}: Please Select your Action/Target manually (with 'action [action] [optional-target]')")
        elif len(choices) == 0:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to choose 0 targets")
        elif len(choices) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to more than one target: {choices}")
            
        choice = list(choices)[0]
        
        if choice not in self._option_emojis:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to select a nonvalid emoji: {choice}")
            
        target_index = self._option_emojis[choice] - 1
        target = self.player_order[target_index]
                     
        return self.process_action(player_name, self.current_action, target)
            
    def process_lose_influence_prompt_results(self, prompt_results):
    
        if len(prompt_results) == 0:
            raise GameExceptions.DiscordGameError("result from 'lose influence prompt' is empty")
        elif len(prompt_results) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"result from 'lose influence prompt' has too many results: {prompt_results.keys()}")
            
        player_name = list(prompt_results.keys())[0]
        choices = prompt_results[player_name]
        
        if choices is None:
            raise GameExceptions.DiscordGameIllegalMove(f"The 'Lose Influence Prompt' Timed out. {player_name}: Please select which card you want to reveal manually (with 'reveal [card]')")
        elif len(choices) == 0:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to choose 0 cards")
        elif len(choices) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to more than one card: {choices}")
            
        choice = list(choices)[0]
        
        if choice not in self._option_emojis:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to select a nonvalid emoji: {choice}")
         
        player = self.get_player_from_name(player_name)
         
        card_index = self._option_emojis[choice] - 1
        card = player.cards[card_index]
                     
        return self.process_lost_influence(player, card.name)
    
    def process_exchange_prompt_results(self, prompt_results):
    
        if len(prompt_results) == 0:
            raise GameExceptions.DiscordGameError("result from 'exchange prompt' is empty")
        elif len(prompt_results) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"result from 'exchange prompt' has too many results: {prompt_results.keys()}")
            
        player_name = list(prompt_results.keys())[0]
        choices = prompt_results[player_name]
        
        if choices is None:
            raise GameExceptions.DiscordGameIllegalMove(f"The 'Exchange Prompt' Timed out. {player_name}: Please select which card(s) you want to return to the court deck manually (with 'exchange [card_1] [card_2]')")
        elif len(choices) == 0:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to choose 0 cards")
        elif len(choices) == 1:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to choose only 1 cards")
        elif len(choices) == 2:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to more than two cards: {choices}")
        
        choices = list(choices)
        for choice in choices:
            if choice not in self._option_emojis:
                raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to select a nonvalid emoji: {choice}")
         
        player = self.get_player_from_name(player_name)
        
        cards = []
        for choice in choices:
            card_index = self._option_emojis[choice] - 1
            card = player.cards[card_index]
            cards.append(card)
                     
        return self.process_exchange_cards(player_name, cards[0].name, cards[1].name)
        
    def process_reveal_prompt_results(self, prompt_results):
    
        if len(prompt_results) == 0:
            raise GameExceptions.DiscordGameError("result from 'reveal prompt' is empty")
        elif len(prompt_results) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"result from 'reveal prompt' has too many results: {prompt_results.keys()}")
            
        player_name = list(prompt_results.keys())[0]
        choices = prompt_results[player_name]
        
        if choices is None:
            raise GameExceptions.DiscordGameIllegalMove(f"The 'Reveal Prompt' Timed out. {player_name}: Please select which card you want to reveal manually (with 'reveal [card]')")
        elif len(choices) == 0:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to choose 0 cards")
        elif len(choices) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to more than one card: {choices}")
            
        choice = list(choices)[0]
        
        if choice not in self._option_emojis:
            raise GameExceptions.DiscordGameError(f"{player_name} somehow managed to select a nonvalid emoji: {choice}")
         
        player = self.get_player_from_name(player_name)
         
        card_index = self._option_emojis[choice] - 1
        card = player.cards[card_index]
                     
        return self.process_reveal(player_name, card.name)
        
    def process_challenge_interrupt_results(self, interrupt_results):
    
        if len(interrupt_results) == 0:
            raise GameExceptions.DiscordGameError("result from 'challenge interrupt' is empty")
      
        #get a dict of all players who responded
        responding_players = {player_name : choices for player_name, choices in interrupt_results.items() if len(choices)>0}
        
        if len(responding_players) == 0:
            #no one wants to challenge
            return self.process_challenge()
            
        elif len(responding_players) == 1:
            #one person responded
            
            responding_player = list(responding_players.keys())[0]
            choices = list(responding_players[responding_player])
            
            #make sure exactly one thing was selected
            if len(choices) == 0:
                raise GameExceptions.DiscordGameError("Bad Game State: should be logically impossible to get here")
            elif len(choices) == 1:
                pass
            else:
                raise GameExceptions.DiscordGameError(f"Somehow {responding_player} managed to challenge with more than one emoji response: {choices}")
                
            choice = choices[0]
            
            if choice == self._challenge_emoji:
                return self.process_challenge(responding_player)
            else:
                raise GameExceptions.DiscordGameError(f"Somehow {responding_player} managed to challenge with an invalid emoji: {choice}")
            
        else:
            raise GameExceptions.DiscordGameError(f"Somehow more than one player responded to a 'challenge interrupt': {responding_players.keys()}")
            
    def process_reaction_interrupt_results(self, interrupt_results):
    
        if len(interrupt_results) == 0:
            raise GameExceptions.DiscordGameError("result from 'reaction interrupt' is empty")
      
        #get a dict of all players who responded
        responding_players = {player_name : choices for player_name, choices in interrupt_results.items() if len(choices)>0}
        
        if len(responding_players) == 0:
            #no one wants to react
            return self.process_reaction()
            
        elif len(responding_players) == 1:
            #one person responded
            
            responding_player = list(responding_players.keys())[0]
            choices = list(responding_players[responding_player])
            
            #make sure exactly one thing was selected
            if len(choices) == 0:
                raise GameExceptions.DiscordGameError("Bad Game State: should be logically impossible to get here")
            elif len(choices) == 1:
                pass
            else:
                raise GameExceptions.DiscordGameError(f"Somehow {responding_player} managed to react with more than one emoji response: {choices}")
                
            response = self._option_emojis[choices[0]]
                        
            if response in ["captain", "ambassador", "contessa", "duke", "assassin"]:
                return self.process_reaction(responding_player, response)
            else:
                raise GameExceptions.DiscordGameError(f"Somehow {responding_player} managed to react with an invalid emoji: {choice[0]}")
            
        else:
            raise GameExceptions.DiscordGameError(f"Somehow more than one player responded to a 'reaction interrupt': {responding_players.keys()}")

    ################################################
    #Game Functions called by the process functions#
    ################################################
    
    def lose_influence(self, player_name, message = None):
    
        if message is None:
            message = []
    
        player = self.get_player_from_name(player_name)
    
        if len(player.cards) >= 2:
            message.append(f"{player.name}: Please choose a card to reveal and lose")
            
            if self.enable_buttons:
                message.append(self.create_lose_influence_prompt(player))
            else:
                message.append("DM the bot which card you want to reveal and lose: 'reveal [card]'")
                
                message.append(player.create_message_for(text = f"{player.name}. Please choose a card to reveal and lose: 'reveal [card]'"))
            
            player.give_role("active_player")
            self.interrupt_turn("lose_influence")
            return message
            
        else:
            lost_card = player.cards[0]
            
            message.append(f"{player.name} only has one card in hand and will therefore automatically reveal it.")
            message.append(player.create_message_for(text = f"{player.name}, you only have one card in hand. So you automatically reveal: {lost_card.name}"))
            
            self.interrupt_turn("lose_influence")
            return self.process_lost_influence(player, lost_card.name, message)
    
    def ask_for_reaction(self, message = None):
    
        if message is None:
            message = []
    
        if self.enable_buttons and self.enable_interrupts:
            message.append(self.create_reaction_interrupt())
        else:
            message.append("To react to this move. Use the command: 'reaction [card]'. Where [card] is which card you're responding with: eg. 'reaction ambassador'")
            if self.current_action == "assassinate" or self.current_action == "steal":
                message.append(f"Only {self.current_action_target} may react since they're the target of this move")
            message.append("If no one wants to react. Anyone can use to the command: 'next' to move on.")
        
        self.advance_turn_state("reaction")
        return message
        
    def ask_for_challenge(self, message = None):
    
        if message is None:
            message = []
                
        if self.state == "action":
            self.advance_turn_state("challenge")
        elif self.state == "reaction":
            self.advance_turn_state("reaction_challenge")
        else:
            raise GameGlasses.DiscordGameError(f"Cannot ask for challenge in game state: {self.state}")
        
        if self.enable_buttons and self.enable_interrupts:
            message.append(self.create_challenge_interrupt())
        else:
            message.append("To challenge this claim. Use the command: 'challenge'\nOtherwise have a player use the command 'next' to have everyone pass on challenging")
        
        return message 
    
    def ask_for_reveal(self, player, card, message = None):
    
        if message is None:
            message = []
        
        #if the player has more than one card in hand
        if len(player.cards) >= 2:
        
            player.give_role("active_player")
            self.interrupt_turn("reveal")
        
            if self.enable_buttons:
                message.append(self.create_reveal_prompt(player, card))
            else:
                message.append(f"{player.name}: Please reveal a {card} card from your hand; if you cannot, reveal a different card and lose that influence")
                message.append(player.create_message_for(text=f"{player.name}: Please reveal a {card} card from your hand; if you cannot, reveal a different card and lose that influence [command = 'reveal [card]']"))
        
            return message
        
        #if the player only has one card in hand
        else:
            revealed_card = player.cards[0]
            
            message.append(f"{player.name} only has one card in hand and will therefore automatically reveal it.")
            message.append(player.create_message_for(text = f"{player.name}, you only have one card in hand. So you automatically reveal: {revealed_card.name}"))
        
            self.interrupt_turn("reveal")
            return self.process_reveal(player.name, revealed_card.name, message)            
        
    def process_lost_influence(self, player, lost_card_name, message = None):
    
        if message is None:
            message = []
        
        lost_card = self.get_card_from_name(lost_card_name)
        
        if lost_card not in player.cards:
            raise GameClasses.DiscordGameIllegalMove(f"{player.name} cannot reveal the chosen card because they don't have one")
        
        player.take_cards(lost_card)
        self.revealed_cards.append(lost_card)
        message += player.create_card_messages()
        message.append(f"{player.name} loses an influence and reveals: {lost_card.name}")
        
        player.remove_role("active_player")
        
        #if the player who just lost influence loses
        if len(player.cards) == 0:
            
            message.append(f"{player.name} has lost their last influence and is out of the game!")
            
            if player.has_role("current_player"):
                #if the current player just lost, pass it to the previous player before removing that player from the player order and processing next turn or ending the game
                player.remove_role("current_player")
                
                previous_player_index = self.player_order.index(player.name) - 1
                previous_player = self.get_player_from_name(self.player_order[previous_player_index])
                previous_player.give_role("current_player")
                
                #remove the player who lost from the turn order
                self.player_order.remove(player.name)
                
                #if there is only one player left the game is over
                if len(self.player_order) == 1:
                    return self.process_game_over(message)
                else:
                    return self.process_next_turn(message)
                
            else:
                #if the the player is a player besides the current player, remove them from the player order. If there's only one player left end the game
                self.player_order.remove(player.name)
                
                if len(self.player_order) <= 1:
                    return self.process_game_over(message)
        
        if self.state == "lose_influence":
            #This branch implies a player lost an influence due to an unsuccessful challenge or a game action such as 'coup' or 'assassinate'
        
            if self.turn_state == "action":                
                #This branch implies a player took an action (such as coup or assassinate) which caused a player to lose an influence 
                #Now we need to return from the interrupt and go to the next turn
                
                self.return_from_turn_interrupt()
                return self.process_next_turn(message)
                
            elif self.turn_state == "challenge":
                #This branch implies a player took an action (tax, assassinate, steal, or exchange) was challenged, 
                #AND the challenge was unsuccessful (so the challenging player lost an influence)
                #we need to now resolve the action after the unsuccessful challenge 
                
                current_player = self.find_current_player()
                
                if self.current_action == "tax":
                    self.return_from_turn_interrupt()
                    return self.process_tax(current_player, message)
                
                elif self.current_action == "assassinate":
                    self.return_from_turn_interrupt()
                    return self.process_assassinate_attempt(current_player, message)    
                    
                elif self.current_action == "steal":
                    self.return_from_turn_interrupt()
                    return self.process_steal_attempt(current_player, message)
                    
                elif self.current_action == "exchange":
                    self.return_from_turn_interrupt()
                    return self.process_exchange_action(current_player, message)
                    
                else:
                    raise GameExceptions.DiscordGameError(f"Game State Error: game_state='lose_influence', turn_state='challenge', current_action='{self.current_action}' should not be possible") 
        
            elif self.turn_state == "reaction":
                #This branch implies a player took an action (such as assassinate) which caused a player to lose an influence
                #That could be responded to AND no one chose to respond to the action. That player has lost an influence now we go to the next turn
                
                self.return_from_turn_interrupt()
                return self.process_next_turn(message)
                
            elif self.turn_state == "reaction_challenge":
                #This branch implies a player reactioned to an action with a challengable response (ie they blocked with their Duke, Contessa, Captain or Ambassador)
                #AND this response was challenged unsuccessfully. The challenger lost an influence and the responder blocked the action and now we move on to the next turn
                
                current_player = self.find_current_player()
                
                if self.current_action == "foreign_aid":
                    message.append(f"{current_player.name}'s 'Foreign Aid' was blocked by {self.reacting_player.name}'s {self.reacting_player_card}")
                
                elif self.current_action == "assassinate":
                    message.append(f"{current_player.name}'s attempt to 'Assassinate' {self.current_action_target} was blocked by {self.reacting_player.name}'s {self.reacting_player_card}")
                    
                elif self.current_action == "steal":
                    message.append(f"{current_player.name}'s attempt to 'Steal' from {self.current_action_target} was blocked by {self.reacting_player.name}'s {self.reacting_player_card}")
                    
                else:
                    raise GameExceptions.DiscordGameError(f"Game State Error: game_state='lose_influence', turn_state='reaction_challenge', current_action='{self.current_action}' should not be possible")
                
                self.return_from_turn_interrupt()
                return self.process_next_turn(message)
                
            else:
                raise GameExceptions.DiscordGameError(f"Game State Error: game_state='lose_influence', turn_state='{self.turn_state}' should not be possible") 
        
        elif self.state == "reveal":
            #This branch implies a player revealed a card during a challenge and the revealed card didn't match the challenged card
            
        
            if self.turn_state == "challenge":
                #This branch implies a player took an action (tax, assassinate, steal, or exchange) was challenged, 
                #AND the challenge was successful (so the player taking the action revealed a card in order to lose an influence)
                #we need to now need to return from the interrupt and move on to the next turn
                
                self.return_from_turn_interrupt()
                return self.process_next_turn(message)
                
            elif self.turn_state == "reaction_challenge":
                #This branch implies a player reactioned to an action with a challengable response (ie they blocked with their Duke, Contessa, Captain or Ambassador)
                #AND this response was challenged successfully. The responding player lost an influence and now we have to resolve the successful action
                
                current_player = self.find_current_player()
                
                if self.current_action == "foreign_aid":
                    self.return_from_turn_interrupt()
                    return self.process_foreign_aid_successful(current_player, message)
                
                elif self.current_action == "assassinate":
                    self.return_from_turn_interrupt()
                    return self.process_assassinate_successful(current_player, message)
                    
                elif self.current_action == "steal":
                    self.return_from_turn_interrupt()
                    return self.process_steal_successful(current_player, message)
                    
                else:
                    raise GameExceptions.DiscordGameError(f"Game State Error: game_state='reveal', turn_state='{self.turn_state}' should not be possible") 
        
        else:
            raise GameExceptions.DiscordGameError(f"Game State Error: In game state {self.state} during 'process_lost_influence'")
        
    ####################
    #Process Game Moves#
    ####################
    
    def process_start_game(self):
    
        players = self.get_players_in_registry()
        player_count = len(players)
        if player_count < 3:
            raise GameExceptions.DiscordGameIllegalMove(f"Need at least 3 players to start! There are currently: {player_count}")
        if player_count > 6:
            raise GameExceptions.DiscordGameIllegalMove(f"Max player count is 6! There are currently: {player_count}")
    
        self.deck = CommonGamePieces.DeckOfCards(cards = list(self._all_cards + self._all_cards + self._all_cards))
        for player in players:
            hand = self.deck.draw(2)
            player.give_cards(*hand)
            player.money = 2
        
        self.player_order = [player.name for player in players]
        random.shuffle(self.player_order)
        
        first_player = self.get_player_from_name(self.player_order[0])
        first_player.give_role("current_player")
        
        self.advance_turn_state("action")
        
        self.reacting_player = None
        self.reacting_player_card = None
        
        self.challenging_player = None
        
        self.current_action = None
        self.current_action_target = None
        
        #create a message to each player to let them know their hand
        message = []
        for player in players:
            message += player.create_card_messages()
            
        message.append("Begining Game of Coup!")
        message.append(self.generate_board())
        message.append(f"{first_player.name} it is your turn!")
        
        if self.enable_buttons:
            message.append(self.create_action_prompt(first_player))
        else:
            message.append("Use the command 'action [action]' to take a game action")
            message.append(f"Options: {self._all_game_actions}")
            
            message.append(first_player.create_message_for(text = f"{first_player.name} it's your turn. Please take a game action: 'action [action]'"))
            
        return message   
    
    def process_next_turn(self, message = None):
    
        if message is None:
            message = []
    
        current_player = self.find_current_player()
        
        next_player_index = self.player_order.index(current_player.name) + 1
        if next_player_index == len(self.player_order):
            next_player_index = 0
        next_player = self.get_player_from_name(self.player_order[next_player_index])
        
        current_player.remove_role("current_player")
        next_player.give_role("current_player")
        
        message.append(self.generate_board())
        message.append(f"{next_player.name} it is your turn!")
        
        self.advance_turn_state("action")
        
        self.reacting_player = None
        self.reacting_player_card = None
        
        self.challenging_player = None
        
        self.current_action = None
        self.current_action_target = None
        
        if self.enable_buttons:
            message.append(self.create_action_prompt(next_player))
        else:
            message.append("Use the command 'action [action]' to take a game action")
            message.append(f"Options: {self._all_game_actions}")
            
            message.append(next_player.create_message_for(text = f"{next_player.name} it's your turn. Please take a game action: 'action [action]'"))
                
        return message
    
    def process_action(self, player_name, action, target = None):
    
        player = self.get_player_from_name(player_name)
        
        if (player.money >= 10) and (action != "coup"):
            raise GameExceptions.DiscordGameIllegalMove(f"{player.name}: you have 10 or more money. You have to 'Coup' someone")
        
        self.current_action = action
        self.current_action_target = target
    
        if action == "income":
            
            if target is not None:
                
                raise GameExceptions.DiscordGameIllegalMove("Cannot have a target for move 'income': ex. 'action income'")
            
            return self.process_income(player)
                
        elif action == "foreign_aid":
        
            if target is not None:
                
                raise GameExceptions.DiscordGameIllegalMove("Cannot have a target for move 'foreign_aid': ex. 'action foreign_aid'")
            
            return self.process_foreign_aid_attempt(player)
                    
        elif action == "coup":
        
            if target is None:
            
                raise GameExceptions.DiscordGameIllegalMove("To attempt the action 'coup' you need to choose a target: ex. 'action coup <player_name>'")
        
            if target not in self.player_order:
            
                raise GameExceptions.DiscordGameIllegalMove(f"Player not found: {target}")
                
            if player.money < 7:
            
                raise GameExceptions.DiscordGameIllegalMove(f"You don't have enough money to 'coup': requires 7")
        
            return self.process_coup(player)
                    
        elif action == "tax":
            
            if target is not None:
                
                raise GameExceptions.DiscordGameIllegalMove("Cannot have a target for move 'tax': ex. 'action tax'")
                
            message = [f"{player_name} is attempting to 'Tax' with their Duke. Does anyone wish to challenge them having a Duke?"]
                        
            return self.ask_for_challenge(message)
            
        elif action == "assassinate":
            
            if target is None:
                
                raise GameExceptions.DiscordGameIllegalMove("To attempt the action 'assassinate' you need to choose a target: ex. 'action assassinate <player_name>'")
            
            if target not in self.player_order:
            
                raise GameExceptions.DiscordGameIllegalMove(f"Player not found: {target}")
            
            if player.money < 3:
            
                raise GameExceptions.DiscordGameIllegalMove(f"You don't have enough money to 'assassinate': requires 3")
            
            message = [f"{player_name} is attempting to 'Assassinate' {target} with their Assassin. Does anyone wish to challenge them having an Assassin?"]
                        
            return self.ask_for_challenge(message)
            
        elif action == "steal":
        
            if target is None:
                
                raise GameExceptions.DiscordGameIllegalMove("To attempt the action 'steal' you need to choose a target: ex. 'action steal <player_name>'")
            
            if target not in self.player_order:
            
                raise GameExceptions.DiscordGameIllegalMove(f"Player not found: {target}")
            
            message = [f"{player_name} is attempting to 'Steal' from {target} with their Captain. Does anyone wish to challenge them having a Captain?"]
                        
            return self.ask_for_challenge(message)
            
        elif action == "exchange":
        
            if target is not None:
                
                raise GameExceptions.DiscordGameIllegalMove("Cannot have a target for move 'exchange': ex. 'action exchange'")
                
            message = [f"{player_name} is attempting to 'Exchange' with their Ambassador. Does anyone wish to challenge them having an Ambassador?"]

            return self.ask_for_challenge(message)
            
        else:
        
            raise GameExceptions.DiscordGameIllegalMove(f"Action: {action} not recognized") 
       
    def process_challenge(self, player_name = None):
    
        if player_name is None:
            #if there was no challenge to the card
            
            current_player = self.find_current_player()
            
            if self.turn_state == "challenge":
                #if it's an action that was not challenged then the action resolves
                
                if self.current_action == "tax":
                    message = [f"No one chose to challenge {current_player.name}'s claim of having a Duke."]
                    self.return_from_turn_interrupt()
                    return self.process_tax(current_player, message)
                
                elif self.current_action == "assassinate":
                    message = [f"No one chose to challenge {current_player.name}'s claim of having an Assassin"]
                    self.return_from_turn_interrupt()
                    return self.process_assassinate_attempt(current_player, message)    
                    
                elif self.current_action == "steal":
                    message = [f"No one chose to challenge {current_player.name}'s claim of having an Captain"]
                    self.return_from_turn_interrupt()
                    return self.process_steal_attempt(current_player, message)
                    
                elif self.current_action == "exchange":
                    message = [f"No one chose to challenge {current_player.name}'s claim of having an Ambassador"]
                    self.return_from_turn_interrupt()
                    return self.process_exchange_action(current_player, message)
                    
                else:
                    raise GameExceptions.DiscordGameError(f"Game State Error: game_state='challenge', turn_state='challenge', current_action='{self.current_action}' should not be possible")
                    
            elif self.turn_state == "reaction_challenge":
                #if it's a reaction that was NOT challenged then the reaction successfully blocks the action and we move on to the next turn
                
                message = [f"No one chose to challenge {self.reacting_player.name}'s claim of having {self.reacting_player_card}"]
                message.append(f"{current_player.name}'s attempt at the action '{self.current_action}' is blocked.")
                
                self.return_from_turn_interrupt()
                return self.process_next_turn(message)
                
        #if there was a challenge to the card
        
        if self.turn_state == "challenge":
            challenged_player = self.find_current_player()
        
            if self.current_action == "tax":
                claimed_card = "duke"
            
            elif self.current_action == "assassinate":
                claimed_card = "assassin"
            
            elif self.current_action == "steal":
                claimed_card = "captain"
            
            elif self.current_action == "exchange":
                claimed_card = "ambassador"
            
            else:
                raise GameExceptions.DiscordGameError(f"Game State Error: player is attemping to challenge when the current action is {self.current_action}")
        
        elif self.turn_state == "reaction_challenge":
        
            challenged_player = self.reacting_player
            
            claimed_card = self.reacting_player_card
        
        else:
            raise GameExceptions.DiscordGameError(f"Game State Error: In turn state {self.turn_state} during 'process_challenge'")
    
        #if someone tries to challenge their own action
        if challenged_player.name == player_name:
            raise GameExceptions.DiscordGameIllegalMove(f"{player_name} cannot challenge their own claim.")
    
        self.challenging_player = self.get_player_from_name(player_name)
    
        message = [f"{self.challenging_player.name} is challenging {challenged_player.name}'s claim of having '{claimed_card}'."]
            
        return self.ask_for_reveal(challenged_player, claimed_card, message)
    
    def process_reaction(self, player_name = None, card = None):
    
        if player_name is None:
            #if there was not a reaction to the current action
            
            current_player = self.find_current_player()
                
            if self.current_action == "foreign_aid":
                message = [f"No one chose to try and block {current_player.name}'s foreign aid"]
                self.return_from_turn_interrupt()
                return self.process_foreign_aid_successful(current_player, message)
                
            elif self.current_action == "assassinate":
                message = [f"No one chose to try and block {current_player.name}'s attempt to assassinate"]
                self.return_from_turn_interrupt()
                return self.process_assassinate_successful(current_player, message)
                    
            elif self.current_action == "steal":
                message = [f"No one chose to try and block {current_player.name}'s attempt to steal"]
                self.return_from_turn_interrupt()
                return self.process_steal_successful(current_player, message)
                    
            else:
                raise GameExceptions.DiscordGameError(f"Game State Error: game_state='reaction', current_action='{self.current_action}' should not be possible") 
    
        #if there was a reaction to the current action
        self.reacting_player = self.get_player_from_name(player_name)
        self.reacting_player_card = card
    
        if self.current_action == "foreign_aid":
        
            if player_name == self.find_current_player().name:
                raise GameExceptions.DiscordGameIllegalMove(f"{player_name}: You cannot block your own attempt at 'foreign_aid'")
        
            if card == "duke":
                message = [f"{player_name} is attempting to block 'foreign aid'. Claiming they have a Duke"]
            else:
                raise GameExceptions.DiscordGameIllegalMove(f"Cannot block 'foreign aid' with {card}")
        
        elif self.current_action == "assassinate":
        
            if player_name != self.current_action_target:
                raise GameExceptions.DiscordGameIllegalMove(f"Cannot block 'assassinate' unless you're the target of the assassination attempt")
        
            if card == "contessa":
                message = [f"{player_name} is attempting to block an 'assassination' attempt. Claiming they have a Contessa"]
            else:
                raise GameExceptions.DiscordGameIllegalMove(f"Cannot block 'assassinate' with {card}")
        
        elif self.current_action == "steal":
        
            if player_name != self.current_action_target:
                raise GameExceptions.DiscordGameIllegalMove(f"Cannot block 'steal' unless you're the target of the steal attempt")
    
            if card == "captain":
                message = [f"{player_name} is attempting to block a 'steal' attempt. Claiming they have a Captain"]
            elif card == "ambassador":
                message = [f"{player_name} is attempting to block a 'steal' attempt. Claiming they have an Ambassador"]
            else:
                raise GameExceptions.DiscordGameIllegalMove(f"Cannot block 'steal' with {card}")
    
        else:
            raise GameExceptions.DiscordGameError(f"Game State Error: player is attemping to react when the current action is {self.current_action}")
    
        #currently, all the reactions are challengable. so we need to ask if anyone wants to challenge the reaction
        return self.ask_for_challenge(message)
            
    def process_reveal(self, player_name, card, message = None):
    
        if message is None:
            message = []
    
        player = self.get_player_from_name(player_name)
        message.append(player.create_message_for(text = f"{player_name} you revealed {card}"))    
    
        if self.turn_state == "challenge":
            
            if player.name != self.find_current_player().name:
                raise GameExceptions.DiscordGameIllegalMove(f"{player.name}: {self.find_current_player().name} is currently being challenged and needs to reveal a card not you.")
        
            if self.current_action == "tax":
                claimed_card = "duke"
            
            elif self.current_action == "assassinate":
                claimed_card = "assassin"
            
            elif self.current_action == "steal":
                claimed_card = "captain"
            
            elif self.current_action == "exchange":
                claimed_card = "ambassador"
            
            else:
                raise GameExceptions.DiscordGameError(f"Game State Error: player is attemping to challenge when the current action is {self.current_action}")
                        
        elif self.turn_state == "reaction_challenge":
        
            if player.name != self.reacting_player.name:
                raise GameExceptions.DiscordGameIllegalMove(f"{player.name}: {self.reacting_player.name} is currently being challenged and needs to reveal a card not you.")
                    
            claimed_card = self.reacting_player_card
        
        else:
            raise GameExceptions.DiscordGameError(f"Game State Error: In turn state {self.turn_state} during 'process_challenge'")
        
        player.remove_role("active_player")
        
        message.append(f"{player.name} claimed to have {claimed_card} and revealed {card}.\n")
        if claimed_card == card:
            #if the claimed card matches the revealed card
            
            message.append(f"This matches the claimed card and {self.challenging_player.name} will now lose an influence")
            
            #shuffle the revealed card back into the deck
            removed_card = self.get_card_from_name(card)
            player.take_cards(removed_card)
            self.deck.add_to_deck([removed_card])
            self.deck.shuffle()
            
            #deal the player a new card from the deck
            drawn_cards = self.deck.draw()
            player.give_cards(*drawn_cards)
            
            #send the player a DM letting them know what their new hand is
            message += player.create_card_messages()
        
            message.append(f"{player.name}'s {claimed_card} has been shuffled back into the deck and they've been dealt a new card")
            
            return self.lose_influence(self.challenging_player.name, message)
        else:
            #if the claimed card does NOT match the claimed card
            
            message.append(f"This does NOT match the claimed card {player.name} will now lose this influence")
        
            return self.process_lost_influence(player = player, lost_card_name = card, message = message)
     
    def process_exchange_cards(self, player_name, card_1_name, card_2_name):
        
        player = self.get_player_from_name(player_name)
        
        card_1 = self.get_card_from_name(card_1_name)
        card_2 = self.get_card_from_name(card_2_name)
        
        if player.get_card_count(card_1) < 1:
            raise GameExceptions.DiscordGameIllegalMove(f"You don't have {card_1_name} in your hand. Please try to exchange two cards again")
            
        if player.get_card_count(card_2) < 1:
            raise GameExceptions.DiscordGameIllegalMove(f"You don't have {card_2_name} in your hand. Please try to exchange two cards again")
            
        if (card_1==card_2) and player.get_card_count(card_1) < 2:
            raise GameExceptions.DiscordGameIllegalMove(f"You don't have two copies of {card_1_name} in your hand. Please try to exchange two cards again")
        
        #remove the two exchanged cards from the player and send DM's to the player letting them know their new hand
        player.take_cards(card_1, card_2)
        message = [player.create_message_for(text = f"You returned {card_1_name} and {card_2_name} to the court deck")]
        message += player.create_card_messages()
        message.append(f"{player.name} returned 2 cards to the court deck")
        
        #return the two exchanged cards to the deck and shuffle it
        self.deck.add_to_deck([card_1, card_2])
        self.deck.shuffle()
        message.append("The court deck has been shuffled")
        
        return self.process_next_turn(message)
            
    def process_game_over(self, message = None):
    
        if message is None:
            message = []
    
        if len(self.player_order) == 0:
            raise GameExceptions.DiscordGameError("Somehow the game is over and there are not players left. RIP")
        elif len(self.player_order) == 1:
            pass
        else:
            raise GameExceptions.DiscordGameError("Somehow game over was triggered and there are multiple players left in the game.")
    
        self.state = "game_end"
        self.turn_state = None
        
        winning_player = self.get_player_from_name(self.player_order[0])
        
        message.append(f"GAME OVER\n{winning_player.name} is the only player left standing! They win!!!\n Play Again? (use the command: 'restart')")
        
        return message
            
    ################################################################################
    #Process Game Actions###########################################################
    #(These get called after the action is *not* challenged or the challenge fails)#
    ################################################################################
    
    def process_income(self, player, message = None):
        if message is None:
            message = []
            
        player.money += 1
        message.append(f"{player.name} took 'Income' and gained 1 coin")
            
        return self.process_next_turn(message)
    
    def process_foreign_aid_attempt(self, player, message = None):
        """
        Process an attempt at collecting forign aid, offering the other players the option to block
        (If they don't block, or the block is unsuccessful due to a challenge,
        the game will then call process_foreign_aid_successful)
        """
        
        if message is None:
            message = []
    
        message = [f"{player.name} is attempting to collect 'Foreign Aid'. Does anyone wish to block this action with their Duke?"]
                        
        return self.ask_for_reaction(message)
    
    def process_foreign_aid_successful(self, player, message = None):
        if message is None:
            message = []
            
        player.money += 2
        message.append(f"{player.name} took 'Foreign Aid' and gained 2 coins")
        
        self.return_from_turn_interrupt()
        
        return self.process_next_turn(message)
        
    def process_coup(self, player, message = None):
        if message is None:
            message = []
        
        message.append(f"{player.name} pays 7 coins in order to take the action: 'coup'")
        player.money -= 7
        
        message.append(f"{player.name} has 'couped' {self.current_action_target}.")    
        return self.lose_influence(self.current_action_target, message)
    
    def process_tax(self, player, message = None):
        if message is None:
            message = []
            
        player.money += 3
        message.append(f"{player.name} 'Taxed' and gained 3 coins")
            
        return self.process_next_turn(message)
        
    def process_assassinate_attempt(self, player, message = None):
        """
        Process an assassination attempt, offering the defending player the option to block
        (If they don't block, or the block is unsuccessful due to a challenge,
        the game will then call process_assassinate_successful)
        """
        
        if message is None:
            message = []
                
        message.append(f"{player.name} pays 3 coins in order to take the action: 'assassinate'")
        player.money -= 3
        
        if self.current_action_target in self.player_order:
            message.append(f"{player.name} is attempting to 'assassinate' {self.current_action_target}.\n{self.current_action_target} do you wish to block this action with a Contessa?")
            return self.ask_for_reaction(message)
        else:
            message.append(f"{player.name} is attempting to 'assassinate' {self.current_action_target}.\nHowever, that player is already out of the game so nothing happends")
            return self.process_next_turn(message)
    
    def process_assassinate_successful(self, player, message = None):
        """
        Process a successful assassination
        """
        
        if message is None:
            message = []
            
        message.append(f"{player.name} is assassinating {self.current_action_target}.")
        
        self.return_from_turn_interrupt()
        self.advance_turn_state("action")
        self.interrupt_turn("lose_influence")
        
        if self.current_action_target not in self.player_order:
            message.append("However, that player is already out of the game so nothing happends")
            return self.process_next_turn(message)
        else:        
            return self.lose_influence(self.current_action_target, message)  
    
    def process_steal_attempt(self, player, message = None):
        """
        Process an steal attempt, offering the defending player the option to block
        (If they don't block, or the block is unsuccessful due to a challenge,
        the game will then call process_steal_successful)
        """
    
        if message is None:
            message = []
                
        message.append(f"{player.name} is attempting to 'steal' from {self.current_action_target}.\n {self.current_action_target} do you wish to block this action with a Captain/Ambassador?")    
        
        return self.ask_for_reaction(message)
     
    def process_steal_successful(self, player, message = None):
        """
        Process a successful steal
        """
        
        if message is None:
            message = []
                
        target_player = self.get_player_from_name(self.current_action_target)
        if target_player.money < 2:
            message.append(f"{target_player.name} only has {target_player.money} coin(s) so only that amount will be stolen")
            steal_amount = target_player.money
        else:
            steal_amount = 2
        
        message.append(f"{player.name} is stealing {steal_amount} coin(s) from {self.current_action_target}.")
        
        player.money += steal_amount
        if self.current_action_target not in self.player_order:
            message.append("However, that player is already out of the game so they don't lose any money")
        else:
            target_player.money -= steal_amount
         
        self.return_from_turn_interrupt()
         
        return self.process_next_turn(message)
     
    def process_exchange_action(self, player, message = None):
        if message is None:
            message = []
            
        message.append(f"{player.name} is performing the action: exchange\n{player.name} draws 2 cards from the court deck and now must return 2 cards from their hand to the court deck")
        
        new_cards = self.deck.draw(number=2)
        player.give_cards(*new_cards)
        
        message += player.create_card_messages()
        
        if self.enable_buttons:
            message.append(self.create_exchange_prompt(player))
        else:
            message.append(f"{player.name}: please DM the bot the command 'exchange [card_1] [card_2]' to return [card_1] and [card_2] to the deck")           
            message.append(player.create_message_for(text = f"{player.name}: Use the command 'exchange [card_1] [card_2]' to return [card_1] and [card_2] to the deck"))
        
        self.advance_turn_state("exchange")
        return message

    ###############
    #Game Commands#
    ###############
    
    @DiscordGame.command(player=_all_states, help="restart the game (go back to 'new_game')", requires_lock = True)
    def restart(self):
        self.reset_game()
        
        return "Restarting Game!"
    
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
        
            player = self.register_player(DiscordAuthorContext, player_name, CoupPlayer)
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
    
    @DiscordGame.command(player=_all_states, help="print all currently available commands")
    def commands(self, *, DiscordChannelContext):
    
        commands = self.check_current_commands()
        
        message = [f"{command.name} | {command.help_message} | {roles}" for command, roles in commands.items()]
        
        return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = "\n".join(message))
    
    @DiscordGame.command(player=["new_game"], help="start the game of Coup", requires_lock = True)
    def start(self):
    
        return self.process_start_game()

    @DiscordGame.command(current_player = ["action"], help = "take a particular game action on your turn. ex: 'action coup bob", requires_lock = True)
    def action(self, action, target = None, *, DiscordAuthorContext):
     
        action = action.lower()
     
        player_name = self.controls[str(DiscordAuthorContext)]

        if target == player_name:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot target yourself with {action}. Try again.")

        return self.process_action(player_name, action, target)
    
    @DiscordGame.command(player=['challenge', 'reaction_challenge'], help = "challenge the move or reaction just made", requires_lock = True)
    def challenge(self, *, DiscordAuthorContext):
    
        player_name = self.controls[str(DiscordAuthorContext)]
        
        return self.process_challenge(player_name)  
    
    @DiscordGame.command(player=['reaction'], help = "React to a particular Game Action by claiming to have {arg_1}", requires_lock = True)
    def reaction(self, reaction, *, DiscordAuthorContext):
    
        reaction = reaction.lower()
    
        player_name = self.controls[str(DiscordAuthorContext)]
        
        return self.process_reaction(player_name, reaction)
    
    @DiscordGame.command(player=['challenge', 'reaction', 'reaction_challenge'], help = "Have everyone pass on challenging or reacting", requires_lock = True)
    def next(self):
    
        if (self.state == "challenge") or (self.state == "reaction_challenge"):
        
            return self.process_challenge()
            
        elif self.state == "reaction":
            
            return self.process_reaction()
            
        else:
            
            raise GameExceptions.DiscordGameError(f"Theoretically impossible state. Somehow they managed to call next from '{self.state}'")
    
    @DiscordGame.command(active_player=['lose_influence','reveal'], help = "Reveal a card because a player challenged you or you lost an influence", requires_lock = True)
    def reveal(self, card_name, *, DiscordAuthorContext):
    
        card_name = card_name.lower()
    
        player_name = self.controls[str(DiscordAuthorContext)]
        
        player = self.get_player_from_name(player_name)
        card = self.get_card_from_name(card_name)
        
        if player.get_card_count(card) == 0:
            return player.create_message_for(text = f"You don't have {card_name} in your hand. Choose another")
        
        if self.state == "reveal":
            return self.process_reveal(player_name, card_name)
        elif self.state == "lose_influence":
            message = player.create_message_for(text=f"{player_name} you revealed {card_name}")      
        
            return self.process_lost_influence(player, card_name)
        else:
            raise GameExceptions.DiscordGameError(f"Theoretically impossible state. Somehow they managed to call reveal from '{self.state}'")

    @DiscordGame.command(current_player=['exchange'], help = "Place two cards drawn from 'Exchange' back in the deck", requires_lock = True)
    def exchange(self, card_1, card_2, *, DiscordAuthorContext):
        
        card_1 = card_1.lower()
        card_2 = card_2.lower()
        
        player_name = self.controls[str(DiscordAuthorContext)]
        
        return self.process_exchange_cards(player_name, card_1, card_2)
    
    @DiscordGame.command(player=_all_states, help="options: board, rules, options, my_info")
    def check(self, category, *, DiscordAuthorContext, DiscordChannelContext):
    
        category = category.lower()
        
        if category == "board":
            if self.state == "new_game":
                return GameClasses.CommandResultMessage(text = "NEW GAME", destination = DiscordChannelContext)
            else:
                return self.generate_board()
                
        elif category == "rules":
            
            cheat_sheet = []
            
            for action in self._non_character_actions:
                cheat_sheet.append(f"Character: {None} | Action: {action[0]} | Effect: {action[1]} | Reaction: {None}")
                
            for card in self._all_cards:
                cheat_sheet.append(f"Character: {card.name} | Action: {card.action} | Effect: {card.effect} | Reaction: {card.reaction}")
            
            message = "Rule Cheat Sheet:\n(If 10+ coins you must choose Coup Action during your turn)\n\n"
            message += "\n".join(cheat_sheet)
            
            return GameClasses.CommandResultMessage(text = message, destination = DiscordChannelContext)
            
        elif category == "options":
        
            message = ["Options Enabled:"]
            if self.enable_emojis:
                message.append("     Emojis in Game Messages")
            if self.enable_buttons:
                message.append("     Button Prompts for Game Actions")
            if self.enable_buttons and self.enable_interrupts:
                message.append("     Button Prompts for Game Interrupts (Challenging/Blocking)")
                
            return GameClasses.CommandResultMessage(text = "\n".join(message), destination = DiscordChannelContext)
            
        elif category == "my_info":
        
            if self.state == "new_game":
                return GameClasses.CommandResultMessage(text = "No Info: Game not started", destination = DiscordChannelContext)
            else:
                player_name = self.controls[str(DiscordAuthorContext)]
                player = self.get_player_from_name(player_name)
                return player.create_card_messages()
                
        else:
            raise GameExceptions.DiscordGameIllegalMove(f"check option '{category}' not recognized")
    
    @DiscordGame.command(user=["new_game"], help="print the rule options (for change_rule)")
    def all_options(self, *, DiscordChannelContext):
        
        message = []
                
        #add enable rules
        message.append("Enable/Disable-able Rules:")
        for option, info in self._all_enable_rules.items():
            message.append(f"\nrule : '{option}' | options: 'enable' 'disable' | description: {info['description']}")
            
        return GameClasses.CommandResultMessage(destination = DiscordChannelContext, text = "\n".join(message))         
    
    @DiscordGame.command(player=["new_game"], help="change a game option (ex. change_option button_prompts enable)")
    def change_option(self, option, value):
        
        value = value.lower()
        
        if option in self._all_enable_rules:
        
            if value == "enable":
            
                option_boolean = True
                message = self._all_enable_rules[option]["enable_message"]
                
            elif value == "disable":
            
                option_boolean = False
                message = self._all_enable_rules[option]["disable_message"]
                
            else:
            
                raise GameExceptions.DiscordGameIllegalMove(f"modifiyer not recognized, please select 'enable' or 'disable' to change option: {option}")
                
            if option == "emojis":
                self.enable_emojis = option_boolean
            elif option == "button_prompts":
                self.enable_buttons = option_boolean
            elif option == "interrupt_prompts":
                self.enable_interrupts = option_boolean
            else:
                raise GameExceptions.DiscordGameError(f"Option dictionary misconfigured for option: {option}")
                
            return message
                
        else:
        
            raise GameExceptions.DiscordGameIllegalMove(f"Rule not recognized: {rule}")
    
    @DiscordGame.command(player = _all_states, help = "print out all secert information", debug = True)
    def cheat(self):
    
        message = [f"Deck: {[str(card) for card in self.deck.deck]}"]
        
        for player in self.get_players_in_registry():
            message.append("\n")
            message.append(player.name)
            message.append(f"{[card.name for card in player.cards]}")
            message.append(str(player.money))
            
        return "\n".join(message)