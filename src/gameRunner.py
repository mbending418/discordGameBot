import discord
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
        
        self.bot.run(self.token)
        
    def make_command(self, command):
        
        def process_command_result(command_result):
                
            if isinstance(command_result, str):
                return {"content" : command_result}
                
            elif isinstance(command_result, games.common.GameClasses.CommandResultMessage):
                
                return_dict = {}
                
                if (self.use_images) and (command_result.image is not None):
                    return_dict["file"] = discord.File(command_result.image)
                
                if (not self.use_images) or (command_result.image is None) or (command_result.send_both):
                    return_dict["content"] = command_result.text
                   
                if command_result.destination is not None:
                   
                    return_dict["destination"] = command_result.destination
                    
                return return_dict
                    
            elif isinstance(command_result, (list, tuple)):
                return [process_command_result(cr) for cr in command_result]
                    
            elif command_result is None:
                return None
                
            else:
                return {"content" : f"result from commmand '{command.name}' not recognized: {type(command_result)}"}
        
        async def new_function(ctx, *args, **kwargs):
        
            try:
                                
                #find the guild and channel the game is using
                guild = discord.utils.find(lambda guild: guild.name == self.game_guild_name, self.bot.guilds)
                game_channel = discord.utils.find(lambda channel: channel.name == self.game_channel_name, guild.channels)
                
                #check which players are controlled by the discord user who is trying to use this command
                players = [player for player in self.game.get_players_in_registry() if player.discord_name == str(ctx.author)]
                
                #check to make sure if it's a DM, that it's from a player in the game
                if isinstance(ctx.channel, discord.channel.DMChannel) and len(players) == 0:
                    await ctx.author.send("Permission Denied! Please join the game in order to Send Commands")
                    return
                    
                #check to make sure if it's a text channel, that it's from the game_channel
                if isinstance(ctx.channel, discord.channel.TextChannel) and game_channel != ctx.channel:
                    return
                    
                #check to make sure it's either a text channel or a DM
                if not isinstance(ctx.channel, (discord.channel.DMChannel, discord.channel.TextChannel)):
                    return
                                
                #add the author and the channel to the kwargs
                kwargs["DiscordAuthorContext"] = ctx.author
                kwargs["DiscordChannelContext"] = ctx.channel
            
                #run the command
                result = self.game.__getattribute__(command.name)(*args, **kwargs)
                
                #parse the messages returned by the command
                messages = process_command_result(result)

                if messages is None:
                    pass
                    
                elif isinstance(messages, dict):
                    destination = messages.pop("destination", game_channel)
                    await destination.send(**messages)
                    
                elif isinstance(messages, list):
                    for msg in messages:
                        destination = msg.pop("destination", game_channel)
                        await destination.send(**msg)
                else:
                    raise games.common.GameExceptions.DiscordGameError("Reached Theoretically Impossible State???")
                
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