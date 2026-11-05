import unittest

import nlu_j2_reference_primitives_v1 as primitives


class J2ReferencePrimitiveTests(unittest.TestCase):
    def test_utf8_bytes_truncate_without_redecode_and_pad_right(self):
        encoded = primitives.encode_input("abc")
        self.assertEqual((97, 98, 99), encoded[:3])
        self.assertEqual((256,) * 509, encoded[3:])
        split = primitives.encode_input("a" * 511 + "é")
        self.assertEqual(512, len(split))
        self.assertEqual(0xC3, split[-1])

    def test_empty_wrong_type_and_overlength_are_bounded(self):
        for value in ("", b"bytes", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                primitives.encode_input(value)
        self.assertEqual((120,) * 512, primitives.encode_input("x" * 600))

    def test_splitmix64_known_sequence_and_wrap(self):
        generator = primitives.SplitMix64(0)
        self.assertEqual(
            [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F],
            [generator.next_u64() for _ in range(3)])
        value = primitives.SplitMix64((1 << 64) - 1).next_u64()
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, primitives.MASK64)

    def test_uniform_uses_high_53_bits(self):
        integer = primitives.SplitMix64(20261104).next_u64()
        value = primitives.SplitMix64(20261104).uniform53()
        self.assertEqual((integer >> 11) / float(1 << 53), value)
        self.assertGreaterEqual(value, 0.0)
        self.assertLess(value, 1.0)

    def test_seed_bounds_fail_closed(self):
        for seed in (-1, 1 << 64, 1.0, "0"):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                primitives.SplitMix64(seed)


if __name__ == "__main__": unittest.main()
