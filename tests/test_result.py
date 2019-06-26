from __future__ import print_function
import pytest
import orz


def test_ok():
    rz = orz.Ok(42)
    assert bool(rz) is True
    assert len(rz) == 1
    assert rz.is_err() is False
    assert rz.is_ok() is True
    assert str(rz) == "Ok(42)"
    assert repr(rz) == "Ok(42)"
    assert rz.value == 42
    assert orz.Ok(42) == orz.Ok(42)
    with pytest.raises(AttributeError):
        rz.error


def test_err():
    rz = orz.Err(ValueError("failed"))
    assert bool(rz) is False
    assert len(rz) == 0
    assert rz.is_err() is True
    assert rz.is_ok() is False
    assert orz.Err("failed") == orz.Err("failed")
    assert orz.Err("failed") != orz.Err("wrong")
    assert str(rz).startswith("Err(ValueError('failed'")
    assert repr(rz).startswith("Err(ValueError('failed'")

    with pytest.raises(AttributeError):
        assert rz.value == 42

    assert isinstance(rz.error, ValueError)


def test_as_result():
    assert orz.as_result(orz.Ok(42)) == orz.Ok(42)
    assert orz.as_result(42) == orz.Ok(42)
    assert orz.as_result(orz.Err("failed")) == orz.Err("failed")


def test_catch():
    def get_value(k):
        if not isinstance(k, str):
            raise ValueError("k should be of str type")
        d = {"a": 42}
        return d[k]

    rz = orz.catch(KeyError, get_value, "a")
    assert rz.is_ok()
    assert rz.value == 42

    with pytest.raises(ValueError):
        rz = orz.catch(KeyError, get_value, 3)

    rz = orz.catch(KeyError, get_value, "b")
    assert rz.is_err()
    assert isinstance(rz.error, KeyError)

    rz = orz.catch((ValueError, KeyError), get_value, "b")
    assert rz.is_err()
    assert isinstance(rz.error, KeyError)

    rz = orz.catch((ValueError, KeyError), get_value, 3)
    assert rz.is_err()
    assert isinstance(rz.error, ValueError)

    rz = orz.catch([ValueError, KeyError], get_value, 3)
    assert rz.is_err()
    assert isinstance(rz.error, ValueError)


def test_resultify():
    def get_value(k):
        if not isinstance(k, str):
            raise ValueError("k should be of str type")
        d = {"a": 42}
        return d[k]

    get_value_rz = orz.resultify((ValueError, KeyError), get_value)
    assert get_value_rz("a") == orz.Ok(42)
    assert get_value_rz("b").is_err()
    assert isinstance(get_value_rz("b").error, KeyError)

    @orz.resultify((ValueError, KeyError))
    def get_value_rz(k):
        if not isinstance(k, str):
            raise ValueError("k should be of str type")
        d = {"a": 42}
        return d[k]

    assert get_value_rz("a") == orz.Ok(42)
    assert get_value_rz("b").is_err()
    assert isinstance(get_value_rz("b").error, KeyError)


def test_auto_unwrap():
    assert orz.Ok(orz.Ok(orz.Ok(42))) == orz.Ok(42)
    assert orz.Err(orz.Err(orz.Err("failed"))) == orz.Err("failed")
    with pytest.raises(ValueError):
        rz = orz.Err(orz.Ok(42))
    with pytest.raises(ValueError):
        rz = orz.Ok(orz.Err("failed"))


def test_get_or():
    rz = orz.Ok(3)
    assert rz.get_or(0) == 3
    assert rz.get_or_raise(0) == 3

    rz = orz.Err(ValueError("failed"))
    assert rz.get_or(0) == 0
    with pytest.raises(ValueError):
        rz.get_or_raise()


def test_and_then():
    rz = orz.Ok(20).then(lambda v: v * 2).then(lambda v: v + 2)
    assert rz.value == 42
    assert rz == orz.Ok(42)

    rz = orz.Ok(20).then(lambda v: orz.Ok(v * 2)).then(lambda v: orz.Ok(v + 2))
    assert rz.value == 42
    assert rz == orz.Ok(42)


def test_and_then_catch_raises():
    with pytest.raises(ValueError):
        orz.Ok("a").then(int)

    with pytest.raises(KeyError):
        orz.Ok({}).then(lambda d: d["k"])

    rz = orz.Ok("3").then(int, catch_raises=ValueError)
    assert rz.is_ok()
    assert rz.value == 3

    rz = orz.Ok("a").then(int, catch_raises=ValueError)

    assert rz.is_err()
    assert isinstance(rz.error, ValueError)


def test_and_then_return_result():
    rz = orz.Ok({"k": 42}).then(
        lambda d: orz.Ok(d["k"]) if "k" in d else orz.Err("k not exist")
    )
    assert rz.is_ok()
    assert rz.value == 42

    rz = orz.Ok({"k": 42}).then(
        lambda d: d["k"] if "k" in d else orz.Err("k not exist")
    )
    assert rz.is_ok()
    assert rz.value == 42

    rz = orz.Ok({}).then(
        lambda d: orz.Ok(d["k"]) if "k" in d else orz.Err("k not exist")
    )
    assert rz.is_err()
    assert rz.error == "k not exist"


def test_check():
    rz = orz.Ok(3).check(lambda v: v > 0)
    assert rz.is_ok()
    assert rz.value == 3

    rz = orz.Ok(3).check(lambda v: v < 0)
    assert rz.is_err()
    assert isinstance(rz.error, orz.InvalidValueError)
    assert "Ok(3) was failed to pass the check:" in repr(rz.error)

    rz = orz.Err("failed").check(lambda v: v < 0)
    assert rz.is_err()
    assert rz == orz.Err("failed")

    rz = orz.Err("failed").check(lambda v: True)
    assert rz.is_err()
    assert rz == orz.Err("failed")

    rz = orz.Ok(3).check(lambda v: v < 0, err='check failed')
    assert rz.is_err()
    assert rz == orz.Err("check failed")

    rz = orz.Ok(3).check(lambda v: v < 0, err=orz.Err('check failed 2'))
    assert rz.is_err()
    assert rz == orz.Err("check failed 2")


def test_err_then(capsys):
    rz = orz.Ok(3).err_then(lambda error: print(error))
    assert rz == orz.Ok(3)

    rz = orz.Err("failed").err_then(lambda error: print(error))
    captured = capsys.readouterr()
    assert captured.out == "failed\n"


def test_first():
    def get_candidates():
        yield orz.Err("failed 1")
        yield orz.Ok(1)
        yield orz.Ok(2)
        yield orz.Err("failed 2")

    rz = orz.first_ok(get_candidates())
    assert rz == orz.Ok(1)

    def get_candidates():
        yield orz.Err("failed 1")
        yield orz.Err("failed 2")

    rz = orz.first_ok(get_candidates())
    assert rz == orz.Err("failed 2")
