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
import asyncio
import json
import os
import io
import time
import urllib.parse
import random
from dotenv import load_dotenv

# Richiede discord.py >= 2.4 (per allowed_installs / allowed_contexts → supporto User Install)
# Aggiorna con: pip install -U discord.py

load_dotenv()

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
BASE_URL      = "https://gen.pollinations.ai/v1"
AUTH_URL      = "https://enter.pollinations.ai/api/device"
APP_KEY       = "pk_yQpEnADty90tWmr0"  # Nov App Key
BOT_NAME      = "Nov"
BOT_COLOR     = 0x5865F2
BOT_VERSION   = "3.0.0"

# Chiavi per utente { user_id: "sk_..." }
USER_KEYS:        dict[int, str]  = {}
# Modelli per utente { user_id: { tipo: modello } }
USER_MODELS:      dict[int, dict] = {}
# Memoria utenti { user_id: { "name": str, ... } }
USER_MEMORY:      dict[int, dict] = {}
# Thread di chat attivi { thread_id: { user_id, model, history } }
CHAT_THREADS:     dict[int, dict] = {}
# Storico generazioni per utente (max 20) { uid: [{type,prompt,url,model,ts}] }
USER_HISTORY:     dict[int, list] = {}
# Persona attiva per utente { uid: "persona_name" }
USER_PERSONA:     dict[int, str]  = {}
# Canale gallery per server { guild_id: channel_id }
GALLERY_CHANNELS: dict[int, int]  = {}
# Identità personalizzata per server { guild_id: { name, personality, owner_id } }
SERVER_IDENTITY:  dict[int, dict] = {}
# Statistiche server { guild_id: { uid: {images,texts,videos,audios} } }
SERVER_STATS:     dict[int, dict] = {}

# Persona presets
PERSONAS = {
    "default":     "Be helpful, friendly, and concise.",
    "sarcastic":   "You are extremely sarcastic and witty. Every answer drips with irony, but you still help.",
    "formal":      "You are a formal, professional assistant. Use proper grammar and a business-like tone at all times.",
    "pirate":      "You speak like a pirate. Use pirate slang (arrr, matey, landlubber) naturally in every reply.",
    "anime":       "You are an enthusiastic anime character. Use Japanese honorifics (senpai, kun, chan) and express emotions very dramatically.",
    "hacker":      "You speak like an elite hacker. Use hacker slang, l33tspeak occasionally, and reference the matrix.",
    "shakespeare": "You speak in the style of William Shakespeare. Use thee, thou, doth, hath, and poetic language.",
    "chef":        "You are a passionate Italian chef who relates everything to food and cooking.",
}

DEFAULT_MODELS = {
    "text":  "GPT-5.4 Nano",
    "image": "Flux Schnell",
    "audio": "Nova",
    "video": "Veo 3.1 Fast (PAID)",
}

# Modelli reali Pollinations — quelli con (PAID) richiedono crediti Pollen
# Mappa: nome visualizzato → ID API reale
# (PAID) = box gialla sul dashboard | nessun suffisso = box verde (free)
MODEL_DISPLAY_TO_ID = {
    # ── TEXT ──────────────────────────────────────
    # FREE (box verde)
    "GPT-5 Nano":                          "openai-fast",
    "GPT-5.4 Nano":                        "openai",
    "GPT-5.4 Mini":                        "gpt-5.4-mini",
    "GPT-5.4":                             "gpt-5.4",
    "GPT-5.5":                             "openai-large",
    "GPT Audio Mini":                      "openai-audio",
    "GPT Audio 1.5":                       "openai-audio-large",
    "Nova Micro":                          "nova-fast",
    "Nova 2 Lite":                         "nova",
    "DeepSeek V4 Flash (Lite)":            "deepseek",
    "DeepSeek V4 Pro":                     "deepseek-pro",
    "Mistral Small 3.2":                   "mistral-small-3.2",
    "Mistral Small 4":                     "mistral",
    "Mistral Large 3":                     "mistral-large",
    "Meta Llama 3.3 70B":                  "llama",
    "Meta Llama 4 Scout":                  "llama-scout",
    "Qwen3 Coder 30B":                     "qwen-coder",
    "Qwen3 VL 30B A3B Instruct":           "qwen-vision",
    "Qwen3.7 Plus":                        "qwen-large",
    "Qwen3 VL 235B A22B Thinking":         "qwen-vision-pro",
    "Qwen3Guard 8B":                       "qwen-safety",
    "MiniMax M2.7":                        "minimax-m2.7",
    "MiniMax M3":                          "minimax",
    "StepFun Step 3.5 Flash":              "step-3.5-flash",
    "StepFun Step 3.7 Flash":              "step-flash",
    "Grok 4.20 Non-Reasoning":             "grok",
    "Grok 4.20 Reasoning":                 "grok-4-20-reasoning",
    "Grok 4.3":                            "grok-large",
    "Perplexity Sonar":                    "perplexity-fast",
    "Perplexity Sonar Pro":                "perplexity",
    "Perplexity Sonar Reasoning":          "perplexity-reasoning",
    "Moonshot Kimi K2.6":                  "kimi",
    "Moonshot Kimi K2.7 Code":             "kimi-code",
    "MIDIjourney":                         "midijourney",
    "MIDIjourney Large":                   "midijourney-large",
    "Z.ai GLM-5.2":                        "glm",
    "Polly by @Itachi-1824":               "polly",
    # PAID (box gialla)
    "Gemini 2.5 Flash Lite (PAID)":        "gemini-fast",
    "Gemini 3.1 Flash Lite (PAID)":        "gemini-flash-lite-3.1",
    "Gemini 3.1 Flash Lite Search (PAID)": "gemini-search-fast",
    "Google Gemini 2.5 Flash Search (PAID)": "gemini-search",
    "Gemini 3 Flash (PAID)":               "gemini-3-flash",
    "Gemini 3.5 Flash (PAID)":             "gemini",
    "Gemini 3.5 Flash Search (PAID)":      "gemini-search-large",
    "Gemini 3.1 Pro (PAID)":               "gemini-large",
    "Gemma 4 26B (PAID)":                  "gemma",
    "Mercury 2 (PAID)":                    "mercury",
    "Qwen3 Coder Next (PAID)":             "qwen-coder-large",
    "Meta Llama 4 Maverick (PAID)":        "llama-maverick",
    "Claude Haiku 4.5 (PAID)":             "claude-fast",
    "Claude Sonnet 4.6 (PAID)":            "claude",
    "Claude Opus 4.6 (PAID)":              "claude-opus-4.6",
    "Claude Opus 4.7 (PAID)":              "claude-opus-4.7",
    "Claude Opus 4.8 (PAID)":              "claude-large",
    # ── IMAGE ─────────────────────────────────────
    # FREE (box verde)
    "Flux Schnell":                        "flux",
    "FLUX.2 Klein 4B":                     "klein",
    "FLUX.1 Kontext":                      "kontext",
    "GPT Image 1 Mini":                    "gptimage",
    "GPT Image 1.5":                       "gptimage-large",
    "Z-Image Turbo":                       "zimage",
    "Nova Canvas":                         "nova-canvas",
    # PAID (box gialla)
    "Pruna p-image (PAID)":               "p-image",
    "Pruna p-image-edit (PAID)":          "p-image-edit",
    "Grok Imagine (PAID)":                "grok-imagine",
    "Grok Imagine Pro (PAID)":            "grok-imagine-pro",
    "Seedream 4.0 (PAID)":                "seedream",
    "Seedream 4.5 Pro (PAID)":            "seedream-pro",
    "Seedream 5.0 Lite (PAID)":           "seedream5",
    "Ideogram 4.0 Turbo (PAID)":          "ideogram-v4-turbo",
    "Ideogram 4.0 Balanced (PAID)":       "ideogram-v4-balanced",
    "Ideogram 4.0 Quality (PAID)":        "ideogram-v4-quality",
    "Wan 2.7 Image (PAID)":               "wan-image",
    "Wan 2.7 Image Pro (PAID)":           "wan-image-pro",
    "GPT Image 2 (PAID)":                 "gpt-image-2",
    "NanoBanana (PAID)":                  "nanobanana",
    "NanoBanana 2 (PAID)":                "nanobanana-2",
    "NanoBanana Pro (PAID)":              "nanobanana-pro",
    "Qwen Image Plus (PAID)":             "qwen-image",
    # ── AUDIO ─────────────────────────────────────
    # TTS voices OpenAI (parametro voice in /audio/speech)
    "Nova":                               "nova",
    "Alloy":                              "alloy",
    "Echo":                               "echo",
    "Fable":                              "fable",
    "Onyx":                               "onyx",
    "Shimmer":                            "shimmer",
    "Ash":                                "ash",
    "Ballad":                             "ballad",
    "Coral":                              "coral",
    "Sage":                               "sage",
    "Verse":                              "verse",
    # FREE (box verde)
    "Whisper Large V3":                    "whisper",
    "AssemblyAI Universal-2":              "universal-2",
    "AssemblyAI Universal-3 Pro":          "universal-3-pro",
    "ACE-Step 1.5 Turbo":                  "acestep",
    # PAID (box gialla)
    "Scribe v2 (PAID)":                   "scribe",
    "ElevenLabs v3 TTS (PAID)":           "elevenlabs",
    "ElevenLabs Flash v2.5 (PAID)":       "elevenflash",
    "ElevenLabs Multilingual v2 (PAID)":  "eleven-multilingual-v2",
    "ElevenLabs Music (PAID)":            "elevenmusic",
    "ElevenLabs Sound Effects (PAID)":    "eleven-sfx",
    "Qwen3-TTS Flash (PAID)":             "qwen-tts",
    "Qwen3-TTS Instruct (PAID)":          "qwen-tts-instruct",
    "Stable Audio 2.5 (PAID)":            "stable-audio-2.5",
    "Stable Audio 3 (PAID)":              "stable-audio-3",
    "Stable Audio 3 Medium (PAID)":       "stable-audio-3-medium",
    "Stable Audio 3 Large (PAID)":        "stable-audio-3-large",
    # ── VIDEO ─────────────────────────────────────
    # FREE (box verde)
    "LTX-2.3":                            "ltx-2",
    "Nova Reel":                          "nova-reel",
    # PAID (box gialla)
    "Veo 3.1 Fast (PAID)":               "veo",
    "Seedance Pro-Fast (PAID)":           "seedance-pro",
    "Seedance 2.0 (PAID)":               "seedance-2.0",
    "Wan 2.6 (PAID)":                    "wan",
    "Wan 2.2 (PAID)":                    "wan-fast",
    "Wan 2.7 (PAID)":                    "wan-pro",
    "Wan 2.7 1080p (PAID)":              "wan-pro-1080p",
    "Grok Video Pro (PAID)":             "grok-video-pro",
    "Pruna p-video 720p (PAID)":         "p-video-720p",
    "Pruna p-video 1080p (PAID)":        "p-video-1080p",
}

# Mappa inversa: ID API → nome visualizzato
MODEL_ID_TO_DISPLAY = {v: k for k, v in MODEL_DISPLAY_TO_ID.items()}

KNOWN_MODELS = {
    "text": [
        # FREE (box verde)
        "GPT-5 Nano", "GPT-5.4 Nano", "GPT-5.4 Mini", "GPT-5.4", "GPT-5.5",
        "GPT Audio Mini", "GPT Audio 1.5",
        "Nova Micro", "Nova 2 Lite",
        "DeepSeek V4 Flash (Lite)", "DeepSeek V4 Pro",
        "Mistral Small 3.2", "Mistral Small 4", "Mistral Large 3",
        "Meta Llama 3.3 70B", "Meta Llama 4 Scout",
        "Qwen3 Coder 30B", "Qwen3 VL 30B A3B Instruct", "Qwen3.7 Plus",
        "Qwen3 VL 235B A22B Thinking", "Qwen3Guard 8B",
        "MiniMax M2.7", "MiniMax M3",
        "StepFun Step 3.5 Flash", "StepFun Step 3.7 Flash",
        "Grok 4.20 Non-Reasoning", "Grok 4.20 Reasoning", "Grok 4.3",
        "Perplexity Sonar", "Perplexity Sonar Pro", "Perplexity Sonar Reasoning",
        "Moonshot Kimi K2.6", "Moonshot Kimi K2.7 Code",
        "MIDIjourney", "MIDIjourney Large",
        "Z.ai GLM-5.2", "Polly by @Itachi-1824",
        # PAID (box gialla)
        "Gemini 2.5 Flash Lite (PAID)", "Gemini 3.1 Flash Lite (PAID)",
        "Gemini 3.1 Flash Lite Search (PAID)", "Google Gemini 2.5 Flash Search (PAID)",
        "Gemini 3 Flash (PAID)", "Gemini 3.5 Flash (PAID)",
        "Gemini 3.5 Flash Search (PAID)", "Gemini 3.1 Pro (PAID)",
        "Gemma 4 26B (PAID)", "Mercury 2 (PAID)",
        "Qwen3 Coder Next (PAID)", "Meta Llama 4 Maverick (PAID)",
        "Claude Haiku 4.5 (PAID)", "Claude Sonnet 4.6 (PAID)",
        "Claude Opus 4.6 (PAID)", "Claude Opus 4.7 (PAID)", "Claude Opus 4.8 (PAID)",
    ],
    "image": [
        # FREE (box verde)
        "Flux Schnell", "FLUX.2 Klein 4B", "FLUX.1 Kontext",
        "GPT Image 1 Mini", "GPT Image 1.5",
        "Z-Image Turbo", "Nova Canvas",
        # PAID (box gialla)
        "Pruna p-image (PAID)", "Pruna p-image-edit (PAID)",
        "Grok Imagine (PAID)", "Grok Imagine Pro (PAID)",
        "Seedream 4.0 (PAID)", "Seedream 4.5 Pro (PAID)", "Seedream 5.0 Lite (PAID)",
        "Ideogram 4.0 Turbo (PAID)", "Ideogram 4.0 Balanced (PAID)", "Ideogram 4.0 Quality (PAID)",
        "Wan 2.7 Image (PAID)", "Wan 2.7 Image Pro (PAID)",
        "GPT Image 2 (PAID)",
        "NanoBanana (PAID)", "NanoBanana 2 (PAID)", "NanoBanana Pro (PAID)",
        "Qwen Image Plus (PAID)",
    ],
    "audio": [
        # Voci TTS OpenAI — gratuite via /v1/audio/speech
        "Nova", "Alloy", "Echo", "Fable", "Onyx", "Shimmer",
        "Ash", "Ballad", "Coral", "Sage", "Verse",
        # FREE (numero verde dashboard)
        "AssemblyAI Universal-2",
        "Whisper Large V3",
        "ACE-Step 1.5 Turbo",
        "AssemblyAI Universal-3 Pro",
        # PAID (numero giallo dashboard)
        "Scribe v2 (PAID)",
        "Qwen3-TTS Flash (PAID)", "Qwen3-TTS Instruct (PAID)",
        "ElevenLabs Flash v2.5 (PAID)",
        "ElevenLabs Sound Effects (PAID)",
        "ElevenLabs v3 TTS (PAID)",
        "ElevenLabs Multilingual v2 (PAID)",
        "Stable Audio 2.5 (PAID)",
        "Stable Audio 3 (PAID)",
        "Stable Audio 3 Medium (PAID)",
        "ElevenLabs Music (PAID)",
        "Stable Audio 3 Large (PAID)",
    ],
    "video": [
        # FREE (box verde)
        "LTX-2.3", "Nova Reel",
        # PAID (box gialla)
        "Veo 3.1 Fast (PAID)", "Seedance Pro-Fast (PAID)", "Seedance 2.0 (PAID)",
        "Wan 2.6 (PAID)", "Wan 2.2 (PAID)", "Wan 2.7 (PAID)", "Wan 2.7 1080p (PAID)",
        "Grok Video Pro (PAID)",
        "Pruna p-video 720p (PAID)", "Pruna p-video 1080p (PAID)",
    ],
}

# Converte nome visualizzato → ID API reale
def clean_model(name: str) -> str:
    return MODEL_DISPLAY_TO_ID.get(name, name.replace(" (PAID)", "").strip())

TYPE_EMOJI = {"text": "💬", "image": "🖼️", "audio": "🔊", "video": "🎬"}

# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def has_personal_key(user_id: int) -> bool:
    """True se l'utente ha collegato il proprio account (sk_)."""
    return bool(USER_KEYS.get(user_id) or os.getenv("POLLINATIONS_KEY"))

def get_key(user_id: int) -> str:
    """Ritorna la key da usare: sk_ utente → env → pk_ del bot (fallback)."""
    return USER_KEYS.get(user_id) or os.getenv("POLLINATIONS_KEY") or APP_KEY

def get_model(user_id: int, tipo: str) -> str:
    return clean_model(USER_MODELS.get(user_id, {}).get(tipo, DEFAULT_MODELS[tipo]))

def get_memory(user_id: int) -> dict:
    return USER_MEMORY.get(user_id, {})

def set_memory(user_id: int, key: str, value: str):
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {}
    USER_MEMORY[user_id][key] = value

def get_server_name(guild_id: int | None) -> str:
    """Ritorna il nome del bot per questo server (se impostato), altrimenti il default."""
    if guild_id and guild_id in SERVER_IDENTITY:
        return SERVER_IDENTITY[guild_id]["name"]
    return BOT_NAME

def build_system_prompt(user_id: int, custom: str, guild_id: int | None = None) -> str:
    mem = get_memory(user_id)
    name_line = f"The user's name is {mem['name']}. " if mem.get("name") else ""
    extra = f" {custom}" if custom else ""
    # Identità server ha priorità sulla persona utente
    if guild_id and guild_id in SERVER_IDENTITY:
        identity   = SERVER_IDENTITY[guild_id]
        bot_n      = identity["name"]
        persona_text = identity["personality"]
    else:
        bot_n      = BOT_NAME
        persona_text = PERSONAS.get(USER_PERSONA.get(user_id, "default"), PERSONAS["default"])
    return (
        f"Your name is {bot_n}. You are a helpful AI assistant living inside Discord, "
        f"powered by Pollinations AI. Always refer to yourself as {bot_n}, never as ChatGPT, "
        f"Claude, Gemini, or any other AI name. {name_line}{persona_text}{extra}"
    )

def auth_headers(key) -> dict:
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h

def is_free_model(name: str) -> bool:
    return "(PAID)" not in name

# Modelli disponibili SENZA account — endpoint pubblico text.pollinations.ai
# Solo quelli che Pollinations eroga davvero senza autenticazione
FREE_MODELS_NO_AUTH = {
    "text": [
        "GPT-5.4 Nano",         # openai (default)
        "GPT-5.4 Mini",         # openai-large
        "Mistral Small 4",      # mistral
        "Mistral Large 3",      # mistral-large
        "Meta Llama 3.3 70B",   # llama
        "Meta Llama 4 Scout",   # llama-scout
        "DeepSeek V4 Flash (Lite)", # deepseek
        "DeepSeek V4 Pro",      # deepseek-r1
        "Qwen3 Coder 30B",      # qwen-coder
        "Phi-4",                # phi
        "MIDIjourney",          # midijourney
        "Z.ai GLM-5.2",         # unity/glm
    ],
    "image": [
        "Flux Schnell",         # flux — unico senza key
    ],
}

def not_logged_in_embed():
    return discord.Embed(
        title="🔒 Account required",
        description=(
            "This command requires a Pollinations account.\n\n"
            "**→ Use `/connect` to link your account for free**\n"
            "[enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xED4245
    )

def available_models(tipo: str, user_id: int) -> list:
    """Tutti i modelli se l'utente ha account, solo quelli pubblici altrimenti."""
    if has_personal_key(user_id):
        return KNOWN_MODELS[tipo]
    return FREE_MODELS_NO_AUTH.get(tipo, KNOWN_MODELS[tipo])

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
    """Usato solo per audio/video che richiedono sempre un account."""
    return discord.Embed(
        title="🔑 Account required",
        description=(
            "This command requires a Pollinations account.\n\n"
            "**→ Use `/connect` to link your account**\n\n"
            "Get one free at [enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xED4245
    )

def paid_model_no_key_embed(name: str) -> discord.Embed:
    """Utente senza key tenta di usare un modello PAID."""
    return discord.Embed(
        title="🔒 Account required for this model",
        description=(
            f"`{name}` requires Pollen credits.\n\n"
            "**→ Use `/connect` to link your Pollinations account**\n"
            "Free models are available without an account!\n\n"
            "Get one at [enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xFEE75C
    )

def invalid_model_embed(tipo: str, name: str, user_id: int = 0):
    avail = available_models(tipo, user_id) if user_id else KNOWN_MODELS[tipo]
    valid = "\n".join(f"`{m}`" for m in avail)
    note  = "\n\n🔓 *Connect an account to unlock paid models.*" if user_id and not has_personal_key(user_id) else ""
    return discord.Embed(
        title="❌ Unknown model",
        description=f"`{name}` is not a valid **{tipo}** model.\n\n**Available models:**\n{valid}{note}",
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
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    # Permette di installare Nov sul proprio account utente (non solo su un server)
    allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    # Permette di usare i comandi in server, DM e DM di gruppo
    allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
)

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
    tipo = interaction.namespace.type
    uid  = interaction.user.id
    if not tipo or tipo not in KNOWN_MODELS:
        all_models = [m for t in KNOWN_MODELS for m in available_models(t, uid)]
        choices = [app_commands.Choice(name=m, value=m) for m in all_models if current.lower() in m.lower()]
    else:
        choices = [
            app_commands.Choice(name=m, value=m)
            for m in available_models(tipo, uid)
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
    uid    = interaction.user.id
    key    = get_key(uid)
    model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return

    model  = get_model(uid, "text")
    system = build_system_prompt(interaction.user.id, system, interaction.guild_id)
    await interaction.response.defer(thinking=True)

    try:
        async with aiohttp.ClientSession() as session:
            if has_personal_key(uid):
                # Endpoint autenticato con sk_
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
            else:
                # Endpoint pubblico senza key
                encoded_prompt = urllib.parse.quote(prompt)
                pub_url = f"https://text.pollinations.ai/{encoded_prompt}?model={model}&system={urllib.parse.quote(system)}"
                async with session.get(pub_url) as resp:
                    resp.raise_for_status()
                    reply = await resp.text()

        # Risposta silenziosa all'interazione
        in_guild_text_channel = interaction.guild is not None and isinstance(interaction.channel, discord.TextChannel)

        if in_guild_text_channel:
            # Comportamento originale: apre un thread nel canale del server
            await interaction.followup.send("💬 Opening chat thread...", ephemeral=True)

            channel = interaction.channel
            embed_intro = discord.Embed(
                description=f"**{interaction.user.display_name}:** {prompt}",
                color=BOT_COLOR
            )
            embed_intro.set_author(name=f"Nov Chat - {model_name}")
            embed_intro.set_footer(text="Thread opened - just type here to keep chatting!")
            msg = await channel.send(embed=embed_intro)

            target_channel = await msg.create_thread(
                name=f"Nov - {interaction.user.display_name} - {prompt[:40]}",
                auto_archive_duration=60
            )
        else:
            # DM, DM di gruppo o canale senza supporto thread: risponde qui direttamente,
            # la conversazione continua semplicemente scrivendo in questo stesso canale
            embed_intro = discord.Embed(
                description=f"**{interaction.user.display_name}:** {prompt}",
                color=BOT_COLOR
            )
            embed_intro.set_author(name=f"Nov Chat - {model_name}")
            embed_intro.set_footer(text="Just keep typing here to continue - say /close to end.")
            await interaction.followup.send(embed=embed_intro)
            target_channel = interaction.channel

        # Manda risposta come testo normale
        if len(reply) <= 2000:
            await target_channel.send(reply)
        else:
            for chunk in [reply[i:i+2000] for i in range(0, len(reply), 2000)]:
                await target_channel.send(chunk)

        # Salva stato thread/canale
        CHAT_THREADS[target_channel.id] = {
            "user_id":  uid,
            "model":    model,
            "system":   system,
            "key":      key,
            "has_key":  has_personal_key(uid),
            "history": [
                {"role": "system",    "content": system},
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": reply},
            ]
        }

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  on_message — thread di chat + DM automatici
# ──────────────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    thread_data = CHAT_THREADS.get(message.channel.id)

    # ── DM auto-reply ──
    # Se non c'è sessione attiva, ma siamo in DM e non è un comando → avvia auto-conversazione
    if (
        not thread_data
        and isinstance(message.channel, discord.DMChannel)
        and not message.content.startswith("/")
        and not message.content.startswith("!")
    ):
        uid        = message.author.id
        model      = get_model(uid, "text")
        key        = get_key(uid)
        sys_prompt = build_system_prompt(uid, "", message.guild.id if message.guild else None)
        CHAT_THREADS[message.channel.id] = {
            "user_id": uid,
            "model":   model,
            "system":  sys_prompt,
            "key":     key,
            "has_key": has_personal_key(uid),
            "private": True,
            "history": [{"role": "system", "content": sys_prompt}],
        }
        thread_data = CHAT_THREADS[message.channel.id]

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
        if isinstance(message.channel, discord.Thread):
            await message.channel.edit(archived=True, locked=True)
        return

    async with message.channel.typing():
        history = thread_data["history"]
        history.append({"role": "user", "content": message.content})

        try:
            async with aiohttp.ClientSession() as session:
                t_key = thread_data["key"]
                if thread_data.get("has_key"):
                    payload = {
                        "model":    thread_data["model"],
                        "messages": history,
                        "max_tokens": 1500,
                    }
                    data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, t_key)
                    reply = data["choices"][0]["message"]["content"]
                else:
                    last_msg       = history[-1]["content"]
                    encoded_prompt = urllib.parse.quote(last_msg)
                    sys_q          = urllib.parse.quote(thread_data.get("system", ""))
                    pub_url = f"https://text.pollinations.ai/{encoded_prompt}?model={thread_data['model']}&system={sys_q}"
                    async with session.get(pub_url) as resp:
                        resp.raise_for_status()
                        reply = await resp.text()

            history.append({"role": "assistant", "content": reply})
            if len(reply) <= 2000:
                await message.channel.send(reply)
            else:
                for chunk in [reply[i:i+2000] for i in range(0, len(reply), 2000)]:
                    await message.channel.send(chunk)

        except Exception as e:
            await message.channel.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  View — bottone "Copy URL" sotto le immagini
# ──────────────────────────────────────────────
class ImageURLView(discord.ui.View):
    """Aggiunge un link button + un copy-URL button sotto ogni immagine generata."""

    def __init__(self, url: str):
        super().__init__(timeout=600)   # bottoni attivi 10 min
        self._url = url
        # Link button → apre direttamente l'immagine nel browser
        self.add_item(discord.ui.Button(
            label="🔗 Open Image",
            style=discord.ButtonStyle.link,
            url=url,
            row=0
        ))

    @discord.ui.button(label="📋 Copy URL", style=discord.ButtonStyle.secondary, row=0)
    async def copy_url_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Invia l'URL come messaggio ephemeral — facile da selezionare e copiare."""
        await interaction.response.send_message(
            f"```\n{self._url}\n```",
            ephemeral=True
        )

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
    uid  = interaction.user.id
    key  = get_key(uid)
    model_name = USER_MODELS.get(uid, {}).get("image", DEFAULT_MODELS["image"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model = get_model(uid, "image")

    try:
        async with aiohttp.ClientSession() as session:
            w, h = size.split("x")
            seed = random.randint(1, 9999999)
            encoded = urllib.parse.quote(prompt)
            if has_personal_key(uid):
                img_url = f"https://gen.pollinations.ai/image/{encoded}?model={model}&width={w}&height={h}&nologo=true&seed={seed}"
                async with session.get(img_url, headers=auth_headers(get_key(uid))) as resp:
                    resp.raise_for_status()
                    img_bytes = await resp.read()
            else:
                # Endpoint pubblico gratuito — nessuna auth
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?model={model}&width={w}&height={h}&nologo=true&seed={seed}&nofeed=true"
                async with session.get(img_url) as resp:
                    resp.raise_for_status()
                    img_bytes = await resp.read()

        file  = discord.File(fp=io.BytesIO(img_bytes), filename="nov.png")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🖼️ {model_name} - {size}")
        embed.set_image(url="attachment://nov.png")
        embed.set_footer(text=prompt[:100])
        await interaction.followup.send(embed=embed, file=file, view=ImageURLView(img_url))

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /audio
# ──────────────────────────────────────────────
@bot.tree.command(name="audio", description="Convert text to speech")
@app_commands.describe(text="Text to convert to audio")
async def cmd_audio(interaction: discord.Interaction, text: str):
    uid = interaction.user.id
    voice_name = USER_MODELS.get(uid, {}).get("audio", DEFAULT_MODELS["audio"])
    FREE_VOICES = ["Nova", "Alloy", "Echo", "Fable", "Onyx", "Shimmer",
                   "Ash", "Ballad", "Coral", "Sage", "Verse",
                   "AssemblyAI Universal-2", "Whisper Large V3",
                   "ACE-Step 1.5 Turbo", "AssemblyAI Universal-3 Pro"]
    if voice_name not in FREE_VOICES and not has_personal_key(uid):
        await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
        return
    key = get_key(uid)

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
    if not has_personal_key(interaction.user.id):
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return
    key = get_key(interaction.user.id)

    await interaction.response.defer(thinking=True)
    model = get_model(interaction.user.id, "video")

    try:
        async with aiohttp.ClientSession() as session:
            encoded = urllib.parse.quote(prompt)
            vid_url_req = f"https://gen.pollinations.ai/video/{encoded}?model={model}"
            async with session.get(vid_url_req, headers=auth_headers(key)) as resp:
                resp.raise_for_status()
                vid_bytes = await resp.read()

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
    uid = interaction.user.id
    if not has_personal_key(uid):
        await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
        return
    key = get_key(uid)

    # Modello non nella lista globale
    if not is_valid_model(type, name):
        await interaction.response.send_message(embed=invalid_model_embed(type, name, uid), ephemeral=True)
        return

    # Modello PAID senza account personale
    if not is_free_model(name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(name), ephemeral=True)
        return

    if uid not in USER_MODELS:
        USER_MODELS[uid] = dict(DEFAULT_MODELS)

    prev = USER_MODELS[uid].get(type, DEFAULT_MODELS[type])
    USER_MODELS[uid][type] = name

    embed = discord.Embed(title="✅ Model updated", color=0x57F287)
    embed.add_field(name="Type",   value=f"{TYPE_EMOJI[type]} {type}", inline=True)
    embed.add_field(name="Before", value=f"`{prev}`",                  inline=True)
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
    uid = interaction.user.id
    if not has_personal_key(uid):
        # Mostra solo testo e immagini gratis + voci TTS gratis
        embed = discord.Embed(
            title="📋 Nov - Available Models",
            description="🔓 *Free models only — `/connect` to unlock all*",
            color=BOT_COLOR
        )
        for t in ["text", "image"]:
            lista = "\n".join(f"`{m}`" for m in FREE_MODELS_NO_AUTH.get(t, []))
            embed.add_field(name=f"{TYPE_EMOJI[t]} {t.capitalize()}", value=lista or "*none*", inline=False)
        voices = "\n".join(f"`{v}`" for v in ["Nova","Alloy","Echo","Fable","Onyx","Shimmer","Ash","Ballad","Coral","Sage","Verse"])
        embed.add_field(name="🔊 Audio (TTS voices)", value=voices, inline=False)
        embed.add_field(name="🎬 Video", value="🔒 Requires account — `/connect`", inline=False)
        embed.set_footer(text="/connect to unlock paid models, video and more")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    tipi = [type] if type != "all" else ["text", "image", "audio", "video"]
    embed = discord.Embed(title="📋 Nov - Available Models", color=BOT_COLOR)
    for t in tipi:
        models_list = KNOWN_MODELS[t]
        # Spezza in chunks da max 1000 chars per rispettare il limite Discord
        chunk_str = ""
        chunk_num = 1
        for m in models_list:
            line = f"`{m}`\n"
            if len(chunk_str) + len(line) > 1000:
                embed.add_field(
                    name=f"{TYPE_EMOJI[t]} {t.capitalize()}" + (f" ({chunk_num})" if chunk_num > 1 else ""),
                    value=chunk_str.strip(),
                    inline=False
                )
                chunk_str = line
                chunk_num += 1
            else:
                chunk_str += line
        if chunk_str:
            embed.add_field(
                name=f"{TYPE_EMOJI[t]} {t.capitalize()}" + (f" ({chunk_num})" if chunk_num > 1 else ""),
                value=chunk_str.strip(),
                inline=False
            )
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
#  /privtext  — thread privato (solo tu e il bot)
# ──────────────────────────────────────────────
@bot.tree.command(name="privtext", description="Open a private AI chat thread (only you and Nov can see it)")
@app_commands.describe(prompt="Your first message", system="Optional custom system prompt")
async def cmd_privtext(interaction: discord.Interaction, prompt: str, system: str = ""):
    in_guild_text_channel = interaction.guild is not None and isinstance(interaction.channel, discord.TextChannel)

    uid        = interaction.user.id
    key        = get_key(uid)
    model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return

    model      = get_model(uid, "text")
    sys_prompt = build_system_prompt(uid, system, interaction.guild_id)
    await interaction.response.defer(thinking=True, ephemeral=in_guild_text_channel)

    try:
        async with aiohttp.ClientSession() as session:
            if has_personal_key(uid):
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user",   "content": prompt},
                    ],
                    "max_tokens": 1500,
                }
                data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
                reply = data["choices"][0]["message"]["content"]
            else:
                encoded = urllib.parse.quote(prompt)
                async with session.get(
                    f"https://text.pollinations.ai/{encoded}?model={model}&system={urllib.parse.quote(sys_prompt)}"
                ) as resp:
                    resp.raise_for_status()
                    reply = await resp.text()

        if in_guild_text_channel:
            # Crea thread privato — visibile solo all'utente, al bot e ai moderatori
            channel = interaction.channel
            target_channel = await channel.create_thread(
                name=f"🔒 Nov · {interaction.user.display_name} · {prompt[:35]}",
                type=discord.ChannelType.private_thread,
                invitable=False,          # solo moderatori possono aggiungere altri
                auto_archive_duration=60,
            )

            # Aggiungi l'utente al thread (necessario esplicitamente nei private thread)
            await target_channel.add_user(interaction.user)

            # Primo messaggio nel thread
            intro = discord.Embed(
                description=f"🔒 **Private thread** — only you and Nov can see this.\n\n**You:** {prompt}",
                color=0x2B2D31
            )
            intro.set_author(name=f"Nov Chat (Private) - {model_name}")
            intro.set_footer(text="Just type here to keep chatting. Use /close to end.")
            await target_channel.send(embed=intro)
        else:
            # DM o DM di gruppo: è già privato di natura, risponde direttamente qui
            intro = discord.Embed(
                description=f"🔒 **Private chat** — only you and Nov can see this.\n\n**You:** {prompt}",
                color=0x2B2D31
            )
            intro.set_author(name=f"Nov Chat (Private) - {model_name}")
            intro.set_footer(text="Just keep typing here to continue. Use /close to end.")
            await interaction.followup.send(embed=intro)
            target_channel = interaction.channel

        # Risposta del bot
        if len(reply) <= 2000:
            await target_channel.send(reply)
        else:
            for chunk in [reply[i:i+2000] for i in range(0, len(reply), 2000)]:
                await target_channel.send(chunk)

        # Salva stato thread/canale
        CHAT_THREADS[target_channel.id] = {
            "user_id": uid,
            "model":   model,
            "system":  sys_prompt,
            "key":     key,
            "has_key": has_personal_key(uid),
            "private": True,
            "history": [
                {"role": "system",    "content": sys_prompt},
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": reply},
            ]
        }

        if in_guild_text_channel:
            await interaction.followup.send(
                f"🔒 Private thread opened! → {target_channel.mention}",
                ephemeral=True
            )

    except discord.Forbidden:
        await interaction.followup.send(
            embed=discord.Embed(
                title="❌ Missing permissions",
                description=(
                    "Nov can't create private threads here.\n\n"
                    "Make sure the server has **Community** enabled and Nov has "
                    "**Create Private Threads** permission."
                ),
                color=0xED4245
            ),
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245),
            ephemeral=True
        )

# ──────────────────────────────────────────────
#  /ping — latency con barra colorata
# ──────────────────────────────────────────────
@bot.tree.command(name="ping", description="Check Nov's latency")
async def cmd_ping(interaction: discord.Interaction):
    t_start = time.monotonic()
    await interaction.response.defer(thinking=True)
    api_ms = round((time.monotonic() - t_start) * 1000)
    ws_ms  = round(bot.latency * 1000)

    def colored_bar(ms: int):
        filled = min(10, max(1, ms // 30))
        bar    = "█" * filled + "░" * (10 - filled)
        if ms < 100:
            emoji = "🟢"
        elif ms < 200:
            emoji = "🟡"
        else:
            emoji = "🔴"
        return emoji, bar

    ws_e,  ws_bar  = colored_bar(ws_ms)
    api_e, api_bar = colored_bar(api_ms)

    embed = discord.Embed(title="🏓 Pong!", color=BOT_COLOR)
    embed.add_field(name="WebSocket", value=f"{ws_e} `{ws_bar}` **{ws_ms} ms**",  inline=False)
    embed.add_field(name="API Round-trip", value=f"{api_e} `{api_bar}` **{api_ms} ms**", inline=False)
    embed.set_footer(text="🟢 <100ms  🟡 100–200ms  🔴 >200ms")
    await interaction.followup.send(embed=embed)

# ──────────────────────────────────────────────
#  /ask — risposta istantanea senza thread
# ──────────────────────────────────────────────
@bot.tree.command(name="ask", description="Get an instant AI reply without opening a thread")
@app_commands.describe(prompt="Your question or request")
async def cmd_ask(interaction: discord.Interaction, prompt: str):
    uid        = interaction.user.id
    model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model      = get_model(uid, "text")
    key        = get_key(uid)
    sys_prompt = build_system_prompt(uid, "", interaction.guild_id)

    try:
        async with aiohttp.ClientSession() as session:
            if has_personal_key(uid):
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user",   "content": prompt},
                    ],
                    "max_tokens": 1000,
                }
                data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
                reply = data["choices"][0]["message"]["content"]
            else:
                encoded = urllib.parse.quote(prompt)
                async with session.get(
                    f"https://text.pollinations.ai/{encoded}?model={model}&system={urllib.parse.quote(sys_prompt)}"
                ) as resp:
                    resp.raise_for_status()
                    reply = await resp.text()

        embed = discord.Embed(description=reply[:4096], color=BOT_COLOR)
        embed.set_author(name=f"💬 {model_name}")
        embed.set_footer(text=f"Quick reply for {interaction.user.display_name} • /text for full chat")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /translate — traduce con il modello text attivo
# ──────────────────────────────────────────────
@bot.tree.command(name="translate", description="Translate text into any language using the active text model")
@app_commands.describe(text="Text to translate", language="Target language (e.g. Italian, Japanese, French)")
async def cmd_translate(interaction: discord.Interaction, text: str, language: str):
    uid        = interaction.user.id
    model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model      = get_model(uid, "text")
    key        = get_key(uid)
    sys_prompt = (
        f"You are a professional translator. Translate the following text into {language}. "
        "Output ONLY the translation — no explanations, no preamble."
    )

    try:
        async with aiohttp.ClientSession() as session:
            if has_personal_key(uid):
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user",   "content": text},
                    ],
                    "max_tokens": 1000,
                }
                data   = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
                result = data["choices"][0]["message"]["content"]
            else:
                encoded = urllib.parse.quote(text)
                async with session.get(
                    f"https://text.pollinations.ai/{encoded}?model={model}&system={urllib.parse.quote(sys_prompt)}"
                ) as resp:
                    resp.raise_for_status()
                    result = await resp.text()

        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🌐 Translation → {language}")
        embed.add_field(name="🔤 Original", value=text[:1000],   inline=False)
        embed.add_field(name=f"🌐 {language}", value=result[:1000], inline=False)
        embed.set_footer(text=f"Model: {model_name}")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /summarize — 4 stili di riassunto
# ──────────────────────────────────────────────
@bot.tree.command(name="summarize", description="Summarize text in 4 different styles")
@app_commands.describe(text="Text to summarize", style="Summary style")
@app_commands.choices(style=[
    app_commands.Choice(name="• Bullet points", value="bullet"),
    app_commands.Choice(name="📄 Paragraph",    value="paragraph"),
    app_commands.Choice(name="1️⃣ One sentence", value="sentence"),
    app_commands.Choice(name="📢 TL;DR",        value="tldr"),
])
async def cmd_summarize(interaction: discord.Interaction, text: str, style: str = "bullet"):
    uid        = interaction.user.id
    model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model = get_model(uid, "text")
    key   = get_key(uid)

    STYLE_PROMPTS = {
        "bullet":    "Summarize the following text as a concise bullet point list. Use • for each bullet.",
        "paragraph": "Summarize the following text in a single coherent paragraph.",
        "sentence":  "Summarize the following text in exactly one sentence. Nothing else.",
        "tldr":      "Write a TL;DR summary of the following text. Start with 'TL;DR:'",
    }
    STYLE_LABELS = {
        "bullet": "• Bullet Points", "paragraph": "📄 Paragraph",
        "sentence": "1️⃣ One Sentence", "tldr": "📢 TL;DR",
    }
    sys_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["bullet"])

    try:
        async with aiohttp.ClientSession() as session:
            if has_personal_key(uid):
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user",   "content": text},
                    ],
                    "max_tokens": 800,
                }
                data   = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
                result = data["choices"][0]["message"]["content"]
            else:
                encoded = urllib.parse.quote(text)
                async with session.get(
                    f"https://text.pollinations.ai/{encoded}?model={model}&system={urllib.parse.quote(sys_prompt)}"
                ) as resp:
                    resp.raise_for_status()
                    result = await resp.text()

        embed = discord.Embed(
            title=f"📝 Summary — {STYLE_LABELS.get(style, style)}",
            description=result[:4096],
            color=BOT_COLOR
        )
        embed.set_footer(text=f"Model: {model_name}")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /poll — AI genera domanda + 4 opzioni
# ──────────────────────────────────────────────
@bot.tree.command(name="poll", description="AI generates a poll question with 4 options and auto-adds reactions")
@app_commands.describe(topic="Poll topic (e.g. best programming language, favorite season)")
async def cmd_poll(interaction: discord.Interaction, topic: str):
    uid   = interaction.user.id
    await interaction.response.defer(thinking=True)
    model = get_model(uid, "text")
    key   = get_key(uid)
    sys_prompt = (
        "You are a poll generator. Given a topic, create a fun and engaging poll question with exactly 4 short answer options. "
        'Respond ONLY with valid JSON — no markdown, no backticks, no extra text — in this exact format: '
        '{"question": "...", "options": ["...", "...", "...", "..."]}'
    )

    try:
        async with aiohttp.ClientSession() as session:
            if has_personal_key(uid):
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user",   "content": f"Create a poll about: {topic}"},
                    ],
                    "max_tokens": 300,
                }
                data = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
                raw  = data["choices"][0]["message"]["content"]
            else:
                encoded = urllib.parse.quote(f"Create a poll about: {topic}")
                async with session.get(
                    f"https://text.pollinations.ai/{encoded}?model={model}&system={urllib.parse.quote(sys_prompt)}"
                ) as resp:
                    resp.raise_for_status()
                    raw = await resp.text()

        raw       = raw.strip().strip("```json").strip("```").strip()
        poll_data = json.loads(raw)
        question  = poll_data["question"]
        options   = poll_data["options"][:4]
        letters   = ["🇦", "🇧", "🇨", "🇩"]

        desc = f"**{question}**\n\n"
        for i, opt in enumerate(options):
            desc += f"{letters[i]} {opt}\n"

        embed = discord.Embed(title="📊 Poll", description=desc, color=BOT_COLOR)
        embed.set_footer(text=f"React to vote! • Topic: {topic[:60]}")
        msg = await interaction.followup.send(embed=embed)

        for letter in letters[:len(options)]:
            await msg.add_reaction(letter)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Poll error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /roast — roast comico
# ──────────────────────────────────────────────
@bot.tree.command(name="roast", description="Get a harmless but spicy AI roast 🔥")
@app_commands.describe(target="Who (or what) to roast")
async def cmd_roast(interaction: discord.Interaction, target: str):
    uid   = interaction.user.id
    await interaction.response.defer(thinking=True)
    model = get_model(uid, "text")
    key   = get_key(uid)
    sys_prompt = (
        "You are a comedy roast master. Write a short, funny, and harmless roast — purely playful, "
        "no hate speech, no slurs, no offensive content. Keep it to 3–4 sentences max. "
        "Pure wit and humor only."
    )

    try:
        async with aiohttp.ClientSession() as session:
            if has_personal_key(uid):
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user",   "content": f"Roast: {target}"},
                    ],
                    "max_tokens": 300,
                }
                data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
                roast = data["choices"][0]["message"]["content"]
            else:
                encoded = urllib.parse.quote(f"Roast: {target}")
                async with session.get(
                    f"https://text.pollinations.ai/{encoded}?model={model}&system={urllib.parse.quote(sys_prompt)}"
                ) as resp:
                    resp.raise_for_status()
                    roast = await resp.text()

        embed = discord.Embed(title=f"🔥 Roasting: {target}", description=roast, color=0xFF4500)
        embed.set_footer(text=f"Requested by {interaction.user.display_name} • all in good fun 😄")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /batch — genera variazioni in parallelo
# ──────────────────────────────────────────────
@bot.tree.command(name="batch", description="Generate multiple image variations in parallel")
@app_commands.describe(prompt="Image description", count="Number of variations (2–4)")
@app_commands.choices(count=[
    app_commands.Choice(name="2 images", value=2),
    app_commands.Choice(name="3 images", value=3),
    app_commands.Choice(name="4 images", value=4),
])
async def cmd_batch(interaction: discord.Interaction, prompt: str, count: int = 2):
    uid        = interaction.user.id
    model_name = USER_MODELS.get(uid, {}).get("image", DEFAULT_MODELS["image"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model   = get_model(uid, "image")
    encoded = urllib.parse.quote(prompt)

    def make_url(seed: int) -> str:
        if has_personal_key(uid):
            return (f"https://gen.pollinations.ai/image/{encoded}"
                    f"?model={model}&width=1024&height=1024&nologo=true&seed={seed}")
        return (f"https://image.pollinations.ai/prompt/{encoded}"
                f"?model={model}&width=1024&height=1024&nologo=true&seed={seed}&nofeed=true")

    async def fetch_one(session: aiohttp.ClientSession, url: str) -> bytes:
        if has_personal_key(uid):
            async with session.get(url, headers=auth_headers(get_key(uid))) as resp:
                resp.raise_for_status()
                return await resp.read()
        else:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()

    try:
        seeds    = [random.randint(1, 9_999_999) for _ in range(count)]
        urls     = [make_url(s) for s in seeds]
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(*[fetch_one(session, u) for u in urls], return_exceptions=True)

        good = [(i, r, urls[i]) for i, r in enumerate(results) if not isinstance(r, Exception)]
        if not good:
            raise Exception("All generations failed")

        files = [discord.File(fp=io.BytesIO(r), filename=f"nov_batch_{i+1}.png") for i, r, _ in good]

        # View con un bottone "📋 #N" per ogni immagine riuscita
        class BatchURLView(discord.ui.View):
            def __init__(self, image_urls: list[str]):
                super().__init__(timeout=600)
                self._urls = image_urls
                for idx, u in enumerate(image_urls):
                    self.add_item(discord.ui.Button(
                        label=f"🔗 #{idx+1}",
                        style=discord.ButtonStyle.link,
                        url=u,
                        row=0
                    ))
                # Un bottone "Copy All" che manda tutti gli URL in ephemeral
                self._all = "\n".join(f"**#{i+1}** `{u}`" for i, u in enumerate(image_urls))

            @discord.ui.button(label="📋 Copy All URLs", style=discord.ButtonStyle.secondary, row=1)
            async def copy_all(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message(self._all, ephemeral=True)

        good_urls = [u for _, _, u in good]
        embed = discord.Embed(
            title=f"🖼️ Batch — {len(good)}/{count} generated",
            description=f"**Prompt:** {prompt[:200]}",
            color=BOT_COLOR
        )
        embed.set_footer(text=f"Model: {model_name} • {count} parallel variations")
        await interaction.followup.send(embed=embed, files=files, view=BatchURLView(good_urls))

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Batch error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /edit — modifica immagine con Kontext
# ──────────────────────────────────────────────
@bot.tree.command(name="edit", description="Edit an image with FLUX.1 Kontext (requires account)")
@app_commands.describe(image_url="URL of the source image", prompt="What to change in the image")
async def cmd_edit(interaction: discord.Interaction, image_url: str, prompt: str):
    uid = interaction.user.id
    if not has_personal_key(uid):
        await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    key = get_key(uid)

    try:
        encoded_prompt = urllib.parse.quote(prompt)
        encoded_img    = urllib.parse.quote(image_url)
        seed           = random.randint(1, 9_999_999)
        edit_url = (
            f"https://gen.pollinations.ai/image/{encoded_prompt}"
            f"?model=kontext&input_image={encoded_img}&nologo=true&seed={seed}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(edit_url, headers=auth_headers(key)) as resp:
                resp.raise_for_status()
                img_bytes = await resp.read()

        file  = discord.File(fp=io.BytesIO(img_bytes), filename="nov_edit.png")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name="✏️ FLUX.1 Kontext — Image Edit")
        embed.add_field(name="Edit prompt", value=prompt[:500], inline=False)
        embed.set_image(url="attachment://nov_edit.png")
        embed.set_footer(text="Powered by FLUX.1 Kontext")
        await interaction.followup.send(embed=embed, file=file, view=ImageURLView(edit_url))

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(
            title="❌ Edit error",
            description=f"`{e}`\n\n💡 Make sure the image URL is publicly accessible.",
            color=0xED4245
        ))

# ──────────────────────────────────────────────
#  /reset — chiude e archivia il thread corrente
# ──────────────────────────────────────────────
@bot.tree.command(name="reset", description="Close and archive this chat thread (owner only)")
async def cmd_reset(interaction: discord.Interaction):
    ch          = interaction.channel
    thread_data = CHAT_THREADS.get(ch.id)

    if not thread_data:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Not in a Nov thread",
                description="Use this command inside an active Nov chat thread.",
                color=0xED4245
            ), ephemeral=True
        )
        return

    if thread_data["user_id"] != interaction.user.id:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔒 Not your thread",
                description="Only the thread owner can reset it.",
                color=0xFEE75C
            ), ephemeral=True
        )
        return

    del CHAT_THREADS[ch.id]
    await interaction.response.send_message(
        embed=discord.Embed(title="🗑️ Thread closed", description="This chat session has been ended.", color=0x57F287)
    )
    if isinstance(ch, discord.Thread):
        try:
            await ch.edit(archived=True, locked=True)
        except Exception:
            pass

# ──────────────────────────────────────────────
#  /export — scarica cronologia come .txt
# ──────────────────────────────────────────────
@bot.tree.command(name="export", description="Download this thread's chat history as a .txt file")
async def cmd_export(interaction: discord.Interaction):
    ch          = interaction.channel
    thread_data = CHAT_THREADS.get(ch.id)

    if not thread_data:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Not in a Nov thread",
                description="Use this inside an active Nov chat thread.",
                color=0xED4245
            ), ephemeral=True
        )
        return

    history = thread_data.get("history", [])
    lines   = [f"Nov Chat Export — {interaction.user.display_name}\n", "=" * 50 + "\n\n"]
    for msg in history:
        role = msg["role"].upper()
        if role == "SYSTEM":
            continue
        lines.append(f"[{role}]\n{msg['content']}\n\n")

    content = "".join(lines)
    file    = discord.File(fp=io.BytesIO(content.encode("utf-8")), filename="nov_chat_export.txt")
    await interaction.response.send_message(
        content="📄 Here's your chat history:", file=file, ephemeral=True
    )

# ──────────────────────────────────────────────
#  /profile — tier, GitHub, balance Pollen
# ──────────────────────────────────────────────
@bot.tree.command(name="profile", description="View your Pollinations profile (requires account)")
async def cmd_profile(interaction: discord.Interaction):
    uid = interaction.user.id
    if not has_personal_key(uid):
        await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    key = get_key(uid)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{AUTH_URL}/userinfo",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                resp.raise_for_status()
                ui = await resp.json()

        username = ui.get("preferred_username") or ui.get("name") or "Unknown"
        github   = ui.get("github_username") or username
        tier     = ui.get("tier") or "Free"
        pollen   = ui.get("pollen_balance") or ui.get("balance") or "N/A"

        embed = discord.Embed(title="👤 Your Pollinations Profile", color=BOT_COLOR)
        embed.add_field(name="🐙 GitHub",   value=f"`{github}`",  inline=True)
        embed.add_field(name="⚡ Tier",     value=f"`{tier}`",    inline=True)
        embed.add_field(name="🌸 Pollen",   value=f"`{pollen}`",  inline=True)
        embed.set_footer(text="enter.pollinations.ai • manage your account online")
        await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True
        )

# ──────────────────────────────────────────────
#  /privchat — thread privato senza primo messaggio
# ──────────────────────────────────────────────
@bot.tree.command(name="privchat", description="Open a private thread with Nov (no message needed)")
async def cmd_privchat(interaction: discord.Interaction):
    uid                  = interaction.user.id
    model_name           = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
    in_guild_text_channel = (
        interaction.guild is not None and isinstance(interaction.channel, discord.TextChannel)
    )

    await interaction.response.defer(thinking=True, ephemeral=in_guild_text_channel)
    sys_prompt = build_system_prompt(uid, "", interaction.guild_id)

    try:
        if in_guild_text_channel:
            thread = await interaction.channel.create_thread(
                name=f"🔒 Nov · {interaction.user.display_name}",
                type=discord.ChannelType.private_thread,
                invitable=False,
                auto_archive_duration=60,
            )
            await thread.add_user(interaction.user)

            greeting = (
                f"Hey {interaction.user.display_name}! 👋\n"
                "This is your private space with Nov. Just type here — I'll reply to everything.\n"
                "Use `/reset` to end the session."
            )
            intro = discord.Embed(description=f"🔒 **Private chat started**\n\n{greeting}", color=0x2B2D31)
            intro.set_author(name=f"Nov Chat (Private) — {model_name}")
            await thread.send(embed=intro)

            CHAT_THREADS[thread.id] = {
                "user_id": uid,
                "model":   get_model(uid, "text"),
                "system":  sys_prompt,
                "key":     get_key(uid),
                "has_key": has_personal_key(uid),
                "private": True,
                "history": [{"role": "system", "content": sys_prompt}],
            }
            await interaction.followup.send(f"🔒 Private thread opened! → {thread.mention}", ephemeral=True)

        else:
            # In DM è già privato — attiva semplicemente la sessione
            greeting = (
                f"Hey {interaction.user.display_name}! 👋\n"
                "Private chat active. Just type here — I'll reply to everything.\n"
                "Use `/reset` to end the session."
            )
            intro = discord.Embed(description=f"🔒 **Private chat started**\n\n{greeting}", color=0x2B2D31)
            intro.set_author(name=f"Nov Chat (Private) — {model_name}")
            await interaction.followup.send(embed=intro)

            CHAT_THREADS[interaction.channel.id] = {
                "user_id": uid,
                "model":   get_model(uid, "text"),
                "system":  sys_prompt,
                "key":     get_key(uid),
                "has_key": has_personal_key(uid),
                "private": True,
                "history": [{"role": "system", "content": sys_prompt}],
            }

    except discord.Forbidden:
        await interaction.followup.send(embed=discord.Embed(
            title="❌ Missing permissions",
            description=(
                "Nov can't create private threads here.\n\n"
                "Make sure **Community** is enabled and Nov has "
                "**Create Private Threads** permission."
            ),
            color=0xED4245
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True
        )

# ──────────────────────────────────────────────
#  /help
# ──────────────────────────────────────────────
@bot.tree.command(name="help", description="Show all Nov commands")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(title=f"✨ Nov — Commands", description="AI-powered bot by Pollinations", color=BOT_COLOR)
    embed.add_field(name="🔑 Setup",
        value="`/connect` · Link your Pollinations key\n`/disconnect` · Remove your key\n`/info` · View your settings\n`/profile` · Tier, GitHub & Pollen balance",
        inline=False)
    embed.add_field(name="🧠 Memory",
        value="`/remember [key] [value]` · Save info about you\n`/forget` · Clear your memory",
        inline=False)
    embed.add_field(name="💬 Chat",
        value=(
            "`/text` · Open AI chat thread\n"
            "`/privtext` · 🔒 Private chat thread (with first message)\n"
            "`/privchat` · 🔒 Private thread (no message needed)\n"
            "`/ask [prompt]` · Instant reply, no thread\n"
            "`/reset` · Close & archive current thread *(owner)*\n"
            "`/export` · Download chat history as .txt"
        ), inline=False)
    embed.add_field(name="🖼️ Image",
        value=(
            "`/image [prompt]` · Generate an image\n"
            "`/batch [prompt] [2-4]` · Multiple variations in parallel\n"
            "`/edit [url] [prompt]` · Edit image with Kontext *(account)*"
        ), inline=False)
    embed.add_field(name="🔊 Audio / 🎬 Video",
        value="`/audio [text]` · Text to speech\n`/video [prompt]` · Generate a video *(account)*",
        inline=False)
    embed.add_field(name="⚙️ Models",
        value="`/model` · Change AI model *(autocomplete!)*\n`/models` · List available models",
        inline=False)
    embed.add_field(name="🛠️ Utilities",
        value=(
            "`/ping` · Latency with colored bar\n"
            "`/translate [text] [lang]` · Translate to any language\n"
            "`/summarize [text] [style]` · 4 styles: bullets / paragraph / sentence / TL;DR\n"
            "`/poll [topic]` · AI poll with auto reactions 🇦🇧🇨🇩\n"
            "`/roast [target]` · Harmless but spicy roast 🔥\n"
            "`/matrix [message]` · Animated Matrix rain 💚\n"
            "`/event [title] [date]` · AI-generated event announcement 📅\n"
        ), inline=False)
    embed.add_field(name="🎭 Server Identity",
        value=(
            "`/globalidentity [name] [personality]` · Give NovAI a custom name & persona in this server\n"
            "`/resetidentity` · Revert to default *(only the activator)*"
        ), inline=False)
    embed.set_footer(text=f"Nov v{BOT_VERSION} · Works in DMs too! · enter.pollinations.ai")
    await interaction.response.send_message(embed=embed)


# ──────────────────────────────────────────────
#  /globalidentity — nome e personalità per server
# ──────────────────────────────────────────────
@bot.tree.command(name="globalidentity", description="Give NovAI a custom name & personality in this server")
@app_commands.describe(
    name="Bot name for this server (e.g. 'Aria', 'Max', 'Nexus')",
    personality="Custom personality (e.g. 'You are a snarky hacker who loves 90s references.')"
)
async def cmd_globalidentity(interaction: discord.Interaction, name: str, personality: str):
    if not interaction.guild:
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ Server only", description="This command only works in a server.", color=0xED4245),
            ephemeral=True
        )
        return

    gid = interaction.guild.id

    # Già impostata da qualcun altro?
    if gid in SERVER_IDENTITY and SERVER_IDENTITY[gid]["owner_id"] != interaction.user.id:
        owner_id = SERVER_IDENTITY[gid]["owner_id"]
        current  = SERVER_IDENTITY[gid]["name"]
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔒 Identity already set",
                description=(
                    f"This server already has a custom identity: **{current}**\n"
                    f"Set by <@{owner_id}>. Only they can change or reset it with `/resetidentity`."
                ),
                color=0xFEE75C
            ), ephemeral=True
        )
        return

    SERVER_IDENTITY[gid] = {
        "name":        name[:32].strip(),
        "personality": personality[:500].strip(),
        "owner_id":    interaction.user.id,
    }

    embed = discord.Embed(
        title=f"✅ Identity set — {name}",
        description=(
            f"In this server, NovAI will now answer as **{name}**.\n\n"
            f"**Personality:**\n> {personality[:280]}{'…' if len(personality) > 280 else ''}\n\n"
            f"*Only you can change or remove this with `/resetidentity`.*"
        ),
        color=0x57F287
    )
    embed.set_footer(text=f"Set by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


# ──────────────────────────────────────────────
#  /resetidentity — rimuove identità del server
# ──────────────────────────────────────────────
@bot.tree.command(name="resetidentity", description="Reset NovAI's custom server identity (only the activator can do this)")
async def cmd_resetidentity(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ Server only", description="This command only works in a server.", color=0xED4245),
            ephemeral=True
        )
        return

    gid = interaction.guild.id

    if gid not in SERVER_IDENTITY:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ℹ️ No custom identity",
                description="This server doesn't have a custom identity set.",
                color=BOT_COLOR
            ), ephemeral=True
        )
        return

    identity = SERVER_IDENTITY[gid]
    if identity["owner_id"] != interaction.user.id:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔒 Not authorized",
                description=f"Only <@{identity['owner_id']}> can reset the identity for this server.",
                color=0xED4245
            ), ephemeral=True
        )
        return

    old_name = identity["name"]
    del SERVER_IDENTITY[gid]

    await interaction.response.send_message(
        embed=discord.Embed(
            title="🔄 Identity reset",
            description=f"**{old_name}** removed. NovAI is back to its default identity in this server.",
            color=0x57F287
        )
    )


# ──────────────────────────────────────────────
#  /matrix — pioggia Matrix animata con ANSI
# ──────────────────────────────────────────────
_MATRIX_CHARS = list("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン01234567890101110100101")

def _matrix_frame(cols: int = 18, rows: int = 9, reveal: str = "") -> str:
    """Genera un frame della pioggia Matrix in ANSI Discord."""
    mid = rows // 2
    lines = []
    for r in range(rows):
        if reveal and r == mid:
            msg  = reveal[:cols]
            pad  = (cols - len(msg)) // 2
            side = cols - pad - len(msg)
            left  = "".join(random.choice(_MATRIX_CHARS) for _ in range(pad))
            right = "".join(random.choice(_MATRIX_CHARS) for _ in range(side))
            line = (
                f"\u001b[2;32m{left}\u001b[0m"
                f"\u001b[1;37m {msg} \u001b[0m"
                f"\u001b[2;32m{right}\u001b[0m"
            )
        else:
            raw = "".join(random.choice(_MATRIX_CHARS) for _ in range(cols))
            # Colonna "testa" casuale più brillante
            head = random.randint(0, cols - 1)
            line = ""
            for i, ch in enumerate(raw):
                if i == head:
                    line += f"\u001b[1;32m{ch}\u001b[0m"
                elif random.random() > 0.55:
                    line += f"\u001b[32m{ch}\u001b[0m"
                else:
                    line += f"\u001b[2;32m{ch}\u001b[0m"
        lines.append(line)
    return "```ansi\n" + "\n".join(lines) + "\n```"


@bot.tree.command(name="matrix", description="Display an animated Matrix rain in the channel 💚")
@app_commands.describe(message="Secret message to reveal at the end (optional)")
async def cmd_matrix(interaction: discord.Interaction, message: str = ""):
    await interaction.response.defer()

    reveal_text = message.strip()[:16] if message.strip() else "SYSTEM ONLINE"

    # Frame 1 — invio iniziale
    msg = await interaction.followup.send(_matrix_frame())

    # Frame 2-5 — animazione
    for _ in range(4):
        await asyncio.sleep(0.85)
        try:
            await msg.edit(content=_matrix_frame())
        except Exception:
            break

    # Frame finale — rivela messaggio
    await asyncio.sleep(0.85)
    final_frame = _matrix_frame(reveal=reveal_text)
    caption = f"\n-# 🔓 `{reveal_text}`" if message.strip() else "\n-# 💚 Wake up, Neo…"
    try:
        await msg.edit(content=final_frame + caption)
    except Exception:
        pass


# ──────────────────────────────────────────────
#  /event — annuncio evento generato da AI
# ──────────────────────────────────────────────
@bot.tree.command(name="event", description="Create an AI-powered event announcement 🎉")
@app_commands.describe(
    title="Event name",
    date="When? (e.g. 'Saturday July 12th at 8PM UTC')",
    details="Extra details about the event (optional)"
)
async def cmd_event(interaction: discord.Interaction, title: str, date: str, details: str = ""):
    await interaction.response.defer(thinking=True)
    uid = interaction.user.id
    key = get_key(uid)

    ai_prompt = (
        f"Write a hype Discord event announcement for '{title}' happening on {date}. "
        f"{'Additional details: ' + details if details else ''} "
        "Make it enthusiastic, use 2-3 relevant emojis, max 120 words. "
        "Return ONLY the announcement body text, nothing else."
    )

    try:
        async with aiohttp.ClientSession() as session:
            data = await api_post_json(session, f"{BASE_URL}/chat/completions", {
                "model":    "openai",
                "messages": [{"role": "user", "content": ai_prompt}],
                "max_tokens": 220,
            }, key)
        ai_text = data["choices"][0]["message"]["content"].strip()
    except Exception:
        ai_text = details or "Join us for this special event!"

    colors = [0x5865F2, 0xFEE75C, 0x57F287, 0xEB459E, 0xED4245]
    embed = discord.Embed(
        title=f"📅  {title}",
        description=ai_text,
        color=random.choice(colors)
    )
    embed.add_field(name="🗓️ When",  value=f"`{date}`",                   inline=True)
    embed.add_field(name="📢 Host",   value=interaction.user.mention,       inline=True)
    if interaction.guild:
        embed.add_field(name="📍 Where", value=interaction.guild.name,         inline=True)
    embed.set_footer(text="React below if you're coming! ✅ = yes · ❌ = no · 🤔 = maybe")

    followup_msg = await interaction.followup.send(embed=embed)
    for emoji in ["✅", "❌", "🤔"]:
        try:
            await followup_msg.add_reaction(emoji)
        except Exception:
            pass



# ──────────────────────────────────────────────
#  START
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌  DISCORD_TOKEN missing in .env!")
        exit(1)
    print(f"🚀  Starting {BOT_NAME} v{BOT_VERSION}...")
    bot.run(DISCORD_TOKEN)
