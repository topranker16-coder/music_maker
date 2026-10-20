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
    ]
    scale_guitar = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]
    scale_bass = [65.41, 73.42, 82.41, 87.31, 98.00, 110.00]

    track_sounds = []

    for obj in objects:
      if "path" in obj:
        path_data = obj["path"]
        if len(path_data) > 0:
          start_y = path_data[0][2] if len(path_data[0]) >= 3 else 150
          y_points = [point[2] for point in path_data if len(point) >= 3]

          step = max(1, len(y_points) // 30)
          sampled_y = y_points[::step]

          single_line_wave = []

          # 피아노 영역
          if start_y <= 100:
            for y in sampled_y:
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(100, 100 - y))
              idx = int((norm_y / 100) * (len(scale_piano) - 1))
              freq = scale_piano[idx]
              wave = (
                  0.3 * np.sin(2 * np.pi * freq * t)
                  + 0.1 * np.sin(2 * np.pi * freq * 2 * t)
              ) * np.exp(-4 * t / note_duration)
              single_line_wave.append(wave)

          # 기타 영역
          elif start_y <= 200:
            for y in sampled_y:
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(100, 200 - y))
              idx = int((norm_y / 100) * (len(scale_guitar) - 1))
              freq = scale_guitar[idx]
              wave = (
                  0.25
                  * np.arcsin(np.sin(2 * np.pi * freq * t))
                  * np.exp(-2.5 * t / note_duration)
              )
              single_line_wave.append(wave)

          # 드럼 & 베이스 영역
          else:
            for i, y in enumerate(sampled_y):
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              beat_type = i % 4
              if beat_type == 0 or beat_type == 2:
                kick_f = np.linspace(140, 35, total_samples_per_note)
                drum = np.sin(2 * np.pi * kick_f * t) * np.exp(-8 * t)
              else:
                drum = (
                    np.random.uniform(-0.4, 0.4, total_samples_per_note)
                    * np.exp(-12 * t)
                )

              norm_y = max(0, min(100, 300 - y))
              idx = int((norm_y / 100) * (len(scale_bass) - 1))
              bass_freq = scale_bass[idx]
              bass = 0.3 * np.sin(2 * np.pi * bass_freq * t) * np.exp(-2 * t)

              single_line_wave.append(0.5 * drum + bass)

          if len(single_line_wave) > 0:
            track_sounds.append(np.concatenate(single_line_wave))

    if len(track_sounds) > 0:
      max_len = max(len(t) for t in track_sounds)
      padded_tracks = [
          np.pad(t, (0, max_len - len(t)), "constant") for t in track_sounds
      ]
      final_mix = np.sum(padded_tracks, axis=0)

      max_val = np.max(np.abs(final_mix))
      if max_val > 0:
        final_mix = final_mix / max_val * 0.85

      audio_data = (final_mix * 32767).astype(np.int16)

      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 악기별 합주 곡 다운로드 (.wav)",
          data=wav_bytes,
          file_name="instrument_band_drawn_music.wav",
          mime="audio/wav",
      )
      st.success(
          "🎉 대단합니다! 그려주신 악기 트랙들이 하나로 모여 완벽한 밴드 연주가"
          " 완성되었습니다!"
      )
    else:
      st.warning("⚠️ 캔버스에 선을 그려주세요!")
  else:
    st.warning("⚠️ 먼저 캔버스의 피아노, 기타, 드럼 구역에 선을 그려보세요!")
