import ast
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
except (ValueError, FileNotFoundError, SyntaxError):
    tappers = {}
print(tappers)


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

    if 'tap' == message.content:
        await tap(message)
    elif 'stats' == message.content:
        await stats(message)
    elif 'leaderboard' == message.content:
        await leaderboard(message)


async def tap(message: discord.Message):
    if message.author.id not in tappers:
        tappers[message.author.id] = {'id': message.author.id, 'taps': 0, 'spent': 0, 'highest': 0, 'highest_booms': 0,
                                      'current': 0,
                                      'current_booms': 0}
    tapper = tappers[message.author.id]

    if tapper['current'] == 30:
        await message.reply('You already hit 30★!')
        return

    tapper['taps'] += 1
    random.seed(message.author.id * (tapper['taps']))
    roll = random.randrange(10000)
    sf_rate = sf_rates[tapper['current']]
    tapper['spent'] += sf_rate['cost']
    tap_message_content = (f'### Tap #{tapper["taps"]} - ★ {tapper["current"]}\n'
                           f'- Cost: {sf_rate["cost"]:,} mesos\n'
                           f'- Success: {sf_rate["success"]:,} or higher ({sf_rate["p_success"]})\n')
    if sf_rate['failure'] > 0:
        tap_message_content += f'- Destruction: {sf_rate["failure"] - 1:,} or lower ({sf_rate["p_trace"]})\n'
    tap_message_content += f'Your roll [0-9,999]: {roll:,}\n'
    if roll >= sf_rate['success']:
        tapper['current'] += 1
        if tapper['current'] > tapper['highest']:
            tapper['highest'] = tapper['current']
            tapper['highest_booms'] = tapper['current_booms']
        tap_message_content += f'### Success - ★ {tapper["current"]}'
    elif roll >= sf_rate['failure']:
        tap_message_content += f'### Failure - ★ {tapper["current"]}'
    else:
        tapper['current'] = sf_rate['trace']
        tapper['current_booms'] += 1
        tap_message_content += f'### Destroyed - ★ {tapper["current"]}'

    # Save tappers
    with open("tappers.txt", "w") as f:
        f.write(tappers.__str__())

    await message.reply(tap_message_content)


async def stats(message):
    if message.author.id not in tappers:
        await message.reply('No stats yet, start tapping!')
    tapper = tappers[message.author.id]

    stats_message_content = (f'### {message.author.mention}\'s stats\n'
                             f'- tapped {tapper["taps"]:,} times\n'
                             f'- {tapper["spent"]:,} mesos spent\n'
                             f'- currently at ★ {tapper["current"]}, {tapper["current_booms"]:,} booms\n'
                             f'- record is ★ {tapper["highest"]}, {tapper["highest_booms"]:,} booms\n')
    await message.reply(stats_message_content)


async def leaderboard(message):
    sorted_tappers = sorted(tappers.values(),
                            key=lambda tapper: (-tapper['highest'], tapper['highest_booms'], tapper['spent']))
    leaderboard_message_content = f'### Leaderboard\n'
    message = await message.reply(leaderboard_message_content)
    for i in range(min(5, len(sorted_tappers))):
        tapper = sorted_tappers[i]
        leaderboard_message_content += f'{i}. ★ {tapper["highest"]}, {tapper["highest_booms"]} booms - <@{tapper["id"]}>\n'
    await message.edit(content=leaderboard_message_content)


starforce_simulator.run(config.BOT_TOKEN)
