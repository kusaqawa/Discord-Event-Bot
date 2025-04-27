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

eventname = {}

cluster = pymongo.MongoClient(f"put ur mongo-db link")
database = cluster.sweetness.close

async def update_team_info(self, inter):
    custom_id = inter.component.custom_id
    msg_id = database.find_one({'_id': int(inter.author.id)})['msg']
    msg_id_data = database.find_one({'_id': int(msg_id)})
    host = disnake.utils.get(inter.guild.members, id=int(msg_id_data['author']))
    game = database.find_one({'_id': str(host.id)}, {'game': 1})['game']
    mode = database.find_one({'_id': str(host.id)}, {'mode': 1})['mode']
    prize = database.find_one({'_id': str(host.id)}, {'prize': 1})['prize']

    embed = disnake.Embed(color=disnake.Color(hex_to_rgb("#5a66ea")))
    embed.set_author(name=f"Запись на клоз {game}", icon_url=inter.guild.icon.url)
    embed.set_thumbnail(url=inter.author.display_avatar.url)
    if inter.author.id in msg_id_data['blacklist']:
        embed.description = f"{inter.author.mention}, **Вы** были **исключены** ведущим и теперь вы не можете **принять участие** в этом клозе."
        return await inter.send(ephemeral=True, embed=embed)

    database_stats = getattr(database, game)

    if database_stats.count_documents({"_id": str(inter.author.id)}) == 0:
        database_stats.insert_one({"_id": str(inter.author.id), "wins": 0, "loses": 0})
    if game == "Dota2":
        roles_and_fields = [
            ('carry', '<:1pos:1153676338310418432> Керри'),
            ('mid', '<:2pos:1153676341607137411> Мидер'),
            ('hard', '<:3pos:1153676343473610762> Сложная'),
            ('hard_support', '<:4pos:1153676346254430208> Частичная поддержка'),
            ('full_support', '<:5pos:1153676347927965768> Полная поддержка'),
        ]
        for role, role_name in roles_and_fields:
            if custom_id == f'tree_team_{role}':
                if len(msg_id_data[role]) == 2:
                    embed.description = f"{inter.author.mention}, **Свободных** слотов для {role_name.lower()} **не осталось**"
                    await inter.send(ephemeral=True, embed=embed)
                else:
                    await update_team_and_roles(self, inter, role, role_name, msg_id_data, msg_id, database_stats)

    else:
        team_roles = {
            'tree_team_one': 'team_one',
            'tree_team_two': 'team_two',
        }
        role_to_add = cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})[f'team1_id' if custom_id == 'tree_team_one' else 'team2_id']
        role_to_remove = cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})[f'team2_id' if custom_id == 'tree_team_one' else 'team1_id']
        if custom_id in team_roles:
            team_role = team_roles[custom_id]
            if len(msg_id_data[team_role]) == int(mode[-1]):
                embed.description = f"{inter.author.mention}, Свободных слотов в команде {team_role[-3]} нету"
                await inter.send(ephemeral=True, embed=embed)
            else:
                await update_team_and_roles(self, inter, team_role, f'Команда {team_role[-3]}', msg_id_data, msg_id, database_stats, role_to_add, role_to_remove)

    embed.description = f"{inter.author.mention}, **Вы** успешно **зарегистрировались**, теперь **подключайтесь в лобби** и ожидайте начала!"
    await inter.send(ephemeral=True, embed=embed)

    await update_team_embed(self, embed, inter, msg_id_data, database_stats, mode, prize)

async def update_team_and_roles(self, inter, team_role, team_name, msg_id_data, msg_id, database_stats, role_to_add=None, role_to_remove=None):
    author_id = int(inter.author.id)

    msg_id = database.find_one({'_id': int(inter.author.id)})['msg']
    msg_id_data = database.find_one({'_id': int(msg_id)})
    host = disnake.utils.get(inter.guild.members, id=int(msg_id_data['author']))
    game = database.find_one({'_id': str(host.id)}, {'game': 1})['game']
    if game == "Dota2":
        team_roles = ['carry', 'mid', 'hard', 'hard_support', 'full_support']
        for role in team_roles:
            team_list = msg_id_data[role]
            if author_id in team_list:
                database.update_one({'_id': int(msg_id)}, {'$pull': {role: author_id}}, upsert=True)
    else:
        team_roles = ['team_one', 'team_two']
        for role in team_roles:
            team_list = msg_id_data[role]
            if author_id in team_list:
                database.update_one({'_id': int(msg_id)}, {'$pull': {role: author_id}}, upsert=True)

    if game == "Dota2":
        role_name = team_role
        database.update_one({'_id': int(msg_id)}, {'$push': {role_name: author_id}}, upsert=True)
    else:
        await inter.author.add_roles(disnake.utils.get(inter.guild.roles, id=role_to_add))
        await inter.author.remove_roles(disnake.utils.get(inter.guild.roles, id=role_to_remove))

        role_name = team_role
        database.update_one({'_id': int(msg_id)}, {'$push': {role_name: author_id}}, upsert=True)

async def update_team_embed(self, embed, inter, msg_id_data, database_stats, mode, prize):
    msg_id = database.find_one({'_id': int(inter.author.id)})['msg']
    msg_id_data = database.find_one({'_id': int(msg_id)})
    host = disnake.utils.get(inter.guild.members, id=int(msg_id_data['author']))
    game = database.find_one({'_id': str(host.id)}, {'game': 1})['game']

    embed.color = 3092790
    embed.set_author(name=f"CLOSE: {game} | {inter.guild.name}", icon_url=inter.guild.icon.url)
    embed.set_image(url = "")

    need = int(mode[-1]) * 2
    if game == "Dota2":
        roles_and_fields = [
            ('carry', '<:1pos:1153676338310418432> Керри'),
            ('mid', '<:2pos:1153676341607137411> Мидер'),
            ('hard', '<:3pos:1153676343473610762> Сложная'),
            ('hard_support', '<:4pos:1153676346254430208> Частичная поддержка'),
            ('full_support', '<:5pos:1153676347927965768> Полная поддержка'),
        ]


        carry = msg_id_data['carry']
        mid = msg_id_data['mid']
        hard = msg_id_data['hard']
        hard_support = msg_id_data['hard_support']
        full_support = msg_id_data['full_support']

        all_players = len(carry) + len(mid) + len(hard) + len(hard_support) + len(full_support)

        for role, emoji in roles_and_fields:
            players_in_role = msg_id_data[role]
            empty_slots = 2 - len(players_in_role)
            role_mentions = ", ".join([f"<@{player_id}>" for player_id in players_in_role])
            
            if empty_slots > 0:
                for _ in range(empty_slots):
                    role_mentions += "\nПусто"

            embed.add_field(name=emoji, value=role_mentions, inline=False)

            for player_id in players_in_role:
                try:
                    wins, loses, total_games, winrate, name, mmr, steam_info = await get_player_stats(self, player_id, database_stats, game)
                    player_info = f"> <:winrate:1110588767124869130> Винрейт: **{winrate}%**\n> <:battle:1110588765128380486> Всего игр: **{total_games}**\n"
                    if steam_info:
                        player_info += f"> > Игровой никнейм: **{name}**\n> MMR: **{mmr}**\n"
                    player_name = disnake.utils.get(inter.guild.members, id = int(player_id))
                except:
                    player_info += f"> * Steam: **Непривязано**"
                embed.add_field(name=f'> Статистика {player_name.name}:', value=player_info, inline=False)

                embed.description=f'<:ver:1110588762121048084> **Зарегистрировано**: {all_players}/{need}\n<:giftbox:1110588981025972385> **Награда**: {prize} 💰\n<:online:1109846973378470050> Для старта необходимо ещё **{need - all_players}** игроков!'
                await inter.message.edit(embed=embed)

    else:  # For other games
        team_one = msg_id_data['team_one']
        team_two = msg_id_data['team_two']

        all_players = len(team_one) + len(team_two)
        value1 = ""
        value2 = ""

        idd = 0
        idd1 = 0

        empty_slots = 5 - len(team_one)
        for _ in range(empty_slots):
            value1 += f"{idd + 1}. Пусто\n"
            idd += 1

        empty_slots1 = 5 - len(team_two)
        for _ in range(empty_slots1):
            value2 += f"{idd1 + 1}. Пусто\n"
            idd1 += 1

        for team_member_id in team_one:
            wins, loses, total_games, winrate, name, mmr, steam_info = await get_player_stats(self, team_member_id, database_stats, game)
            value1 += f"{idd + 1}. <@{team_member_id}>\n> <:winrate:1110588767124869130> Винрейт: **{winrate}%**\n> <:battle:1110588765128380486> Всего игр: **{total_games}**\n"
            idd += 1

        for team_member_id in team_two:
            wins, loses, total_games, winrate, name, mmr, steam_info = await get_player_stats(self, team_member_id, database_stats, game)
            value2 += f"{idd1 + 1}. <@{team_member_id}>\n> <:winrate:1110588767124869130> Винрейт: **{winrate}%**\n> <:battle:1110588765128380486> Всего игр: **{total_games}**\n"
            idd1 += 1

        embed.add_field(name=f'Команда 1', value=value1, inline=False)
        embed.add_field(name=f'Команда 2', value=value2, inline=False)
        message_take = await inter.channel.fetch_message(int(msg_id))
        embed.description=f'<:ver:1110588762121048084> **Зарегистрировано**: {all_players}/{need}\n<:giftbox:1110588981025972385> **Награда**: {prize} 💰\n<:online:1109846973378470050> Для старта необходимо ещё **{need - all_players}** игроков!'
        await message_take.edit(embed=embed)

async def get_player_stats(self, team_member_id, database_stats, game):
    stats = database_stats.find_one({'_id': str(team_member_id)}, {'wins': 1, 'loses': 1})
    wins = stats['wins']
    loses = stats['loses']
    total_games = wins + loses
    winrate = (wins / total_games) * 100 if total_games != 0 else 0
    winrate = f"{winrate:.2f}".rstrip("0").rstrip(".")
    try:
        steam_info = cluster.sweetness.steam.find_one({'_id': str(team_member_id)})
        name = steam_info['name']
        mmr = steam_info['mmr']
        return wins, loses, total_games, winrate, name, mmr, True
    except:
        return wins, loses, total_games, winrate, None, None, False

class ReportMenu(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.green, emoji = '<:11:1096126530247204966>', custom_id = 'move_one_report', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.green, emoji = '<:zxc3:1009168371213926452>', custom_id = 'accept_one', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.green, emoji = '<:zxc2:1009168373936050206>', custom_id = 'accept_two', row = 0))

class BallReportDisabled(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.secondary, label = 'Вы успешно оставили отзыв', custom_id = 'ball_report', row = 0, disabled=True))

class BallReport(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.secondary, label = 'Оставить отзыв', custom_id = 'ball_report', row = 0))

class ReportView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.green, label = 'Принять', custom_id = 'accept_report', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Отклонить', custom_id = 'decline_report', row = 0))

class InviteLink(disnake.ui.View):
    def __init__(self, invite_url):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Мероприятия", custom_id = "list_activity", emoji = "<:events:1142849807698886676>"))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Запись", emoji = "<:game:1142847886044971018>", url = invite_url))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Отправить жалобу", custom_id = "report_activity", emoji = "<:report:1142856573992042496>"))

class EditClose(disnake.ui.View):
    def __init__(self, manage):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Управление", url = manage))

class ChoiceTeam(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Первую", custom_id = 'tree_team_one'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Вторую", custom_id = 'tree_team_two'))

class WinClose(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Первая", custom_id = 'win_team_one'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Вторая", custom_id = 'win_team_two'))

class YesOrno(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Принять", custom_id = 'accept_balance', emoji = '<:yes1:1092007373733900348>'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Отклонить", custom_id = 'decline_balance', emoji = '<:close:1092013516392767528>'))

class ChatClose(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Открыть чат", custom_id = 'open_chat', emoji = '▶️', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Закрыть чат", custom_id = 'close_chat', emoji = '❌', row = 0))

class VoiceClose(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Открыть войс", custom_id = 'open_voice', emoji = '▶️', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Закрыть войс", custom_id = 'close_voice', emoji = '❌', row = 0))

class Notifications(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'notifications_on', emoji = '🔔', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'notifications_off', emoji = '🔕', row = 0))

class ManageClose(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'start_close', emoji = '▶️', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'member_close', emoji = '❌', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'anonce_close', emoji = '📌', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'win_close', emoji = "<:top1:1139161095265853460>", row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'mute_close', emoji = ':mute:942394507616485396>', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'unmute_close', emoji = '<:unmute:942394404168142919>', row = 1))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, custom_id = 'cancel_close', emoji = '🗑️', row = 1))

class CloseReg(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Зарегистрироваться", custom_id = 'reg', emoji = '<:ver:1110588762121048084>', row = 0))

class CloseDota(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, custom_id = 'tree_team_carry', emoji = "<:1pos:1153676338310418432>", row = 0))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, custom_id = 'tree_team_mid', emoji = "<:2pos:1153676341607137411>", row = 0))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, custom_id = 'tree_team_hard', emoji = "<:3pos:1153676343473610762>", row = 0))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, custom_id = 'tree_team_hard_support', emoji = "<:4pos:1153676346254430208>", row = 0))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, custom_id = 'tree_team_full_support', emoji = "<:5pos:1153676347927965768>", row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Привязать стим", custom_id = 'registerSteam', emoji = '<:steam:1153714447899173015>', row = 1))


class RegDisabled(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Зарегистрироваться", custom_id = 'reg', emoji = '<:ver:1110588762121048084>', row = 0, disabled = True))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Привязать стим", custom_id = 'registerSteam', emoji = '<:steam:1153714447899173015>', row = 1, disabled = True))

class EventBack(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Меню", custom_id = 'back_close', emoji = '<:menu:1092007362354757672>', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = "Выход", custom_id = 'close_back', emoji = '<:close:1092013516392767528>', row = 0))

class CloseManageDropdown1(disnake.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Выберите игру",
            options = [
                disnake.SelectOption(label="Rust", value = 'choice_close_Rust', description="Rust"),
                disnake.SelectOption(label="CS:GO", value = 'choice_close_CSGO', description = "CS:GO"),
                disnake.SelectOption(label="CS:GO Pub", value = 'choice_close_CSGOPub', description = "CS:GO Pub"),
                disnake.SelectOption(label="Dota 2", value = 'choice_close_Dota2', description = "Dota 2"),
                disnake.SelectOption(label="Dota Pub", value = 'choice_close_DotaPub', description = "Dota Pub"),
                disnake.SelectOption(label="Valorant", value = 'choice_close_Valorant', description = "Valorant"),
                disnake.SelectOption(label="Roblox", value = 'choice_close_Roblox', description = "Roblox"),
                disnake.SelectOption(label="Apex", value = 'choice_close_Apex', description = "Apex"),
                disnake.SelectOption(label="Rainbow Six", value = 'choice_close_RainbowSix', description = "Rainbow six"),
                disnake.SelectOption(label="BrawlHalla", value = 'choice_close_BrawlHalla', description = "BrawlHalla"),
                disnake.SelectOption(label="Mobile Legends", value = 'choice_close_MobileLegends', description = "MobileLegends"),
            ],
        )

class CloseManageDropdown2(disnake.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Выберите режим",
            options = [
                disnake.SelectOption(label="1x1", value='choice_close_mode_1x1', description="1x1"),
                disnake.SelectOption(label="2x2", value='choice_close_mode_2x2', description="2x2"),
                disnake.SelectOption(label="3x3", value='choice_close_mode_3x3', description="3x3"),
                disnake.SelectOption(label="4x4", value='choice_close_mode_4x4', description="4x4"),
                disnake.SelectOption(label="5x5", value='choice_close_mode_5x5', description="5x5"),
            ],
        )

class CloseEdit(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.blurple, label = "Настроить", custom_id = 'edit_close', emoji = "<:manage:950741317883953182>"))
        self.add_item(disnake.ui.Button(style = ButtonStyle.green, label = "Создать", custom_id = 'create_close', emoji = "<:close:1143172416688902196>"))

class CloseManage(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(CloseManageDropdown1())
        self.add_item(CloseManageDropdown2())
        self.add_item(disnake.ui.Button(style = ButtonStyle.blurple, label = "Настроить награду", custom_id = 'close_edit_prize', emoji = "<:manage:950741317883953182>"))
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = "Отмена", custom_id = 'close_back'))

def hex_to_rgb(value):
    value = value.lstrip('#')
    RGB = list(tuple(int(value[i:i + len(value) // 3], 16) for i in range(0, len(value), len(value) // 3)))
    return (RGB[0]<<16) + (RGB[1]<<8) + RGB[2]

class closebot(commands.Cog):
    def __init__(self, bot: commands.Bot(intents = disnake.Intents.all(), command_prefix = 'test!')):
        self.bot = bot

    @commands.slash_command(description = 'Создание клоза')
    @commands.has_any_role(1167104361067974707)
    async def close(self, inter):
        if database.count_documents({"_id": str(inter.author.id)}) == 0:
            database.insert_one({"_id": str(inter.author.id), "game": "Неизвестно", 'mode': 'Неизвестно', 'prize': 'Неизвестно'})

        game = database.find_one({'_id': str(inter.author.id)})['game']
        mode = database.find_one({'_id': str(inter.author.id)})['mode']
        prize = database.find_one({'_id': str(inter.author.id)})['prize']

        embed = disnake.Embed(color = 3092790, description = f"> **Игра**: {game}\n> **Режим**: {mode}\n> **Награда**: {prize}")
        embed.set_author(name = f"Создание клоза | {inter.guild.name}", icon_url = inter.guild.icon.url)
        embed.set_image(url = "")
        return await inter.send(ephemeral = True, embed = embed, view = CloseEdit())
    @close.error
    async def close_error(self, inter, error):
        if isinstance(error, commands.MissingAnyRole):
            embed = disnake.Embed(description = f'{inter.author.mention}, У **Вас** нет на это **разрешения**!', color = disnake.Color.red())
            embed.set_author(name = f"Запустить клоз | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            embed.set_author(name = inter.author, icon_url = inter.author.avatar.url)
            await inter.send(embed = embed)
        else: 
            print(error)

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        custom_id = inter.component.custom_id

        if custom_id == 'reg':
            embed = disnake.Embed(color = 3092790)
            embed.set_author(name = f"Close | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)

            database.update_one({'_id': int(inter.author.id)}, {'$set': {'msg': int(inter.message.id)}}, upsert = True)
            
            embed.description = f"{inter.author.mention}, **Выбери** в какую **команду** ты хочешь записаться"
            await inter.send(ephemeral = True, embed = embed, view = ChoiceTeam())
            
        if custom_id.startswith('tree_team'):
            await inter.response.defer()
            await update_team_info(self, inter)

        if custom_id == "list_activity":
            embed = disnake.Embed(description = "", color = 3092790)
            embed.set_author(name = f"Активные мероприятия | {inter.guild.name}", icon_url = inter.guild.icon.url)
            event_count = 0
            for event in cluster.sweetness.event_list.find():
                try:
                    start = cluster.sweetness.event_list.find_one({'_id': str(event['_id'])})['start']
                    category = cluster.sweetness.event_list.find_one({'_id': str(event['_id'])})['category']

                    members = 0
                    for channel in disnake.utils.get(inter.guild.categories, id = int(category)).voice_channels:
                        try:
                            members += len(channel.members)
                        except:
                            pass

                    invitelink = cluster.sweetness.event_list.find_one({'_id': str(event['_id'])})['invitelink']
                    host = cluster.sweetness.event_list.find_one({'_id': str(event['_id'])})['host']
                    prize = cluster.sweetness.event_list.find_one({'_id': str(event['_id'])})['prize']

                    embed.description += f"### **Мероприятие**: {event['_id']}\n<:tribune:1142846971032371331> Ведущий: <@{host}>\n<:timely:1130199657482571888> Награда `{prize}`\n<:date1:1139169091840655421> Начало ивента {start}\n \
                    <:members:1142853455304720525> Кол-во участников: `{members}`\n"
                    event_count += 1
                except:
                    cluster.sweetness.event_list.delete_one({'_id': str(event['_id'])})
            if event_count == 0:
                embed.description += f"# В данное время на сервере отсутствуют какие-либо клозы или мероприятия."
            embed.set_footer(text = f"Счетчик мероприятий: {event_count}")
            return await inter.send(embed = embed, ephemeral = True)

        if custom_id == 'create_close':
            if cluster.sweetness.closemod.count_documents({"_id": str(inter.author.id)}) == 0:
                cluster.sweetness.closemod.insert_one({"_id": str(inter.author.id), "game": "Отсутствует", "category": 0})
            cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'game': "Отсутствует"}}, upsert = True)

            game = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['game']
            
            if not game == 'Отсутствует':
                embed = disnake.Embed(color = disnake.Color(hex_to_rgb("#ffad20")), description = f"{inter.author.mention}, **Вы** не можете запустить **ещё один клоз**, вам нужно **закончить предыдущий**!")
                embed.set_author(name = f"Клозы | {inter.guild.name}", icon_url = inter.guild.icon.url)
                embed.set_thumbnail(url = inter.author.display_avatar.url)
                return await inter.send(ephemeral = True, embed = embed)

            game = database.find_one({'_id': str(inter.author.id)})['game']
            cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'game': game}}, upsert = True)
            mode = database.find_one({'_id': str(inter.author.id)})['mode']
            prize = database.find_one({'_id': str(inter.author.id)})['prize']

            image = disnake.Embed(color = 3092790)
            embed = disnake.Embed(color = 3092790)
            match (game, mode):
                case ('CSGO', '5x5'):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('CSGO', '1x1'):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('Dota2', '5x5'):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('Dota2', '1x1'):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('Valorant', '5x5'):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('Valorant', '1x1'):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('DotaPub', _):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('CSGOPub', _):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('ValorantPub', _):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('BrawlHalla', _):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case ('MobileLegends', _):
                    image_url = 'https://media.discordapp.net/attachments/1154165500302069760/1156216528455336006/anounce_ban.gif?ex=65142a0d&is=6512d88d&hm=2b7e154293b7949058fbe83beba856107d46a4c568b91527f8f42b7e4fad6ea8&=&width=611&height=215'
                case (_, _):
                    embed.description = f"{inter.author.mention}, **Вы** не выбрали **игру** либо **режим.**"
                    return await inter.send(inter.author.mention, embed = embed)

            image.set_image(url=image_url)

            embed1 = disnake.Embed(color = 3092790)
            embed1.set_thumbnail(url = inter.author.avatar.url)
            embed1.set_author(name = f"Клозы | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed1.description = f'{inter.author.mention}, **Вы** успешно **запустили клоз** под названием **{game}**!'
            await inter.send(content = inter.author.mention, embed = embed1)
            print('asfd')
            if game in ['DotaPub', 'CSGOPub', 'ValorantPub', 'BrawlHalla', 'MobileLegends']:
                MainCategory = await inter.guild.create_category(f"{game} | {inter.author.name}")
            else:
                MainCategory = await inter.guild.create_category(f"{game} {mode} | {inter.author.name}")
            edit_channel = await inter.guild.create_text_channel(name = "💻・Управление", category = MainCategory)

            await edit_channel.set_permissions(inter.guild.default_role, view_channel = False)
            await edit_channel.set_permissions(inter.author, view_channel = True)

            channel_1 = await inter.guild.create_voice_channel(name = f"🔷・Лобби", category = MainCategory)
            channel_2 = await inter.guild.create_voice_channel(name = f"🔹・Команда ¹", category = MainCategory)

            if not game in ['DotaPub', 'CSGOPub']:
                channel_3 = await inter.guild.create_voice_channel(name = f"🔹・Команда ²", category = MainCategory)

                await channel_2.set_permissions(inter.guild.default_role, connect = False)
                await channel_3.set_permissions(inter.guild.default_role, connect = False)
                await channel_2.set_permissions(inter.author, view_channel = True, connect = True)
                await channel_3.set_permissions(inter.author, view_channel = True, connect = True)

                await channel_2.set_permissions(inter.guild.default_role, connect = False)
                await channel_3.set_permissions(inter.guild.default_role, connect = False)
                await channel_2.set_permissions(inter.author, view_channel = True, connect = True)
                await channel_3.set_permissions(inter.author, view_channel = True, connect = True)

                await channel_1.set_permissions(inter.guild.default_role, connect = False)
                await channel_1.set_permissions(inter.author, view_channel = True, connect = True)

                await channel_1.set_permissions(disnake.utils.get(inter.guild.roles, id = int(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team1_id'])), view_channel = True, connect = True)
                await channel_1.set_permissions(disnake.utils.get(inter.guild.roles, id = int(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team2_id'])), view_channel = True, connect = True)

                await channel_2.set_permissions(disnake.utils.get(inter.guild.roles, id = int(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team1_id'])), view_channel = True, connect = True)
                await channel_3.set_permissions(disnake.utils.get(inter.guild.roles, id = int(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team2_id'])), view_channel = True, connect = True)

                await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['unverify_id']), view_channel = False) # unverify
                await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['nedo_id']), view_channel = False) # не допуск
                await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['localban_id']), view_channel = False) # local ban
                await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['closeban_id']), connect = False) # close ban

                embed2 = disnake.Embed(color = 3092790, description = f'<:ver:1110588762121048084> **Зарегистрировано**: 0/{int(mode[-1]) + int(mode[-1])}\n<:giftbox:1110588981025972385> **Награда**: {prize} 💰\n<:online:1109846973378470050> Для старта необходимо ещё **{int(mode[-1]) + int(mode[-1])}** игроков!')
                embed2.set_author(name = f"CLOSE: {game}", icon_url = inter.guild.icon.url)
                embed2.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')
                value = ""
                close_channel = await inter.guild.create_text_channel(name=f"📧・Запись",category = MainCategory)

                await close_channel.set_permissions(inter.guild.default_role, send_messages = False)
        
                invitelink = await close_channel.create_invite(max_uses = 99)
                invite_url = invitelink.url

                for i in range(2):
                    value += f"{i + 1}. Пусто \n"
                if game == "Dota2":
                    embed2.add_field(name = "<:1pos:1153676338310418432> Керри", value = value, inline = False)
                    embed2.add_field(name = "<:2pos:1153676341607137411> Мид", value = value, inline = False)
                    embed2.add_field(name = "<:3pos:1153676343473610762> Сложная", value = value, inline = False)
                    embed2.add_field(name = "<:4pos:1153676346254430208> Частичная поддержка", value = value, inline = False)
                    embed2.add_field(name = "<:5pos:1153676347927965768> Полная поддержка", value = value, inline = False)
                    msg = await close_channel.send(embed = embed2, view = CloseDota())
                    database.insert_one({"_id": int(msg.id), 'author': int(inter.author.id), 'carry': [], 'mid': [], 'hard': [], 'hard_support': [], "full_support": [], 'blacklist': [], 'lobby': channel_1.id})
                else:
                    embed2.add_field(name = "Команда 1", value = value, inline = False)
                    embed2.add_field(name = "Команда 2", value = value, inline = False)
                    msg = await close_channel.send(embed = embed2, view = CloseReg())
                    database.insert_one({"_id": int(msg.id), 'author': int(inter.author.id), 'team_one': [], 'team_two': [], 'blacklist': [], 'lobby': channel_1.id})

                embed1 = disnake.Embed(color = 3092790, description = f"Close - Закрытые игры по типу турниров. За победу в клозах можно получить награду в виде определенного количества 💰\n\nРегулярно, несколько раз в неделю наши <@&1120613357867778068> проводят закрытые игры. Включайте уведомления, чтобы не пропустить!")
                embed1.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')

                embed.set_footer(text = f'Ведущий: {inter.author}', icon_url = inter.author.display_avatar.url)
                embed.set_author(name = f"Close - {game} {mode}", icon_url = inter.guild.icon.url)
                embed.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')

                input = datetime.datetime.now()
                data = int(input.timestamp())

                embed.description = f"```fix\nClose - Закрытые игры по типу турниров. За победу в клозах можно получить награду в виде определенного количества 💰!```"
                embed.add_field(name = f"<:tribune:1142846971032371331> Ведущий", value = f"{inter.author.mention}")
                embed.add_field(name = f"<:timely:1130199657482571888> Награда", value = f"{prize} 💰")
                embed.add_field(name = f"<:date1:1139169091840655421> Начало ивента", value = f'<t:{data}:F>')
                message = await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['news_channel_id']).send(embeds = [image, embed], view = InviteLink(invite_url))

                database.update_one({'_id': int(inter.author.id)}, {'$set': {'msg': int(msg.id)}}, upsert = True)
                database.update_one({'_id': int(inter.author.id)}, {'$set': {'channel': int(close_channel.id)}}, upsert = True)
                database.update_one({'_id': int(inter.author.id)}, {'$set': {'prize': prize}}, upsert = True)
                database.update_one({'_id': int(inter.author.id)}, {'$set': {'channel': int(close_channel.id)}}, upsert = True)

                cluster.sweetness.event_list.insert_one({"_id": str(f"{game} {mode} #{random.randint(1, 1000)}"), 'start': f"<t:{data}:F>", 'category': int(MainCategory.id), 'invitelink': invite_url, 'host': int(inter.author.id), 'prize': prize})
                cluster.sweetness.event_report.insert_one({"_id": str(message.id), 'game': f"{game} {mode}", 'start': f"<t:{data}:F>", 'category': int(MainCategory.id), 'invitelink': invite_url, 'host': int(inter.author.id), 'prize': prize})
           
            embed = disnake.Embed(color = 3092790)
            embed.set_author(name = f"Управление клозом - {game} {mode}", icon_url = inter.guild.icon.url)
            embed.description = "▶️ - Начать игру\n❌ - Удалить пользователя из записи на игру\n📌 - Объявить о поиске недостающих игроков\n<:top1:1139161095265853460> - Определить победителя\n<:mute:942394507616485396> Замутить всех игроков\n<:unmute:942394404168142919> Размутить всех игроков\n🗑️ - Отменить игру"
            embed.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')
            await edit_channel.send(inter.author.mention, embed = embed, view = ManageClose())

            channel = disnake.utils.get(inter.guild.categories, id = int(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['category_id']))
            channelxd = channel.position
            
            await MainCategory.edit(position = int(channelxd))
            cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'category': MainCategory.id}}, upsert = True)

            t = "<:snejok:1043825591494901760>"
            embed = disnake.Embed(color = 3092790, description = f"{t} Название: {game}\n{t} Категория: <#{MainCategory.id}>")
            embed.set_author(name = f"Начал клоз - {inter.author}", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['logs_channel_id']).send(embed = embed)

        if custom_id == "report_activity":
            id_message = str(inter.message.id)

            await inter.response.send_modal(title = "Отправить жалобу", custom_id = "report_activity", components = [
                disnake.ui.TextInput(label="Причина",custom_id = "Причина",style=disnake.TextInputStyle.paragraph, max_length=200)])
            
            modal_inter: disnake.ModalInteraction = await self.bot.wait_for("modal_submit",check=lambda i: i.custom_id == "report_activity" and i.author.id == inter.author.id)

            for key, value in modal_inter.text_values.items():
                reason = value

            number = randint(1, 15)

            embed = disnake.Embed(color = 3092790, description=f"{inter.author.mention}, **Жалоба** была успешно **отправлена** на рассмотрение, под номером **{number}**")
            embed.set_author(name = "Жалоба", icon_url = "https://cdn.discordapp.com/attachments/1125009710446288926/1142861099897716879/report.png")
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            await modal_inter.response.send_message(embed = embed, ephemeral = True)

            embed = disnake.Embed(description="", color = 3092790)
            event = cluster.sweetness.event_report.find_one({'_id': str(id_message)})['game']
            start = cluster.sweetness.event_report.find_one({'_id': str(id_message)})['start']

            category = cluster.sweetness.event_list.find_one({'_id': str(event['_id'])})['category']
            members = 0
            for channel in disnake.utils.get(inter.guild.categories, id = int(category)).voice_channels:
                try:
                    members += len(channel.members)
                except:
                    pass
                
            invitelink = cluster.sweetness.event_report.find_one({'_id': str(id_message)})['invitelink']
            host = cluster.sweetness.event_report.find_one({'_id': str(id_message)})['host']
            prize = cluster.sweetness.event_report.find_one({'_id': str(id_message)})['prize']

            embed.description += f"### **Мероприятие**: {event}\n<:tribune:1142846971032371331> Ведущий: <@{host}>\n<:timely:1130199657482571888> Награда `{prize}`\n<:date1:1139169091840655421> Начало ивента {start}\n \
            <:members:1142853455304720525> Кол-во участников: `{members}`\n"

            embed.set_author(name = "Жалоба", icon_url = "https://cdn.discordapp.com/attachments/1125009710446288926/1142861099897716879/report.png")
            embed.add_field(name = "> Информация о истце:", value = f"⠀**Пользователь:** {inter.author.mention}\n⠀**ID:** {inter.author.id}", inline = True)
            embed.add_field(name = "> ID жалобы:", value = f"⠀**{number}**", inline = True)
            embed.add_field(name = "> Причина", value = f"```{reason}```", inline = False)
            msg = await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['report_channel_id']).send(content = "<@&1129862670468776025>", embed = embed, view = ReportView())
            
            database.update_one({'_id': str(msg.id)}, {'$set': {'user': inter.author.id}}, upsert = True)

        if custom_id == 'ball_report':
            await inter.response.send_modal(title=f"Отзыв", custom_id = "review_report", components=[
                disnake.ui.TextInput(label=f"Текст", custom_id = f"Текст", style=disnake.TextInputStyle.paragraph, max_length=500)])

        if custom_id[-6:] == 'report':
            if custom_id == 'accept_report':
                embed = inter.message.embeds[0]
                embed.set_footer(text=f"Принял репорт - {inter.author} / id - {inter.author.id}", icon_url=inter.author.display_avatar.url)
                await inter.message.edit(embed=embed, components = [])
                number = randint(1000, 9999)

                category = disnake.utils.get(inter.guild.categories, id = cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['report_category_id'])
                report_channel_text = await inter.guild.create_text_channel(name = f"💬・Жалоба ивенты {number}", category = category)
                report_channel_voice = await inter.guild.create_voice_channel(name = f"🚫・Жалоба ивенты {number}", category = category)
                await report_channel_voice.set_permissions(inter.author, connect = True, view_channel = True)

                user = disnake.utils.get(inter.guild.members, id = database.find_one({'_id': str(inter.message.id)})['user'])

                embed = disnake.Embed(color = 3092790, description=f"{user.mention}, Ваша **жалоба** на мероприятие была **Принята** старшим администратром, в скором **Времени** с вами свяжутся.")
                embed.set_author(name = f"Events Logs | {inter.guild.name}", icon_url = inter.guild.icon.url)
                embed.set_thumbnail(url = user.display_avatar.url)
                embed.add_field(name = "Модератор", value = f"> {inter.author.mention}\n> {inter.author.id}")
                embed.set_footer(text = f"Сервер {inter.guild.name}", icon_url = inter.guild.icon.url)
                msg = await user.send(embed = embed)

                embed = disnake.Embed(description=f"<:11:1096126530247204966> - переместить {user.mention}\n<:zxc3:1009168371213926452> - завершить в пользу {user.mention} \
                                      \n<:zxc2:1009168373936050206> - отклонить жалобу {user.mention}", color = 3092790)
                embed.set_author(name = "Управление жалобой", icon_url = inter.guild.icon.url)
                embed.set_footer(text = f"Модератор - {inter.author} / id - {inter.author.id}", icon_url = inter.author.display_avatar.url)
                embed.set_thumbnail(url = inter.author.display_avatar.url)
                msg = await report_channel_text.send(inter.author.mention, embed = embed, view = ReportMenu())

                database.update_one({'_id': str(msg.id)}, {'$set': {'text_channel': report_channel_text.id}}, upsert = True)
                database.update_one({'_id': str(msg.id)}, {'$set': {'channel': report_channel_voice.id}}, upsert = True)
                database.update_one({'_id': str(msg.id)}, {'$set': {'user': user.id}}, upsert = True)
                
            if custom_id == 'decline_report':
                embed = inter.message.embeds[0]
                embed.set_footer(text=f"Отклонил репорт - {inter.author} / id - {inter.author.id}", icon_url=inter.author.display_avatar.url)
                await inter.message.edit(embed=embed, components = [])

            if custom_id == 'move_one_report':
                await inter.response.defer()
                report_channel_voice = database.find_one({'_id': str(inter.message.id)})['channel']
                user = disnake.utils.get(inter.guild.members, id = database.find_one({'_id': str(inter.message.id)})['user'])
                try:
                    await user.move_to(self.bot.get_channel(report_channel_voice))
                except:
                    embed = disnake.Embed(color = 3092790, description = f"{inter.author.mention}, **{user.mention}** находится не в голосовом канале")
                    embed.set_author(name = f"Репорты | {inter.guild.name}", icon_url = inter.guild.icon.url)
                    embed.set_thumbnail(url = inter.author.display_avatar.url)
                    await inter.send(embed = embed)

        if custom_id == 'accept_one':
            user = disnake.utils.get(inter.guild.members, id = database.find_one({'_id': str(inter.message.id)})['user'])
            await inter.message.edit(components = [])
            try:
                embed = disnake.Embed(color = 3092790, description=f"{user.mention}, **Разбор** Вашей жалобы **был** завершен в вашу пользу. В скором времени наказание будет выдано. Ожидайте ответа старшей администрации.\n\nОставьте **отзыв** администратору, который **занимался** Вашей **жалобой**")
                embed.set_author(name = f"Events Logs | {inter.guild.name}", icon_url = inter.guild.icon.url)
                embed.set_thumbnail(url = user.display_avatar.url)
                embed.add_field(name = "Администратор", value = f"> {inter.author.mention}\n> {inter.author.id}")
                embed.set_footer(text = f"Сервер {inter.guild.name}", icon_url = inter.guild.icon.url)
                msg = await user.send(embed = embed, view = BallReport())
                database.update_one({'_id': str(msg.id)}, {'$set': {'moderator': int(inter.author.id)}}, upsert = True)
            except:
                pass

            report_channel_voice = self.bot.get_channel(database.find_one({'_id': str(inter.message.id)})['channel'])
            report_channel_text = self.bot.get_channel(database.find_one({'_id': str(inter.message.id)})['text_channel'])
            await report_channel_text.delete()
            await report_channel_voice.delete()

        if custom_id == 'accept_two':
            user = disnake.utils.get(inter.guild.members, id = database.find_one({'_id': str(inter.message.id)})['user'])
            await inter.message.edit(components = [])
            try:
                embed = disnake.Embed(color = 3092790, description=f"{user.mention}, **Разбор** Вашей жалобы **был** завершен. Решением старшей администрации, жалоба была отклонена.\nОставьте **отзыв** администратору, который **занимался** Вашей **жалобой**")
                embed.set_author(name = f"Events Logs | {inter.guild.name}", icon_url = inter.guild.icon.url)
                embed.set_thumbnail(url = user.display_avatar.url)
                embed.add_field(name = "Администратор", value = f"> {inter.author.mention}\n> {inter.author.id}")
                embed.set_footer(text = f"Сервер {inter.guild.name}", icon_url = inter.guild.icon.url)
                msg = await user.send(embed = embed, view = BallReport())
                database.update_one({'_id': str(msg.id)}, {'$set': {'moderator': int(inter.author.id)}}, upsert = True)
            except:
                pass

            report_channel_voice = self.bot.get_channel(database.find_one({'_id': str(inter.message.id)})['channel'])
            report_channel_text = self.bot.get_channel(database.find_one({'_id': str(inter.message.id)})['text_channel'])
            await report_channel_text.delete()
            await report_channel_voice.delete()

        if custom_id == 'close_edit_prize':
            await inter.response.send_modal(title = "Изменить награду", custom_id = "close_edit_prize", components = [
                disnake.ui.TextInput(label="Награда",placeholder="Например: 5000",custom_id = "Награда",style=disnake.TextInputStyle.short, max_length=4)])

        if custom_id == 'edit_close':
            embed = disnake.Embed(color = 3092790, description = f"{inter.author.mention}, Выберите что вы хотите настроить")
            embed.set_author(name = f"Создание клоза | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            await inter.response.edit_message(embed = embed, view = CloseManage())
        if custom_id == 'close_back':
            result = cluster.sweetness.close
            game = result.find_one({'_id': str(inter.author.id)})['game']
            mode = result.find_one({'_id': str(inter.author.id)})['mode']
            prize = result.find_one({'_id': str(inter.author.id)})['prize']
            embed = disnake.Embed(color = 3092790, description = f"**Игра**: {game}\n**Режим**: {mode}\n**Награда**: {prize}")
            embed.set_author(name = f"Создание клоза | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_image(url = "")
            return await inter.response.edit_message(embed = embed, view = CloseEdit())
        if custom_id[-5:] == 'close':
            embed = disnake.Embed(color = 3092790)
            embed.set_author(name = "Управление клозом", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.avatar.url)

            msg_id = database.find_one({'_id': int(inter.author.id)})['msg']
            id_channel = database.find_one({'_id': int(inter.author.id)})['channel']
            channel = self.bot.get_channel(id_channel)
            message = await channel.fetch_message(int(msg_id))

            game = database.find_one({'_id': str(inter.author.id)})['game']
            mode = database.find_one({'_id': str(inter.author.id)})['mode']

            if custom_id == 'start_close':
                embed = disnake.Embed(color = 3092790, description = f'{inter.author.mention}, **Вы** успешно начали клоз!')
                embed.set_author(name = f"Начать клоз | {inter.guild.name}", icon_url = inter.guild.icon.url)

                msg = database.find_one({'_id': int(inter.author.id)})['msg']
                if game == "Dota2":
                    no_voice = []
                    await inter.response.defer()
                    for member in database.find_one({'_id': int(msg)})['carry']:
                        try:
                            member_take = disnake.utils.get(inter.guild.members, id = int(member))
                            channel_member = member_take.voice.channel.id
                        except:
                            no_voice.append(f"<@{member}>\n")
                    for member in database.find_one({'_id': int(msg)})['mid']:
                        try:
                            member_take = disnake.utils.get(inter.guild.members, id = int(member))
                            channel_member = member_take.voice.channel.id
                        except:
                            no_voice.append(f"<@{member}>\n")
                    for member in database.find_one({'_id': int(msg)})['hard']:
                        try:
                            member_take = disnake.utils.get(inter.guild.members, id = int(member))
                            channel_member = member_take.voice.channel.id
                        except:
                            no_voice.append(f"<@{member}>\n")
                    for member in database.find_one({'_id': int(msg)})['hard_support']:
                        try:
                            member_take = disnake.utils.get(inter.guild.members, id = int(member))
                            channel_member = member_take.voice.channel.id
                        except:
                            no_voice.append(f"<@{member}>\n")
                    for member in database.find_one({'_id': int(msg)})['full_support']:
                        try:
                            member_take = disnake.utils.get(inter.guild.members, id = int(member))
                            channel_member = member_take.voice.channel.id
                        except:
                            no_voice.append(f"<@{member}>\n")
                    if not no_voice == []:
                        embed.description = f"{inter.author.mention}, Ожидаю игроков\n{''.join(no_voice)}!"
                        await inter.send(embed = embed, ephemeral = True)

                        return await message.channel.send(f"**Игра началась, у вас есть 5 минут чтобы зайти в войс**\n{''.join(no_voice)}")

                    category_id = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['category']
                    MainCategory = disnake.utils.get(inter.guild.categories, id = category_id)

                    await message.edit(view = RegDisabled())

                    password = random.randint(100, 999)
                    lobby = random.randint(0, 100)

                    carry = database.find_one({'_id': int(msg)})['carry']
                    mid = database.find_one({'_id': int(msg)})['mid']
                    hard = database.find_one({'_id': int(msg)})['hard']
                    hard_support = database.find_one({'_id': int(msg)})['hard_support']
                    full_support = database.find_one({'_id': int(msg)})['full_support']

                    random.shuffle(carry)
                    random.shuffle(mid)
                    random.shuffle(hard)
                    random.shuffle(hard_support)
                    random.shuffle(full_support)

                    embed.description = f'Готовность: <:verify:1080867738572050463>\n\nНазвание лобби: **sweetness{lobby}**\nПароль: **{password}**'
                    embed.set_author(name = f"Информация о матче | {game} {mode}", icon_url = inter.guild.icon.url)

                    await disnake.utils.get(inter.guild.members, id = int(carry[0])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152629960704540784))
                    await disnake.utils.get(inter.guild.members, id = int(mid[0])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152629960704540784))
                    await disnake.utils.get(inter.guild.members, id = int(hard[0])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152629960704540784))
                    await disnake.utils.get(inter.guild.members, id = int(hard_support[0])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152629960704540784))
                    await disnake.utils.get(inter.guild.members, id = int(full_support[0])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152629960704540784))

                    await disnake.utils.get(inter.guild.members, id = int(carry[1])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152630559621795931))
                    await disnake.utils.get(inter.guild.members, id = int(mid[1])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152630559621795931))
                    await disnake.utils.get(inter.guild.members, id = int(hard[1])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152630559621795931))
                    await disnake.utils.get(inter.guild.members, id = int(hard_support[1])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152630559621795931))
                    await disnake.utils.get(inter.guild.members, id = int(full_support[1])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152630559621795931))

                    embed.add_field(name = f"Team Alpha", value = f"<:1pos:1153676338310418432> <:to4kaa:947909744985800804> <@{carry[0]}>\n<:2pos:1153676341607137411> <:to4kaa:947909744985800804> <@{mid[0]}> \
                    \n<:3pos:1153676343473610762> <:to4kaa:947909744985800804> <@{hard[0]}>\n<:4pos:1153676346254430208> <:to4kaa:947909744985800804> <@{hard_support[0]}>\n<:5pos:1153676347927965768> <:to4kaa:947909744985800804> <@{full_support[0]}>")

                    embed.add_field(name = f"Team Beta", value = f"<:1pos:1153676338310418432> <:to4kaa:947909744985800804> <@{carry[1]}>\n<:2pos:1153676341607137411> <:to4kaa:947909744985800804> <@{mid[1]}> \
                    \n<:3pos:1153676343473610762> <:to4kaa:947909744985800804> <@{hard[1]}>\n<:4pos:1153676346254430208> <:to4kaa:947909744985800804> <@{hard_support[1]}>\n<:5pos:1153676347927965768> <:to4kaa:947909744985800804> <@{full_support[1]}>")
                    embed.set_footer(text = f"Ведущий: {inter.author}", icon_url = inter.author.display_avatar.url)                    
                    await message.channel.send(f"**{game} {mode} Команды набраны**", embed = embed)

                    embed.description = f'{inter.author.mention}, **Вы** успешно начали клоз {game}!'
                    await inter.send(embed = embed, ephemeral = True)
                else:
                    no_voice = []
                    await inter.response.defer()
                    value1 = ""
                    value2 = ""
                    for member in database.find_one({'_id': int(msg)})['team_one']:
                        try:
                            member_take = disnake.utils.get(inter.guild.members, id = int(member))
                            channel_member = member_take.voice.channel.id
                            value1 += f"<@{member}>\n"
                        except:
                            no_voice.append(f"<@{member}>\n")
                    for member in database.find_one({'_id': int(msg)})['team_two']:
                        try:
                            member_take = disnake.utils.get(inter.guild.members, id = int(member))
                            channel_member = member_take.voice.channel.id
                            value2 += f"<@{member}>\n"
                        except:
                            no_voice.append(f"<@{member}>\n")
                    if not no_voice == []:
                        embed.description = f"{inter.author.mention}, Ожидаю игроков\n{''.join(no_voice)}!"
                        await inter.send(embed = embed, ephemeral = True)

                        return await message.channel.send(f"**Игра началась, у вас есть 5 минут чтобы зайти в войс**\n{''.join(no_voice)}")

                    category_id = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['category']
                    MainCategory = disnake.utils.get(inter.guild.categories, id = category_id)

                    await message.edit(view = RegDisabled())

                    team_one = database.find_one({'_id': int(msg)})['team_one']
                    team_two = database.find_one({'_id': int(msg)})['team_two']

                    random.shuffle(team_one)
                    random.shuffle(team_two)

                    embed.description = f'Готовность: <:verify:1080867738572050463>'
                    embed.set_author(name = f"Информация о матче | {game} {mode}", icon_url = inter.guild.icon.url)

                    await disnake.utils.get(inter.guild.members, id = int(team_one[0])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152629960704540784))
                    await disnake.utils.get(inter.guild.members, id = int(team_two[0])).add_roles(disnake.utils.get(inter.guild.roles, id = 1152629960704540784))

                    embed.add_field(name = f"Team Alpha", value = value1)
                    embed.add_field(name = f"Team Beta", value = value2)

                    embed.set_footer(text = f"Ведущий: {inter.author}", icon_url = inter.author.display_avatar.url)                    
                    await message.channel.send(f"**{game} {mode} Команды набраны**", embed = embed)

                    embed.description = f'{inter.author.mention}, **Вы** успешно начали клоз {game}!'
                    await inter.send(embed = embed, ephemeral = True)

            if custom_id == 'cancel_close':
                return await inter.response.send_modal(title=f"Отменить клоз", custom_id = "cancel_close", components=[
                    disnake.ui.TextInput(label="Причина", placeholder="Например: недостаточно участников",custom_id = "Причина", style=disnake.TextInputStyle.short, max_length=100)])
    
            if custom_id == 'member_close':
                return await inter.response.send_modal(title=f"Айди участника", custom_id = "id_delete_member", components=[
                    disnake.ui.TextInput(label="Айди", placeholder="Например: 849353684249083914",custom_id = "Айди", style=disnake.TextInputStyle.short, max_length=25)])
    
            if custom_id == 'anonce_close':
                game = database.find_one({'_id': str(inter.author.id)})['game']
                mode = database.find_one({'_id': str(inter.author.id)})['mode']
                embed = disnake.Embed(color = 3092790)
                embed.set_author(name = f"Анонсировать клоз | {inter.guild.name}", icon_url = inter.guild.icon.url)
                embed.description = f"{inter.author.mention}, **Вы** успешно анонсировали клоз в <#{message.channel.id}>"
                await inter.send(embed = embed, ephemeral = True)
                if game == 'Rust':
                    embed = disnake.Embed(color = 3092790, description = f'Нужны ещё участники в **CLOSE матч** по игре `RUST [UKN] {mode}`.')
                    await message.channel.send(f"CLOSE: RUST [UKN] {mode} Есть свободные места <@&1016327573866827776>", embed = embed)
                else:
                    embed = disnake.Embed(color = 3092790, description = f'Нужны ещё участники в **CLOSE матч** по игре `{game} {mode}`.')
                    await message.channel.send(f"CLOSE: {game} {mode} Есть свободные места <@&1016327573866827776>", embed = embed)
                await asyncio.sleep(4)
                await inter.delete_original_message()

            if custom_id == 'win_close':
                game = database.find_one({'_id': str(inter.author.id)})['game']
                mode = database.find_one({'_id': str(inter.author.id)})['mode']
                embed = disnake.Embed(color = 3092790)
                embed.set_author(name = f"Определить победителя | {inter.guild.name}", icon_url = inter.guild.icon.url)
                embed.description = f"{inter.author.mention}, Выберите победившую команду"
                return await inter.send(embed = embed, view = WinClose())
            
        if custom_id[:3] == 'win':
            await inter.response.defer()

            if custom_id == "win_team_one":
                team = "1"
            if custom_id == "win_team_two":
                team = "2"

            cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'game': "Отсутствует"}}, upsert = True)
            msg_id = database.find_one({'_id': int(inter.author.id)})['msg']
            id_channel = database.find_one({'_id': int(inter.author.id)})['channel']
            channel = self.bot.get_channel(id_channel)
            message = await channel.fetch_message(int(msg_id))
            prize = database.find_one({'_id': str(inter.author.id)})['prize']
            game = database.find_one({'_id': str(inter.author.id)})['game']
            mode = database.find_one({'_id': str(inter.author.id)})['mode']

            attr_name = f"{game}"
            database_stats = getattr(database, attr_name)

            embed = disnake.Embed(color = 3092790, description = f"{inter.author.mention}, **Вы** успешно завершили **CLOSE матч** по игре {game} {mode}")
            embed.set_author(name = "Завершение CLOSE матч", icon_url = inter.guild.icon.url)
            embed.add_field(name = "Выбранная команда", value = f"Команда {team}")
            await inter.message.edit(embed = embed, components = [])

            embed = disnake.Embed(color = disnake.Color(hex_to_rgb("#ffad20")), description = f'Завершился **CLOSE матч** по игре `{game} {mode}`. Победителем стала **Команда {team}**')
            embed.set_author(name = f"Клозы {inter.guild.name}", icon_url = inter.guild.icon.url)
            value = ""
            if team == "1":
                team_win = database.find_one({'_id': int(msg_id)})['team_one']
                team_losers = database.find_one({'_id': int(msg_id)})['team_two']
            else:
                team_win = database.find_one({'_id': int(msg_id)})['team_two']
                team_losers = database.find_one({'_id': int(msg_id)})['team_one']
            for i in range(int(mode[-1])):
                if i < len(team_win):
                    database.users.update_one({"id": str(team_win[i])},{"$inc": {"balance": +int(prize)}})
                    if database_stats.count_documents({"_id": str(team_win[i])}) == 0:
                        database_stats.insert_one({"_id": str(team_win[i]), "wins": 0, "loses": 0})
                    database_stats.update_one({"_id": str(team_win[i])},{"$inc": {"wins": +1}})
                    wins = database_stats.find_one({'_id': str(team_win[i])})['wins']
                    loses = database_stats.find_one({'_id': str(team_win[i])})['loses']
                    total_games = wins + loses
                    try:
                        winrate = (wins / total_games) * 100
                    except:
                        winrate = 0
                    embed1 = disnake.Embed(description = f"Поздравляем с **победой!** Награда в виде **{prize}** 💰 была **разделена** между **победителями**\n\n**Будем ждать вас на следующем close-матче!**", color = 3092790)
                    embed1.set_author(name = f"Клозы {inter.guild.name}", icon_url = inter.guild.icon.url)
                    await disnake.utils.get(inter.guild.members, id = int(team_win[i])).send(embed = embed1)
                    winrate = f"{winrate:.2f}".rstrip("0").rstrip(".")
                    value += f"{i + 1}. <@{int(team_win[i])}> **Винрейт**: <:winrate:1110588767124869130> {winrate}% > **Всего игр {game} {mode}**: <:battle:1110588765128380486> {total_games}\n"
                else:
                    value += f"{i + 1}. Пусто\n"

            for i in range(int(mode[-1])):
                if i < len(team_losers):
                    embed1 = disnake.Embed(description = f"К сожалению **вы проиграли**. **Будем ждать** вас на следующем **close-матче**.", color = 3092790)
                    embed1.set_author(name = f"Клозы {inter.guild.name}", icon_url = inter.guild.icon.url)
                    await disnake.utils.get(inter.guild.members, id = int(team_losers[i])).send(embed = embed1)
                    if database_stats.count_documents({"_id": str(team_losers[i])}) == 0:
                        database_stats.insert_one({"_id": str(team_losers[i]), "wins": 0, "loses": 0})
                    database_stats.update_one({"_id": str(team_losers[i])}, {"$inc": {"loses": +1}})
            try:
                try:
                    for member in database.find_one({'_id': int(msg_id)})['team_one']:
                        await disnake.utils.get(inter.guild.members, id = int(member)).remove_roles(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team1_id']))
                    for member in database.find_one({'_id': int(msg_id)})['team_two']:
                        await disnake.utils.get(inter.guild.members, id = int(member)).remove_roles(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team2_id']))
                except:
                    pass

                category_id = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['category']
                category = disnake.utils.get(inter.guild.categories, id = category_id)
                for channel in category.voice_channels:
                    for member in channel.members:
                        await member.move_to(self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['first_mod_channel_id']))
                    await channel.delete()
                for channel in category.text_channels:
                    await channel.delete()
                await self.bot.get_channel(int(cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['category'])).delete()
            except:
                pass

            embed.add_field(name = f"Победители:", value = f"{value}\nПризовая награда в виде **{prize}** 💰 была разделена между игроками!", inline = False)
            await self.bot.get_channel(1167104883258822726).send(embed = embed)

    @commands.Cog.listener()
    async def on_modal_submit(self, inter):
        custom_id = inter.custom_id
        if custom_id == "ProfileSteamDOTA":
            for key, value in inter.text_values.items():
                id = value

            embed = disnake.Embed(color = 3092790, timestamp = datetime.datetime.utcnow())
            embed.set_author(name = f"Привязка Steam аккаунта", icon_url = inter.guild.icon.url)
            embed.set_footer(text = f"Запросил(а) {inter.author} | ID: {id}", icon_url = inter.author.display_avatar.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            embed.set_footer(text = "Откройте свой Steam профиль для обновления статистики в реальном времени.", icon_url = "https://cdn.discordapp.com/emojis/1074903723106635809.gif?size=96&quality=lossless")
            url = f"https://stratz.com/players/{id}"

            # Отправляем GET-запрос на указанный URL и получаем содержимое страницы
            response = requests.get(url)

            # Проверяем успешность запроса
            if response.status_code == 200:
                # Создаем объект BeautifulSoup для анализа HTML-кода
                soup = BeautifulSoup(response.text, "html.parser")

                # Находим элемент <image>
                image_element = soup.find("image")

                # Если элемент найден, извлекаем значение атрибута href
                if image_element:
                    img_url = image_element.get("href")

                    # Используем регулярное выражение для извлечения числа из строки img_url
                    number_match = re.search(r"medal_(\d+)\.png", img_url)

                    # Если число найдено, сохраняем его в переменной number
                    if number_match:
                        medal_number  = number_match.group(1)
                        match int(medal_number):
                            case 1:
                                rating = "0-610"
                            case 2:
                                rating = "770-1400"
                            case 3:
                                rating = "1540-2150"
                            case 4:
                                rating = "2310-2930"
                            case 5:
                                rating = "3080-3700"
                            case 6:
                                rating = "3850-4460"
                            case 7:
                                rating = "4620-5420"
                            case 8:
                                rating = "Выше 5420"
                            case _:
                                rating = "На калибровке"

                        target_element = soup.find("span", class_="hitagi__sc-41hgfb-1 hHdoEl")
                        if target_element:
                            name = target_element.get_text()
                        else:
                            embed.description = f'* {inter.author.mention}, Не удалось найти никнейм'
                            return await inter.send(embed = embed)
                        cluster.sweetness.steam.update_one({'_id': str(inter.author.id)}, {'$set': {'name': name}}, upsert = True)
                        cluster.sweetness.steam.update_one({'_id': str(inter.author.id)}, {'$set': {'mmr': rating}}, upsert = True)
                        embed.description = f'* {inter.author.mention}, **Вы** успешно привязали стим аккаунт **{name}**!\n Диапазон вашего рейтинга: **{rating}**'
                        await inter.send(embed = embed, ephemeral = True)
                    
                        msg = database.find_one({'_id': int(inter.author.id)})['msg']
                        id_channel = inter.channel.id
                        channel = self.bot.get_channel(id_channel)
                        msg_id = await channel.fetch_message(msg)
                        msg_id_data = database.find_one({'_id': int(msg_id.id)})
                        blacklist = msg_id_data['blacklist']
                        id = msg_id_data['author']
                        lobby_id = msg_id_data['lobby']
                        team_one = msg_id_data['team_one']
                        team_two = msg_id_data['team_two']

                        lobby = self.bot.get_channel(lobby_id)
                        ved = disnake.utils.get(inter.guild.members, id=int(id))
                        game = database.find_one({'_id': str(ved.id)}, {'game': 1})['game']
                        mode = database.find_one({'_id': str(ved.id)}, {'mode': 1})['mode']
                        prize = database.find_one({'_id': str(ved.id)}, {'prize': 1})['prize']

                        if inter.author.id in blacklist:
                            embed = disnake.Embed(description=f"{inter.author.mention}, **Вы** были **исключены** ведущим и теперь вы не можете **принять участие** в этом клозе.", color=disnake.Color(hex_to_rgb("#5a66ea")))
                            embed.set_author(name = f"Запись на клоз {game}", icon_url = inter.guild.icon.url)
                            embed.set_thumbnail(url = inter.author.display_avatar.url)
                            await inter.response.edit_message(embed=embed, components=[])

                        attr_name = f"{game}"
                        database_stats = getattr(database, attr_name)

                        msg_id_data = database.find_one({'_id': int(msg_id.id)})
                        team_one = msg_id_data['team_one']
                        team_two = msg_id_data['team_two']
                        need = int(mode[-1]) * 2
                        all_players = len(team_one) + len(team_two)

                        embed = disnake.Embed(color=disnake.Color(hex_to_rgb("#5a66ea")), description=f'<:ver:1110588762121048084> **Зарегистрировано**: {all_players}/{need}\n<:giftbox:1110588981025972385> **Награда**: {prize} 💰\n<:online:1109846973378470050> Для старта необходимо ещё **{need - all_players}** игроков!')
                        embed.set_author(name = f"CLOSE: {game} | {inter.guild.name}", icon_url = inter.guild.icon.url)
                        embed.set_image(url = "")

                        value = ""
                        for i in range(int(mode[-1])):
                            if i < len(team_one):
                                team_member_id = team_one[i]
                                stats = database_stats.find_one({'_id': str(team_member_id)}, {'wins': 1, 'loses': 1})
                                wins = stats['wins']
                                loses = stats['loses']
                                total_games = wins + loses
                                winrate = (wins / total_games) * 100 if total_games != 0 else 0
                                winrate = f"{winrate:.2f}".rstrip("0").rstrip(".")
                                value += f"{i + 1}. <@{int(team_one[i])}> **Винрейт**: <:winrate:1110588767124869130> {winrate}% > **Всего игр {game} {mode}**: <:battle:1110588765128380486> {total_games}\n"
                            else:
                                value += f"{i + 1}. Пусто\n"
                        embed.add_field(name="Команда 1", value=value, inline=False)

                        value = ""
                        for i in range(int(mode[-1])):
                            if i < len(team_two):
                                team_member_id = team_two[i]
                                database_stats.update_one({'_id': str(team_member_id)}, {'$set': {'loses': 0}}, upsert=True)
                                database_stats.update_one({'_id': str(team_member_id)}, {'$set': {'wins': 0}}, upsert=True)
                                stats = database_stats.find_one({'_id': str(team_member_id)}, {'wins': 1, 'loses': 1})
                                wins = stats['wins']
                                loses = stats['loses']
                                total_games = wins + loses
                                winrate = (wins / total_games) * 100 if total_games != 0 else 0
                                winrate = f"{winrate:.2f}".rstrip("0").rstrip(".")
                                value += f"{i + 1}. <@{int(team_two[i])}> **Винрейт**: <:winrate:1110588767124869130> {winrate}% > **Всего игр {game} {mode}**: <:battle:1110588765128380486> {total_games}\n"
                            else:
                                value += f"{i + 1}. Пусто\n"
                        embed.add_field(name="Команда 2", value=value, inline=False)
                        await msg_id.edit(embed=embed)
                    else:
                        embed.description = f'* {inter.author.mention}, Не удалось число ммр'
                        return await inter.send(embed = embed)
                else:
                    embed.description = f'* {inter.author.mention}, Не удалось найти ммр'
                    return await inter.send(embed = embed)
            else:
                embed.description = f'* {inter.author.mention}, Не удалось аккаунт'
                return await inter.send(embed = embed)


        if custom_id == 'cancel_close':

            for key, value in inter.text_values.items():
                reason = value

            await inter.response.defer()

            msg = database.find_one({'_id': int(inter.author.id)})['msg']
            game = database.find_one({'_id': str(inter.author.id)})['game']
            mode = database.find_one({'_id': str(inter.author.id)})['mode']
            try:
                for member in database.find_one({'_id': int(msg)})['team_one']:
                    embed = disnake.Embed(description = f"CLOSE матч был отменен\nПричина: `{reason}`", color = disnake.Color(hex_to_rgb("#ffad20")))
                    await disnake.utils.get(inter.guild.members, id = int(member)).send(f"CLOSE: {game} {mode} матч был отменен.", embed = embed)
                for member in database.find_one({'_id': int(msg)})['team_two']:
                    embed = disnake.Embed(description = f"CLOSE матч был отменен\nПричина: `{reason}`", color = disnake.Color(hex_to_rgb("#ffad20")))
                    await disnake.utils.get(inter.guild.members, id = int(member)).send(f"CLOSE: {game} {mode} матч был отменен.", embed = embed)
            except:
                pass
            name = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['game']
            cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'game': "Отсутствует"}}, upsert = True)
            try:
                for member in database.find_one({'_id': int(msg)})['team_one']:
                    await disnake.utils.get(inter.guild.members, id = int(member)).remove_roles(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team1_id']))
                for member in database.find_one({'_id': int(msg)})['team_two']:
                    await disnake.utils.get(inter.guild.members, id = int(member)).remove_roles(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team2_id']))
            except:
                pass
            try:
                category_id = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['category']
                category = disnake.utils.get(inter.guild.categories, id = category_id)
                for channel in category.voice_channels:
                    for member in channel.members:
                        await member.move_to(self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['first_mod_channel_id']))
                    await channel.delete()
                for channel in category.text_channels:
                    await channel.delete()
                await self.bot.get_channel(int(cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['category'])).delete()
            except:
                pass

        if custom_id == 'close_edit_prize':
            for key, value in inter.text_values.items():
                target = value
            database.update_one({'_id': str(inter.author.id)}, {'$set': {'prize': int(target)}}, upsert = True)
            game = database.find_one({'_id': str(inter.author.id)})['game']
            mode = database.find_one({'_id': str(inter.author.id)})['mode']
            prize = database.find_one({'_id': str(inter.author.id)})['prize']
            embed = disnake.Embed(color = 3092790, description = f"**Игра**: {game}\n**Режим**: {mode}\n**Награда**: {prize}")
            embed.set_author(name = f"Создание клоза| {inter.guild.name}", icon_url = inter.guild.icon.url)
            await inter.response.edit_message(embed = embed, view = CloseEdit())

        if custom_id == 'id_delete_member':
            for key, value in inter.text_values.items():
                target = value
            member = disnake.utils.get(inter.guild.members, id = int(target))
            try:
                if member.voice and member.voice.channel:
                    await member.move_to(None)
            except:
                pass
            msg = database.find_one({'_id': int(inter.author.id)})['msg']
            try:
                await member.remove_roles(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team1_id']))
                await member.remove_roles(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['team2_id']))
            except:
                pass
            id_channel = database.find_one({'_id': int(inter.author.id)})['channel']
            channel = self.bot.get_channel(id_channel)
            msg_id = await channel.fetch_message(int(msg))
            team_one = database.find_one({'_id': int(msg_id.id)})['team_one']
            team_two = database.find_one({'_id': int(msg_id.id)})['team_two']

            database.update_one({'_id': int(msg_id.id)}, {'$push': {'blacklist': int(target)}}, upsert = True)

            if int(target) in team_one:
                database.update_one({'_id': int(msg_id.id)}, {'$pull': {'team_one': int(target)}}, upsert = True)
            elif int(target) in team_two:
                database.update_one({'_id': int(msg_id.id)}, {'$pull': {'team_two': int(target)}}, upsert = True)
            team_one = database.find_one({'_id': int(msg_id.id)})['team_one']
            team_two = database.find_one({'_id': int(msg_id.id)})['team_two']

            embed = disnake.Embed(description = f"{inter.author.mention}, **Вы** успешно удалили <@{target}> из записи", color = 3092790)
            embed.set_author(name = f"Удалить пользователя из записи на игру", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            await inter.send(embed = embed, ephemeral = True)

            game = database.find_one({'_id': str(inter.author.id)})['game']
            mode = database.find_one({'_id': str(inter.author.id)})['mode']
            prize = database.find_one({'_id': str(inter.author.id)})['prize']
            need = int(mode[-1]) + int(mode[-1])
            all_players = len(team_one) + len(team_two)
            embed = disnake.Embed(color = 3092790, description = f'<:ver:1110588762121048084> **Зарегистрировано**: {all_players}/{need}\n<:giftbox:1110588981025972385> **Награда**: {prize} 💰\n<:online:1109846973378470050> Для старта необходимо ещё **{need - all_players}** игроков!')
            embed.set_author(name = f"CLOSE: {game} | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')
            value = ""
            for i in range(int(mode[-1])):
                if i < len(team_one):
                    value += f"{i + 1}. <@{int(team_one[i])}> **Винрейт**: <:winrate:1110588767124869130> 0% > **Всего игр {game} {mode}**: <:battle:1110588765128380486> 0\n"
                else:
                    value += f"{i + 1}. Пусто\n"
            embed.add_field(name = "Команда 1", value = value, inline = False)
            value = ""
            for i in range(int(mode[-1])):
                if i < len(team_two):
                    value += f"{i + 1}. <@{int(team_two[i])}> **Винрейт**: <:winrate:1110588767124869130> 0% > **Всего игр {game} {mode}**: <:battle:1110588765128380486> 0\n"
                else:
                    value += f"{i + 1}. Пусто\n"
            embed.add_field(name = "Команда 2", value = value, inline = False)
            await msg_id.edit(embed = embed)
            await asyncio.sleep(7)
            await inter.delete_original_message()

    @commands.Cog.listener()
    async def on_dropdown(self, inter):
        custom_id = inter.values[0]
        if custom_id[:12] == 'choice_close':
            if custom_id[:17] == 'choice_close_mode':
                database.update_one({'_id': str(inter.author.id)}, {'$set': {'mode': custom_id[-3:]}}, upsert = True)
            else:
                database.update_one({'_id': str(inter.author.id)}, {'$set': {'game': custom_id[13:]}}, upsert = True)
            game = database.find_one({'_id': str(inter.author.id)})['game']
            mode = database.find_one({'_id': str(inter.author.id)})['mode']
            prize = database.find_one({'_id': str(inter.author.id)})['prize']
            embed = disnake.Embed(color = 3092790, description = f"**Игра**: {game}\n**Режим**: {mode}\n**Награда**: {prize}")
            embed.set_author(name = f"Создание клоза | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_image(url = "")
            await inter.response.edit_message(embed = embed, view = CloseEdit())
        
def setup(bot): 
    bot.add_cog(closebot(bot))