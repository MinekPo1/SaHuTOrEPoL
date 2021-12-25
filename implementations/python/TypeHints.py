from typing import Literal, TypeAlias, TypedDict


class AST:
	class Element(TypedDict):
		pos: tuple[int, int]

	class Root(Element):
		type: Literal['root']
		children: list["AST.Elements"]
		type_defs:dict[str,"AST.TypeDef"]

	class If(Element):
		type: Literal['if']
		expresion: "AST.Expresion"
		children: list["AST.Elements"]

	class While(Element):
		type: Literal['while']
		expresion: "AST.Expresion"
		children: list["AST.Elements"]

	class TypeDef(Element):
		type: Literal['type_def']
		name: str
		children: list["AST.Elements"]

	class EmptyVarDef(Element):
		type: Literal['var_def']
		name: str

	class FuncOrMethodDef(Element):
		type: Literal['func_def']
		name: str
		args: list[str]
		children: list["AST.Elements"]

	VarDef: TypeAlias = EmptyVarDef | FuncOrMethodDef

	class VarSet(Element):
		type: Literal['var_set']
		name: str
		value: "AST.Expresion"

	class MethodCall(Element):
		type: Literal['method_call']
		name: str
		args: list["AST.Expresion"]

	class Expresions:
		class Base(TypedDict):
			pos: tuple[int, int]

		class Multi(Base):
			type: Literal['multi_expression']
			expressions: list["AST.Expresion"]

		class Var(Base):
			type: Literal['var_expression']
			name: str

		class Literal_(Base):
			type: Literal['literal_expression']
			value: "AST.Expresions.LiteralValue"

		class LiteralValues:
			class s(TypedDict):
				type: Literal['s']
				value: str

			class i(TypedDict):
				type: Literal['i']
				value: int

			class f(TypedDict):
				type: Literal['f']
				value: float

			class b(TypedDict):
				type: Literal['b']
				value: bool

			any: TypeAlias = s | i | f | b

		class FunctionCall(Base):
			type: Literal['function_call']
			name: str
			args: list["AST.Expresion"]

		LiteralValue: TypeAlias = LiteralValues.any

	Expresion: TypeAlias = Expresions.Multi | Expresions.Var \
		| Expresions.Literal_ | Expresions.FunctionCall

	Elements: TypeAlias = Root | While | If | VarDef | VarSet\
		| MethodCall
	Contexts: TypeAlias = Root | While | If | FuncOrMethodDef | TypeDef
