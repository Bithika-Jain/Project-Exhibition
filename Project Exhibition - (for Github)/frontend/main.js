document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Role selection
    const roleButtons = document.querySelectorAll('.role-btn');
    roleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            roleButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Login form submitted');

            const username = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const role = document.querySelector('.role-btn.active').dataset.role;

            try {
                const response = await fetch("http://127.0.0.1:8000/api/auth/login/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    }),
                });

                if (!response.ok) {
                    throw new Error(`Login failed: Invalid credentials`);
                }

                const data = await response.json();
                console.log('Login successful:', data);

                // Verify user's actual role by checking their profile
                const actualRole = await verifyUserRole(data.access);
                
                if (actualRole !== role) {
                    throw new Error(`Access denied: You are a ${actualRole}, not a ${role}`);
                }

                // Save tokens and user info
                localStorage.setItem("access", data.access);
                localStorage.setItem("refresh", data.refresh);
                localStorage.setItem("currentUser", JSON.stringify({
                    username: username,
                    role: actualRole,
                    name: username
                }));

                // Redirect based on actual role
                if (actualRole === 'faculty') {
                    window.location.href = 'faculty.html';
                } else if (actualRole === 'student') {
                    window.location.href = 'student.html';
                } else {
                    throw new Error('Invalid user role');
                }

            } catch (error) {
                console.error("Login failed:", error);
                alert("Login failed: " + error.message);
            }
        });
    }

    // Logout functionality
    const logoutBtns = document.querySelectorAll('#logoutBtn');
    logoutBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            localStorage.clear();
            window.location.href = 'index.html';
        });
    });

    // Welcome message
    const welcomeElements = document.querySelectorAll('.welcome');
    if (welcomeElements.length > 0) {
        const userData = JSON.parse(localStorage.getItem('currentUser'));
        if (userData) {
            welcomeElements.forEach(el => {
                el.textContent = `Welcome, ${userData.name}`;
            });
        }
    }
});

// Verify user role by checking their profiles
async function verifyUserRole(token) {
    try {
        // Check if user is a student
        const studentResponse = await fetch("http://127.0.0.1:8000/api/students/", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (studentResponse.ok) {
            const students = await studentResponse.json();
            const currentUserId = getCurrentUserId(token);
            if (students.some(student => student.user === currentUserId)) {
                return 'student';
            }
        }

        // Check if user is faculty
        const facultyResponse = await fetch("http://127.0.0.1:8000/api/faculty/", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (facultyResponse.ok) {
            const faculties = await facultyResponse.json();
            const currentUserId = getCurrentUserId(token);
            if (faculties.some(faculty => faculty.user === currentUserId)) {
                return 'faculty';
            }
        }

        throw new Error('Unable to determine user role');
    } catch (error) {
        console.error('Role verification failed:', error);
        throw new Error('Role verification failed');
    }
}

// Helper function to get user ID from JWT token
function getCurrentUserId(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.user_id;
    } catch (e) {
        return null;
    }
}

// Load projects for student dashboard
async function loadProjects() {
    const projectsList = document.getElementById("projectsList");
    if (!projectsList) return;

    // Check if user is actually a student
    const userData = JSON.parse(localStorage.getItem('currentUser'));
    if (!userData || userData.role !== 'student') {
        window.location.href = 'index.html';
        return;
    }

    console.log('Loading projects...');
    
    try {
        const token = localStorage.getItem("access");
        
        const response = await fetch("http://127.0.0.1:8000/api/projects/", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.status === 403) {
            alert('Access denied: Students only');
            window.location.href = 'index.html';
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const projects = await response.json();
        console.log('Projects loaded:', projects);

        // Filter only approved projects
        const approvedProjects = projects.filter(project => project.is_approved === true);

        if (approvedProjects.length === 0) {
            projectsList.innerHTML = '<div class="empty-state"><h3>No Approved Projects</h3><p>No projects are currently approved for applications.</p></div>';
            return;
        }

        projectsList.innerHTML = '';
        approvedProjects.forEach(project => {
            const projectCard = document.createElement('div');
            projectCard.className = 'project-card';
            
            const seatsInfo = project.seats_available > 0 ? 
                `<span style="color: green;">Seats Available: ${project.seats_available}</span>` :
                `<span style="color: red;">No Seats Available</span>`;
            
            projectCard.innerHTML = `
                <h3>${project.title}</h3>
                <p><strong>Abstract:</strong> ${project.abstract || 'No abstract provided'}</p>
                <p><strong>Timeline:</strong> ${project.timeline || 'Not specified'}</p>
                <p><strong>Difficulty:</strong> ${project.difficulty}</p>
                <p><strong>Total Seats:</strong> ${project.seats}</p>
                <p>${seatsInfo}</p>
                <button class="apply-btn" data-id="${project.id}" ${project.seats_available <= 0 ? 'disabled' : ''}>
                    ${project.seats_available > 0 ? 'Apply' : 'Full'}
                </button>
            `;
            projectsList.appendChild(projectCard);
        });

        // Apply button logic
        document.querySelectorAll(".apply-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                if (btn.disabled) return;
                
                const projectId = btn.dataset.id;
                try {
                    btn.disabled = true;
                    btn.textContent = 'Applying...';
                    
                    const applyResponse = await fetch("http://127.0.0.1:8000/api/applications/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${token}`
                        },
                        body: JSON.stringify({ project: parseInt(projectId) })
                    });

                    if (!applyResponse.ok) {
                        const errorData = await applyResponse.json();
                        throw new Error(errorData.detail || errorData.error || "Failed to apply");
                    }

                    alert("Application submitted successfully!");
                    loadProjects(); // Reload to update seat count
                    loadMyApplications(); // Reload applications
                    
                } catch (error) {
                    console.error("Application error:", error);
                    alert("Error: " + error.message);
                    btn.disabled = false;
                    btn.textContent = 'Apply';
                }
            });
        });

    } catch (error) {
        console.error('Error loading projects:', error);
        projectsList.innerHTML = '<div class="empty-state"><h3>Error Loading Projects</h3><p>Please refresh the page or contact support.</p></div>';
    }
}

// Load my applications for student
async function loadMyApplications() {
    const myAppsList = document.getElementById("myApplicationsList");
    if (!myAppsList) return;

    try {
        const token = localStorage.getItem("access");
        const response = await fetch("http://127.0.0.1:8000/api/applications/my/", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            const applications = await response.json();
            
            if (applications.length === 0) {
                myAppsList.innerHTML = `<p class="empty-state">You haven't applied to any projects yet.</p>`;
                return;
            }

            myAppsList.innerHTML = "";
            applications.forEach(app => {
                const appDiv = document.createElement("div");
                appDiv.classList.add("application-card");
                
                const statusColor = {
                    'pending': '#f39c12',
                    'shortlisted': '#3498db',
                    'selected': '#2ecc71',
                    'rejected': '#e74c3c'
                };
                
                appDiv.innerHTML = `
                    <h4>Application Status</h4>
                    <p><strong>Status:</strong> <span style="color: ${statusColor[app.status] || '#333'}">${app.status}</span></p>
                    <p><strong>Applied:</strong> ${new Date(app.applied_at).toLocaleDateString()}</p>
                `;
                myAppsList.appendChild(appDiv);
            });
        } else {
            myAppsList.innerHTML = `<p class="error">Could not load applications.</p>`;
        }
    } catch (error) {
        console.error("Error loading applications:", error);
        myAppsList.innerHTML = `<p class="error">Error loading applications.</p>`;
    }
}

// Load projects when page loads (for students)
document.addEventListener("DOMContentLoaded", loadProjects);
document.addEventListener("DOMContentLoaded", loadMyApplications);

// Faculty dashboard functionality
async function loadFacultyDashboard() {
    const facultyContainer = document.getElementById("facultyProjectsContainer");
    if (!facultyContainer) return;

    // Check if user is actually faculty
    const userData = JSON.parse(localStorage.getItem('currentUser'));
    if (!userData || userData.role !== 'faculty') {
        window.location.href = 'index.html';
        return;
    }

    try {
        const token = localStorage.getItem("access");
        
        const response = await fetch("http://127.0.0.1:8000/api/projects/my/", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.status === 403) {
            alert('Access denied: Faculty only');
            window.location.href = 'index.html';
            return;
        }

        if (!response.ok) {
            throw new Error("Failed to load faculty projects");
        }

        const projects = await response.json();

        // Update stats
        const total = projects.length;
        const approved = projects.filter(p => p.is_approved === true).length;
        const pending = projects.filter(p => p.status === "pending").length;

        // Get applications count
        let totalApplications = 0;
        try {
            const appsResponse = await fetch("http://127.0.0.1:8000/api/applications/faculty_applications/", {
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });
            if (appsResponse.ok) {
                const applications = await appsResponse.json();
                totalApplications = applications.length;
            }
        } catch (e) {
            console.log("Could not fetch applications count");
        }

        // Update stat cards
        const statCards = document.querySelectorAll(".stat-card .count");
        if (statCards.length >= 4) {
            statCards[0].textContent = total;
            statCards[1].textContent = approved;
            statCards[2].textContent = pending;
            statCards[3].textContent = totalApplications;
        }

        // Show/hide empty state
        const emptyState = document.querySelector(".empty-state");
        if (projects.length > 0 && emptyState) {
            emptyState.style.display = 'none';
        } else if (projects.length === 0 && emptyState) {
            emptyState.style.display = 'block';
        }

    } catch (error) {
        console.error("Error loading faculty dashboard:", error);
    }
}

// Load pending projects for committee review
async function loadPendingProjects() {
    const reviewProjectsList = document.getElementById("reviewProjectsList");
    if (!reviewProjectsList) return;

    try {
        const token = localStorage.getItem("access");
        const response = await fetch("http://127.0.0.1:8000/api/projects/pending_review/", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            const projects = await response.json();
            
            if (projects.length === 0) {
                reviewProjectsList.innerHTML = `<p>No projects pending review.</p>`;
                document.getElementById("noReviewProjects").style.display = 'block';
                return;
            }

            document.getElementById("noReviewProjects").style.display = 'none';
            reviewProjectsList.innerHTML = "";
            
            projects.forEach(project => {
                const projectDiv = document.createElement("div");
                projectDiv.className = "project-review-card";
                projectDiv.innerHTML = `
                    <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                        <h4>${project.title}</h4>
                        <p><strong>Faculty:</strong> ${project.faculty_name || 'Unknown'}</p>
                        <p><strong>Abstract:</strong> ${project.abstract}</p>
                        <p><strong>Timeline:</strong> ${project.timeline}</p>
                        <p><strong>Difficulty:</strong> ${project.difficulty}</p>
                        <p><strong>Seats:</strong> ${project.seats}</p>
                        <div style="margin-top: 10px;">
                            <button onclick="approveProject(${project.id})" style="background: #2ecc71; color: white; border: none; padding: 8px 15px; margin-right: 10px; border-radius: 4px; cursor: pointer;">
                                Approve
                            </button>
                            <button onclick="rejectProject(${project.id})" style="background: #e74c3c; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer;">
                                Reject
                            </button>
                        </div>
                    </div>
                `;
                reviewProjectsList.appendChild(projectDiv);
            });
        } else {
            reviewProjectsList.innerHTML = `<p>Error loading projects for review.</p>`;
        }
    } catch (error) {
        console.error("Error loading pending projects:", error);
        reviewProjectsList.innerHTML = `<p>Error loading projects for review.</p>`;
    }
}

// GLOBAL FUNCTIONS - These can be called from HTML onclick
window.approveProject = async function(projectId) {
    try {
        const token = localStorage.getItem("access");
        const response = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/approve/`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            alert("Project approved successfully!");
            loadPendingProjects(); // Reload the list
        } else {
            const error = await response.json();
            alert("Error: " + (error.error || "Failed to approve project"));
        }
    } catch (error) {
        console.error("Error approving project:", error);
        alert("Error approving project");
    }
};

window.rejectProject = async function(projectId) {
    try {
        const token = localStorage.getItem("access");
        const response = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/reject/`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            alert("Project rejected successfully!");
            loadPendingProjects(); // Reload the list
        } else {
            const error = await response.json();
            alert("Error: " + (error.error || "Failed to reject project"));
        }
    } catch (error) {
        console.error("Error rejecting project:", error);
        alert("Error rejecting project");
    }
};

// Load faculty dashboard when page loads
document.addEventListener("DOMContentLoaded", loadFacultyDashboard);
document.addEventListener("DOMContentLoaded", loadPendingProjects);