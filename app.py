import streamlit as st
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(BASE_DIR, "fonts", "Roboto-Regular.ttf")

# Lista pracowników
pracownicy = ["Michał", "Gosia", "Dawid", "Damian", "Kasia", "Ola", "Aurelia", "Oskar", "Olaf"]

# Kolory dla długości trasy
KOLORY_TRASY = {
    "D": "#CC0000",   # czerwony
    "Ś": "#0055CC",   # niebieski
    "K": "#007700",   # zielony
}

# Przypisanie długości trasy do godzin z listy (zmień wg potrzeb)
TRASA_DLA_GODZINY = {
    "9:10": "D",
    "9:30": "D",
    "11:20": "D",
    "11:45": "D",
    "13:30": "Ś",
    "14:10": "K",
    "15:00": "K",
    "15:20": "D",
    "15:50": "D",
    "17:30": "D",
    "17:50": "D",
    "19:30": "K",
}

def create_schedule_image(dzien, kursy):
    dni_polskie = ["poniedziałek", "wtorek", "środę", "czwartek", "piątek", "sobotę", "niedzielę"]
    dzien_obj = datetime.strptime(dzien, "%Y-%m-%d")
    dzien_tygodnia = dni_polskie[dzien_obj.weekday()]
    dzien_formatted = dzien_obj.strftime('%d.%m')
    tytul = f"Grafik na {dzien_tygodnia} {dzien_formatted}"

    szerokosc = 900
    if any(len(k["pomocnicy"]) >= 3 for k in kursy):
        szerokosc += 100
    wysokosc = 160 + 60 * len(kursy) + 60

    img = Image.new('RGB', (szerokosc, wysokosc), color='#f9f9f9')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(font_path, 46)
        font_header = ImageFont.truetype(font_path, 38)
        font = ImageFont.truetype(font_path, 32)
        font_trasa = ImageFont.truetype(font_path, 32)
    except:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font = ImageFont.load_default()
        font_trasa = ImageFont.load_default()

    # Nagłówek
    title_width = draw.textlength(tytul, font=font_title)
    draw.text(((szerokosc - title_width) / 2, 20), tytul, fill='black', font=font_title)

    # Godzina i Trasa: łącznie 2/5, Kierownik i Pomocnicy: łącznie 3/5
    col_widths = [
        szerokosc // 5,       # Godzina   (1/5)
        szerokosc // 5,       # Trasa     (1/5)
        szerokosc * 3 // 10,  # Kierownik (3/10)
        szerokosc * 3 // 10,  # Pomocnicy (3/10)
    ]
    col_starts = [0]
    for w in col_widths[:-1]:
        col_starts.append(col_starts[-1] + w)

    y = 100
    row_height = 60

    headers = ["Godzina", "Trasa", "Kierownik", "Pomocnicy"]
    for i, header in enumerate(headers):
        x_center = col_starts[i] + col_widths[i] // 2
        w = draw.textlength(header, font=font_header)
        draw.text((x_center - w / 2, y), header, fill='black', font=font_header)

    y += 40
    draw.line([(20, y), (szerokosc - 20, y)], fill='black')

    bbox = draw.textbbox((0, 0), "Ag", font=font)
    font_height = bbox[3] - bbox[1]
    y += (60 - font_height)
    
    for kurs in kursy:
        y += 10
        godz = kurs["godzina"]
        kier = kurs["kierownik"] or "-"
        pomoc = ", ".join(kurs["pomocnicy"]) if kurs["pomocnicy"] else "-"
        trasa = kurs.get("dlugosc_trasy", "")

        # Kolumny tekstowe (czarny): Godzina=0, Kierownik=2, Pomocnicy=3
        for i, val in zip([0, 2, 3], [godz, kier, pomoc]):
            x_center = col_starts[i] + col_widths[i] // 2
            w = draw.textlength(val, font=font)
            draw.text((x_center - w / 2, y), val, fill='black', font=font)

        # Kolumna Trasa=1 – kolorowa litera
        if trasa:
            PELNE_NAZWY = {"D": "Długa", "Ś": "Średnia", "K": "Krótka"}
            kolor = KOLORY_TRASY.get(trasa, 'black')
            tekst_trasy = PELNE_NAZWY.get(trasa, trasa)
            x_center = col_starts[1] + col_widths[1] // 2
            w = draw.textlength(tekst_trasy, font=font_trasa)
            draw.text((x_center - w / 2, y + 1), tekst_trasy, fill=kolor, font=font_trasa)

        y += row_height

    return img

def main():
    st.set_page_config(page_title="Kreator Grafiku LKD")
    st.title("Kreator Grafiku LKD")

    dzien = st.date_input("Wybierz dzień:", value=date.today())

    dzien_tyg = datetime.strptime(str(dzien), "%Y-%m-%d").weekday()
    if dzien_tyg < 4:
        godziny_domyslne = ["16:00"]
    else:
        godziny_domyslne = ["9:15", "11:25", "13:35", "15:45", "17:50", "19:20"]

    if "kursy" not in st.session_state or st.session_state.get("last_date") != dzien:
        st.session_state.kursy = [{"godzina": "", "kierownik": None, "pomocnicy": [], "dlugosc_trasy": ""}]
        st.session_state.last_date = dzien

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": [], "dlugosc_trasy": ""})

    def usun_kurs(idx):
        if len(st.session_state.kursy) > 1:
            st.session_state.kursy.pop(idx)

    st.write("### Kursy / Zmiany")

    for idx, kurs in enumerate(st.session_state.kursy):
        godzina = kurs["godzina"]
        kier = kurs["kierownik"] or ""
        pomocnicy = kurs["pomocnicy"]
        dlugosc_trasy = kurs.get("dlugosc_trasy", "")

        podglad = ""
        if godzina:
            podglad += f"   {godzina}"
        if kier:
            podglad += f"   {kier}"
        if pomocnicy:
            podglad += " + " + ", ".join(pomocnicy)
        if dlugosc_trasy:
            podglad += f"   [{dlugosc_trasy}]"

        expanded = True if idx == len(st.session_state.kursy) - 1 else False
        with st.expander(f"Kurs {idx+1}{podglad}", expanded=expanded):
            godzina_typ = st.radio(f"Wybierz opcję godziny dla kursu {idx+1}", ["Z listy", "Wpisz ręcznie"], key=f"typ_godz_{idx}")

            if godzina_typ == "Z listy":
                godz = st.selectbox(f"Godzina kursu {idx+1}", options=[""] + godziny_domyslne, index=godziny_domyslne.index(kurs["godzina"]) + 1 if kurs["godzina"] in godziny_domyslne else 0, key=f"godz_{idx}")
                trasa = TRASA_DLA_GODZINY.get(godz, "")
                if trasa:
                    etykiety = {"D": "długa", "Ś": "średnia", "K": "krótka"}
                    st.caption(f"Długość trasy: **{trasa}** ({etykiety[trasa]})")
            else:
                godz = st.text_input(f"Godzina kursu {idx+1}", value=kurs["godzina"], key=f"godz_input_{idx}")
                opcje_trasy = ["", "D", "Ś", "K"]
                trasa_idx = opcje_trasy.index(dlugosc_trasy) if dlugosc_trasy in opcje_trasy else 0
                trasa = st.selectbox(
                    f"Długość trasy kursu {idx+1}",
                    options=opcje_trasy,
                    index=trasa_idx,
                    format_func=lambda x: {"": "— brak —", "D": "D (długa)", "Ś": "Ś (średnia)", "K": "K (krótka)"}.get(x, x),
                    key=f"trasa_{idx}"
                )

            kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy, index=pracownicy.index(kurs["kierownik"]) + 1 if kurs["kierownik"] in pracownicy else 0, key=f"kier_{idx}")

            pomoc = []
            if kier:
                mozliwi_pomocnicy = [p for p in pracownicy if p != kier]
                pomoc = st.multiselect(f"Pomocnicy kursu {idx+1}", options=mozliwi_pomocnicy, default=[p for p in kurs["pomocnicy"] if p in mozliwi_pomocnicy], key=f"pomoc_{idx}_fixed")

            st.session_state.kursy[idx]["godzina"] = godz
            st.session_state.kursy[idx]["kierownik"] = kier if kier else None
            st.session_state.kursy[idx]["pomocnicy"] = pomoc
            st.session_state.kursy[idx]["dlugosc_trasy"] = trasa

            if idx > 0 and idx == len(st.session_state.kursy) - 1:
                if st.button(f"❌ Usuń kurs {idx+1}", key=f"usun_{idx}"):
                    usun_kurs(idx)
                    st.experimental_rerun()

    ostatni_kurs = st.session_state.kursy[-1]
    if ostatni_kurs["godzina"] and ostatni_kurs["kierownik"]:
        st.button("➕ Dodaj kolejny kurs", on_click=dodaj_kurs)

    if st.button("🎨 Generuj grafik"):
        kursy_do_wykresu = [k for k in st.session_state.kursy if k["godzina"] and k["kierownik"]]
        if not kursy_do_wykresu:
            st.warning("Dodaj co najmniej jeden kurs z godziną i kierownikiem.")
            return
        img = create_schedule_image(dzien.strftime("%Y-%m-%d"), kursy_do_wykresu)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.image(img)
        st.download_button("⬇️ Pobierz grafik PNG", data=buf.getvalue(), file_name=f"grafik_{dzien}.png", mime="image/png")

if __name__ == "__main__":
    main()
