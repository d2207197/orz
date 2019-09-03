import inspect
from abc import abstractmethod
import functools as fnt

from .exceptions import CheckError

__all__ = ["Result", "Ok", "Err", "ensure", "catch", "first_ok", "all", "is_result"]


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
    def then_unpack(self, func, catch_raises=None):
        raise NotImplementedError()

    @abstractmethod
    def check(self, func, error=UnSet):
        raise NotImplementedError()

    @abstractmethod
    def check_not_none(self, err=UnSet):
        raise NotImplementedError()

    @abstractmethod
    def err_then(self, func, catch_raises=None):
        raise NotImplementedError()

    @abstractmethod
    def err_then_unpack(self, func, catch_raises=None):
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
    >>> orz.first_ok([orz.Err('wrong value'), orz.Ok(42), orz.Ok(3)])
    Ok(42)

    >>> @orz.first_ok.wrap
    >>> def get_value_rz(key):
    ...     yield l1cache_rz(key)
    ...     yield l2cache_rz(key)
    ...     yield get_db_rz(key)

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
    >>> @orz.catch(raises=KeyError)
    ... def get_score_rz(subj):
    ...     score_db = {'math': 80, 'physics': 95}
    ...     return score_db[subj]

    >>> get_score_rz('math')
    Ok(80)
    >>> get_score_rz('bio')
    Err(KeyError('bio',))

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


def all(results):
    """returns an Ok of all values if all ok, or an Err of first Err

    Examples
    --------
    >>> orz.all([orz.Ok(39), orz.Ok(2), orz.Ok(1)])
    Ok([39, 2, 1])
    >>> orz.all([orz.Ok(40), orz.Err('wrong value'), orz.Ok(1)])
    Err('wrong value')

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
            rzs.append(rz.value)

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
