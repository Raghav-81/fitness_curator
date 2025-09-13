/**
 * Workout Video Search System - Dashboard JavaScript
 * Handles authentication, navigation, and dashboard interactions
 */

// Main application class
class WorkoutDashboardApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentUser = null;
        this.authToken = null;
        this.currentView = 'login'; // login, trainer, client
        this.currentSection = 'dashboard'; // dashboard, clients, plans, videos
        
        // Initialize the application
        this.init();
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing dashboard application...');
        this.setupEventListeners();
        this.checkAuthentication();
    }
    
    /**
     * Setup event listeners for UI interactions
     */
    setupEventListeners() {
        // Auth tab switching
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = e.target.getAttribute('data-tab');
                this.switchAuthTab(tabId);
            });
        });
        
        // Login form
        document.getElementById('login-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // Register form
        document.getElementById('register-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleRegistration();
        });
        
        // Google login
        document.getElementById('google-login-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleGoogleLogin();
        });

        // Google register
        const googleRegisterBtn = document.getElementById('google-register-btn');
        if (googleRegisterBtn) {
            console.log('Found "Register with Google" button. Attaching listener.');
            googleRegisterBtn.addEventListener('click', (e) => {
                console.log('"Register with Google" button clicked.');
                e.preventDefault();
                this.handleGoogleLogin(); // The same function can handle both login and registration
            });
        } else {
            console.error('Could not find the "Register with Google" button.');
        }
        
        // Logout buttons
        document.getElementById('logout-btn')?.addEventListener('click', () => this.handleLogout());
        document.getElementById('client-logout-btn')?.addEventListener('click', () => this.handleLogout());
        
        // Navigation tabs
        document.querySelectorAll('.navbar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.target.closest('.navbar-item').getAttribute('data-section');
                if (section) {
                    this.switchSection(section);
                }
            });
        });
        
        // Modal close buttons
        document.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    this.closeModal(modal.id);
                }
            });
        });
        
        // Add client button
        document.getElementById('add-client-btn')?.addEventListener('click', () => {
            this.openModal('add-client-modal');
        });
        
        // Create plan button
        document.getElementById('create-plan-btn')?.addEventListener('click', () => {
            this.openModal('create-plan-modal');
        });
        
        // Form submissions
        document.getElementById('add-client-submit')?.addEventListener('click', () => {
            this.handleAddClient();
        });
        
        document.getElementById('create-plan-submit')?.addEventListener('click', () => {
            this.handleCreatePlan();
        });
    }
    
    /**
     * Check if user is authenticated
     */
    checkAuthentication() {
        // Check for token in local storage
        const token = localStorage.getItem('authToken');
        const userData = localStorage.getItem('userData');
        
        if (token && userData) {
            try {
                this.authToken = token;
                this.currentUser = JSON.parse(userData);
                this.showUserDashboard();
            } catch (error) {
                console.error('Error parsing user data:', error);
                this.showLoginView();
            }
        } else {
            this.showLoginView();
        }
    }
    
    /**
     * Switch between login and register tabs
     */
    switchAuthTab(tabId) {
        // Hide all forms
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.remove('active');
        });
        
        // Deactivate all tabs
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Activate selected tab and form
        document.querySelector(`.auth-tab[data-tab="${tabId}"]`)?.classList.add('active');
        document.getElementById(`${tabId}-form`)?.classList.add('active');
    }
    
    /**
     * Switch between dashboard sections
     */
    switchSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Deactivate all nav items
        document.querySelectorAll('.navbar-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Activate selected section and nav item
        document.getElementById(`${sectionId}-section`)?.classList.add('active');
        document.querySelector(`.navbar-item[data-section="${sectionId}"]`)?.classList.add('active');
        
        this.currentSection = sectionId;
        
        // Load section-specific data
        this.loadSectionData(sectionId);
    }
    
    /**
     * Handle user login
     */
    async handleLogin() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        if (!email || !password) {
            this.showToast('Please fill in all fields', 'error');
            return;
        }
        
        try {
            // Convert to FormData for compatibility with OAuth2PasswordRequestForm
            const formData = new FormData();
            formData.append('username', email); // OAuth2 uses 'username' even though we're using email
            formData.append('password', password);
            
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }
            
            // Save auth data
            this.authToken = data.access_token;
            this.currentUser = {
                id: data.user_id,
                email: data.email,
                fullName: data.full_name,
                userType: data.user_type
            };
            
            // Store in localStorage for persistence
            localStorage.setItem('authToken', this.authToken);
            localStorage.setItem('userData', JSON.stringify(this.currentUser));
            
            // Show appropriate dashboard
            this.showUserDashboard();
            this.showToast('Login successful!', 'success');
        } catch (error) {
            console.error('Login error:', error);
            this.showToast(error.message || 'Login failed. Please try again.', 'error');
        }
    }
    
    /**
     * Handle user registration
     */
    async handleRegistration() {
        const fullName = document.getElementById('register-name').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const userType = document.querySelector('input[name="user-type"]:checked').value;
        
        if (!fullName || !email || !password) {
            this.showToast('Please fill in all fields', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email,
                    password,
                    full_name: fullName,
                    user_type: userType
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }
            
            // Save auth data
            this.authToken = data.access_token;
            this.currentUser = {
                id: data.user_id,
                email: data.email,
                fullName: data.full_name,
                userType: data.user_type
            };
            
            // Store in localStorage for persistence
            localStorage.setItem('authToken', this.authToken);
            localStorage.setItem('userData', JSON.stringify(this.currentUser));
            
            // Show appropriate dashboard
            this.showUserDashboard();
            this.showToast('Account created successfully!', 'success');
        } catch (error) {
            console.error('Registration error:', error);
            this.showToast(error.message || 'Registration failed. Please try again.', 'error');
        }
    }
    
    /**
     * Handle Google login (simulated for demo)
     */
    async handleGoogleLogin() {
        // Simulate Google Auth Flow for demo purposes
        const fullName = prompt("Simulating Google Login:\nEnter your full name:", "Demo User");
        const email = prompt("Enter your email:", "demo@example.com");

        if (!fullName || !email) {
            this.showToast('Google login simulation cancelled.', 'info');
            return;
        }

        // Determine if this is for login or registration based on active tab
        const activeAuthTab = document.querySelector('.auth-tab.active').getAttribute('data-tab');
        const userType = (activeAuthTab === 'register') 
            ? document.querySelector('input[name="user-type"]:checked').value 
            : 'client'; // Default to client for login, can be improved

        try {
            // In a real app, you'd send a Google token to the backend.
            // Here, we'll just send the simulated user info.
            const response = await fetch(`${this.apiBaseUrl}/auth/google`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    token: 'simulated-google-token', // Backend expects a token
                    user_type: userType,
                    // Sending extra info for simulation
                    simulated_user: {
                        email: email,
                        full_name: fullName
                    }
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Google login failed');
            }

            // Save auth data
            this.authToken = data.access_token;
            this.currentUser = {
                id: data.user_id,
                email: data.email,
                fullName: data.full_name,
                userType: data.user_type
            };

            // Store in localStorage for persistence
            localStorage.setItem('authToken', this.authToken);
            localStorage.setItem('userData', JSON.stringify(this.currentUser));

            // Show appropriate dashboard
            this.showUserDashboard();
            this.showToast('Google login successful!', 'success');

        } catch (error) {
            console.error('Google login error:', error);
            this.showToast(error.message || 'Google login failed. Please try again.', 'error');
        }
    }
    
    /**
     * Handle logout
     */
    handleLogout() {
        // Clear auth data
        this.authToken = null;
        this.currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        
        // Show login view
        this.showLoginView();
        this.showToast('Logged out successfully', 'success');
    }
    
    /**
     * Show login view
     */
    showLoginView() {
        document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
        document.getElementById('login-view').classList.add('active');
        this.currentView = 'login';
    }
    
    /**
     * Show appropriate dashboard based on user type
     */
    showUserDashboard() {
        document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
        
        if (this.currentUser.userType === 'trainer') {
            document.getElementById('trainer-view').classList.add('active');
            this.currentView = 'trainer';
            this.switchSection('dashboard');
            
            // Update trainer name in UI
            document.querySelectorAll('.user-name').forEach(el => {
                el.textContent = this.currentUser.fullName;
            });
            
        } else if (this.currentUser.userType === 'client') {
            document.getElementById('client-view').classList.add('active');
            this.currentView = 'client';
            this.switchSection('client-dashboard');
            
            // Update client name in UI
            document.querySelectorAll('.client-name').forEach(el => {
                el.textContent = this.currentUser.fullName;
            });
            document.querySelectorAll('.user-name').forEach(el => {
                el.textContent = this.currentUser.fullName;
            });
        }
    }
    
    /**
     * Load section-specific data
     */
    async loadSectionData(sectionId) {
        if (!this.authToken) return;
        
        switch(sectionId) {
            case 'dashboard':
                await this.loadTrainerDashboard();
                break;
            case 'clients':
                await this.loadClientsData();
                break;
            case 'plans':
                await this.loadPlansData();
                break;
            case 'videos':
                await this.loadVideosData();
                break;
            case 'client-dashboard':
                await this.loadClientDashboard();
                break;
            case 'client-plans':
                await this.loadClientPlans();
                break;
            case 'client-progress':
                await this.loadClientProgress();
                break;
        }
    }
    
    /**
     * Open a modal
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }
    
    /**
     * Close a modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        // Icon based on type
        let icon = 'info-circle';
        if (type === 'success') icon = 'check-circle';
        if (type === 'error') icon = 'exclamation-circle';
        if (type === 'warning') icon = 'exclamation-triangle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon} toast-icon"></i>
            <span>${message}</span>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    /**
     * Make authenticated API request
     */
    async apiRequest(endpoint, options = {}) {
        if (!this.authToken) {
            throw new Error('Not authenticated');
        }
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.authToken}`
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        const response = await fetch(`${this.apiBaseUrl}${endpoint}`, mergedOptions);
        
        if (response.status === 401) {
            // Token expired or invalid
            this.handleLogout();
            throw new Error('Authentication expired. Please login again.');
        }
        
        return response;
    }
    
    // Section data loading methods would be implemented here
    // For brevity, these are stubbed out for now
    
    async loadTrainerDashboard() {
        console.log('Loading trainer dashboard data...');
        // This would fetch stats, recent activities, etc.
    }
    
    async loadClientsData() {
        console.log('Loading clients data...');
        // This would fetch trainer's clients
    }
    
    async loadPlansData() {
        console.log('Loading plans data...');
        // This would fetch workout plans
    }
    
    async loadVideosData() {
        console.log('Loading videos data...');
        // This would fetch workout videos
    }
    
    async loadClientDashboard() {
        console.log('Loading client dashboard data...');
        // This would fetch client's dashboard data
    }
    
    async loadClientPlans() {
        console.log('Loading client plans data...');
        // This would fetch client's assigned plans
    }
    
    async loadClientProgress() {
        console.log('Loading client progress data...');
        // This would fetch client's progress data
    }
    
    async handleAddClient() {
        const clientEmail = document.getElementById('client-email').value;
        if (!clientEmail) {
            this.showToast('Please enter client email', 'error');
            return;
        }
        
        // This would add a client to trainer's list
        console.log('Adding client:', clientEmail);
        this.closeModal('add-client-modal');
        this.showToast('Client invitation sent', 'success');
    }
    
    async handleCreatePlan() {
        const title = document.getElementById('plan-title').value;
        const clientId = document.getElementById('plan-client').value;
        
        if (!title || !clientId) {
            this.showToast('Please fill required fields', 'error');
            return;
        }
        
        // This would create a new workout plan
        console.log('Creating plan:', title, 'for client:', clientId);
        this.closeModal('create-plan-modal');
        this.showToast('Plan created successfully', 'success');
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new WorkoutDashboardApp();
});
