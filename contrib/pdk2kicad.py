#!/usr/bin/env python
import logging          as log
from os                 import environ
from enum               import Enum, auto
from argparse           import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from pathlib            import Path
from concurrent.futures import ThreadPoolExecutor

import datetime
import sys

import tatsu
from jinja2             import Template, Environment
from rich               import traceback
from rich.logging       import RichHandler

env = Environment(trim_blocks = True, lstrip_blocks = True)
env.globals['now'] = datetime.datetime.utcnow
env.globals['len'] = len

LEF_TATSU = '''\
@@grammar :: lef
@@left_recursion :: True
@@parseinfo :: False
@@eol_comments :: /#([^\n]*?)$/

start = { lef_statements } "END" /\s+/ "LIBRARY" $;

lef_statements = ver:version | nowiree | divchar:dividerchar | buschar:busbitchars
               | macro:macro | propdefs:propdefs | case:casesens | units:units
			   | mfr:mfrid
               ;


version     = "VERSION" ~ /\s+/ major:DIGIT "." minor:DIGIT [ ("." rev:DIGIT)] end_stmt ;
mfrid       = "MANUFACTURINGGRID" ~ /\s+/ val:NUMERIC end_stmt ;
nowiree     = "NOWIREEXTENSIONATPIN" ~ /\s+/ ( "ON" | "OFF" ) end_stmt ;
casesens    = "NAMESCASESENSITIVE" ~ /\s+/ ( "ON" | "OFF" ) end_stmt ;
dividerchar = "DIVIDERCHAR" ~ /\s+/ '"' /\W/ '"' end_stmt;
busbitchars = "BUSBITCHARS" ~ /\s+/ '"' /\W/ /\W/ '"' end_stmt;
macro       = "MACRO" ~ /\s+/ name:IDENT /\n/ mstmts:{ macro_stmt } /\n/ "END" /\s+/ IDENT ;
propdefs    = "PROPERTYDEFINITIONS" ~ /\n/ prps:{ p_defs } /\n/ "END" /\s+/ "PROPERTYDEFINITIONS" ;
units       = "UNITS" ~ /\n/ defs:{ unit_def } /\n/ "END" /\s+/ "UNITS" ;

unit_def    = time:unit_d_time | cap:unit_d_cap | res:unit_d_res | pow:unit_d_pow
            | cur:unit_d_cur | volt:unit_d_volt | db:unit_d_db | freq:unit_d_freq
            ;

unit_d_time = "TIME" ~ /\s+/ "NANOSECONDS" /\s+/ val:NUMERIC end_stmt ;
unit_d_cap  = "CAPACITANCE" ~ /\s+/ "PICOFARADS" /\s+/ val:NUMERIC end_stmt ;
unit_d_res  = "RESISTANCE" ~ /\s+/ "OHMS" /\s+/ val:NUMERIC end_stmt ;
unit_d_pow  = "POWER" ~ /\s+/ "MILLIWATTS" /\s+/ val:NUMERIC end_stmt ;
unit_d_cur  = "CURRENT" ~ /\s+/ "MILLIAMPS" /\s+/ val:NUMERIC end_stmt ;
unit_d_volt = "VOLTAGE" ~ /\s+/ "VOLTS" /\s+/ val:NUMERIC end_stmt ;
unit_d_db   = "DATABASE" ~ /\s+/ "MICRONS" /\s+/ val:NUMERIC end_stmt ;
unit_d_freq = "FREQUENCY" ~ /\s+/ "MEGAHERTZ" /\s+/ val:NUMERIC end_stmt ;


p_defs      = "MACRO" ~ /\s+/ name:IDENT /\s+/ type:IDENT end_stmt ;


macro_stmt  = class:macro_s_class | foreign:macro_s_foreign | origin:macro_s_origin
            | eeq:macro_s_eeq | size:macro_s_size | symmetry:macro_s_symmetry
            | site:macro_s_site | pin:macro_s_pin | obs:macro_s_obs
            | density:macro_s_density | prop:property
            ;


macro_s_class    = "CLASS" ~ type:macro_s_class_tp end_stmt ;
macro_s_class_tp = ( "COVER"  | "cover"  ) ~ [ "BUMP" ] | "RING" | "BLOCK" [  "BLACKBOX" | "SOFT"  ]
                 | ( "PAD"    | "pad"    ) ~ [ "INPUT" | "OUTPUT" | "INOUT" | "POWER" | "SPACER" | "AREAIO"  ]
                 | ( "CORE"   | "core"   ) ~ [ "FEEDTRU" | "TIEHIGH" | "TIELOW" | "SPACER" | "ANTENNACELL" | "WELLTAP"  ]
                 | ( "ENDCAP" | "endcap" ) ~ [ "PRE" | "POST" | "TOPLEFT" | "TOPRIGHT" | "BOTTOMLEFT" | "BOTTOMRIGHT"  ]
	             ;
macro_s_foreign  = "FOREIGN" ~  /\s+/ name:IDENT [ /\s+/ POINT [ /\s+/ ORIENTATION ] ] end_stmt ;
macro_s_origin   = "ORIGIN" ~ /\s+/ POINT end_stmt ;
macro_s_eeq      = "EEQ" ~ /\s+/ name:IDENT end_stmt ;
macro_s_size     = "SIZE" ~ /\s+/ NUMERIC "BY" /\s+/ NUMERIC end_stmt ;
macro_s_symmetry = "SYMMETRY" ~ { ("X" | "Y" | "R90") }+ end_stmt ;
macro_s_site     = "SITE" ~ /\s+/ name:IDENT [ DIGIT DIGIT ORIENTATION [ step_patern ] ] end_stmt ;
macro_s_pin      = "PIN" ~ /\s+/ name:IDENT /\n/ pstmnts:{ macro_pin_stmt } /\n/ "END" /\s+/ IDENT  ;
macro_s_obs      = "OBS" ~ /\n/ { layer_geometry } /\n/ "END" ;
macro_s_density  = "DENSITY" ~ /\n/ { layer } /\n/ "END" ;


macro_pin_stmt   =  taperule:pin_taperule | dir:pin_direction | use:pin_use
                 | netexpr:pin_netexpr | splysns:pin_supplysens | gndsns:pin_gndsens
                 | shape:pin_shape | mustjoin:pin_mustjoin | port:pin_port
                 | prop:property | antenna:pin_antenna
                 ;
pin_taperule     = "TAPERULE" ~ /\s+/ IDENT end_stmt ;
pin_direction    = "DIRECTION" ~ pin_dir:( "INPUT" | "OUTPUT" [ "TRISTATE" ] | "INOUT" | "FEEDTRHU" ) end_stmt ;
pin_use          = "USE" ~ pin_type:( "SIGNAL" | "ANALOG" | "POWER" | "GROUND" | "CLOCK" ) end_stmt ;
pin_netexpr      = "NETEXPR" ~ '"' IDENT /\s+/ IDENT '"' end_stmt ;
pin_supplysens   = "SUPPLYSENSITIVITY" ~ /\s+/ IDENT end_stmt ;
pin_gndsens      = "GROUNDSENSITIVITY" ~ /\s+/ IDENT end_stmt ;
pin_shape        = "SHAPE" ~ shp:( "ABUTMENT" | "RING" | "FEEDTHRU" ) end_stmt ;
pin_mustjoin     = "MUSTJOIN" ~ /\s+/ IDENT end_stmt ;
pin_port         = "PORT" ~ /\n/ class:["CLASS" class_type:( "NONE" | "CORE" | "BUMP" | "none" | "core" | "bump" ) end_stmt ] geometry:{ layer_geometry }+ /\n/ "END" ;
pin_antenna      = pin_antenna_pmetal | pin_antenna_pmetalside | pin_antenna_pcut
                 | pin_antenna_diffarea | pin_antenna_model | pin_antenna_gatearea
                 | pin_antenna_maxareac | pin_antenna_maxsideareac | pin_antenna_maxcutc
                 ;
pin_antenna_pmetal       = "ANTENNAPARTIALMETALAREA" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;
pin_antenna_pmetalside   = "ANTENNAPARTIALMETALSIDEAREA" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;
pin_antenna_pcut         = "ANTENNAPARTIALCUTAREA" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;
pin_antenna_diffarea     = "ANTENNADIFFAREA" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;
pin_antenna_model        = "ANTENNAMODEL" ~ ( "OXIDE1" | "OXIDE2" | "OXIDE3" | "OXIDE4" ) end_stmt ;
pin_antenna_gatearea     = "ANTENNAGATEAREA" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;
pin_antenna_maxareac     = "ANTENNAMAXAREACAR" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;
pin_antenna_maxsideareac = "ANTENNAMAXSIDEAREACAR" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;
pin_antenna_maxcutc      = "ANTENNAMAXCUTCAR" ~ /\s+/ NUMERIC [ "LAYER" /\s+/ IDENT ] end_stmt ;





layer_geometry   = layer  geometry:{ shape:(poly:polygon | path:path | rect:rectangle) }* ;

layer            = "LAYER" ~ /\s+/ name:IDENT [ "EXCEPTPGNET" ] { layer_sw } end_stmt ;
layer_sw         = layer_sw_spacing | layer_sw_drwidth ;
layer_sw_spacing = "SPACING" ~ /\s+/ NUMERIC ;
layer_sw_drwidth = "DESIGNRULEWIDTH" ~ /\s+/ NUMERIC ;

property    = "PROPERTY" ~ /\s+/ name:IDENT /\s+/ [ '"' ] value:(IDENT | NUMERIC) [ '"' ] end_stmt ;
polygon     = "POLYGON" ~ /\s+/ p0:POINT /\s+/ p1:POINT /\s+/ p2:POINT /\s+/ pts:{ ptn:POINT /\s+/ } end_stmt ;
path        = "PATH" ~ /\s+/ points:{ pt:POINT /\s+/ }+ end_stmt ;
rectangle   = "RECT" ~ /\s+/ pt0:NUMERIC /\s+/ pt1:NUMERIC /\s+/ pt2:NUMERIC /\s+/ pt3:NUMERIC [ /\s+/ diffusion:NUMERIC ] end_stmt ;
step_patern = "DO" ~ /\s+/ cntx:NUMERIC "BY" /\s+/ cnty:NUMERIC "STEP" /\s+/ stpx:NUMERIC /\s+/ stpy:NUMERIC ;

POINT       = x:NUMERIC /\s+/ y:NUMERIC ;
IDENT       = { (ALPHA | "_") } { ( ALPHANUM | "[" | "]" | /\w+/) } ;
NUMERIC     = (@:FLOAT | @:INTEGER) ;
FLOAT       = [ /\-/ | /\+/ ] { DIGIT }+ /\./ ~ { DIGIT }+ ;
INTEGER     = [ /\-/ | /\+/ ] { DIGIT }+ ;
ALPHANUM    = ALPHA | DIGIT ;
DIGIT       = /\d/ ;
ALPHA       = /\w/ ;

ORIENTATION = "N" | "E" | "S" | "W" | "FN" | "FS" | "FE" | "FW" ;

end_stmt = ";" ;

'''

KISYM_TEMPLATE = env.from_string('''\
{#;; THIS FILE HAS BEEN AUTOGENERATED #}
(kicad_symbol_lib (version 20211014) (generator pdk2kicad)
{#  ;; Generated on: {{ now() }}  #}
{#  ;;     LEF file: {{ lef_file }} #}
{#  ;;      # Cells: {{ len(symbols) }} #}
{#  ;; Library Name: {{ name }} #}
  {% for sym in symbols %}
  (symbol
{#    ;; Total Pins: {{ sym.pin_count() }} #}
{#    ;; # Pwr Pins: {{ sym.pwr_pins() }} #}
{#    ;; # Gnd Pins: {{ sym.gnd_pins() }} #}
{#    ;; # Inp Pins: {{ sym.inp_pins() }} #}
{#    ;; # Out Pins: {{ sym.out_pins() }} #}
{#    ;; # Iop Pins: {{ sym.iop_pins() }} #}
    "{{ sym.id }}"
    (in_bom no)
    (on_board yes)
    {% for prop in sym.properties %}
    (property
      "{{ prop.name }}"
      "{{ prop.value }}"
      (id {{ prop.id }})
      (at {{ prop.pos[0] }} {{ prop.pos[1] }} {{ prop.pos[2] }})
      (effects
        (font
          (size 1 1)
        )
        {% if prop.justify %}
        (justify top)
        {% endif %}
        {% if prop.hide %}
        hide
        {% endif %}
      )
    )
    {% endfor %}
    {{ sym.get_rect() }}
    {% for pin in sym.pins %}
    (pin
      {{ pin.electrical_type() }}
      {{ pin.graphical_style() }}
      (at {{ pin.pos[0] }} {{ pin.pos[1] }} {{ pin.pos[2] }})
      (length 2.54)
      (name "{{ pin.name }}"
        (effects
          (font
            (size 1 1)
          )
          hide
        )
     )
     (number "{{ pin.number }}"
       (effects
          (font
            (size 1 1)
          )
          hide
        )
      )
    )
    {% endfor %}
  )
  {% endfor %}
)
''')


def _setup_logging(args: Namespace = None) -> None:
	level = log.INFO
	if args is not None and args.verbose:
		level = log.DEBUG

	log.basicConfig(
		force    = True,
		format   = '%(message)s',
		datefmt  = '[%X]',
		level    = level,
		handlers = [
			RichHandler(rich_tracebacks = True, show_path = False)
		]
	)

class Property:
	def __init__(self, name, value, pid, hide = True):
		self.name = name
		self.value = value
		self.id = pid
		self.hide = hide
		self.pos = (0, 0, 0)
		self.justify = False

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f'(property "{self.name}" "{self.value}" (id {self.id}))'

class Cell:
	def _count_pins(self):
		pwr = 0
		gnd = 0
		inp = 0
		out = 0
		iop = 0

		for pin in self.pins:
			if pin.type == PinType.POWER:
				pwr += 1
			elif pin.type == PinType.GROUND:
				gnd += 1
			elif pin.type == PinType.SIGNAL or pin.type == PinType.CLOCK:
				if pin.dir == PinDir.INPUT:
					inp += 1
				elif pin.dir == PinDir.OUTPUT:
					out += 1
				elif pin.dir == PinDir.BIDIRECTIONAL:
					iop += 1

		self._pin_counts = (pwr, gnd, inp, out, iop)

	def _calc_bounds(self):
		hpad = 0
		wpad = 0

		for pin in self.pins:
			nlen = len(pin.name)
			if pin.type == PinType.POWER or pin.type == PinType.GROUND:
				hpad = max(hpad, nlen)
			else:
				wpad = max(wpad, nlen)

		hpad *= 1.27
		wpad *= 1.27

		self._padding = (wpad, hpad)

		width = (max(self._pin_counts[0], self._pin_counts[1]) * 2.54) + 2.54
		x = width / 2

		lheight = self._pin_counts[2]
		rheight = self._pin_counts[3]

		hdiff = lheight - rheight

		iops = self._pin_counts[4]
		io_fixup = min(abs(hdiff), iops)

		if hdiff < 0:
			lheight += io_fixup
		else:
			rheight += io_fixup

		iops -= io_fixup

		lheight += iops // 2
		rheight += iops - (iops // 2)

		height = (max(lheight, rheight) * 2.54) + 2.54
		y = height / 2

		return (-x - wpad, -y - hpad, x + wpad, y + hpad)

	def _fixup_pins(self):
		x0, y0, x1, y1 = self._bounds

		pin_idx = 0
		for pin in self.pins:
			if pin.type == PinType.POWER:
				pin.set_y(y1 + 2.54)
				pin.set_x(x0 + (2.54 * (pin_idx +1)) + self._padding[0])
				pin.set_rot(270)
				pin_idx += 1

		pin_idx = 0
		for pin in self.pins:
			if pin.type == PinType.GROUND:
				pin.set_y(y0 - 2.54)
				pin.set_x(x0 + (2.54 * (pin_idx +1)) + self._padding[0])
				pin.set_rot(90)
				pin_idx += 1

		pin_idx = 0
		inp_y = y0 + 2.54
		for pin in self.pins:
			if (pin.type == PinType.SIGNAL or pin.type == PinType.CLOCK) and pin.dir == PinDir.INPUT:
				pin.set_x(x0 - 2.54)
				inp_y = (y1 - (2.54 * (pin_idx + 1)) - self._padding[1])
				pin.set_y(inp_y)
				pin_idx += 1

		pin_idx = 0
		out_y = y0 + 2.54
		for pin in self.pins:
			if (pin.type == PinType.SIGNAL or pin.type == PinType.CLOCK) and pin.dir == PinDir.OUTPUT:
				pin.set_x(x1 + 2.54)
				out_y = (y1 - (2.54 * (pin_idx + 1)) - self._padding[1])
				pin.set_y(out_y)
				pin.set_rot(180)
				pin_idx += 1


		iop_remaining = abs(self._pin_counts[2] - self._pin_counts[3])

		rot = 0
		for pin in self.pins:
			if pin.type == PinType.SIGNAL or pin.type == PinType.CLOCK:
				if pin.dir == PinDir.BIDIRECTIONAL or pin.dir == PinDir.PASSIVE:
					if iop_remaining > 0:
						if inp_y < out_y:
							pin.set_x(x1 + 2.54)
							pin.set_rot(180)
						else:
							pin.set_x(x0 - 2.54)
							pin.set_rot(0)


						pin.set_y(min(inp_y, out_y) + 2.54)

						if inp_y < out_y:
							inp_y += 2.54
						else:
							out_y += 2.54

						iop_remaining -= 1
					else:
						if rot == 0:
							pin.set_x(x0 - 2.54)
							pin.set_y(inp_y)
							pin.set_rot(rot)
							inp_y += 2.54
							rot = 180
						else:
							pin.set_x(x1 + 2.54)
							pin.set_y(out_y)
							pin.set_rot(rot)
							out_y += 2.54
							rot = 0

	def _fixup_properties(self):
		for prop in self.properties:
			if prop.name == 'Value':
				prop.pos = (self._bounds[0], self._bounds[1], 0)
				prop.justify = True


	def __init__(self, name, pins, lef_file_name, bounds = (0.0, 0.0), properties = []):
		self.id = name
		self.pins = pins
		self._pin_counts = None
		self._count_pins()
		self._padding = (0, 0, 0, 0)
		self._bounds = self._calc_bounds()

		self._fixup_pins()

		self.properties = [
			Property('Reference', 'X',           0),
			Property('Value',     name,          1, False),
			Property('Footprint', f'{bounds}',   2),
			Property('Datasheet', lef_file_name, 3),
			*properties
		]

		self._fixup_properties()

	def get_rect(self):
		return f'''\
(rectangle
      (start {self._bounds[0]} {self._bounds[1]})
      (end {self._bounds[2]} {self._bounds[3]})
      (stroke
        (width 0.1)
        (type solid)
        (color 0 0 0 0)
      )
      (fill
        (type background)
      )
    )'''

	def pin_count(self):
		return len(self.pins)

	def pwr_pins(self):
		return self._pin_counts[0]

	def gnd_pins(self):
		return self._pin_counts[1]

	def inp_pins(self):
		return self._pin_counts[2]

	def out_pins(self):
		return self._pin_counts[3]

	def iop_pins(self):
		return self._pin_counts[4]

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f'(cell "{self.id}" {" ".join(map(str, self.pins))})'

class PinDir(Enum):
	INPUT         = auto()
	OUTPUT        = auto()
	TRISTATE      = auto()
	BIDIRECTIONAL = auto()
	PASSIVE       = auto()
	UNSPECIFIED   = auto()

	def __str__(self):
		if self == PinDir.INPUT:
			return 'input'
		elif self == PinDir.OUTPUT:
			return 'output'
		elif self == PinDir.TRISTATE:
			return 'tristate'
		elif self == PinDir.BIDIRECTIONAL:
			return 'bidirectional'
		elif self == PinDir.PASSIVE:
			return 'passive'
		else:
			return 'unspecified'

	@staticmethod
	def from_str(s):
		if s is None:
			return PinDir.BIDIRECTIONAL

		normalized = s.lower()

		if normalized == 'input':
			return PinDir.INPUT
		elif normalized == 'output':
			return PinDir.OUTPUT
		elif 'tristate' in normalized:
			return PinDir.TRISTATE
		elif normalized == 'bidirectional' or normalized == 'inout':
			return PinDir.BIDIRECTIONAL
		elif normalized == 'passive' or normalized == 'feedthru':
			return PinDir.PASSIVE
		else:
			return PinDir.UNSPECIFIED

class PinType(Enum):
	SIGNAL = auto()
	POWER  = auto()
	GROUND = auto()
	CLOCK  = auto()

	def __str__(self):
		if self == PinType.POWER:
			return 'power'
		elif self == PinType.GROUND:
			return 'ground'
		elif self == PinType.CLOCK:
			return 'clock'
		else:
			return 'signal'

	@staticmethod
	def from_str(s):
		if s is None:
			return PinType.SIGNAL
		normalized = s.lower()

		if normalized == 'power':
			return PinType.POWER
		elif normalized == "ground":
			return PinType.GROUND
		elif normalized == 'clock':
			return PinType.CLOCK
		else:
			return PinType.SIGNAL

class Pin:
	def __init__(self, name, d, typ, num = 0):
		self.name = name
		self.number = num
		self.dir = PinDir.from_str(d)
		self.type = PinType.from_str(typ)
		self.pos = (0, 0, 0)

	def set_x(self, x):
		self.pos = (x, self.pos[1], self.pos[2])

	def set_y(self, y):
		self.pos = (self.pos[0], y, self.pos[2])

	def set_rot(self, r):
		self.pos = (self.pos[0], self.pos[1], r)

	def electrical_type(self):
		if self.type == PinType.POWER or self.type == PinType.GROUND:
			return 'power_in'
		else:
			if self.dir == PinDir.INPUT:
				return 'input'
			elif self.dir == PinDir.OUTPUT:
				return 'output'
			elif self.dir == PinDir.TRISTATE:
				return 'tristate'
			elif self.dir == PinDir.BIDIRECTIONAL:
				return 'bidirectional'
			elif self.dir == PinDir.PASSIVE:
				return 'passive'
			else:
				return 'unspecified'

	def graphical_style(self):
		if self.is_clk():
			return 'clock'
		elif self.is_inverted():
			return 'inverted'
		else:
			return 'line'

	def is_clk(self):
		return self.type == PinType.CLOCK

	def is_inverted(self):
		return self.name.lower().split('_')[-1] in ('bar', 'n')

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f'(pin "{self.name}" {self.type} {self.dir})'

def _flatten(col):
	return [i for sl in list(col) for i in sl]

def _flatten_str(col):
	return ''.join(_flatten(col))


def extract(model, cellib: Path, args: Namespace):
	IGNORE_PWR: bool = args.ignore_pwr
	INFER_PWR: bool = not args.dont_infer_pwr
	SPLIT_STR: str = args.split_char
	PDK: str = args.pdk
	STRIP_NAME: bool = not args.dont_strip

	ast = None
	cells = list()

	log.debug(f' ==> Parsing {cellib.name}')
	with cellib.open('r') as lib:
		ast = model.parse(''.join(lib.readlines()))

	if ast is None:
		log.error(f'Error parsing cell library {cellib.name}')
		return None

	log.debug(' ==> Extracting cells')
	for elem in ast[0]:
		macro = None if 'macro' not in elem else elem['macro']
		if macro is not None:
			raw_name = ''.join(macro['name'][0])
			cell_name = raw_name.split(SPLIT_STR)[-1] if SPLIT_STR is not None else raw_name
			if STRIP_NAME:
				cell_name = cell_name.removeprefix(f'{cellib.stem}__')
			log.debug(f' ===> Found cell \'{cell_name}\'')

			cell_pins = list()
			ignored_pins = 0

			log.debug(f' ===> Looking for pins')
			for stmt in macro['mstmts']:
				pin = None if 'pin' not in stmt else stmt['pin']
				if pin is not None:
					pin_name = _flatten_str(pin['name'])
					pin_dir = None
					pin_type = None
					for stmt in pin['pstmnts']:
						if 'dir' in stmt:
							pin_dir = stmt['dir']['pin_dir']
						if 'use' in stmt:
							pin_type = stmt['use']['pin_type']

					if pin_type is None and INFER_PWR:
						if 'vss' in pin_name.lower() or 'gnd' in pin_name.lower():
							pin_type = 'GROUND'
						elif 'vdd' in pin_name.lower() or 'vcc' in pin_name.lower():
							pin_type = 'POWER'

					if IGNORE_PWR and pin_type in ('GROUND', 'POWER'):
						ignored_pins += 1
						continue

					cell_pins.append(Pin(
						pin_name, pin_dir, pin_type, num = len(cell_pins)
					))

			log.debug(f' ===> Found {len(cell_pins)} pins in cell \'{cell_name}\' ({ignored_pins} ignored)')

			bounds     = (0.0, 0.0)
			origin     = (0.0, 0.0)
			cell_class = ''
			foreign    = ''
			symmetry   = ''

			for stmt in macro['mstmts']:
				if 'size'     in stmt:
					bounds = (
						float(_flatten_str(stmt['size'][2])),
						float(_flatten_str(stmt['size'][5])),
					)
				if 'origin'   in stmt:
					origin = (
						float(_flatten_str(stmt['origin'][2]['x'])),
						float(_flatten_str(stmt['origin'][2]['y'])),
					)
				if 'class'    in stmt:
					cell_class = stmt['class']['type']
				if 'foreign'  in stmt:
					foreign = _flatten_str(stmt['foreign']['name'])
				if 'symmetry' in stmt:
					symmetry = _flatten_str(stmt['symmetry'][1])


			cells.append(Cell(
				cell_name, cell_pins, cellib.name,
				bounds = bounds, properties = (
					Property('Cell Class',    f'{cell_class}',  10),
					Property('Foreign Cell',  f'{foreign}',     11),
					Property('Cell Origin',   f'{origin}',      12),
					Property('Cell Size',     f'{bounds}',      13),
					Property('Cell Symmetry', f'{symmetry}',    14),
					Property('Cell PDK',      f'{PDK}',         15),
					Property('Cell Library',  f'{cellib.stem}', 16)
				)
			))

	log.info(f' ==> Found {len(cells)} cells in {cellib.stem}')
	return cells


def collect_lefs(args: Namespace):
	PDK: str = args.pdk
	PDK_ROOT: Path = args.pdk_root
	PDK_PATH   = (PDK_ROOT / PDK)
	PDK_REFLIB = (PDK_PATH / 'libs.ref')
	SKIP_SRAM: bool = args.skip_sram

	lef_files = list()

	log.info(f'Collecting LEF files from \'{PDK}\'')
	log.debug(f'PDK_ROOT: {PDK_ROOT}, PDK: {PDK}')

	if not PDK_PATH.exists() or not PDK_REFLIB.exists():
		log.error(f'Unable to find PDK {PDK} in PDK_ROOT: {PDK_ROOT}')
		return None

	for cellib in PDK_REFLIB.iterdir():
		log.info(f' => Found Cell library \'{cellib.name}\'')

		if SKIP_SRAM and 'sram' in cellib.name.lower():
			log.info(' ==> Skipping cell library, likely contains SRAM cells')
			continue

		CELL_LEFS = (cellib / 'lef')
		if not CELL_LEFS.exists():
			log.warning(f' => Cell library \'{cellib.name}\' has no LEF files, skipping...')
			continue

		for lef in CELL_LEFS.iterdir():
			if lef.suffix.lower() == '.lef':
				log.debug(f' => Found LEF file \'{lef}\'')
				lef_files.append(lef)

	log.info(f'Found {len(lef_files)} LEF files for PDK')
	return lef_files

def process_lefs(args: Namespace, lefs: list[Path]):
	OUTDIR: Path = args.outdir
	PDK: str = args.pdk
	SKIP: bool = args.skip_existing
	FLATTEN: bool = args.flatten
	JOBS: int = args.jobs

	if not FLATTEN:
		OUTDIR = (OUTDIR / PDK)

	if not OUTDIR.exists():
		OUTDIR.mkdir(exist_ok = True, parents = True)

	log.info('Processing LEFs')

	log.info('Compiling TatSu parser, this might take a minute')
	model = tatsu.compile(LEF_TATSU)

	log.info('Processing cell libraries, this will take a while.')
	def _process_cell_lib(cellib: Path):
		if FLATTEN:
			KISYM_LIB = (OUTDIR / f'{PDK}_{cellib.stem}.kicad_sym')
		else:
			KISYM_LIB = (OUTDIR / f'{cellib.stem}.kicad_sym')

		if KISYM_LIB.exists() and SKIP:
			log.info(f' => Cell library {KISYM_LIB.name} already exists, skipping')
			return

		log.info(f' => Processing Cell Library \'{PDK}/{cellib.stem}\'')
		cells = extract(model, cellib, args)
		if cells is not None:
			log.info(f' => Writing KiCad symbols to \'{KISYM_LIB.name}\'')

			log.debug(' ==> Rendering Symbol Library')
			symfile = KISYM_TEMPLATE.render(
				name     = cellib.stem,
				lef_file = cellib.name,
				symbols  = cells
			)

			log.debug(f' ==> Writing to \'{KISYM_LIB}\'')
			with KISYM_LIB.open('w') as sym:
				sym.write(symfile)
				sym.write('\n')

	if JOBS == 1:
		for cellib in lefs:
			_process_cell_lib(cellib)
		return 0
	else:
		futures = list()
		with ThreadPoolExecutor(max_workers = JOBS) as pool:
			for cellib in lefs:
				futures.append(pool.submit(
					_process_cell_lib, cellib
				))

		return all(map(lambda f: f.result(), futures))


def main():
	traceback.install()
	_setup_logging()

	parser = ArgumentParser(
		prog            = 'pdk2kicad',
		description     = 'Generate KiCad symbol libraries from an open_pdk PDK',
		formatter_class = ArgumentDefaultsHelpFormatter
	)

	core_options    = parser.add_argument_group('Core Options')
	parsing_options = parser.add_argument_group('Parsing Options')
	pdk_options     = parser.add_argument_group('PDK Options')
	symbol_options  = parser.add_argument_group('PDK Options')

	core_options.add_argument(
		'--verbose', '-v',
		action = 'store_true',
		help   = 'Enable verbose output'
	)

	core_options.add_argument(
		'--outdir', '-o',
		type    = str,
		default = Path.cwd() / 'symbols',
		help    = 'output directory for kicad_sym files'
	)

	core_options.add_argument(
		'--skip-existing', '-S',
		action = 'store_true',
		help   = 'Skip ingestion and parsing of a LEF file if the .kicad_sym file already exists'
	)

	core_options.add_argument(
		'--jobs', '-j',
		type    = int,
		default = 1,
		help    = 'Number of independant threads to run'
	)

	parsing_options.add_argument(
		'--ignore-pwr', '-I',
		action = 'store_true',
		help   = 'Ignore power pins from cells'
	)

	parsing_options.add_argument(
		'--dont-infer-pwr', '-i',
		action  = 'store_true',
		default = False,
		help    = 'Don\'t try to infer power signals based on name id pin has no type'
	)

	parsing_options.add_argument(
		'--split-char', '-s',
		type = str,
		help = 'The characters to split cell names on, (such as `__`), the left most element will be selected as the cell name'
	)

	pdk_options.add_argument(
		'--pdk-root',
		type    = Path,
		default = environ.get('PDK_ROOT', None),
		help    = 'The PDK Root',
	)

	pdk_options.add_argument(
		'--pdk', '-p',
		type     = str,
		choices  = (
			'sky130A', 'sky130B',
			'gf180mcuA', 'gf180mcuB', 'gf180mcuC', 'gf180mcuD'
		),
		default  = 'sky130B',
		help     = 'The PDK to generate the KiCad libraries for.'
	)

	pdk_options.add_argument(
		'--skip-sram',
		action  = 'store_true',
		default = False,
		help    = 'Skip libraries with \'sram\' in the name, might improve speed.'
	)

	symbol_options.add_argument(
		'--flatten', '-f',
		action  = 'store_true',
		default = False,
		help    = 'Flatten the directory structure for the output symbol libraries'
	)

	symbol_options.add_argument(
		'--spice',
		action  = 'store_true',
		default = False,
		help    = 'Attempt to extract and then embed SPICE info in the symbol files'
	)

	symbol_options.add_argument(
		'--dont-strip', '-D',
		action  = 'store_true',
		default = False,
		help    = 'Don\'t strip the cell library name from the cell'
	)

	args = parser.parse_args()
	_setup_logging(args)

	if not args.pdk_root.exists():
		log.error(f'PDK_ROOT {args.pdk_root} does not exist!')
		return 1

	log.info(f'Generating KiCad symbol libraries for PDK {args.pdk}')
	log.info('This might take some time...')

	lefs = collect_lefs(args)
	if lefs is None:
		log.error('PDK had no LEF files, aborting')
		return 1

	return process_lefs(args, lefs)



if __name__ == '__main__':
	sys.exit(main())
