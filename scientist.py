import discord
from discord.ext import commands
import scientist_config
import asyncio
import os
import aiohttp
import xml.etree.ElementTree as ET
import random
import datetime

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
    for k in ctx.bot.location_channels:
        try:
            c = ctx.bot.get_channel(k)
        except:
            continue
        if c.guild.id == ctx.guild.id:
            location_channel_names.append(c.mention)
    await ctx.send("?{} can only be used in the location channels: {}.".format(
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
            513959986506760202: { #tge location
                "owner_role_id": 513965041331077120,
                "part_role_id": 513965079876599808
            },
            535616180526776321: { #tge alt location
                "owner_role_id": 535617241530499074,
                "part_role_id": 535617268806189066
            }
            #NOTE - CHANNELS SCIENTIST CANNOT SEE CAUSE ward() TO CRASH
        }
        self.is_rp = False
        self.close_rp_callbacks = {}
        self.remove_command("help")
        self.add_command(location)
        self.add_command(invite)
        self.add_command(close)
        self.add_command(rolelist)
        #self.add_command(approve)
        self.add_command(ticket)
        #self.managed_nations = [scientist_config.tge_election]
        #next_midnight = datetime.datetime.utcnow().replace(hour=23,minute=59,tzinfo=datetime.timezone.utc).timestamp()
        #self.loop.call_at(next_midnight,issue)

    """async def issue(self):
        # check for new issue
        async with aiohttp.ClientSession() as h:
            for nation in self.managed_nations:
                channel = self.get_channel(nation["channel"])
                async with h.get("https://www.nationstates.net/cgi-bin/api.cgi?nation={}&q=issues".format(nation.name),
                    headers = {
                    "X-Autologin":nation.autologin,
                    "X-Pin":nation.pin}) as issue_r:
                    # GET THE FRIGGIN PIN
                    issues_t = await issue_r.text('utf-8')
                    issues_x = ET.fromstring(ir_t)
                    for issue in issues_x.get("ISSUES").iter():
                        if issue.get("id",default=None) != nation["current_issue_id"]:
                            # we haven't seen this issue before
                            if nation["current_issue_id"] != None:
                                # we have an old issue to be replaced by this one
                                # resolve current issue:
                                weights = []
                                for i in nation["option_msg_ids"]:
                                    r_count = self.get_message(i).reactions[0].count #assuming there's only one reaction
                                    weights.append(r_count)
                                choice = random.choices(range(0,len(weights)),weights)
                                async with h.post("https://www.nationstates.net/cgi-bin/api.cgi",
                                    headers={
                                        "X-Autologin":nation.autologin,
                                        "X-Pin":nation.pin
                                    },
                                    data="nation={}&c=issue&issue={}&option={}".format(
                                        nation.name,
                                        nation.current_issue_id,
                                        choice)) as issue_a:
                                    issues_a = await issue_a.text('utf-8')
                                    issues_a_x = ET.fromstring(issues_a)
                                    # PRINT INTO A MESSAGE
                                await channel.send("**OPTION {} CHOSEN**. In the future, data will be sent here.".format(choice+1))
                                nation["current_issue_id"] = None
                            else:
                                # we need to make this our current issue and post it
                                nation["current_issue_id"] = issue.get("id")
                                await channel.send("**{}**\n\n{}".format(issue.find("TITLE").text,issue.find("TEXT").text))
                                for option in issue.findall("OPTION"):
                                    msg = await channel.send("OPTION {}:{}".format(option.get("id")+1, option.text))
                                    nation["option_msg_ids"].append(msg.id)
                            break #if we have a ton of issues, chill out on them
                        else:
                            # we have seen this issue before
        self.loop.call_at()"""

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
            if msg.channel.id in self.close_rp_callbacks and self.close_rp_callbacks[msg.channel.id] is not None:
                self.close_rp_callbacks[msg.channel.id].cancel()
            self.close_rp_callbacks[msg.channel.id] = self.loop.create_task(close_rp_timeout(self, msg.guild, msg.channel))
        elif msg.author.id != 513989250283208714 and msg.channel.id == 578383389812588546:
            await msg.channel.send(f"{msg.author.display_name}: {msg.content}")
            await msg.delete()
        await self.process_commands(msg)

    #async def on_reaction_add(self, reaction, user):
    #    if reaction.message.channel.id == 505141941348859904:
    #        if reaction.

async def run(token):
    scientist = Scientist()
    try:
        await scientist.start(token)
    except KeyboardInterrupt:
        await scientist.logout()

@commands.command()
@commands.is_owner()
async def rolelist(ctx):
    rl = "\n".join(["{}: {}".format(r.name,r.id) for r in ctx.guild.roles])
    if len(rl) < 2000:
        await ctx.send(rl)
    with open(os.path.join("id_lists",str(ctx.guild.id) + ".txt"), 'w') as f:
        f.write(rl)

@commands.command()
async def location(ctx, *, location=None):
    if ctx.channel.id not in ctx.bot.location_channels:
        await ward(ctx,"location")
        return
    lowner_role = ctx.guild.get_role(ctx.bot.location_channels[ctx.channel.id]["owner_role_id"])
    if len(lowner_role.members) != 0:
        await ctx.send("There is already an RP in progress. Please wait until it is closed or 10 minutes of inactivity pass.")
        return
    if location == "" or location is None:
        await ctx.send("Please specify a location in your command, such as `?location A peaceful lake`.")
        return
    await ctx.author.add_roles(lowner_role,reason="?location invoked")
    await ctx.channel.edit(topic=location,reason="?location invoked")
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False, reason="?location invoked")
    await ctx.send("{} has been restricted to {}, the current RP owner. Channel description set. Please use `?invite @NATION1 @NATION2...` with pings to the nations you want to allow in the RP. As a courtesy to other nations, please use ?close to close the RP when you are done. Otherwise, your session will be ended after 10 minutes of inactivity."
        .format(ctx.channel.mention, ctx.author.mention))



@commands.command()
async def invite(ctx, members: commands.Greedy[discord.Member]):
    if ctx.channel.id not in ctx.bot.location_channels:
        await ward(ctx,"invite")
        return
    if ctx.guild.get_role(ctx.bot.location_channels[ctx.channel.id]["owner_role_id"]) not in ctx.author.roles:
        await ctx.send("You are not the owner of this channel and may not invite others.")
        return
    if len(members) == 0:
        await ctx.send("You must invite nations with `?invite @NATION1 @NATION2...`")
        return
    for m in members:
        await m.add_roles(ctx.guild.get_role(ctx.bot.location_channels[ctx.channel.id]["part_role_id"]),reason="?invite invoked")
    await ctx.send("Added {} to the RP.".format(xyandz([m.mention for m in members])))


@commands.command()
async def close(ctx):
    if ctx.channel.id not in ctx.bot.location_channels:
        await ward(ctx,"close")
        return
    if ctx.guild.get_role(ctx.bot.location_channels[ctx.channel.id]["owner_role_id"]) not in ctx.author.roles:
        await ctx.send("You are not the owner of this channel and may not close it.")
        return
    ctx.bot.close_rp_callbacks[ctx.channel.id].cancel()
    await close_rp(ctx.bot, ctx.guild, ctx.channel, True)

async def close_rp_timeout(bot, guild, channel):
    await asyncio.sleep(600)
    await close_rp(bot, guild, channel, False)

@commands.command()
async def approve(ctx, member: discord.Member):
    # oh lord time for some hardcoding to get this up asap EVENTS IS 505141941348859904
    async for m in ctx.bot.get_channel(505141941348859904).history(after=ctx.message.created_at - datetime.timedelta(minutes=10),oldest_first=False):
        if m.author.id == member.id and ctx.author.id in m.raw_mentions:
            await m.add_reaction("🛡")
            await ctx.send(f"{m.author.mention}, your message addressing {member.mention} has been approved!")
            return
    await ctx.send("Could not find a events post by that member.")

@commands.command()
async def ticket(ctx):
    mod_role = ctx.guild.get_role(298280102746259466)
    sci_role = ctx.guild.get_role(513990148338352128)
    ticket = await ctx.guild.create_text_channel(
        name=datetime.datetime.utcnow().isoformat(),
        overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            mod_role: discord.PermissionOverwrite(read_messages=True,manage_channels=True), #mods
            sci_role: discord.PermissionOverwrite(read_messages=True,manage_channels=True), #scientist itself
            ctx.author: discord.PermissionOverwrite(read_messages=True)
        },
        category=ctx.guild.categories[4], #oh no my hardcoding
        reason="opening ticket",
        topic=f"Ticket created by {ctx.author.display_name}",
        position=0
    )
    await ticket.send(f"Ticket created by {ctx.author.mention}. A mod will be with you shortly, __please do not ping anyone unless it's an emergency.__")
    await ctx.bot.wait_for('message', check=lambda m: m.author.top_role == mod_role and m.channel == ticket and m.content == "?close_ticket")
    #for target in ticket.overwrites:
        #print(target.id)
    #    if target.id not in (mod_role.id, sci_role.id,ctx.guild.default_role.id):
    #        await ticket.set_permissions(target, overwrite=None,reason="closing ticket")
    await ticket.send("Archiving ticket.")
    s = ""
    async for m in ticket.history(oldest_first=True):
        if m.edited_at:
            s += "[{} edited {}] {}: {}".format(
                m.created_at.isoformat(),
                m.edited_at.isoformat(),
                m.author.display_name,
                m.clean_content)
        else:
            s += "[{}] {}: {}".format(
                m.created_at.isoformat(),
                m.author.display_name,
                m.clean_content)
        if m.attachments:
            s += "\n[MESSAGE HAS ATTACHMENT]"
        s += "\n"
    s = s.replace("\n","\r\n")
    with open("out.txt", 'w') as f:
        f.write(s)
    await ctx.bot.get_channel(309153025644036106).send(
            file=discord.File(
                fp="out.txt"))
    await ticket.delete(reason="closing ticket")

async def close_rp(bot, guild, channel, closed):
    if closed:
        reason = "?close invoked"
    else:
        reason = "RP timed out"
    for r in (guild.get_role(bot.location_channels[channel.id]["owner_role_id"]),guild.get_role(bot.location_channels[channel.id]["part_role_id"])):
        for m in r.members:
            await m.remove_roles(r,reason=reason)
    await channel.set_permissions(guild.default_role, send_messages=None, reason=reason)
    await channel.edit(topic="Use ?location followed by a location description to initiate an RP.",reason=reason)
    await channel.send("RP closed. Please use ?location followed by a location description to initiate a new RP. All other messages will be deleted.")

loop = asyncio.get_event_loop()
loop.run_until_complete(run(scientist_config.token))
