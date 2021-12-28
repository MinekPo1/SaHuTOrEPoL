
from abc import ABC, abstractmethod
import re
from typing import IO, TYPE_CHECKING, Any, Callable, ClassVar, Generic,\
	Literal, Optional, Protocol, Type as LType, TypeVar, overload
from typing import TypeAlias
import warnings
import sys


T = TypeVar('T','Type','i')
TRet = TypeVar('TRet', 'LType[Type]', 'None')


def check_compatability():
	locals()['a'] = 0
	if 'a' not in locals():
		raise Exception(
			"Your python version is not compatible with this module"
			"due to `local` behavior."
		)


class NamespaceContext(object):
	previous: Optional["NamespaceContext"]
	is_builtin = False
	vars: "Vars"
	types: "Types"

	class Vars(object):
		def __init__(self,namespace: "NamespaceContext") -> None:
			self.namespace = namespace
			self._vars = {}
			if namespace.previous is None:
				self._g_vars = {}
			else:
				self._g_vars = namespace.previous.vars._g_vars

		def __getitem__(self,key:str) -> "TypeLike":
			if "-" in key:
				keys = key.split("-")
				obj = self[keys[0]]
				for k in keys[1:]:
					obj = getattr(obj,k)
				return obj

			if key in self._g_vars:
				return self._g_vars[key]

			if key in self._vars:
				return self._vars[key]

			p = self.namespace
			while p.previous is not None:
				p = p.previous
				if key in p.vars._vars:
					return p.vars._vars[key]

			raise KeyError(f"variable {key} not in namespace")

		def __setitem__(self,key:str,value:"TypeLike") -> None:
			if key[0] == "_":
				self._vars[key] = value
				return

			self._g_vars[key] = value

		def __contains__(self,key:str) -> bool:
			if key in self._g_vars:
				return True

			if key in self._vars:
				return True

			p = self.namespace
			while p.previous is not None:
				p = p.previous
				if key in p.vars._vars:
					return True

			return False

	class Types(object):
		_types: dict[str,LType["Type"]]

		def __init__(self,namespace: "NamespaceContext") -> None:
			self.namespace = namespace
			if namespace.previous is None:
				self._types = {}
			else:
				# all types are global so
				self._types = namespace.previous.types._types

		def __getitem__(self,key:str) -> LType["Type"]:
			if key in self._types:
				return self._types[key]
			elif not(self.namespace.is_builtin):
				return builtin_namespace.types._types[key]
			raise KeyError(key)

		def __setitem__(self,key:str,value:"LType[Type]") -> None:
			if key in self._types and isinstance(self._types[key],_FutureType):
				self._types[key].ref = value  # type:ignore
			self._types[key] = value

		def __contains__(self,key:str) -> bool:
			if key in self._types:
				return True
			if not(self.namespace.is_builtin):
				return key in builtin_namespace.types._types
			return False

	def __init__(self) -> None:
		self.local_ref = sys._getframe(1).f_locals

	def __enter__(self) -> 'NamespaceContext':
		if not(self.is_builtin):
			self.previous = self.get_current_context()
		else:
			self.previous = None
		self.vars = self.Vars(self)
		self.types = self.Types(self)
		self.local_ref['namespace_context'] = self
		return self

	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		self.local_ref['namespace_context'] = self.previous

	@classmethod
	def get_current_context(cls) -> "NamespaceContext":
		try:
			if context is not None:  # type:ignore
				return context   # type:ignore
		except NameError:
			pass

		i = 0
		while True:
			try:
				c = sys._getframe(i).f_locals.get('context',None)
			except ValueError:
				return builtin_namespace

			if c is not None:
				return c
			i += 1


class _FutureType(type):
	is_future: Literal[True] = True

	class Typed(Protocol):
		is_future: Literal[True]

	def __new__(cls,name:str) -> "_FutureType":
		return super().__new__(
			cls,
			name,
			(object,),
			{
				"name": name,
				"is_future": True,
			}
		)

	def __init__(self,name:str) -> None:
		self.name = name
		self.context = NamespaceContext.get_current_context()
		self.__qualname__ = f"Futute[{self.__qualname__}]"
		self.ref = None


class TypeReference(object):
	def __init__(self,ref: "LType[Type] | _FutureType") -> None:
		self._ref = ref

	@property
	def ref(self) -> "LType[Type] | _FutureType":
		if isinstance(self._ref, _FutureType) and self._ref.ref is not None:
			self._ref = self._ref.ref
		return self._ref


builtin_namespace = NamespaceContext()
builtin_namespace.is_builtin = True
builtin_namespace.__enter__()

for name in "s i n b S q t f m".split():
	builtin_namespace.types[name] = _FutureType(name)  # type:ignore


method = type(builtin_namespace.get_current_context)


def check_var_name(name:str) -> tuple[bool,str] | tuple[Literal[False],None]:
	if len(name) < 3 or len(name) > 8:
		return False, None
	if not(re.fullmatch(r"[a-zA-Z]*_[a-zA-Z]*_[a-zA-Z]*",name)):
		return False, None
	t = name.replace("_", "")[0]
	return len(name) < 6, t


WarpedMethodOrFunction = TypeVar(
	"WarpedMethodOrFunction",
	"BuiltinMethodOrFunction",
	"MethodOrFunction"
)
ReturnType = TypeVar("ReturnType", "LType[Type]", "None")


class MethodOrFunction(ABC, Generic[ReturnType]):
	__name__: str = ""
	__qualname__: str = ""
	__doc__: str = ""
	alias_type = None
	return_type: "LType[ReturnType]"
	arg_types: list["TypeReference | Literal['self']"]

	@abstractmethod
	def __call__(self, *args: "TypeLike") -> ReturnType:
		...


class BoundMethodOrFunction(
		MethodOrFunction,
		Generic[WarpedMethodOrFunction, ReturnType]
	):
	wrapped: "Optional[WarpedMethodOrFunction]"
	obj: "TypeLike"
	alias_type = None
	return_type: "LType[ReturnType]"

	def __init__(self,obj,wrapped:WarpedMethodOrFunction = None) -> None:
		self.obj = obj
		self.wrapped = wrapped
		if wrapped is not None:
			self.__name__ = wrapped.__name__
			self.__qualname__ = wrapped.__qualname__
			self.__doc__ = wrapped.__doc__
			self.arg_types = wrapped.arg_types
			self.return_type = wrapped.return_type

	@overload
	def __call__(self, *args: "TypeLike | ConvType") -> ReturnType:
		...

	@overload
	def __call__(self, wrapped: WarpedMethodOrFunction)\
			-> "BoundMethodOrFunction[WarpedMethodOrFunction,TRet]":
		...

	def __call__(self, *args):
		if self.wrapped is None:
			self.__name__ = args[0].__name__
			self.__qualname__ = args[0].__qualname__
			self.__doc__ = args[0].__doc__
			self.wrapped = args[0]
			self.arg_types = args[0].arg_types
			self.return_type = args[0].return_type
			return self
		return self.wrapped(self.obj,*args)

	def __repr__(self) -> str:
		return f"<BoundMethodOrFunction {self.__qualname__} of {self.obj!r}>"


class BuiltinMethodOrFunction(MethodOrFunction):
	type_n: ClassVar[str]

	def __init__(self,wrapped: Callable) -> None:
		self.arg_types = []
		arg_names = []
		context = NamespaceContext.get_current_context()
		if context is None:
			raise ValueError("No context found")

		names_to_check = wrapped.__code__.co_varnames
		names_to_check = names_to_check[:wrapped.__code__.co_argcount]

		for i in names_to_check:
			if i == 'self':
				self.arg_types.append('self')
				continue
			v,t = check_var_name(i)
			if t is None:
				raise ValueError(f"{i!r} is not a valid variable name")
			if not(v):
				warnings.warn(f"{i!r} is longer than the recommended five characters")
			try:
				self.arg_types.append(TypeReference(context.types[t]))
				arg_names.append(i)
			except KeyError:
				raise ValueError(f"Type {t!r} could not be found.")

		v,t = check_var_name(wrapped.__name__)
		if t and not(v):
			warnings.warn(
				f"{wrapped.__name__!r} is longer than the recommended five characters"
			)
		elif not(v) or t is None or t != self.type_n:
			raise ValueError(f"{wrapped.__name__!r} is not a valid function name")

		self.wrapped = wrapped

		self.__name__ = wrapped.__name__
		self.__qualname__ = wrapped.__qualname__
		self.__doc__ = wrapped.__doc__

	def __init_subclass__(cls,type_n: str) -> None:
		cls.type_n = type_n

	def __get__(self,obj,cls) ->\
			"BoundMethodOrFunction | BuiltinMethodOrFunction":
		if obj is None:
			return self

		return BoundMethodOrFunction(obj,self)

	@abstractmethod
	def __call__(self,*args: "TypeLike") -> "TypeLike | None":
		...

	def __repr__(self) -> str:
		return f"<{self.__class__.__name__} {self.__qualname__}>"


class BuiltinFunction(BuiltinMethodOrFunction,type_n="f"):
	def __init__(self,wrapped: Callable) -> None:
		super().__init__(wrapped)

		context = NamespaceContext.get_current_context()
		if context is None:
			raise ValueError("No context found")

		v,t = check_var_name(wrapped.__name__)
		if t is None:
			raise ValueError(f"{wrapped.__name__!r} is not a valid function name")
		try:
			t = context.types[t]
			self.return_type = TypeReference(t)
		except KeyError:
			raise ValueError(f"Type {t!r} could not be found.")

	def __call__(self,*args) -> "TypeLike":
		if len(args) > len(self.arg_types):
			raise ValueError(
				f"Incorrect number of arguments, expected {len(self.arg_types)}, "
				f"got {len(args)}"
			)
		nargs = list(args)
		for i,(a,r) in enumerate(zip(args,self.arg_types)):
			t = r.ref if isinstance(r,TypeReference) else r
			if t == "self":
				continue
			if not(isinstance(a,t)):
				nargs[i] = t(a)

		ret = self.wrapped(*nargs)

		if not(isinstance(ret,self.return_type.ref)):
			al_type = self.return_type.ref.alias_type
			if al_type is None:
				return self.return_type(ret)
			if isinstance(ret,al_type):
				return ret
			return self.return_type.ref(ret)

		return ret


class BuiltinMethod(BuiltinMethodOrFunction,type_n="m"):
	def __init__(self,wrapped: Callable) -> None:
		super().__init__(wrapped)
		self.return_type = None

		v,t = check_var_name(wrapped.__name__)
		if t and not(v):
			warnings.warn(
				f"{wrapped.__name__!r} is longer than the recommended five characters"
			)
		elif not(v) or t is None or t != "m":
			raise ValueError(f"{wrapped.__name__!r} is not a valid method name")

		self.wrapped = wrapped

	def __call__(self,*args) -> None:
		if len(args) > len(self.arg_types):
			raise ValueError("Incorrect number of arguments")
		nargs = list(args)
		for i,(a,r) in enumerate(zip(args,self.arg_types)):
			t = r.ref if isinstance(r,TypeReference) else r
			if t == "self":
				continue
			if not(isinstance(a,t)):
				nargs[i] = t(a)

		ret = self.wrapped(*nargs)

		if ret is not None:
			raise TypeError("Method must return None")


def builtin_function(wrapped: Callable[...,'TypeLike']) -> BuiltinFunction:
	return BuiltinFunction(wrapped)


def builtin_method(wrapped: Callable[...,None]) -> BuiltinMethod:
	return BuiltinMethod(wrapped)


class Type(ABC):
	alias_type: Optional[LType['TypeLike']] = None

	def __init_subclass__(cls) -> None:
		NamespaceContext.get_current_context().types[cls.__name__[0]] = cls

	@staticmethod
	def convert(v:'TypeLike | ConvType',t: 'LType[T]') -> 'T':
		if isinstance(v,Type):
			if not(hasattr(t,"alias_type")):
				t.alias_type = None
			if isinstance(v,t):
				return v
			if t.alias_type is not None and isinstance(v,t.alias_type):
				return v  # type:ignore
			try:
				return v.cast(t)
			except TypeError as ex:
				if hasattr(t,'cast_to'):
					return getattr(t,'cast_to')(v)
				raise ex
		else:
			match v:
				case int(v):
					r = i()
					r.value = v
				case float(v):
					r = n()
					r.value = v
				case str(v):
					r = s()
					r.value = v
				case bool(v):
					r = b()
					r.value = v
				case list(v):
					if all(isinstance(i,int) for i in v):
						r = q()
						r.value = v
					else:
						raise TypeError(f"Cannot convert {v!r}")
				case _:
					raise TypeError(f"Cannot convert {v!r} to {t!r}")
			return Type.convert(r,t)

	def __init__(self,*args) -> None:
		args = [i for i in args if i is not None]
		if not args:
			self.gmeof("__me")()
		elif len(args) == 1:
			r = self.gmeof("__ms").arg_types[1]
			t = r.ref if isinstance(r,TypeReference) else r
			if isinstance(t,_FutureType):
				raise ValueError(f"type {t.__name__} is not yet defined")
			if t == "self":
				raise RuntimeError
			arg = self.convert(args[0],t)
			self.gmeof("__ms")(arg)
		elif len(args) == 2:
			r1 = self.gmeof("__mm").arg_types[1]
			r2 = self.gmeof("__mm").arg_types[2]
			t1 = r1.ref if isinstance(r1,TypeReference) else r1
			t2 = r2.ref if isinstance(r2,TypeReference) else r2

			if isinstance(t1,_FutureType):
				raise ValueError(f"type {t1.__name__} is not yet defined")
			if isinstance(t2,_FutureType):
				raise ValueError(f"type {t2.__name__} is not yet defined")

			if t1 == "self" or t2 == "self":
				raise RuntimeError
			arg1 = self.convert(args[0],t1)
			arg2 = self.convert(args[1],t2)
			self.gmeof("__mm")(arg1,arg2)
		else:
			raise TypeError("Cannot construct a type with more than two arguments.")

	@builtin_method
	def __me(self) -> None:
		pass

	@builtin_method
	def __ms(self,s__a) -> None:
		pass

	@builtin_method
	def __mm(self,s__a,s__b) -> None:
		pass

	def cast(self,t:LType[T]) -> T:
		# sourcery skip: assign-if-exp, remove-redundant-if
		if hasattr(self,'_f_{t.__name__}'):
			r: T
			if TYPE_CHECKING:
				if issubclass(t,Type):
					r = t()
				else:
					r = t(lambda: None)
					# the line above would cause an error, if it was actually ran
					# but it's not a problem, because it's only to tell the type checker
					# what happened
			else:
				if TYPE_CHECKING:
					m__c = None
					# why is this here?
					# good question

				r = None  # tell python the scope of the variable
				exec(
					"@builtin_method\n"
					f"def m__c({t}__v):\n"
					"	nonlocal r\n"
					f"	r = {t}__v\n"
				)
				getattr(self,'_f_{t.__name__}')(m__c)

			return r
		raise TypeError(f"Cannot cast {self!r} to {t!r}")

	def gmeof(self, __name: str) -> Any:
		if __name.startswith("__"):
			name = f"_{self.__class__.__name__}{__name}"
			if hasattr(self,name):
				return getattr(self,name)
			for pt in self.__class__.__mro__[1:]:
				name = f"_{pt.__name__}{__name}"
				if hasattr(self,name):
					return getattr(self,name)
			raise AttributeError(f"{self!r} has no attribute {__name!r}")

		return getattr(self,__name)


class s(Type):
	alias_type = None

	value: str = ""

	@builtin_method
	def __ms(self,s__v: 's') -> None:
		self.value = s__v.value

	@builtin_method
	def __mm(self,s__l: 's',s__r: 's') -> None:
		self.value = s__l.value + s__r.value

	@builtin_function
	def f__i(self,i__i: 'i') -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(self.value[i__i.value])
			return f()

		return f__f

	@builtin_function
	def f__m(self,i__s: 'i',i__e: 'i') -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(self.value[i__s.value:i__e.value])
			return f()

		return f__f

	# type casting

	@builtin_function
	def _f_i(self) -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(int(self.value))
			return f()

		return f__f

	@builtin_function
	def _f_n(self) -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(float(self.value))
			return f()

		return f__f


class i(Type):
	value: int = 0

	@builtin_method
	def __ms(self,i__v: 'i') -> None:
		self.value = i__v.value

	@builtin_method
	def __mm(self,i__l: 'i',i__r: 'i') -> None:
		self.value = i__l.value + i__r.value

	@builtin_function
	def f__i(self) -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(-self.value)
			return f()

		return f__f


class n(Type):
	value: float = 0.0

	@builtin_method
	def __ms(self,i__v: 'i') -> None:
		self.value = i__v.value

	@builtin_method
	def __mm(self,i__l: 'i',i__r: 'i') -> None:
		self.value = i__l.value + i__r.value

	@builtin_function
	def f__i(self) -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(-self.value)
			return f()

		return f__f


class b(Type):
	value: bool = False

	@builtin_method
	def __ms(self,b__v: 'b') -> None:
		self.value = b__v.value

	@builtin_method
	def __mm(self,b__l: 'b',b__r: 'b') -> None:
		self.value = b__l.value ^ b__r.value

	@builtin_function
	def f__i(self) -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(not(self.value))
			return f()

		return f__f

	@classmethod
	def cast_to(cls,value: "TypeLike | ConvType") -> 'b':
		r = b()
		if isinstance(value,TypeLike)\
				and (val:=getattr(value,'value',None)) is not None:
			r.value = bool(val)
			return r
		r.value = bool(value)
		return r


class S(Type):
	out: IO[str]
	in_: IO[str]

	@builtin_method
	def __me(self) -> None:
		self.out = sys.stdout
		self.in_ = sys.stdin

	@builtin_method
	def __ms(self,s__v: 's') -> None:
		f = open(s__v.value,"r+")
		self.out = f
		self.in_ = f

	@builtin_method
	def __mm(self,s__l: 's',s__r: 's') -> None:
		raise TypeError("Cannot construct a S with more than two arguments.")

	@builtin_function
	def f__r(self) -> 'any_f':
		v = self.in_.readline()

		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(v)
			return f()

		return f__f

	@builtin_method
	def m__w(self,s__v: 's') -> None:
		self.out.write(s__v.value)


class q(Type):
	value: list[int]

	@builtin_method
	def __me(self) -> None:
		self.value = []

	@builtin_method
	def __ms(self,q__v: 'q') -> None:
		self.value = q__v.value.copy()

	@builtin_method
	def __mm(self,q__l: 'q',q__r: 'q') -> None:
		self.value = q__l.value.copy()
		self.value.extend(q__r.value)

	@builtin_function
	def f__p(self) -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(self.value.pop())
			return f()

		return f__f

	@builtin_method
	def m__a(self,i__v: 'i') -> None:
		self.value.append(i__v.value)


class t(Type):
	s__v: 's' = s()
	_child_l: Optional['t'] = None
	_child_r: Optional['t'] = None

	@builtin_method
	def __ms(self,s__v: 's') -> None:
		self.s__v = s__v

	@builtin_method
	def __mm(self,t__l: 't',t__r: 't') -> None:
		self._child_l = t__l
		self._child_r = t__r

	@property
	def t__l(self) -> 't':
		if self._child_l is None:
			return t()
		return self._child_l

	@property
	def t__r(self) -> 't':
		if self._child_r is None:
			return t()
		return self._child_r

	@builtin_method
	def m__c(self,t__v: 't') -> None:
		if self._child_l is None:
			self._child_l = t__v
			return
		if self._child_r is None:
			self._child_r = t__v
			return

	@builtin_function
	def f__f(self) -> 'any_f':
		@builtin_function
		def f__f(f__f: 'any_f') -> 'any_f':
			f__f(self._child_l is not None and self._child_r is not None)
			return f()

		return f__f


class RuntimeMethodOrFunction(MethodOrFunction):
	namespace_hook: Optional[Callable[[NamespaceContext],None]] = None

	@overload
	def __init__(self) -> None:
		...

	@overload
	def __init__(self,inner, args: list[str]) -> None:
		...

	def __init__(self, inner=None, args:list[str] = None) -> None:
		self.inner = inner
		if inner is not None and args is None:
			raise ValueError("args must be provided if inner is not None.")
		if args:
			context = NamespaceContext.get_current_context()
			self.arg_types = []
			self.args:list[str] = []
			for i in args:
				v,t = check_var_name(i)
				if t is None:
					raise ValueError(f"Invalid argument name: {i=}")
				self.arg_types.append(TypeReference(context.types[t]))
				self.args.append(i)

	def __call__(
			self, *args, namespace_hook: Callable[[NamespaceContext],None] = None
		) -> None:
		with NamespaceContext() as context:
			for r,n,v in zip(self.arg_types,self.args,args):
				t = r.ref if isinstance(r,TypeReference) else r
				if t == "self":
					raise RuntimeError
				if isinstance(t,_FutureType):
					raise ValueError(f"type {t=} is not yet defined.")
				context.vars._vars[n] = t.convert(v,t)

			if namespace_hook is not None:
				namespace_hook(context)

			self.inner.run()


class f(RuntimeMethodOrFunction, Type):
	alias_type = BuiltinFunction
	return_type: 'LType[f]'

	def __init__(self, inner=None, args:list[str] = None) -> None:
		super().__init__(inner, args)  # type:ignore
		self.return_type = f

	def __call__(self, *args) -> 'f':
		if self.inner is None:
			if len(args) != 0:
				raise TypeError(f"Function takes no arguments, {len(args)+1} given.")
			return self

		r = None

		def namespace_hook(context: 'NamespaceContext') -> None:
			@builtin_method
			def __mr(self: f) -> None:
				nonlocal r
				r = self

			context.vars["__mr"] = __mr

		super().__call__(*args,namespace_hook=namespace_hook)

		if r is None:
			if self.return_type is None:
				raise TypeError("Function has no return type.")
			return self.return_type()
		return r

	@classmethod
	def cast_to(cls, value: Callable[...,Any]) -> 'any_f':
		try:
			return builtin_function(value)
		except ValueError:
			raise TypeError(f"Cannot cast {value!r} to {cls!r}")


class m(RuntimeMethodOrFunction, Type):
	alias_type = BuiltinMethod

	@overload
	def __init__(self) -> None:
		...

	@overload
	def __init__(self,inner, args: list[str]) -> None:
		...

	def __init__(self, inner=None, args:list[str] = None) -> None:
		super().__init__(inner, args)  # type:ignore
		self.return_type = None

	@classmethod
	def cast_to(cls, value: Callable[...,None]) -> 'any_m':
		try:
			return builtin_method(value)
		except ValueError:
			raise TypeError(f"Cannot cast {value!r} to {cls!r}")


any_f: TypeAlias = f | BuiltinFunction
any_m: TypeAlias = m | BuiltinMethod
TypeLike = Type | MethodOrFunction
ConvType = int | float | str | bool | IO[str] | list[int]\
	| tuple[tuple | str, tuple | str] | Callable
