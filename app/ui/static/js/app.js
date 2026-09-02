// Show user info in nav
const userName = localStorage.getItem('user_name');
const userRole = localStorage.getItem('user_role');
const userInfo = document.getElementById('user-info');
if (userInfo && userName) {
    const roleEmoji = userRole === 'admin' ? '👑' : userRole === 'manager' ? '📊' : '🏪';
    userInfo.textContent = `${roleEmoji} ${userName} (${userRole})`;
}

// Logout function
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_role');
    window.location.href = '/login';
}
