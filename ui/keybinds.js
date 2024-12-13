document.addEventListener('keydown', function(event) {
    switch (event.key) {
        case 'F6':
            console.log('F6 pressed');
            event.preventDefault();
            pywebview.api.export_audio_wave();
            break;
        case 'F7':
            console.log('F7 pressed');
            event.preventDefault();
            pywebview.api.pause();
            break;
        case 'F8':
            console.log('F8 pressed');
            event.preventDefault();
            toggleRunning();
            break;
        default:
            break;
    }
});
