FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY miniapp/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy app source
COPY miniapp/ .

# Copy main project files (if needed by api_integration.js)
COPY loyalty.db ./
COPY ux_copy_texts.py ../
COPY ux_copy_texts_minimal.py ../

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/ || exit 1

# Start the application
CMD ["npm", "start"]
