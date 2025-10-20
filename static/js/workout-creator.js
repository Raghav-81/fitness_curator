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
    exerciseCounter: 0,
    dayFormat: 'day_number',
    currentPlanId: null  // Track if editing existing plan
};  // 'day_number' or 'day_of_week'

// Initialize workout creator
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('workout-creator-section')) {
        initWorkoutCreator();
    }
});

// Initialize workout creator
function initWorkoutCreator() {
    loadClients();
    loadVideos();
    setupEventListeners();
    initializeDragAndDrop();
}

// Initialize drag-and-drop for exercise tables
function initializeDragAndDrop() {
    const sections = ['warmup', 'main', 'cooldown'];
    
    sections.forEach(section => {
        const tbody = document.getElementById(`${section}-table-body`);
        if (tbody && typeof Sortable !== 'undefined') {
            Sortable.create(tbody, {
                animation: 150,
                handle: '.exercise-row-drag-handle',
                ghostClass: 'sortable-ghost',
                onEnd: function() {
                    window.toast.success('✅ Exercise order updated');
                }
            });
        }
    });
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

// Load existing plans for selected client
window.loadClientPlans = async function(clientId) {
    const container = document.getElementById('existing-plans-container');
    const select = document.getElementById('existing-plan-select');
    
    if (!clientId) {
        container.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/workout-plans?client_id=${clientId}`);
        const plans = await response.json();
        
        if (plans.length > 0) {
            select.innerHTML = '<option value="">Create New Plan</option>';
            plans.forEach(plan => {
                const option = document.createElement('option');
                option.value = plan.id;
                option.textContent = `${plan.plan_name} (${plan.created_at ? new Date(plan.created_at).toLocaleDateString() : 'N/A'})`;
                select.appendChild(option);
            });
            container.style.display = 'block';
        } else {
            container.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading client plans:', error);
    }
};

// Load plan data into form for editing
window.loadPlanToEdit = async function(planId) {
    const deleteBtn = document.getElementById('delete-plan-btn');
    
    if (!planId) {
        // Reset form if "Create New Plan" is selected
        resetWorkoutCreatorForm();
        workoutCreatorState.currentPlanId = null;
        if (deleteBtn) deleteBtn.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/workout-plans/${planId}`);
        const plan = await response.json();
        
        // Store the plan ID for updating
        workoutCreatorState.currentPlanId = plan.id;
        
        // Show delete button
        if (deleteBtn) deleteBtn.style.display = 'block';
        
        // Populate form fields
        document.getElementById('plan-name').value = plan.plan_name || '';
        document.getElementById('plan-description').value = plan.description || '';
        document.getElementById('plan-start-date').value = plan.start_date ? plan.start_date.split('T')[0] : '';
        document.getElementById('plan-end-date').value = plan.end_date ? plan.end_date.split('T')[0] : '';
        
        // Set day format
        const dayTypeInput = document.getElementById('plan-day-type');
        if (dayTypeInput) {
            dayTypeInput.value = plan.day_type || 'day_number';
            setDayFormat(plan.day_type || 'day_number');
        }
        
        // Clear existing exercises
        ['warmup', 'main', 'cooldown'].forEach(section => {
            const tbody = document.getElementById(`${section}-table-body`);
            if (tbody) tbody.innerHTML = '';
        });
        
        // Add exercises to appropriate sections
        if (plan.exercises && plan.exercises.length > 0) {
            plan.exercises.forEach(exercise => {
                const section = exercise.section || 'main';
                
                if (exercise.is_custom) {
                    // Add custom exercise
                    const customExercise = {
                        is_custom: true,
                        custom_name: exercise.custom_name,
                        custom_youtube_url: exercise.custom_youtube_url,
                        custom_equipment: exercise.custom_equipment
                    };
                    addExerciseRow(customExercise, section, exercise);
                } else if (exercise.video_id) {
                    // Find video from loaded videos
                    const video = workoutCreatorState.videos.find(v => v.id === exercise.video_id);
                    if (video) {
                        addExerciseRow(video, section, exercise);
                    }
                }
            });
        }
        
        window.toast.success(`📝 Loaded plan: ${plan.plan_name}`);
        
    } catch (error) {
        console.error('Error loading plan:', error);
        window.toast.error('Failed to load plan: ' + error.message);
    }
};

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
    
    // Show modal to select which section to add to
    const modalContent = `
        <h3 style="margin-bottom: 20px; color: #333;">Add to which section?</h3>
        <p style="margin-bottom: 20px; color: #666;">Choose where to add <strong>${video.title}</strong></p>
        <div style="display: flex; flex-direction: column; gap: 12px;">
            <button class="btn-modern btn-fire" onclick="addVideoToSection(${videoId}, 'warmup')" style="justify-content: flex-start; padding: 16px;">
                <i class="fas fa-fire" style="color: #f59e0b;"></i>
                <span>Warmup</span>
            </button>
            <button class="btn-modern btn-fire" onclick="addVideoToSection(${videoId}, 'main')" style="justify-content: flex-start; padding: 16px;">
                <i class="fas fa-dumbbell"></i>
                <span>Main Workout</span>
            </button>
            <button class="btn-modern btn-fire" onclick="addVideoToSection(${videoId}, 'cooldown')" style="justify-content: flex-start; padding: 16px;">
                <i class="fas fa-wind" style="color: #3b82f6;"></i>
                <span>Cooldown</span>
            </button>
        </div>
    `;
    
    window.modal.show(modalContent, { showClose: true });
}

// Add video to specific section
window.addVideoToSection = function(videoId, section) {
    const video = workoutCreatorState.videos.find(v => v.id === videoId);
    if (!video) return;
    
    // Add to specified section
    addExerciseRow(video, section);
    
    // Close modal
    document.querySelector('.modal-modern.active')?.classList.remove('active');
    
    // Visual feedback
    const sectionNames = { warmup: 'Warmup', main: 'Main Workout', cooldown: 'Cooldown' };
    window.toast.success(`✅ Added to ${sectionNames[section]}!`);
};

// Open video selector to change an exercise
window.openVideoSelector = function(rowIndex) {
    // Store the row index we're changing
    workoutCreatorState.changingRowIndex = rowIndex;
    
    // Open the video selection modal
    const modalContent = `
        <h3 style="margin-bottom: 20px;">Select a Video</h3>
        <div style="margin-bottom: 15px;">
            <input type="text" id="change-video-search" placeholder="Search videos..." 
                   style="width: 100%; padding: 10px; border: 2px solid #fed7aa; border-radius: 8px;">
        </div>
        <div style="max-height: 400px; overflow-y: auto; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px;">
            ${workoutCreatorState.filteredVideos.map(video => `
                <div class="premium-card" onclick="changeExerciseVideo(${video.id})" style="cursor: pointer; padding: 15px;">
                    <h4 style="margin: 0 0 8px 0; color: #ff6b35; font-size: 0.95rem;">${video.title}</h4>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">${video.category}</p>
                </div>
            `).join('')}
        </div>
        <div style="margin-top: 20px; text-align: right;">
            <button class="btn-modern btn-outline" onclick="window.modal.close(this.closest('.modal-modern'))">Cancel</button>
        </div>
    `;
    
    window.modal.show(modalContent, { showClose: true });
    
    // Add search functionality
    setTimeout(() => {
        const searchInput = document.getElementById('change-video-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                workoutCreatorState.filteredVideos = workoutCreatorState.videos.filter(v => 
                    v.title.toLowerCase().includes(query) || v.category.toLowerCase().includes(query)
                );
                // Re-render would go here, but for simplicity we'll keep it as is
            });
        }
    }, 100);
};

// Change exercise video
window.changeExerciseVideo = function(videoId) {
    const video = workoutCreatorState.videos.find(v => v.id === videoId);
    if (!video || workoutCreatorState.changingRowIndex === undefined) return;
    
    // Find the row
    const allRows = document.querySelectorAll('.exercise-row');
    const row = allRows[workoutCreatorState.changingRowIndex];
    
    if (row) {
        // Update the video display in the row
        const videoPreview = row.querySelector('.exercise-video-preview');
        if (videoPreview) {
            videoPreview.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="exercise-video-thumb" onclick="previewVideo(${video.id})" style="cursor: pointer;">
                        <i class="fas fa-play"></i>
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span class="exercise-video-name" style="font-weight: 500; font-size: 0.9rem;">${video.title}</span>
                        </div>
                        <button class="btn-text" onclick="openVideoSelector(${workoutCreatorState.changingRowIndex})" style="font-size: 0.75rem; color: #ff6b35; padding: 0; margin-top: 2px;">
                            <i class="fas fa-exchange-alt"></i> Change
                        </button>
                    </div>
                    <input type="hidden" class="exercise-video-id" value="${video.id}">
                </div>
            `;
        }
        
        window.toast.success('✅ Video changed!');
    }
    
    // Close modal
    window.modal.close(document.querySelector('.modal-modern.active'));
    delete workoutCreatorState.changingRowIndex;
};

// Custom Exercise Modal Functions
let customExerciseTargetSection = 'main';

window.openCustomExerciseModal = function(section) {
    customExerciseTargetSection = section;
    const modal = document.getElementById('custom-exercise-modal');
    modal.classList.add('active');
};

window.closeCustomExerciseModal = function() {
    const modal = document.getElementById('custom-exercise-modal');
    modal.classList.remove('active');
    document.getElementById('custom-exercise-form').reset();
};

// Handle custom exercise form submission
document.getElementById('custom-exercise-form')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const name = document.getElementById('custom-exercise-name').value;
    const youtubeUrl = document.getElementById('custom-youtube-url').value;
    const equipment = document.getElementById('custom-equipment').value;
    
    // Create a custom exercise object (mimics video structure)
    const customExercise = {
        id: `custom_${Date.now()}`,
        title: name,
        video_url: youtubeUrl,
        custom_equipment: equipment,
        is_custom: true
    };
    
    // Add to the exercise table
    addExerciseRow(customExercise, customExerciseTargetSection);
    
    // Close modal
    closeCustomExerciseModal();
    
    // Success message
    const sectionNames = { warmup: 'Warmup', main: 'Main Workout', cooldown: 'Cooldown' };
    window.toast.success(`✅ Custom exercise added to ${sectionNames[customExerciseTargetSection]}!`);
});

// Toggle exercise section (warmup, main, cooldown)
window.toggleExerciseSection = function(sectionName) {
    const content = document.getElementById(`${sectionName}-section`);
    const toggleIcon = document.getElementById(`${sectionName}-toggle`);
    
    if (content && toggleIcon) {
        const isCollapsed = content.classList.contains('collapsed');
        
        if (isCollapsed) {
            content.classList.remove('collapsed');
            toggleIcon.classList.remove('rotated');
        } else {
            content.classList.add('collapsed');
            toggleIcon.classList.add('rotated');
        }
    }
};

// Update exercise count for a section
function updateExerciseCount(sectionName) {
    const tbody = document.getElementById(`${sectionName}-table-body`);
    const countEl = document.getElementById(`${sectionName}-count`);
    if (tbody && countEl) {
        const count = tbody.querySelectorAll('tr').length;
        countEl.textContent = `(${count} exercise${count !== 1 ? 's' : ''})`;
    }
}

// Add exercise row to table
window.addExerciseRow = function(video = null, section = 'main', exerciseData = null) {
    const tbody = document.getElementById(`${section}-table-body`);
    if (!tbody) return;
    
    const index = workoutCreatorState.exerciseCounter++;
    const row = document.createElement('tr');
    row.className = 'exercise-row animate__animated animate__fadeIn';
    row.dataset.index = index;
    
    row.dataset.section = section;
    
    // Get day options based on current format
    const dayOptions = workoutCreatorState.dayFormat === 'day_number' ? `
        <option value="1">Day 1</option>
        <option value="2">Day 2</option>
        <option value="3">Day 3</option>
        <option value="4">Day 4</option>
        <option value="5">Day 5</option>
        <option value="6">Day 6</option>
        <option value="7">Day 7</option>
    ` : `
        <option value="Monday">Monday</option>
        <option value="Tuesday">Tuesday</option>
        <option value="Wednesday">Wednesday</option>
        <option value="Thursday">Thursday</option>
        <option value="Friday">Friday</option>
        <option value="Saturday">Saturday</option>
        <option value="Sunday">Sunday</option>
    `;
    
    row.innerHTML = `
        <td>
            <i class="fas fa-grip-vertical exercise-row-drag-handle"></i>
        </td>
        <td>
            <select class="exercise-input-small exercise-day-select" required>
                ${dayOptions}
            </select>
        </td>
        <td>
            <div class="exercise-video-preview">
                ${video ? `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        ${video.is_custom ? `
                            <div class="exercise-video-thumb" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); cursor: default;">
                                <i class="fas fa-pen"></i>
                            </div>
                        ` : `
                            <div class="exercise-video-thumb" onclick="previewVideo(${video.id})" style="cursor: pointer;">
                                <i class="fas fa-play"></i>
                            </div>
                        `}
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 6px;">
                                ${video.is_custom ? '<span class="badge" style="background: #3b82f6; color: white; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px;">CUSTOM</span>' : ''}
                                <span class="exercise-video-name" style="font-weight: 500; font-size: 0.9rem;">${video.title}</span>
                            </div>
                            ${video.is_custom && video.custom_equipment ? `<div style="font-size: 0.75rem; color: #666; margin-top: 2px;"><i class="fas fa-dumbbell"></i> ${video.custom_equipment}</div>` : ''}
                            <button class="btn-text" onclick="openVideoSelector(${index})" style="font-size: 0.75rem; color: #ff6b35; padding: 0; margin-top: 2px;">
                                <i class="fas fa-exchange-alt"></i> Change
                            </button>
                        </div>
                        <input type="hidden" class="exercise-video-id" value="${video.id}">
                        ${video.is_custom ? `
                            <input type="hidden" class="exercise-is-custom" value="true">
                            <input type="hidden" class="exercise-custom-name" value="${video.title}">
                            <input type="hidden" class="exercise-custom-url" value="${video.video_url || ''}">
                            <input type="hidden" class="exercise-custom-equipment" value="${video.custom_equipment || ''}">
                        ` : ''}
                    </div>
                ` : `
                    <button class="btn-modern btn-outline" onclick="openVideoSelector(${index})" style="padding: 8px 16px; font-size: 0.85rem;">
                        <i class="fas fa-video"></i> Add Video
                    </button>
                `}
            </div>
        </td>
        <td>
            <input type="number" class="exercise-input-small exercise-sets" placeholder="3" min="1" max="10" value="${exerciseData?.sets || ''}">
        </td>
        <td>
            <input type="text" class="exercise-input-small exercise-reps" placeholder="10" value="${exerciseData?.reps || ''}">
        </td>
        <td>
            <div style="display: flex; gap: 4px; align-items: center;">
                <input type="number" class="exercise-input-small exercise-time" placeholder="30" min="0" step="1" style="flex: 1;" value="${exerciseData?.time || ''}">
                <select class="exercise-input-small exercise-time-unit" style="width: 60px;">
                    <option value="sec" ${exerciseData?.time_unit === 'sec' ? 'selected' : ''}>sec</option>
                    <option value="min" ${exerciseData?.time_unit === 'min' ? 'selected' : ''}>min</option>
                </select>
            </div>
        </td>
        <td>
            <input type="text" class="exercise-input-medium exercise-notes" placeholder="Add notes..." value="${exerciseData?.notes || ''}">
        </td>
        <td>
            <button class="btn-remove-exercise" onclick="removeExerciseRow(${index}, '${section}')">
                <i class="fas fa-times"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
    
    // Set day value if provided
    if (exerciseData?.day) {
        const daySelect = row.querySelector('.exercise-day-select');
        if (daySelect) {
            daySelect.value = exerciseData.day;
        }
    }
    
    // Store exercise data
    workoutCreatorState.exercises.push({
        index,
        video: video,
        section: section,
        row: row
    });
    
    // Update count
    updateExerciseCount(section);
};

// Remove exercise row
window.removeExerciseRow = function(index, section) {
    const row = document.querySelector(`tr[data-index="${index}"]`);
    if (row) {
        row.classList.add('animate__animated', 'animate__fadeOut');
        setTimeout(() => {
            row.remove();
            workoutCreatorState.exercises = workoutCreatorState.exercises.filter(e => e.index !== index);
            // Update count after removal
            if (section) {
                updateExerciseCount(section);
            }
        }, 500);
    }
};

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
    if (searchInput && !searchInput.dataset.listenerAttached) {
        searchInput.addEventListener('input', filterVideos);
        searchInput.dataset.listenerAttached = 'true';
    }
    
    // Category filter
    const categoryFilter = document.getElementById('video-library-category');
    if (categoryFilter && !categoryFilter.dataset.listenerAttached) {
        categoryFilter.addEventListener('change', filterVideos);
        categoryFilter.dataset.listenerAttached = 'true';
    }
    
    // Add exercise button
    const addExerciseBtn = document.getElementById('add-exercise-btn');
    if (addExerciseBtn && !addExerciseBtn.dataset.listenerAttached) {
        addExerciseBtn.addEventListener('click', () => addExerciseRow());
        addExerciseBtn.dataset.listenerAttached = 'true';
    }
    
    // Save plan button
    const savePlanBtn = document.getElementById('save-plan-btn');
    if (savePlanBtn && !savePlanBtn.dataset.listenerAttached) {
        savePlanBtn.addEventListener('click', saveWorkoutPlan);
        savePlanBtn.dataset.listenerAttached = 'true';
    }
    
    // Toggle video panel
    const toggleBtn = document.getElementById('toggle-video-panel-btn');
    if (toggleBtn && !toggleBtn.dataset.listenerAttached) {
        toggleBtn.addEventListener('click', window.toggleVideoPanel);
        toggleBtn.dataset.listenerAttached = 'true';
    }
    
    // Create new client button
    const newClientBtn = document.getElementById('new-client-btn');
    if (newClientBtn && !newClientBtn.dataset.listenerAttached) {
        newClientBtn.addEventListener('click', openClientModal);
        newClientBtn.dataset.listenerAttached = 'true';
    }
    
    // Day format is now handled by setDayFormat() function
}

// Set day format (toggle button handler)
window.setDayFormat = function(format) {
    workoutCreatorState.dayFormat = format;
    document.getElementById('plan-day-type').value = format;
    
    // Update toggle buttons
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        if (btn.dataset.value === format) {
            btn.classList.add('active');
            btn.style.background = 'linear-gradient(135deg, #ff6b35 0%, #f7931e 100%)';
            btn.style.color = 'white';
        } else {
            btn.classList.remove('active');
            btn.style.background = 'white';
            btn.style.color = '#666';
        }
    });
    
    // Update all existing day dropdowns
    document.querySelectorAll('.exercise-day-select').forEach(select => {
        const currentValue = select.value;
        updateDayDropdownOptions(select);
        
        // Try to preserve selection if possible
        if (format === 'day_of_week') {
            // Convert day numbers to weekdays
            const dayMap = { '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', '4': 'Thursday', '5': 'Friday', '6': 'Saturday', '7': 'Sunday' };
            select.value = dayMap[currentValue] || 'Monday';
        } else {
            // Convert weekdays to day numbers
            const weekdayMap = { 'Monday': '1', 'Tuesday': '2', 'Wednesday': '3', 'Thursday': '4', 'Friday': '5', 'Saturday': '6', 'Sunday': '7' };
            select.value = weekdayMap[currentValue] || '1';
        }
    });
};

// Update day dropdown options based on format
function updateDayDropdownOptions(selectElement) {
    if (workoutCreatorState.dayFormat === 'day_number') {
        selectElement.innerHTML = `
            <option value="1">Day 1</option>
            <option value="2">Day 2</option>
            <option value="3">Day 3</option>
            <option value="4">Day 4</option>
            <option value="5">Day 5</option>
            <option value="6">Day 6</option>
            <option value="7">Day 7</option>
        `;
    } else {
        selectElement.innerHTML = `
            <option value="Monday">Monday</option>
            <option value="Tuesday">Tuesday</option>
            <option value="Wednesday">Wednesday</option>
            <option value="Thursday">Thursday</option>
            <option value="Friday">Friday</option>
            <option value="Saturday">Saturday</option>
            <option value="Sunday">Sunday</option>
        `;
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
window.toggleVideoPanel = function() {
    const panel = document.querySelector('.creator-video-panel');
    const btn = document.getElementById('toggle-video-panel-btn');
    
    if (panel && btn) {
        const isCollapsed = panel.classList.contains('collapsed');
        
        if (isCollapsed) {
            panel.classList.remove('collapsed');
            btn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        } else {
            panel.classList.add('collapsed');
            btn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        }
    }
};

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
        const dayType = document.getElementById('plan-day-type')?.value || 'day_number';
        
        // Validate
        if (!clientId) {
            window.toast.error('⚠️ Please select a client');
            return;
        }
        
        if (!planName) {
            window.toast.error('⚠️ Please enter a plan name');
            return;
        }
        
        // Collect exercises from all sections
        const exercises = [];
        let orderIndex = 0;
        
        // Helper function to collect exercises from a section
        const collectFromSection = (sectionName) => {
            const tbody = document.getElementById(`${sectionName}-table-body`);
            if (!tbody) return;
            
            const rows = tbody.querySelectorAll('.exercise-row');
            rows.forEach(row => {
                const videoId = row.querySelector('.exercise-video-id')?.value;
                const isCustom = row.querySelector('.exercise-is-custom')?.value === 'true';
                const day = row.querySelector('.exercise-day-select')?.value;
                const sets = row.querySelector('.exercise-sets')?.value;
                const reps = row.querySelector('.exercise-reps')?.value;
                const time = row.querySelector('.exercise-time')?.value;
                const timeUnit = row.querySelector('.exercise-time-unit')?.value || 'sec';
                const notes = row.querySelector('.exercise-notes')?.value;
                
                // Either regular video or custom exercise
                if (videoId || isCustom) {
                    const exerciseData = {
                        section: sectionName,
                        day: day,
                        sets: sets ? parseInt(sets) : null,
                        reps: reps || null,
                        time: time ? parseInt(time) : null,
                        time_unit: timeUnit,
                        notes: notes || null,
                        order_index: orderIndex++
                    };
                    
                    if (isCustom) {
                        // Custom exercise
                        exerciseData.is_custom = true;
                        exerciseData.custom_name = row.querySelector('.exercise-custom-name')?.value;
                        exerciseData.custom_youtube_url = row.querySelector('.exercise-custom-url')?.value;
                        exerciseData.custom_equipment = row.querySelector('.exercise-custom-equipment')?.value;
                        exerciseData.video_id = null;  // No video_id for custom exercises
                    } else {
                        // Regular video exercise
                        exerciseData.video_id = parseInt(videoId);
                        exerciseData.is_custom = false;
                    }
                    
                    exercises.push(exerciseData);
                }
            });
        };
        
        // Collect from all sections
        collectFromSection('warmup');
        collectFromSection('main');
        collectFromSection('cooldown');
        
        if (exercises.length === 0) {
            window.toast.error('⚠️ Please add at least one exercise');
            return;
        }
        
        // Create plan object
        const planData = {
            client_id: parseInt(clientId),
            plan_name: planName,
            description: description || null,
            start_date: startDate || null,
            end_date: endDate || null,
            is_template: true,  // Always save as template
            day_type: dayType,
            exercises: exercises
        };
        
        // Determine if updating or creating
        const isUpdating = workoutCreatorState.currentPlanId !== null;
        const url = isUpdating 
            ? `/api/workout-plans/${workoutCreatorState.currentPlanId}`
            : '/api/workout-plans';
        const method = isUpdating ? 'PUT' : 'POST';
        
        // Send to API
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(planData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to save workout plan');
        }
        
        const savedPlan = await response.json();
        
        // Show success message
        if (isUpdating) {
            window.toast.success('✅ Workout plan updated successfully!');
        } else {
            window.toast.success('✅ Workout plan created successfully!');
        }
        
        // Show share link modal
        if (savedPlan.share_token) {
            const shareUrl = `${window.location.origin}/workout-plan/${savedPlan.share_token}`;
            const modalTitle = isUpdating ? '✅ Workout Plan Updated!' : '🎉 Workout Plan Created!';
            const modalContent = `
                <h3 style="margin-bottom: 20px;">${modalTitle}</h3>
                <p style="margin-bottom: 15px;">Share this link with your client:</p>
                <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                    <input type="text" value="${shareUrl}" readonly style="flex: 1; border: none; background: transparent; font-family: monospace; font-size: 0.9rem;" id="share-url-input">
                    <button class="btn-modern btn-outline" onclick="copyToClipboard('${shareUrl}', '🔗 Link copied!')" style="padding: 8px 16px;">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button class="btn-modern btn-outline" onclick="window.modal.close(this.closest('.modal-modern')); resetWorkoutCreatorForm();">
                        <i class="fas fa-redo"></i> Create Another Plan
                    </button>
                    <button class="btn-modern btn-fire" onclick="window.modal.close(this.closest('.modal-modern'))">
                        <i class="fas fa-check"></i> Done
                    </button>
                </div>
            `;
            window.modal.show(modalContent, { showClose: true });
        }
        
        // DON'T auto-reset - let user decide when to reset
        
    } catch (error) {
        console.error('Error saving workout plan:', error);
        window.toast.error('❌ Failed to save: ' + error.message);
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
window.resetWorkoutCreatorForm = function() {
    // Confirm reset
    if (!confirm('Are you sure you want to reset the entire form? All unsaved changes will be lost.')) {
        return;
    }
    
    // Clear form fields
    document.getElementById('plan-client-select').value = '';
    document.getElementById('plan-name').value = '';
    document.getElementById('plan-description').value = '';
    document.getElementById('plan-start-date').value = '';
    document.getElementById('plan-end-date').value = '';
    document.getElementById('plan-day-type').value = 'day_number';
    
    // Reset day format toggle
    setDayFormat('day_number');
    
    // Clear all exercise sections
    document.getElementById('warmup-table-body').innerHTML = '';
    document.getElementById('main-table-body').innerHTML = '';
    document.getElementById('cooldown-table-body').innerHTML = '';
    
    // Reset state
    workoutCreatorState.exercises = [];
    workoutCreatorState.exerciseCounter = 0;
    workoutCreatorState.dayFormat = 'day_number';
    workoutCreatorState.currentPlanId = null;  // Clear editing state
    
    // Update exercise counts
    updateExerciseCount('warmup');
    updateExerciseCount('main');
    updateExerciseCount('cooldown');
    
    // Success message
    window.toast.success('✅ Form reset successfully!');
};

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

// Delete current plan from workout creator
window.deleteCurrentPlan = async function() {
    if (!workoutCreatorState.currentPlanId) {
        window.toast.error('⚠️ No plan selected to delete');
        return;
    }
    
    const planName = document.getElementById('plan-name')?.value || 'this plan';
    const clientId = document.getElementById('plan-client-select')?.value;
    
    // Confirm deletion
    const confirmed = confirm(`⚠️ Are you sure you want to delete "${planName}"?\n\nThis action cannot be undone. The client will lose access to this workout plan.`);
    
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/workout-plans/${workoutCreatorState.currentPlanId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete plan');
        }
        
        window.toast.success(`✅ "${planName}" deleted successfully`);
        
        // Reset the form
        resetWorkoutCreatorForm();
        
        // Reload the plans dropdown if client is still selected
        if (clientId) {
            await loadClientPlans(clientId);
        }
        
    } catch (error) {
        console.error('Error deleting plan:', error);
        window.toast.error('❌ Failed to delete plan: ' + error.message);
    }
};

// Open client modal (to be implemented)
function openClientModal() {
    showToast('Client creation modal coming soon!', 'info');
    // TODO: Implement client creation modal
}
