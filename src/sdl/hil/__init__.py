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
from sdl.hil.status import (
    LabStatus,
    collect_lab_status,
    format_status_lines,
    label_camera,
    label_ls55,
    label_marlin,
)

__all__ = [
    "CheckResult",
    "LabStatus",
    "collect_lab_status",
    "extract_json_object",
    "format_status_lines",
    "label_camera",
    "label_ls55",
    "label_marlin",
    "ls55_identity_detail",
    "ls55_identity_ok",
    "marlin_reply_ok",
    "resolve_ls55_port",
    "resolve_marlin_port",
    "resolve_video_device",
    "run_hil_bringup",
]
