import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="스마트 자동 반주 곡선 작곡기 🎵", layout="centered"
)

st.title("🧙‍♂️ 기준선 하나로 완성되는 스마트 자동 반주 작곡기")
st.markdown(
    "복잡하게 여러 선을 그릴 필요가 없습니다! **원하는 메인 느낌대로 선을 하나만"
    " 슥 그리면**, 알고리즘이 화음, 베이스, 드럼 반주를 알아서 찰떡같이"
    " 붙여줍니다."
)

# 1. 심플한 단일 캔버스
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=5,
    stroke_color="#1E88E5",
    background_color="#F8FAFC",
    height=280,
    width=680,
    drawing_mode="freedraw",
    key="canvas_smart_accompaniment",
)

st.caption(
    "💡 **팁:** 마우스로 왼쪽에서 오른쪽으로 원하는 음높이 흐름을 자유롭게 그려보세요!"
)

st.markdown("---")
st.subheader("🎧 AI 자동 반주 완성하기")

if st.button("✨ 이 선에 맞춰 풀-밴드 자동 반주 연주하기!"):
  if (
      canvas_result is not None
      and canvas_result.json_data is not None
      and "objects" in canvas_result.json_data
      and len(canvas_result.json_data["objects"]) > 0
  ):
    # 가장 마지막에 그린(또는 대표) 선 하나를 메인 기준선으로 추출
    objects = canvas_result.json_data["objects"]
    main_obj = objects[-1]

    if "path" in main_obj and len(main_obj["path"]) > 0:
      y_points = [point[2] for point in main_obj["path"] if len(point) >= 3]

      if len(y_points) > 0:
        sample_rate = 44100
        bpm = 124  # 어깨가 들썩이는 가요 댄스 템포
        beat_duration = 60.0 / bpm
        note_duration = beat_duration / 2  # 8비트 박자 (약 0.24초)
        total_samples_per_note = int(sample_rate * note_duration)

        # C 메이저 스케일 (음악적으로 어울리는 음계 구성)
        melody_scale = [
            261.63,
            293.66,
            329.63,
            349.23,
            392.00,
            440.00,
            493.88,
            523.25,
            587.33,
            659.25,
            783.99,
        ]
        # 코드 반주용 3도/5도 화음 매핑
        bass_scale = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00]  # 낮은 베이스

        step = max(1, len(y_points) // 60)
        sampled_y = y_points[::step]

        melody_track = []
        harmony_track = []
        bass_track = []
        drum_track = []

        # 2. 메인 기준선 하나를 바탕으로 4가지 악기 반주 자동 형성 (Auto-Arrangement)
        for i, y in enumerate(sampled_y):
          t = np.linspace(
              0, note_duration, total_samples_per_note, endpoint=False
          )

          # (1) 메인 멜로디 (유저의 그린 선을 그대로 반영)
          norm_y = max(0, min(280, 280 - y))
          scale_idx = int((norm_y / 280) * (len(melody_scale) - 1))
          main_freq = melody_scale[scale_idx]

          melody_wave = (
              0.35 * np.sin(2 * np.pi * main_freq * t)
              + 0.1 * np.sin(2 * np.pi * main_freq * 2 * t)
          ) * np.exp(-2.5 * t / note_duration)
          melody_track.append(melody_wave)

          # (2) 화음 반주 (메인 멜로디에 잘 어울리는 3도 위 화음 자동 형성)
          harm_freq = main_freq * 1.25  # 풍성한 장3도 화음
          harmony_wave = (
              0.20
              * np.arcsin(np.sin(2 * np.pi * harm_freq * t))
              * np.exp(-3 * t / note_duration)
          )
          harmony_track.append(harmony_wave)

          # (3) 베이스 반주 (메인 음의 근음에 맞춰 묵직한 가요 베이스 자동 형성)
          bass_freq = bass_scale[scale_idx % len(bass_scale)]
          bass_wave = (
              0.4
              * (
                  np.sin(2 * np.pi * bass_freq * t)
                  + 0.3 * np.sin(2 * np.pi * bass_freq * 2 * t)
              )
              * np.exp(-1.5 * t / note_duration)
          )
          bass_track.append(bass_wave)

          # (4) 댄스 드럼 비트 반주 (4/4박자 가요 리듬 자동 형성)
          beat_type = i % 4
          if beat_type == 0:  # 쿵 (강력한 킥)
            kick = np.sin(
                2 * np.pi * np.linspace(150, 40, total_samples_per_note) * t
            ) * np.exp(-8 * t)
            drum_wave = 0.65 * kick
          elif beat_type == 1 or beat_type == 3:  # 치 (하이햇)
            hihat = (
                np.random.uniform(-0.25, 0.25, total_samples_per_note)
                * np.exp(-20 * t)
            )
            drum_wave = hihat
          else:  # 딱 (스네어)
            snare_t = np.sin(2 * np.pi * 180 * t) * np.exp(-12 * t)
            snare_n = (
                np.random.uniform(-0.35, 0.35, total_samples_per_note)
                * np.exp(-10 * t)
            )
            drum_wave = 0.4 * snare_t + 0.4 * snare_n

          drum_track.append(drum_wave)

        # 3. 메인 멜로디 + AI 자동 형성 반주들 하나로 믹싱 (Mastering)
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
            label="💾 자동 반주 완성 음원 다운로드 (.wav)",
            data=wav_bytes,
            file_name="auto_accompanied_music.wav",
            mime="audio/wav",
        )
        st.success(
            "🎉 완벽합니다! 그린 기준선 하나를 바탕으로 AI가 주변 화음, 베이스,"
            " 드럼 반주를 완성했습니다!"
        )
      else:
        st.warning("⚠️ 캔버스에 선을 조금 더 길게 그려주세요!")
    else:
      st.warning("⚠️ 선이 제대로 인식되지 않았습니다. 지우고 다시 그려주세요!")
  else:
    st.warning("⚠️ 먼저 캔버스에 기준이 될 선을 하나만 자유롭게 그려보세요!")
