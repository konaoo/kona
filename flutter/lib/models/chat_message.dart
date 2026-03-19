/// AI 聊天消息模型
class ChatMessage {
  final String role; // 'user' | 'assistant'
  final String content;
  final DateTime timestamp;

  ChatMessage({required this.role, required this.content, DateTime? timestamp})
    : timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() => {
    'role': role,
    'content': content,
    'timestamp': timestamp.toIso8601String(),
  };

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    final rawTimestamp = '${json['timestamp'] ?? ''}'.trim();
    return ChatMessage(
      role: '${json['role'] ?? ''}',
      content: '${json['content'] ?? ''}',
      timestamp: rawTimestamp.isNotEmpty
          ? DateTime.tryParse(rawTimestamp)
          : null,
    );
  }
}
