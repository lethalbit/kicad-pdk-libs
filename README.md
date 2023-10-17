# KiCad PDK Library

This is a [KiCad] symbol library that contains the collection of cells from the [sky130] and [gf180mcu] PDKs for use in schematic capture and SPICE simulation.


> [!IMPORTANT]
> The in-repo libraries are exported with SPICE libraries as a link, not embedded. To ensure spice works, you need `PDK_ROOT` set in your KiCad paths for that to work.

To get started see the [installation](./docs/install.md) instructions and then once you're done there you can follow the [introduction](./docs/intro.md) to get your first SPICE sim done!

## Documentation

The documentation for usage and installation can be found [here](./docs/index.md).

## License

The [`pdk2kicad`](./contrib/pdk2kicad.py) script is licensed under the [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html), the full text of which can be found in the [`LICENSE.script`](./LICENSE.script) file.

The [library symbols](./symbols/) generated from the `pdk2kicad` script are licensed under the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) as they are extracted from the [open_pdk] builds, which are also Apache 2.0 licensed. The full text of which can be found in the [`LICENSE.data`](./LICENSE.data) file.


[KiCad]: https://www.kicad.org/
[sky130]: https://skywater-pdk.readthedocs.io/en/main/
[gf180mcu]: https://gf180mcu-pdk.readthedocs.io/en/latest/
[open_pdk]: https://github.com/RTimothyEdwards/open_pdks
[volare]: https://github.com/efabless/volare
[PCM]: https://www.kicad.org/pcm/
