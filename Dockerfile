FROM homeassistant/home-assistant:stable

# Copy custom component
COPY custom_components/intuis /config/custom_components/intuis

# Set working directory
WORKDIR /config

# Expose port
EXPOSE 8123

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8123/ || exit 1
