# Video Processing Frontend

A modern, responsive React frontend for the AI-powered video processing platform built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- 🎬 **Next.js 14 App Router** - Modern React framework with app directory
- 🎨 **Tailwind CSS** - Utility-first CSS framework with custom design system
- 🔄 **TanStack Query** - Powerful data synchronization and caching
- 🗃️ **Zustand** - Lightweight state management
- 📱 **Responsive Design** - Mobile-first approach with responsive layouts
- 🎥 **react-player** - Video playback integration
- 🌐 **WebSocket Support** - Real-time job progress updates
- 📝 **React Hook Form** - Form handling with validation
- 🎯 **TypeScript** - Full type safety throughout the application

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Landing page
│   ├── jobs/              # Jobs dashboard
│   │   └── page.tsx
│   └── job/[id]/          # Job detail page
│       └── page.tsx
├── components/            # React components
│   ├── forms/            # Form components
│   │   └── job-submission-form.tsx
│   ├── layout/           # Layout components
│   │   └── header.tsx
│   ├── providers/        # Context providers
│   │   └── query-provider.tsx
│   └── ui/               # Reusable UI components
│       ├── badge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── clip-preview.tsx
│       ├── job-card.tsx
│       └── progress.tsx
├── hooks/                # Custom React hooks
│   └── use-websocket.ts
├── lib/                  # Utility libraries
│   ├── api/              # API client
│   │   └── client.ts
│   └── utils/            # Utility functions
│       └── index.ts
├── store/                # State management
│   └── index.ts
├── styles/               # Global styles
│   └── globals.css
└── types/                # TypeScript types
    └── index.ts
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (optional - works in mock mode)

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your API configuration:
   ```
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check

## Core Features

### Landing Page
- Hero section with job submission form
- YouTube URL validation
- Job type selection (Shorts, Clips, Analysis)
- Feature overview and benefits

### Jobs Dashboard
- Grid view of all submitted jobs
- Status filtering and sorting
- Job statistics and counts
- Quick actions for each job

### Job Detail View
- Real-time progress tracking
- Processing stage timeline
- Generated clip preview grid
- Download and sharing options
- WebSocket live updates

### UI Components
- **Progress Bars** - Customizable progress indicators
- **Status Badges** - Color-coded status indicators with icons
- **Job Cards** - Comprehensive job display with actions
- **Clip Preview** - Video player with inline controls
- **Forms** - Validated form components with error handling

## API Integration

The frontend integrates with the FastAPI backend through REST endpoints and WebSocket connections for real-time updates.

### Mock Mode
When the backend is unavailable, the application automatically falls back to mock mode with simulated data for testing purposes.

## Design System

- **Colors**: Primary blue, success green, warning yellow, error red
- **Typography**: Inter font with proper scaling
- **Spacing**: Consistent spacing scale
- **Components**: Reusable UI primitives with variants

## Development

This frontend scaffold is ready for development and includes:
- TypeScript strict mode
- ESLint configuration
- Tailwind CSS setup
- Component library
- State management
- API client
- WebSocket integration
- Responsive design

Run `npm run dev` to start the development server and begin building!
