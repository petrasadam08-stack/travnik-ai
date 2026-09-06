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
                    img_obj.thumbnail((1024, 1024))
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

            Pravidla pro odpověď:
            1. **Běžná konverzace / Pozdravy / Poděkování:** Odpověz přátelsky, stručně, s trávníkovou tématikou.
            2. **Diagnostika:** Vyhodnoť situaci a pokud je to pro diagnózu nejlepší, rovnou si řekni o fotku.
            3. **Situace "Nemůžu teď fotit":** Pokud uživatel hlásí, že fotit nemůže, přejdi na slovní popis.
            4. **Manuální vs. Strojové řešení:** 
               - Pokud lze činnost provést jak ručně, tak strojově, **vždy nabídni obě varianty** (např. variantu A a variantu B).
            5. **ČEKACÍ FÁZE A PRŮBĚŽNÁ PÉČE (DŮLEŽITÉ):** 
               - Jakmile uživatel dokončí náročnější zásah (hnojení, aerifikace, postřik, vertikutace), **zakaž AI vymýšlet hned další radikální kroky**. 
               - Místo toho AI vyhlásí klidový režim (např. *„Teď musíme nechat trávník a hnojivo/půdu pár dní v klidu, než to zabere.“*).
               - **Zároveň ale uživateli na dotaz (nebo preventivně) normálně dál radíš s běžnou údržbou** – to znamená, že naprosto v klidu a detailně vysvětlíš, jak má teď probíhat zálivka (kolik litrů na metr, jak často), jak sekat, dokud tráva regeneruje.
            6. **Jediný úkol a variabilita:** 
               - Vždy dávej **pouze jeden hlavní krok** nebo se drž probíhající údržby.
               - Větu s úkolem uvoď přirozenou výzvou, kterou **obměňuj** (*„Teď udělej tohle:“*, *„Vrhni se na tohle:“*, atd.).
            7. **Konkrétní rozměry a hodnoty:** Uváděj přesné parametry (hloubka, rozteče, gramáž, litry zálivky).
            8. **Fyzické akce:** Pokud zadáváš úkol vyžadující delší práci, přidej pokyn, ať se ozve, až to bude hotové.
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
                    if response and response.text:
                        ai_reply = response.text
                        break
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        ai_reply = "⚠️ Vyčerpán bezplatný limit požadavků pro tento den. Zkus to prosím za chvíli znovu."
                        break
                    if pokus == max_pokusu - 1:
                        ai_reply = "Rozumím. Koukám na podklady, pojďme pokračovat – co přesně vnímáš jako hlavní změnu na trávníku?"
                    else:
                        time.sleep(1.5)

            with st.chat_message("assistant"):
                st.markdown(ai_reply)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
