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
    
    # Inicializace paměti chatu v session_state
    if "messages" not in st.session_state:
        st.session_state.messages = []

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

    # Vykreslení dosavadní historie chatu
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width="stretch")
            st.markdown(message["content"])

    # Vstup pro novou zprávu od uživatele (chat input dole)
    odpoved_uzivatele = st.chat_input("Napiš odpověď koučovi...")
    
    # Volitelná fotka vedle chatu
    fotka = st.file_uploader("Nebo nahraj novou fotku k aktuálnímu úkolu", type=["jpg", "jpeg", "png"])

    if odpoved_uzivatele or fotka:
        # Uložení zprávy uživatele do historie
        user_content = odpoved_uzivatele if odpoved_uzivatele else "Posílám fotku k úkolu."
        
        img_obj = None
        if fotka:
            img_obj = Image.open(fotka)

        # Zobrazení uživatelské zprávy v rozhraní
        with st.chat_message("user"):
            if img_obj:
                st.image(img_obj, width="stretch")
            st.markdown(user_content)

        # Přidání do historie
        st.session_state.messages.append({"role": "user", "content": user_content, "image": img_obj})

        with st.spinner("Kouč analyzuje tvou odpověď..."):
            
            # Sestavení kontextu z celé historie, aby AI věděla, co řešíme
            historie_text = f"Fáze trávníku: {krok}\n\n"
            for m in st.session_state.messages[:-1]:
                historie_text += f"{m['role'].upper()}: {m['content']}\n"
            
            plny_prompt = f"""
            {historie_text}
            USER (aktuální reakce): {user_content}

            Jsi osobní agronomický kouč. VEDÉŠ UŽIVATELE POSTUPNĚ, NIKDY NEDÁVEJ VŠECHNY ÚKOLY NARÁZ.
            Mluv přímo k uživateli v ty-formě ("Vezmi", "Udělej", "Napiš mi").

            TVÁ STRUKTURA ODPOVĚDI:
            1. 🔍 **Stručný pohled:** Krátce zhodnoť reakci uživatele.
            2. 🎯 **Jeden konkrétní úkol:** Dej uživateli POUZE JEDNU JEDINOU věc, kterou má teď udělat. 
            3. ❓ **Co chci slyšet / vidět:** Jasně řekni, co po něm budeš chtít v dalším kroku.
            """
            
            contents = [plny_prompt]
            if img_obj:
                contents.append(img_obj)
            
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=contents
                )
                ai_reply = response.text
            except Exception as e:
                ai_reply = "Omlouvám se, server je teď přetížený. Zkus zprávu odeslat za chvíli znovu."

            # Zobrazení odpovědi AI a uložení do historie
            with st.chat_message("assistant"):
                st.markdown(ai_reply)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
