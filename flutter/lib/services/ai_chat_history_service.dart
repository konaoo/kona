import '../models/chat_message.dart';
import 'cache_service.dart';

class AiChatHistoryService {
  static const String _storageVersion = 'v1';
  static const int _maxMessages = 100;

  final CacheService _cache;

  AiChatHistoryService({CacheService? cache})
    : _cache = cache ?? CacheService();

  String _storageKey({required String? userId, required String? username}) {
    final normalizedUserId = (userId ?? '').trim();
    if (normalizedUserId.isNotEmpty) {
      return 'ai_chat_history_$_storageVersion:$normalizedUserId';
    }
    final normalizedUsername = (username ?? '').trim().toLowerCase();
    if (normalizedUsername.isNotEmpty) {
      return 'ai_chat_history_$_storageVersion:user:$normalizedUsername';
    }
    return 'ai_chat_history_$_storageVersion:guest';
  }

  Future<List<ChatMessage>> loadMessages({
    required String? userId,
    required String? username,
  }) async {
    final payload = await _cache.getJson(
      _storageKey(userId: userId, username: username),
    );
    if (payload == null) return const <ChatMessage>[];
    final items = payload['items'];
    if (items is! List) return const <ChatMessage>[];
    return items
        .whereType<Map>()
        .map((item) => ChatMessage.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<void> persistMessages({
    required String? userId,
    required String? username,
    required List<ChatMessage> messages,
  }) async {
    final trimmed = messages.length > _maxMessages
        ? messages.sublist(messages.length - _maxMessages)
        : messages;
    await _cache.setJson(_storageKey(userId: userId, username: username), {
      'items': trimmed.map((item) => item.toJson()).toList(),
      'saved_at': DateTime.now().toIso8601String(),
    });
  }

  Future<void> clearMessages({
    required String? userId,
    required String? username,
  }) async {
    await _cache.remove(_storageKey(userId: userId, username: username));
  }
}
