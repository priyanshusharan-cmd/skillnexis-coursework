# PDF knowledge base: example answers

**Q: What does ParamSpec allow you to annotate?** (expected pep-0612.pdf, rank 2)

For aesthetic purposes we allow these to be omitted. [2] Without that, we unfortunately get into a situation where we have to use a Function-variable as an improvised ParamSpec, in that we never actually bind the return type. [3] Semantics The inference rules for the return type of a function invocation whose signature contains a ParamSpec variable are analogous to those around evaluating ones with TypeVar\ s. [2]

Sources: [2] pep-0612.pdf p.2; [3] pep-0612.pdf p.4

**Q: How can I write a union type using the | operator?** (expected pep-0604.pdf, rank 1)

With this new operator, it is possible to write int | str instead of Union[int, str]. [1] args: '[' paramslist ']' paramslist: annotation (',' annotation)* [','] - To describe a disjunction (union type), the user must use Union[X, Y]. [1] In addition to annotations, the result of this expression would then be valid in isinstance() and issubclass():: isinstance(5, int | str) issubclass(bool, int | float) We will also be able to write t | None or None | t instead of Optional[t]:: isinstance(None, int | None) isinstance(42, None | int) Specification The new union syntax should be accepted for function, variable and parameter annotations. [2]

Sources: [1] pep-0604.pdf p.1; [2] pep-0604.pdf p.1

**Q: How do I annotate a method that returns an instance of its own class?** (expected pep-0673.pdf, rank 3)

Motivation A common use case is to write a method that returns an instance of the same class, usually by returning self. [3] For example, in class A the first argument of an instance method has the implicit type A. [4] Class and instance variable annotations Type annotations can also be used to annotate class and instance variables in class bodies and methods. [2]

Sources: [2] pep-0526.pdf p.3; [3] pep-0673.pdf p.1; [4] pep-0484.pdf p.2

**Q: What is LiteralString used for?** (expected pep-0675.pdf, rank 1)

Valid Locations for LiteralString LiteralString can be used where any other type can be used: :: variable_annotation: LiteralString def my_function(literal_string: LiteralString) -> LiteralString: ... [1] class Foo: my_attribute: LiteralString type_argument: List[LiteralString] T = TypeVar("T", bound=LiteralString) It cannot be nested within unions of Literal types: :: bad_union: Literal["hello", LiteralString] # Not OK bad_nesting: Literal[LiteralString] # Not OK Type Inference Inferring LiteralString Any literal string type is compatible with LiteralString. [1] For example, x: LiteralString = "foo" is valid [1]

Sources: [1] pep-0675.pdf p.4

**Q: What does the dataclass_transform decorator do?** (expected pep-0681.pdf, rank 1)

If dataclass_transform is applied to a function, using the decorated function as a decorator is assumed to apply dataclass-like semantics. [1] When applied to an overload, the dataclass_transform decorator still impacts all usage of the function. [1] This example demonstrates the above: Runtime behavior At runtime, the dataclass_transform decorator's only effect is to set an attribute named __dataclass_transform__ on the decorated function or class to support introspection. [2]

Sources: [1] pep-0681.pdf p.2; [2] pep-0681.pdf p.4

**Q: What is the new syntax for declaring type parameters in a generic class?** (expected pep-0695.pdf, rank 1)

Type Parameter Declarations Here is a new syntax for declaring type parameters for generic classes, functions, and type aliases. [1] The syntax adds support for a comma-delimited list of type parameters in square brackets after the name of the class, function, or type alias. [1] While generic types and type parameters have grown in popularity, the syntax for specifying type parameters still feels "bolted on" to Python. [2]

Sources: [1] pep-0695.pdf p.3; [2] pep-0695.pdf p.1

**Q: How do I attach extra metadata to a type with Annotated?** (expected pep-0593.pdf, rank 1)

Specifically, a type T can be annotated with metadata x via the typehint Annotated[T, x]. [1] If a library (or tool) encounters a typehint Annotated[T, x] and has no special logic for metadata x, it should ignore it and simply treat the type as T. [1] Rationale This PEP adds an Annotated type to the typing module to decorate existing types with context-specific metadata. [1]

Sources: [1] pep-0593.pdf p.1

**Q: Can I use list[int] instead of typing.List[int]?** (expected pep-0585.pdf, rank 4)

Simplified Syntax :: # Instead of # def f(list: List[Union[int, str]], param: Optional[int]) -> Union[float, str] def f(list: List[int | str], param: int | None) -> float | str: pass f([1, "abc"], None) # Instead of typing.List[typing.Union[str, int]] typing.List[str | int] list[str | int] # Instead of typing.Dict[str, typing.Union[int, float]] typing.Dict[str, int | float] dict[str, int | float] The existing typing.Union and | syntax should be equivalent. [1] To help with type inference in complex cases, a comment of the following format may be used:: x = [] # type: List[Employee] x, y, z = [], [], [] # type: List[int], List[int], List[str] x, y, z = [], [], [] # type: (List[int], List[int], List[str]) a, b, *c = range(5) # type: float, float, List[float] x = [1, 2] # type: List[int] Type comments should be put on the last line of the statement that contains the variable definition. [3] :: # valid isinstance("", int | str) # invalid isinstance(2, list[int]) # TypeError: isinstance() argument 2 cannot be a parameterized generic isinstance(1, int | list[int]) # valid issubclass(bool, int | float) # invalid issubclass(bool, bool | list[int]) Incompatible changes In some situations, some exceptions will not be raised as expected. [2]

Sources: [1] pep-0604.pdf p.1; [2] pep-0604.pdf p.2; [3] pep-0484.pdf p.18

**Q: What is the syntax for annotating a variable with a type?** (expected pep-0526.pdf, rank 1)

# type: str class Starship: # 'stats' is a class variable stats = {} # type: Dict[str, int] This PEP aims at adding syntax to Python for annotating the types of variables (including class variables and instance variables), instead of expressing them through comments:: primes: List[int] = [] captain: str # Note: no initial value! [3] In this case the return type may use the same type variable, thus making that method a generic function. [2] In addition, the first argument in an instance method can be annotated with a type variable. [2]

Sources: [2] pep-0484.pdf p.15; [3] pep-0526.pdf p.1

**Q: What is a type hint stub file?** (expected pep-0484.pdf, rank 1)

If a stub file is found the type checker should not read the corresponding "real" module. [1] Storing and distributing stub files The easiest form of stub file storage and distribution is to put them alongside Python modules in the same directory. [2] The type checker should have a configurable search path for stub files. [1]

Sources: [1] pep-0484.pdf p.20; [2] pep-0484.pdf p.22

## Unanswerable

**Q: What is the capital of Australia?** → I don't know. The documents don't seem to cover this.
**Q: How do I reset my router?** → I don't know. The documents don't seem to cover this.
