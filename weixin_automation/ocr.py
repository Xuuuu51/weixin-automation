from __future__ import annotations

from pathlib import Path


def normalize_recognized_lines(lines: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for line in lines:
        clean = " ".join(str(line).strip().split())
        if not clean or clean in seen:
            continue
        normalized.append(clean)
        seen.add(clean)
    return normalized


def recognize_text_in_image(image_path: Path, languages: list[str] | None = None) -> list[str]:
    try:
        from Foundation import NSURL  # type: ignore
        from Vision import (  # type: ignore
            VNImageRequestHandler,
            VNRecognizeTextRequest,
            VNRequestTextRecognitionLevelAccurate,
        )
    except ImportError as exc:
        raise RuntimeError(
            "PyObjC Vision is required. Run: uv sync"
        ) from exc

    recognized_lines: list[str] = []

    def handle_request(request, error):
        if error is not None:
            raise RuntimeError(f"Vision OCR failed: {error}")
        for observation in request.results() or []:
            candidates = observation.topCandidates_(1)
            if candidates:
                recognized_lines.append(str(candidates[0].string()))

    request = VNRecognizeTextRequest.alloc().initWithCompletionHandler_(handle_request)
    request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    if languages:
        request.setRecognitionLanguages_(languages)

    url = NSURL.fileURLWithPath_(str(image_path))
    handler = VNImageRequestHandler.alloc().initWithURL_options_(url, {})
    ok, error = handler.performRequests_error_([request], None)
    if not ok:
        raise RuntimeError(f"Vision OCR failed: {error}")

    return normalize_recognized_lines(recognized_lines)
