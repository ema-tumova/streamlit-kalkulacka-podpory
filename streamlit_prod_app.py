import streamlit as st
import pandas as pd

st.header("Kalkulačka podpory v nezaměstnanosti :memo:")

st.write("Na této stránce si můžete vypočítat, kolik by činila Vaše podpora v nezaměstnanosti v roce 2026.\n\n" \
"Disclaimer: Jedná se o zjednodušený model. Více o podmínkách podpory naleznete přímo na webu Úřadu práce: https://up.gov.cz/")

vek_input = st.number_input(
    "Věk:", min_value=18, max_value=120, value=None, placeholder="Vyplňte věk..."
    )
prijem_input = st.number_input(
    "Čistý příjem v posledním ukončeném zaměstnání:", min_value=0, max_value=1000000, value=None, placeholder="Vyplňte příjem..."
    )

# ROK 2026
max_podpora_2026 = 38537 # max. 0,8násobek průměrné mzdy v národním hospodářství za 1. až 3. čtvrtletí předcházejícího roku
schema_perc_2026 = [0.8,0.5,0.4] # Podpora se s časem snižuje: 80 % příjmu, poté 50 %, nakonec 40 %.
schema_mesice_2026 = [[2,2,1],[3,3,2],[3,3,5]] # Ve třech věkových pásmech je odlišná délka a rozložení podpory po měsících.
vek_lim_1_2026 = 52 # dolní věkové omezení 2. pásma
vek_lim_2_2026 = 57 # horní věkové omezení 2. pásma

# ROK 2025
max_podpora_2025 = 26163 # 0,58násobek průměrné mzdy
schema_perc_2025 = [0.65,0.5,0.45]
schema_mesice_2025 = [[2,2,1],[2,2,4],[2,2,7]]
vek_lim_1_2025 = 50
vek_lim_2_2025 = 55


def vypocita_mesice_proc_schema(vek:int, vek_lim_1:int ,vek_lim_2:int, schema_perc:list, schema_mesice:list) -> list:
# Na základě věku vrátí seznam seznamů, které obsahují vždy číslo měsíce a procenta pro výpočet podpory za daný měsíc.
    schema_podpory = []

    if vek < vek_lim_1: # věk pod 1. limitem
        for mesic,perc in zip(schema_mesice[0],schema_perc):
            schema_podpory.extend(mesic*[perc])
    
    elif vek in range(vek_lim_1, vek_lim_2 + 1): # věk od 1. limitu do 2. limitu (včetně)
        for mesic,perc in zip(schema_mesice[1],schema_perc):
            schema_podpory.extend(mesic*[perc])
    
    else: # věk nad 2. limitem
        for mesic,perc in zip(schema_mesice[2],schema_perc):
            schema_podpory.extend(mesic*[perc])
    for poradi,polozka in enumerate(schema_podpory):
        schema_podpory[poradi] = [poradi+1,polozka]
    
    return schema_podpory


def prida_castky_a_puvodni_prijem(schema_podpory:list, prijem:int, max_podpora:int) -> list:
# K seznamům připojí konkrétní částky podpory a přidá na začátek záznam se zadaným příjmem.
    
    # dopočítá částku podpory pro každý měsíc
    for udaj in schema_podpory:
        podpora = int(prijem * udaj[1])
        if podpora <= max_podpora:
            udaj.append(podpora)
        else:
            udaj.append(max_podpora)

    # přidá na začátek záznam pro srovnání stavu před podporou (plný příjem)
    schema_podpory.insert(0,["Původní příjem",1,prijem])

    return schema_podpory


def vypocita_cele_schema(vek:int, vek_lim_1:int ,vek_lim_2:int, schema_perc:list, schema_mesice:list, prijem:int, max_podpora:int) -> list:
# Spojí předchozí funkce dohromady pro výpočet finálního schématu.
    schema_prvni = vypocita_mesice_proc_schema(vek,vek_lim_1,vek_lim_2,schema_perc,schema_mesice)
    schema_final = prida_castky_a_puvodni_prijem(schema_prvni,prijem,max_podpora)
    return schema_final


# ZOBRAZENÍ VÝSTUPŮ V APLIKACI
if st.button("Vypočítat"): # Pokud zmáčkne tlačítko, vypočítá se podpora.
    # výpočet hodnot
    schema_podpory_2026 = vypocita_cele_schema(vek_input,vek_lim_1_2026,vek_lim_2_2026,schema_perc_2026,schema_mesice_2026,
                                               prijem_input,max_podpora_2026)
    delka_podpory_2026 = len(schema_podpory_2026) - 1 # bez záznamu 'před nezaměstnaností'
    schema_podpory_2025 = vypocita_cele_schema(vek_input,vek_lim_1_2025,vek_lim_2_2025,schema_perc_2025,schema_mesice_2025,
                                               prijem_input,max_podpora_2025)
    
    st.write(f"V roce 2026 máte nárok na **{delka_podpory_2026} měsíců** podpory.")

    # vytvoření pandas df
    df_podpora_2026 = pd.DataFrame(schema_podpory_2026, columns=["Měsíc","Procenta příjmu","Částka pro rok 2026"]).drop(columns=["Procenta příjmu"])
    df_podpora_2025 = pd.DataFrame(schema_podpory_2025, columns=["Měsíc","Procenta příjmu","Částka pro rok 2025"]).drop(columns=["Procenta příjmu"])
    # V roce 2025 trvala podpora vždy stejně dlouho nebo déle než v roce 2026 (pro stejný věk). Proto k ní potenciálně kratší tabulku (2026)
    # připojím LEFT joinem:
    df_podpora_oba_roky = pd.merge(df_podpora_2025, df_podpora_2026, on="Měsíc", how="left")
    
    # vizualizace
    st.header("Porovnání podpory 2025 vs. 2026", text_alignment="center")
    st.bar_chart(data=df_podpora_oba_roky, x="Měsíc", sort=False, stack=False, color=["#afeeee","#13bdac"])

    # detailní výpis částek pro každý měsíc (2026)
    st.write("V grafu také vidíte, kolik by byla Vaše podpora v roce 2025.\n\n" \
            "V roce 2026 je to:")
    detail_mesice_podpory = ""
    for i in schema_podpory_2026[1:]: # bez záznamu 'před nezaměstnaností'
        castka_mezery = "{:,}".format(i[2]).replace(","," ") # v částce oddělím tisíce mezerou
        detail_mesice_podpory += f"\t{i[0]}. měsíc: {castka_mezery} Kč\n"
    st.write(detail_mesice_podpory)