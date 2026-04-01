import ast
import asyncio
import random

import discord
from discord.ext import commands

import config

sf_rates = {
    0: {'cost': 626000, 'failure': 0, 'success': 500, 'p_success': '95%'},
    1: {'cost': 1251000, 'failure': 0, 'success': 1000, 'p_success': '90%'},
    2: {'cost': 1876000, 'failure': 0, 'success': 1500, 'p_success': '85%'},
    3: {'cost': 2501000, 'failure': 0, 'success': 1500, 'p_success': '85%'},
    4: {'cost': 3126000, 'failure': 0, 'success': 2000, 'p_success': '80%'},
    5: {'cost': 3751000, 'failure': 0, 'success': 2500, 'p_success': '75%'},
    6: {'cost': 4376000, 'failure': 0, 'success': 3000, 'p_success': '70%'},
    7: {'cost': 5001000, 'failure': 0, 'success': 3500, 'p_success': '65%'},
    8: {'cost': 5626000, 'failure': 0, 'success': 4000, 'p_success': '60%'},
    9: {'cost': 6251000, 'failure': 0, 'success': 4500, 'p_success': '55%'},
    10: {'cost': 25324300, 'failure': 0, 'success': 5000, 'p_success': '50%'},
    11: {'cost': 58236400, 'failure': 0, 'success': 5500, 'p_success': '45%'},
    12: {'cost': 106018100, 'failure': 0, 'success': 6000, 'p_success': '40%'},
    13: {'cost': 176593800, 'failure': 0, 'success': 6500, 'p_success': '35%'},
    14: {'cost': 312037300, 'failure': 0, 'success': 7000, 'p_success': '30%'},
    15: {'cost': 139289100, 'failure': 210, 'success': 7000, 'trace': 12, 'p_success': '30%', 'p_trace': '2.1%'},
    16: {'cost': 164060800, 'failure': 210, 'success': 7000, 'trace': 12, 'p_success': '30%', 'p_trace': '2.1%'},
    17: {'cost': 255250300, 'failure': 680, 'success': 8500, 'trace': 12, 'p_success': '15%', 'p_trace': '6.8%'},
    18: {'cost': 632932500, 'failure': 680, 'success': 8500, 'trace': 12, 'p_success': '15%', 'p_trace': '6.8%'},
    19: {'cost': 1130808000, 'failure': 850, 'success': 8500, 'trace': 12, 'p_success': '15%', 'p_trace': '8.5%'},
    20: {'cost': 290257600, 'failure': 1050, 'success': 7000, 'trace': 15, 'p_success': '30%', 'p_trace': '10.5%'},
    21: {'cost': 526565100, 'failure': 1275, 'success': 8500, 'trace': 17, 'p_success': '15%', 'p_trace': '21.75%'},
    22: {'cost': 371070400, 'failure': 1700, 'success': 8500, 'trace': 17, 'p_success': '15%', 'p_trace': '17%'},
    23: {'cost': 416256900, 'failure': 1800, 'success': 9000, 'trace': 19, 'p_success': '10%', 'p_trace': '18%'},
    24: {'cost': 464760300, 'failure': 1800, 'success': 9000, 'trace': 19, 'p_success': '10%', 'p_trace': '18%'},
    25: {'cost': 516676700, 'failure': 1800, 'success': 9000, 'trace': 19, 'p_success': '10%', 'p_trace': '18%'},
    26: {'cost': 572101300, 'failure': 1860, 'success': 9300, 'trace': 20, 'p_success': '7%', 'p_trace': '18.6%'},
    27: {'cost': 631127900, 'failure': 1900, 'success': 9500, 'trace': 20, 'p_success': '5%', 'p_trace': '19%'},
    28: {'cost': 693849500, 'failure': 1940, 'success': 9700, 'trace': 20, 'p_success': '3%', 'p_trace': '19.4%'},
    29: {'cost': 760357800, 'failure': 1980, 'success': 9900, 'trace': 20, 'p_success': '1%', 'p_trace': '19.8%'}
}


class StarforceSimulator(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)


starforce_simulator_intents = discord.Intents.default()
starforce_simulator_intents.message_content = True
starforce_simulator = StarforceSimulator(command_prefix='#', intents=starforce_simulator_intents)

try:
    with open("tappers.txt") as f:
        tappers = ast.literal_eval(f.read())
except (ValueError, FileNotFoundError, SyntaxError) as e:
    print(e)
    tappers = {}

async_locks = {}


@starforce_simulator.event
async def on_ready():
    print(f'Logged in as {starforce_simulator.user} (ID: {starforce_simulator.user.id})')
    print('------')


@starforce_simulator.event
async def on_message(message: discord.Message):
    if message.author == starforce_simulator.user:
        return

    if message.channel.id != config.TAP_CHANNEL_ID:
        return

    if message.author.id not in async_locks:
        async_locks[message.author.id] = {'lock': asyncio.Lock(), 'command': ''}

    if message.author.id not in tappers:
        tappers[message.author.id] = {'id': message.author.id, 'taps': 0,
                                      'prestiges': [{'spent': 0, 'highest': 0, 'highest_booms': 0,
                                                     'current': 0, 'current_booms': 0, 'taps': 0}]}

    command = message.content.lower().strip()
    if 'tap' == command:
        await tap(message, tappers[message.author.id])
    elif 'skip' == command:
        await skip(message, tappers[message.author.id])
    elif 'prestige' == command:
        await prestige(message, tappers[message.author.id])
    elif 'stats' == command:
        await stats(message, tappers[message.author.id])
    elif 'leaderboard' == command:
        await leaderboard(message)


async def tap(message: discord.Message, tapper):
    if async_locks[message.author.id]['lock'].locked() and async_locks[message.author.id]['command'] == 'skip':
        return await skipping(message, tappers[message.author.id])
    async with async_locks[message.author.id]['lock']:
        async_locks[message.author.id]['command'] = 'tap'
        prestige = tapper['prestiges'][-1]

        if prestige['current'] == 30:
            await message.reply('You already hit ★ 30! Perhaps Prestige ⬖?')
            return

        tapper['taps'] += 1
        prestige['taps'] += 1
        random.seed(message.author.id * (tapper['taps']))
        roll = random.randrange(10000)
        sf_rate = sf_rates[prestige['current']]
        prestige['spent'] += sf_rate['cost']
        tap_message_content = (f'### Tap #{prestige["taps"]:,} - ★ {prestige["current"]}\n'
                               f'- Cost: {sf_rate["cost"]:,} mesos\n'
                               f'- Success: {sf_rate["success"]:,} or higher ({sf_rate["p_success"]})\n')
        if len(tapper['prestiges']) > 1:
            tap_message_content = f'### Prestige ⬖ {len(tapper["prestiges"]) - 1:,}\n' + tap_message_content
        if sf_rate['failure'] > 0:
            tap_message_content += f'- Destruction: {sf_rate["failure"] - 1:,} or lower ({sf_rate["p_trace"]})\n'
        tap_message_content += f'Your roll [0-9,999]: {roll:,}\n'
        if roll >= sf_rate['success']:
            prestige['current'] += 1
            if prestige['current'] > prestige['highest']:
                prestige['highest'] = prestige['current']
                prestige['highest_booms'] = prestige['current_booms']
            elif prestige['current'] == prestige['highest'] and prestige['current_booms'] < prestige['highest_booms']:
                prestige['highest_booms'] = prestige['current_booms']
            tap_message_content += f'### :star: Success - ★ {prestige["current"]}'
        elif roll >= sf_rate['failure']:
            tap_message_content += f'### Failure - ★ {prestige["current"]}'
        else:
            prestige['current'] = sf_rate['trace']
            prestige['current_booms'] += 1
            tap_message_content += f'### :boom: Destroyed - ★ {prestige["current"]}'

        # Save tappers
        with open("tappers.txt", "w") as f:
            f.write(tappers.__str__())

        await message.reply(tap_message_content)


async def skip(message, tapper):
    if async_locks[message.author.id]['lock'].locked() and async_locks[message.author.id]['command'] == 'skip':
        return await skipping(message, tappers[message.author.id])
    async with async_locks[message.author.id]['lock']:
        async_locks[message.author.id]['command'] = 'skip'
        prestige = tapper['prestiges'][-1]

        if prestige['current'] == 30:
            await message.reply('You already hit ★ 30! Perhaps Prestige ⬖?')
            return

        if prestige['current'] >= prestige['highest']:
            await message.reply('You cannot skip beyond what you have yet to achieve. You must tap from here.')
            return

        await message.reply(f'Tapping until ★ {prestige["highest"]}...')
        before = prestige.copy()
        while prestige['current'] < prestige['highest']:
            tapper['taps'] += 1
            prestige['taps'] += 1
            random.seed(message.author.id * (tapper['taps']))
            roll = random.randrange(10000)
            sf_rate = sf_rates[prestige['current']]
            prestige['spent'] += sf_rate['cost']
            if roll >= sf_rate['success']:
                prestige['current'] += 1
            elif roll >= sf_rate['failure']:
                pass
            else:
                prestige['current'] = sf_rate['trace']
                prestige['current_booms'] += 1

            # Sleep so this task doesn't block
            await asyncio.sleep(0)

        tap_message_content = (
            f'### Taps #{before["taps"] + 1:,} to {prestige["taps"]:,} ({prestige["taps"] - before["taps"]:,} taps)\n'
            f'- Cost: {prestige["spent"] - before["spent"]:,} mesos\n'
            f'- Booms: {prestige["current_booms"] - before["current_booms"]:,}\n'
            f'### :fast_forward: Skip to ★ {prestige["current"]}')
        if len(tapper['prestiges']) > 1:
            tap_message_content = f'### Prestige ⬖ {len(tapper["prestiges"]) - 1:,}\n' + tap_message_content
        await message.reply(tap_message_content)


async def prestige(message, tapper):
    if async_locks[message.author.id]['lock'].locked() and async_locks[message.author.id]['command'] == 'skip':
        return await skipping(message, tappers[message.author.id])
    async with async_locks[message.author.id]['lock']:
        async_locks[message.author.id]['command'] = 'prestige'
        prestige = tapper['prestiges'][-1]
        if prestige['current'] < 30:
            await message.reply('Reach ★ 30 to Prestige ⬖.')
            return

        tapper['prestiges'].append(
            {'spent': 0, 'highest': 0, 'highest_booms': 0, 'current': 0, 'current_booms': 0, 'taps': 0})

        await message.reply(
            f'You have reached Prestige ⬖ {len(tapper["prestiges"]) - 1:,}! Your stars and booms have been reset.')


async def stats(message, tapper):
    if async_locks[message.author.id]['lock'].locked() and async_locks[message.author.id]['command'] == 'skip':
        return await skipping(message, tappers[message.author.id])
    async with async_locks[message.author.id]['lock']:
        async_locks[message.author.id]['command'] = 'stats'
        stats_message_content = f'## {message.author.mention} stats\n'
        current_prestige = tapper['prestiges'][-1]
        if len(tapper['prestiges']) > 1:
            stats_message_content += f'### Current Prestige ⬖ {len(tapper["prestiges"]) - 1:,}\n'
        stats_message_content += (f'- Tapped {current_prestige["taps"]:,} times\n'
                                  f'- Current: ★ {current_prestige["current"]} | {current_prestige["current_booms"]:,} booms\n'
                                  f'- Record: ★ {current_prestige["highest"]} | {current_prestige["highest_booms"]:,} booms\n')
        if len(tapper['prestiges']) > 1:
            best_prestige = \
                sorted(tapper['prestiges'], key=lambda prestige: (-prestige['highest'], prestige['highest_booms']))[
                    0].copy()

            stats_message_content += f'### Best Prestige ⬖ {tapper["prestiges"].index(best_prestige):,}\n'
            stats_message_content += (f'- Tapped {best_prestige["taps"]:,} times\n'
                                      f'- ★ {best_prestige["highest"]} | {best_prestige["highest_booms"]:,} booms\n')
            stats_message_content += f'### Full Journey\n'
            stats_message_content += (f'- Total taps: {tapper["taps"]:,}\n'
                                      f'- Total booms: {sum(prestige["current_booms"] for prestige in tapper["prestiges"]):,}\n'
                                      f'- Total mesos: {sum(prestige["spent"] for prestige in tapper["prestiges"]):,}\n')

        await message.reply(stats_message_content)


async def skipping(message, tapper):
    prestige = tapper['prestiges'][-1]
    await message.reply(
        f'Still tapping until ★ {prestige["highest"]}...')


async def leaderboard(message):
    leaderboard_message_content = f'## Leaderboard\n'
    leaderboard_message_content += f'### Prestige\n'
    sorted_by_prestige_level = sorted([tapper for tapper in tappers.values() if len(tapper['prestiges']) > 1],
                                      key=lambda tapper: (-len(tapper['prestiges']), tapper['taps']))
    for i in range(min(10, len(sorted_by_prestige_level))):
        tapper = sorted_by_prestige_level[i]
        leaderboard_message_content += f'{i}. Prestige ⬖ {len(tapper["prestiges"]) - 1:,} | {tapper["taps"]:,} - <@{tapper["id"]}>\n'

    leaderboard_message_content += f'### Star Force\n'
    best_prestige_of_tappers = []
    for tapper in tappers.values():
        best_prestige = sorted(tapper['prestiges'],
                               key=lambda prestige: (-prestige['highest'], prestige['highest_booms']))[0].copy()
        best_prestige['id'] = tapper['id']
        best_prestige_of_tappers.append(best_prestige)
    sorted_best_prestige_of_tappers = sorted(best_prestige_of_tappers,
                                             key=lambda prestige: (-prestige['highest'], prestige['highest_booms']))
    for i in range(min(10, len(sorted_best_prestige_of_tappers))):
        tapper = sorted_best_prestige_of_tappers[i]
        leaderboard_message_content += f'{i}. ★ {tapper["highest"]} | {tapper["highest_booms"]:,} booms - <@{tapper["id"]}>\n'

    message = await message.reply('## Leaderboard')
    await message.edit(content=leaderboard_message_content)


starforce_simulator.run(config.BOT_TOKEN)
