import inspect
import warnings
from abc import abstractmethod, abstractproperty
from .exceptions import InvalidValueError
from functools import wraps

__all__ = ["Result", "Ok", "Err"]


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
    def get_or_raise(self, default_error=None):
        raise NotImplementedError()

    @abstractmethod
    def and_then(self, func, catch_raises=None):
        raise NotImplementedError()

    @abstractmethod
    def guard(self, func, error):
        raise NotImplementedError()

    @abstractmethod
    def or_else(self, func):
        raise NotImplementedError()

    @abstractmethod
    def __and__(self):
        raise NotImplementedError()

    @abstractmethod
    def __or__(self):
        raise NotImplementedError()

    @classmethod
    def first_ok(cls, results):
        """first ok or last err

        >>> Result.all([f, g, h]).then(lambda f, g, h: )

        >>> Result.first_ok([Err('wrong'), Ok(42), Err('error')])
        Ok(42)
        >>> Result.first_ok(Ok(i) if i % 3 == 2 else Err(i) for i in range(6))
        Ok(2)
        """
        result = None
        for result in results:
            if result.is_ok():
                return result
        return result

    @classmethod
    def first_err(cls, results):
        """first err or last ok"""
        result = None
        for result in results:
            if result.is_err():
                return result
        return result

    @classmethod
    def capture(cls, f, errors=(Exception,)):
        """capture exception and return Result

        >>> d = {'a': 40}
        >>> orz.capture(lambda: d['a'], KeyError).map(lambda v: v + 2).get_or(0)
        42
        >>> orz.capture(lambda: d['b'], KeyError).map(lambda v: v + 2).get_or(0)
        0
        """
        try:
            v = f()
        except errors as e:
            return Err(e)
        else:
            return Ok(v)

    @classmethod
    def silent(cls, f_or_error, *errors):
        """
        >>> @silent
        >>>
        """

        if inspect.isclass(f_or_error) and issubclass(f_or_error, Exception):
            errors = (f_or_error,) + tuple(more_errors)

            def deco(f):
                return cls._wrap_exceptable(f, errors)

            return deco
        if callable(f_or_error):
            f = f_or_error
            return cls._wrap_exceptable(f, errors)

    @classmethod
    def _wrap_exceptable(cls, f, errors):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                res = f(*args, **kwargs)
            except errors:
                return Nothing
            else:
                return Some(res)

        return wrapper


class UnSet(object):
    pass


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

    def get_or_raise(self, default_error=None):
        return self._value

    def and_then(self, func, catch_raises=None):
        if catch_raises is None:
            result = func(self._value)
        else:
            try:
                result = func(self._value)
            except catch_raises as e:
                result = Err(e)

        if not isinstance(result, Result):
            result = Ok(result)

        return result

    def guard(self, func, error=UnSet):
        if func(self._value):
            return self
        else:
            if error is UnSet:
                error = InvalidValueError(
                    "{} was failed to pass the guard: {!r}".format(self, func)
                )
            return Err(error)

    def or_else(self, result_func):
        return self


class Err(Result):
    __slots__ = "_error"

    def __init__(self, error):
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

    def get_or_raise(self, default_error=None):
        if default_error is not None:
            raise default_error
        else:
            raise self._error

    def and_then(self, func):
        return self

    def guard(self, func, error=UnSet):
        return self

    def or_else(self, func):
        result = func(self._error)
        if not isinstance(result, Result):
            raise ValueError("function should return a Result object")
        return result


Result.Ok = Ok
Result.Err = Err
