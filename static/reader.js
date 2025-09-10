 
let currentPage = 1;
let isPlaying = false;
let isAutoPlaying = false;

// Initialize story on page load
document.addEventListener('DOMContentLoaded', function() {
    // Story data is already loaded in the template
    if (!window.storyData) {
        StorybookUtils.showNotification('No story data available', 'danger');
        return;
    }

    try {
        // Initialize first page
        updatePage(1);
        
        // Setup audio ended event for auto-play
        const audio = document.getElementById('pageAudio');
        audio.addEventListener('ended', function() {
            if (isAutoPlaying && currentPage < window.storyData.pages.length) {
                changePage(1);
            } else {
                isPlaying = false;
                updatePlayButton();
            }
        });

        // Setup progress tracking
        audio.addEventListener('timeupdate', updateAudioProgress);
    } catch (error) {
        StorybookUtils.showNotification('Failed to load story', 'danger');
    }
});

function changePage(delta) {
    const newPage = currentPage + delta;
    if (newPage >= 1 && newPage <= window.storyData.pages.length) {
        stopAudio();
        currentPage = newPage;
        updatePage(currentPage);
        
        // Auto-play audio if enabled
        if (isAutoPlaying) {
            setTimeout(toggleAudio, 500);
        }
    }
}

function updatePage(pageNum) {
    try {
        console.log("Updating page", pageNum);
        console.log("Story data:", window.storyData);
        console.log("Image paths:", window.imagePaths);
        console.log("Audio paths:", window.audioPaths);
        
        // Update text
        const pageText = document.getElementById('pageText');
        if (window.storyData && window.storyData.pages) {
            pageText.textContent = window.storyData.pages[pageNum - 1].text;
        } else {
            console.error("Invalid story data structure");
            return;
        }
        
        // Update image
        const pageImage = document.getElementById('pageImage');
        pageImage.style.display = 'none'; // Hide by default
        if (window.imagePaths && window.imagePaths[pageNum - 1]) {
            const imagePath = window.imagePaths[pageNum - 1];
            if (imagePath) {
                pageImage.src = '/image/' + imagePath;
                pageImage.style.display = 'block';
            }
        }
        
        // Update audio source
        const pageAudio = document.getElementById('pageAudio');
        if (window.audioPaths && window.audioPaths[pageNum - 1]) {
            const audioPath = window.audioPaths[pageNum - 1];
            if (audioPath) {
                pageAudio.src = '/audio/' + audioPath;
            } else {
                pageAudio.src = '';
            }
        } else {
            pageAudio.src = '';
        }
    } catch (error) {
        console.error('Error updating page:', error);
        StorybookUtils.showNotification('Error loading page content', 'danger');
    }
    
    // Update page number
    document.getElementById('pageNumber').textContent = `Page ${pageNum} of ${window.storyData.pages.length}`;
    
    // Update progress bar
    const progress = (pageNum / window.storyData.pages.length) * 100;
    document.getElementById('progressBar').style.width = `${progress}%`;
    document.getElementById('progressPercent').textContent = `${Math.round(progress)}%`;
    
    // Update navigation buttons
    document.getElementById('prevBtn').disabled = pageNum === 1;
    document.getElementById('nextBtn').disabled = pageNum === window.storyData.pages.length;
}

function toggleAudio() {
    const audio = document.getElementById('pageAudio');
    const playBtn = document.getElementById('playBtn');
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');
    const stopBtn = document.getElementById('stopBtn');
    const audioProgress = document.getElementById('audioProgress');
    
    if (!isPlaying) {
        audio.play().then(() => {
            isPlaying = true;
            playIcon.textContent = '⏸️';
            playText.textContent = 'Pause';
            stopBtn.style.display = 'inline-block';
            audioProgress.style.display = 'block';
        }).catch(error => {
            StorybookUtils.showNotification('Failed to play audio', 'danger');
        });
    } else {
        audio.pause();
        isPlaying = false;
        playIcon.textContent = '🔊';
        playText.textContent = 'Listen to Page';
    }
}

function stopAudio() {
    const audio = document.getElementById('pageAudio');
    audio.pause();
    audio.currentTime = 0;
    isPlaying = false;
    updatePlayButton();
    document.getElementById('stopBtn').style.display = 'none';
    document.getElementById('audioProgress').style.display = 'none';
}

function toggleAutoPlay() {
    isAutoPlaying = !isAutoPlaying;
    const icon = document.getElementById('autoPlayIcon');
    icon.textContent = isAutoPlaying ? '⏹️' : '⏯️';
    
    if (isAutoPlaying && !isPlaying) {
        toggleAudio();
    }
}

function togglePlayAll() {
    const playAllBtn = document.getElementById('playAllBtn');
    const playAllIcon = document.getElementById('playAllIcon');
    const playAllText = document.getElementById('playAllText');
    
    if (!isPlaying) {
        currentPage = 1;
        updatePage(currentPage);
        isAutoPlaying = true;
        document.getElementById('autoPlayIcon').textContent = '⏹️';
        toggleAudio();
        playAllIcon.textContent = '⏹️';
        playAllText.textContent = 'Stop Story';
    } else {
        stopAudio();
        isAutoPlaying = false;
        document.getElementById('autoPlayIcon').textContent = '⏯️';
        playAllIcon.textContent = '🎵';
        playAllText.textContent = 'Play Full Story';
    }
}

function updatePlayButton() {
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');
    
    playIcon.textContent = isPlaying ? '⏸️' : '🔊';
    playText.textContent = isPlaying ? 'Pause' : 'Listen to Page';
}

function updateAudioProgress() {
    const audio = document.getElementById('pageAudio');
    const progressBar = document.getElementById('audioProgressBar');
    const currentTime = document.getElementById('audioCurrentTime');
    const duration = document.getElementById('audioDuration');
    
    if (audio.duration) {
        const progress = (audio.currentTime / audio.duration) * 100;
        progressBar.style.width = `${progress}%`;
        currentTime.textContent = StorybookUtils.formatTime(audio.currentTime);
        duration.textContent = StorybookUtils.formatTime(audio.duration);
    }
}

function enlargeImage() {
    const image = document.getElementById('pageImage');
    if (!document.fullscreenElement) {
        if (image.requestFullscreen) {
            image.requestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}
