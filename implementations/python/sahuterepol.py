from typing import Optional
import re
from simple_warnings import catch_warnings, warn, print_warning

from Types import NamespaceContext
import Types
import TypeHints


class SaHuTOrEPoLError(Exception):
	"""
		Error raised by the parser or interpreter.
	"""
	pos: tuple[int, int]

	def __init__(self, message, pos) -> None:
		self.message = message
		self.pos = pos

	def __str__(self) -> str:
		return (
			f"{self.message} "
			f"at line {self.pos[0]}, column {self.pos[1]}"
		)

	def __repr__(self) -> str:
		return (
			f"{type(self).__name__}:{self.message} "
			f"at line {self.pos[0]}, column {self.pos[1]}"
		)


class SaHuTOrEPoLWarning(Warning):
	"""
		Warning raised by the parser or interpreter.
	"""
	pos: tuple[int, int]

	def __init__(self, message, pos) -> None:
		self.message = message
		self.pos = pos

	def __str__(self) -> str:
		return (
			f"{self.message} "
			f"at line {self.pos[0]}, column {self.pos[1]}"
		)

	def __repr__(self) -> str:
		return (
			f"{type(self).__name__}:{self.message} "
			f"at line {self.pos[0]}, column {self.pos[1]}"
		)


class CodePointer(object):
	def __init__(self,code:str) -> None:
		self.code = iter(code)
		self.column = 0
		self.line = 1

	@property
	def pos(self) -> tuple[int, int]:
		return self.line, self.column

	def __next__(self) -> str:
		c = next(self.code)
		if c == '\n':
			self.column = 0
			self.line += 1
		else:
			self.column += 1
		return c


class RegexBank:
	variable_name = r'[a-zA-Z_]+'
	variable = rf'{variable_name}(-{variable_name})*'
	type_name = r'[a-zA-Z]'
	i_literal = r'[1-9]\d*'
	f_literal = r'[1-9]\d*\.(\d*[1-9]|0)'
	b_literal = r'(yes|no)'
	s_literal = r'(?P<s>[\"\'])[^\n\r]*(?P=s)'


def check_var_name(name:str) -> tuple[bool,Optional[str]]:
	if "-" in name:
		# split the name into its parts
		parts = [check_var_name(i) for i in name.split("-")]

		return(
			all(i[0] for i in parts),
			(parts[-1][1] if all(i[1] for i in parts) else None)
		)
	if len(name) < 3 or len(name) > 8:
		return False, None
	if not(re.fullmatch(r"[a-zA-Z]*\_[a-zA-Z]*\_[a-zA-Z]*$",name)):
		return False, None
	t = name.replace("_", "")[0]
	return len(name) < 6, t


class Code(object):
	ast: TypeHints.AST.Root

	def __init__(self,ast: TypeHints.AST.Root) -> None:
		self.ast = ast

	def resolve_expr(self,expr: TypeHints.AST.Expresion) -> Types.TypeLike:
		context: NamespaceContext
		context = NamespaceContext.get_current_context()
		match expr:
			case {"type": "multi_expression", "expressions": list(e)}:
				elements = [self.resolve_expr(i) for i in e]
				obj = type(elements[0])(elements.pop(0),elements.pop())
				while elements:
					obj = type(obj)(obj,elements.pop())
				return obj
			case {"type": "var_expression", "name": name}:
				return context.vars[name]
			case {"type": "literal_expression", "value": value}:
				return context.types[value['type']](value['value'])  # type:ignore
			case {"type":"function_call", "name": name, "args": list(args)}:
				args = [self.resolve_expr(i) for i in args]
				f = context.vars[name]
				if not isinstance(f,(Types.f,Types.BuiltinFunction)):
					raise SaHuTOrEPoLError(f"{name} is not a function",expr['pos'])
				return f(*args)
			case _:
				raise SaHuTOrEPoLError(f"Unknown expression type {expr}", expr['pos'])

	def _run(self,ast: TypeHints.AST.Contexts) -> None:
		context: NamespaceContext
		context = NamespaceContext.get_current_context()
		for i in ast['children']:
			match i:
				case {"type": "var_def", "name": name}:
					v,t = check_var_name(name)
					if t is None:
						raise SaHuTOrEPoLError("Invalid type name",i['pos'])
					if t not in context.types:
						raise SaHuTOrEPoLError(f"Unknown type {t}",i['pos'])
					t = context.types[t]
					if not issubclass(t,Types.Type):
						raise SaHuTOrEPoLError(f"{t} is not a type",i['pos'])
					context.vars[name] = t()
				case {
					"type": "func_def", "name": name, "args": list(args), "children": children
				}:
					v,t = check_var_name(name)
					if t is None:
						raise SaHuTOrEPoLError("Invalid type name",i['pos'])
					if t not in "fm":
						raise SaHuTOrEPoLError(
							f"Type {t} cannot be defined in this way.",
							i['pos']
						)
					if t == "f":
						context.vars[name] = Types.f(children,args)
					else:
						context.vars[name] = Types.m(children,args)
				case {"type": "method_call", "name": name, "args": list(args)}:
					v,t = check_var_name(name)
					if t is None:
						raise SaHuTOrEPoLError("Invalid type name",i['pos'])
					f = context.vars[name]
					if not isinstance(
						f,
						(Types.f,Types.BuiltinFunction,Types.m,Types.BuiltinMethod)
					) and not(callable(f)):
						raise SaHuTOrEPoLError(f"{f!r} is not callable",i['pos'])
					args = [self.resolve_expr(i) for i in args]
					f(*args)
				case {"type": "while", "condition": condition, "children": children}:
					while self.resolve_expr(condition):
						self._run(children)
				case {"type": "if", "condition": condition, "children": children}:
					if self.resolve_expr(condition):
						self._run(children)
				case {"type": "var_set", "name": name, "value": value}:
					if name in context.vars:
						context.vars[name] = self.resolve_expr(value)
					else:
						raise SaHuTOrEPoLError(f"Unknown variable {name}",i['pos'])

	def run(self) -> None:
		with Types.NamespaceContext():
			self._run(self.ast)


def parse_expr(expr:str,pos: tuple[int,int]) -> TypeHints.AST.Expresion:
	# remove unesery brackets
	expr = expr.strip(" \t()")
	if "." in expr:
		split_expr: list[str] = [""]
		brackets: int = 0
		for i in expr:
			if i == "(":
				brackets += 1
				split_expr[-1] += i
			elif i == ")":
				brackets -= 1
				split_expr[-1] += i
			elif i == "." and brackets == 0:
				split_expr.append("")
			else:
				split_expr[-1] += i

		return {
			'type': 'multi_expression',
			'expressions': [parse_expr(i,pos) for i in split_expr],
			'pos': pos
		}
	if re.fullmatch(RegexBank.variable,expr):
		return {
			'type': 'var_expression',
			'name': expr,
			'pos': pos
		}
	if m:=re.fullmatch(rf"({RegexBank.variable})\((.)\)",expr):
		return {
			'type': 'function_call',
			'name': m.group(1),
			'args': [parse_expr(m.group(3),pos)],
			'pos': pos
		}
	if re.fullmatch(RegexBank.i_literal,expr):
		return {
			'type': 'literal_expression',
			'value': {
				'type': 'i',
				'value':int(expr),
			},
			'pos': pos
		}
	if re.fullmatch(RegexBank.f_literal,expr):
		return {
			'type': 'literal_expression',
			'value': {
				'type': 'f',
				'value':float(expr),
			},
			'pos': pos
		}
	if re.fullmatch(RegexBank.s_literal,expr):
		return {
			'type': 'literal_expression',
			'value': {
				'type': 's',
				'value':expr[1:-1],
			},
			'pos': pos
		}
	if re.fullmatch(RegexBank.b_literal,expr):
		return {
			'type': 'literal_expression',
			'value': {
				'type': 'b',
				'value':expr == "yes",
			},
			'pos': pos
		}
	raise SaHuTOrEPoLError(f"Invalid expression: {expr}",pos)


happyness_warning_messages = {
	14:  "Parser is made slightly sad",
	10:  "Parser is made quite sad",
	5:   "Parser is made very sad",
	0:   "Parser is made extremely sad",
	-2:  "Parser disappointed but not surprised",
	-8:  "Parser is somehow surprised again",
	-15: "Parser asks for the meaning of life",
	-25: "The parser asks for you to pay for its therapy",
	-50: "<Message that makes you feel bad>",
	-75:
		"Wow do these warnings not irritate you?"
		"This is the tenth and final one!",
	-76:"Ok this is actually the final low happyness warning message"
}


def parse(code:str) -> TypeHints.AST.Root:  # sourcery no-metrics

	ptr = CodePointer(code)

	tree: TypeHints.AST.Root = {
		"pos": (0,0),
		"type": "root",
		"children": [],
		"type_defs": {},
	}
	happines = 15
	symbol = ""
	cur_indent = 0
	context: list[TypeHints.AST.Contexts] = [tree]
	p_do = False
	e_do = False
	while True:
		c = next(ptr, None)
		if p_do:
			if c != "\n":
				happines -= 1
				if happines in happyness_warning_messages:
					warn(
						SaHuTOrEPoLWarning(
							happyness_warning_messages[happines],
							ptr.pos
						)
					)
			p_do = False

		if c is None:
			break
		if symbol == "":
			if c == "\t" and cur_indent % 1 == 0:
				cur_indent += 0.5
			elif c == " " and cur_indent % 1 == 0.5:
				cur_indent += 0.5
			elif c in " \t":
				raise SaHuTOrEPoLError(
					"Invalid indentation."
					"An indentation level must be tabulator followed by a space.",
					ptr.pos
				)
			elif c == "\n":
				cur_indent = 0
			else:
				if cur_indent % 1 == 0.5:
					raise SaHuTOrEPoLError(
						"Indent not completed",
						ptr.pos
					)
				if cur_indent > len(context) - 1:
					raise SaHuTOrEPoLError(
						"Unexpected indent",
						ptr.pos
					)
				if cur_indent <= len(context) - 2:
					e_do = True
				symbol += c
		elif c in " \t" and symbol[-1] in " \t":
			pass
		elif c in " \t\n":
			symbol += " "
		else:
			symbol += c

		if re.fullmatch(r" ?\$\$",symbol):
			while c != "\n" and c is not None:
				c = next(ptr, None)
			symbol = ""

		if e_do:
			if symbol == "do":
				context.pop()
				e_do = False
				p_do = True
				symbol = ""

				if cur_indent <= len(context) - 2:
					raise SaHuTOrEPoLError(
						"Unexpected de-indent",
						ptr.pos
					)

			if len(symbol) == 2:
				raise SaHuTOrEPoLError(
					"Unexpected indent",
					ptr.pos
				)
			continue

		if context[-1]['type'] != "type_def":
			if m:=re.fullmatch(rf"({RegexBank.variable})\$(.+)do",symbol):
				name = m.group(1)
				args = m.group(2)
				print(f"{symbol=} {name=} {args=}")
				v,t = check_var_name(name)
				if t is None:
					raise SaHuTOrEPoLError(
						f"Invalid variable name {name!r}",
						ptr.pos
					)
				if not(v):
					warn(
						SaHuTOrEPoLWarning(
							f"Variable name {name!r} longer than the recommended five characters",
							ptr.pos
						)
					)
				context[-1]['children'].append({
					'type': 'var_set',
					'name': name,
					'value': parse_expr(args,ptr.pos),
					'pos': ptr.pos,
				})
				symbol = ""
				p_do = True

			if m:=re.fullmatch(rf"({RegexBank.variable})\((.+)\) do",symbol):
				name = m.group(1)
				args = m.group(3)
				v,t = check_var_name(name)
				if t is None:
					raise SaHuTOrEPoLError(
						f"Invalid variable name {name!r}",
						ptr.pos
					)
				if not(v):
					warn(
						SaHuTOrEPoLWarning(
							f"Variable name {name!r} longer than the recommended five characters",
							ptr.pos
						)
					)
				if t not in "fm":
					raise SaHuTOrEPoLError(
						f"Invalid variable type {t!r}",
						ptr.pos
					)
				context[-1]['children'].append(
					{
						'type': 'method_call',
						'name': name,
						'args': [parse_expr(i,ptr.pos) for i in args.split(",")],
						'pos': ptr.pos,
					}
				)
				symbol = ""
				p_do = True

			if m:=re.fullmatch(r'if ?\((.)\)',symbol):
				args = m.group(1)
				context[-1]['children'].append({
					'type': 'if',
					'expresion': parse_expr(args,ptr.pos),
					'children': [],
					'pos': ptr.pos,
				})
				context.append(context[-1]['children'][-1])  # type:ignore
				symbol = ""

			if m:=re.fullmatch(r'while ?\((.)\)',symbol):
				args = m.group(1)
				context[-1]['children'].append({
					'type': 'while',
					'expresion': parse_expr(args,ptr.pos),
					'children': [],
					'pos': ptr.pos,
				})
				context.append(context[-1]['children'][-1])  # type:ignore
				symbol = ""

		if context[-1]['type'] == "root":
			if m:=re.fullmatch(rf"type ?({RegexBank.type_name})",symbol):
				name = m.group(1)
				tree['type_defs'][name] = {
					'type': 'type_def',
					'name': name,
					'pos': ptr.pos,
					'children': [],
				}
				context.append(tree['type_defs'][name])
				symbol = ""

		if m:=re.fullmatch(rf"\$({RegexBank.variable}) do",symbol):
			name = m.group(1)
			v,t = check_var_name(name)
			if t is None:
				raise SaHuTOrEPoLError(
					f"Invalid variable name {name!r}",
					ptr.pos
				)
			if not(v):
				warn(
					SaHuTOrEPoLWarning(
						f"Variable name {name!r} longer than the recommended five characters",
						ptr.pos
					)
				)
			context[-1]['children'].append({
				'type': 'var_def',
				'name': name,
				'pos': ptr.pos,
			})
			symbol = ""
			p_do = True

		if m:=re.fullmatch(rf"\$({RegexBank.variable}) ?\((.+)\)",symbol):
			name = m.group(1)
			args = m.group(3)
			v,t = check_var_name(name)
			if t is None:
				raise SaHuTOrEPoLError(
					f"Invalid variable name {name!r}",
					ptr.pos
				)
			if not(v):
				warn(
					SaHuTOrEPoLWarning(
						f"Variable name {name!r} longer than the recommended five characters",
						ptr.pos
					)
				)
			if t not in "fn":
				raise SaHuTOrEPoLError(
					f"Invalid variable type {t!r}",
					ptr.pos
				)
			context[-1]['children'].append({
				'type': 'func_def',
				'name': name,
				'args': (args.split(",")),
				'children': [],
				'pos': ptr.pos,
			})
			context.append(context[-1]['children'][-1])  # type:ignore
			symbol = ""

	if symbol != "":
		raise SaHuTOrEPoLError(
			f"Unexpected end of file, {symbol!r} left hanging",
			ptr.pos
		)

	return tree


def show_error_or_warning(error: SaHuTOrEPoLError | SaHuTOrEPoLWarning,
		file: str):
	"""
	Show the error message and the code snippet where it occurred.
	"""
	with open(file,"r") as f:
		lines = f.readlines()
		print(
			f"{'Error' if isinstance(error,SaHuTOrEPoLError) else 'Warning'}: "
			f"{error.message} at {error.pos}"
		)
		try:
			print(f"{error.pos[0]: >3}|{lines[error.pos[0]-1][:-1]}")
			print(" "*(error.pos[1]+3)+"^ here")
		except IndexError:
			pass


help_s = {
tuple(): """
	Usage:
	sahutorepol parse [<options>] <file> [<output>]
	sahutorepol check [<options>] <file>
	sahutorepol run [<options>] <file>
	sahutorepol help [<command>]
""",
("help",): """
	Usage:
	sahutorepol parse [<options>] <file> [<output>]
	sahutorepol run [<options>] <file>
	sahutorepol help [<command>]

	Common options:
	-s  silent, don't show warnings
	-S  strict, if any warning is found, do not continue
	-r  raise, if any error or warning is found, raise it instead of showing it
""",
("help", "parse"): """
	Usage:
	sahutorepol parse [<options>] <file> [<output>]

	Options:
	-s  silent, don't show warnings
	-S  strict, if any warning is found, do not continue
	-r  raise, if any error or warning is found, raise it instead of showing it
	-y  yaml, output the parsed tree in yaml format, else use json
""",
("help", "check"): """
	Usage:
	sahutorepol parse [<options>] <file> [<output>]

	Options:
	-s  silent, don't show warnings
	-S  strict, if any warning is found, do not continue
	-r  raise, if any error or warning is found, raise it instead of showing it
	-p  parsable, output the error and/or warnings in parsable format
	-y  yaml, output the parsable output in yaml format, else use json
""",
("help", "run"): """
	Usage:
	sahutorepol run [<options>] <file>

	Options:
	-s  silent, don't show warnings
	-S  strict, if any warning is found, do not continue
	-r  raise, if any error or warning is found, raise it instead of showing it

"""

}


def main(*args):
	import sys
	import json
	import yaml

	match args:
		case ["parse", options, file, output]:
			method = "parse"
		case ["parse", options, file]:
			method = "parse"
			output = None
		case ["parse", file]:
			method = "parse"
			options = ""
			output = None

		case ["run", options, file]:
			method = "run"
			output = None
		case ["run", file]:
			method = "run"
			options = ""
			output = None

		case ["check", options, file]:
			method = "check"
			output = None
		case ["check", file]:
			method = "check"
			options = ""
			output = None

		case _:
			if tuple(args[:2]) in help_s:
				print(help_s[tuple(args[:2])])
			else:
				print(help_s[tuple()])
			sys.exit(0)

	match method:
		case "parse":
			with open(file) as f:
				err = False
				with catch_warnings(record=True) as w:
					try:
						t = parse(f.read())
					except SaHuTOrEPoLError as ex:
						if "r" in options:
							raise ex
						t = None
						show_error_or_warning(ex,file)
						err = True
				if "s" not in options:
					for warning in w:
						if isinstance(warning,SaHuTOrEPoLWarning) and "s" not in options:
							show_error_or_warning(warning,file)
						else:
							print_warning(warning)
					if "S" in options and w:
						err = True
				if err:
					sys.exit(1)
				if t is None:
					raise RuntimeError
				if "y" in options:
					dump = yaml.dump(t,default_flow_style=False)
				else:
					dump = json.dumps(t,indent=2)
				if output is None:
					print(dump)
				elif "n" not in options:
					with open(output,"w") as f:
						f.write(dump)

		case "check":
			with open(file) as f:
				data = []
				err = False
				with catch_warnings(record=True) as w:
					try:
						parse(f.read())
					except SaHuTOrEPoLError as ex:
						if "r" in options:
							raise ex
						if "p" in options:
							data.append(
								{
									"type": "error",
									"message": ex.message,
									"pos": ex.pos
								}
							)
							err = True
						else:
							show_error_or_warning(ex,file)
							err = True
				if "s" not in options:
					for warning in w:
						if isinstance(warning,SaHuTOrEPoLWarning) and "s" not in options:
							if "p" in options:
								data.append(
									{
										"type": "warning",
										"message": warning.message,
										"pos": warning.pos,
									}
								)
							show_error_or_warning(warning,file)
						else:
							print_warning(warning)
					if "S" in options and w:
						err = True
				if "p" in options:
					if "y" in options:
						dump = yaml.dump(data,default_flow_style=False)
					else:
						dump = json.dumps(data,indent=2)

					print(dump)
				if err:
					sys.exit(1)

		case "run":
			with open(file) as f:
				err = False
				with catch_warnings(record=True) as w:
					try:
						t = parse(f.read())
					except SaHuTOrEPoLError as ex:
						if "r" in options:
							raise ex
						show_error_or_warning(ex,file)
						t = None
						err = True
				if "s" not in options:
					for warning in w:
						if isinstance(warning,SaHuTOrEPoLWarning) and "s" not in options:
							show_error_or_warning(warning,file)
						else:
							print_warning(warning)
					if "S" in options and w:
						err = True
				if err:
					sys.exit(1)
				if t is None:
					raise RuntimeError
				Code(t).run()


if __name__ == "__main__":
	import sys
	main(*sys.argv[1:])
