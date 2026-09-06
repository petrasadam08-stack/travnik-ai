import streamlit as st
import google.generativeai as genai
from PIL import Image

# Nastavení mobilního vzhledu
st.set_page_config(page_title="Trávníkový Průvodce", page_icon="🌱", layout="centered")

st.title("🌱 Osobní Trávníkový Průvodce")
st.caption("Krok za krokem od přípravy půdy až po dokonalý trávník")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chybí Gemini API klíč v Secrets!")
else:
    genai.configure(api_key=api_key)
    
    # KROKOVÁNÍ PODLE TVÉHO KONCEPTU
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
                
                # PŘÍSNÝ SYSTEM PROMPT NA MÍRU TVÉMU NÁPADU
                system_instruction = """
                Jsi specializovaný kouč pro zakládání a péči o trávník. Tovým úkolem je vést uživatele KROK ZA KROKEM.
                Nikdy nedávej obecné poučky. Chovej se jako inspektor na stavbě trávníku.

                PRAVIDLA PRO JEDNOTLIVÉ FÁZE:
                
                - Pokud jde o '1. Test podloží': Zhodnoť strukturu půdy z fotky sondy/rýče. Urči, zda je půda utlačená, jílovitá nebo písčitá a jak hluboko je vlhko.
                - Pokud jde o '2. Kontrola výsevu': Posuď viditelnou hustotu osiva a zda je dostatečně překryté vrstvou zeminy/substrátu. 
                - Pokud jde o '3. Kontrola hnojení': Zkontroluj rovnoměrnost granulek na povrchu. Pokud hrozí spálení nebo je dávka malá, hned reaguj.
                - Pokud jde o '4. Vyhodnocení zálivky': Propoj vizuální stav povrchu s tím, co napsal uživatel o počasí. Řekni PŘESNĚ, kolik litrů/mm vody dát, nebo zda nezalévat vůbec.
                
                STRUKTURA ODPOVĚDI:
                1. 🔍 **Hodnocení fotky:** (Co přesně vidíš - hustota, vlhkost podloží, vrstva hlíny)
                2. 🚦 **Verdikt:** (OK / PŘIDAT / UBRAT / PROLÍT VODOU)
                3. ➡️ **Následující úkol pro uživatele:** (Co má udělal TEĎ a co bude další fotka, kterou po něm budeš chtít)
                """
                
                # Použití stabilního názvu modelu
                model = genai.GenerativeModel(
                   model_name="gemini-1.5-flash",
                    system_instruction=system_instruction
                )
                
                prompt = f"Aktuální krok procesu: {krok}. Poznámka od uživatele: {komentar}."
                response = model.generate_content([prompt, img])
                
                st.markdown("---")
                st.subheader("👨‍🌾 Instrukce pro tento krok:")
                st.write(response.text)
