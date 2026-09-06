import time
from datetime import date
import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Trávníkový Průvodce", page_icon="🌱", layout="centered")

st.title("🌱 Osobní Trávníkový Průvodce – Verze 3")
st.caption("Inteligentní agronomický kouč s časovou osou a pamětí")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chybí Gemini API klíč v Secrets ve Streamlitu!")
else:
    client = genai.Client(api_key=api_key)
    
    # Inicializace stavu chatu a strukturované časové osy (paměti)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "timeline" not in st.session_state:
        st.session_state.timeline = [
            {"date": str(date.today()), "action": "Založení deníku / Start péče", "note": "Počáteční stav trávníku."}
        ]

    if "last_sent_photo_name" not in st.session_state:
        st.session_state.last_sent_photo_name = None

    # Postranní panel nebo záložka pro přehled časové osy
    with st.expander("📅 Zahradní deník & Časová osa zásahů"):
        st.write("Tady vidíš historii klíčových akcí, ze kterých čerpá AI paměť:")
        for idx, item in enumerate(st.session_state.timeline):
            st.markdown(f"**{item['date']}** – `{item['action']}`: {item['note']}")

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

        with st.spinner("Kouč vyhodnocuje data a počasí..."):
            
            # Sestavení paměti z časové osy pro AI
            historie_casove_osy = "\n".join([f"- {i['date']}: {i['action']} ({i['note']})" for i in st.session_state.timeline])
            
            historie_text = f"Fáze trávníku: {krok}\n\nČASOVÁ OSA HISTORIE ZÁSAHŮ:\n{historie_casove_osy}\n\n"
            for m in st.session_state.messages[:-1]:
                historie_text += f"{m['role'].upper()}: {m['content']}\n"
            
            plny_prompt = f"""
            {historie_text}
            USER (aktuální zpráva): {user_content}

            Jsi zkušený agronomický kouč. Mluv přímo v ty-formě ("Vezmi", "Udělej", "Napiš mi"). Mluv věcně, stručně a vynechávej prázdná klišé.

            Pravidla pro odpověď:
            1. **Využití časové osy a počasí:** Vždy zohledni, kdy proběhlo poslední hnojení nebo zásah (viz časová osa). Vyhodnoť stav a případně doporuč další krok na základě uplynulého času. (Simuluj, že bereš v úvahu aktuální srážky a teploty pro zálivku a rozpuštění hnojiva).
            2. **Automatický zápis do deníku:** Pokud uživatel hlásí, že dokončil nějakou významnou práci (hnojení, aerifikace, vertikutace, postřik), přidej na samý začátek své odpovědi skrytý příkaz v tomto přesném formátu: `[ZAPIS:Název akce|Stručný popis]`. Aplikace ho detekuje a sama uloží do časové osy.
            3. **Běžná konverzace / Diagnostika / Nemůžu fotit:** Reaguj přátelsky, stručně, popřípadě si řekni o fotku nebo přejdi na slovní popis.
            4. **Manuální vs. Strojové řešení:** Pokud lze činnost provést ručně i strojově, vždy nabídni obě varianty.
            5. **ČEKACÍ FÁZE A PRŮBĚŽNÁ PÉČE:** Po náročném zásahu vyhlásit klidový režim (nechat působit), ale na dotaz dál radit s běžnou údržbou (zálivka, sečení).
            6. **Jediný úkol, hodnoty a fyzické akce:** Dávej pouze jeden hlavní krok s přesnými parametry (hloubka, rozteče, gramáž, litry zálivky) a výzvou k hlášení po dokončení.
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

            # Automatické parethování a zápis do časové osy, pokud AI vrátila značku [ZAPIS:...]
            if ai_reply and "[ZAPIS:" in ai_reply:
                try:
                    start_idx = ai_reply.find("[ZAPIS:") + 7
                    end_idx = ai_reply.find("]", start_idx)
                    zapis_content = ai_reply[start_idx:end_idx]
                    casti = zapis_content.split("|")
                    akce_nazev = casti[0]
                    akce_popis = casti[1] if len(casti) > 1 else "Provedeno na základě pokynu."
                    
                    # Přidání do session state časové osy
                    st.session_state.timeline.append({
                        "date": str(date.today()),
                        "action": akce_nazev,
                        "note": akce_popis
                    })
                    
                    # Odstranění tagu z textu, který vidí uživatel
                    ai_reply = ai_reply.replace(f"[ZAPIS:{zapis_content}]", "").strip()
                except Exception:
                    pass

            with st.chat_message("assistant"):
                st.markdown(ai_reply)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
