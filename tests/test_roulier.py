
import types


def get_expected_carriers():
    from roulier import carriers
    from roulier.carrier import Carrier

    expected_carriers = {}
    for carrier_name, carrier_module in vars(carriers).items():
        if (
            carrier_name.startswith('_')
            or not isinstance(carrier_module, types.ModuleType)
            or not hasattr(carrier_module, carrier_name)
        ):
            continue
        base_carrier_module = getattr(carrier_module, carrier_name)
        if not isinstance(base_carrier_module, types.ModuleType):
            continue
        for attr_name, attr_value in vars(base_carrier_module).items():
            if (
                attr_name.startswith('_')
                or not issubclass(attr_value, Carrier)
            ):
                continue
            expected_carriers[carrier_name] = attr_value
    return expected_carriers


def test_get_carriers():
    """
    Verifies that roulier.get_carriers and roulier.get return expected values
    """
    from roulier import roulier
    carrier_names = roulier.get_carriers()
    expected_carriers = get_expected_carriers()
    assert isinstance(carrier_names, list), \
        "get_carriers must return a list"
    assert set(carrier_names) == set(expected_carriers.keys()), \
        "get_carriers does not return all expected carriers"
    for carrier_name in carrier_names:
        assert isinstance(roulier.get(carrier_name), expected_carriers.get(carrier_name)), \
            "roulier.get seems to not return the expected carrier"


def test_mro_carriers():
    """
    Verifies that each specific carrier class extends our `Carrier` base class
    """
    from roulier import roulier
    from roulier.carrier import Carrier
    for carrier_name in roulier.get_carriers():
        assert isinstance(roulier.get(carrier_name), Carrier), \
            "This specific carrier does not extends roulier.carrier.Carrier"
