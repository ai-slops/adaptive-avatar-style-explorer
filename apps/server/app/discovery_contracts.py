from typing import Literal

from pydantic import Field, model_validator

from .contracts import Strict

Part = Literal["face", "hair", "outfit", "body", "accessories", "palette"]


class DiscoveryRoundInput(Strict):
    requestId: str = Field(min_length=1, max_length=100)
    expectedRevision: int = Field(ge=0)
    intent: Literal["continue", "different", "focus", "observe", "correct", "adopt"] = (
        "continue"
    )
    candidateId: str | None = None
    directionId: str | None = None
    part: Part = "hair"
    preservePart: Part | None = None
    view: Literal["front", "character_left_profile", "back"] = "front"
    brief: str = Field(default="", max_length=2000)
    count: int = Field(default=4, ge=1, le=6)


class DiscoveryReactionInput(Strict):
    requestId: str = Field(min_length=1, max_length=100)
    expectedRevision: int = Field(ge=0)
    action: Literal[
        "interest",
        "release_direction",
        "choose_a",
        "choose_b",
        "both",
        "no_preference",
        "neither",
        "skip",
        "image_wrong",
        "keep_part",
        "unlock_part",
        "use_design",
        "undo",
        "rename_direction",
    ]
    candidateIds: list[str] = Field(default_factory=list, max_length=6)
    linkIds: list[str] = Field(default_factory=list, max_length=6)
    part: Part | None = None
    targetReactionId: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    replaceSelection: bool = False

    @model_validator(mode="after")
    def shape(self):
        if self.action == "undo":
            if not self.targetReactionId or self.candidateIds or self.linkIds:
                raise ValueError("Undo needs only a prior reaction")
        elif not self.candidateIds:
            raise ValueError("Choose the options actually shown")
        if (
            self.action in ("choose_a", "choose_b", "both", "no_preference")
            and len(self.candidateIds) != 2
        ):
            raise ValueError("A relative reaction needs exactly two options")
        if (
            self.action
            in (
                "interest",
                "release_direction",
                "keep_part",
                "unlock_part",
                "use_design",
                "rename_direction",
                "image_wrong",
            )
            and len(self.candidateIds) != 1
        ):
            raise ValueError("This action applies to one option")
        if self.action in ("keep_part", "unlock_part") and self.part is None:
            raise ValueError("Name the visible part")
        return self


class DiscoveryImportItem(Strict):
    assetId: str
    filename: str = Field(default="", max_length=255)
    candidateId: str | None = None
    independentReference: bool = False
    exportPermission: bool = False


class DiscoveryImportInput(Strict):
    requestId: str = Field(min_length=1, max_length=100)
    items: list[DiscoveryImportItem] = Field(min_length=1, max_length=12)
    roundId: str | None = None


class DiscoveryGenerationInput(Strict):
    requestId: str = Field(min_length=1, max_length=100)
    candidateIds: list[str] = Field(min_length=1, max_length=6)
    authorizeTurns: int = Field(ge=1, le=6)
    approveReferenceTransmission: bool = False
    exportPermission: bool = False
    model: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def bounded(self):
        if len(set(self.candidateIds)) != len(
            self.candidateIds
        ) or self.authorizeTurns != len(self.candidateIds):
            raise ValueError(
                "Authorize exactly one turn for each distinct pending option"
            )
        return self


class DiscoveryActiveRound(Strict):
    roundId: str


class DiscoveryLibraryInput(Strict):
    requestId: str = Field(min_length=1, max_length=100)
    expectedRevision: int = Field(ge=0)
    versionId: str


class DiscoveryReferencesInput(Strict):
    requestId: str = Field(min_length=1, max_length=100)
    expectedRevision: int = Field(ge=0)
    inspirationIds: list[str] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def distinct(self):
        if len(self.inspirationIds) != len(set(self.inspirationIds)):
            raise ValueError("Choose each reference once")
        return self
