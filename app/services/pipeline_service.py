"""
Pipeline Service — Shap-E, Meshy API, Mock + Post-processing
"""

import asyncio
import base64
import logging
import mimetypes
from pathlib import Path
from typing import Callable

import httpx

from app.core.config import settings
from app.core.constants import PipelineStage
from app.models.job_model import JobModel
from app.services.mesh_service import MeshService

logger = logging.getLogger(__name__)
ProgressCallback = Callable[[int, str], None]
MESHY_API_BASE = "https://api.meshy.ai/openapi/v2"
MESHY_IMAGE_API_BASE = "https://api.meshy.ai/openapi/v1"
mesh_service = MeshService()


class PipelineService:
    def __init__(self) -> None:
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, job: JobModel, on_progress: ProgressCallback) -> str:
        if job.metadata.get("job_type") == "image_bust":
            output_path = await self._run_meshy_image(job, on_progress)
        elif job.backend == "shap_e":
            output_path = await self._run_shap_e(job, on_progress)
        elif job.backend == "meshy":
            output_path = await self._run_meshy(job, on_progress)
        elif job.backend == "mock":
            output_path = await self._run_mock(job, on_progress)
        else:
            raise ValueError(f"Unknown backend: {job.backend}")

        # Post-processing
        pp = job.metadata.get("post_processing", {})
        if pp.get("enabled", False):
            on_progress(96, "post_processing")
            loop = asyncio.get_event_loop()
            output_path = await loop.run_in_executor(
                None,
                lambda: mesh_service.process(
                    output_path,
                    clean=pp.get("clean", True),
                    decimate=pp.get("decimate", 1.0),
                    smooth=pp.get("smooth", False),
                    smooth_iterations=pp.get("smooth_iterations", 3),
                    target_size_mm=pp.get("target_size_mm", 100.0),
                )
            )

        return output_path

    async def _run_shap_e(self, job: JobModel, cb: ProgressCallback) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._shap_e_sync, job, cb)

    def _shap_e_sync(self, job: JobModel, cb: ProgressCallback) -> str:
        try:
            import torch
            from shap_e.diffusion.sample import sample_latents
            from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
            from shap_e.models.download import load_model, load_config
            from shap_e.util.notebooks import decode_latent_mesh
        except ImportError as e:
            raise RuntimeError(f"Shap-E is not installed: {e}") from e

        device = torch.device("cpu")
        torch.set_default_dtype(torch.float32)
        job.metadata["device"] = str(device)

        cb(5, PipelineStage.INITIALIZING)
        xm = load_model("transmitter", device=device)
        model = load_model("text300M", device=device)
        diffusion = diffusion_from_config(load_config("diffusion"))
        cb(20, PipelineStage.ENCODING_TEXT)
        cb(60, PipelineStage.GENERATING_LATENTS)

        prompt = job.active_prompt
        latents = sample_latents(
            batch_size=1, model=model, diffusion=diffusion,
            guidance_scale=job.guidance_scale,
            model_kwargs={"texts": [prompt]},
            progress=True, clip_denoised=True, use_fp16=False,
            use_karras=True, karras_steps=job.num_steps,
            sigma_min=1e-3, sigma_max=160, s_churn=0,
        )

        cb(85, PipelineStage.DECODING_MESH)
        t = decode_latent_mesh(xm, latents[0]).tri_mesh()
        cb(95, PipelineStage.EXPORTING_FILE)
        output_path = self._export_mesh_shap_e(t, job)
        cb(100, PipelineStage.DONE)
        return str(output_path.resolve())

    def _export_mesh_shap_e(self, t, job: JobModel) -> Path:
        import numpy as np
        fmt = job.output_format
        output_path = self.output_dir / f"{job.id}.{fmt}"
        if fmt == "obj":
            with open(output_path, "w") as f: t.write_obj(f)
        elif fmt == "ply":
            with open(output_path, "wb") as f: t.write_ply(f)
        elif fmt in ("glb", "stl"):
            import trimesh
            verts = np.array([[v.x, v.y, v.z] for v in t.verts])
            faces = np.array(t.faces)
            mesh = trimesh.Trimesh(vertices=verts, faces=faces)
            mesh.export(str(output_path), file_type=fmt)
        else:
            output_path = self.output_dir / f"{job.id}.obj"
            with open(output_path, "w") as f: t.write_obj(f)
            job.output_format = "obj"
        return output_path

    async def _run_meshy(self, job: JobModel, cb: ProgressCallback) -> str:
        api_key = settings.MESHY_API_KEY
        if not api_key:
            raise RuntimeError("MESHY_API_KEY is not set in .env")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        cb(5, PipelineStage.INITIALIZING)
        prompt = job.active_prompt

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{MESHY_API_BASE}/text-to-3d", headers=headers,
                json={"mode": "preview", "prompt": prompt, "art_style": "realistic",
                      "negative_prompt": "low quality, low resolution, ugly"})
            resp.raise_for_status()
            meshy_id = resp.json()["result"]
            job.metadata["meshy_id"] = meshy_id

        cb(20, PipelineStage.GENERATING_LATENTS)
        for _ in range(120):
            await asyncio.sleep(5)
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{MESHY_API_BASE}/text-to-3d/{meshy_id}", headers=headers)
                resp.raise_for_status()
                data = resp.json()
            status = data.get("status")
            progress = data.get("progress", 0)
            if status == "SUCCEEDED":
                cb(90, PipelineStage.EXPORTING_FILE)
                return await self._download_meshy_file(data, job, headers)
            elif status == "FAILED":
                raise RuntimeError(f"Meshy failed: {data.get('task_error')}")
            else:
                cb(int(20 + progress * 0.65), PipelineStage.GENERATING_LATENTS)
        raise RuntimeError("Meshy job timed out")

    async def _run_meshy_image(self, job: JobModel, cb: ProgressCallback) -> str:
        api_key = settings.MESHY_API_KEY
        if not api_key:
            raise RuntimeError("MESHY_API_KEY is not set in .env")

        image_paths = job.metadata.get("image_paths", [])
        if not image_paths:
            raise RuntimeError("No uploaded images found for this job")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        cb(5, PipelineStage.INITIALIZING)
        data_uris = [self._image_to_data_uri(Path(p)) for p in image_paths]

        cb(15, PipelineStage.ENCODING_TEXT)
        single = len(data_uris) == 1
        create_endpoint = f"{MESHY_IMAGE_API_BASE}/{'image-to-3d' if single else 'multi-image-to-3d'}"
        payload = {"image_url": data_uris[0]} if single else {"image_urls": data_uris}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(create_endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            meshy_id = resp.json()["result"]
            job.metadata["meshy_id"] = meshy_id

        cb(25, PipelineStage.GENERATING_LATENTS)
        status_endpoint = f"{create_endpoint}/{meshy_id}"
        for _ in range(120):
            await asyncio.sleep(5)
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(status_endpoint, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            status = data.get("status")
            progress = data.get("progress", 0)
            if status == "SUCCEEDED":
                cb(90, PipelineStage.EXPORTING_FILE)
                return await self._download_meshy_file(data, job, headers)
            elif status == "FAILED":
                raise RuntimeError(f"Meshy failed: {data.get('task_error')}")
            else:
                cb(int(25 + progress * 0.6), PipelineStage.GENERATING_LATENTS)
        raise RuntimeError("Meshy image job timed out")

    def _image_to_data_uri(self, path: Path) -> str:
        mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"

    async def _download_meshy_file(self, data: dict, job: JobModel, headers: dict) -> str:
        fmt = job.output_format
        model_urls = data.get("model_urls", {})
        url = model_urls.get(fmt)
        if not url:
            for fallback in ["obj", "glb", "fbx", "stl"]:
                url = model_urls.get(fallback)
                if url:
                    job.output_format = fallback
                    fmt = fallback
                    break
        if not url:
            raise RuntimeError("No download URL found")
        output_path = self.output_dir / f"{job.id}.{fmt}"
        async with httpx.AsyncClient(timeout=120, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
        return str(output_path.resolve())

    async def _run_mock(self, job: JobModel, cb: ProgressCallback) -> str:
        for stage in PipelineStage.ORDERED[:-1]:
            await asyncio.sleep(0.4)
            cb(PipelineStage.PROGRESS_MAP[stage], stage)
        fmt = job.output_format
        output_path = self.output_dir / f"{job.id}.{fmt}"
        cube_obj = "# Mock cube\nv -0.5 -0.5  0.5\nv  0.5 -0.5  0.5\nv  0.5  0.5  0.5\nv -0.5  0.5  0.5\nv -0.5 -0.5 -0.5\nv  0.5 -0.5 -0.5\nv  0.5  0.5 -0.5\nv -0.5  0.5 -0.5\nf 1 2 3\nf 1 3 4\nf 2 6 7\nf 2 7 3\nf 6 5 8\nf 6 8 7\nf 5 1 4\nf 5 4 8\nf 4 3 7\nf 4 7 8\nf 5 6 2\nf 5 2 1\n"
        if fmt in ("obj", "fbx"):
            output_path = self.output_dir / f"{job.id}.obj"
            output_path.write_text(cube_obj)
            job.output_format = "obj"
        elif fmt == "stl":
            try:
                import trimesh, numpy as np
                verts = [[-0.5,-0.5,0.5],[0.5,-0.5,0.5],[0.5,0.5,0.5],[-0.5,0.5,0.5],[-0.5,-0.5,-0.5],[0.5,-0.5,-0.5],[0.5,0.5,-0.5],[-0.5,0.5,-0.5]]
                faces = [[0,1,2],[0,2,3],[1,5,6],[1,6,2],[5,4,7],[5,7,6],[4,0,3],[4,3,7],[3,2,6],[3,6,7],[4,5,1],[4,1,0]]
                trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces)).export(str(output_path), file_type="stl")
            except ImportError:
                output_path = self.output_dir / f"{job.id}.obj"
                output_path.write_text(cube_obj)
                job.output_format = "obj"
        elif fmt == "ply":
            output_path.write_bytes(b"ply\nformat ascii 1.0\nelement vertex 8\nproperty float x\nproperty float y\nproperty float z\nelement face 12\nproperty list uchar int vertex_indices\nend_header\n-0.5 -0.5 0.5\n0.5 -0.5 0.5\n0.5 0.5 0.5\n-0.5 0.5 0.5\n-0.5 -0.5 -0.5\n0.5 -0.5 -0.5\n0.5 0.5 -0.5\n-0.5 0.5 -0.5\n3 0 1 2\n3 0 2 3\n3 1 5 6\n3 1 6 2\n3 5 4 7\n3 5 7 6\n3 4 0 3\n3 4 3 7\n3 3 2 6\n3 3 6 7\n3 4 5 1\n3 4 1 0\n")
        elif fmt == "glb":
            try:
                import trimesh, numpy as np
                verts = [[-0.5,-0.5,0.5],[0.5,-0.5,0.5],[0.5,0.5,0.5],[-0.5,0.5,0.5],[-0.5,-0.5,-0.5],[0.5,-0.5,-0.5],[0.5,0.5,-0.5],[-0.5,0.5,-0.5]]
                faces = [[0,1,2],[0,2,3],[1,5,6],[1,6,2],[5,4,7],[5,7,6],[4,0,3],[4,3,7],[3,2,6],[3,6,7],[4,5,1],[4,1,0]]
                trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces)).export(str(output_path), file_type="glb")
            except ImportError:
                output_path = self.output_dir / f"{job.id}.obj"
                output_path.write_text(cube_obj)
                job.output_format = "obj"
        else:
            output_path.write_text(cube_obj)
        cb(100, PipelineStage.DONE)
        return str(output_path.resolve())
