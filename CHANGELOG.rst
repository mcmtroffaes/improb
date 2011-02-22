Version 0.1.1 (in development)
------------------------------

* Fixed calculation of conditional credal set.

* Added SetFunction.get_choquet to calculate the Choquet integral
  (contributed by Erik Quaeghebeur).

* Added __radd__, __rmul__, and __rsub__ for Gamble (contributed by
  Erik Quaeghebeur).

* Event.__sub__ now only does set difference with a collections.Set
  (so Event minus Gamble will be a Gamble via Gamble.__radd__, but
  Event minus Event is an Event).

* Event.__init__ now raises a ValueError when creating an event with
  elements that are not in the possibility space, instead of silently
  omitting them (fixes issue #3, reported by Erik Quaeghebeur).

Version 0.1.0 (24 August 2010)
------------------------------

* First release.
