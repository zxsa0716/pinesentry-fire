"""ISOFIT atmospheric correction wrapper (skeleton).

ISOFIT (Thompson et al. 2018 RSE; github.com/isofit/isofit) is JPL's gold
standard for hyperspectral atm-corr. Heavy dependencies (MODTRAN6, GPU).

Recommended deployment: Docker (`docker pull isofit/isofit:latest`).

For 4-month timeline, prefer:
  - EMIT L2A (already corrected, NetCDF SR)
  - Tanager L2A from Planet Open Data (pending; falls back to L1B + ISOFIT)
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ISOFIT_DOCKER_IMAGE = "isofit/isofit:latest"


def isofit_correct_docker(
    radiance_h5: Path,
    output_dir: Path,
    docker_image: str = ISOFIT_DOCKER_IMAGE,
    extra_args: list[str] | None = None,
) -> Path:
    """Run ISOFIT atm-corr inside Docker.

    Args:
        radiance_h5: Tanager Basic Radiance HDF5 path
        output_dir:  where to write Surface Reflectance NetCDF

    Returns:
        Path to surface reflectance file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{radiance_h5.parent.absolute()}:/in",
        "-v", f"{output_dir.absolute()}:/out",
        docker_image,
        "isofit", "apply_oe",
        f"/in/{radiance_h5.name}",
        "/out/",
    ]
    if extra_args:
        cmd += extra_args
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return output_dir / radiance_h5.with_suffix(".nc").name


def fallback_6sv():
    """Lightweight fallback: 6SV vector (https://6s.ltdri.org).

    Less accurate than ISOFIT but no Docker/GPU dependency. Suitable for
    rapid prototyping; switch to ISOFIT for final submission.
    """
    raise NotImplementedError(
        "6SV fallback — install via py6S; see notebook 02 for details."
    )
