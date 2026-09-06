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
    
    if "last_photo_name" not in st.session_state:
        st.session_state.last_photo_name = None

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

    # Detekce, zda jde o ÚPLNĚ NOVOU fotku, kterou uživatel právě vybral
    current_photo_name = fotka.name if fotka else None
    is_brand_new_photo = current_photo_name and (current_photo_name != st.session_state.last_photo_name)

    if odpoved_uzivatele or is_brand_new_photo or tlacitko_bez_fotky_stisknuto:
        if tlacitko_bez_fotky_stisknuto:
            user_content = "Nemůžu teď fotit (je tma / nemám u sebe foťák). Můžeme pokračovat bez fotky popisem?"
            img_obj = None
        else:
            user_content = odpoved_uzivatele if odpoved_uzivatele else "Posílám vyžádanou fotku."
            
            img_obj = None
            if is_brand_new_photo:
                img_obj = Image.open(fotka)
                st.session_state.last_photo_name = current_photo_name

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

            Jsi zkušený agronomický kouč. Mluv přímo v ty-formě ("Vezmi", "Udělej", "Napiš mi").

            PRAVIDLA PRO ODPOVĚĎ:
            1. **Běžná konverzace / Pozdravy / Poděkování:** Pokud uživatel píše jen obecnou věc, odpověz přátelsky, stručně, s lehkou trávníkovou tématikou.
            2. **Fyzické testy (bez fotky):** U úkolů jako test šroubovákem, zkouška pevnosti kořenů tahem apod. fotku **nevyžaduj**, ptej se slovně na odpor nebo chování trávníku.
            3. **Vizuální detaily (s fotkou):** Pokud jde o chorobu, skvrny nebo barva stébel, vyzvěď fotku. 
            4. **Situace "Nemůžu teď fotit":** Pokud uživatel hlásí, že fotit nemůže, vyhodnoť to a zkus pokračovat slovně.
            5. **ZVÝRAZNĚNÍ ÚKOLU (VELMI DŮLEŽITÉ):** Vždy, když uživateli zadáváš konkrétní praktický úkol (např. píchnout šroubovák, udělat řez rýčem, vyfotit stébla), musíš větu nebo odstavec s tímto úkonem začít přesnou frází **"Teď udělej tohle:"**. 
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
