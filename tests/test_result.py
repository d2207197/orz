import pytest
import orz


def test_ok_basics():
    rz = orz.ok(42)
    assert bool(rz) is True
    assert len(rz) == 1
    assert rz.is_err() is False
    assert rz.is_ok() is True
    assert str(rz) == "Ok(42)"
    assert repr(rz) == "Ok(42)"
    assert rz.value == 42
    assert orz.ok(42) == orz.ok(42)
    with pytest.raises(AttributeError):
        rz.error


def test_err_basics():
    rz = orz.err(ValueError("failed"))
    assert bool(rz) is False
    assert len(rz) == 0
    assert rz.is_err() is True
    assert rz.is_ok() is False
    assert orz.err("failed") == orz.err("failed")
    assert orz.err("failed") != orz.err("wrong")
    assert str(rz) == "Err(ValueError('failed',))"
    assert repr(rz) == "Err(ValueError('failed',))"

    with pytest.raises(AttributeError):
        assert rz.value == 42

    assert isinstance(rz.error, ValueError)


def test_auto_unwrap():
    assert orz.ok(orz.ok(orz.ok(42))) == orz.ok(42)
    assert orz.err(orz.err(orz.err("failed"))) == orz.err("failed")
    with pytest.raises(ValueError):
        rz = orz.err(orz.ok(42))
    with pytest.raises(ValueError):
        rz = orz.ok(orz.err("failed"))


def test_get_or():
    rz = orz.ok(3)
    assert rz.get_or(0) == 3
    assert rz.get_or_raise(0) == 3

    rz = orz.err(ValueError("failed"))
    assert rz.get_or(0) == 0
    with pytest.raises(ValueError):
        rz.get_or_raise()


def test_and_then():
    rz = orz.ok(20).and_then(lambda v: v * 2).and_then(lambda v: v + 2)
    assert rz.value == 42
    assert rz == orz.ok(42)

    rz = orz.ok(20).and_then(lambda v: orz.ok(v * 2)).and_then(lambda v: orz.ok(v + 2))
    assert rz.value == 42
    assert rz == orz.ok(42)


def test_and_then_catch_raises():
    with pytest.raises(ValueError):
        orz.ok("a").and_then(int)

    with pytest.raises(KeyError):
        orz.ok({}).and_then(lambda d: d["k"])

    rz = orz.ok("3").and_then(int, catch_raises=ValueError)
    assert rz.is_ok()
    assert rz.value == 3

    rz = orz.ok("a").and_then(int, catch_raises=ValueError)

    assert rz.is_err()
    assert isinstance(rz.error, ValueError)


def test_and_then_return_result():
    rz = orz.ok({"k": 42}).and_then(
        lambda d: orz.ok(d["k"]) if "k" in d else orz.err("k not exist")
    )
    assert rz.is_ok()
    assert rz.value == 42

    rz = orz.ok({"k": 42}).and_then(
        lambda d: d["k"] if "k" in d else orz.err("k not exist")
    )
    assert rz.is_ok()
    assert rz.value == 42

    rz = orz.ok({}).and_then(
        lambda d: orz.ok(d["k"]) if "k" in d else orz.err("k not exist")
    )
    assert rz.is_err()
    assert rz.error == "k not exist"


def test_guard():
    rz = orz.ok(3).guard(lambda v: v > 0)
    assert rz.is_ok()
    assert rz.value == 3

    rz = orz.ok(3).guard(lambda v: v < 0)
    assert rz.is_err()
    assert isinstance(rz.error, orz.InvalidValueError)
    assert "Ok(3) was failed to pass the guard:" in repr(rz.error)

    rz = orz.err("failed").guard(lambda v: v < 0)
    assert rz.is_err()
    assert rz == orz.err("failed")

    rz = orz.err("failed").guard(lambda v: True)
    assert rz.is_err()
    assert rz == orz.err("failed")
