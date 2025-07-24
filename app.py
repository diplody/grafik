import streamlit as st
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import io
import time

pracownicy = ["Michał", "Gosia", "Dawid", "Damian", "Kasia", "Ola", "Aurelia", "Oskar", "Olaf"]

def create_schedule_image(dzien, kursy):
    # ... (bez zmian)
    pass

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
    if "pomocnik_invalid" not in st.session_state:
        st.session_state.pomocnik_invalid = {}

    def dodaj_kurs():
        st.session_state.kursy.append({"godzina": "", "kierownik": None, "pomocnicy": []})

    def usun_kurs(idx):
        if len(st.session_state.kursy) > 1:
            st.session_state.kursy.pop(idx)

    st.write("### Kursy / Zmiany")

    zajete_godziny = set()

    # ... reszta kodu bez zmian ...

for idx, kurs in enumerate(st.session_state.kursy):
    expanded = True if idx == len(st.session_state.kursy) - 1 else False
    with st.expander(f"Kurs {idx+1}   {kurs['godzina']}   {kurs['kierownik'] or '-'} + {', '.join(kurs['pomocnicy']) if kurs['pomocnicy'] else '-'}", expanded=expanded):
        godzina_typ = st.radio(f"Wybierz opcję godziny dla kursu {idx+1}", ["Z listy", "Wpisz ręcznie"], key=f"typ_godz_{idx}")

        if godzina_typ == "Z listy":
            dostepne_godziny = [g for g in godziny_domyslne if g not in zajete_godziny]
            godz = st.selectbox(f"Godzina kursu {idx+1}", options=[""] + dostepne_godziny,
                               index=dostepne_godziny.index(kurs["godzina"]) + 1 if kurs["godzina"] in dostepne_godziny else 0,
                               key=f"godz_{idx}")
        else:
            godz = st.text_input(f"Godzina kursu {idx+1}", value=kurs["godzina"], key=f"godz_input_{idx}")

        kier = st.selectbox(f"Kierownik kursu {idx+1}", options=[""] + pracownicy,
                           index=pracownicy.index(kurs["kierownik"]) + 1 if kurs["kierownik"] in pracownicy else 0,
                           key=f"kier_{idx}")

        st.session_state.kursy[idx]["godzina"] = godz
        st.session_state.kursy[idx]["kierownik"] = kier if kier else None

        if kier:
            # Lista pomocników bez kierownika
            mozliwi_pomocnicy = [p for p in pracownicy if p != kier]

            wybrane_pomocnicy = kurs["pomocnicy"]

            def render_multiselect_with_block(idx, options, selected):
                selected_set = set(selected)
                key_invalid = f"pomocnik_invalid_{idx}"

                nowe_wybrane = []
                for p in options:
                    zaznaczony = p in selected_set
                    checked = st.checkbox(p, value=zaznaczony, key=f"pomocnik_{idx}_{p}")

                    if checked:
                        if p in nowe_wybrane:
                            if key_invalid not in st.session_state or not st.session_state[key_invalid]:
                                st.session_state[key_invalid] = True
                                st.warning(f"Pomocnik {p} jest już wybrany w tym kursie!", icon="⚠️")
                        else:
                            nowe_wybrane.append(p)
                    else:
                        if p in nowe_wybrane:
                            nowe_wybrane.remove(p)

                if key_invalid in st.session_state and st.session_state[key_invalid]:
                    st.session_state[key_invalid] = False

                return nowe_wybrane

            pomoc = render_multiselect_with_block(idx, mozliwi_pomocnicy, wybrane_pomocnicy)
            st.session_state.kursy[idx]["pomocnicy"] = pomoc
        else:
            st.session_state.kursy[idx]["pomocnicy"] = []

        if godz:
            zajete_godziny.add(godz)

        if idx > 0 and idx == len(st.session_state.kursy) - 1:
            if st.button(f"❌ Usuń kurs {idx+1}", key=f"usun_{idx}"):
                usun_kurs(idx)
                st.experimental_rerun()

# ... reszta kodu bez zmian ...


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
