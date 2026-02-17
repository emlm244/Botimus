from tools.math import range_map


def test_range_map_regular_case():
    assert range_map(0.5, 0.0, 1.0, 0.0, 10.0) == 5.0


def test_range_map_degenerate_input_range_returns_out_min():
    assert range_map(7.0, 2.0, 2.0, 11.0, 99.0) == 11.0
