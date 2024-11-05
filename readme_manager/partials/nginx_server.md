server_tokens               off;
access_log                  /var/log/nginx/supersecure.access.log;
error_log                   /var/log/nginx/supersecure.error.log;

server {
    listen         80;
    server_name    [DOMAIN_NAME];
    # force https-redirects
    if ($scheme = http) {
        return 301 https://$server_name$request_uri;
        }

    location / {
         proxy_pass              http://{ip_of_home_server}:[PROJECT_DOCKER_PORT];
         proxy_set_header        Host $host;
         proxy_set_header        X-Forwarded-Proto $scheme;

	 # WebSocket support
         proxy_http_version 1.1;
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection "upgrade";
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/arpansahu.me/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/arpansahu.me/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}