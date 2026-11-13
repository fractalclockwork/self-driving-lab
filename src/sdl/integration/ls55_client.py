"""LS 55 integration: HTTP client + offline fixture double."""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

import httpx

from sdl.models import MeasurementResult

CLIP_SOFT = 900_000.0


@runtime_checkable
class LS55Client(Protocol):
    """Minimal analytical-metrology surface used by SOPs."""

    def connect(
        self,
        *,
        gate_a_pass: bool = True,
        compartment_closed: bool = True,
        port: Optional[str] = None,
        fixture_dir: Optional[str] = None,
    ) -> dict[str, Any]: ...

    def disconnect(self) -> dict[str, Any]: ...

    def state(self) -> dict[str, Any]: ...

    def setup(self, **optics: Any) -> dict[str, Any]: ...

    def single_read(
        self,
        *,
        ex_nm: float,
        em_nm: float,
        integration_s: float = 1.0,
        dark_correct: bool = True,
        dilution_ratio: Optional[float] = None,
    ) -> MeasurementResult: ...

    def scan(
        self,
        *,
        ex_nm: float = 350.0,
        em_lo: float = 400.0,
        em_hi: float = 550.0,
        interval_nm: float = 2.0,
        speed: int = 120,
        ex_slit: float = 5.0,
        em_slit: float = 5.0,
        dilution: Optional[str] = None,
        dilution_ratio: Optional[float] = None,
        role: str = "sample",
        experiment: str = "tonic-dilution",
        guide_nm: float = 447.0,
        blank_csv: Optional[str] = None,
        persist: bool = True,
    ) -> MeasurementResult: ...

    def shutter_off(self) -> dict[str, Any]: ...

    def abort(self) -> dict[str, Any]: ...


def _rel_conc(dilution_ratio: Optional[float]) -> Optional[float]:
    if dilution_ratio is None or dilution_ratio <= 0:
        return None
    return 1.0 / float(dilution_ratio)


def _normalize_scout(payload: dict[str, Any], *, dilution_ratio: Optional[float]) -> MeasurementResult:
    intensity = payload.get("corrected")
    if intensity is None:
        intensity = payload.get("intensity")
    clipped = bool(payload.get("clipped"))
    warnings = list(payload.get("warnings") or [])
    overload = clipped or any("0107" in str(w) for w in warnings)
    if intensity is not None and abs(float(intensity)) >= CLIP_SOFT:
        clipped = True
        overload = True
    return MeasurementResult(
        kind="scout",
        peak_nm=payload.get("em_nm"),
        peak_intensity=float(intensity) if intensity is not None else None,
        snr=None,
        clipped=clipped,
        overload=overload,
        dilution_ratio=dilution_ratio,
        relative_concentration=_rel_conc(dilution_ratio),
        raw=payload,
        ok=bool(payload.get("ok", True)),
        warnings=warnings,
        errors=list(payload.get("errors") or []),
    )


def _normalize_scan(
    payload: dict[str, Any],
    *,
    dilution_ratio: Optional[float],
    guide_nm: float,
    review: Optional[dict[str, Any]] = None,
) -> MeasurementResult:
    sample = payload.get("sample") or {}
    intensities = sample.get("intensity") or []
    wavelengths = sample.get("wavelength_nm") or []
    clipped = bool(payload.get("clipped"))
    overload = clipped or any("0107" in str(w) for w in (payload.get("warnings") or []))

    peak_nm: Optional[float] = None
    peak_intensity: Optional[float] = None
    snr: Optional[float] = None

    if review:
        peak_nm = review.get("peak_nm")
        peak_intensity = review.get("peak_intensity")
        snr = review.get("absolute_snr") or review.get("contrast_snr")
        clipped = clipped or bool(review.get("clipped"))
    elif wavelengths and intensities:
        # Nearest-to-guide fallback when review is unavailable.
        best_i = min(range(len(wavelengths)), key=lambda i: abs(float(wavelengths[i]) - guide_nm))
        peak_nm = float(wavelengths[best_i])
        peak_intensity = float(intensities[best_i])

    artifacts = dict(payload.get("artifacts") or {})
    return MeasurementResult(
        kind="scan",
        peak_nm=peak_nm,
        peak_intensity=peak_intensity,
        snr=snr,
        clipped=clipped,
        overload=overload,
        dilution_ratio=dilution_ratio,
        relative_concentration=_rel_conc(dilution_ratio),
        artifacts=artifacts,
        raw={"scan": payload, "review": review},
        ok=bool(payload.get("passed", True)) and not payload.get("aborted", False),
        warnings=list(payload.get("warnings") or []),
        errors=list(payload.get("errors") or []),
    )


class LS55HttpClient:
    """HTTP adapter for spectrometer-lab FastAPI console (default :8055)."""

    def __init__(self, base_url: str = "http://127.0.0.1:8055", *, timeout_s: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout_s)

    def close(self) -> None:
        self._client.close()

    def connect(
        self,
        *,
        gate_a_pass: bool = True,
        compartment_closed: bool = True,
        port: Optional[str] = None,
        fixture_dir: Optional[str] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "gate_a_pass": gate_a_pass,
            "compartment_closed": compartment_closed,
        }
        if port:
            body["port"] = port
        if fixture_dir:
            body["fixture_dir"] = fixture_dir
        r = self._client.post("/api/connect", json=body)
        r.raise_for_status()
        return r.json()

    def disconnect(self) -> dict[str, Any]:
        r = self._client.post("/api/disconnect")
        r.raise_for_status()
        return r.json()

    def state(self) -> dict[str, Any]:
        r = self._client.get("/api/state")
        r.raise_for_status()
        return r.json()

    def setup(self, **optics: Any) -> dict[str, Any]:
        r = self._client.post("/api/setup", json=optics)
        r.raise_for_status()
        return r.json()

    def single_read(
        self,
        *,
        ex_nm: float,
        em_nm: float,
        integration_s: float = 1.0,
        dark_correct: bool = True,
        dilution_ratio: Optional[float] = None,
    ) -> MeasurementResult:
        r = self._client.post(
            "/api/single-read",
            json={
                "ex_nm": ex_nm,
                "em_nm": em_nm,
                "integration_s": integration_s,
                "dark_correct": dark_correct,
            },
        )
        r.raise_for_status()
        return _normalize_scout(r.json(), dilution_ratio=dilution_ratio)

    def scan(
        self,
        *,
        ex_nm: float = 350.0,
        em_lo: float = 400.0,
        em_hi: float = 550.0,
        interval_nm: float = 2.0,
        speed: int = 120,
        ex_slit: float = 5.0,
        em_slit: float = 5.0,
        dilution: Optional[str] = None,
        dilution_ratio: Optional[float] = None,
        role: str = "sample",
        experiment: str = "tonic-dilution",
        guide_nm: float = 447.0,
        blank_csv: Optional[str] = None,
        persist: bool = True,
    ) -> MeasurementResult:
        dil_str = dilution
        if dil_str is None and dilution_ratio is not None:
            dil_str = f"1:{int(round(dilution_ratio))}"
        body: dict[str, Any] = {
            "mx": 1,
            "ex_nm": ex_nm,
            "em_lo": em_lo,
            "em_hi": em_hi,
            "interval_nm": interval_nm,
            "speed": speed,
            "ex_slit": ex_slit,
            "em_slit": em_slit,
            "include_dark": True,
            "n_accumulate": 1,
            "experiment": experiment,
            "dilution": dil_str,
            "role": role,
            "persist": persist,
        }
        r = self._client.post("/api/scan", json=body)
        r.raise_for_status()
        payload = r.json()

        review: Optional[dict[str, Any]] = None
        artifacts = payload.get("artifacts") or {}
        csv_path = artifacts.get("csv")
        review_body: dict[str, Any] = {
            "guide_nm": guide_nm,
            "half_window_nm": 25.0,
            "noise_lo_nm": 410.0,
            "noise_hi_nm": 420.0,
            "mode": "fluorescence",
        }
        if csv_path:
            review_body["csv_path"] = csv_path
        if blank_csv:
            review_body["blank_csv"] = blank_csv
        sample = payload.get("sample") or {}
        if sample.get("wavelength_nm") and sample.get("intensity"):
            review_body["wavelength_nm"] = sample["wavelength_nm"]
            review_body["sample_on"] = [float(v) for v in sample["intensity"]]
        try:
            rr = self._client.post("/api/review/recompute", json=review_body)
            if rr.status_code < 400:
                review = rr.json()
        except httpx.HTTPError:
            review = None

        return _normalize_scan(
            payload,
            dilution_ratio=dilution_ratio,
            guide_nm=guide_nm,
            review=review,
        )

    def shutter_off(self) -> dict[str, Any]:
        r = self._client.post("/api/shutter/off")
        r.raise_for_status()
        return r.json()

    def abort(self) -> dict[str, Any]:
        r = self._client.post("/api/abort")
        r.raise_for_status()
        return r.json()


class FixtureLS55Client:
    """
    Offline instrument double for CI / dry-run.

    Simulates tonic quinine response: linear at low concentration, IFE roll-off
    and clipping at high concentration (usefulness gate near 1:450).
    """

    def __init__(
        self,
        *,
        linear_scale: float = 2.0e7,
        ife_onset: float = 1.0 / 100.0,
        clip_onset: float = 1.0 / 40.0,
        peak_nm: float = 447.0,
        noise: float = 50.0,
    ) -> None:
        self.linear_scale = linear_scale
        self.ife_onset = ife_onset
        self.clip_onset = clip_onset
        self.peak_nm = peak_nm
        self.noise = noise
        self._connected = False
        self._optics: dict[str, Any] = {
            "ex_nm": 350.0,
            "em_nm": 450.0,
            "ex_slit": 5.0,
            "em_slit": 5.0,
        }
        self.last_dilution_ratio: Optional[float] = None

    def _intensity(self, dilution_ratio: float) -> tuple[float, bool]:
        conc = 1.0 / float(dilution_ratio)
        # Soft saturation above IFE onset; hard clip above clip_onset.
        if conc >= self.clip_onset:
            return CLIP_SOFT, True
        raw = self.linear_scale * conc
        if conc >= self.ife_onset:
            # Roll-off: measured intensity grows slower than linear.
            excess = (conc - self.ife_onset) / max(self.ife_onset, 1e-12)
            raw = self.linear_scale * self.ife_onset * (1.0 + 0.35 * excess)
        return float(raw + self.noise), False

    def connect(
        self,
        *,
        gate_a_pass: bool = True,
        compartment_closed: bool = True,
        port: Optional[str] = None,
        fixture_dir: Optional[str] = None,
    ) -> dict[str, Any]:
        if not gate_a_pass:
            raise ValueError("gate_a_pass required")
        if not compartment_closed:
            raise ValueError("compartment_closed required")
        self._connected = True
        return {
            "ok": True,
            "fixture": True,
            "port": port or fixture_dir or "fixture:offline",
            "state": "idle_safe",
        }

    def disconnect(self) -> dict[str, Any]:
        self._connected = False
        return {"ok": True, "state": "disconnected"}

    def state(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "state": "idle_safe" if self._connected else "disconnected",
            "optics": dict(self._optics),
        }

    def setup(self, **optics: Any) -> dict[str, Any]:
        self._require()
        self._optics.update({k: v for k, v in optics.items() if v is not None})
        return {"ok": True, "optics": dict(self._optics)}

    def _require(self) -> None:
        if not self._connected:
            raise RuntimeError("not connected")

    def single_read(
        self,
        *,
        ex_nm: float,
        em_nm: float,
        integration_s: float = 1.0,
        dark_correct: bool = True,
        dilution_ratio: Optional[float] = None,
    ) -> MeasurementResult:
        self._require()
        ratio = float(dilution_ratio or self.last_dilution_ratio or 80.0)
        self.last_dilution_ratio = ratio
        intensity, clipped = self._intensity(ratio)
        payload = {
            "ok": True,
            "ex_nm": ex_nm,
            "em_nm": em_nm,
            "integration_s": integration_s,
            "intensity": intensity,
            "corrected": intensity if dark_correct else intensity,
            "clipped": clipped,
            "warnings": ["PMT over-range 0107 during $RD"] if clipped else [],
            "errors": [],
        }
        return _normalize_scout(payload, dilution_ratio=ratio)

    def scan(
        self,
        *,
        ex_nm: float = 350.0,
        em_lo: float = 400.0,
        em_hi: float = 550.0,
        interval_nm: float = 2.0,
        speed: int = 120,
        ex_slit: float = 5.0,
        em_slit: float = 5.0,
        dilution: Optional[str] = None,
        dilution_ratio: Optional[float] = None,
        role: str = "sample",
        experiment: str = "tonic-dilution",
        guide_nm: float = 447.0,
        blank_csv: Optional[str] = None,
        persist: bool = True,
    ) -> MeasurementResult:
        self._require()
        ratio = float(dilution_ratio or self.last_dilution_ratio or 80.0)
        self.last_dilution_ratio = ratio
        peak_i, clipped = self._intensity(ratio)
        wavelengths: list[float] = []
        intensities: list[float] = []
        wl = float(em_lo)
        while wl <= em_hi + 1e-9:
            # Rough Gaussian-ish band around peak_nm.
            delta = wl - self.peak_nm
            shape = max(0.05, 1.0 - (delta / 40.0) ** 2)
            intensities.append(peak_i * shape)
            wavelengths.append(wl)
            wl += interval_nm
        payload = {
            "passed": True,
            "aborted": False,
            "clipped": clipped,
            "warnings": ["PMT over-range 0107 on sample scan"] if clipped else [],
            "errors": [],
            "sample": {
                "wavelength_nm": wavelengths,
                "intensity": intensities,
                "max_abs_intensity": int(max(abs(v) for v in intensities)),
            },
            "artifacts": {
                "csv": f"fixture://{experiment}/{dilution or f'1:{int(ratio)}'}.csv",
                "persist": persist,
                "blank_csv": blank_csv,
                "optics": {
                    "ex_nm": ex_nm,
                    "em_lo": em_lo,
                    "em_hi": em_hi,
                    "ex_slit": ex_slit,
                    "em_slit": em_slit,
                    "speed": speed,
                },
            },
        }
        # Synthetic review metrics.
        snr = (peak_i / self.noise) if peak_i and not clipped else 0.0
        review = {
            "peak_nm": self.peak_nm,
            "peak_intensity": peak_i,
            "absolute_snr": snr,
            "clipped": clipped,
        }
        return _normalize_scan(
            payload,
            dilution_ratio=ratio,
            guide_nm=guide_nm,
            review=review,
        )

    def shutter_off(self) -> dict[str, Any]:
        return {"ok": True, "es": 1}

    def abort(self) -> dict[str, Any]:
        return {"ok": True, "aborted": True}
