// ==================== Common Functionality ====================
document.addEventListener('DOMContentLoaded', function() {
    // Role selection (on login page)
    const roleButtons = document.querySelectorAll('.role-btn');
    if (roleButtons.length > 0) {
        roleButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                roleButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                const emailInput = document.getElementById('email');
                if (this.dataset.role === 'student') {
                    emailInput.placeholder = 'student@student.edu';
                } else {
                    emailInput.placeholder = 'faculty@university.edu';
                }
            });
        });
    }

    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const role = document.querySelector('.role-btn.active').dataset.role;

            try {
                const response = await fetch("http://127.0.0.1:8000/api/auth/login/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        username: email,
                        password: password
                    }),
                });

                if (!response.ok) {
                    throw new Error("Invalid credentials");
                }

                const data = await response.json();

                // Save tokens + user info
                localStorage.setItem("access", data.access);
                localStorage.setItem("refresh", data.refresh);

                localStorage.setItem("currentUser", JSON.stringify({
                    email: email,
                    role: role,
                    name: email
                }));

                // Redirect
                window.location.href = role === 'faculty' ? 'faculty.html' : 'student.html';

            } catch (error) {
                alert("Login failed: " + error.message);
            }
        });
    }

    // Logout
    const logoutBtns = document.querySelectorAll('#logoutBtn');
    logoutBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            localStorage.removeItem('currentUser');
            window.location.href = 'index.html';
        });
    });

    // Welcome message
    const welcomeElements = document.querySelectorAll('.welcome');
    if (welcomeElements.length > 0) {
        const userData = JSON.parse(localStorage.getItem('currentUser'));
        if (!userData) {
            window.location.href = 'index.html';
            return;
        }

        welcomeElements.forEach(el => {
            el.textContent = `Welcome, ${userData.name}`;
        });
    }
});

// ==================== Student Dashboard Logic ====================
async function loadProjects() {
    const projectsContainer = document.getElementById("projectsContainer");
    if (!projectsContainer) return;

    try {
        const token = localStorage.getItem("access");
        const response = await fetch("http://127.0.0.1:8000/api/projects/", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error("Failed to load projects");

        const projects = await response.json();

        if (projects.length === 0) {
            projectsContainer.innerHTML = `
                <div class="empty-state">
                    <h2>No Projects Available</h2>
                    <p>There are currently no projects available for application.</p>
                </div>
            `;
            return;
        }

        projectsContainer.innerHTML = "";
        projects.forEach(project => {
            const projectCard = document.createElement("div");
            projectCard.classList.add("project-card");
            projectCard.innerHTML = `
                <h3>${project.title}</h3>
                <p>${project.description}</p>
                <button class="apply-btn" data-id="${project.id}">Apply</button>
            `;
            projectsContainer.appendChild(projectCard);
        });

        // Apply button logic
        document.querySelectorAll(".apply-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const projectId = btn.dataset.id;
                try {
                    const applyResponse = await fetch("http://127.0.0.1:8000/api/applications/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${token}`
                        },
                        body: JSON.stringify({ project: projectId })
                    });

                    if (!applyResponse.ok) throw new Error("Failed to apply");

                    alert("Application submitted successfully!");
                } catch (error) {
                    alert("Error: " + error.message);
                }
            });
        });

    } catch (error) {
        console.error("Error loading projects:", error);
    }
}
document.addEventListener("DOMContentLoaded", loadProjects);

// ==================== Faculty Dashboard Logic ====================
async function loadFacultyDashboard() {
    const facultyContainer = document.getElementById("facultyProjectsContainer");
    if (!facultyContainer) return;

    try {
        const token = localStorage.getItem("access");
        const response = await fetch("http://127.0.0.1:8000/api/projects/my/", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error("Failed to load faculty projects");

        const projects = await response.json();

        // Stats counters
        const total = projects.length;
        const approved = projects.filter(p => p.status === "approved").length;
        const pending = projects.filter(p => p.status === "pending").length;
        const applications = projects.reduce((sum, p) => sum + (p.applications_count || 0), 0);

        document.querySelector(".stat-card:nth-child(1) .count").textContent = total;
        document.querySelector(".stat-card:nth-child(2) .count").textContent = approved;
        document.querySelector(".stat-card:nth-child(3) .count").textContent = pending;
        document.querySelector(".stat-card:nth-child(4) .count").textContent = applications;

        // Render project list
        facultyContainer.innerHTML = "";
        if (projects.length === 0) {
            facultyContainer.innerHTML = `
                <div class="empty-state">
                    <h2>No Projects Yet</h2>
                    <p>You haven't submitted any project proposals yet.</p>
                </div>
            `;
            return;
        }

        projects.forEach(project => {
            const projectCard = document.createElement("div");
            projectCard.classList.add("project-card");
            projectCard.innerHTML = `
                <h3>${project.title}</h3>
                <p>${project.description}</p>
                <p><strong>Status:</strong> ${project.status}</p>
                <p><strong>Applications:</strong> ${project.applications_count || 0}</p>
            `;
            facultyContainer.appendChild(projectCard);
        });

    } catch (error) {
        console.error("Error loading faculty dashboard:", error);
    }
}
document.addEventListener("DOMContentLoaded", loadFacultyDashboard);
