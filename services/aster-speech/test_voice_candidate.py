import asyncio
import threading
import unittest

from voice_candidate import VoiceScheduler, normalize_for_speech, semantic_units


class VoicePolicyTests(unittest.TestCase):
    def test_approved_normalization_and_pronunciations(self):
        self.assertEqual(
            normalize_for_speech("Home Assistant reports CA $1,234.50 for Lutron Caséta in B.C."),
            "Home uh-sist-unt reports one thousand two hundred and thirty-four Canadian "
            "dollars and fifty cents for Loo-tron kuh-set-uh in British Columbia.",
        )

    def test_semantic_units_preserve_all_words(self):
        text = "The first sentence is short. The second clause is longer, but remains readable."
        units = semantic_units(text, maximum=35)
        self.assertGreater(len(units), 2)
        self.assertEqual(" ".join(units).replace(". ", ". "), text)
        self.assertTrue(all(len(unit) <= 35 for unit in units))


class VoiceSchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = []

        def renderer(text):
            self.calls.append(text)
            return text.encode(), 24000

        self.scheduler = VoiceScheduler(renderer)
        await self.scheduler.start()

    async def asyncTearDown(self):
        await self.scheduler.close()

    async def test_stream_returns_ordered_units(self):
        result = [
            unit async for unit in self.scheduler.stream(
                "request-1", "First sentence. Second sentence."
            )
        ]
        self.assertEqual([unit.index for unit in result], [0, 1])
        self.assertEqual([unit.pcm for unit in result], [b"First sentence.", b"Second sentence."])

    async def test_rejects_empty_and_oversized_requests(self):
        with self.assertRaises(ValueError):
            await self.scheduler.stream("request-2", " ").__anext__()
        with self.assertRaises(ValueError):
            await self.scheduler.stream("request-3", "x" * 2001).__anext__()

    async def test_batch_does_not_occupy_second_worker(self):
        entered = threading.Event()
        release = threading.Event()

        def renderer(text):
            if text == "Batch work.":
                entered.set()
                release.wait(timeout=2)
            return text.encode(), 24000

        await self.scheduler.close()
        self.scheduler = VoiceScheduler(renderer)
        await self.scheduler.start()
        batch_task = asyncio.create_task(self._collect("batch", "Batch work.", "batch"))
        await asyncio.wait_for(asyncio.to_thread(entered.wait), timeout=1)
        interactive = await asyncio.wait_for(
            self._collect("interactive", "There, that's done.", "interactive"), timeout=1
        )
        self.assertEqual(interactive[0].pcm, b"There, that's done.")
        release.set()
        await batch_task

    async def _collect(self, request_id, text, caller):
        return [unit async for unit in self.scheduler.stream(request_id, text, caller)]


if __name__ == "__main__":
    unittest.main()
