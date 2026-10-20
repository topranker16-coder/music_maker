import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="가요 스타일 풀-트랙 곡선 작곡기 🎵", layout="centered"
)

st.title("🎤 가요 댄스/팝 리듬 곡선 작곡기")
st.markdown(
    "왼쪽 악기 영역(피아노, 기타, 베이스, 드럼)에 선을 **길~게** 그려보세요! **진짜"
    " 가요처럼 생동감 넘치는 댄스 비트와 합주가 길게 연주**됩니다."
)

# 1. 멀티 악기 트랙 캔버스 (가로폭을 늘려 길게 그릴 수 있게 확장)
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=5,
    stroke_color="#1E88E5",
    background_color="#F8FAFC",
    height=320,
    width=680,
    drawing_mode="freedraw",
    key="canvas_kpop_band",
)

st.caption(
    "📍 **[0~80]:** 🎹 피아노 (메인 멜로디)  |  **[81~160]:** 🎸 일렉/어쿠스틱"
    " 기타 (찰진 화음)  |  **[161~240]:** 🎸 묵직한 가요 베이스  |  **[241~320]:** 🥁"
    " 리얼 댄스 드럼 비트"
)

st.markdown("---")
st.subheader("🎧 가요 음원 완성하기")

if st.button("🔥 댄스 가요 스타일로 길게 연주 시작!"):
  if (
      canvas_result.json_data is not None
      and len(canvas_result.json_data["objects"]) > 0
  ):
    objects = canvas_result.json_data["objects"]

    sample_rate = 44100
    bpm = 120  # 신나는 가요 댄스 템포 (120 BPM)
    beat_duration = 60.0 / bpm  # 1박자당 0.5초
    note_duration = beat_duration / 2  # 8비트 박자감 (0.25초)
    total_samples_per_note = int(sample_rate * note_duration)

    # 신나는 가요 스케일 (메이저/펜타토닉 믹스)
    scale_piano = [
        523.25,
        587.33,
        659.25,
        783.99,
        880.00,
        1046.50,
        1174.66,
    ]  # C5~D6
    scale_guitar = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]  # C4~C5
    scale_bass = [65.41, 73.42, 82.41, 98.00, 110.00, 130.81]  # C2~C3

    all_instrument_tracks = []

    for obj in objects:
      if "path" in obj:
        path_data = obj["path"]
        if len(path_data) > 0:
          start_y = path_data[0][2] if len(path_data[0]) >= 3 else 150
          y_points = [point[2] for point in path_data if len(point) >= 3]

          # 곡 길이를 길게 가져가기 위해 샘플링 수 확장 (최대 100마디/음표 = 약 25초 연주)
          step = max(1, len(y_points) // 80)
          sampled_y = y_points[::step]

          single_track = []

          # 🎹 1. 피아노 구역 (0~80)
          if start_y <= 80:
            for y in sampled_y:
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(80, 80 - y))
              idx = int((norm_y / 80) * (len(scale_piano) - 1))
              freq = scale_piano[idx]
              # 풍성한 피아노 어택 + 리버브 잔향
              wave = (
                  0.3 * np.sin(2 * np.pi * freq * t)
                  + 0.15 * np.sin(2 * np.pi * freq * 2 * t)
                  + 0.05 * np.sin(2 * np.pi * freq * 3 * t)
              ) * np.exp(-3 * t / note_duration)
              single_track.append(wave)

          # 🎸 2. 기타 구역 (81~160)
          elif start_y <= 160:
            for y in sampled_y:
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(80, 160 - y))
              idx = int((norm_y / 80) * (len(scale_guitar) - 1))
              freq = scale_guitar[idx]
              # 찰진 기타 리듬 커팅 (톱니파 + 삼각파 변형)
              wave = (
                  0.25
                  * np.arcsin(np.sin(2 * np.pi * freq * t))
                  * np.exp(-4 * t / note_duration)
              )
              single_track.append(wave)

          # 🎸 3. 묵직한 베이스 구역 (161~240)
          elif start_y <= 240:
            for i, y in enumerate(sampled_y):
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(80, 240 - y))
              idx = int((norm_y / 80) * (len(scale_bass) - 1))
              freq = scale_bass[idx]
              # 둥둥거리는 일렉트릭 슬랩 베이스 톤
              wave = (
                  0.4
                  * (
                      np.sin(2 * np.pi * freq * t)
                      + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
                  )
                  * np.exp(-1.5 * t / note_duration)
              )
              single_track.append(wave)

          # 🥁 4. 리얼 댄스 드럼 구역 (241~320)
          else:
            for i, y in enumerate(sampled_y):
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              beat_type = i % 4

              #
