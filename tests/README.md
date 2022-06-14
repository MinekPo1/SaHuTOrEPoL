# How these tests work

## *.test

There are two parts to a .test file, split by three dashes.

The first is the input, and the second is the expected output.
If a line starts with a `@` it can indicate a non io output.
A `$$` indicates a comment.

Due to popular editors striping leading whitespace, each line of the input or output can be placed inside of square brackets.
If a line is empty, it will be ignored, unless it is placed in square brackets.

Multiple tests can be placed in a single file by splitting the file with three equal signs.

### Non io output

- `@success`: the test is expected not to raise an exception.
- `@failure`: the test is expected to raise an exception.
