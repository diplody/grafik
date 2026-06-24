import streamlit as st
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(BASE_DIR, "fonts", "Roboto-Regular.ttf")

# ── Konfiguracja ────────────────────────────────────────────────────────────

pracownicy = ["Michał", "Gosia", "Dawid", "Damian", "Kasia", "Ola", "Aurelia", "Oskar", "Olaf"]

KOLORY_TRASY = {"D": "#CC0000", "Ś": "#0055CC", "K": "#007700"}
NAZWY_TRASY = {"D": "Długa", "Ś": "Średnia", "K": "Krótka"}
ROZKLAD = {
    "R": [  # Roboczy (pon–pt)
        {"godzina": "9:30", "trasa": "D"},
        {"godzina": "11:45", "trasa": "D"},
        {"godzina": "14:10", "trasa": "K"},
        {"godzina": "15:20", "trasa": "D"},
        {"godzina": "17:30", "trasa": "D"},
        {"godzina": "19:30", "trasa": "K"},
    ],
    "W": [  # Weekend (sob–nd)
        {"godzina": "9:10", "trasa": "D"},
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

# ── Generowanie obrazka ──────────────────────────────────────────────────────

def create_schedule_image(dzien, kursy):
    dni_polskie = ["poniedziałek", "wtorek", "środę", "czwartek", "piątek", "sobotę", "niedzielę"]
    dzien_obj = datetime.strptime(dzien, "%Y-%m-%d")
    tytul = f"Grafik na {dni_polskie[dzien_obj.weekday()]} {dzien_obj.strftime('%d.%m')}"

    base = 1000
    col_widths = [
        base // 4,       # Godzina   (1/4)
        base // 4,       # Trasa     (1/4)
        base // 4,       # Kierownik (1/4)
        base // 4,       # Pomocnicy (1/4)
    ]
    max_pomocnicy = max(len(k["pomocnicy"]) for k in kursy)
    col_widths[3] += max(0, max_pomocnicy - 2) * 100

    szerokosc = sum(col_widths)
    wysokosc = 160 + 60 * len(kursy) + 60

    img = Image.new('RGB', (szerokosc, wysokosc), color='#f9f9f9')
    draw = ImageDraw.Draw(img)

    try:
        font_title  = ImageFont.truetype(font_path, 46)
        font_header = ImageFont.truetype(font_path, 38)
        font        = ImageFont.truetype(font_path, 32)
    except:
        font_title = font_header = font = ImageFont.load_default()

    # Tytuł
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

    # Nagłówki
    for i, header in enumerate(["Godzina", "Trasa", "Kierownik", "Pomocnicy"]):
        w = draw.textlength(header, font=font_header)
        draw.text((cx(i) - w / 2, y_header), header, fill='black', font=font_header)

    # Oblicz odstęp x między wierszami danych i pozycję linii
    header_height = draw.textbbox((0, 0), "Ag", font=font_header)[3] - draw.textbbox((0, 0), "Ag", font=font_header)[1]
    font_height   = draw.textbbox((0, 0), "Ag", font=font)[3]        - draw.textbbox((0, 0), "Ag", font=font)[1]
    x_gap         = row_height + 10 - font_height   # odstęp między wierszami danych
    header_bottom = y_header + header_height
    line_y        = round(header_bottom + x_gap / 2)
    y_first_row   = header_bottom + x_gap

    draw.line([(20, line_y), (szerokosc - 20, line_y)], fill='black')

    # Wiersze danych
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
        st.session_state.kursy    = [{"godzina": "", "kierownik": None, "pomocnicy": [], "dlugosc_trasy": ""}]
        st.session_state.last_date = dzien

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
        if kurs["kierownik"]: podglad += f"   {kurs['kierownik']}"
        if kurs["pomocnicy"]: podglad += " + " + ", ".join(kurs["pomocnicy"])
        if dlugosc_trasy:     podglad += f"   [{dlugosc_trasy}]"

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
                "godzina":      godz,
                "kierownik":    kier or None,
                "pomocnicy":    pomoc,
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
        st.image(img)
        st.download_button("⬇️ Pobierz grafik PNG", data=buf.getvalue(), file_name=f"grafik_{dzien}.png", mime="image/png")

if __name__ == "__main__":
    main()
