import pymongo
import disnake
import asyncio
import datetime
import json
import random
import requests
import re
from disnake.utils import get
from random import randint
from disnake.ext import commands
from disnake import Localized
from disnake.enums import ButtonStyle, TextInputStyle
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

cluster = pymongo.MongoClient(f"put ur mongo-db link")
database = cluster.sweetness.steam

class steam_profile(commands.Cog):
    def __init__(self, bot: commands.Bot(intents = disnake.Intents.all(), command_prefix="tribune!")):
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        custom_id = inter.component.custom_id
        if custom_id == "registerSteam":
            if database.count_documents({"_id": str(inter.author.id)}) == 0:
                database.insert_one({"_id": str(inter.author.id), "SteamID": "Отсутствует"})
            if database.find_one({'_id': str(inter.author.id)})['SteamID'] == "Отсутствует":
                await inter.response.send_modal(title=f"Привязать стим аккаунт", custom_id = "ProfileSteamDOTA", components=[disnake.ui.TextInput(label="ID_DOTA", 
                custom_id = "ID_DOTA",style=disnake.TextInputStyle.short, max_length=40)])

def setup(bot): 
    bot.add_cog(steam_profile(bot))