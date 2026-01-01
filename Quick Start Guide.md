# Quick Start Guide - Dating App Development
## Get Started in 30 Minutes

This guide will help you set up your development environment and create the initial project structure.

---

## Prerequisites Checklist

- [ ] **Operating System**: Windows 10/11, macOS, or Linux
- [ ] **RAM**: Minimum 8GB (16GB recommended)
- [ ] **Storage**: At least 20GB free space
- [ ] **Internet**: Stable connection for downloads and testing

---

## Step 1: Install Development Tools (15 minutes)

### 1.1 Install Flutter

**Windows:**
```powershell
# Download Flutter SDK
# Visit: https://flutter.dev/docs/get-started/install/windows
# Extract to C:\src\flutter

# Add to PATH
# Add C:\src\flutter\bin to your system PATH

# Verify installation
flutter doctor
```

**macOS:**
```bash
# Install via Homebrew
brew install --cask flutter

# Verify installation
flutter doctor
```

**Linux:**
```bash
# Download and extract
cd ~/development
git clone https://github.com/flutter/flutter.git -b stable
export PATH="$PATH:`pwd`/flutter/bin"

# Verify installation
flutter doctor
```

### 1.2 Install Node.js

**All Platforms:**
1. Visit: https://nodejs.org/
2. Download LTS version (20.x)
3. Install with default settings
4. Verify:
```bash
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x
```

### 1.3 Install VS Code

1. Visit: https://code.visualstudio.com/
2. Download and install
3. Install extensions:
   - Flutter (Dart)
   - ESLint
   - Prettier
   - GitLens

### 1.4 Install Git

**Windows:**
- Download: https://git-scm.com/download/win
- Install with default settings

**macOS:**
```bash
brew install git
```

**Linux:**
```bash
sudo apt-get install git  # Ubuntu/Debian
```

---

## Step 2: Set Up Database (10 minutes)

### Option A: Supabase (Recommended for MVP)

1. Visit: https://supabase.com
2. Sign up (free account)
3. Create new project
4. Note your credentials:
   - Project URL
   - API Key (anon/public)
   - Database password

### Option B: Local PostgreSQL

**Windows:**
```powershell
# Download PostgreSQL from https://www.postgresql.org/download/windows/
# Install with default settings
# Remember the postgres user password
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

---

## Step 3: Initialize Projects (5 minutes)

### 3.1 Create Flutter Project

```bash
# Create project
flutter create dating_app
cd dating_app

# Verify it works
flutter run -d chrome  # For web
# OR
flutter run  # For mobile (requires emulator/device)
```

### 3.2 Create Backend Project

```bash
# Create directory
mkdir dating_app_backend
cd dating_app_backend

# Initialize Node.js project
npm init -y

# Install TypeScript
npm install -D typescript @types/node @types/express ts-node nodemon
npm install express cors dotenv

# Create tsconfig.json
npx tsc --init

# Create basic structure
mkdir -p src/{config,models,routes,controllers,services,middleware,utils}
```

### 3.3 Initialize Git Repository

```bash
# In project root
git init
echo "node_modules/" >> .gitignore
echo ".dart_tool/" >> .gitignore
echo ".flutter-plugins" >> .gitignore
echo ".env" >> .gitignore

# Create initial commit
git add .
git commit -m "Initial project setup"
```

---

## Step 4: Configure Development Environment

### 4.1 Backend Environment Variables

Create `dating_app_backend/.env`:
```env
# Server
PORT=3000
NODE_ENV=development

# Database (Supabase)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_EXPIRES_IN=7d

# Firebase (get from Firebase Console)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email

# Azure Blob Storage (optional for now)
AZURE_STORAGE_ACCOUNT=your-account
AZURE_STORAGE_KEY=your-key
AZURE_STORAGE_CONTAINER=profiles

# Redis (optional for now)
REDIS_URL=redis://localhost:6379
```

### 4.2 Flutter Configuration

Create `dating_app/lib/config/app_config.dart`:
```dart
class AppConfig {
  // Backend API
  static const String apiBaseUrl = 'http://localhost:3000/api/v1';
  
  // Firebase (add your config)
  // static const String firebaseApiKey = 'your-key';
  
  // Environment
  static const String environment = 'development';
}
```

---

## Step 5: Test Your Setup

### 5.1 Test Backend

```bash
cd dating_app_backend

# Create src/server.ts
# (Basic Express server)

# Run
npm run dev  # If you set up nodemon
# OR
npx ts-node src/server.ts
```

### 5.2 Test Flutter

```bash
cd dating_app
flutter pub get
flutter run -d chrome
```

---

## Step 6: Install Essential Packages

### 6.1 Flutter Packages

```bash
cd dating_app
flutter pub add provider http dio shared_preferences
```

### 6.2 Backend Packages

```bash
cd dating_app_backend
npm install express cors dotenv
npm install -D @types/express @types/cors
```

---

## Next Steps

1. ✅ **Set up database schema** - See Database Schema.txt
2. ✅ **Implement authentication** - Firebase Auth + JWT
3. ✅ **Create profile screens** - Flutter UI
4. ✅ **Build API endpoints** - Express routes
5. ✅ **Connect frontend to backend** - API integration

---

## Troubleshooting

### Flutter Issues

**Problem:** `flutter doctor` shows errors
**Solution:** Follow the instructions shown by `flutter doctor`

**Problem:** Can't run on iOS (macOS only)
**Solution:** Install Xcode from App Store

**Problem:** Can't run on Android
**Solution:** Install Android Studio and set up Android SDK

### Node.js Issues

**Problem:** `npm` command not found
**Solution:** Restart terminal after installing Node.js

**Problem:** Port 3000 already in use
**Solution:** Change PORT in .env file

### Database Issues

**Problem:** Can't connect to Supabase
**Solution:** Check your connection string and firewall settings

**Problem:** PostgreSQL connection refused
**Solution:** Ensure PostgreSQL service is running

---

## Development Workflow

### Daily Routine

1. **Morning:**
   ```bash
   # Start backend
   cd dating_app_backend
   npm run dev
   
   # Start Flutter (new terminal)
   cd dating_app
   flutter run
   ```

2. **During Development:**
   - Make changes
   - Hot reload (Flutter: `r` in terminal, VS Code: Save)
   - Test in browser/emulator

3. **End of Day:**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push  # If using remote repository
   ```

---

## Resources

- **Flutter Docs:** https://flutter.dev/docs
- **Node.js Docs:** https://nodejs.org/docs
- **Supabase Docs:** https://supabase.com/docs
- **VS Code:** https://code.visualstudio.com/docs

---

**Ready to code?** Start with authentication implementation!


