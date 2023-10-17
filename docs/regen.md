# KiCad-PDK-Libs: Regenerating

There shouldn't be a need to re-generate the libraries from scratch, but in the case one wishes to do so, then a few prerequisites are needed.

## Install Dependencies

First, set up a python [virtual environment](https://docs.python.org/3/tutorial/venv.html) and then install all the needed dependencies and tools into it.

```
$ python -m venv .venv
$ source .venv/bin/active
$ python -m pip install tatsu rich jinja2 volare
```
## Setup PDKs

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

## Regenerate Symbols

Once that is done, you can invoke [`pdk2kicad`](./contrib/pdk2kicad.py) to generate the symbol libraries for [KiCad].

> [!WARNING]
> This will take a /very/ long time, for options to possibly speed  it up see the next section.

```
$ python ./contrib/pdk2kicad.py --pdk sky130A --spice --link
$ python ./contrib/pdk2kicad.py --pdk sky130B --spice --link
$ python ./contrib/pdk2kicad.py --pdk gf180mcuA --spice --link
$ python ./contrib/pdk2kicad.py --pdk gf180mcuB --spice --link
$ python ./contrib/pdk2kicad.py --pdk gf180mcuC --spice --link
$ python ./contrib/pdk2kicad.py --pdk gf180mcuD --spice --link
```

When it's all over, all of the symbols will be located in [`symbols/<PDK>/`](./symbols/).

## Tips On Speeding Up Generation

The part that takes the longest is the ingestion of the PDK data, mainly the LEF files which describe the cells.

To speed this up, you can use the `-j` option to specify the number of parallel threads used for processing, if that is still too slow, you can also use [pypy], the setup of which is outside the scope of this document, but it should contribute a large chunk of performance.


[KiCad]: https://www.kicad.org/
[sky130]: https://skywater-pdk.readthedocs.io/en/main/
[gf180mcu]: https://gf180mcu-pdk.readthedocs.io/en/latest/
[open_pdk]: https://github.com/RTimothyEdwards/open_pdks
[volare]: https://github.com/efabless/volare
[PCM]: https://www.kicad.org/pcm/
[pypy]: https://www.pypy.org/
