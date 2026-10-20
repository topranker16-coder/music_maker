import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="악기 트랙별 곡선 작곡기 🎵", layout="centered"
)

st.title("🎼 트랙별 악기 멀티 라인 작곡기")
st.markdown(
    "왼쪽의 **악기 구역(피아노, 기타, 드럼)**을 확인하고, 원하는 위치에서"
    " 오른쪽으로 선을 그려보세요! **해당 악기만의 고유한 음색으로 오케스트라"
    " 합주**가 펼쳐집니다."
)

# 1. 악기 영역 표시가 포함된 멀티 트랙 캔버스
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=4,
    stroke_color="#1E88E5",
    background_color="#F9FAFB",
    height=300,
    width=650,
    drawing_mode="freedraw",
    key="canvas_multi_track",
)

# 캔버스 밑에 악기 위치 가이드 안내
st.caption(
    "📍 **위쪽 영역 (Y: 0~100):** 🎹 피아노 (고음 멜로디)  |  **중간 영역 (Y:"
    " 101~200):** 🎸 기타 (중음 화음)  |  **아래쪽 영역 (Y: 201~300):** 🥁"
    " 드럼&베이스 (리듬 비트)"
)

st.markdown("---")
st.subheader("🎧 악기별 합주 오디오 생성하기")

if st.button("🚀 선택한 악기들로 합주 연주 시작!"):
  if (
      canvas_result.json_data is not None
      and len(canvas_result.json_data["objects"]) > 0
  ):
    objects = canvas_result.json_data["objects"]

    sample_rate = 44100
    note_duration = 0.18
    total_samples_per_note = int(sample_rate * note_duration)

    # 음계 세팅
    scale_piano = [
        523.25,
        587.33,
        659.25,
        698.46,
        783.99,
        880.00,
        987.77,
        1046.50,
    ]  # 높은 음역대
    scale_guitar = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]  # 중음역대
    scale_bass = [65.41, 73.42, 82.41, 87.31, 98.00, 110.00]  # 낮은 음역대

    track_sounds = []

    # 2. 그려진 각 선의 시작 Y 좌표를 읽어 악기 분류 및 사운드 생성
    for obj in objects:
      if "path" in obj:
        path_data = obj["path"]
        if len(path_data) > 0:
          start_y = path_data[0][2] if len(path_data[0]) >= 3 else 150
          y_points = [point[2] for point in path_data if len(point) >= 3]

          step = max(1, len(y_points) // 30)
          sampled_y = y_points[::step]

          single_line_wave = []

          # (1) 위쪽 영역에서 시작한 선 -> 🎹 피아노 (맑고 청아한 음색)
          if start_y <= 100:
            for y in sampled_y:
              t = np.linspace(
