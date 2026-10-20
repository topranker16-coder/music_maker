import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="오선지 콩나물 자동 반주 작곡기 🎵", layout="centered"
)

st.title("🎼 오선지 콩나물 음표 작곡기")
st.markdown(
    "오선지 위에 원하는 멜로디 높낮이대로 **점(콩나물 음표)**을 찍거나"
    " **짧은 선**을 그어보세요!\n내가 찍은 **정확한 음표 멜로디**에 맞춰 AI가"
    " 풍성한 반주를 완성합니다."
)

# 1. 오선지 배경 가이드라인이 그려진 캔버스 (높이 250px)
# 오선지 줄 위치 (Y 좌표): 50, 80, 110, 140, 170
canvas_result = st_canvas(
    fill_color="rgba(255, 75, 75, 0.8)",  # 음표 점 색상 (빨간 포인트)
    stroke_width=6,
    stroke_color="#1E88E5",  # 선 색상 (파란색)
    background_color="#FFFFFF",
    height=250,
    width=680,
    drawing_mode="freedraw",
    key="canvas_sheet_music",
)

st.caption(
    "🎼 **오선지 음높이 가이드 (위에서부터 아래로):**\n"
    "• 맨 위 (Y: ~40): 높은 도~레  |  • 1번줄 근처 (Y: 50~70): 시~라  |  • 중간"
    " (Y: 80~120): 솔~파~미\n"
    "• 아래쪽 (Y: 130~160): 레~도  |  • 맨 아래 (Y: 170~): 낮은 시~라"
)

st.markdown("---")
st.subheader("🎧 오선지 멜로디 & 자동 반주 연주하기")

if st.button("🎵 내가 찍은 콩나물 음표로 완곡 연주!"):
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
    note_duration = beat_duration / 2  # 8비트 박자 (0.25초)
    total_samples_per_note = int(sample_rate * note_duration)

    # C 메이저 정음계 (오선지 줄/칸 위치에 대응하는 정확한 Hz)
    # 높은 도(523.25)부터 낮은 도(261.63)까지 정확히 배치
    note_scale = [
        523.25,  # 높은 도 (0~30)
        493.88,  # 시     (31~50)
        440.00,  # 라     (51~70)
        392.00,  # 솔     (71~90)
        349.23,  # 파     (91~110)
        329.63,  # 미     (111~130)
        293.66,  # 레     (131~150)
        261.63,  # 도     (151~170)
        220.00,  # 낮은 라 (171~)
    ]

    bass_scale = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00]

    # 그려진 점/선들의 X좌표(시간순)에 따라 정렬하여 멜로디 구성
    collected_notes = []
    for obj in objects:
      if "path" in obj and len(obj["path"]) > 0:
        for pt in obj["path"]:
          if len(pt) >= 3:
            collected_notes.append((pt[1], pt[2]))  # (X좌표, Y좌표)

    if len(collected_notes) > 0:
      # X축(시간) 순서대로 음표 정렬
      collected_notes.sort(key=lambda item: item[0])

      # 박자 간격에 맞춰 음표 샘플링 (최대 50개 콩나물)
      step = max(1, len(collected_notes) // 50)
      sampled_notes = collected_notes[::step]

      melody_track = []
      harmony_track = []
      bass_track = []
      drum_track = []

      for i, (x_pos, y_pos) in enumerate(sampled_notes):
        t = np.linspace(
            0, note_duration, total_samples_per_note, endpoint=False
        )

        # Y좌표를 정확한 오선지 음계 index로 변환
        norm_y = max(0, min(200, y_pos))
        scale_idx = int((norm_y / 200) * (len(note_scale) - 1))
        exact_freq = note_scale[scale_idx]

        # 1. 메인 피아노 멜로디 (정확한 음 표현)
        melody_wave = (
            0.4 * np.sin(2 * np.pi * exact_freq * t)
            + 0.15 * np.sin(2 * np.pi * exact_freq * 2 * t)
        ) * np.exp(-3 * t / note_duration)
        melody_track.append(melody_wave)

        # 2. 3도 화음 반주
        harm_freq = exact_freq * 1.25
        harmony_wave = (
            0.18
            * np.arcsin(np.sin(2 * np.pi * harm_freq * t))
            * np.exp(-3.5 * t / note_duration)
        )
        harmony_track.append(harmony_wave)

        # 3. 묵직한 베이스 반주
        bass_freq = bass_scale[scale_idx % len(bass_scale)]
        bass_wave = (
            0.35
            * (
                np.sin(2 * np.pi * bass_freq * t)
                + 0.2 * np.sin(2 * np.pi * bass_freq * 2 * t)
            )
            * np.exp(-1.8 * t / note_duration)
        )
        bass_track.append(bass_wave)

        # 4. 신나는 댄스 드럼 비트
        beat_type = i % 4
        if beat_type == 0:
          kick = np.sin(
              2 * np.pi * np.linspace(150, 40, total_samples_per_note) * t
          ) * np.exp(-8 * t)
          drum_wave = 0.6 * kick
        elif beat_type == 1 or beat_type == 3:
          hihat = (
              np.random.uniform(-0.25, 0.25, total_samples_per_note)
              * np.exp(-20 * t)
          )
          drum_wave = hihat
        else:
          snare_t = np.sin(2 * np.pi * 180 * t) * np.exp(-12 * t)
          snare_n = (
              np.random.uniform(-0.3, 0.3, total_samples_per_note)
              * np.exp(-10 * t)
          )
          drum_wave = 0.4 * snare_t + 0.4 * snare_n

        drum_track.append(drum_wave)

      # 믹싱 처리
      full_melody = np.concatenate(melody_track)
      full_harmony = np.concatenate(harmony_track)
      full_bass = np.concatenate(bass_track)
      full_drum = np.concatenate(drum_track)

      mixed_audio = full_melody + full_harmony + full_bass + full_drum

      max_val = np.max(np.abs(mixed_audio))
      if max_val > 0:
        mixed_audio = mixed_audio / max_val * 0.9

      audio_data = (mixed_audio * 32767).astype(np.int16)

      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 오선지 악보 음원 다운로드 (.wav)",
          data=wav_bytes,
          file_name="sheet_music_auto_track.wav",
          mime="audio/wav",
      )
      st.success(
          "🎼 오선지에 찍은 음표대로 정확하게 멜로디가 연주되며 풍성한 반주가"
          " 완성되었습니다!"
      )
    else:
      st.warning(
          "⚠️ 음표가 인식되지 않았습니다. 캔버스 위에 점이나 선을 찍어주세요!"
      )
  else:
    st.warning("⚠️ 먼저 오선지 위 원하는 음높이 위치에 음표 점을 찍어보세요!")
