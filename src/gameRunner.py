import discord
import asyncio
import traceback
from discord.ext import commands

import games.common

class GameRunner:
    def __init__(self, GameClass, token, game_guild_name, game_channel_name, command_prefix, logging_info, use_images = True, debug = False):    
        self.token = token
        self.game_guild_name = game_guild_name
        self.game_channel_name = game_channel_name
        self.command_prefix = command_prefix
        self.use_images = use_images
        
        self.illegal_move_log_channel = logging_info.get("IllegalMoveLog")
        self.error_log_channel = logging_info.get("ErrorLog")
                
        self.bot = commands.Bot(command_prefix = self.command_prefix)
    
        self.game = GameClass(debug)
        
        self.game_commands = self.game.get_commands()
        
        for command in self.game_commands:
            if debug or (not command.debug):
                self.make_command(command)
        
        self.make_kill_command()
        
        self.is_locked = False
        
        self.bot.run(self.token)
            
    def make_command(self, command):
                        
        async def process_command_result(game_channel, command_result):
            
            if command_result is None:
                pass
                
            elif isinstance(command_result, str):
                await game_channel.send(command_result)
                
            elif isinstance(command_result, games.common.GameClasses.CommandResultMessage):
                
                destination =  command_result.destination
                if destination is None:
                    destination = game_channel                
                
                kwargs = {}
                
                if (self.use_images) and (command_result.image is not None):
                    kwargs["file"] = discord.File(command_result.image)
                    
                if (not self.use_images) or (command_result.image is None) or (command_result.send_both):
                    kwargs["content"] = command_result.text
                    
                await destination.send(**kwargs)
                
            elif isinstance(command_result,(list,tuple)):
                [await process_command_result(game_channel, cr) for cr in command_result]
                
            else:
                raise games.common.GameExceptions.DiscordGameError(f"result from commmand '{command.name}' not recognized: {type(command_result)}")
        
        async def prompt_player(default_channel, prompt : games.common.GameClasses.CommandResultPrompt):
            
            vote_box = discord.Embed(title = prompt.title, description = prompt.description)
            
            channel = prompt.channel
            if channel is None:
                channel = default_channel
            
            message = await channel.send(embed= vote_box)
            for emoji in prompt.emojis:
                await message.add_reaction(emoji)
                
            def check(reaction, user):
                return (user == prompt.player.discord_channel) and (reaction.message.id == message.id)
                
               
            choices = set()
            while len(choices) < prompt.count:
                
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout = prompt.timeout, check = check)
                    if prompt.channel is None:
                        await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    timeout_box = discord.Embed(title = prompt.title, description = "Timed out! Please manually make selection with game commands")
                    await message.edit(embed = timeout_box)
                    choices = None
                    break
                    
                if reaction.emoji in prompt.emojis:
                
                    if reaction.emoji in choices:
                        choices.remove(reaction.emoji)
                    else:
                        choices.add(reaction.emoji)
                        
                    if len(choices) < prompt.count:
                        current_choices = choices
                        if current_choices == set():
                            current_choices = "None"
                        choice_box = discord.Embed(title = prompt.title, description = f"Current selection: {current_choices}")
                        await message.edit(embed = choice_box)
                        
            if (choices is not None) and (len(choices) == 1):
                desc = f"{prompt.result_message} {list(choices)[0]}"
            else:
                desc = f"{prompt.result_message} {choices}"
            recorded_box = discord.Embed(title = prompt.title, description = desc)
            await message.edit(embed = recorded_box)
            
            return (prompt.key, choices)
        
        async def prompt_interrupt(game_channel, interrupt : games.common.GameClasses.CommandResultInterrupt):
                       
            responses = {player.name : set() for player in interrupt.players}
            player_map = {player.discord_name : player.name for player in interrupt.players}
            description = "\n".join(f"{player.name}: {list(responses[player.name])}" for player in interrupt.players)
            interrupt_box = discord.Embed(title = interrupt.title, description = description)
                        
            message = await game_channel.send(embed= interrupt_box)
            for emoji in interrupt.emojis:
                await message.add_reaction(emoji)
            await message.add_reaction(interrupt.end_emoji)
                
            def check(reaction, user):
                return (user in [player.discord_channel for player in interrupt.players]) and (reaction.message.id == message.id)
                
            count = 0
            reaction = None
            while (reaction is None or reaction.emoji != interrupt.end_emoji) and (interrupt.max_responses is None or count < interrupt.max_responses):
                
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout = interrupt.timeout, check = check)
                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    timeout_box = discord.Embed(title = interrupt.title, description = "Timed out! Please manually make selection with game commands")
                    await message.edit(embed = timeout_box)
                    break
                    
                if reaction.emoji in interrupt.emojis:
                
                    player_name = player_map[str(user)]
                
                    if reaction.emoji in responses[player_name]:
                        responses[player_name].remove(reaction.emoji)
                        count-=1
                    else:
                        responses[player_name].add(reaction.emoji)
                        count+=1
                    
                    description = "\n".join(f"{player.name}: {list(responses[player.name])}" for player in interrupt.players)
                    interrupt_box = discord.Embed(title = interrupt.title, description = description)
                    await message.edit(embed = interrupt_box)   
            
            print(interrupt.result_message)
            
            description = "\n".join(f"{player.name}: {list(responses[player.name])}" for player in interrupt.players)
            description += f"\n\n{interrupt.result_message}"
            interrupt_box = discord.Embed(title = interrupt.title, description = description)
            await message.edit(embed = interrupt_box)
            
            return responses
        
        async def new_function(ctx, *args, **kwargs):
            
            #Check to see if the user is allowed to use this command right now
            try:
                #find the guild and channel the game is using
                guild = discord.utils.find(lambda guild: guild.name == self.game_guild_name, self.bot.guilds)
                game_channel = discord.utils.find(lambda channel: channel.name == self.game_channel_name, guild.channels)
                
                #check which players are controlled by the discord user who is trying to use this command
                players = [player for player in self.game.get_players_in_registry() if player.discord_name == str(ctx.author)]
                
                #check to make sure if it's a DM, that it's from a player in the game
                if isinstance(ctx.channel, discord.channel.DMChannel) and len(players) == 0:
                    await ctx.author.send("Permission Denied! Please join the game in order to Send Commands")
                    raise games.common.GameExceptions.DiscordGameIllegalMove(f"'{ctx.author.name}' tried to send a command via DM to a game they're aren't in")
                    
                #check to make sure if it's a text channel, that it's from the game_channel
                if isinstance(ctx.channel, discord.channel.TextChannel) and game_channel != ctx.channel:
                    raise games.common.GameExceptions.DiscordGameIllegalMove(f"'{ctx.author.name}' tried to send a command to a game from the wrong channel")
                    
                #check to make sure it's either a text channel or a DM
                if not isinstance(ctx.channel, (discord.channel.DMChannel, discord.channel.TextChannel)):
                    raise games.common.GameExceptions.DiscordGameIllegalMove(f"Got a message from '{ctx.channel}'. Which of unrecognized type: {type(ctx.channel)}")
                
                #if the command requires a lock atttempt to acquire it
                if command.requires_lock:
                                    
                    if self.is_locked:
                        await ctx.channel.send(f"Illegal Move: Another command currently has the Game Lock. Cannot call '{command.name}'")
                        raise games.common.GameExceptions.DiscordGameIllegalMove(f"Another command currently has the Game Lock. Cannot call '{command.name}'")
                    else:
                        self.is_locked=True
                
            except games.common.GameExceptions.DiscordGameIllegalMove as e:
                
                try:
                    if self.illegal_move_log_channel is not None:
                        guild_name = self.illegal_move_log_channel["Guild"]
                        channel_name = self.illegal_move_log_channel["Channel"]
                    
                        guild = discord.utils.find(lambda guild: guild.name == guild_name, self.bot.guilds)
                        channel = discord.utils.find(lambda channel: channel.name == channel_name, guild.channels)
                    
                        await channel.send("\n=========================")
                        await channel.send(type(e))
                        await channel.send(e)
                        await channel.send("\n".join(traceback.format_tb(e.__traceback__)))   
                except:
                    pass
                finally:
                    return
            
            #catch any Game Errors thrown
            except games.common.GameExceptions.DiscordGameError as e:
                await ctx.channel.send(f"Game Error: {e}")
                
                try:
                    if self.error_log_channel is not None:
                        guild_name = self.error_log_channel["Guild"]
                        channel_name = self.error_log_channel["Channel"]
                        
                        guild = discord.utils.find(lambda guild: guild.name == guild_name, self.bot.guilds)
                        channel = discord.utils.find(lambda channel: channel.name == channel_name, guild.channels)
                        
                        await channel.send("\n=========================")
                        await channel.send(type(e))
                        await channel.send(e)
                        await channel.send("\n".join(traceback.format_tb(e.__traceback__)))
                        
                except:
                    pass
            
            except Exception as e:
                await ctx.channel.send(f"Unrecognized Exception: {e}")
                
                try:
                    if self.error_log_channel is not None:
                        guild_name = self.error_log_channel["Guild"]
                        channel_name = self.error_log_channel["Channel"]
                    
                        guild = discord.utils.find(lambda guild: guild.name == guild_name, self.bot.guilds)
                        channel = discord.utils.find(lambda channel: channel.name == channel_name, guild.channels)
                      
                        await channel.send("\n=========================")
                        await channel.send(type(e))
                        await channel.send(e)
                        await channel.send("\n".join(traceback.format_tb(e.__traceback__)))
                except:
                    pass
                finally:
                    return
                        
            #Run the command
            try:                    
                                                
                #add the author and the channel to the kwargs
                kwargs["DiscordAuthorContext"] = ctx.author
                kwargs["DiscordChannelContext"] = ctx.channel
            
                #run the command
                result = self.game.__getattribute__(command.name)(*args, **kwargs)
                
                #seperate out the prompts from the messages
                if isinstance(result, (list, tuple)):
                    interrupts = [res for res in result if isinstance(res, games.common.GameClasses.CommandResultInterrupt)]
                    prompts = [res for res in result if isinstance(res, games.common.GameClasses.CommandResultPrompt)]
                    messages = [res for res in result if not isinstance(res, games.common.GameClasses.CommandResultPrompt)]
                elif isinstance(result, games.common.GameClasses.CommandResultPrompt):
                    interrupts = []
                    prompts = [result]
                    messages = None
                elif isinstance(result, games.common.GameClasses.CommandResultInterrupt):
                    interrupts = [result]
                    prompts = []
                    messages = None                    
                else: 
                    interrupts = []
                    prompts = []
                    messages = result
                                
                #send the messages returned by the command
                await process_command_result(game_channel, messages)
                                
                #keep looping until there are no more game prompts or interrupts
                while len(prompts) != 0 or len(interrupts) != 0:
                
                    if len(prompts) != 0 and len(interrupts) != 0:
                        raise games.common.GameExceptions.DiscordGameError("Command returned CommandResultPrompts and CommandResultInterrupt. Only one or the other is allowed.")
                    
                    if len(prompts) != 0:
                    
                        #send out the CommandResultPrompts to the respective players
                
                        #validate that the field "func_name" matches for all the CommandResultPrompts and that "func_name" is a function in the game
                        func_name = prompts[0].func_name
                
                        for prompt in prompts:
                            if func_name != prompt.func_name:
                                raise games.common.GameExceptions.DiscordGameError(f"Two of the follow up functions for the CommandResultPrompts don't match: {func_name} and {prompte.func_name}")
                        
                        if func_name not in dir(self.game):
                            raise games.common.GameExceptions.DiscordGameError(f"The Game has not field by the name '{func_name}'. Cannot use this as a follow up functon")
                
                        #prompt the players and get their results
                        prompt_results = await asyncio.gather(*[prompt_player(game_channel, prompt) for prompt in prompts])
                        prompt_results_dict = {pr[0] : pr[1] for pr in prompt_results}
                
                        #call the return function
                        result = self.game.__getattribute__(func_name)(prompt_results_dict)
                    
                    elif len(interrupts) == 1:
                        interrupt = interrupts[0]
                    
                        #prompt the players to see if they want to interrupt
                        prompt_results = await prompt_interrupt(game_channel, interrupt)
                        
                        #call the return function
                        result = self.game.__getattribute__(interrupt.func_name)(prompt_results)
                    
                    else:
                        raise games.common.GameExceptions.DiscordGameError("Command returned multiple CommandResultInterrupts. Only one is allowed.")
                    
                    #seperate out the prompts and interrupts from the messages
                    if isinstance(result, (list, tuple)):
                        interrupts = [res for res in result if isinstance(res, games.common.GameClasses.CommandResultInterrupt)]
                        prompts = [res for res in result if isinstance(res, games.common.GameClasses.CommandResultPrompt)]
                        messages = [res for res in result if not isinstance(res, games.common.GameClasses.CommandResultPrompt)]
                    elif isinstance(result, games.common.GameClasses.CommandResultPrompt):
                        interrupts = []
                        prompts = [result]
                        messages = None
                    elif isinstance(result, games.common.GameClasses.CommandResultInterrupt):
                        interrupts = [result]
                        prompts = []
                        messages = None                    
                    else: 
                        interrupts = []
                        prompts = []
                        messages = result
                                
                    #send the messages returned by the command
                    await process_command_result(game_channel, messages)  
            
            #catch any Illegal Game Moves thrown
            except games.common.GameExceptions.DiscordGameIllegalMove as e:
                await ctx.channel.send(f"Illegal Move: {e}")
                
                try:
                    if self.illegal_move_log_channel is not None:
                        guild_name = self.illegal_move_log_channel["Guild"]
                        channel_name = self.illegal_move_log_channel["Channel"]
                        
                        guild = discord.utils.find(lambda guild: guild.name == guild_name, self.bot.guilds)
                        channel = discord.utils.find(lambda channel: channel.name == channel_name, guild.channels)
                        
                        await channel.send("\n=========================")
                        await channel.send(type(e))
                        await channel.send(e)
                        await channel.send("\n".join(traceback.format_tb(e.__traceback__)))
                        
                except:
                    pass
                
            #catch any Game Errors thrown
            except games.common.GameExceptions.DiscordGameError as e:
                await ctx.channel.send(f"Game Error: {e}")
                
                try:
                    if self.error_log_channel is not None:
                        guild_name = self.error_log_channel["Guild"]
                        channel_name = self.error_log_channel["Channel"]
                        
                        guild = discord.utils.find(lambda guild: guild.name == guild_name, self.bot.guilds)
                        channel = discord.utils.find(lambda channel: channel.name == channel_name, guild.channels)
                        
                        await channel.send("\n=========================")
                        await channel.send(type(e))
                        await channel.send(e)
                        await channel.send("\n".join(traceback.format_tb(e.__traceback__)))
                        
                except:
                    pass
            
            #catch any other Exceptions Thrown
            except Exception as e:
                await ctx.channel.send(f"Unrecognized Exception: {e}")
                
                try:
                    if self.error_log_channel is not None:
                        guild_name = self.error_log_channel["Guild"]
                        channel_name = self.error_log_channel["Channel"]
                        
                        guild = discord.utils.find(lambda guild: guild.name == guild_name, self.bot.guilds)
                        channel = discord.utils.find(lambda channel: channel.name == channel_name, guild.channels)
                        
                        await channel.send("\n=========================")
                        await channel.send(type(e))
                        await channel.send(e)
                        await channel.send("\n".join(traceback.format_tb(e.__traceback__)))
                        
                except:
                    pass
                    
            #release the game lock if it was acquired
            finally:
                if command.requires_lock:
                    self.is_locked = False    
        
        new_function.__name__ = f"{command.name}_command"
        new_command = commands.Command(new_function, name=command.name, help=command.help_message)
        
        self.bot.add_command(new_command)             
    
    def make_kill_command(self):
    
        async def kill_function(ctx):
            
            #find the guild and channel the game is using
            guild = discord.utils.find(lambda guild: guild.name == self.game_guild_name, self.bot.guilds)
            game_channel = discord.utils.find(lambda channel: channel.name == self.game_channel_name, guild.channels)
                                    
            #check to make sure if it's a text channel, that it's from the game_channel
            if isinstance(ctx.channel, discord.channel.TextChannel) and game_channel != ctx.channel:
                return
                 
            #check to make sure it's a text channel
            if not isinstance(ctx.channel, discord.channel.TextChannel):
                return
            
            self.game.kill_game()
            
            await ctx.send(f"killing game with prefix {self.command_prefix}")
            await self.bot.logout()
            
        kill_command = commands.Command(kill_function, name="killGame", help=f"Kill this game")
        self.bot.add_command(kill_command)