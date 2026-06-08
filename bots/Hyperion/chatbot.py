import os
import discord
import requests
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from groq import Groq

# ---------------- LOAD ENV ----------------
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------------- AI CLIENT ----------------
client = Groq(api_key=GROQ_API_KEY)

# ---------------- DISCORD SETUP ----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- DATA ----------------
chat_memory = {}          # per-server chat memory
allowed_channels = {}     # chatbot channel per server
meme_channels = {}        # meme channel per server
MEME_INTERVAL = 15        # minutes

# ---------------- LOAD SAVED CHANNELS ----------------
if os.path.exists("channels.txt"):
    with open("channels.txt", "r") as f:
        for line in f:
            if ":" in line:
                gid, cid = line.strip().split(":")
                allowed_channels[int(gid)] = int(cid)

def save_channels():
    with open("channels.txt", "w") as f:
        for gid, cid in allowed_channels.items():
            f.write(f"{gid}:{cid}\n")

# ---------------- BOT READY ----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    auto_meme.start()
    print(f"Logged in as {bot.user}")

# ---------------- SET CHAT CHANNEL ----------------
@bot.tree.command(name="setchannel", description="Set chatbot channel for this server")
async def setchannel(interaction: discord.Interaction):
    allowed_channels[interaction.guild.id] = interaction.channel.id
    save_channels()
    await interaction.response.send_message(
        f"✅ Chatbot restricted to <#{interaction.channel.id}>",
        ephemeral=True
    )

# ---------------- SET MEME CHANNEL ----------------
@bot.tree.command(name="setmemechannel", description="Set meme channel")
async def setmemechannel(interaction: discord.Interaction):
    meme_channels[interaction.guild.id] = interaction.channel.id
    await interaction.response.send_message("😂 Meme channel set!", ephemeral=True)

# ---------------- TRANSLATE ----------------
@bot.tree.command(name="translate", description="Translate text")
@app_commands.describe(language="Target language", text="Text to translate")
async def translate(interaction: discord.Interaction, language: str, text: str):
    result = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"Translate into {language}"},
            {"role": "user", "content": text}
        ]
    )
    await interaction.response.send_message(result.choices[0].message.content)

# ---------------- IMAGE MEME ----------------
@bot.tree.command(name="meme", description="Send a meme")
async def meme(interaction: discord.Interaction):
    data = requests.get("https://meme-api.com/gimme").json()
    await interaction.response.send_message(data["url"])

# ---------------- AUTO MEME ----------------
@tasks.loop(minutes=MEME_INTERVAL)
async def auto_meme():
    for gid, cid in meme_channels.items():
        channel = bot.get_channel(cid)
        if channel:
            meme = requests.get("https://meme-api.com/gimme").json()
            await channel.send(meme["url"])

# ---------------- CHAT LISTENER ----------------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.guild.id not in allowed_channels:
        return

    if message.channel.id != allowed_channels[message.guild.id]:
        return

    chat_memory.setdefault(message.guild.id, [])
    chat_memory[message.guild.id].append(
        {"role": "user", "content": message.content}
    )
    chat_memory[message.guild.id] = chat_memory[message.guild.id][-10:]

    result = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=chat_memory[message.guild.id]
    )

    reply = result.choices[0].message.content
    chat_memory[message.guild.id].append(
        {"role": "assistant", "content": reply}
    )

    # -------- SPLIT LONG MESSAGES --------
    for i in range(0, len(reply), 2000):
        await message.channel.send(reply[i:i+2000])

# ---------------- RUN ----------------

bot.run(DISCORD_TOKEN)
