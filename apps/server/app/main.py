"""Same-origin loopback API with launch bootstrap, application sessions and CSRF."""
import hmac
import os
from pathlib import Path
import secrets
import shutil
import time
from urllib.parse import urlsplit
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from pydantic import Field
from .common import DomainError
from .contracts import *
from .storage.database import Database
from .storage.assets import Assets, MAX_BYTES
from .service import Service
from .planning import Planning
from .exports import Exports

class Bootstrap(Strict):
    secret: str = Field(min_length=1, max_length=200)

class NextInput(Strict):
    versionId: str


def create_app(data_root=None, origin='http://127.0.0.1:8765', bootstrap_secret=None):
    root = Path(data_root or '.data')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    service = Service(Database(root / 'workspace.sqlite'))
    assets = Assets(service, root / 'assets')
    planning = Planning(service)
    exports = Exports(service, assets, planning)
    secret = bootstrap_secret or secrets.token_urlsafe(32)
    profile_path = root / 'offline-profile'
    if not profile_path.exists():
        fd = os.open(profile_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as file:
            file.write(secrets.token_hex(16))
    principal = profile_path.read_text().strip()
    service.principal(principal)
    sessions = {}
    app = FastAPI(title='Adaptive Avatar Style Explorer', docs_url=None, redoc_url=None, openapi_url=None)
    app.state.service = service
    app.state.bootstrap_secret = secret
    app.state.principal = principal
    app.state.sessions = sessions

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse({'detail': exc.message}, status_code=exc.status)

    @app.middleware('http')
    async def local_security(request: Request, call_next):
        authority = urlsplit(origin).netloc
        if request.headers.get('host') != authority:
            return JSONResponse({'detail': 'Unrecognized local host'}, status_code=403)
        req_origin = request.headers.get('origin')
        if req_origin and req_origin != origin:
            return JSONResponse({'detail': 'Cross-origin access denied'}, status_code=403)
        if request.method not in ('GET', 'HEAD') and req_origin != origin:
            return JSONResponse({'detail': 'Same-origin mutation required'}, status_code=403)
        if request.url.path.startswith('/api/') and request.url.path != '/api/session/bootstrap':
            session = sessions.get(request.cookies.get('avatar_session'))
            if not session or session['expires'] < time.time():
                return JSONResponse({'detail': 'Open the local launch link to sign in'}, status_code=401)
            if request.method not in ('GET', 'HEAD') and not hmac.compare_digest(request.headers.get('x-csrf-token', ''), session['csrf']):
                return JSONResponse({'detail': 'Invalid CSRF token'}, status_code=403)
            request.state.principal = session['principal']
            request.state.session = session
        response = await call_next(request)
        response.headers.update({'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store',
                                 'Content-Security-Policy': "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response

    @app.post('/api/session/bootstrap')
    def bootstrap(data: Bootstrap):
        if not hmac.compare_digest(data.secret, secret):
            raise DomainError('Invalid launch secret', 401)
        session_id, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        sessions[session_id] = {'principal': principal, 'csrf': csrf, 'expires': time.time() + 12 * 3600}
        response = JSONResponse({'csrfToken': csrf, 'profile': 'Local offline profile'})
        response.set_cookie('avatar_session', session_id, httponly=True, samesite='strict', path='/', max_age=12 * 3600)
        return response

    @app.get('/api/session')
    def session(request: Request):
        return {'csrfToken': request.state.session['csrf'], 'profile': 'Local offline profile', 'mode': 'community_prompt_only', 'allowImageGeneration': False}

    @app.post('/api/auth/sign-out')
    def sign_out(request: Request):
        sessions.pop(request.cookies.get('avatar_session'), None)
        response = JSONResponse({'localSignedOut': True, 'remoteRevocation': 'not_connected'})
        response.delete_cookie('avatar_session')
        return response

    @app.get('/api/projects')
    def projects(request: Request):
        return service.projects(request.state.principal)

    @app.post('/api/projects')
    def create_project(request: Request, data: ProjectInput):
        return service.create_project(request.state.principal, data.title)

    @app.get('/api/projects/{p}/designs')
    def designs(p: str, request: Request):
        return service.designs(request.state.principal, p)

    @app.post('/api/projects/{p}/designs')
    def create_design(p: str, data: DesignInput, request: Request):
        return service.create_design(request.state.principal, p, data)

    @app.post('/api/projects/{p}/designs/{d}/versions')
    def new_version(p: str, d: str, data: VersionInput, request: Request):
        return service.new_version(request.state.principal, p, d, data)

    @app.post('/api/projects/{p}/assets')
    async def import_asset(p: str, request: Request):
        # Bound the stream rather than trusting Content-Length or reading an unbounded upload.
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > MAX_BYTES:
                raise DomainError('Image must be at most 20 MiB', 413)
        return assets.import_image(request.state.principal, p, bytes(content))

    @app.get('/api/projects/{p}/assets/{a}')
    def asset(p: str, a: str, request: Request):
        return FileResponse(assets.display_path(request.state.principal, p, a), media_type='image/png')

    @app.post('/api/projects/{p}/depictions')
    @app.post('/api/projects/{p}/external-results')
    def depiction(p: str, data: DepictionInput, request: Request):
        return service.create_depiction(request.state.principal, p, data)

    @app.post('/api/projects/{p}/depiction-links')
    def link(p: str, data: LinkInput, request: Request):
        return service.create_link(request.state.principal, p, data)

    @app.post('/api/projects/{p}/evidence-reviews')
    def review_evidence(p: str, data: EvidenceReviewInput, request: Request):
        return service.evidence_review(request.state.principal, p, data)

    @app.get('/api/projects/{p}/design-versions/{v}/evidence')
    def evidence(p: str, v: str, request: Request):
        return service.evidence(request.state.principal, p, v)

    @app.post('/api/projects/{p}/review-sessions')
    def review(p: str, data: ReviewInput, request: Request):
        return service.review(request.state.principal, p, data)

    @app.post('/api/projects/{p}/feedback')
    def feedback(p: str, data: FeedbackInput, request: Request):
        return service.feedback(request.state.principal, p, data)

    @app.get('/api/projects/{p}/preferences')
    def preferences(p: str, request: Request, branchId: str = 'main'):
        return service.preferences(request.state.principal, p, branchId)

    @app.post('/api/projects/{p}/next-actions')
    def next_actions(p: str, data: NextInput, request: Request):
        return planning.next_actions(request.state.principal, p, data.versionId)

    @app.get('/api/projects/{p}/prompt-packs')
    def plans(p: str, request: Request):
        return planning.plans(request.state.principal, p)

    @app.post('/api/projects/{p}/prompt-packs')
    def plan(p: str, data: PlanInput, request: Request):
        return planning.compile(request.state.principal, p, data)

    @app.post('/api/projects/{p}/model-builds')
    def model_build(p: str, data: ModelBuildInput, request: Request):
        return planning.model_build(request.state.principal, p, data)

    @app.post('/api/projects/{p}/checkpoints')
    def checkpoint(p: str, data: CheckpointInput, request: Request):
        return planning.checkpoint(request.state.principal, p, data)

    @app.post('/api/projects/{p}/exports')
    def export(p: str, data: ExportInput, request: Request):
        content = exports.build(request.state.principal, p, data.versionId, data.kind)
        return Response(content, media_type='application/zip', headers={'Content-Disposition': 'attachment; filename="avatar-design-handoff.zip"'})

    @app.delete('/api/projects/{p}')
    def delete_project(p: str, request: Request):
        with service.database.connect() as db:
            service.owned(db, request.state.principal, p)
            db.execute('DELETE FROM projects WHERE project_id=?', (p,))
        shutil.rmtree(assets.root / p, ignore_errors=False) if (assets.root / p).exists() else None
        return {'deleted': True, 'retention': 'Project database records and on-disk assets removed. Previously downloaded exports are outside application control.'}

    web = Path(__file__).resolve().parents[2] / 'web' / 'dist'
    @app.get('/{path:path}')
    def web_file(path: str):
        if path.startswith(('api/', 'auth/')):
            raise DomainError('Unknown route', 404)
        candidate = (web / path).resolve()
        if candidate.is_relative_to(web.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        if (web / 'index.html').exists():
            return FileResponse(web / 'index.html')
        return JSONResponse({'detail': 'Frontend not built. Run npm run build in apps/web.'}, status_code=503)

    return app
