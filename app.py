import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Trávníkový Průvodce", page_icon="🌱", layout="centered")

st.title("🌱 Osobní Trávníkový Průvodce")
st.caption("Krok za krokem od přípravy půdy až po dokonalý trávník")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chybí Gemini API klíč v Secrets ve Streamlitu!")
else:
    client = genai.Client(api_key=api_key)
    
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
                
                plny_prompt = f"""
                Jsi specializovaný kouč pro zakládání a péči o trávník. Tvým úkolem je vést uživatele KROK ZA KROKEM.
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

                Aktuální krok procesu: {krok}
                Poznámka od uživatele: {komentar}
                """
                
                # Aktualizováno na model požadovaný rozhraním Google API
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[img, plny_prompt]
                )
                
                st.markdown("---")
                st.subheader("👨‍🌾 Instrukce pro tento krok:")
                st.write(response.text)
