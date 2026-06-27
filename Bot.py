"""
███╗   ██╗ ██████╗ ██╗   ██╗
████╗  ██║██╔═══██╗██║   ██║
██╔██╗ ██║██║   ██║██║   ██║
██║╚██╗██║██║   ██║╚██╗ ██╔╝
██║ ╚████║╚██████╔╝ ╚████╔╝
╚═╝  ╚═══╝ ╚═════╝   ╚═══╝

Nov — Discord bot powered by Pollinations AI
Text · Images · Audio · Video · BYOP
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import io
import urllib.parse
import random
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
BASE_URL      = "https://gen.pollinations.ai/v1"
AUTH_URL      = "https://enter.pollinations.ai/api/device"
APP_KEY       = "pk_POwfuMPTfQYz66O5"  # Nov App Key
BOT_NAME      = "Nov"
BOT_COLOR     = 0x5865F2
BOT_VERSION   = "1.1.0"

# Chiavi per utente { user_id: "sk_..." }
USER_KEYS: dict[int, str] = {}

# Modelli per utente { user_id: { tipo: modello } }
USER_MODELS: dict[int, dict] = {}

# Memoria utenti { user_id: { "name": str, ... } }
USER_MEMORY: dict[int, dict] = {}

# Thread di chat attivi { thread_id: { user_id, model, history } }
CHAT_THREADS: dict[int, dict] = {}

DEFAULT_MODELS = {
    "text":  "ChatGPT 4o",
    "image": "FLUX.1 Dev",
    "audio": "Nova",
    "video": "Google Veo 2 (PAID)",
}

# Modelli reali Pollinations — quelli con (PAID) richiedono crediti Pollen
# Mappa: nome visualizzato → ID API reale
MODEL_DISPLAY_TO_ID = {
    # TEXT
    "ChatGPT 4o mini":           "openai-fast",
    "ChatGPT 4o":                "openai",
    "ChatGPT 4o Large":          "openai-large",
    "ChatGPT o3 mini":           "openai-reasoning",
    "ChatGPT 5.4 (PAID)":        "gpt-5.4",
    "ChatGPT 5.4 mini (PAID)":   "gpt-5.4-mini",
    "Claude 3 Haiku":            "claude-fast",
    "Claude 3.5 Sonnet (PAID)":  "claude",
    "Claude 3.7 Sonnet (PAID)":  "claude-large",
    "Claude Opus 4.6 (PAID)":    "claude-opus-4.6",
    "Claude Opus 4.7 (PAID)":    "claude-opus-4.7",
    "Gemini 2.0 Flash":          "gemini-fast",
    "Gemini 2.5 Flash":          "gemini",
    "Gemini 2.5 Flash Thinking": "gemini-thinking",
    "Gemini 2.5 Pro":            "gemini-search",
    "DeepSeek V3":               "deepseek",
    "DeepSeek R1 (PAID)":        "deepseek-pro",
    "Mistral Small 3.2":         "mistral-small-3.2",
    "Mistral 7B":                "mistral",
    "Mistral Large (PAID)":      "mistral-large",
    "Llama 4 Scout":             "llama-scout",
    "Llama 4 Maverick":          "llama-maverick",
    "Llama 3.3 70B":             "llama",
    "Qwen2.5 Coder":             "qwen-coder",
    "Qwen2.5 72B":               "qwen-large",
    "Qwen2.5 VL":                "qwen-vision",
    "Grok 3 (PAID)":             "grok",
    "Grok 3 Large (PAID)":       "grok-large",
    "Perplexity (PAID)":         "perplexity",
    "Perplexity Deep (PAID)":    "perplexity-deep",
    "Perplexity R1 (PAID)":      "perplexity-reasoning",
    "Mercury":                   "mercury",
    "Kimi":                      "kimi",
    "GLM-4":                     "glm",
    "Phi-4":                     "phi",
    # IMAGE
    "FLUX.1 Schnell":            "flux-schnell",
    "FLUX.1 Dev":                "flux",
    "FLUX.1 Realism":            "flux-realism",
    "FLUX.1 Anime":              "flux-anime",
    "FLUX.1 3D":                 "flux-3d",
    "FLUX.1 Pro (PAID)":         "kontext",
    "DALL-E 3 (PAID)":           "gptimage",
    "DALL-E 3 HD (PAID)":        "gptimage-large",
    "GPT Image 2 (PAID)":        "gpt-image-2",
    "Seedream 3.0 (PAID)":       "seedream",
    "Seedream Pro (PAID)":       "seedream-pro",
    "Seedream 5 (PAID)":         "seedream5",
    "Ideogram v4 Turbo (PAID)":  "ideogram-v4-turbo",
    "Ideogram v4 (PAID)":        "ideogram-v4-balanced",
    "Ideogram v4 Quality (PAID)":"ideogram-v4-quality",
    "Wan Image (PAID)":          "wan-image",
    "Wan Image Pro (PAID)":      "wan-image-pro",
    "Grok Imagine (PAID)":       "grok-imagine",
    "Grok Imagine Pro (PAID)":   "grok-imagine-pro",
    "Turbo":                     "turbo",
    "Nova Canvas (PAID)":        "nova-canvas",
    # AUDIO (voci TTS)
    "Nova":                      "nova",
    "Alloy":                     "alloy",
    "Echo":                      "echo",
    "Fable":                     "fable",
    "Onyx":                      "onyx",
    "Shimmer":                   "shimmer",
    "Ash":                       "ash",
    "Ballad":                    "ballad",
    "Coral":                     "coral",
    "Sage":                      "sage",
    "Verse":                     "verse",
    "ElevenLabs (PAID)":         "elevenlabs",
    "ElevenLabs Flash (PAID)":   "elevenflash",
    "ElevenLabs Multilingual (PAID)": "eleven-multilingual-v2",
    "ElevenLabs Music (PAID)":   "elevenmusic",
    "ElevenLabs SFX (PAID)":     "eleven-sfx",
    "ACE Step (PAID)":           "acestep",
    "Stable Audio 3 (PAID)":     "stable-audio-3-medium",
    "Stable Audio 3 Large (PAID)":"stable-audio-3-large",
    # VIDEO
    "Google Veo 2 (PAID)":       "veo",
    "Seedance Pro (PAID)":       "seedance-pro",
    "Seedance 2.0 (PAID)":       "seedance-2.0",
    "Wan (PAID)":                "wan",
    "Wan Fast (PAID)":           "wan-fast",
    "Wan Pro (PAID)":            "wan-pro",
    "Wan Pro 1080p (PAID)":      "wan-pro-1080p",
    "Grok Video Pro (PAID)":     "grok-video-pro",
    "LTX Video 2 (PAID)":        "ltx-2",
    "Nova Reel (PAID)":          "nova-reel",
}

# Mappa inversa: ID API → nome visualizzato
MODEL_ID_TO_DISPLAY = {v: k for k, v in MODEL_DISPLAY_TO_ID.items()}

KNOWN_MODELS = {
    "text": [k for k in MODEL_DISPLAY_TO_ID if k in [
        "ChatGPT 4o mini", "ChatGPT 4o", "ChatGPT 4o Large", "ChatGPT o3 mini",
        "ChatGPT 5.4 (PAID)", "ChatGPT 5.4 mini (PAID)",
        "Claude 3 Haiku", "Claude 3.5 Sonnet (PAID)", "Claude 3.7 Sonnet (PAID)",
        "Claude Opus 4.6 (PAID)", "Claude Opus 4.7 (PAID)",
        "Gemini 2.0 Flash", "Gemini 2.5 Flash", "Gemini 2.5 Flash Thinking", "Gemini 2.5 Pro",
        "DeepSeek V3", "DeepSeek R1 (PAID)",
        "Mistral Small 3.2", "Mistral 7B", "Mistral Large (PAID)",
        "Llama 4 Scout", "Llama 4 Maverick", "Llama 3.3 70B",
        "Qwen2.5 Coder", "Qwen2.5 72B", "Qwen2.5 VL",
        "Grok 3 (PAID)", "Grok 3 Large (PAID)",
        "Perplexity (PAID)", "Perplexity Deep (PAID)", "Perplexity R1 (PAID)",
        "Mercury", "Kimi", "GLM-4", "Phi-4",
    ]],
    "image": [k for k in MODEL_DISPLAY_TO_ID if k in [
        "FLUX.1 Schnell", "FLUX.1 Dev", "FLUX.1 Realism", "FLUX.1 Anime", "FLUX.1 3D", "Turbo",
        "FLUX.1 Pro (PAID)", "DALL-E 3 (PAID)", "DALL-E 3 HD (PAID)", "GPT Image 2 (PAID)",
        "Seedream 3.0 (PAID)", "Seedream Pro (PAID)", "Seedream 5 (PAID)",
        "Ideogram v4 Turbo (PAID)", "Ideogram v4 (PAID)", "Ideogram v4 Quality (PAID)",
        "Wan Image (PAID)", "Wan Image Pro (PAID)",
        "Grok Imagine (PAID)", "Grok Imagine Pro (PAID)", "Nova Canvas (PAID)",
    ]],
    "audio": [k for k in MODEL_DISPLAY_TO_ID if k in [
        "Nova", "Alloy", "Echo", "Fable", "Onyx", "Shimmer",
        "Ash", "Ballad", "Coral", "Sage", "Verse",
        "ElevenLabs (PAID)", "ElevenLabs Flash (PAID)", "ElevenLabs Multilingual (PAID)",
        "ElevenLabs Music (PAID)", "ElevenLabs SFX (PAID)",
        "ACE Step (PAID)", "Stable Audio 3 (PAID)", "Stable Audio 3 Large (PAID)",
    ]],
    "video": [k for k in MODEL_DISPLAY_TO_ID if k in [
        "Google Veo 2 (PAID)", "Seedance Pro (PAID)", "Seedance 2.0 (PAID)",
        "Wan (PAID)", "Wan Fast (PAID)", "Wan Pro (PAID)", "Wan Pro 1080p (PAID)",
        "Grok Video Pro (PAID)", "LTX Video 2 (PAID)", "Nova Reel (PAID)",
    ]],
}

# Converte nome visualizzato → ID API reale
def clean_model(name: str) -> str:
    return MODEL_DISPLAY_TO_ID.get(name, name.replace(" (PAID)", "").strip())

TYPE_EMOJI = {"text": "💬", "image": "🖼️", "audio": "🔊", "video": "🎬"}

# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def get_key(user_id: int) -> str | None:
    return USER_KEYS.get(user_id) or os.getenv("POLLINATIONS_KEY") or None

def get_model(user_id: int, tipo: str) -> str:
    return clean_model(USER_MODELS.get(user_id, {}).get(tipo, DEFAULT_MODELS[tipo]))

def get_memory(user_id: int) -> dict:
    return USER_MEMORY.get(user_id, {})

def set_memory(user_id: int, key: str, value: str):
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {}
    USER_MEMORY[user_id][key] = value

def build_system_prompt(user_id: int, custom: str) -> str:
    mem = get_memory(user_id)
    name_line = f"The user's name is {mem['name']}. " if mem.get("name") else ""
    extra = f" {custom}" if custom else ""
    return (
        f"Your name is Nov. You are a helpful AI assistant living inside Discord, "
        f"powered by Pollinations AI. Always refer to yourself as Nov, never as ChatGPT, "
        f"Claude, Gemini, or any other AI name. {name_line}{extra}"
    )

def auth_headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

async def api_post_json(session, url, payload, key):
    async with session.post(url, headers=auth_headers(key), json=payload) as resp:
        resp.raise_for_status()
        return await resp.json()

async def api_post_bytes(session, url, payload, key):
    async with session.post(url, headers=auth_headers(key), json=payload) as resp:
        resp.raise_for_status()
        return await resp.read()

async def api_get_bytes(session, url):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.read()

def no_key_embed():
    return discord.Embed(
        title="🔑 No API key connected",
        description=(
            "You need to connect your Pollinations key first!\n\n"
            "**→ Use `/connect` and paste your `sk_...` key**\n\n"
            "Get your key at [enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xED4245
    )

def invalid_model_embed(tipo: str, name: str):
    valid = "\n".join(f"`{m}`" for m in KNOWN_MODELS[tipo])
    return discord.Embed(
        title="❌ Unknown model",
        description=f"`{name}` is not a valid **{tipo}** model.\n\n**Available models:**\n{valid}",
        color=0xED4245
    )

def is_valid_model(tipo: str, name: str) -> bool:
    return clean_model(name) in [clean_model(m) for m in KNOWN_MODELS[tipo]]

# ──────────────────────────────────────────────
#  BOT SETUP
# ──────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="pollinations.ai ✨")
    )
    print(f"✅  {BOT_NAME} v{BOT_VERSION} online as {bot.user}")

# ──────────────────────────────────────────────
#  AUTOCOMPLETE per model name
# ──────────────────────────────────────────────
async def model_name_autocomplete(interaction: discord.Interaction, current: str):
    tipo = interaction.namespace.type  # prende il valore già scelto per "type"
    if not tipo or tipo not in KNOWN_MODELS:
        # Se non ha ancora scelto il tipo, mostra tutti
        all_models = [m for models in KNOWN_MODELS.values() for m in models]
        choices = [app_commands.Choice(name=m, value=m) for m in all_models if current.lower() in m.lower()]
    else:
        choices = [
            app_commands.Choice(name=m, value=m)
            for m in KNOWN_MODELS[tipo]
            if current.lower() in m.lower()
        ]
    return choices[:25]

# ──────────────────────────────────────────────
#  /connect — Device Flow BYOP
# ──────────────────────────────────────────────
@bot.tree.command(name="connect", description="Connect your Pollinations account to Nov")
async def cmd_connect(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{AUTH_URL}/code",
                headers={"Content-Type": "application/json"},
                json={"client_id": APP_KEY, "scope": "generate"}
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        device_code = data["device_code"]
        user_code   = data["user_code"]

        embed = discord.Embed(
            title="🔑 Connect your Pollinations account",
            description=(
                f"**1.** Go to **[enter.pollinations.ai/device](https://enter.pollinations.ai/device)**\n"
                f"**2.** Enter this code:\n\n"
                f"# `{user_code}`\n\n"
                f"**3.** Authorize Nov and come back here!\n\n"
                f"*Waiting for authorization... (expires in 10 minutes)*"
            ),
            color=BOT_COLOR
        )
        embed.set_footer(text="Your Pollen pays for your usage • Nov earns a small fee")
        await interaction.followup.send(embed=embed, ephemeral=True)

        import asyncio
        async with aiohttp.ClientSession() as session:
            for _ in range(120):
                await asyncio.sleep(5)
                async with session.post(
                    f"{AUTH_URL}/token",
                    headers={"Content-Type": "application/json"},
                    json={"device_code": device_code}
                ) as poll_resp:
                    poll_data = await poll_resp.json()

                if poll_data.get("access_token"):
                    sk = poll_data["access_token"]
                    USER_KEYS[interaction.user.id] = sk
                    masked = sk[:6] + "•" * max(0, len(sk) - 9) + sk[-3:]
                    try:
                        async with session.get(
                            f"{AUTH_URL}/userinfo",
                            headers={"Authorization": f"Bearer {sk}"}
                        ) as ui_resp:
                            ui = await ui_resp.json()
                            username = ui.get("preferred_username") or ui.get("name", "")
                            if username:
                                set_memory(interaction.user.id, "pollinations_username", username)
                    except Exception:
                        pass
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="✅ Connected!",
                            description=f"Your Pollinations account is now linked to Nov.\n`{masked}`\n\nYou can now use all commands!",
                            color=0x57F287
                        ).set_footer(text="Only you can see this • Key stored in memory only"),
                        ephemeral=True
                    )
                    return

                if poll_data.get("error") == "access_denied":
                    await interaction.followup.send(
                        embed=discord.Embed(title="❌ Authorization denied.", color=0xED4245),
                        ephemeral=True
                    )
                    return

        await interaction.followup.send(
            embed=discord.Embed(title="⏰ Timed out", description="You took too long. Run `/connect` again.", color=0xFEE75C),
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245),
            ephemeral=True
        )

@bot.tree.command(name="disconnect", description="Remove your connected Pollinations account")
async def cmd_disconnect(interaction: discord.Interaction):
    removed = interaction.user.id in USER_KEYS
    if removed:
        del USER_KEYS[interaction.user.id]
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Disconnected." if removed else "You didn't have an account connected.",
            color=0x57F287 if removed else 0xFEE75C
        ), ephemeral=True
    )

# ──────────────────────────────────────────────
#  /remember — salva info su di te
# ──────────────────────────────────────────────
@bot.tree.command(name="remember", description="Tell Nov something to remember about you")
@app_commands.describe(
    key="What to remember (e.g. name, language, style)",
    value="The value (e.g. Marco, Italian, casual)"
)
async def cmd_remember(interaction: discord.Interaction, key: str, value: str):
    set_memory(interaction.user.id, key.lower(), value)
    await interaction.response.send_message(
        embed=discord.Embed(
            title="🧠 Remembered!",
            description=f"**{key}** → `{value}`\nI'll keep this in mind for our chats.",
            color=0x57F287
        ), ephemeral=True
    )

@bot.tree.command(name="forget", description="Clear everything Nov remembers about you")
async def cmd_forget(interaction: discord.Interaction):
    USER_MEMORY.pop(interaction.user.id, None)
    await interaction.response.send_message(
        embed=discord.Embed(title="🧹 Memory cleared!", color=0x57F287),
        ephemeral=True
    )

# ──────────────────────────────────────────────
#  /text — apre thread di chat
# ──────────────────────────────────────────────
@bot.tree.command(name="text", description="Open an AI chat thread")
@app_commands.describe(prompt="Your first message", system="Optional custom system prompt")
async def cmd_text(interaction: discord.Interaction, prompt: str, system: str = ""):
    if not interaction.guild:
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ Server only", description="Use this command in a server channel.", color=0xED4245),
            ephemeral=True
        )
        return

    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    model  = get_model(interaction.user.id, "text")
    system = build_system_prompt(interaction.user.id, system)
    await interaction.response.defer(thinking=True)

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt}
                ],
                "max_tokens": 1500,
            }
            data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
            reply = data["choices"][0]["message"]["content"]

        # Risposta silenziosa all'interazione
        await interaction.followup.send("💬 Opening chat thread...", ephemeral=True)

        # Manda il messaggio nel canale direttamente
        channel = interaction.channel
        embed_intro = discord.Embed(
            description=f"**{interaction.user.display_name}:** {prompt}",
            color=BOT_COLOR
        )
        embed_intro.set_author(name=f"Nov Chat - {model}")
        embed_intro.set_footer(text="Thread opened - just type here to keep chatting!")
        msg = await channel.send(embed=embed_intro)

        # Crea thread
        thread = await msg.create_thread(
            name=f"Nov - {interaction.user.display_name} - {prompt[:40]}",
            auto_archive_duration=60
        )

        # Manda risposta nel thread
        embed_reply = discord.Embed(description=reply[:4000], color=BOT_COLOR)
        embed_reply.set_footer(text=f"{model} - type /close to end")
        await thread.send(embed=embed_reply)

        # Salva stato thread
        CHAT_THREADS[thread.id] = {
            "user_id": interaction.user.id,
            "model":   model,
            "system":  system,
            "key":     key,
            "history": [
                {"role": "system",    "content": system},
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": reply},
            ]
        }

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  on_message — risponde nei thread di chat
# ──────────────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not isinstance(message.channel, discord.Thread):
        await bot.process_commands(message)
        return

    thread_data = CHAT_THREADS.get(message.channel.id)
    if not thread_data:
        await bot.process_commands(message)
        return

    if message.author.id != thread_data["user_id"]:
        return

    if message.content.strip().lower() in ["/close", "!close"]:
        del CHAT_THREADS[message.channel.id]
        await message.channel.send(embed=discord.Embed(
            title="✅ Chat closed",
            description="Use `/text` to start a new chat!",
            color=0x57F287
        ))
        await message.channel.edit(archived=True, locked=True)
        return

    async with message.channel.typing():
        history = thread_data["history"]
        history.append({"role": "user", "content": message.content})

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model":    thread_data["model"],
                    "messages": history,
                    "max_tokens": 1500,
                }
                data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, thread_data["key"])
                reply = data["choices"][0]["message"]["content"]

            history.append({"role": "assistant", "content": reply})
            embed = discord.Embed(description=reply[:4000], color=BOT_COLOR)
            embed.set_footer(text=f"{thread_data['model']} - type /close to end")
            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /image
# ──────────────────────────────────────────────
@bot.tree.command(name="image", description="Generate an image with AI")
@app_commands.describe(prompt="Describe the image", size="Image size")
@app_commands.choices(size=[
    app_commands.Choice(name="1024x1024 (square)",    value="1024x1024"),
    app_commands.Choice(name="1792x1024 (landscape)", value="1792x1024"),
    app_commands.Choice(name="1024x1792 (portrait)",  value="1024x1792"),
])
async def cmd_image(interaction: discord.Interaction, prompt: str, size: str = "1024x1024"):
    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model = get_model(interaction.user.id, "image")

    try:
        async with aiohttp.ClientSession() as session:
            w, h = size.split("x")
            encoded = urllib.parse.quote(prompt)
            img_url = f"https://image.pollinations.ai/prompt/{encoded}?model={model}&width={w}&height={h}&nologo=true&seed={random.randint(1,99999)}"
            img_bytes = await api_get_bytes(session, img_url)

        file  = discord.File(fp=io.BytesIO(img_bytes), filename="nov.png")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🖼️ {model} - {size}")
        embed.set_image(url="attachment://nov.png")
        embed.set_footer(text=prompt[:100])
        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /audio
# ──────────────────────────────────────────────
@bot.tree.command(name="audio", description="Convert text to speech")
@app_commands.describe(text="Text to convert to audio")
async def cmd_audio(interaction: discord.Interaction, text: str):
    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    voice = get_model(interaction.user.id, "audio")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"model": "tts-1", "input": text, "voice": voice}
            audio   = await api_post_bytes(session, f"{BASE_URL}/audio/speech", payload, key)

        file = discord.File(fp=io.BytesIO(audio), filename="nov_audio.mp3")
        await interaction.followup.send(
            content=f"🔊 **{voice}** — *{text[:80]}{'...' if len(text)>80 else ''}*",
            file=file
        )

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /video
# ──────────────────────────────────────────────
@bot.tree.command(name="video", description="Generate a video with AI (requires Pollen credits)")
@app_commands.describe(prompt="Describe the video")
async def cmd_video(interaction: discord.Interaction, prompt: str):
    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model = get_model(interaction.user.id, "video")

    try:
        async with aiohttp.ClientSession() as session:
            data    = await api_post_json(session, f"{BASE_URL}/video/generations", {"model": model, "prompt": prompt}, key)
            vid_url = data.get("data", [{}])[0].get("url", "")
            if not vid_url:
                raise Exception("No video URL returned")
            vid_bytes = await api_get_bytes(session, vid_url)

        file  = discord.File(fp=io.BytesIO(vid_bytes), filename="nov_video.mp4")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🎬 {model}")
        embed.set_footer(text=prompt[:100])
        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(
            title="❌ Video error",
            description=f"`{e}`\n\n💡 Requires Pollen credits at [enter.pollinations.ai](https://enter.pollinations.ai)",
            color=0xED4245
        ))

# ──────────────────────────────────────────────
#  /model — cambia modello con autocomplete e validazione
# ──────────────────────────────────────────────
@bot.tree.command(name="model", description="Change the AI model for text/image/audio/video")
@app_commands.describe(type="Generation type", name="Model name (suggestions appear as you type)")
@app_commands.choices(type=[
    app_commands.Choice(name="💬 Text",  value="text"),
    app_commands.Choice(name="🖼️ Image", value="image"),
    app_commands.Choice(name="🔊 Audio", value="audio"),
    app_commands.Choice(name="🎬 Video", value="video"),
])
@app_commands.autocomplete(name=model_name_autocomplete)
async def cmd_model(interaction: discord.Interaction, type: str, name: str):
    # Validazione — il modello deve essere nella lista
    if not is_valid_model(type, name):
        await interaction.response.send_message(embed=invalid_model_embed(type, name), ephemeral=True)
        return

    uid = interaction.user.id
    if uid not in USER_MODELS:
        USER_MODELS[uid] = dict(DEFAULT_MODELS)

    old = USER_MODELS[uid].get(type, DEFAULT_MODELS[type])
    USER_MODELS[uid][type] = name

    embed = discord.Embed(title="✅ Model updated", color=0x57F287)
    embed.add_field(name="Type",   value=f"{TYPE_EMOJI[type]} {type}", inline=True)
    embed.add_field(name="Before", value=f"`{old}`",                   inline=True)
    embed.add_field(name="Now",    value=f"`{clean_model(name)}`",     inline=True)
    if "(PAID)" in name:
        embed.add_field(name="⚠️ Note", value="This model requires Pollen credits at [enter.pollinations.ai](https://enter.pollinations.ai)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ──────────────────────────────────────────────
#  /models — lista modelli
# ──────────────────────────────────────────────
@bot.tree.command(name="models", description="List available models")
@app_commands.choices(type=[
    app_commands.Choice(name="All",      value="all"),
    app_commands.Choice(name="💬 Text",  value="text"),
    app_commands.Choice(name="🖼️ Image", value="image"),
    app_commands.Choice(name="🔊 Audio", value="audio"),
    app_commands.Choice(name="🎬 Video", value="video"),
])
async def cmd_models(interaction: discord.Interaction, type: str = "all"):
    embed = discord.Embed(title=f"📋 Nov - Available Models", color=BOT_COLOR)
    tipi  = [type] if type != "all" else ["text", "image", "audio", "video"]
    for t in tipi:
        lista = "\n".join(f"`{m}`" for m in KNOWN_MODELS[t])
        embed.add_field(name=f"{TYPE_EMOJI[t]} {t.capitalize()}", value=lista, inline=True)
    embed.set_footer(text="(PAID) = requires Pollen credits • /model to change")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ──────────────────────────────────────────────
#  /info
# ──────────────────────────────────────────────
@bot.tree.command(name="info", description="Show your current Nov settings")
async def cmd_info(interaction: discord.Interaction):
    uid    = interaction.user.id
    models = USER_MODELS.get(uid, DEFAULT_MODELS)
    mem    = get_memory(uid)

    embed = discord.Embed(title=f"⚙️ Nov - Your Settings", color=BOT_COLOR)

    if USER_KEYS.get(uid):
        k = USER_KEYS[uid]
        embed.add_field(name="🔑 Key", value=f"`{k[:6]}{'•'*(len(k)-9)}{k[-3:]}` ✅", inline=False)
    elif os.getenv("POLLINATIONS_KEY"):
        embed.add_field(name="🔑 Key", value="Using server default key", inline=False)
    else:
        embed.add_field(name="🔑 Key", value="❌ Not connected - use `/connect`", inline=False)

    for tipo in ["text", "image", "audio", "video"]:
        embed.add_field(name=f"{TYPE_EMOJI[tipo]} {tipo.capitalize()}", value=f"`{models.get(tipo, DEFAULT_MODELS[tipo])}`", inline=True)

    if mem:
        mem_str = "\n".join(f"**{k}:** {v}" for k, v in mem.items())
        embed.add_field(name="🧠 Memory", value=mem_str, inline=False)
    else:
        embed.add_field(name="🧠 Memory", value="Nothing saved yet - use `/remember`", inline=False)

    embed.set_footer(text=f"Nov v{BOT_VERSION} - Powered by Pollinations AI")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ──────────────────────────────────────────────
#  /help
# ──────────────────────────────────────────────
@bot.tree.command(name="help", description="Show all Nov commands")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(title=f"✨ Nov - Commands", description="AI-powered bot by Pollinations", color=BOT_COLOR)
    embed.add_field(name="🔑 Setup",     value="`/connect` - Connect your Pollinations key\n`/disconnect` - Remove your key\n`/info` - View your settings", inline=False)
    embed.add_field(name="🧠 Memory",    value="`/remember [key] [value]` - Save info about you\n`/forget` - Clear your memory", inline=False)
    embed.add_field(name="💬 Generate",  value="`/text` - Open AI chat thread\n`/image` - Generate an image\n`/audio` - Text to speech\n`/video` - Generate a video", inline=False)
    embed.add_field(name="⚙️ Models",    value="`/model` - Change AI model (with autocomplete!)\n`/models` - List available models", inline=False)
    embed.set_footer(text=f"Nov v{BOT_VERSION} - enter.pollinations.ai")
    await interaction.response.send_message(embed=embed)

# ──────────────────────────────────────────────
#  START
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌  DISCORD_TOKEN missing in .env!")
        exit(1)
    print(f"🚀  Starting {BOT_NAME} v{BOT_VERSION}...")
    bot.run(DISCORD_TOKEN)
