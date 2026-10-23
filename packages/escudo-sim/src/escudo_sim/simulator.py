"""Simulador con semilla de pagos inmediatos: tráfico legítimo (incluidos casos difíciles) y ataques con
ground truth. Día 0 = historia de calentamiento; día 1 = evaluación con ataques.

El orden de las llamadas al generador aleatorio es parte del contrato: cambiarlo cambia todas las cifras
de la línea base (lo vigila tests/test_baselines.py).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import StrEnum

from escudo_domain import Transfer

CITIES = {
    "bogota": (4.711, -74.072),
    "medellin": (6.244, -75.581),
    "cali": (3.452, -76.532),
    "barranquilla": (10.964, -74.796),
    "bucaramanga": (7.119, -73.122),
}
ABROAD = [(40.4168, -3.7038), (25.7617, -80.1918)]  # Madrid, Miami
DAY = 8 * 3600  # un "día" simulado de 8 horas
MIN_CUSTOMERS = 200  # los ataques eligen 200 víctimas distintas


class Scenario(StrEnum):
    LEGIT = "legit"
    ATO = "ato"  # toma de cuenta
    BURST = "burst"  # vaciado en ráfaga
    TRAVEL = "travel"  # viaje imposible
    APP_SCAM = "app_scam"  # estafa: la víctima paga a una mula desde su propio celular
    MULE_OUT = "mule_out"  # la mula reenvía a la colectora


@dataclass(frozen=True, slots=True)
class Labeled:
    transfer: Transfer
    is_fraud: bool
    scenario: Scenario


@dataclass(frozen=True, slots=True)
class _Customer:
    lat: float
    lon: float
    device: str
    typical: float
    payees: list[str]


class _World:
    """Estado de una simulación. Cada escenario es un método: la vitrina podrá dispararlos por separado."""

    def __init__(self, seed: int, n_customers: int) -> None:
        self.seed = seed
        self.rnd = rnd = random.Random(seed)
        self.ids = [f"c{seed}_{i}" for i in range(n_customers)]
        self.cust: dict[str, _Customer] = {}
        for c in self.ids:
            lat, lon = CITIES[rnd.choice(list(CITIES))]
            self.cust[c] = _Customer(
                lat=lat + rnd.uniform(-0.05, 0.05),
                lon=lon + rnd.uniform(-0.05, 0.05),
                device=f"{c}-phone",
                typical=min(max(rnd.lognormvariate(math.log(80_000), 0.8), 5_000), 3_000_000),
                payees=rnd.sample(self.ids, 4),
            )
        self.key_age = {c: rnd.uniform(30, 720) * 24 for c in self.ids}
        self.events: list[Labeled] = []
        self._counter = 0

    def emit(
        self,
        ts: float,
        sender: str,
        receiver: str,
        amount: float,
        device: str,
        where: tuple[float, float],
        receiver_key_age_h: float,
        scenario: Scenario,
    ) -> None:
        self._counter += 1
        t = Transfer(
            f"{self.seed}-{self._counter}",
            ts,
            sender,
            receiver,
            int(amount),
            device,
            where[0],
            where[1],
            receiver_key_age_h,
        )
        self.events.append(Labeled(t, scenario is not Scenario.LEGIT, scenario))

    def fraud_key_age(self) -> float:
        """60 % llaves recién creadas, 40 % cuentas "alquiladas" con llave vieja."""
        return self.rnd.uniform(1, 47) if self.rnd.random() < 0.6 else self.rnd.uniform(5, 300) * 24

    def when(self) -> float:
        return self.rnd.uniform(DAY + 600, 2 * DAY - 3600)

    def legit_traffic(self) -> None:
        """Dos días de pagos normales, con "legítimos difíciles": viajeros, celulares nuevos, llaves recién
        creadas, compras grandes y ráfagas para dividir una cuenta entre amigos."""
        rnd = self.rnd
        for c, p in self.cust.items():
            traveler = rnd.random() < 0.03
            for _ in range(rnd.randint(2, 14)):
                ts = rnd.uniform(0, 2 * DAY)
                where = (p.lat, p.lon)
                if traveler and ts > DAY:
                    where = CITIES[rnd.choice(list(CITIES))]
                device = p.device if rnd.random() > 0.03 else f"{c}-nuevo-{rnd.randint(0, 9)}"
                if rnd.random() < 0.85:
                    receiver, kage = rnd.choice(p.payees), None
                else:  # destinatario nuevo; en la era de las llaves muchas son recientes
                    receiver = f"nuevo-{rnd.randint(0, 10**9)}"
                    kage = rnd.uniform(1, 47) if rnd.random() < 0.15 else rnd.uniform(30, 720) * 24
                amount = p.typical * rnd.lognormvariate(0, 0.5) * (10 if rnd.random() < 0.02 else 1)
                key_age = kage if kage is not None else self.key_age.get(receiver, 9999)
                self.emit(ts, c, receiver, amount, device, where, key_age, Scenario.LEGIT)
            if rnd.random() < 0.05:
                t0 = rnd.uniform(DAY, 2 * DAY - 300)
                for k in range(rnd.randint(4, 6)):
                    self.emit(
                        t0 + k * rnd.uniform(5, 20),
                        c,
                        rnd.choice(self.ids),
                        rnd.uniform(20_000, 90_000),
                        p.device,
                        (p.lat, p.lon),
                        9999,
                        Scenario.LEGIT,
                    )

    def account_takeovers(self, victims: list[str]) -> None:
        """Dispositivo nuevo, otra ciudad o el exterior; la mitad de los atacantes usa montos discretos."""
        for v in victims:
            t0, p = self.when(), self.cust[v]
            where = self.rnd.choice(list(CITIES.values()) + ABROAD)
            mult = (5, 20) if self.rnd.random() < 0.5 else (1, 3)
            for k in range(self.rnd.randint(1, 3)):
                ts = t0 + k * self.rnd.uniform(60, 300)
                amount = min(p.typical * self.rnd.uniform(*mult), 8_000_000)
                self.emit(
                    ts,
                    v,
                    f"dest-ato-{v}-{k}",
                    amount,
                    f"atacante-{v}",
                    where,
                    self.fraud_key_age(),
                    Scenario.ATO,
                )

    def bursts(self, victims: list[str]) -> None:
        """Vaciado de cuenta: 5 a 8 envíos en menos de un minuto."""
        for v in victims:
            t0 = self.when()
            for k in range(self.rnd.randint(5, 8)):
                ts = t0 + k * self.rnd.uniform(4, 10)
                self.emit(
                    ts,
                    v,
                    f"dest-burst-{v}-{k}",
                    self.rnd.uniform(100_000, 400_000),
                    f"atacante-{v}",
                    (self.cust[v].lat, self.cust[v].lon),
                    self.fraud_key_age(),
                    Scenario.BURST,
                )

    def impossible_travel(self, victims: list[str]) -> None:
        """Un pago legítimo en Colombia y, 10 a 30 minutos después, otro desde Madrid o Miami."""
        for v in victims:
            p = self.cust[v]
            t0 = self.when()
            self.emit(
                t0,
                v,
                p.payees[0],
                p.typical,
                p.device,
                (p.lat, p.lon),
                self.key_age[p.payees[0]],
                Scenario.LEGIT,
            )
            where = self.rnd.choice(ABROAD)
            ts = t0 + self.rnd.uniform(600, 1800)
            self.emit(
                ts,
                v,
                f"dest-viaje-{v}",
                self.rnd.uniform(500_000, 3_000_000),
                f"atacante-{v}",
                where,
                self.fraud_key_age(),
                Scenario.TRAVEL,
            )

    def mule_rings(self, victims: list[str], rings: int = 5, mules_per_ring: int = 3) -> None:
        """Estafa APP: las víctimas pagan desde SU celular y ciudad.

        Cada mula reenvía el 90 % de lo recibido a una cuenta colectora.
        """
        vi = 0
        for ring in range(rings):
            mules = [f"mula{self.seed}_{ring}_{m}" for m in range(mules_per_ring)]
            collector = f"colector{self.seed}_{ring}"
            t0 = self.when()
            mule_key_age = self.fraud_key_age()
            for m in mules:
                received = 0
                for _ in range(self.rnd.randint(3, 9)):  # algunas mulas reciben poco: más difíciles
                    v = victims[vi % len(victims)]
                    vi += 1
                    p = self.cust[v]
                    amount = p.typical * self.rnd.uniform(1, 6)
                    received += int(amount)
                    self.emit(
                        t0 + self.rnd.uniform(0, 3000),
                        v,
                        m,
                        amount,
                        p.device,
                        (p.lat, p.lon),
                        mule_key_age,
                        Scenario.APP_SCAM,
                    )
                self.emit(
                    t0 + self.rnd.uniform(3100, 3500),
                    m,
                    collector,
                    received * 0.9,
                    f"{m}-phone",
                    (4.6, -74.1),
                    9999,
                    Scenario.MULE_OUT,
                )


def simulate(seed: int, n_customers: int = 1500) -> list[Labeled]:
    """Dos días de pagos de `n_customers` clientes en 5 ciudades, con ataques el día 1.

    Los eventos se devuelven ordenados por tiempo.
    """
    if n_customers < MIN_CUSTOMERS:
        raise ValueError(f"n_customers debe ser >= {MIN_CUSTOMERS} (víctimas de los escenarios de ataque)")
    world = _World(seed, n_customers)
    world.legit_traffic()
    victims = world.rnd.sample(world.ids, MIN_CUSTOMERS)
    world.account_takeovers(victims[:25])
    world.bursts(victims[25:35])
    world.impossible_travel(victims[35:45])
    world.mule_rings(
        victims[45:] + victims[:45]
    )  # mismo recorrido circular de víctimas que la prueba de concepto
    world.events.sort(key=lambda e: e.transfer.ts)
    return world.events
