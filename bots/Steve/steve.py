import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# BOT SETUP & INTENTS
# ----------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True  # Required to read messages and use commands
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------------------------------------------------
# THE MEMORY TRACKER
# Format: { user_id: { "general": [used_indexes], "savage": [used_indexes] } }
# ----------------------------------------------------------------------
user_roast_history = {}

# ----------------------------------------------------------------------
# DYNAMIC ROAST GENERATORS & LISTS
# ----------------------------------------------------------------------
def generate_minecraft_scorecard(mention):
    """Generates a scorecard with completely randomized, embarrassing stats."""
    blocks = random.randint(2, 19)
    junk_block = random.choice(["dirt", "diorite", "granite", "coarse dirt", "gravel"])
    void_falls = random.randint(45, 300)
    deaths = random.choice(["a baby zombie", "fall damage while bridging", "their own TNT", "a wandering trader", "a berry bush"])
    
    return (
        f"📊 **Pulling real-time server stats for {mention}...**\n"
        f"* **Blocks Mined:** {blocks} (all {junk_block})\n"
        f"* **Diamonds Found:** 0\n"
        f"* **Times Fallen into the Void:** {void_falls}\n"
        f"* **Most Embarrassing Death:** Killed by {deaths}.\n"
        f"* **Clutch Potential:** Mathematically impossible."
    )

GENERAL_ROASTS = [
    "I asked a supercomputer to find {mention}'s best play, and it overheated trying to find one.",
    "{mention} has a clear 'Main Character' aesthetic, but their actual presence gives off major background NPC energy.",
    "Therapist: 'The thrower isn't real, they can't hurt you.'\nThe Thrower: *Literally {mention} every single game.*",
    "Nobody:\nAbsolutely nobody:\n{mention}: 'Guys, watch this insane play!' *(proceeds to immediately disconnect)*"
]

SAVAGE_ROASTS = [
    "If lagging was a competitive sport, {mention} would finally have a world championship.",
    "{mention} changes their Discord status to a sad song lyric every single time they lose a 1v1.",
    "Watching {mention} attempt to clutch up is the closest human experience to watching a simulation completely glitch out.",
    "{mention} is the reason the server needs a dedicated 'emotional support' voice channel."
]

def get_unique_roast(user_id, category_name, roast_list):
    """Fetches a joke the user hasn't seen yet and updates their history."""
    # Initialize the user in the memory dictionary if they don't exist yet
    if user_id not in user_roast_history:
        user_roast_history[user_id] = {"general": [], "savage": []}
        
    used_indexes = user_roast_history[user_id][category_name]
    
    # If the user has seen every single roast, reset their history for this category
    if len(used_indexes) >= len(roast_list):
        used_indexes.clear()
        
    # Find which jokes the user hasn't seen yet
    available_indexes = [i for i in range(len(roast_list)) if i not in used_indexes]
    
    # Pick a random joke from the un-seen list
    chosen_index = random.choice(available_indexes)
    
    # Add it to their history so they don't get it again soon
    used_indexes.append(chosen_index)
    
    return roast_list[chosen_index]

# ----------------------------------------------------------------------
# BOT EVENTS & COMMANDS
# ----------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="roast", description="Deliver a randomized, non-repeating roast!")
@app_commands.describe(member="The target of your roast", category="Choose the style")
@app_commands.choices(category=[
    app_commands.Choice(name="Minecraft Scorecard", value="minecraft"),
    app_commands.Choice(name="General Memes", value="general"),
    app_commands.Choice(name="Savage Hits", value="savage")
])
async def roast(interaction: discord.Interaction, member: discord.Member, category: app_commands.Choice[str]):
    # Defer the response so Discord doesn't time out while the bot is "thinking"
    await interaction.response.defer()

    target_mention = member.mention
    user_id = member.id
    response_text = ""

    # Generate the unique roast based on the user's category choice
    if category.value == "minecraft":
        # Scorecards are fully dynamic, so they bypass the memory tracker
        response_text = generate_minecraft_scorecard(target_mention)
    elif category.value == "general":
        response_text = get_unique_roast(user_id, "general", GENERAL_ROASTS).format(mention=target_mention)
    elif category.value == "savage":
        response_text = get_unique_roast(user_id, "savage", SAVAGE_ROASTS).format(mention=target_mention)

    # Send the final formatted message
    await interaction.followup.send(response_text)

# ----------------------------------------------------------------------
# SECURE EXECUTION
# ----------------------------------------------------------------------
# Load environment variables from the .env file
load_dotenv()

# Securely grab the token
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("CRITICAL ERROR: No token found. Please check your .env file.")
else:
    bot.run(TOKEN)