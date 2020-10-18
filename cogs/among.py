import time
from threading import Timer
from cogs import config
from discord import utils
from discord.ext import commands
from discord import ChannelType

lol = 'dsfffsfs'
list_of_lobbies = []
mutedList = []


class Among(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def mv(self, ctx):
        print('.mv requested by ' + ctx.author.name.__str__())
        leader = ctx.author
        start = time.time()
        try:
            channel = self.bot.get_channel(leader.voice.channel.id)
            for member in list(channel.members):
                await member.edit(deafen=True, mute=True)
                mutedList.append(member)
            end = time.time()
            endedTime = round((end - start), 2)
            await ctx.send('muted everyone in voice channel ' + channel.name + ' in ' + endedTime.__str__() + 's.')
        except AttributeError:
            print("exception in .mv")

    @commands.command(pass_context=True)
    async def uv(self, ctx):
        print('.uv requested by ' + ctx.author.name.__str__())
        leader = ctx.author
        start = time.time()
        end = None
        try:
            channel = self.bot.get_channel(leader.voice.channel.id)
            for member in list(channel.members):
                await member.edit(deafen=False, mute=False)
            end = time.time()
            endedTime = round((end - start), 2)
            await ctx.send('unmuted everyone in voice channel ' + channel.name + ' in ' + endedTime.__str__() + 's.')
        except AttributeError:
            print("exception in .uv")
        print(end - start)

    @commands.command(pass_context=True)
    async def uvall(self, ctx):
        print('.uvall requested by ' + ctx.author.name.__str__())
        start = time.time()
        end = None
        try:
            for member in list(mutedList):
                await member.edit(deafen=False, mute=False)
            end = time.time()
            ended_time = round((end - start), 2)
            await ctx.send('unmuted everyone who were muted before for ' + ended_time.__str__() + 's.')
        except AttributeError:
            print("exception in .uvall")
        print(end - start)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot started')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = utils.get(message.guild.members, id=payload.user_id)
        emoji = None
        try:
            emoji = str(payload.emoji)
            role = utils.get(message.guild.roles, id=config.ROLES[emoji])
            print(member.__str__() + ' added reaction for role' + role.__str__())

            if len([i for i in member.roles if i.id not in config.EXCROLES]) < config.MAX_ROLES_PER_USER:
                await member.add_roles(role)
                print('[SUCCESS] User {0.display_name} has been granted with role {1.name}'.format(member, role))
                print('Колличество правильных ролей: ' + (
                    len([i for i in member.roles if i.id not in config.EXCROLES])).__str__())

            elif ((len([i for i in member.roles if i.id not in config.EXCROLES]) >= config.MAX_ROLES_PER_USER) and (
                    emoji not in config.SPECIALROLES)):
                await message.remove_reaction(payload.emoji, member)
                print('[ERROR] Too many roles for user {0.display_name}'.format(member))

            elif ((len([i for i in member.roles if i.id not in config.EXCROLES]) >= config.MAX_ROLES_PER_USER) and (
                    emoji in config.SPECIALROLES)):
                await member.add_roles(role)
                print('[SUCCESS] User {0.display_name} has been granted with role {1.name}'.format(member, role))
                print('Колличество правильных ролей: ' + (
                    len([i for i in member.roles if i.id not in config.EXCROLES])).__str__())

        except KeyError:
            print('[ERROR KeyError, no role found for ' + emoji)
        except Exception:
            print('exception in on_raw_reaction_add')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = utils.get(message.guild.members, id=payload.user_id)
        emoji = None
        try:
            emoji = str(payload.emoji)
            role = utils.get(message.guild.roles, id=config.ROLES[emoji])
            print(member.__str__() + ' removed reaction for role' + role.__str__())
            await member.remove_roles(role)
            print('[SUCCESS] Role {1.name} has been remove for user {0.display_name}'.format(member, role))

        except KeyError:
            print('[ERROR] KeyError, no role found for ' + emoji)
        except Exception:
            print('exception in on_raw_rection_remove')

    @commands.command(pass_context=True)
    async def here(self, ctx):
        if not list_of_lobbies:
            self.fill_list_of_lobbies(ctx)
        try:
            channel = self.bot.get_channel(ctx.author.voice.channel.id)
            self.check_timers()
            if self.check_if_lobby_on_cooldown(channel.id):
                if ctx.prefix.__str__() == '@':
                    try:
                        i = 0
                        for member in list(channel.members):
                            i += 1
                        count_needed = 10 - i
                        shit = ctx.message
                        await shit.delete()
                        await ctx.send('@here ' + ctx.author.__str__() + ' needs ' +
                                       count_needed.__str__() + ' more people in ' + channel.name)
                        print('@here called from  ' + channel.id.__str__())
                        self.set_timer_on_lobby(channel.id)
                    except Exception:
                        print('Exception in @here command')
                        await ctx.send('Something went wrong')
            elif not self.check_if_lobby_on_cooldown(channel.id):
                await ctx.send('Your lobyy is on cooldown.')
        except Exception:
            print('Exception in @here command')
            await ctx.send('You are not in voice channel@')

    def check_if_lobby_on_cooldown(self, lobby_id):
        for lobby in list_of_lobbies:
            if lobby_id.__str__() in lobby.__str__():
                if 'Timer' in lobby.__str__():
                    return False
                else:
                    return True

    def fill_list_of_lobbies(self, ctx):
        channels = (c.id for c in ctx.message.guild.channels if c.type == ChannelType.voice)
        print('list of lobbies:')
        i = 0
        for c in channels:
            i += 1
            print('added vc #' + i.__str__() + ' ' + c.__str__())
            # t = Timer(10, function=self.reset_timer)
            # t.start()
            list_of_lobbies.append((c.__str__(), 0))  # time.perf_counter()))

    def check_timers(self):
        print('reset timer called')
        i = 0
        for x in list_of_lobbies:
            print('123 ' + x.__str__())
            if 'stopped' in x.__str__():
                print('found stopped timer, reseting timer')
                list_of_lobbies[i] = (x.__str__()[2:20], 0)
            i += 1

    def timer_ended(self):
        pass

    def set_timer_on_lobby(self, lobby_id):
        i = 0
        for x in list_of_lobbies:
            if x.__str__()[2:-5] == lobby_id.__str__():
                t = Timer(10, function=self.timer_ended)
                t.start()
                list_of_lobbies[i] = (x.__str__()[2:-5], t)
                # x = (x.__str__()[2:-5], t)
                print('lobby  ' + lobby_id.__str__() + ' set on 30 min cooldown ')
            i += 1

    @commands.command(pass_context=True)
    async def dd(self, ctx):
        for x in list_of_lobbies:
            print(x.__str__())


def setup(bot):
    bot.add_cog(Among(bot))
