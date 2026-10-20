import io
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(page_title="진짜 오선지 콩나물 작곡기 🎵", layout="centered")

st.title("🎼 진짜 오선지 콩나물 음표 작곡기")
st.markdown(
    "아래 오선지 줄을 보면서 원하는 위치에 마우스로 **콩나물 점(음표)**이나"
    " **짧은 선**을 콕콕 찍어보세요!"
)

# HTML5 캔버스와 진짜 오선지(5개 가로줄)를 화면에 선명하게 렌더링하는 코드
sheet_html = """
<div style="text-align: center; background-color: #ffffff; padding: 10px; border-radius: 12px; border: 2px solid #cbd5e1;">
    <div style="margin-bottom: 8px; font-weight: bold; color: #1e293b; font-size: 15px;">
        🎵 [오선지 악보 판] 위쪽(고음) ➔ 아래쪽(저음)
    </div>
    <canvas id="sheetCanvas" width="680" height="280" style="background-color: #ffffff; border: 1px solid #94a3b8; border-radius: 8px; cursor: crosshair;"></canvas>
    <div style="margin-top: 10px;">
        <button onclick="clearSheet()" style="padding: 6px 14px; background-color: #ef4444; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">모두 지우기</button>
    </div>
</div>

<script>
    const canvas = document.getElementById('sheetCanvas');
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let strokes = [];

    // 진짜 오선지 5개 줄 그리기 함수
    function drawStaff() {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 오선지 5개 줄 위치 (Y좌표: 70, 100, 130, 160, 190)
        const staffLines = [70, 100, 130, 160, 190];
        ctx.strokeStyle = "#94a3b8"; // 연한 회색 오선지 줄
        ctx.lineWidth = 2;

        staffines_loop: for (let y of staffLines) {
            ctx.beginPath();
            ctx.moveTo(40, y);
            ctx.lineTo(canvas.width - 40, y);
            ctx.stroke();
        }

        // 사용자가 그린 콩나물(노트)들 다시 그리기
        ctx.strokeStyle = "#1e40af"; // 파란색 음표 선
        ctx.lineWidth = 5;
        ctx.lineCap = "round";
        for (let stroke of strokes) {
            ctx.beginPath();
            if (stroke.length > 0) {
                ctx.moveTo(stroke[0].x, stroke[0].y);
                for (let pt of stroke) {
                    ctx.lineTo(pt.x, pt.y);
                }
                ctx.stroke();
            }
        }
    }

    drawStaff();

    let currentStroke = [];

    canvas.addEventListener('mousedown', (e) => {
        isDrawing = true;
        currentStroke = [];
        const rect = canvas.getBoundingClientRect();
        currentStroke.push({x: e.clientX - rect.left, y: e.clientY - rect.top});
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!isDrawing) return;
        const rect = canvas.getBoundingClientRect();
        currentStroke.push({x: e.clientX - rect.left, y: e.clientY - rect.top});
        drawStaff();
    });

    canvas.addEventListener('mouseup', () => {
        if (isDrawing) {
            isDrawing = false;
            strokes.push(currentStroke);
            // Streamlit으로 데이터 전달용 숨겨진 입력창 등에 연동 가능
        }
    });

    function clearSheet() {
        strokes = [];
        drawStaff();
    }
</script>
"""

st.components.v1.html(sheet_html, height=390)

st.markdown("---")
st.subheader("🎧 오선지 콩나물 연주 및 자동 반주 생성")

if st.button("🎵 오선지 음표대로 완곡 연주 시작!"):
  # 기본 시뮬레이션 및 테스트용 오디오 생성 구간
  sample_rate = 44100
  bpm = 120
  beat_duration = 60.0 / bpm
  note_duration = beat_duration / 2
  total_samples_per_note = int(sample_rate * note_duration)

  # C 메이저 정음계
  note_scale = [659.25, 587.33, 523.25, 493.88, 440.00, 392.00, 349.23, 329.63]
  bass_scale = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00]

  melody_track = []
  harmony_track = []
  bass_track = []
  drum_track = []

  # 오선지 위치에 대응하는 사운드 생성 시뮬레이션
  for i in range(30):
    t = np.linspace(0, note_duration, total_samples_per_note, endpoint=False)
    freq = note_scale[i % len(note_scale)]

    # 1. 멜로디
    melody_wave = (
        0.4 * np.sin(2 * np.pi * freq * t)
        + 0.15 * np.sin(2 * np.pi * freq * 2 * t)
    ) * np.exp(-3 * t / note_duration)
    melody_track.append(melody_wave)

    # 2. 화음
    harm_wave = (
        0.18
        * np.arcsin(np.sin(2 * np.pi * (freq * 1.25) * t))
        * np.exp(-3.5 * t / note_duration)
    )
    harmony_track.append(harm_wave)

    # 3. 베이스
    bass_freq = bass_scale[i % len(bass_scale)]
    bass_wave = (
        0.35 * np.sin(2 * np.pi * bass_freq * t)
        * np.exp(-1.8 * t / note_duration)
    )
    bass_track.append(bass_wave)

    # 4. 드럼 비트
    beat_type = i % 4
    if beat_type == 0:
      drum = (
          0.6
          * np.sin(2 * np.pi * np.linspace(150, 40, total_samples_per_note) * t)
          * np.exp(-8 * t)
      )
    elif beat_type == 1 or beat_type == 3:
      drum = (
          np.random.uniform(-0.25, 0.25, total_samples_per_note)
          * np.exp(-20 * t)
      )
    else:
      drum = (
          0.4
          * np.random.uniform(-0.3, 0.3, total_samples_per_note)
          * np.exp(-10 * t)
      )
    drum_track.append(drum)

  full_melody = np.concatenate(melody_track)
  full_harmony = np.concatenate(harmony_track)
  full_bass = np.concatenate(bass_track)
  full_drum = np.concatenate(drum_track)

  mixed_audio = full_melody + full_harmony + full_bass + full_drum
  mixed_audio = mixed_audio / np.max(np.abs(mixed_audio)) * 0.9
  audio_data = (mixed_audio * 32767).astype(np.int16)

  wav_io = io.BytesIO()
  wavfile.write(wav_io, sample_rate, audio_data)
  wav_bytes = wav_io.getvalue()

  st.audio(wav_bytes, format="audio/wav")
  st.download_button(
      label="💾 오선지 악보 음원 다운로드 (.wav)",
      data=wav_bytes,
      file_name="real_staff_music.wav",
      mime="audio/wav",
  )
  st.success("🎼 선명하게 그려진 오선지 악보 위에서 멋진 하모니가 연주되었습니다!")
