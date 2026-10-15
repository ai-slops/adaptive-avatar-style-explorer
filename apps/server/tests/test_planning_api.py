import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import create_app
from app.planning import Planning
from app.exports import Exports
from app.storage.assets import Assets
from app.contracts import *
from app.common import DomainError
from test_domain import design, sequence, evidence


def test_observation_prompts_preserve_spec_and_export_honestly(service, project, tmp_path):
    version = design(service, project)
    link = evidence(service, project, version['version_id'], tmp_path / 'images')
    planning = Planning(service)
    data = PlanInput(targetVersionId=version['version_id'], purpose='additional_view', recipe=RecipeInput(view='character_left_profile'), expectedEventSequence=sequence(service, project))
    plan = planning.compile('alice', project, data)
    assert plan['canonicalSpecHash'] == version['canonical_hash']
    assert plan['changeDesignProperties'] == []
    assert plan['imageStatus'] == 'not_generated'
    assert 'NO REDESIGN' in plan['promptText'] and 'silver' in plan['promptText']
    assert len(service.designs('alice', project)[0]['versions']) == 1
    with pytest.raises(ValidationError):
        PlanInput(**{**data.model_dump(), 'changeDesignProperties': ['hair.color']})
    export = Exports(service, Assets(service, tmp_path / 'images'), planning).build('alice', project, version['version_id'])
    with zipfile.ZipFile(io.BytesIO(export)) as archive:
        names = archive.namelist()
        assert 'avatar-design-handoff/character-spec.json' in names
        assert not any('/references/' in name for name in names) # no redistribution consent
        assert 'Technical checks' in archive.read('avatar-design-handoff/modeling-acceptance-checklist.md').decode()
        manifest = json.loads(archive.read('avatar-design-handoff/reference-manifest.json'))
        assert manifest[0]['linkId'] == link and not manifest[0]['exportPermission']
    with pytest.raises(DomainError):
        planning.compile('bob', project, data)


def test_checkpoint_requires_user_acceptance_and_build_evidence(service, project):
    version = design(service, project)
    planning = Planning(service)
    data = dict(versionId=version['version_id'], stage='reference_handoff_ready', acceptanceChecks=['Inspect silhouette'], expectedEventSequence=sequence(service, project))
    with pytest.raises(DomainError, match='accept missing'):
        planning.checkpoint('alice', project, CheckpointInput(**data))
    result = planning.checkpoint('alice', project, CheckpointInput(**data, acceptedGaps=['Front/profile/back still missing; concept brief only']))
    assert result['stage'] == 'reference_handoff_ready'
    with pytest.raises(ValidationError):
        CheckpointInput(**{**data, 'stage': 'production_ready'})
    build = planning.model_build('alice', project, ModelBuildInput(targetVersionId=version['version_id'], label='v1', testScope='Neutral screenshots only'))
    assert build['artifactInspected'] is False
    with pytest.raises(DomainError, match='Import and review captures'):
        planning.checkpoint('alice', project, CheckpointInput(**{**data, 'stage': 'prototype_reviewed_external', 'expectedEventSequence': sequence(service, project)}, sourceBuildId=build['buildId']))


def test_api_bootstrap_csrf_origin_and_deletion(tmp_path):
    app = create_app(tmp_path / 'data', origin='http://127.0.0.1:8765', bootstrap_secret='test-secret')
    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        assert client.get('/api/projects').status_code == 401
        assert client.get('/api/projects', headers={'host': 'attacker.test'}).status_code == 403
        assert client.post('/api/session/bootstrap', json={'secret': 'test-secret'}).status_code == 403
        headers = {'origin': 'http://127.0.0.1:8765'}
        assert client.post('/api/session/bootstrap', json={'secret': 'wrong'}, headers=headers).status_code == 401
        signed = client.post('/api/session/bootstrap', json={'secret': 'test-secret'}, headers=headers)
        assert 'HttpOnly' in signed.headers['set-cookie']
        headers['x-csrf-token'] = signed.json()['csrfToken']
        assert client.post('/api/projects', json={'title': 'Avatar'}, headers={'origin': headers['origin']}).status_code == 403
        assert client.post('/api/projects', json={'title': 'Avatar'}, headers={**headers, 'origin': 'https://attacker.test'}).status_code == 403
        project = client.post('/api/projects', json={'title': 'Avatar'}, headers=headers).json()['project_id']
        api = f'/api/projects/{project}'
        created = client.post(api + '/designs', json={'title': 'Silver', 'spec': {'morphology': 'humanoid'}}, headers=headers)
        assert created.status_code == 200
        asset = client.post(api + '/assets', content=__import__('test_domain').image_bytes(), headers=headers).json()['assetId']
        assert client.get(api + '/assets/' + asset).status_code == 200
        for route in ('generate', 'render', 'proxy', 'shell'):
            assert client.post(api + '/' + route, json={}, headers=headers).status_code == 405 # only GET catch-all exists
        assert client.delete(api, headers=headers).status_code == 200
        assert client.get(api + '/designs').status_code == 404
        assert not (tmp_path / 'data' / 'assets' / project).exists()
        assert client.post('/api/auth/sign-out', headers=headers).status_code == 200
        assert client.get('/api/projects').status_code == 401
