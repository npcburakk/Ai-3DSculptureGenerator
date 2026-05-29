"""
Mesh Service — post-processing pipeline
- Mesh cleaning
- Decimation
- Smoothing  
- Auto scaling (mm)
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MeshService:

    def process(
        self,
        file_path: str,
        clean: bool = True,
        decimate: float = 1.0,
        smooth: bool = False,
        smooth_iterations: int = 3,
        target_size_mm: float = 100.0,
    ) -> str:
        try:
            import trimesh
            import numpy as np
        except ImportError:
            logger.warning("trimesh not installed, skipping post-processing")
            return file_path

        path = Path(file_path)
        ext = path.suffix.lower()

        if ext in ('.glb', '.gltf', '.fbx'):
            logger.info(f"Skipping post-processing for {ext} format")
            return file_path

        try:
            mesh = trimesh.load(file_path, force='mesh')

            if not isinstance(mesh, trimesh.Trimesh):
                logger.warning("Could not load as single mesh, skipping")
                return file_path

            original_faces = len(mesh.faces)
            logger.info(f"Post-processing: {original_faces} faces")

            # 1. Mesh temizleme
            if clean:
                mesh.remove_degenerate_faces()
                mesh.remove_duplicate_faces()
                mesh.remove_unreferenced_vertices()
                mesh.fill_holes()
                logger.info(f"After clean: {len(mesh.faces)} faces")

            # 2. Decimation
            if decimate < 1.0 and decimate > 0:
                target_faces = max(100, int(len(mesh.faces) * decimate))
                mesh = mesh.simplify_quadric_decimation(target_faces)
                logger.info(f"After decimation ({decimate}): {len(mesh.faces)} faces")

            # 3. Smoothing
            if smooth and smooth_iterations > 0:
                trimesh.smoothing.filter_laplacian(mesh, iterations=smooth_iterations)
                logger.info(f"Applied {smooth_iterations} smoothing iterations")

            # 4. Otomatik ölçekleme
            if target_size_mm > 0:
                bounds = mesh.bounds
                current_size = max(bounds[1] - bounds[0])
                if current_size > 0:
                    scale_factor = target_size_mm / current_size
                    mesh.apply_scale(scale_factor)
                    logger.info(f"Scaled: {current_size:.1f} → {target_size_mm:.1f}mm (factor: {scale_factor:.5f})")

            # Kaydet
            if ext == '.obj':
                mesh.export(file_path, file_type='obj')
            elif ext == '.stl':
                mesh.export(file_path, file_type='stl')
            elif ext == '.ply':
                mesh.export(file_path, file_type='ply')
            else:
                mesh.export(file_path)

            logger.info(f"Post-processing complete: {original_faces} → {len(mesh.faces)} faces")
            return file_path

        except Exception as e:
            logger.error(f"Post-processing failed: {e}", exc_info=True)
            return file_path
