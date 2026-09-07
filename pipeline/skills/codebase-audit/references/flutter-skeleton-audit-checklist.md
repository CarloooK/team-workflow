# Flutter 骨架项目审计检查清单

从物流管理系统移动端（Flutter 3.x + Provider）审计中提炼。

## 一、登录流程 Bug 模式

### 常见错误：Provider 使用不当

```dart
// BAD — 自定义 extension 但方法体 throw
extension AuthServiceAccessor on BuildContext {
  AuthService get auth => AuthService.of(this);
}
class AuthService {
  static AuthService of(BuildContext context) {
    throw UnimplementedError();  // 永远不会走到这里
  }
}

// GOOD — 通过 Provider 获取
final auth = Provider.of<AuthService>(context, listen: false);
// 或
final auth = context.read<AuthService>();
```

### 检查要点
1. Provider 是否在 `main.dart` 的 `MultiProvider` 中正确注册
2. `ProxyProvider` 的 `update` 回调签名是否正确
3. 登录后 token 是否保存到 `SharedPreferences` 并在下次启动时读取

## 二、API 层常见问题

```dart
// BAD — baseUrl 硬编码
ApiService(baseUrl: 'http://YOUR_SERVER:3000/api/v1')

// GOOD — 环境变量或配置类
ApiService(baseUrl: dotenv.env['API_URL'] ?? 'http://localhost:3000/api/v1')
```

### 检查要点
1. 错误处理：HTTP 4xx/5xx 是否统一处理？是否抛异常？
2. Token 过期：401 时是否自动跳转登录页？
3. 响应格式：后端返回格式是否与客户端期望一致？

## 三、路由未注册

```dart
// BAD — 页面跳转路由未在 MaterialApp 中注册
Navigator.pushNamed(context, '/driver/tasks');
// 需要在 MaterialApp 中定义：
// routes: { '/driver/tasks': (context) => const DriverTasksPage() }

// GOOD — 使用 onGenerateRoute 统一管理
```

### 检查要点
1. `MaterialApp.routes` 或 `onGenerateRoute` 是否覆盖所有 `pushNamed` 调用
2. 路由命名是否一致（注意大小写和拼写）

## 四、Flutter 项目完整性检查

### 文件清单
```
mobile/
├── pubspec.yaml            # 依赖声明
├── lib/
│   ├── main.dart           # 入口 + Provider 注册 + 路由
│   ├── services/
│   │   ├── api_service.dart    # HTTP 请求封装
│   │   └── auth_service.dart   # 登录状态管理 + token 持久化
│   └── pages/
│       ├── common/
│       │   ├── login_page.dart # 登录页
│       │   └── home_page.dart  # 主页（按角色分发）
│       ├── driver/
│       │   └── driver_home.dart # 司机端首页
│       ├── boss/
│       │   └── boss_home.dart   # 老板端首页
│       └── finance/
│           └── finance_home.dart # 财务端首页
```

### 骨架 vs 可用状态判断
| 有 ✅ | 缺 ❌ |
|-------|-------|
| 项目结构完整 | 子页面（任务详情/打卡/费用提交/报销进度/油耗）未实现 |
| Provider 状态管理 | 路由未注册 |
| HTTP 请求封装 | login_page.dart 有自引用 bug |
| 按角色分发主页 | baseUrl 硬编码 |
| 司机端 6 个快捷入口 UI | 非司机角色页面为空 |

## 五、依赖合理性评估

| 依赖 | 用途 | 评估 |
|------|------|------|
| `provider` | 状态管理 | ✅ 适合中小项目 |
| `http` | HTTP 请求 | ✅ 简单够用，不需要 dio |
| `shared_preferences` | 本地存储 | ✅ token 持久化 |
| `geolocator` | 定位打卡 | ✅ 符合需求 |
| `image_picker` | 费用拍照 | ✅ 符合需求 |
| `intl` | 日期格式化 | ✅ |
| `flutter_local_notifications` | 通知推送 | ⚠️ 骨架阶段可用，生产环境需接入极光/FCM |
