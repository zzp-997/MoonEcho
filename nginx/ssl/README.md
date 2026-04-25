# SSL 证书配置说明

本目录用于存放 Nginx SSL 证书文件。

## 证书文件命名

生产环境需要放置以下文件：

```
nginx/ssl/
├── fullchain.pem    # 完整证书链（包含域名证书 + 中间证书）
├── privkey.pem      # 私钥文件
└── README.md        # 本说明文件
```

## 获取证书的方式

### 方式一：Let's Encrypt（推荐，免费）

使用 Certbot 自动获取和续期证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书（替换 your-domain.com 为实际域名）
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# 证书将保存在 /etc/letsencrypt/live/your-domain.com/
# 复制到项目目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./nginx/ssl/

# 设置权限
sudo chmod 644 ./nginx/ssl/fullchain.pem
sudo chmod 600 ./nginx/ssl/privkey.pem
```

自动续期：

```bash
# 测试续期
sudo certbot renew --dry-run

# 添加定时任务自动续期
sudo crontab -e

# 添加以下行（每天凌晨 3 点检查续期）
0 3 * * * certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/your-domain.com/*.pem /path/to/project/nginx/ssl/ && docker-compose restart nginx"
```

### 方式二：购买商业证书

1. 从证书颁发机构（如 DigiCert、GeoTrust、阿里云等）购买证书
2. 生成 CSR 文件：

```bash
# 生成私钥
openssl genrsa -out privkey.pem 2048

# 生成 CSR
openssl req -new -key privkey.pem -out server.csr -subj "/CN=your-domain.com"
```

3. 将 CSR 提交给证书颁发机构
4. 获取证书后保存为 `fullchain.pem`

### 方式三：自签名证书（仅用于开发测试）

```bash
# 生成自签名证书（有效期 365 天）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/CN=localhost"

# 注意：自签名证书会导致浏览器警告，仅用于本地开发
```

## 启用 HTTPS

修改 `nginx/nginx.conf`，取消 HTTPS server 块的注释：

```nginx
# 找到以下部分并取消注释
server {
    listen 443 ssl http2;
    server_name _;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # ... 其他配置
}
```

## 安全建议

1. **私钥文件权限**：确保 `privkey.pem` 权限为 600，仅 root 可读
2. **证书更新**：定期检查证书有效期，提前续期
3. **HTTPS 重定向**：生产环境强制 HTTPS，在 HTTP server 块中添加重定向：

```nginx
location / {
    return 301 https://$host$request_uri;
}
```

## Docker Compose 配置

证书文件已通过 volume 挂载到容器内：

```yaml
volumes:
  - ./nginx/ssl:/etc/nginx/ssl:ro
```

修改配置后重启 Nginx：

```bash
docker-compose restart nginx
```

## 常见问题

### Q: 证书链不完整

浏览器显示"证书不可信"，但单独访问证书显示有效。

**解决方案**：确保 `fullchain.pem` 包含完整的证书链（域名证书 + 中间证书）。

```bash
# 检查证书链
openssl s_client -connect your-domain.com:443 -showcerts
```

### Q: HTTP/2 不生效

确保 Nginx 配置中包含 `http2` 参数：

```nginx
listen 443 ssl http2;
```

### Q: 混合内容警告

确保网页中所有资源（图片、脚本、样式）都使用 HTTPS 链接。检查 HTML 源码中的 `http://` 链接。

---

**注意**：证书文件包含敏感信息，请勿提交到 Git 仓库。`.gitignore` 中应包含：

```
nginx/ssl/*.pem
!nginx/ssl/README.md
```
