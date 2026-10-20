import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎸 프로 가요풍 연주곡(MR) 스튜디오",
    page_icon="🎶",
    layout="centered",
)

st.title("🎸 프로 가요풍 연주곡(MR) AI 작곡 스튜디오")
st.markdown("가창(보컬) 없이도 기타, 피아노, 스트링, 드럼이 꽉 찬 하모니를 이루는 고품격 연주 트랙을 완성합니다!")

st.markdown("---")

# --- 설정 영역 ---
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
    "🎸 메인 악기 주법 & 스타일:",
    ["어쿠스틱 스트럼 + 스트링 패드 (웅장한 감성)", "핑거스타일 아르페지오 + 피아노 (잔잔한 발라드)"]
)

total_bars = st.select_slider(
    "📏 곡 전체 길이 (마디 수):",
    options=[4, 8, 12, 16],
    value=8,
    format_func=lambda x: f"{x}마디 (약 {int(x * 2.0)}초 연주)"
)

bpm = st.slider("⏱️ 템포 (BPM):", min_value=70, max_value=130, value=96)

# --- 코드 매핑 ---
if "C - G - Am - F" in progression_choice:
    preview_chords = ["C", "G", "Am", "F"]
    bar_chords = ["C", "G", "Am", "F"]
    bass_roots = [130.81, 98.00, 110.00, 87.31]
elif "Am - F - C - G" in progression_choice:
    preview_chords = ["Am", "F", "C", "G"]
    bar_chords = ["Am", "F", "C", "G"]
    bass_roots = [110.00, 87.31, 130.81, 98.00]
elif "C - Am - F - G" in progression_choice:
    preview_chords = ["C", "Am", "F", "G"]
    bar_chords = ["C", "Am", "F", "G"]
    bass_roots = [130.81, 110.00, 87.31, 98.00]
else:
    preview_chords = ["Am7", "Fmaj7", "G7", "C"]
    bar_chords = ["Am7", "Fmaj7", "G7", "C"]
    bass_roots = [110.00, 87.31, 98.00, 130.81]

st.info(f"**📌 적용되는 4코드 순환 루프:** " + ", ".join([f"{i+1}마디({preview_chords[i%len(preview_chords)]})" for i in range(total_bars)]))

# --- 고품질 악기 합성 엔진 ---
def synthesize_chord_sound(chord_freqs, duration, sample_rate, style_type):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    signal = np.zeros_like(t)
    string_delay = int(sample_rate * 0.02)
    
    for i, freq in enumerate(chord_freqs):
        offset = i * string_delay
        if offset >= num_samples:
            continue
        sub_t = t[:num_samples - offset]
        
        # 풍성한 배음 구조
        sound = (0.45 * np.sin(2 * np.pi * freq * sub_t) +
                 0.25 * np.sin(2 * np.pi * freq * 2 * sub_t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * sub_t))
        
        if "스트럼" in style_type:
            decay = np.exp(-3.8 * sub_t / duration)
        else:
            decay = np.exp(-2.5 * sub_t / duration)
            
        sound *= decay
        signal[offset:offset + len(sound)] += sound
        
    return signal

def synthesize_string_pad(chord_freqs, duration, sample_rate):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    pad = np.zeros_like(t)
    
    for freq in chord_freqs[:3]: # 상위 화음으로 웅장한 스트링 패드 연출
        vibrato = 1.0 + 0.004 * np.sin(2 * np.pi * 5.0 * t)
        wave = 0.3 * np.sin(2 * np.pi * freq * vibrato * t) + 0.15 * np.sin(2 * np.pi * freq * 2 * vibrato * t)
        envelope = np.exp(-1.2 * t / duration)
        pad += wave * envelope
        
    return pad

def synthesize_drum_hit(drum_type, duration, sample_rate):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    if drum_type == "kick":
        f_sweep = np.linspace(130, 30, len(t))
        return 0.75 * np.sin(2 * np.pi * f_sweep * t) * np.exp(-14 * t / duration)
    elif drum_type == "snare":
        noise = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-16 * t / duration)
        body = 0.35 * np.sin(2 * np.pi * 170 * t) * np.exp(-18 * t / duration)
        return noise + body
    elif drum_type == "hihat":
        return 0.22 * np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-40 * t / duration)
    return np.zeros_like(t)

# --- 생성 버튼 ---
if st.button("🚀 고품격 연주곡(MR) 생성하기!", type="primary"):
    with st.spinner("🎵 기타, 피아노, 스트링 및 밴드 세션을 믹싱하여 풍성한 연주곡을 만드는 중입니다..."):
        sample_rate = 44100
        beat_dur = 60.0 / bpm
        bar_dur = 4 * beat_dur
        total_duration = total_bars * bar_dur
        total_samples = int(sample_rate * total_duration)

        guitar_track = np.zeros(total_samples)
        string_pad_track = np.zeros(total_samples)
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

            # 곡의 기승전결: 후반부(후렴구)로 갈수록 사운드 볼륨 고조 (다이나믹스 부여)
            section_intensity = 0.8 + 0.2 * (b / total_bars)

            slot_samples = bar_samples // 4

            for beat in range(4):
                st_s = b_start + beat * slot_samples
                st_e = min(total_samples, st_s + slot_samples)
                st_dur = (st_e - st_s) / sample_rate
                if st_dur <= 0 or st_s >= total_samples:
                    continue

                # 1. 메인 기타/피아노 스트럼
                g_hit = section_intensity * 0.6 * synthesize_chord_sound(chord_freqs, st_dur * 1.3, sample_rate, strum_type)
                g_len = min(len(g_hit), st_e - st_s)
                if g_len > 0:
                    guitar_track[st_s:st_s + g_len] += g_hit[:g_len]

                # 2. 웅장한 스트링 패드 (공간감 부여)
                s_pad = section_intensity * 0.4 * synthesize_string_pad(chord_freqs, st_dur * 2.2, sample_rate)
                s_len = min(len(s_pad), st_e - st_s)
                if s_len > 0:
                    string_pad_track[st_s:st_s + s_len] += s_pad[:s_len]

                # 3. 베이스 기타
                if beat in [0, 2]:
                    b_hit = section_intensity * 0.65 * synthesize_chord_sound([bass_freq, bass_freq * 1.5], st_dur * 1.8, sample_rate, "아르페지오")
                    b_len = min(len(b_hit), st_e - st_s)
                    if b_len > 0:
                        bass_track[st_s:st_s + b_len] += b_hit[:b_len]

            # 4. 찰진 밴드 드럼 리듬 (16분음표)
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
                        drum_track[sl_s:sl_s + dk_len] += section_intensity * dk[:dk_len]
                if slot in [4, 12]:
                    ds = synthesize_drum_hit("snare", sl_dur, sample_rate)
                    ds_len = min(len(ds), sl_e - sl_s)
                    if ds_len > 0:
                        drum_track[sl_s:sl_s + ds_len] += section_intensity * ds[:ds_len]
                if slot % 2 == 1 or slot % 2 == 0:
                    dh = synthesize_drum_hit("hihat", sl_dur, sample_rate)
                    dh_len = min(len(dh), sl_e - sl_s)
                    if dh_len > 0:
                        drum_track[sl_s:sl_s + dh_len] += section_intensity * dh[:dh_len]

        # 최종 믹싱
        full_audio = (0.7 * guitar_track + 
                      0.5 * string_pad_track + 
                      0.65 * bass_track + 
                      0.6 * drum_track)
                      
        max_val = np.max(np.abs(full_audio))
        if max_val > 0:
            full_audio = (full_audio / max_val) * 0.95

        audio_int16 = (full_audio * 32767).astype(np.int16)
        buf = io.BytesIO()
        wavfile.write(buf, sample_rate, audio_int16)
        wav_bytes = buf.getvalue()

        st.success(f"🎉 약 {int(total_duration)}초 분량 ({total_bars}마디)의 고품격 연주 트랙(MR)이 완성되었습니다!")
        st.audio(wav_bytes, format="audio/wav")

        st.download_button(
            label="💾 고품격 연주 트랙 음원 다운로드 (.wav)",
            data=wav_bytes,
            file_name=f"kpop_mr_track_{total_bars}bars.wav",
            mime="audio/wav"
        )
