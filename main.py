import os
import sys
import time
import json
import aiohttp
import config
from discord import utils
from discord.ext import commands

# Path of project
path = os.path.abspath(os.path.dirname(__file__))
os.chdir(path)  # for relative files
sys.path.insert(0, path)  # for modules load

# Path to data.json file
cwd = os.getcwd()
json_file_path = '%s/%s' % (cwd, 'data.json')
data_props = {}

try:
    with open(json_file_path) as data_file:
        data_props = json.load(data_file)
except IOError as e:
    print('Exception while trying to open json: '+e.__str__())

osu_api_key = data_props['osu_api_key']
token = data_props['token']
mutedList = []
botClient = commands.Bot(command_prefix='.')


async def use_api(ctx, url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as channel:
                res = await channel.json()
                return res
        except Exception:
            await ctx.send('Invalid URL parse :wheelchair:')
            return


async def parse_match(ctx, games):
    plist = {}
    for game in games:
        try:
            del game['play_mode']
        except:
            pass
        try:
            del game['match_type']
        except:
            pass
        try:
            del game['team_type']
        except:
            pass
        try:
            del game['start_time']
            del game['end_time']
            del game['scoring_type']
        except:
            pass
        scoresum = 0
        game['newscores'] = []
        game['playercount'] = 0
        for score in game['scores']:
            g = dict()

            g['user_id'] = score['user_id']
            plist[g['user_id']] = 0
            g['score'] = score['score']
            g['maxcombo'] = score['maxcombo']
            g['enabled_mods'] = score['enabled_mods']
            scoresum += int(score['score'])
            game['playercount'] += 1
            game['newscores'].append(g)

        game['scoresum'] = scoresum

    player_number = 0
    text_string = ''
    print('started parsing match scores')
    for player in plist:
        player_number = player_number + 1
        map_number = 0
        player_username = await get_username(ctx, player)
        text_string += (player_number.__str__() + '. ' + player_username + ': ')
        for game in games:
            map_number = map_number + 1
            for score in game['scores']:
                if player == score['user_id']:
                    text_string += score['score'] + ' '
        print('player ' + player_number.__str__() + ' finished')
        text_string += '\n'

    return text_string


async def get_username(ctx, player_id):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://osu.ppy.sh/api/get_user?u=" + player_id + "&k=" + osu_api_key) as channel:
                res = await channel.json()
                return res[0]['username']
        except Exception:
            await ctx.send('get username error')
            return


@botClient.command(pass_context=True)
async def ms(ctx, url):
    print('.ms ' + url.__str__() + ' requested by ' + ctx.author.name.__str__())
    if 'https://osu.ppy.sh/community/matches' in url:
        try:
            url = url.split("matches/")
        except:
            await ctx.send('Invalid URL :wheelchair:')
            return
        url = url[1]
        res = await use_api(ctx, "https://osu.ppy.sh/api/get_match?k=" + osu_api_key + "&mp=" + url)
        message = await parse_match(ctx, res['games'])
        await ctx.send(message)


@botClient.command(pass_context=True)
async def mv(ctx):
    print('.mv requested by ' + ctx.author.name.__str__())
    leader = ctx.author
    start = time.time()
    try:
        channel = botClient.get_channel(leader.voice.channel.id)
        for member in list(channel.members):
            await member.edit(deafen=True, mute=True)
            mutedList.append(member)
        end = time.time()
        endedTime = round((end - start), 2)
        await ctx.send('muted everyone in voice channel ' + channel.name + ' in ' + endedTime.__str__() + 's.')
    except AttributeError:
        print("exception in .mv")


@botClient.command(pass_context=True)
async def uv(ctx):
    print('.uv requested by ' + ctx.author.name.__str__())
    leader = ctx.author
    start = time.time()
    end = None
    try:
        channel = botClient.get_channel(leader.voice.channel.id)
        for member in list(channel.members):
            await member.edit(deafen=False, mute=False)
        end = time.time()
        endedTime = round((end - start), 2)
        await ctx.send('unmuted everyone in voice channel ' + channel.name + ' in ' + endedTime.__str__() + 's.')
    except AttributeError:
        print("exception in .uv")
    print(end - start)


@botClient.command(pass_context=True)
async def uvall(ctx):
    print('.uvall requested by ' + ctx.author.name.__str__())
    start = time.time()
    end = None
    try:
        for member in list(mutedList):
            await member.edit(deafen=False, mute=False)
        end = time.time()
        ended_time = round((end - start), 2)
        await ctx.send('unmuted everyone who were muted before for ' + ended_time.__str__()+'s.')
    except AttributeError:
        print("exception in .uvall")
    print(end - start)


@botClient.event
async def on_ready():
    print('Bot started')


@botClient.event
async def on_raw_reaction_add(payload):
    channel = botClient.get_channel(payload.channel_id)
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


@botClient.event
async def on_raw_reaction_remove(payload):
    channel = botClient.get_channel(payload.channel_id)
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


botClient.run(token)
