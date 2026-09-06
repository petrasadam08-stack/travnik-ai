import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Trávníkový Průvodce", page_icon="🌱", layout="centered")

st.title("🌱 Osobní Trávníkový Průvodce")
st.caption("Interaktivní agronomický kouč – krok za krokem")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chybí Gemini API klíč v Secrets ve Streamlitu!")
else:
    client = genai.Client(api_key=api_key)
    
    krok = st.selectbox(
        "📍 V jaké fázi se právě nacházíš?",
        [
            "1. Test podloží & Příprava půdy",
            "2. Kontrola výsevu",
            "3. Kontrola hnojení",
            "4. Vyhodnocení zálivky a stavu",
            "5. Diagnostika problému (fleky, choroby, škůdci)"
        ]
    )

    odpoved_uzivatele = st.text_input("Tvoje zpráva / odpověď na předchozí úkol:")
    
    fotka = st.camera_input("Vyfoť aktuální stav (pokud si o ni kouč řekl)") or st.file_uploader("Nebo nahraj fotku", type=["jpg", "jpeg", "png"])

    if st.button("💬 Odeslat koučovi"):
        with st.spinner("Kouč analyzuje situaci..."):
            
            plny_prompt = f"""
            Jsi osobní agronomický kouč. Tvojí zásadou je VÉST UŽIVATELE POSTUPNĚ, NIKDY NEDÁVEJ VŠECHNY ÚKOLY NARÁZ.
            Mluv přímo k uživateli v ty-formě ("Vezmi", "Udělej", "Napiš mi").

            TVÁ STRUKTURA ODPOVĚDI:
            1. 🔍 **Stručný pohled:** Krátce zhodnoť stav (co vidíš nebo co uživatel napsal).
            2. 🎯 **Jeden konkrétní úkol:** Dej uživateli POUZE JEDNU JEDINOU věc, kterou má teď udělat. 
            3. ❓ **Co chci slyšet / vidět:** Jasně řekni, co po tobě v dalším kroku budeš chtít (zda slovní odpověď, nebo fotku).

            AKTUÁLNÍ VSTUP OD UŽIVATELE:
            Fáze: {krok}
            Odpověď / reakce uživatele: {odpoved_uzivatele}
            """
            
            contents = [plny_prompt]
            if fotka:
                img = Image.open(fotka)
                st.image(img, caption="Aktuální podklad", width="stretch")
                contents.append(img)
            
            # Aktualizováno na model požadovaný rozhraním
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents
            )
            
            st.markdown("---")
            st.subheader("👨‍🌾 Kouč radí:")
            st.write(response.text)
