"""
Database module, exposes classes for simplifying working with Postgres.

class.ConnectionParameters:
    Dataclass to assist with correctly setting up a Postgres connection.

class.Client:
    The bread & butter of this module. Wraps aiopg to simplify connecting to,
    executing queries on, & disconnecting from a Postgres database.

class.Model:
    Not quite an ORM, but close. Used to assist in defining database queries &
    associating a Model type. Using this class will help manage separation of
    concerns.

class.ModelData:
    A simple TypedDict to define the shape of the data for a specific
    Model instance.
"""
from .connection import ConnectionParameters
from .client import Client
from .model import Model, ModelData
