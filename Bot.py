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
# Servizi collegati per utente { uid: { "ai": { "provider": "key" }, "social": { "telegram": {"token","chat_id"} } } }
USER_CONNECTIONS: dict[int, dict] = {}

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
#  /connect — Hub di connessione (AI · Social · Other)
# ──────────────────────────────────────────────

# ── Helpers connessione ──
def get_user_conn(uid: int, category: str, service: str = None):
    """Ritorna i dati di connessione per categoria/servizio."""
    cat = USER_CONNECTIONS.get(uid, {}).get(category, {})
    return cat.get(service) if service else cat

def set_user_conn(uid: int, category: str, service: str, data):
    """Salva una connessione."""
    if uid not in USER_CONNECTIONS:
        USER_CONNECTIONS[uid] = {}
    if category not in USER_CONNECTIONS[uid]:
        USER_CONNECTIONS[uid][category] = {}
    USER_CONNECTIONS[uid][category][service] = data

def del_user_conn(uid: int, category: str, service: str):
    """Rimuove una connessione."""
    try:
        del USER_CONNECTIONS[uid][category][service]
    except KeyError:
        pass

def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "•" * len(key)
    return key[:4] + "•" * max(0, len(key) - 7) + key[-3:]

# ── Modal per inserire API key ──
class ApiKeyModal(discord.ui.Modal):
    def __init__(self, service: str, category: str, label: str, placeholder: str, hint: str = ""):
        super().__init__(title=f"Connect {service}")
        self._service  = service
        self._category = category
        self._hint     = hint
        self.key_input = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            style=discord.TextStyle.short,
            required=True,
            max_length=512,
        )
        self.add_item(self.key_input)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        key = self.key_input.value.strip()
        set_user_conn(uid, self._category, self._service, key)
        embed = discord.Embed(
            title=f"✅ {self._service} connected!",
            description=f"Key saved: `{mask_key(key)}`",
            color=0x57F287
        )
        if self._hint:
            embed.set_footer(text=self._hint)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ════════════════════════════════════════════════
#  MODALI PER OGNI SERVIZIO
# ════════════════════════════════════════════════

# ── Telegram ──
class TelegramModal(discord.ui.Modal, title="Connect Telegram Bot"):
    token   = discord.ui.TextInput(label="Bot Token (from @BotFather)", placeholder="123456:ABCdef...", style=discord.TextStyle.short, required=True, max_length=200)
    chat_id = discord.ui.TextInput(label="Default Chat ID (optional)", placeholder="-100123456789 or @username", style=discord.TextStyle.short, required=False, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        tok = self.token.value.strip()
        cid = self.chat_id.value.strip()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.telegram.org/bot{tok}/getMe") as resp:
                    data = await resp.json()
            if not data.get("ok"):
                await interaction.response.send_message(embed=discord.Embed(title="❌ Invalid token", description="Telegram rejected the token.", color=0xED4245), ephemeral=True)
                return
            bot_info = data["result"]
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)
            return
        set_user_conn(uid, "social", "telegram", {"token": tok, "chat_id": cid or None, "username": bot_info.get("username","")})
        embed = discord.Embed(title="✅ Telegram connected!", description=(
            f"**Bot:** @{bot_info.get('username','?')} (`{bot_info.get('first_name','?')}`)\n"
            f"**Default chat:** `{cid or 'not set'}`\n\nUse `/tg-send` and `/tg-read` from Discord!"
        ), color=0x229ED9)
        embed.set_footer(text="Stored in memory only")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ── Twitter / X ──
class TwitterModal(discord.ui.Modal, title="Connect Twitter / X"):
    api_key    = discord.ui.TextInput(label="API Key",              placeholder="Your Twitter API Key",        style=discord.TextStyle.short, required=True,  max_length=100)
    api_secret = discord.ui.TextInput(label="API Secret",           placeholder="Your Twitter API Secret",     style=discord.TextStyle.short, required=True,  max_length=100)
    acc_token  = discord.ui.TextInput(label="Access Token",         placeholder="Your Access Token",           style=discord.TextStyle.short, required=True,  max_length=200)
    acc_secret = discord.ui.TextInput(label="Access Token Secret",  placeholder="Your Access Token Secret",    style=discord.TextStyle.short, required=True,  max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        set_user_conn(uid, "social", "twitter", {
            "api_key":    self.api_key.value.strip(),
            "api_secret": self.api_secret.value.strip(),
            "acc_token":  self.acc_token.value.strip(),
            "acc_secret": self.acc_secret.value.strip(),
        })
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Twitter / X connected!",
            description="Use `/tweet [text]` to post from Discord.",
            color=0x1DA1F2
        ), ephemeral=True)

# ── Reddit ──
class RedditModal(discord.ui.Modal, title="Connect Reddit"):
    client_id     = discord.ui.TextInput(label="Client ID",     placeholder="From reddit.com/prefs/apps", style=discord.TextStyle.short, required=True,  max_length=50)
    client_secret = discord.ui.TextInput(label="Client Secret", placeholder="App secret",                 style=discord.TextStyle.short, required=True,  max_length=100)
    username      = discord.ui.TextInput(label="Reddit Username",placeholder="u/yourname",                style=discord.TextStyle.short, required=True,  max_length=50)
    password      = discord.ui.TextInput(label="App Password",  placeholder="Your Reddit password",       style=discord.TextStyle.short, required=True,  max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        set_user_conn(uid, "social", "reddit", {
            "client_id":     self.client_id.value.strip(),
            "client_secret": self.client_secret.value.strip(),
            "username":      self.username.value.strip(),
            "password":      self.password.value.strip(),
        })
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Reddit connected!",
            description="Use `/reddit-post` and `/reddit-read` from Discord.",
            color=0xFF4500
        ), ephemeral=True)

# ── Slack ──
class SlackModal(discord.ui.Modal, title="Connect Slack"):
    token   = discord.ui.TextInput(label="Bot Token (xoxb-...)", placeholder="xoxb-...", style=discord.TextStyle.short, required=True,  max_length=200)
    channel = discord.ui.TextInput(label="Default Channel (optional)", placeholder="#general or C012AB3CD", style=discord.TextStyle.short, required=False, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        tok = self.token.value.strip()
        # Verify token
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://slack.com/api/auth.test", headers={"Authorization": f"Bearer {tok}"}) as resp:
                    data = await resp.json()
            if not data.get("ok"):
                await interaction.response.send_message(embed=discord.Embed(title="❌ Invalid Slack token", description=data.get("error","unknown"), color=0xED4245), ephemeral=True)
                return
            team = data.get("team","?")
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)
            return
        set_user_conn(uid, "social", "slack", {"token": tok, "channel": self.channel.value.strip() or None, "team": team})
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Slack connected!",
            description=f"**Workspace:** {team}\nUse `/slack-send` from Discord.",
            color=0x4A154B
        ), ephemeral=True)

# ── Mastodon ──
class MastodonModal(discord.ui.Modal, title="Connect Mastodon"):
    instance = discord.ui.TextInput(label="Instance URL", placeholder="https://mastodon.social", style=discord.TextStyle.short, required=True,  max_length=100)
    token    = discord.ui.TextInput(label="Access Token", placeholder="Your access token",        style=discord.TextStyle.short, required=True,  max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        uid      = interaction.user.id
        base_url = self.instance.value.strip().rstrip("/")
        tok      = self.token.value.strip()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/v1/accounts/verify_credentials", headers={"Authorization": f"Bearer {tok}"}) as resp:
                    data = await resp.json()
            if "error" in data:
                await interaction.response.send_message(embed=discord.Embed(title="❌ Invalid token", description=data["error"], color=0xED4245), ephemeral=True)
                return
            acct = data.get("acct","?")
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)
            return
        set_user_conn(uid, "social", "mastodon", {"base_url": base_url, "token": tok, "acct": acct})
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Mastodon connected!",
            description=f"**Account:** @{acct}@{base_url.replace('https://','')}\nUse `/toot` from Discord.",
            color=0x6364FF
        ), ephemeral=True)

# ── Notion ──
class NotionModal(discord.ui.Modal, title="Connect Notion"):
    token   = discord.ui.TextInput(label="Integration Token (secret_...)", placeholder="secret_...", style=discord.TextStyle.short, required=True,  max_length=200)
    db_id   = discord.ui.TextInput(label="Default Database ID (optional)", placeholder="32-char hex or URL", style=discord.TextStyle.short, required=False, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        tok = self.token.value.strip()
        db  = self.db_id.value.strip().replace("-","")[:32] or None
        set_user_conn(uid, "productivity", "notion", {"token": tok, "db_id": db})
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Notion connected!",
            description="Use `/notion-add` and `/notion-read` from Discord.",
            color=0x000000
        ), ephemeral=True)

# ── GitHub (con default repo) ──
class GitHubModal(discord.ui.Modal, title="Connect GitHub"):
    token = discord.ui.TextInput(label="Personal Access Token (ghp_...)", placeholder="ghp_...", style=discord.TextStyle.short, required=True, max_length=200)
    repo  = discord.ui.TextInput(label="Default repo (optional)", placeholder="owner/repo-name", style=discord.TextStyle.short, required=False, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        tok = self.token.value.strip()
        rep = self.repo.value.strip() or None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com/user", headers={"Authorization": f"token {tok}", "Accept": "application/vnd.github+json"}) as resp:
                    data = await resp.json()
            if "login" not in data:
                await interaction.response.send_message(embed=discord.Embed(title="❌ Invalid token", color=0xED4245), ephemeral=True)
                return
            login = data["login"]
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)
            return
        set_user_conn(uid, "productivity", "github", {"token": tok, "repo": rep, "login": login})
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ GitHub connected!",
            description=f"**User:** @{login}\n**Default repo:** `{rep or 'not set'}`\nUse `/gh-issue` and `/gh-read` from Discord.",
            color=0x24292E
        ), ephemeral=True)

# ── Email SMTP ──
class EmailModal(discord.ui.Modal, title="Connect Email (SMTP)"):
    host     = discord.ui.TextInput(label="SMTP Host",          placeholder="smtp.gmail.com",     style=discord.TextStyle.short, required=True,  max_length=100)
    username = discord.ui.TextInput(label="Email / Username",   placeholder="you@gmail.com",      style=discord.TextStyle.short, required=True,  max_length=100)
    password = discord.ui.TextInput(label="App Password",       placeholder="App-specific password", style=discord.TextStyle.short, required=True, max_length=100)
    port     = discord.ui.TextInput(label="Port (default 587)", placeholder="587",                style=discord.TextStyle.short, required=False, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        set_user_conn(uid, "productivity", "email", {
            "host":     self.host.value.strip(),
            "username": self.username.value.strip(),
            "password": self.password.value.strip(),
            "port":     int(self.port.value.strip() or 587),
        })
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Email connected!",
            description=f"**From:** {self.username.value.strip()}\nUse `/email-send` from Discord.",
            color=0xEA4335
        ), ephemeral=True)

# ── Pastebin ──
class PastebinModal(discord.ui.Modal, title="Connect Pastebin"):
    api_key = discord.ui.TextInput(label="Pastebin API Key", placeholder="From pastebin.com/api", style=discord.TextStyle.short, required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        set_user_conn(uid, "productivity", "pastebin", self.api_key.value.strip())
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Pastebin connected!",
            description="Use `/paste [content]` to create pastes from Discord.",
            color=0x02A6C4
        ), ephemeral=True)

# ── Webhook ──
class WebhookModal(discord.ui.Modal, title="Connect a Webhook"):
    url   = discord.ui.TextInput(label="Webhook URL", placeholder="https://...", style=discord.TextStyle.short, required=True, max_length=500)
    label = discord.ui.TextInput(label="Label (optional)", placeholder="My Webhook", style=discord.TextStyle.short, required=False, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        lbl = self.label.value.strip() or "webhook"
        set_user_conn(uid, "social", f"webhook_{lbl}", self.url.value.strip())
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Webhook connected!",
            description=f"**Label:** `{lbl}`\nUse `/wh-send {lbl} [payload]` to fire it.",
            color=0x57F287
        ), ephemeral=True)

# ════════════════════════════════════════════════
#  CONNECT VIEWS (Social / Productivity)
# ════════════════════════════════════════════════

# ── View categoria Social ──
class ConnectSocialView(discord.ui.View):
    _SERVICES = {
        "telegram":  ("✈️",  "Telegram Bot",   "Bot token via @BotFather → send & read messages"),
        "twitter":   ("🐦",  "Twitter / X",    "Post tweets & read timeline via API v2"),
        "reddit":    ("🤖",  "Reddit",          "Post & read subreddits via Reddit API"),
        "slack":     ("💼",  "Slack",           "Send messages to channels via Bot Token"),
        "mastodon":  ("🐘",  "Mastodon",        "Post toots via any Mastodon instance"),
        "webhook":   ("🔗",  "Webhook",         "POST JSON to any URL when triggered"),
        "discord_bot":("🤖", "Discord Bot",     "Relay commands to another bot token you own"),
    }

    def __init__(self, uid: int):
        super().__init__(timeout=120)
        self._uid = uid
        options = []
        for svc, (emoji, label, desc) in self._SERVICES.items():
            connected = bool(get_user_conn(uid, "social", svc) or any(
                k.startswith("webhook_") for k in get_user_conn(uid, "social") or {}
            ) if svc == "webhook" else False)
            options.append(discord.SelectOption(
                label=label, emoji=emoji,
                description=("✅ Connected — " if connected and svc != "webhook" else "") + desc[:50],
                value=svc
            ))
        sel = discord.ui.Select(placeholder="Choose a social service...", options=options, min_values=1, max_values=1)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        svc = interaction.data["values"][0]
        modal_map = {
            "telegram":   TelegramModal,
            "twitter":    TwitterModal,
            "reddit":     RedditModal,
            "slack":      SlackModal,
            "mastodon":   MastodonModal,
            "webhook":    WebhookModal,
        }
        if svc == "discord_bot":
            modal = ApiKeyModal(service="discord_bot", category="social", label="Bot Token (another bot you own)", placeholder="MTxx...YYYY", hint="Nov can relay commands to this bot via Discord API")
            await interaction.response.send_modal(modal)
        elif svc in modal_map:
            await interaction.response.send_modal(modal_map[svc]())

# ── View categoria Productivity ──
class ConnectProductivityView(discord.ui.View):
    _SERVICES = {
        "github":   ("🐙", "GitHub",   "Create issues, read repos via Personal Access Token"),
        "notion":   ("📓", "Notion",   "Create pages & read databases via Integration Token"),
        "email":    ("📧", "Email",    "Send emails from Discord via SMTP"),
        "pastebin": ("📋", "Pastebin", "Create and share pastes from Discord"),
    }

    def __init__(self, uid: int):
        super().__init__(timeout=120)
        self._uid = uid
        options = []
        for svc, (emoji, label, desc) in self._SERVICES.items():
            connected = bool(get_user_conn(uid, "productivity", svc))
            options.append(discord.SelectOption(
                label=label, emoji=emoji,
                description=("✅ Connected — " if connected else "") + desc[:50],
                value=svc
            ))
        sel = discord.ui.Select(placeholder="Choose a productivity service...", options=options, min_values=1, max_values=1)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        svc = interaction.data["values"][0]
        modal_map = {
            "github":   GitHubModal,
            "notion":   NotionModal,
            "email":    EmailModal,
            "pastebin": PastebinModal,
        }
        if svc in modal_map:
            await interaction.response.send_modal(modal_map[svc]())

# ── View categoria Other ──
class ConnectOtherView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=120)
        self._uid = uid

    @discord.ui.button(label="Custom API", emoji="⚙️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_custom(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        modal = ApiKeyModal(service="custom_api", category="other", label="Custom API Key / Token", placeholder="your-api-key", hint="Generic credential slot for custom integrations")
        await interaction.response.send_modal(modal)

# ════════════════════════════════════════════════
#  CONNECT VIEW — AI
# ════════════════════════════════════════════════

# ── View categoria AI ──
class ConnectAIView(discord.ui.View):
    PROVIDERS = {
        "Pollinations": ("🌸", "Your sk_ key from enter.pollinations.ai", "Bearer sk_..."),
        "OpenAI":       ("🤖", "OpenAI API key (sk-...)",                  "sk-proj-..."),
        "Anthropic":    ("🟣", "Anthropic API key (sk-ant-...)",           "sk-ant-..."),
        "Gemini":       ("✨", "Google Gemini API key",                    "AIza..."),
        "Groq":         ("⚡", "Groq API key (gsk_...)",                   "gsk_..."),
        "Mistral":      ("🌊", "Mistral API key",                          "..."),
        "LLM7":         ("7️⃣", "LLM7 API key (if required)",              "..."),
        "OpenRouter":   ("🔀", "OpenRouter API key (sk-or-...)",           "sk-or-..."),
        "xAI":          ("🛸", "xAI (Grok) API key",                      "xai-..."),
        "Together":     ("🤝", "Together AI API key",                     "..."),
    }

    def __init__(self, uid: int):
        super().__init__(timeout=120)
        self._uid = uid
        # Mostra 5 provider alla volta con Select
        options = []
        for name, (emoji, label, placeholder) in self.PROVIDERS.items():
            connected = bool(get_user_conn(uid, "ai", name.lower()))
            options.append(discord.SelectOption(
                label=name,
                emoji=emoji,
                description=("✅ Connected" if connected else label[:50]),
                value=name
            ))
        select = discord.ui.Select(
            placeholder="Choose an AI provider to connect...",
            options=options[:25],
            min_values=1, max_values=1
        )
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True)
            return
        name = interaction.data["values"][0]
        _, label, placeholder = self.PROVIDERS[name]

        if name == "Pollinations":
            # Usa il Device Flow originale
            await interaction.response.defer(ephemeral=True, thinking=True)
            await _pollinations_device_flow(interaction)
            return

        modal = ApiKeyModal(
            service=name,
            category="ai",
            label=f"{name} API Key",
            placeholder=placeholder,
            hint=f"Key stored only in memory • use /disconnect-service to remove"
        )
        # Normalize service name to lowercase for storage
        modal._service = name.lower()
        await interaction.response.send_modal(modal)


# ── View principale /connect ──
class ConnectMenuView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=120)
        self._uid = uid

    def _connected_summary(self) -> str:
        conns = USER_CONNECTIONS.get(self._uid, {})
        lines = []
        for cat, services in conns.items():
            for svc in services:
                lines.append(f"✅ **{cat.capitalize()}** › {svc}")
        return "\n".join(lines) if lines else "*Nothing connected yet*"

    @discord.ui.button(label="🤖  AI Providers", style=discord.ButtonStyle.primary, row=0)
    async def btn_ai(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        embed = discord.Embed(
            title="🤖 Connect an AI Provider",
            description=(
                "Choose a provider to link your API key.\n"
                "Once connected, Nov will use that provider's models when you ask.\n\n"
                "**Pollinations** uses a secure Device Flow (no paste needed).\n"
                "All others use a direct API key."
            ),
            color=BOT_COLOR
        )
        await interaction.response.send_message(embed=embed, view=ConnectAIView(self._uid), ephemeral=True)

    @discord.ui.button(label="📱  Social", style=discord.ButtonStyle.primary, row=0)
    async def btn_social(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        embed = discord.Embed(
            title="📱 Connect a Social Service",
            description=(
                "Link external platforms so Nov can act on them from Discord.\n\n"
                "✈️ **Telegram** — send & read messages via your bot\n"
                "🐦 **Twitter / X** — post tweets & read timeline\n"
                "🤖 **Reddit** — post & read subreddits\n"
                "💼 **Slack** — send messages to channels\n"
                "🐘 **Mastodon** — post toots on any instance\n"
                "🔗 **Webhook** — POST to any URL\n"
                "🤖 **Discord Bot** — relay to another bot you own"
            ),
            color=0x229ED9
        )
        await interaction.response.send_message(embed=embed, view=ConnectSocialView(self._uid), ephemeral=True)

    @discord.ui.button(label="🛠️  Productivity", style=discord.ButtonStyle.primary, row=0)
    async def btn_productivity(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        embed = discord.Embed(
            title="🛠️ Connect a Productivity Service",
            description=(
                "Link dev tools and productivity apps.\n\n"
                "🐙 **GitHub** — create issues, read repos\n"
                "📓 **Notion** — create pages & query databases\n"
                "📧 **Email** — send emails via SMTP\n"
                "📋 **Pastebin** — create & share pastes"
            ),
            color=0xFEE75C
        )
        await interaction.response.send_message(embed=embed, view=ConnectProductivityView(self._uid), ephemeral=True)

    @discord.ui.button(label="🔧  Other", style=discord.ButtonStyle.secondary, row=1)
    async def btn_other(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        embed = discord.Embed(
            title="🔧 Other",
            description="**Custom API** — generic credential slot for any API key.",
            color=0x99AAB5
        )
        await interaction.response.send_message(embed=embed, view=ConnectOtherView(self._uid), ephemeral=True)

    @discord.ui.button(label="📋  View Connected", style=discord.ButtonStyle.secondary, row=1)
    async def btn_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        embed = discord.Embed(title="🔗 Your Connected Services", description=self._connected_summary(), color=BOT_COLOR)
        embed.set_footer(text="Use /disconnect-service to remove one")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def _pollinations_device_flow(interaction: discord.Interaction):
    """Esegue il Device Flow Pollinations e salva la sk_ key."""
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
            title="🌸 Connect your Pollinations account",
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
                    set_user_conn(interaction.user.id, "ai", "pollinations", sk)
                    masked = mask_key(sk)
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
                            title="✅ Pollinations connected!",
                            description=f"Account linked to Nov.\n`{masked}`\n\nYou can now use all commands!",
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


@bot.tree.command(name="connect", description="Connect AI providers, social services and more to Nov")
async def cmd_connect(interaction: discord.Interaction):
    uid   = interaction.user.id
    conns = USER_CONNECTIONS.get(uid, {})
    total = sum(len(v) for v in conns.values()) if conns else 0

    embed = discord.Embed(
        title="🔗 Nov — Connect Services",
        description=(
            "Link external services so Nov can use them directly from Discord.\n\n"
            "**🤖 AI Providers** — Pollinations, Claude, OpenAI, Gemini, Groq, Mistral, LLM7…\n"
            "**📱 Social** — Telegram, Twitter/X, Reddit, Slack, Mastodon, Webhooks\n"
            "**🛠️ Productivity** — GitHub, Notion, Email, Pastebin\n"
            "**🔧 Other** — custom API keys\n\n"
            f"Currently connected: **{total} service{'s' if total != 1 else ''}**"
        ),
        color=BOT_COLOR
    )
    embed.set_footer(text="Everything is stored in memory only • private to you")
    await interaction.response.send_message(embed=embed, view=ConnectMenuView(uid), ephemeral=True)

@bot.tree.command(name="disconnect", description="Remove your connected Pollinations account")
async def cmd_disconnect(interaction: discord.Interaction):
    removed = interaction.user.id in USER_KEYS
    if removed:
        del USER_KEYS[interaction.user.id]
        del_user_conn(interaction.user.id, "ai", "pollinations")
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Pollinations disconnected." if removed else "You didn't have a Pollinations account connected.",
            description="Use `/disconnect-service` to remove other services." if removed else None,
            color=0x57F287 if removed else 0xFEE75C
        ), ephemeral=True
    )

# ──────────────────────────────────────────────
#  /disconnect-service — rimuove un servizio collegato
# ──────────────────────────────────────────────
class DisconnectSelectView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=60)
        self._uid = uid
        conns = USER_CONNECTIONS.get(uid, {})
        options = []
        for cat, services in conns.items():
            for svc in services:
                options.append(discord.SelectOption(
                    label=f"{svc}",
                    description=f"Category: {cat}",
                    value=f"{cat}::{svc}"
                ))
        if not options:
            options = [discord.SelectOption(label="(nothing connected)", value="__none__")]
        sel = discord.ui.Select(placeholder="Choose service to remove...", options=options[:25])
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self._uid:
            await interaction.response.send_message("Not your menu!", ephemeral=True); return
        val = interaction.data["values"][0]
        if val == "__none__":
            await interaction.response.send_message("Nothing to remove.", ephemeral=True); return
        cat, svc = val.split("::", 1)
        del_user_conn(self._uid, cat, svc)
        await interaction.response.send_message(
            embed=discord.Embed(title=f"✅ {svc} removed", description=f"Category: {cat}", color=0x57F287),
            ephemeral=True
        )

@bot.tree.command(name="disconnect-service", description="Remove a connected service from Nov")
async def cmd_disconnect_service(interaction: discord.Interaction):
    uid   = interaction.user.id
    conns = USER_CONNECTIONS.get(uid, {})
    total = sum(len(v) for v in conns.values()) if conns else 0
    if total == 0:
        await interaction.response.send_message(
            embed=discord.Embed(title="ℹ️ No services connected", description="Use `/connect` to link services.", color=BOT_COLOR),
            ephemeral=True
        )
        return
    await interaction.response.send_message(
        embed=discord.Embed(title="🗑️ Remove a service", description="Choose which service to disconnect:", color=0xED4245),
        view=DisconnectSelectView(uid), ephemeral=True
    )

# ──────────────────────────────────────────────
#  /tg-send — invia messaggio Telegram tramite Nov
# ──────────────────────────────────────────────
@bot.tree.command(name="tg-send", description="Send a Telegram message via your connected bot")
@app_commands.describe(message="Message to send", chat_id="Chat ID or @username (optional, uses default if set)")
async def cmd_tg_send(interaction: discord.Interaction, message: str, chat_id: str = ""):
    uid     = interaction.user.id
    tg_data = get_user_conn(uid, "social", "telegram")
    if not tg_data:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Telegram not connected",
                description="Use `/connect` → 📱 Social → Telegram Bot first.",
                color=0xED4245
            ), ephemeral=True
        )
        return

    token  = tg_data["token"]
    target = chat_id.strip() or tg_data.get("chat_id") or ""
    if not target:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ No chat ID",
                description="Provide a `chat_id` or set a default one via `/connect` → Telegram.",
                color=0xED4245
            ), ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": target, "text": message, "parse_mode": "Markdown"}
            ) as resp:
                data = await resp.json()
        if not data.get("ok"):
            raise Exception(data.get("description", "Unknown error"))

        embed = discord.Embed(
            title="✈️ Telegram message sent!",
            description=f"**To:** `{target}`\n**Message:** {message[:300]}",
            color=0x229ED9
        )
        embed.set_footer(text=f"Via @{tg_data.get('username','?')}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(title="❌ Telegram error", description=f"`{e}`", color=0xED4245),
            ephemeral=True
        )

# ──────────────────────────────────────────────
#  /tg-read — leggi ultimi messaggi Telegram
# ──────────────────────────────────────────────
@bot.tree.command(name="tg-read", description="Read recent Telegram messages from your connected bot")
@app_commands.describe(limit="Number of recent messages to show (1–10)")
async def cmd_tg_read(interaction: discord.Interaction, limit: int = 5):
    uid     = interaction.user.id
    tg_data = get_user_conn(uid, "social", "telegram")
    if not tg_data:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Telegram not connected",
                description="Use `/connect` → 📱 Social → Telegram Bot first.",
                color=0xED4245
            ), ephemeral=True
        )
        return

    limit   = max(1, min(10, limit))
    token   = tg_data["token"]
    await interaction.response.defer(thinking=True, ephemeral=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"limit": 50, "timeout": 0}
            ) as resp:
                data = await resp.json()

        if not data.get("ok"):
            raise Exception(data.get("description", "Unknown error"))

        updates = data.get("result", [])
        messages = []
        for upd in reversed(updates):
            msg = upd.get("message") or upd.get("edited_message")
            if msg and msg.get("text"):
                sender = msg.get("from", {})
                name   = sender.get("first_name","?") + (f" @{sender['username']}" if sender.get("username") else "")
                chat   = msg.get("chat", {}).get("title") or msg["chat"].get("first_name","?")
                messages.append((name, chat, msg["text"]))
            if len(messages) >= limit:
                break

        if not messages:
            await interaction.followup.send(
                embed=discord.Embed(title="📭 No recent messages", description="No new messages in your bot's updates.", color=BOT_COLOR),
                ephemeral=True
            )
            return

        embed = discord.Embed(title=f"✈️ Telegram — Last {len(messages)} messages", color=0x229ED9)
        for name, chat, text in messages:
            embed.add_field(
                name=f"{name} in {chat}",
                value=text[:500],
                inline=False
            )
        embed.set_footer(text=f"Via @{tg_data.get('username','?')} • only messages sent to your bot")
        await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(title="❌ Telegram error", description=f"`{e}`", color=0xED4245),
            ephemeral=True
        )

# ──────────────────────────────────────────────
#  HELPER — controlla connessione servizio
# ──────────────────────────────────────────────
def _require_conn(uid: int, category: str, service: str, interaction_ref=None) -> tuple:
    """Ritorna (data, None) se connesso, (None, embed) se non connesso."""
    data = get_user_conn(uid, category, service)
    if not data:
        label = service.replace("_"," ").title()
        embed = discord.Embed(
            title=f"❌ {label} not connected",
            description=f"Use `/connect` → connect **{label}** first.",
            color=0xED4245
        )
        return None, embed
    return data, None

# ──────────────────────────────────────────────
#  TWITTER / X
# ──────────────────────────────────────────────
@bot.tree.command(name="tweet", description="Post a tweet via your connected Twitter / X account")
@app_commands.describe(text="Tweet text (max 280 chars)")
async def cmd_tweet(interaction: discord.Interaction, text: str):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "social", "twitter")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return

    await interaction.response.defer(thinking=True, ephemeral=True)
    # Twitter OAuth 1.0a — usa requests_oauthlib se disponibile, altrimenti aiohttp con header manuale
    import hmac, hashlib, base64, time as _time, uuid
    def _oauth1_header(method, url, params, creds):
        oauth_params = {
            "oauth_consumer_key":     creds["api_key"],
            "oauth_nonce":            uuid.uuid4().hex,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp":        str(int(_time.time())),
            "oauth_token":            creds["acc_token"],
            "oauth_version":          "1.0",
        }
        all_params = {**params, **oauth_params}
        param_str  = "&".join(f"{urllib.parse.quote(k,'')  }={urllib.parse.quote(str(v),'')}" for k, v in sorted(all_params.items()))
        base_str   = "&".join([method.upper(), urllib.parse.quote(url,""), urllib.parse.quote(param_str,"")])
        sign_key   = f"{urllib.parse.quote(creds['api_secret'],'')}&{urllib.parse.quote(creds['acc_secret'],'')}"
        sig        = base64.b64encode(hmac.new(sign_key.encode(), base_str.encode(), hashlib.sha1).digest()).decode()
        oauth_params["oauth_signature"] = sig
        header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(str(v),"")}"' for k, v in sorted(oauth_params.items()))
        return header

    try:
        url     = "https://api.twitter.com/2/tweets"
        payload = {"text": text[:280]}
        header  = _oauth1_header("POST", url, {}, data)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Authorization": header, "Content-Type": "application/json"}) as resp:
                result = await resp.json()
        if "data" not in result:
            raise Exception(result.get("detail") or result.get("errors", [{}])[0].get("message","Unknown error"))
        tweet_id = result["data"]["id"]
        await interaction.followup.send(embed=discord.Embed(
            title="🐦 Tweet posted!",
            description=f"{text[:280]}\n\n[View tweet](https://twitter.com/i/web/status/{tweet_id})",
            color=0x1DA1F2
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Twitter error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  REDDIT
# ──────────────────────────────────────────────
async def _reddit_token(data: dict) -> str:
    """Ottiene un access token Reddit tramite password grant."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=aiohttp.BasicAuth(data["client_id"], data["client_secret"]),
            data={"grant_type": "password", "username": data["username"], "password": data["password"]},
            headers={"User-Agent": "NovBot/1.0"}
        ) as resp:
            r = await resp.json()
    if "access_token" not in r:
        raise Exception(r.get("message", "Reddit auth failed"))
    return r["access_token"]

@bot.tree.command(name="reddit-post", description="Submit a post to a subreddit via your connected Reddit account")
@app_commands.describe(subreddit="Subreddit name (no r/ prefix)", title="Post title", text="Post body text")
async def cmd_reddit_post(interaction: discord.Interaction, subreddit: str, title: str, text: str = ""):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "social", "reddit")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        token = await _reddit_token(data)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth.reddit.com/api/submit",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "NovBot/1.0"},
                data={"sr": subreddit, "kind": "self", "title": title, "text": text, "api_type": "json"}
            ) as resp:
                result = await resp.json()
        errors = result.get("json", {}).get("errors", [])
        if errors:
            raise Exception(str(errors[0]))
        post_url = result.get("json", {}).get("data", {}).get("url", "")
        await interaction.followup.send(embed=discord.Embed(
            title="🤖 Reddit post submitted!",
            description=f"**r/{subreddit}** — {title}\n{post_url}",
            color=0xFF4500
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Reddit error", description=f"`{e}`", color=0xED4245), ephemeral=True)

@bot.tree.command(name="reddit-read", description="Read hot posts from a subreddit")
@app_commands.describe(subreddit="Subreddit name (no r/ prefix)", limit="Number of posts (1–10)")
async def cmd_reddit_read(interaction: discord.Interaction, subreddit: str, limit: int = 5):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "social", "reddit")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    limit = max(1, min(10, limit))
    try:
        token = await _reddit_token(data)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://oauth.reddit.com/r/{subreddit}/hot",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "NovBot/1.0"},
                params={"limit": limit}
            ) as resp:
                result = await resp.json()
        posts = result.get("data", {}).get("children", [])
        if not posts:
            await interaction.followup.send(embed=discord.Embed(title="📭 No posts found", color=BOT_COLOR), ephemeral=True); return
        embed = discord.Embed(title=f"🤖 r/{subreddit} — Hot Posts", color=0xFF4500)
        for p in posts[:limit]:
            d = p["data"]
            embed.add_field(name=f"⬆️ {d['score']}  {d['title'][:80]}", value=f"by u/{d['author']} • [link](https://reddit.com{d['permalink']})", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Reddit error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  SLACK
# ──────────────────────────────────────────────
@bot.tree.command(name="slack-send", description="Send a message to Slack via your connected bot")
@app_commands.describe(message="Message to send", channel="Channel ID or name (optional, uses default)")
async def cmd_slack_send(interaction: discord.Interaction, message: str, channel: str = ""):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "social", "slack")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    target = channel.strip() or data.get("channel") or ""
    if not target:
        await interaction.response.send_message(embed=discord.Embed(title="❌ No channel", description="Provide a `channel` or set a default via `/connect` → Slack.", color=0xED4245), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {data['token']}", "Content-Type": "application/json"},
                json={"channel": target, "text": message}
            ) as resp:
                result = await resp.json()
        if not result.get("ok"):
            raise Exception(result.get("error", "unknown"))
        await interaction.followup.send(embed=discord.Embed(title="💼 Slack message sent!", description=f"**To:** `{target}`\n{message[:300]}", color=0x4A154B), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Slack error", description=f"`{e}`", color=0xED4245), ephemeral=True)

@bot.tree.command(name="slack-read", description="Read recent messages from a Slack channel")
@app_commands.describe(channel="Channel ID (e.g. C012AB3CD)", limit="Number of messages (1–10)")
async def cmd_slack_read(interaction: discord.Interaction, channel: str = "", limit: int = 5):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "social", "slack")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    target = channel.strip() or data.get("channel") or ""
    if not target:
        await interaction.response.send_message(embed=discord.Embed(title="❌ No channel", description="Provide a `channel` ID.", color=0xED4245), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    limit = max(1, min(10, limit))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://slack.com/api/conversations.history",
                headers={"Authorization": f"Bearer {data['token']}"},
                params={"channel": target, "limit": limit}
            ) as resp:
                result = await resp.json()
        if not result.get("ok"):
            raise Exception(result.get("error", "unknown"))
        msgs = result.get("messages", [])
        if not msgs:
            await interaction.followup.send(embed=discord.Embed(title="📭 No messages", color=BOT_COLOR), ephemeral=True); return
        embed = discord.Embed(title=f"💼 Slack — #{target}", color=0x4A154B)
        for m in msgs[:limit]:
            embed.add_field(name=f"<t:{int(float(m.get('ts',0)))}:R>", value=(m.get("text","") or "*attachment*")[:400], inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Slack error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  MASTODON
# ──────────────────────────────────────────────
@bot.tree.command(name="toot", description="Post a toot on Mastodon via your connected account")
@app_commands.describe(text="Toot content (max 500 chars)", visibility="Who can see it")
@app_commands.choices(visibility=[
    app_commands.Choice(name="🌐 Public",   value="public"),
    app_commands.Choice(name="🔓 Unlisted", value="unlisted"),
    app_commands.Choice(name="🔒 Followers only", value="private"),
])
async def cmd_toot(interaction: discord.Interaction, text: str, visibility: str = "public"):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "social", "mastodon")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{data['base_url']}/api/v1/statuses",
                headers={"Authorization": f"Bearer {data['token']}"},
                json={"status": text[:500], "visibility": visibility}
            ) as resp:
                result = await resp.json()
        if "error" in result:
            raise Exception(result["error"])
        toot_url = result.get("url","")
        await interaction.followup.send(embed=discord.Embed(
            title="🐘 Toot posted!",
            description=f"{text[:500]}\n\n[View toot]({toot_url})",
            color=0x6364FF
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Mastodon error", description=f"`{e}`", color=0xED4245), ephemeral=True)

@bot.tree.command(name="mastodon-read", description="Read your Mastodon home timeline")
@app_commands.describe(limit="Number of posts to show (1–10)")
async def cmd_mastodon_read(interaction: discord.Interaction, limit: int = 5):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "social", "mastodon")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    limit = max(1, min(10, limit))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{data['base_url']}/api/v1/timelines/home",
                headers={"Authorization": f"Bearer {data['token']}"},
                params={"limit": limit}
            ) as resp:
                posts = await resp.json()
        if not posts:
            await interaction.followup.send(embed=discord.Embed(title="📭 No posts", color=BOT_COLOR), ephemeral=True); return
        embed = discord.Embed(title="🐘 Mastodon — Home Timeline", color=0x6364FF)
        for p in posts[:limit]:
            acct    = p.get("account",{}).get("acct","?")
            content = p.get("content","").replace("<p>","").replace("</p>","\n").replace("<br />","\n")
            # Strip other HTML tags
            import re; content = re.sub(r"<[^>]+>","",content).strip()
            embed.add_field(name=f"@{acct}", value=content[:400] or "*no text*", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Mastodon error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  WEBHOOK
# ──────────────────────────────────────────────
@bot.tree.command(name="wh-send", description="Fire a webhook with a custom payload")
@app_commands.describe(label="Webhook label (set when connecting)", payload="JSON payload or plain text message")
async def cmd_wh_send(interaction: discord.Interaction, label: str, payload: str):
    uid = interaction.user.id
    url = get_user_conn(uid, "social", f"webhook_{label}")
    if not url:
        await interaction.response.send_message(embed=discord.Embed(title="❌ Webhook not found", description=f"No webhook with label `{label}`. Use `/connect` → Social → Webhook.", color=0xED4245), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        try:
            body = json.loads(payload)
        except Exception:
            body = {"content": payload}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body) as resp:
                status = resp.status
        await interaction.followup.send(embed=discord.Embed(title=f"🔗 Webhook fired!", description=f"**Label:** `{label}`\n**Status:** `{status}`", color=0x57F287), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Webhook error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  GITHUB
# ──────────────────────────────────────────────
@bot.tree.command(name="gh-issue", description="Create a GitHub issue on a repo")
@app_commands.describe(title="Issue title", body="Issue body", repo="owner/repo (optional, uses default)")
async def cmd_gh_issue(interaction: discord.Interaction, title: str, body: str = "", repo: str = ""):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "productivity", "github")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    target = repo.strip() or data.get("repo") or ""
    if not target:
        await interaction.response.send_message(embed=discord.Embed(title="❌ No repo", description="Provide a `repo` (owner/repo) or set a default via `/connect` → GitHub.", color=0xED4245), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.github.com/repos/{target}/issues",
                headers={"Authorization": f"token {data['token']}", "Accept": "application/vnd.github+json"},
                json={"title": title, "body": body}
            ) as resp:
                result = await resp.json()
        if "number" not in result:
            raise Exception(result.get("message","Unknown error"))
        await interaction.followup.send(embed=discord.Embed(
            title=f"🐙 Issue #{result['number']} created!",
            description=f"**{title}**\n[View on GitHub]({result['html_url']})",
            color=0x24292E
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ GitHub error", description=f"`{e}`", color=0xED4245), ephemeral=True)

@bot.tree.command(name="gh-read", description="Read recent issues or commits from a GitHub repo")
@app_commands.describe(repo="owner/repo (optional, uses default)", what="What to read")
@app_commands.choices(what=[
    app_commands.Choice(name="🐛 Open Issues", value="issues"),
    app_commands.Choice(name="📝 Recent Commits", value="commits"),
    app_commands.Choice(name="📦 Repo Info", value="info"),
])
async def cmd_gh_read(interaction: discord.Interaction, repo: str = "", what: str = "issues"):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "productivity", "github")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    target = repo.strip() or data.get("repo") or ""
    if not target:
        await interaction.response.send_message(embed=discord.Embed(title="❌ No repo", description="Provide a `repo` or set a default via `/connect` → GitHub.", color=0xED4245), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        headers = {"Authorization": f"token {data['token']}", "Accept": "application/vnd.github+json"}
        async with aiohttp.ClientSession() as session:
            if what == "issues":
                async with session.get(f"https://api.github.com/repos/{target}/issues", headers=headers, params={"state":"open","per_page":8}) as resp:
                    items = await resp.json()
                embed = discord.Embed(title=f"🐛 {target} — Open Issues", color=0x24292E)
                for i in (items if isinstance(items,list) else [])[:8]:
                    embed.add_field(name=f"#{i['number']} {i['title'][:60]}", value=f"by {i['user']['login']} • [link]({i['html_url']})", inline=False)
            elif what == "commits":
                async with session.get(f"https://api.github.com/repos/{target}/commits", headers=headers, params={"per_page":8}) as resp:
                    items = await resp.json()
                embed = discord.Embed(title=f"📝 {target} — Recent Commits", color=0x24292E)
                for c in (items if isinstance(items,list) else [])[:8]:
                    msg = c["commit"]["message"].split("\n")[0][:70]
                    sha = c["sha"][:7]
                    embed.add_field(name=f"`{sha}` {msg}", value=f"by {c['commit']['author']['name']}", inline=False)
            else:
                async with session.get(f"https://api.github.com/repos/{target}", headers=headers) as resp:
                    r = await resp.json()
                embed = discord.Embed(title=f"📦 {target}", description=r.get("description",""), color=0x24292E)
                embed.add_field(name="⭐ Stars",  value=r.get("stargazers_count",0), inline=True)
                embed.add_field(name="🍴 Forks",  value=r.get("forks_count",0),      inline=True)
                embed.add_field(name="🐛 Issues", value=r.get("open_issues_count",0),inline=True)
                embed.add_field(name="🌿 Branch", value=r.get("default_branch","?"), inline=True)
                embed.add_field(name="📄 License",value=(r.get("license") or {}).get("spdx_id","None"), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ GitHub error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  NOTION
# ──────────────────────────────────────────────
@bot.tree.command(name="notion-add", description="Add a page to your Notion database")
@app_commands.describe(title="Page title", content="Page content (optional)", db_id="Database ID (optional, uses default)")
async def cmd_notion_add(interaction: discord.Interaction, title: str, content: str = "", db_id: str = ""):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "productivity", "notion")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    target = db_id.strip().replace("-","")[:32] or data.get("db_id") or ""
    if not target:
        await interaction.response.send_message(embed=discord.Embed(title="❌ No database ID", description="Provide a `db_id` or set a default via `/connect` → Notion.", color=0xED4245), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        payload = {
            "parent": {"database_id": target},
            "properties": {"title" if True else "Name": {"title": [{"text": {"content": title}}]}},
        }
        if content:
            payload["children"] = [{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":content[:2000]}}]}}]
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.notion.com/v1/pages",
                headers={"Authorization": f"Bearer {data['token']}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
                json=payload
            ) as resp:
                result = await resp.json()
        if result.get("object") == "error":
            raise Exception(result.get("message","Unknown error"))
        page_url = result.get("url","")
        await interaction.followup.send(embed=discord.Embed(
            title="📓 Notion page created!",
            description=f"**{title}**\n[Open in Notion]({page_url})",
            color=0x000000
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Notion error", description=f"`{e}`", color=0xED4245), ephemeral=True)

@bot.tree.command(name="notion-read", description="Read entries from your Notion database")
@app_commands.describe(db_id="Database ID (optional, uses default)", limit="Number of entries (1–10)")
async def cmd_notion_read(interaction: discord.Interaction, db_id: str = "", limit: int = 5):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "productivity", "notion")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    target = db_id.strip().replace("-","")[:32] or data.get("db_id") or ""
    if not target:
        await interaction.response.send_message(embed=discord.Embed(title="❌ No database ID", color=0xED4245), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    limit = max(1, min(10, limit))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.notion.com/v1/databases/{target}/query",
                headers={"Authorization": f"Bearer {data['token']}", "Notion-Version": "2022-06-28"},
                json={"page_size": limit}
            ) as resp:
                result = await resp.json()
        if result.get("object") == "error":
            raise Exception(result.get("message","Unknown error"))
        pages = result.get("results", [])
        if not pages:
            await interaction.followup.send(embed=discord.Embed(title="📭 No entries", color=BOT_COLOR), ephemeral=True); return
        embed = discord.Embed(title="📓 Notion Database", color=0x000000)
        for p in pages[:limit]:
            props = p.get("properties", {})
            title_prop = next((v for v in props.values() if v.get("type") == "title"), {})
            title_text = (title_prop.get("title") or [{}])[0].get("plain_text","Untitled") if title_prop else "Untitled"
            embed.add_field(name=title_text[:80], value=f"[Open]({p.get('url','')})", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Notion error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  EMAIL
# ──────────────────────────────────────────────
@bot.tree.command(name="email-send", description="Send an email via your connected SMTP account")
@app_commands.describe(to="Recipient email", subject="Subject", body="Email body")
async def cmd_email_send(interaction: discord.Interaction, to: str, subject: str, body: str):
    uid  = interaction.user.id
    data, err = _require_conn(uid, "productivity", "email")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg          = MIMEText(body)
        msg["Subject"] = subject
        msg["From"]  = data["username"]
        msg["To"]    = to
        loop = asyncio.get_event_loop()
        def _send():
            with smtplib.SMTP(data["host"], data.get("port", 587)) as smtp:
                smtp.starttls()
                smtp.login(data["username"], data["password"])
                smtp.send_message(msg)
        await loop.run_in_executor(None, _send)
        await interaction.followup.send(embed=discord.Embed(
            title="📧 Email sent!",
            description=f"**To:** {to}\n**Subject:** {subject}",
            color=0xEA4335
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Email error", description=f"`{e}`", color=0xED4245), ephemeral=True)

# ──────────────────────────────────────────────
#  PASTEBIN
# ──────────────────────────────────────────────
@bot.tree.command(name="paste", description="Create a Pastebin paste and get the URL")
@app_commands.describe(content="Content to paste", title="Paste title (optional)", visibility="Visibility")
@app_commands.choices(visibility=[
    app_commands.Choice(name="🌐 Public",   value="0"),
    app_commands.Choice(name="🔓 Unlisted", value="1"),
    app_commands.Choice(name="🔒 Private",  value="2"),
])
async def cmd_paste(interaction: discord.Interaction, content: str, title: str = "Nov Paste", visibility: str = "1"):
    uid  = interaction.user.id
    api_key, err = _require_conn(uid, "productivity", "pastebin")
    if err:
        await interaction.response.send_message(embed=err, ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://pastebin.com/api/api_post.php",
                data={"api_dev_key": api_key, "api_option": "paste", "api_paste_code": content, "api_paste_name": title, "api_paste_private": visibility}
            ) as resp:
                result = await resp.text()
        if not result.startswith("https://"):
            raise Exception(result)
        await interaction.followup.send(embed=discord.Embed(
            title="📋 Paste created!",
            description=f"**{title}**\n{result}",
            color=0x02A6C4
        ), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Pastebin error", description=f"`{e}`", color=0xED4245), ephemeral=True)

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
        value=(
            "`/connect` · Link AI providers, Telegram, GitHub & more\n"
            "`/disconnect` · Remove Pollinations account\n"
            "`/disconnect-service` · Remove any other connected service\n"
            "`/info` · View your settings\n"
            "`/profile` · Tier, GitHub & Pollen balance"
        ),
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
    embed.add_field(name="📱 Social (via /connect)",
        value=(
            "`/tg-send [message]` · Send a Telegram message\n"
            "`/tg-read` · Read recent Telegram messages"
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
            "`/event [title] [date]` · AI-generated event announcement 📅"
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
