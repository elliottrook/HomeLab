"""Least-privilege coordinator for AsterTV Music and Books requests.

The coordinator owns no HTTP endpoint or provider credential. Callers inject
one exact revalidator and writer per supported media type. Every submission is
resolved again from the authoritative sanitized discovery feed before either
call, and the returned television response is reduced to the shared contract.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from aster_acquisition_contract import (Command, ContractError, proposal,
                                        resolve, response)
from aster_tv_discovery import DiscoveryFeedError, read_feed


class BrokerError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthorityResolution:
    identity: str
    state: str
    payload: Any = None


class AcquisitionBroker:
    def __init__(self, feed_root: Path,
                 revalidators: Mapping[str, Callable[[Command], AuthorityResolution]],
                 writers: Mapping[str, Callable[[Command, Any], Mapping[str, Any]]],
                 feed_reader=read_feed):
        self.feed_root = Path(feed_root)
        self.revalidators = dict(revalidators)
        self.writers = dict(writers)
        self.feed_reader = feed_reader
        expected = {"album", "ebook", "audiobook"}
        if (set(self.revalidators) != expected or set(self.writers) != expected
                or not all(callable(value) for value in self.revalidators.values())
                or not all(callable(value) for value in self.writers.values())):
            raise BrokerError("acquisition-broker-capabilities-invalid")

    def submit(self, value: Any) -> dict[str, Any]:
        try:
            accepted = proposal(value)
            domain = "music" if accepted["media_type"] == "album" else "books"
            command = resolve(self.feed_reader(self.feed_root, domain), accepted)
        except (ContractError, DiscoveryFeedError, OSError, ValueError) as error:
            raise BrokerError("acquisition-candidate-unavailable") from error
        try:
            current = self.revalidators[command.media_type](command)
        except Exception as error:
            raise BrokerError("acquisition-revalidation-unavailable") from error
        if (not isinstance(current, AuthorityResolution)
                or current.identity != command.identity
                or current.state not in ("available", "requestable", "blocked")):
            raise BrokerError("acquisition-revalidation-invalid")
        if current.state == "available":
            return response(command, "available", None)
        if current.state != "requestable":
            raise BrokerError("acquisition-candidate-unavailable")
        try:
            result = self.writers[command.media_type](command, current.payload)
        except Exception as error:
            # The client journal treats any transport failure as uncertain and
            # never retries it automatically. Do not infer a safe retry here.
            raise BrokerError("acquisition-write-outcome-uncertain") from error
        if (not isinstance(result, Mapping)
                or set(result) != {"status", "request_id"}
                or result.get("status") not in ("pending", "processing")):
            raise BrokerError("acquisition-write-result-invalid")
        try:
            return response(command, result["status"], result["request_id"])
        except ContractError as error:
            raise BrokerError("acquisition-write-result-invalid") from error
