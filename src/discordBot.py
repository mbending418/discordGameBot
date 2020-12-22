import os
import json
import random
from multiprocessing import Process
from emoji import EMOJI_ALIAS_UNICODE as EMOJIS

from discord.ext import commands
import discord

from gameRunner import GameRunner
from games.avalon.game import Avalon
from games.rockpaperscissors.game import RockPaperScissors

TOKEN_FILE = os.path.join("..", "resources", "settings.json")
COMMAND_PREFIX = "@bot "
GAMES={
    "Avalon" : Avalon,
    "RockPaperScissors" : RockPaperScissors
}

with open(TOKEN_FILE, "r") as token_file:
    settings = json.load(token_file)
    
    TOKEN=settings["TOKEN"]
    
    LOGGING = settings["LOGGING"]
    
    IllegalMoveLog = settings.get("IllegalMoveLog", {})

bot = commands.Bot(command_prefix=COMMAND_PREFIX)
threads = {}

def validate_prefix(main_prefix, new_prefix):
    
    return not (main_prefix.startswith(new_prefix) or new_prefix.startswith(main_prefix))

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name = "test_page", help="test buttons")
async def test_page_buttons(ctx):
    client = bot
    
    page1 = discord.Embed (
        title = 'Page 1/3',
        description = 'Description',
        colour = discord.Colour.orange()
    )
    page2 = discord.Embed (
        title = 'Page 2/3',
        description = 'Description',
        colour = discord.Colour.orange()
    )
    page3 = discord.Embed (
        title = 'Page 3/3',
        description = 'Description',
        colour = discord.Colour.orange()
    )
    
    pages = [page1, page2, page3]

    message = await ctx.send(embed = page1)
    await message.add_reaction('⏮')
    await message.add_reaction('◀')
    await message.add_reaction('▶')
    await message.add_reaction('⏭')

    def check(reaction, user):
        return user == ctx.author

    i = 0
    reaction = None

    while True:
        if str(reaction) == '⏮':
            i = 0
            await message.edit(embed = pages[i])
        elif str(reaction) == '◀':
            if i > 0:
                i -= 1
                await message.edit(embed = pages[i])
        elif str(reaction) == '▶':
            if i < 2:
                i += 1
                await message.edit(embed = pages[i])
        elif str(reaction) == '⏭':
            i = 2
            await message.edit(embed = pages[i])
        
        try:
            reaction, user = await client.wait_for('reaction_add', timeout = 30.0, check = check)
            await message.remove_reaction(reaction, user)
        except:
            break

    await message.clear_reactions()

@bot.command("vote_test", help="set value for x using buttons")
async def vote_test(ctx):
   
    #approve_token = ":white_check_mark:"
    #reject_token = ":x:"
    
    #approve_token = ":track_next:"
    #reject_token = ":track_previous:"
    
    #approve_token = "⏭"
    #reject_token = "⏮"
    
    approve_token = EMOJIS[":white_check_mark:"]
    reject_token = EMOJIS[':x:']
   
    vote_box = discord.Embed(title = "Choose an Option", description = f"approve {approve_token} | reject {reject_token}")
   
    message = await ctx.send(embed = vote_box)
    await message.add_reaction(approve_token)
    await message.add_reaction(reject_token)
        
    def check(reaction, user, channel):
        return (user == ctx.author) and (channel == ctx.channel)
        
    reaction = None
    vote = None
    
    while vote is None:
        if str(reaction) == approve_token:
            vote = "approve"
            
            approve_box = discord.Embed(title = "Congratulations You Voted!", description = "You voted: approve")
            
            await message.edit(embed = approve_box)
            
            break
            
        elif str(reaction) == reject_token:
        
            vote = "reject"
            
            reject_box = discord.Embed(title = "Congratulations You Voted!", description = "You voted: reject")
            
            await message.edit(embed = reject_box)
            
            break
            
        else:
            pass
            
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout = 30.0, check = check)
            #await message.remove_reaction(reaction, user)
        except:
            break
            
    await ctx.send(f"You voted: {vote}")

x=[0]
@bot.command("set_x", help="set value for x ")
async def set_x(ctx):
   x[0] = x_value 
   await ctx.send(f"x set to: {x[0]}")
    
@bot.command("get_x", help="get value of x")
async def get_x(ctx):
    await ctx.send(f"x = {x[0]}")

@bot.command(name='roll_dice', help="Simulates rolling dice")
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    
    if number_of_dice > 20:
        await ctx.send("Screw you Derek that's too many dice")
        return
    
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))

@bot.command(name="checkGames", help="check which games are registered")
async def check_games(ctx):
    await ctx.send("\n".join(list(GAMES.keys())))

@bot.command(name="StartGame", pass_context = True, help="Start game 'arg1' with command prefix 'arg2'")
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
            
                threads[game_command_prefix] = runner
            
                await channel.send(f"{game} game started in '{guild}' : '{channel}' using prefix: {game_command_prefix}")
            
        else:
        
            await ctx.send(f"Cannot start {game}. Invalid Command Prefix: {game_command_prefix}")
            
    else:
    
        await ctx.send(f"Cannot start {game}. Game Not Found")        
 
@bot.command(name="killBot", help="kills the bot")
async def kill_bot(ctx):

    kill = True
    keys_to_remove = []

    for key, thread in threads.items():
        if thread.is_alive():
            kill = False
            await ctx.send(f"'killBot' command failed. Remove game with command prefix '{key}' or use 'forceKillBot'")
        else:
            keys_to_remove = key
    
    for key in keys_to_remove:
        threads.pop(key)

    if kill:
        await ctx.send("Killing bot")
        await bot.logout()
    
@bot.command(name="forceKillBot", help="kills the bot (even if there's games runnning")
async def force_kill_bot(ctx):

    for key, thread in threads.items():
        if thread.is_alive():
            await ctx.send(f"game with command prefix '{key}' still active")

    await ctx.send("Killing bot")
    await bot.logout()

@bot.command(name="print", help="prints message (default = 'default_message')")
async def print_stuff(ctx, message="default_message"):
    await ctx.send(message)

def main():

    bot.run(TOKEN)

if __name__ == "__main__":
   main()