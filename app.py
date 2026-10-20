import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="멀티 라인 하모니 작곡기 🎵", layout="centered"
)

st.title("🎼 멀티 라인 동시 연주 & 풀-밴드 작곡기")
st.markdown(
    "파란 캔버스에 **여러 개의 선(줄)**을 슥슥 그려보세요! 그린 선들이"
    " **각각 다른 악기와 화음**이 되어 동시에 합주됩니다."
)

# 1. 캔버스 영역 (여러 개 그리기가 자연스러운 캔버스)
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
st.subheader("🎧 여러 줄 합주 오디오 생성하기")

if st.button("✨ 모든 선을 모아서 오케스트라 연주 시작!"):
  if (
      canvas_result.json_data is not None
      and len(canvas_result.json_data["objects"]) > 0
  ):
    objects = canvas_result.json_data["objects"]

    sample_rate = 44100
    note_duration = 0.2
    total_samples_per_note = int(sample_rate * note_duration)

    # 악기별 스케일 설정
    scale = [
        261.63,
        293.66,
        329.63,
        392.00,
        440.00,
        523.25,
        587.33,
        659.25,
        783.99,
        880.00,
    ]
    bass_scale = [65.41, 73.42, 82.41, 98.00, 110.00]

    all_tracks_audio = []

    # 2. 사용자가 그린 '모든 선(Objects)'을 하나씩 순회하며 소리로 변환
    for obj_idx, obj in enumerate(objects):
      if "path" in obj:
        path_data = obj["path"]
        y_points = [point[2] for point in path_data if len(point) >= 3]

        if len(y_points) > 0:
          step = max(1, len(y_points) // 30)
          sampled_y = y_points[::step]

          track_wave = []
          for i, y in enumerate(sampled_y):
            t = np.linspace(
                0, note_duration, total_samples_per_note, endpoint=False
            )
            normalized_y = max(0, min(250, 250 - y))
            scale_index = int((normalized_y / 250) * (len(scale) - 1))
            freq = scale[scale_index]

            # 그린 선의 순서(첫 번째 줄, 두 번째 줄...)에 따라 악기 음색 다르게 부여
            if obj_idx % 3 == 0:
              # 첫 번째 줄 계열: 메인 리드 신스 (밝은 톤)
              wave = (
                  0.25
                  * np.sin(2 * np.pi * freq * t)
                  * np.exp(-3 * t / note_duration)
              )
            elif obj_idx % 3 == 1:
              # 두 번째 줄 계열: 부드러운 화음 패드
              wave = (
                  0.2
                  * np.sin(2 * np.pi * (freq * 1.5) * t)
                  * np.exp(-2 * t / note_duration)
              )
            else:
              # 세 번째 줄 계열: 묵직한 서브 멜로디
              wave = (
                  0.3
                  * np.sin(2 * np.pi * (freq * 0.5) * t)
                  * np.exp(-2.5 * t / note_duration)
              )

            track_wave.append(wave)

          if len(track_wave) > 0:
            all_tracks_audio.append(np.concatenate(track_wave))

    # 3. 드럼 & 베이스 기본 리듬 트랙 추가 (흥을 돋우는 배경)
    drum_bass_track = []
    for i in range(30):
      t = np.linspace(0, note_duration, total_samples_per_note, endpoint=False)
      # 쿵-딱 드럼
      beat_type = i % 4
      if beat_type == 0 or beat_type == 2:
        kick_freq = np.linspace(130, 35, total_samples_per_note)
        drum_note = 0.4 * np.sin(2 * np.pi * kick_freq * t) * np.exp(-10 * t)
      else:
        drum_note = (
            np.random.uniform(-0.2, 0.2, total_samples_per_note)
            * np.exp(-14 * t)
        )

      # 베이스
      b_freq = bass_scale[i % len(bass_scale)]
      bass_note = (
          0.3 * np.sin(2 * np.pi * b_freq * t) * np.exp(-2 * t / note_duration)
      )

      drum_bass_track.append(drum_note + drum_note)  # 간단 합성

    if len(all_tracks_audio) > 0:
      # 모든 선의 오디오와 기본 리듬 합치기
      max_len = max(len(t) for t in all_tracks_audio)
      # 길이를 동일하게 맞춤
      padded_tracks = [
          np.pad(t, (0, max_len - len(t)), "constant") for t in all_tracks_audio
      ]
      combined_lines = np.sum(padded_tracks, axis=0)

      # 드럼 베이스도 길이 맞춰서 합산
      db_full = np.tile(
          np.concatenate(drum_bass_track),
          int(np.ceil(max_len / len(np.concatenate(drum_bass_track)))),
      )[:max_len]

      final_mix = combined_lines + db_full

      max_val = np.max(np.abs(final_mix))
      if max_val > 0:
        final_mix = final_mix / max_val * 0.85

      audio_data = (final_mix * 32767).astype(np.int16)

      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 멀티 하모니 완곡 다운로드 (.wav)",
          data=wav_bytes,
          file_name="multi_line_harmony.wav",
          mime="audio/wav",
      )
      st.success(
          "🎉 대단합니다! 여러 줄의 선이 서로 어우러져 멋진 멀티 하모니 곡이"
          " 완성되었습니다!"
      )
    else:
      st.warning("⚠️ 캔버스에 선을 그려주세요!")
  else:
    st.warning("⚠️ 먼저 파란 캔버스에 선을 여러 개 그려보세요!")
