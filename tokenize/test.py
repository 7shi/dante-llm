"""
Tests for Italian tokenizer.
Test cases are derived from analysis.md examples.
"""
import pytest
from tokenizer import tokenize

class TestSimpleCases:
    """Basic tokenization without apostrophes."""

    def test_line_1(self):
        text = "Nel mezzo del cammin di nostra vita"
        expected = ["Nel", " ", "mezzo", " ", "del", " ", "cammin", " ", "di", " ", "nostra", " ", "vita"]
        assert tokenize(text) == expected

    def test_line_2(self):
        text = "mi ritrovai per una selva oscura,"
        expected = ["mi", " ", "ritrovai", " ", "per", " ", "una", " ", "selva", " ", "oscura", ","]
        assert tokenize(text) == expected

class TestApostropheAtEnd:
    """Words ending with apostrophe (elision)."""

    def test_line_7(self):
        text = "Tant' è amara che poco è più morte;"
        expected = ["Tant'", " ", "è", " ", "amara", " ", "che", " ", "poco", " ", "è", " ", "più", " ", "morte", ";"]
        assert tokenize(text) == expected

class TestApostropheInMiddle:
    """Words with apostrophe in the middle."""

    def test_line_8(self):
        text = "ma per trattar del ben ch'i' vi trovai,"
        expected = ["ma", " ", "per", " ", "trattar", " ", "del", " ", "ben", " ", "ch'", "i'", " ", "vi", " ", "trovai", ","]
        assert tokenize(text) == expected

    def test_line_9(self):
        text = "dirò de l'altre cose ch'i' v'ho scorte."
        expected = ["dirò", " ", "de", " ", "l'", "altre", " ", "cose", " ", "ch'", "i'", " ", "v'", "ho", " ", "scorte", "."]
        assert tokenize(text) == expected

class TestMultipleApostrophes:
    """Lines with multiple apostrophes."""

    def test_line_10(self):
        text = "Io non so ben ridir com' i' v'intrai,"
        expected = ["Io", " ", "non", " ", "so", " ", "ben", " ", "ridir", " ", "com'", " ", "i'", " ", "v'", "intrai", ","]
        assert tokenize(text) == expected

class TestApostropheAtBeginning:
    """Words starting with apostrophe."""

    def test_line_13(self):
        text = "Ma poi ch'i' fui al piè d'un colle giunto,"
        expected = ["Ma", " ", "poi", " ", "ch'", "i'", " ", "fui", " ", "al", " ", "piè", " ", "d'", "un", " ", "colle", " ", "giunto", ","]
        assert tokenize(text) == expected

    def test_line_17(self):
        text = "vestite già de' raggi del pianeta"
        expected = ["vestite", " ", "già", " ", "de'", " ", "raggi", " ", "del", " ", "pianeta"]
        assert tokenize(text) == expected

    def test_line_24(self):
        text = "si volge a l'acqua perigliosa e guata,"
        expected = ["si", " ", "volge", " ", "a", " ", "l'", "acqua", " ", "perigliosa", " ", "e", " ", "guata", ","]
        assert tokenize(text) == expected

    def test_line_35(self):
        text = "anzi 'mpediva tanto il mio cammino,"
        expected = ["anzi", " ", "'mpediva", " ", "tanto", " ", "il", " ", "mio", " ", "cammino", ","]
        assert tokenize(text) == expected

    def test_line_38(self):
        text = "e 'l sol montava 'n sù con quelle stelle"
        expected = ["e", " ", "'l", " ", "sol", " ", "montava", " ", "'n", " ", "sù", " ", "con", " ", "quelle", " ", "stelle"]
        assert tokenize(text) == expected

    def test_line_45(self):
        text = "la vista che m'apparve d'un leone."
        expected = ["la", " ", "vista", " ", "che", " ", "m'", "apparve", " ", "d'", "un", " ", "leone", "."]
        assert tokenize(text) == expected

class TestQuotationMarks:
    """Lines with guillemets (« ») and single quotes."""

    def test_line_65(self):
        text = "«Miserere di me», gridai a lui,"
        expected = ["«", "Miserere", " ", "di", " ", "me", "»", ",", " ", "gridai", " ", "a", " ", "lui", ","]
        assert tokenize(text) == expected

class TestSpecialCharacters:
    """Lines with special characters like ï."""

    def test_line_75(self):
        text = "poi che 'l superbo Ilïón fu combusto."
        expected = ["poi", " ", "che", " ", "'l", " ", "superbo", " ", "Ilïón", " ", "fu", " ", "combusto", "."]
        assert tokenize(text) == expected

    def test_line_104(self):
        text = "ma sapïenza, amore e virtute,"
        expected = ["ma", " ", "sapïenza", ",", " ", "amore", " ", "e", " ", "virtute", ","]
        assert tokenize(text) == expected

    def test_line_110(self):
        text = "fin che l'avrà rimessa ne lo 'nferno,"
        expected = ["fin", " ", "che", " ", "l'", "avrà", " ", "rimessa", " ", "ne", " ", "lo", " ", "'nferno", ","]
        assert tokenize(text) == expected

class CombinedWithQuotationMarks:
    """Lines combining apostrophes and quotation marks."""

    def test_purgatorio_15_82(self):
        text = "Com' io voleva dicer \u2018Tu m'appaghe\u2019,"
        expected = ["Com'", " ", "io", " ", "voleva", " ", "dicer", " ", "\u2018", "Tu", " ", "m'", "appaghe", "\u2019", ","]
        assert tokenize(text) == expected

class TestReconstruction:
    """Verify that concatenating tokens reconstructs the original text."""

    @pytest.mark.parametrize("text", [
        "Nel mezzo del cammin di nostra vita",
        "mi ritrovai per una selva oscura,",
        "Tant' è amara che poco è più morte;",
        "ma per trattar del ben ch'i' vi trovai,",
        "e 'l sol montava 'n sù con quelle stelle",
        "«Miserere di me», gridai a lui,",
        "poi che 'l superbo Ilïón fu combusto.",
    ])
    def test_reconstruction(self, text):
        tokens = tokenize(text)
        assert "".join(tokens) == text
