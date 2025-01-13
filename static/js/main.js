document.addEventListener('DOMContentLoaded', function() {
    // Video Player Controls
    document.querySelectorAll('.video-wrapper').forEach(wrapper => {
        const video = wrapper.querySelector('video');
        const playPauseBtn = wrapper.querySelector('.play-pause-btn');
        const volumeBtn = wrapper.querySelector('.volume-btn');
        const progressBar = wrapper.querySelector('.progress-bar');
        const progressFilled = wrapper.querySelector('.progress-filled');
        const timeDisplay = wrapper.querySelector('.progress-time');

        // Format time in MM:SS
        function formatTime(seconds) {
            const minutes = Math.floor(seconds / 60);
            seconds = Math.floor(seconds % 60);
            return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        // Update progress bar and time display
        function updateProgress() {
            const percent = (video.currentTime / video.duration) * 100;
            progressFilled.style.width = `${percent}%`;
            timeDisplay.textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
        }

        // Skip to clicked position
        function scrub(e) {
            const scrubTime = (e.offsetX / progressBar.offsetWidth) * video.duration;
            video.currentTime = scrubTime;
        }

        // Play/Pause functionality
        playPauseBtn.addEventListener('click', () => {
            if (video.paused) {
                video.play();
                playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
            } else {
                video.pause();
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
            }
        });

        // Volume control
        volumeBtn.addEventListener('click', () => {
            video.muted = !video.muted;
            volumeBtn.innerHTML = video.muted ? 
                '<i class="fas fa-volume-mute"></i>' : 
                '<i class="fas fa-volume-up"></i>';
        });

        // Progress bar controls
        let mousedown = false;
        progressBar.addEventListener('click', scrub);
        progressBar.addEventListener('mousemove', (e) => mousedown && scrub(e));
        progressBar.addEventListener('mousedown', () => mousedown = true);
        progressBar.addEventListener('mouseup', () => mousedown = false);
        progressBar.addEventListener('mouseleave', () => mousedown = false);

        // Update progress
        video.addEventListener('timeupdate', updateProgress);
        video.addEventListener('loadedmetadata', updateProgress);

        // Autoplay when in view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    video.play();
                    playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
                } else {
                    video.pause();
                    playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
                }
            });
        }, { threshold: 0.5 });

        observer.observe(wrapper);
    });

    // Comments Section
    document.querySelectorAll('.comment-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Close any other open comments section
            document.querySelectorAll('.comments-section.active').forEach(section => {
                if (section !== btn.closest('.video-card').querySelector('.comments-section')) {
                    section.classList.remove('active');
                }
            });
            
            // Toggle current comments section
            const commentsSection = btn.closest('.video-card').querySelector('.comments-section');
            commentsSection.classList.toggle('active');
        });
    });

    // Close comments button
    document.querySelectorAll('.close-comments').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.comments-section').classList.remove('active');
        });
    });

    // Async Comment Form Submission
    document.querySelectorAll('.comment-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const videoId = form.dataset.videoId;
            const input = form.querySelector('input[name="content"]');
            const content = input.value;

            try {
                const response = await fetch(`/add_comment/${videoId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: content })
                });

                if (response.ok) {
                    const data = await response.json();
                    const commentsList = form.closest('.comments-section').querySelector('.comments-list');
                    
                    // Create new comment element
                    const commentElement = document.createElement('div');
                    commentElement.className = 'comment';
                    commentElement.innerHTML = `
                        <img src="${data.user.profile_pic}" alt="Profile Picture">
                        <div class="comment-content">
                            <a href="/profile/${data.user.username}" class="username">${data.user.username}</a>
                            <p>${data.content}</p>
                            <span class="timestamp">${new Date(data.timestamp).toLocaleString()}</span>
                        </div>
                    `;
                    
                    // Add new comment to the top of the list
                    commentsList.insertBefore(commentElement, commentsList.firstChild);
                    
                    // Update comment count
                    const countElement = form.closest('.video-card').querySelector('.comment-btn .count');
                    countElement.textContent = parseInt(countElement.textContent) + 1;
                    
                    // Clear input
                    input.value = '';
                    
                    // Update header count
                    const headerCount = form.closest('.comments-section').querySelector('.comments-header h4');
                    const currentCount = parseInt(headerCount.textContent.match(/\d+/)[0]);
                    headerCount.textContent = `Comments (${currentCount + 1})`;
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });

    // Like functionality
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const videoId = btn.dataset.videoId;
            const response = await fetch(`/like/${videoId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            const countSpan = btn.querySelector('.count');
            countSpan.textContent = data.likes;
            
            if (data.action === 'liked') {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    });

    // Infinite scroll
    const loadMore = document.querySelector('.load-more');
    if (loadMore) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    loadMoreVideos();
                }
            });
        });

        observer.observe(loadMore);
    }

    async function loadMoreVideos() {
        const page = loadMore.dataset.page;
        const response = await fetch(`/?page=${page}`);
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newVideos = doc.querySelectorAll('.video-container');
        
        newVideos.forEach(video => {
            document.querySelector('.video-feed').insertBefore(video, loadMore);
        });

        const nextPage = doc.querySelector('.load-more')?.dataset.page;
        if (nextPage) {
            loadMore.dataset.page = nextPage;
        } else {
            loadMore.remove();
        }
    }
});
