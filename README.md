# Banking Complaint Agent — Group 6

## Prerequisites
- PostgreSQL 15+ (service must be running)
- Node.js 18+ and npm
- Java 21+ and Maven (for the backend, when implemented)

---

## 1. Database

Run scripts in order from the project root. Replace `postgres` with your admin username if different.

```bash
psql -U postgres -f database/00_create_database.sql
psql -U bca_g6_app -d "bca-g6" -f database/01_schema.sql
psql -U bca_g6_app -d "bca-g6" -f database/02_seed.sql
psql -U bca_g6_app -d "bca-g6" -f database/03_validate.sql
```

App user credentials created by the scripts:
- **User:** `bca_g6_app`
- **Password:** `bca_g6_app_change_me` (change before any shared deployment)
- **Database:** `bca-g6`

See [database/README.md](database/README.md) for rollback instructions.

---

## 2. Backend

Spring Boot 3.4.3 / Java 21 project in the `backend/` folder.

```bash
cd backend

# Build (use project-local settings to bypass corporate Maven mirror)
mvn -s .mvn\settings.xml compile

# Run
mvn -s .mvn\settings.xml spring-boot:run
```

Default URL: `http://localhost:8080`  
Swagger UI: `http://localhost:8080/swagger-ui.html`

The database connection is configured in [backend/src/main/resources/application.properties](backend/src/main/resources/application.properties).  
Run the database scripts first (Step 1) before starting the backend.

### File uploads

Complaint attachments are stored on the local filesystem at:

```
%USERPROFILE%\bca-uploads\      (Windows default, e.g. C:\Users\<you>\bca-uploads)
~/bca-uploads/                  (Linux / macOS default)
```

Each file is saved as `<UUID>_<filename>` to prevent name collisions. The original name, path, size, and MIME type are recorded in the `complaint_attachment` database table.

To use a different directory, set `app.upload.dir` in `application.properties`:

```properties
app.upload.dir=C:/my-custom-upload-dir
```

---

## 3. Frontend

```bash
cd frontend

# First time only — install dependencies
npm install

# Copy environment config and set backend URL if needed
copy .env.example .env.local

# Start development server (http://localhost:3000)
npm run dev
```

### Environment variables (`frontend/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8080` | Base URL of the Spring Boot backend |

### Build for production

```bash
cd frontend
npm run build      # output in frontend/dist/
npm run preview    # preview the production build locally
```

---

## Project Structure

```
banking-complaint-agent-group-6/
├── database/          # PostgreSQL schema, seed and validation scripts
├── backend/           # Spring Boot API (Java)
├── frontend/          # React application (Vite)
├── agent/             # AI agent (Python)
├── ARCHITECTURE.md    # Requirements and TODOs
├── DESIGN.md          # Visual design system reference
├── DATABASE_PLAN.md   # Database implementation plan
├── BACKEND_PLAN.md    # Backend implementation plan
└── FRONTEND_PLAN.md   # Frontend implementation plan
```
