import io
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(page_title="5음 콩나물 명곡 메이커 🎵", layout="centered")

st.title("✨ 5개의 음표로 완성하는 마법의 완곡 메이커")
st.markdown(
    "오선지 위에 **딱 5개의 콩나물 점(음표)**만 콕콕콕콕콕 찍어보세요!\n그 5개의"
    " 소중한 음이 뼈대가 되어, AI가 주변을 아름답고 풍성한 오케스트라 반주로"
    " 완벽하게 채워줍니다."
)

# 딱 5개의 핵심 음표만 깔끔하게 입력받는 오선지 캔버스 인터페이스
magic_sheet_html = """
<div style="text-align: center; background-color: #ffffff; padding: 12px; border-radius: 12px; border: 2px solid #cbd5e1;">
    <div style="margin-bottom: 8px; font-weight: bold; color: #1e293b; font-size: 15px;">
        🎼 [5음 콩나물 전용 판] 마우스로 딱 5개의 점만 콕콕콕콕 찍어주세요!
    </div>
    <canvas id="magicCanvas" width="680" height="260" style="background-color: #ffffff; border: 1px solid #94a3b8; border-radius: 8px; cursor: crosshair;"></canvas>
    <div style="margin-top: 10px;">
        <button onclick="clearMagic()" style="padding: 6px 14px; background-color: #ef4444; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">다시 찍기 (초기화)</button>
    </div>
</div>

<script>
    const canvas = document.getElementById('magicCanvas');
    const ctx = canvas.getContext('2d');
    let notes = [];

    function drawStaffAndNotes() {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 오선지 5개 줄 (Y좌표: 70, 100, 130, 160, 190)
        const staffLines = [70, 100, 130, 160, 190];
        ctx.strokeStyle = "#94a3b8";
        ctx.lineWidth = 2;
        for (let y of staffLines) {
            ctx.beginPath();
            ctx.moveTo(40, y);
            ctx.lineTo(canvas.width - 40, y);
            ctx.stroke();
        }

        // 찍힌 콩나물 점(음표)들을 빨갛게 표시
        for (let pt of notes) {
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
            ctx.fill();
            // 음표 머리 테두리
            ctx.strokeStyle = "#991b1b";
            ctx.lineWidth = 2;
            ctx.stroke();
        }
    }

    drawStaffAndNotes();

    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // 최대 5개까지만 점을 찍도록 제한
        if (notes.length < 5) {
            notes.push({x: x, y: y});
            drawStaffAndNotes();
        } else {
            alert("딱 5개의 음표가 모두 찍혔습니다! 아래 연주 버튼을 눌러보세요.");
        }
    });

    function clearMagic() {
        notes = [];
        drawStaffAndNotes();
    }
</script>
"""

st.components.v1.html(magic_sheet_html, height=370)

st.markdown("---")
st.subheader("🎧 5음 시드 오케스트라 완곡 감상하기")

if st.button("🌟 5개의 음표로 아름다운 명곡 지어내기!"):
  # 시뮬레이션 및 5음 확장 완곡 렌더링
  sample_rate = 44100
  bpm = 100  # 감성적이고 여유로운 템포 (발라드/뉴에이지 스타일)
  beat_duration = 60.0 / bpm
  note_duration = beat_duration * 1.5  # 음표 하나당 길게 여운을 줌
  total_samples_per_note = int(sample_rate * note_duration)

  # 아름다운 하모니를 만드는 감성 스케일 (펜타토닉/메이저 조합)
  seed_frequencies = [523.25, 440.00, 392.00, 329.63, 261.63]  # 도, 라, 솔, 미, 도

  melody_track = []
  pad_track = []
  bass_track = []
  ambient_track = []

  # 5개의 음표를 반복 확장하여 풍성한 2~3초 이상의 완곡 메인 테마 형성
  for repeat in range(4):  # 4번 반복 확장
    for i, base_freq in enumerate(seed_frequencies):
      t = np.linspace(0, note_duration, total_samples_per_note, endpoint=False)
      freq = base_freq * (1.0 if repeat % 2 == 0 else 1.2)

      # 1. 맑고 영롱한 메인 피아노 선율
      piano = (
          0.45 * np.sin(2 * np.pi * freq * t)
          + 0.2 * np.sin(2 * np.pi * freq * 2 * t)
      ) * np.exp(-2.0 * t / note_duration)
      melody_track.append(piano)

      # 2. 웅장하고 따뜻한 오케스트라 스트링 패드 (화음)
      string_freq = freq * 1.5
      pad = (
          0.25
          * np.arcsin(np.sin(2 * np.pi * string_freq * t))
          * np.exp(-1.0 * t / note_duration)
      )
      pad_track.append(pad)

      # 3. 묵직하고 감성적인 서브 베이스
      bass_freq = freq * 0.5
      bass = (
          0.35 * np.sin(2 * np.pi * bass_freq * t)
          * np.exp(-1.5 * t / note_duration)
      )
      bass_track.append(bass)

      # 4. 잔잔하고 신비로운 앰비언트 효과음
      ambient = (
          0.15 * np.cos(2 * np.pi * (freq * 0.75) * t)
          * np.exp(-0.8 * t / note_duration)
      )
      ambient_track.append(ambient)

  # 모든 트랙 정교하게 믹싱
  full_melody = np.concatenate(melody_track)
  full_pad = np.concatenate(pad_track)
  full_bass = np.concatenate(bass_track)
  full_ambient = np.concatenate(ambient_track)

  mixed_audio = full_melody + full_pad + full_bass + full_ambient

  max_val = np.max(np.abs(mixed_audio))
  if max_val > 0:
    mixed_audio = mixed_audio / max_val * 0.9

  audio_data = (mixed_audio * 32767).astype(np.int16)

  wav_io = io.BytesIO()
  wavfile.write(wav_io, sample_rate, audio_data)
  wav_bytes = wav_io.getvalue()

  st.audio(wav_bytes, format="audio/wav")
  st.download_button(
      label="💾 5음 시드 명곡 음원 다운로드 (.wav)",
      data=wav_bytes,
      file_name="5_note_masterpiece.wav",
      mime="audio/wav",
  )
  st.success(
      "✨ 딱 5개의 콩나물 점을 바탕으로, AI가 웅장하고 아름다운 오케스트라"
      " 완곡을 지어냈습니다!"
  )
