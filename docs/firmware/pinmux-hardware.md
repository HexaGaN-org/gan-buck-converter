# F280039C Hardware Pin Assignment

**Status:** Physical pin allocation frozen for PCB routing on 2026-11-11. This records the saved seven-sheet KiCad schematic for the 64-pin PM package, F280039CSPMR. It does not configure the MCU. A TI SysConfig `pinmux.syscfg` file and generated firmware have not yet been created or compiled.

The package pins and available functions below were checked against the [TI F28003x datasheet, Rev. C, Figure 5-4 and Tables 5-2/5-6](https://www.ti.com/lit/ds/symlink/tms320f280039c.pdf). Board nets were checked against a fresh KiCad XML netlist export of `hardware/gan-buck-converter/gan-buck-converter.kicad_sch` on 2026-11-11. "TI + netlist" means the physical pin, supported function, and saved board connection agree; it does not mean peripheral routing or trip behavior has been tested in firmware.

| Board signal or circuit | U501 pin | MCU pad and intended function | Source check / firmware status |
|---|---:|---|---|
| `MCU_PWMH` | 52 | GPIO0 / EPWM1_A | TI GPIO mux + netlist; ePWM setup pending |
| `MCU_PWML` | 51 | GPIO1 / EPWM1_B | TI GPIO mux + netlist; dead-band setup pending |
| `MCU_EN` | 50 | GPIO2 / output | TI package + netlist; default-low GPIO setup pending |
| `WD_IN` | 49 | GPIO3 / output | TI package + netlist; watchdog schedule pending |
| `STAGE_EN_FB` | 48 | GPIO4 / input | TI package + netlist; GPIO setup pending |
| `SCI_TX` | 1 | GPIO29 / SCIA_TX, to U701 RXD pin 20 | TI GPIO mux + netlist; UART setup pending |
| `SCI_RX` | 2 | GPIO28 / SCIA_RX, from U701 TXD pin 21 | TI GPIO mux + netlist; UART setup pending |
| `HEARTBEAT` LED via R509 | 46 | GPIO39 / output | TI package + netlist; GPIO setup pending |
| `FAULT` LED via R508 | 53 | GPIO40 / output | TI package + netlist; GPIO setup pending |
| `I_OUT_SENSE` | 8 | ADCA A3 / CMPSS3 high positive input 5 | TI analog table + netlist; ADC/CMPSS/ePWM trip route pending |
| `V_OUT_SENSE` | 14 | ADCB B7 / CMPSS1 high positive input 4 | TI analog table + netlist; ADC/CMPSS/ePWM trip route pending |
| `V_IN_SENSE` | 15 | ADCC C15 / CMPSS3 low positive input 2 | TI analog table + netlist; inverted overvoltage trip route pending |
| `I_IN_SENSE` | 9 | ADCC C9 | TI analog table + netlist; ADC setup pending |
| `HS_TEMP_SENSE` | 23 | ADCC C14 | TI analog table + netlist; ADC setup pending |
| `LS_TEMP_SENSE` | 13 | ADCC C2 | TI analog table + netlist; ADC setup pending |
| `BOOT_GPIO24`, R504 and JP501 | 35 | GPIO24 / boot strap | TI package + netlist; OTP boot settings must be checked |
| `BOOT_GPIO32`, R505 and JP502 | 40 | GPIO32 / boot strap | TI package + netlist; OTP boot settings must be checked |
| `TCK` | 36 | TCK input | TI package + netlist; reserve for JTAG |
| `TMS` | 38 | TMS input | TI package + netlist; reserve for JTAG |
| `TDI` | 39 | GPIO35 / TDI input | TI package + netlist; reserve for JTAG |
| `TDO` | 37 | GPIO37 / TDO output | TI package + netlist; reserve for JTAG |
| `XRSn` | 3 | active-low reset, shared with U601 and H701 | TI package + netlist; reset sequence pending |
| Crystal `X2` via R503 | 41 | GPIO18 / X2 | TI package + netlist; external-oscillator setup pending |
| Crystal `X1` | 42 | GPIO19 / X1 | TI package + netlist; 16 MHz PLL setup pending |

Fixed analog/reference and supply pins are outside the programmable pin mux: VREFHI 16, VREFLO 17, VSSA 21, VDDA 22, VDD 4/27/44/59, VDDIO 28/43/60, and VSS 5/26/45/58. The no-connect pins remain unassigned; their firmware pull-up policy is described in [the MCU design note](../design/mcu.md).

## Firmware handoff

Create a real `firmware/pinmux.syscfg` inside the future C2000 firmware project using the installed TI SysConfig version for F280039C. Match this table before generating code. Configure GPIO0/1 as one EPWM1_A/B pair with dead-band, GPIO28/29 as SCIA_RX/TX, the six ADC channels above, and the CMPSS3 high/low and CMPSS1 high comparator inputs. Pin 8 also carries VDAC and pin 15 also carries DACA_OUT: use VDDA for the comparator DAC reference and leave the buffered DAC outputs disabled while those pins carry sense signals. Check that the two CMPSS3 outputs can be routed to separate cycle-by-cycle and one-shot ePWM actions as required by [firmware requirements](firmware-requirements.md). Verify the default boot and OTP configuration before relying on JP501/JP502.

The board allocation can be routed from this table. Firmware mux selections, trip X-BAR routing, ADC timing, PWM dead time, and boot behavior remain implementation and bench-validation tasks. Any change to a physical pin or board net requires a matching schematic and table update before routing is frozen.
