class NegativeSumError(Exception):
    def __init__(self, a, b):
        self.message = f"The sum of {a} and {b} is negative"
        super().__init__(self.message)


def sum_with_exceptions(a, b):
    sum = a + b
    if sum < 0:
        raise NegativeSumError(a, b)
    else:
        return sum
