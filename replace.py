import sys
with open(r'C:\Users\pragy\Downloads\HerWell-\backend\static\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                <section id="view-login" class="app-view">
                    <div class="auth-card-container">
                        <div class="auth-brand-header">
                            <div class="brand-emoji">🌸</div>
                            <h2>Welcome to HerWellness Hub</h2>
                            <p>Your personalized companion for cycle tracking, mental wellness, and cycle-synced fitness.</p>
                        </div>

                        <!-- Auth Tabs -->
                        <div class="auth-tabs">
                            <button class="auth-tab-btn active" id="tab-login-btn" onclick="switchAuthTab('login')">Log In</button>
                            <button class="auth-tab-btn" id="tab-signup-btn" onclick="switchAuthTab('signup')">Sign Up</button>
                        </div>

                        <!-- Alert Messages -->
                        <div id="auth-alert" class="alert-message hidden"></div>

                        <!-- Login Form -->
                        <form id="form-login" class="auth-form" onsubmit="handleLoginSubmit(event)">
                            <div class="form-group">
                                <label for="login-email">Email Address</label>
                                <input type="email" id="login-email" required placeholder="you@example.com">
                            </div>
                            <div class="form-group">
                                <label for="login-password">Password</label>
                                <input type="password" id="login-password" required placeholder="••••••••">
                            </div>
                            <button type="submit" class="btn btn-primary btn-block">Sign In</button>
                        </form>

                        <!-- Signup Form -->
                        <form id="form-signup" class="auth-form hidden" onsubmit="handleSignupSubmit(event)">
                            <div class="form-group">
                                <label for="signup-email">Email Address</label>
                                <input type="email" id="signup-email" required placeholder="you@example.com">
                            </div>
                            <div class="form-group">
                                <label for="signup-password">Create Password (min 6 chars)</label>
                                <input type="password" id="signup-password" required minlength="6" placeholder="••••••••">
                            </div>
                            <button type="submit" class="btn btn-primary btn-block">Create Account</button>
                        </form>

                        <div class="auth-divider">
                            <span>OR</span>
                        </div>

                        <!-- Quick Hackathon Demo Mode -->
                        <button class="btn btn-secondary btn-block demo-btn" onclick="enableDemoMode()">
                            ✨ Instant Demo Mode (No Login Required)
                        </button>
                    </div>
                </section>'''

replacement = '''                <section id="view-login" class="app-view">
                    <div class="login-split-container">
                        <div class="login-left-panel">
                            <div class="auth-card-container">
                                <div class="auth-brand-header">
                                    <div class="brand-emoji">🌸</div>
                                    <h2>Welcome to HerWellness Hub</h2>
                                    <p>Your personalized companion for cycle tracking, mental wellness, and cycle-synced fitness.</p>
                                </div>

                                <!-- Auth Tabs -->
                                <div class="auth-tabs">
                                    <button class="auth-tab-btn active" id="tab-login-btn" onclick="switchAuthTab('login')">Log In</button>
                                    <button class="auth-tab-btn" id="tab-signup-btn" onclick="switchAuthTab('signup')">Sign Up</button>
                                </div>

                                <!-- Alert Messages -->
                                <div id="auth-alert" class="alert-message hidden"></div>

                                <!-- Login Form -->
                                <form id="form-login" class="auth-form" onsubmit="handleLoginSubmit(event)">
                                    <div class="form-group">
                                        <label for="login-email">Email Address</label>
                                        <input type="email" id="login-email" required placeholder="you@example.com">
                                    </div>
                                    <div class="form-group">
                                        <label for="login-password">Password</label>
                                        <input type="password" id="login-password" required placeholder="••••••••">
                                    </div>
                                    <button type="submit" class="btn btn-primary btn-block">Sign In</button>
                                </form>

                                <!-- Signup Form -->
                                <form id="form-signup" class="auth-form hidden" onsubmit="handleSignupSubmit(event)">
                                    <div class="form-group">
                                        <label for="signup-email">Email Address</label>
                                        <input type="email" id="signup-email" required placeholder="you@example.com">
                                    </div>
                                    <div class="form-group">
                                        <label for="signup-password">Create Password (min 6 chars)</label>
                                        <input type="password" id="signup-password" required minlength="6" placeholder="••••••••">
                                    </div>
                                    <button type="submit" class="btn btn-primary btn-block">Create Account</button>
                                </form>

                        <div class="auth-divider">
                            <span>OR</span>
                        </div>

                        <!-- Quick Hackathon Demo Mode -->
                        <button class="btn btn-secondary btn-block demo-btn" onclick="enableDemoMode()">
                            ✨ Instant Demo Mode (No Login Required)
                        </button>
                            </div>
                        </div>
                        <div class="login-right-panel">
                            <div class="animated-gradient-bg"></div>
                            <div class="login-right-content">
                                <div class="login-quote-box glass-panel">
                                    <h3>Empowering your everyday wellness.</h3>
                                    <p>Track, understand, and thrive with HerWellness Hub.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>'''

# Normalize newlines
content = content.replace('\r\n', '\n')
target = target.replace('\r\n', '\n')

new_content = content.replace(target, replacement)
if new_content == content:
    print("Warning: Content was not replaced!")
    sys.exit(1)

with open(r'C:\Users\pragy\Downloads\HerWell-\backend\static\index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
    print("Success")
