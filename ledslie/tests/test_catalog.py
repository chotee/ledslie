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
        seq.program = program_name
        seq.frames = sequence_content
        seq.valid_time = valid_time
        catalog.add_program(program_name, seq)

    def test_get_frames(self):
        catalog = self.test_init()
        iter = catalog.frames_iter()
        assert "Bar" == next(iter)
        assert "Quux" == next(iter)
        assert "Foo" == next(iter)
        assert "Bar" == next(iter)

    def test_empty_catalog(self):
        catalog = Catalog()
        try:
            next(catalog.frames_iter())
        except IndexError:
            pass
        else:
            assert "Should not get here!"

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
        assert "Foo" == next(f_iter)  # Only foo is shown
        assert "Foo" == next(f_iter)
        catalog.now = lambda: 20  # Time passes
        self._create_and_add_sequence(catalog, "Second", ["Bar"])
        assert "Bar" == next(f_iter)
        assert "Foo" == next(f_iter)
        assert "Bar" == next(f_iter)
        catalog.now = lambda: 20+Config()["PROGRAM_RETIREMENT_AGE"]
        assert "Foo" == next(f_iter)  # Foo now gets retired.
        assert "Bar" == next(f_iter)
        assert "Bar" == next(f_iter)
        self._create_and_add_sequence(catalog, "Second", ["Bar2"])  # "Second" got updated
        assert "Bar2" == next(f_iter)
        catalog.now = lambda: 30+Config()["PROGRAM_RETIREMENT_AGE"]
        assert "Bar2" == next(f_iter)  # Still exists, because "Second" was updated.

    def test_valid_for(self):
        catalog = Catalog()
        f_iter = catalog.frames_iter()
        catalog.now = lambda: 10
        self._create_and_add_sequence(catalog, "long", ['Long'])
        catalog.now = lambda: 15
        self._create_and_add_sequence(catalog, "short", ['Short'], valid_time=30)
        assert "Short" == next(f_iter)
        assert "Long" == next(f_iter)
        catalog.now = lambda: 40
        assert "Short" == next(f_iter)
        assert "Long" == next(f_iter)
        catalog.now = lambda: 46  # Now the short program should be retired.
        assert "Short" == next(f_iter)
        assert "Long" == next(f_iter)
        assert "Long" == next(f_iter)
        assert "Long" == next(f_iter)

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