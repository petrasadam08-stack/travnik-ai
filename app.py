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

    # Vykreslení historie chatu
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("image"):
                st.image(message["image"], width="stretch")
            st.markdown(message["content"])

    with st.expander("📷 Chce kouč fotku? Klikni sem pro nahrání"):
        fotka = st.file_uploader("Vyber fotku", type=["jpg", "jpeg", "png"], key="dynamic_photo")

    odpoved_uzivatele = st.chat_input("Napiš odpověď koučovi...")

    if odpoved_uzivatele or fotka:
        user_content = odpoved_uzivatele if odpoved_uzivatele else "Posílám vyžádanou fotku."
        
        img_obj = Image.open(fotka) if fotka else None

        with st.chat_message("user"):
            if img_obj:
                st.image(img_obj, width="stretch")
            st.markdown(user_content)

        # Uložíme do historie (fotku si paměť nechá pro zobrazení, ale AI ji nedostane opakovaně)
        st.session_state.messages.append({"role": "user", "content": user_content, "image": img_obj})

        with st.spinner("Kouč analyzuje tvou odpověď..."):
            
            # Sestavení textové historie rozhovoru
            historie_text = f"Fáze trávníku: {krok}\n\n"
            for m in st.session_state.messages[:-1]:
                historie_text += f"{m['role'].upper()}: {m['content']}\n"
            
            plny_prompt = f"""
            {historie_text}
            USER (aktuální reakce): {user_content}

            Jsi zkušený agronomický kouč. Vedeš uživatele krok za krokem.
            
            PRAVIDLA:
            1. Reaguj primárně na aktuální odpověď uživatele a posouvej vyšetřování kupředu k finální diagnóze. Nevracej se k hodnocení prvotní fotky, pokud už jsme ji rozebrali a udělali test.
            2. Mluv přímo k uživateli v ty-formě ("Vezmi", "Udělej", "Napiš mi").
            3. Dej POUZE JEDNU JEDINOU věc, kterou má teď udělat.

            TVÁ STRUKTURA ODPOVĚDI:
            1. 🔍 **Stručný pohled:** Reaguj na výsledek úkolu.
            2. 🎯 **Jeden konkrétní úkol:** Co má udělat teď.
            3. ❓ **Co chci slyšet / vidět:** Co po něm budeš chtít příště.
            """
            
            # Posíláme primárně textový prompt s historií. Pokud uživatel *teď v této zprávě* nahrál novou fotku, přiložíme ji.
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

            with st.chat_message("assistant"):
                st.markdown(ai_reply)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
