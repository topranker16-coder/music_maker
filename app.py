import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎸 기타 코드 반주 AI 작곡 스튜디오",
    page_icon="🎶",
    layout="wide",
)

# --- CSS 스타일 ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1100px !important;
    }
    .header-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #1e3a8a 50%, #2563eb 100%);
        padding: 24px 28px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
        border: 1px solid #60a5fa;
    }
    .chord-badge {
        display: inline-block;
        background: #2563eb;
        color: white;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: bold;
        margin: 4px;
        font-size: 0.95rem;
        border: 1px solid #93c5fd;
    }
    .status-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 18px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 주파수 테이블 ---
NOTE_FREQS = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99, "A5": 880.00
}

# --- 기타 스트럼 및 악기 합성 엔진 ---
def synthesize_guitar_strum(chord_freqs, duration, sample_rate, strum_type="어쿠스틱 스트럼"):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    
    t = np.linspace(0, duration, num_samples, endpoint=False)
    strum_signal = np.zeros_like(t)
    
    string_delay = int(sample_rate * 0.025)
    
    for i, freq in enumerate(chord_freqs):
        offset = i * string_delay
        if offset >= num_samples:
            continue
        sub_t = t[:num_samples - offset]
        
        string_sound = (0.4 * np.sin(2 * np.pi * freq * sub_t) +
                        0.25 * np.sin(2 * np.pi * freq * 2 * sub_t) +
                        0.12 * np.sin(2 * np.pi * freq * 3 * sub_t))
        
        if "스트럼" in strum_type:
            pluck_decay = np.exp(-4.5 * sub_t / duration)
        else:
            pluck_decay = np.exp(-3.0 * sub_t / duration)
            
        string_sound *= pluck_decay
        
        fade_len = min(int(0.01 * sample_rate), len(sub_t) // 2)
        if fade_len > 0:
            string_sound[:fade_len] *= np.linspace(0, 1, fade_len)
            string_sound[-fade_len:] *= np.linspace(1, 0, fade_len)
            
        strum_signal[offset:offset + len(string_sound)] += string_sound
        
    return strum_signal

def synthesize_drum_hit(drum_type, duration, sample_rate):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    if drum_type == "kick":
        f_sweep = np.linspace(120, 30, len(t))
        return 0.7 * np.sin(2 * np.pi * f_sweep * t) * np.exp(-12 * t / duration)
    elif drum_type == "snare":
        noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-15 * t / duration)
        body = 0.3 * np.sin(2 * np.pi * 180 * t) * np.exp(-18 * t / duration)
        return noise + body
    elif drum_type == "hihat":
        return 0.2 * np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-35 * t / duration)
    return np.zeros_like(t)

def generate_guitar_band_song(progression_name, strum_type, total_bars, bpm, sample_rate):
    beat_dur = 60.0 / bpm
    bar_dur = 4 * beat_dur
    total_duration = total_bars * bar_dur
    total_samples = int(sample_rate * total_duration)

    guitar_track = np.zeros(total_samples)
    piano_pad_track = np.zeros(total_samples)
    bass_track = np.zeros(total_samples)
    drum_track = np.zeros(total_samples)

    chord_library = {
        "C": [261.63, 329.63, 392.00, 523.25],
        "Am": [220.00, 261.63, 329.63, 440.00],
        "F": [174.61, 220.00, 261.63, 349.23],
        "G": [196.00, 246.94, 293.66, 392.00],
        "Am7": [220.00, 261.63, 329.63, 392.00],
        "Fmaj7": [174.61, 220.00, 261.63, 329.63],
        "G7": [196.00, 246.94, 293.66, 349.23],
    }

    if "I - V - VIm - IV" in progression_name:
        bar_chords = ["C", "G", "Am", "F"]
        bass_roots = [130.81, 98.00, 110.00, 87.31]
    elif "VIm - IV - I - V" in progression_name:
        bar_chords = ["Am", "F", "C", "G"]
        bass_roots = [110.00, 87.31, 130.81, 98.00]
    elif "I - VIm - IV - V" in progression_name:
        bar_chords = ["C", "Am", "F", "G"]
        bass_roots = [130.81, 110.00, 87.31, 98.00]
    else:
        bar_chords = ["Am7", "Fmaj7", "G7", "C"]
        bass_roots = [110.00, 87.31, 98.00, 130.81]

    bar_samples = int(sample_rate * bar_dur)

    for b in range(total_bars):
        b_start = b * bar_samples
        b_end = min(total_samples, (b + 1) * bar_samples)
        b_len = b_end - b_start
        if b_len <= 0:
            break

        current_chord_name = bar_chords[b % len(bar_chords)]
        chord_freqs = chord_library[current_chord_name]
        bass_freq = bass_roots[b % len(bass_roots)]

        slot_samples = bar_samples // 4

        for beat in range(4):
            st_s = b_start + beat * slot_samples
            st_e = min(total_samples, st_s + slot_samples)
            st_dur = (st_e - st_s) / sample_rate
            if st_dur <= 0 or st_s >= total_samples:
                continue

            guitar_hit = 0.55 * synthesize_guitar_strum(chord_freqs, st_dur * 1.2, sample_rate, strum_type)
            g_len = min(len(guitar_hit), st_e - st_s)
            if g_len > 0:
                guitar_track[st_s:st_s + g_len] += guitar_hit[:g_len]

            if beat == 0 or beat == 2:
                pad_hit = 0.3 * synthesize_guitar_strum(chord_freqs, st_dur * 2.0, sample_rate, "아르페지오")
                p_len = min(len(pad_hit), st_e - st_s)
                if p_len > 0:
                    piano_pad_track[st_s:st_s + p_len] += pad_hit[:p_len]

            if beat in [0, 2]:
                bass_hit = 0.6 * synthesize_guitar_strum([bass_freq, bass_freq * 1.5], st_dur * 1.8, sample_rate, "아르페지오")
                b_len = min(len(bass_hit), st_e - st_s)
                if b_len > 0:
                    bass_track[st_s:st_s + b_len] += bass_hit[:b_len]

        slot_16_samples = bar_samples // 16
        for slot in range(16):
            sl_s = b_start + slot * slot_16_samples
            sl_e = min(total_samples, sl_s + slot_16_samples)
            sl_dur = (sl_e - sl_s) / sample_rate
            if sl_dur <= 0 or sl_s >= total_samples:
                continue

            if slot % 4 == 0:
                dk = synthesize_drum_hit("kick", sl_dur, sample_rate)
                dk_len = min(len(dk), sl_e - sl_s)
                if dk_len > 0:
                    drum_track[sl_s:sl_s + dk_len] += dk[:dk_len]
            if slot in [4, 12]:
                ds = synthesize_drum_hit("snare", sl_dur, sample_rate)
                ds_len = min(len(ds), sl_e - sl_s)
                if ds_len > 0:
                    drum_track[sl_s:sl_s + ds_len] += ds[:ds_len]
            if slot % 2 == 1 or slot % 2 == 0:
                dh = synthesize_drum_hit("hihat", sl_dur, sample_rate)
                dh_len = min(len(dh), sl_e - sl_s)
                if dh_len > 0:
                    drum_track[sl_s:sl_s + dh_len] += dh[:dh_len]

    full_audio = (0.75 * guitar_track + 
                  0.45 * piano_pad_track + 
                  0.65 * bass_track + 
                  0.65 * drum_track)
                  
    max_val = np.max(np.abs(full_audio))
    if max_val > 0:
        full_audio = (full_audio / max_val) * 0.95

    return full_audio, total_duration

# --- UI 레이아웃 ---
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size: 1.8rem; color: white;">🎸 기타 코드 반주 AI 작곡 스튜디오</h1>
    <p style="margin-top: 6px; color: #e2e8f0; font-size: 0.95rem;">
        세련된 가요풍 기타 코드 진행과 리듬 스트럼으로 꽉 찬 반주곡을 즉시 완성합니다!
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎛️ 1. 코드 진행 및 스타일 설정")
    
    progression_choice = st.selectbox(
        "🎼 가요풍 코드 진행 선택:",
        [
            "I - V - VIm - IV (발라드 국민 진행: C - G - Am - F)",
            "VIm - IV - I - V (감성 팝 진행: Am - F - C - G)",
            "I - VIm - IV - V (두왑 / 팝 발라드: C - Am - F - G)",
            "R&B / 인디 감성 진행 (Am7 - Fmaj7 - G7 - C)"
        ]
    )

    strum_type = st.selectbox(
        "🎸 기타 주법 (스트럼 스타일):",
        ["어쿠스틱 스트럼 (청량한 리듬 긁기)", "핑거스타일 아르페지오 (부드러운 분산 화음)"]
    )

    total_bars = st.select_slider(
        "📏 곡 전체 길이 (마디 수):",
        options=[4, 8, 12, 16],
        value=8,
        format_func=lambda x: f"{x}마디 (약 {int(x * 2.0)}초 연주)"
    )
    
    bpm = st.slider("⏱️ 템포 (BPM):", min_value=70, max_value=130, value=100)

with col2:
    st.subheader("🪄 2. 반주 곡 생성하기")
    st.info("💡 버튼을 누르면 기타 스트럼과 밴드 세션이 믹싱됩니다.")

    if "C - G - Am - F" in progression_choice:
        preview_chords = ["C", "G", "Am", "F"]
    elif "Am - F - C - G" in progression_choice:
        preview_chords = ["Am", "F", "C", "G"]
    elif "C - Am - F - G" in progression_choice:
        preview_chords = ["C", "Am", "F", "G"]
    else:
        preview_chords = ["Am7", "Fmaj7", "G7", "C"]

    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.markdown("**📌 적용되는 4코드 순환 루프:**")
    badges = []
    for i in range(total_bars):
        c_name = preview_chords[i % len(preview_chords)]
        badges.append(f'<span class="chord-badge">{i+1}마디: {c_name}</span>')
    st.markdown(" ".join(badges), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 기타 반주 밴드 곡 연주하기!", type="primary", use_container_width=True):
        with st.spinner("🎸 기타 스트럼 주법과 밴드 세션을 연주 중입니다..."):
            sample_rate = 44100
            generated_audio, act_dur = generate_guitar_band_song(
                progression_choice, strum_type, total_bars, bpm, sample_rate
            )

            audio_int16 = (generated_audio * 32767).astype(np.int16)
            buf = io.BytesIO()
            wavfile.write(buf, sample_rate, audio_int16)
            wav_bytes = buf.getvalue()

            st.success(f"🎉 **약 {int(act_dur)}초 분량 ({total_bars}마디)**의 기타 반주 곡이 완성되었습니다!")
            st.audio(wav_bytes, format="audio/wav")

            st.download_button(
                label="💾 기타 반주 음원 다운로드 (.wav)",
                data=wav_bytes,
                file_name=f"guitar_band_song_{total_bars}bars.wav",
                mime="audio/wav"
            )
