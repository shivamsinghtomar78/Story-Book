 
document.addEventListener('DOMContentLoaded', function() {
    const storyForm = document.getElementById('storyForm');
    if (!storyForm) return; // Only run on pages with the story form

    storyForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const prompt = document.getElementById('prompt').value;
        const length = document.getElementById('length').value;
        
        // Show progress
        const progressCard = document.getElementById('progressCard');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const generateBtn = document.getElementById('generateBtn');
        const spinner = document.getElementById('spinner');
        const generateText = document.getElementById('generateText');
        
        progressCard.classList.remove('d-none');
        generateBtn.disabled = true;
        spinner.classList.remove('d-none');
        generateText.textContent = 'Generating...';
        
        try {
            // Generate story
            progressText.textContent = 'Creating your magical story...';
            progressBar.style.width = '25%';
            
            // Update progress
            progressBar.style.width = '25%';
            progressText.textContent = 'Generating story text...';
            
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt, length })
            });
            
            progressBar.style.width = '50%';
            progressText.textContent = 'Creating illustrations...';
            
            if (!response.ok) {
                throw new Error('Story generation failed');
            }
            
            const data = await response.json();
            
            if (data.success) {
                progressBar.style.width = '100%';
                progressText.textContent = 'Story is ready!';
                
                // Show results
                const resultsCard = document.getElementById('resultsCard');
                resultsCard.classList.remove('d-none');
                
                // Update download links with proper URLs
                const storyId = data.story_id;
                const downloadBtn = document.getElementById('downloadBtn');
                const audiobookBtn = document.getElementById('audiobookBtn');
                const readerBtn = document.getElementById('readerBtn');
                
                downloadBtn.href = `/download-pdf/${storyId}`;
                audiobookBtn.href = `/download-audiobook/${storyId}`;
                readerBtn.href = `/reader/${storyId}`;
                
                // Enable buttons
                downloadBtn.classList.remove('disabled');
                audiobookBtn.classList.remove('disabled');
                readerBtn.classList.remove('disabled');
                
                // Add click handler for reader button
                readerBtn.onclick = (e) => {
                    e.preventDefault();
                    window.location.href = `/reader/${storyId}`;
                };
                
                // Scroll to results
                resultsCard.scrollIntoView({ behavior: 'smooth' });
            } else {
                throw new Error(data.error || 'Story generation failed');
            }
        } catch (error) {
            // Show error
            const errorAlert = document.getElementById('errorAlert');
            const errorMessage = document.getElementById('errorMessage');
            errorAlert.classList.remove('d-none');
            errorMessage.textContent = error.message || 'Something went wrong. Please try again.';
            errorAlert.scrollIntoView({ behavior: 'smooth' });
        } finally {
            // Reset form state
            progressCard.classList.add('d-none');
            generateBtn.disabled = false;
            spinner.classList.add('d-none');
            generateText.textContent = '🎨 Generate My Storybook';
        }
    });
});
