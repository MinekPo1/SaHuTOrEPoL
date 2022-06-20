# SaHuTOrEPoL

**S**t**a**tically **Hu**ngarian **T**yped **O**bject O**r**iented **E**soteric **P**r**o**gramming **L**anguage

## Basic Syntax

### Comments

Two dollar sings are used to start a line comment.

### Code structure

Instructions end with do and should be followed by a new line. Leaving out the new line will result in the parser being less happy.

A tabulator followed by a space is used to indent a block of code.

#### If statements

An if statement starts with the `if` keyword, followed by an expression in brackets. The expression is evaluated and then a boolean value is constructed from the result. If the boolean value is true, the code in the block is executed. The body of the if statement ends with a `do` keyword and is indented by one more level than the if keyword.

#### While loops

An while loop starts with the `while` keyword, followed by an expression in brackets. The expression is evaluated and then a boolean value is constructed from the result. While the boolean value is true, the code in the block is executed. The body of the while loop ends with a `do` keyword and is indented by one more level than the while keyword.

### Variables

Variables in SaHuTOrEPoL are defined with a dollar sign followed by a name. The name can contain between 3 and 8 characters, however is recommended that it is less than 6 characters. The name must have exactly two underscores in it and the frist non underscore character must be a letter, which declares the variable type.

Variables starting with a underscore are considered local.

Setting a variables value can be done by writing the variable name followed by an expression, separated by dolar sign.

#### Member access

Members can be accessed by writing the variable name followed by a hyphen and the member name. This can be repeated to access members of members.

### Expressions

Expressions can have multiple elements, separated by a dot. Each of the elements can be either a function call, a variable or a literal.

#### Multi expressions

If the expression has more then one expression, the type of the first element is used to determine the type of the expression. It is then constructed with the first element or the result of the previous pass if it has happened already and the last element, which was not yet used in previous passes. This is repeated until all elements are used.

#### Literals

- values of type `i` cannot have leading zeros, must fill the regex `^-?[1-9]\d*$`
- values of type `n` cannot have leading or leaning zeros, unless it is the only digit after the decimal point, must fill the regex `^-?([1-9]\d*|0),(\d*[1-9]|0)$`
- values of type `s` must be surrounded by single or double quotes, which must be matching
- values of type `b` must be either `yes` or `no`

Variables can be accessed in the same way as in set instructions.
Functions can be called in the same way as outside expressions.

### Functions and methods

Methods and functions can be called by following the function or method name by brackets, within which the arguments are specified, separated by pipe characters. If the argument if of a different type than it should be, it is converted. If an argument is missing, it is constructed with no arguments being passed to the constructor.

If a function or method is called outside of an expression it must be followed by do, as any other instruction.

Methods cannot be called in expressions.

A common practise it for a function to return a function which takes a method as an argument. This is called fishing.

### Defined Types

A type definition is started with the character, which the type is bound followed by the type body split by a dolar sign.
The type body is a list of variables.
A type definition cannot be inside a function, method or type definition.

Special functions and methods are:

- `__me`: Called when the type is constructed with no arguments.
- `__ms`: Called when the type is constructed with a single argument.
- `__mm`: Called when the type is constructed with two arguments.
- `_f_X`: Called to convert a value of the type to a value of the type X. Should take a single argument, being the value to convert and the returned function should take a single argument, a callback method which should be called with the converted value.

### taking from a library

To take a variable or defined type from a library, first the dollar sign is used followed by the taken variable or defined type name, followed by the library name speared by another dollar sign.
First the library is searched for in the library path(s), then in the current directory.
Library names may not contain whitespace or hyphens, which are used as separators.
The implementation may be specified in the library file name, by adding a dot and the implementation name after the library name.
Folders which are specified in the library paths may, but don't have to be, specified before the library name.
Library path may be stored in the `SaHPath` system variable separated by a colon.

See [std specification](STDSpec.md) for information on standard libraries.

## Bult-in types

### `s` - String

Behaviour with two arguments: Convert the two inputs to strings and concatenate the results

Members:
| Name | Description
|:----:|:-----------
|`f__i`|Takes one argument: The index. Fishes the character in that index.
|`f__s`|Takes two arguments: The first argument is the start index, the second is the end index. Fishes the index and the string in that index.

### `i` - Integer

Behaviour with two arguments: Convert the two inputs to integers and add the results

Members:
| Name | Description
|:----:|:-----------
|`f__i`|Takes no arguments. Fishes the integer inverted.

### `n` - Number

Behaviour with two arguments: Convert the two inputs to numbers and add the results

Members:
| Name | Description
|:----:|:-
|`f__i`|Takes no arguments. Fishes the number inverted.

### `b` - Boolean

Behaviour with two arguments: XOR the truthiness of the two inputs

Members:
| Name | Description
|:----:|:-
|`f__i`|Takes no arguments, fishes the boolean inverted.

### `S` - Stream

When no arguments are given, the standard input and output are used.

When one argument of type `s` a file is opened and the io operations are preformed on that file.

Cannot be constructed with more then one argument.

Members:
| Name | Description
|:----:|:-
|`m__w`|Takes one argument: The string to write.
|`f__r`|Takes no arguments, fishes the string read from the stream.

### `q` - Queue of integers

Behaviour with two arguments: Create a new queue with the second as the first element.

Members:
| Name | Description
|:----:|:-
|`f__p`|Takes no arguments. Fishes the front element of the queue. The element is removed from the queue.
|`m__a`|Takes one argument: the value to be added to the queue.

### `t` - Tree of strings

Behaviour with two arguments: Create a tree with the first argument as the root and the second as the left child, if it is of type `t`. If the first argument is a tree and has two children, it is swapped with the second argument.

Members:
| Name | Description
|:----:|:-
|`s__v`|Value of the tree.
|`t__l`|The left child of the tree, empty tree otherwise.
|`t__r`|The right child of the tree, empty tree otherwise.
|`m__c`|Takes one argument: the value to be added to the tree. If the tree has two children, nothing is done.
|`f__f`|Takes no arguments. Fishes a boolean indicating if the tree has two children.

### `f` - Function

Cannot be constructed. When attempted to construct a function with no parameters, return a function which takes no arguments, does nothing and returns itself. It should not to be relied on the empty function being or not being the exact same function every time.

While defining a variable of type `f` the function can be defined, by placing the arguments (if any) in brackets after the variable name followed by the body. The body may extend over multiple lines, but must be placed into a new layer of indentation. Inside the function body the `__mr` method can be used to return a value. The return type is stated by the first non underscore character of the variable name. If no value was returned, a new The `do` keyword is used to end the function definition.

Has no members.

### `m` - Method

Cannot be constructed. When attempted to construct a function with no parameters, return a method which takes no arguments and does nothing. It should not to be relied on the empty method being or not being the exact same method every time.

While defining a variable of type `m` the method can be defined, by placing the arguments (if any) in brackets after the variable name followed by the body. The body may extend over multiple lines, but must be placed into a new layer of indentation. The `do` keyword is used to end the function definition.

Has no members.

## Conversion

`s` -> `i`: Treat the string as an byte array and convert it to an integer.

`i` -> `s`: Convert the integer to a string.

`n` -> `i`: Round the number to an integer.

`n` -> `s`: Convert the number to a string.

`s` -> `q`: Treat each character of the string as an integer and place them in a queue, first the even indexes left to right, then the odd indexes right to left.

`i` -> `q`: Create a queue with the integer as the first and only element.

`q` -> `i`: Return the first element of the queue.
