# 🚀 Technoverse Portal | Hari University (Deemed to be University)

An executive, mobile-responsive management portal for the **Technoverse Club** (Official Technical Body of Hari University), built with **FastHTML**, **Supabase** (PostgreSQL & S3 Cloud Storage), and ready for **100% FREE** deployment on **Render.com** or **Hugging Face Spaces**.

---

## 🏛️ Official Committee Credentials & Hierarchy

| S.No | Designation | Appointed Officer | Branch | Roll Number (User ID) | Mobile Number (Password) | Provisioned Role |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | **President** | **Karthik** | CSE-1 (1st Year B.Tech) | `26ET103047` | `9032936677` | `president` |
| **2** | **Vice President** | **D. Yakshagna** | CSM-3 (1st Year B.Tech) | `26ET104152` | `9894474159` | `vice_president` |
| **3** | **Secretary** | **B. Sariyu** | CSD (1st Year B.Tech) | `26ET102005` | `8519802425` | `secretary` |
| **4** | **Treasurer** | **Chaitanya** | CSM-1 (1st Year B.Tech) | `26ET104048` | `8639638181` | `treasurer` |
| **5** | **Technical Lead** | **Harsha** | CSE-1 | `26ET1030` | `7382620603` | `technical_lead` |
| **6** | **Technical Lead** | **Manikanta** | CSE-2 | `26ET103101` | `9948856065` | `technical_lead` |
| **7** | **Event Coordinator** | **Swetha** | CSM-2 | `26ET104126` | `7816013446` | `event_coordinator` |
| **8** | **Event Coordinator** | **B. Thanusree** | CSC | `26ET101037` | `9281289762` | `event_coordinator` |
| **9** | **Event Coordinator** | **Sahasra** | CSE-2 | `26ET103065` | `9505499928` | `event_coordinator` |
| **10**| **Club Coordinator** | **Chandini.B** | CSE (Faculty Advisor) | `COORD01` | `coordinator123` | `club_coordinator` |

---

## ⚡ Key Enterprise Features

1. **👑 Presidential Governance Desk (`/president`):** Exclusive executive command suite with Presidential Directive Dispatcher, major budget sanctions, and committee member provisioning.
2. **⚔️ VP Operations Command (`/vice-president`):** Direct operational task allocation, live inter-wing Kanban task injection, and Hari University campus venue clearances.
3. **🛠️ Secret Admin Control CMS (`/admin-control`):** Complete autonomous content manager for President and Club Coordinator to update all sections (Hero, 4 Pillars, Urgent Alert Banner, Club Schedule, Maintenance Mode) without touching code.
4. **☁️ Supabase Cloud File Storage (`/files`):** Direct cloud file uploads (PDFs, images, ZIPs, decks) into Supabase S3 storage bucket `club-files`.
5. **⏰ 24/7 Supabase Keep-Alive (`.github/workflows/supabase_keepalive.yml`):** Automated scheduled cron that runs every 3 days to prevent Supabase inactivity pausing.

---

## 💻 Local Quickstart

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Verify Configuration:**
   Ensure `.env` contains:
   ```env
   SECRET_KEY=e7e2cd2ac66414f8dc826931c5dcaee066d2b1c647657655ea02889b2ad25c76
   SUPABASE_URL=https://yqhiigzwlumnidqqtfpw.supabase.co
   SUPABASE_SERVICE_KEY=your_service_role_key
   ```
3. **Run Dev Server:**
   ```bash
   python app.py
   ```
   Open `http://localhost:5001` in your browser.

---

## 🌐 Free Cloud Deployment (Without Vercel)

### Option A: Render.com (100% Free Forever)
1. Push this repository to your GitHub account:
   ```bash
   git remote set-url origin https://github.com/<YOUR_USERNAME>/technoverse-portal.git
   git push -u origin main
   ```
2. Go to [render.com](https://render.com) → Click **New +** → **Web Service** → Select `technoverse-portal`.
3. Render automatically detects [`render.yaml`](render.yaml). Add environment variables:
   - `SUPABASE_URL`: `https://yqhiigzwlumnidqqtfpw.supabase.co`
   - `SUPABASE_SERVICE_KEY`: `your_service_role_key`
4. Click **Deploy Web Service** → Live at `https://technoverse-portal.onrender.com`!

### Option B: Hugging Face Spaces (Free 24/7 Docker Web App)
1. Open [huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose **Docker** or **Blank**, name it `technoverse-portal`.
3. Drag and drop project files in the browser and commit to main.
4. Add environment variables under Settings → Secrets.

---

## 🛡️ Security & Registration Constraints
- **Public Registration Blocked:** Direct signup (`/register`) is permanently disabled with a security notice.
- **Provisioning Authority:** Only **Chandini.B** (`COORD01`) and **Karthik** (`26ET103047`) can provision new accounts from `/team`.
- **Passcode Hashing:** All credentials protected with salted `bcrypt`.
