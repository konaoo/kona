# 快速回退指南

## 稳定版本: v10.9.10

**功能状态：**
- ✅ 数据正常显示（全部21条）
- ✅ 分类切换正常（全部、A股、基金、港股、美股）
- ✅ 无感知数据更新（只更新变化的数值，不闪烁）
- ✅ 港股、美股、基金价格正常获取

## 快速回退命令

### 方法1：使用稳定标签（推荐）
```bash
git checkout stable-v10.9.10
```

### 方法2：使用备份分支
```bash
git checkout backup-stable-v10.9.10
```

## 重启服务
```bash
# 停止当前服务
lsof -ti:5003 | xargs kill -9

# 重启Flask
python3 app.py &
```

## 查看所有版本标签
```bash
git tag -l
```

## 查看版本记录
```bash
cat CHANGELOG.md
```

## 当前已验证的版本
- v10.9.10 - 稳定工作版本（数据正常显示，分类切换正常）
- v10.9.10 - 修复：使用绝对URL避免浏览器相对URL拼接问题

## 如果需要继续在main分支开发
回退到稳定版本后，如果需要继续开发：
```bash
# 创建新的分支进行开发
git checkout -b feature-xxx stable-v10.9.10
```
