import asyncio
import threading
import unittest

from voice_candidate import VoiceScheduler, normalize_for_speech, semantic_units


class VoicePolicyTests(unittest.TestCase):
    def test_approved_normalization_and_pronunciations(self):
        self.assertEqual(
            normalize_for_speech("Home Assistant reports CA $1,234.50 for Lutron Caséta in B.C."),
            "Home Assistant reports one thousand two hundred and thirty-four Canadian "
            "dollars and fifty cents for Lutron Caseta in British Columbia.",
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

    async def test_two_distinct_renderers_back_the_interactive_workers(self):
        await self.scheduler.close()
        first_entered = threading.Event()
        release_first = threading.Event()

        def first(text):
            first_entered.set()
            release_first.wait(timeout=2)
            return b"worker-0:" + text.encode(), 24000

        def second(text):
            return b"worker-1:" + text.encode(), 24000

        self.scheduler = VoiceScheduler((first, second))
        await self.scheduler.start()
        first_task = asyncio.create_task(self._collect("first", "First.", "interactive"))
        await asyncio.wait_for(asyncio.to_thread(first_entered.wait), timeout=1)
        second_result = await asyncio.wait_for(
            self._collect("second", "Second.", "interactive"), timeout=1
        )
        self.assertEqual(second_result[0].pcm, b"worker-1:Second.")
        release_first.set()
        await first_task

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

    async def test_dedicated_batch_renderer_leaves_both_interactive_workers_free(self):
        await self.scheduler.close()
        batch_entered = threading.Event()
        release_batch = threading.Event()
        interactive_calls = []

        def interactive(text):
            interactive_calls.append(text)
            return b"interactive:" + text.encode(), 24000

        def batch(text):
            batch_entered.set()
            release_batch.wait(timeout=2)
            return b"batch:" + text.encode(), 24000

        self.scheduler = VoiceScheduler(interactive, batch_renderer=batch)
        await self.scheduler.start()
        batch_task = asyncio.create_task(self._collect("batch", "News briefing.", "batch"))
        await asyncio.wait_for(asyncio.to_thread(batch_entered.wait), timeout=1)
        results = await asyncio.gather(
            self._collect("interactive-1", "First reply.", "interactive"),
            self._collect("interactive-2", "Second reply.", "interactive"),
        )
        self.assertEqual(
            {result[0].pcm for result in results},
            {b"interactive:First reply.", b"interactive:Second reply."},
        )
        self.assertCountEqual(interactive_calls, ["First reply.", "Second reply."])
        release_batch.set()
        batch_result = await batch_task
        self.assertEqual(batch_result[0].pcm, b"batch:News briefing.")

    async def _collect(self, request_id, text, caller):
        return [unit async for unit in self.scheduler.stream(request_id, text, caller)]


if __name__ == "__main__":
    unittest.main()
