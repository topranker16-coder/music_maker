import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="자동 반주 밴드 작곡기 🎸", layout="centered")

st.title("🎸 드럼 & 피아노 자동 반주 밴드 메이커")
st.markdown(
    "오선지 위에 콩나물 점을 찍어보세요! 선택한 **반주 스타일**에 맞춰"
    " 드럼(킥, 스네어, 하이햇)과 피아노 반주가 자동으로 멋지게 어우러집니다."
)

# 반주 스타일 선택 옵션 추가
band_style = st.selectbox(
    "🎵 원하시는 자동 반주 스타일을 선택하세요:",
    ["신나는 팝/댄스 (Pop/Dance)", "감성적인 발라드 (Ballad)", "웅장한 록 밴드 (Rock)"],
)

canvas_result = st_canvas(
    fill_color="rgba(239, 68, 68, 0.9)",
    stroke_width=8,
    stroke_color="#ef4444",
    background_color="#ffffff",
    height=260,
    width=680,
    drawing_mode="point",
    key="canvas_auto_band",
)

st.markdown("---")
st.subheader("🎧 풀밴드 자동 반주 음원 생성하기")

if st.button("🥁 드럼과 피아노 반주를 얹어 완곡 연주하기!"):
  if (
      canvas_result is not None
      and canvas_result.json_data is not None
      and "objects" in canvas_result.json_data
      and len(canvas_result.json_data["objects"]) > 0
  ):
    objects = canvas_result.json_data["objects"]

    sample_rate = 44100
    # 스타일에 따른 템포(BPM) 조절
    if "댄스" in band_style:
      bpm = 124
    elif "발라드" in band_style:
      bpm = 85
    else:
      bpm = 115

    beat_duration = 60.0 / bpm
    note_duration = beat_duration
    total_samples_per_note = int(sample_rate * note_duration)

    note_scale = [
        659.25,
        587.33,
        523.25,
        493.88,
        440.00,
        392.00,
        349.23,
        329.63,
        293.66,
        261.63,
        220.00,
    ]
    bass_scale = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00]

    user_notes = []
    for obj in objects:
      if "left" in obj and "top" in obj:
        user_notes.append((obj["left"], obj.get("top", 130)))
      elif "path" in obj and len(obj["path"]) > 0:
        for pt in obj["path"]:
          if len(pt) >= 3:
            user_notes.append((pt[1], pt[2]))

    if len(user_notes) > 0:
      user_notes.sort(key=lambda item: item[0])

      melody_track = []
      piano_chord_track = []
      bass_track = []
      drum_track = []

      # 유저가 찍은 음표 시드(Seed)를 바탕으로 4마디 이상의 풍성한 밴드 연주 생성
      for repeat in range(2):
        for idx, (x_pos, y_pos) in enumerate(user_notes):
          t = np.linspace(
              0, note_duration, total_samples_per_note, endpoint=False
          )

          norm_y = max(0, min(260, y_pos))
          scale_idx = int((norm_y / 260) * (len(note_scale) - 1))
          freq = note_scale[scale_idx]

          # 1. 메인 멜로디
          piano_lead = (
              0.5 * np.sin(2 * np.pi * freq * t)
              + 0.2 * np.sin(2 * np.pi * freq * 2 * t)
          ) * np.exp(-3.0 * t / note_duration)
          melody_track.append(piano_lead)

          # 2. 피아노 리듬 반주 (코드 아르페지오)
          chord_freq = freq * 1.25
          piano_chord = (
              0.25
              * np.sin(2 * np.pi * chord_freq * t)
              * np.exp(-4.0 * t / note_duration)
              * (1 if idx % 2 == 0 else 0.7)
          )
          piano_chord_track.append(piano_chord)

          # 3. 묵직한 베이스 기타
          bass_freq = bass_scale[scale_idx % len(bass_scale)]
          bass = (
              0.4 * np.sin(2 * np.pi * bass_freq * t)
              * np.exp(-2.0 * t / note_duration)
          )
          bass_track.append(bass)

          # 4. 자동 드럼 엔진 (킥, 스네어, 하이햇 조합)
          # 비트 박자(1~4박)에 따른 타격감 구현
          drum_beat = np.zeros(total_samples_per_note)
          sub_len = total_samples_per_note // 4

          for sub in range(4):
            sub_t = np.linspace(
                0, note_duration / 4, sub_len, endpoint=False
            )
            # 킥 (1, 3박 또는 댄스 리듬)
            if sub == 0 or (
                "댄스" in band_style and (sub == 2 or sub == 3)
            ):
              kick = (
                  0.7
                  * np.sin(
                      2
                      * np.pi
                      * np.linspace(120, 40, sub_len)
                      * sub_t
                  )
                  * np.exp(-12 * sub_t)
              )
              drum_beat[sub * sub_len : (sub + 1) * sub_len] += kick

            # 스네어 (2, 4박)
            if sub == 1 or sub == 3:
              snare = (
                  0.5
                  * np.random.uniform(-1, 1, sub_len)
                  * np.exp(-15 * sub_t)
              )
              drum_beat[sub * sub_len : (sub + 1) * sub_len] += snare

            # 하이햇 (매 쪼개진 박자)
            hihat = (
                0.2
                * np.random.uniform(-1, 1, sub_len)
                * np.exp(-30 * sub_t)
            )
            drum_beat[sub * sub_len : (sub + 1) * sub_len] += hihat

          drum_track.append(drum_beat)

      # 트랙 결합 및 믹싱
      full_melody = np.concatenate(melody_track)
      full_piano = np.concatenate(piano_chord_track)
      full_bass = np.concatenate(bass_track)
      full_drum = np.concatenate(drum_track)

      mixed_audio = full_melody + full_piano + full_bass + full_drum

      max_val = np.max(np.abs(mixed_audio))
      if max_val > 0:
        mixed_audio = mixed_audio / max_val * 0.95

      audio_data = (mixed_audio * 32767).astype(np.int16)

      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 풀밴드 음원 다운로드 (.wav)",
          data=wav_bytes,
          file_name="full_band_music.wav",
          mime="audio/wav",
      )
      st.success(
          f"🥁 선택하신 [{band_style}] 스타일에 맞춰 드럼과 피아노 반주가"
          " 완벽하게 믹싱되었습니다!"
      )
    else:
      st.warning("⚠️ 오선지 위에 콩나물 점을 먼저 콕콕 찍어주세요!")
  else:
    st.warning("⚠️ 먼저 오선지 판 위에 콩나물 점을 찍어주세요!")
