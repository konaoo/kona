import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart' show VoidCallback;
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/chat_message.dart';
import 'api_service.dart';

typedef AiCreditsRequiredHandler =
    void Function({
      required String message,
      required int aiCreditsBalance,
      required String userGroupText,
      required String userGroupImageUrl,
    });

/// AI 聊天 SSE 流式请求封装
class AiChatService {
  final ApiService _api = ApiService();

  /// 发送聊天消息，通过回调流式返回结果
  ///
  /// [messages] 对话历史
  /// [onDelta] 每收到一段文本时回调
  /// [onDone] 流式传输完成时回调
  /// [onError] 发生错误时回调
  ///
  /// 返回一个函数，调用可取消请求
  Future<VoidCallback?> sendMessage({
    required List<ChatMessage> messages,
    required void Function(String delta) onDelta,
    required void Function() onDone,
    required void Function(String error) onError,
    AiCreditsRequiredHandler? onCreditsRequired,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}${ApiConfig.aiChat}');
    final headers = _api.buildHeaders();

    final request = http.Request('POST', url);
    request.headers.addAll(headers);
    request.body = jsonEncode({
      'messages': messages.map((m) => m.toJson()).toList(),
    });

    http.Client? client;
    try {
      client = http.Client();
      final response = await client.send(request).timeout(
            const Duration(seconds: 120),
          );

      if (response.statusCode != 200) {
        final body = await response.stream.bytesToString();
        String errorMsg;
        try {
          final data = jsonDecode(body);
          if (data is Map<String, dynamic> &&
              data['code']?.toString() == 'AI_CREDITS_REQUIRED') {
            onCreditsRequired?.call(
              message: data['error']?.toString().trim().isNotEmpty == true
                  ? data['error'].toString()
                  : '当前没有可用积分，加入咔咔用户群获取积分',
              aiCreditsBalance: _asInt(data['ai_credits_balance']),
              userGroupText: data['user_group_text']?.toString().trim().isNotEmpty == true
                  ? data['user_group_text'].toString().trim()
                  : '加入咔咔用户群',
              userGroupImageUrl: data['user_group_image_url']?.toString().trim() ?? '',
            );
            client.close();
            return null;
          }
          errorMsg = data['error'] ?? '请求失败 (${response.statusCode})';
        } catch (_) {
          if (response.statusCode == 429) {
            errorMsg = '请求过于频繁，请稍后再试';
          } else {
            errorMsg = '请求失败 (${response.statusCode})';
          }
        }
        onError(errorMsg);
        client.close();
        return null;
      }

      // 用一个变量追踪 client，以便在外部取消
      final activeClient = client;
      void cancel() {
        activeClient.close();
      }

      // 异步消费 SSE 流
      _consumeStream(
        response.stream,
        onDelta,
        onDone,
        onError,
        activeClient,
        onCreditsRequired: onCreditsRequired,
      );

      return cancel;
    } catch (e) {
      client?.close();
      if (e is TimeoutException) {
        onError('请求超时，请稍后再试');
      } else {
        onError('网络连接失败');
      }
      return null;
    }
  }

  void _consumeStream(
    http.ByteStream stream,
    void Function(String) onDelta,
    void Function() onDone,
    void Function(String) onError,
    http.Client client, {
    AiCreditsRequiredHandler? onCreditsRequired,
  }
  ) {
    String buffer = '';

    stream.transform(utf8.decoder).listen(
      (chunk) {
        buffer += chunk;
        // 按行处理 SSE 数据
        while (buffer.contains('\n')) {
          final idx = buffer.indexOf('\n');
          final line = buffer.substring(0, idx).trim();
          buffer = buffer.substring(idx + 1);

          if (!line.startsWith('data: ')) continue;
          final jsonStr = line.substring(6);

          try {
            final data = jsonDecode(jsonStr);
            if (data['done'] == true) {
              onDone();
              client.close();
              return;
            }
            if (data['code']?.toString() == 'AI_CREDITS_REQUIRED') {
              onCreditsRequired?.call(
                message: data['error']?.toString().trim().isNotEmpty == true
                    ? data['error'].toString()
                    : '当前没有可用积分，加入咔咔用户群获取积分',
                aiCreditsBalance: _asInt(data['ai_credits_balance']),
                userGroupText: data['user_group_text']?.toString().trim().isNotEmpty == true
                    ? data['user_group_text'].toString().trim()
                    : '加入咔咔用户群',
                userGroupImageUrl: data['user_group_image_url']?.toString().trim() ?? '',
              );
              client.close();
              return;
            }
            if (data['error'] != null) {
              onError(data['error']);
              client.close();
              return;
            }
            if (data['delta'] != null) {
              onDelta(data['delta'] as String);
            }
          } catch (_) {
            // 忽略解析失败的行
          }
        }
      },
      onDone: () {
        onDone();
        client.close();
      },
      onError: (e) {
        onError('连接中断');
        client.close();
      },
    );
  }

  int _asInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    if (value is String) return int.tryParse(value.trim()) ?? 0;
    return 0;
  }
}
