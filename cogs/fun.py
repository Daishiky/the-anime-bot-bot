import asyncio
from utils.subclasses import AnimeContext
import config
import json
import os
import random
import re
import textwrap
import time
import typing
from io import BytesIO

import aiohttp
import async_timeout
import discord
import gtts
from asyncdagpi import Client
from bottom import from_bottom, to_bottom
from cryptography.fernet import Fernet
from discord.ext import commands
from menus import menus
from PIL import Image, ImageDraw, ImageFont
from utils.asyncstuff import asyncexe
from utils.embed import embedbase
from utils.paginator import AnimePages

talk_token = config.talk_token
rapid_api_key = config.rapid_api_key
tenor_API_key = config.tenor_API_key


class UrbanDictionaryPageSource(menus.ListPageSource):
    BRACKETED = re.compile(r"(\[(.+?)\])")

    def __init__(self, data):
        super().__init__(entries=data, per_page=1)

    def cleanup_definition(self, definition, *, regex=BRACKETED):
        def repl(m):
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        ret = regex.sub(repl, definition)
        if len(ret) >= 2048:
            return ret[0:2000] + " [...]"
        return ret

    def format_page(self, menu, entry):
        maximum = self.get_max_pages()
        title = f'{entry["word"]}: {menu.current_page + 1} / {maximum}' if maximum else entry["word"]
        embed = discord.Embed(title=title, colour=0x00FF6A, url=entry["permalink"])
        embed.set_footer(text=f'By {entry["author"]}')
        embed.description = self.cleanup_definition(
            f"**Definition:**\n {entry['definition']}\n**Example:**\n{entry['example']}"
        )

        try:
            up, down = entry["thumbs_up"], entry["thumbs_down"]
        except KeyError:
            pass
        else:
            embed.add_field(
                name="Votes",
                value=f"Thumbs Up {up} Thumbs Down {down}",
                inline=False,
            )

        try:
            date = discord.utils.parse_time(entry["written_on"][0:-1])
        except (ValueError, KeyError):
            pass
        else:
            embed.timestamp = date

        return embed


class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.talk_channels = []

    async def get_quote(self):
        async with self.bot.session.get("https://leksell.io/zen/api/quotes/random") as resp:
            quotes = await resp.json()
        return quotes["quote"]

    async def getmeme(self):
        async with self.bot.session.get("https://meme-api.herokuapp.com/gimme") as resp:
            meme = await resp.json()
            if meme["nsfw"] == True:
                return True
            link = meme["postLink"]
            title = meme["title"]
            nsfw = meme["nsfw"]
            image = meme["preview"][-1]
            return link, title, nsfw, image

    async def hug_(self):
        gifs = []
        async with self.bot.session.get(
            f"https://api.tenor.com/v1/search?q=animehug&key={tenor_API_key}&limit=50&contentfilter=low"
        ) as resp:
            text = await resp.json()
            for i in text["results"]:
                for x in i["media"]:
                    gifs.append(x["gif"]["url"])
        return random.choice(gifs)

    async def tenor_(self, search):
        tenor_ = []
        async with self.bot.session.get(
            f"https://api.tenor.com/v1/search?q={search}&key={tenor_API_key}&limit=50&contentfilter=low"
        ) as resp:
            text = await resp.json()
            for i in text["results"]:
                for x in i["media"]:
                    tenor_.append(x["gif"]["url"])
        return random.choice(tenor_)

    async def reddit_(self, text):
        async with self.bot.session.get(f"https://meme-api.herokuapp.com/gimme/{text}") as resp:
            meme = await resp.json()
            if meme["nsfw"] == True:
                return True
            link = meme["postLink"]
            title = meme["title"]
            nsfw = meme["nsfw"]
            image = meme["preview"][-1]
            return link, title, nsfw, image

    @staticmethod
    def bottoms(mode, text):
        if mode == "to_bottom":
            return to_bottom(text)
        else:
            return from_bottom(text)

    @commands.command()
    async def bigtext(self, ctx, *, text: str):
        await ctx.send(
            getattr("", "join")(
                [
                    getattr(":regional_indicator_{}:", "format")(i)
                    if i in getattr(__import__("string"), "ascii_lowercase")
                    else getattr("{}\N{combining enclosing keycap}", "format")(i)
                    if i in getattr(__import__("string"), "digits")
                    else "\U00002757"
                    if i == "!"
                    else "\U000025c0"
                    if i == "<"
                    else "\U000025b6"
                    if i == ">"
                    else "\U00002753"
                    if i == "?"
                    else i
                    for i in getattr(text, "lower")()
                ]
            )
        )

    @commands.command()
    async def ship(
        self,
        ctx: AnimeContext,
        user_1: typing.Union[discord.Member, discord.User],
        user_2: typing.Union[discord.Member, discord.User],
    ):
        random.seed(user_1.id + user_2.id + 34 + 35 + 69)
        amount = int(str(random.randint(0, 100))[0]) if len(str(random.randint(0, 100))) >= 2 else 1
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{user_1.name} + {user_2.name} = **{random.randint(0, 100)}**%\n{'<a:rooLove:744346239075877518>'* amount}",
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def pic(self, ctx: AnimeContext, animal: str):
        async with self.bot.session.get(f"https://some-random-api.ml/img/{animal}") as resp:
            if resp.status == 404:
                return await ctx.send("we can't find picture of that animal")
            pic = await resp.json()
            async with self.bot.session.get(pic["link"]) as resp:
                pic = BytesIO(await resp.read())
                await ctx.send(file=discord.File(pic, filename=animal + ".png"))

    @commands.command()
    async def fact(self, ctx: AnimeContext, animal: str):
        async with self.bot.session.get(f"https://some-random-api.ml/facts/{animal}") as resp:
            if resp.status == 404:
                return await ctx.send("we can't find fact about that animal")
            fact = await resp.json()
            await ctx.send(fact["fact"])
                         
    @commands.command()
    async def hi(self, ctx):
        await ctx.send("H")
            

    @commands.command()
    async def http(self, ctx: AnimeContext, *, code: str = "404"):
        async with self.bot.session.get(f"https://http.cat/{code}") as resp:
            buffer = await resp.read()
        await ctx.send(file=discord.File(BytesIO(buffer), filename=f"{code}.png"))

    @commands.command()
    async def robtea(self, ctx):
        embed = discord.Embed(
            description="Click it in 10 seconds to get your tea in perfect tempature",
            color=0x00FF6A,
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction("\U0001f375")
        start = time.time()

        def check(payload):
            return (
                payload.message_id == message.id
                and payload.emoji.name == "\U0001f375"
                and payload.user_id == ctx.author.id
            )

        payload = await self.bot.wait_for("raw_reaction_add", check=check)
        end = time.time()
        embed = discord.Embed(
            description=f"You robbed the tea in {round(end-start, 3)} seconds",
            color=0x00FF6A,
        )
        await message.edit(embed=embed)

    @commands.command(aliases=["balls"])
    async def ball(self, ctx: AnimeContext, *, question):
        await ctx.send(self.bot.ball.response(question))

    # @commands.command()
    async def spamclick(self, ctx):
        counter = 0
        embed = discord.Embed(
            color=0x00FF6A,
            description="Rules:\nafter the countdown end you will spam click the reaction as fast as you can",
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        embed = discord.Embed(color=0x00FF6A, description="3")
        await message.edit(embed=embed)
        await asyncio.sleep(1)
        embed = discord.Embed(color=0x00FF6A, description="2")
        await message.edit(embed=embed)
        await asyncio.sleep(1)
        embed = discord.Embed(color=0x00FF6A, description="1")
        await message.edit(embed=embed)
        await asyncio.sleep(1)
        embed = discord.Embed(color=0x00FF6A, description="NOW")
        await message.edit(embed=embed)
        await message.add_reaction("<:stab:744345955637395586>")

        def check(payload):
            return payload.emoji.id == 744345955637395586 and payload.message_id == message.id

        async with async_timeout.timeout(10):
            while True:
                tasks = [
                    asyncio.ensure_future(self.bot.wait_for("raw_reaction_add", check=check)),
                    asyncio.ensure_future(self.bot.wait_for("raw_reaction_remove", check=check)),
                ]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                counter += 1
                for task in pending:
                    task.cancel()
        await ctx.send(f"You clicked {counter} times")

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def latest(self, ctx: AnimeContext, user: discord.Member = None):
        async with ctx.typing():
            user1 = user
            if user1 is None:
                user1 = ctx.author
            async for message in ctx.channel.history(limit=10000):
                if message.author.id == user1.id:
                    msg = message
                    break
            embed = discord.Embed(color=0x00FF6A, timestamp=msg.created_at)
            embed.set_author(name=msg.author, icon_url=str(msg.author.avatar_url))
            embed.set_footer(text=f"id: {msg.id} Created at: ")
            if msg.embeds != []:
                content = "Embed"
            elif msg.attachments != []:
                content = "Attachment"
            else:
                content = msg.content
            embed.add_field(name="Content", value=content, inline=False)
            embed.add_field(name="Jump link", value=f"[url]({msg.jump_url})", inline=False)
            await ctx.send(embed=embed)
            if msg.attachments != []:
                await ctx.send(msg.attachments[0].url)
            if msg.embeds != []:
                await ctx.send(embed=msg.embeds[0])

    @commands.command(aliases=["rm"])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def randommessage(self, ctx: AnimeContext, limit=300):
        limit = min(limit, 10000)
        if limit <= 0:
            limit = 300
        async with ctx.typing():
            async for message in ctx.channel.history(limit=limit):
                # if user:
                #   lists = []
                #   counter = 0
                #   if message.author.id == user.id:
                #     lists.append(message)
                #     counter += 1
                #   if counter == 10:
                #     msg = random.choice(lists)
                #     break
                # else:
                if random.randint(0, 100) == 1:
                    msg = message
                    break
            # if user != None:
            #   lists = []
            #   for i in msg:
            #     if i.author.id == user.id:
            #       lists.append(i)
            # else:
            #   lists = msg
            # if lists == []:
            #   return await ctx.send(f"Can not find message that is send by {user}")
            # msg = random.choice(lists)
            embed = discord.Embed(color=0x00FF6A, timestamp=msg.created_at)
            embed.set_author(name=msg.author, icon_url=str(msg.author.avatar_url))
            embed.set_footer(text=f"id: {msg.id} Created at: ")
            if msg.embeds != []:
                content = "Embed"
            elif msg.attachments != []:
                content = "Attachment"
            else:
                content = msg.content
            embed.add_field(name="Content", value=content, inline=False)
            embed.add_field(name="Jump link", value=f"[url]({msg.jump_url})", inline=False)
            await ctx.send(embed=embed)
            if msg.attachments != []:
                await ctx.send(msg.attachments[0].url)
            if msg.embeds != []:
                await ctx.send(embed=msg.embeds[0])

    @commands.command()
    async def reddit(self, ctx: AnimeContext, *, text):
        await ctx.trigger_typing()
        link, title, nsfw, image = await self.reddit_(text)
        if nsfw == True:
            return
        embed = discord.Embed(color=0x00FF6A)
        embed.set_author(name=title, url=link)
        embed.set_image(url=image)
        embed.set_footer(
            text=f"requested by {ctx.author} response time : {round(self.bot.latency * 1000)} ms",
            icon_url=ctx.author.avatar_url,
        )
        await ctx.reply(embed=embed)

    @commands.command()
    async def bottomdecode(self, ctx: AnimeContext, *, text):
        bottoms = await self.bot.loop.run_in_executor(None, self.bottoms, "from_bottom", text)
        if len(bottoms) > 500:
            return await ctx.send(str(await self.bot.mystbin.post(bottoms)))
        await ctx.send(bottoms)

    @commands.command()
    async def bottomencode(self, ctx: AnimeContext, *, text):
        bottoms = await self.bot.loop.run_in_executor(None, self.bottoms, "to_bottom", text)
        if len(bottoms) > 500:
            return await ctx.send(str(await self.bot.mystbin.post(bottoms)))
        await ctx.send(bottoms)

    @staticmethod
    def render_emoji(text):
        return (
            text.replace("0", "\U00002b1b")
            .replace("1", "\U00002b1c")
            .replace("2", "\U0001f7e6")
            .replace("3", "\U0001f7eb")
            .replace("4", "\U0001f7e9")
            .replace("5", "\U0001f7e7")
            .replace("6", "\U0001f7ea")
            .replace("7", "\U0001f7e5")
            .replace("8", "\U0001f7e8")
            .replace("9", "")
        )

    @commands.command(aliases=["grid", "toemoji"])
    async def renderemoji(self, ctx: AnimeContext, *, codes: int):
        codes_ = await self.bot.loop.run_in_executor(None, self.render_emoji, str(codes))
        await ctx.reply(codes_)

    @commands.command()
    async def urban(self, ctx: AnimeContext, *, search: str):
        if ctx.channel.nsfw == False:
            lists = [
                "dick",
                "pussy",
                "horny",
                "porn",
                "cum",
                "cunt",
                "cock",
                "penis",
                "hole",
                "fuck",
                "shit",
                "bitch",
            ]
            if any(i in search for i in lists):
                return await ctx.send("Can not search nsfw words in non nsfw channel")
        async with self.bot.session.get(f"http://api.urbandictionary.com/v0/define?term={search}") as resp:
            if resp.status != 200:
                return await ctx.send(f"An error occurred: {resp.status} {resp.reason}")
            js = await resp.json()
            data = js.get("list", [])
            if not data:
                return await ctx.send("No results found, sorry.")

        pages = AnimePages(UrbanDictionaryPageSource(data))
        try:
            await pages.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)

    @commands.command(aliases=["chat"])
    @commands.max_concurrency(1, commands.cooldowns.BucketType.channel, wait=False)
    async def talk(self, ctx):
        """
        Chat with the bot you might stop by saying `end`
        """
        # for i in self.talk_channels:
        #   if i == ctx.message.channel.id:
        #     embed = discord.Embed(color=0x00ff6a, description="A chat session has already been established in this channel")
        #     return await ctx.reply(embed=embed)
        self.talk_channels.append(ctx.message.channel.id)
        embed = discord.Embed(color=0x00FF6A, description="A chat session has been established")
        await ctx.reply(embed=embed)

        def check(m):
            return m.author == ctx.author and (3 <= len(m.content) <= 60)

        talking = True
        while talking:
            chats = ["Hii", "helooo"]
            try:
                message = await self.bot.wait_for("message", timeout=60, check=check)
                chats.append(message.content)
                if message.content == "end":
                    self.talk_channels.remove(ctx.message.channel.id)
                    embed = discord.Embed(color=0x00FF6A, description="Ended")
                    await ctx.reply(embed=embed)
                    talking = False
                    return False
                payload = {
                    "text": message.content,
                    "context": [chats[-2], chats[-1]],
                }
                async with ctx.channel.typing(), self.bot.session.post(
                    "https://public-api.travitia.xyz/talk",
                    json=payload,
                    headers={"authorization": talk_token},
                ) as res:
                    await message.reply((await res.json())["response"])
            except asyncio.TimeoutError:
                self.talk_channels.remove(ctx.message.channel.id)
                embed = discord.Embed(color=0x00FF6A, description="Ended")
                await message.reply(embed=embed)
                talking = False
                return False

    @talk.error
    async def talk_error(self, ctx: AnimeContext, error):
        if isinstance(error, commands.errors.MaxConcurrencyReached):
            embed = discord.Embed(
                color=0x00FF6A,
                description="A chat session has already been established in this channel",
            )
            return await ctx.reply(embed=embed)

    @commands.command()
    async def sob(self, ctx: AnimeContext, level: int = 1):
        if level > 70:
            embed = discord.Embed(
                color=0x00FF6A,
                description=f"The level must be 70 or lower then 70",
            )
            return await ctx.send(embed=embed)
        emojis2 = ["<:rooSob:744345453923139714>" for _ in range(level)]
        emojis = " ".join(emojis2)
        embed = discord.Embed(color=0x00FF6A, description=f"{emojis}")
        await ctx.send(embed=embed)

    # @commands.command(aliases=["tr", "typerace"])
    async def typeracer(self, ctx):
        quote = await self.get_quote()
        font = ImageFont.truetype("lexiereadable-bold.ttf", 16)
        img = Image.new("RGB", (400, 100), color="black")
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), "\n".join(textwrap.wrap(quote, 46)), font=font)
        buffer = BytesIO()
        img.save(buffer, "png")
        file_ = discord.File(buffer, filename="quote.png")
        message = await ctx.reply(file=file_)

        def check(m):
            return m.channel == ctx.message.channel and m.content == quote

        start = time.perf_counter()
        msg = await self.bot.wait_for("message", check=check)
        end = time.perf_counter()
        final_ = end - start
        final_ = round(final_)
        embed = await embedbase.embed(self, ctx)
        embed.set_author(name=f"{msg.author} got it in {final_} seconds")
        embed2 = await embedbase.embed(self, ctx)
        embed2.set_author(name=f"{msg.author} got it in {final_} seconds")
        embed2.set_image(url="attachment://quote.png")
        await message.edit(embed=embed2)
        await ctx.send(embed=embed)

    @commands.command()
    async def tenor(self, ctx: AnimeContext, *, search):
        gif = await self.tenor_(search)
        async with self.bot.session.get(gif) as resp:
            gif = BytesIO(await resp.read())
        embed = await embedbase.embed(self, ctx)
        embed.set_image(url=f"attachment://{search}.gif")
        await ctx.send(embed=embed, file=discord.File(gif, f"{search}.gif"))

    @commands.command(aliases=["sw", "speedwatch"])
    async def speedwatcher(self, ctx: AnimeContext, member: discord.Member = None):
        member1 = member
        if member1 is None:
            member1 = ctx.author
        variable = random.randint(1, 2)
        variable2 = random.randint(0, 10)
        random.seed(member1.id)
        speed_ = random.random()
        speed = round(speed_ * 100)
        speed = speed + variable2 if variable == 1 else speed - variable2
        if speed < 0:
            bar_ = "\u2800"
        elif speed <= 10:
            bar_ = "<:angery:747680299311300639>"
        elif speed <= 20:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639>"
        elif speed <= 30:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639>"
        elif speed <= 40:
            bar_ = "<:angery:747680299311300639> <:angery:747680299311300639> <:angery:747680299311300639> <:angery:747680299311300639>"
        elif speed <= 50:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639>"
        elif speed <= 60:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639>"
        elif speed <= 70:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639>"
        elif speed <= 80:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639>"
        elif speed <= 90:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639>"
        elif speed >= 100:
            bar_ = "<:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639><:angery:747680299311300639>"

        embed = await embedbase.embed(self, ctx)
        embed.add_field(
            name=f"{member1} is",
            value=f"`{speed}%` anime speedwatcher\n{bar_}",
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def hug(self, ctx: AnimeContext, member: discord.Member = None):
        gif = await self.hug_()
        member1 = member
        if member1 is None:
            member1 = "themself"
        embed = await embedbase.embed(self, ctx)
        embed.set_author(name=f"{ctx.author} just hugged {member1}")
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @staticmethod
    @asyncexe()
    def tts_(text, lang):
        t = gtts.gTTS(text=text, lang=lang)
        buffer = BytesIO()
        t.write_to_fp(buffer)
        buffer.seek(0)
        return discord.File(buffer, filename="audio.mp3")

    @commands.command()
    async def tts(self, ctx: AnimeContext, lang="en", *, text="enter something "):
        async with ctx.typing():
            file = await self.tts_(text, lang)
            await ctx.send(file=file)

    @commands.command()
    async def sushi(self, ctx):
        embed = await embedbase.embed(self, ctx)
        embed.add_field(name="Get the sushi", value="3")
        message = await ctx.send(embed=embed)
        await asyncio.sleep(1)
        embed = await embedbase.embed(self, ctx)
        embed.add_field(name="Get the sushi", value="2")
        await message.edit(embed=embed)
        await asyncio.sleep(1)
        embed = await embedbase.embed(self, ctx)
        embed.add_field(name="Get the sushi", value="1")
        await message.edit(embed=embed)
        await asyncio.sleep(1)
        embed = await embedbase.embed(self, ctx)
        embed.add_field(name="Get the sushi", value="**NOW**")
        await message.edit(embed=embed)
        await message.add_reaction("\U0001f363")
        start = time.perf_counter()

        def check(reaction, user):
            return reaction.message.id == message.id and user != self.bot.user and str(reaction.emoji) == "\U0001f363"

        reaction, user = await self.bot.wait_for("reaction_add", check=check)
        end = time.perf_counter()
        users = await reaction.users().flatten()
        for i in users:
            if i.bot == True:
                users.remove(i)
        lists = []
        for i in users:
            lists.append(str(i.name))
        # await functions.in_lb(user)
        # score = await functions.get_lb(user)
        final = end - start
        # final = int(final)
        # if final == None or final == "null":
        #   await functions.update_lb(user, final)
        #   embed = await embedbase.embed(self, ctx)
        #   embed.add_field(name="Get the sushi", value=f"**{user} got it in {round(final * 1000)} ms new person record**")
        #   await message.edit(embed=embed)
        #   return
        # if final < score:
        #   await functions.update_lb(user, final)
        #   embed = await embedbase.embed(self, ctx)
        #   embed.add_field(name="Get the sushi", value=f"**{user} got it in {round(final * 1000)} ms new person record**")
        #   await message.edit(embed=embed)
        #   return

        embed = await embedbase.embed(self, ctx)
        embed.add_field(
            name="Get the sushi",
            value=f"**{user.mention} got it in {round(final * 1000)} ms **",
            inline=False,
        )
        embed.add_field(name="participant", value="\n".join(lists), inline=False)
        await message.edit(embed=embed)

        def check(payload):
            return payload.message_id == message.id

        while True:
            payload = await self.bot.wait_for("raw_reaction_add", check=check)
            msg = await self.bot.get_message(payload.message_id)
            if not msg:
                break
            reactions = msg.reactions[0]
            users = await reactions.users().flatten()
            print(users)
            for i in users:
                if i.bot == True:
                    users.remove(i)
            lists = []
            for i in users:
                lists.append(str(i.name))
            embed = await embedbase.embed(self, ctx)
            embed.add_field(
                name="Get the sushi",
                value=f"**{user.mention} got it in {round(final * 1000)} ms **",
                inline=False,
            )
            embed.add_field(name="participant", value="\n".join(lists), inline=False)
            await message.edit(embed=embed)

    @commands.command()
    async def meme(self, ctx):
        await ctx.trigger_typing()
        link, title, nsfw, image = await self.getmeme()
        if nsfw == True:
            return
        embed = discord.Embed(color=0x00FF6A)
        embed.set_author(name=title, url=link)
        embed.set_image(url=image)
        embed.set_footer(
            text=f"requested by {ctx.author} response time : {round(self.bot.latency * 1000)} ms",
            icon_url=ctx.author.avatar_url,
        )
        await ctx.reply(embed=embed)

    @commands.command()
    async def decode(self, ctx: AnimeContext, *, text):
        await ctx.trigger_typing()
        text1 = text
        key = config.key
        f = Fernet(key)
        try:
            if text1.startswith("https://mystb.in/"):
                text1 = str(await self.bot.mystbin.get(text))
            new = bytes(text1, "utf-8")
            decrypted = f.decrypt(new)
            decrypted = str(decrypted, "utf-8")
            await ctx.reply(decrypted, allowed_mentions=discord.AllowedMentions.none())
        except:
            await ctx.send("You provided a invalid link")

    @commands.command()
    async def encode(self, ctx: AnimeContext, *, text: str):
        await ctx.trigger_typing()
        key = config.key
        f = Fernet(key)
        newtext = bytes(text, "utf-8")
        new_token = f.encrypt(newtext)
        new_token = str(new_token, "utf-8")
        if len(new_token) > 0:
            paste = await self.bot.mystbin.post(new_token)
            new_token = str(paste)
        await ctx.reply(new_token)

    @commands.command()
    async def ovoly(self, ctx: AnimeContext, *, text):
        ovo = text.replace("l", "v").replace("L", "v").replace("r", "v").replace("R", "v")
        await ctx.reply(f"{ovo} ovo")

    @commands.command()
    async def roast(self, ctx: AnimeContext, member: discord.Member = None):
        if member is None:
            member = ctx.author
        if member == self.bot.user or member.id == 590323594744168494:
            return await ctx.send("nope")
        await ctx.trigger_typing()
        async with self.bot.session.get("https://evilinsult.com/generate_insult.php") as resp:
            response = await resp.text()
        async with self.bot.session.get("https://insult.mattbas.org/api/insult") as resp:
            response3 = await resp.text()
        response2 = await self.bot.dag.roast()
        choice = random.randint(1, 3)
        if choice == 1:
            response = response
        elif choice == 2:
            response == response2
        else:
            response == response3
        text = f"{member.mention}, {response}"
        await ctx.send(text)


def setup(bot):
    bot.add_cog(fun(bot))
