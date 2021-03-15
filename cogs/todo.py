import discord
from discord.ext import commands
from menus import menus
from jishaku.paginators import PaginatorEmbedInterface, PaginatorInterface

class TodoMenuSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=5)
    async def format_page(self, menu, entries):
        return {"embed": discord.Embed(color=menu.ctx.bot.color, title=f"{menu.ctx.author.name}'s menu", description="\n".join(entries))}

class todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group(invoke_without_command=True)
    async def todo(self, ctx):
        pass
    @todo.command()
    async def remove(self, ctx, index: commands.Greedy[int]):
        todos = await self.bot.db.fetch("SELECT * FROM todos WHERE author_id = $1", ctx.author.id)
        to_delete = [todos[num - 1]["created_at"] for num in index]
        to_display = []
        for i in index:
            to_display.append(f"{i} - {todos[i-1]['content']}")
        await self.bot.db.execute("DELETE FROM todos WHERE author_id = $1 AND created_at = ANY ($2)", ctx.author.id, tuple(to_delete))
        return await ctx.send(embed=discord.Embed(color=self.bot.color, title=f"Deleted {len(index)} tasks", description="\n".join(to_display)))
    @todo.command()
    async def list(self, ctx):
        todos = await self.bot.db.fetch("SELECT * FROM todos WHERE author_id = $1 ORDER BY created_at", ctx.author.id)
        if not todos:
            return await ctx.send(embed=discord.Embed(color=self.bot.color, description=f"you have no todos `{ctx.prefix}todo add sometodos` to make one"))
        lists = []
        counter = 1
        for i in todos:
            lists.append(f"[{counter}]({i['jump_url']}). {i['content']}")
            counter += 1
        pages = menus.MenuPages(source=TodoMenuSource(lists), clear_reactions_after=True)
        await pages.start(ctx)
    @todo.command()
    async def add(self, ctx, *, content):
        todos = await self.bot.db.fetch("INSERT INTO todos (author_id, content, created_at, message_id, jump_url) VALUES ($1, $2, $3, $4, $5) RETURNING *", ctx.author.id, content, ctx.message.created_at, ctx.message.id, ctx.message.jump_url)
        return await ctx.send(embed=discord.Embed(color=self.bot.color, title="Successfully added new todo", description=f"{len(todos)} - {content}"))

        
def setup(bot):
    bot.add_cog(todo(bot))
