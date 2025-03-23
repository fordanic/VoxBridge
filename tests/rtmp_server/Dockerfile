FROM alpine:3.18

# Install nginx with rtmp module
RUN apk add --no-cache \
    nginx \
    nginx-mod-rtmp && \
    mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Create directories and set permissions
RUN mkdir -p /var/www/html /tmp/hls && \
    chown -R nginx:nginx /tmp/hls /var/www/html

# Create status page
RUN echo '<html>\
    <head>\
        <title>RTMP Server Status</title>\
        <meta http-equiv="refresh" content="5">\
        <style>\
            body { font-family: sans-serif; margin: 20px; }\
            .status { padding: 10px; margin: 10px 0; background: #f5f5f5; }\
        </style>\
    </head>\
    <body>\
        <h1>RTMP Server Status</h1>\
        <div class="status">\
            <p><strong>Server Running</strong></p>\
            <p>Stream URL: rtmp://localhost/live/test</p>\
            <p>Port: 1935</p>\
        </div>\
    </body>\
    </html>' > /var/www/html/index.html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
RUN chown nginx:nginx /etc/nginx/nginx.conf && \
    chmod 644 /etc/nginx/nginx.conf

# Configure logging
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# Expose ports
EXPOSE 1935 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
