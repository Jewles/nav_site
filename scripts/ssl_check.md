# ssl_check.sh — SSL 证书到期检查

> 不用改 hosts，IP + 域名（SNI）直连查证书

## 存放位置

```
~/.openclaw/workspace/scripts/ssl_check.sh
```

## 用法

### 1. 查单个

```
./ssl_check.sh <IP> <域名>
```

示例：

```
./ssl_check.sh 121.40.97.229 fabu.go2.cn
./ssl_check.sh 47.108.39.118 openclaw.test.com
```

### 2. 批量查（一次看一堆）

先建一个域名清单文件，每行一个 `IP 域名`：

```
# domains.txt
121.40.97.229 fabu.go2.cn
47.108.39.118 crond.go2labs.cn
192.168.1.100 internal.dashboard.com
```

然后：

```
./ssl_check.sh -f domains.txt
```

以 `#` 开头的行会被跳过（可以写注释）。

### 3. 交互模式

直接跑，按提示输入：

```
./ssl_check.sh
```

然后依次输入 IP 和域名即可。

## 输出说明

| 颜色 | 含义 |
|------|------|
| 🟢 绿色 | ✅ 剩余 > 30 天，正常 |
| 🟡 黄色 | ⚠️ 剩余 7–30 天，快续了 |
| 🔴 红色 | ❌ < 7 天甚至已过期，立刻处理 |

## 依赖

- **`openssl`** — macOS / Linux 通常自带

## 系统兼容

| 系统 | 状态 | 备注 |
|------|------|------|
| macOS | ✅ 原生支持 | `date -j` 解析日期 |
| Linux | ⚠️ 需微调 | `date` 参数不同 |

Linux 上跑如果日期解析报错，把脚本里这行：

```bash
expire_epoch=$(date -j -f "%b %d %T %Y %Z" "$not_after" +%s 2>/dev/null)
```

改成：

```bash
expire_epoch=$(date -d "$not_after" +%s 2>/dev/null)
```

或者告诉我你在 Linux 上用，我给你准备双平台兼容版。