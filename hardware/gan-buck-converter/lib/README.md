# Project component libraries

The custom symbol and footprint libraries are named `hexagan`, matching `main`:

- Symbols: `lib/symbols/hexagan.kicad_sym`
- Footprints: `lib/footprints/hexagan.pretty/`
- 3D models: `lib/3d/`

Library and 3D model paths are relative to `${KIPRJMOD}`.

## MCU: F280039CSPM

In KiCad's symbol chooser, select **`hexagan:F280039CSPM`**.
Place both units under the same reference, U501:

- **U1A:** core/I/O/analog power, ADC reference, and reset (17 pins).
- **U1B:** GPIO, analog signals, and JTAG (47 pins).

The default footprint is **`hexagan:F280039CSPM`**, the TI PM0064A
manufacturer example land pattern: 64 pins, 0.5 mm pitch, 0.3 x 1.5 mm pads,
and 11.4 mm between opposing pad-row centres. The footprint retains the TI
`PM0064A-MFG` pad geometry. The alternate imported
`F280039CSPM-IPC_A`, `F280039CSPM-IPC_B`, and `F280039CSPM-IPC_C`
footprints are available for assembly review. Use one footprint per physical MCU.

A local generic KiCad LQFP-64, 10 x 10 mm body, 0.5 mm pitch STEP model is
bundled as `3d/F280039CSPM.step` and referenced by all four footprints. It is a package model,
not a manufacturer-specific die or marking model. Its embedded KiCad copyright
and CC-BY-SA 4.0 license with exception are retained. See the
[KiCad 3D library license](https://gitlab.com/kicad/libraries/kicad-packages3D/-/blob/master/LICENSE.md).

## Import provenance and corrections

Imported November 3, 2026 from the supplied Ultra Librarian archive
`ul_XF280039CSPM.zip` (original source symbol: `XF280039CSPM`).
Archive SHA-256: `30ffe7db1369b2411e37c73b7b87b28b80e25b2227c0876fa2c12e08ae8b1ca4`.
The original download and loose import guides are retained in the local
migration-backup directory outside this Git repository.

The project uses the production, non-automotive **F280039CSPM** orderable part,
from the TMS320F280039C family. The downloaded experimental symbol is not an
unchanged production-part definition:

- Pin **46** was corrected from `VREGENZ` to **`GPIO39`**, bidirectional, and
  moved from the power unit to the signal unit, matching the standard 64-pin
  PM pinout in TI SPRSP61C Figure 5-4. The Q-temperature PM variant has a
  different pin-46 function and is not represented by this symbol.
- Undefined analog pin types were replaced with input types; shared DAC/ADC
  pins and VREFHI are bidirectional. VREFLO is a power-input reference return.
- Symbol reference/value fields were moved clear of the pins.
- Each footprint's internal name and value use the production part number and
  match its filename; the download
  incorrectly called every variant `PM0064A-IPC_A`.
- Removed stray `Designator153` text and added front courtyards at least 0.25 mm
  outside the maximum package lead span or copper, whichever extends farther.
  Pin-1 markers and footprint reference/value text were moved clear of copper.
- Imported copper/paste/mask pad geometry and numbering are preserved.
- The files were upgraded and loaded with KiCad 10.

References:

- [TI production part details](https://www.ti.com/product/TMS320F280039C/part-details/F280039CSPM)
- [TI SPRSP61C datasheet](https://www.ti.com/lit/ds/symlink/tms320f280039c.pdf):
  Figure 5-4 for pinout, and PM0064A package/land-pattern drawings.
- [Local TI package drawing](../../../docs/datasheets/tms320f280039c-pm64-package.pdf), drawing 4215162/A.

## Import checks

All 64 symbol pin numbers/names were checked against TI's standard PM pinout.
Each footprint has exactly one pad per pin, 1 through 64; original pad geometry
is preserved. Manufacturer pad sizes/spacing were checked against TI's example
land pattern. Library-table and STEP paths resolve locally. Both symbol units,
all four footprints, and the default footprint's 3D package alignment were
rendered and inspected. These are component-library checks; board schematic,
ERC, layout, and assembly approval remain separate design work.

## Optional MCU crystal

Use `Device:Crystal_GND24` with footprint
`hexagan:ECS-200-8-30B-CKM`. This project footprint follows the
[ECS ECX-53B suggested land pattern](https://www.ecsxtal.com/store/pdf/ecx_53b.pdf):
four 1.6 × 1.25 mm pads, centres spaced 3.7 × 2.2 mm; active pads 1/3, ground
pads 2/4. See [MCU design notes](../../../docs/design/mcu.md) for the DNP circuit
and drive/startup validation still required before population. No 3D model is assigned.

## Board power symbols

`hexagan:V_IN` and `hexagan:V_OUT` preserve the incoming
power-stage and sensing power-net names. They share the existing project library.
