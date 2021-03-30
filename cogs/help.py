import discord
from discord.ext import commands

from menus import menus

from jishaku.paginators import PaginatorEmbedInterface
from jishaku.models import copy_context_with

class HelpMenuSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)
    async def format_page(self, menu, entries):
        return {"embed": discord.Embed(color=menu.ctx.bot.color, title=f"Help command", description="\n".join(entries))}


class HelpCommand(commands.HelpCommand):
    def get_command_signature(self, command):
        return f"{self.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_group_help(self, group):
        lists = []
        for i in group.walk_commands():
            lists.append(self.get_command_signature(i))
        pages = menus.MenuPages(source=HelpMenuSource(lists), delete_message_after=True)
        await pages.start(self.context)

    async def send_command_help(self, command):
        embed = discord.Embed(color=self.context.bot.color, title=self.get_command_signature(command),
                              description=command.help or "oh seems like my owner is too lazy to add help for this command sorry")
        await self.context.send(embed=embed)

    async def send_cog_help(self, cog):
        lists = []
        commands_ = cog.get_commands()
        lists_ = []
        for i in commands_:
            if isinstance(i, commands.Group):
                for v in i.walk_commands():
                    lists_.append(self.get_command_signature(v))
            else:
                lists_.append(self.get_command_signature(i))
        for i in lists_:
            lists.append(f"**{i}**")
        pages = menus.MenuPages(source=HelpMenuSource(lists), delete_message_after=True)
        await pages.start(self.context)

    async def send_bot_help(self, mapping):
        cogs = "\n".join(self.context.bot.cogs.keys())

        embed = discord.Embed(color=self.context.bot.color, description=f"""
        Hi Welcome to The Anime bot's help command
        You can use the following commands

        `{self.context.prefix}help [command]`

        `{self.context.prefix}help [module]`

        **Available Modules are:**
        ```
fun
utility
moderations
chat
owners
Music
others
animes
todo
tag
commandsusage
events
pictures
logging
socket
        ```
        """)
        embed.set_thumbnail(url=str(self.context.me.avatar_url_as(format="png")))
        await self.context.send(embed=embed)
        # is_working = True
        # dicts = {
        #     739614767941156874: "animes",
        #     747680003021471825: "fun",
        #     596577110982918146: "moderations",
        #     747680120763973654: "Music",
        #     759933903959228446: "others",
        #     597589960270544916: "pictures",
        #     744346239075877518: "utility"
        # }
        # embed = discord.Embed(color=self.context.bot.color,
        #                       description="**Hi welcome to The Anime Bot's help menu**\n```diff\nBefore we start something you need to know about\n <argument> means that argument is require\n[requirment] mean that argument is optional\n```")
        # embed.add_field(name="Categorys", value="**Animes:** <:rooDuck:739614767941156874>\n**Fun:** <:rooAww:747680003021471825>\n**Moderations:** <:rooCop:596577110982918146>\n**Music:** <a:rooCool:747680120763973654>\n**Others:** <a:rooClap:759933903959228446>\n**Pictures:** <:rooBless:597589960270544916>\n**Utility:** <a:rooLove:744346239075877518>")
        # channel = self.get_destination()
        # message = await channel.send(embed=embed)
        # for i in dicts.keys():
        #     await message.add_reaction(self.context.bot.get_emoji(i))
        # def check(payload):
        #     return payload.message_id == message.id and payload.author_id == self.context.author.id and payload.emoji.id in dicts.keys()
        # payload = await self.context.bot.wait_for("raw_reaction_add", check=check)
        # await self.context.bot.invoke(copy_context_with(self.context, content="ovo help " + dicts.get(payload.emoji.id)))
        # await message.delete()

class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.help_command = HelpCommand()


def setup(bot):
    bot.add_cog(help(bot))
