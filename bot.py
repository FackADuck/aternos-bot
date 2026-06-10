import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ATERNOS_COOKIE = os.getenv("ATERNOS_COOKIE")
ATERNOS_USERNAME = os.getenv("ATERNOS_USERNAME")
ATERNOS_PASSWORD = os.getenv("ATERNOS_PASSWORD")
ATERNOS_SERVER_NAME = os.getenv("ATERNOS_SERVER_NAME")

channel_id_raw = os.getenv("STATUS_CHANNEL_ID")
if not channel_id_raw:
    print("FOUT: STATUS_CHANNEL_ID staat niet in je .env bestand!")
    exit(1)
STATUS_CHANNEL_ID = int(channel_id_raw.strip())

# Vaste server ID — wordt ingevuld bij opstarten
SERVER_ID = "TSsy3G64PIco0RYc"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
status_message = None
is_starting = False  # Handmatige "aan het starten" vlag


def parse_cookies(cookie_str):
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            cookies.append({"name": name.strip(), "value": value.strip(), "domain": ".aternos.org", "path": "/"})
    return cookies


async def sluit_popups(page):
    for tekst in ["Close", "Consent", "Do not consent", "Okay"]:
        try:
            await page.locator(f"text={tekst}").first.click(timeout=1000, force=True)
            await page.wait_for_timeout(400)
        except:
            pass


async def get_server_status():
    """Haal status op via directe serverpagina."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            await context.add_cookies(parse_cookies(ATERNOS_COOKIE))
            page = await context.new_page()

            await page.goto(f"https://aternos.org/server/#{SERVER_ID}", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(4000)

            if "go" in page.url or "login" in page.url.lower():
                await browser.close()
                return "offline"

            # Wacht tot status element zichtbaar is
            try:
                await page.wait_for_selector(".statuslabel-label", timeout=8000)
                status_el = page.locator(".statuslabel-label").first
                status = (await status_el.inner_text()).strip().lower()
            except:
                status = "offline"

            await browser.close()
            return status

    except Exception as e:
        print(f"Fout bij ophalen status: {e}")
        return "offline"


async def start_server():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            await context.add_cookies(parse_cookies(ATERNOS_COOKIE))
            page = await context.new_page()

            print("Naar serverpagina...")
            await page.goto(f"https://aternos.org/server/#{SERVER_ID}", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)

            if "go" in page.url or "login" in page.url.lower():
                print("Niet ingelogd, probeer login...")
                await page.goto("https://aternos.org/go/", wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                await page.fill("input[type='text']", ATERNOS_USERNAME)
                await page.fill("input[type='password']", ATERNOS_PASSWORD)
                await page.wait_for_timeout(1000)
                await page.locator("button", has_text="Inloggen").first.click()
                await page.wait_for_timeout(5000)
                await page.goto(f"https://aternos.org/server/#{SERVER_ID}", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)

            await sluit_popups(page)
            print(f"URL: {page.url}")

            start_geklikt = False
            for selector in ["#start", ".start-button", "[data-id='start']"]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click(force=True)
                        start_geklikt = True
                        print(f"Start geklikt via {selector}")
                        break
                except:
                    continue

            await page.wait_for_timeout(2000)
            await browser.close()
            return start_geklikt

    except Exception as e:
        import traceback
        print(f"Fout bij starten: {e}")
        traceback.print_exc()
        return False


def get_embed(status: str, starting: bool):
    if starting or any(x in status for x in ["starting", "loading", "preparing", "waiting"]):
        color = discord.Color.orange()
        emoji = "🟠"
        status_text = "Aan het starten..."
        show_start = False
    elif "online" in status:
        color = discord.Color.green()
        emoji = "🟢"
        status_text = "Online"
        show_start = False
    else:
        color = discord.Color.red()
        emoji = "🔴"
        status_text = "Offline"
        show_start = True

    embed = discord.Embed(title="🎮 Minecraft Server Status", color=color)
    embed.add_field(name="Status", value=f"{emoji} {status_text}", inline=True)
    embed.add_field(name="Adres", value=f"`{ATERNOS_SERVER_NAME}`", inline=True)
    embed.set_footer(text="Wordt elke 15 seconden bijgewerkt")
    return embed, show_start


class StartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="▶ Start Server", style=discord.ButtonStyle.success, custom_id="persistent_start")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global is_starting
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("⏳ Bezig met starten, even geduld...", ephemeral=True)

        # Zet vlag aan zodat embed meteen oranje wordt
        is_starting = True
        await update_status()

        success = await start_server()

        if success:
            await interaction.followup.send("✅ Startcommando verstuurd! De server start zo op.", ephemeral=True)
        else:
            is_starting = False
            await interaction.followup.send("❌ Kon de server niet starten. Probeer het opnieuw.", ephemeral=True)


@tasks.loop(seconds=15)
async def update_status():
    global status_message, is_starting
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if channel is None:
        return

    status = await get_server_status()

    # Reset is_starting als server echt online of offline is
    if "online" in status:
        is_starting = False
    elif "offline" in status and not is_starting:
        is_starting = False

    embed, show_start = get_embed(status, is_starting)
    view = StartView() if show_start else discord.ui.View(timeout=None)

    try:
        if status_message is None:
            await channel.purge(limit=10)
            status_message = await channel.send(embed=embed, view=view)
        else:
            await status_message.edit(embed=embed, view=view)
    except discord.NotFound:
        status_message = None
        await channel.purge(limit=10)
        status_message = await channel.send(embed=embed, view=view)
    except Exception as e:
        print(f"Fout bij updaten bericht: {e}")


@bot.event
async def on_ready():
    print(f"Bot ingelogd als {bot.user}")
    print(f"Server ID: {SERVER_ID}")
    bot.add_view(StartView())
    update_status.start()


bot.run(DISCORD_TOKEN)
