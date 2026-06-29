import streamlit as st
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(BASE_DIR, "fonts", "Roboto-Regular.ttf")

# ── Konfiguracja ────────────────────────────────────────────────────────────

PRACOWNICY = {
    "Michał":  1432598760,
    "Gosia":   2387614509,
    "Dawid":   3521478963,
    "Damian":  6791832282,
    "Kasia":   4198237645,
    "Ola":     5763920184,
    "Aurelia": 7629384510,
    "Oskar":   8374651029,
    "Olaf":    9012845673,
}
pracownicy = list(PRACOWNICY.keys())

KOLORY_TRASY = {"D": "#CC0000", "Ś": "#0055CC", "K": "#007700"}
NAZWY_TRASY  = {"D": "Długa",   "Ś": "Średnia", "K": "Krótka"}

ROZKLAD = {
    "R": [
        {"godzina": "9:30",  "trasa": "D"},
        {"godzina": "11:45", "trasa": "D"},
        {"godzina": "14:10", "trasa": "K"},
        {"godzina": "15:20", "trasa": "D"},
        {"godzina": "17:30", "trasa": "D"},
        {"godzina": "19:30", "trasa": "K"},
    ],
    "W": [
        {"godzina": "9:10",  "trasa": "D"},
        {"godzina": "11:20", "trasa": "D"},
        {"godzina": "13:30", "trasa": "Ś"},
        {"godzina": "15:00", "trasa": "K"},
        {"godzina": "15:50", "trasa": "D"},
        {"godzina": "17:50", "trasa": "D"},
    ],
}

# ── Helpery ─────────────────────────────────────────────────────────────────

def typ_dnia(dzien):
    return "R" if dzien.weekday() <= 4 else "W"

def godziny_dla_dnia(dzien):
    return [k["godzina"] for k in ROZKLAD[typ_dnia(dzien)]]

def trasa_dla_godziny(dzien, godzina):
    for k in ROZKLAD[typ_dnia(dzien)]:
        if k["godzina"] == godzina:
            return k["trasa"]
    return ""

def get_bot_token():
    try:
        return st.secrets["TELEGRAM_BOT_TOKEN"]
    except:
        return os.environ.get("TELEGRAM_BOT_TOKEN", "")

def wyslij_telegram(img_bytes, osoby):
    token = get_bot_token()
    if not token:
        return {"__error__": "Brak tokenu bota. Ustaw TELEGRAM_BOT_TOKEN w secrets lub zmiennych środowiskowych."}

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    wyniki = {}
    for osoba in sorted(osoby):
        chat_id = PRACOWNICY.get(osoba)
        if not chat_id:
            wyniki[osoba] = "❓ brak ID"
            continue
        try:
            resp = requests.post(
                url,
                data={"chat_id": chat_id},
                files={"photo": ("grafik.png", io.BytesIO(img_bytes), "image/png")},
                timeout=10,
            )
            wyniki[osoba] = "✅ wysłano" if resp.json().get("ok") else f"❌ {resp.json().get('description', 'błąd')}"
        except Exception as e:
            wyniki[osoba] = f"❌ {e}"
    return wyniki

# ── Generowanie obrazka ──────────────────────────────────────────────────────

def create_schedule_image(dzien, kursy):
    dni_polskie = ["poniedziałek", "wtorek", "środę", "czwartek", "piątek", "sobotę", "niedzielę"]
    dzien_obj = datetime.strptime(dzien, "%Y-%m-%d")
    tytul = f"Grafik na {dni_polskie[dzien_obj.weekday()]} {dzien_obj.strftime('%d.%m')}"

    base = 1000
    col_widths = [
        base // 4,  # Godzina
        200,        # Trasa
        base // 4,  # Kierownik
        300,        # Pomocnicy
    ]
    max_pomocnicy = max(len(k["pomocnicy"]) for k in kursy)
    col_widths[3] += max(0, max_pomocnicy - 2) * 100

    szerokosc = sum(col_widths)
    wysokosc  = 160 + 60 * len(kursy) + 60

    img  = Image.new('RGB', (szerokosc, wysokosc), color='#f9f9f9')
    draw = ImageDraw.Draw(img)

    try:
        font_title  = ImageFont.truetype(font_path, 46)
        font_header = ImageFont.truetype(font_path, 38)
        font        = ImageFont.truetype(font_path, 32)
    except:
        font_title = font_header = font = ImageFont.load_default()

    tw = draw.textlength(tytul, font=font_title)
    draw.text(((szerokosc - tw) / 2, 20), tytul, fill='black', font=font_title)

    col_starts = []
    x = 0
    for w in col_widths:
        col_starts.append(x)
        x += w

    def cx(col):
        return col_starts[col] + col_widths[col] // 2

    row_height = 60
    y_header   = 100

    for i, header in enumerate(["Godzina", "Trasa", "Kierownik", "Pomocnicy"]):
        w = draw.textlength(header, font=font_header)
        draw.text((cx(i) - w / 2, y_header), header, fill='black', font=font_header)

    header_height = draw.textbbox((0, 0), "Ag", font=font_header)[3] - draw.textbbox((0, 0), "Ag", font=font_header)[1]
    font_height   = draw.textbbox((0, 0), "Ag", font=font)[3]        - draw.textbbox((0, 0), "Ag", font=font)[1]
    x_gap         = row_height + 10 - font_height
    header_bottom = y_header + header_height
    line_y        = round(header_bottom + x_gap / 2)
    y_first_row   = header_bottom + x_gap

    draw.line([(20, line_y), (szerokosc - 20, line_y)], fill='black')

    y = y_first_row
    for kurs in kursy:
        godz  = kurs["godzina"]
        kier  = kurs["kierownik"] or "-"
        pomoc = ", ".join(kurs["pomocnicy"]) if kurs["pomocnicy"] else "-"
        trasa = kurs.get("dlugosc_trasy", "")

        for col, val in zip([0, 2, 3], [godz, kier, pomoc]):
            w = draw.textlength(val, font=font)
            draw.text((cx(col) - w / 2, y), val, fill='black', font=font)

        if trasa:
            tekst = NAZWY_TRASY.get(trasa, trasa)
            kolor = KOLORY_TRASY.get(trasa, 'black')
            w = draw.textlength(tekst, font=font)
            draw.text((cx(1) - w / 2, y + 1), tekst, fill=kolor, font=font)

        y += row_height + 10

    return img

# ── UI ───────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Kreator Grafiku LKD")
    st.title("Kreator Grafiku LKD")

    dzien   = st.date_input("Wybierz dzień:", value=date.today())
    godziny = godziny_dla_dnia(dzien)

    if "kursy" not in st.session_state or st.session_state.get("last_date") != dzien:
        st.session_state.kursy     = [{"godzina": "", "kierownik": None, "pomocnicy": [], "dlugosc_trasy": ""}]
        st.session_state.last_date = dzien
        st.session_state.pop("img_bytes",      None)
        st.session_state.pop("osoby_grafiku",  None)
        st.session_state.pop("nazwa_grafiku",  None)

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": [], "dlugosc_trasy": ""})

    def usun_kurs(idx):
        if len(st.session_state.kursy) > 1:
            st.session_state.kursy.pop(idx)

    st.write("### Kursy / Zmiany")

    for idx, kurs in enumerate(st.session_state.kursy):
        dlugosc_trasy = kurs.get("dlugosc_trasy", "")

        podglad = ""
        if kurs["godzina"]:   podglad += f"   {kurs['godzina']}"
        if dlugosc_trasy:     podglad += f"   [{NAZWY_TRASY[dlugosc_trasy]}]"
        if kurs["kierownik"]: podglad += f"   {kurs['kierownik']}"
        if kurs["pomocnicy"]: podglad += " + " + ", ".join(kurs["pomocnicy"])

        with st.expander(f"Kurs {idx+1}{podglad}", expanded=(idx == len(st.session_state.kursy) - 1)):
            godzina_typ = st.radio(
                f"Wybierz opcję godziny dla kursu {idx+1}",
                ["Z listy", "Wpisz ręcznie"],
                key=f"typ_godz_{idx}"
            )

            if godzina_typ == "Z listy":
                godz = st.selectbox(
                    f"Godzina kursu {idx+1}",
                    options=[""] + godziny,
                    index=godziny.index(kurs["godzina"]) + 1 if kurs["godzina"] in godziny else 0,
                    key=f"godz_{idx}"
                )
                trasa = trasa_dla_godziny(dzien, godz)
                if trasa:
                    st.caption(f"Długość trasy: **{trasa}** ({NAZWY_TRASY[trasa].lower()})")
            else:
                godz = st.text_input(
                    f"Godzina kursu {idx+1}",
                    value=kurs["godzina"],
                    key=f"godz_input_{idx}"
                )
                opcje_trasy = ["", "D", "Ś", "K"]
                trasa = st.selectbox(
                    f"Długość trasy kursu {idx+1}",
                    options=opcje_trasy,
                    index=opcje_trasy.index(dlugosc_trasy) if dlugosc_trasy in opcje_trasy else 0,
                    format_func=lambda x: {"": "— brak —", "D": "D (długa)", "Ś": "Ś (średnia)", "K": "K (krótka)"}.get(x, x),
                    key=f"trasa_{idx}"
                )

            kier = st.selectbox(
                f"Kierownik kursu {idx+1}",
                options=[""] + pracownicy,
                index=pracownicy.index(kurs["kierownik"]) + 1 if kurs["kierownik"] in pracownicy else 0,
                key=f"kier_{idx}"
            )

            pomoc = []
            if kier:
                mozliwi = [p for p in pracownicy if p != kier]
                pomoc = st.multiselect(
                    f"Pomocnicy kursu {idx+1}",
                    options=mozliwi,
                    default=[p for p in kurs["pomocnicy"] if p in mozliwi],
                    key=f"pomoc_{idx}_fixed"
                )

            st.session_state.kursy[idx].update({
                "godzina":       godz,
                "kierownik":     kier or None,
                "pomocnicy":     pomoc,
                "dlugosc_trasy": trasa,
            })

            if idx > 0 and idx == len(st.session_state.kursy) - 1:
                if st.button(f"❌ Usuń kurs {idx+1}", key=f"usun_{idx}"):
                    usun_kurs(idx)
                    st.experimental_rerun()

    if st.session_state.kursy[-1]["godzina"] and st.session_state.kursy[-1]["kierownik"]:
        st.button("➕ Dodaj kolejny kurs", on_click=dodaj_kurs)

    if st.button("🎨 Generuj grafik"):
        do_wykresu = [k for k in st.session_state.kursy if k["godzina"] and k["kierownik"]]
        if not do_wykresu:
            st.warning("Dodaj co najmniej jeden kurs z godziną i kierownikiem.")
            return

        img = create_schedule_image(dzien.strftime("%Y-%m-%d"), do_wykresu)
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        # Zbierz unikalne osoby z grafiku
        osoby = set()
        for k in do_wykresu:
            if k["kierownik"]: osoby.add(k["kierownik"])
            osoby.update(k["pomocnicy"])

        st.session_state.img_bytes     = buf.getvalue()
        st.session_state.osoby_grafiku = osoby
        st.session_state.nazwa_grafiku = f"grafik_{dzien}.png"

    # Pokaż grafik i przyciski jeśli wygenerowany
    if "img_bytes" in st.session_state:
        st.image(st.session_state.img_bytes)

        st.download_button(
            "⬇️ Pobierz grafik PNG",
            data=st.session_state.img_bytes,
            file_name=st.session_state.nazwa_grafiku,
            mime="image/png"
        )
        
        if st.button("📤 Wyślij grafik botem Telegram"):
            with st.spinner("Wysyłanie..."):
                wyniki = wyslij_telegram(
                    st.session_state.img_bytes,
                    st.session_state.osoby_grafiku
                )
            if "__error__" in wyniki:
                st.error(wyniki["__error__"])
            else:
                for osoba, status in wyniki.items():
                    st.write(f"{osoba}: {status}")

if __name__ == "__main__":
    main()
