# GigNova Frontend

## Overview

The GigNova frontend is a React-based web application that provides the user interface for the GigNova freelancer platform. It allows clients to post jobs, freelancers to find work, and both parties to manage their contracts through a blockchain-powered escrow system.

## Features

- **User Authentication**: Login and registration for clients and freelancers
- **Job Management**: Create, view, and manage job postings
- **Contract Handling**: Interact with smart contracts for secure escrow payments
- **Profile Management**: Create and update user profiles
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Styling**: CSS with modular approach
- **Linting**: ESLint with TypeScript support

## Directory Structure

```
frontend/
├── public/             # Static assets
├── src/
│   ├── assets/         # Images, fonts, etc.
│   ├── App.tsx         # Main application component
│   ├── App.css         # Main application styles
│   ├── main.tsx        # Application entry point
│   ├── index.css       # Global styles
│   └── vite-env.d.ts   # Vite environment types
├── Dockerfile          # Docker configuration
├── package.json        # Dependencies and scripts
└── tsconfig.json       # TypeScript configuration
```

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

```bash
# Navigate to the frontend directory
cd /Users/a/Documents/Agrlab/superior-agents/GigNova/frontend

# Install dependencies
npm install
# or
yarn install
```

### Development

```bash
# Start the development server
npm run dev
# or
yarn dev
```

The application will be available at `http://localhost:5173`.

### Building for Production

```bash
# Build the application
npm run build
# or
yarn build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
# Preview the production build
npm run preview
# or
yarn preview
```

## Integration with Backend

The frontend communicates with the backend API at `http://localhost:8889/api/v1`. The main API endpoints used are:

- `/auth/login` - User authentication
- `/jobs` - Job management
- `/profiles` - User profile management

## Integration with Blockchain

The frontend interacts with the GigNovaContract smart contract through the backend API. The contract handles:

- Job creation with escrow funding
- Job completion tracking
- Payment release mechanism
- Dispute creation and resolution

## Docker Support

The frontend can be run in a Docker container using the provided Dockerfile:

```bash
# Build the Docker image
docker build -t gignova-frontend .

# Run the container
docker run -p 5173:80 gignova-frontend
```

## Development Guidelines

### Code Style

- Follow the TypeScript best practices
- Use functional components with hooks
- Use descriptive variable and function names
- Add comments for complex logic

### Adding New Features

1. Create new components in the `src/components` directory (create if it doesn't exist)
2. Update the main `App.tsx` file to include your new components
3. Add any new API calls to the appropriate sections
4. Update styles in the corresponding CSS files

### Testing

To add tests:

1. Create a `__tests__` directory
2. Add test files with the `.test.tsx` extension
3. Run tests with `npm test` or `yarn test` (after adding the test script to package.json)

## Troubleshooting

### Common Issues

- **API Connection Errors**: Ensure the backend server is running at the expected URL
- **Build Errors**: Check for TypeScript errors or missing dependencies
- **Smart Contract Interaction Issues**: Verify the contract address and ABI are correct

## Future Enhancements

- Add real-time notifications
- Implement a messaging system between clients and freelancers
- Add portfolio showcase for freelancers
- Integrate with more payment methods
- Add advanced search and filtering for jobs
