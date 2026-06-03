let currentSpeed = 60;
let lastDriveState = { command: 'stop', speed: 0 };
const joystickState = { active: false, maxRadius: 92 };

function updateDriveStatus(command, speed) {
    const directionEl = document.getElementById('drive-direction');
    const speedEl = document.getElementById('drive-speed');
    if (directionEl) directionEl.textContent = command.toUpperCase().replace('-', ' ');
    if (speedEl) speedEl.textContent = `${speed}%`;
}

function sendDriveCommand(command, speed) {
    const normalized = command === 'stop' ? 'stop' : String(command).trim().toLowerCase();
    const speedValue = normalized === 'stop' ? 0 : Math.max(0, Math.min(100, parseInt(speed, 10) || currentSpeed));
    const payload = { command: normalized, speed: speedValue };

    if (lastDriveState.command === payload.command && lastDriveState.speed === payload.speed) {
        return;
    }

    if (typeof socket !== 'undefined' && socket && socket.emit) {
        socket.emit('drive_command', payload, (response) => {
            if (response && response.status === 'ok') {
                updateDriveStatus(payload.command, payload.speed);
            } else {
                console.warn('Drive command error', response);
            }
        });
    }

    lastDriveState = payload;
    currentSpeed = speedValue;
}

function applyJoystickPosition(x, y) {
    const stick = document.getElementById('joystick-stick');
    if (!stick) return;

    const distance = Math.min(joystickState.maxRadius, Math.hypot(x, y));
    const angle = Math.atan2(y, x);
    const dx = Math.cos(angle) * distance;
    const dy = Math.sin(angle) * distance;
    stick.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;

    if (distance < 16) {
        sendDriveCommand('stop', 0);
        return;
    }

    const normalizedX = dx / joystickState.maxRadius;
    const normalizedY = -dy / joystickState.maxRadius;
    let command;

    if (Math.abs(normalizedY) >= Math.abs(normalizedX)) {
        command = normalizedY > 0 ? 'forward' : 'backward';
    } else {
        command = normalizedX > 0 ? 'right' : 'left';
    }

    const speed = Math.round(Math.min(100, Math.hypot(normalizedX, normalizedY) * 100));
    sendDriveCommand(command, speed);
}

function initJoystickWindow() {
    const frame = document.getElementById('joystick-frame');
    const stick = document.getElementById('joystick-stick');
    const speedSlider = document.getElementById('speed-slider');
    if (!frame || !stick) return;

    if (speedSlider) {
        currentSpeed = parseInt(speedSlider.value, 10) || 60;
        speedSlider.addEventListener('input', (event) => {
            currentSpeed = Math.max(0, Math.min(100, parseInt(event.target.value, 10) || 0));
            updateDriveStatus(lastDriveState.command, currentSpeed);
        });
    }

    frame.addEventListener('pointerdown', (event) => {
        joystickState.active = true;
        stick.setPointerCapture(event.pointerId);
        stick.classList.add('active');
    });

    frame.addEventListener('pointermove', (event) => {
        if (!joystickState.active) return;
        const rect = frame.getBoundingClientRect();
        const x = event.clientX - rect.left - rect.width / 2;
        const y = event.clientY - rect.top - rect.height / 2;
        applyJoystickPosition(x, y);
    });

    const releaseJoystick = () => {
        if (!joystickState.active) return;
        joystickState.active = false;
        stick.classList.remove('active');
        stick.style.transform = 'translate(-50%, -50%)';
        sendDriveCommand('stop', 0);
    };

    frame.addEventListener('pointerup', releaseJoystick);
    frame.addEventListener('pointercancel', releaseJoystick);
    frame.addEventListener('pointerleave', releaseJoystick);
    document.addEventListener('pointerup', releaseJoystick);
}
