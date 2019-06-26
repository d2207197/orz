**orz**: Result type
=============================

**orz** aims to provide a more pythonic and mature Result type(or similar to Result type) for Python.

Result is a Monad type for handling success response and errors without using `try ... except` or special values(e.g. `-1`, `0` or `None`). It makes your code more readable and more elegant.

Many langauges already have a builtin Result type. e.g. `Result in Rust<https://doc.rust-lang.org/std/result/>`_, `Either type in Haskell<http://hackage.haskell.org/package/base-4.12.0.0/docs/Data-Either.html>`_ , `Result type in Swift <https://developer.apple.com/documentation/swift/result>`_ and `Result type in OCaml<https://ocaml.org/learn/tutorials/error_handling.html#Resulttype>`_. There's a `proposal in Go<https://github.com/golang/go/issues/19991>`_. Although `Promise in Javascript<https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise>`_ is not a Result type, it handles errors fluently in a similar way.

There're some existing Result type Python libraries, such as `dbrgn/result<https://github.com/dbrgn/result>`_, `arcrose/result_py <https://github.com/arcrose/result_py>`_, and `ipconfiger/result2 <https://github.com/ipconfiger/result2>`_. However, most of these libraries doesn't support Python 2(sadly, I still have to use it). And due to the limitation of Python syntax, like lack of pattern matching, it's not easy to show all the strength of Result type.

Getting Start
=============

Just like other Python package, install it by `pip <https://pip.pypa.io/en/stable/>`_ into a `virtualenv <https://hynek.me/articles/virtualenv-lives/>`_, or use  `poetry <https://poetry.eustace.io/>`_ to automatically create and manage the virtualenv.

.. code-block:: console

   $ pip install orz

.. code-block:: python

   import orz

   def get_user_email_rz(user):
       if user not in user_email_table:
           # Err for denoting
           return orz.Err('no such user')

       email = user_email_table['user']
       return (
         orz.as_result(email)
         .check(lambda email: email is not None,
                err='no valid email')
       )

   def get_message_candidates_rz(user):
       yield get_message1(user)
       yield get_message2(user)
       yield get_message3(user)

   def send_message(user):
       email_rz = (
        get_user_email(user)
        .check(lambda email: not email.endswith('test.com'))
       )
       message_rz = (
        orz.first_ok(get_message_candidates_rz())
       )
       (orz.all(email_rz, message_rz)
        .then(lambda email_rz


   user =
   get_user_email().
