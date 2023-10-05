# KiCad PDK Library

This is a [KiCad] symbol library that contains the collection of cells from the [sky130] and [gf180mcu] PDKs for use in schematic capture and SPICE simulation.


## Re-generating the libraries

There shouldn't be a need to re-generate the libraries from scratch, but in the case one wishes to do so, then a few prerequisites are needed.

First, set up a python [virtual environment](https://docs.python.org/3/tutorial/venv.html) and then install all the needed dependencies and tools into it.

```
$ python -m venv .venv
$ source .venv/bin/active
$ python -m pip install tatsu rich jinja2 volare
```

Next, we setup PDK root we want to use:

```
$ export PDK_ROOT="${HOME}/.local/share/PDK"
$ mkdir -p "${PDK_ROOT}"
```

It's not recommended to use your existing PDK root if there is one.

Next, setup the PDKs using [volare], we build the PDKs from source to ensure we get all of the cell libraries for the PDKs as well as the correct version of the PDK we want. This will take a while.

```
$ volare build --pdk sky130 -l all dd7771c384ed36b91a25e9f8b314355fc26561be
$ volare build --pdk gf180mcu -l all dd7771c384ed36b91a25e9f8b314355fc26561be

```

Next ensure the PDKs are enabled so they are symlinked to the `PDK_ROOT` we set up

```
$ volare enable --pdk sky130 -l all dd7771c384ed36b91a25e9f8b314355fc26561be
$ volare enable --pdk gf180mcu -l all dd7771c384ed36b91a25e9f8b314355fc26561be
```

Once that is done, you can invoke [`pdk2kicad`](./contrib/pdk2kicad.py) to generate the symbol libraries for [KiCad]. This will take a long time.

```
$ python ./contrib/pdk2kicad.py --pdk sky130A
$ python ./contrib/pdk2kicad.py --pdk sky130B
$ python ./contrib/pdk2kicad.py --pdk gf180mcuA
$ python ./contrib/pdk2kicad.py --pdk gf180mcuB
$ python ./contrib/pdk2kicad.py --pdk gf180mcuC
$ python ./contrib/pdk2kicad.py --pdk gf180mcuD
```

When it's all over, all of the symbols will be located in [`symbols/<PDK>/`](./symbols/).


## License

The [`pdk2kicad`](./contrib/pdk2kicad.py) script is licensed under the [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html), the full text of which can be found in the [`LICENSE.script`](./LICENSE.script) file.

The [library symbols](./symbols/) generated from the `pdk2kicad` script are licensed under the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) as they are extracted from the [open_pdk] builds, which are also Apache 2.0 licensed. The full text of which can be found in the [`LICENSE.data`](./LICENSE.data) file.


[KiCad]: https://www.kicad.org/
[sky130]: https://skywater-pdk.readthedocs.io/en/main/
[gf180mcu]: https://gf180mcu-pdk.readthedocs.io/en/latest/
[open_pdk]: https://github.com/RTimothyEdwards/open_pdks
[volare]: https://github.com/efabless/volare
