# Deploying Weather Map API to Render.com

## Prerequisites
- A Render.com account
- Git repository with your code
- Python 3.12+

## Deployment Steps

### Option 1: Deploy via Render Dashboard

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create a New Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository: `wetherproject`

3. **Configure the Service**
   - **Name**: `weather-map-api` (or your choice)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free or paid tier

4. **Add Persistent Disk (Important!)**
   - In the service settings, go to "Disks"
   - Add a new disk:
     - **Name**: `meteo-storage`
     - **Mount Path**: `/opt/render/project/src/meteo`
     - **Size**: 1GB (or more as needed)
   - This ensures generated maps persist across deployments

5. **Deploy**
   - Click "Create Web Service"
   - Wait for the build and deployment to complete
   - Your API will be available at: `https://your-service-name.onrender.com`

### Option 2: Deploy via render.yaml (Blueprint)

1. **Push code with render.yaml**
   ```bash
   git add render.yaml
   git commit -m "Add Render blueprint"
   git push origin main
   ```

2. **Deploy from Blueprint**
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will automatically detect `render.yaml`
   - Click "Apply" to deploy

## Environment Variables

No environment variables are required by default. The app automatically uses the `PORT` variable provided by Render.

## Testing Your Deployment

Once deployed, test the API:

```bash
# Get API info
curl https://your-service-name.onrender.com/

# Check health
curl https://your-service-name.onrender.com/health

# List countries
curl https://your-service-name.onrender.com/countries

# Generate all maps
curl -X POST https://your-service-name.onrender.com/generate/all \
  -H "Content-Type: application/json" \
  -d @meteo.json
```

## Accessing Generated Maps

Generated maps are accessible via HTTP:
- List all files: `https://your-service-name.onrender.com/meteo/files`
- Download map: `https://your-service-name.onrender.com/meteo/dz/2026-01-20/maxtemp.png`

## Important Notes

### Free Tier Limitations
- **Spin down**: Free services spin down after 15 minutes of inactivity
- **Cold starts**: First request after spin down takes 30-60 seconds
- **Storage**: Disk storage is not included in free tier
  - Consider upgrading to Starter plan ($7/month) for persistent disk
  - Or use external storage (S3, Cloudinary, etc.)

### Performance Tips
1. **Upgrade to paid plan** for:
   - Persistent disk storage
   - No spin down
   - Better performance

2. **Use external storage** (free tier):
   - Modify `weather_map_service.py` to upload to S3/Cloudinary
   - Store only URLs in your database
   - Serve images from CDN

### Monitoring
- View logs in Render Dashboard → Your Service → Logs
- Monitor service health: Dashboard → Your Service → Metrics

## Troubleshooting

### Maps not persisting
- Ensure persistent disk is configured
- Check mount path matches: `/opt/render/project/src/meteo`
- Verify disk size is sufficient

### Build failures
- Check `requirements.txt` is up to date
- Ensure Python version matches (3.12)
- Review build logs in Render Dashboard

### Port binding errors
- App automatically uses `$PORT` environment variable
- Don't hardcode port 8000 in production

## Updating Your Deployment

Push changes to GitHub:
```bash
git add .
git commit -m "Update description"
git push origin main
```

Render will automatically rebuild and redeploy.

## Alternative: Manual Deploy

If you prefer manual control:
```bash
# On Render shell
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port $PORT
```

## Support

- Render Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com
