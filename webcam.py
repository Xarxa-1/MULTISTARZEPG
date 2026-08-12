import asyncio
from playwright.async_api import async_playwright

URL = "https://www.skylinewebcams.com/es/webcam/espana/cataluna/tarragona/tarragona-balco-del-mediterrani.html"


async def main():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        print("====================================")
        print("CARREGANT SKYLINEWEBCAMS")
        print("====================================")

        def request(request):

            url = request.url

            # Mostrar peticions relacionades amb vídeo/stream
            paraules = [
                ".m3u8",
                ".mpd",
                ".mp4",
                ".ts",
                "manifest",
                "playlist",
                "stream",
                "video"
            ]

            if any(x in url.lower() for x in paraules):

                print()
                print(">>> POSSIBLE STREAM:")
                print(url)

        page.on("request", request)

        try:

            await page.goto(
                URL,
                wait_until="networkidle",
                timeout=90000
            )

        except Exception as e:

            print("Avís de càrrega:")
            print(e)

        print()
        print("Esperant 60 segons...")

        await page.wait_for_timeout(60000)

        print()
        print("Títol:")
        print(await page.title())

        print()
        print("URL actual:")
        print(page.url)

        print()
        print("====================================")
        print("FINAL")
        print("====================================")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
