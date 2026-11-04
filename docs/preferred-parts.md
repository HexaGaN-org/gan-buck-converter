# Preferred Parts

The passives and indicator parts every sheet should pick from first. Most are JLCPCB **Basic** parts, which carry no loading fee on Economic assembly; the rest are well-stocked **Extended** parts chosen so the team uses the same few part numbers everywhere.

> Checked against JLCPCB's catalog in November 2026. Stock changes, so confirm each part with the JLCPCB Tools plugin or on lcsc.com before ordering. See [jlcpcb-assembly.md](jlcpcb-assembly.md) for how library type affects cost.

---

## Rules

1. **Start here.** Choose a value from these tables before searching for anything else.
2. **0603 is the default size** for resistors and small capacitors. Use 0805 or 1206 only for power, voltage or capacitance that 0603 can't provide.
3. **Basic first, then Preferred Extended, then Extended.** Each unique Extended part costs a $3.07 loading fee per order on Economic assembly.
4. **Calculated values are the exception.** A divider or sense value that needs an exact resistance may use one Extended part. Don't combine two Basic resistors to reach a value.
5. **Derate ceramic capacitors from the curve, not the rating.** Choose a voltage rating of at least twice the working voltage, then read the manufacturer's DC-bias curve at your working voltage (Samsung product pages, Murata SimSurfing, TDK, KEMET K-SIM). Even at half its rated voltage, a 22 µF 25 V 1206 keeps only 26 % at 12 V. Prefer parts whose maker publishes the curve; the measured values for common parts are in the tables below.
6. **One 100 V capacitor family on the 48 V side.** No Basic ceramic suits the power loop, so pick one or two of the 100 V parts below and reuse them everywhere on the 48 V bus.
7. **Need something not listed?** Choose it, use it, and add it here in the same pull request so the next person finds it.

---

## Resistors: UNI-ROYAL thick film, 1 % (Basic)

| Size | MPN pattern | Power | Max voltage | Use for |
|---|---|---|---|---|
| 0402 | `0402WGF…TCE` | 62.5 mW | 50 V | Only where space demands it |
| **0603** | `0603WAF…T5E` | 100 mW | 75 V | **Default** |
| 0805 | `0805W8F…T5E` | 125 mW | 150 V | More power, or dividers from the 48 V bus |
| 1206 | `1206W4F…T5E` | 250 mW | 200 V | Highest power and voltage |

### 0603 Basic values

| Value | LCSC | Value | LCSC | Value | LCSC | Value | LCSC |
|---|---|---|---|---|---|---|---|
| 0 Ω | C21189 | 220 Ω | C22962 | 1.5 kΩ | C22843 | 15 kΩ | C22809 |
| 10 Ω | C22859 | 300 Ω | C23025 | 2 kΩ | C22975 | 20 kΩ | C4184 |
| 22 Ω | C23345 | 330 Ω | C23138 | 2.2 kΩ | C4190 | 22 kΩ | C31850 |
| 33 Ω | C23140 | 390 Ω | C23151 | 3 kΩ | C4211 | 30 kΩ | C22984 |
| 47 Ω | C23182 | 470 Ω | C23179 | 3.3 kΩ | C22978 | 33 kΩ | C4216 |
| 49.9 Ω | C23185 | 510 Ω | C23193 | 4.7 kΩ | C23162 | 47 kΩ | C25819 |
| 51 Ω | C23197 | 560 Ω | C23204 | 4.99 kΩ | C23046 | 51 kΩ | C23196 |
| 75 Ω | C4275 | 680 Ω | C23228 | 5.1 kΩ | C23186 | 100 kΩ | C25803 |
| 100 Ω | C22775 | 1 kΩ | C21190 | **10 kΩ** | **C25804** | 200 kΩ | C25811 |
| 120 Ω | C22787 | 1.2 kΩ | C22765 | | | 1 MΩ | C22935 |

About 80 values are Basic in 0603; this table holds the common ones. Search the plugin for others.

### Larger sizes, common values (Basic)

| Value | 0805 | 1206 |
|---|---|---|
| 0 Ω | C17477 | C17888 |
| 10 Ω | C17415 | C17903 |
| 100 Ω | C17408 | C17901 |
| 1 kΩ | C17513 | C4410 |
| 2 kΩ | C17604 | C17944 |
| 4.7 kΩ | C17673 | C17936 |
| 10 kΩ | C17414 | C17902 |
| 100 kΩ | | C17900 |
| 1 MΩ | | C17927 |

### Current-sense shunt (Extended)

| Part | Value | LCSC | Notes |
|---|---|---|---|
| FOJAN FPM253WFR001TML | 1 mΩ, 3 W, 1 %, 2512 | C7420016 | ±50 ppm/°C; no Basic shunts exist |

---

## Ceramic capacitors (MLCC)

Basic ceramics come from three families: **Samsung CL** (`CL10` = 0603, `CL21` = 0805, `CL31` = 1206), **YAGEO CC** and **Fenghua (FH)**.

### 0603 (Basic)

| Value | Voltage | Dielectric | LCSC | Typical use |
|---|---|---|---|---|
| 10 pF | 50 V | C0G | C1634 | |
| 22 pF | 50 V | C0G | C1653 | |
| 47 pF | 50 V | C0G | C1671 | |
| 100 pF | 50 V | C0G | C14858 | RC filters |
| 1 nF | 50 V | X7R | C1588 | RC filters |
| 10 nF | 50 V | X7R | C57112 | |
| 47 nF | 50 V | X7R | C1622 | |
| **100 nF** | **50 V** | **X7R** | **C14663** | **Standard decoupling** |
| 220 nF | 25 V | X7R | C21120 | |
| 470 nF | 25 V | X7R | C1623 | |
| 1 µF | 50 V | X5R | C15849 | Local bulk on 3.3 V / 5 V |
| 2.2 µF | 16 V | X5R | C23630 | |
| 4.7 µF | 16 V | X5R | C19666 | |
| 10 µF | 25 V | X5R | C96446 | Bulk on 3.3 V / 5 V |

Other Basic C0G values in 0603: 12, 15, 18, 20, 30, 33 and 330 pF.

### 0805 and 1206 (Basic)

| Value | Voltage | Dielectric | Size | LCSC |
|---|---|---|---|---|
| **100 nF** | **100 V** | X7R | 0805 | **C28233** (the only Basic 100 V decoupling capacitor) |
| 1 µF | 50 V | X7R | 0805 | C28323 |
| 2.2 µF | 50 V | X5R | 0805 | C377773 |
| 10 µF | 25 V | X5R | 0805 | C15850 |
| 10 µF | 50 V | X5R | 0805 | C440198 (Murata) |
| 22 µF | 25 V | X5R | 0805 | C45783 |
| 2.2 µF | 50 V | X7R | 1206 | C50254 |
| 4.7 µF | 50 V | X7R | 1206 | C29823 |
| 10 µF | 50 V | X5R | 1206 | C13585 |
| 22 µF | 25 V | X5R | 1206 | C12891 |

### 100 V ceramics for the 48 V bus (Extended)

Basic ceramics stop at 50 V, apart from C28233 above. Choose from these and keep the count of unique parts low. "Kept" is the capacitance remaining at that DC voltage, from Samsung's published DC-bias data (measured at 0.5 Vrms).

| Part | Value | Size | LCSC | Kept at 48 V | Kept at 60 V |
|---|---|---|---|---|---|
| Samsung CL21B104KCFNNNE (Basic) | 100 nF 100 V X7R | 0805 | C28233 | 52 % | 42 % |
| Samsung CL31B105KCHNNNE | 1 µF 100 V X7R | 1206 | C13832 | 46 % | 35 % |
| **Samsung CL31B225KCHSNNE** | 2.2 µF 100 V X7R | 1206 | **C170101** | 37.5 % | 29 % |
| Samsung CL32B225KCJSNNE | 2.2 µF 100 V X7R | 1210 | C55151 | 45 % | 34 % |
| Samsung CL32Y475KCIVPNE | 4.7 µF 100 V X7S | 1210 | C2803397 | 38 % | 28 % |
| **Samsung CL32Y106KCV6PNE** | 10 µF 100 V X7S | 1210 | **C22380050** | 26.5 % | 20 % |
| YAGEO CC1206KKX7R0BB225 | 2.2 µF 100 V X7R | 1206 | C577211 | no published curve | |
| PSA FS32X106K101EGG | 10 µF 100 V X7R | 1210 | C5156756 | no published curve | |
| FH 1206B104K101NT | 100 nF 100 V X7R | 1206 | C110255 | no published curve | |

### DC bias of common low-voltage parts

| Part | Value | LCSC | Kept at 5 V | Kept at 12 V |
|---|---|---|---|---|
| Samsung CL10A105KB8NNNC (Basic) | 1 µF 50 V X5R 0603 | C15849 | 66 % | |
| Samsung CL31A226KAHNNNE (Basic) | 22 µF 25 V X5R 1206 | C12891 | 62 % | **26 %** |
| Samsung CL32A226KAJNNNE | 22 µF 25 V X5R 1210 | C52306 | 80 % | 41 % |
| Samsung CL31A106KBHNNNE | 10 µF 50 V X5R 1206 | — | 73 % | 34 % |

At small ripple (around 10 mV), X5R parts lose roughly another 15 % compared with the 0.5 Vrms test signal.

---

## Ferrite beads (Basic)

| Part | Impedance at 100 MHz | Current | Size | LCSC | Use for |
|---|---|---|---|---|---|
| **Murata BLM18PG121SN1D** | 120 Ω | 2 A | 0603 | **C14709** | VDDA filter, supply filtering |
| Sunlord GZ1608D601TF | 600 Ω | 200 mA | 0603 | C1002 | Strong filtering on light loads |
| Sunlord GZ2012D101TF | 100 Ω | 800 mA | 0805 | C1015 | |

---

## Indicator LEDs (Basic)

| Colour | Part | Size | LCSC |
|---|---|---|---|
| Red | KENTO KT-0603R | 0603 | C2286 |
| White | KENTO KT-0603W | 0603 | C2290 |
| Green | KENTO KT-0805G | 0805 | C2297 |
| Yellow | KENTO KT-0805Y | 0805 | C2296 |

There's no Basic green LED in 0603. Use 0805 for all status LEDs, or limit 0603 LEDs to red and white.

---

## No Basic option

These categories are Extended only. Choose with care, and reuse one part number wherever the same function appears.

- **Power inductors:** the output inductor and the aux buck's inductor
- **SMD aluminum electrolytic capacitors:** the input bulk capacitance
- **Current-sense shunts:** see the shunt above
