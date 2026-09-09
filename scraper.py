import sys
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import json
import subprocess
import pytz
from bs4 import BeautifulSoup

# Zones horàries
TZ_NY = pytz.timezone("America/New_York")
TZ_CAT = pytz.timezone("Europe/Madrid")

# Llista de canals a processar
CHANNELS = {
    "STZ1": "STARZ",
    "STZ3": "STARZ Edge",
    "STZ5": "STARZ InBlack",
    "STZ6": "STARZ Kids & Family",
    "STZ7": "STARZ Cinema",
    "STZ8": "STARZ Comedy",
    "STZ9": "STARZ Encore"
}

def parse_iso_to_cat(iso_str):
    """Converteix cadenes ISO/UTC a l'horari de Catalunya (%Y%m%d%H%M%S +0200)."""
    try:
        if not iso_str:
            return None
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_cat = dt.astimezone(TZ_CAT)
        return dt_cat.strftime("%Y%m%d%H%M%S %z")
    except Exception:
        return None

def fetch_html_for_channel(channel_code, date_path):
    """Descarrega l'HTML del canal especificat mitjançant curl."""
    url = f"https://www.starz.com/us/en/schedule/{channel_code}/{date_path}"
    output_file = f"starz_{channel_code}.html"
    print(f"[{channel_code}] Descarregant des de {url}...")
    
    cmd = [
        "curl", "-s", "-L",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "-H", "Accept-Language: en-US,en;q=0.9",
        url,
        "-o", output_file
    ]
    try:
        subprocess.run(cmd, check=True)
        return output_file
    except Exception as e:
        print(f"[{channel_code}] Error en descarregar amb curl: {e}", file=sys.stderr)
        return None

def extract_programs_from_html(file_path):
    """Extreu els programes del bloc __NEXT_DATA__ d'un arxiu HTML descarregat."""
    if not file_path or not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    next_data_script = soup.find("script", id="__NEXT_DATA__")

    if not next_data_script or not next_data_script.string:
        return []

    try:
        data = json.loads(next_data_script.string)
    except Exception:
        return []

    programs = []

    def extract_schedules(obj):
        if isinstance(obj, dict):
            title = obj.get("title") or obj.get("titleName") or obj.get("name")
            start_iso = obj.get("startTime") or obj.get("airStart") or obj.get("start")
            end_iso = obj.get("endTime") or obj.get("airEnd") or obj.get("end")
            desc = obj.get("description") or obj.get("synopsis") or obj.get("logLine", "")
            rating = obj.get("rating") or obj.get("contentRating", "")

            if title and start_iso and isinstance(start_iso, str) and ("T" in start_iso or "Z" in start_iso):
                if not any(p["title"] == title and p["start_iso"] == start_iso for p in programs):
                    programs.append({
                        "title": title,
                        "start_iso": start_iso,
                        "end_iso": end_iso,
                        "desc": desc,
                        "rating": rating
                    })

            for value in obj.values():
                extract_schedules(value)

        elif isinstance(obj, list):
            for item in obj:
                extract_schedules(item)

    extract_schedules(data)
    return programs

def main():
    now_ny = datetime.datetime.now(TZ_NY)
    date_path = now_ny.strftime("%Y/%m/%d")

    tv = ET.Element("tv", {"generator-info-name": "STARZ-EPG-MultiChannel"})

    # 1. Crear la definició de tots els canals a l'XML
    for code, name in CHANNELS.items():
        channel_elem = ET.SubElement(tv, "channel", id=f"starz-{code.lower()}")
        display_name = ET.SubElement(channel_elem, "display-name")
        display_name.text = f"{name} ({code})"

    total_programs = 0

    # 2. Descarregar i processar la programació de cada canal
    for code, name in CHANNELS.items():
        file_path = fetch_html_for_channel(code, date_path)
        programs = extract_programs_from_html(file_path)
        
        channel_xml_id = f"starz-{code.lower()}"
        count = 0

        for item in programs:
            start_cat = parse_iso_to_cat(item.get("start_iso"))
            stop_cat = parse_iso_to_cat(item.get("end_iso")) or start_cat

            if not start_cat:
                continue

            prog = ET.SubElement(tv, "programme", {
                "start": start_cat,
                "stop": stop_cat,
                "channel": channel_xml_id
            })
            
            title = ET.SubElement(prog, "title", lang="en")
            title.text = item["title"]
            
            if item.get("desc"):
                desc = ET.SubElement(prog, "desc", lang="en")
                desc.text = item["desc"]
                
            if item.get("rating"):
                rating = ET.SubElement(prog, "rating")
                val = ET.SubElement(rating, "value")
                val.text = str(item["rating"])
                
            count += 1

        print(f"[{code}] Processats {count} programes.")
        total_programs += count

        # Esborrar l'arxiu HTML temporal per no acumular fitxers inservibles
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    # 3. Guardar el XML final unificat
    rough_string = ET.tostring(tv, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    xml_content = reparsed.toprettyxml(indent="  ")

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print(f"\nProcés finalitzat amb èxit! Total: {total_programs} programes generats a epg.xml.")

if __name__ == "__main__":
    main()
