import time
from datetime import date
import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Trávníkový Průvodce", page_icon="🌱", layout="centered")

st.title("🌱 Osobní Trávníkový Průvodce – Verze 3.6")
st.caption("Inteligentní agronomický kouč s aktivním vstupním hodnocením")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chybí Gemini API klíč v Secrets ve Streamlitu!")
else:
    client = genai.Client(api_key=api_key)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "timeline" not in st.session_state:
        st.session_state.timeline = [
            {"date": str(date.today()), "action": "Založení deníku / Start péče", "note": "Počáteční stav trávníku."}
        ]

    if "last_sent_photo_name" not in st.session_state:
        st.session_state.last_sent_photo_name = None

    if "onboarding_done" not in st.session_state:
        st.session_state.onboarding_done = False

    # --- ÚVODNÍ ONBOARDING OKNO ---
    if not st.session_state.onboarding_done:
        st.markdown("### 🌿 Vítej v Zahradním Kouči!")
        st.write("Než začneme, nastavíme tvůj trávník. Aplikace funguje tak, že **všechny zásahy provádíš primárně na výzvu kouče**, abys nic nezanedbal.")
        
        with st.form("onboarding_form"):
            stav_travniku = st.selectbox(
                "1. V jakém stavu je tvůj trávník?",
                [
                    "Ještě není založený (chci ho zasít)",
                    "Zasel jsem ho nedávno (před pár týdny)",
                    "Je to zavedený, dlouholetý trávník"
                ]
            )
            
            rezim_startu = st.selectbox(
                "2. Jaký je tvůj hlavní cíl pro nejbližší dobu?",
                [
                    "Standardní údržba (chci hlídat zálivku a pravidelné hnojení)",
                    "Akutní řešení problému (trávník neroste / má žlutá místa / chorobu)"
                ]
            )

            frekvence_zalivky = st.selectbox(
                "3. Jak často jsi dosud zálivku prováděl?",
                [
                    "Nepravidelně / podle pocitu",
                    "Pravidelně (cca 2–3x týdně)",
                    "Každý den / téměř denně"
                ]
            )

            st.write("4. **Nahraj aktuální fotku trávníku** (pro vstupní diagnostiku):")
            init_foto = st.file_uploader("Počáteční foto trávníku", type=["jpg", "jpeg", "png"], key="onboarding_photo_input")
            
            submit_onboarding = st.form_submit_button("Spustit aplikaci a zahájit péči 🚀")
            
            if submit_onboarding:
                st.session_state.onboarding_done = True
                st.session_state.stav_travniku = stav_travniku
                st.session_state.rezim_startu = rezim_startu
                st.session_state.frekvence_zalivky = frekvence_zalivky
                
                init_img_obj = None
                if init_foto is not None:
                    init_img_obj = Image.open(init_foto)
                    init_img_obj.thumbnail((1024, 1024))
                    st.session_state.last_sent_photo_name = init_foto.name
                
                st.session_state.timeline.append({
                    "date": str(date.today()),
                    "action": "Vstupní profil",
                    "note": f"Stav: {stav_travniku}, Cíl: {rezim_startu}, Dosavadní zálivka: {frekvence_zalivky}"
                })

                # Pokyn pro AI hned při startu, aby se aktivně chytilo fotky a profilu
                if "Akutní řešení" in rezim_startu:
                    init_prompt = f"""Uživatel právě spustil aplikaci v režimu AKUTNÍ ŘEŠENÍ. 
- Stav trávníku: {stav_travniku}
- Dosavadní zálivka: {frekvence_zalivky}

Jsi zkušený agronomický kouč. Podívej se na jeho úvodní fotku, zhodnoť zdravotní stav trávníku, pojmenuj problém a hned mu řekni PRVNÍ KONKRÉTNÍ KROK, co musí bezodkladně udělat k nápravě. Mluv přímo v ty-formě ("Vezmi", "Udělej")."""
                else:
                    init_prompt = f"""Uživatel právě spustil aplikaci v REŽIMU STANDARDNÍ ÚDRŽBA. 
- Stav trávníku: {stav_travniku}
- Dosavadní zálivka: {frekvence_zalivky}

Jsi zkušený agronomický kouč. Podívej se na jeho úvodní fotku, zhodnoť, zda trávník vypadá zdravě, a jasně mu řekni, co teď MŮŽE nebo NEMUSÍ dělat (zda je vše v pořádku a může jen odpočívat, nebo jestli je potřeba něco drobně upravit). Mluv přímo v ty-formě."""

                with st.spinner("Kouč analyzuje vstupní fotku a data trávníku..."):
                    contents = [init_prompt]
                    if init_img_obj:
                        contents.append(init_img_obj)
                    
                    try:
                        resp = client.models.generate_content(
                            model="gemini-3.1-flash-lite",
                            contents=contents
                        )
                        inicialni_text = resp.text if resp and resp.text else "Zaregistroval jsem tvá vstupní data. Pojďme se pustit do péče o trávník!"
                    except Exception:
                        inicialni_text = "Zaregistroval jsem vstupní data i fotku. Vypadá to dobře, jdeme na to!"

                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": inicialni_text, 
                    "image": init_img_obj
                })
                st.rerun()

    # --- HLAVNÍ APLIKACE ---
    else:
        with st.expander("📅 Zahradní deník & Časová osa zásahů"):
            st.write("Tady vidíš historii klíčových akcí, ze kterých čerpá AI paměť:")
            for idx, item in enumerate(st.session_state.timeline):
                st.markdown(f"**{item['date']}** – `{item['action']}`: {item['note']}")

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

            with st.spinner("Kouč vyhodnocuje data..."):
                
                historie_casove_osy = "\n".join([f"- {item['date']}: {item['action']} ({item['note']})" for item in st.session_state.timeline])
                
                profil_info = f"""ÚVODNÍ PROFIL TRÁVNÍKU:
- Stav trávníku: {st.session_state.get('stav_travniku', 'Nezadáno')}
- Hlavní cíl / režim: {st.session_state.get('rezim_startu', 'Nezadáno')}
- Dosavadní zálivka uživatele: {st.session_state.get('frekvence_zalivky', 'Nezadáno')}

"""
                
                historie_text = f"{profil_info}ČASOVÁ OSA HISTORIE ZÁSAHŮ:\n{historie_casove_osy}\n\n"
                for m in st.session_state.messages[:-1]:
                    historie_text += f"{m['role'].upper()}: {m['content']}\n"
                
                plny_prompt = f"""
                {historie_text}
                USER (aktuální zpráva): {user_content}

                Jsi zkušený agronomický kouč. Mluv přímo v ty-formě ("Vezmi", "Udělej", "Napiš mi"). Mluv věcně, stručně a vynechávej prázdná klišé.

                Pravidla pro odpověď:
                1. **Respektuj odpor uživatele k úkolům:** Pokud uživatel odmítne nějaký složitý test (např. měření kelímky) nebo napíše, že se mu to nechce dělat:
                   - **Nikdy ho nenutť ani nekomentuj jeho lenost.** 
                   - Okamžitě úkol zruš, nabídni rozumný odhad nebo univerzální bezpečný standard a posuň se bez řečí v péči dál.
                2. **Pracuj s úvodním profilem:** Zohledni stav trávníku a dosavadní zálivku.
                3. **Přísná pravidla pro zápis do časové osy (`[ZAPIS:...`):** 
                   - Tag `[ZAPIS:Název akce|Stručný popis]` použij **výhradně** tehdy, když uživatel explicitně hlásí, že dokončil reálnou, velkou fyzickou agronomickou práci (např. *Hnojení*, *Aerifikace*, *Vertikutace*, *Výsev*, *Postřik*). 
                   - **Nikdy nezapisuj** obyčejné dotazy, konverzace ani odmítnutí úkolů.
                4. **ABSOLUTNĚ JEDEN ÚKOL NA JEDNU ZPRÁVU (PŘÍSNÉ PRAVIDLO):** 
                   - Dávej vždy **pouze JEDINÝ, atomický krok**. 
                   - **Nikdy nekombinuj více pokynů do jedné zprávy!**
                5. **Manuální vs. Strojové řešení:** Pokud daný úkol lze provést ručně i strojově, nabídni obě varianty (A/B).
                6. **Fyzické akce a čekání:** Po zadání úkolu přidej pokyn, ať se uživatel ozve, až to bude mít hotové. Nech trávník odpočívat.
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

                if ai_reply and "[ZAPIS:" in ai_reply:
                    try:
                        start_idx = ai_reply.find("[ZAPIS:") + 7
                        end_idx = ai_reply.find("]", start_idx)
                        zapis_content = ai_reply[start_idx:end_idx]
                        casti = zapis_content.split("|")
                        akce_nazev = casti[0]
                        akce_popis = casti[1] if len(casti) > 1 else "Provedeno na základě pokynu."
                        
                        st.session_state.timeline.append({
                            "date": str(date.today()),
                            "action": akce_nazev,
                            "note": akce_popis
                        })
                        
                        ai_reply = ai_reply.replace(f"[ZAPIS:{zapis_content}]", "").strip()
                    except Exception:
                        pass

                with st.chat_message("assistant"):
                    st.markdown(ai_reply)
                
                st.session_state.messages.append({"role": "assistant", "content": ai_reply, "image": img_obj if 'img_obj' in locals() else None})
                st.rerun()
