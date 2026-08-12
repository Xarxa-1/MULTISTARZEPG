import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


URL_PAGINA = (
    "https://www.skylinewebcams.com/es/webcam/espana/"
    "cataluna/tarragona/tarragona-balco-del-mediterrani.html"
)

FITXER_M3U = Path("tarragona.m3u")


async def buscar_stream():

    streams = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        def detectar(request):

            url = request.url

            if ".m3u8" in url.lower():

                if url not in streams:
                    streams.append(url)

        page.on("request", detectar)

        print("Obrint SkylineWebcams...")

        try:

            await page.goto(
                URL_PAGINA,
                wait_until="domcontentloaded",
                timeout=60000
            )

        except Exception as e:

            print("Error carregant la pàgina:")
            print(e)

        # Temps perquè carregui el reproductor
        await page.wait_for_timeout(20000)

        await browser.close()

    if not streams:
        print("No s'ha detectat cap M3U8.")
        return None

    print("Streams detectats:")

    for stream in streams:
        print(stream)

    return streams[0]


async def main():

    stream = await buscar_stream()

    if not stream:
        return

    contingut = (
        "#EXTM3U\n"
        '#EXTINF:-1 tvg-name="Tarragona - Balcó del Mediterrani",'
        "Tarragona - Balcó del Mediterrani\n"
        f"{stream}\n"
    )

    FITXER_M3U.write_text(
        contingut,
        encoding="utf-8"
    )

    print()
    print("Fitxer M3U actualitzat:")
    print(FITXER_M3U)


if __name__ == "__main__":
    asyncio.run(main())
