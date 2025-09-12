from typing import Dict, Any
from javu_agi.vision import extract_text_from_image, extract_text_from_video
from javu_agi.audio_transcriber import transcribe_audio


class MultiModalPerception:
    """
    Unify ingestion from text/image/video/audio into normalized dict.
    """

    def process(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        # text passthrough
        for k, v in observation.items():
            if isinstance(v, (str, int, float, bool)):
                out[k] = v

        # files if present
        img = observation.get("image_path")
        if img:
            out["image_text"] = extract_text_from_image(img)

        vid = observation.get("video_path")
        if vid:
            out["video_text"] = extract_text_from_video(vid)

        aud = observation.get("audio_path")
        if aud:
            out["audio_text"] = transcribe_audio(aud)

        return out
