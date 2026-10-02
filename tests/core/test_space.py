"""KindSpace: a separate universe of names, with its own pool, order, lock and cap."""
import contextvars
import threading

import anyio
import anyio.to_thread
import pytest

from kind import Kind, KindSpace, SpaceError, current_space
from kind.core.space import DEFAULT_SPACE


def test_a_space_is_a_separate_universe_of_names():
    outer = Kind("Stock")
    with KindSpace(name="inner") as inner:
        assert current_space() is inner
        stock = Kind("Stock")
        assert stock is not outer and stock != outer  # same name, another entity
        assert stock.space is inner and Kind.len() == 1
    assert current_space() is outer.space and Kind("Stock") is outer


def test_closing_a_space_drops_its_kinds_and_freezes_the_survivors():
    with KindSpace() as space:
        survivor = Kind("survivor")
        survivor.append(Kind("child"))
    assert space.closed and len(space) == 0
    assert survivor.name == "survivor" and [c.name for c in survivor.children] == ["child"]  # still readable
    with pytest.raises(SpaceError, match="closed space"):
        survivor.append(Kind("another"))
    with pytest.raises(SpaceError, match="closed"):
        with space:
            Kind("new")


def test_edges_across_spaces_are_refused():
    outer = Kind("outer")
    with KindSpace():
        inner = Kind("inner")
        for link in (lambda: inner.append(outer), lambda: outer.append(inner),
                     lambda: inner.relate(outer, how="x"), lambda: outer.insert(inner)):
            with pytest.raises(SpaceError, match="across spaces"):
                link()


def test_nested_spaces_restore_the_outer_one():
    with KindSpace(name="a") as a:
        with KindSpace(name="b") as b:
            assert current_space() is b
        assert current_space() is a


def test_each_space_has_its_own_order_and_counters():
    Kind("x")
    with KindSpace():
        assert Kind.next().name == "kind_0" and Kind.first().name == "kind_0" and Kind("y")._position == 1.0
    assert Kind.first().name == "x"


def test_serialization_stays_inside_the_space():
    Kind("outside").append(Kind("also outside"))
    with KindSpace():
        root = Kind("root")
        root.append(Kind("leaf"))
        text = root.to_json()
    assert "outside" not in text
    with KindSpace():
        rebuilt = Kind.from_json(text)
        assert rebuilt.name == "root" and Kind.len() == 2


def test_the_default_space_cannot_be_closed():
    with pytest.raises(SpaceError, match="default space"):
        DEFAULT_SPACE.close()


@pytest.mark.anyio
async def test_tasks_and_worker_threads_see_the_space_of_their_context():
    with KindSpace() as space:
        seen = []

        async def task():
            seen.append(current_space())

        async with anyio.create_task_group() as group:
            group.start_soon(task)
        seen.append(await anyio.to_thread.run_sync(current_space))  # anyio copies the context
        assert seen == [space, space]


def test_a_plain_thread_needs_the_context_copied():
    with KindSpace() as space:
        seen = {}
        plain = threading.Thread(target=lambda: seen.setdefault("plain", current_space()))
        context = contextvars.copy_context()
        copied = threading.Thread(target=lambda: context.run(lambda: seen.setdefault("copied", current_space())))
        for thread in (plain, copied):
            thread.start()
            thread.join()
    assert seen["plain"] is DEFAULT_SPACE and seen["copied"] is space


def test_concurrent_linking_keeps_both_ends_consistent():
    """Eight threads link 200 children each into shared parents: no lost or duplicated edges."""
    with KindSpace():
        parents = [Kind(f"p{i}") for i in range(4)]
        context = contextvars.copy_context()

        def work(worker):
            for n in range(200):
                child = Kind(f"c{n % 50}")
                parents[(worker + n) % 4].append(child)

        threads = [threading.Thread(target=context.run, args=(work, w)) for w in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for parent in parents:
            assert len(parent.children) == len(set(parent.children)) <= 50
            assert all(parent in child.parents for child in parent.children)
        assert Kind.len() == 54


@pytest.mark.parametrize("settle", ["freeze", "close space"])
def test_metadata_and_context_become_read_only_once_settled(settle):
    with KindSpace():
        kind = Kind("k")
        kind.metadata["kept"] = 1
        kind.context["note"] = "x"
        if settle == "freeze":
            kind.freeze()
    for mapping in (kind.metadata, kind.context):
        with pytest.raises(TypeError):
            mapping["new"] = 2
    assert kind.metadata["kept"] == 1 and kind.context["note"] == "x"
