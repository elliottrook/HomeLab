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

    async def test_batch_units_are_bounded_without_fragmenting_interactive_text(self):
        text = (
            "This briefing sentence is deliberately longer than sixty characters, "
            "but it still contains safe clause and word boundaries."
        )
        batch = await self._collect("bounded-batch", text, "batch")
        interactive = await self._collect("unbounded-interactive", text, "interactive")
        self.assertGreater(len(batch), 1)
        self.assertTrue(all(len(unit.pcm.decode()) <= 20 for unit in batch))
        self.assertEqual(len(interactive), 1)
        self.assertEqual(interactive[0].pcm.decode(), text)

    async def test_batch_admits_only_one_unit_at_a_time(self):
        await self.scheduler.close()
        first_entered = threading.Event()
        release_first = threading.Event()

        def renderer(text):
            self.calls.append(text)
            if len(self.calls) == 1:
                first_entered.set()
                release_first.wait(timeout=2)
            return text.encode(), 24000

        self.scheduler = VoiceScheduler(renderer)
        await self.scheduler.start()
        text = "First batch sentence is here. Second batch sentence follows."
        task = asyncio.create_task(self._collect("one-at-a-time", text, "batch"))
        await asyncio.wait_for(asyncio.to_thread(first_entered.wait), timeout=1)
        self.assertEqual(len(self.calls), 1)
        release_first.set()
        result = await task
        self.assertGreater(len(result), 1)

    async def test_late_interactive_request_wins_batch_admission_grace(self):
        await self.scheduler.close()
        self.scheduler = VoiceScheduler(lambda text: (text.encode(), 24000))
        await self.scheduler.start()
        batch = asyncio.create_task(self._collect("waiting-batch", "Batch work.", "batch"))
        await asyncio.sleep(0.05)
        interactive = await self._collect("late-interactive", "Interactive work.", "interactive")
        self.assertEqual(interactive[0].pcm, b"Interactive work.")
        self.assertFalse(batch.done())
        await batch

    async def _collect(self, request_id, text, caller):
        return [unit async for unit in self.scheduler.stream(request_id, text, caller)]


if __name__ == "__main__":
    unittest.main()
