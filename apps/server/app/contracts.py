"""Strict public write contracts. Ownership and derived eligibility are server fields."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .learning.reference import encode_observed

Region = Literal['whole', 'face', 'hair', 'body', 'outfit', 'accessories', 'palette', 'surface', 'custom']
State = Literal['unspecified', 'proposed', 'inferred', 'user_confirmed']
View = Literal['front', 'front_three_quarter', 'character_left_profile', 'character_right_profile', 'back', 'back_three_quarter', 'top', 'bottom', 'other', 'unknown']

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)

class ProjectInput(Strict):
    title: str = Field(min_length=1, max_length=120)

class Property(Strict):
    value: str | float | bool | list[str] | None
    state: State
    sourceEventIds: list[str] = Field(default_factory=list, max_length=100)
    sourceDepictionLinkIds: list[str] = Field(default_factory=list, max_length=100)
    notes: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def unspecified_is_unknown(self):
        if self.state == 'unspecified' and self.value is not None:
            raise ValueError('An unspecified property must have a null value')
        return self

class Relation(Strict):
    component: str = Field(min_length=1, max_length=120)
    relation: Literal['attached_to', 'layered_over', 'connected_to', 'symmetric_with']
    target: str = Field(min_length=1, max_length=120)
    state: State

class CanonicalInput(Strict):
    morphology: Literal['humanoid', 'non_humanoid', 'unspecified'] = 'unspecified'
    properties: dict[str, Property] = Field(default_factory=dict, max_length=100)
    componentRelations: list[Relation] = Field(default_factory=list, max_length=100)
    unresolvedDecisions: list[str] = Field(default_factory=list, max_length=100)

    @field_validator('properties')
    @classmethod
    def design_properties_only(cls, value):
        forbidden = {'view', 'camera', 'projection', 'framing', 'pose', 'expression', 'lighting', 'background', 'crop'}
        if any(len(k) > 120 or not k or k.split('.')[0].lower() in forbidden for k in value):
            raise ValueError('Presentation conditions do not belong in canonical design properties')
        return value

class DesignInput(Strict):
    title: str = Field(min_length=1, max_length=120)
    branchId: str = 'main'
    spec: CanonicalInput

class VersionInput(Strict):
    parentVersionId: str
    spec: CanonicalInput
    expectedEventSequence: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=2000)

class Presentation(Strict):
    view: View = 'unknown'
    projection: Literal['orthographic', 'perspective', 'unknown'] = 'unknown'
    framing: Literal['full_body', 'upper_body', 'face', 'detail', 'unknown'] = 'unknown'
    poseId: str | None = None
    expressionId: str | None = None
    lightingClass: str | None = None
    backgroundClass: str | None = None
    source: Literal['user_reported', 'visually_estimated', 'renderer_metadata'] = 'user_reported'

class Attribute(Strict):
    value: str | float | None
    confidence: float = Field(ge=0, le=1)
    visibility: Literal['visible', 'occluded', 'out_of_frame', 'unknown']

class Observation(Strict):
    region: Region
    attributes: dict[str, Attribute] = Field(default_factory=dict)
    observedPresentation: Presentation

    @field_validator('attributes')
    @classmethod
    def fixed_schema(cls, value):
        encode_observed({k: v.model_dump() for k, v in value.items()})
        return value

class DepictionInput(Strict):
    assetId: str
    sourceKind: Literal['reference', 'external_result', 'model_capture_user_reported'] = 'reference'
    originPlanId: str | None = None
    originPromptRevision: int | None = Field(default=None, ge=1)
    sourceBuildId: str | None = None
    caption: str = Field(default='', max_length=2000)
    exportPermission: bool = False
    explicitlyUnassociated: bool = False

    @model_validator(mode='after')
    def mapping(self):
        if (self.originPlanId is None) != (self.originPromptRevision is None):
            raise ValueError('Provide both plan ID and exact revision')
        if self.sourceKind == 'external_result' and self.originPlanId is None and not self.explicitlyUnassociated:
            raise ValueError('Map the prompt revision or explicitly choose an unassociated reference')
        if (self.sourceKind == 'model_capture_user_reported') != (self.sourceBuildId is not None):
            raise ValueError('Model captures require a reported build')
        return self

class LinkInput(Strict):
    depictionId: str
    versionId: str

class FindingInput(Strict):
    kind: Literal['presentation_mismatch', 'identity_or_design_drift', 'design_unspecified', 'cross_view_conflict', 'design_suitability', 'execution_defect', 'implementation_issue_reported']
    region: Region
    severity: Literal['info', 'warning', 'blocking']
    description: str = Field(min_length=1, max_length=3000)

class EvidenceReviewInput(Strict):
    linkId: str
    status: Literal['compatible', 'partial', 'mismatch']
    reviewedRegions: list[Region] = Field(min_length=1, max_length=9)
    observations: list[Observation] = Field(default_factory=list, max_length=9)
    findings: list[FindingInput] = Field(default_factory=list, max_length=20)
    expectedEventSequence: int = Field(ge=0)

    @model_validator(mode='after')
    def reviewed_scope(self):
        if self.status == 'mismatch' and self.observations:
            raise ValueError('A mismatching depiction supplies no preference features')
        for obs in self.observations:
            if 'whole' not in self.reviewedRegions and obs.region not in self.reviewedRegions:
                raise ValueError('Observation outside reviewed regions')
        return self

class ReviewInput(Strict):
    branchId: str = 'main'
    region: Region
    versionA: str
    versionB: str
    linkIdsA: list[str] = Field(default_factory=list, max_length=20)
    linkIdsB: list[str] = Field(default_factory=list, max_length=20)
    domain: Literal['visual_design', 'design_intent'] = 'visual_design'
    expectedEventSequence: int = Field(ge=0)

class FeedbackInput(Strict):
    eventId: str = Field(min_length=1, max_length=100)
    branchId: str = 'main'
    action: Literal['compare', 'shortlist_add', 'shortlist_remove', 'reject_design', 'lock_property', 'unlock_property', 'undo', 'reset', 'fork_branch']
    domain: Literal['visual_design', 'design_intent', 'project'] = 'project'
    reviewSessionId: str | None = None
    subjectVersionIds: list[str] = Field(default_factory=list, max_length=2)
    outcome: Literal['A', 'B', 'tie', 'neither', 'skip'] | None = None
    region: Region = 'whole'
    targetEventId: str | None = None
    propertyKey: str | None = None
    newBranchTitle: str | None = Field(default=None, max_length=120)
    preserveLocks: bool = True
    expectedEventSequence: int = Field(ge=0)

    @model_validator(mode='after')
    def action_fields(self):
        if self.action == 'compare':
            if not self.reviewSessionId or self.outcome is None:
                raise ValueError('Comparison requires a sealed review and outcome')
        elif self.reviewSessionId is not None or self.outcome is not None:
            raise ValueError('Only comparisons carry reviews/outcomes')
        if self.action == 'undo' and not self.targetEventId:
            raise ValueError('Undo requires a target event')
        if self.action != 'undo' and self.targetEventId is not None:
            raise ValueError('Only undo carries a target event')
        if self.action in ('lock_property', 'unlock_property') and not self.propertyKey:
            raise ValueError('A property action requires a property key')
        if self.action not in ('lock_property', 'unlock_property') and self.propertyKey is not None:
            raise ValueError('Property key is only valid for lock actions')
        if self.action in ('shortlist_add', 'shortlist_remove', 'reject_design', 'lock_property', 'unlock_property') and len(self.subjectVersionIds) != 1:
            raise ValueError('Action requires exactly one design version')
        if self.action in ('reset', 'fork_branch', 'undo') and self.subjectVersionIds:
            raise ValueError('History actions do not accept design subjects')
        if self.action == 'compare' and self.subjectVersionIds:
            raise ValueError('Comparison subjects are derived from sealed evidence')
        return self

class RecipeInput(Strict):
    view: View = 'front'
    projection: Literal['orthographic', 'perspective', 'unknown'] = 'orthographic'
    framing: Literal['full_body', 'upper_body', 'face', 'detail'] = 'full_body'
    poseId: str = Field(default='neutral', min_length=1, max_length=200)
    expressionId: str = Field(default='neutral', min_length=1, max_length=200)
    lightingClass: str = Field(default='neutral', min_length=1, max_length=200)
    backgroundClass: str = Field(default='plain', min_length=1, max_length=200)

class ReferenceInput(Strict):
    assetId: str
    role: Literal['identity', 'component', 'material', 'view_example']
    instruction: str = Field(min_length=1, max_length=1000)

class PlanInput(Strict):
    targetVersionId: str
    purpose: Literal['design_variant', 'additional_view', 'unspecified_part', 'state_study', 'depiction_correction']
    recipe: RecipeInput
    changeDesignProperties: list[str] = Field(default_factory=list, max_length=20)
    references: list[ReferenceInput] = Field(default_factory=list, max_length=10)
    expectedEventSequence: int = Field(ge=0)

    @model_validator(mode='after')
    def changes(self):
        if self.purpose in ('additional_view', 'state_study', 'depiction_correction') and self.changeDesignProperties:
            raise ValueError('Observation-only plans cannot change design properties')
        if self.purpose in ('design_variant', 'unspecified_part') and not self.changeDesignProperties:
            raise ValueError('Design proposals require explicit property targets')
        return self

class ModelBuildInput(Strict):
    targetVersionId: str
    label: str = Field(min_length=1, max_length=200)
    artifactHash: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    testScope: str = Field(min_length=1, max_length=3000)

class CheckpointInput(Strict):
    versionId: str
    stage: Literal['design_selected', 'reference_handoff_ready', 'prototype_reviewed_external']
    acceptedGaps: list[str] = Field(default_factory=list, max_length=100)
    acceptanceChecks: list[str] = Field(min_length=1, max_length=100)
    sourceBuildId: str | None = None
    expectedEventSequence: int = Field(ge=0)

class ExportInput(Strict):
    versionId: str
    kind: Literal['handoff', 'prompt_pack'] = 'handoff'
