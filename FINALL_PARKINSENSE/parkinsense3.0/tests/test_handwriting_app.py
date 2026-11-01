import types

import cv2
import numpy as np

import handwriting_app


def test_get_upload_key_returns_identity_for_uploaded_file():
    uploaded = types.SimpleNamespace(name="page.png", size=1234)
    assert handwriting_app.get_upload_key(uploaded, None) == ("upload", "page.png", 1234)


def test_should_process_new_image_detects_new_upload():
    uploaded = types.SimpleNamespace(name="page.png", size=1234)
    state = {}
    assert handwriting_app.should_process_new_image(uploaded, None, state) is True
    state["last_upload_key"] = ("upload", "page.png", 1234)
    assert handwriting_app.should_process_new_image(uploaded, None, state) is False


def test_to_rgb_handles_grayscale_and_bgr_images():
    gray = np.zeros((4, 4), dtype=np.uint8)
    rgb_from_gray = handwriting_app.to_rgb(gray)
    assert rgb_from_gray.shape == (4, 4, 3)

    bgr = np.zeros((4, 4, 3), dtype=np.uint8)
    rgb_from_bgr = handwriting_app.to_rgb(bgr)
    assert rgb_from_bgr.shape == (4, 4, 3)
    assert rgb_from_bgr.dtype == np.uint8

    bgra = np.zeros((4, 4, 4), dtype=np.uint8)
    rgb_from_bgra = handwriting_app.to_rgb(bgra)
    assert rgb_from_bgra.shape == (4, 4, 3)
    assert rgb_from_bgra.dtype == np.uint8
