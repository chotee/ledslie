from ledslie.config import Config
from ledslie.messages import FrameSequence, Frame
from ledslie.processors.catalog import Catalog
from ledslie.processors.intermezzos import IntermezzoWipe


class TestCatalog(object):
    def test_init(self, catalog=None):
        catalog = Catalog() if catalog is None else catalog
        assert catalog.is_empty()
        assert not catalog.has_content()

        self._create_and_add_sequence(catalog, "First", ["Foo"])

        assert not catalog.is_empty()
        assert catalog.has_content()

        self._create_and_add_sequence(catalog, "Second", ["Bar", "Quux"])

        return catalog

    def _create_and_add_sequence(self, catalog, program_name, sequence_content, valid_time=None):
        seq = FrameSequence()
        # Frame(bytearray(b'Bar') * int(3456/3)
        seq.program = program_name
        if isinstance(sequence_content[0], Frame):
            seq.frames = sequence_content
        else:
            seq.frames = [Frame(bytearray(f.encode() * int(3456 / len(f))), 10) for f in sequence_content]
        seq.valid_time = valid_time
        catalog.add_program(program_name, seq)
        return seq

    def test_get_frames(self):
        catalog = self.test_init()
        iter = catalog.frames_iter()
        assert bytearray(b"Bar")  == next(iter).raw()[0:3]
        assert bytearray(b"Quux") == next(iter).raw()[0:4]
        assert bytearray(b"Foo")  == next(iter).raw()[0:3]
        assert bytearray(b"Bar")  == next(iter).raw()[0:3]

    def test_empty_catalog(self):
        catalog = Catalog()
        try:
            next(catalog.frames_iter())
        except IndexError:
            pass
        else:
            assert "Should not get here!"
        assert [] == catalog.list_current_programs()

    def test_remove_program(self):
        catalog = self.test_init()
        assert catalog.has_content()
        catalog.remove_program("First")
        catalog.remove_program("Second")
        try: catalog.remove_program("Missing")
        except KeyError: pass
        else: assert False

    def test_program_retire(self):
        catalog = Catalog()
        catalog.now = lambda: 10
        self._create_and_add_sequence(catalog, "First", ["Foo"])
        f_iter = catalog.frames_iter()
        assert bytearray(b"Foo") == next(f_iter).raw()[0:3]  # Only foo is shown
        assert bytearray(b"Foo") == next(f_iter).raw()[0:3]
        catalog.now = lambda: 20  # Time passes
        self._create_and_add_sequence(catalog, "Second", ["Bar"])
        assert bytearray(b"Bar") == next(f_iter).raw()[0:3]
        assert bytearray(b"Foo") == next(f_iter).raw()[0:3]
        assert bytearray(b"Bar") == next(f_iter).raw()[0:3]
        catalog.now = lambda: 20+Config()["PROGRAM_RETIREMENT_AGE"]
        assert bytearray(b"Foo") == next(f_iter).raw()[0:3]  # Foo now gets retired.
        assert bytearray(b"Bar") == next(f_iter).raw()[0:3]
        assert bytearray(b"Bar") == next(f_iter).raw()[0:3]
        self._create_and_add_sequence(catalog, "Second", ["Bar2"])  # "Second" got updated
        assert bytearray(b"Bar2") == next(f_iter).raw()[0:4]
        catalog.now = lambda: 30+Config()["PROGRAM_RETIREMENT_AGE"]
        assert bytearray(b"Bar2") == next(f_iter).raw()[0:4]  # Still exists, because "Second" was updated.

    def test_valid_for(self):
        catalog = Catalog()
        f_iter = catalog.frames_iter()
        catalog.now = lambda: 10
        self._create_and_add_sequence(catalog, "long", ['Long'])
        catalog.now = lambda: 15
        self._create_and_add_sequence(catalog, "short", ['Short'], valid_time=30)
        assert bytearray(b"Short") == next(f_iter).raw()[0:5]
        assert bytearray(b"Long") == next(f_iter).raw()[0:4]
        catalog.now = lambda: 40
        assert bytearray(b"Short") == next(f_iter).raw()[0:5]
        assert bytearray(b"Long") == next(f_iter).raw()[0:4]
        catalog.now = lambda: 46  # Now the short program should be retired.
        assert bytearray(b"Short") == next(f_iter).raw()[0:5]
        assert bytearray(b"Long") == next(f_iter).raw()[0:4]
        assert bytearray(b"Long") == next(f_iter).raw()[0:4]
        assert bytearray(b"Long") == next(f_iter).raw()[0:4]

    def test_intermezzo_wipe(self):
        catalog = Catalog()
        catalog.add_intermezzo(IntermezzoWipe)
        self._create_and_add_sequence(catalog, 'second', [Frame(bytearray(b'\x00'*3456), 10)])
        self._create_and_add_sequence(catalog, 'first',  [Frame(bytearray(b'\xff'*3456), 10)])
        f_iter = catalog.frames_iter()
        res = next(f_iter)
        assert 0xff == res.raw()[0]
        res2 = next(f_iter)
        assert 0x0 == res2.raw()[0]

    def test_mark_program_progress(self):
        catalog = Catalog()
        seq = self._create_and_add_sequence(catalog, 'first',  [Frame(bytearray(b'\xff'*3456), 10)])
        gen = catalog.mark_program_progress(seq, 0, 5)
        next(gen)
        gen = catalog.mark_program_progress(seq, 4, 5)
        next(gen)