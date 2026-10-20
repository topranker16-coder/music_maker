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
    "왼쪽 악기 영역(피아노, 기타, 베이스, 드럼)에 선을 가볍게 그려보세요! **진짜"
    " 가요처럼 생동감 넘치는 댄스 비트와 합주가 연주**됩니다."
)

# 1. 캔버스 생성
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
    "📍 **[0~80]:** 🎹 피아노 | **[81~160]:** 🎸 기타 | **[161~240]:** 🎸"
    " 베이스 | **[241~320]:** 🥁 드럼 비트"
)

st.markdown("---")
st.subheader("🎧 가요 음원 완성하기")

# 2. 버튼 클릭 시 안전하게 실행되는 오디오 생성 로직
if st.button("🔥 댄스 가요 스타일로 연주 시작!"):
  # 데이터가 안전하게 존재하는지 체크하는 안전장치 추가
  if (
      canvas_result is not None
      and canvas_result.json_data is not None
      and "objects" in canvas_result.json_data
      and len(canvas_result.json_data["objects"]) > 0
  ):
    objects = canvas_result.json_data["objects"]

    sample_rate = 44100
    bpm = 120
    beat_duration = 60.0 / bpm
    note_duration = beat_duration / 2
    total_samples_per_note = int(sample_rate * note_duration)

    scale_piano = [523.25, 587.33, 659.25, 783.99, 880.00, 1046.50]
    scale_guitar = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]
    scale_bass = [65.41, 73.42, 82.41, 98.00, 110.00]

    all_instrument_tracks = []

    for obj in objects:
      if "path" in obj:
        path_data = obj["path"]
        if len(path_data) > 0:
          start_y = path_data[0][2] if len(path_data[0]) >= 3 else 150
          y_points = [point[2] for point in path_data if len(point) >= 3]

          step = max(1, len(y_points) // 50)
          sampled_y = y_points[::step]
          single_track = []

          # 피아노 구역 (0~80)
          if start_y <= 80:
            for y in sampled_y:
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(80, 80 - y))
              idx = int((norm_y / 80) * (len(scale_piano) - 1))
              freq = scale_piano[idx]
              wave = (
                  0.3 * np.sin(2 * np.pi * freq * t)
                  + 0.15 * np.sin(2 * np.pi * freq * 2 * t)
              ) * np.exp(-3 * t / note_duration)
              single_track.append(wave)

          # 기타 구역 (81~160)
          elif start_y <= 160:
            for y in sampled_y:
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(80, 160 - y))
              idx = int((norm_y / 80) * (len(scale_guitar) - 1))
              freq = scale_guitar[idx]
              wave = (
                  0.25
                  * np.arcsin(np.sin(2 * np.pi * freq * t))
                  * np.exp(-4 * t / note_duration)
              )
              single_track.append(wave)

          # 베이스 구역 (161~240)
          elif start_y <= 240:
            for y in sampled_y:
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              norm_y = max(0, min(80, 240 - y))
              idx = int((norm_y / 80) * (len(scale_bass) - 1))
              freq = scale_bass[idx]
              wave = (
                  0.4
                  * (
                      np.sin(2 * np.pi * freq * t)
                      + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
                  )
                  * np.exp(-1.5 * t / note_duration)
              )
              single_track.append(wave)

          # 드럼 구역 (241~320)
          else:
            for i, y in enumerate(sampled_y):
              t = np.linspace(
                  0, note_duration, total_samples_per_note, endpoint=False
              )
              beat_type = i % 4
              if beat_type == 0:
                kick = np.sin(
                    2
                    * np.pi
                    * np.linspace(160, 40, total_samples_per_note)
                    * t
                ) * np.exp(-8 * t)
                drum_sound = 0.7 * kick
              elif beat_type == 1 or beat_type == 3:
                hihat = (
                    np.random.uniform(-0.3, 0.3, total_samples_per_note)
                    * np.exp(-20 * t)
                )
                drum_sound = hihat
              else:
                snare_tone = np.sin(2 * np.pi * 180 * t) * np.exp(-12 * t)
                snare_noise = (
                    np.random.uniform(-0.4, 0.4, total_samples_per_note)
                    * np.exp(-10 * t)
                )
                drum_sound = 0.5 * snare_tone + 0.5 * snare_noise
              single_track.append(drum_sound)

          if len(single_track) > 0:
            all_instrument_tracks.append(np.concatenate(single_track))

    if len(all_instrument_tracks) > 0:
      max_len = max(len(t) for t in all_instrument_tracks)
      padded_tracks = [
          np.pad(t, (0, max_len - len(t)), "constant")
          for t in all_instrument_tracks
      ]
      final_mix = np.sum(padded_tracks, axis=0)

      max_val = np.max(np.abs(final_mix))
      if max_val > 0:
        final_mix = final_mix / max_val * 0.9

      audio_data = (final_mix * 32767).astype(np.int16)

      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 가요 스타일 풀-트랙 음원 다운로드 (.wav)",
          data=wav_bytes,
          file_name="kpop_style_full_track.wav",
          mime="audio/wav",
      )
      st.success("🎉 멋진 가요 댄스 비트 음원이 완성되었습니다!")
    else:
      st.warning(
          "⚠️ 선이 올바르게 인식되지 않았습니다. 캔버스를 지우고 선을 다시"
          " 그려주세요!"
      )
  else:
    # 만약 선이 없거나 데이터가 비어있으면 친절하게 경고를 띄워줌 (먹통 방지)
    st.warning(
        "⚠️ 캔버스에 선이 그려지지 않았거나 데이터가 없습니다. 선을 먼저"
        " 그려주세요!"
    )
