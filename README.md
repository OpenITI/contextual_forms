# Contextual Forms

Convert all Arabic letters into their contextual glyph forms, and vice versa.

Arabic letters have four different shapes, depending on their position
in the letter block: initial, medial, final, isolated.

(Letter blocks are groups of one or more connected letters in Arabic.
Some words consist of one letter block (e.g., على), others of more
than one (e.g., the word اقامة consists of three).)

Unicode contains five different code points for each letter:
general, initial, medial, final, isolated.

For example: the letter ba':

| general  | \u0628 | ب |
| isolated | \uFE8F | ﺏ |
| final    | \uFE90 | ﺐ |
| medial   | \uFE92 | ﺒ |
| initial  | \uFE91 | ﺑ |

Normally, only the general form is used in a text,
and most programs will handle the shaping of the letter
automatically by its context.

This module contains 2 main functions:

* contextualize: turns general Arabic letters in a string or file
    into contextualized glyph forms
* decontextualize: turn contextualized Arabic letters in a string or file
    into their general forms.

## Test run on the OCR training data:

`histo_Norm_typf.csv`: contains counts of every character 
in each typeface training data set
after contextualizing the Arabic-script characters.