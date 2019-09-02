import inspect
from abc import abstractmethod
import functools as fnt

from .exceptions import CheckError

__all__ = ["Result", "Ok", "Err", "ensure", "catch", "first_ok"]


class UnSet(object):
    pass


class NonLocal(object):
    pass


class Result(object):
    @abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError()

    @abstractmethod
    def __bool__(self):
        raise NotImplementedError()

    @abstractmethod
    def __len__(self):
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self):
        raise NotImplementedError()

    @abstractmethod
    def value(self):
        raise NotImplementedError()

    @abstractmethod
    def error(self):
        raise NotImplementedError()

    @abstractmethod
    def is_ok(self):
        raise NotImplementedError()

    @abstractmethod
    def is_err(self):
        raise NotImplementedError()

    @abstractmethod
    def get_or(self, default=None):
        raise NotImplementedError()

    @abstractmethod
    def get_or_raise(self, error=None):
        raise NotImplementedError()

    @abstractmethod
    def then(self, func, catch_raises=None):
        raise NotImplementedError()

    @abstractmethod
    def check(self, func, error=UnSet):
        raise NotImplementedError()

    @abstractmethod
    def err_then(self, func, catch_raises=None):
        raise NotImplementedError()

    @abstractmethod
    def __and__(self):
        raise NotImplementedError()

    @abstractmethod
    def __or__(self):
        raise NotImplementedError()


class Ok(Result):
    __slots__ = "_value"

    def __init__(self, value):
        if isinstance(value, Ok):
            value = value.value
        elif isinstance(value, Err):
            raise ValueError("Can't cast Err to Ok")

        self._value = value

    def __iter__(self):
        yield self._value

    def __len__(self):
        return 1

    def __bool__(self):
        return True

    def __repr__(self):
        return "Ok({!r})".format(self._value)

    def __eq__(self, other):
        return isinstance(other, Ok) and other._value == self._value

    @property
    def value(self):
        return self._value

    @property
    def error(self):
        raise AttributeError("`error` attribute does not exist in Ok object")

    def is_ok(self):
        return True

    def is_err(self):
        return False

    def get_or(self, default):
        return self._value

    def get_or_raise(self, error=None):
        return self._value

    def then(self, func, catch_raises=None):
        if catch_raises is None:
            result = func(self._value)
        else:
            try:
                result = func(self._value)
            except catch_raises as e:
                result = Err(e)

        return ensure(result)

    def then_unpack(self, func, catch_raises=None):
        return self.then(lambda value: func(*value), catch_raises=catch_raises)

    def check(self, func, err=UnSet):
        if func(self._value):
            return self

        if err is UnSet:
            err = CheckError("{} was failed to pass the check: {!r}".format(self, func))
        return Err(err)

    def check_not_none(self, err=UnSet):
        if self._value is not None:
            return self

        if err is UnSet:
            caller = inspect.getframeinfo(inspect.stack()[1][0])
            err = CheckError(
                "failed to pass not None check: {}:{}".format(
                    caller.filename, caller.lineno
                )
            )
        return Err(err)

    def err_then(self, func, catch_raises=None):
        return self

    def err_then_unpack(self, func, catch_raises=None):
        return self


class Err(Result):
    __slots__ = "_error"

    def __init__(self, error=None):
        if isinstance(error, Err):
            error = error.error
        elif isinstance(error, Ok):
            raise ValueError("Can't cast Ok to Err")

        self._error = error

    def __iter__(self):
        return

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __repr__(self):
        return "Err({!r})".format(self._error)

    def __eq__(self, other):
        return isinstance(other, Err) and other._error == self._error

    @property
    def value(self):
        raise AttributeError("`value` attribute does not exist in Err object")

    @property
    def error(self):
        return self._error

    def is_ok(self):
        return False

    def is_err(self):
        return True

    def get_or(self, default):
        return default

    def get_or_raise(self, error=None):
        if error is not None:
            raise error
        else:
            raise self._error

    def then(self, func):
        return self

    def check(self, func, err=UnSet):
        return self

    def check_not_none(self, err=UnSet):
        return self

    def err_then(self, func, catch_raises=None):
        if catch_raises is None:
            result = func(self._error)
        else:
            try:
                result = func(self._error)
            except catch_raises as e:
                result = Err(e)

        return ensure(result)

    def err_then_unpack(self, func, catch_raises=None):
        return self.then(lambda value: func(*value), catch_raises=catch_raises)


Result.Ok = Ok
Result.Err = Err


def first_ok(results):
    """first ok or last err

    Examples
    --------
    >>> d = {'legacy_key': 42}
    >>> (orz.first_ok([
    ...      orz.ok(d.get('key')).check(lambda v: v is not None)
    ...      orz.ok(d.get('legacy_key')).check(lambda v: v is not None))
    ...    ]
    ...  .get_or(0)
    ... )
    42

    Parameters
    ----------
    results : Iterator[Result]

    Returns
    -------
    Result
        first ok or last err in parameters
    """
    result = None
    for result in results:
        if result.is_ok():
            return result
    return result


def first_ok_wrap(func):
    def wrapped(*args, **kwargs):
        return first_ok(func(*args, **kwargs))

    return wrapped


first_ok.wrap = first_ok_wrap


def catch(raises=(Exception,), func=None):
    """catch exception and return Ok or Err

    Examples
    --------
    >>> d = {'a': 40}
    >>> get_value = lambda k: d[k]
    >>> (orz.catch(get_value, 'a', raises=KeyError)
    ...     .map(lambda v: v + 2)
    ...     .get_or(0))
    42
    >>> (orz.catch(get_value, 'b', raises=[KeyError])
    ...     .map(lambda v: v + 2)
    ...     .get_or(0))
    0

    Parameters
    ----------
    raises : Tuple[Exception, ...]
        exceptions to be catch
    func : Function
        function will be called without arguments
    *args
        arguments for `func`
    **kwargs
        arguments for `func`

    Returns
    -------
    orz.Result

    """
    if isinstance(raises, list):
        raises = tuple(raises)

    non_local = NonLocal()  # nonlocal support for Python 2
    non_local.func = func
    non_local.raises = raises

    def wrapper(*args, **kwargs):
        if not callable(non_local.func):
            raise ValueError("value of `func` argument should be a callable")

        try:
            v = non_local.func(*args, **kwargs)
        except non_local.raises as e:
            return Err(e)

        return ensure(v)

    if func is None:

        def deco(func):
            non_local.func = func
            return fnt.update_wrapper(wrapper, func)

        return deco
    else:
        return fnt.update_wrapper(wrapper, func)


def all(*results, **kw_results):
    """returns an Ok of all values if all ok, or an Err of first Err

    Examples
    --------
    >>> d = {'n1': 1, 'n2': 2}
    >>> n1_rz = orz.catch(lambda: d['n1'], raises=KeyError)
    >>> n2_rz = orz.catch(lambda: d['n2'], raises=KeyError)
    >>> (orz.all(n1_rz, n2_rz)
    ...  .then(lambda vs: sum(vs))
    ...  .get_or_raise()
    ... )
    3

    >>> (orz.all(n1=n1_rz, n2=n2_rz)
    ...  .then(lambda n1, n2: sum(vs))
    ...  .get_or_raise()
    ... )
    3

    Parameters
    ----------
    results : Iterator[orz.Result]

    Returns
    -------
    orz.Result

    """
    rzs = []
    for rz in results:
        if rz.is_err():
            return rz
        elif rz.is_ok():
            rzs.append(rz)

    return Ok(rzs)


def ensure(obj):
    """ensure object is a Result instance

    Returns
    - ``obj`` if obj is an instance of Result
    - ``Err(obj)`` if obj is an instance of Exception
    - ``Ok(obj)`` for others

    """
    if isinstance(obj, Result):
        return obj
    elif isinstance(obj, Exception):
        return Err(obj)
    else:
        return Ok(obj)


def is_result(obj):
    if isinstance(obj, Result):
        return True

    return False
