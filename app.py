import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="진짜 오선지 콩나물 작곡기 🎵", layout="centered"
)

st.title("🎼 진짜 오선지 콩나물 음표 작곡기")
st.markdown(
    "아래 오선지 가이드라인을 보면서 원하는 위치에 **콩나물 점(음표)**을 찍어보세요!"
)

# 오선지와 음계 가이드가 함께 그려진 HTML/캔버스 인터페이스
sheet_music_html = """
<div style="background-color: white; padding: 15px; border-radius: 10px; border: 2px solid #ddd; text-align: center;">
    <div style="margin-bottom: 5px; font-weight: bold; color: #555; font-size: 14px;">
        🎵 [오선지 가이드] 위쪽: 고음(도~솔) / 중간: 중음(파~미) / 아래쪽: 저음(레~도)
    </div>
</div>
"""
st.markdown(sheet_music_html, unsafe_allow_html=True)

# 1. 시각적 오선지 선들이 배경에 깔린 드로잉 캔버스
canvas_result = st_canvas(
    fill_color="rgba(255, 75, 75, 0.9)",  # 찍히는 음표 점 색상 (빨간색 콩나물)
    stroke_width=6,
    stroke_color="#1E88E5",
    background_color="#FFFFFF",
    background_image=None,
    height=280,
    width=680,
    drawing_mode="freedraw",
    key="canvas_real_sheet",
)

# 캔버스 밑에 오선지 줄 위치 가이드 표시
st.markdown(
    """
    <div style="background: #f0f2f6; padding: 10px; border-radius: 8px; font-size: 13px; color: #333;">
        <b>🎼 오선지 줄 위치 참고:</b><br>
        • <b>1번선 (맨 위 줄):</b> 높은 미 / 파<br>
        • <b>2번선:</b> 레 / 도<br>
        • <b>3번선 (가운데 줄):</b> 시 / 라<br>
        • <b>4번선:</b> 솔 / 파<br>
        • <b>5번선 (맨 아래 줄):</b> 미 / 레 / 도
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")
st.subheader("🎧 오선지 콩나물 연주 및 자동 반주 생성")

if st.button("🎵 오선지 음표대로 완곡 연주 시작!"):
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

    # C 메이저 스케일 (정확한 Hz 매핑)
    note_scale = [
        659.25,  # 높은 미 (E5)
        587.33,  # 높은 레 (D5)
        523.25,  # 높은 도 (C5)
        493.88,  # 시 (B4)
        440.00,  # 라 (A4)
        392.00,  # 솔 (G4)
        349.23,  # 파 (F4)
        329.63,  # 미 (E4)
        293.66,  # 레 (D4)
        261.63,  # 도 (C4)
        220.00,  # 낮은 라 (A3)
    ]

    bass_scale = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00]

    collected_notes = []
    for obj in objects:
      if "path" in obj and len(obj["path"]) > 0:
        for pt in obj["path"]:
          if len(pt) >= 3:
            collected_notes.append((pt[1], pt[2]))  # (X좌표, Y좌표)

    if len(collected_notes) > 0:
      collected_notes.sort(key=lambda item: item[0])
      step = max(1, len(collected_notes) // 40)
      sampled_notes = collected_notes[::step]

      melody_track = []
      harmony_track = []
      bass_track = []
      drum_track = []

      for i, (x_pos, y_pos) in enumerate(sampled_notes):
        t = np.linspace(
            0, note_duration, total_samples_per_note, endpoint=False
        )

        norm_y = max(0, min(280, y_pos))
        scale_idx = int((norm_y / 280) * (len(note_scale) - 1))
        exact_freq = note_scale[scale_idx]

        # 1. 피아노 메인 멜로디
        melody_wave = (
            0.4 * np.sin(2 * np.pi * exact_freq * t)
            + 0.15 * np.sin(2 * np.pi * exact_freq * 2 * t)
        ) * np.exp(-3 * t / note_duration)
        melody_track.append(melody_wave)

        # 2. 화음 반주
        harm_freq = exact_freq * 1.25
        harmony_wave = (
            0.18
            * np.arcsin(np.sin(2 * np.pi * harm_freq * t))
            * np.exp(-3.5 * t / note_duration)
        )
        harmony_track.append(harmony_wave)

        # 3. 베이스
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

        # 4. 댄스 드럼
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
          "🎼 오선지에 찍힌 콩나물 음표 위치에 맞춰 완벽한 하모니가 연주되었습니다!"
      )
    else:
      st.warning("⚠️ 음표가 없습니다. 오선지 위에 콩나물 점을 찍어주세요!")
  else:
    st.warning("⚠️ 먼저 오선지 위에 음표를 찍어보세요!")
