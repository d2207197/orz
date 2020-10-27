=============================
**orz**: Result type
=============================

**orz** aims to provide a more pythonic and mature Result type(or similar to Result type) for Python.

Result is a Monad type for handling success response and errors without using `try ... except` or special values(e.g. `-1`, `0` or `None`). It makes your code more readable and more elegant.

Many langauges already have a builtin Result type. e.g. `Result in Rust <https://doc.rust-lang.org/std/result/>`_, `Either type in Haskell <http://hackage.haskell.org/package/base-4.12.0.0/docs/Data-Either.html>`_ , `Result type in Swift <https://developer.apple.com/documentation/swift/result>`_ and `Result type in OCaml <https://ocaml.org/learn/tutorials/error_handling.html#Resulttype>`_. And there's a `proposal in Go <https://github.com/golang/go/issues/19991>`_. Although `Promise in Javascript <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise>`_ is not a Result type, it handles errors fluently in a similar way.

Existing Result type Python libraries, such as `dbrgn/result <https://github.com/dbrgn/result>`_, `arcrose/result_py <https://github.com/arcrose/result_py>`_, and `ipconfiger/result2 <https://github.com/ipconfiger/result2>`_ did great job on porting Result from other languages. However, most of these libraries doesn't support Python 2(sadly, I still have to use it). And because of the syntax limitation of Python, like lack of pattern matching, it's not easy to show all the strength of Result type.

**orz** trying to make Result more pythonic and readable, useful in most cases.

Install Orz
============

Just like other Python package, install it by `pip
<https://pip.pypa.io/en/stable/>`_ into a `virtualenv
<https://hynek.me/articles/virtualenv-lives/>`_, or use `poetry
<https://poetry.eustace.io/>`_ to automatically create and manage the
virtualenv.

.. code-block:: console

   $ pip install orz

Cheat Sheet
============
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``orz.Ok(value)``                                                 | Create a Result object                                                                            |
| ``orz.Err(error)``                                                |                                                                                                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``orz.catch(raises=(Exception,))(func)``                          | Wrap a function to return an `Ok` when success, or return an `Err` when exception is raised       |
|                                                                   |                                                                                                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``[Ok|Err].then(func, catch_raises=None)``                        | Transform the wrapped value/error through `func`.                                                 |
| ``[Ok|Err].err_then(func, catch_raises=None)``                    |                                                                                                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``[Ok|Err].then_unpack(func, catch_raises=None)``                 |     Same as ``then()`` and ``err_then()``, but values are unpacked as arguments of ``func``.      |
| ``[Ok|Err].err_then_unpack(func, catch_raises=None)``             |                                                                                                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``[Ok|Err].get_or(default)``                                      | ``Ok``: Get the wrapped value.                                                                    |
| ``[Ok|Err].get_or_raise(self, error=None)``                       | ``Err``: Raise excetpion or get default value.                                                    |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``[Ok|Err].guard(pred, err=UnSet)``                               | ``Ok``: Make sure value in Ok pass the predicate function ``pred``, or return an ``Err`` object.  |
| ``[Ok|Err].guard_none(err=UnSet)``                                | ``Err``: Return self.                                                                             |
|                                                                   |                                                                                                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``[Ok|Err].fill(pred, value)``                                    | ``Ok``: Return self.                                                                              |
|                                                                   | ``Err``: Return ``Ok(value)`` if the wrapped error pass the predicate function.                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``bool([Ok|Err])``                                                | Check whether the object is Ok or Err.                                                            |
| ``[Ok|Err].is_ok()``                                              |                                                                                                   |
| ``[Ok|Err].is_err()``                                             |                                                                                                   |
| ``isinstance(obj, orz.Ok)``                                       |                                                                                                   |
| ``isinstance(obj, orz.Err)``                                      |                                                                                                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``orz.is_result(obj)``                                            | Check if the object is a Result object(Ok or Err).                                                |
| ``isinstance(obj, orz.Result)``                                   |                                                                                                   |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``orz.all(results)``                                              | Get an Ok of all values if all are Ok, or an Err of first Err                                     |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``orz.first_ok(results)``                                         | Get first ok or last err                                                                          |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+
| ``orz.ensure(obj)``                                               | Ensure object is an instance of Result.                                                           |
+-------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+



Getting Start
=============

Create a ``orz.Result`` object
------------------------------

Wrap the return value with ``orz.Ok`` explicitly for indicating success. And
return an ``orz.Err`` object when something went wrong. Normally, the value wraped with
``Err`` is an error message or an exception object.

.. code-block:: python

   >>> import orz

   >>> def get_score_rz(subj):
   ...     score_db = {'math': 80, 'physics': 95}
   ...     if subj in score_db:
   ...         return orz.Ok(score_db[subj])
   ...     else:
   ...         return orz.Err('subj does not exist: ' + subj)

   >>> get_score_rz('math')
   Ok(80)
   >>> get_score_rz('bio')
   Err('subj does not exist: bio')

A handy decorator ``orz.catch`` can transform normal function into a
Result-oriented function. The return value would be wraped with ``orz.Ok``
automatically, and exceptions would be captured and wraped with ``orz.Err``.

.. code-block:: python

   >>> @orz.catch(raises=KeyError)
   ... def get_score_rz(subj):
   ...     score_db = {'math': 80, 'physics': 95}
   ...     return score_db[subj]

   >>> get_score_rz('math')
   Ok(80)
   >>> get_score_rz('bio')
   Err(KeyError('bio',))

Processing Pipeline
-------------------

Both ``Ok`` and ``Err`` are of ``Result`` type, they have the same set of methods for further processing. The value in ``Ok`` would be transformed with ``then(func)``. And ``Err`` would skip the transformation, and propogate the error to the next stage.

.. code-block:: python

   >>> def get_letter_grade_rz(score):
   ...     if 90 <= score <= 100: return orz.Ok('A')
   ...     elif 80 <= score < 90: return orz.Ok('B')
   ...     elif 70 <= score < 80: return orz.Ok('C')
   ...     elif 60 <= score < 70: return orz.Ok('D')
   ...     elif 0 <= score <= 60: return orz.Ok('F')
   ...     else: return orz.Err('Wrong value range')

   >>> get_score_rz('math')
   Ok(80)
   >>> get_score_rz('math').then(get_letter_grade_rz)
   Ok('B')
   >>> get_score_rz('bio')
   Err(KeyError('bio',))
   >>> get_score_rz('bio').then(get_letter_grade_rz)
   Err(KeyError('bio',))


The ``func`` pass to the ``then(func, catch_raises=None)`` can be a normal
function which returns an ordinary value. The returned value would be wraped with
``Ok`` automatically. Use ``catch_raises`` to capture exceptions and returned as an ``Err`` object.

.. code-block:: python

   >>> letter_grade_rz = get_score_rz('math').then(get_letter_grade_rz)
   >>> msg_rz = letter_grade_rz.then(lambda letter_grade: 'your grade is {}'.format(letter_grade))
   >>> msg_rz
   Ok('your grade is B')

Connect all the ``then(func)`` calls together. And use
``Result.get_or(default)`` to get the final
value.

.. code-block:: python

   >>> def get_grade_msg(subj):
   ...      return (
   ...          get_score_rz(subj)
   ...          .then(get_letter_grade_rz)
   ...          .then(lambda letter_grade: 'your grade is {}'.format(letter_grade))
   ...          .get_or('something went wrong'))

   >>> get_grade_msg('math')
   'your grade is B'
   >>> get_grade_msg('bio')
   'something went wrong'

If you prefer to raise an exception rather than get a fallback value, use ``get_or_raise(error)`` instead.

.. code-block:: python

   >>> def get_grade_msg(subj):
   ...      return (
   ...          get_score_rz(subj)
   ...          .then(get_letter_grade_rz)
   ...          .then(lambda letter_grade: 'your grade is {}'.format(letter_grade))
   ...          .get_or_raise())

   >>> get_grade_msg('math')
   'your grade is B'
   >>> get_grade_msg('bio')
   Traceback (most recent call last):
   ...
   KeyError: 'bio'


Handling Error
--------------

Use ``Result.err_then(func, catch_raises)`` to convert ``Err`` back to ``Ok`` or to other ``Err``.

.. code-block:: python

   >>> get_score_rz('bio')
   Err(KeyError('bio',))
   >>> get_score_rz('bio').then(get_letter_grade_rz)
   Err(KeyError('bio',))
   >>> (get_score_rz('bio')
   ...  .err_then(lambda error: 0 if isinstance(error, KeyError) else error))
   Ok(0)
   >>> (get_score_rz('bio')
   ...  .err_then(lambda error: 0 if isinstance(error, KeyError) else error)
   ...  .then(get_letter_grade_rz))
   Ok('F')
   >>> (get_score_rz('bio')
   ...  .then(get_letter_grade_rz)
   ...  .err_then(lambda error: 'F' if isinstance(error, KeyError) else error))
   Ok('F')


Most of the time, ``fill()`` is more concise to turn some ``Err`` back.

.. code-block:: python

   >>> get_score_rz('bio').fill(lambda error: isinstance(error, KeyError), 0)
   Ok(0)

Check whether the returned value is `Err` or `Ok`.

.. code-block:: python

   >>> num_rz = orz.Ok(42)
   >>> num_rz.is_ok()
   True
   >>> num_rz.is_err()
   False
   >>> isinstance(num_rz, orz.Ok)
   True
   >>> bool(num_rz)
   True
   >>> bool(orz.Ok(True))  # you always get True for Ok
   True
   >>> bool(orz.Ok(False))  # you always get True for Ok
   True
   >>> bool(orz.Err(True))  # you always get True for Err
   False

More in Orz
===========

Process Multiple Result objects
-------------------------------

To ensure all values are ``Ok`` and handle them together.

.. code-block:: python

   >>> orz.all([orz.Ok(39), orz.Ok(2), orz.Ok(1)])
   Ok([39, 2, 1])
   >>> orz.all([orz.Ok(40), orz.Err('wrong value'), orz.Ok(1)])
   Err('wrong value')

   >>> orz.all([orz.Ok(40), orz.Ok(2)]).then(lambda values: sum(values))
   Ok(42)
   >>> orz.all([orz.Ok(40), orz.Ok(2)]).then_unpack(lambda n1, n2: n1 + n2)
   Ok(42)


``then_all()`` is useful when you want to apply multiple functions to the same value.

.. code-block:: python

   >>> orz.Ok(3).then_all(lambda n: n+2, lambda n: n+1)
   Ok([5, 4])
   >>> orz.Ok(3).then_all(lambda n: n+2, lambda n: n+1).then_unpack(lambda n1, n2: n1 + n2)
   Ok(9)

Use ``first_ok()`` To get the first available value.

.. code-block:: python

   >>> orz.first_ok([orz.Err('E1'), orz.Ok(42), orz.Ok(3)])
   Ok(42)
   >>> orz.first_ok([orz.Err('E1'), orz.Err('E2'), orz.Err('E3')])
   Err('E3')
   >>> orz.Ok(15).then_first_ok(
   ...     lambda v: 2 if (v % 2) == 0 else orz.Err('not a factor'),
   ...     lambda v: 3 if (v % 3) == 0 else orz.Err('not a factor'),
   ...     lambda v: 5 if (v % 5) == 0 else orz.Err('not a factor'))
   Ok(3)

Guard value
-----------

.. code-block:: python

   >>> orz.Ok(3).guard(lambda v: v > 0)
   Ok(3)
   >>> orz.Ok(-3).guard(lambda v: v > 0)
   Err(GuardError('Ok(-3) was failed to pass the guard: <function <lambda> at ...>',))
   >>> orz.Ok(-3).guard(lambda v: v > 0, err=orz.Err('value should be greater than zero'))
   Err('value should be greater than zero')

In fact, guard is a short-hand for a pattern of ``then()``.

.. code-block:: python

   >>> (orz.Ok(-3)
   ...  .then(lambda v:
   ...        orz.Ok(v) if v > 0
   ...        else orz.Err('value should be greater than zero')))
   Err('value should be greater than zero')

   >>> orz.Ok(3).guard_none()
   Ok(3)
   >>> orz.Ok(None).guard_none()
   Err(GuardError('failed to pass not None guard: ...',))

Convert any value to Result type
--------------------------------

``orz.ensure`` always returns a Result object.

.. code-block:: python

   >>> orz.ensure(42)
   Ok(42)
   >>> orz.ensure(orz.Ok(42))
   Ok(42)
   >>> orz.ensure(orz.Ok(orz.Ok(42)))
   Ok(42)
   >>> orz.ensure(orz.Err('failed'))
   Err('failed')
   >>> orz.ensure(KeyError('a'))
   Err(KeyError('a',))


Check if object is a Result
----------------------------

.. code-block:: python

   >>> orz.is_result(orz.Ok(3))
   True
   >>> isinstance(orz.Ok(3), orz.Result)
   True
   >>> orz.Ok(3).is_ok()
   True
   >>> orz.Ok(3).is_err()
   False
   >>> orz.Err('E').is_ok()
   False
   >>> orz.Err('E').is_err()
   True
