# Component Datasheets

Find the datasheet, specification, or mechanical drawing by KiCad reference designator. The reference designators and part numbers come from the project schematic. The connector design notes call CN201 **J201** and U302 **J301**.

## Input supply

| References | Function | Manufacturer and part number | Local copy | Online reference |
|---|---|---|---|---|
| U201 | Auxiliary buck regulator | TI `LM5164DDAR` | [Datasheet](lm5164.pdf) | [Source](https://www.ti.com/lit/ds/symlink/lm5164.pdf) |
| U202 | 3.3 V LDO | STMicroelectronics `LDL1117S33R` | [Datasheet](ldl1117.pdf) | [Source](https://www.st.com/resource/en/datasheet/ldl1117.pdf) |
| U203 | Power mux | TI `TPS2121RUXR` | [Datasheet](tps2121.pdf) | [Source](https://www.ti.com/lit/ds/symlink/tps2121.pdf) |
| Q202 | External 5 V protection MOSFET | Alpha & Omega Semiconductor `AO3401A` | [Datasheet](ao3401a.pdf) | [Source](https://www.aosmd.com/res/datasheets/AO3401A.pdf) |
| D201 | Input TVS | Hongjiacheng `SMBJ51CA` | [Datasheet](hongjiacheng-smbj51ca.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/29e006ceaae5808e6d17d021de7bda89.pdf?productCode=C41376101) |
| F201 | Input fuse | Littelfuse `0451007.MRL` | [Datasheet](littelfuse-451-453.pdf) | [Source](https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1) |
| L201 | Auxiliary buck inductor | Changjiang `FNR8040S470MT` | [Series PDF](changjiang-fnr8040s470mt.pdf#page=17) | [Source](https://datasheet.lcsc.com/datasheet/pdf/a0b12ba9dfe6b9e66b6bb852b7c71c03.pdf?productCode=C168137) |
| C203 | Input bulk capacitor | Ymin `VKME1452A101MV` | [Part specification](ymin-vkm.pdf#page=3) | [Source](https://datasheet.lcsc.com/datasheet/pdf/26b51735fb5c2e65f594023df50aaf97.pdf?productCode=C487440) |
| C206, C207, C208, C209, C210 | Auxiliary buck input MLCC bank | Samsung Electro-Mechanics `CL31B225KCHSNNE` | [Datasheet](samsung-cl31b225kchsnne.pdf) | [Source](https://evelta.com/content/datasheets/110-CL31B225KCHSNNE.pdf) |
| C205, C213, C214, C308, C309 | 22 µF rail capacitors | Samsung Electro-Mechanics `CL31A226KAHNNNE` | [Datasheet](samsung-cl31a226kahnnne.pdf) | [Source](https://media.digikey.com/pdf/Data%20Sheets/Samsung%20PDFs/CL31A226KAHNNNE_Spec.pdf) |

The earlier 48 V return circuit used Q201, an Infineon BSC070N10NS3G, and D202, a Hongjiacheng BZT52C12 gate clamp. Their datasheets support the archived input circuit and loss estimates. [Q201](bsc070n10ns3-g.pdf) · [D202](hongjiacheng-bzt52c12.pdf)

## Main power stage

| References | Function | Manufacturer and part number | Local copy | Online reference |
|---|---|---|---|---|
| Q301, Q302 | GaN half-bridge FETs | Infineon `IGC033S10S1` | [Datasheet](igc033s10s1.pdf) | [Source](https://www.infineon.com/part/IGC033S10S1) |
| U301 | GaN gate driver | TI `LM5113QDPRRQ1` | [Datasheet](lm5113-q1.pdf) | [Source](https://www.ti.com/lit/ds/symlink/lm5113-q1.pdf) |
| L301 | Output inductor | Sunltech `SLB2212P6R8MTT` | [Series PDF](sunltech-slb2212p6r8mtt.pdf#page=2) | [Source](https://datasheet.lcsc.com/datasheet/pdf/792ed416ef23c1dd0e2ebaa12404d7df.pdf?productCode=C2842794) |
| R201, R301 | Input and output current shunts | FOJAN `FPM253WFR001TML` | [Series PDF](fojan-fpm-series.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/c3359fca14918b99b0dc4539e91363e2.pdf?productCode=C7420016) |
| C301, C302, C303 | Main bus MLCC bank | Samsung Electro-Mechanics `CL32Y106KCV6PNE` | [Datasheet](samsung-cl32y106kcv6pne.pdf) | [Source](https://product.samsungsem.com/mlcc/CL32Y106KCV6PN.do) |
| C304, C305, C306, C307 | High-frequency bus bypass | Samsung Electro-Mechanics `CL10B104KC8NNNC` | [Datasheet](samsung-cl10b104kc8nnnc.pdf) | [Source](https://datasheet.octopart.com/CL10B104KC8NNNC-Samsung-datasheet-42770383.pdf) |
| C316, C317 | Output polymer capacitors | Nippon Chemi-Con `APXJ160ARA271MF80J` | [Series PDF](chemi-con-pxj.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/12198b75c8a814e2e506fc713acff675.pdf?productCode=C2944013) |
| D301, D601 | Bootstrap and enable Schottky diodes | Hongjiacheng `BAT46W` | [Datasheet](hongjiacheng-bat46w.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/2f7f37f502efefee1d82933f9084ff3e.pdf?productCode=C7420332) |

## Sensing

| References | Function | Manufacturer and part number | Local copy | Online reference |
|---|---|---|---|---|
| U401, U402, U404, U407 | Voltage and temperature amplifiers | TI `TLV9061IDBVR` | [Datasheet](tlv9061.pdf) | [Source](https://www.ti.com/lit/ds/symlink/tlv9061.pdf) |
| U403, U405 | Current-sense amplifiers | TI `INA241A3IDDFR` | [Datasheet](ina241a.pdf) | [Source](https://www.ti.com/lit/ds/symlink/ina241a.pdf) |
| U406, U408 | Platinum RTDs | Vishay `PTS120601B1K00P100` | [Series PDF](vishay-pts.pdf) | [Source](https://www.vishay.com/docs/28762/pts.pdf) |
| D401, D402 | Sense clamps | Nexperia `BAT54S,215` | [Datasheet](bat54s.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/3fa70e0d1f2c320a83604c0e0e47ce24.pdf?productCode=C47546) |

## MCU and enable

| References | Function | Manufacturer and part number | Local copy | Online reference |
|---|---|---|---|---|
| U501 | C2000 MCU | TI `F280039CSPMR` | [Datasheet](tms320f280039c.pdf) | [Source](https://www.ti.com/lit/ds/symlink/tms320f280039c.pdf) |
| X501 | 16 MHz crystal | Monec `ESD16.0000F12M25F` | [Datasheet](monec-esd16-crystal.pdf) | [Source](https://datasheet.lcsc.com/lcsc/1912111437_ZHUHAI-MONEC-ELEC-ESD16-0000F12M25F_C353726.pdf) |
| U601 | Supervisor and watchdog | TI `TPS3813K33DBVR` | [Datasheet](tps3813.pdf) | [Source](https://www.ti.com/lit/ds/symlink/tps3813.pdf) |
| U602, U603, U604 | Dual AND gates | TI `SN74LVC2G08DCUR` | [Datasheet](sn74lvc2g08.pdf) | [Source](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf) |
| U605 | NAND interlock gate | TI `SN74LVC1G00DBVR` | [Datasheet](sn74lvc1g00.pdf) | [Source](https://www.ti.com/lit/ds/symlink/sn74lvc1g00.pdf) |
| SW601 | Enable slide switch | Shou Han `MSK12C02` | [Part specification](shou-han-msk12c02.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/5162155576bfd231c35aa9a893d25c8c.pdf?productCode=C431540) |

## Communications and connectors

| References | Function | Manufacturer and part number | Local copy | Online reference |
|---|---|---|---|---|
| U701 | USB-to-UART bridge | Silicon Labs `CP2102N-A02-GQFN24R` | [Datasheet](cp2102n.pdf) | [Source](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf) |
| D701 | USB ESD protection | STMicroelectronics `USBLC6-2SC6` | [Datasheet](usblc6-2.pdf) | [Source](https://www.st.com/resource/en/datasheet/usblc6-2.pdf) |
| USBC701 | USB-C receptacle | HRO `TYPE-C-31-M-12` | [Part drawing](hro-type-c-31-m-12.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/9e56b777c022540fcce7c7f67825f55e.pdf?productCode=C165948) |
| H701 | JTAG header | Samtec `FTR-110-03-G-D-06-TR` | [Series drawing](samtec-ftr.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/20e702154724fc528394919d8cb5b233.pdf?productCode=C3332048) |
| CN201 | 48 V input connector | Amass `XT30PW-M30.G.Y` | [Product specification](amass-xt30pw-m.pdf#page=2) | [Source](https://datasheet.lcsc.com/datasheet/pdf/f40c503d729038bd14858056d73ccb74.pdf?productCode=C431092) |
| U302 | 12 V output connector | Amass `XT60PW-F` | [Product specification](amass-xt60pw-f.pdf#page=2) | [Source](https://datasheet.lcsc.com/datasheet/pdf/20ba05e2e8ffaa4dc0ee081e72884460.pdf?productCode=C428722) |
| J202 | External 5 V header | JST `B2B-XH-A(LF)(SN)` | [Series catalog](jst-xh.pdf) | [Source](https://www.jst.com/wp-content/uploads/2025/06/eXH.pdf) |

## Indicators

| References | Function | Manufacturer and part number | Local copy | Online reference |
|---|---|---|---|---|
| LED201, LED501 | Red 48V and FAULT LEDs | NationStar `NCD0805R1` | [Datasheet](nationstar-ncd0805r1.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/e3e35db60c068efe42b02d21fe498cf3.pdf?productCode=C84256) |
| LED202, LED301, LED502 | Green POWER, 12V and HEARTBEAT LEDs | KENTO `KT-0805G` | [Color specification](kento-kt-0805g.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/de342fde3322df0797012cd7a04e2194.pdf?productCode=C2297) |
| LED203 | White EXT 5V LED | KENTO `KT-0805W` | [Color specification](kento-kt-0805w.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/48953f05e6e6e0a517af2e319c9c297c.pdf?productCode=C34499) |
| LED601 | Yellow ARMED LED | KENTO `KT-0805Y` | [Color specification](kento-kt-0805y.pdf) | [Source](https://datasheet.lcsc.com/datasheet/pdf/3f6a14f9ea2fc39f6e05d2ab0fa53e2b.pdf?productCode=C2296) |

## Package and layout references

- [TMS320F280039C 64-pin PM package drawing](tms320f280039c-pm64-package.pdf)
- [Infineon IGC033S10S1 half-bridge evaluation board guide](infineon-ug122052-igc033s10s1-half-bridge-eval.pdf)
- [Infineon PCB layout guidelines for MOSFET gate drivers](infineon-applicationnote-gatedriver-mosfet-pcb-layout-guidelines-for-mosfet-gatedriver-applicationnotes-en.pdf)
- [EPC PCB layout rules for GaN converters](epc-pcb-layout-rules-2025.pdf)
- [EPC WP010 on PCB layout](epc-wp010-optimizing-pcb-layout.pdf)
- [EPC high-performance GaN layout techniques](epc-high-performance-gan-layout-techniques.pdf)
