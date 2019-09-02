**orz**: Result type
=============================

**orz** aims to provide a more pythonic and mature Result type(or similar to Result type) for Python.

Result is a Monad type for handling success response and errors without using `try ... except` or special values(e.g. `-1`, `0` or `None`). It makes your code more readable and more elegant.

Many langauges already have a builtin Result type. e.g. `Result in Rust <https://doc.rust-lang.org/std/result/>`_, `Either type in Haskell <http://hackage.haskell.org/package/base-4.12.0.0/docs/Data-Either.html>`_ , `Result type in Swift <https://developer.apple.com/documentation/swift/result>`_ and `Result type in OCaml <https://ocaml.org/learn/tutorials/error_handling.html#Resulttype>`_. And there's a `proposal in Go <https://github.com/golang/go/issues/19991>`_. Although `Promise in Javascript <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise>`_ is not a Result type, it handles errors fluently in a similar way.

Existing Result type Python libraries, such as `dbrgn/result <https://github.com/dbrgn/result>`_, `arcrose/result_py <https://github.com/arcrose/result_py>`_, and `ipconfiger/result2 <https://github.com/ipconfiger/result2>`_ did great job on porting Result from other languages. However, most of these libraries doesn't support Python 2(sadly, I still have to use it). And because of the syntax limitation of Python, like lack of pattern matching, it's not easy to show all the strength of Result type.

**orz** trying to make Result more pythonic and readable, useful in most cases.

Getting Start
=============

Just like other Python package, install it by `pip <https://pip.pypa.io/en/stable/>`_ into a `virtualenv <https://hynek.me/articles/virtualenv-lives/>`_, or use  `poetry <https://poetry.eustace.io/>`_ to automatically create and manage the virtualenv.

.. code-block:: console

   $ pip install orz

.. code-block:: python

   import orz

   def get_emails_rz(user):
       if user not in user_email_table:
           # Err for error
           return orz.Err('no such user')

       # Ok for success
       emails_rz = orz.Ok(user_emails_table['user'])
       return emails_rz


   # return first Ok value
   @orz.first_ok.wrap
   def get_message_rz(user):
       # orz.ensure for ensuring the value is of Result type
       # .check_not_none() transform Ok(None) into Err()
       yield orz.ensure(get_daily_recommendation_message(user)).check_not_none()

       # orz.catch() calls function and return Result
       yield (orz.catch(Exception, get_weekly_recommendation, user)
              .check_not_none())

       yield orz.ensure(get_greeting_message(user))


   # catch Exception and return Result
   @orz.catch.wrap(RuntimeError)
   def send_message_rz(user):
       nick_rz = get_nick_rz(user)
       email_rz = (
         get_emails_rz(user)
         .then(lambda emails: email[0], catch_raises=KeyError)
         .check(lambda email: not email.endswith('test.com'))
       )
       message_rz = get_message_rz()

       rz.then_unpack(lambda f, g: f+g)

       email = email_rz.get_or_raise(RuntimeError("can't get email addr"))
       message = message_rz.get_or_raise(RuntimeError("no available message"))
       nick = nick_rz.get_or(default=user)

       send_email.submit(
         email=email,
         title='Hi, {}'.format(nick),
         message=message)

       return nick, email


   (send_message_rz('joe')
    .then_unpack(
        lambda nick, email:
            print('message for {}<{}> submitted'.format(nick, email)))
    .or(
   )
   )
