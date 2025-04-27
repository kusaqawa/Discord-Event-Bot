import disnake
import asyncio
import json
import os
from disnake.ext import commands

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('clans!'),
    intents=disnake.Intents.all(),
    test_guilds=[1165811916313198632]
)


@bot.event
async def on_ready():
    print("Bot Ready")

@bot.command(name='load')
async def load(inter, extension):
    if not inter.author.id == 123456789098765432: 
        return
    try:
        await inter.message.delete()
        bot.load_extension(f'cogs.{extension}')
    except:
        pass

@bot.command(name='unload')
async def unload(inter, extension):
    if not inter.author.id == 123456789098765432: 
        return
    try: 
        await inter.message.delete()
        bot.unload_extension(f'cogs.{extension}')
    except:
        pass

@bot.command(name='reload')
async def reload(inter, extension):
    if not inter.author.id == 123456789098765432: 
        return
    try: 
        await inter.message.delete()
        bot.unload_extension(f'cogs.{extension}')
        await asyncio.sleep(4)
        bot.load_extension(f'cogs.{extension}')
    except: 
        pass

if __name__ == '__main__':
    for filename in os.listdir("./tcogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
            
bot.run("Put Ur Token Here")


123456789098765432