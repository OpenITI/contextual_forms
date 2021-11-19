"""Convert all Arabic letters into their contextual glyph forms.

Arabic letters have four different shapes, depending on their position
in the letter block: initial, medial, final, isolated.

(Letter blocks are groups of one or more connected letters in Arabic.
Some words consist of one letter block (e.g., على), others of more
than one (e.g., the word اقامة consists of three).)

Unicode contains five different code points for each letter:
general, initial, medial, final, isolated.

For example: the letter ba':
general:	0628	ب
isolated:	FE8F	ﺏ
final:  	FE90	ﺐ
medial: 	FE92	ﺒ
initial: 	FE91	ﺑ

Normally, only the general form is used in a text,
and most programs will handle the shaping of the letter
automatically by its context.

This module contains 2 main functions:

* contextualize: turns general Arabic letters in a string or file
    into contextualized glyph forms
* decontextualize: turn contextualized Arabic letters in a string or file
    into their general forms.

"""

import json
import os
import re


import sys
import getopt

from openiti.helper.ara import normalize_composites

########################################################
#          CREATE CONTEXTUAL SHAPES DICTIONARIES       #
########################################################

# standard Arabic characters taken from wikipedia:
# https://en.wikipedia.org/wiki/Arabic_script_in_Unicode#Contextual_forms
# some characters added manually

iso_d = {
  "ء": "ﺀ",  # ARABIC LETTER HAMZA : ARABIC LETTER HAMZA ISOLATED FORM
#  "آ": "ﺁ",  # ARABIC LETTER ALEF WITH MADDA ABOVE : ARABIC LETTER ALEF WITH MADDA ABOVE ISOLATED FORM
  "ا": "ﺍ",  # ARABIC LETTER ALEF : ARABIC LETTER ALEF ISOLATED FORM
  "ب": "ﺏ",  # ARABIC LETTER BEH : ARABIC LETTER BEH ISOLATED FORM
  "ة": "ﺓ",  # ARABIC LETTER TEH MARBUTA : ARABIC LETTER TEH MARBUTA ISOLATED FORM
  "ت": "ﺕ",  # ARABIC LETTER TEH : ARABIC LETTER TEH ISOLATED FORM
  "ث": "ﺙ",  # ARABIC LETTER THEH : ARABIC LETTER THEH ISOLATED FORM
  "ج": "ﺝ",  # ARABIC LETTER JEEM : ARABIC LETTER JEEM ISOLATED FORM
  "ح": "ﺡ",  # ARABIC LETTER HAH : ARABIC LETTER HAH ISOLATED FORM
  "خ": "ﺥ",  # ARABIC LETTER KHAH : ARABIC LETTER KHAH ISOLATED FORM
  "د": "ﺩ",  # ARABIC LETTER DAL : ARABIC LETTER DAL ISOLATED FORM
  "ذ": "ﺫ",  # ARABIC LETTER THAL : ARABIC LETTER THAL ISOLATED FORM
  "ر": "ﺭ",  # ARABIC LETTER REH : ARABIC LETTER REH ISOLATED FORM
  "ز": "ﺯ",  # ARABIC LETTER ZAIN : ARABIC LETTER ZAIN ISOLATED FORM
  "س": "ﺱ",  # ARABIC LETTER SEEN : ARABIC LETTER SEEN ISOLATED FORM
  "ش": "ﺵ",  # ARABIC LETTER SHEEN : ARABIC LETTER SHEEN ISOLATED FORM
  "ص": "ﺹ",  # ARABIC LETTER SAD : ARABIC LETTER SAD ISOLATED FORM
  "ض": "ﺽ",  # ARABIC LETTER DAD : ARABIC LETTER DAD ISOLATED FORM
  "ط": "ﻁ",  # ARABIC LETTER TAH : ARABIC LETTER TAH ISOLATED FORM
  "ظ": "ﻅ",  # ARABIC LETTER ZAH : ARABIC LETTER ZAH ISOLATED FORM
  "ع": "ﻉ",  # ARABIC LETTER AIN : ARABIC LETTER AIN ISOLATED FORM
  "غ": "ﻍ",  # ARABIC LETTER GHAIN : ARABIC LETTER GHAIN ISOLATED FORM
  "ف": "ﻑ",  # ARABIC LETTER FEH : ARABIC LETTER FEH ISOLATED FORM
  "ق": "ﻕ",  # ARABIC LETTER QAF : ARABIC LETTER QAF ISOLATED FORM
  "ك": "ﻙ",  # ARABIC LETTER KAF : ARABIC LETTER KAF ISOLATED FORM
  "ل": "ﻝ",  # ARABIC LETTER LAM : ARABIC LETTER LAM ISOLATED FORM
  "م": "ﻡ",  # ARABIC LETTER MEEM : ARABIC LETTER MEEM ISOLATED FORM
  "ن": "ﻥ",  # ARABIC LETTER NOON : ARABIC LETTER NOON ISOLATED FORM
  "ه": "ﻩ",  # ARABIC LETTER HEH : ARABIC LETTER HEH ISOLATED FORM
  "و": "ﻭ",  # ARABIC LETTER WAW : ARABIC LETTER WAW ISOLATED FORM
  "ى": "ﻯ",  # ARABIC LETTER ALEF MAKSURA : ARABIC LETTER ALEF MAKSURA ISOLATED FORM
  "ي": "ﻱ",  # ARABIC LETTER YEH : ARABIC LETTER YEH ISOLATED FORM
  "ٱ": "ﭐ",  # ARABIC LETTER ALEF WASLA : ARABIC LETTER ALEF WASLA ISOLATED FORM
  "ٹ": "ﭦ",  # ARABIC LETTER TTEH : ARABIC LETTER TTEH ISOLATED FORM
  "پ": "ﭖ",  # ARABIC LETTER PEH : ARABIC LETTER PEH ISOLATED FORM
  "چ": "ﭺ",  # ARABIC LETTER TCHEH : ARABIC LETTER TCHEH ISOLATED FORM
  "ژ": "ﮊ",  # ARABIC LETTER JEH : ARABIC LETTER JEH ISOLATED FORM
  "گ": "ﮒ",  # ARABIC LETTER GAF : ARABIC LETTER GAF ISOLATED FORM
  "ی": "ﯼ",  # ARABIC LETTER FARSI YEH : ARABIC LETTER FARSI YEH ISOLATED FORM
  "ے": "ﮮ",  # ARABIC LETTER YEH BARREE : ARABIC LETTER YEH BARREE ISOLATED FORM
  "ں": "ﮞ",  # ARABIC LETTER NOON GHUNNA : ARABIC LETTER NOON GHUNNA ISOLATED FORM
  "ڈ": "ﮈ",  # ARABIC LETTER DDAL : ARABIC LETTER DDAL ISOLATED FORM
  "ڭ": "ﯓ",  # ARABIC LETTER NG : ARABIC LETTER NG ISOLATED FORM
  "ڑ": "ﮌ",  # ARABIC LETTER RREH : ARABIC LETTER RREH ISOLATED FORM
  "ک": "ﮎ",  # ARABIC LETTER KEHEH : ARABIC LETTER KEHEH ISOLATED FORM
}

end_d = {
  "ء": "ﺀ",  # ARABIC LETTER HAMZA : ARABIC LETTER HAMZA ISOLATED FORM
  #"آ": "ﺂ",  # ARABIC LETTER ALEF WITH MADDA ABOVE : ARABIC LETTER ALEF WITH MADDA ABOVE FINAL FORM
  "ا": "ﺎ",  # ARABIC LETTER ALEF : ARABIC LETTER ALEF FINAL FORM
  "ب": "ﺐ",  # ARABIC LETTER BEH : ARABIC LETTER BEH FINAL FORM
  "ة": "ﺔ",  # ARABIC LETTER TEH MARBUTA : ARABIC LETTER TEH MARBUTA FINAL FORM
  "ت": "ﺖ",  # ARABIC LETTER TEH : ARABIC LETTER TEH FINAL FORM
  "ث": "ﺚ",  # ARABIC LETTER THEH : ARABIC LETTER THEH FINAL FORM
  "ج": "ﺞ",  # ARABIC LETTER JEEM : ARABIC LETTER JEEM FINAL FORM
  "ح": "ﺢ",  # ARABIC LETTER HAH : ARABIC LETTER HAH FINAL FORM
  "خ": "ﺦ",  # ARABIC LETTER KHAH : ARABIC LETTER KHAH FINAL FORM
  "د": "ﺪ",  # ARABIC LETTER DAL : ARABIC LETTER DAL FINAL FORM
  "ذ": "ﺬ",  # ARABIC LETTER THAL : ARABIC LETTER THAL FINAL FORM
  "ر": "ﺮ",  # ARABIC LETTER REH : ARABIC LETTER REH FINAL FORM
  "ز": "ﺰ",  # ARABIC LETTER ZAIN : ARABIC LETTER ZAIN FINAL FORM
  "س": "ﺲ",  # ARABIC LETTER SEEN : ARABIC LETTER SEEN FINAL FORM
  "ش": "ﺶ",  # ARABIC LETTER SHEEN : ARABIC LETTER SHEEN FINAL FORM
  "ص": "ﺺ",  # ARABIC LETTER SAD : ARABIC LETTER SAD FINAL FORM
  "ض": "ﺾ",  # ARABIC LETTER DAD : ARABIC LETTER DAD FINAL FORM
  "ط": "ﻂ",  # ARABIC LETTER TAH : ARABIC LETTER TAH FINAL FORM
  "ظ": "ﻆ",  # ARABIC LETTER ZAH : ARABIC LETTER ZAH FINAL FORM
  "ع": "ﻊ",  # ARABIC LETTER AIN : ARABIC LETTER AIN FINAL FORM
  "غ": "ﻎ",  # ARABIC LETTER GHAIN : ARABIC LETTER GHAIN FINAL FORM
  "ف": "ﻒ",  # ARABIC LETTER FEH : ARABIC LETTER FEH FINAL FORM
  "ق": "ﻖ",  # ARABIC LETTER QAF : ARABIC LETTER QAF FINAL FORM
  "ك": "ﻚ",  # ARABIC LETTER KAF : ARABIC LETTER KAF FINAL FORM
  "ل": "ﻞ",  # ARABIC LETTER LAM : ARABIC LETTER LAM FINAL FORM
  "م": "ﻢ",  # ARABIC LETTER MEEM : ARABIC LETTER MEEM FINAL FORM
  "ن": "ﻦ",  # ARABIC LETTER NOON : ARABIC LETTER NOON FINAL FORM
  "ه": "ﻪ",  # ARABIC LETTER HEH : ARABIC LETTER HEH FINAL FORM
  "و": "ﻮ",  # ARABIC LETTER WAW : ARABIC LETTER WAW FINAL FORM
  "ى": "ﻰ",  # ARABIC LETTER ALEF MAKSURA : ARABIC LETTER ALEF MAKSURA FINAL FORM
  "ي": "ﻲ",  # ARABIC LETTER YEH : ARABIC LETTER YEH FINAL FORM
  "ٱ": "ﭑ",  # ARABIC LETTER ALEF WASLA : ARABIC LETTER ALEF WASLA FINAL FORM
  "ٹ": "ﭧ",  # ARABIC LETTER TTEH : ARABIC LETTER TTEH FINAL FORM
  "پ": "ﭗ",  # ARABIC LETTER PEH : ARABIC LETTER PEH FINAL FORM
  "چ": "ﭻ",  # ARABIC LETTER TCHEH : ARABIC LETTER TCHEH FINAL FORM
  "ژ": "ﮋ",  # ARABIC LETTER JEH : ARABIC LETTER JEH FINAL FORM
  "گ": "ﮓ",  # ARABIC LETTER GAF : ARABIC LETTER GAF FINAL FORM
  "ی": "ﯽ",  # ARABIC LETTER FARSI YEH : ARABIC LETTER FARSI YEH FINAL FORM
  "ے": "ﮯ",  # ARABIC LETTER YEH BARREE : ARABIC LETTER YEH BARREE FINAL FORM
  "ں": "ﮟ",  # ARABIC LETTER NOON GHUNNA : ARABIC LETTER NOON GHUNNA FINAL FORM
  "ڈ": "ﮉ",  # ARABIC LETTER DDAL : ARABIC LETTER DDAL FINAL FORM
  "ڭ": "ﯔ",  # ARABIC LETTER NG : ARABIC LETTER NG FINAL FORM
  "ڑ": "ﮍ",  # ARABIC LETTER RREH : ARABIC LETTER RREH FINAL FORM
  "ک": "ﮏ",  # ARABIC LETTER KEHEH : ARABIC LETTER KEHEH FINAL FORM
}

mid_d = {
  "ء": "ﺀ",  # ARABIC LETTER HAMZA : ARABIC LETTER HAMZA ISOLATED FORM
  #"آ": "ﺂ",  # ARABIC LETTER ALEF WITH MADDA ABOVE : ARABIC LETTER ALEF WITH MADDA ABOVE FINAL FORM
  "ا": "ﺎ",  # ARABIC LETTER ALEF : ARABIC LETTER ALEF FINAL FORM
  "ب": "ﺒ",  # ARABIC LETTER BEH : ARABIC LETTER BEH MEDIAL FORM
  "ة": "ﺔ",  # ARABIC LETTER TEH MARBUTA : ARABIC LETTER TEH MARBUTA FINAL FORM
  "ت": "ﺘ",  # ARABIC LETTER TEH : ARABIC LETTER TEH MEDIAL FORM
  "ث": "ﺜ",  # ARABIC LETTER THEH : ARABIC LETTER THEH MEDIAL FORM
  "ج": "ﺠ",  # ARABIC LETTER JEEM : ARABIC LETTER JEEM MEDIAL FORM
  "ح": "ﺤ",  # ARABIC LETTER HAH : ARABIC LETTER HAH MEDIAL FORM
  "خ": "ﺨ",  # ARABIC LETTER KHAH : ARABIC LETTER KHAH MEDIAL FORM
  "د": "ﺪ",  # ARABIC LETTER DAL : ARABIC LETTER DAL FINAL FORM
  "ذ": "ﺬ",  # ARABIC LETTER THAL : ARABIC LETTER THAL FINAL FORM
  "ر": "ﺮ",  # ARABIC LETTER REH : ARABIC LETTER REH FINAL FORM
  "ز": "ﺰ",  # ARABIC LETTER ZAIN : ARABIC LETTER ZAIN FINAL FORM
  "س": "ﺴ",  # ARABIC LETTER SEEN : ARABIC LETTER SEEN MEDIAL FORM
  "ش": "ﺸ",  # ARABIC LETTER SHEEN : ARABIC LETTER SHEEN MEDIAL FORM
  "ص": "ﺼ",  # ARABIC LETTER SAD : ARABIC LETTER SAD MEDIAL FORM
  "ض": "ﻀ",  # ARABIC LETTER DAD : ARABIC LETTER DAD MEDIAL FORM
  "ط": "ﻄ",  # ARABIC LETTER TAH : ARABIC LETTER TAH MEDIAL FORM
  "ظ": "ﻈ",  # ARABIC LETTER ZAH : ARABIC LETTER ZAH MEDIAL FORM
  "ع": "ﻌ",  # ARABIC LETTER AIN : ARABIC LETTER AIN MEDIAL FORM
  "غ": "ﻐ",  # ARABIC LETTER GHAIN : ARABIC LETTER GHAIN MEDIAL FORM
  "ف": "ﻔ",  # ARABIC LETTER FEH : ARABIC LETTER FEH MEDIAL FORM
  "ق": "ﻘ",  # ARABIC LETTER QAF : ARABIC LETTER QAF MEDIAL FORM
  "ك": "ﻜ",  # ARABIC LETTER KAF : ARABIC LETTER KAF MEDIAL FORM
  "ل": "ﻠ",  # ARABIC LETTER LAM : ARABIC LETTER LAM MEDIAL FORM
  "م": "ﻤ",  # ARABIC LETTER MEEM : ARABIC LETTER MEEM MEDIAL FORM
  "ن": "ﻨ",  # ARABIC LETTER NOON : ARABIC LETTER NOON MEDIAL FORM
  "ه": "ﻬ",  # ARABIC LETTER HEH : ARABIC LETTER HEH MEDIAL FORM
  "و": "ﻮ",  # ARABIC LETTER WAW : ARABIC LETTER WAW FINAL FORM
  "ى": "ﻰ",  # ARABIC LETTER ALEF MAKSURA : ARABIC LETTER ALEF MAKSURA FINAL FORM
  "ي": "ﻴ",  # ARABIC LETTER YEH : ARABIC LETTER YEH MEDIAL FORM
  "ٱ": "ﭑ",  # ARABIC LETTER ALEF WASLA : ARABIC LETTER ALEF WASLA FINAL FORM
  "ٹ": "ﭩ",  # ARABIC LETTER TTEH : ARABIC LETTER TTEH MEDIAL FORM
  "پ": "ﭙ",  # ARABIC LETTER PEH : ARABIC LETTER PEH MEDIAL FORM
  "چ": "ﭽ",  # ARABIC LETTER TCHEH : ARABIC LETTER TCHEH MEDIAL FORM
  "ژ": "ﮋ",  # ARABIC LETTER JEH : ARABIC LETTER JEH FINAL FORM
  "گ": "ﮕ",  # ARABIC LETTER GAF : ARABIC LETTER GAF MEDIAL FORM
  "ی": "ﯿ",  # ARABIC LETTER FARSI YEH : ARABIC LETTER FARSI YEH MEDIAL FORM
  "ے": "ﮯ",  # ARABIC LETTER YEH BARREE : ARABIC LETTER YEH BARREE FINAL FORM
  "ں": "ﮟ",  # ARABIC LETTER NOON GHUNNA : ARABIC LETTER NOON GHUNNA FINAL FORM
  "ڈ": "ﮉ",  # ARABIC LETTER DDAL : ARABIC LETTER DDAL FINAL FORM
  "ڭ": "ﯖ",  # ARABIC LETTER NG : ARABIC LETTER NG MEDIAL FORM
  "ڑ": "ﮍ",  # ARABIC LETTER RREH : ARABIC LETTER RREH FINAL FORM
  "ک": "ﮑ",  # ARABIC LETTER KEHEH : ARABIC LETTER KEHEH MEDIAL FORM
}

beg_d = {
  "ء": "ﺀ",  # ARABIC LETTER HAMZA : ARABIC LETTER HAMZA ISOLATED FORM
  #"آ": "ﺁ",  # ARABIC LETTER ALEF WITH MADDA ABOVE : ARABIC LETTER ALEF WITH MADDA ABOVE ISOLATED FORM
  "ا": "ﺍ",  # ARABIC LETTER ALEF : ARABIC LETTER ALEF ISOLATED FORM
  "ب": "ﺑ",  # ARABIC LETTER BEH : ARABIC LETTER BEH INITIAL FORM
  "ة": "ﺓ",  # ARABIC LETTER TEH MARBUTA : ARABIC LETTER TEH MARBUTA ISOLATED FORM
  "ت": "ﺗ",  # ARABIC LETTER TEH : ARABIC LETTER TEH INITIAL FORM
  "ث": "ﺛ",  # ARABIC LETTER THEH : ARABIC LETTER THEH INITIAL FORM
  "ج": "ﺟ",  # ARABIC LETTER JEEM : ARABIC LETTER JEEM INITIAL FORM
  "ح": "ﺣ",  # ARABIC LETTER HAH : ARABIC LETTER HAH INITIAL FORM
  "خ": "ﺧ",  # ARABIC LETTER KHAH : ARABIC LETTER KHAH INITIAL FORM
  "د": "ﺩ",  # ARABIC LETTER DAL : ARABIC LETTER DAL ISOLATED FORM
  "ذ": "ﺫ",  # ARABIC LETTER THAL : ARABIC LETTER THAL ISOLATED FORM
  "ر": "ﺭ",  # ARABIC LETTER REH : ARABIC LETTER REH ISOLATED FORM
  "ز": "ﺯ",  # ARABIC LETTER ZAIN : ARABIC LETTER ZAIN ISOLATED FORM
  "س": "ﺳ",  # ARABIC LETTER SEEN : ARABIC LETTER SEEN INITIAL FORM
  "ش": "ﺷ",  # ARABIC LETTER SHEEN : ARABIC LETTER SHEEN INITIAL FORM
  "ص": "ﺻ",  # ARABIC LETTER SAD : ARABIC LETTER SAD INITIAL FORM
  "ض": "ﺿ",  # ARABIC LETTER DAD : ARABIC LETTER DAD INITIAL FORM
  "ط": "ﻃ",  # ARABIC LETTER TAH : ARABIC LETTER TAH INITIAL FORM
  "ظ": "ﻇ",  # ARABIC LETTER ZAH : ARABIC LETTER ZAH INITIAL FORM
  "ع": "ﻋ",  # ARABIC LETTER AIN : ARABIC LETTER AIN INITIAL FORM
  "غ": "ﻏ",  # ARABIC LETTER GHAIN : ARABIC LETTER GHAIN INITIAL FORM
  "ف": "ﻓ",  # ARABIC LETTER FEH : ARABIC LETTER FEH INITIAL FORM
  "ق": "ﻗ",  # ARABIC LETTER QAF : ARABIC LETTER QAF INITIAL FORM
  "ك": "ﻛ",  # ARABIC LETTER KAF : ARABIC LETTER KAF INITIAL FORM
  "ل": "ﻟ",  # ARABIC LETTER LAM : ARABIC LETTER LAM INITIAL FORM
  "م": "ﻣ",  # ARABIC LETTER MEEM : ARABIC LETTER MEEM INITIAL FORM
  "ن": "ﻧ",  # ARABIC LETTER NOON : ARABIC LETTER NOON INITIAL FORM
  "ه": "ﻫ",  # ARABIC LETTER HEH : ARABIC LETTER HEH INITIAL FORM
  "و": "ﻭ",  # ARABIC LETTER WAW : ARABIC LETTER WAW ISOLATED FORM
  "ى": "ﻯ",  # ARABIC LETTER ALEF MAKSURA : ARABIC LETTER ALEF MAKSURA ISOLATED FORM
  "ي": "ﻳ",  # ARABIC LETTER YEH : ARABIC LETTER YEH INITIAL FORM
  "ٱ": "ﭐ",  # ARABIC LETTER ALEF WASLA : ARABIC LETTER ALEF WASLA ISOLATED FORM
  "ٹ": "ﭨ",  # ARABIC LETTER TTEH : ARABIC LETTER TTEH INITIAL FORM
  "پ": "ﭘ",  # ARABIC LETTER PEH : ARABIC LETTER PEH INITIAL FORM
  "چ": "ﭼ",  # ARABIC LETTER TCHEH : ARABIC LETTER TCHEH INITIAL FORM
  "ژ": "ﮊ",  # ARABIC LETTER JEH : ARABIC LETTER JEH ISOLATED FORM
  "گ": "ﮔ",  # ARABIC LETTER GAF : ARABIC LETTER GAF INITIAL FORM
  "ی": "ﯾ",  # ARABIC LETTER FARSI YEH : ARABIC LETTER FARSI YEH INITIAL FORM
  "ے": "ﮮ",  # ARABIC LETTER YEH BARREE : ARABIC LETTER YEH BARREE ISOLATED FORM
  "ں": "ﮞ",  # ARABIC LETTER NOON GHUNNA : ARABIC LETTER NOON GHUNNA ISOLATED FORM
  "ڈ": "ﮈ",  # ARABIC LETTER DDAL : ARABIC LETTER DDAL ISOLATED FORM
  "ڭ": "ﯕ",  # ARABIC LETTER NG : ARABIC LETTER NG INITIAL FORM
  "ڑ": "ﮌ",  # ARABIC LETTER RREH : ARABIC LETTER RREH ISOLATED FORM
  "ک": "ﮐ",  # ARABIC LETTER KEHEH : ARABIC LETTER KEHEH INITIAL FORM
}

tails_d = {
  "ﺐ" : "ب",  # ARABIC LETTER BEH FINAL FORM : ARABIC LETTER BEH
  "ﺔ" : "ة",  # ARABIC LETTER TEH MARBUTA FINAL FORM : ARABIC LETTER TEH MARBUTA
  "ﺖ" : "ت",  # ARABIC LETTER TEH FINAL FORM : ARABIC LETTER TEH
  "ﺚ" : "ث",  # ARABIC LETTER THEH FINAL FORM : ARABIC LETTER THEH
  "ﺞ" : "ج",  # ARABIC LETTER JEEM FINAL FORM : ARABIC LETTER JEEM
  "ﺢ" : "ح",  # ARABIC LETTER HAH FINAL FORM : ARABIC LETTER HAH
  "ﺦ" : "خ",  # ARABIC LETTER KHAH FINAL FORM : ARABIC LETTER KHAH
  "ﺲ" : "س",  # ARABIC LETTER SEEN FINAL FORM : ARABIC LETTER SEEN
  "ﺶ" : "ش",  # ARABIC LETTER SHEEN FINAL FORM : ARABIC LETTER SHEEN
  "ﺺ" : "ص",  # ARABIC LETTER SAD FINAL FORM : ARABIC LETTER SAD
  "ﺾ" : "ض",  # ARABIC LETTER DAD FINAL FORM : ARABIC LETTER DAD
  "ﻊ" : "ع",  # ARABIC LETTER AIN FINAL FORM : ARABIC LETTER AIN
  "ﻎ" : "غ",  # ARABIC LETTER GHAIN FINAL FORM : ARABIC LETTER GHAIN
  "ﻒ" : "ف",  # ARABIC LETTER FEH FINAL FORM : ARABIC LETTER FEH
  "ﻖ" : "ق",  # ARABIC LETTER QAF FINAL FORM : ARABIC LETTER QAF
  "ﻚ" : "ك",  # ARABIC LETTER KAF FINAL FORM : ARABIC LETTER KAF
  "ﻞ" : "ل",  # ARABIC LETTER LAM FINAL FORM : ARABIC LETTER LAM
  "ﻢ" : "م",  # ARABIC LETTER MEEM FINAL FORM : ARABIC LETTER MEEM
  "ﻦ" : "ن",  # ARABIC LETTER NOON FINAL FORM : ARABIC LETTER NOON
  "ﻪ" : "ه",  # ARABIC LETTER HEH FINAL FORM : ARABIC LETTER HEH
  "ﻰ" : "ى",  # ARABIC LETTER ALEF MAKSURA FINAL FORM : ARABIC LETTER ALEF MAKSURA
  "ﻲ" : "ي",  # ARABIC LETTER YEH FINAL FORM : ARABIC LETTER YEH
  "ﭧ" : "ٹ",  # ARABIC LETTER TTEH FINAL FORM : ARABIC LETTER TTEH
  "ﭗ" : "پ",  # ARABIC LETTER PEH FINAL FORM : ARABIC LETTER PEH
  "ﭻ" : "چ",  # ARABIC LETTER TCHEH FINAL FORM : ARABIC LETTER TCHEH
  "ﮓ" : "گ",  # ARABIC LETTER GAF FINAL FORM : ARABIC LETTER GAF
  "ﯽ" : "ی",  # ARABIC LETTER FARSI YEH FINAL FORM : ARABIC LETTER FARSI YEH
  "ﮯ" : "ے",  # ARABIC LETTER YEH BARREE FINAL FORM : ARABIC LETTER YEH BARREE
  "ﺏ" : "ب",  # ARABIC LETTER BEH ISOLATED FORM : ARABIC LETTER BEH
  "ﺓ" : "ة",  # ARABIC LETTER TEH MARBUTA ISOLATED FORM : ARABIC LETTER TEH MARBUTA
  "ﺕ" : "ت",  # ARABIC LETTER TEH ISOLATED FORM : ARABIC LETTER TEH
  "ﺙ" : "ث",  # ARABIC LETTER THEH ISOLATED FORM : ARABIC LETTER THEH
  "ﺝ" : "ج",  # ARABIC LETTER JEEM ISOLATED FORM : ARABIC LETTER JEEM
  "ﺡ" : "ح",  # ARABIC LETTER HAH ISOLATED FORM : ARABIC LETTER HAH
  "ﺥ" : "خ",  # ARABIC LETTER KHAH ISOLATED FORM : ARABIC LETTER KHAH
  "ﺱ" : "س",  # ARABIC LETTER SEEN ISOLATED FORM : ARABIC LETTER SEEN
  "ﺵ" : "ش",  # ARABIC LETTER SHEEN ISOLATED FORM : ARABIC LETTER SHEEN
  "ﺹ" : "ص",  # ARABIC LETTER SAD ISOLATED FORM : ARABIC LETTER SAD
  "ﺽ" : "ض",  # ARABIC LETTER DAD ISOLATED FORM : ARABIC LETTER DAD
  "ﻉ" : "ع",  # ARABIC LETTER AIN ISOLATED FORM : ARABIC LETTER AIN
  "ﻍ" : "غ",  # ARABIC LETTER GHAIN ISOLATED FORM : ARABIC LETTER GHAIN
  "ﻑ" : "ف",  # ARABIC LETTER FEH ISOLATED FORM : ARABIC LETTER FEH
  "ﻕ" : "ق",  # ARABIC LETTER QAF ISOLATED FORM : ARABIC LETTER QAF
  "ﻙ" : "ك",  # ARABIC LETTER KAF ISOLATED FORM : ARABIC LETTER KAF
  "ﻝ" : "ل",  # ARABIC LETTER LAM ISOLATED FORM : ARABIC LETTER LAM
  "ﻡ" : "م",  # ARABIC LETTER MEEM ISOLATED FORM : ARABIC LETTER MEEM
  "ﻥ" : "ن",  # ARABIC LETTER NOON ISOLATED FORM : ARABIC LETTER NOON
  "ﻩ" : "ه",  # ARABIC LETTER HEH ISOLATED FORM : ARABIC LETTER HEH
  "ﻯ" : "ى",  # ARABIC LETTER ALEF MAKSURA ISOLATED FORM : ARABIC LETTER ALEF MAKSURA
  "ﻱ" : "ي",  # ARABIC LETTER YEH ISOLATED FORM : ARABIC LETTER YEH
  "ﭦ" : "ٹ",  # ARABIC LETTER TTEH ISOLATED FORM : ARABIC LETTER TTEH
  "ﭖ" : "پ",  # ARABIC LETTER PEH ISOLATED FORM : ARABIC LETTER PEH
  "ﭺ" : "چ",  # ARABIC LETTER TCHEH ISOLATED FORM : ARABIC LETTER TCHEH
  "ﮒ" : "گ",  # ARABIC LETTER GAF ISOLATED FORM : ARABIC LETTER GAF
  "ﯼ" : "ی",  # ARABIC LETTER FARSI YEH ISOLATED FORM : ARABIC LETTER FARSI YEH
  "ﮮ" : "ے",  # ARABIC LETTER YEH BARREE ISOLATED FORM : ARABIC LETTER YEH BARREE
  "ﮞ" : "ں",  # ARABIC ARABIC LETTER NOON GHUNNA ISOLATED FORM : LETTER NOON GHUNNA
  "ﮟ" : "ں",  # ARABIC ARABIC LETTER NOON GHUNNA FINAL FORM : LETTER NOON GHUNNA
  "ﯓ" : "ڭ",  # ARABIC LETTER NG ISOLATED FORM : ARABIC LETTER NG
  "ﯔ" : "ڭ",  # ARABIC LETTER NG FINAL FORM : ARABIC LETTER NG
  "ﮏ" : "ک",  # ARABIC LETTER KEHEH FINAL FORM : ARABIC LETTER KEHEH
  "ﮎ" : "ک",  # ARABIC LETTER KEHEH ISOLATED FORM : ARABIC LETTER KEHEH
}


decontext_d = {
  "ﺀ": "ء",  # ARABIC LETTER ISOLATED FORM HAMZA : ARABIC LETTER HAMZA
  "ﭐ": "ٱ",  # ARABIC LETTER ALEF WASLA ISOLATED FORM : ARABIC LETTER ALEF WASLA
  "ﭑ": "ٱ",  # ARABIC LETTER ALEF WASLA FINAL FORM : ARABIC LETTER ALEF WASLA
  "ﭖ": "پ",  # ARABIC LETTER PEH ISOLATED FORM : ARABIC LETTER PEH
  "ﭗ": "پ",  # ARABIC LETTER PEH FINAL FORM : ARABIC LETTER PEH
  "ﭘ": "پ",  # ARABIC LETTER PEH INITIAL FORM : ARABIC LETTER PEH
  "ﭙ": "پ",  # ARABIC LETTER PEH MEDIAL FORM : ARABIC LETTER PEH
  "ﭦ": "ٹ",  # ARABIC LETTER TTEH ISOLATED FORM : ARABIC LETTER TTEH
  "ﭧ": "ٹ",  # ARABIC LETTER TTEH FINAL FORM : ARABIC LETTER TTEH
  "ﭨ": "ٹ",  # ARABIC LETTER TTEH INITIAL FORM : ARABIC LETTER TTEH
  "ﭩ": "ٹ",  # ARABIC LETTER TTEH MEDIAL FORM : ARABIC LETTER TTEH
  "ﭺ": "چ",  # ARABIC LETTER TCHEH ISOLATED FORM : ARABIC LETTER TCHEH
  "ﭻ": "چ",  # ARABIC LETTER TCHEH FINAL FORM : ARABIC LETTER TCHEH
  "ﭼ": "چ",  # ARABIC LETTER TCHEH INITIAL FORM : ARABIC LETTER TCHEH
  "ﭽ": "چ",  # ARABIC LETTER TCHEH MEDIAL FORM : ARABIC LETTER TCHEH
  "ﮊ": "ژ",  # ARABIC LETTER JEH ISOLATED FORM : ARABIC LETTER JEH
  "ﮋ": "ژ",  # ARABIC LETTER JEH FINAL FORM : ARABIC LETTER JEH
  "ﮒ": "گ",  # ARABIC LETTER GAF ISOLATED FORM : ARABIC LETTER GAF
  "ﮓ": "گ",  # ARABIC LETTER GAF FINAL FORM : ARABIC LETTER GAF
  "ﮔ": "گ",  # ARABIC LETTER GAF INITIAL FORM : ARABIC LETTER GAF
  "ﮕ": "گ",  # ARABIC LETTER GAF MEDIAL FORM : ARABIC LETTER GAF
  "ﮮ": "ے",  # ARABIC LETTER YEH BARREE ISOLATED FORM : ARABIC LETTER YEH BARREE
  "ﮯ": "ے",  # ARABIC LETTER YEH BARREE FINAL FORM : ARABIC LETTER YEH BARREE
  "ﯼ": "ی",  # ARABIC LETTER FARSI YEH ISOLATED FORM : ARABIC LETTER FARSI YEH
  "ﯽ": "ی",  # ARABIC LETTER FARSI YEH FINAL FORM : ARABIC LETTER FARSI YEH
  "ﯾ": "ی",  # ARABIC LETTER FARSI YEH INITIAL FORM : ARABIC LETTER FARSI YEH
  "ﯿ": "ی",  # ARABIC LETTER FARSI YEH MEDIAL FORM : ARABIC LETTER FARSI YEH
  "ﺁ": "آ",  # ARABIC LETTER ALEF WITH MADDA ABOVE ISOLATED FORM : ARABIC LETTER ALEF WITH MADDA ABOVE
  "ﺂ": "آ",  # ARABIC LETTER ALEF WITH MADDA ABOVE FINAL FORM : ARABIC LETTER ALEF WITH MADDA ABOVE
  "ﺍ": "ا",  # ARABIC LETTER ALEF ISOLATED FORM : ARABIC LETTER ALEF
  "ﺎ": "ا",  # ARABIC LETTER ALEF FINAL FORM : ARABIC LETTER ALEF
  "ﺏ": "ب",  # ARABIC LETTER BEH ISOLATED FORM : ARABIC LETTER BEH
  "ﺐ": "ب",  # ARABIC LETTER BEH FINAL FORM : ARABIC LETTER BEH
  "ﺑ": "ب",  # ARABIC LETTER BEH INITIAL FORM : ARABIC LETTER BEH
  "ﺒ": "ب",  # ARABIC LETTER BEH MEDIAL FORM : ARABIC LETTER BEH
  "ﺓ": "ة",  # ARABIC LETTER TEH MARBUTA ISOLATED FORM : ARABIC LETTER TEH MARBUTA
  "ﺔ": "ة",  # ARABIC LETTER TEH MARBUTA FINAL FORM : ARABIC LETTER TEH MARBUTA
  "ﺕ": "ت",  # ARABIC LETTER TEH ISOLATED FORM : ARABIC LETTER TEH
  "ﺖ": "ت",  # ARABIC LETTER TEH FINAL FORM : ARABIC LETTER TEH
  "ﺗ": "ت",  # ARABIC LETTER TEH INITIAL FORM : ARABIC LETTER TEH
  "ﺘ": "ت",  # ARABIC LETTER TEH MEDIAL FORM : ARABIC LETTER TEH
  "ﺙ": "ث",  # ARABIC LETTER THEH ISOLATED FORM : ARABIC LETTER THEH
  "ﺚ": "ث",  # ARABIC LETTER THEH FINAL FORM : ARABIC LETTER THEH
  "ﺛ": "ث",  # ARABIC LETTER THEH INITIAL FORM : ARABIC LETTER THEH
  "ﺜ": "ث",  # ARABIC LETTER THEH MEDIAL FORM : ARABIC LETTER THEH
  "ﺝ": "ج",  # ARABIC LETTER JEEM ISOLATED FORM : ARABIC LETTER JEEM
  "ﺞ": "ج",  # ARABIC LETTER JEEM FINAL FORM : ARABIC LETTER JEEM
  "ﺟ": "ج",  # ARABIC LETTER JEEM INITIAL FORM : ARABIC LETTER JEEM
  "ﺠ": "ج",  # ARABIC LETTER JEEM MEDIAL FORM : ARABIC LETTER JEEM
  "ﺡ": "ح",  # ARABIC LETTER HAH ISOLATED FORM : ARABIC LETTER HAH
  "ﺢ": "ح",  # ARABIC LETTER HAH FINAL FORM : ARABIC LETTER HAH
  "ﺣ": "ح",  # ARABIC LETTER HAH INITIAL FORM : ARABIC LETTER HAH
  "ﺤ": "ح",  # ARABIC LETTER HAH MEDIAL FORM : ARABIC LETTER HAH
  "ﺥ": "خ",  # ARABIC LETTER KHAH ISOLATED FORM : ARABIC LETTER KHAH
  "ﺦ": "خ",  # ARABIC LETTER KHAH FINAL FORM : ARABIC LETTER KHAH
  "ﺧ": "خ",  # ARABIC LETTER KHAH INITIAL FORM : ARABIC LETTER KHAH
  "ﺨ": "خ",  # ARABIC LETTER KHAH MEDIAL FORM : ARABIC LETTER KHAH
  "ﺩ": "د",  # ARABIC LETTER DAL ISOLATED FORM : ARABIC LETTER DAL
  "ﺪ": "د",  # ARABIC LETTER DAL FINAL FORM : ARABIC LETTER DAL
  "ﺫ": "ذ",  # ARABIC LETTER THAL ISOLATED FORM : ARABIC LETTER THAL
  "ﺬ": "ذ",  # ARABIC LETTER THAL FINAL FORM : ARABIC LETTER THAL
  "ﺭ": "ر",  # ARABIC LETTER REH ISOLATED FORM : ARABIC LETTER REH
  "ﺮ": "ر",  # ARABIC LETTER REH FINAL FORM : ARABIC LETTER REH
  "ﺯ": "ز",  # ARABIC LETTER ZAIN ISOLATED FORM : ARABIC LETTER ZAIN
  "ﺰ": "ز",  # ARABIC LETTER ZAIN FINAL FORM : ARABIC LETTER ZAIN
  "ﺱ": "س",  # ARABIC LETTER SEEN ISOLATED FORM : ARABIC LETTER SEEN
  "ﺲ": "س",  # ARABIC LETTER SEEN FINAL FORM : ARABIC LETTER SEEN
  "ﺳ": "س",  # ARABIC LETTER SEEN INITIAL FORM : ARABIC LETTER SEEN
  "ﺴ": "س",  # ARABIC LETTER SEEN MEDIAL FORM : ARABIC LETTER SEEN
  "ﺵ": "ش",  # ARABIC LETTER SHEEN ISOLATED FORM : ARABIC LETTER SHEEN
  "ﺶ": "ش",  # ARABIC LETTER SHEEN FINAL FORM : ARABIC LETTER SHEEN
  "ﺷ": "ش",  # ARABIC LETTER SHEEN INITIAL FORM : ARABIC LETTER SHEEN
  "ﺸ": "ش",  # ARABIC LETTER SHEEN MEDIAL FORM : ARABIC LETTER SHEEN
  "ﺹ": "ص",  # ARABIC LETTER SAD ISOLATED FORM : ARABIC LETTER SAD
  "ﺺ": "ص",  # ARABIC LETTER SAD FINAL FORM : ARABIC LETTER SAD
  "ﺻ": "ص",  # ARABIC LETTER SAD INITIAL FORM : ARABIC LETTER SAD
  "ﺼ": "ص",  # ARABIC LETTER SAD MEDIAL FORM : ARABIC LETTER SAD
  "ﺽ": "ض",  # ARABIC LETTER DAD ISOLATED FORM : ARABIC LETTER DAD
  "ﺾ": "ض",  # ARABIC LETTER DAD FINAL FORM : ARABIC LETTER DAD
  "ﺿ": "ض",  # ARABIC LETTER DAD INITIAL FORM : ARABIC LETTER DAD
  "ﻀ": "ض",  # ARABIC LETTER DAD MEDIAL FORM : ARABIC LETTER DAD
  "ﻁ": "ط",  # ARABIC LETTER TAH ISOLATED FORM : ARABIC LETTER TAH
  "ﻂ": "ط",  # ARABIC LETTER TAH FINAL FORM : ARABIC LETTER TAH
  "ﻃ": "ط",  # ARABIC LETTER TAH INITIAL FORM : ARABIC LETTER TAH
  "ﻄ": "ط",  # ARABIC LETTER TAH MEDIAL FORM : ARABIC LETTER TAH
  "ﻅ": "ظ",  # ARABIC LETTER ZAH ISOLATED FORM : ARABIC LETTER ZAH
  "ﻆ": "ظ",  # ARABIC LETTER ZAH FINAL FORM : ARABIC LETTER ZAH
  "ﻇ": "ظ",  # ARABIC LETTER ZAH INITIAL FORM : ARABIC LETTER ZAH
  "ﻈ": "ظ",  # ARABIC LETTER ZAH MEDIAL FORM : ARABIC LETTER ZAH
  "ﻉ": "ع",  # ARABIC LETTER AIN ISOLATED FORM : ARABIC LETTER AIN
  "ﻊ": "ع",  # ARABIC LETTER AIN FINAL FORM : ARABIC LETTER AIN
  "ﻋ": "ع",  # ARABIC LETTER AIN INITIAL FORM : ARABIC LETTER AIN
  "ﻌ": "ع",  # ARABIC LETTER AIN MEDIAL FORM : ARABIC LETTER AIN
  "ﻍ": "غ",  # ARABIC LETTER GHAIN ISOLATED FORM : ARABIC LETTER GHAIN
  "ﻎ": "غ",  # ARABIC LETTER GHAIN FINAL FORM : ARABIC LETTER GHAIN
  "ﻏ": "غ",  # ARABIC LETTER GHAIN INITIAL FORM : ARABIC LETTER GHAIN
  "ﻐ": "غ",  # ARABIC LETTER GHAIN MEDIAL FORM : ARABIC LETTER GHAIN
  "ﻑ": "ف",  # ARABIC LETTER FEH ISOLATED FORM : ARABIC LETTER FEH
  "ﻒ": "ف",  # ARABIC LETTER FEH FINAL FORM : ARABIC LETTER FEH
  "ﻓ": "ف",  # ARABIC LETTER FEH INITIAL FORM : ARABIC LETTER FEH
  "ﻔ": "ف",  # ARABIC LETTER FEH MEDIAL FORM : ARABIC LETTER FEH
  "ﻕ": "ق",  # ARABIC LETTER QAF ISOLATED FORM : ARABIC LETTER QAF
  "ﻖ": "ق",  # ARABIC LETTER QAF FINAL FORM : ARABIC LETTER QAF
  "ﻗ": "ق",  # ARABIC LETTER QAF INITIAL FORM : ARABIC LETTER QAF
  "ﻘ": "ق",  # ARABIC LETTER QAF MEDIAL FORM : ARABIC LETTER QAF
  "ﻙ": "ك",  # ARABIC LETTER KAF ISOLATED FORM : ARABIC LETTER KAF
  "ﻚ": "ك",  # ARABIC LETTER KAF FINAL FORM : ARABIC LETTER KAF
  "ﻛ": "ك",  # ARABIC LETTER KAF INITIAL FORM : ARABIC LETTER KAF
  "ﻜ": "ك",  # ARABIC LETTER KAF MEDIAL FORM : ARABIC LETTER KAF
  "ﻝ": "ل",  # ARABIC LETTER LAM ISOLATED FORM : ARABIC LETTER LAM
  "ﻞ": "ل",  # ARABIC LETTER LAM FINAL FORM : ARABIC LETTER LAM
  "ﻟ": "ل",  # ARABIC LETTER LAM INITIAL FORM : ARABIC LETTER LAM
  "ﻠ": "ل",  # ARABIC LETTER LAM MEDIAL FORM : ARABIC LETTER LAM
  "ﻡ": "م",  # ARABIC LETTER MEEM ISOLATED FORM : ARABIC LETTER MEEM
  "ﻢ": "م",  # ARABIC LETTER MEEM FINAL FORM : ARABIC LETTER MEEM
  "ﻣ": "م",  # ARABIC LETTER MEEM INITIAL FORM : ARABIC LETTER MEEM
  "ﻤ": "م",  # ARABIC LETTER MEEM MEDIAL FORM : ARABIC LETTER MEEM
  "ﻥ": "ن",  # ARABIC LETTER NOON ISOLATED FORM : ARABIC LETTER NOON
  "ﻦ": "ن",  # ARABIC LETTER NOON FINAL FORM : ARABIC LETTER NOON
  "ﻧ": "ن",  # ARABIC LETTER NOON INITIAL FORM : ARABIC LETTER NOON
  "ﻨ": "ن",  # ARABIC LETTER NOON MEDIAL FORM : ARABIC LETTER NOON
  "ﻩ": "ه",  # ARABIC LETTER HEH ISOLATED FORM : ARABIC LETTER HEH
  "ﻪ": "ه",  # ARABIC LETTER HEH FINAL FORM : ARABIC LETTER HEH
  "ﻫ": "ه",  # ARABIC LETTER HEH INITIAL FORM : ARABIC LETTER HEH
  "ﻬ": "ه",  # ARABIC LETTER HEH MEDIAL FORM : ARABIC LETTER HEH
  "ﻭ": "و",  # ARABIC LETTER WAW ISOLATED FORM : ARABIC LETTER WAW
  "ﻮ": "و",  # ARABIC LETTER WAW FINAL FORM : ARABIC LETTER WAW
  "ﻯ": "ى",  # ARABIC LETTER ALEF MAKSURA ISOLATED FORM : ARABIC LETTER ALEF MAKSURA
  "ﻰ": "ى",  # ARABIC LETTER ALEF MAKSURA FINAL FORM : ARABIC LETTER ALEF MAKSURA
  "ﻱ": "ي",  # ARABIC LETTER YEH ISOLATED FORM : ARABIC LETTER YEH
  "ﻲ": "ي",  # ARABIC LETTER YEH FINAL FORM : ARABIC LETTER YEH
  "ﻳ": "ي",  # ARABIC LETTER YEH INITIAL FORM : ARABIC LETTER YEH
  "ﻴ": "ي",  # ARABIC LETTER YEH MEDIAL FORM : ARABIC LETTER YEH
  "ﮞ": "ں",  # ARABIC ARABIC LETTER NOON GHUNNA ISOLATED FORM : LETTER NOON GHUNNA
  "ﮟ": "ں",  # ARABIC ARABIC LETTER NOON GHUNNA FINAL FORM : LETTER NOON GHUNNA
  "ﮉ": "ڈ",  # ARABIC LETTER DDAL FINAL FORM : ARABIC LETTER DDAL
  "ﮈ": "ڈ",  # ARABIC LETTER DDAL ISOLATED FORM : ARABIC LETTER DDAL
  "ﯓ": "ڭ",  # ARABIC LETTER NG ISOLATED FORM : ARABIC LETTER NG
  "ﯔ": "ڭ",  # ARABIC LETTER NG FINAL FORM : ARABIC LETTER NG
  "ﯕ": "ڭ",  # ARABIC LETTER NG INITIAL FORM : ARABIC LETTER NG
  "ﯖ": "ڭ",  # ARABIC LETTER NG MEDIAL FORM : ARABIC LETTER NG
  "ﮍ": "ڑ",  # ARABIC LETTER RREH FINAL FORM : ARABIC LETTER RREH
  "ﮌ": "ڑ",  # ARABIC LETTER RREH ISOLATED FORM : ARABIC LETTER RREH
  "ﮐ": "ک",  # ARABIC LETTER KEHEH INITIAL FORM : ARABIC LETTER KEHEH
  "ﮑ": "ک",  # ARABIC LETTER KEHEH MEDIAL FORM : ARABIC LETTER KEHEH
  "ﮏ": "ک",  # ARABIC LETTER KEHEH FINAL FORM : ARABIC LETTER KEHEH
  "ﮎ": "ک",  # ARABIC LETTER KEHEH ISOLATED FORM : ARABIC LETTER KEHEH
}

##for c in tails_d:
##    if not c in decontext_d:
##        print(c, "not in decontext_d")


############################################
#          DEFINE LETTER CATEGORIES        #
############################################

end_letters = """\
ء	ARABIC LETTER HAMZA
آ	ARABIC LETTER ALEF WITH MADDA ABOVE
أ	ARABIC LETTER ALEF WITH HAMZA ABOVE
ؤ	ARABIC LETTER WAW WITH HAMZA ABOVE
إ	ARABIC LETTER ALEF WITH HAMZA BELOW
ا	ARABIC LETTER ALEF
ٱ	ARABIC LETTER ALIF WASLA
ة	ARABIC LETTER TEH MARBUTA
د	ARABIC LETTER DAL
ذ	ARABIC LETTER THAL
ر	ARABIC LETTER REH
ز	ARABIC LETTER ZAIN
و	ARABIC LETTER WAW
ى	ARABIC LETTER ALEF MAKSURA
ژ	ARABIC LETTER JEH
ے	ARABIC LETTER YEH BARREE
ں	ARABIC LETTER NOON GHUNNA
ڈ	ARABIC LETTER DDAL
ڑ	ARABIC LETTER RREH"""
end_letters = [x.split("\t")[0] for x in end_letters.splitlines()]
end_letters = set(end_letters)

other_letters = """\
ئ	ARABIC LETTER YEH WITH HAMZA ABOVE
ب	ARABIC LETTER BEH
ت	ARABIC LETTER TEH
ث	ARABIC LETTER THEH
ج	ARABIC LETTER JEEM
ح	ARABIC LETTER HAH
خ	ARABIC LETTER KHAH
س	ARABIC LETTER SEEN
ش	ARABIC LETTER SHEEN
ص	ARABIC LETTER SAD
ض	ARABIC LETTER DAD
ط	ARABIC LETTER TAH
ظ	ARABIC LETTER ZAH
ع	ARABIC LETTER AIN
غ	ARABIC LETTER GHAIN
ـ	ARABIC TATWEEL
ف	ARABIC LETTER FEH
ق	ARABIC LETTER QAF
ك	ARABIC LETTER KAF
ل	ARABIC LETTER LAM
م	ARABIC LETTER MEEM
ن	ARABIC LETTER NOON
ه	ARABIC LETTER HEH
ي	ARABIC LETTER YEH
ً	ARABIC FATHATAN
ٌ	ARABIC DAMMATAN
ٍ	ARABIC KASRATAN
َ	ARABIC FATHA
ُ	ARABIC DAMMA
ِ	ARABIC KASRA
ّ	ARABIC SHADDA
ْ	ARABIC SUKUN
ٓ	ARABIC MADDAH ABOVE
ٔ	ARABIC HAMZA ABOVE
ٕ	ARABIC HAMZA BELOW
ٮ	ARABIC LETTER DOTLESS BEH
ٰ	ARABIC LETTER SUPERSCRIPT ALEF
ٹ	ARABIC LETTER TTEH
پ	ARABIC LETTER PEH
چ	ARABIC LETTER TCHEH
ک	ARABIC LETTER KEHEH
گ	ARABIC LETTER GAF
ی	ARABIC LETTER FARSI YEH
ڭ	ARABIC LETTER NG
ک	ARABIC LETTER KEHEH
"""
other_letters = [x.split("\t")[0] for x in other_letters.splitlines()]
other_letters = set(other_letters)

diacritics = """\
ً	064B ARABIC FATHATAN
ٌ	064C ARABIC DAMMATAN
ٍ	064D ARABIC KASRATAN
َ	064E ARABIC FATHA
ُ	064F ARABIC DAMMA
ِ	0650 ARABIC KASRA
ّ	0651 ARABIC SHADDA
ْ	0652 ARABIC SUKUN
ٓ	0653 ARABIC MADDAH ABOVE
ٔ	0654 ARABIC HAMZA ABOVE
ٕ	0655 ARABIC HAMZA BELOW
ٰ	0670 ARABIC SUPERSCRIPT ALEF
ـ	0640 ARABIC TATWEEL"""
diacritics = [x.split("\t")[0] for x in diacritics.splitlines()]
diacritics = set(diacritics)


# build a regex that will be used to add spaces after tails letters:
tails_s = "".join([x for x in tails_d])
diacritics_s = "".join([x for x in diacritics])
other_letters_s = "".join([x for x in decontext_d \
                           if (decontext_d[x] not in diacritics \
                               and decontext_d[x] != "ء")])
tails_regex = "([{}][{}]*)(?=[{}])".format(tails_s, diacritics_s, other_letters_s)


############################
#         FUNCTIONS        #
############################

def normalize(text, method="NFKD"):
    r = [("ہ", "ه"),  # \u06c1 ARABIC LETTER HEH GOAL > \u0647 ARABIC LETTER HEH
         ("ە", "ه"),  # \u06d5 ARABIC LETTER AE > \u0647 ARABIC LETTER HEH
         ("ھ", "ه"),  # \u06d5 \u06be ARABIC LETTER HEH DOACHASHMEE > \u0647 ARABIC LETTER HEH
#         ("ک", "ك"),  # \u06a9	ARABIC LETTER KEHEH > \u0643 ARABIC LETTER KAF
#         ("ی", "ي"),  # \u06cc ARABIC LETTER FARSI YEH > \u064a ARABIC LETTER YEH
         ("ٴ", "ٔ"),    # \u0674 ARABIC LETTER HIGH HAMZA > \u0654 ARABIC HAMZA ABOVE         
         ("۔", "."),  # \u06d4 ARABIC FULL STOP > . FULL STOP
         ("∗", "*"),  # \u2217 ASTERISK OPERATOR > ASTERISK
         ("ݣ", "ڭ"),  # \u0763 ARABIC LETTER KEHEH WITH THREE DOTS ABOVE > \u06AD ARABIC LETTER NG
         #("ـ", ""),  # \u0640 ARABIC TATWEEL > "" (remove)
         ]
    for c1, c2 in r:
        text = re.sub(c1, c2, text)
    return normalize_composites(text, method)


def _contextualize_block(block, iso_d=iso_d, end_d=end_d,
                         mid_d=mid_d, beg_d=beg_d,
                         end_letters=end_letters,
                         other_letters=other_letters,
                         diacritics=diacritics):
    """Turn Arabic letters in a letter block into contextualized glyph forms.

    Args:
        text (str): the string in which letters need to be contextualized.
        iso_d (dict): dictionary containing the isolated letter form
            (keys: general letter form, values: isolated letter form)
        end_d (dict): dictionary containing the final letter form
            (keys: general letter form, values: final letter form)
        mid_d (dict): dictionary containing the medial letter form
            (keys: general letter form, values: medial letter form)
        beg_d (dict): dictionary containing the initial letter form
            (keys: general letter form, values: initial letter form)
        end_letters (list): a list of Arabic letters that end a letter block
        other_letters (list): a list of Arabic letters that don't end
            a letter block
        diacritics (list): a list of Arabic diacritics

    Returns:
        str
    """
    #print(block, len([c for c in block if (c in end_letters or \
    #                                       (c in other_letters and c not in diacritics))]))
    # if the block contains only one letter (+ diacritics):
    if len([c for c in block if (c in end_letters or \
                                 (c in other_letters and c not in diacritics))]) == 1:
        t = ""
        for c in block:
            try:
                t += iso_d[c]
            except:
                t += c
        return t
    
    final_diacritics = ""
    #while block[-1] in diacritics:
    while len(block)>0 and block[-1] in diacritics:
        final_diacritics += block[-1]
        block = block[:-1]

    t = ""
    first = True
    for i, c in enumerate(block):
        if first:
            try:
                t += beg_d[c]
                first = False
            except:
                t += c
        elif i == len(block)-1:
            t += end_d[c]
        else:
            try:
                t += mid_d[c]
            except:
                t += c
    #print(t + final_diacritics)

    # deal with lam-alif ligature:
    t = re.sub("ﻠﺎ", "ﻼ", t)
    t = re.sub("ﻟﺎ", "ﻻ", t)
    
    return t + final_diacritics
            


def contextualize_text(text, iso_d=iso_d, end_d=end_d,
                       mid_d=mid_d, beg_d=beg_d,
                       end_letters=end_letters,
                       other_letters=other_letters,
                       diacritics=diacritics,
                       normalize_func=normalize,
                       normalize_method="NFKD"):
    """Turn Arabic letters in a string into contextualized glyph forms.

    Args:
        text (str): the string in which letters need to be contextualized.
        iso_d (dict): dictionary containing the isolated letter form
            (keys: general letter form, values: isolated letter form)
        end_d (dict): dictionary containing the final letter form
            (keys: general letter form, values: final letter form)
        mid_d (dict): dictionary containing the medial letter form
            (keys: general letter form, values: medial letter form)
        beg_d (dict): dictionary containing the initial letter form
            (keys: general letter form, values: initial letter form)
        end_letters (list): a list of Arabic letters that end a letter block
        other_letters (list): a list of Arabic letters that don't end
            a letter block
        diacritics (list): a list of Arabic diacritics
        normalize_func (funtion): a function to be used to normalize the text
            prior to the contextualization. Defaults to `normalize_composites`
        normalize_method (str): name of a normalization method that
            needs to be passed to `normalize_func`. Defaults to "NFKD", 
            which will split all combined letters and all ligatures.

    Returns:
        str
    """
    if normalize_func:
        try:
            text = normalize_func(text, method=normalize_method)
        except:
            text = normalize_func(text)
    # convert letters in Arabic letter blocks to their contextual form:
    new = ""
    block = ""
    for c in text:
        if c in end_letters: # end of letter block; add to block and convert
            #print(c, "is end letter")
            if block:
                new += _contextualize_block(block+c, iso_d, end_d, mid_d, beg_d)
                block = ""
            else:
                new += iso_d[c]
        elif c in other_letters: # add letter to current letter block
            #print(c, "is other letter")
            block += c
        else: # not an Arabic letter: convert current block and add c to new
            if block: 
                new += _contextualize_block(block, iso_d, end_d, mid_d, beg_d)
                block = ""
                new += c
            else:
                new += c
    # add the letters from the last block:
    if block:
        new += _contextualize_block(block, iso_d, end_d, mid_d, beg_d)
    return new
            


def contextualize(inp, outfp=None, iso_d=iso_d, end_d=end_d,
                  mid_d=mid_d, beg_d=beg_d,
                  end_letters=end_letters,
                  other_letters=other_letters,
                  diacritics=diacritics,
                  normalize_func=normalize,
                  normalize_method="NFKD"):
    """Turn Arabic letters in a string or text file into contextualized glyph forms.

    Args:
        inp (str): the string (or path to a text file)
            in which letters need to be contextualized.
        outfp (str): path to the file in which the converted text will be saved
        iso_d (dict): dictionary containing the isolated letter form
            (keys: general letter form, values: isolated letter form)
        end_d (dict): dictionary containing the final letter form
            (keys: general letter form, values: final letter form)
        mid_d (dict): dictionary containing the medial letter form
            (keys: general letter form, values: medial letter form)
        beg_d (dict): dictionary containing the initial letter form
            (keys: general letter form, values: initial letter form)
        end_letters (list): a list of Arabic letters that end a letter block
        other_letters (list): a list of Arabic letters that don't end
            a letter block
        diacritics (list): a list of Arabic diacritics
        normalize_func (funtion): a function to be used to normalize the text
            prior to the contextualization. Defaults to `normalize_composites`
        normalize_method (str): name of a normalization method that
            needs to be passed to `normalize_func`. Defaults to "NFKD", 
            which will split all combined letters and all ligatures.

    Returns:
        str
    """

    if os.path.isfile(inp):
        with open(inp, mode="r", encoding="utf-8") as file:
            text = file.read()
    else:
        text = inp
    new = contextualize_text(text, iso_d=iso_d, end_d=end_d,
                             mid_d=mid_d, beg_d=beg_d,
                             end_letters=end_letters,
                             other_letters=other_letters,
                             diacritics=diacritics,
                             normalize_func=normalize_func,
                             normalize_method=normalize_method)

    if outfp:
        with open(outfp, mode="w", encoding="utf-8") as file:
            file.write(new)
    else:
        print(new)
    return new

def decontextualize(inp, outfp=None, tails_regex=tails_regex):
    """Turn contextualized Arabic letter forms into general letter forms,\
    making sure that final letter shapes are not connected to the next word.

    Args:
        inp (str): the string (or path to a text file)
            in which letters need to be decontextualized.
        outfp (str): path to the output file in which letters will be decontextualized.
        tails_regex (str): regular expressions that describes the situation
             where a final form code point is followed by another letter.
    Returns:
        str
    """
    if os.path.isfile(inp):
        with open(inp, mode="r", encoding="utf-8") as file:
            text = file.read()
    else:
        text = inp
    new = re.sub(tails_regex, r"\1 ", text)
    new = normalize_composites(new, method="NFKC")
    if outfp:
        with open(outfp, mode="w", encoding="utf-8") as file:
            file.write(new)
    else:
        print(new)
    return new
    




info = """\
Turn Arabic letters into their contextual or general forms.

Arabic letters have four different shapes, depending on their position
in the letter block: initial, medial, final, isolated.

(Letter blocks are groups of one or more connected letters in Arabic.
Some words consist of one letter block (e.g., على), others of more
than one (e.g., the word اقامة consists of three).)

Unicode contains five different code points for each letter:
general, initial, medial, final, isolated.

Normally, only the general form is used in a text,
and most programs will handle the shaping of the letter
automatically by its context.

Command line arguments for ocr_pipeline.py:

-h, --help : print help info
-i, --input : string or path to a file in which characters need to be (de)contextualized
-o, --output_file : path to the output file
-d, --decontextualize : decontextualize letters

Usage:

Turn all general letter forms in a string or file into their contextual forms:

$ python contextual_forms.py -i "ألف باء"
$ python contextual_forms.py -i path/to/input/text.txt

Turn all contextual letter forms in a string or file into their general forms:

$ python contextual_forms.py -d -i "ألف باء"
$ python contextual_forms.py -d -i path/to/input/text.txt

Save the output to a file:

$ python contextual_forms.py -i "ألف باء" -o path/to/output/file.txt
$ python contextual_forms.py -i path/to/input/text.txt -o path/to/output/file.txt
$ python contextual_forms.py -d -i "ألف باء" -o path/to/output/file.txt
$ python contextual_forms.py -d -i path/to/input/text.txt -o path/to/output/file.txt

"""


if __name__ == "__main__":
    
    inp = ""
    outfp = None
    decontext = False
    argv = sys.argv[1:]
    opt_str = "hdi:o:"
    opt_list = ["help", "decontextualize", "input=", "output_file="]
    try:
        opts, args = getopt.getopt(argv, opt_str, opt_list)
    except Exception as e:
        print(e)
        print("Input incorrect: \n"+info)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            print(info)
            sys.exit(2)
            OUTPUT_EXT = "alto"
        elif opt in ["-d", "--decontextualize"]:
            decontext = True
        elif opt in ["-i", "--input"]:
            inp = arg
        elif opt in ["-o", "--output_file"]:
            outfp = arg

    if not inp:
        print("No input provided. Please use the -i parameter.")
        print(info)
        sys.exit(2)
    if decontext:
        decontextualize(inp, outfp=outfp)
    else:
        contextualize(inp, outfp=outfp)
