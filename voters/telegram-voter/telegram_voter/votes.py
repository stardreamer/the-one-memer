import dataclasses
import json
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Set

from telegram_voter.events import GotEvent


class VoteAttemptResult(Enum):
    Accepted = auto()
    VoteWasFinished = auto()
    VotedAlready = auto()

@dataclass
class Vote:
    mid: int
    for_votes: List[int]
    against_votes: List[int]
    base_event: str
    threshold: int

    def upvote(self, voter: int) -> VoteAttemptResult:
        if voter not in self.for_votes:
            self.for_votes.append(voter)
        else:
            return VoteAttemptResult.VotedAlready
        if voter in self.against_votes:
            self.against_votes.remove(voter)

        return VoteAttemptResult.Accepted

    def downvote(self, voter: int) -> VoteAttemptResult:
        if voter not in self.against_votes:
            self.against_votes.append(voter)
        else:
            return VoteAttemptResult.VotedAlready
        if voter in self.for_votes:
            self.for_votes.remove(voter)

        return VoteAttemptResult.Accepted

    @property
    def up(self) -> int:
        return len(self.for_votes)

    @property
    def down(self) -> int:
        return len(self.against_votes)

    @property
    def finished(self) -> bool:
        return self.accepted or self.declined

    @property
    def accepted(self) -> bool:
        return len(self.for_votes) >= self.threshold

    @property
    def declined(self) -> bool:
        return len(self.against_votes) >= self.threshold

    @staticmethod
    def from_got_event(mid: int, threshold: int, ev: GotEvent) -> "Vote":
        return Vote(
            mid=mid,
            for_votes=[],
            against_votes=[],
            base_event=ev.original_event,
            threshold=threshold,
        )

    @staticmethod
    def from_str(js: str) -> "Vote":
        d = json.loads(js)
        v = Vote(**d)
        v.for_votes = list(set(v.for_votes))
        v.against_votes = list(set(v.against_votes))
        return Vote(**d)

    def as_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), separators=(",", ":"))
