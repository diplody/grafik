import streamlit as st
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import io
import calendar
import locale

# Lista pracowników
pracownicy = ["Michał", "Gosia", "Dawid", "Damian", "Kasia", "Ola", "Aurelia", "Oskar", "Olaf"]

def create_schedule_image(dzien, kursy):
   
    locale.setlocale(locale.LC_TIME, "pl_PL.UTF-8")  # ustawienie języka polskiego

    dzien_obj = datetime.strptime(dzien, "%Y-%m-%d")
    dzien_tygodnia = dzien_obj.strftime('%A').lower()
    dzien_formatted = dzien_obj.strftime('%d.%m')
    tytul = f"Grafik na {dzien_tygodnia} {dzien_formatted}"

    # Wymiary i styl
    base_width = 600
    line_height = 50
    extra_width = 100 if any(len(k["pomocnicy"]) >= 3 for k in kursy) else 0
    szerokosc = base_width + extra_width
    wysokosc = 100 + line_height * len(kursy) + 20

    img = Image.new('RGB', (szerokosc, wysokosc), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_header = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font = ImageFont.load_default()

    # Tytuł
    title_width = draw.textlength(tytul, font=font_title)
    draw.text(((szerokosc - title_width) / 2, 10), tytul, fill='black', font=font_title)

    # Nagłówki kolumn
    col_width = szerokosc // 3
    y_start = 70
    headers = ["Godzina", "Kierownik", "Pomocnicy"]
    for i, header in enumerate(headers):
        x = i * col_width + (col_width - draw.textlength(header, font=font_header)) / 2
        draw.text((x, y_start), header, fill='black', font=font_header)

    # Linie poziome
    y_line = y_start + 30
    draw.line([(10, y_line), (szerokosc - 10, y_line)], fill='black')

    # Kursy
    y = y_line + 10
    for kurs in kursy:
        godz = kurs["godzina"]
        kier = kurs["kierownik"] or "-"
        pomoc = ", ".join(kurs["pomocnicy"]) if kurs["pomocnicy"] else "-"
        values = [godz, kier, pomoc]
        for i, val in enumerate(values):
            x = i * col_width + 10
            draw.text((x, y), val, fill='black', font=font)
        y += line_height

    return img

def main():
    st.set_page_config(page_title="Kreator Grafiku LKD")
    st.title("Kreator Grafiku LKD")

    dzien = st.date_input("Wybierz dzień:", value=date.today())
    dzien_tyg = datetime.strptime(str(dzien), "%Y-%m-%d").weekday()

    if dzien_tyg < 5:
        godziny_domyslne = ["9:30", "12:00", "15:20", "17:30"]
    else:
        godziny_domyslne = ["9:15", "11:25", "13:35", "15:45", "17:30"]

    if "selected_day" not in st.session_state:
        st.session_state.selected_day = dzien

    if dzien != st.session_state.selected_day:
        st.session_state.kursy = [{"godzina": "", "kierownik": None, "pomocnicy": []}]
        st.session_state.selected_day = dzien

    if "kursy" not in st.session_state:
        st.session_state.kursy = [{"godzina": "", "kierownik": None, "pomocnicy": []}]

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": []})

    def usun_kurs(idx):
        if len(st.session_state.kursy) > 1:
            st.session_state.kursy.pop(idx)

    st.write("### Kursy / Zmiany")

    for idx, kurs in enumerate(st.session_state.kursy):
        opis = f"Kurs {idx+1}"
        if kurs["godzina"]:
            opis += f"   {kurs['godzina']}"
        if kurs["kierownik"]:
            opis += f"   {kurs['kierownik']}"
        if kurs["pomocnicy"]:
            opis += f" + {', '.join(kurs['pomocnicy'])}"

        expanded = True if idx == len(st.session_state.kursy) - 1 else False
        with st.expander(opis, expanded=expanded):
            godz = st.selectbox(f"Godzina kursu {idx+1}", options=[""] + godziny_domyslne, index=(godziny_domyslne.index(kurs["godzina"]) + 1) if kurs["godzina"] in godziny_domyslne else 0, key=f"godz_{idx}")
            st.session_state.kursy[idx]["godzina"] = godz

            kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy, index=(pracownicy.index(kurs["kierownik"]) + 1) if kurs["kierownik"] in pracownicy else 0, key=f"kier_{idx}")
            st.session_state.kursy[idx]["kierownik"] = kier if kier else None

            pomocnicy = []
            if kier:
                mozliwi_pomocnicy = [p for p in pracownicy if p != kier]
                pomocnicy = st.multiselect(f"Pomocnicy kursu {idx+1}", options=mozliwi_pomocnicy, default=[p for p in kurs["pomocnicy"] if p in mozliwi_pomocnicy], key=f"pomoc_{idx}")
                st.session_state.kursy[idx]["pomocnicy"] = pomocnicy

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
