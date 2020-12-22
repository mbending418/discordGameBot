import os
import inspect
import discord

from . import GameClasses
from . import GameExceptions

def getBaseGameClass():    
    """
    returns a DiscordGame base class be used to make Discord Games
    
    Due to a quirk in how the @command decorator works, each DiscordGame needs to inherit from a different DiscordGame Class. Hence this factory was created.
    """
   
    class DiscordGame:
        """
        DiscordGame should be inhereted by any Discord Game to automatically get the following features:
        
        
        """
    
        _player_registry = []
    
        class command:
            _command_registry = []
        
            def __init__(self, **kwargs):
                self._help = kwargs.pop("help", None)
                self._debug = kwargs.pop("debug", False)
                self._valid_states = kwargs
            
            def __call__(self, func):
            
                new_command = GameClasses.CommandInfo(func.__name__, self._valid_states, self._help, self._debug)
            
                self._command_registry.append(new_command)
            
                valid_states = self._valid_states
            
                def wrapper(game_self, *args, **kwargs):
                    
                    #check to be sure the game has a 'state' field
                    if "state" not in dir(game_self):
                        raise GameExceptions.DiscordGameError(f"Object has no 'state' field")
                                                                
                    #check which players are controlled by the discord user who is trying to use this command
                    players = [player for player in game_self.get_players_in_registry() if player.discord_name == str(kwargs["DiscordAuthorContext"])]
                    
                    #does this player have permission to use this command in this game state
                    has_permission = any([new_command.has_permission(player, game_self.state) for player in players])
                    
                    #find the list of roles that can use this command in this came state
                    permitted_roles = new_command.get_permitted_roles(game_self.state)
                                        
                    #remove DiscordAuthorContext from kwargs if it's not used by the command
                    if not does_function_accept_special_kwarg(func, 'DiscordAuthorContext'):
                        kwargs.pop("DiscordAuthorContext")
                       
                    #remove DiscordChannelContext from kwargs if it's not used by the command
                    if not does_function_accept_special_kwarg(func, 'DiscordChannelContext'):
                        kwargs.pop("DiscordChannelContext")
                                       
                    #if has_permission or "user" in permitted_roles:
                    if has_permission or ("user" in permitted_roles):
                        return func(game_self, *args, **kwargs)
                
                    #user is not permitted to call this right now
                    else:
                        raise GameExceptions.DiscordGameIllegalMove(f"Cannot call '{func.__name__}' from state: {game_self.state}. Requires any of the following roles: {permitted_roles}")
                    
                wrapper.__name__ = func.__name__
                return wrapper 
        
        def get_commands(self):
            return list(self.command._command_registry)  
        
        def check_player_registry(self, player_name):
            for cached_player in self.get_players_in_registry():
                if cached_player.name == player_name:
                    return True
                    
            return False
        
        def get_player_from_name(self, player_name):
            for cached_player in self._player_registry:
                if cached_player.name == player_name:
                    return cached_player
                    
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot find player in registry with name '{player_name}'")
        
        def get_players_in_registry(self):
            return list(self._player_registry)
        
        def register_player(self, DiscordAuthorContext, player_name = None, PlayerClass=GameClasses.Player):
            player = PlayerClass(DiscordAuthorContext, player_name)
            
            if self.check_player_registry(player_name):
                raise GameExceptions.DiscordGameIllegalMove(f"Cannot register player with name '{player_name}'. Name already registered")
            
            self._player_registry.append(player)
            
            return player
        
        def get_users_players(self, DiscordAuthorContext):
            all_players = self.get_players_in_registry()
            
            players = [player for player in all_players if player.discord_name == str(DiscordAuthorContext)]
            
            return players
            
        def remove_player(self, player_name):
            
            to_remove = []
            for cached_player in self._player_registry:
                if cached_player.name == player_name:
                    to_remove.append(cached_player)
            
            for player in to_remove:
                self._player_registry.remove(player)
        
        def check_current_commands(self):
            """
            return a dict of mapping:
                'commands allowed in current state' -> 'list of roles that can use that command'
            """
            
            commands = self.get_commands()
            
            current_commands = {}
            for command in commands:
                roles = command.get_permitted_roles(self.state)
                if len(roles) > 0 and (self.debug or not command.debug):
                    current_commands[command] = roles
                    
            return current_commands
        
        def check_player_current_commands(self, player_name):
            """
            return a list of command names that 'player_name' has permissions for
            """
            player = self.get_player_from_name(player_name)
                
            commands = self.get_commands()
            
            permitted_commands = []
            for command in commands:
                if command.has_permission(player, self.state) and (self.debug or not command.debug):
                    permitted_commands.append(command)
                    
            return permitted_commands  

        def kill_game(self):
            """
            Override this function to have the game clean up stuff when killed
            """
            pass
               

    return DiscordGame
    
def does_function_accept_special_kwarg(func, special_kwarg):
    """
    returns True is the function should be passed the 'special_kwarg' argument as a kwarg
    returns False otherwise
    
    Specifically, this function looks to see if 'special_kwarg' is in the args or keyword only args or if the function **kwargs 
    
    :param func (function): The function to check
    :return (bool): whether or not it should be passed the 'special_kwarg'
    """
    
    argspec = inspect.getfullargspec(func)
    
    if special_kwarg in argspec.args:
        return True
    
    if special_kwarg in argspec.kwonlyargs:
        return True
        
    if argspec.varkw is not None:
        return True
        
    return False