# HR Tool - Hệ thống quản lý nghỉ phép

## 📋 Mô tả

HR Tool là một ứng dụng web được xây dựng bằng Vue.js 3 để quản lý nghỉ phép của nhân viên. Ứng dụng hỗ trợ cả chế độ nhân viên thường và quản lý.

## ✨ Tính năng chính

### 👤 Chế độ nhân viên
- **Đăng nhập an toàn** với Active Directory
- **Xem lịch sử nghỉ phép** theo dạng danh sách hoặc lịch
- **Tạo đơn xin nghỉ phép** mới với giao diện thân thiện
- **Remember Me** - Duy trì đăng nhập
- **Auto token refresh** - Tự động làm mới token

### 👨‍💼 Chế độ quản lý
- **Quản lý danh sách nhân viên** dưới quyền
- **Xem lịch nghỉ phép** của toàn bộ team
- **Phê duyệt/từ chối** đơn xin nghỉ phép
- **Thống kê** nghỉ phép theo tháng

## 🛠️ Công nghệ sử dụng

- **Frontend**: Vue.js 3 + Composition API
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **UI Framework**: Bootstrap 5
- **Build Tool**: Vite
- **Calendar**: FullCalendar
- **HTTP Client**: Fetch API

## 📦 Cài đặt

### Yêu cầu hệ thống
- Node.js 16+ 
- npm hoặc yarn

### Bước 1: Clone repository
```bash
git clone <repository-url>
cd hr_tool
```

### Bước 2: Cài đặt dependencies
```bash
npm install
```

### Bước 3: Cấu hình environment
Tạo file `.env` trong thư mục gốc:
```env
# API Configuration
VITE_API_BASE_URL=http://192.168.1.70:5002

# App Configuration
VITE_APP_TITLE=HR Tool
VITE_APP_VERSION=1.0.0

# Development Configuration
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug
```

### Bước 4: Chạy ứng dụng
```bash
# Development mode
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## 🏗️ Cấu trúc project

```
hr_tool/
├── src/
│   ├── components/          # Vue components
│   │   ├── AddLeave.vue     # Form tạo đơn nghỉ phép
│   │   ├── LeaveData.vue    # Hiển thị danh sách nghỉ phép
│   │   ├── LeaveDataCalendar.vue  # Hiển thị lịch nghỉ phép
│   │   ├── ManagerList.vue  # Quản lý danh sách nhân viên
│   │   ├── ManagerCalendar.vue    # Lịch nghỉ phép quản lý
│   │   └── UserInfo.vue     # Thông tin người dùng
│   ├── views/               # Page components
│   │   ├── login.vue        # Trang đăng nhập
│   │   ├── home.vue         # Trang chính nhân viên
│   │   └── manager.vue      # Trang chính quản lý
│   ├── stores/              # Pinia stores
│   │   └── user.js          # User state management
│   ├── router/              # Vue Router
│   │   └── index.js         # Route configuration
│   ├── services/            # API services
│   │   └── api.js           # API service layer
│   ├── config/              # Configuration files
│   │   └── api.js           # API configuration
│   ├── utils/               # Utility functions
│   │   └── userUtils.js     # User-related utilities
│   └── assets/              # Static assets
├── public/                  # Public files
├── index.html               # HTML template
├── package.json             # Dependencies
├── vite.config.js           # Vite configuration
└── README.md                # Project documentation
```

## 🔧 Cấu hình API

### Endpoints
- `POST /auth/login` - Đăng nhập
- `POST /auth/logout` - Đăng xuất  
- `POST /auth/refresh` - Làm mới token
- `POST /leave/attendance` - Lấy dữ liệu nghỉ phép
- `POST /leave/type` - Lấy danh sách loại phép
- `POST /leave/submit` - Gửi đơn nghỉ phép
- `GET /user/profile` - Thông tin người dùng
- `GET /user/subordinates` - Danh sách nhân viên dưới quyền

### Authentication
Ứng dụng sử dụng JWT token với Bearer authentication:
```
Authorization: Bearer <access_token>
```

## 🚀 Deployment

### Build cho production
```bash
npm run build
```

### Deploy lên GitHub Pages
```bash
npm run deploy
```

### Deploy lên server khác
1. Build project: `npm run build`
2. Copy thư mục `dist/` lên server
3. Cấu hình web server (nginx, Apache) để serve static files
4. Cấu hình CORS nếu cần thiết

## 🔒 Bảo mật

- **Token-based authentication** với JWT
- **Auto token refresh** để duy trì session
- **Remember Me** với localStorage/sessionStorage
- **Input validation** và sanitization
- **CORS protection** (cần cấu hình server)

## 🐛 Troubleshooting

### Lỗi kết nối API
1. Kiểm tra `VITE_API_BASE_URL` trong file `.env`
2. Đảm bảo API server đang chạy
3. Kiểm tra CORS configuration trên server

### Lỗi authentication
1. Xóa localStorage và sessionStorage
2. Đăng nhập lại
3. Kiểm tra token expiration

### Lỗi build
1. Xóa `node_modules/` và `package-lock.json`
2. Chạy `npm install` lại
3. Kiểm tra Node.js version

## 📝 Changelog

### Version 1.0.0
- ✅ Đăng nhập với Active Directory
- ✅ Xem lịch sử nghỉ phép
- ✅ Tạo đơn xin nghỉ phép
- ✅ Quản lý nhân viên (Manager)
- ✅ Lịch nghỉ phép
- ✅ Remember Me functionality
- ✅ Auto token refresh
- ✅ Responsive design

## 🤝 Đóng góp

1. Fork project
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Liên hệ

- **Email**: support@company.com
- **Phone**: +84 xxx xxx xxx
- **Address**: Company Address

---

**Lưu ý**: Đây là phiên bản beta. Vui lòng báo cáo bugs và đề xuất cải tiến qua GitHub Issues.
