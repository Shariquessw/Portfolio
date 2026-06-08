import discord
from discord.ext import commands
from discord import app_commands
from google import genai
import os
import sqlite3
from dotenv import load_dotenv


# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

client_ai = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# 2. DATABASE INITIALIZATION
# ==========================================
conn = sqlite3.connect('multiverse.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS server_theories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER,
        user_mention TEXT,
        title TEXT,
        law_text TEXT
    )
''')
conn.commit()

# ==========================================
# 3. BOT EVENTS & SLASH COMMANDS
# ==========================================
@bot.event
async def on_ready():
    try:
        # Syncs the commands cleanly without wiping the bot's memory first!
        synced = await bot.tree.sync()
        print(f"✅ SYNC COMPLETE: Registered {len(synced)} modern slash commands!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
        
    print(f'The Multiverse Oracle is online as {bot.user}')

@bot.tree.command(name='theory', description="Displays all established physics laws in this universe.")
async def theory(interaction: discord.Interaction):
    cursor.execute('SELECT title, user_mention, law_text FROM server_theories WHERE server_id = ?', (interaction.guild_id,))
    rows = cursor.fetchall()
    
    total_laws = len(rows) + 1 
    
    embed = discord.Embed(
        title="🌌 The Multiverse Theories",
        description=f"Total established laws in this universe: **{total_laws}**\nEvery law below is currently active simultaneously.",
        color=0x00ffff
    )
    
    # --- IMPORTANT: Paste your actual User ID here! ---
    embed.add_field(
        name="1. The Recycling Universe", 
        value="**Lead Physicist:** <@1453441629343056026>\nThe **Recycling Universe** hypothesis proposes that the cosmos operates in a self-sustaining, endless loop rather than expanding infinitely into a cold, dark void. In this model, the universe eventually utilizes its own internal energy to halt its expansion and begin a massive, gravitational contraction. All matter and energy are pulled back into a dense singularity—a **Big Crunch** —which perfectly conserves and recycles the cosmic energy. This recycled energy then immediately triggers the next **Big Bang**, initiating a brand new cycle of expansion in an eternal cosmic heartbeat.", 
        inline=False
    )
    
    count = 2
    for row in rows:
        title = row[0]
        user_mention = row[1]
        law_text = row[2]
        
        # Limit max fields to prevent Discord from crashing
        if count >= 25:
            embed.add_field(name="...", value="*The multiverse has too many laws to display them all here!*", inline=False)
            break
            
        # Limit text length to prevent 1024-character Discord limit crash
        if len(law_text) > 950:
            law_text = law_text[:950] + "... *(Text shortened for reality stability)*"
            
        embed.add_field(
            name=f"{count}. {title}", 
            value=f"**Added by:** {user_mention}\n{law_text}", 
            inline=False
        )
        count += 1
        
    embed.set_footer(text="Official Multiverse Oracle Database")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='addlaw', description="Add a new permanent law of physics with a title.")
@app_commands.describe(title="Give your theory a unique name.", new_law="Type the new universal law you want to add.")
async def addlaw(interaction: discord.Interaction, title: str, new_law: str):
    # Check if the title already exists in this server
    cursor.execute('SELECT 1 FROM server_theories WHERE server_id = ? AND LOWER(title) = LOWER(?)', (interaction.guild_id, title))
    if cursor.fetchone():
        await interaction.response.send_message(f"⚠️ A theory with the title **'{title}'** already exists! Please choose a different name.", ephemeral=True)
        return

    # If it's unique, save it to the database
    cursor.execute('''
        INSERT INTO server_theories (server_id, user_mention, title, law_text) 
        VALUES (?, ?, ?, ?)
    ''', (interaction.guild_id, interaction.user.mention, title, new_law))
    conn.commit()
    
    await interaction.response.send_message(f"🌌 **New Reality Forged: {title}**\n**By:** {interaction.user.mention}\n> {new_law}\n\n*Check `/theory` to see the updated list of reality!*")

@bot.tree.command(name='deletelaw', description="Erase a specific theory from the multiverse.")
@app_commands.describe(title="Type the exact title of the theory you want to delete.")
async def deletelaw(interaction: discord.Interaction, title: str):
    cursor.execute('DELETE FROM server_theories WHERE server_id = ? AND LOWER(title) = LOWER(?)', (interaction.guild_id, title))
    
    if cursor.rowcount > 0:
        conn.commit()
        await interaction.response.send_message(f"🗑️ The theory **'{title}'** has been successfully erased from reality.")
    else:
        await interaction.response.send_message(f"❌ Could not find a theory named **'{title}'**. Make sure you spelled it exactly as it appears in `/theory`!", ephemeral=True)

@bot.tree.command(name='oracle', description="Asks the AI to simulate life under the CURRENT COMBINED physics laws.")
@app_commands.describe(user_prompt="What do you want to ask the oracle?")
async def oracle(interaction: discord.Interaction, user_prompt: str = "Tell me about daily life today."):
    # Defer response to give the AI time to think
    await interaction.response.defer()
    
    cursor.execute('SELECT title, law_text FROM server_theories WHERE server_id = ?', (interaction.guild_id,))
    rows = cursor.fetchall()
    
    all_laws = "1. The Recycling Universe: The universe operates in a self-sustaining loop.\n"
    for i, row in enumerate(rows):
        all_laws += f"{i+2}. {row[0]}: {row[1]}\n"
    
    system_prompt = (
        "You are the Multiverse Oracle. You simulate alternate realities. "
        f"Today's reality is governed by ALL of these combined laws at the exact same time:\n{all_laws}\n"
        f"Respond to the user's prompt based on these physics laws in a fun, sci-fi tone: {user_prompt}"
    )
    
    try:
        response = client_ai.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt
        )
        
        reply = response.text
        
        # SPLIT LONG MESSAGES: Loops through AI reply and sends in 2000-character chunks
        for i in range(0, len(reply), 2000):
            await interaction.followup.send(reply[i:i+2000])
            
    except Exception as e:
        print(f"Error: {e}")
        await interaction.followup.send("The multiverse connection fractured. Try again!")

# ==========================================
# 4. START THE SYSTEMS
# ==========================================

bot.run(DISCORD_TOKEN)
