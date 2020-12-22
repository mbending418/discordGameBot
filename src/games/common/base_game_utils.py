import os
import inspect
import discord

class DiscordGameError(Exception):
    def __init__(self, message):

        super().__init__(message)

class DiscordGameIllegalMove(Exception):
    def __init__(self, message):
    
        super().__init__(message)

class CommandInfo:
    """
    An object for storing information about a Command for a DiscordGame
    
    contructors:
    
    __init__(self, name : str, valid_states : Dict[str -> List[str]], help_message : str, debug : bool)
    
        name (str) : The string used by a user/player to invoke this command
        
        valid_states (Dict[str -> List[str]]) : A Dict that maps game roles (str) to a List of what game states (str)
                                                that the role let's you use this command from
                                               
        help_message (str) : The help message to display to describe this command
        
        debug (bool) : Set this flag to True if this command is only available from debug mode
        
    instance_methods:
    
    .get_permitted_roles(self, game_state : str) -> List[str])
    
        returns what roles are permitted to use this command at a particular game state
    
        game_state (str) : The game state
        
        return (List[str]) : A List of which "roles" are permitted to use this command at 'game_state'
        
    .has_permission(self, player : Player, game_state : str) -> bool
        
        returns whether a particular player is allowed to use this command at 'game_state'
        
        player (Player): The player you want to check permissions for
        
        game_state (str) : The game state you want to check permissions for
        
        return (bool) : Returns True iff the player has permission to use this command at game_state
    
    instance_fields:
    
    name (str) : The string used by a user/player to invoke this command
        
    _valid_states (Dict[str -> List[str]]) : A Dict that maps game roles (str) to a List of what game states (str)
                                                that the role let's you use this command from
                                               
    help_message (str) : The help message to display to describe this command
        
    debug (bool) : Set this flag to True if this command is only available from debug mode
    """
    
    def __init__(self, name, valid_states, help_message = None, debug = False):
        self.name = name
        self._valid_states = valid_states
        self.help_message = help_message
        self.debug = debug
        
    def get_permitted_roles(self, game_state):
        """
        returns what roles are permitted to use this command at a particular game state
    
        :param game_state (str) : The game state
        
        :return (List[str]): A List of which "roles" are permitted to use this command at 'game_state'
        """
        permitted_roles = []
        for role, permissions in self._valid_states.items():
            if game_state in permissions:
                permitted_roles.append(role)
    
        return permitted_roles
        
    def has_permission(self, player, game_state):
        """
        returns whether a particular player is allowed to use this command at 'game_state'
        
        :param player (Player): The player you want to check permissions for
        :param game_state (str) : The game state you want to check permissions for
        
        :returns (bool): returns True iff the player has permission to use this command at game_state
        """
    
        permitted_roles = self.get_permitted_roles(game_state)
        
        return any([player.has_role(role) for role in permitted_roles]) or "user" in permitted_roles

class CommandResultMessage:
    """
    An object used for sending results back for a DiscordGame Command. 
    
    The GameRunner knows to take any "CommandResultMessage", "str" or List containing CommandResultMessage and/or str
    returned by a DiscordGame Command and use it to send a message
    
    (Context refers to a Discord.Context object. It realy just needs a .send method which can send stuff to it on discord. be it an author, channel, etc)
    
    Contructors:
       
    __init__(self, destination : Context, text : str, image : str, send_both : bool)
    
        destination (Context) : What Discord.Context object this message should be sent to. If None the GameRunner will use the default location. Usually the Channel the bot was made in.
        
        text (str): The text of the message
        
        image (str): The path to the image to send
        
        send_both (bool) : Set to True if both the text AND the image should be sent
    
    How to Use:
    
    If you set the 'destination' field, the GameRunner will send this message to that whatever Discord.Context object.
    Otherwise it will just send it to the default location, usualy the Channel that started the bot
    
    Setting the 'text' field will set the 'content' field of the message sent by the GameRunner
    
    Setting the 'image' field will set the 'file' field of the message sent by the GameRunner
    
    By default the GameRunner will:
        Send the 'image' file if there is one and use_images is True
        Send the 'text' content if there is no image sent or if 'send_both' is set to True
    """
    
    def __init__(self, destination = None, text = "", image = None, send_both = False):
        self.destination = destination
        self.text = text
        self.image = image
        self.send_both = send_both
        
class Player:
    """
    An object for storing information about a Player for a DiscordGame
    
    contructors:
    
    __init__(self,  DicordAuthorContext : Context, name : str)
    
        DiscordAuthorContext (Context): The Discord.Context object representing the discord username that controls this Player.
    
        name (str): The name of the player as far as the DiscordGame is concerned (if None, the field will be set to str(DiscordAuthorContext))
    
    instance methods:
    
    .give_role(self, *roles : List[str])
    
        gives roles to a particular player that the DiscordGame uses to determine permissions
        
        *roles (List[str]) : The roles you want to give this Player in the game
        
    .remove_role(self, *roles : List[str])
    
        removes roles from a particular player that the DiscordGame uses to determine permission. If the player doesn't have the role it does nothing.
        
        *roles (List[str]) : The roles you want to remove from this Player in the game
        
    .has_role(self, role : str)
    
        returns True iff the player has the specified role
        
        role (str) : The role to check to see if the Player has
        
        return (bool) : True if Player has role, False otherwise
            
    .create_message_for(self, text = "", image = None, send_both = False)
        
        returns a CommandResultMessage to this player with text, image, and send_both fields set as input to this function
        
        text (str): The text of the message
        
        image (str) : The file path to the image file
        
        send_both (bool) : Whether to send both the text and image if both are present AND send_images is True
        
        return (CommandResultMessage) : Returns the CommandResultMessage that tells the GameRunner how to 
        
    .add_to_cache(self, key, value):
        
    .remove_from_cache(self, key):
    
    .get_from_cache(self, key):
    
    instance_fields:
    
    _discord_channel
    discord_name
    name
    roles
    _player_cache
    """
    
    def __init__(self,  DicordAuthorContext, name=None):
        
        self._discord_channel = DicordAuthorContext
        self.discord_name = str(DicordAuthorContext)
        
        if name is None:
            name = self.discord_name
        
        self.name = name
        self.roles = set()
        
        self._player_cache = {}
        
    def give_role(self, *roles):
        """
        gives roles to a particular player that the DiscordGame uses to determine permissions
        
        :param *roles (List[str]) : The roles you want to give this Player in the game
        """
    
        for role in roles:
            self.roles.add(role)
        
    def remove_role(self, *roles):
        """
        removes roles from a particular player that the DiscordGame uses to determine permission. If the player doesn't have the role it does nothing.
        
        :param *roles (List[str]) : The roles you want to remove from this Player in the game
        """
        
        for role in roles:
            if role in self.roles:
                self.roles.remove(role)
        
    def has_role(self, role):
        """
        returns True iff the player has the specified role
        
        :param role (str) : The role to check to see if the Player has
        
        :return (bool): True if Player has role, False otherwise
        """
        return role in self.roles
        
    def create_message_for(self, text = "", image = None, send_both = False):
        """
        returns a CommandResultMessage to this player with text, image, and send_both fields set as input to this function
        
        :param text (str): The text of the message
        
        :param image (str) : The file path to the image file
        
        :param send_both (bool) : Whether to send both the text and image if both are present AND send_images is True
        
        :return (CommandResultMessage): Returns the CommandResultMessage that tells the GameRunner how to
        """
        
        return CommandResultMessage(destination = self._discord_channel, text = text, image = image, send_both = send_both)
        
    def add_to_cache(self, key, value):
        
        self._player_cache[key] = value
      
    def remove_from_cache(self, key):
    
        self._player_cache.pop(key, None)
        
    def get_from_cache(self, key):
    
        return self._player_cache.get(key, None)

def getBaseGameClass():    
    """
    returns a DiscordGame base class be used to make Discord Games
    
    Due to a quirk in how the @command works, each DiscordGame needs to inherit from a different DiscordGame Class. Hence this factory was created.
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
            
                new_command = CommandInfo(func.__name__, self._valid_states, self._help, self._debug)
            
                self._command_registry.append(new_command)
            
                valid_states = self._valid_states
            
                def wrapper(game_self, *args, **kwargs):
                    
                    #check to be sure the game has a '_state' field
                    if "_state" not in dir(game_self):
                        raise DiscordGameError(f"Object has no '_state' field")
                                                                
                    #check which players are controlled by the discord user who is trying to use this command
                    players = [player for player in game_self.get_players_in_registry() if player.discord_name == str(kwargs["DiscordAuthorContext"])]
                    
                    #does this player have permission to use this command in this game state
                    has_permission = any([new_command.has_permission(player, game_self._state) for player in players])
                    
                    #find the list of roles that can use this command in this came state
                    permitted_roles = new_command.get_permitted_roles(game_self._state)
                                        
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
                        raise DiscordGameIllegalMove(f"Cannot call '{func.__name__}' from state: {game_self._state}. Requires any of the following roles: {permitted_roles}")
                    
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
                    
            raise DiscordGameIllegalMove(f"Cannot find player in registry with name '{player_name}'")
        
        def get_players_in_registry(self):
            return list(self._player_registry)
        
        def register_player(self, DiscordAuthorContext, player_name = None, PlayerClass=Player):
            player = PlayerClass(DiscordAuthorContext, player_name)
            
            if self.check_player_registry(player_name):
                raise DiscordGameIllegalMove(f"Cannot register player with name '{player_name}'. Name already registered")
            
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
                roles = command.get_permitted_roles(self._state)
                if len(roles) > 0 and (self._debug or not command.debug):
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
                if command.has_permission(player, self._state) and (self._debug or not command.debug):
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

def generate_temp_dir(temp_base):
    """
    generate a new temp directory in the base temp directory folder for this game
    
    This function will try to make a temp directory at os.path.join(temp_base, 'temp_0'),
    if that temp directory already exists it will try os.path.join(temp_base, 'temp_1')
    and so on until it finds an unused temp directory name
    
    It will then return the temp directory name after it makes the temp directory
    """

    index = 0
    while os.path.isdir(os.path.join(temp_base, f"temp_{index}")):
        index+=1
        
    temp_dir = os.path.join(temp_base, f"temp_{index}")
    os.mkdir(temp_dir)
    
    return temp_dir   