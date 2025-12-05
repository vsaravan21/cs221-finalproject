# TripCompass Deployment Guide

This guide explains how to deploy TripCompass to free hosting platforms so it's accessible to anyone with a link.

## Important: Repository Size

This repository uses `.gitignore` to exclude large raw data files. Only essential runtime files are committed:
- ✅ `tripcompass/data/pois_sf_enriched.csv` (processed POI catalog)
- ✅ `tripcompass/data/user_profiles.csv` (user profiles)
- ✅ `tripcompass/main_nn_model.npz` (trained model)
- ✅ `tripcompass/main_scaler.joblib` (feature scaler)
- ❌ Large raw CSV files are excluded (they can be regenerated if needed)

## Quick Start: Deploy to Render.com (Recommended)

Render.com offers free hosting with automatic SSL, perfect for demos and low-traffic applications.

### Prerequisites

1. A GitHub account
2. Your code pushed to a GitHub repository
3. A Render.com account (sign up at https://render.com)

### Step-by-Step Deployment

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Create a Render Web Service**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` configuration

3. **Configure the Service** (if not using render.yaml)
   - **Name**: `tripcompass` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m tripcompass.api_server`
   - **Environment Variables**:
     - `PORT`: `10000` (Render sets this automatically, but we specify it)
     - `FLASK_DEBUG`: `False`

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your app
   - Wait for the build to complete (usually 5-10 minutes)
   - Your app will be available at `https://tripcompass.onrender.com` (or your custom domain)

### Important Notes for Render

- **Cold Starts**: Free tier services spin down after 15 minutes of inactivity. The first request after inactivity may take 15-30 seconds to wake up the service.
- **Build Time**: First deployment may take longer as it installs all dependencies.
- **Data Files**: Ensure all data files (`pois_sf_enriched.csv`, model files, etc.) are committed to your repository.

## Alternative Hosting Options

### Railway.app

Railway offers $5 free credit per month with better uptime than Render's free tier.

1. Sign up at https://railway.app
2. Create a new project
3. Connect your GitHub repository
4. Railway will auto-detect Python and install dependencies
5. Set start command: `python -m tripcompass.api_server`
6. Railway automatically provides a public URL

**Advantages**: Better uptime, no cold starts, $5 free credit/month

### PythonAnywhere

Good for Python-specific applications with a free tier.

1. Sign up at https://www.pythonanywhere.com
2. Upload your code via Git or file upload
3. Create a new Web App
4. Configure WSGI file to point to `tripcompass.api_server:app`
5. Reload the web app

**Advantages**: Python-focused, good documentation, free tier available

### Fly.io

Fast deployment with good performance on free tier.

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up: `fly auth signup`
3. Deploy: `fly launch` (follow prompts)
4. Create `Dockerfile` (Fly can generate one)

**Advantages**: Fast, good performance, global edge network

## Local Testing Before Deployment

Before deploying, test that the production configuration works locally:

```bash
# Set production environment variables
export PORT=5001
export FLASK_DEBUG=False

# Run the server
python -m tripcompass.api_server

# Test in browser
# Open http://localhost:5001
```

## Troubleshooting

### Build Fails

- **Issue**: Dependencies not installing
  - **Solution**: Check `requirements.txt` has all dependencies
  - Ensure Python version is compatible (3.8+)

- **Issue**: Module not found errors
  - **Solution**: Ensure all files are committed to repository
  - Check that `tripcompass/` directory structure is correct

### App Crashes on Start

- **Issue**: Port binding error
  - **Solution**: Ensure using `PORT` environment variable (Render sets this automatically)

- **Issue**: Data files not found
  - **Solution**: Ensure all CSV files and model files are in the repository
  - Check paths in `tripcompass/config.py` are relative

### Frontend Not Loading

- **Issue**: Static files not serving
  - **Solution**: Check that `ui/` directory is in the repository
  - Verify Flask static folder configuration in `api_server.py`

- **Issue**: API calls failing
  - **Solution**: Check browser console for CORS errors
  - Verify API URL is using `window.location.origin` in production

### Cold Start Issues (Render Free Tier)

- **Issue**: First request takes 15-30 seconds
  - **Solution**: This is expected behavior on Render's free tier
  - Consider upgrading to paid tier for better performance
  - Or use Railway.app which has better free tier performance

## Environment Variables

The following environment variables can be set:

- `PORT`: Server port (default: 5001, Render sets automatically)
- `FLASK_DEBUG`: Enable debug mode (default: False, set to "True" for development)

## Updating Your Deployment

After making changes:

1. Commit and push to GitHub
2. Render/Railway will automatically detect changes and redeploy
3. Monitor the build logs in the dashboard

## Custom Domain (Optional)

Both Render and Railway support custom domains:

1. In your service settings, go to "Custom Domains"
2. Add your domain
3. Follow DNS configuration instructions
4. SSL certificates are automatically provisioned

## Monitoring

- **Render**: Check logs in the dashboard under "Logs" tab
- **Railway**: View logs in the project dashboard
- **Health Check**: Your app has a health endpoint at `/api/health`

## Cost Considerations

- **Render Free Tier**: Free, but with cold starts and limited resources
- **Railway**: $5 free credit/month, then pay-as-you-go
- **PythonAnywhere**: Free tier available, paid plans start at $5/month
- **Fly.io**: Free tier with usage limits, then pay-as-you-go

For long-term free hosting, Render's free tier is the best option, though Railway's $5 credit/month is very generous and provides better performance.

