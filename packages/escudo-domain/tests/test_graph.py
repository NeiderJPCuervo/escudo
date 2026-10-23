from collections import defaultdict

from hypothesis import given
from hypothesis import strategies as st

from escudo_domain import Transfer, UnionFind, mule_rings, pass_through_accounts


def t(i: int, ts: float, sender: str, receiver: str, amount: int) -> Transfer:
    return Transfer(f"t{i}", ts, sender, receiver, amount, "cel", 0.0, 0.0, 999)


def scenario() -> list[Transfer]:
    txs = [t(i, i * 60, f"victima{i}", "mula1", 500_000) for i in range(6)]
    txs += [t(10 + i, i * 60, f"victima{10 + i}", "mula2", 400_000) for i in range(5)]
    txs += [t(30, 900, "mula1", "colector", 2_800_000), t(31, 950, "mula2", "colector", 1_900_000)]
    txs += [t(40 + i, i * 60, f"cliente{i}", "tienda", 50_000) for i in range(8)]  # comercio: no reenvía
    return txs


def test_mules_forward_almost_everything_merchants_do_not() -> None:
    assert pass_through_accounts(scenario()) == {"mula1", "mula2"}


def test_forwarding_outside_window_does_not_count() -> None:
    txs = [t(i, i * 60, f"v{i}", "m", 100) for i in range(5)]
    txs.append(t(99, 3600 * 5, "m", "colector", 500))
    assert pass_through_accounts(txs) == set()


def test_rings_group_mules_with_shared_collector() -> None:
    txs = scenario()
    assert mule_rings(txs, pass_through_accounts(txs)) == [{"mula1", "mula2", "colector"}]


edges = st.lists(st.tuples(st.integers(0, 9), st.integers(0, 9)), max_size=25)


@given(edges)
def test_union_find_matches_connected_components(pairs: list[tuple[int, int]]) -> None:
    uf = UnionFind()
    adj: defaultdict[str, set[str]] = defaultdict(set)
    for a, b in pairs:
        uf.union(str(a), str(b))
        adj[str(a)].add(str(b))
        adj[str(b)].add(str(a))
    seen: set[str] = set()
    expected: list[set[str]] = []
    for start in adj:
        if start in seen:
            continue
        comp, stack = set(), [start]
        while stack:
            n = stack.pop()
            if n not in comp:
                comp.add(n)
                stack.extend(adj[n] - comp)
        seen |= comp
        expected.append(comp)
    assert sorted(map(sorted, uf.groups())) == sorted(map(sorted, expected))
