var ZoomLevel = 1.0;
var LastLogPosition = 0;
var Volume = 1.0;
let isRunning = false;

function switchPane(paneId) {
    document.querySelectorAll('.pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(paneId).classList.add('active');
    adjustLogSectionHeight();
}


function logError(msg){
    const logSection = document.getElementById('log-section');
    logSection.innerHTML += `<hr><span style="color:red">${msg.replace(/\\n/g, '<br>')}</span><hr>`;
}

function adjustZoom(val) {
    ZoomLevel = val;
    document.getElementById('zoom-label').textContent = `Zoom: ${val}x`;
    document.getElementById('zoom').value = val;
    document.body.style.setProperty('zoom', val);
    pywebview.api.set_config('zoom', val);
    adjustLogSectionHeight();
}

function adjustVolume(val) {
    Volume = val;
    document.getElementById('volume-label').textContent = `Volume: ${parseInt(val*100)}`;
    document.getElementById('volume').value = val;
    pywebview.api.set_config('volume', val);
    adjustLogSectionHeight();
}

function adjustLogSectionHeight() {
    const logSection = document.getElementById('log-section');
    const containerHeight = window.innerHeight;
    const navbarHeight = document.querySelector('.nav-bar').offsetHeight * ZoomLevel;
    const bottomControlsHeight = document.querySelector('.bottom-controls').offsetHeight * ZoomLevel;

    // Adjust height based on zoom level
    const adjustedHeight = (containerHeight - navbarHeight - bottomControlsHeight - 80) / ZoomLevel;
    console.log(adjustedHeight)
    logSection.style.height = `${adjustedHeight}px`;
}
window.addEventListener('resize', adjustLogSectionHeight);

async function updateLogSection() {{
    const ret = await pywebview.api.get_logs(LastLogPosition);
    const logs = ret['logs'];
    const panel = document.getElementById('log-section');
    let npos = parseInt(ret['pos'] || 0);
    if(LastLogPosition == npos){ return ''; }
    let content = '';
    let tmp = ''
    LastLogPosition = npos;
    console.log(logs);
    for(let line of logs.split(/[\r\n]+/)){
        var cls = '';
        if(line.includes('[ERROR]')){cls = 'error';}
        if(line.includes('[WARNING]')){cls = 'warning';}
        if(line.includes('[INFO]')){cls = 'info';}
        if(line.includes('[DEBUG]')){cls = 'debug';}
        if(cls && tmp){ content += tmp + '</p>'; tmp = ''; }
        if(!tmp){ tmp = `<p class="${cls}">${line}`; }
        else{ tmp += `<br>${line}`}
    }
    panel.innerHTML += content+tmp;
    if(document.getElementById('autoscroll').checked){
        panel.scrollTop = panel.scrollHeight;
    }
    pywebview.api.set_config('last_log_pos', LastLogPosition);
    return content;
}}

async function fetchAudioDevices(pref_input_index=null, pref_output_index=null) {
    try {{
        const devices = await pywebview.api.get_devices();
        const inputList = document.getElementById('audio-input');
        const outputList = document.getElementById('audio-output');
        inputList.innerHTML = '';
        outputList.innerHTML = '';
        console.log(`Fetched devices: ${devices.length}`)
        for(let d of devices){
            if(d.defaultSampleRate != 44100){ continue; }
            const option = document.createElement('option');
            option.value = `${d.index}`;
            option.textContent = `${d.name} (${d.defaultSampleRate}Hz, ${d.maxInputChannels|d.maxOutputChannels} channels)`;
            if (d.maxInputChannels > 0) {
                inputList.appendChild(option.cloneNode(true));
            }
            if (d.maxOutputChannels > 0) {
                outputList.appendChild(option.cloneNode(true));
            }
        }
        if(pref_input_index){ inputList.value = pref_input_index; }
        if(pref_output_index){ outputList.value = pref_output_index; }
    }} catch (error) {{
        logError("Error fetching log content:", error);
    }}
}

function setAudioInputDevice(val) {
    let node = document.getElementById('audio-input');
    node.disabled = true;
    setTimeout(() => {
        node.disabled = false;
    }, 1000);
    pywebview.api.set_config('audio_input', val);
}

function setAudioOutputDevice(val) {
    let node = document.getElementById('audio-output');
    node.disabled = true;
    setTimeout(() => {
        node.disabled = false;
    }, 1000);
    pywebview.api.set_config('audio_output', val);
}

function setTriggerThreshold(i, v){
    pywebview.api.set_config(`fish_threshold_${i}`, v);
}

function setPlayback(v){
    pywebview.api.set_config(`playback`, !!v);
}

function init(){
    document.getElementById('start-stop').addEventListener('click', toggleRunning);
    adjustLogSectionHeight();
    generateThresholdSettings()
    setup();
}

function toggleRunning(){
    isRunning = !isRunning;
    document.getElementById('start-stop').textContent = isRunning ? 'Stop' : 'Start';
    if (isRunning) {
        pywebview.api.start_fishing();
    } else {
        pywebview.api.stop_fishing();
    }
}

async function setup(){
    try{
        pywebview;
    } catch {
        return setTimeout(setup, 100);
    }
    const config = await pywebview.api.get_config();
    console.log(config);
    adjustZoom(parseFloat(config.zoom));
    adjustVolume(parseFloat(config.volume));
    fetchAudioDevices(config.audio_input, config.audio_output);
    for(let i=1;i<=5;++i){
        document.getElementById(`inp_threshold_${i}l`).value = parseInt(config[`fish_threshold_${i}l`] || 0);
        document.getElementById(`inp_threshold_${i}h`).value = parseInt(config[`fish_threshold_${i}h`] || 0);
    }
    LastLogPosition = config.last_log_pos || 0;
    document.getElementById('playback').checked = config.playback;
    setInterval(updateLogSection, 1000);
}

function generateThresholdSettings(){
    const triggerSettings = document.getElementById('threshold-settings');
    for (let i = 1; i <= 5; i++) {
        const p = document.createElement('p');
        p.innerHTML = `
            ${i}.
            <input id="inp_threshold_${i}l" oninput="setTriggerThreshold('${i}l', this.value)" style="width:120px" type="number" min="0" max="1000000" value="0" />
            ～
            <input id="inp_threshold_${i}h" oninput="setTriggerThreshold('${i}h', this.value)" style="width:120px" type="number" min="0" max="1000000" value="0" />
        `;
        triggerSettings.appendChild(p);
    }
}

window.addEventListener('load', init);