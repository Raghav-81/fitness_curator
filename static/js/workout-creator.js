/**
 * Workout Creator JavaScript
 * Handles workout plan creation with drag-and-drop, video library integration
 */

// State management
const workoutCreatorState = {
    clients: [],
    videos: [],
    filteredVideos: [],
    exercises: [],
    selectedClient: null,
    exerciseCounter: 0
};

// Initialize workout creator
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('workout-creator-section')) {
        initWorkoutCreator();
    }
});

async function initWorkoutCreator() {
    await loadClients();
    await loadVideos();
    setupEventListeners();
    initializeSortable();
}

// Load clients from API
async function loadClients() {
    try {
        const response = await fetch('/api/clients');
        if (response.ok) {
            workoutCreatorState.clients = await response.json();
            populateClientDropdown();
        }
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

// Load videos from API
async function loadVideos() {
    try {
        const response = await fetch('/api/videos');
        if (response.ok) {
            workoutCreatorState.videos = await response.json();
            workoutCreatorState.filteredVideos = [...workoutCreatorState.videos];
            displayVideoLibrary();
        }
    } catch (error) {
        console.error('Error loading videos:', error);
    }
}

// Populate client dropdown
function populateClientDropdown() {
    const select = document.getElementById('plan-client-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">Select a client...</option>';
    
    workoutCreatorState.clients.forEach(client => {
        const option = document.createElement('option');
        option.value = client.id;
        option.textContent = `${client.name} (${client.email})`;
        select.appendChild(option);
    });
}

// Display video library
function displayVideoLibrary() {
    const container = document.getElementById('video-library-list');
    if (!container) return;
    
    if (workoutCreatorState.filteredVideos.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-video-slash"></i>
                <h3>No videos found</h3>
                <p>Try adjusting your search filters</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = workoutCreatorState.filteredVideos.map(video => `
        <div class="video-library-item" data-video-id="${video.id}" onclick="selectVideo(${video.id})">
            <div class="video-item-header">
                <div class="video-item-icon">
                    <i class="fas fa-play"></i>
                </div>
                <div class="video-item-title">${video.title}</div>
            </div>
            <div class="video-item-meta">
                ${video.category ? `<span class="video-badge badge-category">${video.category}</span>` : ''}
                ${video.difficulty_level ? `<span class="video-badge badge-difficulty">${video.difficulty_level}</span>` : ''}
            </div>
        </div>
    `).join('');
}

// Select video from library
function selectVideo(videoId) {
    const video = workoutCreatorState.videos.find(v => v.id === videoId);
    if (!video) return;
    
    // Add to exercises table
    addExerciseRow(video);
    
    // Visual feedback
    showToast('Video added to workout plan', 'success');
}

// Add exercise row to table
function addExerciseRow(video = null) {
    const tbody = document.getElementById('exercises-table-body');
    if (!tbody) return;
    
    const index = workoutCreatorState.exerciseCounter++;
    const row = document.createElement('tr');
    row.className = 'exercise-row animate__animated animate__fadeIn';
    row.dataset.index = index;
    
    row.innerHTML = `
        <td>
            <i class="fas fa-grip-vertical exercise-row-drag-handle"></i>
        </td>
        <td>
            <select class="exercise-input-small exercise-day-select" required>
                <option value="1">Day 1</option>
                <option value="2">Day 2</option>
                <option value="3">Day 3</option>
                <option value="4">Day 4</option>
                <option value="5">Day 5</option>
                <option value="6">Day 6</option>
                <option value="7">Day 7</option>
                <option value="Monday">Mon</option>
                <option value="Tuesday">Tue</option>
                <option value="Wednesday">Wed</option>
                <option value="Thursday">Thu</option>
                <option value="Friday">Fri</option>
                <option value="Saturday">Sat</option>
                <option value="Sunday">Sun</option>
            </select>
        </td>
        <td>
            <div class="exercise-video-preview">
                ${video ? `
                    <div class="exercise-video-thumb" onclick="previewVideo(${video.id})">
                        <i class="fas fa-play"></i>
                    </div>
                    <div class="exercise-video-name">${video.title}</div>
                    <input type="hidden" class="exercise-video-id" value="${video.id}">
                ` : `
                    <button class="btn-secondary" onclick="openVideoSelector(${index})">
                        <i class="fas fa-plus"></i> Select Video
                    </button>
                `}
            </div>
        </td>
        <td>
            <input type="number" class="exercise-input-small exercise-sets" placeholder="3" min="1" max="10">
        </td>
        <td>
            <input type="text" class="exercise-input-small exercise-reps" placeholder="10">
        </td>
        <td>
            <input type="text" class="exercise-input-medium exercise-notes" placeholder="Add notes...">
        </td>
        <td>
            <button class="btn-remove-exercise" onclick="removeExerciseRow(${index})">
                <i class="fas fa-times"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
    
    // Store exercise data
    workoutCreatorState.exercises.push({
        index,
        video: video,
        row: row
    });
}

// Remove exercise row
function removeExerciseRow(index) {
    const row = document.querySelector(`tr[data-index="${index}"]`);
    if (row) {
        row.classList.add('animate__animated', 'animate__fadeOut');
        setTimeout(() => {
            row.remove();
            workoutCreatorState.exercises = workoutCreatorState.exercises.filter(e => e.index !== index);
        }, 300);
    }
}

// Preview video in modal
function previewVideo(videoId) {
    const video = workoutCreatorState.videos.find(v => v.id === videoId);
    if (!video) return;
    
    // Reuse existing video modal from index.html
    if (typeof openVideoModal === 'function') {
        const videoIndex = workoutCreatorState.videos.findIndex(v => v.id === videoId);
        window.currentVideos = workoutCreatorState.videos;
        openVideoModal(videoIndex);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Video search
    const searchInput = document.getElementById('video-library-search');
    if (searchInput) {
        searchInput.addEventListener('input', filterVideos);
    }
    
    // Category filter
    const categoryFilter = document.getElementById('video-library-category');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterVideos);
    }
    
    // Add exercise button
    const addExerciseBtn = document.getElementById('add-exercise-btn');
    if (addExerciseBtn) {
        addExerciseBtn.addEventListener('click', () => addExerciseRow());
    }
    
    // Save plan button
    const savePlanBtn = document.getElementById('save-plan-btn');
    if (savePlanBtn) {
        savePlanBtn.addEventListener('click', saveWorkoutPlan);
    }
    
    // Toggle video panel
    const toggleBtn = document.getElementById('toggle-video-panel-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleVideoPanel);
    }
    
    // Create new client button
    const newClientBtn = document.getElementById('new-client-btn');
    if (newClientBtn) {
        newClientBtn.addEventListener('click', openClientModal);
    }
}

// Filter videos
function filterVideos() {
    const searchTerm = document.getElementById('video-library-search')?.value.toLowerCase() || '';
    const category = document.getElementById('video-library-category')?.value || '';
    
    workoutCreatorState.filteredVideos = workoutCreatorState.videos.filter(video => {
        const matchesSearch = video.title.toLowerCase().includes(searchTerm) ||
                            (video.description && video.description.toLowerCase().includes(searchTerm));
        const matchesCategory = !category || video.category === category;
        
        return matchesSearch && matchesCategory;
    });
    
    displayVideoLibrary();
}

// Toggle video panel
function toggleVideoPanel() {
    const panel = document.querySelector('.creator-video-panel');
    const btn = document.getElementById('toggle-video-panel-btn');
    
    if (panel) {
        panel.classList.toggle('collapsed');
        btn.innerHTML = panel.classList.contains('collapsed') ? 
            '<i class="fas fa-chevron-left"></i>' : 
            '<i class="fas fa-chevron-right"></i>';
    }
}

// Save workout plan
async function saveWorkoutPlan() {
    const saveBtnEl = document.getElementById('save-plan-btn');
    const originalHTML = saveBtnEl.innerHTML;
    
    try {
        // Show loading state
        saveBtnEl.disabled = true;
        saveBtnEl.innerHTML = '<span class="loading-spinner"></span> Saving...';
        
        // Collect form data
        const clientId = document.getElementById('plan-client-select')?.value;
        const planName = document.getElementById('plan-name')?.value;
        const description = document.getElementById('plan-description')?.value;
        const startDate = document.getElementById('plan-start-date')?.value;
        const endDate = document.getElementById('plan-end-date')?.value;
        const isTemplate = document.getElementById('plan-is-template')?.checked || false;
        const dayType = document.getElementById('plan-day-type')?.value || 'day_number';
        
        // Validate
        if (!clientId) {
            showToast('Please select a client', 'error');
            return;
        }
        
        if (!planName) {
            showToast('Please enter a plan name', 'error');
            return;
        }
        
        // Collect exercises
        const exercises = [];
        const rows = document.querySelectorAll('.exercise-row');
        
        rows.forEach((row, index) => {
            const videoId = row.querySelector('.exercise-video-id')?.value;
            const day = row.querySelector('.exercise-day-select')?.value;
            const sets = row.querySelector('.exercise-sets')?.value;
            const reps = row.querySelector('.exercise-reps')?.value;
            const notes = row.querySelector('.exercise-notes')?.value;
            
            if (videoId) {
                exercises.push({
                    video_id: parseInt(videoId),
                    day: day,
                    sets: sets ? parseInt(sets) : null,
                    reps: reps || null,
                    notes: notes || null,
                    order_index: index
                });
            }
        });
        
        if (exercises.length === 0) {
            showToast('Please add at least one exercise', 'error');
            return;
        }
        
        // Create plan object
        const planData = {
            client_id: parseInt(clientId),
            plan_name: planName,
            description: description || null,
            start_date: startDate || null,
            end_date: endDate || null,
            is_template: isTemplate,
            day_type: dayType,
            exercises: exercises
        };
        
        // Send to API
        const response = await fetch('/api/workout-plans', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(planData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save workout plan');
        }
        
        const savedPlan = await response.json();
        
        // Show success message with share link
        showToast('Workout plan saved successfully!', 'success');
        
        // Show share link modal
        showShareLinkModal(savedPlan);
        
        // Reset form
        setTimeout(() => {
            resetWorkoutCreatorForm();
        }, 2000);
        
    } catch (error) {
        console.error('Error saving workout plan:', error);
        showToast('Failed to save workout plan: ' + error.message, 'error');
    } finally {
        saveBtnEl.disabled = false;
        saveBtnEl.innerHTML = originalHTML;
    }
}

// Show share link modal
function showShareLinkModal(plan) {
    const shareUrl = `${window.location.origin}/workout-plan/${plan.share_token}`;
    
    const modal = document.createElement('div');
    modal.className = 'modal active animate__animated animate__fadeIn';
    modal.innerHTML = `
        <div class="modal-content animate__animated animate__zoomIn">
            <div class="modal-header">
                <h3><i class="fas fa-share-alt"></i> Workout Plan Created!</h3>
                <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="margin-bottom: 15px;">Share this link with your client:</p>
                <div style="display: flex; gap: 10px;">
                    <input type="text" value="${shareUrl}" id="share-link-input" 
                           style="flex: 1; padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px;" readonly>
                    <button class="btn-primary" onclick="copyShareLink()" style="flex: 0 0 auto;">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
                <p style="margin-top: 15px; font-size: 0.9rem; color: #666;">
                    <i class="fas fa-info-circle"></i> Your client can use this link to view and track their workout plan.
                </p>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Copy share link
function copyShareLink() {
    const input = document.getElementById('share-link-input');
    input.select();
    document.execCommand('copy');
    showToast('Link copied to clipboard!', 'success');
}

// Reset form
function resetWorkoutCreatorForm() {
    document.getElementById('plan-client-select').value = '';
    document.getElementById('plan-name').value = '';
    document.getElementById('plan-description').value = '';
    document.getElementById('plan-start-date').value = '';
    document.getElementById('plan-end-date').value = '';
    document.getElementById('plan-is-template').checked = false;
    
    // Clear exercises
    document.getElementById('exercises-table-body').innerHTML = '';
    workoutCreatorState.exercises = [];
    workoutCreatorState.exerciseCounter = 0;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type} animate__animated animate__slideInRight`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('animate__slideInRight');
        toast.classList.add('animate__slideOutRight');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize Sortable.js for drag-and-drop
function initializeSortable() {
    const tbody = document.getElementById('exercises-table-body');
    if (tbody && typeof Sortable !== 'undefined') {
        new Sortable(tbody, {
            animation: 150,
            handle: '.exercise-row-drag-handle',
            ghostClass: 'dragging',
            onEnd: function() {
                // Update order indices
                const rows = tbody.querySelectorAll('.exercise-row');
                rows.forEach((row, index) => {
                    row.dataset.orderIndex = index;
                });
            }
        });
    }
}

// Open client modal (to be implemented)
function openClientModal() {
    showToast('Client creation modal coming soon!', 'info');
    // TODO: Implement client creation modal
}
