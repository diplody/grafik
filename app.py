import streamlit as st
from datetime import date
from PIL import Image, ImageDraw, ImageFont
import io

# Lista pracowników
pracownicy = ["Michał", "Gosia", "Dawid", "Damian", "Kasia", "Ola", "Aurelia", "Oskar", "Olaf"]

def create_schedule_image(dzien, kursy):
    # Parametry obrazka
    szerokosc = 600
    wysokosc = 100 + 40 * len(kursy)
    img = Image.new('RGB', (szerokosc, wysokosc), color='white')
    draw = ImageDraw.Draw(img)

    # Czcionka (wbudowana PIL)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    # Nagłówek
    draw.text((10, 10), f"Grafik na dzień: {dzien}", fill='black', font=font)

    # Tabela nagłówki
    start_y = 50
    draw.text((10, start_y), "Godzina", fill='black', font=font)
    draw.text((150, start_y), "Kierownik", fill='black', font=font)
    draw.text((350, start_y), "Pomocnicy", fill='black', font=font)
    draw.line([(10, start_y+25), (szerokosc-10, start_y+25)], fill='black')

    # Wiersze z danymi
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

    # Lista kursów (dynamiczna)
    if "kursy" not in st.session_state:
        st.session_state.kursy = [{"godzina": "", "kierownik": None, "pomocnicy": []}]

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": []})

    # Pokazujemy kursy
    st.write("### Kursy / Zmiany")

    for idx, kurs in enumerate(st.session_state.kursy):
        with st.expander(f"Kurs {idx+1}"):
            godz = st.text_input(f"Godzina kursu {idx+1}", value=kurs["godzina"], key=f"godz_{idx}")
            kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy, index=pracownicy.index(kurs["kierownik"]) + 1 if kurs["kierownik"] in pracownicy else 0, key=f"kier_{idx}")
            # Lista pomocników - bez kierownika
            mozliwi_pomocnicy = [p for p in pracownicy if p != kier]
            pomoc = st.multiselect(f"Pomocnicy kursu {idx+1}", options=mozliwi_pomocnicy, default=kurs["pomocnicy"], key=f"pomoc_{idx}")

            # Zapisujemy do stanu
            st.session_state.kursy[idx]["godzina"] = godz
            st.session_state.kursy[idx]["kierownik"] = kier if kier else None
            st.session_state.kursy[idx]["pomocnicy"] = pomoc

    st.button("➕ Dodaj kolejny kurs", on_click=dodaj_kurs)

    if st.button("🎨 Generuj grafik"):
        # Sprawdzenie i filtracja kursów z godziną i kierownikiem
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
