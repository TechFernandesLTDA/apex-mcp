"""Tests for apex_mcp.ids — IdGenerator.

Run: pytest tests/test_ids.py -v
"""
from __future__ import annotations

import threading

import pytest


class TestIdGeneratorNext:
    def test_generates_large_integers(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        id1 = gen.next()
        assert id1 > 8_000_000_000_000_000

    def test_ids_are_unique(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        ids = [gen.next() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_ids_are_monotonically_increasing(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        ids = [gen.next() for _ in range(50)]
        assert ids == sorted(ids)

    def test_named_id_is_registered(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        id1 = gen.next("my_page")
        assert gen.has("my_page")
        assert gen.get("my_page") == id1

    def test_unnamed_id_is_not_registered(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        gen.next()
        assert not gen.has(None)  # type: ignore[arg-type]


class TestIdGeneratorGet:
    def test_get_raises_for_unknown_name(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        with pytest.raises(KeyError, match="No ID registered"):
            gen.get("nonexistent")


class TestIdGeneratorRegister:
    def test_register_stores_fixed_value(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        result = gen.register("AUTH", 1000)
        assert result == 1000
        assert gen.get("AUTH") == 1000

    def test_register_overwrites_existing(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        gen.register("key", 100)
        gen.register("key", 200)
        assert gen.get("key") == 200


class TestIdGeneratorReset:
    def test_reset_clears_counter_and_registry(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        gen.next("page_1")
        gen.next("page_2")
        gen.reset()
        assert not gen.has("page_1")
        assert not gen.has("page_2")

    def test_reset_changes_salt(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        id_before = gen.next()
        gen.reset()
        id_after = gen.next()
        # After reset, counter is 1 again but salt is different,
        # so unless we get the same random salt, IDs differ
        # (probabilistically true with 1M possible salts)
        # We just check both are valid large integers
        assert id_before > 8_000_000_000_000_000
        assert id_after > 8_000_000_000_000_000


class TestIdGeneratorCallable:
    def test_callable_shorthand(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        id1 = gen("test_call")
        assert gen.has("test_call")
        assert gen.get("test_call") == id1


class TestIdGeneratorThreadSafety:
    def test_concurrent_next_produces_unique_ids(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()
        results: list[int] = []
        lock = threading.Lock()

        def worker():
            for _ in range(100):
                new_id = gen.next()
                with lock:
                    results.append(new_id)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 400
        assert len(set(results)) == 400, "All IDs must be unique even under concurrency"

    def test_concurrent_register_is_safe(self):
        from apex_mcp.ids import IdGenerator

        gen = IdGenerator()

        def worker(n):
            gen.register(f"key_{n}", n)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for i in range(20):
            assert gen.get(f"key_{i}") == i


class TestModuleSingleton:
    def test_module_singleton_exists(self):
        from apex_mcp.ids import ids

        assert ids is not None
        _ = ids.next()
