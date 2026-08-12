import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


URL_PAGINA = (
    "https://www.skylinewebcams.com/es/webcam/espana/"
    "cataluna/tarragona/tarragona-balco-del-mediterrani.html"
)

FITXER_M3U = Path("tarragona.m3u")


async def main():

    streams = []

    async with async_playwright() as p:

        print("Iniciant Chromium...")

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        # ------------------------------------------------
        # CAPTURA DE PETICIONS
        # ------------------------------------------------

        def request_handler(request):

            url = request.url.lower()

            extensions = [
                ".m3u8",
                ".mp4",
                ".ts",
                ".m3u",
                "manifest",
                "playlist",
                "stream"
            ]

            if any(x in url for x in extensions):

                print()
                print("======================================")
                print("PETICIÓ DE STREAMING")
                print("======================================")
                print(request.url)
                print()

                if request.url not in streams:
                    streams.append(request.url)

        page.on(
            "request",
            request_handler
        )

        # ------------------------------------------------
        # CARREGAR LA WEB
        # ------------------------------------------------

        print("Carregant SkylineWebcams...")

        try:

            await page.goto(
                URL_PAGINA,
                wait_until="domcontentloaded",
                timeout=60000
            )

        except Exception as e:

            print("ERROR carregant la pàgina:")
            print(e)

        # ------------------------------------------------
        # ESPERAR EL REPRODUCTOR
        # ------------------------------------------------

        print()
        print("Esperant el reproductor...")

        await page.wait_for_timeout(30000)

        # ------------------------------------------------
        # RESULTATS
        # ------------------------------------------------

        print()
        print("======================================")
        print("RESULTAT")
        print("======================================")

        if not streams:

            print("NO S'HA TROBAT CAP STREAMING.")

        else:

            print("Streams trobats:")

            for i, stream in enumerate(streams):

                print()
                print(f"[{i}] {stream}")

        # ------------------------------------------------
        # CREAR M3U NOMÉS SI HI HA STREAM
        # ------------------------------------------------

        if streams:

            stream = streams[0]

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
            print("M3U CREAT CORRECTAMENT:")
            print(contingut)

        else:

            print()
            print(
                "El fitxer M3U NO s'ha modificat "
                "perquè no s'ha detectat cap stream."
            )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
