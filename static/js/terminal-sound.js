let audioCtx = null;

export function ensureAudio() {
    if (!audioCtx) {
        try {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        } catch {
            audioCtx = null;
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

function tone(freq, startOffset, duration, peak, type) {
    const now = audioCtx.currentTime;
    const oscillator = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    oscillator.type = type;
    oscillator.frequency.value = freq;

    gain.gain.setValueAtTime(0.0001, now + startOffset);
    gain.gain.exponentialRampToValueAtTime(peak, now + startOffset + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + startOffset + duration);

    oscillator.connect(gain).connect(audioCtx.destination);
    oscillator.start(now + startOffset);
    oscillator.stop(now + startOffset + duration + 0.02);
}

function playSound(kind) {
    if (!audioCtx) return;

    switch (kind) {
        case 'ping':
            tone(1760, 0, 0.18, 0.22, 'sine');
            break;
        case 'chime':
            tone(880, 0, 0.2, 0.25, 'sine');
            tone(1320, 0.12, 0.2, 0.25, 'sine');
            break;
        case 'siren':
            [0, 0.18, 0.36].forEach((offset) => {
                tone(700, offset, 0.1, 0.22, 'square');
                tone(1100, offset + 0.09, 0.1, 0.22, 'square');
            });
            break;
        case 'bloop':
            tone(440, 0, 0.15, 0.22, 'triangle');
            break;
        case 'alert':
            [0, 0.14, 0.28].forEach((offset) => tone(2000, offset, 0.08, 0.28, 'sawtooth'));
            break;
    }
}

export function beep(enabled, soundType) {
    if (!enabled || !audioCtx) return;
    playSound(soundType);
}

export function renderSoundToggle(enabled) {
    const soundEl = document.getElementById('status-sound');
    if (!soundEl) return;

    soundEl.textContent = enabled ? 'SOUND ON' : 'SOUND OFF';
    soundEl.style.color = enabled ? '#22c55e' : '';
}

export function syncSoundPicker(soundType) {
    const soundSelect = document.getElementById('sound-pick');
    if (soundSelect) soundSelect.value = soundType;
}

export function bindSoundPicker({ getSoundType, setSoundType, isSoundEnabled, savePrefs }) {
    const select = document.getElementById('sound-pick');
    if (!select) return;

    select.value = getSoundType();
    select.addEventListener('change', () => {
        const soundType = select.value;
        setSoundType(soundType);
        savePrefs({ soundType });
        ensureAudio();
        beep(isSoundEnabled(), soundType);
    });
}

export function bindSoundToggle({ isSoundEnabled, setSoundEnabled, getSoundType, savePrefs }) {
    const soundEl = document.getElementById('status-sound');
    if (!soundEl) return;

    soundEl.addEventListener('click', () => {
        const enabled = !isSoundEnabled();
        setSoundEnabled(enabled);
        savePrefs({ soundEnabled: enabled });
        renderSoundToggle(enabled);
        ensureAudio();
        beep(enabled, getSoundType());
    });
}
