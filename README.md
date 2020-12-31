# discordGameBot
A Discord Bot that hosts playing games

# requirements

python 3.7.4 or higher

pip install discord

pip install imageio

pip install numpy

pip install emoji

# setup instructions:

In order to actually run this bot you'll need to do the following:


1.) Create an application using the Discord Developer Portal

2.) Turn that application into a bot and obtain the Token

3.) Add that bot to whatever Discord Server(s) you want to run the bot on


Detailed instructions on how to do that can be found here: https://realpython.com/how-to-make-a-discord-bot-python/

Once you've done this you need to create a JSON file at "resources/settings.json" with the following contents:

{
   "TOKEN" : [your-discord-bots-token]
}
  
where [your-discord-bots-token] should be replaced with the token for you bot from the developer portal
 
Additionally, you can also add an optional field to the JSON file to enable additional logging information. Normally, all exceptions thrown by a running game respond with an error message back to whoever send the command to the game. However, you can also enable the bot to also send more verbose error messages back to a prespecified discord server/channel. This can be useful for logging and subsequent debugging since the more verbose logs include the traceback. (I suggest if you do this that you set up a test server where only you have access to avoid polluting a discord server people are actually using with logs).

{

  "LOGGING" : {
  
       "ErrorLog" : {"Guild" : [discord-server], "Channel" : [discord-channel-for-error-log]},
       
       "IllegalMoveLog" : {"Guild" : [discord-server], "Channel" : [discord-channel-for-illegal-move-log]}
       
  }
  
}
  
[discord-server] is the name of the discord server that you want the bot to send the logging information to
  
[discord-channel-for-illegal-move-log] is the name of the channel on the above server you want all "DiscordGameIllegalMove" exceptions to be sent to
  
[discord-channel-for-error-log] is the name of the channel on the above server that you want other Exceptions to be sent to
  
In this way, the main error log doesn't get polluted with logs of players trying to do illegal moves so long as the game catches it and handles it appropriately  

# run instructions:

Set your working directory to "/src" and run "discordBot.py" using python3. You should get a message: "<name of bot> has connected to Discord!"
 
# current supported commands:
  
The following commands are currently supported by the bot (these can be checked with "@bot help"):
  
  @bot roll_dice <num_dice> <num_sides> : roll <num_dice> dice with <num_dice> sides
      ex "@bot roll_dice 5 20" will roll 5 20 sided dice and return the results
      
  @bot print <message> : have the bot print a message
      ex. "@bot print hello_world" will make the bot respond "hello_world"
  
  @bot checkGames: check to see which games are currently loaded into the bot
  
  @bot StartGame <game> <prefix> : Start the game <game> with the command prefix <prefix>
      ex. "@bot StartGame Avalon !" will start a game of avalon where all the commands have the command prefix "!"
      Additionally there are two optional boolean flags you can include.
          If you set the first one to False, all images the game sends will instead not be sent
          If you set the second on to True, the game will be run in debug mode and will enable whatever debug commands/options that were created for it
      ex. "@bot StartGame Avalon ! True True" will start a game in debug mode
 
  @bot killBot: kill the bot, fails if any games are running (it's faster to kill the bot using this command then to try and shutdown the python process manually)
  
  @bot killBotForce: kill the bot, even if there are games running
  
# current supported games:

Avalon : based off of the board game "The Resistance: Avalon"

Coup: Based of the board game "Coup"

RockPaperScissors: The childrens game (useful as a simple example game and to familiarize yourself with how everything works)
  
