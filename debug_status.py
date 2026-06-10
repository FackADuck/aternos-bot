from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

ATERNOS_COOKIE = os.getenv("ATERNOS_COOKIE")
ATERNOS_SERVER_NAME = os.getenv("ATERNOS_SERVER_NAME")

def parse_cookies(cookie_str):
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            cookies.append({"name": name.strip(), "value": value.strip(), "domain": ".aternos.org", "path": "/"})
    return cookies

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    context.add_cookies(parse_cookies(ATERNOS_COOKIE))
    page = context.new_page()

    page.goto("https://aternos.org/servers/", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    page.screenshot(path="debug_status.png")

    servers = page.locator(".server-body").all()
    print(f"{len(servers)} servers gevonden")

    for i, server in enumerate(servers):
        print(f"\n--- Server {i+1} ---")
        print(f"Volledige tekst: {repr(server.inner_text()[:200])}")
        print(f"data-id: {server.get_attribute('data-id')}")
        
        # Print alle child elementen met hun klasse
        children = server.locator("[class]").all()
        for child in children:
            cls = child.get_attribute("class")
            txt = child.inner_text().strip()[:50]
            if txt:
                print(f"  class='{cls}' tekst='{txt}'")

    input("Druk Enter om te sluiten...")
    browser.close()
