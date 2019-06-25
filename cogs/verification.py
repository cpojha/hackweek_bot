import aiohttp
import json
from random import choices

from discord.ext import commands
from discord.utils import get


class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx):
        """Enable the verification system"""
        # Create role and channel
        role = await ctx.guild.create_role(name="Unverified")
        channel = await ctx.guild.create_text_channel(name="Verification")
        config = json.loads(open('config.json', 'r').read())
        config[str(ctx.message.guild.id)].update(verification_enabled=True, verification_channel=channel.id, verification_role=role.id)
        json.dump(config, open('config.json', 'w'), indent=2, separators=(',', ': '))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx):
        """Disable the verification system"""
        config = json.loads(open('config.json', 'r').read())
        # Delete role and channel
        await get(ctx.guild.roles, id=config[str(ctx.guild.id)]["verification_role"]).delete()
        await get(ctx.guild.text_channels, id=config[str(ctx.guild.id)]["verification_channel"]).delete()
        config[str(ctx.message.guild.id)].update(verification_enabled=False, verification_channel=None, verification_role=None)
        json.dump(config, open('config.json', 'w'), indent=2, separators=(',', ': '))

    @commands.command()
    async def verify(self, ctx):
        """Verify yourself (the bot will DM you)"""
        # Retrieve list of words from MIT page
        async with aiohttp.ClientSession() as client:
            async with client.get("https://www.mit.edu/~ecprice/wordlist.10000") as response:
                text = await response.text()
                words = text.splitlines()
            await client.close()

        # Pick three random words and DM them to the user
        random_phrase = ' '.join(choices(words, k=3))
        await ctx.message.author.send(f"Please reply with the following phrase: {random_phrase}")
        # Wait for 30 seconds for the user to send back the verification phrase
        await self.bot.wait_for("message", timeout=30, check=lambda message: message.content == random_phrase)
        await ctx.message.author.send("Verification complete 👍")
        # If they pass, remove the unverified role
        config = json.loads(open('config.json', 'r').read())
        role = get(ctx.guild.roles, id=config[str(ctx.guild.id)]["verification_role"])
        await ctx.message.author.remove_roles(role)

    @verify.error
    async def verify_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.message.author.send("Command timeout! Please rerun the command to verify")


def setup(bot):
    bot.add_cog(Verification(bot))
