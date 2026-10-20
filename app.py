import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="진짜 오선지 콩나물 작곡기 🎵", layout="centered")

st.title("🎼 내 손으로 찍는 오선지 콩나물 작곡기")
st.markdown(
    "아래 오선지 판 위에 마우스로 **콩나물 점(음표)**을 찍어보세요!\n찍힌 위치의"
    " 높낮이에 따라 **나만의 고유한 멜로디와 자동 반주**가 만들어집니다."
)

# 1. 파이썬과 데이터가 실시간으로 연동되는 인터랙티브 오선지 캔버스
# (오선지 가이드라인을 배경에 깔아둠)
canvas_result = st_canvas(
    fill_color="rgba(239, 68, 68, 0.9)",  # 빨간색 콩나물 점
    stroke_width=8,
    stroke_color="#ef4444",
    background_color="#ffffff",
    height=260,
    width=680,
    drawing_mode="point",  # 클릭할 때마다 콩나물 점이 콕콕 찍히는 모드
    key="canvas_real_notes",
)

st.caption(
    "🎼 **오선지 음높이 가이드:** 위쪽에 찍을수록 ➔ **높은 고음**, 아래쪽에"
    " 찍을수록 ➔ **낮은 저음**이 연주됩니다!"
)

st.markdown("---")
st.subheader("🎧 내가 찍은 콩나물 음원 생성하기")

if st.button("🌟 이 음표들에 맞춰 나만의 음악 연주하기!"):
  if (
      canvas_result is not None
      and canvas_result.json_data is not None
      and "objects" in canvas_result.json_data
      and len(canvas_result.json_data["objects"]) > 0
  ):
    objects = canvas_result.json_data["objects"]

    sample_rate = 44100
    bpm = 110
    beat_duration = 60.0 / bpm
    note_duration = beat_duration * 1.2
    total_samples_per_note = int(sample_rate * note_duration)

    # 오선지 높낮이(Y: 0 ~ 260)에 대응하는 정음계 세팅 (고음 -> 저음)
    note_scale = [
        659.25,  # E5 (가장 위)
        587.33,  # D5
        523.25,  # C5 (높은 도)
        493.88,  # B4
        440.00,  # A4 (라)
        392.00,  # G4 (솔)
        349.23,  # F4 (파)
        329.63,  # E4 (미)
        293.66,  # D4 (레)
        261.63,  # C4 (도)
        220.00,  # A3 (가장 아래)
    ]

    bass_scale = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00]

    # 찍힌 콩나물들의 위치를 X좌표(왼쪽에서 오른쪽 순서)로 정렬
    user_notes = []
    for obj in objects:
      # point 모드 또는 freedraw 모드 지원
      if "left" in obj and "top" in obj:
        user_notes.append((obj["left"], obj.get("top", 130)))
      elif "path" in obj and len(obj["path"]) > 0:
        for pt in obj["path"]:
          if len(pt) >= 3:
            user_notes.append((pt[1], pt[2]))

    if len(user_notes) > 0:
      # 왼쪽에서 오른쪽으로 연주 순서 정렬
      user_notes.sort(key=lambda item: item[0])

      melody_track = []
      harmony_track = []
      bass_track = []
      ambient_track = []

      # 유저가 찍은 음표들을 순서대로 읽어서 오디오로 변환
      for x_pos, y_pos in user_notes:
        t = np.linspace(
            0, note_duration, total_samples_per_note, endpoint=False
        )

        # Y 좌표를 음계 인덱스로 변환 (캔버스 높이 260 기준)
        norm_y = max(0, min(260, y_pos))
        scale_idx = int((norm_y / 260) * (len(note_scale) - 1))
        freq = note_scale[scale_idx]

        # 1. 메인 피아노 선율 (유저가 찍은 바로 그 음)
        piano = (
            0.45 * np.sin(2 * np.pi * freq * t)
            + 0.2 * np.sin(2 * np.pi * freq * 2 * t)
        ) * np.exp(-2.2 * t / note_duration)
        melody_track.append(piano)

        # 2. 감성 화음 패드
        harm_freq = freq * 1.25
        pad = (
            0.22
            * np.arcsin(np.sin(2 * np.pi * harm_freq * t))
            * np.exp(-1.2 * t / note_duration)
        )
        harmony_track.append(pad)

        # 3. 묵직한 서브 베이스
        bass_freq = bass_scale[scale_idx % len(bass_scale)]
        bass = (
            0.35 * np.sin(2 * np.pi * bass_freq * t)
            * np.exp(-1.5 * t / note_duration)
        )
        bass_track.append(bass)

        # 4. 신비로운 앰비언트 효과음
        ambient = (
            0.15 * np.cos(2 * np.pi * (freq * 0.75) * t)
            * np.exp(-1.0 * t / note_duration)
        )
        ambient_track.append(ambient)

      # 트랙 결합 및 믹싱
      full_melody = np.concatenate(melody_track)
      full_harmony = np.concatenate(harmony_track)
      full_bass = np.concatenate(bass_track)
      full_ambient = np.concatenate(ambient_track)

      mixed_audio = full_melody + full_harmony + full_bass + full_ambient

      max_val = np.max(np.abs(mixed_audio))
      if max_val > 0:
        mixed_audio = mixed_audio / max_val * 0.9

      audio_data = (mixed_audio * 32767).astype(np.int16)

      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 내 음표 악보 음원 다운로드 (.wav)",
          data=wav_bytes,
          file_name="my_custom_note_music.wav",
          mime="audio/wav",
      )
      st.success(
          "✨ 유저님이 오선지에 찍어주신 콩나물 위치 그대로 고유한 멜로디와 반주가"
          " 완성되었습니다!"
      )
    else:
      st.warning("⚠️ 캔버스 위에 콩나물 점을 먼저 콕콕 찍어주세요!")
  else:
    st.warning("⚠️ 먼저 오선지 판 위에 콩나물 점을 찍어주세요!")
