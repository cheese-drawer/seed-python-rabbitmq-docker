"""Script for managing database migrations.

Exposes two methods:
    sync        diff app to live db & apply changes, use for dev primarily
    pending     diff schema dump & save to file, used for prod primarily
"""

from contextlib import contextmanager
import io
import os
import random
import string
import sys
from typing import Any, Tuple, Generator

from migra import Migration  # type: ignore
from psycopg2 import connect  # type: ignore
from psycopg2 import sql
from psycopg2.sql import Composed
from sqlbag import (  # type: ignore
    S,
    load_sql_from_folder,
    load_sql_from_file)

# DB_USER = os.getenv('DB_USER', 'postgres')
# DB_PASS = os.getenv('DB_PASS', 'postgres')
# DB_HOST = os.getenv('DB_HOST', 'localhost')
# DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'test')
DB_PASS = os.getenv('DB_PASS', 'pass')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'dev')

DB_URL = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}'


def _prompt(question: str) -> bool:
    """Prompt user with simple yes/no question & return True if answer is y."""
    print(f'{question} ', end='')
    return input().strip().lower() == 'y'


def _temp_name() -> str:
    """
    Generate a temporary name.

    Prefixes a string of 10 random characters with 'temp_db' & returns it.
    """
    random_letters = [random.choice(string.ascii_lowercase) for _ in range(10)]
    rnd = "".join(random_letters)
    tempname = 'temp_db' + rnd

    return tempname


def _create_db(cursor: Any, name: str) -> None:
    """Create a database with a given name."""
    query = sql.SQL('create database {name};').format(
        name=sql.Identifier(name))

    cursor.execute(query)


def _kill_query(dbname: str) -> Composed:
    """Build & return SQL query that kills connections to a given database."""
    query = """
    SELECT
        pg_terminate_backend(pg_stat_activity.pid)
    FROM
        pg_stat_activity
    WHERE
        pg_stat_activity.datname = {dbname}
        AND pid <> pg_backend_pid();
    """

    return sql.SQL(query).format(dbname=sql.Literal(dbname))


def _drop_db(cursor: Any, name: str) -> None:
    """Drop a database with a given name."""
    revoke: Composed = sql.SQL(
        'REVOKE CONNECT ON DATABASE {name} FROM PUBLIC;'
    ).format(
        name=sql.Identifier(name))

    kill_other_connections: Composed = _kill_query(name)

    drop: Composed = sql.SQL('DROP DATABASE {name};').format(
        name=sql.Identifier(name))

    cursor.execute(revoke)
    cursor.execute(kill_other_connections)
    cursor.execute(drop)


def _load_pre_migration(session: S) -> None:
    """
    Load schema for production server.

    Uses sql schema file saved at migrations/production.dump.sql
    """
    load_sql_from_file(session, 'migrations/production.dump.sql')


def _load_from_app(session: S) -> None:
    """
    Load schema from application source.

    Uses all .sql files stored at ./src/models/**
    """
    load_sql_from_folder(session, 'src/models')


@contextmanager
def _get_schema_diff(
    from_db_url: str,
    target_db_url: str
) -> Generator[Tuple[str, Migration], Any, Any]:
    """Get schema diff between two databases using djrobstep/migra."""
    with S(from_db_url) as from_schema_session, \
            S(target_db_url) as target_schema_session:
        migration = Migration(
            from_schema_session,
            target_schema_session)
        migration.set_safety(False)
        migration.add_all_changes()

        yield migration.sql, migration


@contextmanager
def _temp_db(host: str, user: str, password: str) -> Generator[str, Any, Any]:
    """Create, yield, & remove a temporary database as context."""
    connection = connect(f'postgres://{user}:{password}@{host}/{DB_NAME}')
    connection.set_session(autocommit=True)
    name = _temp_name()

    with connection.cursor() as cursor:
        _create_db(cursor, name)
        yield f'postgres://{user}:{password}@{host}/{name}'
        _drop_db(cursor, name)

    connection.close()


def sync() -> None:
    """
    Compare live database to application schema & apply changes to database.

    Uses running database specified for application via
    `DB_[USER|PASS|HOST|NAME]` environment variables & compares to application
    schema defined at `./src/models/**/*.sql`.
    """
    with _temp_db(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
    ) as temp_db_url:
        print(f'db url: {DB_URL}')
        print(f'temp url: {temp_db_url}')

        with S(temp_db_url) as session:
            _load_from_app(session)

        with _get_schema_diff(DB_URL, temp_db_url) as diff:
            pending_changes, migration = diff

            if migration.statements:
                print('THE FOLLOWING CHANGES ARE PENDING:', end='\n\n')
                print(pending_changes)

                if _prompt('Apply these changes?'):
                    print('Applying...')
                    migration.apply()
                else:
                    print('Not applying.')

            else:
                print('Already synced.')


def pending() -> None:
    """
    Compare a production schema to application schema & save difference.

    Uses production schema stored at `./migrations/production.dump.sql` &
    application schema defined at `./src/models/**/*.sql`, then saves
    difference at `./migrations/pending.sql`.
    """
    with _temp_db(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
    ) as prod_schema_db_url, _temp_db(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
    ) as target_db_url:
        print(f'prod temp url: {prod_schema_db_url}')
        print(f'target temp url: {target_db_url}')
        _load_pre_migration(prod_schema_db_url)
        _load_from_app(target_db_url)

        with _get_schema_diff(prod_schema_db_url, target_db_url) as diff:
            pending_changes, _ = diff

            print(f'Pending changes: \n{pending_changes}')

            with io.open('migrations/pending.sql') as file:
                file.write(pending_changes)


if __name__ == '__main__':
    tasks = {
        'sync': sync,
        'pending': pending,
    }

    try:
        tasks[sys.argv[1]]()
    except KeyError:
        print('No such task')
    except IndexError:
        print('No task given')
