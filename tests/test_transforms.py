import pytest
from decimal import Decimal
from marketplace_data import flatten_orders, validate_records

SAMPLE = [{"order_id":"O1","date":"2026-04-07","status":"paid",
          "items":[{"item_id":1,"seller_id":5,"product_id":30,
                    "quantity":3,"unit_price":"10.90"}]}]


def test_flatten_amount_and_structure():
    rows = flatten_orders(SAMPLE, '2026-04-07')
    assert len(rows) == 1
    assert rows[0][:3] == ('O1',1,'2026-04-07')
    assert rows[0][7] == Decimal('32.70')


def test_flatten_rejects_duplicate_items():
    bad = [dict(SAMPLE[0],items=SAMPLE[0]['items']*2)]
    with pytest.raises(ValueError, match='dupliquée'):
        flatten_orders(bad,'2026-04-07')


def test_flatten_rejects_wrong_day():
    with pytest.raises(ValueError, match='Date inattendue'):
        flatten_orders(SAMPLE,'2026-04-08')


def test_data_quality_non_empty():
    with pytest.raises(ValueError, match='vide'):
        validate_records([], '2026-04-07')


def test_data_quality_approved():
    validate_records(flatten_orders(SAMPLE, '2026-04-07'), '2026-04-07')


def test_data_quality_rejects_future_date():
    with pytest.raises(ValueError, match='futur'):
        validate_records(flatten_orders([dict(SAMPLE[0], date='2099-01-01')], '2099-01-01'), '2099-01-01')
