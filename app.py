import time
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
    
    if "last_sent_photo_name" not in st.session_state:
        st.session_state.last_sent_photo_name = None

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

    # Zjistíme, jestli poslední zpráva od AI vyžadovala fotku
    posledni_zprava_ai = ""
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        posledni_zprava_ai = st.session_state.messages[-1]["content"].lower()

    chce_fotku = any(slovo in posledni_zprava_ai for slovo in ["fotku", "vyfotit", "snímek", "vyfoť"])
    
    tlacitko_bez_fotky_stisknuto = False
    if chce_fotku:
        if st.button("🚫 Nemůžu teď fotit (pokračovat bez fotky)"):
            tlacitko_bez_fotky_stisknuto = True

    with st.expander("📷 Chce kouč fotku? Klikni sem pro nahrání"):
        fotka = st.file_uploader("Vyber fotku", type=["jpg", "jpeg", "png"], key="dynamic_photo")

    odpoved_uzivatele = st.chat_input("Napiš zprávu koučovi...")

    if odpoved_uzivatele or tlacitko_bez_fotky_stisknuto:
        if tlacitko_bez_fotky_stisknuto:
            user_content = "Nemůžu teď fotit (je tma / nemám u sebe foťák). Můžeme pokračovat bez fotky popisem?"
            img_obj = None
        else:
            user_content = odpoved_uzivatele
            
            img_obj = None
            if fotka is not None:
                current_photo_name = fotka.name
                if current_photo_name != st.session_state.last_sent_photo_name:
                    img_obj = Image.open(fotka)
                    st.session_state.last_sent_photo_name = current_photo_name

        with st.chat_message("user"):
            if img_obj:
                st.image(img_obj, width="stretch")
            st.markdown(user_content)

        st.session_state.messages.append({"role": "user", "content": user_content, "image": img_obj})

        with st.spinner("Kouč přemýšlí..."):
            
            historie_text = f"Fáze trávníku: {krok}\n\n"
            for m in st.session_state.messages[:-1]:
                historie_text += f"{m['role'].upper()}: {m['content']}\n"
            
            plny_prompt = f"""
            {historie_text}
            USER (aktuální zpráva): {user_content}

            Jsi zkušený agronomický kouč. Mluv přímo v ty-formě ("Vezmi", "Udělej", "Napiš mi"). Mluv věcně, stručně a vynechávej prázdná klišé.

            PRAVIDLA PRO ODPOVĚĎ:
            1. **Běžná konverzace / Pozdravy / Poděkování:** Odpověz přátelsky, stručně, s trávníkovou tématikou.
            2. **Diagnostika:** Vyhodnoť situaci a pokud je to pro diagnózu nejlepší, rovnou si řekni o fotku.
            3. **Situace "Nemůžu teď fotit":** Pokud uživatel hlásí, že fotit nemůže, přejdi na slovní popis.
            4. **JEDINÝ ÚKOL A VARIABILITA:** 
               - Vždy dávej **pouze jeden jediný, naprosto konkrétní úkol** (nikdy nekombinuj víc věcí najednou).
               - Větu s úkolem uvoď přirozenou výzvou, kterou **obměňuj** (např. *„Teď udělej tohle:“*, *„Vrhni se na tohle:“*, *„Tvůj další krok:“*, *„Zkus teď toto:“*).
            5. **KONKRÉTNÍ ROZMĚRY A HODNOTY:** 
               - Pokud zadáváš úkol typu propichování vidlemi, aerifikace, hnojení, vertikutace apod., **vždy rovnou uveď i přesné parametry** (např. jak daleko od sebe mají být díry, do jaké hloubky, kolik gramů na metr apod.), aby se na to uživatel nemusel doplptávat.
            6. **FYZICKÉ AKCE (MIMO FOCENÍ A PSANÍ):** 
               - Pokud zadáváš úkol, který vyžaduje fyzickou práci trvající delší dobu (např. vertikutace, hnojení, sečení, postřik, aerifikace vidlemi), **na konec zprávy přidej pokyn, ať se ti uživatel ozve, až to bude mít hotové** (např. *„Až to budeš mít hotové, dej mi vědět a koukneme se na další krok.“*).
               - Pokud jde o rychlé focení nebo odpověď na dotaz, tuto větu nepřidávej.
            """
            
            contents = [plny_prompt]
            if img_obj:
                contents.append(img_obj)
            
            ai_reply = None
            max_pokusu = 3
            
            for pokus in range(max_pokusu):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=contents
                    )
                    ai_reply = response.text
                    break
                except Exception as e:
                    error_str = str(e)
                    if pokus == max_pokusu - 1:
                        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                            ai_reply = "⚠️ Vyčerpán bezplatný limit požadavků pro tento den. Zkus to prosím za chvíli znovu."
                        else:
                            ai_reply = f"Omlouvám se, server je teď plně vytížený. Zkus zprávu za chvíli zopakovat. (Chyba: {e})"
                    else:
                        time.sleep(2)

            with st.chat_message("assistant"):
                st.markdown(ai_reply)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
