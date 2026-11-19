"""Ponawianie operacji z backoffem wykładniczym (#28 backlog). Czysto funkcyjne,
sleep wstrzykiwalny (testy = natychmiast). Pod egzekucję brokera: przejściowe błędy
(429/5xx/sieć) ponawiamy, trwałe (walidacja, 'insufficient balance') NIE — od tego
jest `should_retry`."""
import time


def with_retries(fn, *, attempts: int = 4, base_delay: float = 2.0,
                 retry_on: tuple = (Exception,), should_retry=None, sleep=time.sleep):
    """Woła fn() do `attempts` razy. Ponawia tylko wyjątki z `retry_on`, a gdy podano
    `should_retry(exc)->bool` — tylko te, dla których zwróci True (reszta leci dalej od
    razu). Backoff: base_delay * 2**i między próbami. Po wyczerpaniu rzuca ostatni błąd."""
    last = None
    n = max(1, attempts)
    for i in range(n):
        try:
            return fn()
        except retry_on as e:  # noqa: PERF203
            last = e
            if should_retry is not None and not should_retry(e):
                raise
            if i < n - 1 and base_delay > 0:
                sleep(base_delay * (2 ** i))
    raise last
