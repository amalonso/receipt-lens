/**
 * Admin Navigation Helper
 * Adds admin menu to sidebar if user is admin
 */

function addAdminNavigation(user) {
    if (!user || !user.is_admin) {
        return;
    }

    const adminSection = document.getElementById('admin-nav-section');
    if (!adminSection) {
        return;
    }

    adminSection.style.display = 'block';
    adminSection.innerHTML = `
        <div style="height: 1px; background: rgba(255, 255, 255, 0.1); margin: 1rem 0;"></div>
        <div style="padding: 0.5rem 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: rgba(255, 255, 255, 0.5); letter-spacing: 0.05em;">
            Administración
        </div>
        <a href="/admin-dashboard.html" class="nav-item">
            <span class="icon">👑</span>
            <span>Panel de Admin</span>
        </a>
    `;
}
