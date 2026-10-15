import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { image } from "../ui";
import type { Project, Link } from "../types";
export function CropEditor({
  link,
  project,
  onClose,
  onSaved,
  run,
}: {
  link: Link;
  project: Project;
  onClose: () => void;
  onSaved: () => Promise<void>;
  run: (f: () => Promise<void>) => Promise<void>;
}) {
  const [size, setSize] = useState({ width: 1, height: 1 }),
    [crop, setCrop] = useState({ x: 0, y: 0, width: 1, height: 1 });
  const start = useRef<{ x: number; y: number } | null>(null);
  useEffect(() => {
    void run(async () => {
      const s = await api<{ width: number; height: number }>(
        `/projects/${project.project_id}/assets/${link.depiction.asset_id}/metadata`,
      );
      setSize(s);
      setCrop({ x: 0, y: 0, ...s });
    });
  }, [link.link_id]);
  function coordinates(e: React.PointerEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    return {
      x: Math.max(
        0,
        Math.min(
          size.width - 1,
          Math.round(((e.clientX - rect.left) * size.width) / rect.width),
        ),
      ),
      y: Math.max(
        0,
        Math.min(
          size.height - 1,
          Math.round(((e.clientY - rect.top) * size.height) / rect.height),
        ),
      ),
    };
  }
  return (
    <div className="modal-scrim">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="crop-title"
      >
        <button className="close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <p className="eyebrow">NON-GENERATIVE IMAGE PROCESSING</p>
        <h2 id="crop-title">Inspect a visible region.</h2>
        <p>
          Drag a rectangle or enter source coordinates. Cropping preserves the
          design version and source family. It creates no taste label.
        </p>
        <div className="crop-canvas">
          <img
            src={image(project.project_id, link)}
            alt="Imported source for a user-selected crop"
          />
          <svg
            viewBox={`0 0 ${size.width} ${size.height}`}
            preserveAspectRatio="none"
            aria-label="Drag to select a crop"
            onPointerDown={(e) => {
              start.current = coordinates(e);
              e.currentTarget.setPointerCapture(e.pointerId);
            }}
            onPointerMove={(e) => {
              if (!start.current) return;
              const end = coordinates(e);
              setCrop({
                x: Math.min(start.current.x, end.x),
                y: Math.min(start.current.y, end.y),
                width: Math.max(1, Math.abs(start.current.x - end.x)),
                height: Math.max(1, Math.abs(start.current.y - end.y)),
              });
            }}
            onPointerUp={(e) => {
              start.current = null;
              e.currentTarget.releasePointerCapture(e.pointerId);
            }}
          >
            <rect
              x={crop.x}
              y={crop.y}
              width={crop.width}
              height={crop.height}
            />
          </svg>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              await api(
                `/projects/${project.project_id}/depiction-links/${link.link_id}/crop`,
                { ...crop, expectedEventSequence: project.event_sequence },
              );
              await onSaved();
              onClose();
            });
          }}
        >
          <div className="inline-inputs">
            {(["x", "y", "width", "height"] as const).map((key) => (
              <label key={key}>
                Crop {key}
                <input
                  type="number"
                  min={key === "x" || key === "y" ? 0 : 1}
                  max={
                    key === "x" || key === "width" ? size.width : size.height
                  }
                  value={crop[key]}
                  required
                  onChange={(e) =>
                    setCrop({ ...crop, [key]: Number(e.target.value) })
                  }
                />
              </label>
            ))}
          </div>
          <button className="primary">Save crop for review →</button>
        </form>
      </section>
    </div>
  );
}
