import discord
from discord.ext import commands
import scientist_config
import asyncio

#BOT GOALS:
#!location to set Location topic
#!nations with a list of nations

"""def x_y_and_z(o):
    s = o.split()
    if len(s) == 1:
        return o
    elif len(s) == 2:
        return "{} and {}".format(s[0],s[1])
    else:
        return ", ".join(s[:-1]) + "and " + s[-1]"""
async def ward(ctx, cmdname):
    location_channel_names = []
    for k in self.location_channels:
        try:
            c = self.get_channel(k)
        except:
            continue
        if c.guild.id == ctx.guild.id:
            location_channel_names.append(c.mention)
    await ctx.send("?{}} can only be used in the location channels: {}.".format(
        cmdname, xyandz(location_channel_names)))

def xyandz(l):
    if len(l) == 1:
        return l[0]
    elif len(l) == 2:
        return "{} and {}".format(l[0],l[1])
    else:
        m = ""
        for e in l[:-1]:
            m += e + ", "
        m += "and {}".format(l[-1])
        return m

class Scientist(commands.Bot):
    #subclassing Bot so i can store my own properites
    #ripped from altarrel
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix="?"
        )
        self.location_channels = {
            513959986506760202: {
                "owner_role_id": 513965041331077120,
                "part_role_id": 513965079876599808
            },
            535616180526776321: {
                "owner_role_id": 535617241530499074,
                "part_role_id": 535617268806189066
            }
        }
        self.is_rp = False
        self.close_rp_callback = None
        self.remove_command("help")
        self.add_command(location)
        self.add_command(invite)
        self.add_command(close)
        self.add_command(rolelist)

    async def on_message(self, msg):
        if (
                msg.channel.id in self.location_channels
                and msg.author.id not in (513989250283208714, 209876515192569856)
                and msg.guild.get_role(self.location_channels[msg.channel.id]["owner_role_id"]).members == []
                and not msg.content.startswith("?location")
            ):
            await msg.author.send("Please use the ?location command followed by a location description before sending messages in {}.".format(msg.channel.mention))
            await msg.delete()
            return
        elif (
                msg.channel.id in self.location_channels
                and len(msg.guild.get_role(self.location_channels[msg.channel.id]["owner_role_id"]).members) != 0
                and not msg.content.startswith("?close")
            ):
            if self.close_rp_callback is not None:
                self.close_rp_callback.cancel()
            self.close_rp_callback = self.loop.create_task(close_rp_timeout(msg.guild, msg.channel))
        await self.process_commands(msg)

async def run(token):
    scientist = Scientist()
    try:
        await scientist.start(token)
    except KeyboardInterrupt:
        await scientist.logout()

@commands.command()
@commands.is_owner()
async def rolelist(ctx):
    await ctx.send("\n".join(["{}: {}".format(r.name,r.id) for r in ctx.guild.roles]))

@commands.command()
async def location(ctx, *, location):
    if ctx.channel.id not in self.location_channels:
        await ward(ctx,"location")
        return
    lowner_role = ctx.guild.get_role(self.location_channels[ctx.channel.id]["owner_role_id"])
    if len(lowner_role.members) != 0:
        await ctx.send("There is already an RP in progress. Please wait until it is closed or 10 minutes of inactivity pass.")
        return
    await ctx.author.add_roles(lowner_role,reason="?location invoked")
    await ctx.channel.edit(topic=location,reason="?location invoked")
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False, reason="?location invoked")
    await ctx.send("{} has been restricted to {}, the current RP owner. Channel description set. Please use `?invite @NATION1 @NATION2...` with pings to the nations you want to allow in the RP. As a courtesy to other nations, please use ?close to close the RP when you are done. Otherwise, your session will be ended after 10 minutes of inactivity."
        .format(ctx.channel.mention, ctx.author.mention))



@commands.command()
async def invite(ctx, members: commands.Greedy[discord.Member]):
    if ctx.channel.id not in self.location_channels:
        await ward(ctx,"invite")
        return
    if ctx.guild.get_role(self.location_channels[ctx.channel.id]["owner_role_id"]) not in ctx.author.roles:
        await ctx.send("You are not the owner of this channel and may not invite others.")
        return
    if len(members) == 0:
        await ctx.send("You must invite nations with `?invite @NATION1 @NATION2...`")
        return
    for m in members:
        await m.add_roles(ctx.guild.get_role(self.location_channels[ctx.channel.id]["part_role_id"]),reason="?invite invoked")
    await ctx.send("Added {} to the RP.".format(xyandz([m.mention for m in members])))


@commands.command()
async def close(ctx):
    if ctx.channel.id not in self.location_channels:
        await ward(ctx,"close")
        return
    if ctx.guild.get_role(self.location_channels[ctx.channel.id]["owner_role_id"]) not in ctx.author.roles:
        await ctx.send("You are not the owner of this channel and may not close it.")
        return
    ctx.bot.close_rp_callback.cancel()
    await close_rp(ctx.guild.id, ctx.channel.id, True)

async def close_rp_timeout(guild, channel):
    await asyncio.sleep(600)
    await close_rp(guild, channel, False)

async def close_rp(guild, channel, closed):
    if closed:
        reason = "?close invoked"
    else:
        reason = "RP timed out"
    for r in (guild.get_role(lowner_role_id),guild.get_role(lpart_role_id)):
        for m in r.members:
            await m.remove_roles(r,reason=reason)
    await channel.set_permissions(guild.default_role, send_messages=None, reason=reason)
    await channel.edit(topic="Use ?location followed by a location description to initiate an RP.",reason=reason)
    await channel.send("RP closed. Please use ?location followed by a location description to initiate a new RP. All other messages will be deleted.")


loop = asyncio.get_event_loop()
loop.run_until_complete(run(scientist_config.token))