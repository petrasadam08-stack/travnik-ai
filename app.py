import json
import time
import urllib.parse
import urllib.request
from datetime import date
import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Trávníkový Průvodce", page_icon="🌱", layout="centered")

st.title("🌱 Osobní Trávníkový Průvodce – Verze 3.14")
st.caption("Inteligentní agronomický kouč – živé počasí, ověřené postupy ČR a srozumitelné kroky")

# --- OVĚŘENÁ AGRONOMICKÁ ZÁKLADNA (METODIKA ČR / STŘEDNÍ EVROPA) ---
AGRONOMICKA_BAZE_ZNALOSTI = """
OVĚŘENÉ ZÁSADY PÉČE O TRÁVNÍK V ČR (ČZU / METODIKA TRÁVNÍKÁŘSTVÍ / REGISTR ÚKZÚZ):

1. POVINNÝ DIAGNOSTICKÝ PROTOKOL (NEŽ VYSLOVÍŠ DIAGNÓZU):
- Hnědé nebo žluté skvrny na fotce mají 3 nejčastější příčiny, které vypadají téměř stejně:
  a) Lokální sucho / nerovnoměrný dosah zálivky,
  b) Popálení hnojivem nebo močí,
  c) Houbová choroba (např. plíseň sněžná, kornatka, padání klíčků).
- NIKDY nestřílej finální diagnózu choroby hned z jedné fotky a NIKDY v první zprávě neposílej uživatele kupovat chemii.
- Nejdřív nechej uživatele udělat rychlé ověření na místě (např. zapíchnout prst nebo šroubovák do hlíny přímo v suchém místě pro zjištění vlhkosti a zhutnění, nebo zkontrolovat zblízka stébla, zda na nich je bílý/růžový povlak či sliz).

2. LEGISLATIVA ČR A POUŽITÍ CHEMIE:
- V ČR a EU je většina silných fungicidů (zejména přípravky běžné v USA) pro hobby zahrady zakázaná nebo nedostupná.
- NIKDY nedoporučuj neregistrované postřiky ani neuváděj obecné výzvy „kup si jakýkoliv fungicid“.
- Základem nápravy v ČR jsou pěstební opatření (úprava režimu zálivky, provzdušnění, úprava výšky seče, vyvážená výživa) a v ČR legálně dostupné pomocné či biologické přípravky (např. mykoparazitická houba Pythium oligandrum – např. Polyversum, nebo hnojiva se zvýšeným obsahem draslíku pro posílení pletiv).

3. OVĚŘENÉ PĚSTEBNÍ ZÁSADY A PRÁCE S POČASÍM:
- Zálivka: Zavedený trávník se zalévá méně často, ale vydatně (cca 15–20 l/m² jednou za 3–4 dny podle počasí), aby voda pronikla ke kořenům do 10–15 cm. Zalévá se výhradně ráno nebo dopoledne, aby listy do večera oschly (prevence plísní). Pouze čerstvý výsev do vzejití se udržuje vlhký na povrchu častějšími malými dávkami.
- Reakce na srážky a teplotu (POVINNÉ): Vždy zkontroluj data z počasí. Pokud za poslední 2–3 dny spadlo přes 10–15 mm srážek nebo se v příštích 24 hodinách čeká vydatný déšť, zálivku odlož. V chladnějším počasí (pod 15 °C) NIKDY nedoporučuj odpolední ani večerní zálivku – pouze ranní.
- Zimní klid a mráz: Pokud se denní maxima dlouhodobě drží pod 8 °C a noční teploty klesají k 0 °C nebo pod bod mrazu, trávník je ve vegetačním klidu (neroste). V mrazu nebo před mrazivou nocí se NESMÍ zalévat, hnojit ani sekat (hrozí poškození pletiv a plíseň sněžná).
- Sečení: Platí pravidlo jedné třetiny (nikdy neuseknout víc než 1/3 délky stébla najednou). Běžná výška je 3,5–5 cm, v horku a suchu zvednout na 5–6 cm. Roztřepené, našedlé konečky listů znamenají tupý nůž sekačky, nikoli chorobu.
- Výživa (NPK): Jaro až léto: hnojiva s vyšším podílem dusíku (N) pro růst a hustotu (účinek běžného hnojiva je 4–8 týdnů). Pozdní léto a podzim (od září): podzimní hnojiva se sníženým dusíkem a vysokým draslíkem (K) pro vyzrávání pletiv a odolnost proti vymrzání a plísni sněžné (nikdy na podzim nedávat čistě dusíkatá jarní hnojiva). Čerstvý výsev hnojit jen speciálním startovacím hnojivem s fosforem (P).
- Mech: Není primárně choroba, ale důsledek stínu, utužené půdy, příliš nízkého sečení nebo hladovění trávníku. Řeší se úpravou podmínek a provzdušněním.

4. AERIFIKACE VS. VERTIKUTACE (BEZPEČNÉ PROVZDUŠNĚNÍ):
- PŘÍSNÝ ZÁKAZ VERTIKUTACE U MLADÝCH TRÁVNÍKŮ: Pokud byl trávník zasetý před méně než 1 rokem, NIKDY nedoporučuj vertikutaci (ani ručními vertikutačními hráběmi). Mladé rostliny nemají prokořeněný drn a nože by je vytrhaly. Vertikutace patří jen na starší, plně zapojený trávník.
- Šetrné provzdušnění (aerifikace vidlemi) pro zhutnělou půdu: Použijí se obyčejné rycí vidle. Zapíchnou se kolmo dolů do hloubky 10–15 cm, topůrkem se jen lehce zakýve o 2–3 cm dopředu a dozadu (tím se v hlíně otevře kanálek pro vodu a vzduch) a vidle se vytáhnou rovně nahoru BEZ páčení hlíny nahoru, aby se nepotrhaly kořínky a nezničila rovina.
"""

@st.cache_data(ttl=1800, show_spinner=False)
def ziskej_pocasi(mesto: str) -> str:
    """Stáhne zdarma aktuální teplotu, srážky za poslední 3 dny a předpověď z Open-Meteo."""
    if not mesto or not mesto.strip():
        return "Lokalita nebyla zadána, AI vychází z obecného ročního období v ČR."
    try:
        encoded_city = urllib.parse.quote(mesto.strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=cs&format=json"
        with urllib.request.urlopen(geo_url, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))

        if not geo_data.get("results"):
            return f"Lokalitu '{mesto}' se nepodařilo najít, AI vychází z obecného ročního období v ČR."

        loc = geo_data["results"][0]
        lat = loc["latitude"]
        lon = loc["longitude"]
        nazev_mista = loc.get("name", mesto)

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,precipitation"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&past_days=3&forecast_days=5&timezone=auto"
        )
        with urllib.request.urlopen(weather_url, timeout=5) as resp:
            w_data = json.loads(resp.read().decode("utf-8"))

        akt_teplota = w_data.get("current", {}).get("temperature_2m", "?")
        daily = w_data.get("daily", {})
        dates = daily.get("time", [])
        t_max = daily.get("temperature_2m_max", [])
        t_min = daily.get("temperature_2m_min", [])
        rain = daily.get("precipitation_sum", [])

        radky = [f"**Lokalita:** {nazev_mista} | **Aktuální teplota:** {akt_teplota} °C"]
        dnes_str = str(date.today())

        minule = []
        budouci = []
        for d, mx, mn, r in zip(dates, t_max, t_min, rain):
            zaznam = f"- {d}: {mn} až {mx} °C, srážky {r} mm"
            if d < dnes_str:
                minule.append(zaznam)
            else:
                budouci.append(zaznam)

        if minule:
            radky.append("**Srážky a teploty za poslední dny:**\n" + "\n".join(minule))
        if budouci:
            radky.append("**Předpověď (dnes a další dny):**\n" + "\n".join(budouci))

        return "\n\n".join(radky)
    except Exception as e:
        return f"Data o počasí se teď nepodařilo načíst ({e}), AI vychází z data v kalendáři."


def zavolej_gemini(client, contents):
    """Zkusí hlavní model, při přetížení (503) počká a případně přepne na záložní model."""
    modely = ["gemini-3.1-flash-lite", "gemini-3.6-flash"]
    for model_name in modely:
        for pokus in range(2):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if resp and resp.text:
                    return resp.text, None
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    return None, "⚠️ Vyčerpán bezplatný limit požadavků API. Zkus to prosím za minutku znovu."
                if "503" in err or "UNAVAILABLE" in err or "500" in err:
                    time.sleep(1.5)
                    continue
                break
    return None, "⚠️ Servery AI jsou teď dočasně přetížené (chyba 503). Zkus to prosím za pár vteřin znovu."


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

            posledni_hnojeni = st.selectbox(
                "4. Před jakou dobou jsi naposledy hnojil?",
                [
                    "Vůbec / letos ještě nehnojeno",
                    "V posledních 2 týdnech (čerstvě pohnojeno)",
                    "Před 3 až 6 týdny",
                    "Před 2 a více měsíci"
                ]
            )

            lokalita = st.text_input(
                "5. Město nebo obec (pro automatické sledování srážek a teplot):",
                value="Praha",
                placeholder="Např. Praha, Brno, Horní Počernice..."
            )

            dalsi_info = st.text_area(
                "6. Další doplňující informace pro kouče (volitelné):",
                placeholder="Např. velký stín ze stromů, pes na zahradě, robotická sekačka, problém s mechem...",
                height=80
            )

            st.write("7. **Nahraj aktuální fotku trávníku** (pro vstupní diagnostiku):")
            init_foto = st.file_uploader("Počáteční foto trávníku", type=["jpg", "jpeg", "png"], key="onboarding_photo_input")
            
            submit_onboarding = st.form_submit_button("Spustit aplikaci a zahájit péči 🚀")
            
            if submit_onboarding:
                dalsi_info_clean = dalsi_info.strip() if dalsi_info.strip() else "Žádné"
                lokalita_clean = lokalita.strip() if lokalita.strip() else "Praha"
                aktualni_pocasi = ziskej_pocasi(lokalita_clean)
                
                init_img_obj = None
                if init_foto is not None:
                    init_img_obj = Image.open(init_foto)
                    init_img_obj.thumbnail((1024, 1024))

                init_prompt = f"""Uživatel právě spustil aplikaci (dnešní datum: {date.today()}). 
- Stav trávníku: {stav_travniku}
- Cíl: {rezim_startu}
- Dosavadní zálivka: {frekvence_zalivky}
- Poslední hnojení: {posledni_hnojeni}
- Lokalita: {lokalita_clean}
- Další informace od uživatele: {dalsi_info_clean}

AKTUÁLNÍ DATA O POČASÍ V LOKALITĚ UŽIVATELE:
{aktualni_pocasi}

{AGRONOMICKA_BAZE_ZNALOSTI}

Jsi zkušený agronomický kouč pro české podmínky. Podívej se na úvodní fotku a zohledni všechny údaje z profilu uživatele i reálné počasí.
PŘÍSNÁ PRAVIDLA:
1. Vycházej z výše uvedených ověřených zásad a aktuálního počasí (teploty a srážky). Pokud jsou venkovní teploty pod 8 °C nebo hrozí mráz, respektuj zimní klid a nedoporučuj zálivku ani hnojení. Pokud narazíš na specifický problém mimo zásady, máš volnou ruku použít své obecné agronomické znalosti, ale vždy zohledni situaci uživatele a podmínky v ČR.
2. BEZPEČNÁ DIAGNOSTIKA: Pokud jsou na fotce žluté nebo hnědé skvrny, neříkej hned s jistotou, že jde o konkrétní chorobu, a NIKDY v této první zprávě nedoporučuj chemii (fungicidy). Nejdřív nechej uživatele ověřit stav na místě (např. kontrola vlhkosti hlíny prstem/šroubovákem v suchém místě nebo detail stébel), abyste vyloučili sucho či spálení hnojivem.
3. ŽÁDNÝ ODBORNÝ ŽARGON BEZ NÁVODU: Uživatel je laik. Nikdy mu jen neřekni odborný název úkonu (např. „udělej aerifikaci“ nebo „vertikutaci“). Vždy v 1–2 stručných větách napiš, co má vyloženě vzít do ruky a jak to udělat. Nepiš zbytečně dlouhé eseje (na detaily se uživatel případně doptá), ale základní provedení musí být hned jasné.
4. LIMIT ÚKOLŮ: Dej uživateli VŽDY MAXIMÁLNĚ 1 AŽ 2 KONKRÉTNÍ ÚKOLY (nikdy ne 3 a více úkolů najednou, uživatele to odradí!).
5. Respektuj údaj o posledním hnojení (pokud bylo hnojeno v posledních 2 týdnech, v žádném případě nedoporučuj další hnojení).
6. Nepřidávej na konec žádné další „tipy pro příště“ ani vedlejší otázky navíc.
7. Pokud je zvolena standardní údržba a trávník vypadá zdravě (nebo je v zimním klidu), klidně řekni, že teď nemusí dělat nic (maximálně 1 drobný udržovací krok).
8. Mluv přímo v ty-formě, stručně a věcně."""

                with st.spinner("Kouč analyzuje vstupní fotku, data a aktuální počasí..."):
                    contents = [init_prompt]
                    if init_img_obj:
                        contents.append(init_img_obj)
                    
                    inicialni_text, chyba_startu = zavolej_gemini(client, contents)

                if chyba_startu:
                    st.warning(chyba_startu)
                else:
                    st.session_state.onboarding_done = True
                    st.session_state.stav_travniku = stav_travniku
                    st.session_state.rezim_startu = rezim_startu
                    st.session_state.frekvence_zalivky = frekvence_zalivky
                    st.session_state.posledni_hnojeni = posledni_hnojeni
                    st.session_state.lokalita = lokalita_clean
                    st.session_state.dalsi_info = dalsi_info_clean
                    if init_foto is not None:
                        st.session_state.last_sent_photo_name = init_foto.name

                    st.session_state.timeline.append({
                        "date": str(date.today()),
                        "action": "Vstupní profil",
                        "note": f"Místo: {lokalita_clean}, Stav: {stav_travniku}, Cíl: {rezim_startu}, Zálivka: {frekvence_zalivky}, Hnojení: {posledni_hnojeni}, Poznámka: {dalsi_info_clean}"
                    })

                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": inicialni_text, 
                        "image": init_img_obj
                    })
                    st.rerun()

    # --- HLAVNÍ APLIKACE ---
    else:
        aktualni_lokalita = st.session_state.get("lokalita", "Praha")
        aktualni_pocasi = ziskej_pocasi(aktualni_lokalita)

        with st.expander(f"🌤️ Aktuální počasí a srážky ({aktualni_lokalita})"):
            st.markdown(aktualni_pocasi)

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

            with st.spinner("Kouč vyhodnocuje data a počasí..."):
                
                historie_casove_osy = "\n".join([f"- {item['date']}: {item['action']} ({item['note']})" for item in st.session_state.timeline])
                
                profil_info = f"""ÚVODNÍ PROFIL TRÁVNÍKU (dnešní datum: {date.today()}):
- Lokalita: {aktualni_lokalita}
- Stav trávníku: {st.session_state.get('stav_travniku', 'Nezadáno')}
- Hlavní cíl / režim: {st.session_state.get('rezim_startu', 'Nezadáno')}
- Dosavadní zálivka uživatele: {st.session_state.get('frekvence_zalivky', 'Nezadáno')}
- Poslední hnojení: {st.session_state.get('posledni_hnojeni', 'Nezadáno')}
- Další doplňující informace: {st.session_state.get('dalsi_info', 'Žádné')}

"""
                
                # Oříznutí na posledních 8 zpráv šetří tokeny a drží aplikaci v bezplatných limitech
                konverzace_historie = ""
                for m in st.session_state.messages[-8:]:
                    konverzace_historie += f"{m['role'].upper()}: {m['content']}\n"

                plny_prompt = f"""
{profil_info}
AKTUÁLNÍ DATA O POČASÍ V LOKALITĚ UŽIVATELE:
{aktualni_pocasi}

Časová osa:
{historie_casove_osy}

{AGRONOMICKA_BAZE_ZNALOSTI}

Poslední zprávy konverzace:
{konverzace_historie}

Jsi zkušený agronomický kouč pro české podmínky. Odpověz na poslední zprávu uživatele. 
Pravidla:
1. Vycházej z ověřených zásad péče výše (včetně zákazu vertikutace mladých trávníků do 1 roku) a VŽDY zohledni aktuální počasí (srážky za poslední dny, předpověď teplot a případný zimní klid pod 8 °C). Pokud je problém specifický a v zásadách chybí, máš volnou ruku použít své obecné agronomické znalosti, ale vždy zohledni situaci uživatele, jeho profil a podmínky v ČR.
2. BEZPEČNÁ DIAGNOSTIKA A ZÁKAZ ZAKÁZANÉ CHEMIE: Než vyslovíš diagnózu choroby, vždy si nejdřív ověř fakta na místě (vlhkost půdy, detail stébel, stav nože sekačky), abys vyloučil prosté sucho nebo chybu v údržbě. Nikdy nedoporučuj v ČR/EU zakázané nebo neregistrované postřiky; upřednostni pěstební úpravy a v ČR legálně dostupné přípravky.
3. ŽÁDNÝ ODBORNÝ ŽARGON BEZ NÁVODU: Uživatel je laik. Nikdy nepoužij jen odborný termín (např. „aerifikace“, „vertikutace“, „pískování“) bez okamžitého vysvětlení, co má uživatel reálně udělat. Ke každému úkonu přidej 1–2 stručné věty s konkrétním postupem (jaký nástroj vzít a jak s ním pracovat, např. zapíchnout vidle 10–15 cm kolmo, lehce zakývat a vytáhnout bez páčení). Nepiš dlouhé eseje (na detaily se uživatel doptá), ale musí přesně vědět, co má dělat.
4. Reaguj kontextuálně na to, co uživatel napsal, odpovídej na jeho otázky a neopakuj dokola stejné věty.
5. PŘÍSNÝ LIMIT ÚKOLŮ: V jedné zprávě dej uživateli VŽDY MAXIMÁLNĚ 1 AŽ 2 KONKRÉTNÍ ÚKOLY (ideálně 1, absolutní maximum jsou 2). Nikdy nevypisuj seznamy o 3 a více úkolech ani nepřidávej další „tipy navíc“ na konec, protože dlouhý seznam uživatele odradí.
6. Pokud uživatel odmítne nějaký složitější úkol nebo test, bez řečí to akceptuj, použij bezpečný odhad a posuň se dál.
7. Mluv v ty-formě, stručně a věcně.
8. Pokud uživatel hlásí dokončení velké akce (Hnojení, Výsev, Aerifikace, Vertikutace, Postřik), zapiš to do formátu [ZAPIS:Název akce|Popis]. Jinak tag nepoužívej.
"""
                
                contents = [plny_prompt]
                if img_obj:
                    contents.append(img_obj)
                
                ai_reply, chyba_chatu = zavolej_gemini(client, contents)
                if chyba_chatu:
                    ai_reply = chyba_chatu

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
                
                st.session_state.messages.append({"role": "assistant", "content": ai_reply, "image": None})
                st.rerun()
