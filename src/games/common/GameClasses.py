from emoji import EMOJI_ALIAS_UNICODE as EMOJIS

from . import GameExceptions

END_EMOJI = EMOJIS[":x:"]

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
        
    valid_states (Dict[str -> List[str]]) : A Dict that maps game roles (str) to a List of what game states (str)
                                                that the role let's you use this command from
                                               
    help_message (str) : The help message to display to describe this command
    
    requires_lock (bool): Set this flag to True if this command requires the game lock. Only one command requiring the game lock can be run at a time
        
    debug (bool) : Set this flag to True if this command is only available from debug mode
    """
    
    def __init__(self, name, valid_states, help_message = None, requires_lock = False, debug = False):
        self.name = name
        self.valid_states = valid_states
        self.help_message = help_message
        self.requires_lock = requires_lock
        self.debug = debug
                
    def get_permitted_roles(self, game_state):
        """
        returns what roles are permitted to use this command at a particular game state
    
        :param game_state (str) : The game state
        
        :return (List[str]): A List of which "roles" are permitted to use this command at 'game_state'
        """
        permitted_roles = []
        for role, permissions in self.valid_states.items():
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
        
class CommandResultInterrupt:

    """See if any player wants to respond to the current game action"""
    
    def __init__(self, title, players, func_name, emojis, end_emoji = None, max_responses = None, result_message = "", timeout = 30.0):
      
        #default end_emoji
        if end_emoji is None:
            end_emoji = END_EMOJI
        
        self.players = players
        
        self.func_name = func_name        
        
        self.title = title
        self.result_message = result_message
        self.emojis = emojis
        self.end_emoji = end_emoji
        self.max_responses = max_responses
        self.timeout = timeout

class CommandResultPrompt:

    """Prompt a Player to make a Selection or Selections"""

    def __init__(self, player, title, func_name, emojis = None, dm = False, count = 1, key = None, description = None, result_message = None, timeout = 30.0):
        
        if not isinstance(count, int):
            raise GameExceptions.DiscordGameError(f"count for CommandResultPrompt must be of type 'int': type(count) = {type(count)}")
        if count < 1:
            raise GameExceptions.DiscordGameError(f"count for CommandResultPrompt must be at least 1: count = {count}")
        
        #key defaults to the player name
        if key is None:
            key = player.name
            
        #default message description
        if description is None:
            description = f"Please Select {count} of the following: {emojis}"
            
        if result_message is None:
            result_message = f"You Chose: "
    
        if count > len(emojis):
            raise GameExceptions.DiscordGameError(f"count must be <= the number of emoji options: emojis = {emojis} | count = {count}")
                
        if len(set(emojis)) < len(emojis):
            raise GameExceptions.DiscordGameError(f"emoji list must contain no duplicates")
    
        self.player = player
        self.key = key
        self.func_name = func_name        
        
        if dm:
            self.channel = player.discord_channel
        else:
            self.channel = None
        
        self.title = title
        self.description = description
        self.result_message = result_message
        self.emojis = emojis
        self.count = count
        self.timeout = timeout
               
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
        
        self.discord_channel = DicordAuthorContext
        self.discord_name = str(DicordAuthorContext)
        
        if name is None:
            name = self.discord_name
        
        self.name = name
        self.roles = set()
        
        self.player_cache = {}
        
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
        
        return CommandResultMessage(destination = self.discord_channel, text = text, image = image, send_both = send_both)