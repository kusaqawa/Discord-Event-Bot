from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pymongo
import random
import os
import json
import datetime
import disnake
from disnake.ext import commands, tasks

cluster = pymongo.MongoClient(f"put ur mongo-db link")

db = cluster["sweetness"]
collection = db["files_event"]

class EmojiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not self.event_ban.is_running():
            self.event_ban.start()
        if not self.giveonline.is_running():
            self.giveonline.start()
        if not self.files.is_running():
            self.files.start()

    @tasks.loop(seconds=60)
    async def event_ban(self):
        try:
            guild = self.bot.get_guild(1165811916313198632)
            embed = disnake.Embed(color = 3092790).set_thumbnail(url = guild.icon.url)
            for x in db.event_ban.find():
                data_delete = db.event_ban.find_one({'_id': str(x['_id'])})['time']
                role_id = db.event_ban.find_one({'_id': str(x['_id'])})['role']
                remaining_seconds = (data_delete - datetime.datetime.now()).total_seconds()
                if remaining_seconds < 1:
                    user = disnake.utils.get(guild.members, id = int(x['_id']))
                    rolemute = disnake.utils.get(guild.roles, id = int(role_id))
                    try:
                        await user.remove_roles(rolemute)
                    except:
                        pass
                    embed.description=f'Привет {user.mention}, **Ваш** ивент бан был закончен!', 
                    embed.set_author(name = f'Ивент бан | {guild.name}', icon_url = guild.icon.url)
                    try:
                        await user.send(embed = embed) 
                    except:
                        pass
                    
                    try:
                        await user.move_to(user.voice.channel)
                    except: 
                        pass

                    db.event_ban.delete_one({'_id': str(x['_id'])})
        except Exception as e:
            print(e)

    @tasks.loop(seconds = 60)
    async def giveonline(self):
        try:
            channels = self.bot.get_guild(1165811916313198632).voice_channels
            for channel in channels:
                for member in channel.members:
                    if not member.bot == True:
                        for role in member.roles:
                            if role.id in [1167104359864225884]:
                                if member.voice.channel.name[:2] == "🔷・":
                                    if cluster.sweetness.online_event.count_documents({"_id": str(member.id)}) == 0:
                                        cluster.sweetness.online_event.insert_one({"_id": str(member.id), "online": 0})

                                    cluster.sweetness.online_event.update_one({"_id": str(member.id)}, {"$inc": {"online": +60}})
        except:
            pass

    @tasks.loop(seconds=60)
    async def files(self):
        for x in db.query_events.find():
            try:
                emoji_name = x['_id']

                src_path = db.query_event.find_one({'_id': str(x['_id'])})['src_path']
                if not collection.count_documents({"_id": str(x['_id'])}) == 0:
                    try:
                        existing_emoji = disnake.utils.get(self.bot.emojis, id = collection.find_one({'_id': str(x['_id'])})['emoji_id'])
                        await existing_emoji.delete(reason="Обновление эмоджи")
                    except:
                        pass
                    guilds = []

                    for guild in self.bot.guilds:
                        if int(guild.owner.id) == 584297528523096074:
                            if not len(guild.emojis) >= 50:
                                guilds.append(guild.id)
                    if guilds == []:
                        for i in range(10):
                            guild = await self.bot.create_guild(name = "Emoji Creative")
                    else:
                        guild = self.bot.get_guild(random.choice(guilds))
                    with open(src_path, "rb") as emoji_image:
                        new_emoji = await guild.create_custom_emoji(name=emoji_name, image=emoji_image.read(), reason="Добавление нового эмоджи")

                        collection.update_one({'_id': str(emoji_name)}, {'$set': {"emoji_take": f"<:{emoji_name}:{new_emoji.id}>"}}, upsert = True)
                        collection.update_one({'_id': str(emoji_name)}, {'$set': {"emoji_id": f"{new_emoji.id}"}}, upsert = True)
                else:
                    guilds = []
                    for guild in self.bot.guilds:
                        if int(guild.owner.id) == 1009505345577697352:
                            if not len(guild.emojis) >= 50:
                                guilds.append(guild.id)
                    if guilds == []:
                        for i in range(10):
                            guild = await self.bot.create_guild(name = "Emoji Creative")
                    else:
                        guild = self.bot.get_guild(random.choice(guilds))

                    with open(src_path, "rb") as emoji_image:
                        new_emoji = await guild.create_custom_emoji(name=emoji_name, image=emoji_image.read(), reason="Добавление нового эмоджи")
                        collection.update_one({'_id': str(emoji_name)}, {'$set': {"emoji_take": f"<:{emoji_name}:{new_emoji.id}>"}}, upsert = True)
                        collection.update_one({'_id': str(emoji_name)}, {'$set': {"emoji_id": f"{new_emoji.id}"}}, upsert = True)
                db.query_events.delete_one({'_id': str(emoji_name)})
            except:
                pass



def setup(bot):
    bot.add_cog(EmojiCog(bot))