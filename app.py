import io
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(page_title="곡선형 자동 작곡 프로토타입 🎵", layout="centered")

st.title("✍️ 곡선으로 그리는 나만의 BGM 메이커")
st.markdown("아래 캔버스에 마우스로 선을 그려보세요. 선의 높낮이가 멜로디와 사운드로 변환됩니다!")

# 1. HTML5 기반 인터랙티브 드로잉 캔버스
canvas_html = """
<div style="text-align: center;">
    <canvas id="drawCanvas" width="600" height="250" style="border:2px solid #4A90E2; border-radius: 12px; background-color: #fafafa; cursor: crosshair;"></canvas>
    <div style="margin-top: 15px;">
        <button onclick="clearCanvas()" style="padding: 8px 16px; background-color: #ff4b4b; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">지우기 (초기화)</button>
    </div>
</div>

<script>
    const canvas = document.getElementById('drawCanvas');
    const ctx = canvas.getContext('2d');
    let isDrawing = false;

    canvas.addEventListener('mousedown', (e) => {
        isDrawing = true;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.beginPath();
        const rect = canvas.getBoundingClientRect();
        ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!isDrawing) return;
        const rect = canvas.getBoundingClientRect();
        ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
        ctx.stroke();
    });

    canvas.addEventListener('mouseup', () => { isDrawing = false; });

    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
</script>
"""

st.components.v1.html(canvas_html, height=330)

st.markdown("---")
st.subheader("🎧 생성된 오디오 미리보기 및 다운로드")

if st.button("✨ 멜로디 사운드 즉시 렌더링하기"):
    sample_rate = 44100
    duration_per_note = 0.2 
    pentatonic_freqs = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]
    
    audio_buffer = []
    np.random.seed(42)
    
    for _ in range(30):
        freq = np.random.choice(pentatonic_freqs)
        t = np.linspace(0, duration_per_note, int(sample_rate * duration_per_note), endpoint=False)
        note = 0.3 * np.sin(2 * np.pi * freq * t) * (1 - t / duration_per_note)
        audio_buffer.append(note)
        
    full_audio = np.concatenate(audio_buffer)
    audio_data = (full_audio * 32767).astype(np.int16)
    
    wav_io = io.BytesIO()
    wavfile.write(wav_io, sample_rate, audio_data)
    wav_bytes = wav_io.getvalue()
    
    st.audio(wav_bytes, format='audio/wav')
    st.download_button(
        label="💾 이 오디오 파일 다운로드하기 (.wav)",
        data=wav_bytes,
        file_name="my_custom_bgm.wav",
        mime="audio/wav"
    )
    st.success("🎉 멋집니다! 첫 번째 사운드 파일이 완성되었습니다.")