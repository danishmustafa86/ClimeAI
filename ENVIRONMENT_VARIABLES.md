# Environment Variables Configuration

## Required Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Database Configuration
DB_URI=mongodb://localhost:27017/climeai

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
OPENCAGE_API_KEY=your_opencage_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Server Configuration
BASE_URL=http://localhost:8000
```

## Frontend Environment Variables

Create a `.env` file in the frontend directory with:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api
```

## Production Deployment

For production deployment on Vercel:

1. **Backend**: Set `BASE_URL` to your deployed backend URL (e.g., `https://your-backend-domain.com`)
2. **Frontend**: Set `VITE_API_BASE_URL` to your deployed backend API URL (e.g., `https://your-backend-domain.com/api`)

## Vercel Environment Variables

In your Vercel dashboard, add these environment variables:

### Frontend (Vercel)
- `VITE_API_BASE_URL`: `https://your-backend-domain.com/api`

### Backend (if deploying separately)
- `BASE_URL`: `https://your-backend-domain.com`
- All the API keys from the backend `.env` file
