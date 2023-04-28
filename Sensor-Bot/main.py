from psutil import (
    cpu_percent,
    net_io_counters,
    disk_io_counters,
    sensors_fans,
    sensors_temperatures,
    virtual_memory,
    disk_usage,
    boot_time,
)
from discord import Client, Intents, Embed
from datetime import datetime
from discord.ext import tasks
from random import choice
from json import load
from os import environ

if "discordToken" in environ.keys():
    botToken = environ["botToken"]
else:
    with open("secerets.json", "r", encoding="utf-8") as f:
        botToken = load(f)["botToken"]

colors = [
    0xFFE4E1,
    0x00FF7F,
    0xD8BFD8,
    0xDC143C,
    0xFF4500,
    0xDEB887,
    0xADFF2F,
    0x800000,
    0x4682B4,
    0x006400,
    0x808080,
    0xA0522D,
    0xF08080,
    0xC71585,
    0xFFB6C1,
    0x00CED1,
]
home_server = False


class MyClient(Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        monitor.start(self)


intents = Intents.default()
client = MyClient(intents=intents)


@tasks.loop(seconds=15.0)
async def monitor(self):
    with open("/proc/uptime", "r") as f:
        uptime_seconds = float(f.readline().split()[0])
        if uptime_seconds < 60:
            uptime = f"{round(uptime_seconds,2)} Secs"
        elif uptime_seconds >= 60 and uptime_seconds < 3600:
            uptime = f"{round(uptime_seconds/60,2)} Mins"
        elif uptime_seconds >= 3600 and uptime_seconds < 86400:
            uptime = f"{round(uptime_seconds/3600,2)} Hours"
        elif uptime_seconds >= 86400 and uptime_seconds < 604800:
            uptime = f"{round(uptime_seconds/86400,2)} Days"
        elif uptime_seconds >= 604800:
            uptime = f"{round(uptime_seconds/604800,2)} Weeks"
    GB = 1000000000
    C = " \N{DEGREE SIGN}" + "C"
    embed = Embed(title="Server Monitor", color=choice(colors))
    embed.add_field(name="Cpu Ussage:", value=str(cpu_percent()) + "%", inline=True)
    embed.add_field(
        name="Network Data Sent:",
        value=f"{round(net_io_counters().bytes_sent/1000000,2)} MB",
        inline=True,
    )
    embed.add_field(
        name="Network Data Received:",
        value=f"{round(net_io_counters().bytes_recv/1000000,2)} MB",
        inline=True,
    )
    embed.add_field(
        name="Disk Data Written:",
        value=f"{round(disk_io_counters().write_bytes/1000000,2)} MB",
        inline=True,
    )
    embed.add_field(
        name="Disk Data Read:",
        value=f"{round(disk_io_counters().read_bytes/1000000,2)} MB",
        inline=True,
    )
    if home_server:
        embed.add_field(name="Fan RPM:", value=sensors_fans()["asus"][0][1], inline=True)
        embed.add_field(
            name="MB Temp:",
            value=str(sensors_temperatures()["asus"][0][1]) + C,
            inline=True,
        )
        embed.add_field(
            name="Cpu Temp:",
            value=str(sensors_temperatures()["coretemp"][0][1]) + C,
            inline=True,
        )
    embed.add_field(name="Uptime:", value=uptime, inline=True)
    embed.add_field(
        name="Ram Ussage:",
        value=f"{round(virtual_memory().used/GB,2)} GB/{round(virtual_memory().total/GB,2)} GB({virtual_memory().percent}%)",
        inline=False,
    )
    embed.add_field(
        name="Storage Used:",
        value=f'{round(disk_usage("/").used/GB,2)} GB/ {round(disk_usage("/").total/GB,2)} GB({disk_usage("/").percent}%)',
        inline=False,
    )
    embed.set_footer(
        text=f'Last updated: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}, Last Boot: {datetime.fromtimestamp(boot_time()).strftime("%d/%m/%Y %H:%M:%S")}'
    )
    channel = client.get_channel(1018181447128985610)
    async for message in channel.history(limit=200):
        if message.author == self.user:
            await message.edit(embed=embed)
            break
    else:
        await channel.send(embed=embed)


client.run(botToken)