"""Extended JSON encoding to encode API responses properly."""

import logging
from typing import cast, Any
from uuid import UUID

from amqp_worker.connection import Channel
from amqp_worker.serializer import ResponseEncoder, JSONEncoderTypes
from amqp_worker.rpc_worker import JSONGzipRPC
from amqp_worker.queue_worker import JSONGzipMaster


LOGGER = logging.getLogger(__name__)


# The workers need to be able to parse some types not supported by the
# default JSONEncoder. Extending amqp_worker's ResponseEncoder (itself an
# extension of JSONEncoder) & building an amqp pattern object that uses
# our extended encoder allows amqp_worker to serialize our Models
# correctly.

class ExtendedJSONEncoder(ResponseEncoder):
    """Extend JSONEncoder to handle additional data types.

    Now handles the following new types:

    -------------------------------
    | python             | json   |
    |--------------------|--------|
    | uuid.UUID          | string | -> to str, then to JSON string
    -------------------------------

    All others fall back to default JSONEncoder rules.
    """

    def default(self, o: Any) -> JSONEncoderTypes:
        """
        Add serialization for new types.

        Adds support for pydantic.BaseModel, datetime.date, uuid.UUID, &
        decimal.Decimal.
        """
        LOGGER.debug('Using custom serializer...')
        LOGGER.debug(f'o: {o}')
        LOGGER.debug(f'type: {type(o)}')

        # first parse for extended types:

        if isinstance(o, UUID):
            LOGGER.debug('o is instance of UUID')
            return str(o)

        # then, fall back to ResponseEncoder.default method
        return ResponseEncoder.default(self, o)


async def json_gzip_rpc_factory(
    channel: Channel
) -> JSONGzipRPC:
    """
    Build a Pattern using JSONEncoder Extension.

    Intended to be passed to an AMQP Worker on initialization to replace
    default Pattern with default JSONEncoder.
    """
    pattern = cast(
        JSONGzipRPC,
        await JSONGzipRPC.create(channel))
    # replace default encoder with extended JSON encoder
    pattern.json_encoder = ExtendedJSONEncoder()

    return pattern


def json_gzip_queue_factory(
    channel: Channel
) -> JSONGzipMaster:
    """
    Build a Pattern using JSONEncoder Extension.

    Intended to be passed to an AMQP Worker on initialization to replace
    default Pattern with default JSONEncoder.
    """
    pattern = JSONGzipMaster(channel)
    # replace default encoder with extended JSON encoder
    pattern.json_encoder = ExtendedJSONEncoder()

    return pattern
