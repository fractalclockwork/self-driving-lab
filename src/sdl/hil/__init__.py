"""Stage-0 hardware-in-the-loop attach attestation (not campaign SOPs)."""

from sdl.hil.bringup import (
    CheckResult,
    extract_json_object,
    ls55_identity_detail,
    ls55_identity_ok,
    marlin_reply_ok,
    resolve_ls55_port,
    resolve_marlin_port,
    resolve_video_device,
    run_hil_bringup,
)

__all__ = [
    "CheckResult",
    "extract_json_object",
    "ls55_identity_detail",
    "ls55_identity_ok",
    "marlin_reply_ok",
    "resolve_ls55_port",
    "resolve_marlin_port",
    "resolve_video_device",
    "run_hil_bringup",
]
