# Sandisolar HA 9.2.0 – opravy a diagnostika

## Změny oproti 9.1.0
- Opraveno mapování Input 423 (Energy Bought Today) a 425 (Energy Bought Total).
- Opraveno mapování Holding 219/220/221/222:
  - 219 = SecEPS ON SOC (měřítko 0.01)
  - 220 = SecEPS ON Vbat (0.1 V)
  - 221 = SecEPS OFF SOC (0.01)
  - 222 = SecEPS OFF Vbat (0.1 V)
- Nové diagnostické entity pro Input 32 (Fault Main Code) a 34 (Fault Sub Code).
- Nový Fault Main Text kombinuje kód a podkód, například 203(1).
- Nové surové registry Fault Word1–7 (Input 25–31) a BMS Error1–4 (Input 131–134).
- Fault History uchovává posledních 20 událostí zachycených při pravidelném pollingu; obnova z HA Restore State po restartu.
- Stávající entity a jejich unique_id jsou zachovány.

## Omezení
- Význam podkódu 203(1) není ověřen. Kód 203 je překládán jako přetížení ostrovního výstupu.
- Fault Word0 je podle protokolu bitové slovo, zatímco starší entita Fault Word0 Text jej interpretuje jako kód; pro skutečný kód používejte novou Fault Main Text.
- Historie zaznamená pouze události zachycené pollingem, nikoli kompletní interní historii měniče (funkce 0x29 zatím není implementována).
- Grid Power (Input 328) může představovat exportní výkon, nikoli obousměrný výkon sítě. Bez surových měření není mapování měněno.
- GEN Port Work Mode = 2700 není automaticky mapován na volbu 6 bez ověření zařízení.
- BMS FCC/RM a výpočty z nich nejsou v této verzi měněny.
- Nejde o testované nasazení na fyzickém měniči. Před použitím ovládání SecEPS ověřte čtené hodnoty.
- Pokud už Home Assistant uložil chybné dlouhodobé statistiky pro Energy Bought, samotná změna adres je automaticky neopraví.

## Instalace
1. Zálohujte konfiguraci Home Assistantu.
2. Zkopírujte složku custom_components/sandisolar_modbus_rtu do /config/custom_components/.
3. Restartujte Home Assistant.
4. Ověřte nové entity Fault Main Code, Fault Sub Code, Fault Main Text a Fault History.
5. Před zápisy do SecEPS ověřte, že ON/OFF SOC i ON/OFF Vbat odpovídají displeji měniče.
