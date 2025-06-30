FROM node:18-alpine

# Аргумент для URL Mini App
ARG MINIAPP_URL=https://loyalty-bot1.onrender.com
ENV MINIAPP_URL=$MINIAPP_URL

# Install build dependencies
RUN apk add --no-cache python3 make g++ sqlite-dev

# Set working directory
WORKDIR /app

# Copy package files
COPY miniapp/package*.json ./

# Clean npm cache and install dependencies with native modules rebuilt
RUN npm cache clean --force \
    && npm install --production --build-from-source

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
