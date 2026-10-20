import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="곡선형 자동 작곡 & 리듬 믹서 🎵", layout="centered"
)

st.title("💃 드럼 비트가 흐르는 곡선 BGM 메이커")
st.markdown(
    "캔버스에 마우스로 선을 자유롭게 그려보세요! **멜로디와 함께 신나는 드럼"
    " 리듬이 자동으로 합쳐집니다.**"
)

# 1. 캔버스 생성
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
st.subheader("🎧 신나는 자동 편곡 오디오 만들기")

# 2. 곡선 + 드럼 비트 믹싱 엔진
if st.button("🔥 드럼 비트 얹어서 신나게 음악 만들기!"):
  if (
      canvas_result.json_data is not None
      and len(canvas_result.json_data["objects"]) > 0
  ):
    path_data = canvas_result.json_data["objects"][0]["path"]
    y_points = [point[2] for point in path_data if len(point) >= 3]

    if len(y_points) > 0:
      # 펜타토닉 음계 (멜로디용)
      scale = [
          130.81,
          146.83,
          164.81,
          196.00,
          220.00,
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

      sample_rate = 44100
      note_duration = 0.15  # 한 음당 0.15초
      step = max(1, len(y_points) // 40)
      sampled_y = y_points[::step]

      total_samples_per_note = int(sample_rate * note_duration)

      melody_track = []
      drum_track = []

      # 3. 멜로디 생성 + 쿵-딱 드럼 비트 자동 생성
      for i, y in enumerate(sampled_y):
        # (1) 멜로디 음 생성
        normalized_y = max(0, min(250, 250 - y))
        scale_index = int((normalized_y / 250) * (len(scale) - 1))
        freq = scale[scale_index]

        t = np.linspace(
            0, note_duration, total_samples_per_note, endpoint=False
        )
        envelope = np.exp(-3 * t / note_duration)
        note = 0.35 * np.sin(2 * np.pi * freq * t) * envelope
        melody_track.append(note)

        # (2) 드럼 비트 생성 (4박자 패턴: 쿵 - 딱 - 쿵 - 딱)
        beat_type = i % 4
        drum_note = np.zeros(total_samples_per_note)

        if beat_type == 0 or beat_type == 2:  # '쿵' (킥 드럼: 낮은 우웅 소리)
          kick_freq = np.linspace(150, 40, total_samples_per_note)
          drum_note = 0.5 * np.sin(2 * np.pi * kick_freq * t) * np.exp(-12 * t)
        elif beat_type == 1 or beat_type == 3:  # '딱' (스네어 드럼: 찰진 노이즈)
          noise = np.random.uniform(-0.3, 0.3, total_samples_per_note)
          drum_note = noise * np.exp(-15 * t)

        drum_track.append(drum_note)

      # 4. 멜로디 트랙과 드럼 트랙을 하나로 합성 (Mixing)
      full_melody = np.concatenate(melody_track)
      full_drum = np.concatenate(drum_track)

      # 두 소리를 합쳐서 풍성한 오디오로 만들기
      mixed_audio = full_melody + full_drum

      # 오디오 볼륨 정규화 및 변환
      max_val = np.max(np.abs(mixed_audio))
      if max_val > 0:
        mixed_audio = mixed_audio / max_val * 0.8

      audio_data = (mixed_audio * 32767).astype(np.int16)

      # WAV 파일 생성
      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      # 플레이어 출력
      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 신나는 BGM 파일 다운로드 (.wav)",
          data=wav_bytes,
          file_name="my_rhythm_bgm.wav",
          mime="audio/wav",
      )
      st.success(
          "🥁 쿵-딱 드럼 비트가 어우러진 신나는 리듬 음악이 완성되었습니다!"
      )
    else:
      st.warning("⚠️ 캔버스에 선을 조금 더 길게 그려보세요!")
  else:
    st.warning("⚠️ 먼저 위 파란 캔버스 영역에 선을 그려주세요!")
