import streamlit as st
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import io

# Lista pracowników
pracownicy = ["Michał", "Gosia", "Dawid", "Damian", "Kasia", "Ola", "Aurelia", "Oskar", "Olaf"]

def create_schedule_image(dzien, kursy):
    dni_polskie = ["poniedziałek", "wtorek", "środę", "czwartek", "piątek", "sobotę", "niedzielę"]
    dzien_obj = datetime.strptime(dzien, "%Y-%m-%d")
    dzien_tygodnia = dni_polskie[dzien_obj.weekday()]
    dzien_formatted = dzien_obj.strftime('%d.%m')
    tytul = f"Grafik na {dzien_tygodnia} {dzien_formatted}"

    szerokosc = 800
    if any(len(k["pomocnicy"]) >= 3 for k in kursy):
        szerokosc += 100
    wysokosc = 160 + 60 * len(kursy) + 60

    img = Image.new('RGB', (szerokosc, wysokosc), color='#f9f9f9')
    draw = ImageDraw.Draw(img)
    
    try:
        # Arial może nie mieć polskich znaków, dlatego lepiej DejaVuSans
        font_title = ImageFont.truetype("DejaVuSans.ttf", 46)
        font_header = ImageFont.truetype("DejaVuSans.ttf", 34)
        font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        # fallback do domyślnej, ale może brakować polskich znaków
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font = ImageFont.load_default()

    # Nagłówek
    title_width = draw.textlength(tytul, font=font_title)
    draw.text(((szerokosc - title_width) / 2, 20), tytul, fill='black', font=font_title)

    col_width = szerokosc // 3
    y = 100
    row_height = 60

    headers = ["Godzina", "Kierownik", "Pomocnicy"]
    for i, header in enumerate(headers):
        x_center = (i * col_width) + (col_width // 2)
        w = draw.textlength(header, font=font_header)
        draw.text((x_center - w / 2, y), header, fill='black', font=font_header)

    y += 40
    draw.line([(20, y), (szerokosc - 20, y)], fill='black')

    for kurs in kursy:
        y += 10
        godz = kurs["godzina"]
        kier = kurs["kierownik"] or "-"
        pomoc = ", ".join(kurs["pomocnicy"]) if kurs["pomocnicy"] else "-"

        values = [godz, kier, pomoc]
        for i, val in enumerate(values):
            x_center = (i * col_width) + (col_width // 2)
            w = draw.textlength(val, font=font)
            draw.text((x_center - w / 2, y), val, fill='black', font=font)
        y += row_height

    return img

def main():
    st.set_page_config(page_title="Kreator Grafiku LKD")
    st.title("Kreator Grafiku LKD")

    dzien = st.date_input("Wybierz dzień:", value=date.today())

    dzien_tyg = datetime.strptime(str(dzien), "%Y-%m-%d").weekday()
    if dzien_tyg < 5:
        godziny_domyslne = ["9:30", "12:00", "14:15", "15:20", "17:30"]
    else:
        godziny_domyslne = ["9:15", "11:25", "13:35", "15:45", "17:30"]

    if "kursy" not in st.session_state or st.session_state.get("last_date") != dzien:
        st.session_state.kursy = [{"godzina": "", "kierownik": None, "pomocnicy": []}]
        st.session_state.last_date = dzien

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": []})

    def usun_kurs(idx):
        if len(st.session_state.kursy) > 1:
            st.session_state.kursy.pop(idx)

    st.write("### Kursy / Zmiany")

    for idx, kurs in enumerate(st.session_state.kursy):
        godzina = kurs["godzina"]
        kier = kurs["kierownik"] or ""
        pomocnicy = kurs["pomocnicy"]

        podglad = ""
        if godzina:
            podglad += f"   {godzina}"
        if kier:
            podglad += f"   {kier}"
        if pomocnicy:
            podglad += " + " + ", ".join(pomocnicy)

        expanded = True if idx == len(st.session_state.kursy) - 1 else False
        with st.expander(f"Kurs {idx+1}{podglad}", expanded=expanded):
            godzina_typ = st.radio(f"Wybierz opcję godziny dla kursu {idx+1}", ["Z listy", "Wpisz ręcznie"], key=f"typ_godz_{idx}")

            if godzina_typ == "Z listy":
                godz = st.selectbox(f"Godzina kursu {idx+1}", options=[""] + godziny_domyslne, index=godziny_domyslne.index(kurs["godzina"]) + 1 if kurs["godzina"] in godziny_domyslne else 0, key=f"godz_{idx}")
            else:
                godz = st.text_input(f"Godzina kursu {idx+1}", value=kurs["godzina"], key=f"godz_input_{idx}")

            kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy, index=pracownicy.index(kurs["kierownik"]) + 1 if kurs["kierownik"] in pracownicy else 0, key=f"kier_{idx}")

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
