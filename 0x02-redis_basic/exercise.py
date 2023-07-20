#!/usr/bin/env python3
""" Module for studying Redis """

# Import required libraries and modules
from functools import wraps
import redis
from typing import Union, Optional, Callable
from uuid import uuid4, UUID

# Decorator: count_calls
def count_calls(method: Callable) -> Callable:
    """Decorator for counting how many times a function has been called."""

    # Get the qualified name of the method (including the class name)
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Wrapper function for decorator functionality.
        Increments the call count for the method in Redis."""

        # Increment the call count for the method in Redis
        self._redis.incr(key)

        # Call the original method with its arguments and return the result
        return method(self, *args, **kwargs)

    return wrapper

# Decorator: call_history
def call_history(method: Callable) -> Callable:
    """Decorator to store the history of inputs and outputs for a particular function."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Wrapper function for decorator functionality.
        Stores the input and output history in Redis."""

        # Convert input arguments to a string representation
        input = str(args)

        # Store the input in the Redis list with the method's name + ":inputs" key
        self._redis.rpush(method.__qualname__ + ":inputs", input)

        # Call the original method with its arguments and get the output
        output = str(method(self, *args, **kwargs))

        # Store the output in the Redis list with the method's name + ":outputs" key
        self._redis.rpush(method.__qualname__ + ":outputs", output)

        # Return the output from the original method
        return output

    return wrapper

# Function: replay
def replay(fn: Callable):
    """Function that displays the history of calls for a particular function from Redis."""

    # Create a Redis client
    r = redis.Redis()

    # Get the qualified name of the function (including the class name)
    f_name = fn.__qualname__

    # Get the call count for the function from Redis
    n_calls = r.get(f_name)
    try:
        n_calls = n_calls.decode('utf-8')
    except Exception:
        n_calls = 0

    # Print the call count for the function
    print(f'{f_name} was called {n_calls} times:')

    # Get the list of input and output history from Redis
    ins = r.lrange(f_name + ":inputs", 0, -1)
    outs = r.lrange(f_name + ":outputs", 0, -1)

    # Iterate over the input and output history and display them
    for i, o in zip(ins, outs):
        try:
            i = i.decode('utf-8')
        except Exception:
            i = ""
        try:
            o = o.decode('utf-8')
        except Exception:
            o = ""

        print(f'{f_name}(*{i}) -> {o}')

# Class: Cache
class Cache:
    """Class for implementing a Cache."""

    def __init__(self):
        """Constructor Method.
        Initializes the Cache object by creating a Redis client and flushing the database."""

        # Create a Redis client instance and store it as a private variable (_redis)
        self._redis = redis.Redis()

        # Flush the Redis database to start with a clean slate
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """Method that generates a random key and stores data in Redis using the key.
        Returns the generated key."""

        # Generate a random key using uuid4()
        random_key = str(uuid4())

        # Store the data in Redis using the generated key
        self._redis.set(random_key, data)

        # Return the generated key
        return random_key

    def get(self, key: str,
            fn: Optional[Callable] = None) -> Union[str, bytes, int, float]:
        """Method to retrieve data associated with a key from Redis.
        Optionally, the data can be converted to the desired format using the provided function (fn)."""

        # Get the data associated with the key from Redis
        value = self._redis.get(key)

        # If a conversion function (fn) is provided, use it to convert the data
        if fn:
            value = fn(value)

        # Return the data
        return value

    def get_str(self, key: str) -> str:
        """Utility method that automatically converts the retrieved data to a string."""

        # Get the data associated with the key from Redis
        value = self._redis.get(key)

        # Decode the data to a string and return it
        return value.decode("utf-8")

    def get_int(self, key: str) -> int:
        """Utility method that automatically converts the retrieved data to an integer."""

        # Get the data associated with the key from Redis
        value = self._redis.get(key)

        try:
            # Try to convert the data to an integer and return it
            value = int(value.decode("utf-8"))
        except Exception:
            # If the conversion fails, return 0
            value = 0

        return value
