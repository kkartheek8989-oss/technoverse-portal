# Technoverse Portal

A private, mobile-first management portal for the core team of Technoverse Club, built with **FastHTML**, **Supabase** (PostgreSQL), and deployed on **Vercel** / **Render** for **100% FREE**.

---

## 🚀 1. Free Database Setup (Supabase)

Supabase provides a free-tier PostgreSQL database, authentication, and file storage.

1. Go to [https://supabase.com](https://supabase.com) and sign in or create a free account.
2. Click **New Project**:
   - Choose an organization.
   - Enter project name (e.g., `technoverse-portal`).
   - Set a strong database password (keep this safe).
   - Select your nearest region and click **Create new project**.
3. Once the project is provisioned (~1–2 minutes):
   - In the left sidebar, click on **SQL Editor** (the `>_` terminal icon).
   - Click **New Query**.
   - Copy the entire contents of [`schema.sql`](file:///C:/Users/KRISHNA%20KARTHEEK/Downloads/technoverse_portal_fixed/schema.sql) and paste it into the editor.
   - Click **Run** (or press `Ctrl + Enter`).
   - You should see: `Success. No rows returned.` (All 17 tables, indexes, and storage bucket are now created).
4. Get your API Keys:
   - In the left sidebar, go to **Project Settings** (gear icon) → **API**.
   - Copy the **Project URL** (e.g. `https://xyzcompany.supabase.co`).
   - Under **Project API keys**, find `service_role` (secret) and click Reveal/Copy.
     *(Note: The `service_role` key is required because it has server-side admin privileges to bypass RLS).*

---

## 💻 2. Local Setup & Testing

1. In the project root, open `.env` (or copy `.env.example` to `.env`):
   ```env
   SECRET_KEY=e7e2cd2ac66414f8dc826931c5dcaee066d2b1c647657655ea02889b2ad25c76
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-actual-service-role-key
   ```
2. Run the pre-flight verification script:
   ```bash
   python test_connection.py
   ```
   This will verify that your credentials work and that all 17 tables exist in Supabase.
3. Start the local server:
   ```bash
   python app.py
   ```
4. Open your browser at [http://localhost:5001](http://localhost:5001).
   - On the first visit, go to [http://localhost:5001/setup](http://localhost:5001/setup) to create the first **Club Coordinator** account.
   - After creating the account, log in using your Roll Number and Password!

---

## 🌐 3. Make It Live on the Internet for FREE (Vercel)

### Option A: Via GitHub & Vercel Dashboard (Easiest & Recommended)

1. Create a repository on GitHub (can be private or public).
2. Push your project to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit of Technoverse Portal"
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/technoverse-portal.git
   git branch -M main
   git push -u origin main
   ```
3. Go to [https://vercel.com](https://vercel.com) and log in with GitHub.
4. Click **Add New...** → **Project**.
5. Import your `technoverse-portal` repository.
6. Under **Environment Variables**, add the 3 variables:
   - `SECRET_KEY`: (Your 64-char key from `.env`)
   - `SUPABASE_URL`: (Your Supabase project URL)
   - `SUPABASE_SERVICE_KEY`: (Your Supabase service_role secret key)
7. Click **Deploy**.
8. Within 60 seconds, your site is LIVE on the internet with a free `.vercel.app` domain and free HTTPS/SSL!

---

## 🔄 4. Keep-Alive Automation (Prevent Supabase Inactivity Pausing)

Supabase free-tier projects pause if there are no requests for 7 days.
This repository includes an automated GitHub Action workflow:
`.github/workflows/keepalive.yml`

To activate it:
1. In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**.
3. Name: `SITE_URL`
4. Value: Your deployed live URL (e.g. `https://technoverse-portal.vercel.app`).
5. GitHub Actions will automatically ping `https://<YOUR_APP>/health` every 3 days, ensuring your database stays awake 24/7!

---

## 🛡️ Roles & Permissions Reference

| Role | Rank | Access Permissions |
|------|------|--------------------|
| `member` | 1 | Own tasks, register for events, upload files, view team |
| `secretary` | 3 | Meeting minutes owner + section actions |
| `treasurer` | 3 | Club finance owner + section actions |
| `technical_lead` | 3 | Learning hub owner + coding events |
| `event_coordinator` | 3 | Events & registrations owner |
| `vice_president` / `president` | 4 | All section actions + View-As preview persona |
| `club_coordinator` | 5 | Superadmin: all actions, user management, roles & setup |
