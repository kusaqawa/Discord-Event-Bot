import disnake
import pymongo
import random
import datetime
from disnake.utils import get
from disnake.ext import commands
from disnake.enums import ButtonStyle
from disnake import Localized
from PIL import Image, ImageDraw, ImageFont

min = 60
hour = 60 * 60
day = 60 * 60 * 24

action_author = {}

cluster = pymongo.MongoClient(f"put ur mongo-db link")

cluster1 = pymongo.MongoClient(f"put ur mongo-db link")
files = cluster1.futama.files_event

group = {}

async def wait_for_messages(ctx, embed, *message_prompts):
    responses = []
    
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel
    
    for prompt in message_prompts:
        embed.description = prompt
        await ctx.send(ctx.author.mention, embed=embed)
        
        try:
            response = await ctx.bot.wait_for("message", check=check, timeout=500)
            responses.append(response.content)
        except TimeoutError:
            return None
    
    return responses

class ActionListTopDropdown(disnake.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Выберите категорию",
            custom_id = 'top_staff',
            options = [
                disnake.SelectOption(label="Баллы", value = 'top_staff_balls', description="Топ по баллам", emoji = f'{files.find_one({"_id": "balls"})["emoji_take"]}'),
                disnake.SelectOption(label="Выговоры", value = 'top_staff_warn_staff', description="Топ по выговорам", emoji = f'{files.find_one({"_id": "list"})["emoji_take"]}'),
                disnake.SelectOption(label="Ивенты", value = 'top_events_staff', description="Топ по проведенным ивентам", emoji = f'{files.find_one({"_id": "list"})["emoji_take"]}'),
            ],
        )

class RestNo(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Отклонено', custom_id = 'rest_action_accept', emoji = f'<:zxc3:1009168371213926452>', disabled = True))

class Rest(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.green, label = 'Принять', custom_id = 'rest_action_accept', emoji = f'<:zxc3:1009168371213926452>'))
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Отклонить', custom_id = 'rest_action_cancel', emoji = f'<:zxc2:1009168373936050206>'))

class RestYes(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Принято', custom_id = 'rest_action_accept', emoji = f'<:zxc3:1009168371213926452>', disabled = True))

class ActionListTop(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ActionListTopDropdown())
        self.add_item(disnake.ui.Button(style = ButtonStyle.blurple, label = 'Меню', custom_id = 'back_action', emoji = f'{files.find_one({"_id": "menu"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Отмена', custom_id = 'exit_action', emoji = f'{files.find_one({"_id": "basket"})["emoji_take"]}'))

class ActionBack(disnake.ui.View):
    def __init__(self): 
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.blurple, label = 'Меню', custom_id = 'back_action', emoji = f'{files.find_one({"_id": "menu"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Отмена', custom_id = 'exit_action', emoji = f'{files.find_one({"_id": "basket"})["emoji_take"]}'))

class ActionViewProfile(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.blurple, label = 'Меню', custom_id = 'back_action', emoji = f'{files.find_one({"_id": "menu"})["emoji_take"]}', row = 1))
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Отмена', custom_id = 'exit_action', emoji = f'{files.find_one({"_id": "basket"})["emoji_take"]}', row = 1))

class GiveEventPrizeDropdown(disnake.ui.Select):
    def __init__(self, bot, members):
        self.bot = bot
        options = []
        for member_id in members:
            try:
                member = disnake.utils.get(self.bot.get_guild(1165811916313198632).members, id = int(member_id))
                options.append(disnake.SelectOption(label=f"{member.name}", value = f'{member_id}_group', description="Выдать приз", emoji = f'{files.find_one({"_id": "point"})["emoji_take"]}'))
            except:
                pass

        super().__init__(
            placeholder="Выберите участника",
            options = options,
        )

class GiveEventPrize(disnake.ui.View):
    def __init__(self, bot, members):
        super().__init__()
        self.add_item(GiveEventPrizeDropdown(bot, members))

closemod = 1167104361067974707

event_info = {
    'Пазлы': {
        'prize': 10,
        'embed_description': 'Пазлы -  увлекательный ивент, на котором участникам предстоит включить свои способности: логику и воображение. Вы получите разобранную картинку, которую вам предстоит собрать. В конечном итоге вы получите эстетичную или забавную картинку. Расслабьтесь и получите удовольствие от ивента.',
        'image_url': 'https://media.discordapp.net/attachments/849353889815593030/1134124093059367014/e152c879032df906.png?width=1155&height=629'
    },
    'Соло': {
        'prize': 75,
        'embed_description': 'Одна из самых известных и увлекательных карточных игр. Это игра, где необходимо первым избавиться от всех карт.',
        'image_url': 'https://media.discordapp.net/attachments/849353889815593030/1134124092744798268/5ada99f3b63c857a.png?width=1155&height=629'
    },
    'Цитадели': {
        'prize': 75,
        'embed_description': 'Звание главного строителя королевства – это не только высочайшая честь для тех, кто посвятил свою жизнь возведению зданий, но и немалое количество преференций от монарха. Но чтобы его получить, недостаточно просто строить, возводить прекраснейшие достопримечательности и определять на века внешний вид города.',
        'image_url': 'https://media.discordapp.net/attachments/849353889815593030/1134124094456070225/d6685ce1e0962e64.png?width=1155&height=629'
    },
    'Намёк понят': {
        'prize': 75,
        'embed_description': 'В этой игре вы будете писать подсказки к выбранному слову, чтобы помочь ведущему его угадать. Фишка в том, что каждый пишет свою подсказку, не советуясь с другими. А затем одинаковые подсказки удаляются. И по оставшимся ведущий угадывает слово.',
        'image_url': 'https://media.discordapp.net/attachments/849353889815593030/1134124093822734336/170e0a775d4ec889.png?width=1155&height=629'
    },
    'Угадай мелодию': {
        'prize': 75,
        'embed_description': 'Музыкальная игра, суть которой состоит в угадывании песни или исполнителя по звучащей мелодии.',
        'image_url': 'https://media.discordapp.net/attachments/849353889815593030/1134124093436862605/e32bbfc3560ecf27.png?width=1155&height=629'
    },
    'Jackbox': {
        'prize': 75,
        'embed_description': 'Jackbox — весёлая, аркадная игра для большой компании. Используя свои мобильные устройства и компьютер, вам предстоит сыграть в простенькие незамысловатые игры, в кругу своих друзей.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556151866441861/oie_haMM8Fbu33dq.gif'
    },
    'Своя игра': {
        'prize': 75,
        'embed_description': 'Своя игра - интеллектуальная игра, в которой можно проверить свои знания, соревнуясь с другими игроками. Перед вами есть табло из тем. В каждой категории есть несколько вопросов, которые обычно отличаются ценой. Вы сможете играть с вопросами по общим знаниям: книгам, кино, мультфильмам, аниме, музыке и компьютерным играм.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556152411693167/oie_9b42kAmAfjCN.gif'
    },
    'Сломанный телефон': {
        'prize': 35,
        'embed_description': 'Сломанный телефон — объясняющий меняется каждый ход, за минуту необходимо объяснить как можно больше слов, каждое отгаданное слово даёт одно очко команде. В конце каждого раунда игроки вручную выставляют очки по каждому слову, так что правила засчитывания слов могут быть произвольными.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556153720328282/oie_ro3PpXEIWEeH.gif'
    },
    'Шляпа': {
        'prize': 50,
        'embed_description': 'Шляпа — объясняющий меняется каждый ход, за минуту необходимо объяснить как можно больше слов, каждое отгаданное слово даёт одно очко команде. В конце каждого раунда игроки вручную выставляют очки по каждому слову, так что правила засчитывания слов могут быть произвольными.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556153363800125/oie_797SuGUiDEYe.gif'
    },
    'Codenames': {
        'prize': 50,
        'embed_description': 'Codenames — Минимальное количество человек, требующихся для игры – 4. Мастер команды в свой ход даёт игрокам шифрованный намёк и указывает, сколько слов связаны с ним. Шифр состоит из одного слова и одного числа.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556154471096533/oie_hftVVVUXn50r.gif'
    },
    'Among Us': {
        'prize': 30,
        'embed_description': 'Among us - это игра на подобии мафии, в этой игре мы находимся на космической корабле и становимся группой астронавтов, среди которых есть один или несколько предателей.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556375385084005/am0ngsusxh-53.gif'
    },
    'Мафия': {
        'prize': 150,
        'embed_description': 'Мафия — командная психологическая ролевая игра с детективным сюжетом. Жители города, обессилевшие от разгула мафии, выносят решение пересажать в тюрьму всех мафиози до единого. В ответ мафия объявляет войну до полного уничтожения всех мирных горожан.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556150503284887/oie_oJ2iJZuWOVjG.gif'
    },
    'Бункер': {
        'prize': 100,
        'embed_description': 'Бункер — каждый игрок получает определенные характеристики. Тебе предстоит доказать, что именно ты достоин восстановить жизнь на Земле и войти в число выживших. У каждого игрока две цели:\nЛичная – попасть в бункер, чтобы возрождать планету.\nКомандная — проследить, чтобы в бункер попали только здоровые и пригодные к выживанию люди.',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556150960472074/oie_ru2bUvxDY8Fg.gif'
    },
    'Кто я?': {
        'prize': 75,
        'embed_description': 'Кто я - это простая и весёлая игра на внимательность. Суть игры в том, что тебе нужно отгадать персонажа которого  тебе загадали.',
        'image_url': 'https://media.discordapp.net/attachments/849353889815593030/1134124116081905664/70c55bfb420eb2f2.png?width=1088&height=592'
    },
    'Шпион': {
        'prize': 60,
        'embed_description': 'Шпион - интересная и красочная игра. Попробуйте себя в роли шпиона и угадайте, где скрываются остальные участники! Цель шпиона: не раскрыть себя до окончания раунда или определить локацию, в которой все находятся. Цель участников: единогласно указать на шпиона и разоблачить его.',
        'image_url': 'https://media.discordapp.net/attachments/849353889815593030/1134124115737980938/d1b5b69d0cdfb071.png?width=1088&height=592'
    },
    'Монополия': {
        'prize': 100,
        'embed_description': 'Это игра для тех, кто всегда мечтал стать успешным предпринимателем. Зарабатывай миллионы, собирай монополии, продавай и покупай!',
        'image_url': 'https://cdn.discordapp.com/attachments/1154165500302069760/1155556151405060196/oie_3kv047atadng.gif'
    }
}

class ActionView(disnake.ui.View):
    def __init__(self, member):
        super().__init__()
        checks = [
            {'roles': [1167104361067974707, closemod], 'label': 'Профиль', 'custom_id': "profile_action", 'emoji': f'{files.find_one({"_id": "user"})["emoji_take"]}', 'row': 0},
            {'roles': [1167104361067974707, closemod], 'label': 'Топы', 'custom_id': "places_action", 'emoji': f'{files.find_one({"_id": "trophy"})["emoji_take"]}', 'row': 0},
            {'roles': [1167104361067974707, closemod], 'label': 'Отпуск', 'custom_id': "rest_action", 'emoji': f'{files.find_one({"_id": "rest"})["emoji_take"]}', 'row': 0},
            {'roles': [1167104361067974707, closemod], 'label': 'Выговор', 'custom_id': "warn_staff_action", 'emoji': f'{files.find_one({"_id": "staff_warn"})["emoji_take"]}', 'row': 1},
            {'roles': [1167104361067974707, closemod], 'label': 'Выговоры', 'custom_id': "warns_action", 'emoji': f'{files.find_one({"_id": "list"})["emoji_take"]}', 'row': 1},
            {'roles': [1167104361067974707], 'label': 'Настроить', 'custom_id': "settings_action", 'emoji': f'{files.find_one({"_id": "basket"})["emoji_take"]}', 'row': 1},
            {'roles': [1167104361067974707, closemod], 'label': 'Отмена', 'custom_id': "exit_action", 'emoji': f'{files.find_one({"_id": "basket"})["emoji_take"]}', 'row': 1},
        ]

        roles_member = [role.id for role in member.roles]

        for check in checks:
            if any(role_id in roles_member for role_id in check['roles']):
                button = disnake.ui.Button(style=disnake.ButtonStyle.gray, label=check['label'], custom_id=check["custom_id"], emoji=check['emoji'], row=check['row'])
            else:
                button = disnake.ui.Button(style=disnake.ButtonStyle.gray, label=check['label'], custom_id=check["custom_id"], emoji=check['emoji'], row=check['row'], disabled = True)
            
            self.add_item(button)


class EventProfile(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Мероприятия", custom_id = "list_activity", emoji = f'{files.find_one({"_id": "events"})["emoji_take"]}'))

class InviteLink(disnake.ui.View):
    def __init__(self, invite_url):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Мероприятия", custom_id = "list_activity", emoji = f'{files.find_one({"_id": "events"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Присоединиться", emoji = f'{files.find_one({"_id": "game"})["emoji_take"]}', url = invite_url))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Отправить жалобу", custom_id = "report_activity", emoji = f'{files.find_one({"_id": "report"})["emoji_take"]}'))

class ChoiceChat(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Открыть", custom_id = 'open_chat_event', emoji = f'{files.find_one({"_id": "plus"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Закрыть", custom_id = 'close_chat_event', emoji = f'{files.find_one({"_id": "minus"})["emoji_take"]}'))

class ChoiceVoice(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Открыть", custom_id = 'open_voice_event', emoji = f'{files.find_one({"_id": "plus"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Закрыть", custom_id = 'close_voice_event', emoji = f'{files.find_one({"_id": "minus"})["emoji_take"]}'))

class ChoiceMute(disnake.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Замутить", custom_id = 'mute_event', emoji = f'{files.find_one({"_id": "plus"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Размутить", custom_id = 'unmute_event', emoji = f'{files.find_one({"_id": "minus"})["emoji_take"]}'))

class YesOrno(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Принять", custom_id = 'accept_balance', emoji = f'{files.find_one({"_id": "accept"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = disnake.ButtonStyle.secondary, label = "Отклонить", custom_id = 'decline_balance', emoji = f'{files.find_one({"_id": "decline"})["emoji_take"]}'))

class ManageEvent(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Закончить ивент', custom_id = 'cancel_event', emoji = f'{files.find_one({"_id": "one"})["emoji_take"]}', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Открыть/Закрыть чат', custom_id = 'chat_event', emoji = f'{files.find_one({"_id": "two"})["emoji_take"]}', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Открыть/Закрыть войс', custom_id = 'voice_event', emoji = f'{files.find_one({"_id": "three"})["emoji_take"]}', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Отключить/Включить микро', custom_id = 'microphone_event', emoji = f'{files.find_one({"_id": "four"})["emoji_take"]}', row = 0))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Выгнать человека из комнаты', custom_id = 'member_event', emoji = f'{files.find_one({"_id": "five"})["emoji_take"]}', row = 1))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Выдать Ивент бан', custom_id = 'ban_event', emoji = f'{files.find_one({"_id": "six"})["emoji_take"]}', row = 1))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Передать ивент', custom_id='give_event', emoji=f'{files.find_one({"_id": "seven"})["emoji_take"]}', row=1))
        self.add_item(disnake.ui.Button(style = ButtonStyle.gray, label = 'Выдать призы', custom_id = 'prize_event', emoji = f'{files.find_one({"_id": "eight"})["emoji_take"]}', row = 1))

class ActionMuteBan(disnake.ui.View):
    def __init__(self): 
        super().__init__()
        self.add_item(disnake.ui.Button(style = ButtonStyle.secondary, label = 'Выдать бан', custom_id = "ban_give_event", emoji = f'{files.find_one({"_id": "plus"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = ButtonStyle.secondary, label = 'Снять бан', custom_id = "ban_snyat_event", emoji = f'{files.find_one({"_id": "minus"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = ButtonStyle.blurple, label = 'Меню', custom_id = 'back_action', emoji = f'{files.find_one({"_id": "menu"})["emoji_take"]}'))
        self.add_item(disnake.ui.Button(style = ButtonStyle.red, label = 'Отмена', custom_id = 'exit_action', emoji = f'{files.find_one({"_id": "basket"})["emoji_take"]}'))

class eventbot(commands.Cog):
    def __init__(self, bot: commands.Bot(intents = disnake.Intents.all(), command_prefix = 'event!')):
        self.bot = bot

    @commands.slash_command(description = 'Запустить ивент')
    @commands.has_any_role(1167104361067974707)
    async def event(self, inter, ивент: str = commands.Param(choices=[
        Localized("Jackbox", key="1"), 
        Localized("Своя игра", key="2"),
        Localized("Сломанный телефон", key="4"),
        Localized("Шляпа", key="5"),
        Localized("Codenames", key="6"),
        Localized("Among Us", key="7"),
        Localized("Мафия", key="9"),
        Localized("Бункер", key="10"),
        Localized("Крокодил", key="11"),
        Localized("Кто я?", key="13"),
        Localized("Шпион", key="14"),
        Localized("Монополия", key="15"),
        Localized("Цитадели", key="16"),
        Localized("Намёк понят", key="17"),
        Localized("Угадай мелодию", key="21"),
        Localized("Пазлы", key="22"),
        Localized("Соло", key="23"),
        ])):

        if cluster.sweetness.closemod.count_documents({"_id": str(inter.author.id)}) == 0:
            cluster.sweetness.closemod.insert_one({"_id": str(inter.author.id), "game": "Отсутствует", "category": 0, "voice_channel": 0, "text_channel": 0})
        if cluster.sweetness.event_balls.count_documents({"_id": str(inter.author.id)}) == 0:
            cluster.sweetness.event_balls.insert_one({"_id": str(inter.author.id), "event_count": 0, "balls": 0})
            
        cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'game': "Отсутствует"}}, upsert = True)
        game = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['game']
        
        if not game == 'Отсутствует':
            embed = disnake.Embed(color = 3092790, description = f"{inter.author.mention}, **Вы** не можете запустить **ещё один ивент**, вам нужно **закончить предыдущий**!")
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            embed.set_author(name = f"Event - {ивент}", icon_url = inter.guild.icon.url)
            return await inter.send(ephemeral = True, embed = embed)
        
        cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'game': ивент}}, upsert = True)

        await inter.response.defer()

        MainCategory = await inter.guild.create_category(f"───・{ивент}")
        edit_channel = await inter.guild.create_text_channel(name = "💻・Управление", category = MainCategory)
        await edit_channel.set_permissions(inter.guild.default_role, view_channel = False)
        await edit_channel.set_permissions(inter.author, view_channel = True)
        manage = disnake.Embed(color = 3092790)
        manage.set_author(name = f"Управление ивентом ─ {ивент}", icon_url = inter.guild.icon.url)
        manage.description = f'* {files.find_one({"_id": "one"})["emoji_take"]} - Закончить ивент\n* {files.find_one({"_id": "two"})["emoji_take"]} - Открыть/Закрыть чат\n* {files.find_one({"_id": "three"})["emoji_take"]} - \
        Открыть/Закрыть войс\n* {files.find_one({"_id": "four"})["emoji_take"]} - Отключить/Включить микро\n* {files.find_one({"_id": "five"})["emoji_take"]} - Выгнать человека из комнаты \
        \n* {files.find_one({"_id": "six"})["emoji_take"]} - Выдать Ивент бан\n{files.find_one({"_id": "seven"})["emoji_take"]} - Передать ивент\n{files.find_one({"_id": "eight"})["emoji_take"]} - Выдать призы'
        await edit_channel.send(inter.author.mention, embed = manage, view = ManageEvent())

        channel = disnake.utils.get(inter.guild.categories, id = cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['category_id'])
        channelxd = channel.position

        await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['unverify_id']), view_channel = False) #unverify
        await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['nedo_id']), view_channel = False) #не допуск
        await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['localban_id']), view_channel = False) #local ban
        await MainCategory.set_permissions(inter.guild.get_role(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['closeban_id']), connect = False) # event ban
        await MainCategory.edit(position = int(channelxd))

        channel123 = await inter.guild.create_voice_channel(name = f"🔷・{ивент}", category = MainCategory)
        channel12 = await inter.guild.create_text_channel(name = f"🔹・{ивент}", category = MainCategory)
        cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'text_channel': channel12.id}}, upsert = True)
        cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'voice_channel': channel123.id}}, upsert = True)
        cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'manage': edit_channel.id}}, upsert = True)

        invitelink = await channel123.create_invite(max_uses = 99)
        invite_url = invitelink.url

        input = datetime.datetime.now()
        data = int(input.timestamp())
        event_data = event_info[ивент]

        image = disnake.Embed(color = 3092790)
        image.set_image(url = event_data['image_url'])

        embed = disnake.Embed(color = 3092790)
        embed.add_field(name = f"<:tribune:1142846971032371331> Ведущий", value = f"{inter.author.mention}")
        embed.set_author(name = f"Event - {ивент}", icon_url = inter.guild.icon.url)
        embed.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')
        embed.description = event_data["embed_description"]
        embed.add_field(name = f"<:date1:1139169091840655421> Начало ивента", value = f'<t:{data}:F>')
        message = await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['news_channel_id']).send(embeds = [image, embed], view = InviteLink(invite_url))

        cluster.sweetness.event_list.insert_one({"_id": str(f"{ивент} #{random.randint(1, 1000)}"), 'start': f"<t:{data}:F>", 'category': int(MainCategory.id), 'invitelink': invite_url, 'host': int(inter.author.id), 'prize': event_data['prize']})
        cluster.sweetness.event_report.insert_one({"_id": str(message.id), 'game': f"{ивент}", 'start': f"<t:{data}:F>", 'category': int(MainCategory.id), 'invitelink': invite_url, 'host': int(inter.author.id), 'prize': event_data['prize']})
    
        cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'category': MainCategory.id}}, upsert = True)
        cluster.sweetness.closemod.update_one({'_id': str(inter.author.id)}, {'$set': {'time': f"<t:{data}:F>"}}, upsert = True)

        embed3 = disnake.Embed(color = 3092790, description = f"> Ведущий: {inter.author.mention} | ID: {inter.author.id}> Название: {ивент}\n> Текстовый канал: <#{channel12.id}>\n> Войс канал: <#{channel123.id}>\n \
                               > Категория: <#{MainCategory.id}>")
        embed3.set_author(name = f"Начал ивент - {inter.author} ", icon_url = inter.guild.icon.url)
        embed3.set_thumbnail(url = inter.author.display_avatar.url)
        await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['logs_channel_id']).send(embed = embed3)
    
        embed.set_thumbnail(url = inter.author.avatar.url)
        embed.description = f'{inter.author.mention}, **Вы** успешно **запустили ивент** {ивент}!'
        await inter.send(embed = embed)

        cluster.sweetness.event_balls.update_one({"_id": str(inter.author.id)}, {"$inc": {"event_count": +1}})
        cluster.sweetness.event_balls.update_one({"_id": str(inter.author.id)}, {"$inc": {"balls": +3}})

    @event.error
    async def event_error(self, inter, error):
        if isinstance(error, commands.MissingAnyRole):
            embed = disnake.Embed(description = f'{inter.author.mention}, У **Вас** нет на это **разрешения**!', color = disnake.Color.red())
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            embed.set_author(name = f"Начал ивент - {inter.author} ", icon_url = inter.guild.icon.url)
            await inter.send(embed = embed)
        else:
            print(error)

    @commands.slash_command(description="Панель ивентёра")
    async def event_action(self, inter, пользователь: disnake.Member):
        if cluster.sweetness.history_punishment.count_documents({"_id": str(пользователь.id)}) == 0: 
            cluster.sweetness.history_punishment.insert_one({"_id": str(пользователь.id), "warns": 0, "mutes": 0, "bans": 0, "eventban": 0})

        action_author[inter.author.id] = пользователь.id

        if cluster.sweetness.rest.count_documents({"_id": str(пользователь.id)}) == 0: 
            cluster.sweetness.rest.insert_one({"_id": str(пользователь.id), "rest": 'Не активен'})

        if not cluster.sweetness.rest_count.count_documents({"_id": str(пользователь.id)}) == 0:
            rest_dates = cluster.sweetness.rest_count.find_one({'_id': str(пользователь.id)})['data']
            rest_data = max(rest_dates)

        rest = cluster.sweetness.rest.find_one({'_id': str(пользователь.id)})['rest']
        try:
            embed = disnake.Embed(
                color = 3092790,
                description = f"<:user:1135270525711691908> `Пользователь`: {пользователь.mention} | ID: {пользователь.id}\n<:warn_staff:1138812844457087027> `Варны`: [{cluster.sweetness.history_punishment.find_one({'_id': str(пользователь.id)})['warns']}/3] \
                \n<:rest1:1142784634158071889> `Отпуск:` {rest} (Заканчивается: {rest_data})",
            ).set_thumbnail(url = пользователь.display_avatar.url)
            embed.set_author(name = f"Панель ивентёра | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')
        except:
            embed = disnake.Embed(
                color = 3092790,
                description = f"<:user:1135270525711691908> `Пользователь`: {пользователь.mention} | ID: {пользователь.id}\n<:warn_staff:1138812844457087027> `Варны`: [{cluster.sweetness.history_punishment.find_one({'_id': str(пользователь.id)})['warns']}/3] \
                \n<:rest1:1142784634158071889> `Отпуск:` {rest}",
            ).set_thumbnail(url = пользователь.display_avatar.url)
            embed.set_author(name = f"Панель ивентёра | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_image(url = 'https://i.ibb.co/rfRcJgc/bg23232.png')

        await inter.send(inter.author.mention, embed = embed, view=ActionView(inter.author))

    @commands.Cog.listener()
    async def on_dropdown(self, inter):
        custom_id = inter.values[0]

        if custom_id[-5:] == 'group':
            try:
                group[inter.author.id] = int(custom_id[:19])
            except:
                group[inter.author.id] = int(custom_id[:18])
            await inter.response.send_modal(title=f"Выдать валюту {group[inter.author.id]}", custom_id = "money_event",
                                            components=[disnake.ui.TextInput(label="Количество", placeholder = "Введите количество",custom_id = "Количество", style = disnake.TextInputStyle.short, max_length = 4)])

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        custom_id = inter.component.custom_id

        if custom_id == "settings_action":
            embed = disnake.Embed(color = 3092790)
            embed.set_author(name = f"Настроить ивенты, клозы | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)

            responses = await wait_for_messages(inter, embed,
                "Введите айди роли команда 1:",
                "Введите айди роли команда 2:",
                "Введите айди unverify роли:",
                "Введите айди недопуска роли:",
                "Введите айди localban роли:",
                "Введите айди closeban роли:",
                "Введите айди новостного канала с ивентами и клозами:",
                "Введите айди категории сверху которой будет ивент создаваться:",
                "Введите айди канала ивент логов:",
                "Введите айди канала для репортов, где будут упоминаться админы:",
                "Введите айди категории для репортов:",
                "Введите айди канала для взятия отдыха:",
                "Введите айди канала для наград:",
                "Введите айди канала для логов банов:",
                "Введите айди первой модерационной комнаты (войс):"  # Добавил эту строку
            )

            if responses is None:
                return  # Обработка случая, когда произошел TimeoutError

            team1_id, team2_id, unverify_id, nedo_id, localban_id, closeban_id, news_channel_id, category_id, logs_channel_id, report_channel_id, report_category_id, rest_logs_id, award_channel_id, logs_ban_channel_id, first_mod_channel_id = responses

            data_to_insert = {
                "team1_id": int(team1_id),
                "team2_id": int(team2_id),
                "unverify_id": int(unverify_id),
                "nedo_id": int(nedo_id),
                "localban_id": int(localban_id),
                "closeban_id": int(closeban_id),
                "news_channel_id": int(news_channel_id),
                "category_id": int(category_id),
                "logs_channel_id": int(logs_channel_id),
                "report_channel_id": int(report_channel_id),
                "report_category_id": int(report_category_id),
                "rest_logs_id": int(rest_logs_id),
                "award_channel_id": int(award_channel_id),
                "logs_ban_channel_id": int(logs_ban_channel_id),
                "first_mod_channel_id": int(first_mod_channel_id)
            }

            # Выполните операцию обновления с использованием $set
            cluster.sweetness.system.update_one({"_id": str(inter.guild.id)}, {"$set": data_to_insert}, upsert=True)

            embed.description = f"{inter.author.mention}, Вы **Успешно** поставили все айди ролей и каналов для ивентов и клозов"
            return await inter.send(content = inter.author.mention, embed = embed)

        if custom_id[-7:] == 'balance':
            if custom_id == 'accept_balance':
                member = cluster.sweetness.closemod.find_one({'_id': str(inter.message.id)})['member']
                count = cluster.sweetness.closemod.find_one({'_id': str(inter.message.id)})['number']
                cluster.sweetness.economy.update_one({"_id": str(member)}, {"$inc": {"balance": +int(count)}})
                return await inter.response.edit_message(f"{inter.author.mention}, **Вы** успешно выдали {count} <@{member}>", components = [])
            if custom_id == 'decline_balance':
                return await inter.response.edit_message(f"{inter.author.mention}, **ОТМЕНИЛ ЭТУ ТРАНЗАКЦИЮ**", components = [])

        if custom_id[:9] == 'top_staff':
            embed = disnake.Embed(color = 3092790)
            embed.set_author(name = f"Топ ивентеров | {inter.guild.name}", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            if not inter.message.content == inter.author.mention:
                embed.description = f'{inter.author.mention}, **Вы** не можете использовать **чужие кнопки!**'
                return await inter.send(ephemeral = True, embed = embed)

            idd = 1
            description = ''
            if custom_id == 'top_staff_balls':
                top = "Баллам"
                database = cluster.sweetness.event_balls
                received = "balls"
                input = database.find().sort("balls", -1)
                emoji = "<:point:1111689853114003516>"

            if custom_id == 'top_staff_warn_staff':
                top = "Выговорам"
                database = cluster.sweetness.event_modwarn
                received = "warn"
                input = database.find().sort("warns", -1)
                emoji = "<:staff_warn:1111701662097227858>"

            if custom_id == 'top_events_staff':
                top = "Ивентам"
                database = cluster.sweetness.event_balls
                received = "event_count"
                input = database.find().sort("event_count", -1)
                emoji = "<:point:1111689853114003516>"

            for x in input:
                if top == "Голосовому онлайну":
                    N = cluster.sweetness.online_staff.find_one({'_id': str(x['_id'])})['mod']
                    output = f"**{N // hour}**ч. **{(N - (N // hour * hour)) // 60}**м."
                else:
                    output = database.find_one({'_id': str(x['_id'])})[f'{received}']
                match idd:
                    case 1:
                        description += f"**<:1_:1080872684092657714> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 2:
                        description += f"**<:2_:1080872682779856917> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 3:
                        description += f"**<:3_:1080872680452005958> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 4:
                        description += f"**<:4_:1080872678455525497> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 5:
                        description += f"**<:5_:1080872676018638868> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 6:
                        description += f"**<:6_:1080872674735161474> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 7:
                        description += f"**<:7_:1080872673376215160> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 8:
                        description += f"**<:8_:1080872671190990918> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 9:
                        description += f"**<:9_:1080872669215461427> — <@{x['_id']}>** {emoji} {output}\n\n"
                    case 10:
                        description += f"**<:10:1080872666887634974> — <@{x['_id']}>** {emoji} {output}\n\n"
                idd += 1
                if idd > 10:
                    break

            embed.description = description
            embed.set_author(name = f"Топ ивентеров по {top}| {inter.guild.name}")
            return await inter.response.edit_message(embed = embed, view = ActionListTop())

        if custom_id == "rest_action_accept":
            id_member = cluster.sweetness.rest.find_one({'_id': str(inter.message.id)})['author']
            time = cluster.sweetness.rest.find_one({'_id': str(inter.message.id)})['time']
            cluster.sweetness.rest.update_one({'_id': str(id_member)}, {'$set': {'rest': 'Активен'}}, upsert = True)

            new_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(days=int(time))
            cluster.sweetness.rest.update_one({'_id': str(id_member)}, {'$set': {'time': time}}, upsert=True)
            cluster.sweetness.rest.update_one({'_id': str(id_member)}, {'$set': {'days': new_date}}, upsert=True)

            cluster.sweetness.rest_count.update_one({"_id": str(id_member)}, {"$push": {"data": f"<t:{new_date}:F>"}})
            
            member = disnake.utils.get(inter.guild.members, id = int(id_member))

            embed = disnake.Embed(description = f"{member.mention}, {inter.author.mention} `одобрил вам отпуск`", color = disnake.Color.green())
            embed.set_author(name = "Отпуск", icon_url = inter.guild.icon.url)
            embed.add_field(name = '> <:online:1109846973378470050> Время', value = f"```yaml\n{time} дней```")
            embed.set_thumbnail(url = member.display_avatar.url)
            await member.send(embed = embed)

            embed = disnake.Embed(description = f"{inter.author.mention}, **одобрил отпуск** {member.mention}", color = disnake.Color.green())
            embed.set_author(name = f"Взять отпуск {member.name}", icon_url = inter.guild.icon.url)
            embed.add_field(name = '> <:online:1109846973378470050> Время', value = f"```yaml\n{time} дней```")
            embed.set_thumbnail(url = member.display_avatar.url)
            await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['rest_logs_id']).send(embed = embed)

            return await inter.response.edit_message(content = f"{inter.author.mention} одобрил отпуск {member.mention}", view = RestYes())

        if custom_id == "rest_action_cancel":
            id_member = cluster.sweetness.rest.find_one({'_id': str(inter.message.id)})['author']
            time = cluster.sweetness.rest.find_one({'_id': str(inter.message.id)})['time']

            member = disnake.utils.get(inter.guild.members, id = int(id_member))
            
            embed = disnake.Embed(description = f"{member.mention}, {inter.author.mention} `отклонил вам отпуск`", color = disnake.Color.red())
            embed.set_author(name = "Отпуск", icon_url = inter.guild.icon.url)
            embed.add_field(name = '> <:online:1109846973378470050> Время', value = f"```yaml\n{time} дней```")
            embed.set_thumbnail(url = member.display_avatar.url)
            await member.send(embed = embed)

            return await inter.response.edit_message(content = f"{inter.author.mention} отклонил отпуск {member.mention}", view = RestNo())

        if custom_id.endswith("action"):
            embed = disnake.Embed(description = f'{inter.author.mention}, **Вы** не можете использовать **чужие кнопки!**', color = 3092790)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            if not inter.message.content == inter.author.mention:
                embed.description = f'{inter.author.mention}, **Вы** не можете использовать **чужие кнопки!**'
                return await inter.send(ephemeral = True, embed = embed)
            пользователь = disnake.utils.get(inter.guild.members, id = int(action_author[inter.author.id]))

            if custom_id == "profile_action":
                if cluster.sweetness.online_event.count_documents({"_id": str(пользователь.id)}) == 0: 
                    cluster.sweetness.online_event.insert_one({"_id": str(пользователь.id), "online": 0})
                if cluster.sweetness.event_balls.count_documents({"_id": str(пользователь.id)}) == 0:
                    cluster.sweetness.event_balls.insert_one({"_id": str(пользователь.id), "event_count": 0, "balls": 0})
                if cluster.sweetness.event_modwarn.count_documents({"_id": str(пользователь.id)}) == 0: 
                    cluster.sweetness.event_modwarn.insert_one({"_id": str(пользователь.id), "warn": 0, "warns": []})
                if cluster.sweetness.rest.count_documents({"_id": str(пользователь.id)}) == 0: 
                    cluster.sweetness.rest.insert_one({"_id": str(пользователь.id), "rest": 'Не активен'})
                if cluster.sweetness.event_help.count_documents({"_id": str(пользователь.id)}) == 0:
                    cluster.sweetness.event_help.insert_one({"_id": str(пользователь.id), "help": 0})

                result = cluster.sweetness.event_balls.find_one({"_id": str(пользователь.id)})
                time = cluster.sweetness.online_event.find_one({'_id': str(пользователь.id)})['online']
                rest_count = 0
                point = "<:to4kaaa:948159896979922966>"
                
                love_event = "Неизвестно"

                if int(cluster.sweetness.event_balls.find_one({'_id': str(пользователь.id)})['event_count']) > 0:
                    user_document = cluster.sweetness.events.find_one({"_id": str(пользователь.id)})

                    if user_document:
                        event_counts = {key: int(value) for key, value in user_document.items() if key != "_id"}

                        if event_counts:
                            max_event_name = max(event_counts, key=event_counts.get)
                            max_event_count = event_counts[max_event_name]

                            love_event = max_event_name

                else:
                    love_event = "Неизвестно"

                embed = disnake.Embed(color = 3092790)
                embed.set_author(name = f"Профиль ивентёра {пользователь}", icon_url = inter.guild.icon.url)
                embed.add_field(name = f'> {point} Войс актив', value = f'```{time // hour}ч. {(time - (time // hour * hour)) // 60}м.```')
                embed.add_field(name = f'> {point} Выговоры', value = f'```{cluster.sweetness.event_modwarn.find_one({"_id": str(пользователь.id)})["warn"]}/3```')
                embed.add_field(name = f'> {point} Помощь', value = f'```{cluster.sweetness.event_help.find_one({"_id": str(пользователь.id)})["help"]}```')

                embed.add_field(name = f'> {point} Ивенты за неделю', value = f'```{result["event_count"]}```')
                embed.add_field(name = f'> {point} Отпуск', value = f"```🌴 {cluster.sweetness.rest.find_one({'_id': str(пользователь.id)})['rest']}\nВзято: {rest_count} раз.```")
                embed.add_field(name = f'> {point} Любимый ивент', value = f"```{love_event}```")

                embed.set_footer(text = f"Количество баллов {result['balls']}", icon_url = "https://cdn.discordapp.com/attachments/1125009710446288926/1142551859282841760/achiev_1.png")
                embed.set_thumbnail(url = пользователь.display_avatar.url)
                return await inter.response.edit_message(embed = embed, view = ActionViewProfile())

            if custom_id == "places_action":
                embed.description = f'{inter.author.mention}, **Выберите** топ, который вы хотите посмотреть'
                embed.set_thumbnail(url = inter.author.display_avatar.url)
                await inter.response.edit_message(embed = embed, view = ActionListTop())
            if custom_id == "rest_action":
 
                if cluster.sweetness.rest.count_documents({"_id": str(inter.author.id)}) == 0: 
                    cluster.sweetness.rest.insert_one({"_id": str(inter.author.id), "rest": 'Не активен'})

                cluster.sweetness.reportcount.update_one({"_id": str(inter.author.id)}, {"$inc": {"report_count": +1}})

                if cluster.sweetness.rest.find_one({'_id': str(inter.author.id)})['rest'] == 'Активен':

                    await inter.response.send_modal(title = "Снять отпуск",custom_id = "unrest",components=[
                        disnake.ui.TextInput(label="Причина",placeholder="Например: Освободился пораньше",custom_id = "Причина отпуска",style=disnake.TextInputStyle.short,max_length=50)])
                    modal_inter: disnake.ModalInteraction = await self.bot.wait_for("modal_submit", check=lambda i: i.custom_id == "unrest" and i.author.id == inter.author.id)

                    for key, value in modal_inter.text_values.items():
                        reason = value

                    cluster.sweetness.rest.delete_one({'_id': str(inter.author.id)})

                    embed = disnake.Embed(description = f'{inter.author.mention}, **Вы** успешно отменили отпуск **досрочно**', color = disnake.Color.red())
                    embed.set_author(name = "Отпуск", icon_url = inter.guild.icon.url)
                    embed.set_thumbnail(url = inter.author.display_avatar.url)
                    await modal_inter.response.edit_message(embed = embed, view = ActionBack())

                    embed = disnake.Embed(description = f"{inter.author.mention} | {inter.author.name} | **ID:** {inter.author.id} `снял отпуск досрочно`", color = disnake.Color.red())
                    embed.set_author(name = "Отпуск", icon_url = inter.guild.icon.url)
                    embed.add_field(name = '> ・Причина', value = f"```diff\n- {reason}```")
                    embed.set_thumbnail(url = inter.author.display_avatar.url)
                    return await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['rest_logs_id']).send(embed = embed)

                await inter.response.send_modal(title = "Взять отпуск", custom_id = "rest", components=[
                    disnake.ui.TextInput(label="Причина",placeholder="Например: Уезжаю в другой город",custom_id = "Причина отпуска",style=disnake.TextInputStyle.short,max_length=50),
                    disnake.ui.TextInput(label="🕖 Время отпуска",placeholder="Например: 1д или 1d", custom_id = "Время отпуска",style=disnake.TextInputStyle.short,min_length=1, max_length=3)])
            if custom_id == "warn_staff_action":
                await inter.response.send_modal(title = "Выдать выговор", custom_id = "vidat_warn", components = [
                    disnake.ui.TextInput(label="Причина",placeholder="Например: Плохо работал",custom_id = "Причина выговора",style=disnake.TextInputStyle.short, max_length=50)])
            if custom_id == "warns_action":
                if cluster.sweetness.event_modwarn.count_documents({"_id": str(пользователь.id)}) == 0: 
                    cluster.sweetness.event_modwarn.insert_one({"_id": str(пользователь.id), "warn": 0, "warns": []})

                if cluster.sweetness.event_modwarn.find_one({'_id': str(пользователь.id)})['warns'] == []:
                    embed = disnake.Embed(title = f'История выговоров {пользователь}', description = f"{пользователь.mention}, у **{пользователь.mention}** нету **выговоров**", color = 3092790)
                    embed.set_thumbnail(url = пользователь.display_avatar.url)
                    return await inter.response.edit_message(embed = embed, view = ActionBack())

                embed = disnake.Embed(title = f'История выговоров {пользователь}', description = f"{''.join(cluster.sweetness.event_modwarn.find_one({'_id': str(пользователь.id)})['warns'])}", color = 3092790)
                embed.set_thumbnail(url = пользователь.display_avatar.url)
                await inter.response.edit_message(embed = embed, view = ActionBack())
            if custom_id == "back_action":

                if not cluster.sweetness.rest_count.count_documents({"_id": str(пользователь.id)}) == 0:
                    rest_dates = cluster.sweetness.rest_count.find_one({'_id': str(пользователь.id)})['data']
                    rest_data = max(rest_dates)

                rest = cluster.sweetness.rest.find_one({'_id': str(пользователь.id)})['rest']
                try:
                    embed = disnake.Embed(
                        color = 3092790,
                        description = f"<:user:1135270525711691908> `Пользователь`: {пользователь.mention}\n<:warn_staff:1138812844457087027> `Варны`: [{cluster.sweetness.history_punishment.find_one({'_id': str(пользователь.id)})['warns']}/3] \
                        \n<:rest1:1142784634158071889> `Отпуск:` {rest} (Заканчивается: {rest_data})",
                    ).set_thumbnail(url = пользователь.display_avatar.url)
                    embed.set_author(name = f"Панель ивентёра | {inter.guild.name}", icon_url = inter.guild.icon.url)
                except:
                    embed = disnake.Embed(
                        color = 3092790,
                        description = f"<:user:1135270525711691908> `Пользователь`: {пользователь.mention}\n<:warn_staff:1138812844457087027> `Варны`: [{cluster.sweetness.history_punishment.find_one({'_id': str(пользователь.id)})['warns']}/3] \
                        \n<:rest1:1142784634158071889> `Отпуск:` {rest}",
                    ).set_thumbnail(url = пользователь.display_avatar.url)
                    embed.set_author(name = f"Панель ивентёра | {inter.guild.name}", icon_url = inter.guild.icon.url)

                await inter.response.edit_message(embed = embed, view=ActionView(inter.author))

            if custom_id == "exit_action":
                return await inter.message.delete()
        if custom_id[-5:] == 'event':
            embed = disnake.Embed(color = 3092790)
            embed.set_author(name = "Управление ивентом", icon_url = inter.guild.icon.url)
            embed.set_thumbnail(url = inter.author.avatar.url)

            if custom_id == 'cancel_event':
                time = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['time']
                try:
                    members = cluster.sweetness.event_members.find_one({'_id': str(inter.author.id)})['members']
                except:
                    embed.description = f"{inter.author.mention}, **Вы** не выдали награды!"
                    return await inter.send(ephemeral = True, embed = embed, components = [])
                game = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['game']
                embed.set_author(name = f"Event Logs | {inter.guild.name}", icon_url = inter.guild.icon.url)

                input = datetime.datetime.now()
                data = int(input.timestamp())

                embed.description = f"> Ведущий: {inter.author.mention} | ID: {inter.author.id}\n> Время: от {time} до <t:{data}:F>\n> Участвовало людей: {len(members)}\n> Ивент: {game}"
                await inter.response.edit_message(embed = embed, components = [])

                try:
                    fff = cluster.sweetness.events.find_one({'_id': str(inter.author.id)})[f'{game}']
                    cluster.sweetness.events.update_one({"_id": str(inter.author.id)}, {"$inc": {f"{game}": +1}})
                except:
                    cluster.sweetness.events.update_one({'_id': str(inter.author.id)}, {'$set': {f'{game}': 1}}, upsert = True)

                await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['logs_channel_id']).send(embed = embed)
                
                cluster.sweetness.economy.update_one({"_id": str(inter.author.id)}, {"$inc": {"balance": +int(250)}})

                category = disnake.utils.get(inter.guild.categories, id = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['category'])
                for channel in category.voice_channels:
                    try:
                        for member in channel.members:
                            await member.move_to(self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['first_mod_channel_id']))
                    except:
                        pass
                    await channel.delete()
                for channel in category.text_channels:
                    await channel.delete()
                await category.delete()

                cluster.sweetness.closemod.delete_one({'_id': str(inter.author.id)})

            if custom_id == "ban_event":
                embed = disnake.Embed(color = 7334102, description = f'**> {inter.author.mention}, **Выберите** действие ивент бан**')
                embed.set_author(name = "Выдать/Снять ивент бан", icon_url = inter.guild.icon.url)
                embed.set_footer(text = 'Команда работает только для уполномоченных пользователей.').set_thumbnail(url = inter.author.display_avatar.url)
                await inter.send(ephemeral = True, embed = embed, view = ActionMuteBan())

            if custom_id == 'ban_give_event':
                await inter.response.send_modal(title = "Бан", custom_id = "ban_vidat",components=[
                    disnake.ui.TextInput(label="Причина",placeholder="Например: Оскорбление",custom_id = "Причина бана",style=disnake.TextInputStyle.short,max_length=50),
                    disnake.ui.TextInput(label="Айди пользователя",placeholder="Например: 849353684249083914",custom_id = "Айди пользователя",style=disnake.TextInputStyle.short,max_length=50),
                    disnake.ui.TextInput(label="Время бана",placeholder="Например: 10m или 10m",custom_id = "Время бана", style=disnake.TextInputStyle.short,min_length=1,max_length=4)])

            if custom_id == 'ban_snyat_event':
                await inter.response.send_modal(title = "Разбан",custom_id = "ban_snyat",components=[
                    disnake.ui.TextInput(label="Айди пользователя",placeholder="Например: 849353684249083914",custom_id = "Айди пользователя",style=disnake.TextInputStyle.short,max_length=50),
                    disnake.ui.TextInput(label="Причина",placeholder="Например: ошибка",custom_id = "Причина снятия",style=disnake.TextInputStyle.short,max_length=50)])

            if custom_id == "prize_event":
                cluster.sweetness.event_members.update_one({'_id': str(inter.author.id)}, {'$set': {'members': []}}, upsert = True)
                for member in inter.author.voice.channel.members:
                    cluster.sweetness.event_members.update_one({"_id": str(inter.author.id)}, {"$push": {"members": member.id}})

                members = cluster.sweetness.event_members.find_one({'_id': str(inter.author.id)})['members']

                embed.set_author(name = f"Выдача награды", icon_url = inter.guild.icon.url)
                embed.description = f"Участники ивента:\n"
                id = 1
                for member_id in members:
                    embed.description += f"**{id} — <@{member_id}>**\n"
                    id += 1
                    if id > 10:
                        break

                return await inter.send(embed = embed, view = GiveEventPrize(self.bot, members))

            if custom_id == 'chat_event':
                embed.description = f"{inter.author.mention}, Выберите действие"
                await inter.send(embed = embed, ephemeral = True, view = ChoiceChat())
            if custom_id == 'voice_event':
                embed.description = f"{inter.author.mention}, Выберите действие"
                await inter.send(embed = embed, ephemeral = True, view = ChoiceVoice())
        
            if custom_id == 'open_chat_event':
                text_channel = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['text_channel']
                await inter.response.defer()
                await self.bot.get_channel(int(text_channel)).set_permissions(inter.guild.default_role, send_messages=True)
            if custom_id == 'close_chat_event':
                text_channel = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['text_channel']
                await inter.response.defer()
                await self.bot.get_channel(int(text_channel)).set_permissions(inter.guild.default_role, send_messages=False)
        
            if custom_id == 'open_voice_event':
                voice_channel = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['voice_channel']
                await inter.response.defer()
                await self.bot.get_channel(int(voice_channel)).set_permissions(inter.guild.default_role, connect=True)
            if custom_id == 'close_voice_event':
                voice_channel = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})['voice_channel']
                await inter.response.defer()
                await self.bot.get_channel(int(voice_channel)).set_permissions(inter.guild.default_role, connect=False)
        
            if custom_id == 'microphone_event':
                embed.description = f"{inter.author.mention}, Выберите действие"
                await inter.send(embed = embed, ephemeral = True, view = ChoiceMute())

            if custom_id == "give_event":

                embed.description = f"{inter.author.mention}, Введите **айди пользователя** которому вы хотите передать ивент"
                await inter.send(embed = embed, ephemeral = True)

                def check(m):
                    return m.author.id == inter.author.id

                try: 
                    id_user = await self.bot.wait_for("message", check=check, timeout = 120)
                except TimeoutError:
                    return

                user = get(self.bot.get_all_members(), id = int(id_user.content))

                if cluster.sweetness.event_help.count_documents({"_id": str(user.id)}) == 0: 
                    cluster.sweetness.event_help.insert_one({"_id": str(user.id), "help": 0})

                manage_channel = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})["manage"]
                await self.bot.get_channel(manage_channel).set_permissions(user, view_channel = True, send_messages = True)
                await self.bot.get_channel(manage_channel).set_permissions(inter.author, view_channel = False, send_messages = False)

                count = 0
                for event in cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)}):
                    if not count == 0: 
                        try:
                            event_type = cluster.sweetness.closemod.find_one({'_id': str(inter.author.id)})[event]
                            cluster.sweetness.closemod.update_one({'_id': str(user.id)}, {'$set': {f'{event}': event_type}}, upsert = True)
                        except:
                            pass
                    count += 1

                cluster.sweetness.closemod.delete_one({'_id': str(inter.author.id)})

                embed.description = f"{inter.author.mention}, Вы успешно передали ивент {user.mention}"
                await inter.send(embed = embed, ephemeral = True)

                cluster.sweetness.event_help.update_one({"_id": str(user.id)}, {"$inc": {"help": +int(2)}})

            if custom_id == 'member_event':
                embed.description = f"{inter.author.mention}, Введите **Линк/Айди** пользователя которого вы хотите **выгнать**"
                await inter.send(embed = embed, ephemeral = True)

                def check(m):
                    return m.author.id == inter.author.id

                try: 
                    id_user = await self.bot.wait_for("message", check=check, timeout = 120)
                except TimeoutError:
                    return

                try:
                    user = get(self.bot.get_all_members(), id = int(id_user.content))
                except:
                    for member in inter.guild.members:
                        if f'<@{member.id}>' == str(id_user.content):
                            user = get(self.bot.get_all_members(), id = int(member.id))

                if user.voice.channel.id == inter.author.voice.channel.id:
                    try:
                        await user.move_to(None)
                    except:
                        pass

                embed.description = f"{inter.author.mention}, Вы успешно выгнали {user.mention}"
                await inter.send(embed = embed, ephemeral = True)

                return await inter.author.voice.channel.set_permissions(user, connect=False)

            if custom_id == 'mute_event':
                embed.description = f"{inter.author.mention}, Введите **Линк/Айди** пользователя которого вы хотите **замутить**"
                await inter.send(embed = embed, ephemeral = True)

                def check(m):
                    return m.author.id == inter.author.id

                try: 
                    id_user = await self.bot.wait_for("message", check=check, timeout = 120)
                except TimeoutError:
                    return

                try:
                    user = get(self.bot.get_all_members(), id = int(id_user.content))
                except:
                    for member in inter.guild.members:
                        if f'<@{member.id}>' == str(id_user.content):
                            user = get(self.bot.get_all_members(), id = int(member.id))

                await inter.author.voice.channel.set_permissions(user, speak = False)

                try:
                    await user.move_to(user.voice.channel)
                except:
                    pass

                embed.description = f"{inter.author.mention}, Вы успешно замутили {user.mention}"
                await inter.send(embed = embed, ephemeral = True)

            if custom_id == 'unmute_event':
                embed.description = f"{inter.author.mention}, Введите **Линк/Айди** пользователя которого вы хотите **размутить**"
                await inter.send(embed = embed, ephemeral = True)

                def check(m):
                    return m.author.id == inter.author.id

                try: 
                    id_user = await self.bot.wait_for("message", check=check, timeout = 120)
                except TimeoutError:
                    return
                
                try:
                    user = get(self.bot.get_all_members(), id = int(id_user.content))
                except:
                    for member in inter.guild.members:
                        if f'<@{member.id}>' == str(id_user.content):
                            user = get(self.bot.get_all_members(), id = int(member.id))

                await inter.author.voice.channel.set_permissions(user, speak = True)

                try:
                    await user.move_to(user.voice.channel)
                except:
                    pass

                embed.description = f"{inter.author.mention}, Вы успешно размутили {user.mention}"
                await inter.send(embed = embed, ephemeral = True)

    @commands.Cog.listener()
    async def on_modal_submit(self, inter):
        custom_id = inter.custom_id

        if custom_id.endswith("event"):
            if custom_id == "money_event":
                for key, value in inter.text_values.items():
                    количество = value
                пользователь = disnake.utils.get(inter.guild.members, id = int(group[inter.author.id]))

                embed = disnake.Embed(color = 3092790)
                embed.set_author(name = f"Ивенты | {inter.guild.name}", icon_url = inter.guild.icon.url)
                embed.set_thumbnail(url = inter.author.display_avatar.url)
                embed.description = f"{inter.author.mention}, **Вы** успешно запросили выдачу валюты {пользователь.mention}"
                embed.add_field(name = "Число валюты", value = f"{количество}")
                await inter.send(embed = embed, ephemeral = True)

                embed = disnake.Embed(title = "Выдача валюты", color = 3092790)
                embed.set_thumbnail(url = inter.author.display_avatar.url)
                embed.add_field(name = "Ивентер", value = f"{inter.author.mention}")
                embed.add_field(name = "Пользователь", value = f"{пользователь.mention}")
                embed.add_field(name = "Число валюты", value = f"{количество}")
                msg = await self.bot.get_channel(1167104743034855454).send('<@1129862664953282722>', embed = embed, view = YesOrno())
                cluster.sweetness.closemod.insert_one({"_id": str(msg.id), "number": количество, "member": пользователь.id})

        if custom_id[-5:] == 'snyat':
            emb = disnake.Embed(color = 7334102)
            emb.set_author(name = "Снять наказание", icon_url = inter.guild.icon.url)
            emb.set_thumbnail(url = inter.author.display_avatar.url)
            id = 0
            for key, value in inter.text_values.items():
                if id == 0:
                    member_id = value
                else:
                    reason = value
                id += 1

            пользователь = disnake.utils.get(inter.guild.members, id = int(member_id))

            embed = disnake.Embed(color = 7334102)
            embed.set_thumbnail(url = inter.author.display_avatar.url)
            embed.set_author(name = "Снять наказание", icon_url = inter.guild.icon.url)
            embed.add_field(name = f"> Пользователь", value = f"{пользователь.mention} | **ID:** {пользователь.id}")
            embed.add_field(name = f"> Модератор", value = f"{inter.author.mention} | **ID:** {inter.author.id}")
            embed.add_field(name = f"> Причина", value = f"```yaml\n{reason}```")

            if custom_id == 'ban_snyat':
                embed.set_author(name = "Снять бан", icon_url = inter.guild.icon.url)
                emb.description = f"{inter.author.mention}, **Вы** успешно сняли бан {пользователь.mention}" 

                role = disnake.utils.get(inter.guild.roles, id = cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['closeban_id'])
                await пользователь.remove_roles(role)

                cluster.sweetness.event_ban.delete_one({'_id': str(пользователь.id)})

            await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['logs_ban_channel_id']).send(embed = embed)
            
            await inter.response.edit_message(embed = emb)

        if custom_id[-5:] == 'vidat':
            id = 0
            for key, value in inter.text_values.items():
                if id == 0:
                    reason = value
                if id == 1:
                    member_id = value
                else:
                    time = value
                id += 1

            member = disnake.utils.get(inter.guild.members, id = int(member_id))

            if cluster.sweetness.history_punishment.count_documents({"_id": str(member.id)}) == 0: 
                cluster.sweetness.history_punishment.insert_one({"_id": str(member.id), "warns": 0, "mutes": 0, "bans": 0, "eventban": 0})

            if cluster.sweetness.history_add.count_documents({"_id": str(member.id)}) == 0: 
                cluster.sweetness.history_add.insert_one({"_id": str(member.id), "tip_data": [], "punishment": [], "moderator": []})

            if cluster.sweetness.balls.count_documents({"_id": str(inter.author.id)}) == 0: 
                cluster.sweetness.balls.insert_one({"_id": str(inter.author.id), "balls": 0, "warns": 0, "mutes": 0, "bans": 0})

            if cluster.sweetness.balls_week.count_documents({"_id": str(inter.author.id)}) == 0: 
                cluster.sweetness.balls_week.insert_one({"_id": str(inter.author.id), "balls": 0, "warns": 0, "mutes": 0, "bans": 0})

            cluster.sweetness.balls.update_one({"_id": str(inter.author.id)}, {"$inc": {"balls": +int(2)}})
            
            try:
                if time[-1] == 'м': 
                    num = 'минут'
                    time1 = int(time[:-1]) * 60
                    new_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=time1)
                elif time[-1] == 'ч': 
                    num = 'часов'
                    time1 = int(time[:-1]) * 60 * 60
                    new_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=time1)
                elif time[-1] == 'д': 
                    num = 'дней'
                    time1 = int(time[:-1]) * 60 * 60 * 24
                    new_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=time1)
                elif time[-1] == 'm': 
                    num = 'минут'
                    time1 = int(time[:-1]) * 60
                    new_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=time1)
                elif time[-1] == 'h': 
                    num = 'часов'
                    time1 = int(time[:-1]) * 60 * 60
                    new_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=time1)
                elif time[-1] == 'd': 
                    num = 'дней'
                    time1 = int(time[:-1]) * 60 * 60 * 24
                    new_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=time1)
            except:
                pass

            emb = disnake.Embed(color = 7334102).set_thumbnail(url = inter.author.display_avatar.url)

            embed = disnake.Embed(color = 7334102).set_thumbnail(url = inter.author.display_avatar.url)
            embed.add_field(name='> ・Причина', value = f'```yaml\n{reason}```', inline = False)
            try:
                embed.add_field(name='> ・Время', value = f'```yaml\n{time[:-1]} {num}```')
            except:
                pass
            embed.set_footer(text = f'Выполнил(а) команду {inter.author}', icon_url = inter.author.display_avatar.url)

            general = len(cluster.sweetness.history_add.find_one({'_id': str(member.id)})['tip_data']) + 1

            input = datetime.datetime.now()
            data = int(input.timestamp())

            cluster.sweetness.history_add.update_one({"_id": str(member.id)}, {"$push": {"punishment": f"{reason} <:online:1109846973378470050> {time[:-1]} {num}"}})
            cluster.sweetness.history_add.update_one({"_id": str(member.id)}, {"$push": {"moderator": f"{inter.author.id}"}})

            cluster.sweetness.balls.update_one({"_id": str(inter.author.id)}, {"$inc": {"bans": +int(1)}})
            cluster.sweetness.balls_week.update_one({"_id": str(inter.author.id)}, {"$inc": {"bans": +int(1)}})
            cluster.sweetness.history_punishment.update_one({"_id": str(member.id)}, {"$inc": {"bans": +int(1)}})

            cluster.sweetness.history_add.update_one({"_id": str(member.id)}, {"$push": {"tip_data": f"#{general} <:unavailable:1109833288945782854> <t:{data}:F>"}})

            role_id = cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['closeban_id']
            await member.move_to(None)
            desc = f'{inter.author.mention}, **Вы** успешно **забанили**\n{member.mention}!'
            embed.set_author(name = 'Бан', icon_url = inter.guild.icon.url)
            emb.set_author(name = 'Бан', icon_url = inter.guild.icon.url)

            cluster.sweetness.event_ban.update_one({'_id': str(member.id)}, {'$set': {'time': new_date, 'role': role_id}}, upsert = True)

            embed.description = desc
            await inter.send(ephemeral = True, embed = embed)
            try:
                embed = disnake.Embed(color = disnake.Color.red(),description=f'Привет {member.mention}, **Вы** получили **Ивент бан** на сервере {inter.guild.name}!\n> ・Модератор {inter.author.mention} \
                                      \n> ・Время {time[:-1]} {num}\n> ・Причина: **{reason}**')
                embed.set_thumbnail(url = inter.guild.icon.url).set_author(name = f"Ивент бан | {inter.guild.name}", icon_url = inter.guild.icon.url)
                await member.send(embed = embed)
            except:
                pass

            try:
                role_get = disnake.utils.get(inter.guild.roles, id = int(role_id))
                await member.add_roles(role_get)
            except:
                pass

            embed.description = ""
            embed.add_field(name='> ・Модератор', value = f'{inter.author.mention}', inline = False)
            embed.add_field(name='> ・Нарушитель', value = f'{member.mention}', inline = False)
            await self.bot.get_channel(cluster.sweetness.system.find_one({'_id': str(inter.guild.id)})['logs_ban_channel_id']).send(embed = embed)


def setup(bot): 
    bot.add_cog(eventbot(bot))