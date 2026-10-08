def normalise_amount(value: str) -> str:
    return f"{float(value):.2f}"


def test_normalise_amount_rounds_to_two_decimals():
    assert normalise_amount("10.456") == "10.46"


def test_normalise_amount_keeps_integers():
    assert normalise_amount("7") == "7.00"
