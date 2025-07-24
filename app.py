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
        font_title = ImageFont.truetype("arial.ttf", 24)
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font_title = ImageFont.load_default()
        font = ImageFont.load_default()

    tytul = f"Grafik na dzień: {dzien}"
    text_width = draw.textlength(tytul, font=font_title)
    draw.text(((szerokosc - text_width) / 2, 10), tytul, fill='black', font=font_title)

    start_y = 60
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

    def usun_kurs(idx):
        if len(st.session_state.kursy) > 1:
            st.session_state.kursy.pop(idx)

    st.write("### Kursy / Zmiany")

    zajete_godziny = set()

    for idx, kurs in enumerate(st.session_state.kursy):
        expanded = True if idx == len(st.session_state.kursy) - 1 else False
        with st.expander(f"Kurs {idx+1}", expanded=expanded):
            godzina_typ = st.radio(f"Wybierz opcję godziny dla kursu {idx+1}", ["Z listy", "Wpisz ręcznie"], key=f"typ_godz_{idx}")
            poprzednia_godzina = st.session_state.kursy[idx - 1]["godzina"] if idx > 0 else None

            if godzina_typ == "Z listy":
                dostepne_godziny = [g for g in godziny_domyslne if g not in zajete_godziny and (idx == 0 or g > poprzednia_godzina)]
                godz = st.selectbox(f"Godzina kursu {idx+1}", options=[""] + dostepne_godziny, index=dostepne_godziny.index(kurs["godzina"]) + 1 if kurs["godzina"] in dostepne_godziny else 0, key=f"godz_{idx}")
            else:
                godz = st.text_input(f"Godzina kursu {idx+1}", value=kurs["godzina"], key=f"godz_input_{idx}")
                if godz in zajete_godziny:
                    st.warning("Ta godzina została już wybrana.")
                    godz = ""
                elif idx > 0 and poprzednia_godzina and godz <= poprzednia_godzina:
                    st.warning("Godzina musi być późniejsza niż w poprzednim kursie.")
                    godz = ""

            kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy, index=pracownicy.index(kurs["kierownik"]) + 1 if kurs["kierownik"] in pracownicy else 0, key=f"kier_{idx}")

            mozliwi_pomocnicy = [p for p in pracownicy if p != kier]
           pomoc = st.multiselect(
    f"Pomocnicy kursu {idx+1}",
    options=mozliwi_pomocnicy,
    default=[p for p in kurs["pomocnicy"] if p in mozliwi_pomocnicy],
    key=f"pomoc_{idx}_fixed"
)

            st.session_state.kursy[idx]["godzina"] = godz
            st.session_state.kursy[idx]["kierownik"] = kier if kier else None
            st.session_state.kursy[idx]["pomocnicy"] = pomoc

            if kurs["godzina"]:
    zajete_godziny.add(kurs["godzina"])


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
