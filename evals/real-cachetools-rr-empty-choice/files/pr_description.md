# RRCache.popitem: EAFP instead of a length check

Let `choice` signal the empty case, like `random.choice` does, instead of checking `self.__keys` first.
