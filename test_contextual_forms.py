import unittest
import unicodedata

from contextual_forms import contextualize, decontextualize, \
     end_letters, iso_d, beg_d, mid_d, end_d, tails_d

class TestContextualize(unittest.TestCase):
    def test_isolated_character(self):
        inp = "ب"
        res = "ﺏ" # ISOLATED
        self.assertEqual(contextualize(inp), res)

    def test_init_med_end(self):
        inp = "ببب"
        res = "ﺑ" + "ﺒ" + "ﺐ"
        self.assertEqual(contextualize(inp), res)

    def test_all_init_med_end(self):
        for c in iso_d:
            inp = c+c+c
            if c in end_letters:
                res = iso_d[c]+iso_d[c]+iso_d[c]
            else:
                res = beg_d[c] + mid_d[c] + end_d[c]
            self.assertEqual(contextualize(inp), res)

    def test_isolated_last(self):
        inp = "سأل"
        res = "ﺳ" + "ﺎ" + "ٔ" + "ﻝ"
        self.assertEqual(contextualize(inp), res)


class TestDecontextualize(unittest.TestCase):
    def test_isolated_character(self):
        inp = "ﺏ" # ISOLATED
        res = "ب"
        self.assertEqual(decontextualize(inp), res)

    def test_init_med_end(self):
        inp = "ﺑ" + "ﺒ" + "ﺐ"
        res = "ببب"
        self.assertEqual(decontextualize(inp), res)

    def test_all_init_med_end(self):
        for c in sorted(iso_d):
            if c in end_letters:
                inp = iso_d[c]+iso_d[c]+iso_d[c]
                if iso_d[c] in tails_d:
                    res = c+" "+c+" "+c
                else:
                    res = c+c+c
            else:
                inp = beg_d[c] + mid_d[c] + end_d[c]
                res = c+c+c
            #print("inp:", inp)
            #print("res:", res)
            self.assertEqual(decontextualize(inp), res)

class TestDouble(unittest.TestCase):
    def test_1(self):
        inp = "ولا تردد به"
        self.assertEqual(decontextualize(contextualize(inp)), inp)


    def test_2(self):
        inp = "ولا تردي به"
        self.assertEqual(decontextualize(contextualize(inp)), inp)
    

    def test_3(self):
        """no space between word ending on tail letter and next word"""
        inp = contextualize("ولا تردي") + contextualize("به")
        res = "ولا تردي به"
        self.assertEqual(decontextualize(inp), res)

    def test_4(self):
        inp = "ولا ترددبه"
        self.assertEqual(decontextualize(contextualize(inp)), inp)

    def test_tail_plus_hamza(self):
        inp = "شيء"
        self.assertEqual(decontextualize(contextualize(inp)), inp)

    def test_tail_plus_hamza2(self):
        inp = "المقرىء"
        self.assertEqual(decontextualize(contextualize(inp)), inp)

    def test_tail_plus_hamza3(self):
        inp = "كفء"
        self.assertEqual(decontextualize(contextualize(inp)), inp)

    def test_tatwil(self):
        inp = "ســـأل"
        self.assertEqual(decontextualize(contextualize(inp)), inp)

##    def test_lam(self):
##        inp = "ســـأل ســـأل"
##        print("context:", contextualize(inp))
##        for x in contextualize(inp):
##            print(unicodedata.name(x))
##        print("decontext:", decontextualize(contextualize(inp)))

def _form_ok(k, v, form, end_form=None):
    """Check whether the correct form of a letter is used in the \
    keys and values of a dictionary

    Args:
        k (str) : dictionary key, should be a general Arabic-script letter
        v (str) : dictionary value, should be a context form letter of the `form`/`end-form` type
        form (str): name of the contextual form (ISOLATED / FINAL / MEDIAL / INITIAL) of the values in the dictionary
        end_form (str): name of the contextual form (ISOLATED / FINAL) of the values in the dictionary if the key is a letter that ends a letter block (does not connect to the next letter). Default: None (same form as other letters)

    Returns:
        bool"""
    k_name = unicodedata.name(k)
    v_name = unicodedata.name(v)
    if k_name == "ARABIC LETTER HAMZA": # this letter only has an ISOLATED FORM!
        #r = (v_name == k_name + " " + "ISOLATED FORM")
        r = "ISOLATED FORM" in v_name
        if not r:
            print("FALSE!")
        return r
    elif k in end_letters:
        if not end_form:
            end_form = form
        r = "FORM" not in k_name and end_form in v_name
        #r = (v_name == k_name + " " + end_form)
        if not r:
            print("False!", k_name, v_name)
        return r
    else:
        r = "FORM" not in k_name and form in v_name
        #r = (v_name == k_name + " " + form)
        if not r:
            print("FALSE!")
        return r

class Test_dictionaries(unittest.TestCase):
    """Check whether the correct form of a letter is used in the \
    keys and values of the character dictionaries"""
    
    def test_iso_d(self) :
        print("iso_d")
        for k, v in iso_d.items():
             self.assertTrue(_form_ok(k, v, "ISOLATED FORM"))

    def test_end_d(self) :
        print("end_d")
        for k, v in end_d.items():
            self.assertTrue(_form_ok(k, v, "FINAL FORM"))

    def test_beg_d(self) :
        print("beg_d")
        for k, v in beg_d.items():
            self.assertTrue(_form_ok(k, v, "INITIAL FORM", "ISOLATED FORM"))

    def test_mid_d(self) :
        print("mid_d")
        for k, v in mid_d.items():
            self.assertTrue(_form_ok(k, v, "MEDIAL FORM", "FINAL FORM")) 

    def test_tails_d(self):
        print("tails_d")
        for k, v in tails_d.items():
            self.assertTrue(_form_ok(v, k, "FORM")) # context forms in keys!

##    def test_decontext_d(self):
##        print("decontext_d")
##        for k, v in decontext_d.items():
##            self.assertTrue(_form_ok(v, k, "FORM")) # context forms in keys!
        

    def test_file_change(self):
        """check if the number of times each character is in a text file
        changes after contextualizing and decontextualizing it."""
        infp = "test/0851IbnQadiShuhba.TabaqatShaficiyya.JK000195-ara1.inProgress"
        outfp = "test/contextualized.txt"
        contextualize(infp, outfp)
        outfp2 = "test/decontextualized.txt"
        decontextualize(outfp, outfp2)
        chars = dict()
        for i, fp in enumerate([infp, outfp2]):
            with open(fp, mode="r", encoding="utf-8") as file:
                text = file.read()
                for c in text:
                    if not c in chars:
                        chars[c] = [0, 0]
                    chars[c][i] += 1
        for c in sorted(chars.keys()):
            if chars[c][0] != chars[c][1]:
                try:
                    print("character count changed:", c, chars[c], unicodedata.name(c))
                except:
                    print("character count changed:", c, chars[c], "no name")
            self.assertEqual(chars[c][0], chars[c][1])

if __name__ == "__main__":
    unittest.main()
