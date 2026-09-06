import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Trávníkový Průvodce", page_icon="🌱", layout="centered")

st.title("🌱 Osobní Trávníkový Průvodce")
st.caption("Krok za krokem od přípravy půdy až po dokonalý trávník")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chybí Gemini API klíč v Secrets!")
else:
    genai.configure(api_key=api_key)
    
    krok = st.selectbox(
        "📍 V jaké fázi se právě nacházíš?",
        [
            "1. Test podloží & Příprava půdy (Rýčová sonda)",
            "2. Kontrola výsevu (Správná hustota & vrstva hlíny)",
            "3. Kontrola hnojení (Aplikace & krytí)",
            "4. Vyhodnocení zálivky (Stav povrchu + podloží + počasí)",
            "5. Diagnostika & Regenerace (Nestandardní stav)"
        ]
    )

    komentar = st.text_input("Doplňující stav (např. 'včera pršelo 5mm', 'značka hnojiva Agro', 'hlína je jílovitá'):")
    
    fotka = st.camera_input("Vyfoť aktuální krok") or st.file_uploader("Upload fotky", type=["jpg", "jpeg", "png"])

    if fotka:
        img = Image.open(fotka)
        st.image(img, caption="Nahraný podklad pro AI", use_container_width=True)
        
        if st.button("🚀 Vyhodnotit tento krok"):
            with st.spinner("AI provádí hloubkovou analýzu kroku..."):
                
                system_instruction = """
                Jsi specializovaný kouč pro zakládání a péči o trávník. Tovým úkolem je vést uživatele KROK ZA KROKEM.
                Nikdy nedávej obecné poučky. Chovej se jako inspektor na stavbě trávníku.

                PRAVIDLA PRO JEDNOTLIVÉ FÁZE:
                - '1. Test podloží': Zhodnoť strukturu půdy z fotky sondy/rýče. Urči, zda je půda utlačená, jílovitá nebo písčitá a jak hluboko je vlhko.
                - '2. Kontrola výsevu': Posuď viditelnou hustotu osiva a zda je dostatečně překryté vrstvou zeminy/substrátu. 
                - '3. Kontrola hnojení': Zkontroluj rovnoměrnost granulek na povrchu.
                - '4. Vyhodnocení zálivky': Propoj vizuální stav povrchu s tím, co napsal uživatel o počasí. Řekni PŘESNĚ, kolik vody dát.
                
                STRUKTURA ODPOVĚDI:
                1. 🔍 **Hodnocení fotky:**
                2. 🚦 **Verdikt:** 
                3. ➡️ **Následující úkol pro uživatele:**
                """
                
                # Zjištění funkčního modelu dynamicky přes list_models
                dostupne_modely = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                zvoleny_model = "models/gemini-1.5-flash"
                for m in dostupne_modely:
                    if "1.5-flash" in m:
                        zvoleny_model = m
                        break
                
                model = genai.GenerativeModel(
                    model_name=zvoleny_model,
                    system_instruction=system_instruction
                )
                
                prompt = f"Aktuální krok procesu: {krok}. Poznámka od uživatele: {komentar}."
                response = model.generate_content([prompt, img])
                
                st.markdown("---")
                st.subheader("👨‍🌾 Instrukce pro tento krok:")
                st.write(response.text)
