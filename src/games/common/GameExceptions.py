class DiscordGameError(Exception):
    """
    This execption should be used to log a Game Error (ie the game is in a bad state)
    
    When caught by the GameRunner, this exception will send an appropriate messge back
    to the game channel and the appropriate log channel (if specified in settings)
    """
    
    def __init__(self, message):

        super().__init__(message)

class DiscordGameIllegalMove(Exception):
    """
    This execption should be used to log a user trying to do an illegal command/game move
    
    When caught by the GameRunner, this exception will send an appropriate messge back
    to the game channel and the appropriate log channel (if specified in settings)
    """


    def __init__(self, message):
    
        super().__init__(message)