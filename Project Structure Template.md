# Project Structure Template
## Complete File Structure for Dating App

This document provides the complete project structure you should create for both frontend and backend.

---

## Complete Project Structure

```
dating-app/
│
├── dating_app/                    # Flutter Frontend
│   ├── lib/
│   │   ├── main.dart
│   │   │
│   │   ├── config/
│   │   │   ├── app_config.dart
│   │   │   ├── routes.dart
│   │   │   └── theme.dart
│   │   │
│   │   ├── models/
│   │   │   ├── user.dart
│   │   │   ├── profile.dart
│   │   │   ├── match.dart
│   │   │   ├── message.dart
│   │   │   └── api_response.dart
│   │   │
│   │   ├── services/
│   │   │   ├── api_service.dart
│   │   │   ├── auth_service.dart
│   │   │   ├── storage_service.dart
│   │   │   ├── socket_service.dart
│   │   │   ├── location_service.dart
│   │   │   └── notification_service.dart
│   │   │
│   │   ├── providers/
│   │   │   ├── auth_provider.dart
│   │   │   ├── user_provider.dart
│   │   │   ├── match_provider.dart
│   │   │   ├── chat_provider.dart
│   │   │   └── theme_provider.dart
│   │   │
│   │   ├── screens/
│   │   │   ├── splash/
│   │   │   │   └── splash_screen.dart
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── login_screen.dart
│   │   │   │   ├── register_screen.dart
│   │   │   │   └── forgot_password_screen.dart
│   │   │   │
│   │   │   ├── profile/
│   │   │   │   ├── profile_creation_screen.dart
│   │   │   │   ├── profile_edit_screen.dart
│   │   │   │   └── profile_view_screen.dart
│   │   │   │
│   │   │   ├── matches/
│   │   │   │   ├── discover_screen.dart
│   │   │   │   ├── matches_list_screen.dart
│   │   │   │   └── match_detail_screen.dart
│   │   │   │
│   │   │   ├── chat/
│   │   │   │   ├── conversations_list_screen.dart
│   │   │   │   ├── chat_screen.dart
│   │   │   │   └── video_call_screen.dart
│   │   │   │
│   │   │   ├── settings/
│   │   │   │   ├── settings_screen.dart
│   │   │   │   ├── preferences_screen.dart
│   │   │   │   └── privacy_screen.dart
│   │   │   │
│   │   │   └── home/
│   │   │       └── home_screen.dart
│   │   │
│   │   ├── widgets/
│   │   │   ├── common/
│   │   │   │   ├── custom_button.dart
│   │   │   │   ├── custom_text_field.dart
│   │   │   │   ├── loading_indicator.dart
│   │   │   │   └── error_widget.dart
│   │   │   │
│   │   │   ├── profile/
│   │   │   │   ├── profile_card.dart
│   │   │   │   ├── photo_gallery.dart
│   │   │   │   └── interest_chip.dart
│   │   │   │
│   │   │   ├── match/
│   │   │   │   ├── match_card.dart
│   │   │   │   ├── swipe_card.dart
│   │   │   │   └── match_filters.dart
│   │   │   │
│   │   │   └── chat/
│   │   │       ├── message_bubble.dart
│   │   │       ├── chat_input.dart
│   │   │       └── typing_indicator.dart
│   │   │
│   │   └── utils/
│   │       ├── constants.dart
│   │       ├── helpers.dart
│   │       ├── validators.dart
│   │       └── extensions.dart
│   │
│   ├── assets/
│   │   ├── images/
│   │   │   ├── logo.png
│   │   │   └── placeholder.png
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── test/
│   │   ├── unit/
│   │   ├── widget/
│   │   └── integration/
│   │
│   ├── pubspec.yaml
│   ├── .gitignore
│   └── README.md
│
├── dating_app_backend/            # Node.js Backend
│   ├── src/
│   │   ├── server.ts
│   │   │
│   │   ├── config/
│   │   │   ├── database.ts
│   │   │   ├── redis.ts
│   │   │   ├── firebase.ts
│   │   │   └── azure.ts
│   │   │
│   │   ├── models/
│   │   │   ├── User.ts
│   │   │   ├── Profile.ts
│   │   │   ├── Match.ts
│   │   │   ├── Message.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── routes/
│   │   │   ├── index.ts
│   │   │   ├── auth.routes.ts
│   │   │   ├── user.routes.ts
│   │   │   ├── match.routes.ts
│   │   │   ├── message.routes.ts
│   │   │   └── search.routes.ts
│   │   │
│   │   ├── controllers/
│   │   │   ├── auth.controller.ts
│   │   │   ├── user.controller.ts
│   │   │   ├── match.controller.ts
│   │   │   ├── message.controller.ts
│   │   │   └── search.controller.ts
│   │   │
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   ├── user.service.ts
│   │   │   ├── matchmaking.service.ts
│   │   │   ├── ai.service.ts
│   │   │   ├── storage.service.ts
│   │   │   └── notification.service.ts
│   │   │
│   │   ├── middleware/
│   │   │   ├── auth.middleware.ts
│   │   │   ├── validation.middleware.ts
│   │   │   ├── error.middleware.ts
│   │   │   └── rateLimit.middleware.ts
│   │   │
│   │   ├── utils/
│   │   │   ├── logger.ts
│   │   │   ├── errors.ts
│   │   │   ├── validators.ts
│   │   │   └── helpers.ts
│   │   │
│   │   └── types/
│   │       ├── express.d.ts
│   │       └── custom.d.ts
│   │
│   ├── database/
│   │   ├── migrations/
│   │   │   ├── 001_create_users.sql
│   │   │   ├── 002_create_profiles.sql
│   │   │   └── 003_create_matches.sql
│   │   │
│   │   ├── seeds/
│   │   │   └── seed_data.sql
│   │   │
│   │   └── schema.sql
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── .env
│   ├── .env.example
│   ├── package.json
│   ├── tsconfig.json
│   ├── .gitignore
│   └── README.md
│
├── docs/                          # Documentation
│   ├── api/
│   │   └── api_documentation.md
│   ├── database/
│   │   └── schema_diagram.md
│   └── deployment/
│       └── deployment_guide.md
│
└── README.md                      # Project root README
```

---

## Key Files to Create First

### 1. Flutter: `lib/main.dart`
```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/routes.dart';
import 'config/theme.dart';
import 'providers/auth_provider.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: MaterialApp(
        title: 'Dating App',
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        routes: AppRoutes.routes,
        initialRoute: AppRoutes.splash,
      ),
    );
  }
}
```

### 2. Backend: `src/server.ts`
```typescript
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { connectDatabase } from './config/database';
import authRoutes from './routes/auth.routes';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/v1/auth', authRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server
async function startServer() {
  try {
    await connectDatabase();
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
```

### 3. Backend: `package.json` Scripts
```json
{
  "scripts": {
    "dev": "nodemon --exec ts-node src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "jest",
    "lint": "eslint src/**/*.ts",
    "migrate": "ts-node database/migrations/run.ts"
  }
}
```

---

## Development Priority Order

### Week 1-2: Foundation
1. ✅ Project structure
2. ✅ Database schema
3. ✅ Basic authentication
4. ✅ API setup

### Week 3-4: Core Features
1. ✅ User registration/login
2. ✅ Profile creation
3. ✅ Basic matching
4. ✅ Simple messaging

### Week 5-6: Enhancement
1. ✅ Photo uploads
2. ✅ Real-time chat
3. ✅ Match filters
4. ✅ Push notifications

---

## File Naming Conventions

**Flutter:**
- Files: `snake_case.dart`
- Classes: `PascalCase`
- Variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

**Backend:**
- Files: `kebab-case.ts` or `camelCase.ts`
- Classes: `PascalCase`
- Functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/user-authentication

# Make changes
# ...

# Commit
git add .
git commit -m "feat: implement user authentication"

# Push
git push origin feature/user-authentication

# Merge to main (after review)
git checkout main
git merge feature/user-authentication
```

---

This structure provides a solid foundation for scalable development!


