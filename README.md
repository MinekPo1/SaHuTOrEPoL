# SaHuTOrEPoL

**S**t**a**tically **Hu**ngarian **T**yped **O**bject O**r**iented **E**soteric **P**r**o**gramming **L**anguage

## Basic Syntax

### Comments

Two dollar sings are used to start a line comment.

### Code structure

Instructions end with do and should be followed by a new line. Leaving out the new line will result in the interpreter being less happy.

A tabulator followed by a space is used to indent a block of code.

### Variables

Variables in SaHuTOrEPoL are defined with a dollar sign followed by a name. The name can contain between 3 and 8 characters, however is recommended that it is less than 6 characters. The name must have exactly two underscores in it and the frist non underscore character must be a letter, which declares the variable type.

Variables starting with a underscore are considered local.

Setting a variables value can be done by writing the variable name followed by an expression, separated by dolar sign.

### Expressions

Expressions can have multiple elements, separated by a dot. Each of the elements can be either a function call, a variable or a literal.

If the expression has more then one expression, the type of the first element is used to determine the type of the expression. It is then constructed with the first element or the result of the previous pass if it has happened already and the last element, which was not yet used in previous passes. This is repeated until all elements are used.

### Defined Types

A type definition is started with the character, which the type is bound followed by the type body split by a dolar sign.
The type body is a list of variables.

Special functions and methods are:

- `__me`: Called when the type is constructed with no arguments.
- `__ms`: Called when the type is constructed with a single argument.
- `__mm`: Called when the type is constructed with two arguments.
- `_f_X`: Called to convert a value of the type to a value of the type X. Should take a single argument, being the value to convert and the returned function should take a single argument, a callback method which should be called with the converted value.

## Bult-in types

### `s` - String

Behaviour with two arguments: Convert the two inputs to strings and concatenate the results

Members:
| Name | Description
|:----:|:-----------
|`f__i`|Takes one argument: The index. Returns a function taking the in a callbacks method which is called with the character in that index as argument.
|`f__s`|Takes two arguments: The first argument is the start index, the second is the end index. Returns a function taking the in a callbacks method which is called with the index and the string  in that index as arguments.

### `i` - Integer

Behaviour with two arguments: Convert the two inputs to integers and add the results

Members:
| Name | Description
|:----:|:-----------
|`f__i`|Takes no arguments. Returns a function taking one argument of type `m` and calling it with the integer inverted as argument.

### `f` - Float

Behaviour with two arguments: Convert the two inputs to floats and add the results

Members:
| Name | Description
|:----:|:-
|`f__i`|Takes no arguments. Returns a function taking one argument: callbacks method. The callback method is called with the float inverted as argument.

### `b` - Boolean

Behaviour with two arguments: XOR the truthiness of the two inputs

Members:
| Name | Description
|:----:|:-
|`f__i`|Takes no arguments, returns a function taking in a callback method which is called with the boolean inverted as argument.

### `S` - Stream

When no arguments are given, the standard input and output are used.

When one argument of type `s` a file is opened and the io operations are preformed on that file.

Cannot be constructed with more then one argument.

Members:
| Name | Description
|:----:|:-
|`m__w`|Takes one argument: The string to write.
|`f__r`|Takes no arguments, returns a function taking in a callback method which is called with the string read from the stream as argument.

### `q` - Queue of integers

Behaviour with two arguments: If the first is a queue, create a new queue with the second as the first element, otherwise create a queue with the first as the first element and the second as the second element.

Members:
| Name | Description
|:----:|:-
|`f__p`|Takes no arguments. Returns a function taking one argument, which is a method which is called with the front element of the queue as argument. The element is removed from the queue.
|`m__a`|Takes one argument: The argument is the value to be added to the queue.

### `t` - Tree of strings

Behaviour with two arguments: Create a tree with the first argument as the root and the second as the left child, if it is of type `t`. If the first argument is a tree and has two children, it is swapped with the second argument.

Members:
| Name | Description
|:----:|:-
|`f__v`|Takes no arguments. Returns a function taking in a callback method which is called with the value of the tree as the only argument.
|`f__l`|Takes no arguments. Returns a function taking in a callback method which is called with the left child of the tree as the only argument.
|`f__r`|Takes no arguments. Returns a function taking a callback  as an argument method which is called with the right child of the tree as the only argument.
|`m__c`|Takes one argument: The argument is the value to be added to the tree. If the tree has two children, nothing is done.
|`f__f`|Takes no arguments. Returns a function taking one argument: callbacks method. The callback method is called with a boolean indicating if the tree has two children as the only argument.

### `f` - Function

Cannot be constructed. When attempted to construct a function with no parameters, return a function which takes no arguments, does nothing and returns itself. It should not to be relied on the empty function being or not being the exact same function every time.

While defining a variable of type `f` the function can be defined, by placing the arguments (if any) in brackets after the variable name followed by the body. The body may extend over multiple lines, but must be placed into a new layer of indentation. Inside the function body the `__mr` method can be used to return a value. The return type is stated by the first non underscore character of the variable name. If no value was returned, a new The `do` keyword is used to end the function definition.

Has no members.

### `m` - Method

Cannot be constructed. When attempted to construct a function with no parameters, return a method which takes no arguments and does nothing. It should not to be relied on the empty method being or not being the exact same method every time.

While defining a variable of type `m` the method can be defined, by placing the arguments (if any) in brackets after the variable name followed by the body. The body may extend over multiple lines, but must be placed into a new layer of indentation. The `do` keyword is used to end the function definition.

Has no members.
