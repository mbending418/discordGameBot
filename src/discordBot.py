import os
import json
import random
from multiprocessing import Process

from discord.ext import commands
import discord

from gameRunner import GameRunner
from games.avalon.game import Avalon
from games.rockpaperscissors.game import RockPaperScissors
from games.coup.game import Coup

SETTINGS_FILE = os.path.join("..", "resources", "settings.json")
ADMIN_FILE = os.path.join("..","resources","admin.json")
SUBS_FILE = os.path.join("..","resources","subscribers.json")
COMMAND_PREFIX = "gamebot: "
GAMES={
    "Avalon" : Avalon,
    "RockPaperScissors" : RockPaperScissors,
    "Coup" : Coup
}

with open(SETTINGS_FILE, "r") as token_file:
    settings = json.load(token_file)
    
    TOKEN=settings["TOKEN"]
    
    LOGGING = settings.get("LOGGING", {})

bot = commands.Bot(command_prefix=COMMAND_PREFIX)
running_games = {}

def validate_prefix(main_prefix, new_prefix):
    
    return not (main_prefix.startswith(new_prefix) or new_prefix.startswith(main_prefix))

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='roll', help="Simulates rolling dice. To roll 4 d20 use: roll 5 20")
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    
    title = "Dice Roller:"
    
    if number_of_dice > 20:
        description = "That's too many dice. Please choose a number less than 21"
    else:
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        description = ', '.join(dice)
        
    embedding = discord.Embed(title=title, description=description, color = discord.Color.gold())
    await ctx.send(embed=embedding)

async def check_games(ctx):
    
    title = "Games Available:"
    description = "\n\n".join(list(GAMES.keys()))
    
    embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())
    
    await ctx.send(embed=embedding)

async def check_running(ctx):
    
    title = "Running Games:"
    desc_lines = []
    keys_to_remove = []
    for game_id, info in running_games.items():
        
        if info["thread"].is_alive():
        
            desc_lines.append(f"Game: {info['game_name']} | Command_Prefix: {info['command_prefix']} | Server: {info['server']} | Channel: {info['channel']}")
            
        else:
            
            keys_to_remove.append(game_id)
            
    for game_id in keys_to_remove:
        running_games.pop(game_id)            

    title = "Running Games:"
    description = "\n\n".join(desc_lines)
    embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())
    
    await ctx.send(embed=embedding)

@bot.command(name="check", help="Syntax: 'check [games]' or 'check [running]'.")
async def check(ctx, option):
    
    option = option.lower()
    
    if option == "games":
        await check_games(ctx)
        
    elif option == "running":
        await check_running(ctx)
        
    else:
        await ctx.send(f"Check Error: Unknown option {option}")

@bot.command(name="game", pass_context = True, help="Syntax: game [game] [command_prefix]. Starts a game")
async def start_game(ctx, game, game_command_prefix, use_images : bool = True, debug : bool = False):
    if game in GAMES:
        
        if validate_prefix(COMMAND_PREFIX, game_command_prefix):
            
            if ctx.guild is None or ctx.channel is None or not isinstance(ctx.channel, discord.channel.TextChannel):
                
                await ctx.send("You can only start a Game from a Discord Text Channel on a Discord Server!")
                
            else:
            
                guild = ctx.guild
                channel = ctx.channel
            
                runner = Process(target = GameRunner, args = (GAMES[game], TOKEN, str(guild), str(channel), game_command_prefix, LOGGING, use_images, debug))
                runner.start()
            
                game_id = f"{game}_{game_command_prefix}"
                running_games[game_id] = {"thread" : runner, "game_name" : game, "command_prefix" : game_command_prefix, "server" : str(guild), "channel" : str(channel)}
            
                await channel.send(f"{game} game started in '{guild}' : '{channel}' using prefix: {game_command_prefix}")
                
                title = f"Game of {game} Started!"
                description = f"{ctx.author} started a game of {game} on the following server/channel: {guild}/{channel}"
                await send_alerts(ctx, "games", title, description)
            
        else:
        
            await ctx.send(f"Cannot start {game}. Invalid Command Prefix: {game_command_prefix}")
            
    else:
    
        await ctx.send(f"Cannot start {game}. Game Not Found")        

async def prune_game_map(ctx):
    keys_to_remove = []

    for game_id, info in running_games.items():
        if not info["thread"].is_alive():
            keys_to_remove.append(game_id)
            
    for game_id in keys_to_remove:
        running_games.pop(game_id)
        
async def kill_game(ctx, game_id, prune=True):
    
    await ctx.send(f"killing game: {game_id}")
    running_games[game_id]["thread"].terminate()
    
    if prune:
        await prune_game_map(ctx)
    
async def kill_bot(ctx):
    await prune_game_map(ctx)
        
    if len(running_games) > 0:
        await ctx.send(f"'Admin Kill Bot' failed. Games still running. Kill the following games or use 'Admin Kill Bot Force':")
        for game_id, info in running_games.items():
            await ctx.send(f"Game with ID '{game_id}' on server/channel: {info['server']}/{info['channel']}")

    else:
        await ctx.send("Killing bot")
        await bot.logout()

async def force_kill_bot(ctx):
    await prune_game_map(ctx)

    for game_id in running_games:
        await kill_game(ctx, game_id, prune=False)
    
    await ctx.send("Killing bot")
    await bot.logout()

def has_permission(user, level=None):

    with open(ADMIN_FILE, 'r') as admin_file:
        admin_dict = json.load(admin_file)
    
    master_users = [user for user, permissions in admin_dict.items() if "master" in permissions]
 
    if (level == "master" or level is None) and (len(master_users) == 0): #give automatic master permissions if there are no masters
        return True
 
    if user not in admin_dict: #if the user isn't registered as an Admin return false
        return False
    
    if level is None: #if it's just asking if they're any sort of admin return True
        return True
        
    if user in master_users: #if the user is a master user return True
        return True
        
    return level in admin_dict[user]

async def add_admin(ctx, user, level="master"):

    with open(ADMIN_FILE, 'r') as admin_file:
        admin_dict = json.load(admin_file)
        
    permissions = admin_dict.get(user, [])
    if len(permissions) == 0:
        await ctx.send(f"Admin Add: Creating Admin Profile for '{user}'")
    if level in permissions:
        await ctx.send(f"Admin Add: {user} already has Permission: {level}")
    else:
        permissions.append(level)
        admin_dict[user] = permissions
        await ctx.send(f"Admin Add: Added {user} Permission: {level}")
    
    with open(ADMIN_FILE, 'w') as admin_file:
        json.dump(admin_dict, admin_file, indent=4)
        
async def remove_admin(ctx, user, level=None):
    with open(ADMIN_FILE, 'r') as admin_file:
        admin_dict = json.load(admin_file)
    
    if user not in admin_dict:
        await ctx.send(f"Admin Remove: {user} has no Admin Profile.")
    
    if level is None:
        if user in admin_dict:
            admin_dict.pop(user)
            await ctx.send(f"Admin Remove: Removed all of {user}'s Permissions")
    else:
        if level in admin_dict[user]:
            permissions = admin_dict[user]
            permissions.remove(level)
            admin_dict[user] = permissions   
            
        if len(admin_dict[user]) == 0:
            admin_dict.pop(user)
            await ctx.send(f"Admin Remove: Removed {user}'s only Admin Permission")
            
        else:
            await ctx.send(f"Admin Remove: Removed {user}'s Permission: {level}")
    
    with open(ADMIN_FILE, 'w') as admin_file:
        json.dump(admin_dict, admin_file, indent=4)
 
async def display_permissions(ctx, server = None):

    with open(ADMIN_FILE, 'r') as admin_file:
        admin_dict = json.load(admin_file)
        
    display_dict = {}
    for user, permissions in admin_dict.items():
        if (server is None) or (server in permissions):
            display_dict[user] = permissions
            
    title = "Bot Permissions:"
    description = "\n\n".join([f"{user} : {permissions}" for user,permissions in display_dict.items()])
    embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())
    
    await ctx.send(embed=embedding)
 
async def display_subscribers(ctx):

    with open (SUBS_FILE, 'r') as subs_file:
        subs_dict = json.load(subs_file)
        
    display_dict = {}
    for user, option in subs_dict.items():
        
        discord_user = await ctx.guild.fetch_member(user)
        
        if discord_user is not None:
            display_dict[str(discord_user)] = option
        
    title = "Bot Subscribers:"
    description = "\n\n".join([f"{user} : {option}" for user,option in display_dict.items()])
    embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())
    
    await ctx.send(embed=embedding)
 
@bot.command(name="Admin", help="Run Administrator Commands (Use Admin with no args to get options)")
async def admin_commands(ctx, *args):
        
    user = str(ctx.author)
       
    #prune the games real quick
    await prune_game_map(ctx)
    
    if not has_permission(user):
        await ctx.send(f"Admin Permission Denied: {user} is not an Admin for the GameBot")
        return
    
    kwargs = {f"arg_{i}" : arg for i, arg in enumerate(args)}    
    command = kwargs.get("arg_0", None)
    
    if command is None:
        title = "Administrator Commands:"
        description = "Admin Kill Game [Game_ID] : kills game with Game ID = [Game_ID]\n\n"
        if has_permission(user, "master"):
            description += "Admin Kill Bot : kills the Bot (fails if any games are running)\n\n"
            description += "Admin Kill Bot Force : kills the Bot, closing all games first\n\n"
            description += "Admin Add <user> master : make <user> a Bot Admin for entire Bot\n\n"
            description += "Admin Remove <user> : Remove all of <user>'s Bot Admin Permissions\n\n"
            description += "Admin Remove master : Remove <user>'s Entire Bot Admin Permission\n\n"
            description += "Admin Permissions : Check to see all Bot Admin Permissions\n\n"
            description += "Admin Subscribers : Check all the subscribers to the bot\n\n"
        description += "Admin Add <user> <server> : Give <user> Bot Admin Permissions for the server <server>\n\n"
        description += "Admin Remove <user> <server> : Remove <user>'s Bot Admin Permissions for the server <server>\n\n"
        description += "Admin Permissions <server> : Display all users with Bot Admin Permissions on server <server>\n\n"
        embedding = discord.Embed(title=title, description = description, color=discord.Color.gold())
        await ctx.send(embed=embedding)
        return
    
    elif command == "Kill":
        
        option  = kwargs.get("arg_1", None)
        
        if option is None:
            await ctx.send("Admin Error: Admin Command 'Admin Kill' requires additional arg ('Game' or 'Bot')")
            
        elif option == "Game":
            target = kwargs.get("arg_2", None)
            
            if target is None:
                await ctx.send("Admin Error: Admin Command 'Admin Kill Game' requires a target of which game to kill")
            
            elif target not in running_games:
                await ctx.send(f"Admin Error: Cannot kill game {target}. Game not found in running games")                
            
            else:
                server = running_games[target]["server"]
                if has_permission(user, server):
                    await ctx.send(f"Admin Command: Killing game {target}")
                    await kill_game(ctx, target)
                else:
                    await ctx.send(f"Admin Permission Denied: {user} doesn't have Permission to kill games on server: {server}")
            
        elif option == "Bot":
        
            if kwargs.get("arg_2", None) == "Force":
                await ctx.send(f"Admin Command: Force Killing Bot")
                await force_kill_bot(ctx)
                
            else:
                if has_permission(user, "master"):
                    await ctx.send(f"Admin Command: Killing Bot")
                    await kill_bot(ctx)
                    
                else:
                    await ctx.send(f"Admin Permission Denied: {user} doesn't have Permission to kill the Game Bot")
                    
        
        else:
            await ctx.send(f"Admin Error: Unknown arguement for Command 'Admin Kill': {option}")
    
    elif command == "Add":
        
        new_user = kwargs.get("arg_1", None)
        level = kwargs.get("arg_2", "master")
        
        if new_user is None:
            await ctx.send("Admin Error: Admin Command 'Admin Kill' requires additional arg")
            
        elif not has_permission(user, level):
            if level == "master":
                await ctx.send(f"Admin Permission Denied: {user} doesn't have Permission to Add/Remove All Bot Permissions")
            else:
                await ctx.send(f"Admin Permission Denied: {user} doesn't have Permission to Add/Remove Permission on server: {level}")
        else:
            await add_admin(ctx, new_user, level)
            
    elif command == "Remove":
        
        new_user = kwargs.get("arg_1", None)
        level = kwargs.get("arg_2", None)
        
        if new_user is None:
            await ctx.send("Admin Error: Admin Command 'Admin Kill' requires additional arg")
                        
        elif not has_permission(user, level):
            if level == "master" or level == None:
                await ctx.send(f"Admin Permission Denied: {user} doesn't have Permission to Add/Remove All Bot Permissions")
            else:
                await ctx.send(f"Admin Permission Denied: {user} doesn't have Permission to Add/Remove Permission on server: {level}")
        else:
            await remove_admin(ctx, new_user, level)
    
    elif command == "Permissions":
        server = kwargs.get("arg_1", None)
        
        if server is None:
            if not has_permission(user, "master"):
                await ctx.send(f"Admin Permission Denied: {user} doesn't have Bot Level Permissions")
            else:
                await display_permissions(ctx)
        
        elif not has_permission(user, server):
            await ctx.send(f"Admin Permission Denied: {user} doesn't have Permissions on server {server}")
        
        else:
            await display_permissions(ctx, server)
    
    elif command == "Subscribers":
        
        if has_permission(user):
            
            await display_subscribers(ctx)
            
        else:
            
            await ctx.send(f"Admin Perimssion Denied: {user} doesn't have Bot Level Permissions")
    
    else:
        await ctx.send(f"Admin Error: Admin command not found: {command}")

async def send_alerts(ctx, option, title, description):

    with open(SUBS_FILE, 'r') as subs_file:
        subs_dict = json.load(subs_file)

    embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())

    for user, sub in subs_dict.items():
                
        destination = await ctx.guild.fetch_member(user)
        
        if (destination is not None) and (sub == option or sub == "all"):
            
            await destination.send(embed=embedding)

@bot.command(name="subscribe", help="Subscribe to the bot (options: game, announcements, all)")
async def subscribe(ctx, option):
    
    option = option.lower()
    
    allowed_options = {
       "games" : "Whenever a game is started on a Server you are on,  the Game Bot will DM you", 
       "announcements" : "Whenever an announcement by the Bot is made on a Server you are on, the Game Bt will DM you", 
       "all" : "Whenever a game is started or an announcement by the Bot is made on a Server you are on, the Game Bt will DM you"
    }
    
    with open(SUBS_FILE, 'r') as subs_file:
        subs_dict = json.load(subs_file)
   
    user = str(ctx.author)
    user_id = str(ctx.author.id)
    
    if option in allowed_options:
        subs_dict[user_id] = option
        await ctx.send(f"{user} has subscribed to the Game Bot with the option: {option}")
        title = "Game Bot Subscribed"
        description = allowed_options[option]
        description += "\n\nTo Unsubscribe to the Bot use the Command [Unsubscribe] at any time"
        embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())
        await ctx.author.send(embed=embedding)        
    else:
        await ctx.send(f"Invalid Option: {user} cannot subscribe to {option}")
   
    with open(SUBS_FILE, 'w') as subs_file:
        json.dump(subs_dict, subs_file, indent=4)       
        
@bot.command(name="unsubscribe", help="Unsubscribe to the bot")
async def unsubscribe(ctx):
        
    with open(SUBS_FILE, 'r') as subs_file:
        subs_dict = json.load(subs_file)
   
    user = str(ctx.author)
    user_id = str(ctx.author.id)
        
    if user_id in subs_dict:
        subs_dict.pop(user_id)
        await ctx.send(f"{user} is unsubscribed from the bot")
        title = "Game Bot Unsubscribed"
        description = "You have been Unsubscribed to the Game Bot and will no longer receive notifications"
        description += "\n\nYou can Resubscribed at anytime with the command Subscribe"
        embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())
        await ctx.author.send(embed=embedding)    
    else:
        await ctx.send(f"Cannot Unsubscribe {user}. They are not subscribed to the Game Bot")
   
    with open(SUBS_FILE, 'w') as subs_file:
        json.dump(subs_dict, subs_file, indent=4) 

@bot.command(name="announcement", help="make an announcement in the current channel")
async def announcement(ctx, title, description):
    
    embedding = discord.Embed(title=title, description=description, color=discord.Color.gold())
    
    await ctx.send(embed=embedding)
    
    await send_alerts(ctx, "announcements", title, description)

def main():

    if not os.path.isfile(ADMIN_FILE):
        with open(ADMIN_FILE, 'w') as admin_file:
            json.dump({}, admin_file)
            
    if not os.path.isfile(SUBS_FILE):
        with open(SUBS_FILE, 'w') as subs_file:
            json.dump({}, subs_file)

    bot.run(TOKEN)

if __name__ == "__main__":
   main()
