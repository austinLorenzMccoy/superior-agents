document.addEventListener('DOMContentLoaded', function() {
    // Auth button handlers
    const loginBtn = document.querySelector('.auth-buttons .btn-outline');
    const signupBtn = document.querySelector('.auth-buttons .btn-primary');
    
    if (loginBtn) {
        loginBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Show login modal or redirect to login page
            showAuthModal('login');
        });
    }
    
    if (signupBtn) {
        signupBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Show signup modal or redirect to signup page
            showAuthModal('signup');
        });
    }
    // Mobile menu toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    const authButtons = document.querySelector('.auth-buttons');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            
            // Create mobile menu if it doesn't exist
            if (!document.querySelector('.mobile-menu')) {
                const mobileMenu = document.createElement('div');
                mobileMenu.className = 'mobile-menu';
                
                // Clone navigation links
                const navLinksClone = navLinks.cloneNode(true);
                mobileMenu.appendChild(navLinksClone);
                
                // Clone auth buttons
                const authButtonsClone = authButtons.cloneNode(true);
                mobileMenu.appendChild(authButtonsClone);
                
                // Add to DOM
                document.querySelector('header').appendChild(mobileMenu);
                
                // Add styles
                mobileMenu.style.display = 'none';
                mobileMenu.style.position = 'absolute';
                mobileMenu.style.top = '80px';
                mobileMenu.style.left = '0';
                mobileMenu.style.width = '100%';
                mobileMenu.style.backgroundColor = 'white';
                mobileMenu.style.padding = '20px';
                mobileMenu.style.boxShadow = '0 5px 10px rgba(0, 0, 0, 0.1)';
                mobileMenu.style.zIndex = '99';
                
                // Style the cloned elements
                navLinksClone.style.display = 'flex';
                navLinksClone.style.flexDirection = 'column';
                navLinksClone.style.gap = '15px';
                navLinksClone.style.marginBottom = '20px';
                
                authButtonsClone.style.display = 'flex';
                authButtonsClone.style.flexDirection = 'column';
                authButtonsClone.style.gap = '10px';
            }
            
            // Toggle mobile menu
            const mobileMenu = document.querySelector('.mobile-menu');
            mobileMenu.style.display = mobileMenu.style.display === 'none' ? 'block' : 'none';
        });
    }
    
    // Performance tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            tabBtns.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Hide all tab contents
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Show the corresponding tab content
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Create placeholder charts
    createPlaceholderCharts();
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add animation on scroll
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature-card, .workflow-step, .stat-card');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('animate');
            }
        });
    };
    
    // Add animation class to CSS
    const style = document.createElement('style');
    style.textContent = `
        .feature-card, .workflow-step, .stat-card {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .feature-card.animate, .workflow-step.animate, .stat-card.animate {
            opacity: 1;
            transform: translateY(0);
        }
        
        .feature-card:nth-child(2), .workflow-step:nth-child(2) {
            transition-delay: 0.2s;
        }
        
        .feature-card:nth-child(3), .workflow-step:nth-child(3) {
            transition-delay: 0.4s;
        }
        
        .feature-card:nth-child(4), .workflow-step:nth-child(4) {
            transition-delay: 0.6s;
        }
        
        .feature-card:nth-child(5), .workflow-step:nth-child(5) {
            transition-delay: 0.8s;
        }
        
        .feature-card:nth-child(6) {
            transition-delay: 1s;
        }
    `;
    document.head.appendChild(style);
    
    // Run animation on scroll
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Run once on load
});

// Function to create placeholder charts
function createPlaceholderCharts() {
    // Create placeholder for BTC chart
    const btcChart = document.getElementById('btc-chart-placeholder');
    if (btcChart) {
        btcChart.innerHTML = createSVGChart('BTC Dominant Performance', [65, 59, 80, 81, 56, 55, 72, 60, 76, 85, 90, 85]);
    }
    
    // Create placeholders for other regime charts if they exist
    const altChart = document.getElementById('alt-season');
    if (altChart) {
        const altChartPlaceholder = altChart.querySelector('.chart-placeholder');
        if (altChartPlaceholder) {
            altChartPlaceholder.innerHTML = createSVGChart('Alt Season Performance', [45, 59, 80, 91, 76, 85, 72, 78, 82, 95, 89, 80]);
        }
    }
    
    const neutralChart = document.getElementById('neutral');
    if (neutralChart) {
        const neutralChartPlaceholder = neutralChart.querySelector('.chart-placeholder');
        if (neutralChartPlaceholder) {
            neutralChartPlaceholder.innerHTML = createSVGChart('Neutral Market Performance', [55, 49, 60, 71, 66, 55, 62, 58, 72, 65, 75, 70]);
        }
    }
}

// Function to create a simple SVG line chart
function createSVGChart(title, data) {
    const width = 800;
    const height = 300;
    const padding = 40;
    const chartWidth = width - (padding * 2);
    const chartHeight = height - (padding * 2);
    
    // Calculate points
    const points = [];
    const maxValue = Math.max(...data);
    const xStep = chartWidth / (data.length - 1);
    
    for (let i = 0; i < data.length; i++) {
        const x = padding + (i * xStep);
        const y = height - padding - ((data[i] / maxValue) * chartHeight);
        points.push(`${x},${y}`);
    }
    
    // Create SVG
    return `
        <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}">
            <text x="${width / 2}" y="20" text-anchor="middle" font-size="16" font-weight="bold">${title}</text>
            
            <!-- X and Y axes -->
            <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#adb5bd" stroke-width="2" />
            <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="#adb5bd" stroke-width="2" />
            
            <!-- Data line -->
            <polyline points="${points.join(' ')}" fill="none" stroke="#3a86ff" stroke-width="3" />
            
            <!-- Data points -->
            ${data.map((value, i) => {
                const x = padding + (i * xStep);
                const y = height - padding - ((value / maxValue) * chartHeight);
                return `<circle cx="${x}" cy="${y}" r="4" fill="#3a86ff" />`;
            }).join('')}
            
            <!-- Months on X-axis -->
            ${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((month, i) => {
                const x = padding + (i * xStep);
                return `<text x="${x}" y="${height - padding + 20}" text-anchor="middle" font-size="12">${month}</text>`;
            }).join('')}
            
            <!-- Values on Y-axis -->
            ${[0, 25, 50, 75, 100].map((value, i) => {
                const y = height - padding - ((value / 100) * chartHeight);
                return `
                    <text x="${padding - 10}" y="${y}" text-anchor="end" font-size="12">${value}%</text>
                    <line x1="${padding}" y1="${y}" x2="${width - padding}" y2="${y}" stroke="#e9ecef" stroke-width="1" />
                `;
            }).join('')}
        </svg>
    `;
}
