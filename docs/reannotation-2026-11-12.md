# Re-annotation, 2026-11-12

The schematic was re-annotated on 2026-11-12 (PR #15) so that every sheet uses its own range (sheet number × 100), as [CONTRIBUTING.md](../CONTRIBUTING.md) asks. The mcu, enable and comms_debug sheets moved into the 500, 600 and 700 ranges; some references that were already in range on the other sheets also changed. 145 references changed in total.

All design notes, the BOM and the firmware pin-map note now use the new names. Use the tables below to translate older notes, review comments and commit messages. Only references that changed are listed.

The PCB file still carries the old names until it is next updated from the schematic. Its footprints are linked to their symbols by ID, so run *Update PCB from Schematic* with **re-link footprints by reference designator left off**; the footprints then take the new names.

Changes made in the same PR that are not renames: the power stage lost C305 and C307 (10 µF), C313–C318 (22 µF) and C319 (470 µF) under the old names, and gained C316 and C317 (270 µF polymer) under the new names ([power_stage.md](design/power_stage.md) decision #24).

## input_supply

| Old | New | Value |
|---|---|---|
| C213 | C208 | 2.2uF |
| C214 | C209 | 2.2uF |
| C215 | C210 | 2.2uF |
| C208 | C211 | 1uF |
| C209 | C212 | 10uF |
| C210 | C213 | 22uF |
| C211 | C214 | 22uF |
| C212 | C215 | 100nF |

## power_stage

| Old | New | Value |
|---|---|---|
| C306 | C305 | 100nF |
| C309 | C306 | 100nF |
| C310 | C307 | 100nF |
| C311 | C308 | 22uF |
| C312 | C309 | 22uF |
| C320 | C310 | Snubber |
| C321 | C311 | 100nF |
| C322 | C312 | 10uF |
| C323 | C313 | 100nF |
| C324 | C314 | 22pF |
| C325 | C315 | 22pF |
| NT302 | NT301 | NetTie_2 |
| NT301 | NT302 | NetTie_2 |
| R307 | R302 | 10k |
| R302 | R303 | Snubber |
| R303 | R304 | 100R |
| R304 | R305 | 2R |
| R305 | R306 | 1k |
| R306 | R307 | 1k |
| TP_GND1 | TP_GND301 | TestPoint |
| TP_GND2 | TP_GND302 | TestPoint |
| TP_LSG1 | TP_LSG301 | LS_GATE |
| TP_LSS1 | TP_LSS301 | LS_SOURCE |
| TP_SW1 | TP_SW301 | TestPoint |
| TP_VIN1 | TP_VIN301 | TestPoint |
| TP_VOUT1 | TP_VOUT301 | TestPoint |

## sensing

| Old | New | Value |
|---|---|---|
| C410 | C401 | 100nF |
| C406 | C402 | 100nF |
| C408 | C403 | 100nF |
| C411 | C404 | 1nF |
| C404 | C405 | 1nF |
| C415 | C406 | 22pF |
| C401 | C408 | 100nF |
| C402 | C410 | 100nF |
| C413 | C411 | 100nF |
| C416 | C412 | 100nF |
| C403 | C413 | 100nF |
| D405 | D401 | BAT54S |
| D406 | D402 | BAT54S |
| R411 | R402 | 750k |
| R413 | R403 | 1k |
| R407 | R404 | 1k |
| R402 | R405 | 150k |
| R412 | R406 | 20k |
| R417 | R407 | 1k |
| R405 | R408 | 20k |
| R406 | R409 | 4.02k |
| R403 | R410 | 10k |
| R415 | R411 | 1k |
| R418 | R412 | 1k |
| R409 | R413 | 20k |
| R408 | R414 | 4.02k |
| R404 | R415 | 10k |
| TP407 | TP401 | GNDA |
| TP401 | TP402 | V_OUT_SENSE |
| TP402 | TP403 | V_IN_SENSE |
| TP405 | TP404 | I_OUT_SENSE |
| TP403 | TP405 | HS_TEMP_SENSE |
| TP404 | TP407 | LS_TEMP_SENSE |
| U408 | U402 | TLV9061 |
| U402 | U403 | INA241A3 |
| U403 | U404 | TLV9061 |
| U407 | U405 | INA241A3 |
| U404 | U406 | PTS120601B1K00P100 |
| U406 | U407 | TLV9061 |
| U405 | U408 | PTS120601B1K00P100 |

## mcu

| Old | New | Value |
|---|---|---|
| C1 | C501 | 2.2uF |
| C2 | C502 | 22nF |
| C3 | C503 | 18pF |
| C4 | C504 | 18pF |
| Cvdd4 | Cvdd501 | 4.7uF |
| Cvdd3 | Cvdd502 | 4.7uF |
| Cvdd2 | Cvdd503 | 4.7uF |
| Cvdd1 | Cvdd504 | 4.7uF |
| Cvdda5 | Cvdda501 | 4.7uF |
| Cvddio1 | Cvddio501 | 220nF |
| Cvddio3 | Cvddio502 | 220nF |
| Cvddio2 | Cvddio503 | 220nF |
| LED502 | LED501 | FAULT |
| LED501 | LED502 | HEARTBEAT |
| NT1 | NT501 | NetTie_2 |
| R12 | R501 | 2.2k |
| R1 | R502 | 4.7k |
| R4 | R503 | 0R |
| R5 | R504 | 10k |
| R6 | R505 | 10k |
| R2 | R506 | 10k |
| R3 | R507 | 10k |
| R502 | R508 | 1k |
| R501 | R509 | 330R |
| U1 | U501 | F280039C |
| X1 | X501 | 16MHz |

## enable

| Old | New | Value |
|---|---|---|
| C5 | C601 | 220pF |
| C6 | C602 | 100nF |
| C8 | C603 | 100nF |
| C7 | C604 | 100nF |
| C9 | C605 | 100nF |
| C601 | C606 | 100nF |
| D1 | D601 | BAT46W |
| R14 | R601 | 10k |
| R15 | R602 | 0R |
| R13 | R603 | 10k |
| R18 | R604 | 10k |
| R23 | R605 | 1k |
| R16 | R606 | 1k |
| R17 | R607 | 10k |
| R19 | R608 | 10k |
| R21 | R609 | 10k |
| R22 | R610 | 10k |
| R20 | R611 | 10k |
| R601 | R612 | 1k |
| SW1 | SW601 | MSK12C02 |
| TP602 | TP601 | SUP_OK |
| TP603 | TP602 | GND |
| TP601 | TP603 | STAGE_EN |
| U7 | U601 | TPS3813K33DBVR |
| U3 | U602 | SN74LVC2G08DCUR |
| U4 | U603 | SN74LVC2G08DCUR |
| U5 | U604 | SN74LVC2G08DCUR |
| U8 | U605 | SN74LVC1G00 |

## comms_debug

| Old | New | Value |
|---|---|---|
| C10 | C701 | 100nF |
| C709 | C702 | 4.7uF |
| C708 | C703 | 100nF |
| C706 | C704 | 4.7uF |
| C707 | C706 | 100nF |
| C11 | C707 | 100nF |
| H1 | H701 | FTR-110-03-G-D-06-TR |
| R713 | R701 | 5.1k |
| R716 | R702 | 22.1k |
| R715 | R703 | 47.5k |
| R717 | R704 | 1.02k |
| R714 | R705 | 5.1k |
| R720 | R706 | 100R |
| R718 | R707 | 4.7k |
| R719 | R708 | 4.7k |
| U703 | U701 | CP2102N-A02-GQFN24R |
| USBC1 | USBC701 | TYPE-C-31-M-12 |
