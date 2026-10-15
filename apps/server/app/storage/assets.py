"""Validated immutable originals and metadata-free display derivatives."""

import hashlib
import io
import os
import warnings
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from ..common import DomainError, canonical, require, uid

MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class Assets:
    def __init__(self, service, root):
        self.service = service
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def import_image(
        self, principal, project, content, *, parent_asset_id=None, crop=None
    ):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            if parent_asset_id:
                self.service.get(db, "assets", project, "asset_id", parent_asset_id)
        require(0 < len(content) <= MAX_BYTES, "Image must be at most 20 MiB", 413)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as image:
                    require(
                        image.format in ("PNG", "JPEG", "WEBP"),
                        "Only PNG, JPEG and WebP are accepted",
                    )
                    require(
                        image.width * image.height <= MAX_PIXELS,
                        "Decoded image is too large",
                        413,
                    )
                    require(
                        not getattr(image, "is_animated", False),
                        "Import a single still image",
                    )
                    image.load()
                    image = ImageOps.exif_transpose(image)
                    width, height = image.size
                    safe = image.convert(
                        "RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB"
                    )
                    pixel_hash = hashlib.sha256(
                        safe.mode.encode() + str(safe.size).encode() + safe.tobytes()
                    ).hexdigest()
                    safe.thumbnail((2048, 2048))
                    # Do not carry original info/EXIF/text chunks to the derivative.
                    safe.info.clear()
                    output = io.BytesIO()
                    safe.save(output, format="PNG")
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise DomainError("Invalid or unsafe raster image") from exc
        sha = hashlib.sha256(content).hexdigest()
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            existing = db.execute(
                "SELECT asset_id FROM assets WHERE project_id=? AND digest=? AND parent_asset_id IS ? AND json_extract(provenance_json, '$.crop') IS ?",
                (project, sha, parent_asset_id, canonical(crop) if crop else None),
            ).fetchone()
            if existing:
                return {"assetId": existing[0], "deduplicated": True}
            asset = uid()
            directory = self.root / project
            directory.mkdir(mode=0o700, exist_ok=True)
            # UUID project/asset keys are server-generated; request filenames never become paths.
            key = f"{project}/{asset}"
            original, preview = self.root / key, self.root / f"{key}.png"
            try:
                for path, data in ((original, content), (preview, output.getvalue())):
                    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(fd, "wb") as file:
                        file.write(data)
                db.execute(
                    "INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        project,
                        asset,
                        sha,
                        key,
                        "image/png"
                        if content.startswith(b"\x89PNG")
                        else "image/jpeg"
                        if content.startswith(b"\xff\xd8")
                        else "image/webp",
                        width,
                        height,
                        parent_asset_id,
                        canonical(
                            {
                                "kind": "user_selected_crop"
                                if parent_asset_id
                                else "immutable_import",
                                "crop": crop,
                                "pixelHash": pixel_hash,
                                "displayDerivativeHash": hashlib.sha256(
                                    output.getvalue()
                                ).hexdigest(),
                                "displayDerivative": "metadata_stripped_png",
                            }
                        ),
                    ),
                )
            except BaseException:
                original.unlink(missing_ok=True)
                preview.unlink(missing_ok=True)
                raise
            return {
                "assetId": asset,
                "width": width,
                "height": height,
                "deduplicated": False,
            }

    def display_path(self, principal, project, asset):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            row = self.service.get(db, "assets", project, "asset_id", asset)
            return self.root / f"{row['storage_key']}.png"

    def crop(self, principal, project, asset_id, coordinates):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            parent = self.service.get(db, "assets", project, "asset_id", asset_id)
            x, y, width, height = (
                coordinates[k] for k in ("x", "y", "width", "height")
            )
            require(
                x + width <= parent["width"] and y + height <= parent["height"],
                "Crop exceeds the source image bounds",
            )
            path = self.root / parent["storage_key"]
        with Image.open(path) as raw:
            oriented = ImageOps.exif_transpose(raw)
            cropped = oriented.crop((x, y, x + width, y + height))
            cropped.info.clear()
            output = io.BytesIO()
            cropped.save(output, format="PNG")
        return self.import_image(
            principal,
            project,
            output.getvalue(),
            parent_asset_id=asset_id,
            crop=coordinates,
        )
