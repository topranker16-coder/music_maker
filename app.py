import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="곡선형 3D 오디오 작곡기 🎵", layout="centered"
)

st.title("🎸 베이스 & 화음이 함께하는 풀-밴드 곡선 작곡기")
st.markdown(
    "파란 캔버스에 마우스나 손가락으로 선을 그려보세요! **멜로디 + 드럼 +"
    " 묵직한 베이스 + 화음**이 자동으로 우러나옵니다."
)

# 1. 캔버스 영역
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=4,
    stroke_color="#1E88E5",
    background_color="#F0F2F6",
    height=250,
    width=600,
    drawing_mode="freedraw",
    key="canvas",
)

st.markdown("---")
st.subheader("🎧 풀 편곡 오디오 완성하기")

if st.button("🚀 풀-밴드 사운드로 변환하기!"):
  if (
      canvas_result.json_data is not None
      and len(canvas_result.json_data["objects"]) > 0
  ):
    path_data = canvas_result.json_data["objects"][0]["path"]
    y_points = [point[2] for point in path_data if len(point) >= 3]

    if len(y_points) > 0:
      # 메인 스케일 (펜타토닉)
      scale = [
          261.63,
          293.66,
          329.63,
          392.00,
          440.00,  # 4옥타브
          523.25,
          587.33,
          659.25,
          783.99,
          880.00,  # 5옥타브
      ]

      # 베이스 스케일 (낮은 음역대)
      bass_scale = [65.41, 73.42, 82.41, 98.00, 110.00]

      sample_rate = 44100
      note_duration = 0.15
      step = max(1, len(y_points) // 40)
      sampled_y = y_points[::step]

      total_samples_per_note = int(sample_rate * note_duration)

      melody_track = []
      bass_track = []
      drum_track = []

      for i, y in enumerate(sampled_y):
        t = np.linspace(
            0, note_duration, total_samples_per_note, endpoint=False
        )

        # (1) 메인 멜로디
        normalized_y = max(0, min(250, 250 - y))
        scale_index = int((normalized_y / 250) * (len(scale) - 1))
        freq = scale[scale_index]

        harmony_freq = freq * 1.25
        melody_wave = (
            0.3 * np.sin(2 * np.pi * freq * t)
            + 0.15 * np.sin(2 * np.pi * harmony_freq * t)
        ) * np.exp(-3 * t / note_duration)
        melody_track.append(melody_wave)

        # (2) 묵직한 베이스 라인
        bass_freq = bass_scale[i % len(bass_scale)]
        bass_wave = (
            0.4
            * (
                np.sin(2 * np.pi * bass_freq * t)
                + 0.5 * np.sin(2 * np.pi * (bass_freq * 2) * t)
            )
            * np.exp(-2 * t / note_duration)
        )
        bass_track.append(bass_wave)

        # (3) 드럼 비트
        beat_type = i % 4
        drum_note = np.zeros(total_samples_per_note)

        if beat_type == 0 or beat_type == 2:
          kick_freq = np.linspace(130, 35, total_samples_per_note)
          drum_note = 0.6 * np.sin(2 * np.pi * kick_freq * t) * np.exp(-10 * t)
        elif beat_type == 1 or beat_type == 3:
          noise = np.random.uniform(-0.35, 0.35, total_samples_per_note)
          drum_note = noise * np.exp(-14 * t)

        drum_track.append(drum_note)

      # 믹싱 처리
      full_melody = np.concatenate(melody_track)
      full_bass = np.concatenate(bass_track)
      full_drum = np.concatenate(drum_track)

      mixed_audio = full_melody + full_bass + full_drum

      max_val = np.max(np.abs(mixed_audio))
      if max_val > 0:
        mixed_audio = mixed_audio / max_val * 0.85

      audio_data = (mixed_audio * 32767).astype(np.int16)

      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 풀-밴드 완곡 다운로드 (.wav)",
          data=wav_bytes,
          file_name="full_band_drawn_music.wav",
          mime="audio/wav",
      )
      st.success(
          "🎸 멜로디, 화음, 묵직한 베이스, 드럼까지 완성된 풀-밴드 사운드입니다!"
      )
    else:
      st.warning("⚠️ 캔버스에 선을 조금 더 길게 그려보세요!")
  else:
    st.warning("⚠️ 먼저 파란 캔버스에 선을 그려주세요!")
