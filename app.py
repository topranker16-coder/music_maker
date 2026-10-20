import io
import numpy as np
from scipy.io import wavfile
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="곡선형 자동 작곡 프로토타입 🎵", layout="centered"
)

st.title("✍️ 내 마음대로 그리는 곡선 BGM 메이커")
st.markdown(
    "아래 파란 캔버스에 마우스나 손가락으로 **왼쪽에서 오른쪽으로** 자유롭게 선을"
    " 그려보세요!"
)
st.markdown(
    "💡 **위쪽에 그리면 높은 음**, **아래쪽에 그리면 낮은 음**이 소리 납니다."
)

# 1. 스트림릿 전용 드로잉 캔버스 생성 (좌표 데이터를 파이썬이 읽을 수 있는 캔버스)
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=4,
    stroke_color="#1E88E5",  # 선 색상: 파란색
    background_color="#F0F2F6",  # 배경색: 밝은 회색
    height=250,
    width=600,
    drawing_mode="freedraw",
    key="canvas",
)

st.markdown("---")
st.subheader("🎧 내가 그린 곡선으로 오디오 만들기")

# 2. 그린 선의 좌표 데이터를 오디오 소리로 변환하는 엔진
if st.button("🎵 이 곡선으로 음악 렌더링하기!"):
  if (
      canvas_result.json_data is not None
      and len(canvas_result.json_data["objects"]) > 0
  ):
    # 그린 선의 모든 점 좌표(X, Y) 가져오기
    path_data = canvas_result.json_data["objects"][0]["path"]

    # Y 좌표(높낮이) 모으기
    # 캔버스 특성상 맨 위가 Y=0, 맨 아래가 Y=250 입니다.
    y_points = [point[2] for point in path_data if len(point) >= 3]

    if len(y_points) > 0:
      # 편안하고 신나는 펜타토닉 음계 (낮은 음부터 높은 음까지 2옥타브 배열)
      # [도, 레, 미, 솔, 라, 도, 레, 미, 솔, 라, 높은도]
      scale = [
          130.81,
          146.83,
          164.81,
          196.00,
          220.00,  # 3옥타브
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

      sample_rate = 44100
      note_duration = 0.15  # 한 음당 길이 (0.15초)
      audio_segments = []

      # 너무 많은 점이 있으면 듬성듬성 샘플링하여 음악 박자로 변환 (최대 40개 음표)
      step = max(1, len(y_points) // 40)
      sampled_y = y_points[::step]

      for y in sampled_y:
        # Y좌표(0~250)를 음계 범위로 변환 (위로 갈수록 높은 음계 index 지정)
        # 캔버스는 위쪽 Y가 0이므로, (250 - y)로 뒤집어서 높낮이를 정해줍니다.
        normalized_y = max(0, min(250, 250 - y))
        scale_index = int((normalized_y / 250) * (len(scale) - 1))
        freq = scale[scale_index]

        # 음생성 (사인파 오디오 연산 + 부드러운 페이드아웃 효과)
        t = np.linspace(
            0, note_duration, int(sample_rate * note_duration), endpoint=False
        )
        # 소리가 뚝뚝 끊기지 않도록 엔벨롭(잔향) 추가
        envelope = np.exp(-3 * t / note_duration)
        note = 0.4 * np.sin(2 * np.pi * freq * t) * envelope
        audio_segments.append(note)

      # 하나로 이어붙여 전체 오디오 곡으로 완성
      full_audio = np.concatenate(audio_segments)
      audio_data = (full_audio * 32767).astype(np.int16)

      # 스트림릿에서 바로 재생 가능하도록 WAV 파일 빌드
      wav_io = io.BytesIO()
      wavfile.write(wav_io, sample_rate, audio_data)
      wav_bytes = wav_io.getvalue()

      # 플레이어 화면 및 다운로드 버튼 제공
      st.audio(wav_bytes, format="audio/wav")
      st.download_button(
          label="💾 오디오 파일 다운로드 (.wav)",
          data=wav_bytes,
          file_name="my_drawn_music.wav",
          mime="audio/wav",
      )
      st.success("✨ 세상에 하나뿐인 내가 그린 곡선 멜로디가 완성되었습니다!")
    else:
      st.warning("⚠️ 캔버스에 선을 조금 더 길게 그려보세요!")
  else:
    st.warning("⚠️ 먼저 위 파란 캔버스 영역에 선을 그려주세요!")
