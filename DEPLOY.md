# 🚀 MediaGrab Deployment Guide

## Project Structure
```
django_DRF/          ← Django Backend (deploy to Render)
├── django_rest/
├── downloader/
├── requirements.txt
├── build.sh
├── render.yaml
└── manage.py

frontend/            ← React Frontend (deploy to Vercel)
├── src/
├── package.json
├── vercel.json
└── index.html
```

---

## Step 1: Push to GitHub

### Option A: Single Repo (Recommended)
Create ONE GitHub repository for the entire project.

1. Go to **https://github.com/new**
2. Create a repo named `mediagrab` (public or private)
3. **Don't** initialize with README
4. Run these commands:

```bash
cd E:\django_DRF
git remote add origin https://github.com/YOUR_USERNAME/mediagrab.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy Backend on Render

1. Go to **https://render.com** and sign up (use GitHub login)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo `mediagrab`
4. Configure:
   - **Name**: `mediagrab-api`
   - **Root Directory**: `.` (leave empty/root)
   - **Runtime**: `Python`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn django_rest.wsgi:application`
5. Add **Environment Variables**:
   - `DJANGO_SECRET_KEY` → Click "Generate" (any random string)
   - `DEBUG` → `False`
   - `PYTHON_VERSION` → `3.12.0`
6. Select **Free** plan
7. Click **"Create Web Service"**
8. Wait for deployment (5-10 minutes)
9. **Copy your Render URL** (e.g., `https://mediagrab-api.onrender.com`)

---

## Step 3: Deploy Frontend on Vercel

1. Go to **https://vercel.com** and sign up (use GitHub login)
2. Click **"Add New Project"**
3. Import your `mediagrab` GitHub repo
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add **Environment Variable**:
   - Key: `VITE_API_URL`
   - Value: `https://mediagrab-api.onrender.com/api` ← (use YOUR Render URL from Step 2)
6. Click **"Deploy"**
7. Wait for deployment (2-3 minutes)

---

## ✅ Done!

Your app will be live at:
- **Frontend**: `https://mediagrab.vercel.app` (or similar)
- **Backend API**: `https://mediagrab-api.onrender.com/api/`

---

## ⚠️ Important Notes

### Render Free Tier Limitations
- Server **spins down after 15 minutes** of inactivity
- First request after spin-down takes ~30 seconds to wake up
- 750 free hours per month

### Tips
- If downloads seem slow, it's because yt-dlp needs time to process
- The free tier has limited memory (512MB), so very large videos may fail
- Render's free tier comes with FFmpeg pre-installed (Linux), so audio MP3 conversion will work!
