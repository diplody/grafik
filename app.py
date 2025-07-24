import streamlit as st
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import io

# Lista pracowników
pracownicy = ["Michał", "Gosia", "Dawid", "Damian", "Kasia", "Ola", "Aurelia", "Oskar", "Olaf"]

def create_schedule_image(dzien, kursy):
    szerokosc = 600
    wysokosc = 100 + 40 * len(kursy)
    img = Image.new('RGB', (szerokosc, wysokosc), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    draw.text((10, 10), f"Grafik na dzień: {dzien}", fill='black', font=font)

    start_y = 50
    draw.text((10, start_y), "Godzina", fill='black', font=font)
    draw.text((150, start_y), "Kierownik", fill='black', font=font)
    draw.text((350, start_y), "Pomocnicy", fill='black', font=font)
    draw.line([(10, start_y+25), (szerokosc-10, start_y+25)], fill='black')

    y = start_y + 30
    for kurs in kursy:
        godz = kurs["godzina"]
        kier = kurs["kierownik"] or "-"
        pomoc = ", ".join(kurs["pomocnicy"]) if kurs["pomocnicy"] else "-"
        draw.text((10, y), godz, fill='black', font=font)
        draw.text((150, y), kier, fill='black', font=font)
        draw.text((350, y), pomoc, fill='black', font=font)
        y += 40

    return img

def main():
    st.title("Grafik Zmian - Twój Plan")

    dzien = st.date_input("Wybierz dzień:", value=date.today())
    dzien_tyg = datetime.strptime(str(dzien), "%Y-%m-%d").weekday()
    
    if dzien_tyg < 5:
        godziny_domyslne = ["9:30", "12:00", "15:20", "17:30"]
    else:
        godziny_domyslne = ["9:15", "11:25", "13:35", "15:45", "17:30"]

    if "kursy" not in st.session_state:
        st.session_state.kursy = [{"godzina": "", "kierownik": None, "pomocnicy": []}]

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": []})

    st.write("### Kursy / Zmiany")

    for idx, kurs in enumerate(st.session_state.kursy):
        with st.expander(f"Kurs {idx+1}"):
            godzina_typ = st.radio(f"Wybierz opcję godziny dla kursu {idx+1}", ["Z listy", "Wpisz ręcznie"], key=f"typ_godz_{idx}")
            if godzina_typ == "Z listy":
                godz = st.selectbox(f"Godzina kursu {idx+1}", options=[""] + godziny_domyslne, index=godziny_domyslne.index(kurs["godzina"]) + 1 if kurs["godzina"] in godziny_domyslne else 0, key=f"godz_{idx}")
            else:
                godz = st.text_input(f"Godzina kursu {idx+1}", value=kurs["godzina"], key=f"godz_input_{idx}")

            kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy, index=pracownicy.index(kurs["kierownik"]) + 1 if kurs["kierownik"] in pracownicy else 0, key=f"kier_{idx}")

            mozliwi_pomocnicy = [p for p in pracownicy if p != kier]
            pomoc = st.multiselect(f"Pomocnicy kursu {idx+1}", options=mozliwi_pomocnicy, default=[p for p in kurs["pomocnicy"] if p in mozliwi_pomocnicy], key=f"pomoc_{idx}_fixed")

            st.session_state.kursy[idx]["godzina"] = godz
            st.session_state.kursy[idx]["kierownik"] = kier if kier else None
            st.session_state.kursy[idx]["pomocnicy"] = pomoc

        # Dodaj przycisk tylko po uzupełnieniu aktualnego kursu
        if idx == len(st.session_state.kursy) - 1:
            if kurs["godzina"] and kurs["kierownik"]:
                if st.button("➕ Dodaj kolejny kurs"):
                    dodaj_kurs()

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

