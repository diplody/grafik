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
    st.title("Kreator Grafiku LKD")

    nowy_dzien = st.date_input("Wybierz dzień:", value=date.today())
    if "dzien" not in st.session_state or nowy_dzien != st.session_state.get("dzien"):
        st.session_state.dzien = nowy_dzien
        st.session_state.kursy = [{"godzina": "", "kierownik": None, "pomocnicy": []}]

    dzien_tyg = datetime.strptime(str(st.session_state.dzien), "%Y-%m-%d").weekday()
    godziny_domyslne = ["9:30", "12:00", "15:20", "17:30"] if dzien_tyg < 5 else ["9:15", "11:25", "13:35", "15:45", "17:30"]

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": []})

    def usun_kurs(idx):
        if len(st.session_state.kursy) > 1:
            st.session_state.kursy.pop(idx)
            st.experimental_rerun()

    st.write("### Kursy / Zmiany")

    for idx, kurs in enumerate(st.session_state.kursy):
        godz = kurs["godzina"]
        kier = kurs["kierownik"]
        pomoc = ", ".join(kurs["pomocnicy"]) if kurs["pomocnicy"] else ""
        opis = ""
        if godz:
            opis += f"   {godz}"
        if kier:
            opis += f"   {kier}"
        if pomoc:
            opis += f" + {pomoc}"

        expanded = True if idx == len(st.session_state.kursy) - 1 else False
        with st.expander(f"Kurs {idx+1}{opis}", expanded=expanded):
            godzina_typ = st.radio(f"Wybierz opcję godziny dla kursu {idx+1}", ["Z listy", "Wpisz ręcznie"], key=f"typ_godz_{idx}")

            if godzina_typ == "Z listy":
                godz = st.selectbox(f"Godzina kursu {idx+1}", options=[""] + godziny_domyslne, index=godziny_domyslne.index(godz) + 1 if godz in godziny_domyslne else 0, key=f"godz_{idx}")
            else:
                godz = st.text_input(f"Godzina kursu {idx+1}", value=godz, key=f"godz_input_{idx}")

            kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy, index=pracownicy.index(kier) + 1 if kier in pracownicy else 0, key=f"kier_{idx}")

            pomoc = []
            if kier:
                mozliwi_pomocnicy = [p for p in pracownicy if p != kier]
                pomoc = st.multiselect(f"Pomocnicy kursu {idx+1}", options=mozliwi_pomocnicy, default=[p for p in kurs["pomocnicy"] if p in mozliwi_pomocnicy], key=f"pomoc_{idx}_fixed")

            st.session_state.kursy[idx]["godzina"] = godz
            st.session_state.kursy[idx]["kierownik"] = kier if kier else None
            st.session_state.kursy[idx]["pomocnicy"] = pomoc

            if idx > 0 and idx == len(st.session_state.kursy) - 1:
                if st.button(f"❌ Usuń kurs {idx+1}", key=f"usun_{idx}"):
                    usun_kurs(idx)

    ostatni_kurs = st.session_state.kursy[-1]
    if ostatni_kurs["godzina"].strip() and ostatni_kurs["kierownik"]:
        st.button("➕ Dodaj kolejny kurs", on_click=dodaj_kurs)

    if st.button("🎨 Generuj grafik"):
        kursy_do_wykresu = [k for k in st.session_state.kursy if k["godzina"].strip() and k["kierownik"]]
        if not kursy_do_wykresu:
            st.warning("Dodaj co najmniej jeden kurs z godziną i kierownikiem.")
            return
        img = create_schedule_image(st.session_state.dzien.strftime("%Y-%m-%d"), kursy_do_wykresu)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.image(img)
        st.download_button("⬇️ Pobierz grafik PNG", data=buf.getvalue(), file_name=f"grafik_{st.session_state.dzien}.png", mime="image/png")

if __name__ == "__main__":
    main()
