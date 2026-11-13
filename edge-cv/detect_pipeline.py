#!/usr/bin/env python3
"""
Capture image -> crop (640px X 640px)-> YOLO26n detect -> NATS event 1/second

DEMO MODE (current default): frames come from DEMO_IMAGE_DIR instead of the camera,
and events are logged instead of published (until we can order our parts)

Install:
- pip install ultralytics opencv-python numpy nats-py
*** install picamera2 on pi
"""
import asyncio
import json
import logging
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# import nats  
# ============= config
DEMO_IMAGE_DIR = Path("E:\\Drone Detection Data Set\\seraphim") # test pictures (without camera, for demo)
MODEL_PATH = "yolo26n.pt" # trained weights
IMGSZ = 640  #input size for model (640 square)
CONF_THRESHOLD = 0.25
CAPTURE_INTERVAL_S = 1.0
CROP_MODE = "letterbox"
PAD_COLOR = 114   # grey used for the padding (Ultralytics' default letterbox grey)
DEVICE_ID = socket.gethostname()
NATS_URL = "nats://127.0.0.1:4222"
NATS_SUBJECT = "sensors.camera.detections"
PUBLISH_EMPTY = False #emit event if nothing is detected


# temporary
# DEVICE_ID = socket.gethostname()
# NATS_URL = "nats://127.0.0.1:4222"
# NATS_SUBJECT = "sensors.camera.detections"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("detect")

#this is for a demo without the camera; cycle through test images
class FolderSource:
    """Demo source: cycles through the images in a folder, one per call."""

    EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

    def __init__(self, folder: Path):
        if not folder.is_dir():
            raise SystemExit(f"Demo folder does not exist: {folder}")
        self.files = sorted(p for p in folder.iterdir() if p.suffix.lower() in self.EXTS)
        if not self.files:
            raise SystemExit(f"No images found in {folder}")
        self._i = 0
        log.info("Demo mode: %d images in %s", len(self.files), folder)

    def capture(self):
        """Returns (BGR frame, source label), or (None, label) if the file is unreadable."""
        path = self.files[self._i % len(self.files)]
        self._i += 1
        return cv2.imread(str(path)), path.name

    def close(self):
        pass


# ENABLE: Pi Camera Module 3 (replace FolderSource in main() with PiCameraSource())
# class PiCameraSource:
#     def __init__(self):
#         from picamera2 import Picamera2
#         from libcamera import controls
#
#         self.cam = Picamera2() 
#         # BGR-ordered array (ultralytics expects)
#         cfg = self.cam.create_video_configuration(main={"size": (2304, 1296), "format": "RGB888"})
#         self.cam.configure(cfg)
#         self.cam.start()
#         # module 3 has autofocus - fixing focus at infinity
#         self.cam.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})
#         time.sleep(2)  # let auto-exposure / white balance settle
#
#     def capture(self):
#         return self.cam.capture_array(), "picamera"
#
#     def close(self):
#         self.cam.stop()

#==================== IMAGE TO EVENT PIPELINE ====================

def preprocess(frame):
    """
    Returns (model_input, (offset_x, offset_y, scale)) where the tuple maps model-input
    pixel coordinates back to the original frame: orig = offset + model_px * scale.
    """
    if CROP_MODE == "full":
        return frame, (0.0, 0.0, 1.0)  # ultralytics already reports boxes in original frame pixels

    h, w = frame.shape[:2]
    s = min(h, w)
    x0, y0 = (w - s) // 2, (h - s) // 2
    crop = frame[y0:y0 + s, x0:x0 + s]
    crop = cv2.resize(crop, (IMGSZ, IMGSZ), interpolation=cv2.INTER_AREA)
    return crop, (float(x0), float(y0), s / IMGSZ)


def detect(model, frame):
    """Runs the model; returns (detections, inference_ms). Boxes are in original-frame pixels."""
    fh, fw = frame.shape[:2]
    model_input, (ox, oy, sc) = preprocess(frame)

    t0 = time.perf_counter()
    result = model.predict(model_input, imgsz=IMGSZ, conf=CONF_THRESHOLD, verbose=False)[0]
    infer_ms = (time.perf_counter() - t0) * 1000

    detections = []
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        x1, x2 = ox + x1 * sc, ox + x2 * sc
        y1, y2 = oy + y1 * sc, oy + y2 * sc
        x1, x2 = max(0.0, x1), min(float(fw), x2)
        y1, y2 = max(0.0, y1), min(float(fh), y2)
        cls_id = int(box.cls[0])
        detections.append({
            "class_id": cls_id,
            "class_name": result.names[cls_id],
            "confidence": round(float(box.conf[0]), 4),
            "bbox_xyxy": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            "bbox_norm_xywh": [round((x1 + x2) / 2 / fw, 5), round((y1 + y2) / 2 / fh, 5),
                               round((x2 - x1) / fw, 5), round((y2 - y1) / fh, 5)],
        })
    detections.sort(key=lambda d: d["confidence"], reverse=True)
    return detections, infer_ms


def build_event(frame_id, source_label, frame_shape, captured_at, detections, infer_ms):
    fh, fw = frame_shape[:2]
    return {
        "event": "detection" if detections else "no_detection",
        "version": 1,
        "event_id": uuid.uuid4().hex,
        "device_id": DEVICE_ID,
        "timestamp": captured_at.isoformat(),
        "frame_id": frame_id,
        "source": source_label,
        "frame_size": [fw, fh],
        "inference_ms": round(infer_ms, 1),
        "detections": detections,
    }


async def publish_event(nc, event):
    payload = json.dumps(event).encode()

    # await nc.publish(NATS_SUBJECT, payload)

    log.info("EVENT -> %s  %s", NATS_SUBJECT, payload.decode()) #log for now


async def main():
    log.info("Loading model %s", MODEL_PATH)
    model = YOLO(MODEL_PATH)
    model.predict(np.zeros((IMGSZ, IMGSZ, 3), np.uint8), imgsz=IMGSZ, verbose=False)  # warm-up

    source = FolderSource(DEMO_IMAGE_DIR)
    # source = PiCameraSource()  

    nc = None
    # nc = await nats.connect(NATS_URL) 
    # log.info("Connected to NATS at %s", NATS_URL)

    frame_id = 0
    next_tick = time.monotonic()
    try:
        while True:
            captured_at = datetime.now(timezone.utc)
            frame, label = await asyncio.to_thread(source.capture)

            if frame is None:
                log.warning("Could not read frame from %s, skipping", label)
            else:
                detections, infer_ms = await asyncio.to_thread(detect, model, frame)
                if detections or PUBLISH_EMPTY:
                    event = build_event(frame_id, label, frame.shape, captured_at, detections, infer_ms)
                    await publish_event(nc, event)
                else:
                    log.info("frame %d (%s): nothing detected (%.0f ms)", frame_id, label, infer_ms)
                frame_id += 1

            # fixed rate schedule without drift 
            next_tick += CAPTURE_INTERVAL_S
            delay = next_tick - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            else:
                log.warning("Running %.2fs behind the %.1fs interval", -delay, CAPTURE_INTERVAL_S)
                next_tick = time.monotonic()
    finally:
        source.close()
        if nc is not None:
            await nc.drain()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Stopped")