/**
 * Workout Video Search System - Plan Template
 * Handles the creation and management of workout plan templates
 */

class PlanTemplateManager {
    constructor(app) {
        this.app = app;
        this.templates = [];
        this.currentTemplate = null;
        this.currentPlan = null;
        
        this.init();
    }
    
    /**
     * Initialize the template manager
     */
    async init() {
        console.log('Initializing plan template manager...');
        this.setupEventListeners();
        await this.loadTemplates();
    }
    
    /**
     * Setup event listeners for template interactions
     */
    setupEventListeners() {
        // Template selection
        document.getElementById('plan-template')?.addEventListener('change', (e) => {
            const templateId = e.target.value;
            if (templateId) {
                this.selectTemplate(templateId);
            } else {
                this.resetPlanForm();
            }
        });
        
        // Template save button
        document.getElementById('save-template-btn')?.addEventListener('click', () => {
            this.saveCurrentAsTemplate();
        });
        
        // Section add button
        document.getElementById('add-section-btn')?.addEventListener('click', () => {
            this.addSection();
        });
        
        // Video search for plan
        document.getElementById('plan-video-search')?.addEventListener('input', (e) => {
            this.searchVideos(e.target.value);
        });
    }
    
    /**
     * Load available templates
     */
    async loadTemplates() {
        try {
            const response = await this.app.apiRequest('/plans/templates');
            
            if (!response.ok) {
                throw new Error('Failed to load templates');
            }
            
            const data = await response.json();
            this.templates = data.templates || [];
            
            // Populate template dropdown
            this.updateTemplateDropdown();
            
        } catch (error) {
            console.error('Error loading templates:', error);
            this.app.showToast('Failed to load templates', 'error');
        }
    }
    
    /**
     * Update template dropdown with available templates
     */
    updateTemplateDropdown() {
        const dropdown = document.getElementById('plan-template');
        if (!dropdown) return;
        
        // Clear existing options except the default
        while (dropdown.options.length > 1) {
            dropdown.remove(1);
        }
        
        // Add templates
        this.templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.title;
            dropdown.appendChild(option);
        });
    }
    
    /**
     * Select a template to use
     */
    selectTemplate(templateId) {
        const template = this.templates.find(t => t.id === parseInt(templateId));
        if (!template) return;
        
        this.currentTemplate = template;
        
        // Apply template to form
        document.getElementById('plan-description').value = template.description || '';
        
        // Create plan structure based on template
        this.buildPlanStructure(template);
    }
    
    /**
     * Build plan structure from template
     */
    buildPlanStructure(template) {
        if (!template || !template.structure) return;
        
        // Reset current plan
        this.currentPlan = {
            title: document.getElementById('plan-title').value || '',
            client_id: document.getElementById('plan-client').value || '',
            start_date: document.getElementById('plan-start-date').value || '',
            end_date: document.getElementById('plan-end-date').value || '',
            description: template.description || '',
            template_id: template.id,
            sections: []
        };
        
        // Create sections from template structure
        template.structure.sections.forEach(section => {
            this.currentPlan.sections.push({
                title: section.title,
                description: section.description || '',
                order: section.order || 0,
                workouts: []
            });
        });
        
        // Update UI
        this.renderPlanStructure();
    }
    
    /**
     * Reset plan form to empty state
     */
    resetPlanForm() {
        this.currentTemplate = null;
        document.getElementById('plan-description').value = '';
        
        // Initialize empty plan
        this.currentPlan = {
            title: document.getElementById('plan-title').value || '',
            client_id: document.getElementById('plan-client').value || '',
            start_date: document.getElementById('plan-start-date').value || '',
            end_date: document.getElementById('plan-end-date').value || '',
            description: '',
            sections: [{
                title: 'General Workouts',
                description: '',
                order: 0,
                workouts: []
            }]
        };
        
        // Update UI
        this.renderPlanStructure();
    }
    
    /**
     * Render current plan structure to UI
     */
    renderPlanStructure() {
        const planStructureEl = document.getElementById('plan-structure');
        if (!planStructureEl || !this.currentPlan) return;
        
        planStructureEl.innerHTML = '';
        
        this.currentPlan.sections.forEach((section, sectionIndex) => {
            const sectionEl = document.createElement('div');
            sectionEl.className = 'plan-section';
            sectionEl.innerHTML = `
                <div class="section-header">
                    <h4>${section.title}</h4>
                    <div class="section-actions">
                        <button class="btn btn-sm btn-outline section-edit-btn" data-section="${sectionIndex}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline section-delete-btn" data-section="${sectionIndex}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <p class="section-description">${section.description}</p>
                <div class="section-workouts" id="section-workouts-${sectionIndex}">
                    <div class="empty-state">
                        <i class="fas fa-dumbbell"></i>
                        <p>No workouts added yet</p>
                    </div>
                </div>
                <button class="btn btn-sm btn-primary add-workout-btn" data-section="${sectionIndex}">
                    <i class="fas fa-plus"></i> Add Workout
                </button>
            `;
            
            planStructureEl.appendChild(sectionEl);
            
            // Add event listeners for section buttons
            sectionEl.querySelector('.section-edit-btn').addEventListener('click', () => {
                this.editSection(sectionIndex);
            });
            
            sectionEl.querySelector('.section-delete-btn').addEventListener('click', () => {
                this.deleteSection(sectionIndex);
            });
            
            sectionEl.querySelector('.add-workout-btn').addEventListener('click', () => {
                this.openAddWorkoutModal(sectionIndex);
            });
            
            // Render workouts if any
            const workoutsContainer = sectionEl.querySelector(`#section-workouts-${sectionIndex}`);
            if (section.workouts && section.workouts.length > 0) {
                workoutsContainer.innerHTML = '';
                
                section.workouts.forEach((workout, workoutIndex) => {
                    const workoutEl = document.createElement('div');
                    workoutEl.className = 'workout-item';
                    workoutEl.innerHTML = `
                        <div class="workout-info">
                            <h5>${workout.title}</h5>
                            <div class="workout-meta">
                                <span><i class="fas fa-clock"></i> ${workout.duration_minutes || 0} min</span>
                                <span><i class="fas fa-layer-group"></i> ${workout.sets || '-'} sets</span>
                                <span><i class="fas fa-redo"></i> ${workout.reps || '-'} reps</span>
                            </div>
                        </div>
                        <div class="workout-actions">
                            <button class="btn btn-sm btn-outline workout-edit-btn" data-section="${sectionIndex}" data-workout="${workoutIndex}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline workout-delete-btn" data-section="${sectionIndex}" data-workout="${workoutIndex}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                    
                    workoutsContainer.appendChild(workoutEl);
                    
                    // Add event listeners for workout buttons
                    workoutEl.querySelector('.workout-edit-btn').addEventListener('click', (e) => {
                        const sectionIdx = parseInt(e.target.closest('.workout-edit-btn').getAttribute('data-section'));
                        const workoutIdx = parseInt(e.target.closest('.workout-edit-btn').getAttribute('data-workout'));
                        this.editWorkout(sectionIdx, workoutIdx);
                    });
                    
                    workoutEl.querySelector('.workout-delete-btn').addEventListener('click', (e) => {
                        const sectionIdx = parseInt(e.target.closest('.workout-delete-btn').getAttribute('data-section'));
                        const workoutIdx = parseInt(e.target.closest('.workout-delete-btn').getAttribute('data-workout'));
                        this.deleteWorkout(sectionIdx, workoutIdx);
                    });
                });
            }
        });
        
        // Add section button
        const addSectionBtn = document.createElement('button');
        addSectionBtn.className = 'btn btn-outline btn-block';
        addSectionBtn.innerHTML = '<i class="fas fa-plus"></i> Add Section';
        addSectionBtn.addEventListener('click', () => this.addSection());
        
        planStructureEl.appendChild(addSectionBtn);
    }
    
    /**
     * Add a new section to the plan
     */
    addSection() {
        if (!this.currentPlan) {
            this.resetPlanForm();
        }
        
        // Open section modal
        const sectionModal = document.getElementById('section-modal');
        if (sectionModal) {
            // Reset form
            document.getElementById('section-title').value = '';
            document.getElementById('section-description').value = '';
            document.getElementById('section-order').value = this.currentPlan.sections.length;
            document.getElementById('section-index').value = -1; // New section
            
            // Show modal
            sectionModal.style.display = 'flex';
        }
    }
    
    /**
     * Edit an existing section
     */
    editSection(sectionIndex) {
        if (!this.currentPlan || !this.currentPlan.sections[sectionIndex]) return;
        
        const section = this.currentPlan.sections[sectionIndex];
        
        // Open section modal
        const sectionModal = document.getElementById('section-modal');
        if (sectionModal) {
            // Fill form with section data
            document.getElementById('section-title').value = section.title;
            document.getElementById('section-description').value = section.description || '';
            document.getElementById('section-order').value = section.order || 0;
            document.getElementById('section-index').value = sectionIndex; // Existing section
            
            // Show modal
            sectionModal.style.display = 'flex';
        }
    }
    
    /**
     * Delete a section from the plan
     */
    deleteSection(sectionIndex) {
        if (!this.currentPlan || !this.currentPlan.sections[sectionIndex]) return;
        
        if (confirm('Are you sure you want to delete this section and all its workouts?')) {
            this.currentPlan.sections.splice(sectionIndex, 1);
            this.renderPlanStructure();
            this.app.showToast('Section deleted', 'success');
        }
    }
    
    /**
     * Open modal to add a workout to a section
     */
    openAddWorkoutModal(sectionIndex) {
        if (!this.currentPlan || !this.currentPlan.sections[sectionIndex]) return;
        
        // Set current section index for later use
        document.getElementById('workout-section-index').value = sectionIndex;
        document.getElementById('workout-index').value = -1; // New workout
        
        // Reset form
        document.getElementById('workout-title').value = '';
        document.getElementById('workout-description').value = '';
        document.getElementById('workout-day').value = 1;
        document.getElementById('workout-order').value = 1;
        document.getElementById('workout-duration').value = '';
        document.getElementById('workout-sets').value = '';
        document.getElementById('workout-reps').value = '';
        document.getElementById('workout-intensity').value = '';
        document.getElementById('workout-video').value = '';
        
        // Open modal
        const workoutModal = document.getElementById('workout-modal');
        if (workoutModal) {
            workoutModal.style.display = 'flex';
        }
    }
    
    /**
     * Edit an existing workout
     */
    editWorkout(sectionIndex, workoutIndex) {
        if (!this.currentPlan || 
            !this.currentPlan.sections[sectionIndex] || 
            !this.currentPlan.sections[sectionIndex].workouts[workoutIndex]) return;
        
        const workout = this.currentPlan.sections[sectionIndex].workouts[workoutIndex];
        
        // Set indices for later use
        document.getElementById('workout-section-index').value = sectionIndex;
        document.getElementById('workout-index').value = workoutIndex;
        
        // Fill form with workout data
        document.getElementById('workout-title').value = workout.title;
        document.getElementById('workout-description').value = workout.description || '';
        document.getElementById('workout-day').value = workout.day_number || 1;
        document.getElementById('workout-order').value = workout.order_in_day || 1;
        document.getElementById('workout-duration').value = workout.duration_minutes || '';
        document.getElementById('workout-sets').value = workout.sets || '';
        document.getElementById('workout-reps').value = workout.reps || '';
        document.getElementById('workout-intensity').value = workout.intensity || '';
        document.getElementById('workout-video').value = workout.video_id || '';
        
        // Open modal
        const workoutModal = document.getElementById('workout-modal');
        if (workoutModal) {
            workoutModal.style.display = 'flex';
        }
    }
    
    /**
     * Delete a workout from a section
     */
    deleteWorkout(sectionIndex, workoutIndex) {
        if (!this.currentPlan || 
            !this.currentPlan.sections[sectionIndex] || 
            !this.currentPlan.sections[sectionIndex].workouts[workoutIndex]) return;
        
        if (confirm('Are you sure you want to delete this workout?')) {
            this.currentPlan.sections[sectionIndex].workouts.splice(workoutIndex, 1);
            this.renderPlanStructure();
            this.app.showToast('Workout deleted', 'success');
        }
    }
    
    /**
     * Save current plan structure as a template
     */
    async saveCurrentAsTemplate() {
        if (!this.currentPlan) {
            this.app.showToast('No plan to save as template', 'error');
            return;
        }
        
        const title = prompt('Enter template name:', this.currentPlan.title || 'New Template');
        if (!title) return;
        
        try {
            const templateData = {
                title: title,
                description: this.currentPlan.description,
                is_public: false,
                structure: {
                    sections: this.currentPlan.sections.map(section => ({
                        title: section.title,
                        description: section.description,
                        order: section.order
                    }))
                }
            };
            
            const response = await this.app.apiRequest('/plans/templates', {
                method: 'POST',
                body: JSON.stringify(templateData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to save template');
            }
            
            const data = await response.json();
            this.templates.push(data);
            this.updateTemplateDropdown();
            
            this.app.showToast('Template saved successfully', 'success');
        } catch (error) {
            console.error('Error saving template:', error);
            this.app.showToast('Failed to save template', 'error');
        }
    }
    
    /**
     * Search for videos to add to plan
     */
    async searchVideos(query) {
        if (query.length < 3) return;
        
        try {
            const response = await this.app.apiRequest(`/videos/search?query=${encodeURIComponent(query)}&limit=5`);
            
            if (!response.ok) {
                throw new Error('Failed to search videos');
            }
            
            const data = await response.json();
            this.updateVideoSearchResults(data.results);
        } catch (error) {
            console.error('Error searching videos:', error);
        }
    }
    
    /**
     * Update video search results in UI
     */
    updateVideoSearchResults(videos) {
        const resultsContainer = document.getElementById('video-search-results');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = '';
        
        if (!videos || videos.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state"><p>No videos found</p></div>';
            return;
        }
        
        videos.forEach(video => {
            const videoEl = document.createElement('div');
            videoEl.className = 'search-result-item';
            videoEl.innerHTML = `
                <div class="result-info">
                    <h5>${video.title}</h5>
                    <div class="result-meta">
                        <span class="badge badge-primary">${video.category}</span>
                        <span>${video.duration ? `${Math.floor(video.duration / 60)} min` : 'Unknown duration'}</span>
                    </div>
                </div>
                <button class="btn btn-sm btn-primary select-video-btn" data-id="${video.id}">
                    <i class="fas fa-plus"></i>
                </button>
            `;
            
            resultsContainer.appendChild(videoEl);
            
            // Add event listener to select button
            videoEl.querySelector('.select-video-btn').addEventListener('click', (e) => {
                const videoId = e.target.closest('.select-video-btn').getAttribute('data-id');
                document.getElementById('workout-video').value = videoId;
                
                // Set the selected video title
                document.getElementById('selected-video-title').textContent = video.title;
                
                // Hide results
                resultsContainer.innerHTML = '';
            });
        });
    }
    
    /**
     * Get current plan data for API submission
     */
    getPlanData() {
        if (!this.currentPlan) return null;
        
        // Get form values
        const title = document.getElementById('plan-title').value;
        const clientId = document.getElementById('plan-client').value;
        const startDate = document.getElementById('plan-start-date').value;
        const endDate = document.getElementById('plan-end-date').value;
        const description = document.getElementById('plan-description').value;
        
        if (!title || !clientId) {
            this.app.showToast('Title and client are required', 'error');
            return null;
        }
        
        // Update current plan with form values
        this.currentPlan.title = title;
        this.currentPlan.client_id = clientId;
        this.currentPlan.start_date = startDate;
        this.currentPlan.end_date = endDate;
        this.currentPlan.description = description;
        
        return this.currentPlan;
    }
}

// Add to global namespace for use in HTML
window.PlanTemplateManager = PlanTemplateManager;
