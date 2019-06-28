from datetime import datetime
import json

from discord import Embed, Guild, User
from discord.utils import get
from discord.ext import commands


class IncidentReport:

    def __init__(self, server: Guild, action: str, body: str, issuer: User, subject: User):
        self.action = action
        self.issuer = issuer
        self.subject = subject
        self.body = body
        self.server = server
        self.config_full = json.loads(open('config.json').read())
        self.config = self.config_full[str(self.server.id)]
        self.report_number = self.next_report_number()
        self.finalize_report()

    def next_report_number(self):
        return len(self.config['reports']) + 1

    def finalize_report(self):
        report = {
            "report_id": self.report_number,
            "action": self.action,
            "issuer": f'{self.issuer.name}#{self.issuer.discriminator}',
            "subject": f'{self.subject.name}#{self.subject.discriminator}',
            "body": self.body
        }
        self.config["reports"].update({self.report_number: report})
        json.dump(self.config_full, open('config.json', 'w'), indent=2, separators=(',', ': '))

    def generate_receipt(self):
        embed = Embed(title='Incident Report', description=f'Case Number: {self.report_number}', color=0xff0000)
        embed.add_field(name="Issued By:", value=f'{self.issuer.name}#{self.issuer.discriminator}')
        embed.add_field(name="Subject:", value=f'{self.subject.name}#{self.subject.discriminator}')
        embed.add_field(name='Action', value=self.action)
        embed.add_field(name='Reason', value=self.body)
        embed.timestamp = datetime.utcnow()
        return embed


class Punishment(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config_full = json.loads(open('config.json').read())

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, target: User, *, reason: str):
        """Kick the specified user (a report receipt will be send to the recipient and issuer, and optionally reporting channel if enabled)"""
        report = IncidentReport(ctx.message.guild, 'Kick', reason, ctx.message.author, target)
        receipt = report.generate_receipt()
        await ctx.message.author.send(f'User: {target.name}#{target.discriminator} has been kicked. The incident report is attached below:', embed=receipt)
        await target.send(f'You have been kicked from {ctx.message.guild}. The incident report is attached below:', embed=receipt)
        await ctx.message.guild.kick(target, reason=reason)
        await ctx.send(f'User: {target.name}#{target.discriminator} has been kicked. Report ID: {report.report_number}')
        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)]["reporting_channel"] is not None else False
        if reporting_enabled:
            report_channel = get(ctx.message.guild.text_channels, id=self.config_full[str(ctx.message.guild.id)]["reporting_channel"])
            await report_channel.send(embed=receipt)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, target: User, *, reason: str):
        """Ban the specified user (a report receipt will be send to the recipient and issuer, and optionally reporting channel if enabled)"""
        report = IncidentReport(ctx.message.guild, 'Ban', reason, ctx.message.author, target)
        receipt = report.generate_receipt()
        await ctx.message.author.send(f'User: {target.name}#{target.discriminator} has been banned. The incident report is attached below:', embed=receipt)
        await target.send(f'You have been banned from {ctx.message.guild}. The incident report is attached below:', embed=receipt)
        await ctx.message.guild.ban(target, reason=reason)
        await ctx.send(f'User: {target.name}#{target.discriminator} has been banned. Report ID: {report.report_number}')
        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)]["reporting_channel"] is not None else False
        if reporting_enabled:
            report_channel = get(ctx.message.guild.text_channels, id=self.config_full[str(ctx.message.guild.id)]["reporting_channel"])
            await report_channel.send(embed=receipt)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, target_id: int, *, reason: str):
        """Unban the specified user (a report receipt will be send to the recipient and issuer, and optionally reporting channel if enabled, user ID number required)"""
        target = await self.bot.fetch_user(target_id)
        report = IncidentReport(ctx.message.guild, 'Unban', reason, ctx.message.author, target)
        receipt = report.generate_receipt()
        await ctx.message.author.send(f'User: {target.name}#{target.discriminator} has been unbanned. The incident report is attached below:', embed=receipt)
        await ctx.message.guild.unban(target)
        await ctx.send(f'User: {target.name}#{target.discriminator} has been unbanned. Report ID: {report.report_number}')
        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)]["reporting_channel"] is not None else False
        if reporting_enabled:
            report_channel = get(ctx.message.guild.text_channels, id=self.config_full[str(ctx.message.guild.id)]["reporting_channel"])
            await report_channel.send(embed=receipt)


def setup(bot):
    bot.add_cog(Punishment(bot))
